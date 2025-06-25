import datetime
from datetime import date

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (UserCreationForm,
                                       AuthenticationForm)
from django.utils import timezone

from .models import Movie, Review, Session, Ticket

User = get_user_model()


# ────── аккаунты ──────
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email')


class SignInForm(AuthenticationForm):
    pass


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')


# ────── фильм ──────
class MovieForm(forms.ModelForm):
    release_year = forms.IntegerField(
        label='Год выхода',
        min_value=1888,
        max_value=datetime.date.today().year + 5,
        widget=forms.NumberInput(attrs={'placeholder': 'например 2026'}),
    )
    trailer = forms.FileField(                 # <── FileField на форме
        label='Файл трейлера', required=False
    )

    class Meta:
        model = Movie
        exclude = ('release_date', 'avg_rating')
        widgets = {
            'genres': forms.CheckboxSelectMultiple,
            'actors': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['release_year'].initial = \
                self.instance.release_date.year

    def clean(self):
        cleaned = super().clean()
        year = cleaned.get('release_year')
        if year:
            cleaned['release_date'] = date(year, 1, 1)
            self.instance.release_date = cleaned['release_date']
        return cleaned


# ────── отзыв ──────
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'review_text')

    def clean_review_text(self):
        text = self.cleaned_data.get('review_text', '').lower()
        from django.conf import settings
        if any(bad in text for bad in settings.BANNED_WORDS):
            raise forms.ValidationError('Текст содержит запрещённые слова.')
        return text


# ────── покупка билета ──────
class TicketPurchaseForm(forms.Form):
    session = forms.ModelChoiceField(queryset=Session.objects.none(),
                                     label='Сеанс')
    payment_method = forms.ChoiceField(
        label='Способ оплаты',
        choices=[('sbp', 'СБП'), ('cash', 'Наличные')],
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        movie = kwargs.pop('movie')
        super().__init__(*args, **kwargs)
        qs = (Session.objects
              .filter(movie=movie, starts_at__gt=timezone.now())
              .select_related('hall__cinema'))
        self.fields['session'].queryset = qs
        self.movie = movie

    def clean(self):
        cleaned = super().clean()
        session: Session = cleaned.get('session')
        if not session:
            return cleaned

        seats_qs = session.hall.seats.all()
        if seats_qs.exists():
            taken = session.tickets.values_list('seat_id', flat=True)
            has_free = seats_qs.exclude(id__in=taken).exists()
            if not has_free:
                raise forms.ValidationError(
                    'На выбранный сеанс нет свободных мест.'
                )
        return cleaned
