import django_filters as df
from django.db.models import Avg

from .models import Movie, Genre, Country


class MovieFilter(df.FilterSet):
    # ───────── текстовый поиск ─────────
    title = df.CharFilter(
        field_name='title', lookup_expr='icontains', label='Название'
    )

    # ───────── справочники (выпадающие списки в HTML) ─────────
    genre = df.ModelChoiceFilter(
        field_name='genres', queryset=Genre.objects.all(),
        to_field_name='id', label='Доп. жанр'
    )
    main_genre = df.ModelChoiceFilter(
        field_name='main_genre', queryset=Genre.objects.all(),
        to_field_name='id', label='Основной жанр'
    )
    country = df.ModelChoiceFilter(
        field_name='country', queryset=Country.objects.all(),
        to_field_name='id', label='Страна'
    )

    # ───────── фильтр по средней оценке ─────────
    min_rating = df.NumberFilter(
        field_name='computed_rating', lookup_expr='gte', label='Мин. рейтинг'
    )
    max_rating = df.NumberFilter(
        field_name='computed_rating', lookup_expr='lte', label='Макс. рейтинг'
    )

    # ───────── дата выхода ─────────
    release_year = df.NumberFilter(
        field_name='release_date', lookup_expr='year', label='Год выпуска'
    )
    release_after = df.DateFilter(
        field_name='release_date', lookup_expr='gte', label='После даты'
    )
    release_before = df.DateFilter(
        field_name='release_date', lookup_expr='lte', label='До даты'
    )

    class Meta:
        model = Movie
        fields = [
            'title',
            'genre',
            'main_genre',
            'country',
            'min_rating',
            'max_rating',
            'release_year',
            'release_after',
            'release_before',
        ]

    # ───────── аннотируем средний рейтинг ─────────
    @classmethod
    def annotate_queryset(cls, qs):
        return qs.annotate(computed_rating=Avg('reviews__rating'))
