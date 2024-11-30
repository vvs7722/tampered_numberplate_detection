from fastapi import FastAPI, UploadFile, Form, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal, init_db
from .utils import process_image, validate_number_plate
from .crud import add_vehicle

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    init_db()

@app.post("/validate/")
async def validate_plate(file: UploadFile, model: str = Form(...), db: Session = Depends(get_db)):
    file_location = f"static/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    number = process_image(file_location)
    result = validate_number_plate(db, number, model)
    return {"number_plate": number, "result": result}

@app.post("/add/")
async def add_vehicle_data(number: str = Form(...), model: str = Form(...), db: Session = Depends(get_db)):
    vehicle = add_vehicle(db, number, model)
    return {"message": "Vehicle added successfully", "vehicle": {"number": vehicle.number, "model": vehicle.model}}
