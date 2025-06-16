from django.db.models import Avg
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Movie, Genre, Actor, Review, Favorite

User = get_user_model()


# ─────────── User ───────────
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_staff')


# ─────────── Review ───────────
class ReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='user.username', read_only=True)
    is_approved = serializers.BooleanField(read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'movie', 'user', 'author_name',
                  'rating', 'review_text', 'created_at', 'is_approved')
        read_only_fields = ('id', 'created_at', 'author_name', 'is_approved')


# ─────────── Movie ───────────
class MovieSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Genre.objects.all(), required=False
    )
    actors = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Actor.objects.all(), required=False
    )

    main_genre_name = serializers.CharField(
        source='main_genre.name', read_only=True
    )
    country_name = serializers.CharField(
        source='country.name', read_only=True
    )

    average_rating = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = (
            'id', 'title', 'description', 'release_date',
            'poster',
            'country', 'country_name',
            'main_genre', 'main_genre_name',
            'genres', 'actors',
            'average_rating', 'is_favorite',
        )

    # ───── вычисляемые поля ─────
    def get_average_rating(self, obj):
        return getattr(obj, 'computed_rating', None) \
            or obj.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'))['avg']

    def get_is_favorite(self, obj):
        favs = self.context.get('favorite_ids')
        return bool(favs and obj.id in favs)

    # ───── создание / обновление ─────
    def create(self, validated_data):
        genres = validated_data.pop('genres', [])
        actors = validated_data.pop('actors', [])
        movie = super().create(validated_data)
        if genres:
            movie.genres.set(genres)
        if actors:
            movie.actors.set(actors)
        return movie

    def update(self, instance, validated_data):
        genres = validated_data.pop('genres', None)
        actors = validated_data.pop('actors', None)
        movie = super().update(instance, validated_data)
        if genres is not None:
            movie.genres.set(genres)
        if actors is not None:
            movie.actors.set(actors)
        return movie
