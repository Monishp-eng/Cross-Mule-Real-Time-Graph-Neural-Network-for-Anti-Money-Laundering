import { AlertTriangle, Clock, CheckCircle, Eye, Shield, Globe, Activity } from 'lucide-react';
import { mockAlerts, mockClusters } from '../mockData';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card } from './ui/card';

export function AlertsView() {
  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-500/10 text-red-400 border-red-500/20',
      high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
      medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      low: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    };
    return colors[severity] || colors.low;
  };

  const getPatternColor = (pattern?: string) => {
    const colors: Record<string, string> = {
      structuring: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      fragmentation: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
      nesting: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
      'rapid-movement': 'bg-red-500/10 text-red-400 border-red-500/20',
    };
    return pattern ? colors[pattern] || colors.structuring : '';
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white">Mule Clusters & Alerts</h2>
          <p className="text-slate-400 mt-1">Detected suspicious account networks with GNN-based pattern recognition</p>
        </div>
        <div className="flex gap-2">
          <Badge className="bg-red-500/10 text-red-400 border-red-500/20 px-4 py-2">
            {mockAlerts.filter(a => a.status === 'new').length} New Alerts
          </Badge>
          <Badge className="bg-yellow-500/10 text-yellow-400 border-yellow-500/20 px-4 py-2">
            {mockAlerts.filter(a => a.status === 'investigating').length} Investigating
          </Badge>
        </div>
      </div>

      {/* Mule Clusters */}
      <div>
        <h3 className="text-xl font-semibold text-white mb-4">Detected Mule Rings</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {mockClusters.map((cluster, index) => (
            <Card
              key={cluster.id}
              className="bg-slate-900/40 backdrop-blur-xl border-slate-700/50 p-6 hover:border-red-500/30 transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                  <AlertTriangle className="w-6 h-6 text-red-400" />
                </div>
                <div className="flex flex-col gap-1 items-end">
                  <Badge className="bg-red-500 text-white">
                    Risk: {cluster.riskScore}
                  </Badge>
                  {cluster.confidenceScore && (
                    <Badge className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20 text-xs">
                      <Shield className="w-3 h-3 mr-1" />
                      {(cluster.confidenceScore * 100).toFixed(0)}% Confidence
                    </Badge>
                  )}
                </div>
              </div>

              <h4 className="text-lg font-semibold text-white mb-2">{cluster.name}</h4>
              <p className="text-sm text-slate-400 mb-4">ID: {cluster.id}</p>

              <div className="space-y-3 mb-4">
                <div className="flex justify-between">
                  <span className="text-sm text-slate-400">Accounts</span>
                  <span className="text-sm font-semibold text-white">{cluster.accountCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-400">Total Amount</span>
                  <span className="text-sm font-semibold text-cyan-400">
                    ₹{cluster.totalAmount.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-400">Detected</span>
                  <span className="text-sm text-slate-500">
                    {Math.floor((Date.now() - cluster.detectedAt.getTime()) / 86400000)}d ago
                  </span>
                </div>
                {cluster.pattern && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">Pattern</span>
                    <Badge className={getPatternColor(cluster.pattern)}>
                      <Activity className="w-3 h-3 mr-1" />
                      {getPatternLabel(cluster.pattern)}
                    </Badge>
                  </div>
                )}
                {cluster.jurisdictions && cluster.jurisdictions.length > 0 && (
                  <div className="pt-2 border-t border-slate-700/50">
                    <span className="text-xs text-slate-400 flex items-center gap-1 mb-1">
                      <Globe className="w-3 h-3" />
                      Cross-Jurisdiction Activity
                    </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {cluster.jurisdictions.map((jurisdiction, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded bg-slate-700/50 text-slate-300 border border-slate-600/50">
                          {jurisdiction}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <Button className="w-full bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20">
                <Eye className="w-4 h-4 mr-2" />
                Investigate Cluster
              </Button>
            </Card>
          ))}
        </div>
      </div>

      {/* Alerts List */}
      <div>
        <h3 className="text-xl font-semibold text-white mb-4">Recent Alerts</h3>
        <div className="space-y-4">
          {mockAlerts.map((alert, index) => (
            <div
              key={alert.id}
              className="bg-slate-900/40 backdrop-blur-xl rounded-xl border border-slate-700/50 p-6 hover:border-cyan-500/30 transition-all"
            >
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-lg ${
                  alert.severity === 'critical' ? 'bg-red-500/10 border border-red-500/20' :
                  alert.severity === 'high' ? 'bg-orange-500/10 border border-orange-500/20' :
                  'bg-yellow-500/10 border border-yellow-500/20'
                }`}>
                  {alert.status === 'resolved' ? (
                    <CheckCircle className="w-6 h-6 text-green-400" />
                  ) : (
                    <AlertTriangle className={`w-6 h-6 ${
                      alert.severity === 'critical' ? 'text-red-400' :
                      alert.severity === 'high' ? 'text-orange-400' :
                      'text-yellow-400'
                    }`} />
                  )}
                </div>

                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="text-lg font-semibold text-white mb-1 flex items-center gap-2">
                        {alert.title}
                        {alert.sanctionsRelated && (
                          <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-xs">
                            <Shield className="w-3 h-3 mr-1" />
                            Sanctions Alert
                          </Badge>
                        )}
                      </h4>
                      <p className="text-sm text-slate-400">{alert.description}</p>
                    </div>
                    <div className="flex gap-2">
                      <Badge className={getSeverityColor(alert.severity)}>
                        {alert.severity}
                      </Badge>
                      <Badge className={
                        alert.status === 'new' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
                        alert.status === 'investigating' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                        'bg-green-500/10 text-green-400 border-green-500/20'
                      }>
                        {alert.status}
                      </Badge>
                    </div>
                  </div>

                  <div className="flex items-center flex-wrap gap-3 mt-3 mb-3">
                    {alert.pattern && (
                      <Badge className={getPatternColor(alert.pattern)}>
                        <Activity className="w-3 h-3 mr-1" />
                        {getPatternLabel(alert.pattern)}
                      </Badge>
                    )}
                    {alert.confidenceScore && (
                      <Badge className="bg-cyan-500/10 text-cyan-400 border-cyan-500/20">
                        <Shield className="w-3 h-3 mr-1" />
                        Confidence: {(alert.confidenceScore * 100).toFixed(0)}%
                      </Badge>
                    )}
                  </div>

                  <div className="flex items-center justify-between mt-4">
                    <div className="flex items-center gap-4 text-sm text-slate-500">
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {Math.floor((Date.now() - alert.timestamp.getTime()) / 60000)}m ago
                      </div>
                      {alert.clusterId && (
                        <div>Cluster: <span className="font-mono text-cyan-400">{alert.clusterId}</span></div>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-slate-600 text-slate-300 hover:bg-slate-800"
                      >
                        Dismiss
                      </Button>
                      <Button
                        size="sm"
                        className="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20"
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        Investigate
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}