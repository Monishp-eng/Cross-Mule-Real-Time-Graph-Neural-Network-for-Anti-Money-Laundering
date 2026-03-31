import { Account, Transaction, Cluster, Alert, GraphNode, GraphLink } from './types';

// Generate mock accounts with enhanced data
export const mockAccounts: Account[] = [
  { id: 'ACC001', name: 'Account 1', riskScore: 92, type: 'high-risk', channels: ['UPI', 'ATM', 'Wallet'], balance: 50000, clusterId: 'CLU001', jurisdiction: 'India', owner: 'John Doe', confidenceScore: 0.95 },
  { id: 'ACC002', name: 'Account 2', riskScore: 88, type: 'high-risk', channels: ['UPI', 'App'], balance: 30000, clusterId: 'CLU001', jurisdiction: 'India', owner: 'John Doe', confidenceScore: 0.92 },
  { id: 'ACC003', name: 'Account 3', riskScore: 85, type: 'suspicious', channels: ['Wallet', 'Web'], balance: 75000, clusterId: 'CLU001', jurisdiction: 'Singapore', owner: 'Jane Smith', confidenceScore: 0.88 },
  { id: 'ACC004', name: 'Account 4', riskScore: 78, type: 'suspicious', channels: ['ATM', 'UPI'], balance: 120000, clusterId: 'CLU002', jurisdiction: 'UAE', owner: 'Mike Johnson', confidenceScore: 0.85 },
  { id: 'ACC005', name: 'Account 5', riskScore: 82, type: 'suspicious', channels: ['App', 'Wallet'], balance: 65000, clusterId: 'CLU002', jurisdiction: 'India', owner: 'Mike Johnson', confidenceScore: 0.89 },
  { id: 'ACC006', name: 'Account 6', riskScore: 25, type: 'normal', channels: ['UPI'], balance: 45000, jurisdiction: 'India', owner: 'Sarah Williams', confidenceScore: 0.98 },
  { id: 'ACC007', name: 'Account 7', riskScore: 32, type: 'normal', channels: ['ATM', 'App'], balance: 90000, jurisdiction: 'UK', owner: 'David Brown', confidenceScore: 0.96 },
  { id: 'ACC008', name: 'Account 8', riskScore: 95, type: 'high-risk', channels: ['UPI', 'Wallet', 'ATM'], balance: 150000, clusterId: 'CLU001', jurisdiction: 'India', owner: 'John Doe', confidenceScore: 0.97, sanctionsMatch: true },
  { id: 'ACC009', name: 'Account 9', riskScore: 18, type: 'normal', channels: ['App'], balance: 35000, jurisdiction: 'USA', owner: 'Emily Davis', confidenceScore: 0.99 },
  { id: 'ACC010', name: 'Account 10', riskScore: 72, type: 'suspicious', channels: ['Wallet', 'UPI'], balance: 88000, clusterId: 'CLU002', jurisdiction: 'Singapore', owner: 'Mike Johnson', confidenceScore: 0.86 },
  { id: 'ACC011', name: 'Account 11', riskScore: 89, type: 'high-risk', channels: ['ATM', 'App', 'UPI'], balance: 110000, clusterId: 'CLU003', jurisdiction: 'India', owner: 'Robert Chen', confidenceScore: 0.91 },
  { id: 'ACC012', name: 'Account 12', riskScore: 91, type: 'high-risk', channels: ['Wallet', 'Web'], balance: 95000, clusterId: 'CLU003', jurisdiction: 'Hong Kong', owner: 'Robert Chen', confidenceScore: 0.93 },
  { id: 'ACC013', name: 'Account 13', riskScore: 15, type: 'normal', channels: ['UPI'], balance: 42000, jurisdiction: 'India', owner: 'Lisa Anderson', confidenceScore: 0.98 },
  { id: 'ACC014', name: 'Account 14', riskScore: 68, type: 'suspicious', channels: ['App', 'ATM'], balance: 58000, jurisdiction: 'UAE', owner: 'Ahmed Hassan', confidenceScore: 0.84 },
  { id: 'ACC015', name: 'Account 15', riskScore: 87, type: 'high-risk', channels: ['UPI', 'Wallet'], balance: 125000, clusterId: 'CLU003', jurisdiction: 'Singapore', owner: 'Robert Chen', confidenceScore: 0.90 },
];

