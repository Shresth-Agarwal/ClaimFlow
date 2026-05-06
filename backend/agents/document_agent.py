"""
ClaimFlow Document Processing Agent
==================================
Handles comprehensive document processing including PDFs, images, and scanned documents.

Capabilities:
- PDF text extraction and OCR
- Multi-page document processing
- Image preprocessing and enhancement
- AWS Textract integration for complex documents
- Document classification and validation
- Structured data extraction from various document types

Supported Formats:
- PDF (text-based and scanned)
- Images: JPG, PNG, TIFF, BMP, WEBP
- Multi-page TIFF files
- Scanned documents with poor quality
"""

import asyncio
import base64
import json
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

# PDF and image processing
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logging.warning("PyMuPDF not available - PDF text extraction will be limited")

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import cv2
    import numpy as np
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False
    logging.warning("PIL/OpenCV not available - image preprocessing disabled")

logger = logging.getLogger("claimflow.document_agent")

# Document type patterns for classification
DOCUMENT_PATTERNS = {
    "hospital_bill": [
        "hospital", "medical center", "clinic", "patient", "uhid", "bill", "invoice",
        "discharge", "treatment", "consultation", "medicine", "pharmacy"
    ],
    "prescription": [
        "prescription", "rx", "doctor", "tablet", "capsule", "syrup", "dosage",
        "medicine", "drug", "pharmacy", "prescribed"
    ],
    "lab_report": [
        "laboratory", "lab report", "test result", "pathology", "blood test",
        "urine test", "x-ray", "scan", "investigation"
    ],
    "discharge_summary": [
        "discharge summary", "discharge", "admission", "diagnosis", "treatment summary",
        "medical record", "case summary"
    ],
    "repair_invoice": [
        "workshop", "garage", "repair", "service", "spare parts", "labour",
        "mechanic", "automobile", "vehicle service"
    ],
    "rc_document": [
        "registration certificate", "vehicle registration", "rc", "chassis number",
        "engine number", "registration number", "vehicle details"
    ],
    "driving_license": [
        "driving licence", "driving license", "dl", "license number", "driver",
        "transport authority", "license to drive"
    ],
    "fir_document": [
        "fir", "first information report", "police station", "complaint",
        "case number", "police report", "incident report"
    ],
    "property_document": [
        "property", "ownership", "sale deed", "property card", "khata",
        "survey number", "property tax", "municipal"
    ],
    "insurance_policy": [
        "insurance policy", "policy document", "coverage", "premium",
        "policy number", "insured", "beneficiary"
    ]
}


def _get_aws_clients():
    """Get AWS clients for document processing."""
    try:
        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        
        return {
            "textract": session.client("textract"),
            "s3": session.client("s3"),
            "comprehend": session.client("comprehend")
        }
    except Exception as e:
        logger.error(f"Failed to initialize AWS clients: {e}")
        return None


def _enhance_image_quality(image_path: str) -> str:
    """Enhance image quality for better OCR results."""
    if not IMAGE_PROCESSING_AVAILABLE:
        return image_path
    
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return image_path
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Apply sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Save enhanced image
        enhanced_path = image_path.rsplit('.', 1)[0] + '_enhanced.png'
        cv2.imwrite(enhanced_path, sharpened)
        
        logger.info(f"Enhanced image quality: {image_path} -> {enhanced_path}")
        return enhanced_path
        
    except Exception as e:
        logger.warning(f"Image enhancement failed: {e}")
        return image_path


def _extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """Extract text from PDF using PyMuPDF."""
    if not PYMUPDF_AVAILABLE:
        return {"text": "", "pages": 0, "method": "unavailable"}
    
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        page_texts = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            page_texts.append(page_text)
            full_text += page_text + "\n"
        
        doc.close()
        
        return {
            "text": full_text.strip(),
            "pages": len(page_texts),
            "page_texts": page_texts,
            "method": "pymupdf_text"
        }
        
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        return {"text": "", "pages": 0, "method": "failed"}


