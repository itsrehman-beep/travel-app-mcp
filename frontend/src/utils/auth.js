const AUTH_API_URL = 'http://localhost:8000/auth'
const TOKEN_KEY = 'travel_auth_token'
const USER_KEY = 'travel_user'

export const authUtils = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  
  setToken: (token) => localStorage.setItem(TOKEN_KEY, token),
  
  removeToken: () => localStorage.removeItem(TOKEN_KEY),
  
  getUser: () => {
    const userData = localStorage.getItem(USER_KEY)
    return userData ? JSON.parse(userData) : null
  },
  
  setUser: (user) => localStorage.setItem(USER_KEY, JSON.stringify(user)),
  
  removeUser: () => localStorage.removeItem(USER_KEY),
  
  isAuthenticated: () => !!authUtils.getToken(),
  
  logout: () => {
    authUtils.removeToken()
    authUtils.removeUser()
  },
  
  register: async (email, password, firstName, lastName) => {
    const response = await fetch(`${AUTH_API_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email,
        password,
        first_name: firstName,
        last_name: lastName
      })
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.error || 'Registration failed')
    }
    
    if (data.token) {
      authUtils.setToken(data.token)
      authUtils.setUser({
        id: data.user_id,
        email: data.email,
        firstName: data.first_name,
        lastName: data.last_name
      })
    }
    
    return data
  },
  
  login: async (email, password) => {
    const response = await fetch(`${AUTH_API_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.error || 'Login failed')
    }
    
    if (data.token) {
      authUtils.setToken(data.token)
      authUtils.setUser({
        id: data.user_id,
        email: data.email,
        firstName: data.first_name,
        lastName: data.last_name
      })
    }
    
    return data
  },
  
  getCurrentUser: async () => {
    const token = authUtils.getToken()
    if (!token) return null
    
    const response = await fetch(`${AUTH_API_URL}/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      authUtils.logout()
      return null
    }
    
    const data = await response.json()
    authUtils.setUser({
      id: data.id,
      email: data.email,
      firstName: data.first_name,
      lastName: data.last_name
    })
    
    return data
  }
}
