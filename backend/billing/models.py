from decimal import Decimal

from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F, Q
from django.utils import timezone


class Product(models.Model):
    name = models.CharField(max_length=160, db_index=True)
    sku = models.CharField(max_length=64, unique=True)
    barcode = models.CharField(max_length=64, blank=True, db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name", "sku"]),
            models.Index(fields=["barcode"]),
        ]

    def __str__(self) -> str:
        return self.name


class Customer(models.Model):
    name = models.CharField(max_length=140, db_index=True)
    phone = models.CharField(max_length=20, blank=True, db_index=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PAID = "paid", "Paid"
        PARTIAL = "partial", "Partial"
        UNPAID = "unpaid", "Unpaid"
        CANCELLED = "cancelled", "Cancelled"

    number = models.CharField(max_length=32, unique=True, editable=False)
    customer = models.ForeignKey(Customer, related_name="invoices", null=True, blank=True, on_delete=models.SET_NULL)
    customer_name = models.CharField(max_length=140, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.UNPAID)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            today = timezone.localdate()
            prefix = today.strftime("SB%Y%m%d")
            last = Invoice.objects.filter(number__startswith=prefix).order_by("-number").first()
            next_number = int(last.number[-4:]) + 1 if last else 1
            self.number = f"{prefix}{next_number:04d}"
        super().save(*args, **kwargs)

    def refresh_totals(self) -> None:
        subtotal = sum((item.line_subtotal for item in self.items.all()), Decimal("0.00"))
        tax_total = sum((item.line_tax for item in self.items.all()), Decimal("0.00"))
        total = max(subtotal + tax_total - self.discount, Decimal("0.00"))
        paid = sum((payment.amount for payment in self.payments.all()), Decimal("0.00"))
        due = max(total - paid, Decimal("0.00"))
        if total == Decimal("0.00"):
            status = self.Status.UNPAID
        elif paid >= total:
            status = self.Status.PAID
        elif paid > Decimal("0.00"):
            status = self.Status.PARTIAL
        else:
            status = self.Status.UNPAID
        self.subtotal = subtotal
        self.tax_total = tax_total
        self.total = total
        self.paid_amount = paid
        self.due_amount = due
        self.status = status
        self.save(update_fields=["subtotal", "tax_total", "total", "paid_amount", "due_amount", "status", "updated_at"])


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="invoice_items", on_delete=models.PROTECT)
    product_name = models.CharField(max_length=160)
    sku = models.CharField(max_length=64)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    line_subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    line_tax = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        UPI = "upi", "UPI"
        CARD = "card", "Card"
        BANK = "bank", "Bank"

    invoice = models.ForeignKey(Invoice, related_name="payments", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    method = models.CharField(max_length=16, choices=Method.choices, default=Method.CASH)
    reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.invoice.number} - {self.amount}"

    def clean(self) -> None:
        super().clean()
        if not self.invoice_id:
            return
        invoice = Invoice.objects.filter(pk=self.invoice_id).first()
        if not invoice:
            return
        previous_paid = invoice.payments.exclude(pk=self.pk).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")
        if invoice.total > Decimal("0.00") and previous_paid + self.amount > invoice.total:
            remaining = max(invoice.total - previous_paid, Decimal("0.00"))
            raise ValidationError({"amount": f"Payment cannot exceed remaining due amount {remaining}."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.invoice.refresh_totals()

    def delete(self, *args, **kwargs):
        invoice = self.invoice
        result = super().delete(*args, **kwargs)
        invoice.refresh_totals()
        return result


def create_invoice_with_stock(*, invoice_data: dict, items_data: list[dict], payment_data: dict | None = None) -> Invoice:
    with transaction.atomic():
        invoice = Invoice.objects.create(**invoice_data)
        for item in items_data:
            product = Product.objects.select_for_update().get(pk=item["product"].pk)
            quantity = item["quantity"]
            if product.stock < quantity:
                raise ValueError(f"Insufficient stock for {product.name}")
            line_subtotal = product.price * quantity
            line_tax = (line_subtotal * product.tax_rate / Decimal("100.00")).quantize(Decimal("0.01"))
            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                product_name=product.name,
                sku=product.sku,
                quantity=quantity,
                unit_price=product.price,
                tax_rate=product.tax_rate,
                line_subtotal=line_subtotal,
                line_tax=line_tax,
                line_total=line_subtotal + line_tax,
            )
            Product.objects.filter(Q(pk=product.pk) & Q(stock__gte=quantity)).update(stock=F("stock") - quantity)
        invoice.refresh_totals()
        if payment_data and payment_data.get("amount", Decimal("0.00")) > Decimal("0.00"):
            Payment.objects.create(invoice=invoice, **payment_data)
        invoice.refresh_totals()
        return invoice
