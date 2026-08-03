import io
import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cv2

from app.services.storage_service import LocalFileStorage
from app.db.repositories.analysis_repo import get_analysis
from app.db.repositories.image_repo import get_image
from app.db.repositories.stage_prediction_repo import get_stage_by_analysis
from app.db.repositories.risk_repo import get_risk_by_analysis

logger = logging.getLogger(__name__)


class ExplainabilityService:
    """
    Generate explainability artifacts for an analysis: saliency maps, attention maps,
    confidence histograms, cell detection overlays and a JSON explanation.

    Artifacts are saved using LocalFileStorage and URLs are returned so the frontend can fetch them.
    """

    def __init__(self, storage: Optional[LocalFileStorage] = None) -> None:
        self.storage = storage or LocalFileStorage()

    def _read_image_bytes(self, storage_path: str) -> Optional[bytes]:
        try:
            return self.storage.read_file(storage_path)
        except Exception:
            logger.exception("Failed to read image bytes from storage: %s", storage_path)
            return None

    def _save_image_bytes(self, img_bytes: bytes, filename: str) -> str:
        rel_path, _ = self.storage.save_file(img_bytes, filename=filename, subpath="explainability")
        return rel_path

    def _save_json(self, data: Dict[str, Any], filename: str) -> str:
        b = json.dumps(data, default=str).encode("utf-8")
        rel, _ = self.storage.save_file(b, filename=filename, subpath="explainability")
        return rel

    def generate_saliency_map(self, analysis_id: int) -> Optional[str]:
        """
        Create a simple gradient-based saliency map by computing Sobel gradients on the input image.
        This is a lightweight, model-agnostic saliency approximation (not a true gradient of the model).

        Returns relative storage path for the PNG image or None on failure.
        """
        analysis = get_analysis(analysis_id=analysis_id) if callable(get_analysis) else None
        if not analysis:
            logger.error("Analysis %s not found for saliency generation", analysis_id)
            return None

        # find image
        img_rec = get_image(analysis.image_id) if callable(get_image) else None
        if not img_rec:
            logger.error("Image record for analysis %s not found", analysis_id)
            return None

        img_bytes = None
        if getattr(img_rec, "storage_path", None):
            img_bytes = self._read_image_bytes(img_rec.storage_path)
        if not img_bytes:
            logger.error("Image bytes unavailable for %s", img_rec)
            return None

        # decode image
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            logger.error("OpenCV failed to decode image for analysis %s", analysis_id)
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Sobel gradients
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
        magnitude = np.clip((magnitude / magnitude.max()) * 255.0, 0, 255).astype(np.uint8)

        # color mapping
        heatmap = cv2.applyColorMap(magnitude, cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(img, 0.6, heatmap, 0.4, 0)

        is_success, buffer = cv2.imencode('.png', overlay)
        if not is_success:
            logger.error("Failed to encode saliency PNG for analysis %s", analysis_id)
            return None

        filename = f"saliency_{analysis_id}.png"
        rel = self._save_image_bytes(buffer.tobytes(), filename)
        return rel

    def generate_attention_map(self, analysis_id: int) -> Optional[str]:
        """
        Attention maps require a model with attention layers. As a fallback we compute
        a coarse attention approximation by performing a Gaussian blur and emphasizing
        high-frequency regions (as a proxy for attention).
        """
        analysis = get_analysis(analysis_id=analysis_id) if callable(get_analysis) else None
        if not analysis:
            logger.error("Analysis %s not found for attention generation", analysis_id)
            return None
        img_rec = get_image(analysis.image_id) if callable(get_image) else None
        if not img_rec or not getattr(img_rec, "storage_path", None):
            logger.error("Image for analysis %s not found", analysis_id)
            return None
        img_bytes = self._read_image_bytes(img_rec.storage_path)
        if not img_bytes:
            return None
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return None

        # compute Laplacian (edge) as proxy for attention
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        lap = np.absolute(lap)
        lap = (lap / lap.max() * 255).astype(np.uint8)
        heatmap = cv2.applyColorMap(lap, cv2.COLORMAP_INFERNO)
        overlay = cv2.addWeighted(img, 0.65, heatmap, 0.35, 0)

        is_success, buffer = cv2.imencode('.png', overlay)
        if not is_success:
            return None
        filename = f"attention_{analysis_id}.png"
        rel = self._save_image_bytes(buffer.tobytes(), filename)
        return rel

    def generate_confidence_histogram(self, analysis_id: int) -> Optional[str]:
        """
        Generate a histogram of class probabilities stored in the AnalysisResult record.
        """
        analysis = get_analysis(analysis_id=analysis_id) if callable(get_analysis) else None
        if not analysis:
            return None
        probs = getattr(analysis, "probabilities", None)
        if not probs:
            logger.warning("No probabilities found for analysis %s", analysis_id)
            return None
        # probs assumed to be a dict {label: prob}
        labels = list(probs.keys())
        values = [float(probs[k]) for k in labels]

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.bar(labels, values, color='C0')
        ax.set_ylim(0, 1)
        ax.set_ylabel('Probability')
        ax.set_title(f'Confidence Histogram - Analysis {analysis_id}')
        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        filename = f"confidence_hist_{analysis_id}.png"
        rel = self._save_image_bytes(buf.read(), filename)
        return rel

    def generate_cell_overlay(self, analysis_id: int) -> Optional[str]:
        """
        Overlay detected cell centers/bboxes on the original image. This relies on
        preprocessing outputs if available (e.g. cell detection results). As a fallback,
        we perform a simple blob detection to find bright circular regions.
        """
        analysis = get_analysis(analysis_id=analysis_id) if callable(get_analysis) else None
        if not analysis:
            return None
        img_rec = get_image(analysis.image_id) if callable(get_image) else None
        if not img_rec or not getattr(img_rec, "storage_path", None):
            return None
        img_bytes = self._read_image_bytes(img_rec.storage_path)
        if not img_bytes:
            return None
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # blob detector parameters
        params = cv2.SimpleBlobDetector_Params()
        params.filterByArea = True
        params.minArea = 30
        params.maxArea = 5000
        params.filterByCircularity = False
        detector = cv2.SimpleBlobDetector_create(params)
        keypoints = detector.detect(gray)

        overlay = img.copy()
        for kp in keypoints:
            x, y = int(kp.pt[0]), int(kp.pt[1])
            r = int(kp.size / 2)
            cv2.circle(overlay, (x, y), r, (0, 255, 0), 2)
        is_success, buffer = cv2.imencode('.png', overlay)
        if not is_success:
            return None
        filename = f"cell_overlay_{analysis_id}.png"
        rel = self._save_image_bytes(buffer.tobytes(), filename)
        return rel

    def generate_explanation_json(self, analysis_id: int) -> Optional[str]:
        """
        Create a structured JSON explanation including predictions, stage, risk and short reasoning.
        """
        analysis = get_analysis(analysis_id=analysis_id) if callable(get_analysis) else None
        if not analysis:
            return None
        probs = getattr(analysis, "probabilities", {}) or {}
        pred = getattr(analysis, "predicted_class", None)
        stage = get_stage_by_analysis(analysis_id) if callable(get_stage_by_analysis) else None
        risk = get_risk_by_analysis(analysis_id) if callable(get_risk_by_analysis) else None

        explanation = {
            "analysis_id": analysis_id,
            "predicted_class": pred,
            "probabilities": probs,
            "reasoning": [],
            "stage_prediction": {
                "stage": getattr(stage, "stage", None) if stage else None,
                "confidence": getattr(stage, "confidence", None) if stage else None,
            },
            "risk_analysis": {
                "risk_1y": getattr(risk, "risk_1y", None) if risk else None,
                "risk_3y": getattr(risk, "risk_3y", None) if risk else None,
                "risk_5y": getattr(risk, "risk_5y", None) if risk else None,
                "category": getattr(risk, "risk_category", None) if risk else None,
            },
        }

        # simple prediction reasoning: top-3 probs and relative margin
        try:
            items = sorted(probs.items(), key=lambda x: float(x[1]), reverse=True)
            top = items[:3]
            reasoning = []
            for label, p in top:
                reasoning.append({"label": label, "probability": float(p)})
            explanation["reasoning"] = reasoning
        except Exception:
            explanation["reasoning"] = []

        # save json
        filename = f"explanation_{analysis_id}.json"
        rel = self._save_json(explanation, filename)
        return rel

    def generate_all(self, analysis_id: int) -> Dict[str, Optional[str]]:
        """Generate all explainability artifacts and return storage-relative paths."""
        out = {
            "gradcam": None,
            "saliency": None,
            "attention": None,
            "confidence_histogram": None,
            "cell_overlay": None,
            "explanation_json": None,
        }
        try:
            # gradcam may already be stored in analysis.record; we still check/generate via existing pipeline
            # saliency
            out["saliency"] = self.generate_saliency_map(analysis_id)
            out["attention"] = self.generate_attention_map(analysis_id)
            out["confidence_histogram"] = self.generate_confidence_histogram(analysis_id)
            out["cell_overlay"] = self.generate_cell_overlay(analysis_id)
            out["explanation_json"] = self.generate_explanation_json(analysis_id)
        except Exception:
            logger.exception("Failed to generate explainability artifacts for %s", analysis_id)
        return out

    def get_urls(self, rel_paths: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
        urls = {}
        for k, v in rel_paths.items():
            if v:
                try:
                    urls[k] = self.storage.url_for(v)
                except Exception:
                    logger.exception("Failed to generate URL for %s (%s)", k, v)
                    urls[k] = None
            else:
                urls[k] = None
        return urls
