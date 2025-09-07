'use client'
import { BarChart3, TrendingUp } from 'lucide-react'

interface PortfolioChartProps {
  data?: any[]
}

export default function PortfolioChart({ data = [] }: PortfolioChartProps) {
  // Sample chart visualization (placeholder)
  const chartBars = [
    { label: 'Mon', value: 85 },
    { label: 'Tue', value: 92 },
    { label: 'Wed', value: 78 },
    { label: 'Thu', value: 96 },
    { label: 'Fri', value: 89 },
  ]

  return (
    <div className="bg-[#141824] border border-gray-700 rounded p-4 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-orange-500" />
          <h2 className="text-lg font-semibold text-white">Portfolio Performance</h2>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <TrendingUp className="w-4 h-4 text-green-400" />
          <span>5 Day View</span>
        </div>
      </div>

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

      <div className="text-xs text-gray-500 text-center mt-4">
        Portfolio performance visualization • 5-day historical view
      </div>
    </div>
  )
}