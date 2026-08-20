import os
from PIL import Image
import pytesseract
from pypdf import PdfReader
import instructor
from openai import OpenAI
from dotenv import load_dotenv

from app.schemas import ExtractedInvoice

load_dotenv()

client = instructor.from_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))


def extract_text_from_image(file_path: str) -> str:
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)


def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text


def parse_receipt_text_with_llm(text: str) -> ExtractedInvoice:
    system_prompt = (
        "You are an expert accounting OCR parser. Your job is to extract receipt and invoice data "
        "from raw OCR text and structure it cleanly."
    )

    extracted_invoice: ExtractedInvoice = client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=ExtractedInvoice,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract all invoice details from this OCR output:\n\n{text}"}
        ],
        temperature=0.0
    )
    return extracted_invoice


def process_document(file_path: str, content_type: str) -> ExtractedInvoice:
    if "pdf" in content_type.lower():
        raw_text = extract_text_from_pdf(file_path)
    else:
        raw_text = extract_text_from_image(file_path)
        
    return parse_receipt_text_with_llm(raw_text)