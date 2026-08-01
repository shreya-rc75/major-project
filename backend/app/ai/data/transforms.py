from albumentations import Compose, Resize, Normalize, HorizontalFlip, VerticalFlip, Rotate, RandomBrightnessContrast, ShiftScaleRotate
from albumentations.pytorch import ToTensorV2
from typing import Tuple


def train_transforms(target_size: Tuple[int, int] = (300, 300)):
    return Compose([
        Resize(target_size[0], target_size[1]),
        HorizontalFlip(p=0.5),
        VerticalFlip(p=0.1),
        Rotate(limit=15, p=0.3),
        ShiftScaleRotate(shift_limit=0.0625, scale_limit=0.1, rotate_limit=0, p=0.2),
        RandomBrightnessContrast(p=0.3),
        Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2()
    ])


def val_transforms(target_size: Tuple[int, int] = (300, 300)):
    return Compose([
        Resize(target_size[0], target_size[1]),
        Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2()
    ])


def infer_transforms(target_size: Tuple[int, int] = (300, 300)):
    return val_transforms(target_size)
