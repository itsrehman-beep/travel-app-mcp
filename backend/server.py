from fastmcp import FastMCP
from datetime import datetime, date, timedelta
from typing import List, Optional
from models import (
    Flight, FlightSearchRequest, FlightWithAvailability,
    Hotel, Room, HotelSearchRequest, RoomWithAvailability,
    Car, CarSearchRequest, CarWithAvailability,
    Booking, FlightBooking, HotelBooking, CarBooking,
    Passenger, Payment, CreateBookingRequest,
    User, City, Airport,
    PassengerInput, FlightBookingInput, HotelBookingInput, CarBookingInput, PaymentInput,
    BookingResponse, FlightBookingSummary, HotelBookingSummary, CarBookingSummary, PaymentSummary
)
from sheets_client import sheets_client

# Initialize FastMCP server
mcp = FastMCP("Travel Booking API")

# ===== SEARCH ENDPOINTS =====

@mcp.tool()
def search_flights(request: FlightSearchRequest) -> List[FlightWithAvailability]:
    """
    Search for available flights between origin and destination on a specific date.
    Returns flights with airport names and city names for easy understanding.
    
    Args:
        request: Flight search criteria with origin, destination, date, and seat class
    
    Returns:
        List of available flights with seat availability and human-readable location info
    """
    flights_data = sheets_client.read_sheet('Flight')
    flight_bookings = sheets_client.read_sheet('FlightBooking')
    
    results = []
    
    for flight_row in flights_data:
        if not flight_row.get('id'):
            continue
            
        if (flight_row.get('origin_code') == request.origin_code and 
            flight_row.get('destination_code') == request.destination_code):
            
            flight_date = datetime.fromisoformat(flight_row['departure_time']).date()
            if flight_date == request.departure_date:
                # Calculate available seats
                total_bookings = sum(
                    int(fb.get('passengers', 0)) 
                    for fb in flight_bookings 
                    if fb.get('flight_id') == flight_row['id'] and fb.get('seat_class') == request.seat_class
                )
                available_seats = 200 - total_bookings  # Assuming 200 seats per flight
                
                # Get origin airport and city info
                origin_airport = sheets_client.get_airport_by_code(flight_row['origin_code'])
                origin_city = sheets_client.get_city_by_id(origin_airport['city_id']) if origin_airport else None
                
                # Get destination airport and city info
                dest_airport = sheets_client.get_airport_by_code(flight_row['destination_code'])
                dest_city = sheets_client.get_city_by_id(dest_airport['city_id']) if dest_airport else None
                
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
def search_hotels(request: HotelSearchRequest) -> List[RoomWithAvailability]:
    """
    Search for available hotels and rooms in a city for specific dates.
    Returns rooms with full hotel details including address, rating, and city name.
    
    Args:
        request: Hotel search criteria with city_id, check-in/out dates, and guests
    
    Returns:
        List of available rooms with complete hotel information
    """
    hotels_data = sheets_client.read_sheet('Hotel')
    rooms_data = sheets_client.read_sheet('Room')
    hotel_bookings = sheets_client.read_sheet('HotelBooking')
    
    results = []
    
    for hotel in hotels_data:
        if hotel.get('city_id') != request.city_id:
            continue
        
        # Get city name for this hotel
        city = sheets_client.get_city_by_id(hotel.get('city_id', ''))
        city_name = city.get('name', '') if city else ''
        
        for room in rooms_data:
            if room.get('hotel_id') != hotel.get('id'):
                continue
            
            if int(room.get('capacity', 0)) < request.guests:
                continue
            
            # Check if room is available (no overlapping bookings)
            is_available = True
            for booking in hotel_bookings:
                if booking.get('room_id') != room.get('id'):
                    continue
                
                booking_checkin = datetime.fromisoformat(booking['check_in']).date()
                booking_checkout = datetime.fromisoformat(booking['check_out']).date()
                
                # Check for overlap
                if not (request.check_out <= booking_checkin or request.check_in >= booking_checkout):
                    is_available = False
                    break
            
            if is_available:
                # Convert to typed model with full hotel details
                room_model = RoomWithAvailability(
                    id=room['id'],
                    hotel_id=room['hotel_id'],
                    room_type=room['room_type'],
                    capacity=int(room['capacity']),
                    price_per_night=float(room['price_per_night']),
                    available=True,
                    hotel_name=hotel.get('name', ''),
                    hotel_address=hotel.get('address', ''),
                    hotel_rating=float(hotel.get('rating', 0)),
                    city_name=city_name
                )
                results.append(room_model)
    
    return results

