import { useAuth } from '../context/AuthContext'
import './Navbar.css'

export const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth()

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <span className="brand-icon">✈️</span>
          <span className="brand-text">TravelBook</span>
        </div>
        
        {isAuthenticated && (
          <div className="navbar-actions">
            <span className="user-welcome">
              Hello, {user?.firstName || user?.email}
            </span>
            <button onClick={logout} className="btn-logout">
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  )
}
