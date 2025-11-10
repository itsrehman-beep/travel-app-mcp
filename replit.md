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
The application features a Python-based backend using FastMCP (v2.13.0.2) for REST-style endpoints with Pydantic validation, and a React + Vite frontend for a responsive UI. The system supports multi-item booking flows (though currently focused on single-item booking for MVP) and real-time availability checks. Google Sheets serves as the persistent data store, integrated via Replit Connectors.

### UI/UX Decisions
- Modern, responsive design.
- Multi-item booking flow (currently single-item focused for MVP).
- Real-time availability display.

### Technical Implementations
- **Backend**: Python with FastMCP for API endpoints, Pydantic for data validation, and Google Sheets integration.
- **Frontend**: React and Vite for a dynamic and responsive user interface.
- **Data Storage**: Google Sheets, accessed through Replit Connectors, serving as the database for all travel-related entities (User, Session, City, Airport, Flight, Hotel, Room, Car, Booking, FlightBooking, HotelBooking, CarBooking, Passenger, Payment).

### Feature Specifications
- **Search**: Flight (origin/destination, date, class), Hotel (city, dates, guests), Car (city, dates). All search functions include real-time availability checks.
- **Booking**: Two-step process (pending then confirmed via payment), detailed passenger information, and automated total amount calculation.
- **Availability Logic**: Seat-based for flights, date-overlap detection for hotels and cars.

### System Design Choices
- **ID Format**: Standardized prefix + zero-padded digits for all entities (e.g., BK0001 for Booking, PA00001 for Passenger).
- **Booking Workflow**: Browse/Search -> Select Item -> Create Booking (pending) -> Process Payment (confirms booking).
- **API Endpoints**: 13 MCP tools divided into Discovery (e.g., `list_cities()`, `list_flights()`) and Booking Management (e.g., `book_flight()`, `process_payment()`, `cancel_booking()`).

## External Dependencies
- **Google Sheets**: Used as the primary database for all application data.
- **FastMCP**: Python framework for building the backend API.
- **React**: JavaScript library for building the user interface.
- **Vite**: Frontend tooling for a fast development experience.
- **Replit Connectors API**: Facilitates secure and efficient integration with Google Sheets.
- **Pydantic**: Data validation and settings management for Python.