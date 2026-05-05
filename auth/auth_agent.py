import asyncio
from difflib import SequenceMatcher
import re
import sys
import time

import cv2
import pytesseract
from PIL import Image

print("TESSERACT PATH:", pytesseract.pytesseract.tesseract_cmd)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"

def _extract_text(image_path: str) -> str:
    try:
        img = cv2.imread(image_path)
        print("Image loaded:", img is not None)
        if img is None:
            return ""

        print("\n=== DIRECT OCR TEST ===")
        img_test = Image.open("C:/Srivalli/Akhira/dataset/agent_id_image.png")
        print(pytesseract.image_to_string(img_test))

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(
            gray,
            None,
            fx=2,
            fy=2,
            interpolation=cv2.INTER_CUBIC,
        )

        text = pytesseract.image_to_string(
            gray,
            config="--psm 6",
        )
        print("\n=== RAW OCR OUTPUT ===")
        print(text)

        if text.strip() == "":
            return ""

        return text.strip()
    except Exception as exc:
        print("OCR error:", exc)
        return ""


def _normalize_text(text: str) -> str:
    normalized = (text or "").lower()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


async def run(input: dict) -> dict:
    start_time = time.time()

    def _response(success: bool, data: dict, error: str | None, fallback_used: bool) -> dict:
        return {
            "success": success,
            "data": data,
            "error": error,
            "meta": {
                "latency_sec": round(time.time() - start_time, 4),
                "fallback_used": fallback_used,
            },
        }

    try:
        id_type = input.get("id_type")
        id_value = input.get("id_value")
        image_path = input.get("image_path")

        missing = [k for k in ("id_type", "id_value", "image_path") if not input.get(k)]
        if missing:
            return _response(False, {}, f"Missing required field(s): {', '.join(missing)}", False)

        def _process() -> tuple[dict, bool]:
            extracted_text = _extract_text(image_path)
            print("\n=== OCR TEXT ===")
            print(extracted_text)
            if not extracted_text:
                id_match = False
                confidence = 0.2
                print("\n=== MATCH RESULT ===")
                print({"id_match": id_match, "confidence": confidence})
                return (
                    {
                        "is_valid": False,
                        "id_match": id_match,
                        "confidence": confidence,
                        "reason": "ID not found in extracted document text",
                        "extracted_text": "",
                    },
                    True,
                )

            normalized_text = _normalize_text(extracted_text)
            normalized_id_value = _normalize_text(str(id_value))
            tokens = normalized_text.split()

            exact_match = normalized_id_value in normalized_text if normalized_id_value else False
            fuzzy_match = False

            if normalized_id_value and not exact_match and tokens:
                # Optionally prioritize tokens near id-related context words.
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
            print("\n=== MATCH RESULT ===")
            print({"id_match": id_match, "confidence": confidence})
            return (
                {
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
                },
                False,
            )

        data, fallback_used = await asyncio.to_thread(_process)
        is_valid = data["is_valid"]
        confidence = data["confidence"]
        return {
            "is_valid": is_valid,
            "confidence": confidence,
        }
    except Exception as exc:
        return {
            "is_valid": False,
            "confidence": 0.0,
        }


if __name__ == "__main__":
    test_input = {
        "id_type": "agent_id",
        "id_value": "AGT12345",
        "image_path": "C:/Srivalli/Akhira/dataset/agent_id_image.png",
    }

    print("\n=== INPUT ===")
    print(test_input)

    result = asyncio.run(run(test_input))
    print("\n=== AUTH OUTPUT ===")
    print(result)
