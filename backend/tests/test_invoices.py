import pytest
from fastapi import status


@pytest.fixture
def sample_invoice_payload():
    """Payload de ejemplo para crear una factura con ítems e impuestos."""
    return {
        "vendor_name": "Supermercado Kíki",
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-08-20",
        "currency": "CRC",
        "total_amount": 2850.00,
        "items": [
            {
                "description": "Leche Semidescremada 1L",
                "quantity": 2.0,
                "unit_price": 950.00,
                "total_price": 1900.00,
                "taxes": [
                    {
                        "name": "IVA 1%",
                        "rate": 0.01,
                        "amount": 19.00
                    }
                ]
            }
        ]
    }


def test_create_invoice(client, sample_invoice_payload):
    """Verifica la creación exitosa de una factura vía POST."""
    response = client.post("/invoices/", json=sample_invoice_payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["vendor_name"] == "Supermercado Kíki"
    assert data["invoice_number"] == "INV-2026-001"
    assert len(data["items"]) == 1
    assert len(data["items"][0]["taxes"]) == 1
    assert "id" in data


def test_get_invoices_empty(client):
    """Verifica que GET /invoices devuelva una lista vacía cuando no hay registros."""
    response = client.get("/invoices/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_get_invoices_list(client, sample_invoice_payload):
    """Verifica que GET /invoices devuelva el listado con facturas agregadas."""
    # Crear factura
    create_resp = client.post("/invoices/", json=sample_invoice_payload)
    assert create_resp.status_code == status.HTTP_201_CREATED

    response = client.get("/invoices/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["vendor_name"] == "Supermercado Kíki"


def test_get_invoice_by_id_success(client, sample_invoice_payload):
    """Verifica obtener una factura específica por su ID."""
    create_resp = client.post("/invoices/", json=sample_invoice_payload)
    invoice_id = create_resp.json()["id"]

    response = client.get(f"/invoices/{invoice_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == invoice_id
    assert data["vendor_name"] == "Supermercado Kíki"


def test_get_invoice_by_id_not_found(client):
    """Verifica que GET /invoices/{id} devuelva 404 para un ID inexistente."""
    fake_id = "non-existent-uuid"
    response = client.get(f"/invoices/{fake_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Invoice with ID '{fake_id}' not found"


def test_delete_invoice_success(client, sample_invoice_payload):
    """Verifica la eliminación correcta de una factura."""
    create_resp = client.post("/invoices/", json=sample_invoice_payload)
    invoice_id = create_resp.json()["id"]

    # Eliminar
    delete_resp = client.delete(f"/invoices/{invoice_id}")
    assert delete_resp.status_code == status.HTTP_204_NO_CONTENT

    # Confirmar que ya no existe
    get_resp = client.get(f"/invoices/{invoice_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


def test_delete_invoice_not_found(client):
    """Verifica que DELETE /invoices/{id} devuelva 404 si el ID no existe."""
    fake_id = "non-existent-uuid"
    response = client.delete(f"/invoices/{fake_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Invoice with ID '{fake_id}' not found"