import { useAuth } from '../context/AuthContext'
import { PlaneIcon, LogoutIcon } from './Icons'
import './Navbar.css'

export const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth()

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <span className="brand-icon"><PlaneIcon size={28} /></span>
          <span className="brand-text">Travel<span>Book</span></span>
        </div>
        
        {isAuthenticated && (
          <div className="navbar-actions">
            <span className="user-welcome">
              Hello, {user?.firstName || user?.email}
            </span>
            <button onClick={logout} className="btn-logout">
              <LogoutIcon size={18} />
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  )
}
