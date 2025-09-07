'use client'

import { useState, useEffect } from 'react'

interface LoginGateProps {
  children: React.ReactNode
  pageName?: string
}

export default function LoginGate({ children, pageName = 'Dashboard' }: LoginGateProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  
  // CHANGE THIS PASSWORD!
  const SYSTEM_PASSWORD = 'msc-secure-2024'
  
  useEffect(() => {
    // Check if user is already authenticated
    const authToken = localStorage.getItem('msc-auth-token')
    const authExpiry = localStorage.getItem('msc-auth-expiry')
    
    if (authToken && authExpiry) {
      const expiryTime = parseInt(authExpiry)
      if (Date.now() < expiryTime) {
        setIsAuthenticated(true)
      } else {
        // Token expired, clear it
        localStorage.removeItem('msc-auth-token')
        localStorage.removeItem('msc-auth-expiry')
      }
    }
    setIsLoading(false)
  }, [])
  
  const handleLogin = () => {
    if (password === SYSTEM_PASSWORD) {
      // Set auth for 24 hours
      const expiryTime = Date.now() + (24 * 60 * 60 * 1000)
      localStorage.setItem('msc-auth-token', 'authenticated')
      localStorage.setItem('msc-auth-expiry', expiryTime.toString())
      setIsAuthenticated(true)
      setError('')
    } else {
      setError('Invalid password')
      setTimeout(() => setError(''), 3000)
    }
  }
  
  const handleLogout = () => {
    localStorage.removeItem('msc-auth-token')
    localStorage.removeItem('msc-auth-expiry')
    setIsAuthenticated(false)
    setPassword('')
  }
  
  // Make logout function available globally
  useEffect(() => {
    if (isAuthenticated) {
      (window as any).mscLogout = handleLogout
    }
  }, [isAuthenticated])
  
  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#0A0E1A',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ color: '#FF6B35', fontSize: '18px' }}>Loading...</div>
      </div>
    )
  }
  
  if (!isAuthenticated) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#0A0E1A',
        backgroundImage: 'radial-gradient(circle at 20% 50%, #1a1f3a 0%, #0A0E1A 50%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'SF Mono, Monaco, monospace'
      }}>
        <div style={{
          backgroundColor: '#141824',
          border: '1px solid #2D3748',
          borderRadius: '2px',
          padding: '40px',
          width: '400px',
          boxShadow: '0 0 40px rgba(255, 107, 53, 0.1)'
        }}>
          {/* Logo/Title */}
          <div style={{ marginBottom: '30px', textAlign: 'center' }}>
            <h1 style={{
              color: '#FF6B35',
              fontSize: '24px',
              fontWeight: 'bold',
              letterSpacing: '2px',
              marginBottom: '8px'
            }}>
              MULROY STREET CAPITAL
            </h1>
            <div style={{
              color: '#A0A9B8',
              fontSize: '12px',
              textTransform: 'uppercase',
              letterSpacing: '1px'
            }}>
              {pageName} Access
            </div>
          </div>
          
          {/* Login Form */}
          <div>
            <label style={{
              display: 'block',
              color: '#A0A9B8',
              fontSize: '11px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: '8px'
            }}>
              Security Passcode
            </label>
            
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
              placeholder="Enter password"
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: '#0A0E1A',
                border: '1px solid #2D3748',
                borderRadius: '2px',
                color: '#E4E7EB',
                fontSize: '14px',
                fontFamily: 'SF Mono, monospace',
                outline: 'none'
              }}
            />
            
            {error && (
              <div style={{
                color: '#FF3366',
                fontSize: '12px',
                marginTop: '8px'
              }}>
                {error}
              </div>
            )}
            
            <button
              onClick={handleLogin}
              style={{
                width: '100%',
                padding: '12px',
                marginTop: '20px',
                backgroundColor: '#FF6B35',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '2px',
                fontSize: '14px',
                fontWeight: 'bold',
                letterSpacing: '1px',
                cursor: 'pointer',
                textTransform: 'uppercase',
                transition: 'all 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#FF8555'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#FF6B35'}
            >
              Authenticate
            </button>
          </div>
          
          {/* Footer */}
          <div style={{
            marginTop: '30px',
            paddingTop: '20px',
            borderTop: '1px solid #2D3748',
            textAlign: 'center'
          }}>
            <div style={{
              color: '#6B7280',
              fontSize: '10px'
            }}>
              Secured Trading System • 256-bit Encryption
            </div>
          </div>
        </div>
      </div>
    )
  }
  
  // User is authenticated - render the protected content
  return <>{children}</>
}