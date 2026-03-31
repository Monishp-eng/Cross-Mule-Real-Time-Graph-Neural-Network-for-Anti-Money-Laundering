import { Settings, Bell, Shield, Database, Users, Cpu } from 'lucide-react';
import { Card } from './ui/card';
import { Switch } from './ui/switch';
import { Button } from './ui/button';
import { Slider } from './ui/slider';
import { useState } from 'react';

export function SettingsView() {
  const [riskThreshold, setRiskThreshold] = useState([75]);
  const [autoInvestigate, setAutoInvestigate] = useState(true);
  const [realTimeAlerts, setRealTimeAlerts] = useState(true);
  const [gnnEnabled, setGnnEnabled] = useState(true);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-white">System Settings</h2>
        <p className="text-slate-400 mt-1">Configure detection parameters and preferences</p>
      </div>

      {/* Detection Settings */}
      <Card className="bg-slate-900/40 backdrop-blur-xl border-slate-700/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="w-6 h-6 text-cyan-400" />
          <h3 className="text-xl font-semibold text-white">Detection Parameters</h3>
        </div>

        <div className="space-y-6">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <label className="text-sm font-medium text-white">Risk Score Threshold</label>
                <p className="text-xs text-slate-400">Flag transactions above this risk score</p>
              </div>
              <span className="text-lg font-bold text-cyan-400">{riskThreshold[0]}%</span>
            </div>
            <Slider
              value={riskThreshold}
              onValueChange={setRiskThreshold}
              min={0}
              max={100}
              step={5}
            />
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <div>
              <label className="text-sm font-medium text-white">GNN-Based Detection</label>
              <p className="text-xs text-slate-400">Use Graph Neural Networks for pattern recognition</p>
            </div>
            <Switch checked={gnnEnabled} onCheckedChange={setGnnEnabled} />
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <div>
              <label className="text-sm font-medium text-white">Auto-Investigation</label>
              <p className="text-xs text-slate-400">Automatically flag high-risk clusters for review</p>
            </div>
            <Switch checked={autoInvestigate} onCheckedChange={setAutoInvestigate} />
          </div>
        </div>
      </Card>

      {/* Notification Settings */}
      <Card className="bg-slate-900/40 backdrop-blur-xl border-slate-700/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Bell className="w-6 h-6 text-cyan-400" />
          <h3 className="text-xl font-semibold text-white">Notifications</h3>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <div>
              <label className="text-sm font-medium text-white">Real-Time Alerts</label>
              <p className="text-xs text-slate-400">Receive instant notifications for critical alerts</p>
            </div>
            <Switch checked={realTimeAlerts} onCheckedChange={setRealTimeAlerts} />
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <div>
              <label className="text-sm font-medium text-white">Email Summaries</label>
              <p className="text-xs text-slate-400">Daily digest of detected patterns</p>
            </div>
            <Switch defaultChecked />
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <div>
              <label className="text-sm font-medium text-white">Cluster Formation Alerts</label>
              <p className="text-xs text-slate-400">Notify when new mule rings are detected</p>
            </div>
            <Switch defaultChecked />
          </div>
        </div>
      </Card>

      {/* Model Configuration */}
      <Card className="bg-slate-900/40 backdrop-blur-xl border-slate-700/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Cpu className="w-6 h-6 text-cyan-400" />
          <h3 className="text-xl font-semibold text-white">GNN Model Configuration</h3>
        </div>

        <div className="space-y-4">
          <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Model Version</span>
              <span className="text-sm font-semibold text-white">v2.4.1</span>
            </div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Last Training</span>
              <span className="text-sm font-semibold text-white">2 days ago</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Accuracy</span>
              <span className="text-sm font-semibold text-green-400">94.7%</span>
            </div>
          </div>

          <Button variant="outline" className="w-full border-slate-700 text-slate-300 hover:bg-slate-800">
            Retrain Model
          </Button>
        </div>
      </Card>

      {/* Data Management */}
      <Card className="bg-slate-900/40 backdrop-blur-xl border-slate-700/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Database className="w-6 h-6 text-cyan-400" />
          <h3 className="text-xl font-semibold text-white">Data Management</h3>
        </div>

        <div className="space-y-4">
          <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">Storage Used</span>
              <span className="text-sm font-semibold text-white">2.4 TB / 10 TB</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2 mt-2">
              <div className="bg-cyan-500 h-2 rounded-full" style={{ width: '24%' }} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800">
              Export Data
            </Button>
            <Button variant="outline" className="border-red-700 text-red-400 hover:bg-red-950/20">
              Clear Cache
            </Button>
          </div>
        </div>
      </Card>

      {/* User Management */}
      <Card className="bg-slate-900/40 backdrop-blur-xl border-slate-700/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Users className="w-6 h-6 text-cyan-400" />
          <h3 className="text-xl font-semibold text-white">Access Control</h3>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center">
                <span className="text-white font-semibold">JD</span>
              </div>
              <div>
                <p className="text-sm font-medium text-white">John Doe</p>
                <p className="text-xs text-slate-400">Admin</p>
              </div>
            </div>
            <Button size="sm" variant="ghost" className="text-slate-400">
              Edit
            </Button>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-500 flex items-center justify-center">
                <span className="text-white font-semibold">AS</span>
              </div>
              <div>
                <p className="text-sm font-medium text-white">Alice Smith</p>
                <p className="text-xs text-slate-400">Analyst</p>
              </div>
            </div>
            <Button size="sm" variant="ghost" className="text-slate-400">
              Edit
            </Button>
          </div>
        </div>

        <Button className="w-full mt-4 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20">
          Add New User
        </Button>
      </Card>
    </div>
  );
}
