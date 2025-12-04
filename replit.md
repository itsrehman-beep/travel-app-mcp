# Travel Booking Platform

## Overview
A full-stack travel booking application that enables users to book flights, hotels, and cars. The platform offers a modern web interface for searching and booking various travel services, utilizing Google Sheets as its sole data store. Its primary goal is to provide a unified and efficient solution for multi-service travel arrangements, demonstrating a streamlined approach to online travel booking.

## User Preferences
I want iterative development.
I prefer detailed explanations.
Ask before making major changes.
Do not make changes to the folder `Z`.
Do not make changes to the file `Y`.

## System Architecture
The application features a Python-based backend utilizing FastMCP for REST-style endpoints with Pydantic validation, and a React + Vite frontend for a responsive user interface. User authentication is implemented using bearer tokens stored in Google Sheets. The system supports multi-item booking flows (currently focused on single-item booking for MVP) and real-time availability checks. Google Sheets serves as the ONLY data store for all application data, including user and session information, integrated via the `gspread` library.

### UI/UX Decisions
- **Modern Design**: Teal (#14b8a6) and coral (#f97316) color palette with gradient backgrounds.
- **Responsive Layout**: Card-based design system with smooth transitions and hover effects.
- **Tab Navigation**: Clean tab interface for switching between Flights, Hotels, and Cars.
- **Authentication Flow**: Dedicated Login/Register pages with gradient backgrounds.
- **Real-time availability display**: Visual indicators for available/unavailable items.

### Technical Implementations
- **Backend**:
  - Python with FastMCP for API endpoints and Pydantic for data validation.
  - Bearer token authentication with bcrypt password hashing.
  - REST endpoints for authentication (`/auth/register`, `/auth/login`, `/auth/me`).
  - Google Sheets integration for ALL data (User, Session, and travel data entities).
- **Frontend**:
  - React 18 with Vite, utilizing React Router v6 for client-side routing.
  - React Context API for authentication state management.
  - Custom CSS with CSS variables for theming.
  - Protected routes requiring authentication, with JWT token storage in localStorage.
- **Data Storage**:
  - Google Sheets is used for ALL entities, including User, Session, City, Airport, Flight, Hotel, Room, Car, Booking, FlightBooking, HotelBooking, CarBooking, Passenger, and Payment.

### Feature Specifications
- **Authentication**: User registration, login with bearer token generation (7-day expiration), bearer tokens stored in the Google Sheets Session table, and token validation for protected routes.
- **Search**: Public access for Flights (origin/destination, date, class), Hotels (city, dates, guests), and Cars (city, dates), all including real-time availability checks.
- **Booking**: A two-step process (pending then confirmed via payment) requiring authentication. Includes detailed passenger information for flights and automated total amount calculation.
- **Availability Logic**: Seat-based for flights, and date-overlap detection for hotels and cars.

### System Design Choices
- **ID Format**: Standardized prefix + zero-padded digits for all entities (e.g., BK0001 for Booking, USR0001 for User).
- **Authentication Workflow**: Register/Login -> Receive Bearer Token -> Token Stored in Session Table (Google Sheets) -> Access Protected Routes by Validating Token in Session Table.
- **Booking Workflow**: Browse/Search (Public) -> Select Item -> Login (if not authenticated) -> Create Booking (pending) -> Process Payment (confirms booking).
- **API Endpoints**:
  - **REST Endpoints** (Starlette, header-based auth): `/auth/register` (POST), `/auth/login` (POST), `/auth/me` (GET).
  - **MCP Tools** (header-based auth via Authorization: Bearer <token>): Includes tools for authentication (`register`, `login`), discovery (`list_cities`, `list_airports`, `list_hotels`, `list_rooms`, `list_flights`, `list_cars`), and booking management (`book_flight`, `book_hotel`, `book_car`, `process_payment`, `get_booking`, `cancel_booking`, `update_passenger`, `get_user_bookings`, `get_pending_bookings`).

## External Dependencies
- **Google Sheets**: Primary database for all application data.
- **gspread**: Python library for Google Sheets API integration.
- **google-auth**: Authentication library for service account credentials.
- **FastMCP**: Python framework for building the backend API.
- **React**: JavaScript library for building the user interface.
- **React Router**: Client-side routing for React applications.
- **Vite**: Frontend tooling for fast development.
- **Pydantic**: Data validation and settings management for Python.
- **bcrypt**: Password hashing for secure authentication.