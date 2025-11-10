import sys
sys.path.insert(0, 'backend')

from sheets_client import sheets_client
from datetime import datetime, timedelta, timezone

def populate_all_sheets():
    """Populate all Google Sheets tables with sample data using standardized ID format"""
    
    print('Starting to populate all sheets with standardized IDs...\n')
    
    # 1. CITY table
    print('Populating CITY table...')
    cities = [
        ['CTY0001', 'New York', 'USA', 'Northeast'],
        ['CTY0002', 'Los Angeles', 'USA', 'West Coast'],
        ['CTY0003', 'London', 'UK', 'Greater London'],
        ['CTY0004', 'Paris', 'France', 'Île-de-France'],
        ['CTY0005', 'Tokyo', 'Japan', 'Kanto'],
        ['CTY0006', 'Dubai', 'UAE', 'Dubai'],
    ]
    for city in cities:
        sheets_client.append_row('City', city)
    print(f'✓ Added {len(cities)} cities')
    
    # 2. AIRPORT table
    print('\nPopulating AIRPORT table...')
    airports = [
        ['JFK', 'John F. Kennedy International Airport', 'CTY0001'],
        ['LAX', 'Los Angeles International Airport', 'CTY0002'],
        ['LHR', 'London Heathrow Airport', 'CTY0003'],
        ['CDG', 'Charles de Gaulle Airport', 'CTY0004'],
        ['NRT', 'Narita International Airport', 'CTY0005'],
        ['DXB', 'Dubai International Airport', 'CTY0006'],
    ]
    for airport in airports:
        sheets_client.append_row('Airport', airport)
    print(f'✓ Added {len(airports)} airports')
    
    # 3. FLIGHT table
    print('\nPopulating FLIGHT table...')
    flights = [
        ['FL0001', 'AA101', 'American Airlines', 'Boeing 777', 'JFK', 'LAX', 
         (datetime.now(timezone.utc) + timedelta(days=7, hours=8)).isoformat(), 
         (datetime.now(timezone.utc) + timedelta(days=7, hours=14)).isoformat(), '350.00'],
        ['FL0002', 'BA202', 'British Airways', 'Airbus A380', 'LHR', 'JFK', 
         (datetime.now(timezone.utc) + timedelta(days=5, hours=10)).isoformat(), 
         (datetime.now(timezone.utc) + timedelta(days=5, hours=18)).isoformat(), '650.00'],
        ['FL0003', 'AF303', 'Air France', 'Boeing 787', 'CDG', 'DXB', 
         (datetime.now(timezone.utc) + timedelta(days=10, hours=14)).isoformat(), 
         (datetime.now(timezone.utc) + timedelta(days=10, hours=20)).isoformat(), '550.00'],
        ['FL0004', 'JL404', 'Japan Airlines', 'Boeing 777', 'NRT', 'LAX', 
         (datetime.now(timezone.utc) + timedelta(days=15, hours=16)).isoformat(), 
         (datetime.now(timezone.utc) + timedelta(days=15, hours=25)).isoformat(), '800.00'],
    ]
    for flight in flights:
        sheets_client.append_row('Flight', flight)
    print(f'✓ Added {len(flights)} flights')
    
    # 4. HOTEL table
    print('\nPopulating HOTEL table...')
    hotels = [
        ['HTL0001', 'Grand Plaza Hotel', 'CTY0001', '123 Broadway, New York', '4.5', '+1-212-555-0100', 'Luxury hotel in the heart of Manhattan'],
        ['HTL0002', 'Sunset Beach Resort', 'CTY0002', '456 Ocean Ave, Los Angeles', '4.2', '+1-310-555-0200', 'Beautiful beachfront resort'],
        ['HTL0003', 'London Royal Inn', 'CTY0003', '789 Westminster St, London', '4.7', '+44-20-555-0300', 'Historic hotel near Big Ben'],
        ['HTL0004', 'Paris Boutique Hotel', 'CTY0004', '321 Champs-Élysées, Paris', '4.8', '+33-1-555-0400', 'Charming hotel with Eiffel Tower view'],
        ['HTL0005', 'Tokyo Garden Hotel', 'CTY0005', '654 Shibuya, Tokyo', '4.6', '+81-3-555-0500', 'Modern hotel in vibrant Shibuya'],
    ]
    for hotel in hotels:
        sheets_client.append_row('Hotel', hotel)
    print(f'✓ Added {len(hotels)} hotels')
    
    # 5. ROOM table
    print('\nPopulating ROOM table...')
    rooms = [
        ['RM0001', 'HTL0001', 'single', '1', '150.00'],
        ['RM0002', 'HTL0001', 'double', '2', '220.00'],
        ['RM0003', 'HTL0001', 'suite', '4', '450.00'],
        ['RM0004', 'HTL0002', 'single', '1', '120.00'],
        ['RM0005', 'HTL0002', 'double', '2', '180.00'],
        ['RM0006', 'HTL0003', 'double', '2', '200.00'],
        ['RM0007', 'HTL0003', 'suite', '3', '400.00'],
        ['RM0008', 'HTL0004', 'single', '1', '180.00'],
        ['RM0009', 'HTL0004', 'suite', '4', '550.00'],
        ['RM0010', 'HTL0005', 'double', '2', '160.00'],
    ]
    for room in rooms:
        sheets_client.append_row('Room', room)
    print(f'✓ Added {len(rooms)} rooms')
    
    # 6. CAR table
    print('\nPopulating CAR table...')
    cars = [
        ['CAR0001', 'CTY0001', 'Camry', 'Toyota', '2023', '5', 'automatic', 'gasoline', '60.00'],
        ['CAR0002', 'CTY0001', 'Model 3', 'Tesla', '2024', '5', 'automatic', 'electric', '85.00'],
        ['CAR0003', 'CTY0002', 'Mustang', 'Ford', '2023', '4', 'automatic', 'gasoline', '95.00'],
        ['CAR0004', 'CTY0002', 'Civic', 'Honda', '2023', '5', 'automatic', 'gasoline', '55.00'],
        ['CAR0005', 'CTY0003', 'Golf', 'Volkswagen', '2023', '5', 'manual', 'diesel', '50.00'],
        ['CAR0006', 'CTY0004', 'Clio', 'Renault', '2023', '5', 'manual', 'gasoline', '45.00'],
        ['CAR0007', 'CTY0005', 'Prius', 'Toyota', '2024', '5', 'automatic', 'hybrid', '70.00'],
    ]
    for car in cars:
        sheets_client.append_row('Car', car)
    print(f'✓ Added {len(cars)} cars')
    
    # 7. USER table
    print('\nPopulating USER table...')
    users = [
        ['USR0001', 'john.doe@example.com', 'hashed_password_123', 'John Doe', 'user', datetime.now().isoformat(), datetime.now().isoformat()],
        ['USR0002', 'jane.smith@example.com', 'hashed_password_456', 'Jane Smith', 'user', datetime.now().isoformat(), datetime.now().isoformat()],
        ['USR0003', 'admin@travel.com', 'hashed_password_admin', 'Admin User', 'admin', datetime.now().isoformat(), datetime.now().isoformat()],
    ]
    for user in users:
        sheets_client.append_row('User', user)
    print(f'✓ Added {len(users)} users')
    
    # 8. SESSION table
    print('\nPopulating SESSION table...')
    sessions = [
        ['SES0001', 'USR0001', 'token_abc123def456', datetime.now().isoformat(), (datetime.now() + timedelta(days=7)).isoformat()],
        ['SES0002', 'USR0002', 'token_xyz789ghi012', datetime.now().isoformat(), (datetime.now() + timedelta(days=7)).isoformat()],
    ]
    for session in sessions:
        sheets_client.append_row('Session', session)
    print(f'✓ Added {len(sessions)} sessions')
    
    # 9. BOOKING table
    print('\nPopulating BOOKING table...')
    bookings = [
        ['BK0001', 'USR0001', 'confirmed', datetime.now().isoformat(), '1200.00'],
        ['BK0002', 'USR0002', 'pending', datetime.now().isoformat(), '850.00'],
    ]
    for booking in bookings:
        sheets_client.append_row('Booking', booking)
    print(f'✓ Added {len(bookings)} bookings')
    
    # 10. FLIGHTBOOKING table
    print('\nPopulating FLIGHTBOOKING table...')
    flightbookings = [
        ['FBK0001', 'BK0001', 'FL0002', 'economy', '2'],
        ['FBK0002', 'BK0002', 'FL0003', 'business', '1'],
    ]
    for fb in flightbookings:
        sheets_client.append_row('FlightBooking', fb)
    print(f'✓ Added {len(flightbookings)} flight bookings')
    
    # 11. HOTELBOOKING table
    print('\nPopulating HOTELBOOKING table...')
    hotelbookings = [
        ['HBK0001', 'BK0001', 'RM0003', (datetime.now() + timedelta(days=7)).date().isoformat(), (datetime.now() + timedelta(days=10)).date().isoformat(), '2'],
    ]
    for hb in hotelbookings:
        sheets_client.append_row('HotelBooking', hb)
    print(f'✓ Added {len(hotelbookings)} hotel bookings')
    
    # 12. CARBOOKING table
    print('\nPopulating CARBOOKING table...')
    carbookings = [
        ['CBK0001', 'BK0002', 'CAR0001', (datetime.now() + timedelta(days=5)).isoformat(), (datetime.now() + timedelta(days=8)).isoformat(), 'JFK Airport', 'Times Square, NYC'],
    ]
    for cb in carbookings:
        sheets_client.append_row('CarBooking', cb)
    print(f'✓ Added {len(carbookings)} car bookings')
    
    # 13. PASSENGER table
    print('\nPopulating PASSENGER table...')
    passengers = [
        ['PAX0001', 'BK0001', 'John', 'Doe', 'Male', '1990-05-15', 'US123456789'],
        ['PAX0002', 'BK0001', 'Emily', 'Doe', 'Female', '1992-08-22', 'US987654321'],
        ['PAX0003', 'BK0002', 'Jane', 'Smith', 'Female', '1985-03-10', 'UK456789123'],
    ]
    for passenger in passengers:
        sheets_client.append_row('Passenger', passenger)
    print(f'✓ Added {len(passengers)} passengers')
    
    # 14. PAYMENT table
    print('\nPopulating PAYMENT table...')
    payments = [
        ['PMT0001', 'BK0001', 'card', '1200.00', datetime.now().isoformat(), 'success', 'TXN20241109001'],
        ['PMT0002', 'BK0002', 'upi', '850.00', datetime.now().isoformat(), 'success', 'TXN20241109002'],
    ]
    for payment in payments:
        sheets_client.append_row('Payment', payment)
    print(f'✓ Added {len(payments)} payments')
    
    print('\n✅ All sheets populated successfully with standardized IDs!')

if __name__ == '__main__':
    populate_all_sheets()
