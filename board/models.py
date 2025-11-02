import uuid

from django.db import models


class Board(models.Model):
    name = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return self.name


class Column(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="columns")
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Card(models.Model):
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, blank=True, null=True
    )
    due_date = models.DateField(blank=True, null=True)
    assignee = models.CharField(max_length=100, blank=True)
    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name="cards")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.title


class OverviewLane(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filters = models.JSONField(default=dict, blank=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "created_at", "id"]

    def __str__(self):
        name = (self.filters or {}).get("name") or ""
        return name or f"Lane {self.pk}"
