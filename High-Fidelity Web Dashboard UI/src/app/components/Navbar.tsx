import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router';
import { Bell, User, Shield, Moon, Sun, LogOut } from 'lucide-react';
import { Badge } from './ui/badge';
import { useTheme } from '../contexts/ThemeContext';

export function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';
  const [showUserMenu, setShowUserMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const tabs = [
    { name: 'Dashboard', path: '/' },
    { name: 'Graph View', path: '/graph' },
    { name: 'Alerts', path: '/alerts' },
    { name: 'Transactions', path: '/transactions' },
    { name: 'Reports', path: '/reports' },
    { name: 'Settings', path: '/settings' },
  ];

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    setShowUserMenu(false);
    navigate('/login');
  };

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 h-16 backdrop-blur-xl border-b shadow-lg ${
      isDark
        ? 'bg-slate-950/80 border-cyan-500/20 shadow-cyan-500/10'
        : 'bg-white/80 border-slate-300 shadow-slate-200/50'
    }`}>
      <div className="flex items-center justify-between h-full px-6">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Shield className={`w-8 h-8 ${isDark ? 'text-cyan-400' : 'text-cyan-600'}`} />
            <div className={`absolute inset-0 blur-lg ${isDark ? 'bg-cyan-400/30' : 'bg-cyan-600/20'}`} />
          </div>
          <h1 className={`text-2xl font-bold bg-gradient-to-r ${
            isDark ? 'from-cyan-400 to-purple-500' : 'from-cyan-600 to-purple-600'
          } bg-clip-text text-transparent`}>
            MuleGuard AI
          </h1>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1">
          {tabs.map(tab => (
            <Link
              key={tab.path}
              to={tab.path}
              className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                location.pathname === tab.path
                  ? isDark
                    ? 'bg-cyan-500/20 text-cyan-400 shadow-lg shadow-cyan-500/20'
                    : 'bg-cyan-100 text-cyan-700 shadow-lg shadow-cyan-500/10'
                  : isDark
                    ? 'text-slate-400 hover:text-cyan-300 hover:bg-slate-800/50'
                    : 'text-slate-600 hover:text-cyan-600 hover:bg-slate-100'
              }`}
            >
              {tab.name}
            </Link>
          ))}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-4">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-lg transition-all ${
              isDark
                ? 'hover:bg-slate-800/50 text-slate-400 hover:text-cyan-400'
                : 'hover:bg-slate-100 text-slate-600 hover:text-cyan-600'
            }`}
            aria-label="Toggle theme"
          >
            {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>

          <button className={`relative p-2 rounded-lg transition-all ${
            isDark ? 'hover:bg-slate-800/50' : 'hover:bg-slate-100'
          }`}>
            <Bell className={`w-5 h-5 ${isDark ? 'text-slate-400' : 'text-slate-600'}`} />
            <Badge className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center bg-red-500 text-white text-xs p-0">
              3
            </Badge>
          </button>

          {/* User menu */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className={`flex items-center gap-2 p-2 rounded-lg transition-all ${
                isDark ? 'hover:bg-slate-800/50' : 'hover:bg-slate-100'
              }`}
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
            </button>

            {showUserMenu && (
              <div className={`absolute right-0 top-full mt-2 w-48 rounded-xl border shadow-2xl z-50 overflow-hidden ${
                isDark
                  ? 'bg-slate-900 border-slate-700'
                  : 'bg-white border-slate-200'
              }`}>
                <button
                  onClick={handleLogout}
                  className={`w-full text-left px-4 py-3 text-sm flex items-center gap-3 transition-colors ${
                    isDark
                      ? 'text-red-400 hover:bg-red-500/10'
                      : 'text-red-600 hover:bg-red-50'
                  }`}
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
