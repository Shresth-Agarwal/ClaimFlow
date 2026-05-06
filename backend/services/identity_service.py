import asyncio
import io
import logging
import tempfile
import os
from fastapi import HTTPException, UploadFile
from backend.database.interfaces import IUserRepository
from backend.agents import id_proof

logger = logging.getLogger("identity_service")

class IdentityVerificationService:
    def __init__(self, db: IUserRepository):
        self.db = db

    async def verify_agent_with_id_proof(
        self,
        agent_id: int,
        id_type: str,
        id_number: str,
        id_proof_file: UploadFile,
    ) -> dict:
        """Verify an agent by submitted ID proof using OCR verification."""
        if not id_type or not id_number:
            raise HTTPException(status_code=400, detail="ID type and number are required")

        file_contents = await id_proof_file.read()
        if not file_contents:
            raise HTTPException(status_code=400, detail="ID proof file is empty")

        return await self.verify_agent_with_id_proof_bytes(
            agent_id,
            id_type,
            id_number,
            file_contents,
            id_proof_file.filename or "id_proof.png",
        )

    async def verify_agent_with_id_proof_bytes(
        self,
        agent_id: int,
        id_type: str,
        id_number: str,
        file_bytes: bytes,
        filename: str,
    ) -> dict:
        """Verify an agent by raw image bytes using OCR verification."""
        if not id_type or not id_number:
            raise HTTPException(status_code=400, detail="ID type and number are required")

        if not file_bytes:
            raise HTTPException(status_code=400, detail="ID proof file is empty")

        try:
            # Create temporary file for OCR processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
                tmp_file.write(file_bytes)
                tmp_path = tmp_file.name

            try:
                # Call the id_proof agent with the temporary file
                verification_result = await id_proof.run({
                    "id_type": id_type,
                    "id_value": id_number,
                    "image_path": tmp_path,
                })

                logger.info(f"ID proof verification result: {verification_result}")

                # Extract verification result
                is_valid = verification_result.get("is_valid", False)
                confidence = verification_result.get("confidence", 0.0)

                if is_valid and confidence > 0.6:  # High confidence threshold
                    success = self.db.update_verification_status(agent_id, True)
                    if not success:
                        raise HTTPException(status_code=404, detail="Agent not found")
                    
                    return {
                        "status": "success",
                        "message": "Agent verified successfully",
                        "verification_source": "id_proof",
                        "confidence": confidence,
                        "id_match": verification_result.get("id_match", False),
                    }

                raise HTTPException(
                    status_code=400,
                    detail=f"Identity verification failed: {verification_result.get('reason', 'Invalid ID')} (confidence: {confidence:.2f})"
                )

            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temp file {tmp_path}: {cleanup_error}")

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"ID proof verification error: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Verification failed: {str(exc)}")

    def verify_agent(self, agent_id: int, document_data: dict) -> dict:
        """
        Mock identity verification.
        Expects document_data to have a boolean 'is_valid' flag for testing.
        """
        if document_data.get("is_valid") is True:
            success = self.db.update_verification_status(agent_id, True)
            if not success:
                raise HTTPException(status_code=404, detail="Agent not found")
            return {"status": "success", "message": "Agent verified successfully"}
        
        raise HTTPException(status_code=400, detail="Identity verification failed")