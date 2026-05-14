"""
PRISM Platform — Federated Learning Management Endpoints
Manages FL server status, node registration, and round tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
import logging

from backend.utils.auth import get_current_user
from backend.db.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


class NodeRegistration(BaseModel):
    hospital_name: str
    location: Optional[str] = None
    estimated_samples: int = 0


class NodeRegistrationResponse(BaseModel):
    node_id: str
    client_config: dict


class FLStatusResponse(BaseModel):
    server_status: str = "running"
    current_round: int = 0
    total_nodes: int = 0
    active_nodes: int = 0
    global_model_version: str = ""
    cumulative_dp_epsilon: float = 0.0
    last_round_metrics: Optional[dict] = None


class FLRoundSummary(BaseModel):
    round_number: int
    participating_nodes: int
    rejected_nodes: int = 0
    metrics: Optional[dict] = None
    dp_epsilon_spent: float = 0.0
    completed_at: Optional[str] = None


@router.get("/status", response_model=FLStatusResponse)
async def get_fl_status(current_user: dict = Depends(get_current_user)):
    """Get federated learning server status and latest round info."""
    client = get_supabase_client()

    # Get latest FL round
    rounds = client.table("fl_rounds").select("*").order(
        "round_number", desc=True
    ).limit(1).execute()

    # Count nodes
    nodes = client.table("hospital_nodes").select("id, status").execute()
    total_nodes = len(nodes.data) if nodes.data else 0
    active_nodes = len([n for n in (nodes.data or []) if n["status"] == "active"])

    # Cumulative epsilon
    all_rounds = client.table("fl_rounds").select("dp_epsilon_spent").execute()
    cumulative_epsilon = sum(r["dp_epsilon_spent"] for r in (all_rounds.data or []))

    latest = rounds.data[0] if rounds.data else None

    return FLStatusResponse(
        server_status="running",
        current_round=latest["round_number"] if latest else 0,
        total_nodes=total_nodes,
        active_nodes=active_nodes,
        global_model_version=latest["global_model_version"] if latest else "none",
        cumulative_dp_epsilon=cumulative_epsilon,
        last_round_metrics=latest.get("metrics") if latest else None,
    )


@router.post("/register-node", response_model=NodeRegistrationResponse, status_code=201)
async def register_node(
    registration: NodeRegistration,
    current_user: dict = Depends(get_current_user),
):
    """Register a new hospital node for FL participation."""
    client = get_supabase_client()

    from backend.config import get_settings
    settings = get_settings()

    result = client.table("hospital_nodes").insert({
        "hospital_name": registration.hospital_name,
        "location": registration.location,
        "local_sample_count": registration.estimated_samples,
        "status": "active",
    }).execute()

    node = result.data[0]

    return NodeRegistrationResponse(
        node_id=node["id"],
        client_config={
            "server_address": f"fl.prism-health.app:{settings.fl_server_port}",
            "model_name": "prism_cough_classifier",
            "local_epochs": 3,
            "learning_rate": 0.0001,
            "gradient_clip_norm": 1.0,
        },
    )


@router.get("/rounds")
async def list_fl_rounds(
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """List FL training rounds with metrics."""
    client = get_supabase_client()

    result = client.table("fl_rounds").select("*").order(
        "round_number", desc=True
    ).limit(limit).execute()

    return {
        "rounds": [
            FLRoundSummary(
                round_number=r["round_number"],
                participating_nodes=r["participating_nodes"],
                rejected_nodes=r.get("rejected_nodes", 0),
                metrics=r.get("metrics"),
                dp_epsilon_spent=r.get("dp_epsilon_spent", 0.0),
                completed_at=r.get("completed_at"),
            )
            for r in (result.data or [])
        ]
    }
