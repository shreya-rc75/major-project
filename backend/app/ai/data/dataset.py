import torch
from torch.utils.data import Dataset
from PIL import Image
from typing import List, Tuple, Optional
from pathlib import Path
import numpy as np


class PapSmearDataset(Dataset):
    def __init__(self, records: List[Tuple[str, int]], transforms=None, return_path: bool = False):
        """
        records: list of tuples (image_path, label_int)
        transforms: albumentations transform
        return_path: if True, dataset.__getitem__ returns (tensor, label, image_path)
        """
        self.records = records
        self.transforms = transforms
        self.return_path = return_path

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx: int):
        path, label = self.records[idx]
        img = Image.open(path).convert("RGB")
        img_np = np.array(img)
        if self.transforms:
            augmented = self.transforms(image=img_np)
            img_t = augmented["image"]
        else:
            # fallback: convert to CHW float32 tensor normalized
            img_t = torch.from_numpy(img_np.astype("float32")).permute(2, 0, 1) / 255.0
        if self.return_path:
            return img_t, int(label), path
        return img_t, int(label)
