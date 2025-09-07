'use client'
// Main Dashboard - imports components from registry
// To update a component, modify it in components/modules/ not here

import { useEffect, useState } from 'react'
import * as Components from '@/components/registry'

export default function Dashboard() {
  const [account, setAccount] = useState(null)
  const [positions, setPositions] = useState([])
  const [lastUpdate, setLastUpdate] = useState(new Date())
  
  const fetchData = async () => {
    try {
      const [accRes, posRes] = await Promise.all([
        fetch('https://mulroystreetcap.com/api/account'),
        fetch('https://mulroystreetcap.com/api/positions')
      ])
      setAccount(await accRes.json())
      setPositions(await posRes.json())
      setLastUpdate(new Date())
    } catch (err) {
      console.error('Data fetch error:', err)
    }
  }
  
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])
  
  return (
    <div className="min-h-screen bg-[#0A0E1A] text-gray-100">
      <Components.Header />
      <main className="p-6">
        <Components.AccountCards account={account} />
        <Components.PortfolioChart />
        <div className="mb-6">
          <h2 className="text-sm text-gray-400 uppercase tracking-wide mb-3">Live Market Data</h2>
          <Components.MarketData />
        </div>
        <Components.PositionsTable positions={positions} />
      </main>
      <Components.StatusBar lastUpdate={lastUpdate} onRefresh={fetchData} />
    </div>
  )
}