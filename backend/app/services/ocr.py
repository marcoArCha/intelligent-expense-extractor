import os
from typing import Dict, Any, Optional
from PIL import Image
import pytesseract
from pypdf import PdfReader
import instructor
from openai import OpenAI

from app import schemas

# Initialize Instructor-patched OpenAI client
client = instructor.from_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))


def extract_text_from_image(file_path: str) -> str:
    """Extract raw text from JPEG/PNG images using Tesseract OCR."""
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF pages."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text


def parse_receipt_text_with_llm(raw_text: str) -> schemas.InvoiceCreate:
    """
    Pass raw OCR text to OpenAI via Instructor to reliably extract
    vendor details, dates, totals, line items, and tax breakdown.
    """
    prompt = f"""
    You are an expert accounting AI. Analyze the following OCR text extracted from an invoice or receipt.
    Extract all information into the specified structured JSON schema.

    Rules:
    1. Identify the true business/vendor name, ignoring generic titles like "INVOICE" or "FACTURA".
    2. Extract all line items (description, quantity, unit price, total price).
    3. Infer currency standard ISO codes (e.g., USD, CRC, EUR).
    4. Format dates strictly as YYYY-MM-DD.
    5. If a field cannot be determined, set it to null or sensible default.

    Raw OCR Text:
    ---
    {raw_text}
    ---
    """

    # Instructor forces OpenAI to return a validated Pydantic model
    structured_invoice = client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=schemas.InvoiceCreate,
        messages=[
            {"role": "system", "content": "You extract structured data from invoice OCR text."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
    )

    return structured_invoice


def process_document(file_path: str, content_type: str) -> schemas.InvoiceCreate:
    """Unified handler that extracts OCR text and parses it via LLM into an InvoiceCreate schema."""
    if "pdf" in content_type.lower():
        raw_text = extract_text_from_pdf(file_path)
    else:
        raw_text = extract_text_from_image(file_path)

    parsed_invoice = parse_receipt_text_with_llm(raw_text)
    return parsed_invoice