import asyncio
import json
import os
import random
import re
import tempfile
import time
import traceback
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen
from dotenv import load_dotenv
import pytesseract
import cv2

load_dotenv()

try:
    boto3 = __import__("boto3")
except Exception:  # pragma: no cover - optional at runtime
    boto3 = None

pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH", "tesseract")


USE_MOCK = True
_TROCR_CACHE: dict[str, object] = {}
VISION_STRAND_META = {
    "strand_name": "vision_strand",
    "strand_version": "1.0.0",
    "capabilities": [
        "textract_ocr",
        "tesseract_fallback",
        "trocr_handwriting_recovery",
        "domain_detection",
        "document_classification",
        "structured_extraction",
    ],
}


def _vision_execution_meta() -> dict:
    return {
        "strand_name": VISION_STRAND_META["strand_name"],
        "strand_version": VISION_STRAND_META["strand_version"],
        "execution_mode": "mock_pipeline" if USE_MOCK else "model_pipeline",
        "reasoning_mode": "deterministic_ocr_hybrid",
        "strand_capabilities": VISION_STRAND_META["capabilities"],
    }


def _to_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _aws_runtime_config(input_payload: dict | None = None) -> dict:
    payload = input_payload or {}
    return {
        "aws_enabled": _to_bool(payload.get("aws_enabled"), _to_bool(os.getenv("CLAIMFLOW_AWS_ENABLED"), False)),
        "aws_region": payload.get("aws_region") or os.getenv("AWS_REGION") or "us-east-1",
        "s3_bucket": payload.get("s3_bucket") or os.getenv("CLAIMFLOW_S3_BUCKET") or "",
        "textract_mode": (payload.get("textract_mode") or os.getenv("CLAIMFLOW_TEXTRACT_MODE") or "analyze_document").lower(),
        "claim_id": payload.get("claim_id"),
    }


def generate_s3_uri(bucket: str, key: str) -> str:
    clean_bucket = (bucket or "").strip()
    clean_key = (key or "").lstrip("/")
    return f"s3://{clean_bucket}/{clean_key}"


def upload_file_to_s3(local_path: str, bucket: str, key: str, region_name: str) -> str:
    if boto3 is None:
        raise RuntimeError("boto3 is not available; cannot upload to S3.")
    s3 = boto3.client("s3", region_name=region_name)
    s3.upload_file(local_path, bucket, key)
    return generate_s3_uri(bucket, key)


def download_file_from_s3(s3_uri: str, local_path: str, region_name: str) -> str:
    if boto3 is None:
        raise RuntimeError("boto3 is not available; cannot download from S3.")
    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3" or not parsed.netloc or not parsed.path:
        raise ValueError(f"Invalid S3 URI: {s3_uri}")
    s3 = boto3.client("s3", region_name=region_name)
    s3.download_file(parsed.netloc, parsed.path.lstrip("/"), local_path)
    return local_path


def _is_textract_compatible_file(file_path: str) -> bool:
    ext = Path(file_path).suffix.lower()
    # Phase 1: keep PDF disabled.
    return ext in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def _ocr_text_quality_score(text: str) -> float:
    raw = (text or "").strip()
    if not raw:
        return 0.0
    words = re.findall(r"[A-Za-z0-9]+", raw)
    total_chars = len(raw)
    alnum_chars = len(re.findall(r"[A-Za-z0-9]", raw))
    non_alnum_ratio = 1.0 - (alnum_chars / max(1, total_chars))
    short_word_ratio = (
        sum(1 for w in words if len(w) <= 2) / max(1, len(words))
    )
    length_bonus = min(1.0, len(words) / 35.0)
    return max(
        0.0,
        min(1.0, (1.0 - non_alnum_ratio) * 0.45 + (1.0 - short_word_ratio) * 0.35 + length_bonus * 0.20),
    )


def detect_handwritten_content(text: str, image_path: str | None = None) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    quality = _ocr_text_quality_score(text)
    if quality < 0.45:
        reasons.append("low_ocr_quality")
    words = re.findall(r"[A-Za-z0-9]+", text or "")
    if words:
        short_ratio = sum(1 for w in words if len(w) <= 2) / max(1, len(words))
        if short_ratio > 0.45:
            reasons.append("fragmented_words")
    noisy_ratio = (
        len(re.findall(r"[^A-Za-z0-9\s:/\\.,\\-]", text or "")) / max(1, len((text or "").strip()))
    )
    if noisy_ratio > 0.18:
        reasons.append("noisy_extraction")

    if image_path:
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                # Low sharpness + sparse edges often indicates rough handwritten scans/photos.
                lap_var = cv2.Laplacian(img, cv2.CV_64F).var()
                edges = cv2.Canny(img, 50, 150)
                edge_density = float((edges > 0).sum()) / max(1.0, float(edges.size))
                if lap_var < 70 and 0.01 < edge_density < 0.12:
                    reasons.append("handwriting_like_strokes")
        except Exception:
            pass
    return bool(reasons), reasons


