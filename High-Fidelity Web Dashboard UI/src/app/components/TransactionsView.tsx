import { useState } from 'react';
import { ArrowRight, Search, Filter, Download, Shield, Activity, AlertTriangle } from 'lucide-react';
import { mockTransactions } from '../mockData';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table';

export function TransactionsView() {
  const [searchQuery, setSearchQuery] = useState('');

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

  const getRiskColor = (score: number) => {
    if (score > 80) return 'text-red-400';
    if (score > 60) return 'text-orange-400';
    if (score > 40) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getPatternColor = (pattern?: string) => {
    const colors: Record<string, string> = {
      structuring: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      fragmentation: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
      nesting: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
      'rapid-movement': 'bg-red-500/10 text-red-400 border-red-500/20',
    };
    return pattern ? colors[pattern] : '';
  };

  const getPatternLabel = (pattern?: string) => {
    const labels: Record<string, string> = {
      structuring: 'Structuring',
      fragmentation: 'Fragmentation',
      nesting: 'Nesting',
      'rapid-movement': 'Rapid Movement',
    };
    return pattern ? labels[pattern] : '';
  };

  const getComplexityColor = (complexity?: number) => {
    if (!complexity) return 'text-slate-400';
    if (complexity >= 5) return 'text-red-400';
    if (complexity >= 3) return 'text-orange-400';
    return 'text-green-400';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white">Transaction Monitor</h2>
          <p className="text-slate-400 mt-1">Real-time cross-channel transaction analysis with pattern detection</p>
        </div>
        <Button className="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20">
          <Download className="w-4 h-4 mr-2" />
          Export Data
        </Button>
      </div>

      {/* Search and Filters */}
      <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6">
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
            <Input
              type="text"
              placeholder="Search by account ID, transaction ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-slate-800/50 border-slate-700 text-white"
            />
          </div>
          <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6">
          <p className="text-sm text-slate-400 mb-1">Total Transactions</p>
          <p className="text-3xl font-bold text-white">{mockTransactions.length}</p>
        </div>
        <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6">
          <p className="text-sm text-slate-400 mb-1">Flagged</p>
          <p className="text-3xl font-bold text-red-400">
            {mockTransactions.filter(t => t.status === 'flagged').length}
          </p>
        </div>
        <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6">
          <p className="text-sm text-slate-400 mb-1">Total Volume</p>
          <p className="text-3xl font-bold text-cyan-400">
            ₹{mockTransactions.reduce((acc, t) => acc + t.amount, 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6">
          <p className="text-sm text-slate-400 mb-1">Avg Risk Score</p>
          <p className="text-3xl font-bold text-orange-400">
            {Math.round(mockTransactions.reduce((acc, t) => acc + t.riskScore, 0) / mockTransactions.length)}
          </p>
        </div>
        <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6">
          <p className="text-sm text-slate-400 mb-1 flex items-center gap-1">
            <Shield className="w-4 h-4" />
            Sanctions Flags
          </p>
          <p className="text-3xl font-bold text-red-400">
            {mockTransactions.filter(t => t.sanctionsFlag).length}
          </p>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-700/50 hover:bg-slate-800/30">
              <TableHead className="text-slate-300">Transaction ID</TableHead>
              <TableHead className="text-slate-300">From</TableHead>
              <TableHead className="text-slate-300">To</TableHead>
              <TableHead className="text-slate-300">Amount</TableHead>
              <TableHead className="text-slate-300">Channel</TableHead>
              <TableHead className="text-slate-300">Pattern</TableHead>
              <TableHead className="text-slate-300">Complexity</TableHead>
              <TableHead className="text-slate-300">Risk Score</TableHead>
              <TableHead className="text-slate-300">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {mockTransactions.map((txn) => (
              <TableRow
                key={txn.id}
                className={`border-slate-700/50 hover:bg-slate-800/30 ${
                  txn.status === 'flagged' ? 'bg-red-500/5' : ''
                }`}
              >
                <TableCell className="font-mono text-slate-300">
                  <div className="flex items-center gap-2">
                    {txn.id}
                    {txn.sanctionsFlag && (
                      <Shield className="w-4 h-4 text-red-400" title="Sanctions Alert" />
                    )}
                  </div>
                </TableCell>
                <TableCell className="font-mono text-slate-400">{txn.fromAccount}</TableCell>
                <TableCell className="font-mono text-slate-400">{txn.toAccount}</TableCell>
                <TableCell className="text-white font-semibold">
                  ₹{txn.amount.toLocaleString()}
                </TableCell>
                <TableCell>
                  <Badge className={getChannelColor(txn.channel)}>
                    {txn.channel}
                  </Badge>
                </TableCell>
                <TableCell>
                  {txn.pattern ? (
                    <Badge className={getPatternColor(txn.pattern)}>
                      <Activity className="w-3 h-3 mr-1" />
                      {getPatternLabel(txn.pattern)}
                    </Badge>
                  ) : (
                    <span className="text-slate-500 text-sm">-</span>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold ${getComplexityColor(txn.complexity)}`}>
                      {txn.complexity || '-'}
                    </span>
                    {txn.complexity && txn.complexity >= 5 && (
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <span className={`font-semibold ${getRiskColor(txn.riskScore)}`}>
                    {txn.riskScore}%
                  </span>
                </TableCell>
                <TableCell>
                  <Badge
                    className={
                      txn.status === 'flagged'
                        ? 'bg-red-500/10 text-red-400 border-red-500/20'
                        : txn.status === 'pending'
                        ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                        : 'bg-green-500/10 text-green-400 border-green-500/20'
                    }
                  >
                    {txn.status}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pattern Legend */}
      <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Pattern Detection Legend</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="flex items-center gap-3">
            <Badge className="bg-purple-500/10 text-purple-400 border-purple-500/20">
              <Activity className="w-3 h-3 mr-1" />
              Structuring
            </Badge>
            <span className="text-sm text-slate-400">Breaking large amounts into smaller transactions</span>
          </div>
          <div className="flex items-center gap-3">
            <Badge className="bg-orange-500/10 text-orange-400 border-orange-500/20">
              <Activity className="w-3 h-3 mr-1" />
              Fragmentation
            </Badge>
            <span className="text-sm text-slate-400">Splitting funds across multiple accounts</span>
          </div>
          <div className="flex items-center gap-3">
            <Badge className="bg-pink-500/10 text-pink-400 border-pink-500/20">
              <Activity className="w-3 h-3 mr-1" />
              Nesting
            </Badge>
            <span className="text-sm text-slate-400">Layered transactions through intermediaries</span>
          </div>
          <div className="flex items-center gap-3">
            <Badge className="bg-red-500/10 text-red-400 border-red-500/20">
              <Activity className="w-3 h-3 mr-1" />
              Rapid Movement
            </Badge>
            <span className="text-sm text-slate-400">High-velocity fund transfers</span>
          </div>
        </div>
      </div>
    </div>
  );
}