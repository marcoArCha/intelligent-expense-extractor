import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.services.ocr import process_document

router = APIRouter(
    prefix="/uploads",
    tags=["Document Upload & OCR"]
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg", "application/pdf"}


@router.post("/ocr", response_model=schemas.InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def upload_and_process_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'."
        )

    # 1. Save file locally
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    saved_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # 2. Extract structured data via OCR + LLM
    try:
        parsed_data: schemas.ExtractedInvoice = process_document(file_path, file.content_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing OCR document: {str(e)}"
        )

    # 3. Persist Invoice ORM object
    db_invoice = models.Invoice(
        vendor_name=parsed_data.vendor_name,
        invoice_number=parsed_data.invoice_number,
        invoice_date=parsed_data.invoice_date,
        currency=parsed_data.currency,
        total_amount=parsed_data.total_amount,
    )

    # Add nested line items and their corresponding taxes
    for item in parsed_data.items:
        db_item = models.LineItem(
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
        )
        
        # Safely extract item-level taxes if present
        item_taxes = getattr(item, "taxes", [])
        for tax in item_taxes:
            db_tax = models.Tax(
                name=tax.tax_name,
                rate=tax.tax_rate if tax.tax_rate is not None else 0.0,
                amount=tax.amount
            )
            db_item.taxes.append(db_tax)

        db_invoice.items.append(db_item)

    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    return db_invoice