def _convert_pdf_to_images(pdf_path: str) -> List[str]:
    """Convert PDF pages to images for OCR processing."""
    if not PYMUPDF_AVAILABLE:
        return []
    
    try:
        doc = fitz.open(pdf_path)
        image_paths = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Render page as image (higher DPI for better OCR)
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            
            # Save as PNG
            image_path = f"/tmp/pdf_page_{uuid.uuid4().hex[:8]}_{page_num}.png"
            pix.save(image_path)
            image_paths.append(image_path)
        
        doc.close()
        logger.info(f"Converted PDF to {len(image_paths)} images")
        return image_paths
        
    except Exception as e:
        logger.error(f"PDF to image conversion failed: {e}")
        return []


def _upload_to_s3(file_path: str, s3_client, bucket: str) -> str:
    """Upload document to S3 and return URI."""
    key = f"document-processing/{uuid.uuid4().hex}/{Path(file_path).name}"
    
    try:
        s3_client.upload_file(file_path, bucket, key)
        s3_uri = f"s3://{bucket}/{key}"
        logger.info(f"Uploaded document to S3: {s3_uri}")
        return s3_uri
    except ClientError as e:
        logger.error(f"S3 upload failed: {e}")
        raise


def _process_with_textract(s3_uri: str, textract_client) -> Dict[str, Any]:
    """Process document with AWS Textract."""
    try:
        parsed_uri = urlparse(s3_uri)
        bucket = parsed_uri.netloc
        key = parsed_uri.path.lstrip("/")
        
        # Use analyze_document for forms and tables
        response = textract_client.analyze_document(
            Document={
                "S3Object": {
                    "Bucket": bucket,
                    "Name": key
                }
            },
            FeatureTypes=["FORMS", "TABLES"]
        )
        
        # Extract text, forms, and tables
        blocks = response.get("Blocks", [])
        
        # Extract raw text
        text_blocks = [
            block["Text"] for block in blocks 
            if block["BlockType"] == "LINE" and "Text" in block
        ]
        raw_text = "\n".join(text_blocks)
        
        # Extract key-value pairs (forms)
        forms = _extract_textract_forms(blocks)
        
        # Extract tables
        tables = _extract_textract_tables(blocks)
        
        return {
            "text": raw_text,
            "forms": forms,
            "tables": tables,
            "method": "textract",
            "confidence": _calculate_textract_confidence(blocks)
        }
        
    except ClientError as e:
        logger.error(f"Textract processing failed: {e}")
        raise


def _extract_textract_forms(blocks: List[Dict]) -> List[Dict]:
    """Extract form key-value pairs from Textract blocks."""
    forms = []
    block_map = {block["Id"]: block for block in blocks}
    
    for block in blocks:
        if block["BlockType"] == "KEY_VALUE_SET" and "KEY" in block.get("EntityTypes", []):
            key_text = ""
            value_text = ""
            
            # Get key text
            for relationship in block.get("Relationships", []):
                if relationship["Type"] == "CHILD":
                    for child_id in relationship["Ids"]:
                        child = block_map.get(child_id, {})
                        if child.get("BlockType") == "WORD":
                            key_text += child.get("Text", "") + " "
            
            # Get value text
            for relationship in block.get("Relationships", []):
                if relationship["Type"] == "VALUE":
                    for value_id in relationship["Ids"]:
                        value_block = block_map.get(value_id, {})
                        for value_rel in value_block.get("Relationships", []):
                            if value_rel["Type"] == "CHILD":
                                for child_id in value_rel["Ids"]:
                                    child = block_map.get(child_id, {})
                                    if child.get("BlockType") == "WORD":
                                        value_text += child.get("Text", "") + " "
            
            if key_text.strip():
                forms.append({
                    "key": key_text.strip(),
                    "value": value_text.strip(),
                    "confidence": block.get("Confidence", 0)
                })
    
    return forms


