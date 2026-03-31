export interface Account {
  id: string;
  name: string;
  riskScore: number;
  type: 'suspicious' | 'normal' | 'high-risk';
  channels: string[];
  balance: number;
  clusterId?: string;
  jurisdiction?: string;
  owner?: string;
  confidenceScore?: number;
  sanctionsMatch?: boolean;
}

export interface Transaction {
  id: string;
  fromAccount: string;
  toAccount: string;
  amount: number;
  channel: 'UPI' | 'ATM' | 'Wallet' | 'App' | 'Web';
  timestamp: Date;
  riskScore: number;
  status: 'completed' | 'pending' | 'flagged';
  pattern?: 'structuring' | 'fragmentation' | 'nesting' | 'rapid-movement';
  complexity?: number;
  sanctionsFlag?: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  riskScore: number;
  size: number;
  color: string;
  clusterId?: string;
}

export interface GraphLink {
  source: string;
  target: string;
  value: number;
  animated?: boolean;
}

export interface Cluster {
  id: string;
  name: string;
  accountCount: number;
  totalAmount: number;
  riskScore: number;
  detectedAt: Date;
  pattern?: 'structuring' | 'fragmentation' | 'nesting';
  jurisdictions?: string[];
  confidenceScore?: number;
}

export interface Alert {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  clusterId?: string;
  timestamp: Date;
  status: 'new' | 'investigating' | 'resolved';
  pattern?: 'structuring' | 'fragmentation' | 'nesting' | 'rapid-movement';
  confidenceScore?: number;
  sanctionsRelated?: boolean;
}