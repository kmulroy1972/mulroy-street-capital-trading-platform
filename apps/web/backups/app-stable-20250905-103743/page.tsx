import { AccountOverview } from '@/components/dashboard/AccountOverview';
import { PositionsTable } from '@/components/dashboard/PositionsTable';
import { OrderEntry } from '@/components/dashboard/OrderEntry';
import { PerformanceChart } from '@/components/dashboard/PerformanceChart';

export default function DashboardPage() {
  return (
    <div className="p-6">
      <div className="grid grid-cols-12 gap-4">
        {/* Top Row */}
        <div className="col-span-4">
          <AccountOverview />
        </div>
        <div className="col-span-5">
          <PositionsTable />
        </div>
        <div className="col-span-3">
          <OrderEntry />
        </div>

        {/* Middle Row */}
        <div className="col-span-8">
          <PerformanceChart />
        </div>
        <div className="col-span-4">
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-text-primary mb-4">Top Movers</h2>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-text-secondary">NVDA</span>
                <span className="text-primary">+2.34%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-secondary">TSLA</span>
                <span className="text-danger">-1.87%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-secondary">AAPL</span>
                <span className="text-primary">+0.91%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Row */}
        <div className="col-span-4">
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-text-primary mb-4">Crypto Market</h2>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-text-secondary">BTC</span>
                <span className="text-primary">$43,521</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-secondary">ETH</span>
                <span className="text-primary">$2,398</span>
              </div>
            </div>
          </div>
        </div>
        <div className="col-span-4">
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-text-primary mb-4">Market Sectors</h2>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-text-secondary">Technology</span>
                <span className="text-primary">+1.23%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-secondary">Healthcare</span>
                <span className="text-danger">-0.45%</span>
              </div>
            </div>
          </div>
        </div>
        <div className="col-span-4">
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold text-text-primary mb-4">Watchlist</h2>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-text-secondary">SPY</span>
                <span className="text-primary">$421.34</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-secondary">QQQ</span>
                <span className="text-primary">$367.89</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
