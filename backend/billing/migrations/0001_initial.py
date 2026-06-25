from decimal import Decimal

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=140)),
                ("phone", models.CharField(blank=True, db_index=True, max_length=20)),
                ("address", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.CharField(editable=False, max_length=32, unique=True)),
                ("customer_name", models.CharField(blank=True, max_length=140)),
                ("customer_phone", models.CharField(blank=True, max_length=20)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("paid", "Paid"), ("partial", "Partial"), ("unpaid", "Unpaid"), ("cancelled", "Cancelled")], default="unpaid", max_length=16)),
                ("subtotal", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("tax_total", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("discount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("total", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("paid_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("due_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="invoices", to="billing.customer")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=160)),
                ("sku", models.CharField(max_length=64, unique=True)),
                ("barcode", models.CharField(blank=True, db_index=True, max_length=64)),
                ("price", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("tax_rate", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=5)),
                ("stock", models.IntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))])),
                ("method", models.CharField(choices=[("cash", "Cash"), ("upi", "UPI"), ("card", "Card"), ("bank", "Bank")], default="cash", max_length=16)),
                ("reference", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("invoice", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="billing.invoice")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="InvoiceItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name", models.CharField(max_length=160)),
                ("sku", models.CharField(max_length=64)),
                ("quantity", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("tax_rate", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=5)),
                ("line_subtotal", models.DecimalField(decimal_places=2, max_digits=12)),
                ("line_tax", models.DecimalField(decimal_places=2, max_digits=12)),
                ("line_total", models.DecimalField(decimal_places=2, max_digits=12)),
                ("invoice", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="billing.invoice")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="invoice_items", to="billing.product")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.AddIndex(model_name="product", index=models.Index(fields=["name", "sku"], name="billing_pro_name_48adcb_idx")),
        migrations.AddIndex(model_name="product", index=models.Index(fields=["barcode"], name="billing_pro_barcode_8551be_idx")),
    ]