def run_trocr_recognition(image_path: str, model_id: str = "microsoft/trocr-base-handwritten", max_new_tokens: int = 256) -> str:
    try:
        cache_key = f"trocr::{model_id}"
        if cache_key not in _TROCR_CACHE:
            from PIL import Image
            torch = __import__("torch")
            transformers = __import__("transformers")
            TrOCRProcessor = transformers.TrOCRProcessor
            VisionEncoderDecoderModel = transformers.VisionEncoderDecoderModel

            processor = TrOCRProcessor.from_pretrained(model_id)
            model = VisionEncoderDecoderModel.from_pretrained(model_id)
            model.eval()
            _TROCR_CACHE[cache_key] = {
                "processor": processor,
                "model": model,
                "torch": torch,
                "image_cls": Image,
            }

        bundle = _TROCR_CACHE[cache_key]
        processor = bundle["processor"]
        model = bundle["model"]
        torch = bundle["torch"]
        Image = bundle["image_cls"]

        image = Image.open(image_path).convert("RGB")
        pixel_values = processor(images=image, return_tensors="pt").pixel_values
        with torch.no_grad():
            generated_ids = model.generate(pixel_values, max_new_tokens=max_new_tokens)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)
        return (text[0] if text else "").strip()
    except Exception as exc:
        print(f"Handwriting enhancement skipped: {exc}")
        return ""


def recover_low_confidence_ocr(primary_text: str, image_path: str) -> tuple[str, dict]:
    metadata = {
        "handwriting_detected": False,
        "handwriting_ai_used": False,
        "ocr_recovery_applied": False,
    }
    detected, reasons = detect_handwritten_content(primary_text, image_path)
    metadata["handwriting_detected"] = detected
    if not detected:
        return primary_text, metadata

    trocr_text = run_trocr_recognition(image_path)
    if not trocr_text:
        return primary_text, metadata

    base_score = _ocr_text_quality_score(primary_text)
    trocr_score = _ocr_text_quality_score(trocr_text)
    metadata["handwriting_ai_used"] = True
    if trocr_score >= base_score + 0.08:
        metadata["ocr_recovery_applied"] = True
        print(f"OCR recovery applied via TrOCR: reasons={','.join(reasons[:3])}")
        return trocr_text, metadata
    return primary_text, metadata


def analyze_document_forms(textract_response: dict) -> list[dict]:
    blocks = textract_response.get("Blocks") or []
    by_id = {b.get("Id"): b for b in blocks if b.get("Id")}
    forms: list[dict] = []
    for block in blocks:
        if block.get("BlockType") != "KEY_VALUE_SET":
            continue
        if "KEY" not in (block.get("EntityTypes") or []):
            continue
        key_text = ""
        value_text = ""
        for rel in block.get("Relationships") or []:
            if rel.get("Type") == "CHILD":
                key_text = " ".join(
                    child.get("Text", "")
                    for cid in rel.get("Ids") or []
                    for child in [by_id.get(cid) or {}]
                    if child.get("BlockType") == "WORD"
                ).strip()
            if rel.get("Type") == "VALUE":
                for value_id in rel.get("Ids") or []:
                    value_block = by_id.get(value_id) or {}
                    for value_rel in value_block.get("Relationships") or []:
                        if value_rel.get("Type") == "CHILD":
                            value_text = " ".join(
                                child.get("Text", "")
                                for cid in value_rel.get("Ids") or []
                                for child in [by_id.get(cid) or {}]
                                if child.get("BlockType") == "WORD"
                            ).strip()
        if key_text:
            forms.append({"key": key_text, "value": value_text})
    return forms


def analyze_document_tables(textract_response: dict) -> list[list[list[str]]]:
    blocks = textract_response.get("Blocks") or []
    by_id = {b.get("Id"): b for b in blocks if b.get("Id")}
    tables: list[list[list[str]]] = []
    for block in blocks:
        if block.get("BlockType") != "TABLE":
            continue
        rows: dict[int, dict[int, str]] = {}
        for rel in block.get("Relationships") or []:
            if rel.get("Type") != "CHILD":
                continue
            for cid in rel.get("Ids") or []:
                cell = by_id.get(cid) or {}
                if cell.get("BlockType") != "CELL":
                    continue
                row_idx = int(cell.get("RowIndex") or 0)
                col_idx = int(cell.get("ColumnIndex") or 0)
                text_parts: list[str] = []
                for cell_rel in cell.get("Relationships") or []:
                    if cell_rel.get("Type") != "CHILD":
                        continue
                    for wid in cell_rel.get("Ids") or []:
                        word = by_id.get(wid) or {}
                        if word.get("BlockType") == "WORD":
                            text_parts.append(word.get("Text", ""))
                rows.setdefault(row_idx, {})[col_idx] = " ".join(text_parts).strip()
        table_grid: list[list[str]] = []
        for row_idx in sorted(rows.keys()):
            row = rows[row_idx]
            table_grid.append([row.get(col_idx, "") for col_idx in sorted(row.keys())])
        tables.append(table_grid)
    return tables


def extract_document_text(file_path: str, region_name: str, textract_mode: str = "analyze_document") -> str:
    if boto3 is None:
        raise RuntimeError("boto3 is not available; cannot call Textract.")
    if not _is_textract_compatible_file(file_path):
        return ""
    with open(file_path, "rb") as f:
        document_bytes = f.read()
    textract = boto3.client("textract", region_name=region_name)
    if textract_mode == "detect_document_text":
        response = textract.detect_document_text(Document={"Bytes": document_bytes})
    else:
        response = textract.analyze_document(Document={"Bytes": document_bytes}, FeatureTypes=["FORMS", "TABLES"])
        _ = analyze_document_forms(response)
        _ = analyze_document_tables(response)
    lines = [
        block.get("Text", "").strip()
        for block in (response.get("Blocks") or [])
        if block.get("BlockType") == "LINE" and block.get("Text")
    ]
    return "\n".join(lines).strip()


