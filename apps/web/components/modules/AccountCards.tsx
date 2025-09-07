'use client'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface AccountCardsProps {
  account: any
}

export default function AccountCards({ account }: AccountCardsProps) {
  if (!account) return null

  const dailyPL = (account?.equity || 0) - (account?.last_equity || 0)
  const dailyPLPercent = account?.last_equity ? (dailyPL / account.last_equity) * 100 : 0

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-[#141824] border border-gray-700 rounded p-4">
        <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">Portfolio Value</div>
        <div className="text-2xl font-bold font-mono">
          ${account?.equity?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
        </div>
        <div className={`text-sm font-mono mt-1 flex items-center gap-1 ${dailyPL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {dailyPL >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {dailyPL >= 0 ? '+' : ''}{dailyPL.toFixed(2)} ({dailyPLPercent >= 0 ? '+' : ''}{dailyPLPercent.toFixed(2)}%)
        </div>
      </div>
      
      <div className="bg-[#141824] border border-gray-700 rounded p-4">
        <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">Cash Available</div>
        <div className="text-2xl font-bold font-mono">
          ${account?.cash?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
        </div>
      </div>
      
      <div className="bg-[#141824] border border-gray-700 rounded p-4">
        <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">Buying Power</div>
        <div className="text-2xl font-bold font-mono">
          ${account?.buying_power?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
        </div>
      </div>
      
      <div className="bg-[#141824] border border-gray-700 rounded p-4">
        <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">Day Trades</div>
        <div className="text-2xl font-bold font-mono">
          {account?.daytrade_count || 0}/3
        </div>
        <div className="text-xs text-gray-500 mt-1">
          PDT Status
        </div>
      </div>
    </div>
  )
}