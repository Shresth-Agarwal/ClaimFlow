from fastapi import HTTPException, UploadFile
from backend.database.interfaces import IUserRepository

class IdentityVerificationService:
    def __init__(self, db: IUserRepository):
        self.db = db

    async def verify_agent_with_id_proof(
        self,
        agent_id: int,
        id_type: str,
        id_number: str,
        id_proof: UploadFile,
    ) -> dict:
        """Verify an agent by submitted ID proof and prepare for future vision agent integration."""
        if not id_type or not id_number:
            raise HTTPException(status_code=400, detail="ID type and number are required")

        file_contents = await id_proof.read()
        if not file_contents:
            raise HTTPException(status_code=400, detail="ID proof file is empty")

        verified = self._evaluate_id_proof(file_contents, id_type, id_number)
        if verified:
            success = self.db.update_verification_status(agent_id, True)
            if not success:
                raise HTTPException(status_code=404, detail="Agent not found")
            return {
                "status": "success",
                "message": "Agent verified successfully",
                "verification_source": "id_proof"
            }

        raise HTTPException(status_code=400, detail="Identity verification failed")

    def _evaluate_id_proof(self, file_bytes: bytes, id_type: str, id_number: str) -> bool:
        # TODO: Replace this stub with a call to your vision verification agent.
        return len(file_bytes) > 0

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