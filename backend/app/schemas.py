from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# --- Tax Schemas ---

class TaxBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "IVA 1%"})
    rate: float = Field(..., ge=0.0, le=1.0, json_schema_extra={"example": 0.01})
    amount: float = Field(..., ge=0.0, json_schema_extra={"example": 19.00})


class TaxCreate(TaxBase):
    pass


class TaxResponse(TaxBase):
    id: str
    line_item_id: str

    model_config = ConfigDict(from_attributes=True)


# --- Line Item Schemas ---

class LineItemBase(BaseModel):
    description: str = Field(..., json_schema_extra={"example": "Leche Semidescremada 1L"})
    quantity: float = Field(default=1.0, gt=0, json_schema_extra={"example": 2.0})
    unit_price: float = Field(..., ge=0.0, json_schema_extra={"example": 950.00})
    total_price: float = Field(..., ge=0.0, json_schema_extra={"example": 1900.00})


class LineItemCreate(LineItemBase):
    taxes: List[TaxCreate] = []


class LineItemResponse(LineItemBase):
    id: str
    invoice_id: str
    taxes: List[TaxResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Invoice Schemas ---

class InvoiceBase(BaseModel):
    vendor_name: str = Field(..., json_schema_extra={"example": "Supermercado Kíki"})
    invoice_number: Optional[str] = Field(default=None, json_schema_extra={"example": "INV-2026-001"})
    invoice_date: Optional[date] = Field(default=None, json_schema_extra={"example": "2026-08-19"})
    currency: str = Field(default="USD", min_length=3, max_length=3, json_schema_extra={"example": "CRC"})
    total_amount: float = Field(..., ge=0.0, json_schema_extra={"example": 2850.00})


class InvoiceCreate(InvoiceBase):
    items: List[LineItemCreate] = []


class InvoiceResponse(InvoiceBase):
    id: str
    created_at: datetime
    items: List[LineItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Extracted Schemas for OCR / LLM Service ---

class ExtractedTax(BaseModel):
    tax_name: str = Field(default="Tax", description="Tax name")
    tax_rate: Optional[float] = Field(default=None, description="Tax rate percentage")
    amount: float = Field(description="Tax amount")


class ExtractedLineItem(BaseModel):
    description: str = Field(description="Description of item/service")
    quantity: float = Field(default=1.0, description="Quantity")
    unit_price: float = Field(default=0.0, description="Unit price")
    total_price: float = Field(description="Total price for line item")
    taxes: List[ExtractedTax] = Field(default_factory=list, description="Taxes applicable to this item")


class ExtractedInvoice(BaseModel):
    vendor_name: str = Field(description="Vendor name")
    invoice_number: Optional[str] = Field(default=None, description="Invoice number")
    invoice_date: Optional[date] = Field(default=None, description="Invoice date")
    currency: str = Field(default="USD", description="Currency code")
    total_amount: float = Field(description="Total amount")
    items: List[ExtractedLineItem] = Field(default_factory=list)
    taxes: List[ExtractedTax] = Field(default_factory=list)