'use client'
import React, { useEffect, useState } from 'react'
import { Activity, RefreshCw } from 'lucide-react'

interface MarketData {
  price: number
  bid: number
  ask: number
  timestamp: string
}

export default function MarketDataGrid() {
  const [marketData, setMarketData] = useState<Record<string, MarketData>>({})
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  const fetchMarketData = async () => {
    try {
      const response = await fetch('https://mulroystreetcap.com/api/market-data')
      const data = await response.json()
      setMarketData(data)
      setLastUpdate(new Date())
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch market data:', error)
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMarketData()
    const interval = setInterval(fetchMarketData, 15000) // Update every 15 seconds
    
    return () => clearInterval(interval)
  }, [])

  const symbols = ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI']

  if (loading) {
    return (
      <div className="bg-[#141824] border border-gray-700 rounded p-6 flex items-center justify-center">
        <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />
        <span className="ml-2 text-gray-400">Loading market data...</span>
      </div>
    )
  }

  return (
    <div className="bg-[#141824] border border-gray-700 rounded p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-orange-500" />
          <h3 className="text-lg font-semibold text-white">Major ETFs</h3>
        </div>
        <div className="text-xs text-gray-400">
          Last update: {lastUpdate?.toLocaleTimeString() || 'Never'}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left py-2 text-gray-400 font-medium">Symbol</th>
              <th className="text-right py-2 text-gray-400 font-medium">Price</th>
              <th className="text-right py-2 text-gray-400 font-medium">Bid</th>
              <th className="text-right py-2 text-gray-400 font-medium">Ask</th>
              <th className="text-right py-2 text-gray-400 font-medium">Spread</th>
              <th className="text-right py-2 text-gray-400 font-medium">Time</th>
            </tr>
          </thead>
          <tbody>
            {symbols.map((symbol) => {
              const data = marketData[symbol]
              const spread = data ? (data.ask - data.bid).toFixed(2) : '0.00'
              const timestamp = data?.timestamp ? new Date(data.timestamp).toLocaleTimeString() : 'N/A'
              
              return (
                <tr key={symbol} className="border-b border-gray-800 hover:bg-gray-800/30">
                  <td className="py-3 font-mono font-semibold text-white">{symbol}</td>
                  <td className="text-right py-3 font-mono text-white">
                    ${data?.price?.toFixed(2) || '0.00'}
                  </td>
                  <td className="text-right py-3 font-mono text-gray-300">
                    ${data?.bid?.toFixed(2) || '0.00'}
                  </td>
                  <td className="text-right py-3 font-mono text-gray-300">
                    ${data?.ask?.toFixed(2) || '0.00'}
                  </td>
                  <td className="text-right py-3 font-mono text-gray-400">
                    ${spread}
                  </td>
                  <td className="text-right py-3 text-xs text-gray-500">
                    {timestamp}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* ETF Descriptions */}
      <div className="mt-4 text-xs text-gray-500 space-y-1">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          <div><span className="font-mono">SPY</span> - S&P 500</div>
          <div><span className="font-mono">QQQ</span> - Nasdaq 100</div>
          <div><span className="font-mono">DIA</span> - Dow Jones</div>
          <div><span className="font-mono">IWM</span> - Russell 2000</div>
          <div><span className="font-mono">VTI</span> - Total Stock Market</div>
        </div>
      </div>

      <button 
        onClick={fetchMarketData}
        className="mt-4 text-xs text-gray-400 hover:text-white flex items-center gap-1"
      >
        <RefreshCw className="w-3 h-3" /> Refresh Data
      </button>
    </div>
  )
}