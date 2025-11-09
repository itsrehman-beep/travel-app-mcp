from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime, date
from uuid import UUID

# ===== USERS & AUTH =====
class User(BaseModel):
    id: str
    email: EmailStr
    password: str
    full_name: str
    role: Literal["user", "admin"] = "user"
    created_at: datetime
    last_login: Optional[datetime] = None

class Session(BaseModel):
    id: str
    user_id: str
    auth_token: str
    created_at: datetime
    expires_at: datetime

# ===== CORE ENTITIES =====
class City(BaseModel):
    id: str
    name: str
    country: str
    region: str

class Airport(BaseModel):
    code: str
    name: str
    city_id: str

# ===== FLIGHT DATA =====
class Flight(BaseModel):
    id: str
    flight_number: str
    airline_name: str
    aircraft_model: str
    origin_code: str
    destination_code: str
    departure_time: datetime
    arrival_time: datetime
    base_price: float

class FlightBooking(BaseModel):
    id: str
    booking_id: str
    flight_id: str
    seat_class: Literal["economy", "business"]
    passengers: int

# ===== HOTELS =====
class Hotel(BaseModel):
    id: str
    name: str
    city_id: str
    address: str
    rating: float
    contact_number: str
    description: str

class Room(BaseModel):
    id: str
    hotel_id: str
    room_type: Literal["single", "double", "suite"]
    capacity: int
    price_per_night: float

class HotelBooking(BaseModel):
    id: str
    booking_id: str
    room_id: str
    check_in: date
    check_out: date
    guests: int

# ===== CARS =====
class Car(BaseModel):
    id: str
    city_id: str
    model: str
    brand: str
    year: int
    seats: int
    transmission: Literal["manual", "automatic"]
    fuel_type: str
    price_per_day: float

class CarBooking(BaseModel):
    id: str
    booking_id: str
    car_id: str
    pickup_time: datetime
    dropoff_time: datetime
    pickup_location: str
    dropoff_location: str

# ===== BOOKINGS =====
class Booking(BaseModel):
    id: str
    user_id: str
    status: Literal["pending", "confirmed", "cancelled"] = "pending"
    booked_at: datetime
    total_price: float

class Passenger(BaseModel):
    id: str
    booking_id: str
    first_name: str
    last_name: str
    gender: str
    dob: date
    passport_no: str

class Payment(BaseModel):
    id: str
    booking_id: str
    method: str
    amount: float
    paid_at: datetime
    status: Literal["success", "failed", "refunded"]
    transaction_ref: str

# ===== REQUEST/RESPONSE MODELS =====
class FlightSearchRequest(BaseModel):
    origin_code: str
    destination_code: str
    departure_date: date
    seat_class: Literal["economy", "business"] = "economy"

class HotelSearchRequest(BaseModel):
    city_id: str
    check_in: date
    check_out: date
    guests: int

class CarSearchRequest(BaseModel):
    city_id: str
    pickup_date: date
    dropoff_date: date

class CreateBookingRequest(BaseModel):
    user_id: str
    flight_booking: Optional[FlightBooking] = None
    hotel_booking: Optional[HotelBooking] = None
    car_booking: Optional[CarBooking] = None
    passengers: list[Passenger]
    payment: Payment

class FlightWithAvailability(Flight):
    available_seats: int

class RoomWithAvailability(Room):
    available: bool
    hotel_name: str

class CarWithAvailability(Car):
    available: bool
