import uuid
from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import ForeignKey, Numeric, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    vendor_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    invoice_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    items: Mapped[List["LineItem"]] = relationship(
        "LineItem", back_populates="invoice", cascade="all, delete-orphan"
    )


class LineItem(Base):
    __tablename__ = "line_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(10, 3), default=1.0)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")
    taxes: Mapped[List["Tax"]] = relationship(
        "Tax", back_populates="line_item", cascade="all, delete-orphan"
    )


class Tax(Base):
    __tablename__ = "taxes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    line_item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("line_items.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "VAT", "Sales Tax"
    rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)  # e.g., 0.1300 for 13%
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    line_item: Mapped["LineItem"] = relationship("LineItem", back_populates="taxes")