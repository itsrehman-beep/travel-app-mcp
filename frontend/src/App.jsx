import { useState, useEffect } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000/mcp'

let mcpSessionId = null
let requestId = 0

const initializeMCP = async () => {
  if (mcpSessionId) return mcpSessionId
  
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: {
          name: 'travel-booking-client',
          version: '1.0.0'
        }
      },
      id: ++requestId
    })
  })
  
  mcpSessionId = response.headers.get('mcp-session-id')
  
  const contentType = response.headers.get('content-type')
  if (contentType?.includes('text/event-stream')) {
    await parseSSE(response)
  } else {
    await response.json()
  }
  
  return mcpSessionId
}

const parseSSE = async (response) => {
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let result = null
  let eventType = ''
  let dataLines = []
  
  while (true) {
    const { value, done } = await reader.read()
    
    if (done) {
      if (buffer.trim()) {
        const lines = buffer.split('\n')
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            dataLines.push(line.slice(6))
          }
        }
        
        if (eventType === 'message' && dataLines.length > 0) {
          const jsonStr = dataLines.join('\n')
          const data = JSON.parse(jsonStr)
          if (data.error) {
            throw new Error(data.error.message || 'API error')
          }
          result = data.result
        } else if (eventType === 'error' && dataLines.length > 0) {
          const jsonStr = dataLines.join('\n')
          const data = JSON.parse(jsonStr)
          throw new Error(data.error?.message || 'API error')
        }
      }
      break
    }
    
    buffer += decoder.decode(value, { stream: true })
    
    const events = buffer.split('\n\n')
    buffer = events.pop() || ''
    
    for (const event of events) {
      if (!event.trim()) continue
      
      eventType = ''
      dataLines = []
      const lines = event.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          dataLines.push(line.slice(6))
        }
      }
      
      if (eventType === 'message' && dataLines.length > 0) {
        const jsonStr = dataLines.join('\n')
        const data = JSON.parse(jsonStr)
        if (data.error) {
          throw new Error(data.error.message || 'API error')
        }
        result = data.result
      } else if (eventType === 'error' && dataLines.length > 0) {
        const jsonStr = dataLines.join('\n')
        const data = JSON.parse(jsonStr)
        throw new Error(data.error?.message || 'API error')
      } else if (eventType === 'done') {
        break
      }
    }
  }
  
  if (!result) {
    throw new Error('No result found in SSE response')
  }
  return result
}

const callTool = async (toolName, args = {}) => {
  await initializeMCP()
  
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream',
      'Mcp-Session-Id': mcpSessionId
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: args
      },
      id: ++requestId
    })
  })
  
  const contentType = response.headers.get('content-type')
  
  if (contentType?.includes('text/event-stream')) {
    return await parseSSE(response)
  } else {
    const data = await response.json()
    if (data.error) {
      throw new Error(data.error.message || 'API error')
    }
    return data.result
  }
}

