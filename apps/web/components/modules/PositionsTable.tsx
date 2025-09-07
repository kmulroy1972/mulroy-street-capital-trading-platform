'use client'

interface PositionsTableProps {
  positions: any[]
}

export default function PositionsTable({ positions }: PositionsTableProps) {
  if (!positions || positions.length === 0) return null

  return (
    <div className="bg-[#141824] border border-gray-700 rounded p-4 mb-6">
      <h2 className="text-sm text-gray-400 uppercase tracking-wide mb-3">Current Positions</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left py-2 text-gray-400">Symbol</th>
              <th className="text-right py-2 text-gray-400">Qty</th>
              <th className="text-right py-2 text-gray-400">Current</th>
              <th className="text-right py-2 text-gray-400">Value</th>
              <th className="text-right py-2 text-gray-400">P&L</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((pos: any) => (
              <tr key={pos.symbol} className="border-b border-gray-800">
                <td className="py-2 font-mono">{pos.symbol}</td>
                <td className="text-right py-2 font-mono">{pos.qty}</td>
                <td className="text-right py-2 font-mono">${pos.current_price?.toFixed(2)}</td>
                <td className="text-right py-2 font-mono">${pos.market_value?.toFixed(2)}</td>
                <td className={`text-right py-2 font-mono ${pos.unrealized_pl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${pos.unrealized_pl?.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}