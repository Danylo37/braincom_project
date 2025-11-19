from django.db import models
from django.contrib.postgres.fields import ArrayField


class Product(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    regular_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    product_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    vendor = models.CharField(max_length=100, blank=True, null=True)

    color = models.CharField(max_length=50, blank=True, null=True)
    memory_volume = models.CharField(max_length=50, blank=True, null=True)
    review_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    series = models.CharField(max_length=100, blank=True, null=True)
    screen_diagonal = models.CharField(max_length=50, blank=True, null=True)
    screen_resolution = models.CharField(max_length=50, blank=True, null=True)
    photos = ArrayField(models.URLField(blank=True, null=True), blank=True, default=list)
    specifications = models.JSONField(blank=True, null=True)

    link = models.URLField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.link
