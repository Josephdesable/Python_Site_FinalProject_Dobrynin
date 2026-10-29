import logging
import unittest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from listings.models import Listing, Category

logging.basicConfig(filename='test_diploma.log', level=logging.INFO)

class TestDiplomaFeatures(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(name="Тестовая категория")
        self.user = User.objects.create_user(username='tester', password='testpass123')
        self.staff_user = User.objects.create_user(username='moderator', password='modpass123', is_staff=True)
        logging.info("Test setup complete")

    def test_registration(self):
        response = self.client.post(reverse('listings:register'), {
            'username': 'newuser', 'email': 'test@diploma.com',
            'password1': 'SecurePass123!', 'password2': 'SecurePass123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        logging.info("test_registration: PASS")

    def test_create_ad(self):
        self.client.login(username='tester', password='testpass123')
        response = self.client.post(reverse('listings:create_ad'), {
            'title': 'Тестовое платье',
            'description': 'Описание для теста',
            'price': 2500,
            'location': 'Москва',
            'rental_start': '2026-10-01',
            'rental_end': '2026-10-10',
            'contact_info': '+79001234567',
            'categories': [self.cat.pk]
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Listing.objects.filter(title='Тестовое платье').exists())
        logging.info("test_create_ad: PASS")

    def test_search_listings(self):
        Listing.objects.create(
            title='Поисковое пальто',
            description='Тёплое зимнее пальто',
            price=3000,
            location='Санкт-Петербург',
            rental_start='2026-11-01',
            rental_end='2026-11-15',
            contact_info='+79007654321',
            owner=self.staff_user,
            is_moderated=True,
            status='approved'
        )
        response = self.client.get(reverse('listings:listing_list'), {'q': 'пальто'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Поисковое пальто')
        logging.info("test_search_listings: PASS")

    def test_moderation_approval(self):
        self.client.login(username='moderator', password='modpass123')
        pending_ad = Listing.objects.create(
            title='На модерации',
            description='Ждёт одобрения',
            price=1000,
            location='Казань',
            rental_start='2026-12-01',
            rental_end='2026-12-05',
            contact_info='+79001112233',
            owner=self.staff_user,
            is_moderated=False,
            status='pending'
        )
        response = self.client.post(reverse('listings:approve_ad'), data={str(pending_ad.pk): 'on'}, follow=True)
        self.assertEqual(response.status_code, 200)
        pending_ad.refresh_from_db()
        self.assertTrue(pending_ad.is_moderated)
        self.assertEqual(pending_ad.status, 'approved')
        logging.info("test_moderation_approval: PASS")
        

    def test_edit_listing(self):
        
        listing = Listing.objects.create(
            title='Старое название', owner=self.user, price=1000,
            location='Москва', rental_start='2026-10-01', rental_end='2026-10-10',
            contact_info='123', status='approved', is_moderated=True
        )
        listing.title = 'Новое название'
        listing.price = 1500.00
        listing.save()
        listing.refresh_from_db()
        
        self.assertEqual(listing.title, 'Новое название')
        self.assertEqual(listing.price, 1500.00)
        logging.info("test_edit_listing: PASS")

    def test_delete_listing(self):
        listing = Listing.objects.create(
            title='На удаление', owner=self.user, price=500,
            location='Москва', rental_start='2026-10-01', rental_end='2026-10-10',
            contact_info='123', status='approved', is_moderated=True
        )
        listing_id = listing.pk
        listing.delete()
        
        self.assertFalse(Listing.objects.filter(pk=listing_id).exists())
        logging.info("test_delete_listing: PASS")

    def test_create_review(self):
        """Сценарий: Создание отзыва (уникальность pairing уже проверена в models.UniqueConstraint)"""
        from listings.models import Review, ListingStatus
        
       
        test_listing = Listing.objects.create(
            title='Объявление для отзыва',
            owner=self.user,
            price=1000,
            location='Москва',
            rental_start='2026-10-01',
            rental_end='2026-10-10',
            contact_info='123',
            status=ListingStatus.APPROVED,
            is_moderated=True
        )
        
        # 2. Создаем отзыв, привязанный к этому объявлению
        review = Review.objects.create(
            listing=test_listing,
            author=self.user,
            text='Отличное качество, рекомендую!',
            rating=5
        )
        
      
        self.assertEqual(review.rating, 5)
        self.assertTrue(Review.objects.filter(author=self.user, listing=test_listing).exists())
        logging.info("test_create_review: PASS")

    def test_create_rental_request(self):
        from listings.models import RentalRequest, ListingStatus
        target_listing = Listing.objects.create(
            title='Платье для заявки', owner=self.user, price=2000,
            location='Москва', rental_start='2026-11-01', rental_end='2026-11-10',
            contact_info='123', status=ListingStatus.APPROVED, is_moderated=True
        )
        request = RentalRequest.objects.create(
            listing=target_listing,
            renter=self.user,
            start_date='2026-11-01',
            end_date='2026-11-05',
            quantity=1
        )
        self.assertEqual(request.status, 'pending')
        self.assertEqual(request.renter, self.user)
        logging.info("test_create_rental_request: PASS")

    def test_create_transaction(self):
        from listings.models import RentalRequest, Transaction, RequestStatus, TransactionStatus
        req = RentalRequest.objects.create(
            listing=self.user.listings.first() or Listing.objects.create(
                title='Для транзакции', owner=self.user, price=3000,
                location='Москва', rental_start='2026-12-01', rental_end='2026-12-10',
                contact_info='123', status='approved', is_moderated=True
            ),
            renter=self.user, start_date='2026-12-01', end_date='2026-12-10'
        )
        transaction = Transaction.objects.create(
            request=req,
            amount=3000.00,
            rental_start='2026-12-01',
            rental_end='2026-12-10',
            status=TransactionStatus.PAID
        )
        self.assertEqual(transaction.amount, 3000.00)
        self.assertEqual(transaction.status, 'paid')
        logging.info("test_create_transaction: PASS")

if __name__ == '__main__':
    unittest.main()
