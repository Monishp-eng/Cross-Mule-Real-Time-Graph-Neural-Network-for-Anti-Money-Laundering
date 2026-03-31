import { FileText, Download, Calendar, TrendingUp, Share2, Shield, CheckCircle, Clock } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { mockRiskTrend, mockVelocityTrend, mockIntelligenceSharing } from '../mockData';

export function ReportsView() {
  const jurisdictionData = [
    { jurisdiction: 'India', riskScore: 72, transactionCount: 1250 },
    { jurisdiction: 'UAE', riskScore: 58, transactionCount: 420 },
    { jurisdiction: 'Singapore', riskScore: 45, transactionCount: 380 },
    { jurisdiction: 'USA', riskScore: 38, transactionCount: 290 },
    { jurisdiction: 'UK', riskScore: 42, transactionCount: 310 },
  ];

  const complexityData = [
    { month: 'Jan', complexity: 45 },
    { month: 'Feb', complexity: 52 },
    { month: 'Mar', complexity: 68 },
    { month: 'Apr', complexity: 75 },
    { month: 'May', complexity: 82 },
    { month: 'Jun', complexity: 78 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white">Compliance Reports</h2>
          <p className="text-slate-400 mt-1">Generate and download comprehensive analysis reports</p>
        </div>
        <Button className="bg-cyan-500 hover:bg-cyan-600 text-white">
          <Download className="w-4 h-4 mr-2" />
          Generate Full Report
        </Button>
      </div>

      {/* Report Templates */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-slate-900/40 backdrop-blur-xl border-slate-700/50 p-6 hover:border-cyan-500/30 transition-all">
          <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20 w-fit mb-4">
            <FileText className="w-6 h-6 text-cyan-400" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Weekly Summary</h3>
          <p className="text-sm text-slate-400 mb-4">
            Comprehensive overview of detected patterns and alerts
          </p>
          <Button variant="outline" className="w-full border-slate-700 text-slate-300 hover:bg-slate-800">
            <Download className="w-4 h-4 mr-2" />
            Download PDF
          </Button>
        </Card>

        <Card className="bg-slate-900/40 backdrop-blur-xl border-slate-700/50 p-6 hover:border-cyan-500/30 transition-all">
          <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20 w-fit mb-4">
            <TrendingUp className="w-6 h-6 text-purple-400" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Risk Analysis</h3>
          <p className="text-sm text-slate-400 mb-4">
            Detailed risk scoring and behavior analysis report
          </p>
          <Button variant="outline" className="w-full border-slate-700 text-slate-300 hover:bg-slate-800">
            <Download className="w-4 h-4 mr-2" />
            Download CSV
          </Button>
        </Card>

        <Card className="bg-slate-900/40 backdrop-blur-xl border-slate-700/50 p-6 hover:border-cyan-500/30 transition-all">
          <div className="p-3 rounded-lg bg-orange-500/10 border border-orange-500/20 w-fit mb-4">
            <Calendar className="w-6 h-6 text-orange-400" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Monthly Report</h3>
          <p className="text-sm text-slate-400 mb-4">
            Full compliance report with regulatory insights
          </p>
          <Button variant="outline" className="w-full border-slate-700 text-slate-300 hover:bg-slate-800">
            <Download className="w-4 h-4 mr-2" />
            Download PDF
          </Button>
        </Card>
      </div>

      {/* Jurisdiction Risk Scoring */}
      <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6">
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-white mb-2">Jurisdiction Risk Scoring</h3>
          <p className="text-sm text-slate-400">Geographic distribution of suspicious activity</p>
        </div>
        
        <div className="h-80 min-h-[320px]" key="jurisdiction-chart-container">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={jurisdictionData}>
              <CartesianGrid key="bar-grid" strokeDasharray="3 3" stroke="#334155" />
              <XAxis key="bar-xaxis" dataKey="jurisdiction" stroke="#94a3b8" />
              <YAxis key="bar-yaxis" stroke="#94a3b8" />
              <Tooltip
                key="bar-tooltip"
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend key="bar-legend" />
              <Bar key="bar-risk" dataKey="riskScore" fill="#ef4444" name="Risk Score" />
              <Bar key="bar-transaction" dataKey="transactionCount" fill="#06b6d4" name="Transactions" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-5 gap-4 mt-6">
          {jurisdictionData.map((item) => (
            <div key={item.jurisdiction} className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/50">
              <p className="text-xs text-slate-400 mb-1">{item.jurisdiction}</p>
              <p className="text-lg font-semibold text-white">{item.riskScore}</p>
              <Badge className={
                item.riskScore > 70 ? 'bg-red-500/10 text-red-400 border-red-500/20 text-xs mt-1' :
                item.riskScore > 50 ? 'bg-orange-500/10 text-orange-400 border-orange-500/20 text-xs mt-1' :
                'bg-green-500/10 text-green-400 border-green-500/20 text-xs mt-1'
              }>
                {item.riskScore > 70 ? 'High' : item.riskScore > 50 ? 'Medium' : 'Low'}
              </Badge>
            </div>
          ))}
        </div>
      </div>

      {/* Transaction Complexity Score */}
      <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6">
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-white mb-2">Transaction Complexity Score</h3>
          <p className="text-sm text-slate-400">
            Tracking sophistication of money movement patterns over time
          </p>
        </div>

        <div className="h-80 min-h-[320px]" key="complexity-chart-container">
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={complexityData}>
              <CartesianGrid key="line-grid" strokeDasharray="3 3" stroke="#334155" />
              <XAxis key="line-xaxis" dataKey="month" stroke="#94a3b8" />
              <YAxis key="line-yaxis" stroke="#94a3b8" />
              <Tooltip
                key="line-tooltip"
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend key="line-legend" />
              <Line
                key="line-complexity"
                type="monotone"
                dataKey="complexity"
                stroke="#a855f7"
                strokeWidth={3}
                dot={{ fill: '#a855f7', r: 6 }}
                name="Complexity Index"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Behavior-Based Sanctions Signals */}
      <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6">
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-white mb-2">Behavior-Based Sanctions Signals</h3>
          <p className="text-sm text-slate-400">AI-detected patterns matching known sanction evasion tactics</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-white">Layering Detection</h4>
                <Badge className="bg-red-500 text-white">Critical</Badge>
              </div>
              <p className="text-sm text-slate-400 mb-3">
                Multiple rapid transfers through intermediary accounts detected
              </p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Confidence</span>
                <span className="text-red-400 font-semibold">94.5%</span>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-orange-500/10 border border-orange-500/20">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-white">Structuring Pattern</h4>
                <Badge className="bg-orange-500 text-white">High</Badge>
              </div>
              <p className="text-sm text-slate-400 mb-3">
                Systematic transactions just below reporting thresholds
              </p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Confidence</span>
                <span className="text-orange-400 font-semibold">87.2%</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-white">Circular Trading</h4>
                <Badge className="bg-purple-500 text-white">High</Badge>
              </div>
              <p className="text-sm text-slate-400 mb-3">
                Funds returning to origin through complex routing
              </p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Confidence</span>
                <span className="text-purple-400 font-semibold">91.8%</span>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-white">Velocity Anomaly</h4>
                <Badge className="bg-yellow-500 text-white">Medium</Badge>
              </div>
              <p className="text-sm text-slate-400 mb-3">
                Unusual spike in transaction frequency detected
              </p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Confidence</span>
                <span className="text-yellow-400 font-semibold">78.6%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Privacy-Safe Intelligence Sharing */}
      <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6">
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-white mb-2 flex items-center gap-2">
            <Share2 className="w-5 h-5 text-cyan-400" />
            Privacy-Safe Intelligence Sharing
          </h3>
          <p className="text-sm text-slate-400">
            Secure collaboration with partner institutions and regulatory bodies
          </p>
        </div>

        <div className="space-y-4">
          {mockIntelligenceSharing.map((intel) => (
            <div
              key={intel.id}
              className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-5 hover:border-cyan-500/30 transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-semibold text-white">{intel.partner}</h4>
                    <Badge className={
                      intel.status === 'active' 
                        ? 'bg-green-500/10 text-green-400 border-green-500/20'
                        : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                    }>
                      {intel.status === 'active' ? (
                        <>
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Active
                        </>
                      ) : (
                        <>
                          <Clock className="w-3 h-3 mr-1" />
                          Pending Review
                        </>
                      )}
                    </Badge>
                  </div>
                  <div className="text-sm text-slate-400">
                    Shared: {Math.floor((Date.now() - intel.sharedAt.getTime()) / 3600000)}h ago
                  </div>
                </div>
                <Badge className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20">
                  <Shield className="w-3 h-3 mr-1" />
                  {(intel.confidenceScore * 100).toFixed(0)}% Confidence
                </Badge>
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="p-3 rounded-lg bg-slate-700/30">
                  <span className="text-slate-400 block mb-1">Clusters Shared</span>
                  <div className="flex flex-wrap gap-1">
                    {intel.clusterIds.map((clusterId) => (
                      <span key={clusterId} className="text-xs px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                        {clusterId}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-700/30">
                  <span className="text-slate-400 block mb-1">Accounts</span>
                  <p className="text-lg font-semibold text-white">{intel.accountsShared}</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-700/30">
                  <span className="text-slate-400 block mb-1">Data Type</span>
                  <p className="text-xs text-purple-400 font-semibold">Privacy-Preserving</p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-700/50">
                <div className="flex items-center justify-between">
                  <div className="text-xs text-slate-500">
                    <Shield className="w-3 h-3 inline mr-1" />
                    Encrypted with zero-knowledge proof protocol
                  </div>
                  <Button size="sm" variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800">
                    View Details
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 p-4 rounded-lg bg-cyan-500/5 border border-cyan-500/20">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/10">
              <Share2 className="w-5 h-5 text-cyan-400" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-white mb-1">Enable New Intelligence Partnership</h4>
              <p className="text-sm text-slate-400 mb-3">
                Connect with additional financial institutions to expand threat intelligence coverage
              </p>
              <Button className="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20">
                Configure Sharing Rules
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}