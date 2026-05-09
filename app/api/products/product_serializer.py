from rest_framework import serializers

from .product_model import ProductModel


class ProductSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField(min_value=0)
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = ProductModel
        fields = [
            "id",
            "sku",
            "name",
            "description",
            "category",
            "price",
            "stock",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_sku(self, value):
        sku = value.strip()
        if not sku:
            raise serializers.ValidationError("SKU is required.")
        if " " in sku:
            raise serializers.ValidationError("SKU must not contain spaces.")
        return sku

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Name is required.")
        return name

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate(self, attrs):
        for key in ("description", "category"):
            if key in attrs and isinstance(attrs[key], str):
                attrs[key] = attrs[key].strip()
        return attrs