def _resolve_evidence_to_local_path(image_ref: str, aws_cfg: dict) -> tuple[str | None, str | None]:
    if not image_ref:
        return None, None
    if Path(image_ref).exists():
        return image_ref, None
    if image_ref.startswith("s3://"):
        if not aws_cfg.get("aws_enabled"):
            return None, None
        suffix = Path(urlparse(image_ref).path).suffix or ".bin"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
        download_file_from_s3(image_ref, temp_path, aws_cfg["aws_region"])
        return temp_path, temp_path
    parsed = urlparse(image_ref)
    if parsed.scheme in {"http", "https"}:
        suffix = Path(parsed.path).suffix or ".bin"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
        with urlopen(image_ref) as src, open(temp_path, "wb") as dst:
            dst.write(src.read())
        return temp_path, temp_path
    return None, None


def _extract_text_with_ocr_routing(image_ref: str, aws_cfg: dict) -> tuple[str, str, bool, dict]:
    local_path, cleanup_path = _resolve_evidence_to_local_path(image_ref, aws_cfg)
    ocr_meta = {
        "handwriting_detected": False,
        "handwriting_ai_used": False,
        "ocr_recovery_applied": False,
    }
    try:
        if not local_path:
            return "", "none", False, ocr_meta
        if aws_cfg.get("aws_enabled") and _is_textract_compatible_file(local_path):
            try:
                text = extract_document_text(local_path, aws_cfg["aws_region"], aws_cfg["textract_mode"])
                if text:
                    text, ocr_meta = recover_low_confidence_ocr(text, local_path)
                    print("OCR source: textract")
                    return text, "textract", True, ocr_meta
                print("Textract fallback triggered: empty extraction")
            except Exception as exc:
                print(f"Textract fallback triggered: {exc}")
        text = _extract_text_from_image(local_path)
        if text:
            text, ocr_meta = recover_low_confidence_ocr(text, local_path)
            print("OCR source: tesseract")
            return text, "tesseract", bool(aws_cfg.get("aws_enabled")), ocr_meta
        print("OCR extraction failed")
        return "", "tesseract", bool(aws_cfg.get("aws_enabled")), ocr_meta
    finally:
        if cleanup_path and os.path.exists(cleanup_path):
            try:
                os.remove(cleanup_path)
            except OSError:
                pass


def _extract_text_from_image(image_path: str) -> str:
    try:
        img = cv2.imread(image_path)
        if img is None:
            return ""

        configs = [
            "--oem 3 --psm 6",
            "--oem 3 --psm 4",
            "--oem 3 --psm 11",
        ]
        keywords = ["hospital", "bill", "invoice", "amount", "total", "rs"]

        # Pass 1: grayscale + resize + binary threshold.
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, binary = cv2.threshold(resized, 150, 255, cv2.THRESH_BINARY)

        # Pass 2: grayscale + adaptive threshold.
        adaptive = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )

        # Pass 3: original image.
        variants = [binary, adaptive, img]

        texts: list[str] = []
        for img_variant in variants:
            for config in configs:
                text = pytesseract.image_to_string(img_variant, config=config) or ""
                texts.append(text)

        if not any((t or "").strip() for t in texts):
            return ""

        def _score_text(text: str) -> tuple[int, int, int]:
            lowered = (text or "").lower()
            alnum_score = len(re.findall(r"\w", lowered))
            keyword_score = sum(1 for kw in keywords if kw in lowered)
            return (alnum_score, keyword_score, len((text or "").strip()))

        best_text = max(texts, key=_score_text, default="")
        best_text = (best_text or "").strip()
    except Exception as e:
        print(f"OCR extraction failed: {e!r}")
        traceback.print_exc()
        return ""
    return best_text if best_text else ""


