'use client'
import { RefreshCw } from 'lucide-react'

interface StatusBarProps {
  lastUpdate?: Date
  onRefresh?: () => void
}

export default function StatusBar({ lastUpdate, onRefresh }: StatusBarProps) {
  return (
    <div className="text-center text-xs text-gray-500 py-4 border-t border-gray-800 bg-[#0A0E1A]">
      Last Update: {lastUpdate?.toLocaleTimeString() || 'Never'} | 
      <button 
        onClick={onRefresh} 
        className="ml-2 hover:text-white inline-flex items-center gap-1 transition-colors"
      >
        <RefreshCw className="w-3 h-3" /> Refresh
      </button>
    </div>
  )
}