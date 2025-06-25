from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .managers import MovieManager


# ─────────── пользователь ───────────
class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        ordering = ['-date_joined']

    def __str__(self):
        return self.username


# ─────────── справочники ───────────
class Country(models.Model):
    name = models.CharField('страна', max_length=100, unique=True)

    class Meta:
        verbose_name = 'страна'
        verbose_name_plural = 'страны'
        ordering = ['name']

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField('жанр', max_length=100, unique=True)

    class Meta:
        verbose_name = 'жанр'
        verbose_name_plural = 'жанры'
        ordering = ['name']

    def __str__(self):
        return self.name


class Actor(models.Model):
    name = models.CharField('имя актёра', max_length=120, unique=True)
    bio = models.TextField('биография', blank=True)

    class Meta:
        verbose_name = 'актёр'
        verbose_name_plural = 'актёры'
        ordering = ['name']

    def __str__(self):
        return self.name


# ─────────── фильм ───────────
class Movie(models.Model):
    title = models.CharField('название', max_length=255)
    description = models.TextField('описание')
    release_date = models.DateField('дата выхода')

    poster = models.ImageField('постер', upload_to='posters/',
                               blank=True, null=True)
    trailer = models.FileField('файл трейлера', upload_to='trailers/',
                               blank=True, null=True)
    trailer_url = models.URLField(                    # ← URLField
        'URL-трейлера (YouTube)', blank=True, null=True
    )

    country = models.ForeignKey(
        Country, verbose_name='страна', on_delete=models.PROTECT
    )
    main_genre = models.ForeignKey(
        Genre, verbose_name='основной жанр',
        related_name='main_movies', on_delete=models.PROTECT
    )
    genres = models.ManyToManyField(
        Genre, verbose_name='жанры',
        through='MovieGenre', related_name='movies'
    )
    actors = models.ManyToManyField(
        Actor, verbose_name='актёры',
        through='MovieActor', related_name='movies'
    )

    avg_rating = models.DecimalField(
        'средняя оценка (денорм.)', max_digits=4,
        decimal_places=2, default=0, editable=False
    )

    objects = MovieManager()

    class Meta:
        verbose_name = 'фильм'
        verbose_name_plural = 'фильмы'
        ordering = ['-release_date', 'title']
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'release_date'],
                name='unique_movie_title_year'
            )
        ]

    def clean(self):
        if (Movie.objects
                .exclude(pk=self.pk)
                .filter(title__iexact=self.title,
                        release_date=self.release_date)
                .exists()):
            raise ValidationError('Фильм с таким названием и годом уже есть.')

        if self.release_date and self.release_date > timezone.localdate():
            raise ValidationError('Дата выхода не может быть в будущем.')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('cinema:movie-detail', args=[self.pk])


class MovieGenre(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'доп. жанр фильма'
        verbose_name_plural = 'доп. жанры фильма'
        unique_together = ('movie', 'genre')


class MovieActor(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)
    role_name = models.CharField('роль', max_length=120)

    class Meta:
        verbose_name = 'роль актёра'
        verbose_name_plural = 'роли актёров'
        unique_together = ('movie', 'actor')

    def __str__(self):
        return f'{self.actor} в «{self.movie}» — {self.role_name}'


# остальные модели не изменялись …



# ─────────── отзыв и избранное ───────────
class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 11)]

    movie = models.ForeignKey(
        Movie, verbose_name='фильм',
        on_delete=models.CASCADE, related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='автор',
        on_delete=models.CASCADE, related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField('оценка', choices=RATING_CHOICES)
    review_text = models.TextField('текст отзыва', blank=True)
    created_at = models.DateTimeField('создан', default=timezone.now,
                                      editable=False)
    is_approved = models.BooleanField(
        'одобрен модератором', default=False
    )

    class Meta:
        verbose_name = 'отзыв'
        verbose_name_plural = 'отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Отзыв {self.user} к «{self.movie}»'

    def clean(self):
        if not (1 <= self.rating <= 10):
            raise ValidationError('Оценка должна быть от 1 до 10.')

        bad = {w for w in settings.BANNED_WORDS
               if w in self.review_text.lower()}
        if bad:
            raise ValidationError(
                'Отзыв содержит запрещённые слова: ' + ', '.join(bad)
            )


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='пользователь',
        on_delete=models.CASCADE, related_name='favorites'
    )
    movie = models.ForeignKey(
        Movie, verbose_name='фильм',
        on_delete=models.CASCADE, related_name='favorites'
    )
    added_at = models.DateTimeField('дата добавления', default=timezone.now)

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'
        unique_together = ('user', 'movie')
        ordering = ['-added_at']


