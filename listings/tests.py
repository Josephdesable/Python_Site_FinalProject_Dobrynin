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

if __name__ == '__main__':
    unittest.main()
