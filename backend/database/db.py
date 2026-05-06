# backend/database/db.py
# Single source of truth for the active database instance.
#
# Set USE_MOCK_DB=true in .env to use the in-memory mock (no AWS needed).
# Leave it unset or set to false to use DynamoDB.
#
# Every file that needs the DB should import from here:
#   from backend.database.db import db

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("claimflow.db")

USE_MOCK = os.getenv("USE_MOCK_DB", "false").lower() == "true"

if USE_MOCK:
    from backend.database.mock_db import MockUserRepository
    db = MockUserRepository()
    logger.info("Database: using MockUserRepository (in-memory)")
else:
    from backend.database.dynamo_db import DynamoUserRepository
    db = DynamoUserRepository()
    logger.info("Database: using DynamoUserRepository (DynamoDB)")
