from fastapi import FastAPI, File, UploadFile, Form, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from utils import process_image, get_vehicle_by_number
import requests

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_number_plate_with_azure(image_path: str, number_plate: str, model: str):
    """
    Validate the vehicle using Azure Custom Vision API.
    """
    # Azure Custom Vision API details
    endpoint_image = "YOUR_AZURE_CUSTOM_VISION_ENDPOINT"
    prediction_key = "YOUR_AZURE_CUSTOM_VISION_PREDICTION_KEY"

    # Set headers
    headers_image = {
        "Prediction-Key": prediction_key,
        "Content-Type": "application/octet-stream",
    }

    # Read the image file as bytes
    image_data = open(image_path, "rb").read()

    # Make the prediction request for image file
    response_image = requests.post(endpoint_image, headers=headers_image, data=image_data)

    # Handle the response
    if response_image.status_code == 200:
        results_image = response_image.json()
        # Process the results as needed
        highest_prediction_image = max(
            results_image['predictions'], key=lambda x: x['probability']
        )
        print(
            f"The highest probability prediction is: {highest_prediction_image['tagName']} "
            f"with probability {highest_prediction_image['probability']:.2%}"
        )

        # Check if prediction matches the database model
        if highest_prediction_image['tagName'].lower() == model.lower():
            return "This is an Original Vehicle"
        else:
            return "This is a Tampered/Fake Number Plate"
    else:
        print(f"Prediction failed with status code {response_image.status_code}")
        print(response_image.text)
        return "Azure Custom Vision Validation Failed"


@app.post("/validate/")
async def validate_plate(
    file: UploadFile = File(...),
    model: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Validate the number plate image and match it with the vehicle model.
    """
    # Save the uploaded file
    file_location = f"static/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(file.file.read())

    # Extract the number plate text
    number_plate = process_image(file_location)

    if not number_plate:
        return {
            "error": "Failed to detect number plate. Please try again with a clearer image."
        }

    # Retrieve vehicle information from the database
    vehicle = get_vehicle_by_number(db, number_plate)

    if not vehicle:
        return {"number_plate": number_plate, "result": "Data not available for this number plate."}

    # Check if the extracted number plate matches the provided model
    if vehicle.model.lower() == model.lower():
        # Perform Azure Custom Vision API validation
        azure_result = validate_number_plate_with_azure(file_location, number_plate, model)

        return {
            "number_plate": number_plate,
            "model": model,
            "database_validation": "Match found in the database",
            "custom_vision_validation": azure_result,
        }

    return {
        "number_plate": number_plate,
        "model": model,
        "result": "Tampered: Vehicle model does not match the database record.",
    }