@mcp.tool()
def search_cars(request: CarSearchRequest) -> List[CarWithAvailability]:
    """
    Search for available rental cars in a city for specific dates.
    Returns cars with city name for better context.
    
    Args:
        request: Car search criteria with city_id and pickup/dropoff dates
    
    Returns:
        List of available cars with city information
    """
    cars_data = sheets_client.read_sheet('Car')
    car_bookings = sheets_client.read_sheet('CarBooking')
    
    # Convert dates to datetime for overlap checking
    pickup_dt = datetime.combine(request.pickup_date, datetime.min.time())
    dropoff_dt = datetime.combine(request.dropoff_date, datetime.min.time())
    
    results = []
    
    for car in cars_data:
        if car.get('city_id') != request.city_id:
            continue
        
        # Get city name for this car
        city = sheets_client.get_city_by_id(car.get('city_id', ''))
        city_name = city.get('name', '') if city else ''
        
        # Check if car is available (no overlapping bookings)
        is_available = True
        for booking in car_bookings:
            if booking.get('car_id') != car.get('id'):
                continue
            
            booking_pickup = datetime.fromisoformat(booking['pickup_time'])
            booking_dropoff = datetime.fromisoformat(booking['dropoff_time'])
            
            # Check for overlap
            if not (dropoff_dt <= booking_pickup or pickup_dt >= booking_dropoff):
                is_available = False
                break
        
        if is_available:
            # Convert to typed model with city name
            car_model = CarWithAvailability(
                id=car['id'],
                city_id=car['city_id'],
                model=car['model'],
                brand=car['brand'],
                year=int(car['year']),
                seats=int(car['seats']),
                transmission=car['transmission'],
                fuel_type=car['fuel_type'],
                price_per_day=float(car['price_per_day']),
                available=True,
                city_name=city_name
            )
            results.append(car_model)
    
    return results

# ===== AIRPORT HELPER TOOLS =====

@mcp.tool()
def get_airports_by_city(city_id: str) -> List[Airport]:
    """
    Get all airports in a specific city.
    Helps users find airport codes when they know the city.
    
    Args:
        city_id: ID of the city (e.g., CY0001)
    
    Returns:
        List of airports in that city with codes and names
    """
    airports = sheets_client.read_sheet('Airport')
    city_airports = [
        Airport(
            code=a['code'],
            name=a['name'],
            city_id=a['city_id']
        )
        for a in airports if a.get('city_id') == city_id
    ]
    return city_airports

@mcp.tool()
def search_airports(search_term: str = "") -> List[Airport]:
    """
    Search airports by name, code, or list all if no search term provided.
    Helps users find airport codes and information.
    
    Args:
        search_term: Optional search string to filter airports (matches name or code)
    
    Returns:
        List of matching airports with codes and names
    """
    airports = sheets_client.read_sheet('Airport')
    
    if not search_term:
        # Return all airports
        return [
            Airport(
                code=a['code'],
                name=a['name'],
                city_id=a['city_id']
            )
            for a in airports if a.get('code')
        ]
    
    # Filter by search term (case-insensitive partial match on name or code)
    search_lower = search_term.lower()
    matching = [
        Airport(
            code=a['code'],
            name=a['name'],
            city_id=a['city_id']
        )
        for a in airports
        if (a.get('code') and (
            search_lower in a.get('code', '').lower() or
            search_lower in a.get('name', '').lower()
        ))
    ]
    return matching

# ===== BOOKING ENDPOINTS =====

