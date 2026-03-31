import { useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { motion } from 'motion/react';
import { Mail, Lock, Eye, EyeOff, Shield, ChevronRight } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

export function LoginPage() {
  const navigate = useNavigate();
  const { theme } = useTheme();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Mock authentication - in production, this would call your auth API
    console.log('Login attempt:', formData);
    navigate('/');
  };

  const isDark = theme === 'dark';

  return (
    <div className={`min-h-screen flex items-center justify-center p-4 ${
      isDark ? 'bg-slate-950' : 'bg-gradient-to-br from-blue-50 via-white to-purple-50'
    }`}>
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 90, 0],
          }}
          transition={{ duration: 20, repeat: Infinity }}
          className={`absolute -top-40 -right-40 w-96 h-96 rounded-full blur-3xl ${
            isDark ? 'bg-cyan-500/10' : 'bg-cyan-400/20'
          }`}
        />
        <motion.div
          animate={{
            scale: [1.2, 1, 1.2],
            rotate: [90, 0, 90],
          }}
          transition={{ duration: 20, repeat: Infinity }}
          className={`absolute -bottom-40 -left-40 w-96 h-96 rounded-full blur-3xl ${
            isDark ? 'bg-purple-500/10' : 'bg-purple-400/20'
          }`}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative"
      >
        {/* Logo and title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-purple-600 mb-4 shadow-2xl">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className={`text-3xl font-bold mb-2 ${
            isDark ? 'text-white' : 'text-slate-900'
          }`}>
            MuleGuard AI
          </h1>
          <p className={isDark ? 'text-slate-400' : 'text-slate-600'}>
            Cross-Channel Mule Account Detection
          </p>
        </div>

        {/* Login form */}
        <div className={`relative backdrop-blur-xl rounded-2xl p-8 shadow-2xl ${
          isDark 
            ? 'bg-slate-900/50 border-2 border-slate-700/50' 
            : 'bg-white/80 border-2 border-slate-200'
        }`}>
          <h2 className={`text-2xl font-bold mb-6 ${
            isDark ? 'text-white' : 'text-slate-900'
          }`}>
            Sign In
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email field */}
            <div>
              <label className={`block text-sm font-medium mb-2 ${
                isDark ? 'text-slate-300' : 'text-slate-700'
              }`}>
                Email Address
              </label>
              <div className="relative">
                <Mail className={`absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 ${
                  isDark ? 'text-slate-400' : 'text-slate-500'
                }`} />
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className={`w-full pl-10 pr-4 py-3 rounded-lg border-2 transition-all focus:outline-none focus:ring-2 ${
                    isDark
                      ? 'bg-slate-800/50 border-slate-700 text-white placeholder-slate-500 focus:border-cyan-500 focus:ring-cyan-500/20'
                      : 'bg-white border-slate-300 text-slate-900 placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500/20'
                  }`}
                  placeholder="you@example.com"
                />
              </div>
            </div>

            {/* Password field */}
            <div>
              <label className={`block text-sm font-medium mb-2 ${
                isDark ? 'text-slate-300' : 'text-slate-700'
              }`}>
                Password
              </label>
              <div className="relative">
                <Lock className={`absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 ${
                  isDark ? 'text-slate-400' : 'text-slate-500'
                }`} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className={`w-full pl-10 pr-12 py-3 rounded-lg border-2 transition-all focus:outline-none focus:ring-2 ${
                    isDark
                      ? 'bg-slate-800/50 border-slate-700 text-white placeholder-slate-500 focus:border-cyan-500 focus:ring-cyan-500/20'
                      : 'bg-white border-slate-300 text-slate-900 placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500/20'
                  }`}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className={`absolute right-3 top-1/2 -translate-y-1/2 ${
                    isDark ? 'text-slate-400 hover:text-slate-300' : 'text-slate-500 hover:text-slate-700'
                  } transition-colors`}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Remember me and forgot password */}
            <div className="flex items-center justify-between">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-2 border-slate-700 bg-slate-800/50 text-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                />
                <span className={`ml-2 text-sm ${
                  isDark ? 'text-slate-400' : 'text-slate-600'
                }`}>
                  Remember me
                </span>
              </label>
              <a href="#" className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors">
                Forgot password?
              </a>
            </div>

            {/* Submit button */}
            <motion.button
              type="submit"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-3 px-4 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-semibold shadow-lg shadow-cyan-500/25 hover:shadow-xl hover:shadow-cyan-500/30 transition-all flex items-center justify-center gap-2"
            >
              Sign In
              <ChevronRight className="w-5 h-5" />
            </motion.button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className={`absolute inset-0 flex items-center ${
              isDark ? 'border-t border-slate-700' : 'border-t border-slate-300'
            }`} />
            <div className="relative flex justify-center text-sm">
              <span className={`px-4 ${
                isDark ? 'bg-slate-900/50 text-slate-400' : 'bg-white/80 text-slate-500'
              }`}>
                Or continue with
              </span>
            </div>
          </div>

          {/* Social login buttons */}
          <div className="grid grid-cols-2 gap-3">
            <button className={`py-3 px-4 rounded-lg border-2 font-medium transition-all hover:scale-105 ${
              isDark
                ? 'bg-slate-800/50 border-slate-700 text-slate-300 hover:border-slate-600'
                : 'bg-white border-slate-300 text-slate-700 hover:border-slate-400'
            }`}>
              Google
            </button>
            <button className={`py-3 px-4 rounded-lg border-2 font-medium transition-all hover:scale-105 ${
              isDark
                ? 'bg-slate-800/50 border-slate-700 text-slate-300 hover:border-slate-600'
                : 'bg-white border-slate-300 text-slate-700 hover:border-slate-400'
            }`}>
              GitHub
            </button>
          </div>

          {/* Sign up link */}
          <p className={`text-center mt-6 text-sm ${
            isDark ? 'text-slate-400' : 'text-slate-600'
          }`}>
            Don't have an account?{' '}
            <Link
              to="/signup"
              className="text-cyan-400 hover:text-cyan-300 font-semibold transition-colors"
            >
              Create Account
            </Link>
          </p>
        </div>

        {/* Footer */}
        <p className={`text-center mt-6 text-sm ${
          isDark ? 'text-slate-500' : 'text-slate-500'
        }`}>
          © 2024 MuleGuard AI. All rights reserved.
        </p>
      </motion.div>
    </div>
  );
}
