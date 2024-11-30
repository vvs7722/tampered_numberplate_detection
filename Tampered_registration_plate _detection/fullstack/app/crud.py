from sqlalchemy.orm import Session
from .models import Vehicle

def get_vehicle_by_number(db: Session, number: str):
    return db.query(Vehicle).filter(Vehicle.number == number.upper()).first()

def add_vehicle(db: Session, number: str, model: str):
    vehicle = Vehicle(number=number.upper(), model=model.upper())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle
