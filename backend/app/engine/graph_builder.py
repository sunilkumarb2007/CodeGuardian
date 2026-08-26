import uuid
from typing import List, Dict, Any
from app.engine.models import NormalizedEvidence, TraceNode, TraceEdge

class GraphBuilder:
    def __init__(self):
        pass

    def build_graph(self, correlation_result: Dict[str, Any]) -> tuple[List[TraceNode], List[TraceEdge]]:
        """
        Convert correlated evidence into nodes and edges.
        """
        nodes = []
        edges = []
        
        groups = correlation_result.get("groups", [])
        cor_edges = correlation_result.get("edges", [])
        
        # We will create one node per service involved.
        # This simplifies the graph and aggregates evidence by service.
        service_nodes = {}
        seq = 1
        
        all_evidence = []
        for g in groups:
            all_evidence.extend(g)
            
        # Add evidences not in groups (if any) to the list
        for edge in cor_edges:
            if edge["from"] not in all_evidence:
                all_evidence.append(edge["from"])
            if edge["to"] not in all_evidence:
                all_evidence.append(edge["to"])
                
        # Deduplicate evidence
        all_evidence = list({e.id: e for e in all_evidence}.values())
        
        # Sort evidence by timestamp
        all_evidence.sort(key=lambda e: e.timestamp)
        
        # Create nodes
        for ev in all_evidence:
            if ev.service_name not in service_nodes:
                node_id = str(uuid.uuid4())
                node = TraceNode(
                    id=node_id,
                    sequence_number=seq,
                    service_name=ev.service_name,
                    endpoint=ev.endpoint,
                    status_code=ev.status_code if ev.is_error else None,
                    error_message=ev.error_message if ev.is_error else None,
                    evidence_ids=[ev.id]
                )
                service_nodes[ev.service_name] = node
                nodes.append(node)
                seq += 1
            else:
                # Update existing node with more severe errors if any
                node = service_nodes[ev.service_name]
                node.evidence_ids.append(ev.id)
                if ev.is_error:
                    node.status_code = ev.status_code or node.status_code
                    node.error_message = ev.error_message or node.error_message
                    
        # Create edges based on correlation
        for c_edge in cor_edges:
            from_ev = c_edge["from"]
            to_ev = c_edge["to"]
            
            from_node = service_nodes[from_ev.service_name]
            to_node = service_nodes[to_ev.service_name]
            
            if from_node.id != to_node.id:
                # Check if edge already exists
                existing_edge = next((e for e in edges if e.from_node_id == from_node.id and e.to_node_id == to_node.id), None)
                if not existing_edge:
                    edges.append(TraceEdge(
                        id=str(uuid.uuid4()),
                        from_node_id=from_node.id,
                        to_node_id=to_node.id,
                        relationship_type="request",
                        correlation_strength=c_edge["strength"],
                        evidence_ids=[from_ev.id, to_ev.id]
                    ))
                else:
                    # Append evidence to existing edge
                    if from_ev.id not in existing_edge.evidence_ids:
                        existing_edge.evidence_ids.append(from_ev.id)
                    if to_ev.id not in existing_edge.evidence_ids:
                        existing_edge.evidence_ids.append(to_ev.id)
                        
        return nodes, edges