def _preprocess_text(text: str) -> str:
    cleaned = (text or "").lower()
    cleaned = cleaned.replace("rs.", "rs")
    cleaned = cleaned.replace("amt", "amount")
    cleaned = re.sub(r"[^a-z0-9\s:/\-.,]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def extract_hospital(text: str) -> str | None:
    lines = [re.sub(r"\s+", " ", ln).strip(" -:,.") for ln in (text or "").splitlines()]
    lines = [line for line in lines if line]
    for line in lines:
        if "hospital" in line.lower():
            return line
    return lines[0] if lines else None


def extract_amount(text: str) -> int | None:
    patterns = [
        r"(total|amount|bill)[^0-9]{0,10}([0-9]{3,6})",
        r"(rs|inr)[^0-9]{0,5}([0-9]{3,6})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text or "", re.IGNORECASE)
        if match:
            try:
                return int(match.group(2))
            except (TypeError, ValueError):
                continue

    fallback_match = re.search(r"\b([0-9]{3,6})\b", text or "")
    if fallback_match:
        try:
            return int(fallback_match.group(1))
        except ValueError:
            return None
    return None


def extract_date(text: str) -> str | None:
    match = re.search(r"\b(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|\d{4}-\d{2}-\d{2})\b", text or "")
    return match.group(1) if match else None


def extract_doc_type(text: str) -> str | None:
    lowered = (text or "").lower()
    if "bill" in lowered or "invoice" in lowered:
        return "bill"
    return None


def _detect_domain_from_text(text: str) -> str:
    t = (text or "").lower()
    health_kw = (
        "hospital",
        "uhid",
        "patient",
        "doctor",
        "prescription",
        "rx",
        "discharge",
        "lab",
        "investigation",
        "ward",
        "admission",
    )
    motor_kw = ("registration", "rc", "chassis", "engine", "vehicle", "driving licence", "dl no", "workshop", "garage")
    crop_kw = ("crop", "land", "survey", "acre", "hectare", "weather", "rainfall", "drought", "pest")
    prop_kw = ("fir", "police", "station", "complaint", "fire", "flood", "damage", "ownership", "estimate")

    scores = {
        "health": sum(1 for k in health_kw if k in t),
        "motor": sum(1 for k in motor_kw if k in t),
        "crop": sum(1 for k in crop_kw if k in t),
        "property": sum(1 for k in prop_kw if k in t),
    }
    best = max(scores.items(), key=lambda kv: kv[1])[0]
    return best if scores[best] > 0 else "health"


def _detect_document_type(domain: str, text: str) -> str:
    t = (text or "").lower()
    if domain == "health":
        # Strong bill/invoice markers should win even if "report/test" appears in line items.
        if (
            "in patient bill" in t
            or re.search(r"\bbill\s*no\b", t)
            or re.search(r"\bbillno\b", t)
            or "bill of supply" in t
            or "invoice" in t
        ):
            return "hospital_bill"
        if "discharge" in t and ("summary" in t or "diagnosis" in t):
            return "discharge_summary"
        if "rx" in t or "prescription" in t or "tablet" in t or "capsule" in t:
            return "prescription"
        if "lab" in t or "report" in t or "investigation" in t or "test" in t:
            return "lab_report"
        if "bill" in t:
            return "hospital_bill"
        return "health_document"

    if domain == "motor":
        if "driving licence" in t or "dl no" in t or re.search(r"\bdl[-\s]*no\b", t):
            return "driver_license"
        if "registration" in t or re.search(r"\brc\b", t) or "chassis" in t or "engine" in t:
            return "rc"
        if "workshop" in t or "garage" in t or ("invoice" in t and ("labour" in t or "labor" in t)):
            return "repair_invoice"
        return "motor_document"

    if domain == "crop":
        if "weather" in t or "rainfall" in t:
            return "weather_report"
        if "survey" in t or "land" in t or "patta" in t or "khata" in t:
            return "land_document"
        return "crop_document"

    if domain == "property":
        if "fir" in t and ("police" in t or "station" in t):
            return "fir"
        if "fire" in t and "report" in t:
            return "fire_report"
        if "ownership" in t or "sale deed" in t:
            return "ownership_document"
        if "estimate" in t or "quotation" in t:
            return "repair_estimate"
        return "property_document"

    return "document"


def _extract_date_near(label: str, text: str) -> str | None:
    # Supports: dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd, dd-Mon-yyyy
    date_pat = r"(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}[-/][a-z]{3}[-/]\d{4})"
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in (text or "").splitlines() if ln and ln.strip()]
    for ln in lines:
        if label.lower() not in ln.lower():
            continue
        m = re.search(rf"\b{re.escape(label)}\b[^0-9]{{0,25}}{date_pat}", ln, re.IGNORECASE)
        if m:
            return m.group(1)
    m = re.search(rf"\b{re.escape(label)}\b[^0-9]{{0,25}}{date_pat}", text or "", re.IGNORECASE)
    return m.group(1) if m else None


def _largest_money_amount(text: str) -> float | None:
    # Only consider values like 57,450.00 and ignore parenthesized values and common ID contexts.
    raw = text or ""
    money_pat = re.compile(r"\b(\d{1,3}(?:,\d{3})+\.\d{2})\b")
    candidates: list[float] = []
    for m in money_pat.finditer(raw):
        start = m.start()
        end = m.end()
        before = raw[max(0, start - 1) : start]
        after = raw[end : min(len(raw), end + 1)]
        if before == "(" or after == ")":
            continue
        window = raw[max(0, start - 25) : min(len(raw), end + 25)].lower()
        if any(k in window for k in ("gst", "gstin", "hsn", "sac", "code", "item", "service", "uhid")):
            continue
        try:
            candidates.append(float(m.group(1).replace(",", "")))
        except ValueError:
            continue
    return max(candidates) if candidates else None


def _visual_indicators(domain: str, text: str) -> list[str]:
    t = (text or "").lower()
    indicators: list[str] = []
    if domain == "motor":
        for k in ("rust", "dent", "dents", "crack", "cracks"):
            if k in t:
                indicators.append(k if k != "dents" else "dents")
    if domain == "property":
        for k in ("fire", "flood", "crack", "cracks", "structural"):
            if k in t:
                indicators.append("fire_damage" if k == "fire" else ("flood_marks" if k == "flood" else "structural_cracks"))
    if domain == "crop":
        for k in ("drought", "pest"):
            if k in t:
                indicators.append("drought" if k == "drought" else "pest_damage")
    if domain == "health":
        if any(k in t for k in ("illegible", "blur", "unclear", "not captured")):
            indicators.append("low_document_quality")
        if any(k in t for k in ("altered", "tampered", "suspicious")):
            indicators.append("suspicious_formatting")
    # De-dup while preserving order
    out: list[str] = []
    for x in indicators:
        if x not in out:
            out.append(x)
    return out


def _confidence_from_fields(structured_data: dict, key_fields: list[str]) -> float:
    count = sum(1 for k in key_fields if structured_data.get(k) is not None)
    return min(0.95, 0.35 + (0.15 * count))


def _parse_health_hospital_bill(text: str) -> dict:
    # Extends the existing bill parsing with admission/discharge dates.
    parsed = _parse_health_document(text)
    structured = parsed.get("structured_data") or {}
    admission_date = _extract_date_near("Admission Date", text) or _extract_date_near("Admission", text)
    discharge_date = _extract_date_near("Discharge Date", text) or _extract_date_near("Discharge", text)
    if admission_date:
        structured["admission_date"] = admission_date
    if discharge_date:
        structured["discharge_date"] = discharge_date
    structured["document_type"] = "hospital_bill"
    conf = _confidence_from_fields(
        structured,
        ["patient_name", "bill_number", "bill_amount", "date_of_service", "admission_date", "discharge_date"],
    )
    return {"structured_data": structured, "confidence": conf}


def _parse_health_discharge_summary(text: str) -> dict:
    raw = text or ""
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in raw.splitlines() if ln and ln.strip()]
    patient_name = None
    for ln in lines:
        if "name" in ln.lower():
            m = re.search(r"\bname\b\s*[:\-]?\s*([a-z][a-z .]{2,40}?)(?:\s+\b(age|sex|uhid)\b|$)", ln, re.IGNORECASE)
            if m:
                patient_name = m.group(1).strip(" -:,.")
                break
    admission_date = _extract_date_near("Admission Date", raw) or _extract_date_near("Admission", raw)
    discharge_date = _extract_date_near("Discharge Date", raw) or _extract_date_near("Discharge", raw)
    structured = {
        "patient_name": patient_name,
        "admission_date": admission_date,
        "discharge_date": discharge_date,
        "document_type": "discharge_summary",
    }
    conf = _confidence_from_fields(structured, ["patient_name", "admission_date", "discharge_date"])
    return {"structured_data": structured, "confidence": conf}


