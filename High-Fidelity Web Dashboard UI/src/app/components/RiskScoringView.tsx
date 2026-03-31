import { useState } from 'react';
import { mockAccounts } from '../mockData';
import { TrendingUp, TrendingDown, Shield, AlertTriangle, Globe, Users } from 'lucide-react';
import { Badge } from './ui/badge';
import { Card } from './ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export function RiskScoringView() {
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'high' | 'suspicious' | 'normal'>('all');

  const filteredAccounts = mockAccounts.filter(account => {
    if (selectedFilter === 'all') return true;
    if (selectedFilter === 'high') return account.riskScore > 80;
    if (selectedFilter === 'suspicious') return account.riskScore > 60 && account.riskScore <= 80;
    if (selectedFilter === 'normal') return account.riskScore <= 60;
    return true;
  });

  const riskDistribution = [
    { 
      range: '0-20', 
      count: mockAccounts.filter(a => a.riskScore <= 20).length,
      severity: 'Low'
    },
    { 
      range: '21-40', 
      count: mockAccounts.filter(a => a.riskScore > 20 && a.riskScore <= 40).length,
      severity: 'Low'
    },
    { 
      range: '41-60', 
      count: mockAccounts.filter(a => a.riskScore > 40 && a.riskScore <= 60).length,
      severity: 'Medium'
    },
    { 
      range: '61-80', 
      count: mockAccounts.filter(a => a.riskScore > 60 && a.riskScore <= 80).length,
      severity: 'High'
    },
    { 
      range: '81-100', 
      count: mockAccounts.filter(a => a.riskScore > 80).length,
      severity: 'Critical'
    },
  ];

  // Jurisdiction-based risk analysis
  const jurisdictionRisks = mockAccounts.reduce((acc, account) => {
    const jurisdiction = account.jurisdiction || 'Unknown';
    if (!acc[jurisdiction]) {
      acc[jurisdiction] = { count: 0, totalRisk: 0, highRisk: 0 };
    }
    acc[jurisdiction].count++;
    acc[jurisdiction].totalRisk += account.riskScore;
    if (account.riskScore > 80) acc[jurisdiction].highRisk++;
    return acc;
  }, {} as Record<string, { count: number; totalRisk: number; highRisk: number }>);

  const jurisdictionData = Object.entries(jurisdictionRisks).map(([jurisdiction, data]) => ({
    jurisdiction,
    avgRisk: Math.round(data.totalRisk / data.count),
    accounts: data.count,
    highRisk: data.highRisk,
  })).sort((a, b) => b.avgRisk - a.avgRisk);

  // Ownership correlation
  const ownershipGroups = mockAccounts.reduce((acc, account) => {
    const owner = account.owner || 'Unknown';
    if (!acc[owner]) {
      acc[owner] = [];
    }
    acc[owner].push(account);
    return acc;
  }, {} as Record<string, typeof mockAccounts>);

  const suspiciousOwners = Object.entries(ownershipGroups)
    .filter(([owner, accounts]) => accounts.length > 1 && accounts.some(a => a.riskScore > 70))
    .map(([owner, accounts]) => ({
      owner,
      accountCount: accounts.length,
      avgRisk: Math.round(accounts.reduce((sum, acc) => sum + acc.riskScore, 0) / accounts.length),
      totalBalance: accounts.reduce((sum, acc) => sum + acc.balance, 0),
      jurisdictions: [...new Set(accounts.map(a => a.jurisdiction))],
    }))
    .sort((a, b) => b.avgRisk - a.avgRisk);

  const getRiskColor = (score: number) => {
    if (score > 80) return 'text-red-400 bg-red-500/10 border-red-500/20';
    if (score > 60) return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
    if (score > 40) return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
    return 'text-green-400 bg-green-500/10 border-green-500/20';
  };

  const getRiskLabel = (score: number) => {
    if (score > 80) return 'Critical';
    if (score > 60) return 'High';
    if (score > 40) return 'Medium';
    return 'Low';
  };

  const avgRiskScore = Math.round(
    mockAccounts.reduce((sum, acc) => sum + acc.riskScore, 0) / mockAccounts.length
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-white">Risk Scoring Dashboard</h2>
        <p className="text-slate-400 mt-1">GNN-powered risk assessment with jurisdiction analysis and ownership correlation</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-slate-900/50 backdrop-blur-xl border-slate-700/50 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/20">
              <AlertTriangle className="w-5 h-5 text-red-400" />
            </div>
            <p className="text-sm text-slate-400">Critical Risk</p>
          </div>
          <p className="text-3xl font-bold text-red-400">
            {mockAccounts.filter(a => a.riskScore > 80).length}
          </p>
          <p className="text-xs text-slate-500 mt-1">Score &gt; 80</p>
        </Card>

        <Card className="bg-slate-900/50 backdrop-blur-xl border-slate-700/50 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-orange-500/10 border border-orange-500/20">
              <TrendingUp className="w-5 h-5 text-orange-400" />
            </div>
            <p className="text-sm text-slate-400">High Risk</p>
          </div>
          <p className="text-3xl font-bold text-orange-400">
            {mockAccounts.filter(a => a.riskScore > 60 && a.riskScore <= 80).length}
          </p>
          <p className="text-xs text-slate-500 mt-1">Score 61-80</p>
        </Card>

        <Card className="bg-slate-900/50 backdrop-blur-xl border-slate-700/50 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
              <Shield className="w-5 h-5 text-cyan-400" />
            </div>
            <p className="text-sm text-slate-400">Average Score</p>
          </div>
          <p className="text-3xl font-bold text-cyan-400">{avgRiskScore}</p>
          <p className="text-xs text-slate-500 mt-1">Across all accounts</p>
        </Card>

        <Card className="bg-slate-900/50 backdrop-blur-xl border-slate-700/50 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-green-500/10 border border-green-500/20">
              <TrendingDown className="w-5 h-5 text-green-400" />
            </div>
            <p className="text-sm text-slate-400">Low Risk</p>
          </div>
          <p className="text-3xl font-bold text-green-400">
            {mockAccounts.filter(a => a.riskScore <= 60).length}
          </p>
          <p className="text-xs text-slate-500 mt-1">Score ≤ 60</p>
        </Card>
      </div>

      {/* Jurisdiction-Based Risk Scoring */}
      <div className="bg-slate-900/50 backdrop-blur-xl rounded-xl border-2 border-slate-700/50 p-6 shadow-xl">
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-white mb-2 flex items-center gap-2">
            <Globe className="w-5 h-5 text-cyan-400" />
            Jurisdiction-Based Risk Analysis
          </h3>
          <p className="text-sm text-slate-400">Cross-border risk assessment and geographical threat mapping</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {jurisdictionData.map((jd) => (
            <div key={jd.jurisdiction} className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-slate-400" />
                  <h4 className="font-semibold text-white">{jd.jurisdiction}</h4>
                </div>
                <Badge className={getRiskColor(jd.avgRisk)}>
                  {jd.avgRisk}
                </Badge>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Accounts</span>
                  <span className="text-white font-semibold">{jd.accounts}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">High Risk</span>
                  <span className="text-red-400 font-semibold">{jd.highRisk}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Avg Risk Score</span>
                  <span className={`font-semibold ${
                    jd.avgRisk > 80 ? 'text-red-400' :
                    jd.avgRisk > 60 ? 'text-orange-400' :
                    jd.avgRisk > 40 ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>{jd.avgRisk}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Ownership Correlation */}
      <div className="bg-slate-900/50 backdrop-blur-xl rounded-xl border-2 border-slate-700/50 p-6 shadow-xl">
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-white mb-2 flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-400" />
            Ownership Correlation Analysis
          </h3>
          <p className="text-sm text-slate-400">Identify suspicious patterns through linked account ownership</p>
        </div>

        <div className="space-y-4">
          {suspiciousOwners.map((owner) => (
            <div key={owner.owner} className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-5 hover:border-purple-500/30 transition-all">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h4 className="font-semibold text-white mb-1">{owner.owner}</h4>
                  <p className="text-sm text-slate-400">{owner.accountCount} linked accounts</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge className={getRiskColor(owner.avgRisk) + ' border px-3 py-1'}>
                    Avg Risk: {owner.avgRisk}
                  </Badge>
                  {owner.avgRisk > 80 && (
                    <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
                      <AlertTriangle className="w-3 h-3 mr-1" />
                      Critical
                    </Badge>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">Accounts</span>
                  <p className="text-lg font-semibold text-white mt-1">{owner.accountCount}</p>
                </div>
                <div>
                  <span className="text-slate-400">Total Balance</span>
                  <p className="text-lg font-semibold text-cyan-400 mt-1">₹{owner.totalBalance.toLocaleString()}</p>
                </div>
                <div>
                  <span className="text-slate-400">Jurisdictions</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {owner.jurisdictions.map((j, i) => (
                      <span key={i} className="text-xs px-2 py-0.5 rounded bg-slate-700/50 text-slate-300 border border-slate-600/50">
                        {j}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Filter Buttons */}
      <div className="flex gap-3">
        {(['all', 'high', 'suspicious', 'normal'] as const).map(filter => (
          <button
            key={filter}
            onClick={() => setSelectedFilter(filter)}
            className={`px-4 py-2 rounded-lg border transition-all ${
              selectedFilter === filter
                ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400'
                : 'bg-slate-800/30 border-slate-700/50 text-slate-400 hover:bg-slate-800/50'
            }`}
          >
            {filter.charAt(0).toUpperCase() + filter.slice(1)}
          </button>
        ))}
      </div>

      {/* Account List */}
      <div className="bg-slate-900/50 backdrop-blur-xl rounded-xl border-2 border-slate-700/50 p-6 shadow-xl">
        <h3 className="text-xl font-semibold text-white mb-4">Account Risk Scores</h3>
        
        <div className="space-y-3">
          {filteredAccounts.map((account) => (
            <div
              key={account.id}
              className="flex items-center justify-between p-4 rounded-lg bg-slate-800/30 border border-slate-700/50 hover:border-cyan-500/30 transition-all"
            >
              <div className="flex items-center gap-4">
                <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-slate-700/30 border border-slate-600/50">
                  <span className="text-sm font-semibold text-slate-300">
                    {account.id.slice(-3)}
                  </span>
                </div>
                
                <div>
                  <p className="font-semibold text-white">{account.name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-xs text-slate-400">{account.id}</p>
                    <div className="flex gap-1">
                      {account.channels.map((channel) => (
                        <Badge key={channel} className="text-xs px-2 py-0 bg-slate-700/50 text-slate-300 border-slate-600/50">
                          {channel}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-xs text-slate-400">Balance</p>
                  <p className="text-sm font-semibold text-white">
                    ₹{account.balance.toLocaleString()}
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-xs text-slate-400">Risk Score</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="w-32 h-2 bg-slate-700/50 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          account.riskScore > 80 ? 'bg-red-500' :
                          account.riskScore > 60 ? 'bg-orange-500' :
                          account.riskScore > 40 ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`}
                        style={{ width: `${account.riskScore}%` }}
                      />
                    </div>
                    <span className={`text-lg font-bold ${
                      account.riskScore > 80 ? 'text-red-400' :
                      account.riskScore > 60 ? 'text-orange-400' :
                      account.riskScore > 40 ? 'text-yellow-400' :
                      'text-green-400'
                    }`}>
                      {account.riskScore}
                    </span>
                  </div>
                </div>

                <Badge className={`${getRiskColor(account.riskScore)} border px-3 py-1`}>
                  {getRiskLabel(account.riskScore)}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}