from django.contrib import admin

from .models import ContactRequest


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "created_at", "processed"]
    list_filter = ["processed", "created_at"]
    search_fields = ["name", "email", "phone"]
    readonly_fields = ["created_at"]
