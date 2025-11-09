import os
import json
import requests
from datetime import datetime, timedelta
import uuid

# Get access token from Replit Connectors API
def get_google_sheets_access_token():
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    x_replit_token = None
    
    if os.environ.get('REPL_IDENTITY'):
        x_replit_token = 'repl ' + os.environ['REPL_IDENTITY']
    elif os.environ.get('WEB_REPL_RENEWAL'):
        x_replit_token = 'depl ' + os.environ['WEB_REPL_RENEWAL']
    
    if not x_replit_token or not hostname:
        raise Exception('Replit connection tokens not found')
    
    url = f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=google-sheet'
    headers = {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': x_replit_token
    }
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if 'items' not in data or len(data['items']) == 0:
        raise Exception('Google Sheets connection not found')
    
    connection_settings = data['items'][0]
    access_token = connection_settings.get('settings', {}).get('access_token')
    
    if not access_token:
        raise Exception('Access token not found in connection settings')
    
    return access_token

# Update Google Sheet with data
def update_sheet(access_token, spreadsheet_id, range_name, values):
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}?valueInputOption=RAW'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    body = {'values': values}
    
    response = requests.put(url, headers=headers, json=body)
    if response.status_code != 200:
        print(f'Error updating {range_name}: {response.text}')
    else:
        print(f'✓ Successfully updated {range_name}')
    return response

# Main spreadsheet ID (extracted from URLs)
SPREADSHEET_ID = '1J1AGfOiWizwAlTCKyHjbSV-oWVu6SANJfzp_Fzqb288'

