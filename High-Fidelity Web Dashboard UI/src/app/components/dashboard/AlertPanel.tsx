import { AlertTriangle, Eye } from 'lucide-react';
import { mockAlerts } from '../../mockData';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { motion } from 'motion/react';

export function AlertPanel() {
  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-500/10 text-red-400 border-red-500/20',
      high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
      medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      low: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    };
    return colors[severity] || colors.low;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      new: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      investigating: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      resolved: 'bg-green-500/10 text-green-400 border-green-500/20',
    };
    return colors[status] || colors.new;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="bg-slate-900/50 backdrop-blur-xl rounded-xl border-2 border-slate-700/50 flex flex-col shadow-xl h-full"
    >
      {/* Header */}
      <div className="p-6 border-b border-slate-700/50">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white">Risk Alerts</h3>
            <p className="text-sm text-slate-400">Flagged mule clusters and suspicious activity</p>
          </div>
          <Badge className="bg-red-500/10 text-red-400 border-red-500/20">
            {mockAlerts.filter(a => a.status === 'new').length} New
          </Badge>
        </div>
      </div>

      {/* Alert list */}
      <ScrollArea className="flex-1 max-h-96">
        <div className="p-6 space-y-4">
          {mockAlerts.map((alert, index) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50 hover:border-cyan-500/30 transition-all"
            >
              <div className="flex items-start gap-3 mb-3">
                <div className={`p-2 rounded-lg ${
                  alert.severity === 'critical' ? 'bg-red-500/10' :
                  alert.severity === 'high' ? 'bg-orange-500/10' :
                  'bg-yellow-500/10'
                }`}>
                  <AlertTriangle className={`w-5 h-5 ${
                    alert.severity === 'critical' ? 'text-red-400' :
                    alert.severity === 'high' ? 'text-orange-400' :
                    'text-yellow-400'
                  }`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-1">
                    <h4 className="font-semibold text-white">{alert.title}</h4>
                    <Badge className={`text-xs ${getSeverityColor(alert.severity)}`}>
                      {alert.severity}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-400 mb-2">{alert.description}</p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge className={`text-xs ${getStatusColor(alert.status)}`}>
                        {alert.status}
                      </Badge>
                      <span className="text-xs text-slate-500">
                        {Math.floor((Date.now() - alert.timestamp.getTime()) / 60000)}m ago
                      </span>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10"
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      Investigate
                    </Button>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </ScrollArea>
    </motion.div>
  );
}