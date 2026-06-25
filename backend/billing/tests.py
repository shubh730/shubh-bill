from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Product


class InvoiceApiTests(TestCase):
    def test_invoice_creation_updates_stock_and_totals(self):
        product = Product.objects.create(name="Rice", sku="RICE-1", price=Decimal("100.00"), tax_rate=Decimal("5.00"), stock=10)
        client = APIClient()
        response = client.post(
            "/api/invoices/",
            {
                "customer_name": "Walk-in",
                "items": [{"product_id": product.id, "quantity": 2}],
                "paid_amount": "100.00",
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        product.refresh_from_db()
        self.assertEqual(product.stock, 8)
        self.assertEqual(response.data["subtotal"], "200.00")
        self.assertEqual(response.data["tax_total"], "10.00")
        self.assertEqual(response.data["total"], "210.00")
        self.assertEqual(response.data["due_amount"], "110.00")

    def test_part_payment_can_be_added_later(self):
        product = Product.objects.create(name="Oil", sku="OIL-1", price=Decimal("200.00"), tax_rate=Decimal("0.00"), stock=5)
        client = APIClient()
        invoice_response = client.post(
            "/api/invoices/",
            {
                "customer_name": "Amit",
                "items": [{"product_id": product.id, "quantity": 1}],
                "paid_amount": "80.00",
                "payment_method": "upi",
                "payment_reference": "first",
            },
            format="json",
        )
        self.assertEqual(invoice_response.status_code, 201)
        invoice_id = invoice_response.data["id"]
        self.assertEqual(invoice_response.data["status"], "partial")
        self.assertEqual(invoice_response.data["due_amount"], "120.00")

        payment_response = client.post(
            "/api/payments/",
            {"invoice": invoice_id, "amount": "120.00", "method": "cash", "reference": "final"},
            format="json",
        )
        self.assertEqual(payment_response.status_code, 201)

        detail_response = client.get(f"/api/invoices/{invoice_id}/")
        self.assertEqual(detail_response.data["status"], "paid")
        self.assertEqual(detail_response.data["paid_amount"], "200.00")
        self.assertEqual(detail_response.data["due_amount"], "0.00")
        self.assertEqual(len(detail_response.data["payments"]), 2)

    def test_payment_cannot_exceed_invoice_total(self):
        product = Product.objects.create(name="Sugar", sku="SUGAR-1", price=Decimal("50.00"), tax_rate=Decimal("0.00"), stock=5)
        client = APIClient()
        invoice_response = client.post(
            "/api/invoices/",
            {"customer_name": "Walk-in", "items": [{"product_id": product.id, "quantity": 1}], "paid_amount": "0.00"},
            format="json",
        )
        response = client.post(
            "/api/payments/",
            {"invoice": invoice_response.data["id"], "amount": "60.00", "method": "cash"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
