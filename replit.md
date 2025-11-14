# Travel Booking Platform

## Overview
A full-stack travel booking application enabling users to book flights, hotels, and cars. The platform utilizes Google Sheets as its primary data store and offers a modern web interface for searching and booking travel services. Its core purpose is to provide a unified, efficient solution for multi-service travel arrangements, demonstrating a streamlined approach to online travel booking.

## User Preferences
I want iterative development.
I prefer detailed explanations.
Ask before making major changes.
Do not make changes to the folder `Z`.
Do not make changes to the file `Y`.

## System Architecture
The application features a Python-based backend using FastMCP (v2.13.0.2) for REST-style endpoints with Pydantic validation, and a React + Vite frontend for a responsive UI. Full user authentication is implemented with bearer tokens stored in Google Sheets (NO PostgreSQL). The system supports multi-item booking flows (though currently focused on single-item booking for MVP) and real-time availability checks. Google Sheets serves as the ONLY data store for ALL data including User and Session tables, integrated via Replit Connectors.

### UI/UX Decisions
- **Modern Design**: Teal (#14b8a6) and coral (#f97316) color palette with gradient backgrounds
- **Responsive Layout**: Card-based design system with smooth transitions and hover effects
- **Tab Navigation**: Clean tab interface for switching between Flights, Hotels, and Cars
- **Authentication Flow**: Dedicated Login/Register pages with gradient backgrounds
- **Multi-item booking flow**: Currently single-item focused for MVP
- **Real-time availability display**: Visual indicators for available/unavailable items

### Technical Implementations
- **Backend**: 
  - Python with FastMCP for API endpoints
  - Pydantic for data validation
  - Bearer token authentication with bcrypt password hashing
  - REST endpoints for auth (/auth/register, /auth/login, /auth/me)
  - Google Sheets integration for ALL data (User, Session, and travel data)
  - NO PostgreSQL database
- **Frontend**: 
  - React 18 with Vite for fast development
  - React Router v6 for client-side routing
  - React Context API for authentication state management
  - Custom CSS with CSS variables for theming
  - Protected routes requiring authentication
  - JWT token storage in localStorage
- **Data Storage**: 
  - Google Sheets for ALL entities: User, Session, City, Airport, Flight, Hotel, Room, Car, Booking, FlightBooking, HotelBooking, CarBooking, Passenger, Payment (14 tables total)
  - NO PostgreSQL database

### Feature Specifications
- **Authentication**: 
  - User registration with email, password, first name, last name
  - Login with bearer token generation (7-day expiration)
  - Bearer tokens stored in Google Sheets Session table
  - Token validation by checking auth_token column in Session table
  - Protected routes requiring authentication
  - Automatic logout on token expiration
- **Search**: 
  - Flights (origin/destination, date, class) - Public access
  - Hotels (city, dates, guests) - Public access
  - Cars (city, dates) - Public access
  - All search functions include real-time availability checks
- **Booking**: 
  - Two-step process (pending then confirmed via payment)
  - Authentication required for all booking operations
  - Detailed passenger information for flights
  - Automated total amount calculation
  - JWT token passed to backend for user identification
- **Availability Logic**: 
  - Seat-based for flights
  - Date-overlap detection for hotels and cars

### System Design Choices
- **ID Format**: Standardized prefix + zero-padded digits for all entities (e.g., BK0001 for Booking, PA00001 for Passenger, USR0001 for User, SES0001 for Session).
- **Authentication Workflow**: Register/Login -> Receive Bearer Token -> Token Stored in Session Table (Google Sheets) -> Access Protected Routes by Validating Token in Session Table
- **Booking Workflow**: Browse/Search (Public) -> Select Item -> Login (if not authenticated) -> Create Booking with auth_token (pending) -> Process Payment with auth_token (confirms booking).
- **API Endpoints**: 
  - **REST Endpoints** (Starlette, header-based auth):
    - `/auth/register` (POST) - Create new user account
    - `/auth/login` (POST) - Login and receive bearer token
    - `/auth/me` (GET) - Get current user info (requires Authorization header)
    - `/bookings` (GET) - Get all user bookings (requires Authorization header)
    - `/bookings/pending` (GET) - Get pending bookings (requires Authorization header)
  - **MCP Tools** (17 total, parameter-based auth):
    - **Authentication**: `register(email, password, ...)`, `login(email, password)`
    - **Discovery (Public)**: `list_cities()`, `list_airports()`, `list_hotels()`, `list_rooms()`, `list_flights()`, `list_cars()`
    - **Booking Management (Protected)**: `book_flight(auth_token, ...)`, `book_hotel(auth_token, ...)`, `book_car(auth_token, ...)`, `process_payment(auth_token, ...)`, `get_booking()`, `cancel_booking()`, `update_passenger()`, `get_user_bookings(auth_token)`, `get_pending_bookings(auth_token)`

## External Dependencies
- **Google Sheets**: Used as the ONLY database for ALL data (User, Session, travel entities).
- **FastMCP**: Python framework for building the backend API.
- **React**: JavaScript library for building the user interface.
- **React Router**: Client-side routing for React applications.
- **Vite**: Frontend tooling for a fast development experience.
- **Replit Connectors API**: Facilitates secure and efficient integration with Google Sheets.
- **Pydantic**: Data validation and settings management for Python.
- **bcrypt**: Password hashing for secure authentication.

## Recent Changes

### November 14, 2025 (Latest)
- **HYBRID AUTHENTICATION**: Implemented dual-mode authentication for MCP tools and frontend
  - Created `AuthContextMiddleware` that extracts `Authorization: Bearer <token>` header on every request
  - Token stored in request-scoped `ContextVar` for frontend access
  - MCP tools (`get_user_bookings`, `get_pending_bookings`) support **BOTH**:
    1. **Frontend**: Automatic token extraction from Authorization header via middleware
    2. **MCP Clients**: Explicit `auth_token` parameter (e.g., Postman MCP Client)
  - `validate_session_hybrid()` tries parameter first, then context fallback
  - Frontend sends `Authorization: Bearer <token>` header via Axios interceptor
  - Context automatically cleaned up after each request to prevent leakage

- **PORT UNIFICATION FOR PUBLISHING**: Configured Vite proxy for single-port deployment
  - Frontend runs on port 5000 (publicly exposed port)
  - Vite proxies `/mcp` and `/auth` requests to backend on port 8000
  - Both services accessible through single port for clean publishing
  - Updated frontend to use relative URLs (`/auth` instead of `localhost:8000/auth`)

- **DEPLOYMENT READY**: Application configured for Replit deployment
  - Single external port (5000) proxies to both frontend and backend
  - All authentication flows use middleware-based token validation
  - CORS configured for production
  - Ready to publish with "Deploy" button

### November 13, 2025
- **CRITICAL BUG FIX: Google Sheets OAuth Token Expiration**: Fixed backend crash due to expired access tokens
  - Root cause: `sheets_client.py` was caching OAuth access token indefinitely without checking expiration
  - Google Sheets access tokens expire after 1 hour, causing all API calls to fail
  - Fixed: Now checks `expires_at` field before reusing cached token
  - Auto-refreshes token from Replit Connectors API when expired
  - Installed `python-dateutil` for proper ISO 8601 date parsing
  - Better error messages when Google Sheets connection fails

- **CRITICAL BUG FIX: Login Duplicate User Rows**: Fixed bug where login created duplicate User rows instead of updating last_login field
  - Root cause: `update_row()` in `sheets_client.py` was incorrectly adding `+1` to row_index
  - Fixed method to use correct 1-indexed row numbers (row 1 = header, row 2 = first data)
  - Updated all 4 callers in `server.py` that were compensating for the bug:
    * `cancel_booking` (Booking and Payment updates)
    * `update_passenger`
    * `process_payment`
  - Login now properly updates last_login field in existing User row without creating duplicates

- **NEW FEATURE: Booking History Tools**: Added two new MCP tools for viewing user bookings
  - `get_user_bookings(auth_token)`: Returns all bookings for authenticated user with complete details (status, prices, flight/hotel/car info, passengers, payment)
  - `get_pending_bookings(auth_token)`: Returns only pending bookings awaiting payment
  - Both tools return `List[BookingResponse]` with full booking details joined from all related tables
  - Proper null/None handling and type safety with validation before creating Summary objects
  - Helper function `_build_booking_list(user_id)` consolidates shared logic

- **AUTHENTICATION FLOW REFINEMENT**: Updated registration to be true two-step process
  - `register()` now creates ONLY User row (no Session)
  - Returns `UserResponse` with just `{user_id, email}` (no auth_token)
  - Frontend redirects to `/login` after registration with success message and prefilled email
  - User must call `login()` separately to receive Session token and authenticate
  - Frontend updated: `auth.js`, `AuthContext.jsx`, `Register.jsx`, `Login.jsx`
  - Success message displays: "Registration successful! Please log in with your new account"

### November 12, 2025
- **MAJOR REFACTOR: Google Sheets-Only Authentication**: Removed ALL PostgreSQL dependencies
  - Deleted `backend/auth.py` (PostgreSQL User model, JWT functions)
  - Deleted `backend/services/auth_sync.py` (dual-write service)
  - Created `backend/auth_sheets.py` - SheetsAuthService class
  - ALL authentication data now in Google Sheets (User and Session tables)
  - Bearer tokens (NOT JWT) stored in Session table
  - Token validation: Direct lookup in Session table with expiration check
  - Sequential IDs: USR0001, SES0001 using `sheets_client.generate_next_id()`
  - Authentication workflow:
    - Register: Create User in Sheets → Create Session with bearer token → Return token
    - Login: Verify password from Sheets User table → Create Session → Return token  
    - Protected endpoints: Check bearer token in Session table, verify not expired
  - Updated MCP tools and REST endpoints to use SheetsAuthService
  - Server startup message: "Authentication: Google Sheets only (NO PostgreSQL)"

- **Earlier Work (Same Day)**:
  - Added `register()` and `login()` MCP tools (later refactored to use Sheets-only auth)
  - Initially implemented dual-write to PostgreSQL + Sheets (now removed in favor of Sheets-only)

### November 11, 2025
- **Backend Authentication**: Added full JWT-based authentication system with PostgreSQL database
  - Created `backend/auth.py` with User model, password hashing, JWT generation
  - Added REST endpoints for register/login/me
  - Updated all booking tools to require `auth_token` parameter
  - Database auto-initialization on startup
- **Frontend Redesign**: Complete UI overhaul with new teal & coral color scheme
  - New color palette: Teal (#14b8a6) primary, Coral (#f97316) secondary
  - Created authentication pages (Login, Register) with gradient backgrounds
  - Built AuthContext provider for state management
  - Implemented protected routes with React Router
  - Redesigned all search and booking components with modern card-based layout
  - Added Navbar with user info and logout functionality