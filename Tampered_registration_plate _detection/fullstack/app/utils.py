import cv2
import numpy as np
import easyocr
from sqlalchemy.orm import Session
from .crud import get_vehicle_by_number


def process_image(image_path: str) -> str:
    """Process the uploaded image to extract the number plate text."""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17)  # Reduce noise
    edged = cv2.Canny(bfilter, 30, 200)  # Edge detection

    keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(keypoints[0], key=cv2.contourArea, reverse=True)[:10]
    location = None

    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            location = approx
            break

    if location is None:
        return "UNDETECTED"

    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [location], 0, 255, -1)
    new_image = cv2.bitwise_and(img, img, mask=mask)

    (x, y) = np.where(mask == 255)
    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    cropped_image = gray[x1:x2 + 1, y1:y2 + 1]

    reader = easyocr.Reader(['en'])
    result = reader.readtext(cropped_image)
    text = "".join([i[1] for i in result]).upper()
    return text.replace(" ", "").replace("_", "").replace(".", "")


def validate_number_plate(db: Session, number: str, model: str) -> str:
    """Validate the number plate against the database."""
    vehicle = get_vehicle_by_number(db, number)
    if vehicle:
        if vehicle.model == model.upper():
            return "This is an original number"
        return "This is a tampered number"
    return "Data not available"
