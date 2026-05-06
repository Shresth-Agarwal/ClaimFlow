# ClaimFlow — LangGraph Graph Builder & Runner
#
# This is where all the nodes from nodes.py get wired together
# into the actual LangGraph state machine with DynamoDB checkpointing.
#
# Call run_claim_pipeline(state) from your claims router to kick off a claim.

import logging
from typing import Annotated
import operator
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from backend.graph.nodes import (
    inclusion_node,
    vision_node,
    forensic_node,
    policy_node,
    guardrail_node,
    router_node,
    investigator_node,
    human_review_node,
    notification_node,
)
from backend.services.dynamodb_service import get_db_service

logger = logging.getLogger("claimflow.pipeline")


class DynamoDBCheckpointSaver(BaseCheckpointSaver):
    """Custom checkpoint saver that uses DynamoDB for persistence."""
    
    def __init__(self):
        self.db_service = get_db_service()
    
    def get_tuple(self, config):
        """Sync get checkpoint tuple from DynamoDB."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.aget_tuple(config))
    
    def put(self, config, checkpoint, metadata, new_versions):
        """Sync put checkpoint to DynamoDB."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.aput(config, checkpoint, metadata, new_versions))
    
    def put_tuple(self, config, checkpoint, metadata, parent_config):
        """Sync put checkpoint tuple to DynamoDB."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.aput_tuple(config, checkpoint, metadata, parent_config))
    
    def put_writes(self, config, writes, task_id, task_path=""):
        """Sync put writes to DynamoDB."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.aput_writes(config, writes, task_id, task_path))
    
    def list(self, config, *, filter=None, before=None, limit=None):
        """Sync list checkpoints."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.alist(config, filter=filter, before=before, limit=limit))
    
    async def aget_tuple(self, config):
        """Get checkpoint tuple from DynamoDB."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_data = await self.db_service.get_graph_checkpoint(thread_id)
        
        if checkpoint_data:
            return (
                checkpoint_data.get("checkpoint"),
                checkpoint_data.get("metadata", {}),
                checkpoint_data.get("parent_config")
            )
        return None
    
    async def aput_tuple(self, config, checkpoint, metadata, parent_config):
        """Save checkpoint tuple to DynamoDB."""
        thread_id = config["configurable"]["thread_id"]
        
        checkpoint_data = {
            "checkpoint": checkpoint,
            "metadata": metadata,
            "parent_config": parent_config
        }
        
        await self.db_service.save_graph_checkpoint(thread_id, checkpoint_data)
    
    async def alist(self, config, *, filter=None, before=None, limit=None):
        """List checkpoints (simplified implementation)."""
        # For now, just return empty list as we only need the latest checkpoint
        return []
    
    async def aput_writes(self, config, writes, task_id, task_path=""):
        """Save writes to DynamoDB (simplified - just log for now)."""
        # For now, just log the writes - in a full implementation we'd store them
        logger.debug(f"Saving writes for task {task_id}: {writes}")
    
    async def aput(self, config, checkpoint, metadata, new_versions):
        """Save checkpoint to DynamoDB."""
        thread_id = config["configurable"]["thread_id"]
        
        checkpoint_data = {
            "checkpoint": checkpoint,
            "metadata": metadata,
            "parent_config": None,  # No parent config for simple put
            "new_versions": new_versions
        }
        
        await self.db_service.save_graph_checkpoint(thread_id, checkpoint_data)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTING FUNCTIONS
# These are the functions LangGraph calls at conditional edges to decide
# which node to go to next.
# ─────────────────────────────────────────────────────────────────────────────

