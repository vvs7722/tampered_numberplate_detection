import cv2
import numpy as np
import easyocr
from sqlalchemy.orm import Session
from models import Vehicle
import requests


def process_image(image_path: str) -> str:
    """Extracts number plate text from an image."""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Noise reduction and edge detection
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(bfilter, 30, 200)

    # Find contours
    keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(
        keypoints[0], key=cv2.contourArea, reverse=True
    )  # Find largest contours
    location = None

    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:  # Look for a rectangle
            location = approx
            break

    if not location:
        return "Number plate not found"

    # Mask the region of interest
    mask = np.zeros(gray.shape, np.uint8)
    cv2.drawContours(mask, [location], 0, 255, -1)
    new_image = cv2.bitwise_and(img, img, mask=mask)
    (x, y) = np.where(mask == 255)
    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    cropped_image = gray[x1:x2 + 1, y1:y2 + 1]

    # Use EasyOCR to extract text
    reader = easyocr.Reader(["en"])
    result = reader.readtext(cropped_image)
    text = "".join([r[1] for r in result]).replace(" ", "").replace("_", "").replace(".", "")

    return text.upper()


def get_vehicle_by_number(db: Session, number: str):
    """Fetch vehicle information by number plate."""
    return db.query(Vehicle).filter(Vehicle.number == number).first()


def analyze_with_custom_vision(image_path: str, endpoint: str, prediction_key: str) -> str:
    """Send the image to Azure Custom Vision and get the prediction."""
    headers = {
        "Prediction-Key": prediction_key,
        "Content-Type": "application/octet-stream",
    }

    with open(image_path, "rb") as image_file:
        response = requests.post(endpoint, headers=headers, data=image_file)

    if response.status_code == 200:
        results = response.json()
        predictions = results.get("predictions", [])
        if predictions:
            top_prediction = max(predictions, key=lambda x: x["probability"])
            return top_prediction["tagName"]
        return "No prediction available"
    else:
        return f"Error: {response.status_code} - {response.text}"


def validate_number_plate_with_vision(
    db: Session, number: str, model: str, image_path: str, endpoint: str, prediction_key: str
) -> str:
    """Validate the number plate and verify with Azure Custom Vision."""
    vehicle = get_vehicle_by_number(db, number)
    if vehicle:
        # Validate with database
        if vehicle.model == model.upper():
            # Use Azure Custom Vision for further validation
            predicted_model = analyze_with_custom_vision(image_path, endpoint, prediction_key)
            if predicted_model.upper() == model.upper():
                return "This is an original number and vehicle"
            return f"Tampered: Predicted model is {predicted_model}, but expected {model}"
        return "This is a tampered number"
    return "Data not available"
