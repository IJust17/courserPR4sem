import django_filters as df
from django.db.models import Avg

from .models import Movie, Genre, Country


class MovieFilter(df.FilterSet):
    # текстовый поиск (НЕчувствительный) — __icontains
    title = df.CharFilter(field_name='title',
                          lookup_expr='icontains', label='Название')

    # чувствительный поиск по описанию — __contains
    description_contains = df.CharFilter(
        field_name='description',
        lookup_expr='contains', label='Описание содержит (CS)'
    )

    # справочники
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

    # рейтинг
    min_rating = df.NumberFilter(field_name='computed_rating',
                                 lookup_expr='gte', label='Мин. рейтинг')
    max_rating = df.NumberFilter(field_name='computed_rating',
                                 lookup_expr='lte', label='Макс. рейтинг')

    # дата
    release_year = df.NumberFilter(
        field_name='release_date', lookup_expr='year', label='Год выпуска'
    )

    class Meta:
        model = Movie
        fields = ['title', 'description_contains', 'genre',
                  'main_genre', 'country', 'min_rating', 'max_rating',
                  'release_year']

    @classmethod
    def annotate_queryset(cls, qs):
        return qs.annotate(computed_rating=Avg('reviews__rating'))
