from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from billing.views import CustomerViewSet, InvoiceViewSet, PaymentViewSet, ProductViewSet, SummaryView

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("customers", CustomerViewSet, basename="customer")
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/summary/", SummaryView.as_view(), name="summary"),
    path("api/", include(router.urls)),
    re_path(r"^(?!api/|admin/).*", TemplateView.as_view(template_name="index.html"), name="app"),
]
