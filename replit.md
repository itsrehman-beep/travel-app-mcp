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
The application features a Python-based backend using FastMCP (v2.13.0.2) for REST-style endpoints with Pydantic validation, and a React + Vite frontend for a responsive UI. Full user authentication is implemented with JWT tokens and PostgreSQL database. The system supports multi-item booking flows (though currently focused on single-item booking for MVP) and real-time availability checks. Google Sheets serves as the persistent data store for travel data, integrated via Replit Connectors.

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
  - SQLAlchemy 2.0 for PostgreSQL database (user authentication)
  - JWT authentication with bcrypt password hashing
  - REST endpoints for auth (/auth/register, /auth/login, /auth/me)
  - Google Sheets integration for travel data
- **Frontend**: 
  - React 18 with Vite for fast development
  - React Router v6 for client-side routing
  - React Context API for authentication state management
  - Custom CSS with CSS variables for theming
  - Protected routes requiring authentication
  - JWT token storage in localStorage
- **Data Storage**: 
  - PostgreSQL database for user accounts and sessions
  - Google Sheets for travel-related entities (City, Airport, Flight, Hotel, Room, Car, Booking, FlightBooking, HotelBooking, CarBooking, Passenger, Payment)

### Feature Specifications
- **Authentication**: 
  - User registration with email, password, first name, last name
  - Login with JWT token generation (7-day expiration)
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
- **ID Format**: Standardized prefix + zero-padded digits for all entities (e.g., BK0001 for Booking, PA00001 for Passenger, USR0001 for User).
- **Authentication Workflow**: Register/Login -> Receive JWT Token -> Access Protected Routes
- **Booking Workflow**: Browse/Search (Public) -> Select Item -> Login (if not authenticated) -> Create Booking with auth_token (pending) -> Process Payment with auth_token (confirms booking).
- **API Endpoints**: 
  - **REST Auth Endpoints** (Starlette): `/auth/register`, `/auth/login`, `/auth/me`
  - **MCP Tools** (13 total):
    - **Discovery (Public)**: `list_cities()`, `list_airports()`, `list_hotels()`, `list_rooms()`, `list_flights()`, `list_cars()`
    - **Booking Management (Protected)**: `book_flight(auth_token, ...)`, `book_hotel(auth_token, ...)`, `book_car(auth_token, ...)`, `process_payment(auth_token, ...)`, `get_booking()`, `cancel_booking()`, `update_passenger()`

## External Dependencies
- **Google Sheets**: Used as the primary database for travel-related data.
- **PostgreSQL**: User authentication database (Neon-backed via Replit).
- **FastMCP**: Python framework for building the backend API.
- **React**: JavaScript library for building the user interface.
- **React Router**: Client-side routing for React applications.
- **Vite**: Frontend tooling for a fast development experience.
- **Replit Connectors API**: Facilitates secure and efficient integration with Google Sheets.
- **Pydantic**: Data validation and settings management for Python.
- **SQLAlchemy**: ORM for PostgreSQL database interactions.
- **bcrypt**: Password hashing for secure authentication.
- **PyJWT**: JWT token generation and validation.

## Recent Changes (November 11, 2025)
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