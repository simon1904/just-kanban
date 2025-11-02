from django.contrib import admin
from .models import Board, Column, Card, OverviewLane


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    ordering = ("created_at",)


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("name", "board", "order")
    list_filter = ("board",)
    search_fields = ("name",)
    ordering = ("board", "order")


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("title", "column", "priority", "due_date", "assignee")
    list_filter = ("column__board", "priority")
    search_fields = ("title", "description", "assignee")
    raw_id_fields = ("column",)


@admin.register(OverviewLane)
class OverviewLaneAdmin(admin.ModelAdmin):
    list_display = ("display_name", "position", "created_at")
    ordering = ("position", "created_at")
    search_fields = ("filters__name",)

    @admin.display(description="Name")
    def display_name(self, obj):
        return (obj.filters or {}).get("name") or f"Lane {obj.pk}"
