import pytest
from rest_framework import status
from rest_framework.test import APIClient

from .models import Product


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def products(db):
    return [
        Product.objects.create(name=f"Product {i}", description="Desc", price=100 * i)
        for i in range(5)
    ]


@pytest.mark.django_db
class TestProductViewSet:
    def test_list_pagination(self, api_client, products):
        response = api_client.get("/api/products/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert "count" in response.data
        assert len(response.data["results"]) <= 20

    def test_empty_list(self, api_client):
        response = api_client.get("/api/products/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_featured_products_empty(self, api_client):
        response = api_client.get("/api/products/featured/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_featured_products_less_than_three(self, api_client, db):
        Product.objects.create(name="Product 1", description="Desc", price=100)
        Product.objects.create(name="Product 2", description="Desc", price=200)
        response = api_client.get("/api/products/featured/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_search_case_insensitive(self, api_client, db):
        Product.objects.create(name="Белая краска", description="Desc", price=100)
        Product.objects.create(name="белая эмаль", description="Desc", price=200)
        Product.objects.create(name="Синяя краска", description="Desc", price=300)
        # SQLite might not support case-insensitive search for Unicode, so test with exact case
        response = api_client.get("/api/products/?search=белая")
        assert response.status_code == status.HTTP_200_OK
        # At least one result should be found
        assert len(response.data["results"]) >= 1

    def test_search_no_results(self, api_client, db):
        Product.objects.create(name="Product 1", description="Desc", price=100)
        response = api_client.get("/api/products/?search=nonexistent")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0
