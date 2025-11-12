from fastmcp import FastMCP
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Dict, Any
import re
import jwt
from pydantic import BaseModel
from models import (
    Flight, FlightWithAvailability,
    Hotel, HotelWithCity, Room, RoomWithAvailability, RoomWithHotelInfo,
    Car, CarWithCity, CarWithAvailability,
    Booking, FlightBooking, HotelBooking, CarBooking,
    Passenger, Payment, CreateBookingRequest,
    User, City, Airport, AirportWithCity,
    PassengerInput, FlightBookingInput, HotelBookingInput, CarBookingInput, PaymentInput,
    BookingResponse, FlightBookingSummary, HotelBookingSummary, CarBookingSummary, PaymentSummary,
    BookFlightRequest, BookHotelRequest, BookCarRequest, PendingBookingResponse
)
from sheets_client import sheets_client
from auth import (
    RegisterRequest, LoginRequest, AuthResponse,
    extract_user_id_from_token,
    JWT_SECRET, JWT_ALGORITHM
)
from services.auth_sync import create_user_with_session, login_user_with_session

# Initialize FastMCP server
mcp = FastMCP("Travel Booking API")

# Response model for authentication tools
class AuthTokenResponse(BaseModel):
    """Response model for authentication tools with session token"""
    auth_token: str
    token_type: str
    user_id: str
    email: str
    expires_at: datetime

# ===== AUTHENTICATION TOOLS =====