def _extract_textract_tables(blocks: List[Dict]) -> List[List[List[str]]]:
    """Extract tables from Textract blocks."""
    tables = []
    block_map = {block["Id"]: block for block in blocks}
    
    for block in blocks:
        if block["BlockType"] == "TABLE":
            table_data = {}
            
            # Get table cells
            for relationship in block.get("Relationships", []):
                if relationship["Type"] == "CHILD":
                    for cell_id in relationship["Ids"]:
                        cell = block_map.get(cell_id, {})
                        if cell.get("BlockType") == "CELL":
                            row_idx = cell.get("RowIndex", 1) - 1
                            col_idx = cell.get("ColumnIndex", 1) - 1
                            
                            # Get cell text
                            cell_text = ""
                            for cell_rel in cell.get("Relationships", []):
                                if cell_rel["Type"] == "CHILD":
                                    for word_id in cell_rel["Ids"]:
                                        word = block_map.get(word_id, {})
                                        if word.get("BlockType") == "WORD":
                                            cell_text += word.get("Text", "") + " "
                            
                            if row_idx not in table_data:
                                table_data[row_idx] = {}
                            table_data[row_idx][col_idx] = cell_text.strip()
            
            # Convert to 2D array
            if table_data:
                max_row = max(table_data.keys())
                max_col = max(max(row.keys()) for row in table_data.values())
                
                table_array = []
                for row_idx in range(max_row + 1):
                    row = []
                    for col_idx in range(max_col + 1):
                        cell_value = table_data.get(row_idx, {}).get(col_idx, "")
                        row.append(cell_value)
                    table_array.append(row)
                
                tables.append(table_array)
    
    return tables


def _calculate_textract_confidence(blocks: List[Dict]) -> float:
    """Calculate average confidence from Textract blocks."""
    confidences = [
        block.get("Confidence", 0) for block in blocks 
        if "Confidence" in block
    ]
    return sum(confidences) / len(confidences) if confidences else 0.0


def _classify_document_type(text: str) -> str:
    """Classify document type based on content."""
    text_lower = text.lower()
    
    # Count keyword matches for each document type
    scores = {}
    for doc_type, keywords in DOCUMENT_PATTERNS.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            scores[doc_type] = score
    
    if not scores:
        return "unknown_document"
    
    # Return the type with highest score
    return max(scores.items(), key=lambda x: x[1])[0]


