from fastmcp import FastMCP
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import re
from models import (
    Flight, FlightWithAvailability,
    Hotel, HotelWithCity, Room, RoomWithAvailability, RoomWithHotelInfo,
    Car, CarWithCity, CarWithAvailability,
    Booking, FlightBooking, HotelBooking, CarBooking,
    Passenger, Payment, CreateBookingRequest,
    User, City, Airport, AirportWithCity,
    PassengerInput, FlightBookingInput, HotelBookingInput, CarBookingInput, PaymentInput,
    BookingResponse, FlightBookingSummary, HotelBookingSummary, CarBookingSummary, PaymentSummary
)
from sheets_client import sheets_client

# Initialize FastMCP server
mcp = FastMCP("Travel Booking API")

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
def list_airports(city_id: str) -> List[AirportWithCity]:
    """
    Returns airports in a specific city with airport and city names for easy understanding.
    
    Args:
        city_id: ID of the city (e.g., CY0001)
    
    Returns:
        List of airports with codes, names, and city information
    """
    airports = sheets_client.read_sheet('Airport')
    cities = sheets_client.read_sheet('City')
    
    # Build city lookup
    cities_by_id = {c['id']: c for c in cities if c.get('id')}
    city = cities_by_id.get(city_id)
    city_name = city.get('name', '') if city else ''
    
    # Filter airports for this city and return typed models
    result = []
    for a in airports:
        if a.get('city_id') == city_id and a.get('code'):
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
        flight = FlightWithAvailability(
            id=flight_row['id'],
            flight_number=flight_row['flight_number'],
            airline_name=flight_row['airline_name'],
            aircraft_model=flight_row['aircraft_model'],
            origin_code=flight_row['origin_code'],
            destination_code=flight_row['destination_code'],
            departure_time=datetime.fromisoformat(flight_row['departure_time']),
            arrival_time=datetime.fromisoformat(flight_row['arrival_time']),
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
def create_booking(request: CreateBookingRequest) -> BookingResponse:
    """
    Creates a single master booking with optional flight, hotel, and car bookings.
    Booking starts in 'pending' status. Use process_payment() to complete payment and confirm booking.
    
    Args:
        request: Booking request with user_id, optional flight/hotel/car bookings, and passengers
    
    Returns:
        Created booking details with booking_id. Status is 'pending' until payment is processed.
    """
    # Validation: Ensure at least one booking type is provided
    if not any([request.flight_booking, request.hotel_booking, request.car_booking]):
        raise ValueError("At least one of flight_booking, hotel_booking, or car_booking must be provided")
    
    # Validation: Flight booking passenger checks
    if request.flight_booking:
        if request.flight_booking.passengers < 1:
            raise ValueError("Flight booking must have at least 1 passenger")
        if len(request.passengers) == 0:
            raise ValueError("Passengers list cannot be empty when booking a flight")
        if request.flight_booking.passengers != len(request.passengers):
            raise ValueError(f"Flight booking declares {request.flight_booking.passengers} passengers but {len(request.passengers)} passenger records provided")
    
    # Validation: Date range checks
    if request.hotel_booking and request.hotel_booking.check_in >= request.hotel_booking.check_out:
        raise ValueError("Hotel check-in date must be before check-out date")
    
    if request.car_booking and request.car_booking.pickup_time >= request.car_booking.dropoff_time:
        raise ValueError("Car pickup time must be before dropoff time")
    
    # Calculate total price from individual bookings
    flights_data = sheets_client.read_sheet('Flight')
    rooms_data = sheets_client.read_sheet('Room')
    cars_data = sheets_client.read_sheet('Car')
    
    total_price = 0.0
    if request.flight_booking:
        flight = next((f for f in flights_data if f.get('id') == request.flight_booking.flight_id), None)
        if flight:
            total_price += float(flight.get('base_price', 0)) * request.flight_booking.passengers
    
    if request.hotel_booking:
        room = next((r for r in rooms_data if r.get('id') == request.hotel_booking.room_id), None)
        if room:
            nights = (request.hotel_booking.check_out - request.hotel_booking.check_in).days
            total_price += float(room.get('price_per_night', 0)) * nights
    
    if request.car_booking:
        car = next((c for c in cars_data if c.get('id') == request.car_booking.car_id), None)
        if car:
            days = (request.car_booking.dropoff_time - request.car_booking.pickup_time).days
            total_price += float(car.get('price_per_day', 0)) * max(1, days)
    
    # Generate booking ID and timestamp
    booking_id = sheets_client.generate_next_id('Booking', 'BK')
    now = datetime.now()
    
    # Create main booking with 'pending' status
    booking_data = [
        booking_id,
        request.user_id,
        'pending',
        now.isoformat(),
        str(total_price)
    ]
    sheets_client.append_row('Booking', booking_data)
    
    # Create flight booking if provided
    flight_booking_summary = None
    if request.flight_booking:
        flight_booking_id = sheets_client.generate_next_id('FlightBooking', 'FBK')
        flight_booking_data = [
            flight_booking_id,
            booking_id,
            request.flight_booking.flight_id,
            request.flight_booking.seat_class,
            str(request.flight_booking.passengers)
        ]
        sheets_client.append_row('FlightBooking', flight_booking_data)
        
        flight_booking_summary = FlightBookingSummary(
            id=flight_booking_id,
            flight_id=request.flight_booking.flight_id,
            seat_class=request.flight_booking.seat_class,
            passengers=request.flight_booking.passengers
        )
    
    # Create hotel booking if provided
    hotel_booking_summary = None
    if request.hotel_booking:
        hotel_booking_id = sheets_client.generate_next_id('HotelBooking', 'HBK')
        hotel_booking_data = [
            hotel_booking_id,
            booking_id,
            request.hotel_booking.room_id,
            request.hotel_booking.check_in.isoformat(),
            request.hotel_booking.check_out.isoformat(),
            str(request.hotel_booking.guests)
        ]
        sheets_client.append_row('HotelBooking', hotel_booking_data)
        
        hotel_booking_summary = HotelBookingSummary(
            id=hotel_booking_id,
            room_id=request.hotel_booking.room_id,
            check_in=request.hotel_booking.check_in,
            check_out=request.hotel_booking.check_out,
            guests=request.hotel_booking.guests
        )
    
    # Create car booking if provided
    car_booking_summary = None
    if request.car_booking:
        car_booking_id = sheets_client.generate_next_id('CarBooking', 'CBK')
        car_booking_data = [
            car_booking_id,
            booking_id,
            request.car_booking.car_id,
            request.car_booking.pickup_time.isoformat(),
            request.car_booking.dropoff_time.isoformat(),
            request.car_booking.pickup_location,
            request.car_booking.dropoff_location
        ]
        sheets_client.append_row('CarBooking', car_booking_data)
        
        car_booking_summary = CarBookingSummary(
            id=car_booking_id,
            car_id=request.car_booking.car_id,
            pickup_time=request.car_booking.pickup_time,
            dropoff_time=request.car_booking.dropoff_time,
            pickup_location=request.car_booking.pickup_location,
            dropoff_location=request.car_booking.dropoff_location
        )
    
    # Add passengers (with 5-digit PA prefix)
    passenger_ids = []
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
        passenger_ids.append(passenger_id)
    
    # Build and return response - payment must be processed separately
    return BookingResponse(
        booking_id=booking_id,
        user_id=request.user_id,
        status='pending',
        booked_at=now,
        total_amount=total_price,
        flight_booking=flight_booking_summary,
        hotel_booking=hotel_booking_summary,
        car_booking=car_booking_summary,
        passenger_ids=passenger_ids,
        payment=None  # Payment not yet processed
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
def process_payment(booking_id: str, payment: PaymentInput) -> Dict[str, Any]:
    """
    Processes payment for a pending booking. Changes booking status from 'pending' to 'confirmed'.
    
    Args:
        booking_id: ID of the booking to pay for (e.g., BK0001)
        payment: Payment details including method and amount
    
    Returns:
        Payment confirmation with transaction details
    """
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

# Run the server
if __name__ == "__main__":
    import uvicorn
    from starlette.middleware.cors import CORSMiddleware
    
    # Get the HTTP app
    app = mcp.http_app()
    
    # Add CORS middleware to allow frontend requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Run server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
