from django.db.models import Avg
from rest_framework import viewsets, mixins, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend

from .models import Movie, Review, Favorite
from .serializers import MovieSerializer, ReviewSerializer, UserSerializer
from .permissions import IsAdminOrReadOnly
from .filters import MovieFilter

User = get_user_model()


class MovieViewSet(viewsets.ModelViewSet):
    serializer_class = MovieSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = MovieFilter
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = ('title', 'description', 'actors__name')
    ordering_fields = ('release_date', 'computed_rating')

    def get_queryset(self):
        qs = (Movie.objects.with_computed_rating()
              .select_related('country', 'main_genre')
              .prefetch_related('genres', 'actors'))
        return MovieFilter.annotate_queryset(qs)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.request.user.is_authenticated:
            fav_ids = Favorite.objects.filter(user=self.request.user) \
                                      .values_list('movie_id', flat=True)
            ctx['favorite_ids'] = set(fav_ids)
        return ctx

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        movie = self.get_object()
        reviews = movie.reviews.filter(is_approved=True) \
                               .select_related('user') \
                               .order_by('-created_at')
        page = self.paginate_queryset(reviews)
        serializer = ReviewSerializer(page or reviews, many=True)
        return self.get_paginated_response(serializer.data) \
            if page else Response(serializer.data)


class ReviewViewSet(mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthenticated,)

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['movie', 'user', 'is_approved']

    def get_queryset(self):
        qs = Review.objects.select_related('movie', 'user') \
                           .order_by('-created_at')
        # не-админ видит только одобренные отзывы
        if not self.request.user.is_staff:
            qs = qs.filter(is_approved=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            is_approved=self.request.user.is_staff  # админ = сразу одобрено
        )


@api_view(['POST'])
@permission_classes([])
def register(request):
    """
    POST {username, email, password}
    Создаёт пользователя и возвращает auth-token.
    """
    serializer = UserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = User.objects.create_user(
        username=serializer.validated_data['username'],
        email=serializer.validated_data.get('email'),
        password=request.data.get('password')
    )
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': UserSerializer(user).data},
                    status=status.HTTP_201_CREATED)
