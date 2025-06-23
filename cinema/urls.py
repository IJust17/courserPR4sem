from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter

from . import views
from .api_views import MovieViewSet, ReviewViewSet, register

router = DefaultRouter()
router.register('movies', MovieViewSet, basename='movie-api')
router.register('reviews', ReviewViewSet, basename='review-api')

app_name = 'cinema'

urlpatterns = [
    # HTML-интерфейс
    path('', views.MovieListView.as_view(), name='movie-list'),
    path('movies/<int:pk>/', views.MovieDetailView.as_view(), name='movie-detail'),
    path('movies/<int:pk>/favorite/', views.FavoriteToggleView.as_view(), name='movie-favorite'),
    path('movies/create/', views.MovieCreateView.as_view(), name='movie-create'),
    path('movies/<int:pk>/edit/', views.MovieUpdateView.as_view(), name='movie-update'),
    path('movies/<int:pk>/delete/', views.MovieDeleteView.as_view(), name='movie-delete'),

    # ── билеты ──
    path('movies/<int:pk>/buy/', views.TicketPurchaseView.as_view(), name='ticket-buy'),
    path('tickets/', views.TicketListView.as_view(), name='ticket-list'),

    # ── избранное / рекомендации ──
    path('favorites/', views.FavoriteListView.as_view(), name='favorite-list'),
    path('recommendations/', views.RecommendationListView.as_view(), name='recommendations'),

    # ── отзывы ──
    path('moderation/reviews/', views.ReviewModerationListView.as_view(),
         name='review-moderation'),
    path('moderation/reviews/<int:pk>/approve/', views.ReviewApproveView.as_view(),
         name='review-approve'),
    path('reviews/<int:pk>/delete/', views.ReviewDeleteView.as_view(),       # ← добавлено
         name='review-delete'),

    # ── управление пользователями ──
    path('admin-users/', views.UserListView.as_view(), name='user-list'),
    path('admin-users/<int:pk>/toggle-staff/', views.ToggleStaffView.as_view(),
         name='user-toggle-staff'),

    # ── аккаунты ──
    path('accounts/login/',  auth_views.LoginView.as_view(
            template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(
            next_page='cinema:login'),               name='logout'),
    path('accounts/register/', views.SignUpView.as_view(),  name='register'),
    path('accounts/profile/',  views.ProfileView.as_view(), name='profile'),

    # ── REST-API ──
    path('api/', include(router.urls)),
    path('api/auth/register/', register, name='api-register'),

    path('bcexam/', views.BCExamListView.as_view(), name='bcexam-list'),
]
