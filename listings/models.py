from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Категория")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

class Listing(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('pending', 'На модерации'),
        ('approved', 'Опубликовано'),
        ('rented', 'Сдано в аренду'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings', verbose_name="Автор")
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена аренды")
    location = models.CharField(max_length=255, verbose_name="Местоположение")
    rental_start = models.DateField(verbose_name="Начало аренды")
    rental_end = models.DateField(verbose_name="Конец аренды")
    contact_info = models.CharField(max_length=255, verbose_name="Контакты")
    categories = models.ManyToManyField(Category, related_name='listings', verbose_name="Категории")
    is_moderated = models.BooleanField(default=False, verbose_name="Прошло модерацию")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class RentalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('approved', 'Подтверждено'),
        ('rejected', 'Отклонено'),
        ('completed', 'Завершено'),
    ]

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='requests', verbose_name="Объявление")
    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests', verbose_name="Арендатор")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    comments = models.TextField(blank=True, verbose_name="Комментарии")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Запрос на аренду"
        verbose_name_plural = "Запросы на аренду"
        ordering = ['-created_at']

    def __str__(self):
        return f"Запрос от {self.renter.username}"

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачено'),
        ('refunded', 'Возврат'),
    ]

    request = models.OneToOneField(RentalRequest, on_delete=models.CASCADE, related_name='transaction', verbose_name="Запрос")
    amount = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Сумма")
    transaction_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата транзакции")
    rental_start = models.DateField(verbose_name="Период (начало)")
    rental_end = models.DateField(verbose_name="Период (конец)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"

    def __str__(self):
        return f"Транзакция {self.amount}₽"

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images', verbose_name="Объявление")
    image = models.ImageField(upload_to='listings/', verbose_name="Изображение")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"

    def __str__(self):
        return f"Фото для {self.listing.title}"
        
class Review(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews', verbose_name="Объявление")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор отзыва")
    text = models.TextField(verbose_name="Текст отзыва")
    rating = models.PositiveIntegerField(verbose_name="Оценка (1-5)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']


        
