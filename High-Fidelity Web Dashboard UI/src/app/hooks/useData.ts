import { useApi, usePolling, useMutation } from './useApi';
import dataService from '../services/data.service';
import { Account, Transaction, Cluster, Alert, GraphNode, GraphLink } from '../types';
import { config } from '../config/config';

// ============================================
// ACCOUNTS
// ============================================
export function useAccounts() {
  return useApi<Account[]>(() => dataService.getAccounts());
}

export function useAccount(id: string) {
  return useApi<Account>(() => dataService.getAccountById(id), {
    enabled: !!id,
  });
}

// ============================================
// TRANSACTIONS
// ============================================
export function useTransactions(params?: { page?: number; limit?: number; status?: string }) {
  return useApi<Transaction[]>(() => dataService.getTransactions(params));
}

export function useTransaction(id: string) {
  return useApi<Transaction>(() => dataService.getTransactionById(id), {
    enabled: !!id,
  });
}

// Live transactions with polling (updates every 3 seconds)
export function useLiveTransactions(interval?: number) {
  return usePolling<Transaction[]>(
    () => dataService.getLiveTransactions(),
    interval || config.polling.transactions,
    { autoStart: config.enableLiveUpdates }
  );
}

// ============================================
// CLUSTERS
// ============================================
export function useClusters() {
  return useApi<Cluster[]>(() => dataService.getClusters());
}

export function useCluster(id: string) {
  return useApi<Cluster>(() => dataService.getClusterById(id), {
    enabled: !!id,
  });
}

// ============================================
// ALERTS
// ============================================
export function useAlerts(params?: { status?: string; severity?: string }) {
  return useApi<Alert[]>(() => dataService.getAlerts(params));
}

export function useAlert(id: string) {
  return useApi<Alert>(() => dataService.getAlertById(id), {
    enabled: !!id,
  });
}

export function useUpdateAlertStatus() {
  return useMutation<void, { id: string; status: string }>(
    ({ id, status }) => dataService.updateAlertStatus(id, status)
  );
}

export function useDismissAlert() {
  return useMutation<void, string>((id) => dataService.dismissAlert(id));
}

// ============================================
// GRAPH DATA
// ============================================
export function useGraphNodes() {
  return useApi<GraphNode[]>(() => dataService.getGraphNodes());
}

export function useGraphLinks() {
  return useApi<GraphLink[]>(() => dataService.getGraphLinks());
}

export function useGraphData() {
  return useApi<{ nodes: GraphNode[]; links: GraphLink[] }>(() => dataService.getGraphData());
}

// ============================================
// RISK SCORING
// ============================================
export function useRiskDistribution() {
  return useApi<any[]>(() => dataService.getRiskDistribution());
}

export function useJurisdictionRisks() {
  return useApi<any[]>(() => dataService.getJurisdictionRisks());
}

export function useOwnershipCorrelation() {
  return useApi<any[]>(() => dataService.getOwnershipCorrelation());
}

// ============================================
// CHANNEL FLOW
// ============================================
export function useChannelFlow() {
  return useApi<any[]>(() => dataService.getChannelFlow());
}

export function useVelocityTrend() {
  return useApi<any[]>(() => dataService.getVelocityTrend());
}

// ============================================
// REPORTS
// ============================================
export function useRiskTrend(period?: string) {
  return useApi<any[]>(() => dataService.getRiskTrend({ period }));
}

export function useComplexityData() {
  return useApi<any[]>(() => dataService.getComplexityData());
}

export function useGenerateReport() {
  return useMutation<any, { reportType: string; params?: any }>(
    ({ reportType, params }) => dataService.generateReport(reportType, params)
  );
}

export function useExportReport() {
  return useMutation<Blob, { reportId: string; format: 'pdf' | 'csv' }>(
    ({ reportId, format }) => dataService.exportReport(reportId, format)
  );
}

// ============================================
// INTELLIGENCE SHARING
// ============================================
export function useIntelligenceSharing() {
  return useApi<any[]>(() => dataService.getIntelligenceSharing());
}

export function useCreateSharingPartnership() {
  return useMutation<any, any>((data) => dataService.createSharingPartnership(data));
}

// ============================================
// STATISTICS
// ============================================
export function useDashboardStats() {
  return useApi<any>(() => dataService.getDashboardStats());
}

// Polling dashboard stats every 10 seconds
export function useLiveDashboardStats(interval?: number) {
  return usePolling<any>(
    () => dataService.getDashboardStats(),
    interval || config.polling.dashboard,
    { autoStart: config.enableLiveUpdates }
  );
}