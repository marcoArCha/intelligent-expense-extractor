from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models import Invoice, LineItem, Tax
from app.schemas import InvoiceResponse, InvoiceCreate

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/", response_model=List[InvoiceResponse], status_code=status.HTTP_200_OK)
def get_invoices(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    vendor_name: Optional[str] = Query(None, description="Filter by vendor name (case-insensitive substring)"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Retrieve invoices with support for pagination and filtering."""
    query = select(Invoice)

    if vendor_name:
        query = query.where(Invoice.vendor_name.ilike(f"%{vendor_name}%"))

    if start_date:
        query = query.where(Invoice.invoice_date >= start_date)

    if end_date:
        query = query.where(Invoice.invoice_date <= end_date)

    query = query.order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit)

    results = db.scalars(query).all()
    return results


@router.get("/{invoice_id}", response_model=InvoiceResponse, status_code=status.HTTP_200_OK)
def get_invoice_by_id(invoice_id: str, db: Session = Depends(get_db)):
    """Retrieve a single invoice by its ID."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )
    return invoice


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(invoice_in: InvoiceCreate, db: Session = Depends(get_db)):
    """Create a new invoice directly including items and taxes."""
    db_invoice = Invoice(
        vendor_name=invoice_in.vendor_name,
        invoice_number=invoice_in.invoice_number,
        invoice_date=invoice_in.invoice_date,
        currency=invoice_in.currency,
        total_amount=invoice_in.total_amount,
    )

    if getattr(invoice_in, "items", None):
        line_items = []
        for item in invoice_in.items:
            # Safely handle taxes attached to the line item
            item_taxes = (
                [Tax(**tax.model_dump()) for tax in item.taxes]
                if getattr(item, "taxes", None)
                else []
            )
            item_data = item.model_dump(exclude={"taxes"})
            line_item = LineItem(**item_data, taxes=item_taxes)
            line_items.append(line_item)

        db_invoice.items = line_items

    # Check top-level taxes safely without throwing AttributeError
    if getattr(invoice_in, "taxes", None):
        db_invoice.taxes = [
            Tax(**tax.model_dump()) for tax in invoice_in.taxes
        ]

    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: str, db: Session = Depends(get_db)):
    """Delete an invoice by its ID."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found",
        )
    db.delete(invoice)
    db.commit()
    return None