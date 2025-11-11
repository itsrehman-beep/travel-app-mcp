import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import './Home.css'

const API_URL = 'http://localhost:8000/mcp'

let mcpSessionId = null
let requestId = 0
let initPromise = null

const initializeMCP = async () => {
  if (mcpSessionId) return mcpSessionId
  if (initPromise) return initPromise
  
  initPromise = (async () => {
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
    
    if (!mcpSessionId) {
      throw new Error('No mcp-session-id header received from server')
    }
    
    return mcpSessionId
  })()
  
  return initPromise
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
  
  return unwrapResult(result)
}

const unwrapResult = (result) => {
  if (result.structuredContent?.result !== undefined) {
    return result.structuredContent.result
  }
  if (result.content?.[0]?.text) {
    try {
      return JSON.parse(result.content[0].text)
    } catch {
      return result.content[0].text
    }
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
  
  if (!response.ok) {
    const text = await response.text()
    console.error('Error response:', text)
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }
  
  const contentType = response.headers.get('content-type')
  
  if (contentType?.includes('text/event-stream')) {
    return await parseSSE(response)
  } else {
    const data = await response.json()
    if (data.error) {
      throw new Error(data.error.message || 'API error')
    }
    return unwrapResult(data.result)
  }
}

export const Home = () => {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('flights')
  const [cities, setCities] = useState([])
  const [airports, setAirports] = useState([])
  
  // Flight search state
  const [flightSearch, setFlightSearch] = useState({
    origin_code: '',
    destination_code: '',
    date: ''
  })
  const [flightResults, setFlightResults] = useState([])
  const [selectedFlight, setSelectedFlight] = useState(null)
  const [seatClass, setSeatClass] = useState('economy')
  
  // Hotel search state
  const [hotelSearch, setHotelSearch] = useState({
    city: '',
    check_in: '',
    check_out: '',
    guests: 1
  })
  const [hotels, setHotels] = useState([])
  const [selectedHotel, setSelectedHotel] = useState(null)
  const [rooms, setRooms] = useState([])
  const [selectedRoom, setSelectedRoom] = useState(null)
  
  // Car search state
  const [carSearch, setCarSearch] = useState({
    city: '',
    pickup_date: '',
    dropoff_date: ''
  })
  const [carResults, setCarResults] = useState([])
  const [selectedCar, setSelectedCar] = useState(null)
  
  // Booking state
  const [showBookingForm, setShowBookingForm] = useState(false)
  const [passengers, setPassengers] = useState([{
    first_name: '',
    last_name: '',
    gender: '',
    dob: '',
    passport_no: ''
  }])
  
  const [pendingBooking, setPendingBooking] = useState(null)
  const [paymentMethod, setPaymentMethod] = useState('card')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchCitiesAndAirports()
  }, [])

  const fetchCitiesAndAirports = async () => {
    try {
      const citiesData = await callTool('list_cities')
      setCities(citiesData || [])

      const airportsData = await callTool('list_airports')
      setAirports(airportsData || [])
    } catch (error) {
      console.error('Error fetching data:', error)
      setError('Failed to load cities and airports')
    }
  }

  const searchFlights = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const params = {}
      if (flightSearch.origin_code) params.origin_code = flightSearch.origin_code
      if (flightSearch.destination_code) params.destination_code = flightSearch.destination_code
      if (flightSearch.date) params.date = flightSearch.date
      
      const flightsData = await callTool('list_flights', params)
      setFlightResults(flightsData || [])
    } catch (error) {
      console.error('Error searching flights:', error)
      setError('Error searching flights: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const searchHotels = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const params = hotelSearch.city ? { city: hotelSearch.city } : {}
      const hotelsData = await callTool('list_hotels', params)
      setHotels(hotelsData || [])
      setRooms([])
      setSelectedRoom(null)
    } catch (error) {
      console.error('Error searching hotels:', error)
      setError('Error searching hotels: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchRooms = async (hotelId, hotelName) => {
    setLoading(true)
    setError('')
    try {
      const roomsData = await callTool('list_rooms', { hotel_id: hotelId })
      setRooms(roomsData || [])
      setSelectedHotel({ id: hotelId, name: hotelName })
    } catch (error) {
      console.error('Error fetching rooms:', error)
      setError('Error fetching rooms: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const searchCars = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const params = carSearch.city ? { city: carSearch.city } : {}
      const carsData = await callTool('list_cars', params)
      setCarResults(carsData || [])
    } catch (error) {
      console.error('Error searching cars:', error)
      setError('Error searching cars: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const proceedToBooking = () => {
    if (!selectedFlight && !selectedRoom && !selectedCar) {
      setError('Please select at least one item to book')
      return
    }
    if (selectedFlight && passengers.length === 0) {
      setError('Please add at least one passenger for flight booking')
      return
    }
    setShowBookingForm(true)
  }

  const createBooking = async (e) => {
    e.preventDefault()
    
    if (!selectedFlight && !selectedRoom && !selectedCar) {
      setError('No items selected')
      return
    }

    setLoading(true)
    setError('')

    try {
      const authToken = localStorage.getItem('travel_auth_token')
      if (!authToken) {
        setError('Authentication required. Please log in.')
        return
      }

      let bookingResponse
      
      if (selectedFlight) {
        const flightBookingData = {
          request: {
            flight_id: selectedFlight.id,
            seat_class: seatClass,
            passengers: passengers.map(p => ({
              first_name: p.first_name,
              last_name: p.last_name,
              gender: p.gender,
              dob: p.dob,
              passport_no: p.passport_no
            }))
          }
        }
        bookingResponse = await callTool('book_flight', {
          auth_token: authToken,
          ...flightBookingData
        })
      } else if (selectedRoom) {
        const hotelBookingData = {
          request: {
            room_id: selectedRoom.id,
            check_in: hotelSearch.check_in,
            check_out: hotelSearch.check_out,
            guests: hotelSearch.guests
          }
        }
        bookingResponse = await callTool('book_hotel', {
          auth_token: authToken,
          ...hotelBookingData
        })
      } else if (selectedCar) {
        const carBookingData = {
          request: {
            car_id: selectedCar.id,
            pickup_time: carSearch.pickup_date + 'T10:00:00',
            dropoff_time: carSearch.dropoff_date + 'T18:00:00',
            pickup_location: 'Airport',
            dropoff_location: 'Hotel'
          }
        }
        bookingResponse = await callTool('book_car', {
          auth_token: authToken,
          ...carBookingData
        })
      }
      
      if (bookingResponse && bookingResponse.booking_id) {
        setPendingBooking(bookingResponse)
      } else {
        setError('Booking created but no booking ID received')
      }
    } catch (error) {
      console.error('Error creating booking:', error)
      setError('Error creating booking: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const processPayment = async (e) => {
    e.preventDefault()
    
    if (!pendingBooking) {
      setError('No pending booking found')
      return
    }

    setLoading(true)
    setError('')

    try {
      const authToken = localStorage.getItem('travel_auth_token')
      if (!authToken) {
        setError('Authentication required. Please log in.')
        return
      }

      const paymentResponse = await callTool('process_payment', {
        auth_token: authToken,
        booking_id: pendingBooking.booking_id,
        payment: {
          method: paymentMethod,
          amount: pendingBooking.total_amount
        }
      })
      
      if (paymentResponse && paymentResponse.success) {
        alert(`Payment successful!\n\nBooking ID: ${paymentResponse.booking_id}\nPayment ID: ${paymentResponse.payment_id}\nTransaction Ref: ${paymentResponse.transaction_ref}\nStatus: ${paymentResponse.booking_status}`)
        
        // Reset form
        setShowBookingForm(false)
        setPendingBooking(null)
        setSelectedFlight(null)
        setSelectedRoom(null)
        setSelectedCar(null)
        setFlightResults([])
        setHotels([])
        setRooms([])
        setCarResults([])
        setPassengers([{
          first_name: '',
          last_name: '',
          gender: '',
          dob: '',
          passport_no: ''
        }])
      } else {
        setError('Payment failed: ' + (paymentResponse?.error || 'Unknown error'))
      }
    } catch (error) {
      console.error('Error processing payment:', error)
      setError('Error processing payment: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="home-container">
      {/* Hero Section */}
      {!showBookingForm && (
        <div className="hero">
          <h1>Explore the World with TravelBook</h1>
          <p>Book flights, hotels, and cars - all in one place</p>
        </div>
      )}

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={() => setError('')} className="close-btn">×</button>
        </div>
      )}

      {!showBookingForm ? (
        <>
          {/* Tabs */}
          <div className="tabs">
            <button 
              className={`tab ${activeTab === 'flights' ? 'active' : ''}`} 
              onClick={() => setActiveTab('flights')}
            >
              ✈️ Flights
            </button>
            <button 
              className={`tab ${activeTab === 'hotels' ? 'active' : ''}`} 
              onClick={() => setActiveTab('hotels')}
            >
              🏨 Hotels
            </button>
            <button 
              className={`tab ${activeTab === 'cars' ? 'active' : ''}`} 
              onClick={() => setActiveTab('cars')}
            >
              🚗 Cars
            </button>
          </div>

          {/* Flight Search */}
          {activeTab === 'flights' && (
            <div className="search-section">
              <h2>Search Flights</h2>
              <form onSubmit={searchFlights} className="search-form">
                <select 
                  value={flightSearch.origin_code} 
                  onChange={(e) => setFlightSearch({...flightSearch, origin_code: e.target.value})}
                >
                  <option value="">From (All Airports)</option>
                  {airports.map(a => (
                    <option key={a.code} value={a.code}>
                      {a.name} ({a.code})
                    </option>
                  ))}
                </select>
                <select 
                  value={flightSearch.destination_code} 
                  onChange={(e) => setFlightSearch({...flightSearch, destination_code: e.target.value})}
                >
                  <option value="">To (All Airports)</option>
                  {airports.map(a => (
                    <option key={a.code} value={a.code}>
                      {a.name} ({a.code})
                    </option>
                  ))}
                </select>
                <input 
                  type="date" 
                  value={flightSearch.date} 
                  onChange={(e) => setFlightSearch({...flightSearch, date: e.target.value})} 
                  placeholder="Departure Date"
                />
                <button type="submit" disabled={loading}>
                  {loading ? 'Searching...' : 'Search Flights'}
                </button>
              </form>
              
              <div className="results">
                {flightResults.map(flight => (
                  <div 
                    key={flight.id} 
                    className={`result-card ${selectedFlight?.id === flight.id ? 'selected' : ''}`}
                  >
                    <div className="card-header">
                      <h3>{flight.airline_name}</h3>
                      <span className="flight-number">{flight.flight_number}</span>
                    </div>
                    <div className="card-route">
                      <div>
                        <p className="airport-code">{flight.origin_code}</p>
                        <p className="city-name">{flight.origin_name}</p>
                      </div>
                      <div className="route-line">→</div>
                      <div>
                        <p className="airport-code">{flight.destination_code}</p>
                        <p className="city-name">{flight.destination_name}</p>
                      </div>
                    </div>
                    <div className="card-details">
                      <p>✈️ {flight.aircraft_model}</p>
                      <p>📅 {new Date(flight.departure_time).toLocaleString()}</p>
                      <p>💺 {flight.available_seats} seats available</p>
                    </div>
                    <div className="card-footer">
                      <p className="price">${flight.base_price}</p>
                      <button onClick={() => setSelectedFlight(flight)}>
                        {selectedFlight?.id === flight.id ? '✓ Selected' : 'Select'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              
              {selectedFlight && (
                <div className="seat-class-selector">
                  <label>Seat Class:</label>
                  <select value={seatClass} onChange={(e) => setSeatClass(e.target.value)}>
                    <option value="economy">Economy</option>
                    <option value="business">Business</option>
                  </select>
                </div>
              )}
            </div>
          )}

          {/* Hotel Search */}
          {activeTab === 'hotels' && (
            <div className="search-section">
              <h2>Search Hotels</h2>
              <form onSubmit={searchHotels} className="search-form">
                <select 
                  value={hotelSearch.city} 
                  onChange={(e) => setHotelSearch({...hotelSearch, city: e.target.value})}
                >
                  <option value="">Select City (All)</option>
                  {cities.map(c => (
                    <option key={c.id} value={c.name}>
                      {c.name}, {c.country}
                    </option>
                  ))}
                </select>
                <input 
                  type="date" 
                  value={hotelSearch.check_in} 
                  onChange={(e) => setHotelSearch({...hotelSearch, check_in: e.target.value})} 
                  placeholder="Check-in"
                />
                <input 
                  type="date" 
                  value={hotelSearch.check_out} 
                  onChange={(e) => setHotelSearch({...hotelSearch, check_out: e.target.value})} 
                  placeholder="Check-out"
                />
                <input 
                  type="number" 
                  value={hotelSearch.guests} 
                  onChange={(e) => setHotelSearch({...hotelSearch, guests: parseInt(e.target.value)})} 
                  min="1" 
                  placeholder="Guests"
                />
                <button type="submit" disabled={loading}>
                  {loading ? 'Searching...' : 'Search Hotels'}
                </button>
              </form>
              
              <div className="results">
                {hotels.map(hotel => (
                  <div key={hotel.id} className="result-card">
                    <div className="card-header">
                      <h3>{hotel.name}</h3>
                      <div className="rating">
                        {'⭐'.repeat(Math.round(hotel.rating))}
                      </div>
                    </div>
                    <div className="card-details">
                      <p>📍 {hotel.city_name}</p>
                      <p>📧 {hotel.address}</p>
                    </div>
                    <div className="card-footer">
                      <button onClick={() => fetchRooms(hotel.id, hotel.name)}>
                        View Rooms
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              
              {selectedHotel && rooms.length > 0 && (
                <>
                  <h3 className="rooms-title">Rooms at {selectedHotel.name}</h3>
                  <div className="results">
                    {rooms.map(room => (
                      <div 
                        key={room.id} 
                        className={`result-card ${selectedRoom?.id === room.id ? 'selected' : ''}`}
                      >
                        <div className="card-header">
                          <h3>{room.room_type}</h3>
                          <span className={`availability ${room.is_available ? 'available' : 'unavailable'}`}>
                            {room.is_available ? '✓ Available' : '✗ Unavailable'}
                          </span>
                        </div>
                        <div className="card-details">
                          <p>👥 Capacity: {room.capacity} guests</p>
                          <p>🏨 {room.hotel_name}</p>
                        </div>
                        <div className="card-footer">
                          <p className="price">${room.price_per_night}/night</p>
                          <button 
                            onClick={() => setSelectedRoom(room)} 
                            disabled={!room.is_available}
                          >
                            {selectedRoom?.id === room.id ? '✓ Selected' : room.is_available ? 'Select' : 'Unavailable'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Car Search */}
          {activeTab === 'cars' && (
            <div className="search-section">
              <h2>Search Rental Cars</h2>
              <form onSubmit={searchCars} className="search-form">
                <select 
                  value={carSearch.city} 
                  onChange={(e) => setCarSearch({...carSearch, city: e.target.value})}
                >
                  <option value="">Select City (All)</option>
                  {cities.map(c => (
                    <option key={c.id} value={c.name}>
                      {c.name}, {c.country}
                    </option>
                  ))}
                </select>
                <input 
                  type="date" 
                  value={carSearch.pickup_date} 
                  onChange={(e) => setCarSearch({...carSearch, pickup_date: e.target.value})} 
                  placeholder="Pickup Date"
                />
                <input 
                  type="date" 
                  value={carSearch.dropoff_date} 
                  onChange={(e) => setCarSearch({...carSearch, dropoff_date: e.target.value})} 
                  placeholder="Dropoff Date"
                />
                <button type="submit" disabled={loading}>
                  {loading ? 'Searching...' : 'Search Cars'}
                </button>
              </form>
              
              <div className="results">
                {carResults.map(car => (
                  <div 
                    key={car.id} 
                    className={`result-card ${selectedCar?.id === car.id ? 'selected' : ''}`}
                  >
                    <div className="card-header">
                      <h3>{car.brand} {car.model}</h3>
                      <span className="car-year">{car.year}</span>
                    </div>
                    <div className="card-details">
                      <p>📍 {car.city_name}</p>
                      <p>👥 {car.seats} seats</p>
                      <p>⚙️ {car.transmission}</p>
                      <p>⛽ {car.fuel_type}</p>
                    </div>
                    <div className="card-footer">
                      <p className="price">${car.price_per_day}/day</p>
                      <button onClick={() => setSelectedCar(car)}>
                        {selectedCar?.id === car.id ? '✓ Selected' : 'Select'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Booking Summary */}
          {(selectedFlight || selectedRoom || selectedCar) && (
            <div className="booking-summary">
              <div className="summary-content">
                <h3>Your Selection</h3>
                <div className="summary-items">
                  {selectedFlight && (
                    <p>✈️ {selectedFlight.airline_name} {selectedFlight.flight_number} ({seatClass})</p>
                  )}
                  {selectedRoom && (
                    <p>🏨 {selectedRoom.hotel_name} - {selectedRoom.room_type}</p>
                  )}
                  {selectedCar && (
                    <p>🚗 {selectedCar.brand} {selectedCar.model}</p>
                  )}
                </div>
                <button className="proceed-btn" onClick={proceedToBooking}>
                  Proceed to Booking →
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="booking-form">
          {!pendingBooking ? (
            <>
              <h2>Complete Your Booking</h2>
              <form onSubmit={createBooking}>
                {selectedFlight && (
                  <>
                    <h3>Passenger Details</h3>
                    {passengers.map((passenger, index) => (
                      <div key={index} className="passenger-form">
                        <h4>Passenger {index + 1}</h4>
                        <div className="form-row">
                          <input 
                            type="text" 
                            placeholder="First Name" 
                            value={passenger.first_name} 
                            onChange={(e) => {
                              const newPassengers = [...passengers]
                              newPassengers[index].first_name = e.target.value
                              setPassengers(newPassengers)
                            }} 
                            required 
                          />
                          <input 
                            type="text" 
                            placeholder="Last Name" 
                            value={passenger.last_name}
                            onChange={(e) => {
                              const newPassengers = [...passengers]
                              newPassengers[index].last_name = e.target.value
                              setPassengers(newPassengers)
                            }} 
                            required 
                          />
                        </div>
                        <div className="form-row">
                          <select 
                            value={passenger.gender}
                            onChange={(e) => {
                              const newPassengers = [...passengers]
                              newPassengers[index].gender = e.target.value
                              setPassengers(newPassengers)
                            }} 
                            required
                          >
                            <option value="">Select Gender</option>
                            <option value="Male">Male</option>
                            <option value="Female">Female</option>
                            <option value="Other">Other</option>
                          </select>
                          <input 
                            type="date" 
                            placeholder="Date of Birth" 
                            value={passenger.dob}
                            onChange={(e) => {
                              const newPassengers = [...passengers]
                              newPassengers[index].dob = e.target.value
                              setPassengers(newPassengers)
                            }} 
                            required 
                          />
                        </div>
                        <input 
                          type="text" 
                          placeholder="Passport Number" 
                          value={passenger.passport_no}
                          onChange={(e) => {
                            const newPassengers = [...passengers]
                            newPassengers[index].passport_no = e.target.value
                            setPassengers(newPassengers)
                          }} 
                          required 
                        />
                      </div>
                    ))}
                    
                    <div className="form-actions">
                      <button 
                        type="button" 
                        onClick={() => setPassengers([...passengers, {
                          first_name: '',
                          last_name: '',
                          gender: '',
                          dob: '',
                          passport_no: ''
                        }])}
                      >
                        + Add Passenger
                      </button>
                      {passengers.length > 1 && (
                        <button 
                          type="button" 
                          onClick={() => setPassengers(passengers.slice(0, -1))}
                        >
                          - Remove Last Passenger
                        </button>
                      )}
                    </div>
                  </>
                )}
                
                <div className="form-actions">
                  <button type="button" onClick={() => setShowBookingForm(false)}>
                    ← Back to Search
                  </button>
                  <button type="submit" disabled={loading}>
                    {loading ? 'Creating Booking...' : 'Confirm Booking'}
                  </button>
                </div>
              </form>
            </>
          ) : (
            <>
              <h2>Payment</h2>
              <div className="booking-info">
                <p><strong>Booking ID:</strong> {pendingBooking.booking_id}</p>
                <p><strong>Status:</strong> {pendingBooking.status}</p>
                <p><strong>Total Amount:</strong> ${pendingBooking.total_amount}</p>
              </div>
              
              <form onSubmit={processPayment}>
                <div className="form-group">
                  <label>Payment Method</label>
                  <select 
                    value={paymentMethod} 
                    onChange={(e) => setPaymentMethod(e.target.value)}
                  >
                    <option value="card">Credit/Debit Card</option>
                    <option value="wallet">Digital Wallet</option>
                    <option value="upi">UPI</option>
                  </select>
                </div>
                
                <div className="form-actions">
                  <button type="button" onClick={() => {
                    setShowBookingForm(false)
                    setPendingBooking(null)
                  }}>
                    Cancel
                  </button>
                  <button type="submit" disabled={loading}>
                    {loading ? 'Processing...' : `Pay $${pendingBooking.total_amount}`}
                  </button>
                </div>
              </form>
            </>
          )}
        </div>
      )}
    </div>
  )
}
