'use client'
import { useEffect, useState } from 'react'

export default function MarketData() {
  const [data, setData] = useState<any>({})
  const [error, setError] = useState<string>('')
  
  useEffect(() => {
    // First try the API endpoint
    fetch('https://mulroystreetcap.com/api/market-data')
      .then(res => res.json())
      .then(setData)
      .catch(err => {
        console.error('Market data error:', err)
        setError('Market data unavailable')
        // Fallback to mock data for now
        setData({
          SPY: { price: 644.16, change: 1.2 },
          QQQ: { price: 572.23, change: -0.8 },
          DIA: { price: 431.56, change: 0.5 }
        })
      })
  }, [])
  
  if (error) {
    return <div className="text-red-500 text-sm">{error}</div>
  }
  
  return (
    <div className="grid grid-cols-3 md:grid-cols-5 gap-4">
      {Object.entries(data).map(([symbol, info]: any) => (
        <div key={symbol} className="bg-gray-800 p-3 rounded">
          <div className="text-xs text-gray-400">{symbol}</div>
          <div className="text-lg font-bold">${info?.price?.toFixed(2) || '—'}</div>
          <div className={`text-xs ${info?.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {info?.change >= 0 ? '▲' : '▼'} {Math.abs(info?.change || 0).toFixed(2)}%
          </div>
        </div>
      ))}
    </div>
  )
}