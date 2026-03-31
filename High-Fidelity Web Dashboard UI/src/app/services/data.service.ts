import { config } from '../config/config';
import apiService from './api.service';
import {
  mockAccounts,
  mockTransactions,
  mockClusters,
  mockAlerts,
  mockGraphNodes,
  mockGraphLinks,
  mockChannelFlow,
  mockVelocityTrend,
  mockRiskTrend,
  mockIntelligenceSharing,
} from '../mockData';
import { Account, Transaction, Cluster, Alert, GraphNode, GraphLink } from '../types';

/**
 * Data service that switches between mock data and real API calls
 * based on configuration
 */

// Helper to simulate API delay
const simulateDelay = (ms: number = 500) =>
  new Promise((resolve) => setTimeout(resolve, ms));

export const dataService = {
  // ============================================
  // ACCOUNTS
  // ============================================
  async getAccounts(): Promise<Account[]> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve(mockAccounts);
    }
    return apiService.getAccounts();
  },

  async getAccountById(id: string): Promise<Account> {
    if (config.useMockData) {
      await simulateDelay();
      const account = mockAccounts.find((a) => a.id === id);
      if (!account) throw new Error('Account not found');
      return Promise.resolve(account);
    }
    return apiService.getAccountById(id);
  },

  // ============================================
  // TRANSACTIONS
  // ============================================
  async getTransactions(params?: any): Promise<Transaction[]> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve(mockTransactions);
    }
    return apiService.getTransactions(params);
  },

  async getTransactionById(id: string): Promise<Transaction> {
    if (config.useMockData) {
      await simulateDelay();
      const transaction = mockTransactions.find((t) => t.id === id);
      if (!transaction) throw new Error('Transaction not found');
      return Promise.resolve(transaction);
    }
    return apiService.getTransactionById(id);
  },

  async getLiveTransactions(): Promise<Transaction[]> {
    if (config.useMockData) {
      await simulateDelay(200);
      return Promise.resolve(mockTransactions);
    }
    return apiService.getLiveTransactions();
  },

  // ============================================
  // CLUSTERS
  // ============================================
  async getClusters(): Promise<Cluster[]> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve(mockClusters);
    }
    return apiService.getClusters();
  },

  async getClusterById(id: string): Promise<Cluster> {
    if (config.useMockData) {
      await simulateDelay();
      const cluster = mockClusters.find((c) => c.id === id);
      if (!cluster) throw new Error('Cluster not found');
      return Promise.resolve(cluster);
    }
    return apiService.getClusterById(id);
  },

  // ============================================
  // ALERTS
  // ============================================
  async getAlerts(params?: any): Promise<Alert[]> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve(mockAlerts);
    }
    return apiService.getAlerts(params);
  },

  async getAlertById(id: string): Promise<Alert> {
    if (config.useMockData) {
      await simulateDelay();
      const alert = mockAlerts.find((a) => a.id === id);
      if (!alert) throw new Error('Alert not found');
      return Promise.resolve(alert);
    }
    return apiService.getAlertById(id);
  },

  async updateAlertStatus(id: string, status: string): Promise<void> {
    if (config.useMockData) {
      await simulateDelay();
      console.log(`Mock: Updated alert ${id} to status ${status}`);
      return Promise.resolve();
    }
    return apiService.updateAlertStatus(id, status);
  },

  async dismissAlert(id: string): Promise<void> {
    if (config.useMockData) {
      await simulateDelay();
      console.log(`Mock: Dismissed alert ${id}`);
      return Promise.resolve();
    }
    return apiService.dismissAlert(id);
  },

  // ============================================
  // GRAPH DATA
  // ============================================
  async getGraphNodes(): Promise<GraphNode[]> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve(mockGraphNodes);
    }
    return apiService.getGraphNodes();
  },

  async getGraphLinks(): Promise<GraphLink[]> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve(mockGraphLinks);
    }
    return apiService.getGraphLinks();
  },

  async getGraphData(): Promise<{ nodes: GraphNode[]; links: GraphLink[] }> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve({ nodes: mockGraphNodes, links: mockGraphLinks });
    }
    return apiService.getGraphData();
  },

  // ============================================
  // RISK SCORING
  // ============================================
  async getRiskDistribution(): Promise<any[]> {
    if (config.useMockData) {
      await simulateDelay();
      // Calculate from mock accounts
      return Promise.resolve([
        {
          range: '0-20',
          count: mockAccounts.filter((a) => a.riskScore <= 20).length,
          severity: 'Low',
        },
        {
          range: '21-40',
          count: mockAccounts.filter((a) => a.riskScore > 20 && a.riskScore <= 40).length,
          severity: 'Low',
        },
        {
          range: '41-60',
          count: mockAccounts.filter((a) => a.riskScore > 40 && a.riskScore <= 60).length,
          severity: 'Medium',
        },
        {
          range: '61-80',
          count: mockAccounts.filter((a) => a.riskScore > 60 && a.riskScore <= 80).length,
          severity: 'High',
        },
        {
          range: '81-100',
          count: mockAccounts.filter((a) => a.riskScore > 80).length,
          severity: 'Critical',
        },
      ]);
    }
    return apiService.getRiskDistribution();
  },

  async getJurisdictionRisks(): Promise<any[]> {
    if (config.useMockData) {
      await simulateDelay();
      // Calculate from mock accounts
      const jurisdictions = mockAccounts.reduce((acc, account) => {
        const jurisdiction = account.jurisdiction || 'Unknown';
        if (!acc[jurisdiction]) {
          acc[jurisdiction] = { count: 0, totalRisk: 0, highRisk: 0 };
        }
        acc[jurisdiction].count++;
        acc[jurisdiction].totalRisk += account.riskScore;
        if (account.riskScore > 80) acc[jurisdiction].highRisk++;
        return acc;
      }, {} as Record<string, { count: number; totalRisk: number; highRisk: number }>);

      return Promise.resolve(
        Object.entries(jurisdictions).map(([jurisdiction, data]) => ({
          jurisdiction,
          avgRisk: Math.round(data.totalRisk / data.count),
          accounts: data.count,
          highRisk: data.highRisk,
        }))
      );
    }
    return apiService.getJurisdictionRisks();
  },

  async getOwnershipCorrelation(): Promise<any[]> {
    if (config.useMockData) {
      await simulateDelay();
      // Calculate from mock accounts
      const ownershipGroups = mockAccounts.reduce((acc, account) => {
        const owner = account.owner || 'Unknown';
        if (!acc[owner]) {
          acc[owner] = [];
        }
        acc[owner].push(account);
        return acc;
      }, {} as Record<string, typeof mockAccounts>);

      return Promise.resolve(
        Object.entries(ownershipGroups)
          .filter(([owner, accounts]) => accounts.length > 1)
          .map(([owner, accounts]) => ({
            owner,
            accountCount: accounts.length,
            avgRisk: Math.round(
              accounts.reduce((sum, acc) => sum + acc.riskScore, 0) / accounts.length
            ),
            totalBalance: accounts.reduce((sum, acc) => sum + acc.balance, 0),
            jurisdictions: [...new Set(accounts.map((a) => a.jurisdiction))],
          }))
      );
    }
    return apiService.getOwnershipCorrelation();
  },

  // ============================================
  // CHANNEL FLOW
  // ============================================
  async getChannelFlow(): Promise<any[]> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve(mockChannelFlow);
    }
    return apiService.getChannelFlow();
  },

  async getVelocityTrend(): Promise<any[]> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve(mockVelocityTrend);
    }
    return apiService.getVelocityTrend();
  },

  // ============================================
  // REPORTS
  // ============================================
  async getRiskTrend(params?: any): Promise<any[]> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve(mockRiskTrend);
    }
    return apiService.getRiskTrend(params);
  },

  async getComplexityData(): Promise<any[]> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve([
        { month: 'Jan', complexity: 45 },
        { month: 'Feb', complexity: 52 },
        { month: 'Mar', complexity: 68 },
        { month: 'Apr', complexity: 75 },
        { month: 'May', complexity: 82 },
        { month: 'Jun', complexity: 78 },
      ]);
    }
    return apiService.getComplexityData();
  },

  async generateReport(reportType: string, params?: any): Promise<any> {
    if (config.useMockData) {
      await simulateDelay(1000);
      return Promise.resolve({ reportId: 'MOCK_REPORT_' + Date.now(), status: 'generated' });
    }
    return apiService.generateReport(reportType, params);
  },

  async exportReport(reportId: string, format: 'pdf' | 'csv'): Promise<Blob> {
    if (config.useMockData) {
      await simulateDelay(1000);
      const mockData = 'Mock report data';
      return Promise.resolve(new Blob([mockData], { type: 'text/plain' }));
    }
    return apiService.exportReport(reportId, format);
  },

  // ============================================
  // INTELLIGENCE SHARING
  // ============================================
  async getIntelligenceSharing(): Promise<any[]> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve(mockIntelligenceSharing);
    }
    return apiService.getIntelligenceSharing();
  },

  async createSharingPartnership(data: any): Promise<any> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve({ id: 'MOCK_PARTNERSHIP_' + Date.now(), status: 'created' });
    }
    return apiService.createSharingPartnership(data);
  },

  // ============================================
  // STATISTICS
  // ============================================
  async getDashboardStats(): Promise<any> {
    if (config.useMockData) {
      await simulateDelay();
      return Promise.resolve({
        totalAccounts: mockAccounts.length,
        totalTransactions: mockTransactions.length,
        totalClusters: mockClusters.length,
        totalAlerts: mockAlerts.length,
        highRiskAccounts: mockAccounts.filter((a) => a.riskScore > 80).length,
        flaggedTransactions: mockTransactions.filter((t) => t.status === 'flagged').length,
      });
    }
    return apiService.getDashboardStats();
  },
};

export default dataService;
