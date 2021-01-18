from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # создание двух пользователей
        User = get_user_model()
        cls.user_author_1 = User.objects.create(username='testuser1')
        cls.user_author_2 = User.objects.create(username='testuser2')

        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-group',
                                         description='test-group-description')

        cls.post = Post.objects.create(text='Тестовая запись',
                                       author=cls.user_author_1,
                                       group=cls.group)

    def setUp(self):
        # Неавторизованный клиент
        self.guest_client = Client()
        # Создаем двух авторизованных клиентов
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.user_author_1)

        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_author_2)

    def test_urls_for_guest_users(self):
        """Проверяем доступность страниц для гостя."""
        urls = {
            '/': 200,
            '/group/test-group/': 200,
            '/about/author/': 200,
            '/about/tech/': 200,
            '/testuser2/1/edit/': 404,
            '/testuser2/1/comment': 302
        }
        for key, value in urls.items():
            response = self.guest_client.get(key)
            self.assertEqual(response.status_code, value)

    def test_urls_for_authorized_users(self):
        """Проверяем доступность страниц для авторизованного пользователя."""
        urls = {
            '/': 200,
            '/group/test-group/': 200,
            '/new/': 200,
            '/about/author/': 200,
            '/about/tech/': 200,
            '/testuser1/': 200,
            '/testuser1/1/': 200,
            '/testuser1/1/edit/': 200,
            '/testuser2/1/edit/': 404,
            '/testuser2/1/comment': 302,
        }
        for key, value in urls.items():
            response = self.authorized_client_1.get(key)
            self.assertEqual(response.status_code, value)

    def test_new_post_url_for_guest_users(self):
        """
        Тестирование URL для неавторизованных пользователей.
        Удостоверися, что редирект на sign up работает корректно.
        """
        response = self.guest_client.get(reverse('new_post'), follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_post_edit_url_for_another_authorized_users(self):
        """
        Тестирование URL для неавтора поста.
        Удостоверися, что редирект на post.html работает корректно.
        """
        response = self.authorized_client_2.get(reverse(
            'post_edit',
            kwargs={'username': 'testuser1',
                    'post_id': 1})
        )
        self.assertRedirects(response, '/testuser1/1/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        new_post = 'posts/new.html'
        edit_post = 'posts/new.html'

        templates_url_names = {
            'index.html': '/',
            'group.html': '/group/test-group/',
            new_post: '/new/',
            'posts/profile.html': '/testuser1/',
            'posts/post.html': '/testuser1/1/',
            edit_post: '/testuser1/1/edit/',
            'misc/404.html': '/404/',
        }
        for template, reverse_name in templates_url_names.items():
            with self.subTest():
                response = self.authorized_client_1.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_urls_not_found(self):
        """Проверяем возвращается ли код 404, если страница не найдена."""
        urls = {
            '/about/author/1': 404,
        }
        for key, value in urls.items():
            response = self.guest_client.get(key)
            self.assertEqual(response.status_code, value)

    def test_url_comment_post_guest_users(self):
        """Тестирование URL: Comment для гостей сайта"""
        response = self.guest_client.get(reverse('add_comment',
                                                 kwargs={
                                                     'username': 'testuser1',
                                                     'post_id': 1
                                                 }))
        self.assertRedirects(
            response, '/auth/login/?next=/testuser1/1/comment'
        )


# класс тестирования возврата кода 404
class CustomErrorHandlerTests(TestCase):

    @classmethod
    def setUp(self):
        # Неавторизованный клиент
        self.guest_client = Client()

    def test_handler_renders_template_response(self):
        response = self.guest_client.get('/bred/')
        self.assertEqual(response.status_code, 404)
