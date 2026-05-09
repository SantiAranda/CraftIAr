from django.contrib import admin

from app.api.products.product_model import ProductModel


@admin.register(ProductModel)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "sku", "name", "price", "stock", "is_active", "updated_at")
    search_fields = ("sku", "name", "category")
    list_filter = ("is_active", "category")
