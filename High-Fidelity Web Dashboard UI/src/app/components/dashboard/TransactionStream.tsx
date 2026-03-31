import { useEffect, useState } from 'react';
import { ArrowRight, Circle } from 'lucide-react';
import { mockTransactions } from '../../mockData';
import { Transaction } from '../../types';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { motion, AnimatePresence } from 'motion/react';

export function TransactionStream() {
  const [transactions, setTransactions] = useState<Transaction[]>(mockTransactions.slice(0, 8));

  useEffect(() => {
    // Simulate real-time transaction updates
    const interval = setInterval(() => {
      const newTxn: Transaction = {
        id: `TXN${Date.now()}`,
        fromAccount: `ACC${Math.floor(Math.random() * 15) + 1}`.padStart(6, '0'),
        toAccount: `ACC${Math.floor(Math.random() * 15) + 1}`.padStart(6, '0'),
        amount: Math.floor(Math.random() * 50000) + 5000,
        channel: ['UPI', 'ATM', 'Wallet', 'App', 'Web'][Math.floor(Math.random() * 5)] as any,
        timestamp: new Date(),
        riskScore: Math.floor(Math.random() * 100),
        status: Math.random() > 0.7 ? 'flagged' : 'completed',
      };

      setTransactions(prev => [newTxn, ...prev.slice(0, 9)]);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getChannelColor = (channel: string) => {
    const colors: Record<string, string> = {
      UPI: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      ATM: 'bg-green-500/10 text-green-400 border-green-500/20',
      Wallet: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      App: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
      Web: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    };
    return colors[channel] || 'bg-slate-500/10 text-slate-400';
  };

  const getRiskBadge = (score: number) => {
    if (score > 80) return { label: 'Critical', color: 'bg-red-500' };
    if (score > 60) return { label: 'High', color: 'bg-orange-500' };
    if (score > 40) return { label: 'Medium', color: 'bg-yellow-500' };
    return { label: 'Low', color: 'bg-green-500' };
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-slate-900/50 backdrop-blur-xl rounded-xl border-2 border-slate-700/50 h-[500px] flex flex-col shadow-xl"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
        <div>
          <h3 className="text-lg font-semibold text-white">Live Transaction Stream</h3>
          <p className="text-sm text-slate-400">Real-time monitoring</p>
        </div>
        <div className="flex items-center gap-2">
          <Circle className="w-2 h-2 text-green-400 fill-green-400 animate-pulse" />
          <span className="text-xs text-green-400">Live</span>
        </div>
      </div>

      {/* Transaction list */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-3">
          <AnimatePresence>
            {transactions.map((txn, index) => {
              const risk = getRiskBadge(txn.riskScore);
              
              return (
                <motion.div
                  key={txn.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  className={`p-3 rounded-lg border transition-all hover:border-cyan-500/30 ${
                    txn.status === 'flagged'
                      ? 'bg-red-500/5 border-red-500/20'
                      : 'bg-slate-800/30 border-slate-700/50'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500">
                        {txn.timestamp.toLocaleTimeString()}
                      </span>
                      <Badge className={`text-xs px-2 py-0 ${getChannelColor(txn.channel)}`}>
                        {txn.channel}
                      </Badge>
                    </div>
                    <div className={`px-2 py-0.5 rounded text-xs font-medium ${risk.color} text-white`}>
                      {risk.label}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm text-slate-300 font-mono">{txn.fromAccount}</span>
                    <ArrowRight className="w-4 h-4 text-slate-500" />
                    <span className="text-sm text-slate-300 font-mono">{txn.toAccount}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-lg font-semibold text-white">
                      ₹{txn.amount.toLocaleString()}
                    </span>
                    <span className="text-xs text-slate-500">
                      Risk: {txn.riskScore}%
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </ScrollArea>
    </motion.div>
  );
}