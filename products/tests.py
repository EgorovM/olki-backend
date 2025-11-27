import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from .models import Product


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def product_data():
    return {
        "name": "Краска белая",
        "description": "# Описание\nЭто отличная краска",
        "price": "1500.00",
    }


@pytest.fixture
def product_with_image(db):
    image = SimpleUploadedFile(
        name="test_image.jpg", content=b"\x00\x01\x02\x03", content_type="image/jpeg"
    )
    return Product.objects.create(
        name="Краска с изображением", description="Описание", price=2000.00, image=image
    )


@pytest.fixture
def product(db, product_data):
    return Product.objects.create(**product_data)


@pytest.mark.django_db
class TestProductModel:
    def test_create_product(self, product_data):
        product = Product.objects.create(**product_data)
        assert product.name == product_data["name"]
        assert product.description == product_data["description"]
        assert str(product.price) == product_data["price"]
        assert product.id is not None

    def test_product_str(self, product):
        assert str(product) == product.name

    def test_product_ordering(self, db):
        product1 = Product.objects.create(name="Product 1", description="Desc", price=100)
        product2 = Product.objects.create(name="Product 2", description="Desc", price=200)
        products = list(Product.objects.all())
        assert products[0] == product2
        assert products[1] == product1


@pytest.mark.django_db
class TestProductAPI:
    def test_list_products(self, api_client, product):
        response = api_client.get("/api/products/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == product.name

    def test_create_product(self, api_client, product_data):
        response = api_client.post("/api/products/", product_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == product_data["name"]
        assert Product.objects.count() == 1

    def test_retrieve_product(self, api_client, product):
        response = api_client.get(f"/api/products/{product.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == product.name
        assert response.data["price"] == str(product.price)

    def test_update_product(self, api_client, product):
        update_data = {"name": "Updated Name", "description": "Updated", "price": "2500.00"}
        response = api_client.put(f"/api/products/{product.id}/", update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.name == "Updated Name"

    def test_partial_update_product(self, api_client, product):
        update_data = {"price": "3000.00"}
        response = api_client.patch(f"/api/products/{product.id}/", update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert str(product.price) == "3000.00"

    def test_delete_product(self, api_client, product):
        response = api_client.delete(f"/api/products/{product.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Product.objects.count() == 0

    def test_search_products(self, api_client, db):
        Product.objects.create(name="Белая краска", description="Desc", price=100)
        Product.objects.create(name="Синяя краска", description="Desc", price=200)
        response = api_client.get("/api/products/?search=Белая")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert "Белая" in response.data["results"][0]["name"]

    def test_featured_products(self, api_client, db):
        for i in range(5):
            Product.objects.create(name=f"Product {i}", description="Desc", price=100)
        response = api_client.get("/api/products/featured/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_product_image_url(self, api_client, product_with_image):
        response = api_client.get(f"/api/products/{product_with_image.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert "image_url" in response.data
        assert response.data["image_url"] is not None

    def test_product_validation(self, api_client):
        invalid_data = {"name": "Test", "price": "-100"}
        response = api_client.post("/api/products/", invalid_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