def _parse_health_prescription(text: str) -> dict:
    raw = text or ""
    patient_name = None
    m = re.search(
        r"\bname\b\s*[:\-]?\s*([a-z][a-z .]{2,40}?)(?:\s+\b(age|sex|uhid)\b|$)",
        raw,
        re.IGNORECASE,
    )
    if m:
        patient_name = m.group(1).strip(" -:,.")
    prescription_date = _extract_date_near("Date", raw)
    structured = {
        "patient_name": patient_name,
        "date_of_service": prescription_date,
        "document_type": "prescription",
    }
    conf = _confidence_from_fields(structured, ["patient_name", "date_of_service"])
    return {"structured_data": structured, "confidence": conf}


def _parse_health_lab_report(text: str) -> dict:
    raw = text or ""
    patient_name = None
    m = re.search(
        r"\bname\b\s*[:\-]?\s*([a-z][a-z .]{2,40}?)(?:\s+\b(age|sex|uhid)\b|$)",
        raw,
        re.IGNORECASE,
    )
    if m:
        patient_name = m.group(1).strip(" -:,.")
    report_date = _extract_date_near("Date", raw) or _extract_date_near("Report Date", raw)
    structured = {
        "patient_name": patient_name,
        "date_of_service": report_date,
        "document_type": "lab_report",
    }
    conf = _confidence_from_fields(structured, ["patient_name", "date_of_service"])
    return {"structured_data": structured, "confidence": conf}


def _parse_motor_repair_invoice(text: str) -> dict:
    raw = text or ""
    workshop_name = None
    for ln in raw.splitlines():
        if any(k in ln.lower() for k in ("workshop", "garage")):
            workshop_name = re.sub(r"\s+", " ", ln).strip(" -:,.")
            break
    repair_amount = _largest_money_amount(raw)
    structured = {
        "workshop_name": workshop_name,
        "repair_amount": repair_amount,
        "document_type": "repair_invoice",
    }
    conf = _confidence_from_fields(structured, ["workshop_name", "repair_amount"])
    return {"structured_data": structured, "confidence": conf}


def _parse_property_fir(text: str) -> dict:
    raw = text or ""
    fir_number = None
    m = re.search(r"\bfir\b[^0-9a-z]{0,10}([0-9]{2,10}[\/\-]?[0-9]{0,10})", raw, re.IGNORECASE)
    if m:
        fir_number = m.group(1).strip(" -:,.")
    station_name = None
    for ln in raw.splitlines():
        if "police station" in ln.lower() or ("station" in ln.lower() and "police" in ln.lower()):
            station_name = re.sub(r"\s+", " ", ln).strip(" -:,.")
            break
    complaint_date = _extract_date_near("Date", raw) or _extract_date_near("Complaint Date", raw)
    structured = {
        "fir_number": fir_number,
        "station_name": station_name,
        "complaint_date": complaint_date,
        "document_type": "fir",
    }
    conf = _confidence_from_fields(structured, ["fir_number", "station_name", "complaint_date"])
    return {"structured_data": structured, "confidence": conf}


