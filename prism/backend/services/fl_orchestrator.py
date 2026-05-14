"""
PRISM Platform — Federated Learning Orchestrator
Manages FL server lifecycle, node registration, and round tracking.
"""
import logging
from typing import Optional
from backend.db.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class FLOrchestrator:
    """Manages the FL server lifecycle and round tracking."""

    def __init__(self):
        self.is_running = False
        self.server_thread = None

    def start_server(self, port: int = 8080, num_rounds: int = 100):
        """Start the FL server in a background thread."""
        if self.is_running:
            logger.warning("FL server already running")
            return
        import threading
        from backend.federated.fl_server import start_fl_server
        self.server_thread = threading.Thread(
            target=start_fl_server, args=(port, num_rounds), daemon=True,
        )
        self.server_thread.start()
        self.is_running = True
        logger.info("FL server started on port %d for %d rounds", port, num_rounds)

    def stop_server(self):
        """Stop the FL server."""
        self.is_running = False
        logger.info("FL server stop requested")

    def record_round(self, round_number: int, participants: int, rejected: int,
                     model_version: str, epsilon_spent: float, metrics: dict = None):
        """Record a completed FL round in the database."""
        client = get_supabase_client()
        client.table("fl_rounds").insert({
            "round_number": round_number,
            "participating_nodes": participants,
            "rejected_nodes": rejected,
            "global_model_version": model_version,
            "dp_epsilon_spent": epsilon_spent,
            "metrics": metrics,
        }).execute()

    def get_status(self) -> dict:
        """Get current FL server status."""
        client = get_supabase_client()
        rounds = client.table("fl_rounds").select("*").order("round_number", desc=True).limit(1).execute()
        nodes = client.table("hospital_nodes").select("id, status").execute()
        return {
            "is_running": self.is_running,
            "current_round": rounds.data[0]["round_number"] if rounds.data else 0,
            "total_nodes": len(nodes.data) if nodes.data else 0,
            "active_nodes": len([n for n in (nodes.data or []) if n["status"] == "active"]),
        }


# Singleton
fl_orchestrator = FLOrchestrator()
