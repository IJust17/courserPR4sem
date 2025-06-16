from django.test import TestCase
from django.urls import reverse
from .models import Country, Genre, Movie

class MovieViewsTests(TestCase):
    def setUp(self):
        country = Country.objects.create(name='США')
        genre = Genre.objects.create(name='Драма')
        self.movie = Movie.objects.create(
            title='Test',
            description='lorem',
            release_date='2024-01-01',
            country=country,
            main_genre=genre,
        )

    def test_movie_list_view(self):
        resp = self.client.get(reverse('cinema:movie-list'))
        self.assertEqual(resp.status_code, 200)
