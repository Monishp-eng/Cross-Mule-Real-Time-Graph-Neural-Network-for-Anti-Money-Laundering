"""
GNN Detector - Graph Neural Network for mule ring detection
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import math
import logging
import os

try:
    import torch
except Exception:  # pragma: no cover - torch may be unavailable in minimal installs
    torch = None

try:
    from src.gnn_detector.train import MuleGraphSAGE
except Exception:  # pragma: no cover - keep runtime resilient
    MuleGraphSAGE = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleGNNDetector:
    """
    Simplified GNN-based mule detector using GraphSAGE-like aggregation.
    
    In production, use PyTorch Geometric or DGL. This is a reference implementation.
    
    Process:
    1. Extract node features (account-level and user-level attributes)
    2. Aggregate neighbor information (graph neighborhood embedding)
    3. Classify via neural network head
    4. Output: Mule ring probability + confidence
    """
    
    def __init__(self, embedding_dim: int = 64):
        self.embedding_dim = embedding_dim
        self.model_version = "GNN_v1.0_reference"
        self._trained_model = None
        self._trained_model_device = "cpu"
        self._load_trained_model_from_checkpoint()

    def _load_trained_model_from_checkpoint(self) -> None:
        """Load a trained GraphSAGE checkpoint if available, else keep heuristic mode."""
        if torch is None or MuleGraphSAGE is None:
            return

        model_path = os.getenv("GNN_MODEL_PATH", "models/gnn_mule_detector.pt")
        if not os.path.exists(model_path):
            return

        try:
            checkpoint = torch.load(model_path, map_location="cpu")
            cfg = checkpoint.get("config", {})
            in_dim = int(cfg.get("num_features", 10))
            hidden_dim = int(cfg.get("hidden_dim", 64))

            model = MuleGraphSAGE(in_dim=in_dim, hidden_dim=hidden_dim)
            model.load_state_dict(checkpoint["model_state_dict"])
            model.eval()

            self._trained_model = model
            self.model_version = "GraphSAGE_trained_v1"
            logger.info(f"Loaded trained GNN model from {model_path}")
        except Exception as exc:
            logger.warning(f"Could not load trained GNN model from {model_path}: {exc}")

    def _classify_with_trained_model(
        self,
        anchor_account: Dict,
        connected_accounts: List[Dict],
    ) -> Optional[Tuple[float, float]]:
        """Run inference using trained GraphSAGE model for one anchor-centric mini-graph."""
        if self._trained_model is None or torch is None:
            return None

        try:
            anchor_feat = self.extract_node_features(anchor_account)[0]
            neighbor_feats = [self.extract_node_features(acc)[0] for acc in connected_accounts]

            if neighbor_feats:
                x_np = np.vstack([anchor_feat] + neighbor_feats).astype(np.float32)
                # Build star graph: anchor(0) <-> each neighbor(i)
                edge_src = []
                edge_dst = []
                for idx in range(1, len(neighbor_feats) + 1):
                    edge_src.extend([0, idx])
                    edge_dst.extend([idx, 0])
                edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)
            else:
                x_np = np.vstack([anchor_feat]).astype(np.float32)
                edge_index = torch.zeros((2, 0), dtype=torch.long)

            x = torch.tensor(x_np, dtype=torch.float32)
            with torch.no_grad():
                logits = self._trained_model(x, edge_index)
                prob = torch.sigmoid(logits[0]).item()

            # Confidence heuristic for demo runtime.
            confidence = min(0.95, 0.6 + (len(connected_accounts) / 40.0))
            return float(prob), float(confidence)
        except Exception as exc:
            logger.warning(f"Trained model inference failed, falling back to heuristic: {exc}")
            return None
        
    def extract_node_features(self, account_data: Dict) -> np.ndarray:
        """
        Extract features for a single account node.
        
        Features (10-D vector):
        [account_age_days, velocity_score, balance, 
         txn_count_24h, unique_counterparties, device_count,
         avg_amount, structuring_score, is_new, has_high_velocity]
        
        Args:
            account_data: Account properties dictionary
        
        Returns: Feature vector (1, 10)
        """
        features = [
            min(account_data.get("account_age_days", 30) / 30.0, 1.0),  # Normalize
            account_data.get("velocity_score", 0.0),
            min(account_data.get("balance", 0) / 10000, 1.0),
            min(account_data.get("txn_count_24h", 0) / 100, 1.0),
            min(account_data.get("unique_counterparties", 0) / 50, 1.0),
            min(account_data.get("device_count", 1) / 10, 1.0),
            min(account_data.get("avg_amount", 0) / 10000, 1.0),
            account_data.get("structuring_score", 0.0),
            1.0 if account_data.get("is_new", False) else 0.0,
            1.0 if account_data.get("has_high_velocity", False) else 0.0
        ]
        
        return np.array(features, dtype=np.float32).reshape(1, -1)
    
    def aggregate_neighbor_features(
        self,
        node_features: np.ndarray,
        neighbor_features_list: List[np.ndarray],
        edge_weights: List[float]
    ) -> np.ndarray:
        """
        GraphSAGE-style neighbor aggregation.
        
        Takes node features + neighbors, computes weighted average + max pooling.
        
        Args:
            node_features: (1, 10) feature vector
            neighbor_features_list: List of neighbor feature vectors
            edge_weights: Edge weights for aggregation (e.g., transferred amounts)
        
        Returns: Aggregated features (1, 30)
        """
        if not neighbor_features_list or len(neighbor_features_list) == 0:
            # No neighbors → return node features + zeroed weighted/max neighbor slots.
            return np.concatenate(
                [node_features, np.zeros_like(node_features), np.zeros_like(node_features)],
                axis=1,
            )
        
        # Normalize edge weights (sum to 1)
        total_weight = sum(edge_weights)
        if total_weight == 0:
            normalized_weights = [1.0 / len(edge_weights)] * len(edge_weights)
        else:
            normalized_weights = [w / total_weight for w in edge_weights]
        
        # Weighted average of neighbors
        neighbors_stack = np.vstack(neighbor_features_list)  # (N, 10)
        weighted_neighbors = neighbors_stack.T @ np.array(normalized_weights)  # (10,)
        
        # Max pooling across neighbors
        max_neighbors = np.max(neighbors_stack, axis=0)  # (10,)
        
        # Concatenate: [node_features, weighted_avg, max_pool]
        aggregated = np.concatenate([
            node_features[0],
            weighted_neighbors,
            max_neighbors
        ])  # (30,)
        
        return aggregated.reshape(1, -1)
    
    def gnn_forward_pass(
        self,
        node_features: Dict,
        neighbors: Dict[str, List[Dict]],
        edge_weights: Dict[str, List[float]]
    ) -> Tuple[np.ndarray, Dict]:
        """
        Single GNN forward pass for a node.
        
        Aggregates neighborhood information and produces embeddings.
        
        Args:
            node_features: Node properties
            neighbors: {neighbor_id: [neighbor_data]}
            edge_weights: {neighbor_id: [edge_weights]}
        
        Returns: (embeddings, debug_info)
        """
        # Extract features
        node_feat = self.extract_node_features(node_features)
        
        # Get neighbor features and weights
        neighbor_features_list = [
            self.extract_node_features(n) for n in neighbors.get("accounts", [])
        ]
        weights = edge_weights.get("accounts", [1.0] * len(neighbor_features_list))
        
        # Aggregate
        aggregated = self.aggregate_neighbor_features(node_feat, neighbor_features_list, weights)
        
        logger.debug(f"Aggregated shape: {aggregated.shape}")
        
        return aggregated, {
            "node_dim": node_feat.shape,
            "neighbor_count": len(neighbor_features_list),
            "aggregated_dim": aggregated.shape
        }
    
    def classify_as_mule(
        self,
        aggregated_features: np.ndarray
    ) -> Tuple[float, float]:
        """
        Classification head: neural net-like score.
        
        In production, this would be a trained PyTorch model.
        Here: Simple linear classifier with hand-tuned weights.
        
        Args:
            aggregated_features: (1, 30) aggregated embeddings
        
        Returns: (probability, confidence)
        """
        # Pseudo neural net (reference implementation)
        # Weights learned from training data
        
        # Feature importance combines node risk and neighborhood behavior.
        # Index layout: [0..9=node, 10..19=weighted neighbors, 20..29=max neighbors]
        
        features = aggregated_features[0]

        node_velocity = features[1]
        node_counterparties = features[4]
        node_structuring = features[7]
        node_is_new = features[8]

        neigh_velocity = features[11]
        neigh_counterparties = features[14]
        neigh_structuring = features[17]
        neigh_max_counterparties = features[24]
        
        # Weighted combination (hackathon-friendly heuristic; trained model in future work)
        score = (
            0.22 * node_velocity
            + 0.14 * node_counterparties
            + 0.12 * node_structuring
            + 0.10 * node_is_new
            + 0.14 * neigh_velocity
            + 0.12 * neigh_counterparties
            + 0.08 * neigh_structuring
            + 0.08 * neigh_max_counterparties
        )
        
        # Apply sigmoid curve
        sigmoid_score = 1.0 / (1.0 + math.exp(-5.0 * (score - 0.5)))
        
        # Confidence decreases if few neighbors
        neighbor_count = min(len([f for f in features if f > 0.1]), 10)
        confidence = min(0.95, 0.5 + (neighbor_count / 20.0))
        
        logger.debug(f"Mule classification: {sigmoid_score:.3f} ± {confidence:.3f}")
        
        return sigmoid_score, confidence
    
    def detect_mule_ring(
        self,
        anchor_account: Dict,
        connected_accounts: List[Dict],
        transaction_graph: Dict
    ) -> Dict:
        """
        Detect if an account is part of a mule ring.
        
        Args:
            anchor_account: Central account to investigate
            connected_accounts: Accounts connected to anchor
            transaction_graph: Full transaction graph structure
        
        Returns: Detection result with score and pattern
        """
        # Step 1: Extract features
        self.extract_node_features(anchor_account)
        
        # Step 2: Find neighbors
        neighbors = {
            "accounts": connected_accounts
        }
        edge_weights = {
            "accounts": [
                acc.get("transfer_amount", 1000) 
                for acc in connected_accounts
            ]
        }
        
        # Step 3: GNN forward pass
        aggregated, debug_info = self.gnn_forward_pass(
            anchor_account,
            neighbors,
            edge_weights
        )
        
        # Step 4: Classification
        model_result = self._classify_with_trained_model(anchor_account, connected_accounts)
        if model_result is not None:
            mule_prob, confidence = model_result
        else:
            mule_prob, confidence = self.classify_as_mule(aggregated)
        
        # Step 5: Pattern analysis
        pattern = self.analyze_pattern(anchor_account, connected_accounts)
        
        return {
            "anchor_account_id": anchor_account.get("account_id"),
            "mule_probability": mule_prob,
            "confidence": confidence,
            "decision": "HIGH_RISK" if mule_prob > 0.7 else "MEDIUM_RISK" if mule_prob > 0.4 else "LOW_RISK",
            "pattern_type": pattern,
            "num_connected_accounts": len(connected_accounts),
            "model_version": self.model_version,
            "debug": debug_info
        }
    
    def analyze_pattern(
        self,
        anchor_account: Dict,
        connected_accounts: List[Dict]
    ) -> str:
        """
        Analyze transaction pattern topology.
        
        Returns: Pattern type (STAR, CHAIN, RING, UNKNOWN)
        """
        if not connected_accounts:
            return "ISOLATED"
        
        # Star: hub account with many outgoing transfers
        if len(connected_accounts) > 10 and anchor_account.get("outgoing_txn_count", 0) > len(connected_accounts):
            return "STAR"
        
        # Chain: sequential transfers A→B→C→D
        if len(connected_accounts) in [3, 4, 5]:
            return "CHAIN"
        
        # Ring: circular transfers
        # (would need more graph context to detect)
        
        return "UNKNOWN"


# Example usage
if __name__ == "__main__":
    detector = SimpleGNNDetector()
    
    # Sample anchor account (suspected hub)
    anchor = {
        "account_id": "ACC_12345",
        "account_age_days": 2,
        "velocity_score": 0.9,
        "balance": 500,
        "txn_count_24h": 50,
        "unique_counterparties": 38,
        "device_count": 15,
        "avg_amount": 1000,
        "structuring_score": 0.88,
        "is_new": True,
        "has_high_velocity": True,
        "outgoing_txn_count": 50
    }
    
    # Connected accounts
    connected = [
        {
            "account_id": "ACC_67890",
            "account_age_days": 5,
            "velocity_score": 0.7,
            "transfer_amount": 1000,
            "txn_count_24h": 20
        } for _ in range(10)  # 10 connected accounts
    ]
    
    # Detect
    result = detector.detect_mule_ring(anchor, connected, {})
    
    print("Mule Ring Detection Result:")
    print(f"  Probability: {result['mule_probability']:.3f}")
    print(f"  Confidence: {result['confidence']:.3f}")
    print(f"  Decision: {result['decision']}")
    print(f"  Pattern: {result['pattern_type']}")
    print(f"  Connected Accounts: {result['num_connected_accounts']}")
