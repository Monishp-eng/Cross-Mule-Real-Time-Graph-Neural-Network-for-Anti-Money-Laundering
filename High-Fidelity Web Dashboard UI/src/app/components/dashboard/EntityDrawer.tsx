import { X, TrendingUp, Activity, Link2, CreditCard } from 'lucide-react';
import { Account } from '../../types';
import { mockTransactions } from '../../mockData';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import { motion, AnimatePresence } from 'motion/react';

interface EntityDrawerProps {
  account: Account | null;
  open: boolean;
  onClose: () => void;
}

export function EntityDrawer({ account, open, onClose }: EntityDrawerProps) {
  if (!account) return null;

  const relatedTransactions = mockTransactions.filter(
    txn => txn.fromAccount === account.id || txn.toAccount === account.id
  );

  const riskHistory = [
    { day: 'Mon', score: account.riskScore - 15 },
    { day: 'Tue', score: account.riskScore - 10 },
    { day: 'Wed', score: account.riskScore - 5 },
    { day: 'Thu', score: account.riskScore },
    { day: 'Fri', score: account.riskScore + 3 },
    { day: 'Sat', score: account.riskScore + 2 },
    { day: 'Sun', score: account.riskScore },
  ];

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 bottom-0 w-[480px] bg-slate-900/95 backdrop-blur-xl border-l border-cyan-500/20 shadow-2xl z-50"
          >
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-slate-700/50">
                <div>
                  <h2 className="text-xl font-bold text-white">Entity Details</h2>
                  <p className="text-sm text-slate-400">Account analysis and connections</p>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-slate-800/50 text-slate-400 hover:text-white transition-all"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <ScrollArea className="flex-1">
                <div className="p-6 space-y-6">
                  {/* Account Info */}
                  <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-white">{account.name}</h3>
                        <p className="text-sm text-slate-400 font-mono">{account.id}</p>
                      </div>
                      <Badge
                        className={
                          account.riskScore > 80
                            ? 'bg-red-500/10 text-red-400 border-red-500/20'
                            : account.riskScore > 60
                            ? 'bg-orange-500/10 text-orange-400 border-orange-500/20'
                            : 'bg-green-500/10 text-green-400 border-green-500/20'
                        }
                      >
                        {account.type}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Risk Score</p>
                        <div className="flex items-end gap-2">
                          <p className="text-2xl font-bold text-white">{account.riskScore}</p>
                          <TrendingUp className="w-4 h-4 text-red-400 mb-1" />
                        </div>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Balance</p>
                        <p className="text-xl font-semibold text-white">
                          ₹{account.balance.toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Risk Score Trend */}
                  <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                    <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-red-400" />
                      Risk Score Trend
                    </h4>
                    <div className="h-32 min-h-[128px]">
                      <ResponsiveContainer width="100%" height="100%" minHeight={128}>
                        <LineChart data={riskHistory}>
                          <XAxis dataKey="day" stroke="#64748b" fontSize={12} />
                          <YAxis stroke="#64748b" fontSize={12} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: '#1e293b',
                              border: '1px solid #334155',
                              borderRadius: '8px',
                            }}
                          />
                          <Line
                            type="monotone"
                            dataKey="score"
                            stroke="#ef4444"
                            strokeWidth={2}
                            dot={{ fill: '#ef4444', r: 4 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Channels Used */}
                  <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                    <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                      <CreditCard className="w-4 h-4 text-cyan-400" />
                      Active Channels
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {account.channels.map(channel => (
                        <Badge
                          key={channel}
                          className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                        >
                          {channel}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Cluster Info */}
                  {account.clusterId && (
                    <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                      <h4 className="text-sm font-semibold text-red-400 mb-2 flex items-center gap-2">
                        <Link2 className="w-4 h-4" />
                        Cluster Association
                      </h4>
                      <p className="text-sm text-slate-300">
                        Part of suspicious cluster: <span className="font-mono font-semibold">{account.clusterId}</span>
                      </p>
                    </div>
                  )}

                  {/* Transaction History */}
                  <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                    <h4 className="text-sm font-semibold text-white mb-3">Recent Transactions</h4>
                    <div className="space-y-3">
                      {relatedTransactions.slice(0, 5).map(txn => (
                        <div
                          key={txn.id}
                          className="p-3 rounded-lg bg-slate-900/50 border border-slate-700/30"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-slate-400">
                              {txn.timestamp.toLocaleTimeString()}
                            </span>
                            <Badge className="text-xs bg-purple-500/10 text-purple-400 border-purple-500/20">
                              {txn.channel}
                            </Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-semibold text-white">
                              ₹{txn.amount.toLocaleString()}
                            </span>
                            <span className="text-xs text-slate-500">
                              Risk: {txn.riskScore}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Connected Accounts */}
                  <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                    <h4 className="text-sm font-semibold text-white mb-3">Linked Accounts</h4>
                    <div className="space-y-2">
                      {relatedTransactions
                        .slice(0, 4)
                        .map(txn => txn.fromAccount === account.id ? txn.toAccount : txn.fromAccount)
                        .filter((v, i, a) => a.indexOf(v) === i)
                        .map(linkedId => (
                          <div
                            key={linkedId}
                            className="flex items-center justify-between p-2 rounded bg-slate-900/50"
                          >
                            <span className="text-sm text-slate-300 font-mono">{linkedId}</span>
                            <Link2 className="w-4 h-4 text-cyan-400" />
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}