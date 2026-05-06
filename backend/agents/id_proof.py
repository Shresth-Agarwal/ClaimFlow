import asyncio
from difflib import SequenceMatcher
import logging
import os
import re
import sys
import time
from dotenv import load_dotenv
import cv2
import numpy as np
import pytesseract
from PIL import Image

load_dotenv()

# Configure Tesseract path from environment variable and common Windows install locations.
# If no explicit path is found, allow pytesseract to fall back to system PATH.
def _find_tesseract_cmd() -> str | None:
    env_path = os.getenv('TESSERACT_PATH')
    candidates = [env_path, r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            logging.info(f"Using Tesseract executable at: {candidate}")
            return candidate
    logging.warning(
        "Tesseract executable not found. Please install Tesseract OCR and set TESSERACT_PATH if needed."
    )
    return env_path

_tesseract_cmd = _find_tesseract_cmd()
if _tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd

def _extract_text(image_path: str) -> str:
    try:
        if not os.path.exists(image_path):
            logging.warning(f"Image file not found: {image_path}")
            return ""

        img = cv2.imread(image_path)
        if img is None:
            try:
                with Image.open(image_path) as pil_img:
                    pil_img = pil_img.convert("RGB")
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception as inner_exc:
                logging.warning(f"Unable to open image {image_path}: {inner_exc}")
                return ""

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(
            gray,
            None,
            fx=2,
            fy=2,
            interpolation=cv2.INTER_CUBIC,
        )

        try:
            text = pytesseract.image_to_string(
                gray,
                config="--psm 6",
            )
        except pytesseract.TesseractNotFoundError as e:
            logging.error(
                "Tesseract OCR not installed. Install from: https://github.com/UB-Mannheim/tesseract/wiki"
            )
            return ""
        except Exception as ocr_exc:
            logging.warning(f"OCR extraction failed: {ocr_exc}")
            return ""

        if text.strip() == "":
            return ""

        return text.strip()
    except Exception as exc:
        logging.error(f"Error extracting text from image: {exc}", exc_info=True)
        return ""


def _normalize_text(text: str) -> str:
    normalized = (text or "").lower()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


async def run(input: dict) -> dict:
    """
    Verify ID proof from image.
    
    Args:
        input: {
            "id_type": str,
            "id_value": str,
            "image_path": str
        }
    
    Returns:
        {
            "is_valid": bool,
            "confidence": float,
            "id_match": bool,
            "reason": str,
            "extracted_text": str
        }
    """
    start_time = time.time()

    try:
        id_type = input.get("id_type")
        id_value = input.get("id_value")
        image_path = input.get("image_path")

        missing = [k for k in ("id_type", "id_value", "image_path") if not input.get(k)]
        if missing:
            return {
                "is_valid": False,
                "confidence": 0.0,
                "id_match": False,
                "reason": f"Missing required field(s): {', '.join(missing)}",
                "extracted_text": "",
            }

        def _process() -> dict:
            extracted_text = _extract_text(image_path)
            if not extracted_text:
                return {
                    "is_valid": False,
                    "id_match": False,
                    "confidence": 0.2,
                    "reason": "ID not found in extracted document text",
                    "extracted_text": "",
                }

            normalized_text = _normalize_text(extracted_text)
            normalized_id_value = _normalize_text(str(id_value))
            tokens = normalized_text.split()

            exact_match = normalized_id_value in normalized_text if normalized_id_value else False
            fuzzy_match = False

            if normalized_id_value and not exact_match and tokens:
                context_keywords = ["id", "number", "roll", _normalize_text(str(id_type))]
                candidate_tokens = tokens[:]
                for idx, tok in enumerate(tokens):
                    if tok in context_keywords:
                        start = max(0, idx - 4)
                        end = min(len(tokens), idx + 5)
                        candidate_tokens.extend(tokens[start:end])

                best_similarity = 0.0
                for tok in candidate_tokens:
                    sim = SequenceMatcher(None, normalized_id_value, tok).ratio()
                    if sim > best_similarity:
                        best_similarity = sim
                fuzzy_match = best_similarity > 0.8

            id_match = exact_match or fuzzy_match
            confidence = 0.9 if exact_match else (0.7 if fuzzy_match else 0.2)
            
            return {
                "is_valid": id_match,
                "id_match": id_match,
                "confidence": confidence,
                "reason": "Exact ID match found in document"
                if exact_match
                else (
                    "Approximate match found; possible OCR variation"
                    if fuzzy_match
                    else "ID not found in extracted document text"
                ),
                "extracted_text": extracted_text,
            }

        result = await asyncio.to_thread(_process)
        return result
        
    except Exception as exc:
        logging.error("ID proof verification failed", exc_info=True)
        return {
            "is_valid": False,
            "confidence": 0.0,
            "id_match": False,
            "reason": f"Verification error: {str(exc)}",
            "extracted_text": "",
        }
