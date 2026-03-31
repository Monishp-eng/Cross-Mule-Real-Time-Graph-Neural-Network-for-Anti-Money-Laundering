import { useState } from 'react';
import { GraphPanel } from './dashboard/GraphPanel';
import { EntityDrawer } from './dashboard/EntityDrawer';
import { Account } from '../types';
import { Slider } from './ui/slider';
import { Badge } from './ui/badge';
import { Filter } from 'lucide-react';

export function GraphView() {
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [timeWindow, setTimeWindow] = useState([7]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white">Entity Graph Analysis</h2>
          <p className="text-slate-400 mt-1">Interactive network visualization of account relationships</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-cyan-400" />
          <h3 className="font-semibold text-white">Filters</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="text-sm text-slate-400 mb-2 block">Channel</label>
            <div className="flex flex-wrap gap-2">
              {['UPI', 'ATM', 'Wallet', 'App', 'Web'].map(channel => (
                <Badge
                  key={channel}
                  className="cursor-pointer bg-cyan-500/10 text-cyan-400 border-cyan-500/20 hover:bg-cyan-500/20"
                >
                  {channel}
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm text-slate-400 mb-2 block">Risk Level</label>
            <div className="flex flex-wrap gap-2">
              {['High', 'Medium', 'Low'].map(risk => (
                <Badge
                  key={risk}
                  className={`cursor-pointer ${
                    risk === 'High' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                    risk === 'Medium' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                    'bg-green-500/10 text-green-400 border-green-500/20'
                  } hover:opacity-80`}
                >
                  {risk}
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm text-slate-400 mb-2 block">
              Time Window: {timeWindow[0]} days
            </label>
            <Slider
              value={timeWindow}
              onValueChange={setTimeWindow}
              min={1}
              max={30}
              step={1}
              className="mt-2"
            />
          </div>
        </div>
      </div>

      {/* Graph */}
      <GraphPanel onNodeClick={setSelectedAccount} />

      {/* Entity drawer */}
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
