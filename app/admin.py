from django.contrib import admin, messages

from .models import ProductModel
from .tasks import update_product_embeddings


@admin.register(ProductModel)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "sku", "name", "price", "stock", "is_active", "updated_at")
    search_fields = ("sku", "name", "category")
    list_filter = ("is_active", "category")

    actions=['reindex_embeddings']

    @admin.action(description="Reindex embeddings for selected products")
    def reindex_embeddings(self, request, queryset):
        try:
            resultado = update_product_embeddings()
            self.message_user(request, f"Embeddings actualizados para {resultado} productos.", level=messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Error al actualizar embeddings: {str(e)}", level=messages.ERROR)
            return
