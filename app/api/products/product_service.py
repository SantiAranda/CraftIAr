from django.db import transaction

from .product_model import ProductModel


class ProductService:
    @staticmethod
    def list_products():
        return ProductModel.objects.all()

    @staticmethod
    def get_product(product_id):
        return ProductModel.objects.filter(id=product_id).first()

    @staticmethod
    def create_product(data):
        with transaction.atomic(): #type: ignore
            return ProductModel.objects.create(**data)

    @staticmethod
    def update_product(product, data):
        with transaction.atomic(): #type: ignore
            for field, value in data.items():
                setattr(product, field, value)
            product.save()
            return product

    @staticmethod
    def delete_product(product):
        product.delete()
