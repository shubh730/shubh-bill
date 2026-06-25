from __future__ import annotations

import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from billing.models import Customer, Invoice, Payment, Product, create_invoice_with_stock


class Command(BaseCommand):
    help = "Seed demo products, customers, invoices, sales, and partial payment history."

    def add_arguments(self, parser):
        parser.add_argument("--products", type=int, default=100)
        parser.add_argument("--customers", type=int, default=40)
        parser.add_argument("--invoices", type=int, default=100)
        parser.add_argument("--keep-existing", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(20260615)
        product_count = options["products"]
        customer_count = options["customers"]
        invoice_count = options["invoices"]

        if not options["keep_existing"]:
            self._clear_demo_data()

        products = self._create_products(product_count, rng)
        customers = self._create_customers(customer_count)
        invoices = self._create_invoices(invoice_count, products, customers, rng)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(products)} products, {len(customers)} customers, {len(invoices)} invoices, "
                f"{Payment.objects.filter(reference__startswith='DEMO-').count()} payments."
            )
        )

    def _clear_demo_data(self) -> None:
        demo_invoices = Invoice.objects.filter(notes__startswith="DEMO DATA")
        demo_invoices.delete()
        Product.objects.filter(sku__startswith="DEMO-").delete()
        Customer.objects.filter(phone__startswith="90000").delete()

    def _create_products(self, count: int, rng: random.Random) -> list[Product]:
        names = [
            "Basmati Rice",
            "Wheat Flour",
            "Sugar",
            "Sunflower Oil",
            "Mustard Oil",
            "Toor Dal",
            "Moong Dal",
            "Chana Dal",
            "Tea Pack",
            "Coffee",
            "Milk Powder",
            "Salt",
            "Turmeric",
            "Chilli Powder",
            "Coriander Powder",
            "Cumin Seeds",
            "Soap",
            "Shampoo",
            "Toothpaste",
            "Detergent",
        ]
        units = ["500g", "1kg", "2kg", "5kg", "100ml", "250ml", "500ml", "1L", "Small", "Large"]
        products: list[Product] = []
        for index in range(1, count + 1):
            base = names[(index - 1) % len(names)]
            unit = units[(index - 1) % len(units)]
            price = Decimal(rng.randrange(20, 1200)).quantize(Decimal("0.01"))
            tax_rate = Decimal(rng.choice(["0.00", "5.00", "12.00", "18.00"]))
            products.append(
                Product.objects.create(
                    name=f"{base} {unit} #{index:03d}",
                    sku=f"DEMO-P-{index:03d}",
                    barcode=f"8901000{index:06d}",
                    price=price,
                    tax_rate=tax_rate,
                    stock=rng.randrange(80, 260),
                    is_active=True,
                )
            )
        return products

    def _create_customers(self, count: int) -> list[Customer]:
        first_names = ["Amit", "Priya", "Ravi", "Neha", "Suresh", "Pooja", "Vikram", "Anjali", "Rahul", "Kiran"]
        last_names = ["Sharma", "Patel", "Gupta", "Verma", "Yadav", "Singh", "Jain", "Kumar"]
        customers: list[Customer] = []
        for index in range(1, count + 1):
            customers.append(
                Customer.objects.create(
                    name=f"{first_names[(index - 1) % len(first_names)]} {last_names[(index - 1) % len(last_names)]} {index}",
                    phone=f"90000{index:05d}",
                    address=f"Demo Market Road, Block {((index - 1) % 8) + 1}",
                )
            )
        return customers

    def _create_invoices(
        self,
        count: int,
        products: list[Product],
        customers: list[Customer],
        rng: random.Random,
    ) -> list[Invoice]:
        invoices: list[Invoice] = []
        methods = [Payment.Method.CASH, Payment.Method.UPI, Payment.Method.CARD, Payment.Method.BANK]
        now = timezone.now()

        for index in range(1, count + 1):
            customer = rng.choice(customers + [None])
            item_products = rng.sample(products, rng.randrange(1, 5))
            items = [{"product": product, "quantity": rng.randrange(1, 4)} for product in item_products]
            discount = Decimal(rng.choice(["0.00", "5.00", "10.00", "20.00", "50.00"]))
            invoice = create_invoice_with_stock(
                invoice_data={
                    "customer": customer,
                    "customer_name": customer.name if customer else "Walk-in Customer",
                    "customer_phone": customer.phone if customer else "",
                    "discount": discount,
                    "notes": f"DEMO DATA invoice {index:03d}",
                },
                items_data=items,
            )

            created_at = now - timezone.timedelta(days=rng.randrange(0, 30), hours=rng.randrange(0, 10), minutes=rng.randrange(0, 60))
            invoice.created_at = created_at
            invoice.save(update_fields=["created_at", "updated_at"])

            payment_mode = index % 4
            if payment_mode == 0:
                self._add_payment(invoice, invoice.total, rng.choice(methods), f"DEMO-FULL-{index:03d}", created_at)
            elif payment_mode == 1:
                first = (invoice.total * Decimal("0.50")).quantize(Decimal("0.01"))
                self._add_payment(invoice, first, rng.choice(methods), f"DEMO-PART-1-{index:03d}", created_at)
            elif payment_mode == 2:
                first = (invoice.total * Decimal("0.40")).quantize(Decimal("0.01"))
                second = (invoice.total * Decimal("0.35")).quantize(Decimal("0.01"))
                self._add_payment(invoice, first, rng.choice(methods), f"DEMO-PART-1-{index:03d}", created_at)
                self._add_payment(invoice, second, rng.choice(methods), f"DEMO-PART-2-{index:03d}", created_at + timezone.timedelta(days=1))

            invoice.refresh_totals()
            invoices.append(invoice)

        return invoices

    def _add_payment(self, invoice: Invoice, amount: Decimal, method: str, reference: str, created_at) -> None:
        if amount <= Decimal("0.00"):
            return
        payment = Payment.objects.create(invoice=invoice, amount=amount, method=method, reference=reference)
        payment.created_at = created_at
        payment.save(update_fields=["created_at"])
