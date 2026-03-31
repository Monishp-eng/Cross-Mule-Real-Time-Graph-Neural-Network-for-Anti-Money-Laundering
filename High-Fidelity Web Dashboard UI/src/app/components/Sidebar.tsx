import { Link, useLocation } from 'react-router';
import { LayoutDashboard, Network, AlertTriangle, ArrowLeftRight, FileText, Settings, Activity } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

export function Sidebar() {
  const location = useLocation();
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const menuItems = [
    { icon: LayoutDashboard, label: 'Overview', path: '/' },
    { icon: Network, label: 'Entity Graph', path: '/graph' },
    { icon: AlertTriangle, label: 'Mule Clusters', path: '/alerts' },
    { icon: Activity, label: 'Risk Scoring', path: '/risk-scoring' },
    { icon: ArrowLeftRight, label: 'Cross-Channel Flow', path: '/channel-flow' },
    { icon: FileText, label: 'Compliance Reports', path: '/reports' },
  ];

  return (
    <aside className={`fixed left-0 top-16 bottom-0 w-64 backdrop-blur-xl border-r ${
      isDark 
        ? 'bg-slate-950/60 border-cyan-500/10' 
        : 'bg-white/60 border-slate-300'
    }`}>
      <nav className="p-4 space-y-2">
        {menuItems.map((item, index) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={index}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
                isActive
                  ? isDark
                    ? 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-400 shadow-lg shadow-cyan-500/10'
                    : 'bg-gradient-to-r from-cyan-100 to-purple-100 text-cyan-700 shadow-lg shadow-cyan-500/5'
                  : isDark
                    ? 'text-slate-400 hover:text-cyan-300 hover:bg-slate-800/50'
                    : 'text-slate-600 hover:text-cyan-600 hover:bg-slate-100'
              }`}
            >
              <Icon className={`w-5 h-5 ${
                isActive 
                  ? isDark ? 'text-cyan-400' : 'text-cyan-700'
                  : isDark 
                    ? 'text-slate-500 group-hover:text-cyan-400'
                    : 'text-slate-500 group-hover:text-cyan-600'
              }`} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}