from fastmcp import FastMCP
from datetime import datetime, date, timedelta
from typing import List, Optional
from models import (
    Flight, FlightSearchRequest, FlightWithAvailability,
    Hotel, Room, HotelSearchRequest, RoomWithAvailability,
    Car, CarSearchRequest, CarWithAvailability,
    Booking, FlightBooking, HotelBooking, CarBooking,
    Passenger, Payment, CreateBookingRequest,
    User, City, Airport
)
from sheets_client import sheets_client

# Initialize FastMCP server
mcp = FastMCP("Travel Booking API")

# ===== SEARCH ENDPOINTS =====

@mcp.tool()
def search_flights(
    origin_code: str,
    destination_code: str,
    departure_date: str,
    seat_class: str = "economy"
) -> List[dict]:
    """
    Search for available flights between origin and destination on a specific date.
    
    Args:
        origin_code: Airport code for origin (e.g., 'JFK')
        destination_code: Airport code for destination (e.g., 'LAX')
        departure_date: Departure date in YYYY-MM-DD format
        seat_class: Seat class (economy or business)
    
    Returns:
        List of available flights with seat availability
    """
    flights_data = sheets_client.read_sheet('Flight')
    flight_bookings = sheets_client.read_sheet('FlightBooking')
    
    target_date = datetime.fromisoformat(departure_date).date()
    results = []
    
    for flight_row in flights_data:
        if not flight_row.get('id'):
            continue
            
        if (flight_row.get('origin_code') == origin_code and 
            flight_row.get('destination_code') == destination_code):
            
            flight_date = datetime.fromisoformat(flight_row['departure_time']).date()
            if flight_date == target_date:
                # Calculate available seats
                total_bookings = sum(
                    int(fb.get('passengers', 0)) 
                    for fb in flight_bookings 
                    if fb.get('flight_id') == flight_row['id'] and fb.get('seat_class') == seat_class
                )
                available_seats = 200 - total_bookings  # Assuming 200 seats per flight
                
                results.append({
                    **flight_row,
                    'available_seats': available_seats
                })
    
    return results

@mcp.tool()
def search_hotels(
    city_id: str,
    check_in: str,
    check_out: str,
    guests: int
) -> List[dict]:
    """
    Search for available hotels and rooms in a city for specific dates.
    
    Args:
        city_id: UUID of the city
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of guests
    
    Returns:
        List of available rooms with hotel details
    """
    hotels_data = sheets_client.read_sheet('Hotel')
    rooms_data = sheets_client.read_sheet('Room')
    hotel_bookings = sheets_client.read_sheet('HotelBooking')
    
    check_in_date = datetime.fromisoformat(check_in).date()
    check_out_date = datetime.fromisoformat(check_out).date()
    
    results = []
    
    for hotel in hotels_data:
        if hotel.get('city_id') != city_id:
            continue
        
        for room in rooms_data:
            if room.get('hotel_id') != hotel.get('id'):
                continue
            
            if int(room.get('capacity', 0)) < guests:
                continue
            
            # Check if room is available (no overlapping bookings)
            is_available = True
            for booking in hotel_bookings:
                if booking.get('room_id') != room.get('id'):
                    continue
                
                booking_checkin = datetime.fromisoformat(booking['check_in']).date()
                booking_checkout = datetime.fromisoformat(booking['check_out']).date()
                
                # Check for overlap
                if not (check_out_date <= booking_checkin or check_in_date >= booking_checkout):
                    is_available = False
                    break
            
            if is_available:
                results.append({
                    **room,
                    'hotel_name': hotel.get('name'),
                    'hotel_rating': hotel.get('rating'),
                    'hotel_address': hotel.get('address'),
                    'available': True
                })
    
    return results

@mcp.tool()
def search_cars(
    city_id: str,
    pickup_date: str,
    dropoff_date: str
) -> List[dict]:
    """
    Search for available rental cars in a city for specific dates.
    
    Args:
        city_id: UUID of the city
        pickup_date: Pickup date in YYYY-MM-DD format
        dropoff_date: Dropoff date in YYYY-MM-DD format
    
    Returns:
        List of available cars
    """
    cars_data = sheets_client.read_sheet('Car')
    car_bookings = sheets_client.read_sheet('CarBooking')
    
    pickup_dt = datetime.fromisoformat(pickup_date)
    dropoff_dt = datetime.fromisoformat(dropoff_date)
    
    results = []
    
    for car in cars_data:
        if car.get('city_id') != city_id:
            continue
        
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
            results.append({
                **car,
                'available': True
            })
    
    return results

