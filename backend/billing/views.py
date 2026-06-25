from django.db.models import Sum
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer, Invoice, Payment, Product
from .serializers import CustomerSerializer, InvoiceCreateSerializer, InvoiceReadSerializer, PaymentSerializer, ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    search_fields = ["name", "sku", "barcode"]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ["name", "price", "stock", "updated_at"]

    def get_queryset(self):
        queryset = Product.objects.all()
        active = self.request.query_params.get("active")
        if active in {"true", "1"}:
            queryset = queryset.filter(is_active=True)
        return queryset


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    search_fields = ["name", "phone"]
    filter_backends = [filters.SearchFilter]


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.prefetch_related("items", "payments").select_related("customer")
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["number", "customer_name", "customer_phone"]
    ordering_fields = ["created_at", "total", "due_amount"]

    def get_serializer_class(self):
        if self.action == "create":
            return InvoiceCreateSerializer
        return InvoiceReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save()
        return Response(InvoiceReadSerializer(invoice, context=self.get_serializer_context()).data, status=status.HTTP_201_CREATED)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("invoice")
    serializer_class = PaymentSerializer


class SummaryView(APIView):
    def get(self, request):
        today = timezone.localdate()
        invoices = Invoice.objects.filter(created_at__date=today).exclude(status=Invoice.Status.CANCELLED)
        payments = Payment.objects.filter(created_at__date=today)
        return Response(
            {
                "date": today.isoformat(),
                "invoice_count": invoices.count(),
                "sales_total": invoices.aggregate(total=Sum("total"))["total"] or 0,
                "paid_total": payments.aggregate(total=Sum("amount"))["total"] or 0,
                "due_total": invoices.aggregate(total=Sum("due_amount"))["total"] or 0,
                "low_stock_count": Product.objects.filter(is_active=True, stock__lte=5).count(),
            }
        )
