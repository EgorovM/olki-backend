import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory

from .models import Product
from .serializers import ProductSerializer


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def product(db):
    return Product.objects.create(
        name="Test Product", description="Test Description", price=1000.00
    )


@pytest.fixture
def product_with_image(db):
    image = SimpleUploadedFile(
        name="test_image.jpg", content=b"\x00\x01\x02\x03", content_type="image/jpeg"
    )
    return Product.objects.create(
        name="Product with Image", description="Description", price=2000.00, image=image
    )


@pytest.mark.django_db
class TestProductSerializer:
    def test_serialize_product(self, factory, product):
        request = factory.get("/")
        serializer = ProductSerializer(product, context={"request": request})
        data = serializer.data
        assert data["id"] == product.id
        assert data["name"] == product.name
        assert data["description"] == product.description
        # Price might be formatted differently, check numeric value
        assert float(data["price"]) == float(product.price)
        assert "created_at" in data
        assert "updated_at" in data

    def test_serialize_product_with_image(self, factory, product_with_image):
        request = factory.get("/")
        serializer = ProductSerializer(product_with_image, context={"request": request})
        data = serializer.data
        assert data["image_url"] is not None
        assert "http" in data["image_url"] or "/media/" in data["image_url"]

    def test_serialize_product_without_image(self, factory, product):
        request = factory.get("/")
        serializer = ProductSerializer(product, context={"request": request})
        data = serializer.data
        assert data["image_url"] is None

    def test_deserialize_product(self, factory):
        request = factory.get("/")
        data = {
            "name": "New Product",
            "description": "New Description",
            "price": "1500.00",
        }
        serializer = ProductSerializer(data=data, context={"request": request})
        assert serializer.is_valid()
        product = serializer.save()
        assert product.name == "New Product"
        assert product.description == "New Description"
        assert str(product.price) == "1500.00"
