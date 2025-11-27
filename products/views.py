from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с продукцией"""

    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Получить избранные продукты (первые 3)"""
        products = self.get_queryset()[:3]
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
