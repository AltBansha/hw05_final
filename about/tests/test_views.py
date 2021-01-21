from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):

    def setUp(self):
        self.guest_user = Client()

    def test_templates_static_pages(self):
        """Тестирование шаблонов для статических страниц """
        templates_url_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }

        for template, reverse_name in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_user.get(reverse_name)
                self.assertTemplateUsed(response, template)
