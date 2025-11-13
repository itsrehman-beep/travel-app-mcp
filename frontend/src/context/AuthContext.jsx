import { createContext, useContext, useState, useEffect } from 'react'
import { authUtils } from '../utils/auth'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      const token = authUtils.getToken()
      if (token) {
        try {
          await authUtils.getCurrentUser()
          setUser(authUtils.getUser())
        } catch (error) {
          console.error('Failed to load user:', error)
          authUtils.logout()
        }
      }
      setLoading(false)
    }
    
    initAuth()
  }, [])

  const login = async (email, password) => {
    const data = await authUtils.login(email, password)
    setUser(authUtils.getUser())
    return data
  }

  const register = async (email, password, firstName, lastName) => {
    const data = await authUtils.register(email, password, firstName, lastName)
    return data
  }

  const logout = () => {
    authUtils.logout()
    setUser(null)
  }

  const value = {
    user,
    login,
    register,
    logout,
    loading,
    isAuthenticated: !!user
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
