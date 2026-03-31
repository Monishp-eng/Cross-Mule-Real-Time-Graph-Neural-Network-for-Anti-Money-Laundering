import Account from '../models/Account.js';
import Transaction from '../models/Transaction.js';
import Cluster from '../models/Cluster.js';
import Alert from '../models/Alert.js';
import IntelligencePartnership from '../models/IntelligencePartnership.js';

function buildAccounts() {
  const base = [
    { id: 'ACC0001', name: 'Aarav Sharma', riskScore: 88, type: 'high-risk', channels: ['UPI', 'App', 'Wallet'], balance: 240000, clusterId: 'CLSTR001', jurisdiction: 'India', owner: 'Aarav Sharma', confidenceScore: 0.92, sanctionsMatch: false },
    { id: 'ACC0002', name: 'Nisha Verma', riskScore: 81, type: 'suspicious', channels: ['Web', 'UPI'], balance: 120000, clusterId: 'CLSTR001', jurisdiction: 'UAE', owner: 'Aarav Sharma', confidenceScore: 0.86, sanctionsMatch: false },
    { id: 'ACC0003', name: 'Yusuf Khan', riskScore: 74, type: 'suspicious', channels: ['ATM', 'Wallet'], balance: 98000, clusterId: 'CLSTR002', jurisdiction: 'Singapore', owner: 'Yusuf Khan', confidenceScore: 0.8, sanctionsMatch: false },
    { id: 'ACC0004', name: 'Priya Iyer', riskScore: 44, type: 'normal', channels: ['App', 'UPI', 'Web'], balance: 310000, jurisdiction: 'India', owner: 'Priya Iyer', confidenceScore: 0.61, sanctionsMatch: false },
    { id: 'ACC0005', name: 'Rohan Mehta', riskScore: 91, type: 'high-risk', channels: ['Wallet', 'UPI', 'ATM'], balance: 670000, clusterId: 'CLSTR002', jurisdiction: 'UAE', owner: 'Yusuf Khan', confidenceScore: 0.95, sanctionsMatch: true },
    { id: 'ACC0006', name: 'Global Trade FZE', riskScore: 66, type: 'suspicious', channels: ['Web', 'App'], balance: 870000, clusterId: 'CLSTR003', jurisdiction: 'UAE', owner: 'Global Trade Group', confidenceScore: 0.77, sanctionsMatch: false },
    { id: 'ACC0007', name: 'Maya Rao', riskScore: 35, type: 'normal', channels: ['UPI', 'App'], balance: 86000, jurisdiction: 'India', owner: 'Maya Rao', confidenceScore: 0.51, sanctionsMatch: false },
    { id: 'ACC0008', name: 'Soren Holdings', riskScore: 83, type: 'high-risk', channels: ['Web', 'Wallet', 'Bank'], balance: 1450000, clusterId: 'CLSTR003', jurisdiction: 'UK', owner: 'Global Trade Group', confidenceScore: 0.89, sanctionsMatch: true },
    { id: 'ACC0009', name: 'Ananya Das', riskScore: 57, type: 'normal', channels: ['App', 'ATM'], balance: 123000, jurisdiction: 'India', owner: 'Ananya Das', confidenceScore: 0.58, sanctionsMatch: false },
    { id: 'ACC0010', name: 'Kite Exports', riskScore: 72, type: 'suspicious', channels: ['Web', 'UPI', 'Bank'], balance: 540000, clusterId: 'CLSTR001', jurisdiction: 'USA', owner: 'Kite Group', confidenceScore: 0.81, sanctionsMatch: false }
  ];

  return base;
}

