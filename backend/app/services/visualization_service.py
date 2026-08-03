import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

import numpy as np
from skimage import measure
import trimesh
import io

from app.services.storage_service import LocalFileStorage
from app.db.repositories.visualization_repo import create_visualization
from app.db.repositories.analysis_repo import get_analysis

logger = logging.getLogger(__name__)


class VisualizationService:
    """Create 3D visualization artifacts from segmentation masks and save them to storage.

    The service is modular: it can generate a mesh (via marching cubes), compute
    surface area and volume, export a GLB and save metadata. It expects a segmentation
    mask (3D numpy array or path to .npy/.npz/.tif) to be available.
    """

    def __init__(self, storage: Optional[LocalFileStorage] = None):
        self.storage = storage or LocalFileStorage()

    def _load_mask_from_path(self, path: str) -> Optional[np.ndarray]:
        p = Path(path)
        if not p.exists():
            logger.error("Mask path does not exist: %s", path)
            return None
        try:
            if p.suffix == ".npy":
                return np.load(str(p))
            if p.suffix == ".npz":
                return np.load(str(p))["arr_0"]
            # handle single-page tif or image stacks
            if p.suffix in [".tif", ".tiff"]:
                import tifffile
                return tifffile.imread(str(p))
            # fallback: try imread for 2D -> expand to 3D
            import imageio
            img = imageio.imread(str(p))
            if img.ndim == 2:
                return img[np.newaxis, ...]
            return img
        except Exception:
            logger.exception("Failed to load mask from %s", path)
            return None

    def _marching_cubes(self, volume: 'np.ndarray') -> Optional[Dict[str, Any]]:
        try:
            # ensure boolean mask
            mask = (volume > 0).astype(np.uint8)
            # skimage.measure.marching_cubes expects 3D volume with shape (Z, Y, X)
            verts, faces, normals, values = measure.marching_cubes(mask, level=0)
            mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals, process=True)
            return {"mesh": mesh, "verts": verts, "faces": faces}
        except Exception:
            logger.exception("Marching cubes failed")
            return None

    def _export_glb_bytes(self, mesh: 'trimesh.Trimesh') -> Optional[bytes]:
        try:
            # export glb as bytes
            glb = mesh.export(file_type='glb')
            if isinstance(glb, (bytes, bytearray)):
                return bytes(glb)
            # some versions return str
            if isinstance(glb, str):
                return glb.encode('utf-8')
            return None
        except Exception:
            logger.exception("Failed to export GLB bytes")
            return None

    def generate_visualization(self, db, analysis_id: int, mask_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Generate mesh and GLB from a segmentation mask and persist visualization record.
        If mask_path is None the service will try to locate a mask via the analysis record.

        Returns the visualization ORM object as dict-like or None on failure.
        """
        # try to locate mask
        mask = None
        if mask_path:
            mask = self._load_mask_from_path(mask_path)
        else:
            # attempt to derive from analysis record
            analysis = get_analysis(db, analysis_id)
            if analysis and getattr(analysis, 'mask_path', None):
                mask = self._load_mask_from_path(analysis.mask_path)

        if mask is None:
            logger.error("No segmentation mask available for analysis %s", analysis_id)
            return None

        # marching cubes
        mc = self._marching_cubes(mask)
        if mc is None:
            return None
        mesh = mc['mesh']

        # compute metrics
        surface_area = float(mesh.area)
        try:
            volume = float(mesh.volume)
        except Exception:
            # approximate volume by voxel count
            volume = float((mask > 0).sum())

        # export GLB
        glb_bytes = self._export_glb_bytes(mesh)
        if not glb_bytes:
            logger.error("Failed to export GLB for analysis %s", analysis_id)
            return None

        # save files
        mesh_filename = f"visual_mesh_{analysis_id}.glb"
        mesh_rel, _ = self.storage.save_file(glb_bytes, filename=mesh_filename, subpath="visualization")

        # save original volume mask as npz
        try:
            import numpy as _np
            buf = io.BytesIO()
            _np.save(buf, mask)
            buf.seek(0)
            mask_fname = f"visual_mask_{analysis_id}.npy"
            mask_rel, _ = self.storage.save_file(buf.read(), filename=mask_fname, subpath="visualization")
        except Exception:
            logger.exception("Failed to save mask for analysis %s", analysis_id)
            mask_rel = None

        metadata = {
            "analysis_id": analysis_id,
            "surface_area": surface_area,
            "volume": volume,
            "vertices": len(mc['verts']),
            "faces": len(mc['faces']),
        }

        # persist visualization record via repository
        try:
            vis = create_visualization(db, {
                "analysis_id": analysis_id,
                "mesh_path": mesh_rel,
                "texture_path": None,
                "metadata": json.dumps(metadata),
                "volume": volume,
                "surface_area": surface_area,
            })
            return {"visualization": vis, "mesh_rel": mesh_rel, "mask_rel": mask_rel, "metadata": metadata}
        except Exception:
            logger.exception("Failed to create visualization DB record for analysis %s", analysis_id)
            return None