# ─────────── кинотеатры, залы, билеты ───────────
class Cinema(models.Model):
    name = models.CharField('кинотеатр', max_length=200)
    address = models.TextField('адрес')
    lat = models.DecimalField('широта', max_digits=9, decimal_places=6)
    lng = models.DecimalField('долгота', max_digits=9, decimal_places=6)
    contact_info = models.TextField('контакты', blank=True)

    class Meta:
        verbose_name = 'кинотеатр'
        verbose_name_plural = 'кинотеатры'
        ordering = ['name']

    def __str__(self):
        return self.name


class Hall(models.Model):
    cinema = models.ForeignKey(
        Cinema, verbose_name='кинотеатр',
        on_delete=models.CASCADE, related_name='halls'
    )
    name = models.CharField('зал', max_length=100)
    rows = models.PositiveIntegerField('ряды')
    seats_per_row = models.PositiveIntegerField('мест в ряду')

    class Meta:
        verbose_name = 'зал'
        verbose_name_plural = 'залы'
        unique_together = ('cinema', 'name')

    def __str__(self):
        return f'{self.cinema} — {self.name}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            Seat.objects.bulk_create(
                Seat(hall=self, row_num=r, seat_num=s)
                for r in range(1, self.rows + 1)
                for s in range(1, self.seats_per_row + 1)
            )


class Seat(models.Model):
    hall = models.ForeignKey(
        Hall, verbose_name='зал',
        on_delete=models.CASCADE, related_name='seats'
    )
    row_num = models.PositiveIntegerField('ряд')
    seat_num = models.PositiveIntegerField('место')

    class Meta:
        verbose_name = 'место'
        verbose_name_plural = 'места'
        unique_together = ('hall', 'row_num', 'seat_num')

    def __str__(self):
        return f'Ряд {self.row_num}, место {self.seat_num} ({self.hall})'


class Session(models.Model):
    movie = models.ForeignKey(
        Movie, verbose_name='фильм',
        on_delete=models.PROTECT, related_name='sessions'
    )
    hall = models.ForeignKey(
        Hall, verbose_name='зал',
        on_delete=models.PROTECT, related_name='sessions'
    )
    starts_at = models.DateTimeField('начало сеанса')
    price = models.DecimalField('стоимость', max_digits=7, decimal_places=2)

    class Meta:
        verbose_name = 'сеанс'
        verbose_name_plural = 'сеансы'
        ordering = ['starts_at']

    def __str__(self):
        local = timezone.localtime(self.starts_at)
        return f'{self.movie} — {local:%d.%m %H:%M} ({self.hall})'


class Ticket(models.Model):
    class Status(models.TextChoices):
        RESERVED = 'reserved', 'зарезервирован'
        PAID = 'paid', 'оплачен'
        CANCELLED = 'cancelled', 'отменён'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='покупатель',
        on_delete=models.PROTECT, related_name='tickets'
    )
    session = models.ForeignKey(
        Session, verbose_name='сеанс',
        on_delete=models.PROTECT, related_name='tickets'
    )
    seat = models.ForeignKey(
        Seat, verbose_name='место',
        on_delete=models.PROTECT, related_name='tickets'
    )
    status = models.CharField(
        'статус', max_length=10,
        choices=Status.choices, default=Status.PAID
    )
    purchased_at = models.DateTimeField('время покупки',
                                        default=timezone.now)

    class Meta:
        verbose_name = 'билет'
        verbose_name_plural = 'билеты'
        unique_together = ('session', 'seat')

    def __str__(self):
        return f'Билет {self.id} — {self.session} ({self.seat})'
