import { motion } from 'motion/react';
import { mockChannelFlow } from '../../mockData';

export function ChannelFlow() {
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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="bg-slate-900/50 backdrop-blur-xl rounded-xl border-2 border-slate-700/50 p-6 shadow-xl h-full"
    >
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white">Cross-Channel Flow Analysis</h3>
        <p className="text-sm text-slate-400">Transaction flow between channels</p>
      </div>

      <div className="relative h-80 overflow-hidden rounded-lg">
        <svg width="100%" height="100%" className="overflow-hidden">
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
              startY = 80 + fromIndex * 120;
            } else if (middleChannels.includes(flow.from)) {
              startX = 300;
              startY = 80 + fromIndex * 120;
            }

            if (middleChannels.includes(flow.to)) {
              endX = 300;
              endY = 80 + toIndex * 120;
            } else if (rightChannels.includes(flow.to)) {
              endX = 500;
              endY = 80 + toIndex * 120;
            }

            const controlX1 = startX + (endX - startX) / 3;
            const controlX2 = startX + ((endX - startX) * 2) / 3;

            const strokeWidth = Math.max(2, (flow.value / 50000) * 10);

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
                x={50}
                y={60 + i * 120}
                width={100}
                height={40}
                rx={8}
                fill={getChannelColor(channel)}
                fillOpacity={0.2}
                stroke={getChannelColor(channel)}
                strokeWidth={2}
              />
              <text
                x={100}
                y={85 + i * 120}
                textAnchor="middle"
                fill="white"
                fontSize={14}
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
                x={250}
                y={60 + i * 120}
                width={100}
                height={40}
                rx={8}
                fill={getChannelColor(channel)}
                fillOpacity={0.2}
                stroke={getChannelColor(channel)}
                strokeWidth={2}
              />
              <text
                x={300}
                y={85 + i * 120}
                textAnchor="middle"
                fill="white"
                fontSize={14}
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
                x={450}
                y={60 + i * 120}
                width={100}
                height={40}
                rx={8}
                fill={getChannelColor(channel)}
                fillOpacity={0.2}
                stroke={getChannelColor(channel)}
                strokeWidth={2}
              />
              <text
                x={500}
                y={85 + i * 120}
                textAnchor="middle"
                fill="white"
                fontSize={14}
                fontWeight="600"
              >
                {channel}
              </text>
            </g>
          ))}
        </svg>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-slate-700/50">
        <div>
          <p className="text-xs text-slate-400">Total Flow</p>
          <p className="text-xl font-bold text-white">
            ₹{mockChannelFlow.reduce((acc, f) => acc + f.value, 0).toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-400">High Velocity</p>
          <p className="text-xl font-bold text-red-400">
            {mockChannelFlow.filter(f => f.value > 300000).length}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-400">Active Channels</p>
          <p className="text-xl font-bold text-cyan-400">{channels.length}</p>
        </div>
      </div>
    </motion.div>
  );
}