@mcp.tool()
def create_booking(request: CreateBookingRequest) -> BookingResponse:
    """
    Create a unified booking for flights, hotels, and/or cars.
    
    Args:
        request: Booking request with user_id, optional flight/hotel/car bookings, passengers, and payment
    
    Returns:
        Created booking details with all generated IDs and confirmation
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
    
    # Generate booking ID and timestamp
    booking_id = sheets_client.generate_next_id('Booking', 'BK')
    now = datetime.now()
    
    # Create main booking
    booking_data = [
        booking_id,
        request.user_id,
        'confirmed',
        now.isoformat(),
        str(request.payment.amount)
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
    
    # Add passengers
    passenger_ids = []
    for passenger_input in request.passengers:
        passenger_id = sheets_client.generate_next_id('Passenger', 'PAX')
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
    
    # Create payment
    payment_id = sheets_client.generate_next_id('Payment', 'PMT')
    transaction_ref = f'TXN{now.strftime("%Y%m%d%H%M%S")}'
    payment_data = [
        payment_id,
        booking_id,
        request.payment.method,
        str(request.payment.amount),
        now.isoformat(),
        'success',
        transaction_ref
    ]
    sheets_client.append_row('Payment', payment_data)
    
    # Build and return response
    return BookingResponse(
        booking_id=booking_id,
        user_id=request.user_id,
        status='confirmed',
        booked_at=now,
        total_amount=request.payment.amount,
        flight_booking=flight_booking_summary,
        hotel_booking=hotel_booking_summary,
        car_booking=car_booking_summary,
        passenger_ids=passenger_ids,
        payment=PaymentSummary(
            id=payment_id,
            method=request.payment.method,
            amount=request.payment.amount,
            status='success',
            transaction_ref=transaction_ref,
            paid_at=now
        )
    )

# ===== DATA RETRIEVAL ENDPOINTS =====

@mcp.tool()
def get_cities() -> List[City]:
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
def get_airports() -> List[Airport]:
    """
    Get all available airports in the travel booking system.
    Use this to find airport codes needed for flight searches.
    
    Returns:
        List of all airports with codes, names, and city information
    """
    airports = sheets_client.read_sheet('Airport')
    return [
        Airport(
            code=a['code'],
            name=a['name'],
            city_id=a['city_id']
        )
        for a in airports if a.get('code')
    ]

@mcp.tool()
def get_user_bookings(user_id: str) -> List[dict]:
    """
    Get all bookings for a specific user.
    
    Args:
        user_id: UUID of the user
    
    Returns:
        List of user bookings with details
    """
    bookings = sheets_client.read_sheet('Booking')
    user_bookings = [b for b in bookings if b.get('user_id') == user_id]
    
    # Enhance with related data
    for booking in user_bookings:
        booking_id = booking.get('id')
        
        # Get flight bookings
        flight_bookings = sheets_client.read_sheet('FlightBooking')
        booking['flight_bookings'] = [fb for fb in flight_bookings if fb.get('booking_id') == booking_id]
        
        # Get hotel bookings
        hotel_bookings = sheets_client.read_sheet('HotelBooking')
        booking['hotel_bookings'] = [hb for hb in hotel_bookings if hb.get('booking_id') == booking_id]
        
        # Get car bookings
        car_bookings = sheets_client.read_sheet('CarBooking')
        booking['car_bookings'] = [cb for cb in car_bookings if cb.get('booking_id') == booking_id]
        
        # Get passengers
        passengers = sheets_client.read_sheet('Passenger')
        booking['passengers'] = [p for p in passengers if p.get('booking_id') == booking_id]
        
        # Get payment
        payments = sheets_client.read_sheet('Payment')
        booking['payment'] = next((p for p in payments if p.get('booking_id') == booking_id), None)
    
    return user_bookings

@mcp.tool()
def get_booking_details(booking_id: str) -> dict:
    """
    Get detailed information about a specific booking.
    
    Args:
        booking_id: UUID of the booking
    
    Returns:
        Detailed booking information
    """
    bookings = sheets_client.read_sheet('Booking')
    booking = next((b for b in bookings if b.get('id') == booking_id), None)
    
    if not booking:
        return {'error': 'Booking not found'}
    
    # Get flight bookings with flight details
    flight_bookings = sheets_client.read_sheet('FlightBooking')
    flights = sheets_client.read_sheet('Flight')
    booking['flight_bookings'] = []
    for fb in flight_bookings:
        if fb.get('booking_id') == booking_id:
            flight = next((f for f in flights if f.get('id') == fb.get('flight_id')), None)
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
            cb['car_details'] = car
            booking['car_bookings'].append(cb)
    
    # Get passengers
    passengers = sheets_client.read_sheet('Passenger')
    booking['passengers'] = [p for p in passengers if p.get('booking_id') == booking_id]
    
    # Get payment
    payments = sheets_client.read_sheet('Payment')
    booking['payment'] = next((p for p in payments if p.get('booking_id') == booking_id), None)
    
    return booking

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
        expose_headers=["mcp-session-id", "mcp-protocol-version"],
        max_age=86400,
    )
    
    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
