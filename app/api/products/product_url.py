from django.urls import path

from .product_view import ProductApiView, ProductDetailApiView

urlpatterns = [
    path("products", ProductApiView.as_view(), name="products"),
    path("products/<int:product_id>", ProductDetailApiView.as_view(), name="product-detail"),
]
