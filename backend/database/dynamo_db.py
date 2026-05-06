# backend/database/dynamo_db.py
# DynamoDB implementation of IUserRepository.
# Implements the exact same interface as MockUserRepository —
# so nothing in services, routes, or security needs to change.

import os
import boto3
import logging
from typing import Optional
from boto3.dynamodb.conditions import Attr
from dotenv import load_dotenv
from backend.database.interfaces import IUserRepository
from backend.api.schemas import User

load_dotenv()

logger = logging.getLogger("claimflow.dynamo_db")

TABLE_NAME    = os.getenv("DYNAMODB_USERS_TABLE", "claimflow-users")
AWS_REGION    = os.getenv("AWS_REGION", "us-east-1")
AWS_KEY       = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET    = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION   = os.getenv("AWS_SESSION_TOKEN")   # required for temporary credentials


class DynamoUserRepository(IUserRepository):
    """
    DynamoDB implementation of IUserRepository.

    Table schema:
        Partition key : id          (Number)
        GSI           : email-index (email → id lookup for login)

    All User fields are stored as a flat item — no nesting.
    """

    def __init__(self):
        dynamodb   = boto3.resource(
            "dynamodb",
            region_name          = AWS_REGION,
            aws_access_key_id    = AWS_KEY,
            aws_secret_access_key= AWS_SECRET,
            aws_session_token    = AWS_SESSION,   # None if not using temp creds — boto3 ignores it
        )
        self.table = dynamodb.Table(TABLE_NAME)
        logger.info(f"DynamoUserRepository connected to table '{TABLE_NAME}' in {AWS_REGION}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _to_user(self, item: dict) -> User:
        """Converts a raw DynamoDB item dict into a User pydantic model."""
        return User(
            id       = int(item["id"]),
            username = item["username"],
            email    = item["email"],
            role     = item["role"],
            password = item["password"],
            verified = bool(item.get("verified", False)),
        )

    def _next_id(self) -> int:
        """
        Simple auto-increment using a counter item in the same table.
        Item: { id: 0, _type: "counter", value: <current_max> }
        Uses an atomic ADD to avoid race conditions.
        """
        response = self.table.update_item(
            Key={"id": 0},
            UpdateExpression="ADD #val :inc SET #type = if_not_exists(#type, :t)",
            ExpressionAttributeNames={"#val": "value", "#type": "_type"},
            ExpressionAttributeValues={":inc": 1, ":t": "counter"},
            ReturnValues="UPDATED_NEW",
        )
        return int(response["Attributes"]["value"])

    # ── IUserRepository implementation ────────────────────────────────────────

    def create_user(self, user: User) -> User:
        try:
            new_id   = self._next_id()
            new_user = user.model_copy(update={"id": new_id})

            self.table.put_item(Item={
                "id":       new_id,
                "username": new_user.username,
                "email":    new_user.email,
                "role":     new_user.role,
                "password": new_user.password,
                "verified": new_user.verified,
            })

            logger.info(f"Created user id={new_id} email={new_user.email}")
            return new_user
        except Exception as e:
            logger.error(f"DynamoDB create_user failed: {e}", exc_info=True)
            raise

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Scans for the email. For production scale use a GSI on email instead.
        Fine for a hackathon with low user counts.
        """
        response = self.table.scan(
            FilterExpression=Attr("email").eq(email) & Attr("_type").not_exists()
        )
        items = response.get("Items", [])
        if not items:
            return None
        return self._to_user(items[0])

    def get_by_id(self, user_id: int) -> Optional[User]:
        response = self.table.get_item(Key={"id": user_id})
        item     = response.get("Item")
        if not item or item.get("_type") == "counter":
            return None
        return self._to_user(item)

    def update_verification_status(self, user_id: int, status: bool) -> bool:
        try:
            self.table.update_item(
                Key={"id": user_id},
                UpdateExpression="SET verified = :v",
                ExpressionAttributeValues={":v": status},
                ConditionExpression=Attr("id").exists(),
            )
            logger.info(f"Updated verification status for user id={user_id} → {status}")
            return True
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            logger.warning(f"update_verification_status: user id={user_id} not found")
            return False


# ─────────────────────────────────────────────────────────────────────────────
# CLAIMS TABLE — separate table, separate boto3 resource
# ─────────────────────────────────────────────────────────────────────────────

CLAIMS_TABLE_NAME = os.getenv("DYNAMODB_CLAIMS_TABLE", "claimflow-claims")

_boto_kwargs = dict(
    region_name           = AWS_REGION,
    aws_access_key_id     = AWS_KEY,
    aws_secret_access_key = AWS_SECRET,
    aws_session_token     = AWS_SESSION,
)

def _get_claims_table():
    dynamodb = boto3.resource("dynamodb", **_boto_kwargs)
    return dynamodb.Table(CLAIMS_TABLE_NAME)


async def save_claim(item: dict) -> None:
    """Write the initial claim record when a claim is first submitted."""
    try:
        table = _get_claims_table()
        table.put_item(Item=item)
        logger.info(f"save_claim: {item.get('claim_id')}")
    except Exception as e:
        logger.error(f"save_claim failed: {e}", exc_info=True)
        raise


async def get_claim(claim_id: str) -> Optional[dict]:
    """Fetch a single claim by claim_id."""
    try:
        table    = _get_claims_table()
        response = table.get_item(Key={"claim_id": claim_id})
        return response.get("Item")
    except Exception as e:
        logger.error(f"get_claim failed for {claim_id}: {e}", exc_info=True)
        return None


async def update_claim(claim_id: str, updates: dict) -> None:
    """
    Patch specific fields on an existing claim item.
    Only updates the keys present in `updates` — leaves everything else untouched.
    """
    if not updates:
        return
    try:
        table = _get_claims_table()

        expr_parts  = []
        attr_names  = {}
        attr_values = {}

        for i, (key, value) in enumerate(updates.items()):
            placeholder_name  = f"#k{i}"
            placeholder_value = f":v{i}"
            expr_parts.append(f"{placeholder_name} = {placeholder_value}")
            attr_names[placeholder_name]  = key
            attr_values[placeholder_value] = value

        update_expr = "SET " + ", ".join(expr_parts)

        table.update_item(
            Key={"claim_id": claim_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=attr_values,
        )
        logger.info(f"update_claim: {claim_id} — fields: {list(updates.keys())}")
    except Exception as e:
        logger.error(f"update_claim failed for {claim_id}: {e}", exc_info=True)
        raise


async def get_claims_by_status(status: str) -> list:
    """Scan for all claims with a given status. Used for adjuster queue."""
    try:
        table    = _get_claims_table()
        response = table.scan(
            FilterExpression=Attr("status").eq(status)
        )
        return response.get("Items", [])
    except Exception as e:
        logger.error(f"get_claims_by_status failed for status={status}: {e}", exc_info=True)
        return []
