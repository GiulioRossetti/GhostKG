"""
Ghost KG Visualization Module

Provides functionality to export agent interaction history to JSON format
for visualization in the interactive web interface.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path

from ghost_kg.storage.database import KnowledgeDB


class HistoryExporter:
    """Exports agent interaction history to JSON for visualization."""
    
    def __init__(self, db_path: str):
        """
        Initialize the history exporter.
        
        Args:
            db_path: Path to the database file or connection string
        """
        self.db = KnowledgeDB(db_path=db_path)
        
    def export_history(
        self,
        output_file: str,
        agents: Optional[List[str]] = None,
        topic: str = "Knowledge Graph Evolution"
    ) -> Dict[str, Any]:
        """
        Export interaction history to JSON format.
        
        Args:
            output_file: Path to output JSON file
            agents: List of agent names to include (None = auto-detect)
            topic: Title/topic for the visualization
            
        Returns:
            Dictionary containing the exported history
        """
        # Get all logs ordered by time
        logs = self._get_all_logs()
        
        if not logs:
            print("⚠️ Warning: No interaction logs found in database.")
            return {"metadata": {}, "agents": [], "steps": []}
        
        # Auto-detect agents if not specified
        if agents is None:
            agents = self._detect_agents(logs)
        
        # Get all nodes and edges
        all_nodes = self._get_all_nodes()
        all_edges = self._get_all_edges()
        
        # Build history structure
        history = {
            "metadata": {
                "topic": topic,
                "date": datetime.now().isoformat(),
                "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "agents": agents,
            "steps": []
        }
        
        # Step 0: Initial state
        initial_graphs = {agent: {"nodes": [], "links": []} for agent in agents}
        history["steps"].append({
            "step": 0,
            "round": 0,
            "action": "Initialization",
            "graphs": initial_graphs
        })
        
        # Process each log entry
        for i, log in enumerate(logs):
            current_time = self._parse_timestamp(log.get("timestamp"))
            
            step_data = {
                "step": i + 1,
                "round": i + 1,
                "action": self._format_action(log, current_time),
                "graphs": {}
            }
            
            # Build graph state for each agent at this time
            for agent in agents:
                nodes = self._build_nodes_at_time(
                    all_nodes, agent, current_time
                )
                links = self._build_links_at_time(
                    all_edges, nodes, agent, current_time
                )
                
                step_data["graphs"][agent] = {
                    "nodes": nodes,
                    "links": links
                }
            
            history["steps"].append(step_data)
        
        # Write to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"✅ History exported to {output_file}")
        print(f"   Total steps: {len(history['steps'])}")
        print(f"   Agents: {', '.join(agents)}")
        
        return history
    
    def _get_all_logs(self) -> List[Dict[str, Any]]:
        """Get all interaction logs from database."""
        session = self.db.db_manager.get_session()
        try:
            from ghost_kg.storage.models import Log
            logs = session.query(Log).order_by(Log.timestamp.asc()).all()
            return [
                {
                    "id": log.id,
                    "agent_name": log.agent_name,
                    "action_type": log.action_type,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "sim_day": log.sim_day,
                    "sim_hour": log.sim_hour,
                    "content": log.content,
                    "annotations": log.annotations
                }
                for log in logs
            ]
        finally:
            session.close()
    
    def _get_all_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes from database."""
        session = self.db.db_manager.get_session()
        try:
            from ghost_kg.storage.models import Node
            nodes = session.query(Node).all()
            return [
                {
                    "id": node.id,
                    "owner_id": node.owner_id,
                    "stability": node.stability,
                    "last_review": node.last_review.isoformat() if node.last_review else None,
                    "created_at": node.created_at.isoformat() if node.created_at else None,
                    "sim_day": node.sim_day,
                    "sim_hour": node.sim_hour
                }
                for node in nodes
            ]
        finally:
            session.close()
    
    def _get_all_edges(self) -> List[Dict[str, Any]]:
        """Get all edges from database."""
        session = self.db.db_manager.get_session()
        try:
            from ghost_kg.storage.models import Edge
            edges = session.query(Edge).all()
            return [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "relation": edge.relation,
                    "owner_id": edge.owner_id,
                    "created_at": edge.created_at.isoformat() if edge.created_at else None,
                    "sim_day": edge.sim_day,
                    "sim_hour": edge.sim_hour
                }
                for edge in edges
            ]
        finally:
            session.close()
    
    def _detect_agents(self, logs: List[Dict[str, Any]]) -> List[str]:
        """Auto-detect agent names from logs."""
        agents = set()
        for log in logs:
            if log.get("agent_name"):
                agents.add(log["agent_name"])
        return sorted(list(agents))
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse timestamp string to datetime object."""
        if not timestamp_str:
            return datetime.now(timezone.utc)
        
        try:
            dt = datetime.fromisoformat(timestamp_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, AttributeError):
            return datetime.now(timezone.utc)
    
    def _format_action(self, log: Dict[str, Any], current_time: datetime) -> str:
        """Format log entry as action description."""
        agent = log.get("agent_name", "Agent")
        action = log.get("action_type", "action")
        
        # Use simulation time if available, otherwise use timestamp
        if log.get("sim_day") is not None and log.get("sim_hour") is not None:
            time_str = f"Day {log['sim_day']}, Hour {log['sim_hour']}"
        else:
            time_str = current_time.strftime('%H:%M')
        
        return f"{agent} {action} ({time_str})"
    
    def _build_nodes_at_time(
        self,
        all_nodes: List[Dict[str, Any]],
        agent: str,
        current_time: datetime
    ) -> List[Dict[str, Any]]:
        """Build list of nodes visible to agent at given time."""
        potential_nodes = {}
        touched_node_ids = set()
        
        for node in all_nodes:
            if node["owner_id"] != agent:
                continue
            
            # Check if node should exist at this time
            is_self = (node["id"].lower() == "i")
            
            # Self node exists eternally
            if is_self:
                touched_node_ids.add(node["id"])
            
            # Check creation time
            created_at = self._parse_timestamp(node.get("created_at"))
            if not is_self and created_at > current_time:
                continue
            
            # Calculate FSRS retrievability
            stability = node.get("stability", 0.0)
            last_review = self._parse_timestamp(node.get("last_review"))
            
            elapsed_days = (current_time - last_review).total_seconds() / 86400
            if elapsed_days < 0:
                elapsed_days = 0
            
            retrievability = 1.0
            if stability > 0:
                retrievability = (1 + elapsed_days / (9 * stability)) ** -1
            
            # Force self node to be fully active
            if is_self:
                retrievability = 1.0
            
            potential_nodes[node["id"]] = {
                "id": node["id"],
                "group": 0 if is_self else 1,
                "radius": 25 if is_self else 10 + (stability * 0.5),
                "retrievability": round(retrievability, 3),
                "stability": round(stability, 2)
            }
        
        return list(potential_nodes.values())
    
    def _build_links_at_time(
        self,
        all_edges: List[Dict[str, Any]],
        nodes: List[Dict[str, Any]],
        agent: str,
        current_time: datetime
    ) -> List[Dict[str, Any]]:
        """Build list of edges visible to agent at given time."""
        node_ids = {node["id"] for node in nodes}
        valid_edges = []
        
        for edge in all_edges:
            if edge["owner_id"] != agent:
                continue
            
            # Check creation time
            created_at = self._parse_timestamp(edge.get("created_at"))
            if created_at > current_time:
                continue
            
            # Edge is valid only if both nodes exist
            if edge["source"] in node_ids and edge["target"] in node_ids:
                valid_edges.append({
                    "source": edge["source"],
                    "target": edge["target"],
                    "label": edge["relation"],
                    "value": 1,
                    "dashed": False
                })
        
        return valid_edges


def export_history(
    db_path: str,
    output_file: str,
    agents: Optional[List[str]] = None,
    topic: str = "Knowledge Graph Evolution"
) -> Dict[str, Any]:
    """
    Convenience function to export history.
    
    Args:
        db_path: Path to database file or connection string
        output_file: Path to output JSON file
        agents: List of agent names (None = auto-detect)
        topic: Title for visualization
        
    Returns:
        Dictionary containing exported history
    """
    exporter = HistoryExporter(db_path)
    return exporter.export_history(output_file, agents, topic)