# ===== BOOKING ENDPOINTS =====

@mcp.tool()
def create_booking(
    user_id: str,
    flight_id: Optional[str] = None,
    flight_seat_class: Optional[str] = None,
    flight_passengers: Optional[int] = None,
    room_id: Optional[str] = None,
    check_in: Optional[str] = None,
    check_out: Optional[str] = None,
    hotel_guests: Optional[int] = None,
    car_id: Optional[str] = None,
    pickup_time: Optional[str] = None,
    dropoff_time: Optional[str] = None,
    pickup_location: Optional[str] = None,
    dropoff_location: Optional[str] = None,
    passengers_json: str = "[]",
    payment_method: str = "card",
    total_amount: float = 0.0
) -> dict:
    """
    Create a unified booking for flights, hotels, and/or cars.
    
    Args:
        user_id: UUID of the user making the booking
        flight_id: Optional flight UUID
        flight_seat_class: Optional seat class (economy/business)
        flight_passengers: Optional number of passengers
        room_id: Optional room UUID
        check_in: Optional check-in date (YYYY-MM-DD)
        check_out: Optional check-out date (YYYY-MM-DD)
        hotel_guests: Optional number of hotel guests
        car_id: Optional car UUID
        pickup_time: Optional pickup datetime (ISO format)
        dropoff_time: Optional dropoff datetime (ISO format)
        pickup_location: Optional pickup location
        dropoff_location: Optional dropoff location
        passengers_json: JSON array of passenger details
        payment_method: Payment method (card, wallet, upi)
        total_amount: Total booking amount
    
    Returns:
        Created booking details with confirmation
    """
    import json
    
    booking_id = sheets_client.generate_next_id('Booking', 'BK')
    now = datetime.now().isoformat()
    
    # Create main booking
    booking_data = [
        booking_id,
        user_id,
        'confirmed',
        now,
        str(total_amount)
    ]
    sheets_client.append_row('Booking', booking_data)
    
    # Create flight booking if provided
    if flight_id:
        flight_booking_id = sheets_client.generate_next_id('FlightBooking', 'FBK')
        flight_booking_data = [
            flight_booking_id,
            booking_id,
            flight_id,
            flight_seat_class or 'economy',
            str(flight_passengers or 1)
        ]
        sheets_client.append_row('FlightBooking', flight_booking_data)
    
    # Create hotel booking if provided
    if room_id:
        hotel_booking_id = sheets_client.generate_next_id('HotelBooking', 'HBK')
        hotel_booking_data = [
            hotel_booking_id,
            booking_id,
            room_id,
            check_in,
            check_out,
            str(hotel_guests or 1)
        ]
        sheets_client.append_row('HotelBooking', hotel_booking_data)
    
    # Create car booking if provided
    if car_id:
        car_booking_id = sheets_client.generate_next_id('CarBooking', 'CBK')
        car_booking_data = [
            car_booking_id,
            booking_id,
            car_id,
            pickup_time,
            dropoff_time,
            pickup_location or '',
            dropoff_location or ''
        ]
        sheets_client.append_row('CarBooking', car_booking_data)
    
    # Add passengers
    try:
        passengers = json.loads(passengers_json)
        for passenger in passengers:
            passenger_id = sheets_client.generate_next_id('Passenger', 'PAX')
            passenger_data = [
                passenger_id,
                booking_id,
                passenger.get('first_name', ''),
                passenger.get('last_name', ''),
                passenger.get('gender', ''),
                passenger.get('dob', ''),
                passenger.get('passport_no', '')
            ]
            sheets_client.append_row('Passenger', passenger_data)
    except:
        pass
    
    # Create payment
    payment_id = sheets_client.generate_next_id('Payment', 'PMT')
    transaction_ref = f'TXN{datetime.now().strftime("%Y%m%d%H%M%S")}'
    payment_data = [
        payment_id,
        booking_id,
        payment_method,
        str(total_amount),
        now,
        'success',
        transaction_ref
    ]
    sheets_client.append_row('Payment', payment_data)
    
    return {
        'booking_id': booking_id,
        'status': 'confirmed',
        'payment_status': 'success',
        'payment_id': payment_id,
        'total_amount': total_amount
    }

# ===== DATA RETRIEVAL ENDPOINTS =====

@mcp.tool()
def get_cities() -> List[dict]:
    """Get all available cities"""
    return sheets_client.read_sheet('City')

@mcp.tool()
def get_airports() -> List[dict]:
    """Get all available airports"""
    return sheets_client.read_sheet('Airport')

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