def _parse_health_document(text: str) -> dict:
    raw = text or ""
    cleaned = _preprocess_text(raw)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in raw.splitlines() if ln and ln.strip()]

    def _extract_patient_name() -> str | None:
        for ln in lines:
            lnl = ln.lower()
            if "name" not in lnl:
                continue
            if "hospital" in lnl or "doctor" in lnl:
                continue
            m = re.search(
                r"\bname\b\s*[:\-]?\s*([a-z][a-z .]{2,40}?)(?:\s+\b(age|sex|uhid)\b|$)",
                ln,
                re.IGNORECASE,
            )
            if m:
                value = m.group(1).strip(" -:,.")
                if value and len(value) >= 3:
                    return value
        m = re.search(
            r"\bname\b\s*[:\-]?\s*([a-z][a-z .]{2,40}?)(?:\s+\b(age|sex|uhid)\b|$)",
            raw,
            re.IGNORECASE,
        )
        if m:
            value = m.group(1).strip(" -:,.")
            return value if value else None
        return None

    def _extract_bill_number() -> str | None:
        patterns = [
            r"\bbill\s*no\.?\b\s*[:\-]?\s*([a-z0-9][a-z0-9\-\/]{2,24})",
            r"\bbillno\b\s*[:\-]?\s*([a-z0-9][a-z0-9\-\/]{2,24})",
        ]
        for ln in lines:
            for pat in patterns:
                m = re.search(pat, ln, re.IGNORECASE)
                if m:
                    return m.group(1).strip(" -:,.")
        for pat in patterns:
            m = re.search(pat, raw, re.IGNORECASE)
            if m:
                return m.group(1).strip(" -:,.")
        return None

    def _extract_date_of_service() -> str | None:
        date_pat = r"(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}[-/][a-z]{3}[-/]\d{4})"
        for ln in lines:
            if "date" not in ln.lower():
                continue
            m = re.search(rf"\bdate\b[^0-9]{{0,10}}{date_pat}", ln, re.IGNORECASE)
            if m:
                return m.group(1)
        m = re.search(rf"\bdate\b[^0-9]{{0,10}}{date_pat}", cleaned, re.IGNORECASE)
        return m.group(1) if m else None

    def _extract_bill_amount() -> float | None:
        # Only consider monetary values like: 57,450.00
        money_pat = re.compile(r"\b(\d{1,3}(?:,\d{3})+\.\d{2})\b")
        candidates: list[float] = []

        for m in money_pat.finditer(raw):
            start = m.start()
            end = m.end()

            # Ignore values inside parentheses.
            before = raw[max(0, start - 1) : start]
            after = raw[end : min(len(raw), end + 1)]
            if before == "(" or after == ")":
                continue

            # Ignore lines that look like IDs/codes, not totals.
            window = raw[max(0, start - 25) : min(len(raw), end + 25)].lower()
            if any(k in window for k in ("gst", "gstin", "hsn", "sac", "code", "item", "service")):
                continue

            try:
                value = float(m.group(1).replace(",", ""))
            except ValueError:
                continue
            candidates.append(value)

        if not candidates:
            return None
        return max(candidates)

    patient_name = _extract_patient_name()
    bill_number = _extract_bill_number()
    date_of_service = _extract_date_of_service()
    bill_amount = _extract_bill_amount()

    hospital_name = None
    if "hospital" in cleaned:
        for ln in lines[:12]:
            lnl = ln.lower()
            if "hospital" not in lnl:
                continue
            if any(bad in lnl for bad in ("service", "services", "ward", "charges", "room rent", "ot ")):
                continue
            hospital_name = re.sub(r"\s+", " ", ln).strip(" -:,.")
            break

    extracted_fields = sum(
        1 for v in (patient_name, bill_number, bill_amount, date_of_service) if v is not None
    )
    confidence = min(0.9, 0.4 + (0.15 * extracted_fields))

    structured_data: dict = {
        "patient_name": patient_name,
        "bill_number": bill_number,
        "bill_amount": bill_amount,
        "date_of_service": date_of_service,
        "document_type": "hospital_bill",
    }
    if hospital_name:
        structured_data["hospital_name"] = hospital_name

    return {
        "structured_data": structured_data,
        "confidence": confidence,
    }


