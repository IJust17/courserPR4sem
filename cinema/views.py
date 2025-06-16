from django.contrib.auth import login, logout, views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
    TemplateView, FormView
)

from .models import Movie, Favorite, Review, Ticket, Seat, User
from .forms import (
    MovieForm, SignUpForm, SignInForm,
    ReviewForm, ProfileUpdateForm, TicketPurchaseForm
)
from .filters import MovieFilter


# ─────────── учётные записи ───────────
class SignUpView(CreateView):
    template_name = 'registration/register.html'
    form_class = SignUpForm
    success_url = reverse_lazy('cinema:movie-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class LoginView(auth_views.LoginView):
    template_name = 'registration/login.html'
    authentication_form = SignInForm


class LogoutRedirectView(View):
    def get(self, request):
        logout(request)
        return redirect('cinema:login')


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'registration/profile.html'
    form_class = ProfileUpdateForm
    success_url = reverse_lazy('cinema:profile')

    def get_object(self, queryset=None):
        return self.request.user


# ─────────── рекомендации ───────────
class RecommendationListView(LoginRequiredMixin, ListView):
    template_name = 'cinema/recommendations.html'
    context_object_name = 'movies'

    def get_queryset(self):
        user_reviewed = Review.objects.filter(user=self.request.user) \
                                      .values_list('movie_id', flat=True)
        return (Movie.objects.with_computed_rating()
                .filter(computed_rating__gte=7)
                .exclude(id__in=user_reviewed)
                .order_by('-computed_rating')[:20])


# ─────────── каталог ───────────
class MovieListView(ListView):
    model = Movie
    paginate_by = 10
    template_name = 'cinema/movie_list.html'

    def get_queryset(self):
        qs = (Movie.objects.with_computed_rating()
              .select_related('country', 'main_genre')
              .prefetch_related('genres', 'actors'))
        self.filterset = MovieFilter(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filterset'] = self.filterset
        return ctx


# ─────────── страница фильма ───────────
class MovieDetailView(DetailView):
    model = Movie
    template_name = 'cinema/movie_detail.html'

    def get_queryset(self):
        return (Movie.objects.with_computed_rating()
                .select_related('country')
                .prefetch_related('genres', 'actors', 'reviews__user'))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.is_authenticated:
            return redirect('cinema:login')
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            form.instance.movie = self.object
            form.instance.is_approved = request.user.is_staff  # админ = auto approve
            form.save()
            return redirect(self.object.get_absolute_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = ReviewForm()
        ctx['reviews'] = self.object.reviews.filter(is_approved=True)
        if self.request.user.is_authenticated:
            ctx['is_favorite'] = Favorite.objects.filter(
                user=self.request.user, movie=self.object
            ).exists()
        return ctx


# ─────────── покупка билета ───────────
class TicketPurchaseView(LoginRequiredMixin, FormView):
    template_name = 'cinema/ticket_buy.html'
    form_class = TicketPurchaseForm

    def dispatch(self, request, *args, **kwargs):
        self.movie = get_object_or_404(Movie, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['movie'] = self.movie
        return kwargs

    def form_valid(self, form):
        session = form.cleaned_data['session']

        if session.hall.seats.exists():
            taken = session.tickets.values_list('seat_id', flat=True)
            seat = session.hall.seats.exclude(id__in=taken).first()
        else:
            seat, _ = Seat.objects.get_or_create(
                hall=session.hall, row_num=1, seat_num=1
            )

        Ticket.objects.create(
            user=self.request.user,
            session=session,
            seat=seat,
            status=Ticket.Status.PAID,
            purchased_at=timezone.now(),
        )
        return redirect('cinema:ticket-list')


# ─────────── список билетов ───────────
class TicketListView(LoginRequiredMixin, ListView):
    template_name = 'cinema/ticket_list.html'
    context_object_name = 'tickets'

    def get_queryset(self):
        return (Ticket.objects
                .filter(user=self.request.user)
                .select_related('session__movie', 'session__hall__cinema')
                .order_by('-purchased_at'))


# ─────────── избранное и отзывы ───────────
class FavoriteToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        fav_qs = Favorite.objects.filter(user=request.user, movie=movie)
        fav_qs.delete() if fav_qs.exists() else Favorite.objects.create(
            user=request.user, movie=movie
        )
        return redirect(movie.get_absolute_url())


class FavoriteListView(LoginRequiredMixin, ListView):
    template_name = 'cinema/favorite_list.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        return (Favorite.objects
                .filter(user=self.request.user)
                .select_related('movie', 'movie__main_genre'))


# ─────────── модерация отзывов ───────────
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class ReviewModerationListView(StaffRequiredMixin, ListView):
    template_name = 'cinema/review_moderation.html'
    context_object_name = 'reviews'
    queryset = Review.objects.filter(is_approved=False) \
                             .select_related('movie', 'user') \
                             .order_by('-created_at')


class ReviewApproveView(StaffRequiredMixin, View):
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk, is_approved=False)
        review.is_approved = True
        review.save()
        return redirect('cinema:review-moderation')

class ReviewDeleteView(StaffRequiredMixin, View):              # ← добавлено
    """Удаление отзыва прямо со страницы фильма (доступно только staff)."""
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        movie_url = review.movie.get_absolute_url()
        review.delete()
        return redirect(movie_url)


# ─────────── управление пользователями ───────────
class UserListView(StaffRequiredMixin, ListView):
    template_name = 'cinema/user_list.html'
    context_object_name = 'users'
    queryset = User.objects.all().order_by('-date_joined')


class ToggleStaffView(StaffRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user != request.user:               # нельзя лишить себя прав
            user.is_staff = not user.is_staff
            user.save()
        return redirect('cinema:user-list')


# ─────────── CRUD фильмов (staff) ───────────
class MovieCreateView(StaffRequiredMixin, CreateView):
    model = Movie
    form_class = MovieForm
    template_name = 'cinema/movie_form.html'


class MovieUpdateView(StaffRequiredMixin, UpdateView):
    model = Movie
    form_class = MovieForm
    template_name = 'cinema/movie_form.html'


class MovieDeleteView(StaffRequiredMixin, DeleteView):
    model = Movie
    template_name = 'cinema/movie_confirm_delete.html'
    success_url = reverse_lazy('cinema:movie-list')
