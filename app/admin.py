from django.contrib import admin, messages

from .models import ProductModel
from .tasks import update_product_embeddings


@admin.register(ProductModel)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sku",
        "name",
        "price",
        "stock",
        "is_active",
        "category",
        "embedding",
        "updated_at",
    )
    search_fields = ("sku", "name", "category")
    list_filter = ("is_active", "category")

    actions = ["reindex_embeddings", "reset_embeddings"]

    @admin.action(description="Reindex embeddings for selected products")
    def reindex_embeddings(self, request, queryset):
        try:
            product_ids = list(queryset.values_list("id", flat=True))
            update_product_embeddings.delay(product_ids)
            self.message_user(
                request,
                "Reindexacion iniciada para los productos seleccionados.",
                level=messages.SUCCESS,
            )
        except Exception as e:
            self.message_user(
                request,
                f"Error al actualizar embeddings: {str(e)}",
                level=messages.ERROR,
            )
            return

    @admin.action(description="Reset embeddings for all products")
    def reset_embeddings(self, request, queryset):
        updated = queryset.update(embedding=None)
        self.message_user(
            request,
            f"Embeddings reiniciados para {updated} productos seleccionados.",
            level=messages.SUCCESS,
        )