def _extract_structured_data(text: str, document_type: str) -> Dict[str, Any]:
    """Extract structured data based on document type."""
    import re
    
    structured_data = {"document_type": document_type}
    text_lower = text.lower()
    
    # Common patterns
    # Amounts
    amount_patterns = [
        r'(?:total|amount|bill|sum|rs\.?|₹)\s*:?\s*([0-9,]+(?:\.[0-9]{2})?)',
        r'([0-9,]+(?:\.[0-9]{2})?)\s*(?:rs|rupees|₹)'
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                amount_str = match.group(1).replace(",", "")
                structured_data["amount"] = float(amount_str)
                break
            except ValueError:
                pass
    
    # Dates
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            structured_data["date"] = match.group(1)
            break
    
    # Document-specific extraction
    if document_type == "hospital_bill":
        # Patient name
        name_match = re.search(r'patient\s*name\s*:?\s*([a-z\s]+)', text_lower)
        if name_match:
            structured_data["patient_name"] = name_match.group(1).strip().title()
        
        # UHID
        uhid_match = re.search(r'uhid\s*:?\s*([a-z0-9]+)', text_lower)
        if uhid_match:
            structured_data["uhid"] = uhid_match.group(1).upper()
        
        # Hospital name (usually in first few lines)
        lines = text.split('\n')[:5]
        for line in lines:
            if 'hospital' in line.lower() or 'medical' in line.lower():
                structured_data["hospital_name"] = line.strip()
                break
    
    elif document_type == "repair_invoice":
        # Vehicle details
        vehicle_match = re.search(r'vehicle\s*(?:no|number)\s*:?\s*([a-z0-9\s]+)', text_lower)
        if vehicle_match:
            structured_data["vehicle_number"] = vehicle_match.group(1).strip().upper()
        
        # Workshop name
        lines = text.split('\n')[:3]
        for line in lines:
            if any(word in line.lower() for word in ['workshop', 'garage', 'service']):
                structured_data["workshop_name"] = line.strip()
                break
    
    elif document_type == "fir_document":
        # FIR number
        fir_match = re.search(r'fir\s*(?:no|number)\s*:?\s*([0-9/\-]+)', text_lower)
        if fir_match:
            structured_data["fir_number"] = fir_match.group(1)
        
        # Police station
        station_match = re.search(r'police\s*station\s*:?\s*([a-z\s]+)', text_lower)
        if station_match:
            structured_data["police_station"] = station_match.group(1).strip().title()
    
    return structured_data


async def process_document(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main document processing function.
    
    Args:
        input_data: {
            "file_path": str,           # Local file path
            "file_base64": str,         # Base64 encoded file (alternative)
            "s3_uri": str,              # S3 URI (alternative)
            "file_type": str,           # Optional: "pdf", "image", "auto"
            "use_textract": bool,       # Whether to use AWS Textract
            "enhance_images": bool,     # Whether to enhance image quality
            "extract_tables": bool      # Whether to extract table data
        }
    
    Returns:
        {
            "success": bool,
            "text": str,
            "document_type": str,
            "structured_data": dict,
            "forms": list,              # Key-value pairs from forms
            "tables": list,             # Extracted tables
            "confidence": float,
            "pages_processed": int,
            "processing_method": str,
            "processing_time": float,
            "error": str | None
        }
    """
    start_time = time.time()
    cleanup_files = []
    
    try:
        # Determine file path
        file_path = None
        
        if "file_path" in input_data:
            file_path = input_data["file_path"]
            
        elif "file_base64" in input_data:
            # Decode base64 file
            file_data = base64.b64decode(input_data["file_base64"])
            file_extension = input_data.get("file_extension", ".pdf")
            file_path = f"/tmp/doc_{uuid.uuid4().hex[:8]}{file_extension}"
            with open(file_path, "wb") as f:
                f.write(file_data)
            cleanup_files.append(file_path)
            
        elif "s3_uri" in input_data:
            # Download from S3
            aws_clients = _get_aws_clients()
            if not aws_clients:
                raise RuntimeError("AWS clients not available")
            
            s3_uri = input_data["s3_uri"]
            parsed = urlparse(s3_uri)
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
            
            file_extension = Path(key).suffix or ".pdf"
            file_path = f"/tmp/doc_{uuid.uuid4().hex[:8]}{file_extension}"
            aws_clients["s3"].download_file(bucket, key, file_path)
            cleanup_files.append(file_path)
            
        else:
            raise ValueError("No file input provided")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type
        file_extension = Path(file_path).suffix.lower()
        file_type = input_data.get("file_type", "auto")
        
        if file_type == "auto":
            if file_extension == ".pdf":
                file_type = "pdf"
            elif file_extension in [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"]:
                file_type = "image"
            else:
                file_type = "unknown"
        
        # Initialize result
        result = {
            "text": "",
            "forms": [],
            "tables": [],
            "confidence": 0.0,
            "pages_processed": 0,
            "processing_method": "none"
        }
        
        # Process based on file type and preferences
        use_textract = input_data.get("use_textract", True) and os.getenv("CLAIMFLOW_AWS_ENABLED", "false").lower() == "true"
        
        if file_type == "pdf":
            # Try text extraction first
            pdf_result = _extract_text_from_pdf(file_path)
            
            if pdf_result["text"].strip() and len(pdf_result["text"]) > 50:
                # PDF has extractable text
                result.update({
                    "text": pdf_result["text"],
                    "pages_processed": pdf_result["pages"],
                    "processing_method": "pdf_text_extraction",
                    "confidence": 0.95
                })
            else:
                # PDF is scanned - convert to images and OCR
                if use_textract:
                    # Upload to S3 and use Textract
                    aws_clients = _get_aws_clients()
                    s3_bucket = os.getenv("CLAIMFLOW_S3_BUCKET")
                    
                    if aws_clients and s3_bucket:
                        s3_uri = _upload_to_s3(file_path, aws_clients["s3"], s3_bucket)
                        textract_result = _process_with_textract(s3_uri, aws_clients["textract"])
                        result.update(textract_result)
                        result["pages_processed"] = pdf_result["pages"]
                else:
                    # Convert to images and use local OCR
                    image_paths = _convert_pdf_to_images(file_path)
                    cleanup_files.extend(image_paths)
                    
                    if image_paths:
                        # Process first few pages (limit for performance)
                        pages_to_process = image_paths[:5]  # Max 5 pages
                        
                        all_text = []
                        for img_path in pages_to_process:
                            # Use existing vision agent OCR
                            from backend.agents.vision_agent import _extract_text_from_image
                            page_text = _extract_text_from_image(img_path)
                            if page_text:
                                all_text.append(page_text)
                        
                        result.update({
                            "text": "\n\n".join(all_text),
                            "pages_processed": len(pages_to_process),
                            "processing_method": "pdf_to_image_ocr",
                            "confidence": 0.7
                        })
        
        elif file_type == "image":
            # Enhance image quality if requested
            processed_path = file_path
            if input_data.get("enhance_images", True):
                enhanced_path = _enhance_image_quality(file_path)
                if enhanced_path != file_path:
                    processed_path = enhanced_path
                    cleanup_files.append(enhanced_path)
            
            if use_textract:
                # Use AWS Textract
                aws_clients = _get_aws_clients()
                s3_bucket = os.getenv("CLAIMFLOW_S3_BUCKET")
                
                if aws_clients and s3_bucket:
                    s3_uri = _upload_to_s3(processed_path, aws_clients["s3"], s3_bucket)
                    textract_result = _process_with_textract(s3_uri, aws_clients["textract"])
                    result.update(textract_result)
                    result["pages_processed"] = 1
            else:
                # Use local OCR
                from backend.agents.vision_agent import _extract_text_from_image
                text = _extract_text_from_image(processed_path)
                result.update({
                    "text": text,
                    "pages_processed": 1,
                    "processing_method": "local_ocr",
                    "confidence": 0.8 if text else 0.0
                })
        
        # Classify document and extract structured data
        document_type = _classify_document_type(result["text"])
        structured_data = _extract_structured_data(result["text"], document_type)
        
        # Cleanup temporary files
        for temp_file in cleanup_files:
            try:
                os.remove(temp_file)
            except OSError:
                pass
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Document processing completed: {file_type}, "
            f"type={document_type}, method={result['processing_method']}, "
            f"confidence={result['confidence']:.2f}, time={processing_time:.2f}s"
        )
        
        return {
            "success": True,
            "text": result["text"],
            "document_type": document_type,
            "structured_data": structured_data,
            "forms": result.get("forms", []),
            "tables": result.get("tables", []),
            "confidence": result["confidence"],
            "pages_processed": result["pages_processed"],
            "processing_method": result["processing_method"],
            "processing_time": processing_time,
            "error": None
        }
        
    except Exception as e:
        # Cleanup on error
        for temp_file in cleanup_files:
            try:
                os.remove(temp_file)
            except OSError:
                pass
        
        processing_time = time.time() - start_time
        logger.error(f"Document processing failed: {e}", exc_info=True)
        
        return {
            "success": False,
            "text": "",
            "document_type": "unknown",
            "structured_data": {},
            "forms": [],
            "tables": [],
            "confidence": 0.0,
            "pages_processed": 0,
            "processing_method": "failed",
            "processing_time": processing_time,
            "error": str(e)
        }


# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test_document_processing():
        # Test with a sample document
        test_input = {
            "file_path": "test.pdf",  # Replace with actual file
            "use_textract": True,
            "enhance_images": True,
            "extract_tables": True
        }
        
        result = await process_document(test_input)
        print(json.dumps(result, indent=2, default=str))
    
    # asyncio.run(test_document_processing())
    print("Document agent loaded. Use process_document() function.")