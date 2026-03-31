import { useState } from 'react';
import { MetricsCards } from './dashboard/MetricsCards';
import { GraphPanel } from './dashboard/GraphPanel';
import { TransactionStream } from './dashboard/TransactionStream';
import { ChannelFlow } from './dashboard/ChannelFlow';
import { AlertPanel } from './dashboard/AlertPanel';
import { EntityDrawer } from './dashboard/EntityDrawer';
import { Account } from '../types';
import { useTheme } from '../contexts/ThemeContext';

export function DashboardView() {
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className="space-y-8 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            Real-Time Detection Dashboard
          </h2>
          <p className={`mt-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Cross-channel mule account monitoring powered by GNN
          </p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/10 border border-green-500/20">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-green-400 text-sm font-medium">Live Monitoring Active</span>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="relative">
        <MetricsCards />
      </div>

      {/* Graph and Live Transactions Section */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 isolate">
        <div className="xl:col-span-2">
          <GraphPanel onNodeClick={setSelectedAccount} />
        </div>
        <div className="h-full">
          <TransactionStream />
        </div>
      </div>

      {/* Channel Flow and Alerts Section */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 isolate">
        <div>
          <ChannelFlow />
        </div>
        <div>
          <AlertPanel />
        </div>
      </div>

      {selectedAccount && (
        <EntityDrawer
          account={selectedAccount}
          open={!!selectedAccount}
          onClose={() => setSelectedAccount(null)}
        />
      )}
    </div>
  );
}