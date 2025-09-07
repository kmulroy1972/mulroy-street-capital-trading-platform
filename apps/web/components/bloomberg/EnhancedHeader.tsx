'use client'
import React, { useEffect, useState } from 'react'
import { Cloud, CloudRain, Sun, Clock, Activity } from 'lucide-react'

interface WeatherData {
  temp_f: string
  description: string
  humidity: string
}

interface MarketTime {
  time: string
  is_market_hours: boolean
}

export default function EnhancedHeader() {
  const [dcWeather, setDcWeather] = useState<WeatherData | null>(null)
  const [asburyWeather, setAsburyWeather] = useState<WeatherData | null>(null)
  const [marketTimes, setMarketTimes] = useState<Record<string, MarketTime>>({})
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch weather
        const [dc, asbury, times] = await Promise.all([
          fetch('https://mulroystreetcap.com/api/weather/dc').then(r => r.json()),
          fetch('https://mulroystreetcap.com/api/weather/asbury').then(r => r.json()),
          fetch('https://mulroystreetcap.com/api/market-times').then(r => r.json())
        ])
        
        setDcWeather(dc)
        setAsburyWeather(asbury)
        setMarketTimes(times)
      } catch (error) {
        console.error('Failed to fetch header data:', error)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 300000) // Update every 5 minutes
    
    // Update current time every second
    const timeInterval = setInterval(() => setCurrentTime(new Date()), 1000)
    
    return () => {
      clearInterval(interval)
      clearInterval(timeInterval)
    }
  }, [])

  const getWeatherIcon = (description: string) => {
    const desc = description?.toLowerCase() || ''
    if (desc.includes('rain')) return <CloudRain className="w-4 h-4" />
    if (desc.includes('cloud')) return <Cloud className="w-4 h-4" />
    return <Sun className="w-4 h-4" />
  }

  return (
    <div className="bg-gray-900 border-b border-gray-700 px-4 py-2">
      <div className="flex justify-between items-center">
        {/* Left: Logo and Status */}
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-orange-500">MULROY STREET CAPITAL</h1>
          <div className="flex items-center gap-1 text-green-500">
            <Activity className="w-4 h-4" />
            <span className="text-sm">LIVE</span>
          </div>
        </div>

        {/* Center: Market Times */}
        <div className="flex items-center gap-6">
          {Object.entries(marketTimes).map(([city, data]) => (
            <div key={city} className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-gray-400" />
              <span className="text-xs text-gray-300">{city}</span>
              <span className={`text-xs font-mono ${data.is_market_hours ? 'text-green-400' : 'text-gray-500'}`}>
                {data.time}
              </span>
              {data.is_market_hours && (
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              )}
            </div>
          ))}
        </div>

        {/* Right: Weather and Time */}
        <div className="flex items-center gap-6">
          {/* DC Weather */}
          {dcWeather && (
            <div className="flex items-center gap-1">
              {getWeatherIcon(dcWeather.description)}
              <span className="text-xs text-gray-300">DC</span>
              <span className="text-xs text-white">{dcWeather.temp_f}°F</span>
            </div>
          )}

          {/* Asbury Weather */}
          {asburyWeather && (
            <div className="flex items-center gap-1">
              {getWeatherIcon(asburyWeather.description)}
              <span className="text-xs text-gray-300">ASB</span>
              <span className="text-xs text-white">{asburyWeather.temp_f}°F</span>
            </div>
          )}

          {/* Current Time */}
          <div className="text-sm text-gray-300 font-mono">
            {currentTime.toLocaleTimeString('en-US', { 
              hour12: false,
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit'
            })}
          </div>
        </div>
      </div>
    </div>
  )
}