def _invoke_mock_model(image_ref: str, aws_cfg: dict | None = None) -> tuple[str, str, bool, dict]:
    cfg = aws_cfg or {}
    s = (image_ref or "").lower()
    image_path = (image_ref or "").strip()
    ocr_source = "none"
    aws_mode_used = bool(cfg.get("aws_enabled"))
    ocr_meta = {
        "handwriting_detected": False,
        "handwriting_ai_used": False,
        "ocr_recovery_applied": False,
    }

    def _estimate_from_severity(damage_severity: str | None) -> int:
        severity = (damage_severity or "minor").lower()
        if severity == "minor":
            return random.randint(2000, 8000)
        if severity == "moderate":
            return random.randint(8000, 20000)
        if severity == "severe":
            return random.randint(20000, 70000)
        return random.randint(2000, 8000)

    # Domain-first pipeline for local, OCR-able documents.
    try:
        extracted_text, ocr_source, aws_mode_used, ocr_meta = _extract_text_with_ocr_routing(image_path, cfg)
        if extracted_text:
            domain = _detect_domain_from_text(extracted_text)
            document_type = _detect_document_type(domain, extracted_text)
            indicators = _visual_indicators(domain, extracted_text)

            parsed: dict = {"structured_data": {}, "confidence": 0.5}
            if domain == "health":
                if document_type == "hospital_bill":
                    parsed = _parse_health_hospital_bill(extracted_text)
                elif document_type == "discharge_summary":
                    parsed = _parse_health_discharge_summary(extracted_text)
                elif document_type == "prescription":
                    parsed = _parse_health_prescription(extracted_text)
                elif document_type == "lab_report":
                    parsed = _parse_health_lab_report(extracted_text)
                else:
                    # Generic health doc: keep minimal, avoid hallucination.
                    parsed = {"structured_data": {"document_type": document_type}, "confidence": 0.5}

            elif domain == "motor":
                if document_type == "repair_invoice":
                    parsed = _parse_motor_repair_invoice(extracted_text)
                else:
                    parsed = {"structured_data": {"document_type": document_type}, "confidence": 0.5}

            elif domain == "property":
                if document_type == "fir":
                    parsed = _parse_property_fir(extracted_text)
                else:
                    parsed = {"structured_data": {"document_type": document_type}, "confidence": 0.5}

            elif domain == "crop":
                parsed = {"structured_data": {"document_type": document_type}, "confidence": 0.5}

            structured = parsed.get("structured_data") or {}
            structured["document_type"] = document_type
            confidence = float(parsed.get("confidence") or 0.5)

            estimate_amount = structured.get("bill_amount") or structured.get("repair_amount")

            result = json.dumps(
                {
                    "domain": domain,
                    "evidence_type": "document",
                    "document_type": document_type,
                    "structured_data": structured,
                    "visual_indicators": indicators,
                    "confidence": confidence,
                    "damage_estimate_inr": estimate_amount,
                    "damage_confidence": confidence,
                    "damage_zones": ["document_text"],
                }
            )
            return result, ocr_source, aws_mode_used, ocr_meta
    except Exception:
        # Keep mock model resilient; OCR layer already logs errors.
        pass

    if "car" in s:
        damage_severity = "moderate"
        return json.dumps(
            {
                "domain": "motor",
                "evidence_type": "image",
                "document_type": "accident_photo",
                "structured_data": {"damaged_parts": ["front_bumper", "hood"], "damage_severity": damage_severity},
                "visual_indicators": ["dents", "cracks"],
                "confidence": 0.87,
                "damage_estimate_inr": _estimate_from_severity(damage_severity),
                "damage_confidence": 0.87,
                "damage_zones": ["front_bumper", "hood"],
            }
        ), ocr_source, aws_mode_used, ocr_meta
    if "crop" in s:
        # Keep crop estimates lower and stable for demo realism.
        damage_severity = "minor"
        return json.dumps(
            {
                "domain": "crop",
                "evidence_type": "image",
                "document_type": "crop_damage_image",
                "structured_data": {"crop_type": "wheat", "damage_type": "drought", "loss_level": "medium"},
                "visual_indicators": ["drought"],
                "confidence": 0.78,
                "damage_estimate_inr": _estimate_from_severity(damage_severity),
                "damage_confidence": 0.78,
                "damage_zones": ["north_field", "irrigation_strip"],
            }
        ), ocr_source, aws_mode_used, ocr_meta
    if "house" in s or "building" in s:
        damage_severity = "moderate"
        return json.dumps(
            {
                "domain": "property",
                "evidence_type": "image",
                "document_type": "damage_photo",
                "structured_data": {"damage_type": "wind", "damage_area": "roof", "severity": "moderate"},
                "visual_indicators": ["structural_cracks"],
                "confidence": 0.84,
                "damage_estimate_inr": _estimate_from_severity(damage_severity),
                "damage_confidence": 0.84,
                "damage_zones": ["roof", "gutter_line"],
            }
        ), ocr_source, aws_mode_used, ocr_meta
    damage_severity = "minor"
    return json.dumps(
        {
            "domain": "motor",
            "evidence_type": "image",
            "document_type": "accident_photo",
            "structured_data": {"damaged_parts": ["unknown_panel"], "damage_severity": damage_severity},
            "visual_indicators": [],
            "confidence": 0.55,
            "damage_estimate_inr": _estimate_from_severity(damage_severity),
            "damage_confidence": 0.55,
            "damage_zones": ["general_body"],
        }
    ), ocr_source, aws_mode_used, ocr_meta


VISION_PROMPT = """You are an expert multi-domain insurance claim analysis AI.

Your task is to analyze the provided input (image or document) and extract structured information for insurance processing.

IMPORTANT RULES:

* Only use clearly visible evidence.
* Do NOT guess missing details.
* If unsure, return null values and reduce confidence.
* Be strictly conservative.

STEP 1: CLASSIFY DOMAIN
Classify the input into one of:

* "motor" (vehicle damage)
* "health" (hospital bills, discharge summaries)
* "crop" (agriculture damage)
* "property" (home/commercial damage)

STEP 2: DETERMINE EVIDENCE TYPE

* "image"
* "document"
* "mixed"

STEP 3: EXTRACT DOMAIN-SPECIFIC DATA

For "motor":

* damaged_parts (list)
* damage_severity ("minor" | "moderate" | "severe")

For "health":

* hospital_name
* bill_amount
* document_type ("bill" | "discharge_summary")
* date_of_service

For "crop":

* crop_type
* damage_type ("flood" | "drought" | "pest" | "unknown")
* loss_level ("low" | "medium" | "high")

For "property":

* damage_area ("roof" | "wall" | "interior" | "multiple")
* damage_type
* severity

STEP 4: GENERAL EXTRACTION

* Extract visible text (numbers, dates, IDs)

OUTPUT FORMAT (STRICT JSON ONLY):
{
"domain": "motor | health | crop | property",
"evidence_type": "image | document | mixed",
"extracted_data": {
"damaged_parts": null,
"damage_severity": null,
"hospital_name": null,
"bill_amount": null,
"document_type": null,
"date_of_service": null,
"crop_type": null,
"damage_type": null,
"loss_level": null,
"damage_area": null,
"severity": null
},
"confidence": float (0 to 1)
}

CONFIDENCE RULES:

Clear evidence -> >0.8
Partial -> 0.5-0.8
Unclear -> <0.5

IMPORTANT:
If output is not valid JSON, regenerate until it is valid.
"""

