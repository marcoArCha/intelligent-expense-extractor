from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"]
)


@router.post("/", response_model=schemas.InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(invoice_in: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    """
    Create a new invoice along with its line items and taxes in a single transaction.
    """
    # 1. Instantiate Invoice model
    db_invoice = models.Invoice(
        vendor_name=invoice_in.vendor_name,
        invoice_number=invoice_in.invoice_number,
        invoice_date=invoice_in.invoice_date,
        currency=invoice_in.currency,
        total_amount=invoice_in.total_amount,
    )

    # 2. Build nested LineItems and Taxes
    for item_in in invoice_in.items:
        db_item = models.LineItem(
            description=item_in.description,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            total_price=item_in.total_price,
        )
        for tax_in in item_in.taxes:
            db_tax = models.Tax(
                name=tax_in.name,
                rate=tax_in.rate,
                amount=tax_in.amount,
            )
            db_item.taxes.append(db_tax)

        db_invoice.items.append(db_item)

    # 3. Save to database
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    return db_invoice


@router.get("/", response_model=List[schemas.InvoiceResponse])
def list_invoices(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """
    Retrieve a paginated list of all invoices.
    """
    invoices = db.query(models.Invoice).offset(skip).limit(limit).all()
    return invoices


@router.get("/{invoice_id}", response_model=schemas.InvoiceResponse)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a single invoice by ID with its nested line items and taxes.
    """
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found"
        )
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: str, db: Session = Depends(get_db)):
    """
    Delete an invoice by ID. Cascade deletion automatically cleans up associated line items and taxes.
    """
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID '{invoice_id}' not found"
        )
    db.delete(invoice)
    db.commit()
    return None