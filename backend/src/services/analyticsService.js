import Account from '../models/Account.js';
import Transaction from '../models/Transaction.js';
import Alert from '../models/Alert.js';
import Cluster from '../models/Cluster.js';

export async function getRiskDistribution() {
  const accounts = await Account.find().lean();
  const buckets = [
    { range: '0-20', severity: 'Low', min: 0, max: 20 },
    { range: '21-40', severity: 'Low', min: 21, max: 40 },
    { range: '41-60', severity: 'Medium', min: 41, max: 60 },
    { range: '61-80', severity: 'High', min: 61, max: 80 },
    { range: '81-100', severity: 'Critical', min: 81, max: 100 }
  ];

  return buckets.map((bucket) => ({
    range: bucket.range,
    severity: bucket.severity,
    count: accounts.filter((a) => a.riskScore >= bucket.min && a.riskScore <= bucket.max).length
  }));
}

export async function getJurisdictionRisks() {
  const accounts = await Account.find().lean();
  const groups = new Map();

  for (const account of accounts) {
    const key = account.jurisdiction || 'Unknown';
    if (!groups.has(key)) {
      groups.set(key, { count: 0, totalRisk: 0, highRisk: 0 });
    }
    const entry = groups.get(key);
    entry.count += 1;
    entry.totalRisk += account.riskScore;
    if (account.riskScore > 80) entry.highRisk += 1;
  }

  return Array.from(groups.entries()).map(([jurisdiction, g]) => ({
    jurisdiction,
    avgRisk: Math.round(g.totalRisk / g.count),
    accounts: g.count,
    highRisk: g.highRisk
  }));
}

export async function getOwnershipCorrelation() {
  const accounts = await Account.find().lean();
  const groups = new Map();

  for (const account of accounts) {
    const owner = account.owner || 'Unknown';
    if (!groups.has(owner)) groups.set(owner, []);
    groups.get(owner).push(account);
  }

  return Array.from(groups.entries())
    .filter(([, group]) => group.length > 1)
    .map(([owner, group]) => ({
      owner,
      accountCount: group.length,
      avgRisk: Math.round(group.reduce((sum, a) => sum + a.riskScore, 0) / group.length),
      totalBalance: group.reduce((sum, a) => sum + a.balance, 0),
      jurisdictions: [...new Set(group.map((a) => a.jurisdiction || 'Unknown'))]
    }))
    .sort((a, b) => b.avgRisk - a.avgRisk);
}

export async function getChannelFlow() {
  const transactions = await Transaction.find().lean();
  const flowMap = new Map();

  for (const txn of transactions) {
    const from = txn.channel;
    const to = txn.channel === 'UPI' ? 'Wallet' : txn.channel === 'Wallet' ? 'ATM' : txn.channel === 'App' ? 'UPI' : txn.channel === 'Web' ? 'Bank' : 'Bank';
    const key = `${from}->${to}`;
    flowMap.set(key, (flowMap.get(key) || 0) + txn.amount);
  }

  return Array.from(flowMap.entries()).map(([key, value]) => {
    const [from, to] = key.split('->');
    return { from, to, value };
  });
}

export async function getVelocityTrend() {
  const transactions = await Transaction.find().sort({ timestamp: 1 }).lean();
  const buckets = new Map();

  for (const txn of transactions) {
    const hour = new Date(txn.timestamp).toISOString().slice(11, 13);
    buckets.set(hour, (buckets.get(hour) || 0) + 1);
  }

  return Array.from(buckets.entries()).map(([hour, velocity]) => ({
    time: `${hour}:00`,
    velocity
  }));
}

export async function getRiskTrend() {
  const alerts = await Alert.find().sort({ timestamp: 1 }).lean();
  return alerts.map((a) => ({
    date: new Date(a.timestamp).toLocaleDateString('en-US', { weekday: 'short' }),
    score: a.severity === 'critical' ? 90 : a.severity === 'high' ? 75 : a.severity === 'medium' ? 55 : 30
  }));
}

export async function getComplexityData() {
  const transactions = await Transaction.find().sort({ timestamp: 1 }).lean();
  const monthMap = new Map();

  for (const txn of transactions) {
    const month = new Date(txn.timestamp).toLocaleString('en-US', { month: 'short' });
    if (!monthMap.has(month)) monthMap.set(month, []);
    monthMap.get(month).push(txn.complexity || 1);
  }

  return Array.from(monthMap.entries()).map(([month, values]) => ({
    month,
    complexity: Math.round(values.reduce((a, b) => a + b, 0) / values.length)
  }));
}

export async function getDashboardStats() {
  const [accounts, transactions, alerts, highRiskAccounts, flaggedTransactions, clusters] = await Promise.all([
    Account.countDocuments(),
    Transaction.countDocuments(),
    Alert.countDocuments(),
    Account.countDocuments({ riskScore: { $gt: 80 } }),
    Transaction.countDocuments({ status: 'flagged' }),
    Cluster.countDocuments()
  ]);

  return {
    totalAccounts: accounts,
    totalTransactions: transactions,
    totalAlerts: alerts,
    highRiskAccounts,
    flaggedTransactions,
    // Compatibility keys for alternative dashboard widgets.
    newAlerts: alerts,
    suspiciousClusters: clusters
  };
}

export async function getGraphData() {
  const [accounts, transactions] = await Promise.all([
    Account.find().lean(),
    Transaction.find().lean()
  ]);

  const nodes = accounts.map((a) => ({
    id: a.id,
    label: a.name,
    riskScore: a.riskScore,
    size: Math.max(8, Math.floor(a.riskScore / 8)),
    color: a.riskScore > 80 ? '#ef4444' : a.riskScore > 60 ? '#a855f7' : '#06b6d4',
    clusterId: a.clusterId || undefined
  }));

  const links = transactions.map((t) => ({
    source: t.fromAccount,
    target: t.toAccount,
    value: t.amount / 1000,
    animated: t.riskScore > 70
  }));

  return { nodes, links };
}
