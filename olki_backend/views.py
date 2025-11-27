from django.shortcuts import render


def index(request):
    """Главная страница с отчетом о проекте"""
    return render(request, "report.html")
