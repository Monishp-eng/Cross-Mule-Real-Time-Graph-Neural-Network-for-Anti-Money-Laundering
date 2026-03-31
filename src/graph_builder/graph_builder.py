"""
Graph Builder - Constructs and updates Neo4j entity graph from normalized transactions
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Base class for graph nodes"""
    node_id: str
    node_type: str  # USER, ACCOUNT, TRANSACTION, DEVICE, LOCATION
    properties: Dict
    
    def get_cypher_create(self) -> str:
        """Generate Neo4j CREATE statement"""
        props_str = ", ".join(
            f"{k}: {self._format_value(v)}" 
            for k, v in self.properties.items()
        )
        return f"CREATE (n:{self.node_type} {{{props_str}}})"
    
    @staticmethod
    def _format_value(v):
        """Format Python value for Cypher"""
        if isinstance(v, str):
            return f"'{v}'"
        elif isinstance(v, bool):
            return "true" if v else "false"
        elif isinstance(v, (int, float)):
            return str(v)
        elif v is None:
            return "null"
        else:
            return f"'{str(v)}'"


@dataclass
class GraphEdge:
    """Graph relationship"""
    from_node_id: str
    to_node_id: str
    rel_type: str  # HAS_ACCOUNT, SENT_TO, IS_ON_DEVICE, etc.
    properties: Dict
    
    def get_cypher_merge(self) -> str:
        """Generate Neo4j MERGE statement"""
        props_str = ", ".join(
            f"{k}: {self._format_value(v)}" 
            for k, v in self.properties.items()
        )
        if props_str:
            return f"MERGE (a)-[r:{self.rel_type} {{{props_str}}}]->(b)"
        else:
            return f"MERGE (a)-[r:{self.rel_type}]->(b)"
    
    @staticmethod
    def _format_value(v):
        if isinstance(v, str):
            return f"'{v}'"
        elif isinstance(v, bool):
            return "true" if v else "false"
        elif isinstance(v, (int, float)):
            return str(v)
        elif v is None:
            return "null"
        else:
            return f"'{str(v)}'"