// Generate mock transactions with enhanced pattern detection
export const mockTransactions: Transaction[] = [
  { id: 'TXN001', fromAccount: 'ACC001', toAccount: 'ACC002', amount: 15000, channel: 'UPI', timestamp: new Date(Date.now() - 5000), riskScore: 88, status: 'flagged', pattern: 'structuring', complexity: 3 },
  { id: 'TXN002', fromAccount: 'ACC002', toAccount: 'ACC003', amount: 22000, channel: 'Wallet', timestamp: new Date(Date.now() - 15000), riskScore: 85, status: 'flagged', pattern: 'fragmentation', complexity: 4 },
  { id: 'TXN003', fromAccount: 'ACC006', toAccount: 'ACC007', amount: 5000, channel: 'UPI', timestamp: new Date(Date.now() - 25000), riskScore: 12, status: 'completed', complexity: 1 },
  { id: 'TXN004', fromAccount: 'ACC004', toAccount: 'ACC005', amount: 45000, channel: 'ATM', timestamp: new Date(Date.now() - 35000), riskScore: 76, status: 'flagged', pattern: 'nesting', complexity: 5 },
  { id: 'TXN005', fromAccount: 'ACC008', toAccount: 'ACC001', amount: 38000, channel: 'UPI', timestamp: new Date(Date.now() - 45000), riskScore: 92, status: 'flagged', pattern: 'rapid-movement', complexity: 6, sanctionsFlag: true },
  { id: 'TXN006', fromAccount: 'ACC009', toAccount: 'ACC013', amount: 3500, channel: 'App', timestamp: new Date(Date.now() - 55000), riskScore: 8, status: 'completed', complexity: 1 },
  { id: 'TXN007', fromAccount: 'ACC010', toAccount: 'ACC004', amount: 28000, channel: 'Wallet', timestamp: new Date(Date.now() - 65000), riskScore: 71, status: 'flagged', pattern: 'structuring', complexity: 4 },
  { id: 'TXN008', fromAccount: 'ACC011', toAccount: 'ACC012', amount: 52000, channel: 'ATM', timestamp: new Date(Date.now() - 75000), riskScore: 90, status: 'flagged', pattern: 'fragmentation', complexity: 5 },
  { id: 'TXN009', fromAccount: 'ACC003', toAccount: 'ACC008', amount: 19000, channel: 'UPI', timestamp: new Date(Date.now() - 85000), riskScore: 83, status: 'flagged', pattern: 'nesting', complexity: 4 },
  { id: 'TXN010', fromAccount: 'ACC007', toAccount: 'ACC009', amount: 7500, channel: 'App', timestamp: new Date(Date.now() - 95000), riskScore: 15, status: 'completed', complexity: 1 },
  { id: 'TXN011', fromAccount: 'ACC012', toAccount: 'ACC015', amount: 41000, channel: 'Wallet', timestamp: new Date(Date.now() - 105000), riskScore: 88, status: 'flagged', pattern: 'rapid-movement', complexity: 6 },
  { id: 'TXN012', fromAccount: 'ACC015', toAccount: 'ACC011', amount: 33000, channel: 'UPI', timestamp: new Date(Date.now() - 115000), riskScore: 86, status: 'flagged', pattern: 'structuring', complexity: 5 },
];

// Generate mock clusters with enhanced detection patterns
export const mockClusters: Cluster[] = [
  { id: 'CLU001', name: 'Mule Ring Alpha', accountCount: 4, totalAmount: 385000, riskScore: 92, detectedAt: new Date(Date.now() - 86400000), pattern: 'structuring', jurisdictions: ['India', 'Singapore'], confidenceScore: 0.94 },
  { id: 'CLU002', name: 'Mule Ring Beta', accountCount: 3, totalAmount: 273000, riskScore: 76, detectedAt: new Date(Date.now() - 172800000), pattern: 'fragmentation', jurisdictions: ['India', 'UAE', 'Singapore'], confidenceScore: 0.87 },
  { id: 'CLU003', name: 'Mule Ring Gamma', accountCount: 3, totalAmount: 330000, riskScore: 89, detectedAt: new Date(Date.now() - 259200000), pattern: 'nesting', jurisdictions: ['India', 'Hong Kong', 'Singapore'], confidenceScore: 0.91 },
];

