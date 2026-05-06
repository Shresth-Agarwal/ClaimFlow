"""
ClaimFlow DynamoDB Service
=========================
Centralized service for all DynamoDB operations including:
- Claims management
- User management  
- Session/conversation storage
- LangGraph state checkpointing
- Audit trail storage
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("claimflow.dynamodb")
USE_MOCK_DB = os.getenv("USE_MOCK_DB", "false").lower() == "true"

class DynamoDBService:
    def __init__(self):
        """Initialize DynamoDB service with proper configuration."""
        self.region = os.getenv("AWS_REGION", "us-east-1")
        
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=self.region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN")
        )
        
        # Table references
        self.users_table = self.dynamodb.Table(os.getenv("DYNAMODB_USERS_TABLE", "claimflow-users"))
        self.claims_table = self.dynamodb.Table(os.getenv("DYNAMODB_CLAIMS_TABLE", "claimflow-claims"))
        self.sessions_table = self.dynamodb.Table(os.getenv("DYNAMODB_SESSIONS_TABLE", "claimflow-sessions"))
        
        logger.info("DynamoDB service initialized")

    def _convert_decimals(self, obj):
        """Convert DynamoDB Decimal objects to float/int for JSON serialization."""
        if isinstance(obj, list):
            return [self._convert_decimals(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_decimals(value) for key, value in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj) if obj % 1 else int(obj)
        return obj

    def _prepare_for_dynamodb(self, obj):
        """Convert float/int to Decimal for DynamoDB storage."""
        if isinstance(obj, list):
            return [self._prepare_for_dynamodb(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._prepare_for_dynamodb(value) for key, value in obj.items()}
        elif isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, int) and not isinstance(obj, bool):
            return Decimal(obj)
        return obj

    # ─────────────────────────────────────────────────────────────────────────
    # CLAIMS OPERATIONS
    # ─────────────────────────────────────────────────────────────────────────

    async def save_claim(self, claim_data: Dict[str, Any]) -> None:
        """Save a new claim to DynamoDB."""
        try:
            # Add timestamps
            now = datetime.now(timezone.utc).isoformat()
            claim_data.update({
                "created_at": now,
                "updated_at": now
            })
            
            # Convert for DynamoDB
            prepared_data = self._prepare_for_dynamodb(claim_data)
            
            self.claims_table.put_item(Item=prepared_data)
            logger.info(f"Saved claim: {claim_data.get('claim_id')}")
            
        except ClientError as e:
            logger.error(f"Failed to save claim: {e}")
            raise

    async def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a claim by ID."""
        try:
            response = self.claims_table.get_item(Key={"claim_id": claim_id})
            
            if "Item" in response:
                return self._convert_decimals(response["Item"])
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get claim {claim_id}: {e}")
            return None

    async def update_claim(self, claim_id: str, updates: Dict[str, Any]) -> None:
        """Update an existing claim."""
        try:
            # Add update timestamp
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Build update expression
            update_expr = "SET "
            expr_values = {}
            expr_names = {}
            
            for key, value in updates.items():
                safe_key = f"#{key}"
                value_key = f":{key}"
                
                update_expr += f"{safe_key} = {value_key}, "
                expr_names[safe_key] = key
                expr_values[value_key] = self._prepare_for_dynamodb(value)
            
            update_expr = update_expr.rstrip(", ")
            
            self.claims_table.update_item(
                Key={"claim_id": claim_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values
            )
            
            logger.info(f"Updated claim {claim_id}: {list(updates.keys())}")
            
        except ClientError as e:
            logger.error(f"Failed to update claim {claim_id}: {e}")
            raise

    async def get_claims_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all claims with a specific status."""
        try:
            response = self.claims_table.scan(
                FilterExpression="attribute_exists(#status) AND #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": status}
            )
            
            return [self._convert_decimals(item) for item in response.get("Items", [])]
            
        except ClientError as e:
            logger.error(f"Failed to get claims by status {status}: {e}")
            return []

    async def get_claims_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all claims for a specific user."""
        try:
            response = self.claims_table.scan(
                FilterExpression="attribute_exists(user_id) AND user_id = :user_id",
                ExpressionAttributeValues={":user_id": user_id}
            )
            
            return [self._convert_decimals(item) for item in response.get("Items", [])]
            
        except ClientError as e:
            logger.error(f"Failed to get claims for user {user_id}: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────────────
    # SESSION/CONVERSATION OPERATIONS
    # ─────────────────────────────────────────────────────────────────────────

    async def save_session(self, session_data: Dict[str, Any]) -> None:
        """Save chat session data."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            session_data.update({
                "created_at": session_data.get("created_at", now),
                "updated_at": now
            })
            
            prepared_data = self._prepare_for_dynamodb(session_data)
            self.sessions_table.put_item(Item=prepared_data)
            
            logger.info(f"Saved session: {session_data.get('session_id')}")
            
        except ClientError as e:
            logger.error(f"Failed to save session: {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        try:
            response = self.sessions_table.get_item(Key={"session_id": session_id})
            
            if "Item" in response:
                return self._convert_decimals(response["Item"])
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> None:
        """Update session data."""
        try:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Build update expression
            update_expr = "SET "
            expr_values = {}
            expr_names = {}
            
            for key, value in updates.items():
                safe_key = f"#{key}"
                value_key = f":{key}"
                
                update_expr += f"{safe_key} = {value_key}, "
                expr_names[safe_key] = key
                expr_values[value_key] = self._prepare_for_dynamodb(value)
            
            update_expr = update_expr.rstrip(", ")
            
            self.sessions_table.update_item(
                Key={"session_id": session_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values
            )
            
        except ClientError as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            raise

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        try:
            response = self.sessions_table.scan(
                FilterExpression="attribute_exists(user_id) AND user_id = :user_id",
                ExpressionAttributeValues={":user_id": user_id}
            )
            
            return [self._convert_decimals(item) for item in response.get("Items", [])]
            
        except ClientError as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            return []

    # ─────────────────────────────────────────────────────────────────────────
    # LANGGRAPH STATE CHECKPOINTING
    # ─────────────────────────────────────────────────────────────────────────

    async def save_graph_checkpoint(self, thread_id: str, checkpoint_data: Dict[str, Any]) -> None:
        """Save LangGraph checkpoint state."""
        try:
            checkpoint_item = {
                "thread_id": thread_id,
                "checkpoint_data": checkpoint_data,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            prepared_data = self._prepare_for_dynamodb(checkpoint_item)
            
            # Use claims table with a special partition key for checkpoints
            self.claims_table.put_item(Item={
                "claim_id": f"CHECKPOINT#{thread_id}",
                **prepared_data
            })
            
        except ClientError as e:
            logger.error(f"Failed to save checkpoint for {thread_id}: {e}")
            raise

    async def get_graph_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve LangGraph checkpoint state."""
        try:
            response = self.claims_table.get_item(
                Key={"claim_id": f"CHECKPOINT#{thread_id}"}
            )
            
            if "Item" in response:
                item = self._convert_decimals(response["Item"])
                return item.get("checkpoint_data")
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get checkpoint for {thread_id}: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # USER OPERATIONS
    # ─────────────────────────────────────────────────────────────────────────

    async def save_user(self, user_data: Dict[str, Any]) -> None:
        """Save user data."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            user_data.update({
                "created_at": user_data.get("created_at", now),
                "updated_at": now
            })
            
            prepared_data = self._prepare_for_dynamodb(user_data)
            self.users_table.put_item(Item=prepared_data)
            
        except ClientError as e:
            logger.error(f"Failed to save user: {e}")
            raise

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        try:
            response = self.users_table.scan(
                FilterExpression="email = :email",
                ExpressionAttributeValues={":email": email}
            )
            
            items = response.get("Items", [])
            if items:
                return self._convert_decimals(items[0])
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            response = self.users_table.get_item(Key={"id": user_id})
            
            if "Item" in response:
                return self._convert_decimals(response["Item"])
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None


class MockDynamoDBService:
    """In-memory DynamoDB-like service for USE_MOCK_DB local development."""

    def __init__(self):
        self.claims = {}
        self.sessions = {}
        self.graph_checkpoints = {}
        self.users = {}
        logger.info("Using MockDynamoDBService (in-memory)")

    def _convert_decimals(self, obj):
        return obj

    def _prepare_for_dynamodb(self, obj):
        return obj

    async def save_claim(self, claim_data: Dict[str, Any]) -> None:
        claim_id = claim_data.get("claim_id")
        if claim_id is None:
            raise ValueError("claim_id is required")
        now = datetime.now(timezone.utc).isoformat()
        claim_data = dict(claim_data)
        claim_data.setdefault("created_at", now)
        claim_data["updated_at"] = now
        self.claims[claim_id] = claim_data
        logger.info(f"[mock] Saved claim: {claim_id}")

    async def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        return self.claims.get(claim_id)

    async def update_claim(self, claim_id: str, updates: Dict[str, Any]) -> None:
        if claim_id not in self.claims:
            self.claims[claim_id] = {"claim_id": claim_id}
        self.claims[claim_id].update(updates)
        logger.info(f"[mock] Updated claim {claim_id}: {list(updates.keys())}")

    async def get_claims_by_status(self, status: str) -> List[Dict[str, Any]]:
        return [claim for claim in self.claims.values() if claim.get("status") == status]

    async def get_claims_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        return [claim for claim in self.claims.values() if claim.get("user_id") == user_id]

    async def save_session(self, session_data: Dict[str, Any]) -> None:
        session_id = session_data.get("session_id")
        if session_id is None:
            raise ValueError("session_id is required")
        now = datetime.now(timezone.utc).isoformat()
        session_data = dict(session_data)
        session_data.setdefault("created_at", now)
        session_data["updated_at"] = now
        self.sessions[session_id] = session_data
        logger.info(f"[mock] Saved session: {session_id}")

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(session_id)

    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> None:
        if session_id not in self.sessions:
            self.sessions[session_id] = {"session_id": session_id}
        updates = dict(updates)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.sessions[session_id].update(updates)
        logger.info(f"[mock] Updated session {session_id}: {list(updates.keys())}")

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        return [session for session in self.sessions.values() if session.get("user_id") == user_id]

    async def save_graph_checkpoint(self, thread_id: str, checkpoint_data: Dict[str, Any]) -> None:
        self.graph_checkpoints[thread_id] = checkpoint_data
        logger.info(f"[mock] Saved checkpoint for {thread_id}")

    async def get_graph_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        return self.graph_checkpoints.get(thread_id)

    async def save_user(self, user_data: Dict[str, Any]) -> None:
        user_id = user_data.get("id")
        if user_id is None:
            raise ValueError("user id is required")
        self.users[user_id] = dict(user_data)
        logger.info(f"[mock] Saved user: {user_id}")

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        for user in self.users.values():
            if user.get("email") == email:
                return user
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.users.get(user_id)


# Global service instance
_db_service = None

def get_db_service():
    """Get the global DynamoDB service instance."""
    global _db_service
    if _db_service is None:
        _db_service = MockDynamoDBService() if USE_MOCK_DB else DynamoDBService()
    return _db_service


# Convenience functions for backward compatibility
async def save_claim(claim_data: Dict[str, Any]) -> None:
    """Save claim using the global service."""
    await get_db_service().save_claim(claim_data)

async def get_claim(claim_id: str) -> Optional[Dict[str, Any]]:
    """Get claim using the global service."""
    return await get_db_service().get_claim(claim_id)

async def update_claim(claim_id: str, updates: Dict[str, Any]) -> None:
    """Update claim using the global service."""
    await get_db_service().update_claim(claim_id, updates)

async def get_claims_by_status(status: str) -> List[Dict[str, Any]]:
    """Get claims by status using the global service."""
    return await get_db_service().get_claims_by_status(status)