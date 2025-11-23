import cv2
import numpy as np
from fastapi import UploadFile

def check_blur(image_bytes: bytes, threshold=100.0) -> bool:
    """
    Returns True if image is blurry.
    Uses Laplacian variance method.
    """
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    # Compute Laplacian
    laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
    
    # If variance is low, edges are soft -> Blurry
    return laplacian_var < threshold