// Generate mock alerts with pattern types
export const mockAlerts: Alert[] = [
  { id: 'ALT001', title: 'High-Velocity Transaction Pattern', description: 'Cluster CLU001 showing rapid cross-channel transfers with structuring pattern', severity: 'critical', clusterId: 'CLU001', timestamp: new Date(Date.now() - 3600000), status: 'new', pattern: 'structuring', confidenceScore: 0.94 },
  { id: 'ALT002', title: 'Suspicious ATM Withdrawal Chain', description: 'Multiple accounts in CLU002 withdrawing large amounts with fragmentation across jurisdictions', severity: 'high', clusterId: 'CLU002', timestamp: new Date(Date.now() - 7200000), status: 'investigating', pattern: 'fragmentation', confidenceScore: 0.87 },
  { id: 'ALT003', title: 'Cross-Channel Flow Anomaly', description: 'Unusual UPI to Wallet transfer pattern with nesting detected', severity: 'high', clusterId: 'CLU003', timestamp: new Date(Date.now() - 10800000), status: 'new', pattern: 'nesting', confidenceScore: 0.91 },
  { id: 'ALT004', title: 'Large Amount Transfer', description: 'Single transaction exceeds threshold with excessive routing complexity', severity: 'medium', timestamp: new Date(Date.now() - 14400000), status: 'resolved', confidenceScore: 0.72 },
  { id: 'ALT005', title: 'New Mule Cluster Formation', description: 'Potential new cluster identified with 3 linked accounts showing rapid movement pattern', severity: 'critical', clusterId: 'CLU001', timestamp: new Date(Date.now() - 18000000), status: 'investigating', pattern: 'rapid-movement', confidenceScore: 0.89 },
  { id: 'ALT006', title: 'Sanctions List Match', description: 'Account ACC008 matched with sanctions list based on behavioral signals', severity: 'critical', timestamp: new Date(Date.now() - 21600000), status: 'new', sanctionsRelated: true, confidenceScore: 0.97 },
];

// Generate graph nodes from accounts
export const mockGraphNodes: GraphNode[] = mockAccounts.map(account => ({
  id: account.id,
  label: account.name,
  riskScore: account.riskScore,
  size: account.riskScore > 80 ? 20 : account.riskScore > 60 ? 15 : 10,
  color: account.riskScore > 80 ? '#ef4444' : account.riskScore > 60 ? '#a855f7' : '#06b6d4',
  clusterId: account.clusterId,
}));

// Generate graph links from transactions
export const mockGraphLinks: GraphLink[] = mockTransactions.map(txn => ({
  source: txn.fromAccount,
  target: txn.toAccount,
  value: txn.amount / 1000,
  animated: txn.riskScore > 70,
}));

// Channel flow data for Sankey
export const mockChannelFlow = [
  { from: 'App', to: 'UPI', value: 450000 },
  { from: 'App', to: 'Wallet', value: 280000 },
  { from: 'UPI', to: 'ATM', value: 320000 },
  { from: 'UPI', to: 'Wallet', value: 180000 },
  { from: 'Wallet', to: 'ATM', value: 220000 },
  { from: 'Wallet', to: 'Bank', value: 380000 },
  { from: 'ATM', to: 'Bank', value: 290000 },
  { from: 'Web', to: 'UPI', value: 150000 },
  { from: 'Web', to: 'Wallet', value: 120000 },
];

// Velocity trend data
export const mockVelocityTrend = [
  { time: '00:00', velocity: 42 },
  { time: '04:00', velocity: 28 },
  { time: '08:00', velocity: 65 },
  { time: '12:00', velocity: 88 },
  { time: '16:00', velocity: 125 },
  { time: '20:00', velocity: 95 },
];

// Risk metrics over time
export const mockRiskTrend = [
  { date: 'Mon', score: 68 },
  { date: 'Tue', score: 72 },
  { date: 'Wed', score: 78 },
  { date: 'Thu', score: 85 },
  { date: 'Fri', score: 92 },
  { date: 'Sat', score: 88 },
  { date: 'Sun', score: 90 },
];

// Intelligence sharing reports
export const mockIntelligenceSharing = [
  {
    id: 'INT001',
    partner: 'National Payment Corporation',
    sharedAt: new Date(Date.now() - 7200000),
    clusterIds: ['CLU001', 'CLU003'],
    accountsShared: 7,
    confidenceScore: 0.94,
    status: 'active',
  },
  {
    id: 'INT002',
    partner: 'Financial Intelligence Unit',
    sharedAt: new Date(Date.now() - 14400000),
    clusterIds: ['CLU002'],
    accountsShared: 3,
    confidenceScore: 0.87,
    status: 'pending-review',
  },
  {
    id: 'INT003',
    partner: 'Reserve Bank Surveillance',
    sharedAt: new Date(Date.now() - 21600000),
    clusterIds: ['CLU001'],
    accountsShared: 4,
    confidenceScore: 0.96,
    status: 'active',
  },
];