import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
class TestMetrics:
    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert (
            "django_http_requests_total" in response.content.decode()
            or "prometheus" in response.content.decode().lower()
        )
