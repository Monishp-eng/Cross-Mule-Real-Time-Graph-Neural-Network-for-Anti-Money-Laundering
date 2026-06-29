"""GraphSAGE model definition for account-level fraud detection."""

from __future__ import annotations

try:
    import torch
    import torch.nn.functional as F
    from torch import nn
    from torch_geometric.nn import SAGEConv
    _GNN_RUNTIME_AVAILABLE = True
except Exception:  # pragma: no cover
    torch = None
    F = None
    nn = None
    SAGEConv = None
    _GNN_RUNTIME_AVAILABLE = False


if _GNN_RUNTIME_AVAILABLE:
    class GraphSAGEFraudModel(nn.Module):
        """Two-layer GraphSAGE classifier returning node-level fraud logits."""

        def __init__(self, in_dim: int, hidden_dim: int = 64, dropout: float = 0.2):
            super().__init__()
            self.conv1 = SAGEConv(in_dim, hidden_dim)
            self.conv2 = SAGEConv(hidden_dim, hidden_dim)
            self.dropout = float(dropout)
            self.head = nn.Linear(hidden_dim, 1)

        def embed(self, x, edge_index):
            x = self.conv1(x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
            x = self.conv2(x, edge_index)
            x = F.relu(x)
            return x

        def forward(self, x, edge_index):
            embedding = self.embed(x, edge_index)
            logits = self.head(embedding).squeeze(-1)
            return logits
else:
    class GraphSAGEFraudModel:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise RuntimeError("torch and torch_geometric are required for GraphSAGEFraudModel")


# Backward-compatible alias used by existing modules.
MuleGraphSAGE = GraphSAGEFraudModel
