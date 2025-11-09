from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from datetime import datetime, date
from uuid import UUID

# Custom validators for datetime formats
class DateTimeFormat(BaseModel):
    """
    Helper model for datetime validation.
    All datetime fields accept ISO 8601 format: YYYY-MM-DDTHH:MM:SS
    All date fields accept format: YYYY-MM-DD
    Examples:
        - datetime: "2025-11-09T14:30:00"
        - date: "2025-11-09"
    """
    pass

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

# Input models for creating records (without auto-generated IDs)
class PassengerInput(BaseModel):
    first_name: str
    last_name: str
    gender: str
    dob: date
    passport_no: str

class FlightBookingInput(BaseModel):
    flight_id: str
    seat_class: Literal["economy", "business"] = "economy"
    passengers: int

class HotelBookingInput(BaseModel):
    room_id: str
    check_in: date
    check_out: date
    guests: int

class CarBookingInput(BaseModel):
    car_id: str
    pickup_time: datetime
    dropoff_time: datetime
    pickup_location: str
    dropoff_location: str

class PaymentInput(BaseModel):
    method: str = "card"
    amount: float

class CreateBookingRequest(BaseModel):
    user_id: str
    flight_booking: Optional[FlightBookingInput] = None
    hotel_booking: Optional[HotelBookingInput] = None
    car_booking: Optional[CarBookingInput] = None
    passengers: list[PassengerInput] = Field(default_factory=list)
    payment: PaymentInput

class FlightWithAvailability(Flight):
    """Flight search result with availability and human-readable location names"""
    available_seats: int
    origin_airport_name: str = Field(description="Name of departure airport")
    origin_city_name: str = Field(description="Name of departure city")
    destination_airport_name: str = Field(description="Name of arrival airport")
    destination_city_name: str = Field(description="Name of arrival city")

class RoomWithAvailability(Room):
    """Hotel room search result with availability and full hotel details"""
    available: bool
    hotel_name: str = Field(description="Name of the hotel")
    hotel_address: str = Field(description="Full address of the hotel")
    hotel_rating: float = Field(description="Hotel rating (0-5 stars)")
    city_name: str = Field(description="Name of the city where hotel is located")

class CarWithAvailability(Car):
    """Car rental search result with availability and location details"""
    available: bool
    city_name: str = Field(description="Name of the city where car is available")

# ===== BOOKING RESPONSE MODELS =====
class FlightBookingSummary(BaseModel):
    id: str
    flight_id: str
    seat_class: Literal["economy", "business"]
    passengers: int

class HotelBookingSummary(BaseModel):
    id: str
    room_id: str
    check_in: date
    check_out: date
    guests: int

class CarBookingSummary(BaseModel):
    id: str
    car_id: str
    pickup_time: datetime
    dropoff_time: datetime
    pickup_location: str
    dropoff_location: str

class PaymentSummary(BaseModel):
    id: str
    method: str
    amount: float
    status: Literal["success", "failed", "refunded"]
    transaction_ref: str
    paid_at: datetime

class BookingResponse(BaseModel):
    booking_id: str
    user_id: str
    status: Literal["pending", "confirmed", "cancelled"]
    booked_at: datetime
    total_amount: float
    flight_booking: Optional[FlightBookingSummary] = None
    hotel_booking: Optional[HotelBookingSummary] = None
    car_booking: Optional[CarBookingSummary] = None
    passenger_ids: list[str] = Field(default_factory=list)
    payment: PaymentSummary
