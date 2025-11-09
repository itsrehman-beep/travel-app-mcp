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

### Discovery Tools (6 tools)
1. **`list_cities()`** → Returns all cities with details
2. **`list_airports(city_id?)`** → Returns airports, optionally filtered by city (returns ALL airports if no filter)
3. **`list_flights(origin_code?, destination_code?, date?)`** → Returns flights with availability (all params optional - returns ALL flights if no filters)
4. **`list_hotels(city?)`** → Returns hotels, optionally filtered by city name or ID (returns ALL hotels if no filter)
5. **`list_rooms(hotel_id)`** → Returns rooms with real-time availability for a specific hotel
6. **`list_cars(city?)`** → Returns cars, optionally filtered by city name or ID (returns ALL cars if no filter)

### Booking Management Tools (5 tools)
7. **`create_booking(request)`** → Creates a booking with 'pending' status (payment is optional)
8. **`process_payment(booking_id, payment)`** → Processes payment and confirms a pending booking
9. **`get_booking(booking_id)`** → Returns full booking details including all sub-bookings, passengers, and payment
10. **`cancel_booking(booking_id)`** → Cancels a booking and automatically refunds payment
11. **`update_passenger(passenger_id, updates)`** → Updates passenger information

### Typical Booking Workflow (Two-Step Process)
1. **Browse/Search** → Use `list_flights()`, `list_hotels()`, `list_cars()` (with or without filters) to view options
2. **Select Items** → Note the IDs from search results (e.g., FL0001, HTL0001, CAR0001)
3. **Create Booking** → Call `create_booking()` with selected IDs and passenger details (no payment)
4. **Receive Pending Booking** → Get booking_id with status='pending'
5. **Process Payment** → Call `process_payment(booking_id, payment)` to confirm booking
6. **Receive Confirmation** → Booking status updates to 'confirmed', payment record created
7. **Manage Booking** → Use `get_booking()`, `update_passenger()`, or `cancel_booking()` as needed

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

1. **Two-Step Booking Flow Implementation** (Latest - November 9, 2025):
   - **Separated Payment from Booking**:
     * Payment is now **optional** in `CreateBookingRequest` model
     * `create_booking()` creates bookings with `'pending'` status by default
     * Bookings no longer automatically create payment records
   
   - **New `process_payment()` Tool**:
     * Added 11th MCP tool: `process_payment(booking_id, payment)`
     * Accepts booking_id and PaymentInput (method, amount)
     * Verifies payment amount matches booking total
     * Updates booking status from `'pending'` to `'confirmed'`
     * Creates Payment record with transaction reference
   
   - **Updated Booking Workflow**:
     * Step 1: Create booking → Returns booking_id with 'pending' status
     * Step 2: Process payment separately → Confirms booking
     * Enables "create booking now, pay later" use cases
   
   - **Frontend FastMCP Integration**:
     * Completely rebuilt frontend to use FastMCP HTTP transport
     * Fixed MCP session initialization hanging issue
     * initializeMCP() now returns immediately after receiving mcp-session-id header
     * Implemented promise caching to prevent duplicate MCP handshakes
     * Added CORS expose_headers for mcp-session-id to allow frontend access
     * All API calls use structuredContent.result for direct object access
   
   - **Backend Improvements**:
     * Made `list_airports()` city_id parameter optional (returns all airports if omitted)
     * Fixed airport dropdown field name from `airport_name` to `name` in frontend
     * CORS middleware properly exposes custom MCP headers

2. **Major API Simplification & UX Improvements**:
   - **Optional Filtering for Browse/Search Tools**:
     * `list_flights()` - All parameters now optional (returns ALL flights if no filters)
     * `list_hotels()` - Accepts optional city name OR city ID (returns ALL hotels if omitted)
     * `list_cars()` - Accepts optional city name OR city ID (returns ALL cars if omitted)
     * Enables both browsing (no filters) and searching (with filters) use cases
   
   - **City Name Support**:
     * `list_hotels()` and `list_cars()` now accept city names (e.g., "Tokyo") in addition to IDs
     * Case-insensitive city name matching for better user experience
     * Automatically detects whether parameter is ID (starts with "CY") or name
   
   - **Removed Internal Tools**:
     * Removed `test_tools()` - internal testing tool not needed in production API
     * Reduced API surface area from 11 to 10 production tools

2. **Complete MCP Tools Refactoring**:
   - **Tool Renaming & Simplification**:
     * `get_cities()` → `list_cities()`
     * `search_flights(request)` → `list_flights()` with optional parameters
     * `search_hotels()` removed - split into `list_hotels()` and `list_rooms()`
     * `search_cars(request)` → `list_cars()` with optional parameter
     * `get_booking_details()` → `get_booking()`
     * Removed: `get_airports()`, `search_airports()`, `get_user_bookings()`
   
   - **New Tools Created**:
     * `list_hotels()` - List hotels with optional city filter
     * `list_rooms(hotel_id)` - List rooms with real availability calculation
     * `cancel_booking(booking_id)` - Cancel bookings with automatic refund
     * `update_passenger(passenger_id, updates)` - Update passenger details

   - **Enhanced Pydantic Models**:
     * Created AirportWithCity, HotelWithCity, RoomWithHotelInfo, CarWithCity
     * All list tools now return proper typed Pydantic models (not raw dictionaries)
     * Room availability now calculated based on future bookings

   - **Critical Bug Fixes**:
     * Fixed row indexing bugs in cancel_booking and update_passenger
     * These bugs could have caused data corruption by updating wrong sheet rows
     * Now correctly subtracts 1 from find_row_by_id result before calling update_row

   - **ID Generation Updates**:
     * Extended `generate_next_id()` to accept optional `width` parameter
     * Passenger IDs use width=5 (PA00001), all others use width=4
     * Ensures consistency across all entity types

   - **Performance & Usability**:
     * All tools maintain batch-loading for O(1) lookups
     * All responses include human-readable names (city names, airport names, hotel details)
     * Simplified parameters for better developer experience

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
