from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from . import models
from .models import (
    BCExam,
)

# ───────────────────────────────── INLINE ───────────────────────────────────
class MovieGenreInline(admin.TabularInline):
    model = models.MovieGenre
    extra = 1
    raw_id_fields = ('genre',)


class MovieActorInline(admin.TabularInline):
    model = models.MovieActor
    extra = 1
    raw_id_fields = ('actor',)


class HallInline(admin.TabularInline):
    model = models.Hall
    extra = 0


# ─────────────────────────────── Movie ──────────────────────────────────────
@admin.register(models.Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'main_genre', 'release_date',
        'country', 'avg_rating', 'poster_preview',
    )
    list_display_links = ('title',)
    list_filter = ('main_genre', 'country', 'release_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'release_date'
    inlines = (MovieGenreInline, MovieActorInline)
    readonly_fields = ('avg_rating',)
    raw_id_fields = ('country', 'main_genre')

    @admin.display(description='постер')
    def poster_preview(self, obj):
        if obj.poster:
            return format_html('<img src="{}" style="height:60px;" />', obj.poster.url)
        return "—"


# ───────────────────────────── Справочники ──────────────────────────────────
@admin.register(models.Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(models.Actor)
class ActorAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(models.Country)
class CountryAdmin(admin.ModelAdmin):
    search_fields = ('name',)


# ───────────────────────── Cinema / Hall / Seat ─────────────────────────────
@admin.register(models.Cinema)
class CinemaAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    inlines = (HallInline,)
    search_fields = ('name',)


@admin.register(models.Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ('name', 'cinema')
    search_fields = ('name', 'cinema__name')
    autocomplete_fields = ('cinema',)


@admin.register(models.Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('row_num', 'seat_num', 'hall')
    search_fields = (
        'hall__name',
        'hall__cinema__name',
        'row_num',
        'seat_num',
    )
    autocomplete_fields = ('hall',)


# ─────────────────────────────── User ───────────────────────────────────────
@admin.register(models.User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active', 'date_joined')


# ─────────────────────────────── Review ─────────────────────────────────────
@admin.register(models.Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('movie', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    autocomplete_fields = ('movie', 'user')
    search_fields = ('review_text',)


# ─────────────────────────────── Session ────────────────────────────────────
@admin.register(models.Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('movie', 'hall', 'starts_at', 'price')
    list_filter = ('starts_at',)
    autocomplete_fields = ('movie', 'hall')
    search_fields = (
        'movie__title',
        'hall__name',
        'hall__cinema__name',
    )


# ─────────────────────────────── Ticket ─────────────────────────────────────
@admin.register(models.Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'seat', 'user', 'status', 'purchased_at')
    list_filter = ('status',)
    autocomplete_fields = ('session', 'seat', 'user')

@admin.register(BCExam)
class BCExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'exam_date', 'is_public', 'created_at')
    list_filter = (
        'is_public',
        'created_at',
        ('exam_date', admin.DateFieldListFilter),
    )
    search_fields = ('title', 'students__email')
    filter_horizontal = ('students',)