def populate_all_sheets():
    print('Getting access token...')
    access_token = get_google_sheets_access_token()
    print('Access token retrieved successfully!\n')
    
    # 1. USER table (gid=0)
    print('Populating USER table...')
    user_data = [
        ['id', 'email', 'password', 'full_name', 'role', 'created_at', 'last_login'],
        [str(uuid.uuid4()), 'john.doe@example.com', 'hashed_password_123', 'John Doe', 'user', datetime.now().isoformat(), datetime.now().isoformat()],
        [str(uuid.uuid4()), 'jane.smith@example.com', 'hashed_password_456', 'Jane Smith', 'user', datetime.now().isoformat(), datetime.now().isoformat()],
        [str(uuid.uuid4()), 'admin@travel.com', 'hashed_password_admin', 'Admin User', 'admin', datetime.now().isoformat(), datetime.now().isoformat()],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'User'!A1:G4", user_data)
    
    # 2. SESSION table (gid=196552179)
    print('Populating SESSION table...')
    session_data = [
        ['id', 'user_id', 'auth_token', 'created_at', 'expires_at'],
        [str(uuid.uuid4()), user_data[1][0], 'token_' + str(uuid.uuid4()), datetime.now().isoformat(), (datetime.now() + timedelta(days=7)).isoformat()],
        [str(uuid.uuid4()), user_data[2][0], 'token_' + str(uuid.uuid4()), datetime.now().isoformat(), (datetime.now() + timedelta(days=7)).isoformat()],
    ]
    # Get the second sheet by gid
    update_sheet(access_token, SPREADSHEET_ID, "'Session'!A1:E3", session_data)
    
    # 3. CITY table (gid=1294933825)
    print('Populating CITY table...')
    city_data = [
        ['id', 'name', 'country', 'region'],
        [str(uuid.uuid4()), 'New York', 'USA', 'Northeast'],
        [str(uuid.uuid4()), 'Los Angeles', 'USA', 'West Coast'],
        [str(uuid.uuid4()), 'London', 'UK', 'Greater London'],
        [str(uuid.uuid4()), 'Paris', 'France', 'Île-de-France'],
        [str(uuid.uuid4()), 'Tokyo', 'Japan', 'Kanto'],
        [str(uuid.uuid4()), 'Dubai', 'UAE', 'Dubai'],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'City'!A1:D7", city_data)
    
    # 4. AIRPORT table (gid=19291421)
    print('Populating AIRPORT table...')
    airport_data = [
        ['code', 'name', 'city_id'],
        ['JFK', 'John F. Kennedy International Airport', city_data[1][0]],
        ['LAX', 'Los Angeles International Airport', city_data[2][0]],
        ['LHR', 'London Heathrow Airport', city_data[3][0]],
        ['CDG', 'Charles de Gaulle Airport', city_data[4][0]],
        ['NRT', 'Narita International Airport', city_data[5][0]],
        ['DXB', 'Dubai International Airport', city_data[6][0]],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'Airport'!A1:C7", airport_data)
    
    # 5. FLIGHT table (gid=1829729922)
    print('Populating FLIGHT table...')
    flight_data = [
        ['id', 'flight_number', 'airline_name', 'aircraft_model', 'origin_code', 'destination_code', 'departure_time', 'arrival_time', 'base_price'],
        [str(uuid.uuid4()), 'AA101', 'American Airlines', 'Boeing 777', 'JFK', 'LAX', (datetime.now() + timedelta(days=7, hours=8)).isoformat(), (datetime.now() + timedelta(days=7, hours=14)).isoformat(), '350.00'],
        [str(uuid.uuid4()), 'BA202', 'British Airways', 'Airbus A380', 'LHR', 'JFK', (datetime.now() + timedelta(days=5, hours=10)).isoformat(), (datetime.now() + timedelta(days=5, hours=18)).isoformat(), '650.00'],
        [str(uuid.uuid4()), 'AF303', 'Air France', 'Boeing 787', 'CDG', 'DXB', (datetime.now() + timedelta(days=10, hours=14)).isoformat(), (datetime.now() + timedelta(days=10, hours=20)).isoformat(), '550.00'],
        [str(uuid.uuid4()), 'JL404', 'Japan Airlines', 'Boeing 777', 'NRT', 'LAX', (datetime.now() + timedelta(days=15, hours=16)).isoformat(), (datetime.now() + timedelta(days=15, hours=25)).isoformat(), '800.00'],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'Flight'!A1:I5", flight_data)
    
    # 6. HOTEL table (gid=1921469004)
    print('Populating HOTEL table...')
    hotel_data = [
        ['id', 'name', 'city_id', 'address', 'rating', 'contact_number', 'description'],
        [str(uuid.uuid4()), 'Grand Plaza Hotel', city_data[1][0], '123 Broadway, New York', '4.5', '+1-212-555-0100', 'Luxury hotel in the heart of Manhattan'],
        [str(uuid.uuid4()), 'Sunset Beach Resort', city_data[2][0], '456 Ocean Ave, Los Angeles', '4.2', '+1-310-555-0200', 'Beautiful beachfront resort'],
        [str(uuid.uuid4()), 'London Royal Inn', city_data[3][0], '789 Westminster St, London', '4.7', '+44-20-555-0300', 'Historic hotel near Big Ben'],
        [str(uuid.uuid4()), 'Paris Boutique Hotel', city_data[4][0], '321 Champs-Élysées, Paris', '4.8', '+33-1-555-0400', 'Charming hotel with Eiffel Tower view'],
        [str(uuid.uuid4()), 'Tokyo Garden Hotel', city_data[5][0], '654 Shibuya, Tokyo', '4.6', '+81-3-555-0500', 'Modern hotel in vibrant Shibuya'],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'Hotel'!A1:G6", hotel_data)
    
    # 7. ROOM table (gid=1960556347)
    print('Populating ROOM table...')
    room_data = [
        ['id', 'hotel_id', 'room_type', 'capacity', 'price_per_night'],
        [str(uuid.uuid4()), hotel_data[1][0], 'single', '1', '150.00'],
        [str(uuid.uuid4()), hotel_data[1][0], 'double', '2', '220.00'],
        [str(uuid.uuid4()), hotel_data[1][0], 'suite', '4', '450.00'],
        [str(uuid.uuid4()), hotel_data[2][0], 'single', '1', '120.00'],
        [str(uuid.uuid4()), hotel_data[2][0], 'double', '2', '180.00'],
        [str(uuid.uuid4()), hotel_data[3][0], 'double', '2', '200.00'],
        [str(uuid.uuid4()), hotel_data[3][0], 'suite', '3', '400.00'],
        [str(uuid.uuid4()), hotel_data[4][0], 'single', '1', '180.00'],
        [str(uuid.uuid4()), hotel_data[4][0], 'suite', '4', '550.00'],
        [str(uuid.uuid4()), hotel_data[5][0], 'double', '2', '160.00'],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'Room'!A1:E11", room_data)
    
    # 8. CAR table (gid=628352603)
    print('Populating CAR table...')
    car_data = [
        ['id', 'city_id', 'model', 'brand', 'year', 'seats', 'transmission', 'fuel_type', 'price_per_day'],
        [str(uuid.uuid4()), city_data[1][0], 'Camry', 'Toyota', '2023', '5', 'automatic', 'gasoline', '60.00'],
        [str(uuid.uuid4()), city_data[1][0], 'Model 3', 'Tesla', '2024', '5', 'automatic', 'electric', '85.00'],
        [str(uuid.uuid4()), city_data[2][0], 'Mustang', 'Ford', '2023', '4', 'automatic', 'gasoline', '95.00'],
        [str(uuid.uuid4()), city_data[2][0], 'Civic', 'Honda', '2023', '5', 'automatic', 'gasoline', '55.00'],
        [str(uuid.uuid4()), city_data[3][0], 'Golf', 'Volkswagen', '2023', '5', 'manual', 'diesel', '50.00'],
        [str(uuid.uuid4()), city_data[4][0], 'Clio', 'Renault', '2023', '5', 'manual', 'gasoline', '45.00'],
        [str(uuid.uuid4()), city_data[5][0], 'Prius', 'Toyota', '2024', '5', 'automatic', 'hybrid', '70.00'],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'Car'!A1:I8", car_data)
    
    # 9. BOOKING table (gid=1863814684)
    print('Populating BOOKING table...')
    booking_data = [
        ['id', 'user_id', 'status', 'booked_at', 'total_price'],
        [str(uuid.uuid4()), user_data[1][0], 'confirmed', datetime.now().isoformat(), '1200.00'],
        [str(uuid.uuid4()), user_data[2][0], 'pending', datetime.now().isoformat(), '850.00'],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'Booking'!A1:E3", booking_data)
    
    # 10. FLIGHTBOOKING table (gid=1230177364)
    print('Populating FLIGHTBOOKING table...')
    flightbooking_data = [
        ['id', 'booking_id', 'flight_id', 'seat_class', 'passengers'],
        [str(uuid.uuid4()), booking_data[1][0], flight_data[1][0], 'economy', '2'],
        [str(uuid.uuid4()), booking_data[2][0], flight_data[2][0], 'business', '1'],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'FlightBooking'!A1:E3", flightbooking_data)
    
    # 11. HOTELBOOKING table (gid=1494653271)
    print('Populating HOTELBOOKING table...')
    hotelbooking_data = [
        ['id', 'booking_id', 'room_id', 'check_in', 'check_out', 'guests'],
        [str(uuid.uuid4()), booking_data[1][0], room_data[2][0], (datetime.now() + timedelta(days=7)).date().isoformat(), (datetime.now() + timedelta(days=10)).date().isoformat(), '2'],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'HotelBooking'!A1:F2", hotelbooking_data)
    
    # 12. CARBOOKING table (gid=2051961764)
    print('Populating CARBOOKING table...')
    carbooking_data = [
        ['id', 'booking_id', 'car_id', 'pickup_time', 'dropoff_time', 'pickup_location', 'dropoff_location'],
        [str(uuid.uuid4()), booking_data[2][0], car_data[1][0], (datetime.now() + timedelta(days=5)).isoformat(), (datetime.now() + timedelta(days=8)).isoformat(), 'JFK Airport', 'Times Square, NYC'],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'CarBooking'!A1:G2", carbooking_data)
    
    # 13. PASSENGER table (gid=785424319)
    print('Populating PASSENGER table...')
    passenger_data = [
        ['id', 'booking_id', 'first_name', 'last_name', 'gender', 'dob', 'passport_no'],
        [str(uuid.uuid4()), booking_data[1][0], 'John', 'Doe', 'Male', '1990-05-15', 'US123456789'],
        [str(uuid.uuid4()), booking_data[1][0], 'Emily', 'Doe', 'Female', '1992-08-22', 'US987654321'],
        [str(uuid.uuid4()), booking_data[2][0], 'Jane', 'Smith', 'Female', '1985-03-10', 'UK456789123'],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'Passenger'!A1:G4", passenger_data)
    
    # 14. PAYMENT table (gid=1002825379)
    print('Populating PAYMENT table...')
    payment_data = [
        ['id', 'booking_id', 'method', 'amount', 'paid_at', 'status', 'transaction_ref'],
        [str(uuid.uuid4()), booking_data[1][0], 'card', '1200.00', datetime.now().isoformat(), 'success', 'TXN' + str(uuid.uuid4())[:8]],
        [str(uuid.uuid4()), booking_data[2][0], 'upi', '850.00', datetime.now().isoformat(), 'success', 'TXN' + str(uuid.uuid4())[:8]],
    ]
    update_sheet(access_token, SPREADSHEET_ID, "'Payment'!A1:G3", payment_data)
    
    print('\n✅ All sheets populated successfully!')

if __name__ == '__main__':
    populate_all_sheets()
