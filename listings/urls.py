from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [

    path('', views.ListingListView.as_view(), name='listing_list'),
    path('<int:pk>/', views.ListingDetailView.as_view(), name='listing_detail'),
    

    path('create/', views.create_ad, name='create_ad'),       # <-- Теперь ведёт на нашу новую форму!
    path('approve/', views.approve_ad, name='approve_ad'),    # <-- Страница модератора
    
    # Редактирование и удаление (оставляем CBV, они защищены миксинами)
    path('<int:pk>/update/', views.ListingUpdateView.as_view(), name='listing_update'),
    path('<int:pk>/delete/', views.ListingDeleteView.as_view(), name='listing_delete'),
    
    # Аутентификация
    path('accounts/login/', views.user_login, name='login'),
    path('accounts/register/', views.register, name='register'),
    path('<int:pk>/review/', views.add_review, name='add_review'),
]
