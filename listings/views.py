from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.urls import reverse_lazy
from django.db.models import Q

from .models import Listing, Review
from .forms import ListingForm, ReviewForm, RegistrationForm


#  Список + фильтры (публичный)
class ListingListView(ListView):
    model = Listing
    template_name = 'listings/listing_list.html'
    context_object_name = 'listings'
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset().filter(is_moderated=True, status='approved')
        
        q = self.request.GET.get('q')
        location = self.request.GET.get('location')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if location:
            qs = qs.filter(location__icontains=location)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        return qs

#  Детальная страница
# Вставь это ВНУТРЬ класса ListingDetailView (замени старый класс на этот)
class ListingDetailView(DetailView):
    model = Listing
    template_name = 'listings/listing_detail.html'
    context_object_name = 'listing'

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            return qs.filter(is_moderated=True, status='approved')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ReviewForm()
        return context

# ➕ Создание (только авторизованные)
class ListingCreateView(LoginRequiredMixin, CreateView):
    model = Listing
    form_class = ListingForm
    template_name = 'listings/listing_form.html'
    success_url = reverse_lazy('listings:listing_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.is_moderated = False
        form.instance.status = 'pending'
        return super().form_valid(form)

#  Редактирование (только владелец)
class ListingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Listing
    form_class = ListingForm
    template_name = 'listings/listing_form.html'

    def test_func(self):
        return self.get_object().owner == self.request.user

    def get_success_url(self):
        return reverse_lazy('listings:listing_detail', kwargs={'pk': self.object.pk})

#  Удаление (только владелец)
class ListingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Listing
    template_name = 'listings/listing_confirm_delete.html'
    success_url = reverse_lazy('listings:listing_list')

    def test_func(self):
        return self.get_object().owner == self.request.user
        
        
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('listings:listing_list')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('listings:listing_list')
        else:
            return render(request, 'registration/login.html', {'error_message': 'Неверный логин или пароль'})
    return render(request, 'registration/login.html')
    

#Создание объявления (пользовательская версия)
def create_ad(request):
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.is_moderated = False
            listing.status = 'pending'
            listing.save()
            return redirect('listings:listing_list')
    else:
        form = ListingForm()
    
    print("🔍 Контекст для шаблона:", {'form': form}) 
    
    return render(request, 'listings/create_ad.html', {'form': form})

#Модерация/одобрение объявлений
@login_required
def approve_ad(request):
    # Только staff/модераторы видят эту страницу
    if not request.user.is_staff:
        return redirect('listings:listing_list')
        
    listings = Listing.objects.filter(is_moderated=False, status='pending')
    
    if request.method == 'POST':
        for listing in listings:
            if str(listing.id) in request.POST:
                listing.is_moderated = True
                listing.status = 'approved'
                listing.save()
        return redirect('listings:approve_ad')
        
    return render(request, 'listings/approve_ad.html', {'listings': listings})
    
def add_review(request, pk):
    listing = Listing.objects.get(pk=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.listing = listing
            review.author = request.user
            review.save()
            return redirect('listings:listing_detail', pk=pk)
    else:
        form = ReviewForm()
    return redirect('listings:listing_detail', pk=pk)
