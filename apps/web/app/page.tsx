'use client'
// Main entry point with authentication
import LoginGate from '@/components/auth/LoginGate'
import Dashboard from './dashboard'

export default function Home() {
  return (
    <LoginGate pageName="Trading Dashboard">
      <Dashboard />
    </LoginGate>
  )
}