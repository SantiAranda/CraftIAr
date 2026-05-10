from django.db import models


class ProductModel(models.Model):
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=120, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0) #type: ignore
    is_active = models.BooleanField(default=True) #type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    embedding = models.CharField(max_length=20, null=True, blank=True)  # Store embedding as a string (e.g., JSON or base64)

    objects = models.Manager()

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sku} - {self.name}"

    def save(self, *args, **kwargs):
        if self.pk:
            old_product = ProductModel.objects.get(pk=self.pk)
            if (
                old_product.name != self.name
                or old_product.description != self.description
                or old_product.category != self.category
                or old_product.price != self.price
                or old_product.stock != self.stock
                or old_product.is_active != self.is_active 
            ):
                self.embedding = None  # Mark embedding for update
        super().save(*args, **kwargs)