@mcp.tool()
def register(email: str, password: str, first_name: Optional[str] = None, last_name: Optional[str] = None) -> AuthTokenResponse:
    """
    Register a new user account and receive an authentication token.
    Creates user in both PostgreSQL (for auth) and Google Sheets (for data).
    Also creates a session record in Google Sheets.
    
    Args:
        email: User's email address (must be unique)
        password: User's password (will be securely hashed)
        first_name: Optional first name
        last_name: Optional last name
    
    Returns:
        Authentication response with auth_token, user_id (format: USR0001), email, and expiration time
    
    Raises:
        ValueError: If email already exists or validation fails
    """
    try:
        request = RegisterRequest(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Use dual-write service to create user in both PostgreSQL and Google Sheets
        auth_response = create_user_with_session(request)
        
        # Decode token to get expiration time
        # JWT_SECRET is guaranteed to exist (checked in auth.py initialization)
        assert JWT_SECRET is not None, "JWT_SECRET must be set"
        payload = jwt.decode(auth_response.access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        expires_at = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        
        return AuthTokenResponse(
            auth_token=auth_response.access_token,
            token_type=auth_response.token_type,
            user_id=auth_response.user_id,
            email=auth_response.email,
            expires_at=expires_at
        )
    except Exception as e:
        raise ValueError(f"Registration failed: {str(e)}")

@mcp.tool()
def login(email: str, password: str) -> AuthTokenResponse:
    """
    Login with email and password to receive an authentication token.
    Creates a new session record in Google Sheets with each login.
    
    Args:
        email: User's email address
        password: User's password
    
    Returns:
        Authentication response with auth_token, user_id, email, and expiration time
    
    Raises:
        ValueError: If credentials are invalid or user is deactivated
    """
    try:
        request = LoginRequest(email=email, password=password)
        
        # Use dual-write service to authenticate and create session
        auth_response = login_user_with_session(request)
        
        # Decode token to get expiration time
        # JWT_SECRET is guaranteed to exist (checked in auth.py initialization)
        assert JWT_SECRET is not None, "JWT_SECRET must be set"
        payload = jwt.decode(auth_response.access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        expires_at = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        
        return AuthTokenResponse(
            auth_token=auth_response.access_token,
            token_type=auth_response.token_type,
            user_id=auth_response.user_id,
            email=auth_response.email,
            expires_at=expires_at
        )
    except Exception as e:
        raise ValueError(f"Login failed: {str(e)}")

# ===== BASIC LISTING TOOLS =====

@mcp.tool()
def list_cities() -> List[City]:
    """
    Get all available cities in the travel booking system.
    Returns city names, countries, and IDs for booking reference.
    
    Returns:
        List of all cities with their details
    """
    cities = sheets_client.read_sheet('City')
    return [
        City(
            id=c['id'],
            name=c['name'],
            country=c['country'],
            region=c['region']
        )
        for c in cities if c.get('id')
    ]

@mcp.tool()
def list_airports(city_id: Optional[str] = None) -> List[AirportWithCity]:
    """
    Returns airports, optionally filtered by city. If no city_id provided, returns all airports.
    
    Args:
        city_id: Optional ID of the city to filter by (e.g., CY0001)
    
    Returns:
        List of airports with codes, names, and city information
    """
    airports = sheets_client.read_sheet('Airport')
    cities = sheets_client.read_sheet('City')
    
    # Build city lookup
    cities_by_id = {c['id']: c for c in cities if c.get('id')}
    
    # Return all airports with city information
    result = []
    for a in airports:
        if not a.get('code'):
            continue
        
        # Apply city filter if provided
        if city_id and a.get('city_id') != city_id:
            continue
        
        city = cities_by_id.get(a.get('city_id', ''))
        city_name = city.get('name', '') if city else ''
        
        result.append(AirportWithCity(
            code=a['code'],
            name=a['name'],
            city_id=a['city_id'],
            city_name=city_name
        ))
    
    return result

@mcp.tool()
def list_flights(origin_code: Optional[str] = None, destination_code: Optional[str] = None, date: Optional[str] = None) -> List[FlightWithAvailability]:
    """
    Returns flights with availability and human-readable origin/destination information.
    All parameters are optional - if none provided, returns ALL flights.
    
    Args:
        origin_code: Optional origin airport code (e.g., 'JFK'). If omitted, returns flights from all origins.
        destination_code: Optional destination airport code (e.g., 'LAX'). If omitted, returns flights to all destinations.
        date: Optional flight date in YYYY-MM-DD format (e.g., '2025-11-15'). If omitted, returns flights on all dates.
    
    Returns:
        List of available flights with seat availability and location info
    """
    # Batch-load reference data once
    flights_data = sheets_client.read_sheet('Flight')
    flight_bookings = sheets_client.read_sheet('FlightBooking')
    airports_data = sheets_client.read_sheet('Airport')
    cities_data = sheets_client.read_sheet('City')
    
    # Build lookup dictionaries for O(1) access
    airports_by_code = {a['code']: a for a in airports_data if a.get('code')}
    cities_by_id = {c['id']: c for c in cities_data if c.get('id')}
    
    # Parse target date if provided
    target_date = None
    if date:
        try:
            target_date = datetime.fromisoformat(date).date()
        except ValueError:
            raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got: {date}")
    
    results = []
    
    for flight_row in flights_data:
        if not flight_row.get('id'):
            continue
            
        # Apply filters only if provided
        if origin_code and flight_row.get('origin_code') != origin_code:
            continue
        if destination_code and flight_row.get('destination_code') != destination_code:
            continue
            
        flight_date = datetime.fromisoformat(flight_row['departure_time']).date()
        if target_date and flight_date != target_date:
            continue
        # Calculate available seats (assuming all bookings are economy/business, 100 seats each)
        economy_bookings = sum(
            int(fb.get('passengers', 0)) 
            for fb in flight_bookings 
            if fb.get('flight_id') == flight_row['id'] and fb.get('seat_class') == 'economy'
        )
        business_bookings = sum(
            int(fb.get('passengers', 0)) 
            for fb in flight_bookings 
            if fb.get('flight_id') == flight_row['id'] and fb.get('seat_class') == 'business'
        )
        # Simplified availability: 100 economy + 100 business = 200 total
        available_seats = 200 - (economy_bookings + business_bookings)
        
        # Lookup airport and city info
        origin_airport = airports_by_code.get(flight_row['origin_code'])
        origin_city = cities_by_id.get(origin_airport['city_id']) if origin_airport else None
        
        dest_airport = airports_by_code.get(flight_row['destination_code'])
        dest_city = cities_by_id.get(dest_airport['city_id']) if dest_airport else None
        
        # Convert to typed model with human-readable names
        # Parse datetimes and add UTC timezone for RFC3339 compliance
        departure_dt = datetime.fromisoformat(flight_row['departure_time'])
        if departure_dt.tzinfo is None:
            departure_dt = departure_dt.replace(tzinfo=timezone.utc)
        
        arrival_dt = datetime.fromisoformat(flight_row['arrival_time'])
        if arrival_dt.tzinfo is None:
            arrival_dt = arrival_dt.replace(tzinfo=timezone.utc)
        
        flight = FlightWithAvailability(
            id=flight_row['id'],
            flight_number=flight_row['flight_number'],
            airline_name=flight_row['airline_name'],
            aircraft_model=flight_row['aircraft_model'],
            origin_code=flight_row['origin_code'],
            destination_code=flight_row['destination_code'],
            departure_time=departure_dt,
            arrival_time=arrival_dt,
            base_price=float(flight_row['base_price']),
            available_seats=available_seats,
            origin_airport_name=origin_airport.get('name', '') if origin_airport else '',
            origin_city_name=origin_city.get('name', '') if origin_city else '',
            destination_airport_name=dest_airport.get('name', '') if dest_airport else '',
            destination_city_name=dest_city.get('name', '') if dest_city else ''
        )
        results.append(flight)
    
    return results

@mcp.tool()
def list_hotels(city: Optional[str] = None) -> List[HotelWithCity]:
    """
    Returns hotels with full details. Optional city filter by name or ID.
    If no city provided, returns ALL hotels.
    
    Args:
        city: Optional city name (e.g., 'New York') or city ID (e.g., 'CY0001'). If omitted, returns all hotels.
    
    Returns:
        List of hotels with complete information including city name
    """
    hotels_data = sheets_client.read_sheet('Hotel')
    cities_data = sheets_client.read_sheet('City')
    
    # Build city lookups
    cities_by_id = {c['id']: c for c in cities_data if c.get('id')}
    cities_by_name = {c['name'].lower(): c for c in cities_data if c.get('name')}
    
    # Determine if filter is by ID or name
    target_city_id = None
    if city:
        # Normalize input: strip whitespace and uppercase for ID check
        city_normalized = city.strip().upper()
        # Check if it matches city ID pattern: CY followed by digits (e.g., CY0001)
        if re.match(r'^CY\d+$', city_normalized):
            # It's a city ID
            target_city_id = city_normalized
        else:
            # It's a city name - do case-insensitive lookup
            city_obj = cities_by_name.get(city.lower().strip())
            if city_obj:
                target_city_id = city_obj['id']
    
    results = []
    for hotel in hotels_data:
        if not hotel.get('id'):
            continue
            
        # Apply city filter if provided
        if target_city_id and hotel.get('city_id') != target_city_id:
            continue
        
        city_obj = cities_by_id.get(hotel.get('city_id', ''))
        city_name = city_obj.get('name', '') if city_obj else ''
        
        results.append(HotelWithCity(
            id=hotel['id'],
            name=hotel['name'],
            city_id=hotel['city_id'],
            city_name=city_name,
            address=hotel.get('address', ''),
            rating=float(hotel.get('rating', 0)),
            contact_number=hotel.get('contact_number', ''),
            description=hotel.get('description', '')
        ))
    
    return results

@mcp.tool()
def list_rooms(hotel_id: str) -> List[RoomWithHotelInfo]:
    """
    Returns rooms for a specific hotel with availability information and hotel details.
    
    Args:
        hotel_id: ID of the hotel (e.g., HTL0001)
    
    Returns:
        List of rooms with availability status and hotel information
    """
    rooms_data = sheets_client.read_sheet('Room')
    hotels_data = sheets_client.read_sheet('Hotel')
    hotel_bookings = sheets_client.read_sheet('HotelBooking')
    cities_data = sheets_client.read_sheet('City')
    
    # Get hotel details
    hotel = next((h for h in hotels_data if h.get('id') == hotel_id), None)
    if not hotel:
        return []
    
    # Get city name
    cities_by_id = {c['id']: c for c in cities_data if c.get('id')}
    city = cities_by_id.get(hotel.get('city_id', ''))
    city_name = city.get('name', '') if city else ''
    
    results = []
    current_date = datetime.now().date()
    
    for room in rooms_data:
        if room.get('hotel_id') == hotel_id and room.get('id'):
            # Check if room has any future bookings (general availability indicator)
            has_future_bookings = any(
                hb.get('room_id') == room['id'] and 
                datetime.fromisoformat(hb['check_out']).date() >= current_date
                for hb in hotel_bookings if hb.get('room_id')
            )
            
            results.append(RoomWithHotelInfo(
                id=room['id'],
                hotel_id=room['hotel_id'],
                hotel_name=hotel.get('name', ''),
                hotel_address=hotel.get('address', ''),
                hotel_rating=float(hotel.get('rating', 0)),
                city_name=city_name,
                room_type=room['room_type'],
                capacity=int(room['capacity']),
                price_per_night=float(room['price_per_night']),
                is_available=not has_future_bookings  # True if no future bookings
            ))
    
    return results

@mcp.tool()
def list_cars(city: Optional[str] = None) -> List[CarWithCity]:
    """
    Returns available cars with full location information. Optional city filter by name or ID.
    If no city provided, returns ALL cars.
    
    Args:
        city: Optional city name (e.g., 'Tokyo') or city ID (e.g., 'CY0001'). If omitted, returns all cars.
    
    Returns:
        List of cars with complete details including city name
    """
    cars_data = sheets_client.read_sheet('Car')
    cities_data = sheets_client.read_sheet('City')
    
    # Build city lookups
    cities_by_id = {c['id']: c for c in cities_data if c.get('id')}
    cities_by_name = {c['name'].lower(): c for c in cities_data if c.get('name')}
    
    # Determine if filter is by ID or name
    target_city_id = None
    if city:
        # Normalize input: strip whitespace and uppercase for ID check
        city_normalized = city.strip().upper()
        # Check if it matches city ID pattern: CY followed by digits (e.g., CY0001)
        if re.match(r'^CY\d+$', city_normalized):
            # It's a city ID
            target_city_id = city_normalized
        else:
            # It's a city name - do case-insensitive lookup
            city_obj = cities_by_name.get(city.lower().strip())
            if city_obj:
                target_city_id = city_obj['id']
    
    results = []
    for car in cars_data:
        if not car.get('id'):
            continue
            
        # Apply city filter if provided
        if target_city_id and car.get('city_id') != target_city_id:
            continue
        
        city_obj = cities_by_id.get(car.get('city_id', ''))
        city_name = city_obj.get('name', '') if city_obj else ''
        
        results.append(CarWithCity(
            id=car['id'],
            city_id=car['city_id'],
            city_name=city_name,
            model=car['model'],
            brand=car['brand'],
            year=int(car['year']),
            seats=int(car['seats']),
            transmission=car['transmission'],
            fuel_type=car['fuel_type'],
            price_per_day=float(car['price_per_day'])
        ))
    
    return results

# ===== BOOKING MANAGEMENT TOOLS =====

@mcp.tool()
def book_flight(auth_token: str, request: BookFlightRequest) -> PendingBookingResponse:
    """
    Books a flight with passenger details. Returns booking_id with 'pending' status.
    Use process_payment() to complete payment and confirm the booking.
    
    Args:
        auth_token: JWT authentication token from login
        request: Flight booking request with flight_id, seat_class, and passengers
    
    Returns:
        Pending booking with booking_id and total amount to be paid
    """
    # Authenticate user and get user_id
    user_id = require_user(auth_token)
    
    # Validation: Must have at least 1 passenger
    if len(request.passengers) == 0:
        raise ValueError("At least one passenger is required for flight booking")
    
    # Load flight data to calculate price
    flights_data = sheets_client.read_sheet('Flight')
    flight = next((f for f in flights_data if f.get('id') == request.flight_id), None)
    if not flight:
        raise ValueError(f"Flight {request.flight_id} not found")
    
    # Calculate total price
    total_price = float(flight.get('base_price', 0)) * len(request.passengers)
    
    # Generate booking ID and timestamp
    booking_id = sheets_client.generate_next_id('Booking', 'BK')
    now = datetime.now(timezone.utc)
    
    # Create main booking with 'pending' status
    booking_data = [
        booking_id,
        user_id,
        'pending',
        now.isoformat(),
        str(total_price)
    ]
    sheets_client.append_row('Booking', booking_data)
    
    # Create flight booking
    flight_booking_id = sheets_client.generate_next_id('FlightBooking', 'FBK')
    flight_booking_data = [
        flight_booking_id,
        booking_id,
        request.flight_id,
        request.seat_class,
        str(len(request.passengers))
    ]
    sheets_client.append_row('FlightBooking', flight_booking_data)
    
    # Add passengers
    for passenger_input in request.passengers:
        passenger_id = sheets_client.generate_next_id('Passenger', 'PA', width=5)
        passenger_data = [
            passenger_id,
            booking_id,
            passenger_input.first_name,
            passenger_input.last_name,
            passenger_input.gender,
            passenger_input.dob.isoformat(),
            passenger_input.passport_no
        ]
        sheets_client.append_row('Passenger', passenger_data)
    
    return PendingBookingResponse(
        booking_id=booking_id,
        status="pending",
        total_amount=total_price
    )

@mcp.tool()
def book_hotel(auth_token: str, request: BookHotelRequest) -> PendingBookingResponse:
    """
    Books a hotel room. Returns booking_id with 'pending' status.
    Use process_payment() to complete payment and confirm the booking.
    
    Args:
        auth_token: JWT authentication token from login
        request: Hotel booking request with room_id, check-in/out dates, and guests
    
    Returns:
        Pending booking with booking_id and total amount to be paid
    """
    # Authenticate user and get user_id
    user_id = require_user(auth_token)
    
    # Validation: Check-in must be before check-out
    if request.check_in >= request.check_out:
        raise ValueError("Check-in date must be before check-out date")
    
    # Load room data to calculate price
    rooms_data = sheets_client.read_sheet('Room')
    room = next((r for r in rooms_data if r.get('id') == request.room_id), None)
    if not room:
        raise ValueError(f"Room {request.room_id} not found")
    
    # Calculate total price
    nights = (request.check_out - request.check_in).days
    total_price = float(room.get('price_per_night', 0)) * nights
    
    # Generate booking ID and timestamp
    booking_id = sheets_client.generate_next_id('Booking', 'BK')
    now = datetime.now(timezone.utc)
    
    # Create main booking with 'pending' status
    booking_data = [
        booking_id,
        user_id,
        'pending',
        now.isoformat(),
        str(total_price)
    ]
    sheets_client.append_row('Booking', booking_data)
    
    # Create hotel booking
    hotel_booking_id = sheets_client.generate_next_id('HotelBooking', 'HBK')
    hotel_booking_data = [
        hotel_booking_id,
        booking_id,
        request.room_id,
        request.check_in.isoformat(),
        request.check_out.isoformat(),
        str(request.guests)
    ]
    sheets_client.append_row('HotelBooking', hotel_booking_data)
    
    return PendingBookingResponse(
        booking_id=booking_id,
        status="pending",
        total_amount=total_price
    )

@mcp.tool()
def book_car(auth_token: str, request: BookCarRequest) -> PendingBookingResponse:
    """
    Books a rental car. Returns booking_id with 'pending' status.
    Use process_payment() to complete payment and confirm the booking.
    
    Args:
        auth_token: JWT authentication token from login
        request: Car booking request with car_id, pickup/dropoff times and locations
    
    Returns:
        Pending booking with booking_id and total amount to be paid
    """
    # Authenticate user and get user_id
    user_id = require_user(auth_token)
    
    # Validation: Pickup must be before dropoff
    if request.pickup_time >= request.dropoff_time:
        raise ValueError("Pickup time must be before dropoff time")
    
    # Load car data to calculate price
    cars_data = sheets_client.read_sheet('Car')
    car = next((c for c in cars_data if c.get('id') == request.car_id), None)
    if not car:
        raise ValueError(f"Car {request.car_id} not found")
    
    # Calculate total price
    days = (request.dropoff_time - request.pickup_time).days
    total_price = float(car.get('price_per_day', 0)) * max(1, days)
    
    # Generate booking ID and timestamp
    booking_id = sheets_client.generate_next_id('Booking', 'BK')
    now = datetime.now(timezone.utc)
    
    # Create main booking with 'pending' status
    booking_data = [
        booking_id,
        user_id,
        'pending',
        now.isoformat(),
        str(total_price)
    ]
    sheets_client.append_row('Booking', booking_data)
    
    # Create car booking
    car_booking_id = sheets_client.generate_next_id('CarBooking', 'CBK')
    car_booking_data = [
        car_booking_id,
        booking_id,
        request.car_id,
        request.pickup_time.isoformat(),
        request.dropoff_time.isoformat(),
        request.pickup_location,
        request.dropoff_location
    ]
    sheets_client.append_row('CarBooking', car_booking_data)
    
    return PendingBookingResponse(
        booking_id=booking_id,
        status="pending",
        total_amount=total_price
    )

@mcp.tool()
def get_booking(booking_id: str) -> Dict[str, Any]:
    """
    Returns full details of a booking including all sub-bookings, passengers, and payment.
    
    Args:
        booking_id: ID of the booking (e.g., BK0001)
    
    Returns:
        Complete booking information with all related entities
    """
    bookings = sheets_client.read_sheet('Booking')
    booking = next((b for b in bookings if b.get('id') == booking_id), None)
    
    if not booking:
        return {'error': f'Booking {booking_id} not found'}
    
    # Get flight bookings with flight details
    flight_bookings = sheets_client.read_sheet('FlightBooking')
    flights = sheets_client.read_sheet('Flight')
    airports = sheets_client.read_sheet('Airport')
    cities = sheets_client.read_sheet('City')
    
    airports_by_code = {a['code']: a for a in airports if a.get('code')}
    cities_by_id = {c['id']: c for c in cities if c.get('id')}
    
    booking['flight_bookings'] = []
    for fb in flight_bookings:
        if fb.get('booking_id') == booking_id:
            flight = next((f for f in flights if f.get('id') == fb.get('flight_id')), None)
            if flight:
                # Add human-readable airport/city names
                origin_airport = airports_by_code.get(flight.get('origin_code'))
                origin_city = cities_by_id.get(origin_airport['city_id']) if origin_airport else None
                dest_airport = airports_by_code.get(flight.get('destination_code'))
                dest_city = cities_by_id.get(dest_airport['city_id']) if dest_airport else None
                
                flight['origin_airport_name'] = origin_airport.get('name', '') if origin_airport else ''
                flight['origin_city_name'] = origin_city.get('name', '') if origin_city else ''
                flight['destination_airport_name'] = dest_airport.get('name', '') if dest_airport else ''
                flight['destination_city_name'] = dest_city.get('name', '') if dest_city else ''
                
                fb['flight_details'] = flight
            booking['flight_bookings'].append(fb)
    
    # Get hotel bookings with room and hotel details
    hotel_bookings = sheets_client.read_sheet('HotelBooking')
    rooms = sheets_client.read_sheet('Room')
    hotels = sheets_client.read_sheet('Hotel')
    
    booking['hotel_bookings'] = []
    for hb in hotel_bookings:
        if hb.get('booking_id') == booking_id:
            room = next((r for r in rooms if r.get('id') == hb.get('room_id')), None)
            if room:
                hotel = next((h for h in hotels if h.get('id') == room.get('hotel_id')), None)
                if hotel:
                    city = cities_by_id.get(hotel.get('city_id', ''))
                    hotel['city_name'] = city.get('name', '') if city else ''
                hb['room_details'] = room
                hb['hotel_details'] = hotel
            booking['hotel_bookings'].append(hb)
    
    # Get car bookings with car details
    car_bookings = sheets_client.read_sheet('CarBooking')
    cars = sheets_client.read_sheet('Car')
    
    booking['car_bookings'] = []
    for cb in car_bookings:
        if cb.get('booking_id') == booking_id:
            car = next((c for c in cars if c.get('id') == cb.get('car_id')), None)
            if car:
                city = cities_by_id.get(car.get('city_id', ''))
                car['city_name'] = city.get('name', '') if city else ''
                cb['car_details'] = car
            booking['car_bookings'].append(cb)
    
    # Get passengers
    passengers = sheets_client.read_sheet('Passenger')
    booking['passengers'] = [p for p in passengers if p.get('booking_id') == booking_id]
    
    # Get payment
    payments = sheets_client.read_sheet('Payment')
    booking['payment'] = next((p for p in payments if p.get('booking_id') == booking_id), None)
    
    return booking

@mcp.tool()
def cancel_booking(booking_id: str) -> Dict[str, Any]:
    """
    Cancels a booking and associated sub-bookings, updates payment status to refunded.
    
    Args:
        booking_id: ID of the booking to cancel (e.g., BK0001)
    
    Returns:
        Cancellation confirmation with updated status
    """
    # Find the booking
    result = sheets_client.find_row_by_id('Booking', booking_id)
    if not result:
        return {'error': f'Booking {booking_id} not found'}
    
    row_index, booking = result
    
    # Check if already cancelled
    if booking.get('status') == 'cancelled':
        return {'error': f'Booking {booking_id} is already cancelled'}
    
    # Update booking status to cancelled
    booking_data = [
        booking['id'],
        booking['user_id'],
        'cancelled',  # Update status
        booking['booked_at'],
        booking['total_price']
    ]
    # Fix: row_index from find_row_by_id is absolute sheet row, subtract 1 for update_row
    sheets_client.update_row('Booking', row_index - 1, booking_data)
    
    # Update payment status to refunded
    payments = sheets_client.read_sheet('Payment')
    for idx, payment in enumerate(payments):
        if payment.get('booking_id') == booking_id:
            payment_data = [
                payment['id'],
                payment['booking_id'],
                payment['method'],
                payment['amount'],
                payment['paid_at'],
                'refunded',  # Update status
                payment.get('transaction_ref', '')
            ]
            # Fix: idx is 0-based, +1 for update_row's expected 1-based data row index
            sheets_client.update_row('Payment', idx + 1, payment_data)
            break
    
    return {
        'success': True,
        'booking_id': booking_id,
        'status': 'cancelled',
        'message': f'Booking {booking_id} has been cancelled and payment refunded'
    }

@mcp.tool()
def update_passenger(passenger_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates passenger information.
    
    Args:
        passenger_id: ID of the passenger (e.g., PA00001)
        updates: Dictionary of fields to update (first_name, last_name, gender, dob, passport_no)
    
    Returns:
        Updated passenger information
    """
    # Find the passenger
    result = sheets_client.find_row_by_id('Passenger', passenger_id)
    if not result:
        return {'error': f'Passenger {passenger_id} not found'}
    
    row_index, passenger = result
    
    # Update allowed fields
    allowed_fields = {'first_name', 'last_name', 'gender', 'dob', 'passport_no'}
    for field, value in updates.items():
        if field in allowed_fields:
            passenger[field] = value
    
    # Write updated passenger data
    passenger_data = [
        passenger['id'],
        passenger['booking_id'],
        passenger.get('first_name', ''),
        passenger.get('last_name', ''),
        passenger.get('gender', ''),
        passenger.get('dob', ''),
        passenger.get('passport_no', '')
    ]
    # Fix: row_index from find_row_by_id is absolute sheet row, subtract 1 for update_row
    sheets_client.update_row('Passenger', row_index - 1, passenger_data)
    
    return {
        'success': True,
        'passenger_id': passenger_id,
        'updated_fields': list(updates.keys()),
        'passenger': passenger
    }

@mcp.tool()
def process_payment(auth_token: str, booking_id: str, payment: PaymentInput) -> Dict[str, Any]:
    """
    Processes payment for a pending booking. Changes booking status from 'pending' to 'confirmed'.
    
    Args:
        auth_token: JWT authentication token from login
        booking_id: ID of the booking to pay for (e.g., BK0001)
        payment: Payment details including method and amount
    
    Returns:
        Payment confirmation with transaction details
    """
    # Authenticate user
    user_id = require_user(auth_token)
    # Find the booking
    result = sheets_client.find_row_by_id('Booking', booking_id)
    if not result:
        return {'error': f'Booking {booking_id} not found'}
    
    row_index, booking = result
    
    # Check if booking is pending
    if booking.get('status') == 'cancelled':
        return {'error': f'Booking {booking_id} is cancelled and cannot be paid for'}
    
    if booking.get('status') == 'confirmed':
        return {'error': f'Booking {booking_id} is already confirmed and paid'}
    
    # Verify payment amount matches booking total
    booking_total = float(booking.get('total_price', 0))
    if abs(payment.amount - booking_total) > 0.01:  # Allow for floating point rounding
        return {'error': f'Payment amount ${payment.amount} does not match booking total ${booking_total}'}
    
    # Create payment record
    payment_id = sheets_client.generate_next_id('Payment', 'PMT')
    now = datetime.now()
    transaction_ref = f'TXN{now.strftime("%Y%m%d%H%M%S")}{booking_id[-4:]}'
    
    payment_data = [
        payment_id,
        booking_id,
        payment.method,
        str(payment.amount),
        now.isoformat(),
        'success',
        transaction_ref
    ]
    sheets_client.append_row('Payment', payment_data)
    
    # Update booking status to confirmed
    booking_data = [
        booking['id'],
        booking['user_id'],
        'confirmed',
        booking['booked_at'],
        booking['total_price']
    ]
    sheets_client.update_row('Booking', row_index - 1, booking_data)
    
    return {
        'success': True,
        'payment_id': payment_id,
        'booking_id': booking_id,
        'amount': payment.amount,
        'status': 'success',
        'transaction_ref': transaction_ref,
        'paid_at': now.isoformat(),
        'booking_status': 'confirmed'
    }

# Helper function for authentication in MCP tools
def require_user(auth_token: str) -> str:
    """
    Validate auth token and return user_id.
    Raises exception if token is invalid or missing.
    """
    from auth import extract_user_id_from_token
    
    if not auth_token:
        raise Exception('Authentication required. Please provide auth_token.')
    
    user_id = extract_user_id_from_token(auth_token)
    if not user_id:
        raise Exception('Invalid or expired authentication token.')
    
    return user_id

# Run the server
if __name__ == "__main__":
    import uvicorn
    import json
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.middleware.cors import CORSMiddleware
    from starlette.routing import Route
    from auth import (
        init_db, 
        register_user, 
        login_user, 
        get_user_from_token,
        RegisterRequest, 
        LoginRequest
    )
    
    # Initialize database tables
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
    
    # Authentication route handlers
    async def handle_register(request: Request):
        """Register a new user"""
        try:
            body = await request.json()
            reg_request = RegisterRequest(**body)
            response = register_user(reg_request)
            return JSONResponse(content=response.model_dump(), status_code=201)
        except Exception as e:
            return JSONResponse(content={'error': str(e)}, status_code=400)
    
    async def handle_login(request: Request):
        """Login an existing user"""
        try:
            body = await request.json()
            login_request = LoginRequest(**body)
            response = login_user(login_request)
            return JSONResponse(content=response.model_dump())
        except Exception as e:
            return JSONResponse(content={'error': str(e)}, status_code=401)
    
    async def handle_get_me(request: Request):
        """Get current user information from auth token"""
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JSONResponse(
                content={'error': 'Missing or invalid Authorization header'}, 
                status_code=401
            )
        
        token = auth_header.split(' ')[1]
        try:
            user_info = get_user_from_token(token)
            if not user_info:
                return JSONResponse(content={'error': 'Invalid or expired token'}, status_code=401)
            return JSONResponse(content=user_info.model_dump())
        except Exception as e:
            return JSONResponse(content={'error': str(e)}, status_code=401)
    
    # Get the HTTP app
    app = mcp.http_app()
    
    # Add authentication routes
    auth_routes = [
        Route('/auth/register', handle_register, methods=['POST']),
        Route('/auth/login', handle_login, methods=['POST']),
        Route('/auth/me', handle_get_me, methods=['GET']),
    ]
    
    # Mount auth routes to the app
    for route in auth_routes:
        app.router.routes.insert(0, route)
    
    # Add CORS middleware to allow frontend requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id"],  # Expose custom MCP session header
    )
    
    # Run server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
