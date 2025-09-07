'use client'
import React, { useEffect, useState } from 'react'
import { BarChart3, TrendingUp } from 'lucide-react'

interface PortfolioChartProps {
  data: any[]
}

export default function PortfolioChart({ data }: PortfolioChartProps) {
  const [accountData, setAccountData] = useState<any>(null)

  useEffect(() => {
    const fetchAccountData = async () => {
      try {
        const response = await fetch('https://mulroystreetcap.com/api/account')
        const account = await response.json()
        setAccountData(account)
      } catch (error) {
        console.error('Failed to fetch account data:', error)
      }
    }

    fetchAccountData()
    const interval = setInterval(fetchAccountData, 30000) // Update every 30 seconds
    
    return () => clearInterval(interval)
  }, [])

  // Sample chart visualization (placeholder)
  const chartBars = [
    { label: 'Mon', value: 85 },
    { label: 'Tue', value: 92 },
    { label: 'Wed', value: 78 },
    { label: 'Thu', value: 96 },
    { label: 'Fri', value: 89 },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-orange-500" />
          <h2 className="text-lg font-semibold text-white">Portfolio Performance</h2>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <TrendingUp className="w-4 h-4 text-green-400" />
          <span>5 Day View</span>
        </div>
      </div>

      {/* Account Summary */}
      {accountData && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center">
            <div className="text-xs text-gray-400 uppercase tracking-wide">Total Value</div>
            <div className="text-lg font-mono text-white">
              ${accountData.equity?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-400 uppercase tracking-wide">Cash</div>
            <div className="text-lg font-mono text-white">
              ${accountData.cash?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-400 uppercase tracking-wide">Day Trade Count</div>
            <div className="text-lg font-mono text-white">
              {accountData.daytrade_count || 0}/3
            </div>
          </div>
        </div>
      )}

      {/* Simple Bar Chart Placeholder */}
      <div className="h-48 flex items-end justify-between gap-2 bg-gray-900/50 rounded p-4">
        {chartBars.map((bar, index) => (
          <div key={bar.label} className="flex flex-col items-center flex-1">
            <div 
              className="bg-orange-500/20 border-t-2 border-orange-500 rounded-t w-full transition-all duration-300"
              style={{ height: `${bar.value}%` }}
            />
            <div className="text-xs text-gray-400 mt-2">{bar.label}</div>
          </div>
        ))}
      </div>

      {/* Chart Info */}
      <div className="text-xs text-gray-500 text-center">
        Live portfolio data • Updates every 30 seconds
      </div>
    </div>
  )
}