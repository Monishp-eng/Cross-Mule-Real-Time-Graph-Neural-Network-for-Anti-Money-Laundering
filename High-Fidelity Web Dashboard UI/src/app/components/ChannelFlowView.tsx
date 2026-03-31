import { motion } from 'motion/react';
import { mockChannelFlow } from '../mockData';
import { ArrowRight, TrendingUp, AlertCircle } from 'lucide-react';
import { Badge } from './ui/badge';

export function ChannelFlowView() {
  // Calculate positions for Sankey-like visualization
  const channels = ['App', 'Web', 'UPI', 'Wallet', 'ATM', 'Bank'];
  const leftChannels = ['App', 'Web'];
  const middleChannels = ['UPI', 'Wallet'];
  const rightChannels = ['ATM', 'Bank'];

  const getChannelColor = (channel: string) => {
    const colors: Record<string, string> = {
      App: '#06b6d4',
      Web: '#eab308',
      UPI: '#3b82f6',
      Wallet: '#a855f7',
      ATM: '#22c55e',
      Bank: '#f97316',
    };
    return colors[channel] || '#64748b';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-white">Cross-Channel Flow Analysis</h2>
        <p className="text-slate-400 mt-1">Visualize transaction flows across payment channels</p>
      </div>

      {/* Main Flow Visualization */}
      <div className="bg-slate-900/50 backdrop-blur-xl rounded-xl border-2 border-slate-700/50 p-8 shadow-xl">
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-white mb-2">Transaction Flow Map</h3>
          <p className="text-sm text-slate-400">Real-time visualization of money movement patterns</p>
        </div>

        <div className="relative h-96 overflow-hidden rounded-lg bg-slate-950/50 p-6">
          <svg width="100%" height="100%" className="overflow-visible">
            <defs>
              {mockChannelFlow.map((flow, i) => (
                <linearGradient key={i} id={`gradient-${i}`} x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={getChannelColor(flow.from)} stopOpacity="0.6" />
                  <stop offset="100%" stopColor={getChannelColor(flow.to)} stopOpacity="0.6" />
                </linearGradient>
              ))}
            </defs>

            {/* Draw flows */}
            {mockChannelFlow.map((flow, i) => {
              const fromIndex = leftChannels.indexOf(flow.from) !== -1 ? leftChannels.indexOf(flow.from) :
                               middleChannels.indexOf(flow.from) !== -1 ? middleChannels.indexOf(flow.from) : -1;
              const toIndex = middleChannels.indexOf(flow.to) !== -1 ? middleChannels.indexOf(flow.to) :
                             rightChannels.indexOf(flow.to) !== -1 ? rightChannels.indexOf(flow.to) : -1;
              
              let startX = 0, startY = 0, endX = 0, endY = 0;

              if (leftChannels.includes(flow.from)) {
                startX = 100;
                startY = 100 + fromIndex * 140;
              } else if (middleChannels.includes(flow.from)) {
                startX = 350;
                startY = 100 + fromIndex * 140;
              }

              if (middleChannels.includes(flow.to)) {
                endX = 350;
                endY = 100 + toIndex * 140;
              } else if (rightChannels.includes(flow.to)) {
                endX = 600;
                endY = 100 + toIndex * 140;
              }

              const controlX1 = startX + (endX - startX) / 3;
              const controlX2 = startX + ((endX - startX) * 2) / 3;

              const strokeWidth = Math.max(3, (flow.value / 50000) * 12);

              return (
                <motion.path
                  key={i}
                  d={`M ${startX} ${startY} C ${controlX1} ${startY}, ${controlX2} ${endY}, ${endX} ${endY}`}
                  stroke={`url(#gradient-${i})`}
                  strokeWidth={strokeWidth}
                  fill="none"
                  opacity={0.5}
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1.5, delay: i * 0.1 }}
                  className="hover:opacity-100 transition-opacity cursor-pointer"
                >
                  <title>{`${flow.from} → ${flow.to}: ₹${flow.value.toLocaleString()}`}</title>
                </motion.path>
              );
            })}

            {/* Draw channel nodes - Left */}
            {leftChannels.map((channel, i) => (
              <g key={`left-${channel}`}>
                <rect
                  x={40}
                  y={75 + i * 140}
                  width={120}
                  height={50}
                  rx={10}
                  fill={getChannelColor(channel)}
                  fillOpacity={0.2}
                  stroke={getChannelColor(channel)}
                  strokeWidth={2}
                />
                <text
                  x={100}
                  y={105 + i * 140}
                  textAnchor="middle"
                  fill="white"
                  fontSize={16}
                  fontWeight="600"
                >
                  {channel}
                </text>
              </g>
            ))}

            {/* Draw channel nodes - Middle */}
            {middleChannels.map((channel, i) => (
              <g key={`middle-${channel}`}>
                <rect
                  x={290}
                  y={75 + i * 140}
                  width={120}
                  height={50}
                  rx={10}
                  fill={getChannelColor(channel)}
                  fillOpacity={0.2}
                  stroke={getChannelColor(channel)}
                  strokeWidth={2}
                />
                <text
                  x={350}
                  y={105 + i * 140}
                  textAnchor="middle"
                  fill="white"
                  fontSize={16}
                  fontWeight="600"
                >
                  {channel}
                </text>
              </g>
            ))}

            {/* Draw channel nodes - Right */}
            {rightChannels.map((channel, i) => (
              <g key={`right-${channel}`}>
                <rect
                  x={540}
                  y={75 + i * 140}
                  width={120}
                  height={50}
                  rx={10}
                  fill={getChannelColor(channel)}
                  fillOpacity={0.2}
                  stroke={getChannelColor(channel)}
                  strokeWidth={2}
                />
                <text
                  x={600}
                  y={105 + i * 140}
                  textAnchor="middle"
                  fill="white"
                  fontSize={16}
                  fontWeight="600"
                >
                  {channel}
                </text>
              </g>
            ))}
          </svg>
        </div>

        {/* Flow Stats */}
        <div className="grid grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-700/50">
          <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <p className="text-xs text-slate-400 mb-1">Total Flow Volume</p>
            <p className="text-2xl font-bold text-white">
              ₹{mockChannelFlow.reduce((acc, f) => acc + f.value, 0).toLocaleString()}
            </p>
          </div>
          <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <p className="text-xs text-slate-400 mb-1">High Velocity Flows</p>
            <p className="text-2xl font-bold text-red-400">
              {mockChannelFlow.filter(f => f.value > 300000).length}
            </p>
          </div>
          <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <p className="text-xs text-slate-400 mb-1">Active Channels</p>
            <p className="text-2xl font-bold text-cyan-400">{channels.length}</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <p className="text-xs text-slate-400 mb-1">Avg Flow Size</p>
            <p className="text-2xl font-bold text-purple-400">
              ₹{Math.round(mockChannelFlow.reduce((acc, f) => acc + f.value, 0) / mockChannelFlow.length).toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Flow Details Table */}
      <div className="bg-slate-900/50 backdrop-blur-xl rounded-xl border-2 border-slate-700/50 p-6 shadow-xl">
        <h3 className="text-xl font-semibold text-white mb-4">Detailed Flow Analysis</h3>
        
        <div className="space-y-3">
          {mockChannelFlow
            .sort((a, b) => b.value - a.value)
            .map((flow, i) => (
              <div 
                key={i}
                className="flex items-center justify-between p-4 rounded-lg bg-slate-800/30 border border-slate-700/50 hover:border-cyan-500/30 transition-all"
              >
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Badge 
                      className="text-xs px-3 py-1" 
                      style={{ 
                        backgroundColor: `${getChannelColor(flow.from)}20`,
                        color: getChannelColor(flow.from),
                        borderColor: `${getChannelColor(flow.from)}40`
                      }}
                    >
                      {flow.from}
                    </Badge>
                    <ArrowRight className="w-4 h-4 text-slate-500" />
                    <Badge 
                      className="text-xs px-3 py-1"
                      style={{ 
                        backgroundColor: `${getChannelColor(flow.to)}20`,
                        color: getChannelColor(flow.to),
                        borderColor: `${getChannelColor(flow.to)}40`
                      }}
                    >
                      {flow.to}
                    </Badge>
                  </div>
                </div>
                
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-sm text-slate-400">Flow Volume</p>
                    <p className="text-lg font-semibold text-white">₹{flow.value.toLocaleString()}</p>
                  </div>
                  
                  {flow.value > 300000 && (
                    <div className="flex items-center gap-2 text-red-400">
                      <AlertCircle className="w-4 h-4" />
                      <span className="text-xs font-semibold">High Risk</span>
                    </div>
                  )}
                  
                  {flow.value > 200000 && flow.value <= 300000 && (
                    <div className="flex items-center gap-2 text-orange-400">
                      <TrendingUp className="w-4 h-4" />
                      <span className="text-xs font-semibold">Elevated</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
