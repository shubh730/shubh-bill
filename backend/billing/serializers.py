from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from .models import Customer, Invoice, InvoiceItem, Payment, Product, create_invoice_with_stock


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "sku", "barcode", "price", "tax_rate", "stock", "is_active", "created_at", "updated_at"]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "address", "created_at"]


class InvoiceItemReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ["id", "product", "product_name", "sku", "quantity", "unit_price", "tax_rate", "line_subtotal", "line_tax", "line_total"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "invoice", "amount", "method", "reference", "created_at"]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        invoice = attrs.get("invoice") or getattr(self.instance, "invoice", None)
        amount = attrs.get("amount") or getattr(self.instance, "amount", Decimal("0.00"))
        if invoice:
            previous_paid = invoice.payments.exclude(pk=getattr(self.instance, "pk", None)).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            if previous_paid + amount > invoice.total:
                remaining = max(invoice.total - previous_paid, Decimal("0.00"))
                raise serializers.ValidationError({"amount": f"Payment cannot exceed remaining due amount {remaining}."})
        return attrs

    def create(self, validated_data):
        payment = super().create(validated_data)
        return payment

    def update(self, instance, validated_data):
        payment = super().update(instance, validated_data)
        payment.invoice.refresh_totals()
        return payment


class InvoiceReadSerializer(serializers.ModelSerializer):
    items = InvoiceItemReadSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "number",
            "customer",
            "customer_name",
            "customer_phone",
            "status",
            "subtotal",
            "tax_total",
            "discount",
            "total",
            "paid_amount",
            "due_amount",
            "notes",
            "created_at",
            "updated_at",
            "items",
            "payments",
        ]


class InvoiceItemWriteSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(source="product", queryset=Product.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1)


class InvoiceCreateSerializer(serializers.Serializer):
    customer_id = serializers.PrimaryKeyRelatedField(source="customer", queryset=Customer.objects.all(), required=False, allow_null=True)
    customer_name = serializers.CharField(max_length=140, required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"), default=Decimal("0.00"))
    notes = serializers.CharField(required=False, allow_blank=True)
    items = InvoiceItemWriteSerializer(many=True)
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"), default=Decimal("0.00"))
    payment_method = serializers.ChoiceField(choices=Payment.Method.choices, default=Payment.Method.CASH)
    payment_reference = serializers.CharField(max_length=120, required=False, allow_blank=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("At least one item is required.")
        merged: dict[int, dict] = {}
        for item in items:
            product = item["product"]
            current = merged.setdefault(product.id, {"product": product, "quantity": 0})
            current["quantity"] += item["quantity"]
        for item in merged.values():
            if item["product"].stock < item["quantity"]:
                raise serializers.ValidationError(f"Insufficient stock for {item['product'].name}.")
        return list(merged.values())

    def create(self, validated_data):
        items = validated_data.pop("items")
        paid_amount = validated_data.pop("paid_amount", Decimal("0.00"))
        payment_method = validated_data.pop("payment_method", Payment.Method.CASH)
        payment_reference = validated_data.pop("payment_reference", "")
        payment_data = None
        if paid_amount > Decimal("0.00"):
            payment_data = {"amount": paid_amount, "method": payment_method, "reference": payment_reference}
        try:
            return create_invoice_with_stock(invoice_data=validated_data, items_data=items, payment_data=payment_data)
        except ValueError as exc:
            raise serializers.ValidationError({"items": [str(exc)]}) from exc
