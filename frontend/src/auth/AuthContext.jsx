import { createContext, useContext, useEffect, useState } from 'react'
import {
  login as apiLogin,
  signup as apiSignup,
  getMe,
  getStoredToken,
  setStoredToken,
  clearStoredToken,
} from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [name, setName] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function restoreSession() {
      const token = getStoredToken()
      if (!token) {
        setLoading(false)
        return
      }
      try {
        const me = await getMe()
        setName(me.name)
      } catch {
        clearStoredToken()
      } finally {
        setLoading(false)
      }
    }
    restoreSession()
  }, [])

  async function login(username, password) {
    const result = await apiLogin(username, password)
    setStoredToken(result.access_token)
    setName(result.name)
  }

  async function signup(username, password, userDisplayName) {
    await apiSignup(username, password, userDisplayName)
    await login(username, password)
  }

  function logout() {
    clearStoredToken()
    setName(null)
  }

  const value = {
    name,
    isAuthenticated: !!name,
    loading,
    login,
    signup,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth는 AuthProvider 안에서만 사용할 수 있어요')
  }
  return context
}