function buildTransactions() {
  const now = Date.now();
  const transactions = [
    { id: 'TXN1001', fromAccount: 'ACC0001', toAccount: 'ACC0002', amount: 49000, channel: 'UPI', riskScore: 86, status: 'flagged', pattern: 'structuring', complexity: 6, sanctionsFlag: false },
    { id: 'TXN1002', fromAccount: 'ACC0002', toAccount: 'ACC0005', amount: 47000, channel: 'Wallet', riskScore: 89, status: 'flagged', pattern: 'fragmentation', complexity: 7, sanctionsFlag: false },
    { id: 'TXN1003', fromAccount: 'ACC0005', toAccount: 'ACC0008', amount: 93000, channel: 'Web', riskScore: 94, status: 'flagged', pattern: 'nesting', complexity: 8, sanctionsFlag: true },
    { id: 'TXN1004', fromAccount: 'ACC0003', toAccount: 'ACC0006', amount: 22000, channel: 'ATM', riskScore: 63, status: 'pending', pattern: 'rapid-movement', complexity: 5, sanctionsFlag: false },
    { id: 'TXN1005', fromAccount: 'ACC0004', toAccount: 'ACC0007', amount: 12000, channel: 'App', riskScore: 29, status: 'completed', complexity: 2, sanctionsFlag: false },
    { id: 'TXN1006', fromAccount: 'ACC0010', toAccount: 'ACC0001', amount: 76000, channel: 'Web', riskScore: 78, status: 'flagged', pattern: 'structuring', complexity: 6, sanctionsFlag: false },
    { id: 'TXN1007', fromAccount: 'ACC0009', toAccount: 'ACC0004', amount: 9000, channel: 'UPI', riskScore: 22, status: 'completed', complexity: 1, sanctionsFlag: false },
    { id: 'TXN1008', fromAccount: 'ACC0006', toAccount: 'ACC0003', amount: 41000, channel: 'Web', riskScore: 67, status: 'pending', pattern: 'fragmentation', complexity: 4, sanctionsFlag: false },
    { id: 'TXN1009', fromAccount: 'ACC0008', toAccount: 'ACC0010', amount: 115000, channel: 'Wallet', riskScore: 82, status: 'flagged', pattern: 'rapid-movement', complexity: 7, sanctionsFlag: true },
    { id: 'TXN1010', fromAccount: 'ACC0007', toAccount: 'ACC0009', amount: 3000, channel: 'App', riskScore: 15, status: 'completed', complexity: 1, sanctionsFlag: false }
  ];

  return transactions.map((t, idx) => ({ ...t, timestamp: new Date(now - idx * 5 * 60 * 1000) }));
}

function buildClusters() {
  return [
    { id: 'CLSTR001', name: 'Ring Alpha', accountCount: 3, totalAmount: 1720000, riskScore: 89, detectedAt: new Date(Date.now() - 2 * 86400000), pattern: 'structuring', jurisdictions: ['India', 'UAE', 'USA'], confidenceScore: 0.93 },
    { id: 'CLSTR002', name: 'Ring Beta', accountCount: 2, totalAmount: 768000, riskScore: 84, detectedAt: new Date(Date.now() - 4 * 86400000), pattern: 'fragmentation', jurisdictions: ['Singapore', 'UAE'], confidenceScore: 0.87 },
    { id: 'CLSTR003', name: 'Ring Gamma', accountCount: 2, totalAmount: 2320000, riskScore: 79, detectedAt: new Date(Date.now() - 6 * 86400000), pattern: 'nesting', jurisdictions: ['UAE', 'UK'], confidenceScore: 0.82 }
  ];
}

function buildAlerts() {
  return [
    { id: 'ALT001', title: 'Potential Structuring Detected', description: 'Multiple transactions just below regulatory threshold across linked accounts.', severity: 'critical', clusterId: 'CLSTR001', timestamp: new Date(Date.now() - 30 * 60 * 1000), status: 'new', pattern: 'structuring', confidenceScore: 0.94, sanctionsRelated: false },
    { id: 'ALT002', title: 'Cross-Border Fragmentation Pattern', description: 'Rapid distribution of funds to several jurisdictions.', severity: 'high', clusterId: 'CLSTR002', timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), status: 'investigating', pattern: 'fragmentation', confidenceScore: 0.88, sanctionsRelated: false },
    { id: 'ALT003', title: 'Sanctions Linked Entity Activity', description: 'Activity includes account with sanctions match signals.', severity: 'critical', clusterId: 'CLSTR003', timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000), status: 'new', pattern: 'nesting', confidenceScore: 0.96, sanctionsRelated: true }
  ];
}

function buildPartnerships() {
  return [
    {
      id: 'INT001',
      partner: 'National Compliance Cell',
      clusterIds: ['CLSTR001', 'CLSTR002'],
      accountsShared: 5,
      confidenceScore: 0.92,
      status: 'active',
      sharedAt: new Date(Date.now() - 8 * 60 * 60 * 1000)
    },
    {
      id: 'INT002',
      partner: 'Regional AML Network',
      clusterIds: ['CLSTR003'],
      accountsShared: 2,
      confidenceScore: 0.85,
      status: 'pending',
      sharedAt: new Date(Date.now() - 3 * 60 * 60 * 1000)
    }
  ];
}

export async function seedDatabase() {
  const accountsCount = await Account.countDocuments();
  if (accountsCount > 0) {
    return;
  }

  await Account.insertMany(buildAccounts());
  await Transaction.insertMany(buildTransactions());
  await Cluster.insertMany(buildClusters());
  await Alert.insertMany(buildAlerts());
  await IntelligencePartnership.insertMany(buildPartnerships());

  console.log('[seed] Initial dataset inserted');
}
