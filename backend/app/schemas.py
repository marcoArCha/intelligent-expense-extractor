from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- Tax Schemas ---
class TaxBase(BaseModel):
    name: str = Field(..., example="VAT")
    rate: float = Field(..., ge=0.0, le=1.0, example=0.13)
    amount: float = Field(..., ge=0.0, example=13.00)


class TaxCreate(TaxBase):
    pass


class TaxResponse(TaxBase):
    id: str
    line_item_id: str

    model_config = ConfigDict(from_attributes=True)


# --- Line Item Schemas ---
class LineItemBase(BaseModel):
    description: str = Field(..., example="Leche Semidescremada 1L")
    quantity: float = Field(default=1.0, gt=0, example=2.0)
    unit_price: float = Field(..., ge=0.0, example=950.00)
    total_price: float = Field(..., ge=0.0, example=1900.00)


class LineItemCreate(LineItemBase):
    taxes: List[TaxCreate] = []


class LineItemResponse(LineItemBase):
    id: str
    invoice_id: str
    taxes: List[TaxResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Invoice Schemas ---
class InvoiceBase(BaseModel):
    vendor_name: str = Field(..., example="Supermercado Kíki")
    invoice_number: Optional[str] = Field(default=None, example="INV-2026-001")
    invoice_date: Optional[date] = Field(default=None, example="2026-08-19")
    currency: str = Field(default="USD", min_length=3, max_length=3, example="CRC")
    total_amount: float = Field(..., ge=0.0, example=2850.00)


class InvoiceCreate(InvoiceBase):
    items: List[LineItemCreate] = []


class InvoiceResponse(InvoiceBase):
    id: str
    created_at: datetime
    items: List[LineItemResponse] = []

    model_config = ConfigDict(from_attributes=True)