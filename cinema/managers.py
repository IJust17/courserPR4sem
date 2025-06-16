from django.db import models
from django.db.models import Avg


class MovieQuerySet(models.QuerySet):
    """
    Кастомный QuerySet.
    computed_rating — динамически высчитанная средняя оценка на основе связанных Review.
    """
    def with_computed_rating(self):
        return self.annotate(computed_rating=Avg('reviews__rating'))

    def top_rated(self, limit: int = 10):
        return (self.with_computed_rating()
                    .order_by('-computed_rating')[:limit])


class MovieManager(models.Manager):
    """
    Менеджер, проксирующий методы кастомного QuerySet,
    чтобы можно было писать Movie.objects.with_computed_rating().
    """
    def get_queryset(self):
        return MovieQuerySet(self.model, using=self._db)

    def with_computed_rating(self):
        return self.get_queryset().with_computed_rating()

    def top_rated(self, limit: int = 10):
        return self.get_queryset().top_rated(limit=limit)