function App() {
  const [activeTab, setActiveTab] = useState('flights')
  const [cities, setCities] = useState([])
  const [airports, setAirports] = useState([])
  
  const [flightSearch, setFlightSearch] = useState({
    origin_code: '',
    destination_code: '',
    departure_date: '',
    seat_class: 'economy'
  })
  const [flightResults, setFlightResults] = useState([])
  
  const [hotelSearch, setHotelSearch] = useState({
    city_id: '',
    check_in: '',
    check_out: '',
    guests: 1
  })
  const [hotelResults, setHotelResults] = useState([])
  
  const [carSearch, setCarSearch] = useState({
    city_id: '',
    pickup_date: '',
    dropoff_date: ''
  })
  const [carResults, setCarResults] = useState([])
  
  const [selectedBookings, setSelectedBookings] = useState({
    flight: null,
    hotel: null,
    car: null
  })
  
  const [showBookingForm, setShowBookingForm] = useState(false)
  const [passengers, setPassengers] = useState([{
    first_name: '',
    last_name: '',
    gender: '',
    dob: '',
    passport_no: ''
  }])

  useEffect(() => {
    fetchCitiesAndAirports()
  }, [])

  const fetchCitiesAndAirports = async () => {
    try {
      const citiesResult = await callTool('get_cities')
      if (citiesResult?.content?.[0]?.text) {
        setCities(JSON.parse(citiesResult.content[0].text))
      }

      const airportsResult = await callTool('get_airports')
      if (airportsResult?.content?.[0]?.text) {
        setAirports(JSON.parse(airportsResult.content[0].text))
      }
    } catch (error) {
      console.error('Error fetching data:', error)
    }
  }

  const searchFlights = async (e) => {
    e.preventDefault()
    try {
      const result = await callTool('search_flights', flightSearch)
      if (result?.content?.[0]?.text) {
        setFlightResults(JSON.parse(result.content[0].text))
      }
    } catch (error) {
      console.error('Error searching flights:', error)
    }
  }

  const searchHotels = async (e) => {
    e.preventDefault()
    try {
      const result = await callTool('search_hotels', hotelSearch)
      if (result?.content?.[0]?.text) {
        setHotelResults(JSON.parse(result.content[0].text))
      }
    } catch (error) {
      console.error('Error searching hotels:', error)
    }
  }

  const searchCars = async (e) => {
    e.preventDefault()
    try {
      const result = await callTool('search_cars', carSearch)
      if (result?.content?.[0]?.text) {
        setCarResults(JSON.parse(result.content[0].text))
      }
    } catch (error) {
      console.error('Error searching cars:', error)
    }
  }

  const selectItem = (type, item) => {
    setSelectedBookings(prev => ({ ...prev, [type]: item }))
  }

  const proceedToBooking = () => {
    if (!selectedBookings.flight && !selectedBookings.hotel && !selectedBookings.car) {
      alert('Please select at least one item to book')
      return
    }
    setShowBookingForm(true)
  }

  const createBooking = async (e) => {
    e.preventDefault()
    
    const totalAmount = (
      (selectedBookings.flight ? parseFloat(selectedBookings.flight.base_price) * passengers.length : 0) +
      (selectedBookings.hotel ? parseFloat(selectedBookings.hotel.price_per_night) * 
        Math.ceil((new Date(hotelSearch.check_out) - new Date(hotelSearch.check_in)) / (1000 * 60 * 60 * 24)) : 0) +
      (selectedBookings.car ? parseFloat(selectedBookings.car.price_per_day) * 
        Math.ceil((new Date(carSearch.dropoff_date) - new Date(carSearch.pickup_date)) / (1000 * 60 * 60 * 24)) : 0)
    )

    const bookingData = {
      user_id: '42382f88-fcf7-4b7d-ad65-15fff4a0352d',
      flight_id: selectedBookings.flight?.id,
      flight_seat_class: flightSearch.seat_class,
      flight_passengers: passengers.length,
      room_id: selectedBookings.hotel?.id,
      check_in: hotelSearch.check_in,
      check_out: hotelSearch.check_out,
      hotel_guests: hotelSearch.guests,
      car_id: selectedBookings.car?.id,
      pickup_time: carSearch.pickup_date + 'T10:00:00',
      dropoff_time: carSearch.dropoff_date + 'T10:00:00',
      pickup_location: 'Airport',
      dropoff_location: 'Hotel',
      passengers_json: JSON.stringify(passengers),
      payment_method: 'card',
      total_amount: totalAmount
    }

    try {
      const result = await callTool('create_booking', bookingData)
      if (result?.content?.[0]?.text) {
        const bookingResult = JSON.parse(result.content[0].text)
        alert(`Booking confirmed! Booking ID: ${bookingResult.booking_id}`)
        setShowBookingForm(false)
        setSelectedBookings({ flight: null, hotel: null, car: null })
        setFlightResults([])
        setHotelResults([])
        setCarResults([])
      }
    } catch (error) {
      console.error('Error creating booking:', error)
      alert('Error creating booking: ' + error.message)
    }
  }

  return (
    <div className="App">
      <header className="header">
        <h1>Travel Booking Platform</h1>
        <p>Book flights, hotels, and cars all in one place</p>
      </header>

      {!showBookingForm ? (
        <>
          <div className="tabs">
            <button className={activeTab === 'flights' ? 'tab active' : 'tab'} onClick={() => setActiveTab('flights')}>
              Flights
            </button>
            <button className={activeTab === 'hotels' ? 'tab active' : 'tab'} onClick={() => setActiveTab('hotels')}>
              Hotels
            </button>
            <button className={activeTab === 'cars' ? 'tab active' : 'tab'} onClick={() => setActiveTab('cars')}>
              Cars
            </button>
          </div>

          {activeTab === 'flights' && (
            <div className="search-section">
              <h2>Search Flights</h2>
              <form onSubmit={searchFlights} className="search-form">
                <select value={flightSearch.origin_code} onChange={(e) => setFlightSearch({...flightSearch, origin_code: e.target.value})} required>
                  <option value="">Origin Airport</option>
                  {airports.map(a => <option key={a.code} value={a.code}>{a.name} ({a.code})</option>)}
                </select>
                <select value={flightSearch.destination_code} onChange={(e) => setFlightSearch({...flightSearch, destination_code: e.target.value})} required>
                  <option value="">Destination Airport</option>
                  {airports.map(a => <option key={a.code} value={a.code}>{a.name} ({a.code})</option>)}
                </select>
                <input type="date" value={flightSearch.departure_date} onChange={(e) => setFlightSearch({...flightSearch, departure_date: e.target.value})} required />
                <select value={flightSearch.seat_class} onChange={(e) => setFlightSearch({...flightSearch, seat_class: e.target.value})}>
                  <option value="economy">Economy</option>
                  <option value="business">Business</option>
                </select>
                <button type="submit">Search Flights</button>
              </form>
              
              <div className="results">
                {flightResults.map(flight => (
                  <div key={flight.id} className={`result-card ${selectedBookings.flight?.id === flight.id ? 'selected' : ''}`}>
                    <h3>{flight.airline_name} - {flight.flight_number}</h3>
                    <p>{flight.origin_code} → {flight.destination_code}</p>
                    <p>Aircraft: {flight.aircraft_model}</p>
                    <p>Departure: {new Date(flight.departure_time).toLocaleString()}</p>
                    <p>Available Seats: {flight.available_seats}</p>
                    <p className="price">${flight.base_price}</p>
                    <button onClick={() => selectItem('flight', flight)}>
                      {selectedBookings.flight?.id === flight.id ? 'Selected' : 'Select'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'hotels' && (
            <div className="search-section">
              <h2>Search Hotels</h2>
              <form onSubmit={searchHotels} className="search-form">
                <select value={hotelSearch.city_id} onChange={(e) => setHotelSearch({...hotelSearch, city_id: e.target.value})} required>
                  <option value="">Select City</option>
                  {cities.map(c => <option key={c.id} value={c.id}>{c.name}, {c.country}</option>)}
                </select>
                <input type="date" value={hotelSearch.check_in} onChange={(e) => setHotelSearch({...hotelSearch, check_in: e.target.value})} required />
                <input type="date" value={hotelSearch.check_out} onChange={(e) => setHotelSearch({...hotelSearch, check_out: e.target.value})} required />
                <input type="number" value={hotelSearch.guests} onChange={(e) => setHotelSearch({...hotelSearch, guests: parseInt(e.target.value)})} min="1" required />
                <button type="submit">Search Hotels</button>
              </form>
              
              <div className="results">
                {hotelResults.map(room => (
                  <div key={room.id} className={`result-card ${selectedBookings.hotel?.id === room.id ? 'selected' : ''}`}>
                    <h3>{room.hotel_name}</h3>
                    <p>Room Type: {room.room_type}</p>
                    <p>Capacity: {room.capacity} guests</p>
                    <p>Rating: {room.hotel_rating}</p>
                    <p>{room.hotel_address}</p>
                    <p className="price">${room.price_per_night}/night</p>
                    <button onClick={() => selectItem('hotel', room)}>
                      {selectedBookings.hotel?.id === room.id ? 'Selected' : 'Select'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'cars' && (
            <div className="search-section">
              <h2>Search Cars</h2>
              <form onSubmit={searchCars} className="search-form">
                <select value={carSearch.city_id} onChange={(e) => setCarSearch({...carSearch, city_id: e.target.value})} required>
                  <option value="">Select City</option>
                  {cities.map(c => <option key={c.id} value={c.id}>{c.name}, {c.country}</option>)}
                </select>
                <input type="date" value={carSearch.pickup_date} onChange={(e) => setCarSearch({...carSearch, pickup_date: e.target.value})} required />
                <input type="date" value={carSearch.dropoff_date} onChange={(e) => setCarSearch({...carSearch, dropoff_date: e.target.value})} required />
                <button type="submit">Search Cars</button>
              </form>
              
              <div className="results">
                {carResults.map(car => (
                  <div key={car.id} className={`result-card ${selectedBookings.car?.id === car.id ? 'selected' : ''}`}>
                    <h3>{car.brand} {car.model}</h3>
                    <p>Year: {car.year}</p>
                    <p>Seats: {car.seats}</p>
                    <p>Transmission: {car.transmission}</p>
                    <p>Fuel: {car.fuel_type}</p>
                    <p className="price">${car.price_per_day}/day</p>
                    <button onClick={() => selectItem('car', car)}>
                      {selectedBookings.car?.id === car.id ? 'Selected' : 'Select'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(selectedBookings.flight || selectedBookings.hotel || selectedBookings.car) && (
            <div className="booking-summary">
              <h3>Selected Items</h3>
              {selectedBookings.flight && <p>Flight: {selectedBookings.flight.airline_name} {selectedBookings.flight.flight_number}</p>}
              {selectedBookings.hotel && <p>Hotel: {selectedBookings.hotel.hotel_name} - {selectedBookings.hotel.room_type}</p>}
              {selectedBookings.car && <p>Car: {selectedBookings.car.brand} {selectedBookings.car.model}</p>}
              <button className="proceed-btn" onClick={proceedToBooking}>Proceed to Booking</button>
            </div>
          )}
        </>
      ) : (
        <div className="booking-form">
          <h2>Complete Your Booking</h2>
          <form onSubmit={createBooking}>
            <h3>Passenger Details</h3>
            {passengers.map((passenger, index) => (
              <div key={index} className="passenger-form">
                <h4>Passenger {index + 1}</h4>
                <input type="text" placeholder="First Name" value={passenger.first_name} 
                  onChange={(e) => {
                    const newPassengers = [...passengers]
                    newPassengers[index].first_name = e.target.value
                    setPassengers(newPassengers)
                  }} required />
                <input type="text" placeholder="Last Name" value={passenger.last_name}
                  onChange={(e) => {
                    const newPassengers = [...passengers]
                    newPassengers[index].last_name = e.target.value
                    setPassengers(newPassengers)
                  }} required />
                <select value={passenger.gender}
                  onChange={(e) => {
                    const newPassengers = [...passengers]
                    newPassengers[index].gender = e.target.value
                    setPassengers(newPassengers)
                  }} required>
                  <option value="">Select Gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
                <input type="date" placeholder="Date of Birth" value={passenger.dob}
                  onChange={(e) => {
                    const newPassengers = [...passengers]
                    newPassengers[index].dob = e.target.value
                    setPassengers(newPassengers)
                  }} required />
                <input type="text" placeholder="Passport Number" value={passenger.passport_no}
                  onChange={(e) => {
                    const newPassengers = [...passengers]
                    newPassengers[index].passport_no = e.target.value
                    setPassengers(newPassengers)
                  }} required />
              </div>
            ))}
            
            <div className="form-actions">
              <button type="button" onClick={() => setShowBookingForm(false)}>Back</button>
              <button type="submit" className="confirm-btn">Confirm Booking</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}

export default App