MODEL_ID = "anthropic.claude-3-5-sonnet"


async def run(input: dict) -> dict:
    start_time = time.time()
    aws_cfg = _aws_runtime_config(input)

    def _response(
        success: bool,
        data: dict,
        error: str | None,
        fallback_used: bool,
        ocr_source: str = "none",
        aws_mode_used: bool = False,
    ) -> dict:
        strand_meta = _vision_execution_meta()
        return {
            "success": success,
            "data": data,
            "error": error,
            "meta": {
                "latency_sec": round(time.time() - start_time, 4),
                "fallback_used": fallback_used,
                "ocr_source": ocr_source,
                "aws_mode_used": aws_mode_used,
                "strand_name": strand_meta["strand_name"],
                "strand_version": strand_meta["strand_version"],
                "execution_mode": strand_meta["execution_mode"],
                "reasoning_mode": strand_meta["reasoning_mode"],
                "strand_capabilities": strand_meta["strand_capabilities"],
            },
        }

    try:
        image_url = input.get("image_url") or input.get("evidence_url") or input.get("s3_uri")
        if not image_url:
            return _response(False, {}, "Missing required field: image_url/evidence_url/s3_uri", False)

        def _infer_media_type(url: str) -> str:
            path = urlparse(url).path.lower()
            if path.endswith(".png"):
                return "image/png"
            if path.endswith(".webp"):
                return "image/webp"
            if path.endswith(".gif"):
                return "image/gif"
            return "image/jpeg"

        def _extract_json_dict(text: str) -> dict:
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
            match = re.search(r"{.*}", text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return parsed
            raise json.JSONDecodeError("No valid JSON object found", text, 0)

        def _validate_required_keys(data: dict) -> None:
            required = { "damage_confidence", "damage_zones"}
            if not required.issubset(data.keys()):
                missing = sorted(required - set(data.keys()))
                raise ValueError(f"Missing required keys: {', '.join(missing)}")

        def _invoke_model() -> tuple[dict, str, bool]:
            if not USE_MOCK:
                def _invoke_real_model(prompt: str) -> str:
                    _ = prompt
                    raise RuntimeError(
                        "Real model inference is disabled in basic agents. Use claimflow/aws_agents for production Bedrock calls."
                    )
            else:

                def _invoke_real_model(prompt: str) -> str:
                    raise RuntimeError("_invoke_real_model must not run when USE_MOCK is True")

            model_ocr_source = "none"
            model_aws_mode_used = False
            model_ocr_meta = {
                "handwriting_detected": False,
                "handwriting_ai_used": False,
                "ocr_recovery_applied": False,
            }
            for attempt in range(2):
                prompt = VISION_PROMPT
                if attempt > 0:
                    prompt = (
                        VISION_PROMPT
                        + "\n\nYour previous response was not valid JSON. Return only a valid JSON object that matches the required schema."
                    )
                if USE_MOCK:
                    text, model_ocr_source, model_aws_mode_used, model_ocr_meta = _invoke_mock_model(image_url, aws_cfg)
                else:
                    text = _invoke_real_model(prompt)
                try:
                    parsed = _extract_json_dict(text)
                    _validate_required_keys(parsed)
                    parsed.update(model_ocr_meta)
                    return parsed, model_ocr_source, model_aws_mode_used
                except (json.JSONDecodeError, ValueError):
                    if attempt == 1:
                        raise

        try:
            data, ocr_source, aws_mode_used = await asyncio.to_thread(_invoke_model)
        except Exception as exc:
            return _response(False, {}, f"Model call failed: {exc}", False, "none", bool(aws_cfg.get("aws_enabled")))

        if not isinstance(data, dict):
            return _response(False, {}, "Model response is not a valid JSON object", False, ocr_source, aws_mode_used)

        return _response(True, data, None, False, ocr_source, aws_mode_used)
    except (json.JSONDecodeError, ValueError) as exc:
        fallback = {
            "damage_confidence": 0.0,
            "damage_zones": [],
            "severity": "minor",
            "explanation": "Fallback response due to invalid model JSON output.",
        }
        return _response(True, fallback, f"JSON parsing failed: {exc}", True, "none", bool(aws_cfg.get("aws_enabled")))
    except Exception as exc:
        return _response(False, {}, str(exc), False, "none", bool(aws_cfg.get("aws_enabled")))
if __name__ == "__main__":
    import asyncio

    test_input = {
        "image_url": r"C:\Srivalli\Akhira\dataset\hospital.png"
    }

    result = asyncio.run(run(test_input))
    print(result)