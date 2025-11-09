# Travel Booking Platform

## Overview
A full-stack travel booking application that allows users to book flights, hotels, and cars from a single platform. The system uses Google Sheets as the persistent datastore and provides a modern web interface for searching and booking travel services.

## Architecture

### Backend
- **Technology**: Python + FastMCP (v2.13.0.2)
- **Transport**: HTTP on port 8000
- **Endpoint**: http://localhost:8000/mcp
- **Features**:
  - REST-style endpoints with automatic schema validation via Pydantic
  - Streamable HTTP endpoints for real-time data access
  - Built-in MCP discovery for tool endpoints
  - Google Sheets integration via Replit Connectors API

### Frontend
- **Technology**: React + Vite
- **Port**: 5000 (webview)
- **Features**:
  - Modern, responsive UI for searching flights, hotels, and cars
  - Multi-item booking flow (can book flight + hotel + car together)
  - Passenger details form with validation
  - Real-time availability checking

### Data Storage
- **Platform**: Google Sheets (via Replit Connection)
- **Spreadsheet ID**: 1J1AGfOiWizwAlTCKyHjbSV-oWVu6SANJfzp_Fzqb288
- **Tables**: User, Session, City, Airport, Flight, Hotel, Room, Car, Booking, FlightBooking, HotelBooking, CarBooking, Passenger, Payment

## Project Structure

```
/
├── backend/
│   ├── server.py          # FastMCP server with all endpoints
│   ├── models.py          # Pydantic models for data validation
│   └── sheets_client.py   # Google Sheets helper functions
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Main React component
│   │   └── App.css        # Styling
│   ├── vite.config.js     # Vite configuration
│   └── package.json       # Frontend dependencies
├── populate_sheets.py     # Script to populate Google Sheets with sample data
├── .gitignore
└── replit.md
```

## Key Features

### Search Functionality
1. **Flight Search**: Search by origin/destination airports, date, and seat class
   - Calculates available seats dynamically based on existing bookings
   - Shows departure/arrival times, airline, aircraft model, and price

2. **Hotel Search**: Search by city, check-in/out dates, and number of guests
   - Checks for room availability by detecting overlapping bookings
   - Displays hotel name, room type, capacity, rating, and price per night

3. **Car Search**: Search by city and pickup/dropoff dates
   - Checks availability through time overlap detection
   - Shows car brand, model, year, seats, transmission, fuel type, and daily rate

### Booking System
- **Unified Booking**: Create bookings that include flights, hotels, and/or cars
- **Passenger Management**: Add detailed passenger information (name, DOB, passport, gender)
- **Payment Processing**: Automatic payment creation with transaction references
- **Real-time Calculation**: Automatically calculates total booking amount

### Availability Logic
- **Flights**: Seat-based (200 seats per flight minus existing bookings)
- **Hotels**: Overlap detection for room bookings on specific dates
- **Cars**: Time overlap detection for car rentals

## Recent Changes (November 9, 2025)

1. **Standardized ID Format Implementation**:
   - All primary keys now use prefix + zero-padded 4-digit format (e.g., FL0001, USR0001, BK0001)
   - Added `generate_next_id()` function to sheets_client.py for auto-generating sequential IDs
   - Updated populate_sheets.py to use new ID format for all sample data
   - Modified create_booking endpoint to generate IDs using new format
   - Updated frontend to use USR0001 as the current user

2. Populated all Google Sheets tables with headers and sample data using new ID format

3. Created Python FastMCP backend with 9 tool endpoints:
   - search_flights, search_hotels, search_cars
   - create_booking
   - get_cities, get_airports
   - get_user_bookings, get_booking_details

4. Built React frontend with tabbed interface for flights, hotels, and cars

5. Implemented complete booking flow with passenger form and payment confirmation

6. Configured workflows for backend (port 8000) and frontend (port 5000)

7. Fixed CORS issues by adding CORSMiddleware to the FastMCP backend

8. Implemented SSE (Server-Sent Events) parser in frontend to handle FastMCP HTTP transport protocol

## How to Use

### Running the Application
The application automatically starts via two workflows:
- **backend**: Runs the FastMCP server on port 8000
- **frontend**: Runs the Vite dev server on port 5000

### Booking Flow
1. Select a tab (Flights, Hotels, or Cars)
2. Fill in search criteria and click "Search"
3. Browse results and click "Select" on desired items
4. Click "Proceed to Booking" when ready
5. Fill in passenger details
6. Click "Confirm Booking" to complete

### Testing
Sample data is already populated in Google Sheets:
- 6 cities (New York, Los Angeles, London, Paris, Tokyo, Dubai)
- 6 airports (JFK, LAX, LHR, CDG, NRT, DXB)
- 4 sample flights
- 5 hotels with 10 rooms
- 7 rental cars
- 3 users with existing bookings

## Dependencies

### Backend
- fastmcp==2.13.0.2
- pydantic==2.12.4
- uvicorn==0.38.0
- requests==2.32.5

### Frontend
- react
- vite
- Standard Vite/React dependencies

## Environment Variables
- `REPLIT_CONNECTORS_HOSTNAME`: Set by Replit for Google Sheets connection
- `REPL_IDENTITY` or `WEB_REPL_RENEWAL`: Authentication tokens for Replit API

## Notes
- Google Sheets connection is managed via Replit's integration system
- All API endpoints use FastMCP's automatic validation and schema generation
- Frontend communicates with backend via HTTP POST requests to tool endpoints
- **Current user**: All bookings are made as John Doe (user_id: USR0001)
  - This is hard-coded in the frontend for MVP demonstration purposes
  - Future enhancement: Add user authentication or user selection dropdown

## Known Limitations (MVP)
- No user authentication system - bookings use a fixed user ID
- No booking cancellation or modification endpoints
- No email notifications for bookings
- Limited error handling and validation messages on frontend
- No pagination for search results
- **ID Generation Race Condition**: The `generate_next_id()` function has a potential race condition under high concurrent load. Mitigated with retry logic, but for production use, implement atomic counters or use a proper database with auto-increment primary keys
