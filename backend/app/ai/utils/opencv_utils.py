# small opencv utils used by ai modules
import cv2
import numpy as np


def ensure_rgb_and_resize(image_path: str, size=(300,300)) -> np.ndarray:
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not read image")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (size[1], size[0]), interpolation=cv2.INTER_LINEAR)
    return img
