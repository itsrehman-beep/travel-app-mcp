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

class AirportWithCity(BaseModel):
    """Airport with enriched city information"""
    code: str
    name: str
    city_id: str
    city_name: str

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

class HotelWithCity(BaseModel):
    """Hotel with enriched city information"""
    id: str
    name: str
    city_id: str
    city_name: str
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

class RoomWithHotelInfo(BaseModel):
    """Room with complete hotel information and availability"""
    id: str
    hotel_id: str
    hotel_name: str
    hotel_address: str
    hotel_rating: float
    city_name: str
    room_type: Literal["single", "double", "suite"]
    capacity: int
    price_per_night: float
    is_available: bool = True  # General availability indicator

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

class CarWithCity(BaseModel):
    """Car with enriched city information"""
    id: str
    city_id: str
    city_name: str
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
    """Search for flights. Dates must be in YYYY-MM-DD format (e.g., 2025-12-28)."""
    origin_code: str = Field(description="3-letter airport code (e.g., JFK, LAX). Use search_airports to find codes.")
    destination_code: str = Field(description="3-letter airport code (e.g., CDG, NRT). Use search_airports to find codes.")
    departure_date: date = Field(description="Departure date in YYYY-MM-DD format (e.g., 2025-12-28)")
    seat_class: Literal["economy", "business"] = Field(default="economy", description="Seat class: economy or business")

class HotelSearchRequest(BaseModel):
    """Search for hotel rooms. Dates must be in YYYY-MM-DD format (e.g., 2025-12-28)."""
    city_id: str = Field(description="City ID (e.g., CY0001). Use get_cities to find city IDs.")
    check_in: date = Field(description="Check-in date in YYYY-MM-DD format (e.g., 2025-12-28)")
    check_out: date = Field(description="Check-out date in YYYY-MM-DD format (e.g., 2025-12-30)")
    guests: int = Field(description="Number of guests", gt=0)

class CarSearchRequest(BaseModel):
    """Search for rental cars. Dates must be in YYYY-MM-DD format (e.g., 2025-12-28)."""
    city_id: str = Field(description="City ID (e.g., CY0001). Use get_cities to find city IDs.")
    pickup_date: date = Field(description="Pickup date in YYYY-MM-DD format (e.g., 2025-12-28)")
    dropoff_date: date = Field(description="Drop-off date in YYYY-MM-DD format (e.g., 2025-12-30)")

# Input models for creating records (without auto-generated IDs)
class PassengerInput(BaseModel):
    """Passenger details for flight booking."""
    first_name: str = Field(description="Passenger first name")
    last_name: str = Field(description="Passenger last name")
    gender: str = Field(description="Passenger gender (male/female/other)")
    dob: date = Field(description="Date of birth in YYYY-MM-DD format (e.g., 1990-05-15)")
    passport_no: str = Field(description="Passport number")

class FlightBookingInput(BaseModel):
    """Flight booking information."""
    flight_id: str = Field(description="Flight ID from search results")
    seat_class: Literal["economy", "business"] = Field(default="economy", description="Seat class: economy or business")
    passengers: int = Field(description="Number of passengers (must match passenger list length)", gt=0)

class HotelBookingInput(BaseModel):
    """Hotel booking information. Dates must be in YYYY-MM-DD format."""
    room_id: str = Field(description="Room ID from search results")
    check_in: date = Field(description="Check-in date in YYYY-MM-DD format (e.g., 2025-12-28)")
    check_out: date = Field(description="Check-out date in YYYY-MM-DD format (e.g., 2025-12-30)")
    guests: int = Field(description="Number of guests", gt=0)

class CarBookingInput(BaseModel):
    """Car rental booking information. Datetimes must be in ISO 8601 format."""
    car_id: str = Field(description="Car ID from search results")
    pickup_time: datetime = Field(description="Pickup datetime in ISO format (e.g., 2025-12-28T10:00:00)")
    dropoff_time: datetime = Field(description="Drop-off datetime in ISO format (e.g., 2025-12-30T10:00:00)")
    pickup_location: str = Field(description="Pickup location address")
    dropoff_location: str = Field(description="Drop-off location address")

class PaymentInput(BaseModel):
    """Payment information for booking."""
    method: str = Field(default="card", description="Payment method (card/wallet/upi)")
    amount: float = Field(description="Total amount to be paid", gt=0)

class CreateBookingRequest(BaseModel):
    user_id: str
    flight_booking: Optional[FlightBookingInput] = None
    hotel_booking: Optional[HotelBookingInput] = None
    car_booking: Optional[CarBookingInput] = None
    passengers: list[PassengerInput] = Field(default_factory=list)

class BookFlightRequest(BaseModel):
    """Request to book a flight with passenger details."""
    flight_id: str = Field(description="Flight ID from search results")
    seat_class: Literal["economy", "business"] = Field(default="economy", description="Seat class")
    passengers: list[PassengerInput] = Field(description="List of passenger details (at least 1)")

class BookHotelRequest(BaseModel):
    """Request to book a hotel room."""
    room_id: str = Field(description="Room ID from search results")
    check_in: date = Field(description="Check-in date (YYYY-MM-DD)")
    check_out: date = Field(description="Check-out date (YYYY-MM-DD)")
    guests: int = Field(description="Number of guests", gt=0)

class BookCarRequest(BaseModel):
    """Request to book a rental car."""
    car_id: str = Field(description="Car ID from search results")
    pickup_time: datetime = Field(description="Pickup datetime (ISO 8601)")
    dropoff_time: datetime = Field(description="Drop-off datetime (ISO 8601)")
    pickup_location: str = Field(description="Pickup location address")
    dropoff_location: str = Field(description="Drop-off location address")

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

class PendingBookingResponse(BaseModel):
    """Simplified response for newly created pending bookings."""
    booking_id: str = Field(description="Unique booking identifier")
    status: Literal["pending"] = Field(default="pending", description="Booking status (always 'pending' for new bookings)")
    total_amount: float = Field(description="Total booking amount to be paid")
    message: str = Field(default="Booking created successfully. Use process_payment() to complete payment and confirm booking.", description="Next steps information")

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
    payment: Optional[PaymentSummary] = None