class GraphBuilder:
    """
    Builds and updates Neo4j entity graph from transactions.
    
    Node types:
    - USER: Individual accounts
    - ACCOUNT: Payment accounts (wallets, cards, etc.)
    - TRANSACTION: Transfer events
    - DEVICE: Mobile, web, ATM devices
    - LOCATION: Geographic coordinates
    
    Edge types:
    - HAS_ACCOUNT: USER → ACCOUNT
    - SENT_TO: ACCOUNT → ACCOUNT
    - IS_ON_DEVICE: USER/ACCOUNT → DEVICE
    - LOCATED_AT: DEVICE → LOCATION
    - LINKED_WITH: USER → USER
    """
    
    def __init__(self, neo4j_client=None):
        """
        Initialize graph builder
        
        Args:
            neo4j_client: Neo4j Aura client (injected for testing)
        """
        self.neo4j_client = neo4j_client
        self.pending_queries = []

    def _ingest_transaction_to_neo4j(self, normalized_txn: Dict[str, Any]) -> None:
        """Write transaction entities and relationships to Neo4j using a single parameterized query."""
        location_id = (
            f"LOC_{normalized_txn['location']['country']}_"
            f"{int(normalized_txn['location']['latitude'])}_"
            f"{int(normalized_txn['location']['longitude'])}"
        )

        query = """
        MERGE (src:Account {account_id: $source_account_id})
        ON CREATE SET src.created_at = datetime($now), src.transaction_count = 0, src.risk_score = 0.0
        SET src.channel = $channel, src.transaction_count = coalesce(src.transaction_count, 0) + 1

        MERGE (dst:Account {account_id: $dest_account_id})
        ON CREATE SET dst.created_at = datetime($now), dst.transaction_count = 0, dst.risk_score = 0.0
        SET dst.channel = $channel

        MERGE (dev:Device {device_id: $device_id})
        ON CREATE SET dev.first_seen = datetime($now), dev.account_count = 0
        SET dev.device_type = 'UNKNOWN', dev.account_count = coalesce(dev.account_count, 0) + 1

        MERGE (loc:Location {location_id: $location_id})
        ON CREATE SET loc.latitude = $latitude, loc.longitude = $longitude, loc.country = $country

        MERGE (txn:Transaction {txn_id: $event_id})
        SET txn.amount = $amount,
            txn.currency = $currency,
            txn.timestamp = datetime($timestamp),
            txn.channel = $channel

        MERGE (src)-[sent:SENT_TO {txn_id: $event_id}]->(dst)
        SET sent.amount = $amount,
            sent.timestamp = datetime($timestamp),
            sent.velocity_score = 0.5

        MERGE (src)-[on_dev:IS_ON_DEVICE]->(dev)
        ON CREATE SET on_dev.first_seen = datetime($now), on_dev.login_count = 1
        ON MATCH SET on_dev.login_count = coalesce(on_dev.login_count, 0) + 1

        MERGE (dev)-[at_loc:LOCATED_AT]->(loc)
        SET at_loc.timestamp = datetime($timestamp),
            at_loc.frequency = coalesce(at_loc.frequency, 0) + 1

        MERGE (txn)-[:PART_OF]->(src)
        """

        params = {
            "event_id": normalized_txn["event_id"],
            "timestamp": normalized_txn["timestamp"],
            "now": datetime.now().isoformat(),
            "source_account_id": normalized_txn["source_account_id"],
            "dest_account_id": normalized_txn["dest_account_id"],
            "amount": float(normalized_txn["amount"]),
            "currency": normalized_txn["currency"],
            "channel": normalized_txn["channel"],
            "device_id": normalized_txn["device_id"],
            "location_id": location_id,
            "latitude": float(normalized_txn["location"]["latitude"]),
            "longitude": float(normalized_txn["location"]["longitude"]),
            "country": normalized_txn["location"]["country"],
        }

        self.neo4j_client.execute(query, params)
    
    def extract_entities_from_transaction(self, normalized_txn: Dict) -> List[GraphNode]:
        """Extract entities (nodes) from a normalized transaction"""
        nodes = []
        
        # Create ACCOUNT nodes
        src_account = GraphNode(
            node_id=normalized_txn["source_account_id"],
            node_type="Account",
            properties={
                "account_id": normalized_txn["source_account_id"],
                "channel": normalized_txn["channel"],
                "created_at": datetime.now().isoformat(),
                "transaction_count": 1,
                "risk_score": 0.0
            }
        )
        nodes.append(src_account)
        
        dst_account = GraphNode(
            node_id=normalized_txn["dest_account_id"],
            node_type="Account",
            properties={
                "account_id": normalized_txn["dest_account_id"],
                "channel": normalized_txn["channel"],
                "created_at": datetime.now().isoformat(),
                "transaction_count": 0,
                "risk_score": 0.0
            }
        )
        nodes.append(dst_account)
        
        # Create DEVICE node
        device = GraphNode(
            node_id=normalized_txn["device_id"],
            node_type="Device",
            properties={
                "device_id": normalized_txn["device_id"],
                "device_type": "UNKNOWN",
                "first_seen": datetime.now().isoformat(),
                "account_count": 1
            }
        )
        nodes.append(device)
        
        # Create LOCATION node
        location = GraphNode(
            node_id=f"LOC_{normalized_txn['location']['country']}_{int(normalized_txn['location']['latitude'])}_{int(normalized_txn['location']['longitude'])}",
            node_type="Location",
            properties={
                "latitude": normalized_txn["location"]["latitude"],
                "longitude": normalized_txn["location"]["longitude"],
                "country": normalized_txn["location"]["country"]
            }
        )
        nodes.append(location)
        
        # Create TRANSACTION node
        txn = GraphNode(
            node_id=normalized_txn["event_id"],
            node_type="Transaction",
            properties={
                "txn_id": normalized_txn["event_id"],
                "amount": normalized_txn["amount"],
                "currency": normalized_txn["currency"],
                "timestamp": normalized_txn["timestamp"],
                "channel": normalized_txn["channel"]
            }
        )
        nodes.append(txn)
        
        return nodes
    
    def extract_relationships_from_transaction(
        self,
        normalized_txn: Dict
    ) -> List[GraphEdge]:
        """Extract relationships (edges) from a normalized transaction"""
        edges = []
        
        # SENT_TO edge: source → destination account
        edges.append(GraphEdge(
            from_node_id=normalized_txn["source_account_id"],
            to_node_id=normalized_txn["dest_account_id"],
            rel_type="SENT_TO",
            properties={
                "amount": normalized_txn["amount"],
                "timestamp": normalized_txn["timestamp"],
                "txn_id": normalized_txn["event_id"],
                "velocity_score": 0.5  # Will be computed later
            }
        ))
        
        # IS_ON_DEVICE edges
        edges.append(GraphEdge(
            from_node_id=normalized_txn["source_account_id"],
            to_node_id=normalized_txn["device_id"],
            rel_type="IS_ON_DEVICE",
            properties={
                "first_seen": datetime.now().isoformat(),
                "login_count": 1
            }
        ))
        
        # LOCATED_AT edge: device → location
        location_id = f"LOC_{normalized_txn['location']['country']}_{int(normalized_txn['location']['latitude'])}_{int(normalized_txn['location']['longitude'])}"
        edges.append(GraphEdge(
            from_node_id=normalized_txn["device_id"],
            to_node_id=location_id,
            rel_type="LOCATED_AT",
            properties={
                "timestamp": normalized_txn["timestamp"],
                "frequency": 1
            }
        ))
        
        # PART_OF edge: transaction belongs to source account
        edges.append(GraphEdge(
            from_node_id=normalized_txn["event_id"],
            to_node_id=normalized_txn["source_account_id"],
            rel_type="PART_OF",
            properties={"timestamp": normalized_txn["timestamp"]}
        ))
        
        return edges
    
    def ingest_transaction(self, normalized_txn: Dict) -> bool:
        """
        Ingest a transaction: create/update entities and relationships
        
        Returns: Success boolean
        """
        try:
            if self.neo4j_client:
                self._ingest_transaction_to_neo4j(normalized_txn)
                logger.info(f"Upserted transaction {normalized_txn['event_id']} in Neo4j")
                return True

            nodes = self.extract_entities_from_transaction(normalized_txn)
            edges = self.extract_relationships_from_transaction(normalized_txn)
            
            # Generate Cypher queries (would execute against Neo4j)
            cypher_queries = []
            for node in nodes:
                cypher_queries.append(node.get_cypher_create())
            for edge in edges:
                cypher_queries.append(edge.get_cypher_merge())
            
            logger.info(f"Generated {len(cypher_queries)} Cypher queries for txn {normalized_txn['event_id']}")
            
            self.pending_queries.extend(cypher_queries)
            
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting transaction: {e}")
            return False

    def get_connected_accounts(self, account_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Return recently connected counterparties for an account.

        This is a lightweight helper for real-time mule neighborhood scoring.
        """
        if not self.neo4j_client or not hasattr(self.neo4j_client, "query"):
            return []

        query = """
        MATCH (src:Account {account_id: $account_id})-[s:SENT_TO]->(dst:Account)
        RETURN dst.account_id AS account_id,
               count(s) AS edge_count,
               max(s.amount) AS max_transfer_amount,
               avg(s.amount) AS avg_transfer_amount
        ORDER BY edge_count DESC, max_transfer_amount DESC
        LIMIT $limit
        """

        try:
            rows = self.neo4j_client.query(query, {"account_id": account_id, "limit": limit})
            connected = []
            for row in rows:
                connected.append(
                    {
                        "account_id": row.get("account_id"),
                        "transfer_amount": float(row.get("avg_transfer_amount") or 0.0),
                        "txn_count_24h": int(row.get("edge_count") or 0),
                    }
                )
            return connected
        except Exception as exc:
            logger.warning(f"Could not fetch connected accounts for {account_id}: {exc}")
            return []

    def transaction_exists(self, txn_id: str) -> bool:
        """Check if a transaction with the given id already exists in graph storage."""
        if not self.neo4j_client or not hasattr(self.neo4j_client, "query"):
            return False

        query = """
        MATCH (txn:Transaction {txn_id: $txn_id})
        RETURN count(txn) > 0 AS exists
        """
        try:
            rows = self.neo4j_client.query(query, {"txn_id": txn_id})
            return bool(rows and rows[0].get("exists"))
        except Exception as exc:
            logger.warning(f"Could not check transaction existence for {txn_id}: {exc}")
            return False

    def get_account_activity(self, account_id: str) -> Dict[str, Any]:
        """Fetch lightweight account activity metrics for risk scoring."""
        if not self.neo4j_client or not hasattr(self.neo4j_client, "query"):
            return {
                "txn_count_1h": 1,
                "txn_count_24h": 1,
                "unique_counterparties": 1,
                "avg_amount": 0.0,
                "recent_amounts": [],
            }

        summary_query = """
        MATCH (src:Account {account_id: $account_id})-[s:SENT_TO]->(dst:Account)
        WITH src, s, dst
        RETURN
            count(s) AS txn_count_24h,
            count(CASE WHEN s.timestamp >= datetime() - duration('PT1H') THEN 1 END) AS txn_count_1h,
            count(DISTINCT dst) AS unique_counterparties,
            coalesce(avg(s.amount), 0.0) AS avg_amount
        """

        amounts_query = """
        MATCH (:Account {account_id: $account_id})-[s:SENT_TO]->(:Account)
        RETURN s.amount AS amount
        ORDER BY s.timestamp DESC
        LIMIT 20
        """

        try:
            summary_rows = self.neo4j_client.query(summary_query, {"account_id": account_id})
            amounts_rows = self.neo4j_client.query(amounts_query, {"account_id": account_id})
            summary = summary_rows[0] if summary_rows else {}
            recent_amounts = [float(row.get("amount") or 0.0) for row in amounts_rows]

            return {
                "txn_count_1h": int(summary.get("txn_count_1h") or 1),
                "txn_count_24h": int(summary.get("txn_count_24h") or 1),
                "unique_counterparties": int(summary.get("unique_counterparties") or 1),
                "avg_amount": float(summary.get("avg_amount") or 0.0),
                "recent_amounts": recent_amounts,
            }
        except Exception as exc:
            logger.warning(f"Could not fetch account activity for {account_id}: {exc}")
            return {
                "txn_count_1h": 1,
                "txn_count_24h": 1,
                "unique_counterparties": 1,
                "avg_amount": 0.0,
                "recent_amounts": [],
            }
    
    def compute_velocity_score(self, account_id: str, time_window_minutes: int = 60) -> float:
        """
        Compute velocity score for account
        
        Velocity = (txn_count_in_window / baseline_txn_count) normalized to 0-1
        
        Returns: Score 0-1
        """
        # Pseudo-code (would query Neo4j in production)
        # SELECT COUNT(*) as recent_txns FROM transactions
        # WHERE account_id = ? AND timestamp > NOW() - INTERVAL window
        # recent_txn_count / baseline_rate → score
        
        return 0.5  # Placeholder
    
    def link_entities(self, entity1_id: str, entity2_id: str, link_type: str = "SAME_DEVICE") -> bool:
        """
        Create LINKED_WITH relationship between entities
        Example: Multiple accounts on same device → likely same owner
        """
        edge = GraphEdge(
            from_node_id=entity1_id,
            to_node_id=entity2_id,
            rel_type="LINKED_WITH",
            properties={
                "relationship_type": link_type,
                "confidence": 0.95,
                "reason": f"Shared {link_type.lower()}"
            }
        )
        
        if self.neo4j_client:
            self.neo4j_client.execute(edge.get_cypher_merge())
        else:
            self.pending_queries.append(edge.get_cypher_merge())
        
        return True
    
    def get_pending_queries(self) -> List[str]:
        """Return queued but not yet executed queries"""
        return self.pending_queries


# Example usage
if __name__ == "__main__":
    builder = GraphBuilder()
    
    # Sample normalized transaction
    sample_txn = {
        "event_id": "TXN_001",
        "timestamp": datetime.now().isoformat(),
        "source_account_id": "ACC_MOBILE_001",
        "dest_account_id": "ACC_WALLET_XYZ",
        "amount": 1000.0,
        "currency": "USD",
        "channel": "MOBILE",
        "device_id": "device_hash_001",
        "ip_address_hash": "ip_hash_001",
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "country": "US"
        }
    }
    
    # Ingest and see generated queries
    success = builder.ingest_transaction(sample_txn)
    if success:
        print(f"Ingestion successful. Generated {len(builder.get_pending_queries())} queries:")
        for q in builder.get_pending_queries():
            print(f"  {q[:80]}...")
