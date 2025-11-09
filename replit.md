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

## MCP Tools (11 Total)

### Listing Tools (6 tools)
1. **`list_cities()`** → Returns all cities with details
2. **`list_airports(city_id)`** → Returns airports in a city with airport and city names
3. **`list_flights(origin_code, destination_code, date)`** → Returns flights with availability and human-readable origin/destination info
4. **`list_hotels(city_id)`** → Returns hotels in a city with full details and city name
5. **`list_rooms(hotel_id)`** → Returns rooms with availability, hotel info, and city name
6. **`list_cars(city_id)`** → Returns cars with full location info and city name

### Booking Management Tools (5 tools)
7. **`create_booking(request)`** → Creates a single master booking with optional flight/hotel/car bookings, passengers, and payment
8. **`get_booking(booking_id)`** → Returns full booking details including all sub-bookings, passengers, and payment
9. **`cancel_booking(booking_id)`** → Cancels a booking and refunds payment
10. **`update_passenger(passenger_id, updates)`** → Updates passenger information

### Testing Tool (1 tool)
11. **`test_tools()`** → Runs comprehensive end-to-end tests for all 10 tools

## Standardized ID Format

All entities use prefix + zero-padded digits:
- **Booking**: BK + 4 digits (BK0001)
- **FlightBooking**: FBK + 4 digits (FBK0001)
- **HotelBooking**: HBK + 4 digits (HBK0001)
- **CarBooking**: CBK + 4 digits (CBK0001)
- **Passenger**: PA + 5 digits (PA00001) ⭐ *Only entity using 5 digits*
- **Payment**: PMT + 4 digits (PMT0001)
- **Flight**: FL + 4 digits (FL0001)
- **Room**: RM + 4 digits (RM0001)
- **Car**: CAR + 4 digits (CAR0001)
- **User**: USR + 4 digits (USR0001)
- **City**: CY + 4 digits (CY0001)
- **Hotel**: HTL + 4 digits (HTL0001)

## Recent Changes (November 9, 2025)

1. **Complete MCP Tools Refactoring** (Latest):
   - **Tool Renaming & Simplification**:
     * `get_cities()` → `list_cities()`
     * `search_flights(request)` → `list_flights(origin_code, destination_code, date)` - simpler parameters
     * `search_hotels()` removed - split into `list_hotels()` and `list_rooms()`
     * `search_cars(request)` → `list_cars(city_id)` - simpler parameters
     * `get_booking_details()` → `get_booking()`
     * Removed: `get_airports()`, `search_airports()`, `get_user_bookings()`
   
   - **New Tools Created**:
     * `list_hotels(city_id)` - List all hotels in a city with enriched data
     * `list_rooms(hotel_id)` - List rooms with real availability calculation
     * `cancel_booking(booking_id)` - Cancel bookings with automatic refund
     * `update_passenger(passenger_id, updates)` - Update passenger details
     * `test_tools()` - Comprehensive end-to-end testing

   - **Enhanced Pydantic Models**:
     * Created AirportWithCity, HotelWithCity, RoomWithHotelInfo, CarWithCity
     * All list tools now return proper typed Pydantic models (not raw dictionaries)
     * Room availability now calculated based on future bookings

   - **ID Generation Updates**:
     * Extended `generate_next_id()` to accept optional `width` parameter
     * Passenger IDs use width=5 (PA00001), all others use width=4
     * Fixed row indexing bugs in cancel_booking and update_passenger

   - **Performance & Usability**:
     * All tools maintain batch-loading for O(1) lookups
     * All responses include human-readable names (city names, airport names, hotel details)
     * Simplified parameters for better frontend developer experience

2. **Previous Enhancements**:
   - DateTime format documentation with ISO 8601 examples
   - Complete Pydantic type safety for all endpoints
   - Robust validation in create_booking (passenger count, date ranges)
   - Performance optimization with batch-loading
   - Helper functions in sheets_client.py

8. Fixed CORS issues by adding CORSMiddleware to the FastMCP backend

9. Implemented SSE (Server-Sent Events) parser in frontend to handle FastMCP HTTP transport protocol

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
