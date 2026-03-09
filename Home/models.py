from django.db import models


class Business(models.Model):

    data_id = models.CharField(max_length=100, unique=True)

    name = models.CharField(max_length=255)

    address = models.TextField(null=True)


    rating = models.FloatField(null=True)  # overall rating

    total_reviews = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Create your models here.
class Review(models.Model):

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    review_id = models.CharField(max_length=255, unique=True)

    reviewer_name = models.CharField(max_length=255)

    rating = models.IntegerField()

    text = models.TextField(null=True, blank=True)   # FIXED

    response = models.TextField(null=True, blank=True)

    review_link = models.URLField()

    review_date = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer_name} - {self.rating}"