def route_after_router(state: dict) -> str:
    """
    Called after router_node. Returns the name of the next node.

    auto_approve → notification_node  (done — send approval, no human needed)
    reject       → notification_node  (done — send rejection, no human needed)
    investigate  → investigator_node  (start/continue investigator loop)
    human_queue  → human_review_node  (pause — adjuster must decide)

    Human review is ONLY triggered for specific edge cases:
      - Ambiguous fraud score (50-75) after investigator exhausted
      - Suspicious indicators detected by forensic agent
      - Multiple consistency check failures
      - High inflation risk
      - Large claim (> ₹2L)
      - Low vision confidence on non-trivial claim
      - Policy eligibility unverified
    """
    decision = state.get("routing_decision", "human_queue")
    logger.info(f"[{state['claim_id']}] Routing: {decision}")

    mapping = {
        "auto_approve": "notification_node",
        "human_queue":  "human_review_node",
        "reject":       "notification_node",
        "investigate":  "investigator_node",
    }
    return mapping.get(decision, "human_review_node")


def route_after_investigator(state: dict) -> str:
    """
    Called after investigator_node.
    If max iterations reached → router forced it to human_queue → go to human_review.
    Otherwise → re-run vision and forensic with the challenge.

    Returns node name for next step.
    """
    iteration = state.get("investigator_iteration", 0)
    decision  = state.get("routing_decision", "investigate")

    if decision == "human_queue" or iteration >= 3:
        return "human_review_node"

    # Loop back — re-run vision with challenge, then forensic, then router
    return "vision_node"


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Builds and compiles the full ClaimFlow LangGraph pipeline with DynamoDB checkpointing.

    State schema uses Annotated[list, operator.add] for audit_trail so
    LangGraph merges audit entries across nodes instead of overwriting them.
    All other fields use last-write-wins (default dict merge).
    """
    # Define the state schema as a TypedDict so LangGraph knows how to merge.
    # audit_trail uses operator.add so entries accumulate across every node.
    from typing import TypedDict, Optional, Any

    class ClaimState(TypedDict, total=False):
        # Identity
        claim_id:               str
        claim_type:             str
        session_id:             str
        # Claimant context
        user_id:                str
        nationality:            str
        country_of_residence:   str
        # Raw input
        raw_input:              dict
        # Agent results
        inclusion_result:       Optional[Any]
        vision_result:          Optional[Any]
        forensic_result:        Optional[Any]
        policy_result:          Optional[Any]
        # Investigator loop
        investigator_iteration: int
        investigator_challenge: Optional[str]
        # Router output
        routing_decision:       str
        # Human review
        adjuster_decision:      Optional[str]
        adjuster_notes:         Optional[str]
        # Final
        final_status:           Optional[str]
        settlement_amount_inr:  Optional[float]
        # Audit trail — operator.add merges lists across nodes
        audit_trail:            Annotated[list, operator.add]

    graph = StateGraph(ClaimState)

    # ── Register all nodes ────────────────────────────────────────────────────
    graph.add_node("inclusion_node",  inclusion_node)
    graph.add_node("vision_node",     vision_node)
    graph.add_node("forensic_node",   forensic_node)
    graph.add_node("policy_node",     policy_node)
    graph.add_node("guardrail_node",  guardrail_node)
    graph.add_node("router_node",     router_node)
    graph.add_node("investigator_node",   investigator_node)
    graph.add_node("human_review_node",   human_review_node)
    graph.add_node("notification_node",   notification_node)

    # ── Set entry point ───────────────────────────────────────────────────────
    graph.set_entry_point("inclusion_node")

    # ── Linear edges (no branching) ───────────────────────────────────────────
    graph.add_edge("inclusion_node",  "vision_node")
    graph.add_edge("vision_node",     "forensic_node")
    graph.add_edge("forensic_node",   "policy_node")
    graph.add_edge("policy_node",     "guardrail_node")
    graph.add_edge("guardrail_node",  "router_node")

    # ── Conditional edge after router (THE decision point) ────────────────────
    graph.add_conditional_edges(
        "router_node",
        route_after_router,
        {
            "notification_node": "notification_node",   # approve or reject
            "human_review_node": "human_review_node",   # needs adjuster
            "investigator_node": "investigator_node",   # ambiguous fraud
        }
    )

    # ── Investigator loop conditional edge ────────────────────────────────────
    graph.add_conditional_edges(
        "investigator_node",
        route_after_investigator,
        {
            "vision_node":       "vision_node",         # loop: re-examine photos
            "human_review_node": "human_review_node",   # max iterations — human
        }
    )

    # ── Human review → notification ───────────────────────────────────────────
    graph.add_edge("human_review_node", "notification_node")

    # ── All paths end at notification ─────────────────────────────────────────
    graph.add_edge("notification_node", END)

    # ── Compile with DynamoDB checkpoint ──────────────────────────────────────
    # Use DynamoDB for production persistence
    try:
        checkpointer = DynamoDBCheckpointSaver()
        logger.info("Using DynamoDB checkpointer")
    except Exception as e:
        logger.warning(f"DynamoDB checkpointer failed, using memory: {e}")
        checkpointer = MemorySaver()

    compiled = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review_node"],   # pause here for adjuster
    )

    return compiled


# Singleton — build once on import
_graph = None

def get_graph() -> StateGraph:
    global _graph
    if _graph is None:
        _graph = build_graph()
        logger.info("LangGraph pipeline compiled and ready")
    return _graph


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC RUNNER — call this from your claims router
# ─────────────────────────────────────────────────────────────────────────────

async def run_claim_pipeline(initial_state: dict) -> dict:
    """
    Entry point called by POST /api/claims/submit.

    Runs the full graph until it either:
    - Completes (auto_approve or reject) → returns final state with final_status set
    - Pauses at human_review_node       → returns state with routing_decision="human_queue"
                                          and final_status=None (adjuster hasn't decided yet)

    The caller (claims route) checks routing_decision to know which case it is.
    """
    graph      = get_graph()
    claim_id   = initial_state["claim_id"]
    config     = {"configurable": {"thread_id": claim_id}}

    logger.info(f"[{claim_id}] Starting claim pipeline")

    try:
        # graph.invoke() is synchronous — run it in a thread so it doesn't
        # block the uvicorn event loop, and so nodes can spawn their own loops.
        import asyncio
        final_state = await asyncio.to_thread(graph.invoke, initial_state, config)

        routing = final_state.get("routing_decision", "human_queue")
        status  = final_state.get("final_status")

        # If the graph paused at human_review_node, final_status is still None.
        # Set it to "pending_review" so the DB record is meaningful.
        if routing == "human_queue" and not status:
            final_state = {**final_state, "final_status": "pending_review"}

        logger.info(
            f"[{claim_id}] Pipeline completed. "
            f"Decision: {final_state.get('routing_decision')}. "
            f"Status: {final_state.get('final_status')}"
        )
        return final_state

    except Exception as e:
        logger.error(f"[{claim_id}] Pipeline failed: {e}", exc_info=True)
        raise


async def resume_claim_pipeline(claim_id: str, adjuster_decision: str, adjuster_notes: str = "") -> dict:
    """
    Called by POST /api/adjuster/{claim_id}/decision after an adjuster decides.

    Resumes the paused pipeline from the human_review_node checkpoint.
    The adjuster's decision is injected into the state before resuming.

    Args:
        claim_id:          The claim to resume
        adjuster_decision: "approve" or "reject"
        adjuster_notes:    Optional notes from the adjuster

    Returns:
        Final state after notification_node runs
    """
    graph  = get_graph()
    config = {"configurable": {"thread_id": claim_id}}

    logger.info(f"[{claim_id}] Resuming pipeline — adjuster decision: {adjuster_decision}")

    # Inject adjuster decision into the checkpointed state
    graph.update_state(config, {"adjuster_decision": adjuster_decision, "adjuster_notes": adjuster_notes})

    # Resume from the interrupt point in a thread
    import asyncio
    final_state = await asyncio.to_thread(graph.invoke, None, config)

    logger.info(f"[{claim_id}] Pipeline resumed and completed. Status: {final_state.get('final_status')}")
    return final_state