from django.contrib import admin
from django.db.models import Sum
from django.urls import reverse
from django.utils.html import format_html
from django.utils.timezone import localtime

from .models import Customer, Invoice, InvoiceItem, Payment, Product

admin.site.site_header = "Shubh Bill Admin"
admin.site.site_title = "Shubh Bill"
admin.site.index_title = "Billing Management"


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    fields = ["product_name", "sku", "quantity", "unit_price", "tax_rate", "line_subtotal", "line_tax", "line_total"]
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ["amount", "method", "reference", "created_at"]
    readonly_fields = ["created_at"]
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("created_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "sku", "barcode", "price", "tax_rate", "stock", "is_active", "updated_at"]
    search_fields = ["name", "sku", "barcode"]
    list_filter = ["is_active"]
    list_editable = ["price", "tax_rate", "stock", "is_active"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["name"]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "invoice_count", "total_due", "created_at"]
    search_fields = ["name", "phone"]
    readonly_fields = ["created_at"]

    @admin.display(description="Invoices")
    def invoice_count(self, obj):
        return obj.invoices.count()

    @admin.display(description="Due")
    def total_due(self, obj):
        return obj.invoices.aggregate(total=Sum("due_amount"))["total"] or 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["number", "customer_display", "status", "total", "paid_amount", "due_amount", "payment_parts", "created_at"]
    search_fields = ["number", "customer_name", "customer_phone"]
    list_filter = ["status", "created_at"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    inlines = [InvoiceItemInline, PaymentInline]
    actions = ["refresh_selected_totals"]
    readonly_fields = [
        "number",
        "status",
        "subtotal",
        "tax_total",
        "total",
        "paid_amount",
        "due_amount",
        "payment_parts",
        "payment_history",
        "created_at",
        "updated_at",
    ]
    fieldsets = [
        ("Invoice", {"fields": ["number", "status", "created_at", "updated_at"]}),
        ("Customer", {"fields": ["customer", "customer_name", "customer_phone"]}),
        ("Amounts", {"fields": ["subtotal", "tax_total", "discount", "total", "paid_amount", "due_amount"]}),
        ("Payment Details", {"fields": ["payment_parts", "payment_history"]}),
        ("Notes", {"fields": ["notes"]}),
    ]

    @admin.display(description="Customer")
    def customer_display(self, obj):
        if obj.customer:
            url = reverse("admin:billing_customer_change", args=[obj.customer_id])
            return format_html('<a href="{}">{}</a>', url, obj.customer.name)
        return obj.customer_name or "Walk-in"

    @admin.display(description="Parts paid")
    def payment_parts(self, obj):
        return obj.payments.count()

    @admin.display(description="Payment history")
    def payment_history(self, obj):
        payments = obj.payments.order_by("created_at")
        if not payments:
            return "No payment received"
        rows = [
            "<table style='width:100%;border-collapse:collapse'>",
            "<thead><tr><th style='text-align:left'>Date</th><th style='text-align:left'>Method</th><th style='text-align:right'>Amount</th><th style='text-align:left'>Reference</th></tr></thead><tbody>",
        ]
        for payment in payments:
            rows.append(
                "<tr>"
                f"<td>{localtime(payment.created_at).strftime('%d %b %Y, %I:%M %p')}</td>"
                f"<td>{payment.get_method_display()}</td>"
                f"<td style='text-align:right'>{payment.amount}</td>"
                f"<td>{payment.reference or '-'}</td>"
                "</tr>"
            )
        rows.append("</tbody></table>")
        return format_html("".join(rows))

    @admin.action(description="Recalculate selected invoice totals")
    def refresh_selected_totals(self, request, queryset):
        count = 0
        for invoice in queryset.prefetch_related("items", "payments"):
            invoice.refresh_totals()
            count += 1
        self.message_user(request, f"Recalculated {count} invoice total(s).")

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.refresh_totals()


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ["invoice_link", "product_name", "sku", "quantity", "unit_price", "line_total"]
    search_fields = ["invoice__number", "product_name", "sku"]
    list_filter = ["invoice__created_at"]
    readonly_fields = ["invoice", "product", "product_name", "sku", "quantity", "unit_price", "tax_rate", "line_subtotal", "line_tax", "line_total"]

    @admin.display(description="Invoice")
    def invoice_link(self, obj):
        url = reverse("admin:billing_invoice_change", args=[obj.invoice_id])
        return format_html('<a href="{}">{}</a>', url, obj.invoice.number)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["invoice_link", "customer_name", "amount", "method", "reference", "created_at"]
    search_fields = ["invoice__number", "invoice__customer_name", "invoice__customer_phone", "reference"]
    list_filter = ["method", "created_at"]
    date_hierarchy = "created_at"
    autocomplete_fields = ["invoice"]
    readonly_fields = ["created_at"]

    @admin.display(description="Invoice")
    def invoice_link(self, obj):
        url = reverse("admin:billing_invoice_change", args=[obj.invoice_id])
        return format_html('<a href="{}">{}</a>', url, obj.invoice.number)

    @admin.display(description="Customer")
    def customer_name(self, obj):
        return obj.invoice.customer_name or (obj.invoice.customer.name if obj.invoice.customer else "Walk-in")
