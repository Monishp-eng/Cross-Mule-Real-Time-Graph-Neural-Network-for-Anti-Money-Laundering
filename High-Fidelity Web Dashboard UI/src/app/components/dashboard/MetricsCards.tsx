import { TrendingUp, TrendingDown, AlertTriangle, Users, Zap, Shield } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { mockVelocityTrend, mockRiskTrend } from '../../mockData';
import { useTheme } from '../../contexts/ThemeContext';

export function MetricsCards() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const metrics = [
    {
      title: 'Total Active Accounts',
      value: '15,234',
      change: '+12.3%',
      trend: 'up',
      icon: Users,
      color: 'cyan',
      data: mockVelocityTrend,
    },
    {
      title: 'Suspicious Clusters',
      value: '3',
      change: '+2',
      trend: 'up',
      icon: AlertTriangle,
      color: 'red',
      data: mockRiskTrend,
    },
    {
      title: 'Avg Transaction Velocity',
      value: '125',
      change: '+18.5%',
      trend: 'up',
      icon: Zap,
      color: 'purple',
      data: mockVelocityTrend,
    },
    {
      title: 'High-Risk Alerts',
      value: '8',
      change: '-15.2%',
      trend: 'down',
      icon: Shield,
      color: 'green',
      data: mockRiskTrend,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
      {metrics.map((metric, index) => {
        const Icon = metric.icon;
        const TrendIcon = metric.trend === 'up' ? TrendingUp : TrendingDown;
        
        return (
          <div
            key={index}
            className="relative group"
          >
            {/* Glassmorphism card */}
            <div className={`relative backdrop-blur-xl rounded-xl border-2 p-6 hover:border-cyan-500/40 transition-all duration-300 shadow-lg ${
              isDark 
                ? 'bg-slate-900/50 border-slate-700/50' 
                : 'bg-white/50 border-slate-300'
            }`}>
              {/* Glow effect */}
              <div className={`absolute inset-0 rounded-xl bg-gradient-to-br from-${metric.color}-500/0 to-${metric.color}-500/0 group-hover:from-${metric.color}-500/5 group-hover:to-${metric.color}-500/10 transition-all duration-300`} />
              
              <div className="relative">
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-lg bg-${metric.color}-500/10 border border-${metric.color}-500/20`}>
                    <Icon className={`w-6 h-6 text-${metric.color}-400`} />
                  </div>
                  <div className={`flex items-center gap-1 text-sm ${
                    metric.trend === 'up' 
                      ? metric.color === 'red' ? 'text-red-400' : 'text-green-400'
                      : 'text-green-400'
                  }`}>
                    <TrendIcon className="w-4 h-4" />
                    <span>{metric.change}</span>
                  </div>
                </div>

                <div>
                  <p className={`text-sm mb-1 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                    {metric.title}
                  </p>
                  <p className={`text-3xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                    {metric.value}
                  </p>
                </div>

                {/* Mini chart */}
                <div className="mt-4 h-12">
                  <ResponsiveContainer width="100%" height={48}>
                    <LineChart data={metric.data}>
                      <Line
                        type="monotone"
                        dataKey={metric.data[0].velocity !== undefined ? 'velocity' : 'score'}
                        stroke={
                          metric.color === 'cyan' ? '#06b6d4' :
                          metric.color === 'red' ? '#ef4444' :
                          metric.color === 'purple' ? '#a855f7' :
                          '#22c55e'
                        }
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}