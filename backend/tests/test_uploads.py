import io
from unittest.mock import patch
from datetime import date
from app.schemas import ExtractedInvoice, ExtractedLineItem


@patch("app.routers.uploads.process_document")
def test_upload_ocr_success(mock_process_doc, client):
    """Test successful image upload, mock document processing, and DB persistence."""
    mock_process_doc.return_value = ExtractedInvoice(
        vendor_name="Test Store",
        invoice_number="INV-999",
        invoice_date=date(2026, 8, 20),
        currency="USD",
        total_amount=25.00,
        items=[
            ExtractedLineItem(
                description="Test Item",
                quantity=1.0,
                unit_price=25.00,
                total_price=25.00
            )
        ]
    )

    fake_image = io.BytesIO(b"fake image bytes")
    files = {"file": ("test_receipt.png", fake_image, "image/png")}

    response = client.post("/uploads/ocr", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["vendor_name"] == "Test Store"
    assert data["total_amount"] == 25.00
    assert len(data["items"]) == 1
    assert data["items"][0]["description"] == "Test Item"
    assert "id" in data


def test_upload_ocr_invalid_file_type(client):
    """Test rejection of non-allowed file types (e.g. text files)."""
    fake_file = io.BytesIO(b"some plain text content")
    files = {"file": ("notes.txt", fake_file, "text/plain")}

    response = client.post("/uploads/ocr", files=files)

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]