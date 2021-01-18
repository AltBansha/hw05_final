import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = get_user_model().objects.create(
            username='testuser'
        )

        Group.objects.bulk_create([
            Group(
                title=f'Тестовая группа {number}',
                slug=f'test-group{number}',
                description=f'Описание группы {number}',
            ) for number in range(1, 3)
        ])

        Post.objects.bulk_create([
            Post(
                text=f'Тестовая запись {number}',
                author=cls.user_author,
                group=Group.objects.get(pk=number),
            ) for number in range(1, 3)
        ])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group', kwargs={'slug': 'test-group1'}),
            'posts/new.html': reverse('new_post'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
            }
        )
    def test_context_in_index_page(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(response.context.get('page').object_list,
                         list(Post.objects.all()[:10]))

    def test_context_in_group_page(self):
        """ Тестирование содержания context в group"""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': 'test-group1'})
        )

        self.assertEqual(response.context.get('page').object_list,
                         list(Post.objects.all()[:1]))

    def test_context_in_new_post_page(self):
        """ Тестирование содержания context при создании поста"""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'profile',
            kwargs={'username': 'testuser'})
        )
        context_page = {
            'Тестовая запись 1': response.context.get('page')[0].text,
            'testuser': response.context.get('page')[0].author.username,
            'Тестовая группа 1': response.context.get('page')[0].group.title,
        }

        for value, expected in context_page.items():
            with self.subTest():
                self.assertEqual(value, expected)

    def test_context_in_edit_post_page(self):
        """Тестирование содержания context при редактировании поста"""
        response = self.authorized_client.get(
            reverse('post_edit',
                    kwargs={'username': 'testuser',
                            'post_id': 1}))

        context_edit_page = {
            'Тестовая запись 1': response.context.get('post').text,
            'Тестовая группа 1': response.context.get('post').group.title,
        }

        for value, expected in context_edit_page.items():
            with self.subTest():
                self.assertEqual(value, expected)

    def test_post_is_in_correct_group(self):
        """Тестирование на правильность назначения групп для постов."""
        # Проверим, что test-group1 сожержит только назначеный пост

        group = Group.objects.first()
        posts_out_of_group = Post.objects.exclude(group=group)
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': 'test-group1'})
        )
        posts_collection = set(posts_out_of_group)
        response_paginator = response.context.get('paginator').object_list
        self.assertTrue(posts_collection.isdisjoint(response_paginator))


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


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = get_user_model().objects.create(username='testuser')

        Post.objects.bulk_create([
            Post(
                text='Тестовая запись',
                author=cls.user_author,
            ) for number in range(13)
        ])

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_author)

    def test_first_page_contains_ten_records(self):
        """Проверяем, что первая страница содержит 10 постов."""
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_three_records(self):
        """Проверяем, что на второй странице только 3 поста."""
        response = self.authorized_client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)


# класс тестирования кеширования страниц
class CacheViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = get_user_model().objects.create(username='AuthorizedUser')

        Post.objects.bulk_create([Post(text=f'Test{i}', author=cls.user)
                                  for i in range(5)])
        cls.guest_user = Client()

    def test_index_cache(self):
        """Тестирование кеширования на странице Index"""
        response = self.guest_user.get(reverse('index'))
        Post.objects.bulk_create([Post(text=f'Test{i}', author=self.user)
                                  for i in range(3)])

        # Вычисление колличества записей context и колличества записей в базе
        context_cache_data_len = len(response.context.get('page').object_list)
        post_context_cache_len = Post.objects.count()

        # длина кеша должна отличаться от колличества записанных постов в базе
        self.assertNotEqual(context_cache_data_len, post_context_cache_len)
        # очистим кеш, запросим информация заново
        cache.clear()
        response = self.guest_user.get(reverse('index'))
        # вычислим длину
        context_len = len(response.context.get('page').object_list)
        post_len = Post.objects.count()
        # колличество записей должно совпадать
        self.assertEqual(context_len, post_len)


# класс тестирования подписи пользователей друг на друга
class FollowUserTest(TestCase):

    def setUp(self):
        User = get_user_model()
        # создадим 2х пользователей.
        self.auth_user = User.objects.create(username='FollowerUser')
        self.author_post = User.objects.create(username='AuthorUser')

        # создадим 2 записи на нашем сайте
        Post.objects.create(text='Тест',
                            author=self.author_post)

        Post.objects.create(text='Тест',
                            author=self.auth_user)

        # авторизуем подписчика
        self.auth_client_follower = Client()
        self.auth_client_follower.force_login(self.auth_user)

        # авторизуем владельца записи на нашем сайте
        self.auth_client_author = Client()
        self.auth_client_author.force_login(self.author_post)

    def test_authorized_user_follow_to_other_user(self):
        """Тестирование подписывания на пользователей"""
        self.auth_client_follower.post(
            reverse('profile_follow', kwargs={'username': self.author_post})
        )
        self.assertTrue(Follow.objects.filter(user=self.auth_user,
                                              author=self.author_post))

    def test_authorized_user_unfollow(self):
        """Тестирование отписывания от пользователей"""
        self.auth_client_follower.get(
            reverse('profile_unfollow', kwargs={'username': self.author_post})
        )

        self.assertFalse(Follow.objects.filter(user=self.auth_user,
                                               author=self.author_post))

    def test_post_added_to_follow(self):
        """Тестирование на правильность работы подписи на пользователя"""
        # подпишем пользователя на auth_client_author
        self.auth_client_follower.post(
            reverse('profile_follow', kwargs={'username': self.author_post})
        )
        # получим все посты подписанного пользователя
        posts = Post.objects.filter(author__following__user=self.auth_user)

        response_follower = self.auth_client_follower.get(
            reverse('follow_index')
        )
        response_author = self.auth_client_author.get(
            reverse('follow_index')
        )

        # проверим содержание Context страницы follow_index пользователя
        # auth_client_follower и убедимся, что они имеются в ленте
        self.assertIn(posts.get(),
                      response_follower.context['paginator'].object_list)

        # проверим содержание Context страницы follow_index пользователя
        # auth_client_author и убедимся, что записи в ленте не имеется
        self.assertNotIn(posts.get(),
                         response_author.context['paginator'].object_list)


# Класс тестирования постов содержащих в себе изобращение
class PostImageViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.small_jpg = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                         b'\x01\x00\x80\x00\x00\x00\x00\x00'
                         b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                         b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                         b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                         b'\x0A\x00\x3B'
                         )

        cls.uploaded = SimpleUploadedFile(
            name='small.jpg',
            content=cls.small_jpg,
            content_type='image/jpg'
        )
        cls.user = get_user_model().objects.create(username='testuser')

        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-group')
        cls.post = Post.objects.create(text='Тестовая запись',
                                       group=cls.group,
                                       author=cls.user,
                                       image=cls.uploaded)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.auth_client_author = Client()
        self.auth_client_author.force_login(self.user)

    def test_context_index_page(self):
        """Проверяем context страницы index на наличие изображения"""
        response = self.guest_client.get(reverse('index'))
        response_data_image = response.context['page'][0].image
        expected = f'posts/{self.uploaded.name}'

        self.assertEqual(response_data_image, expected)

    def test_context_profile_page(self):
        """Проверяем context страницы profile на наличие изображения"""
        response = self.guest_client.get(
            reverse('profile', kwargs={'username': self.user})
        )

        response_data_image = response.context['page'][0].image
        expected = f'posts/{self.uploaded.name}'

        self.assertEqual(response_data_image, expected)

    def test_context_group_page(self):
        """Проверяем context страницы group на наличие изображения"""
        response = self.guest_client.get(
            reverse('group', kwargs={'slug': 'test-group'})
        )
        response_data_image = response.context['page'][0].image
        expected = f'posts/{self.uploaded.name}'

        self.assertEqual(response_data_image, expected)

    def test_context_post_page(self):
        """Проверяем context страницы post на наличие изображения"""
        response = self.guest_client.get(
            reverse('post', kwargs={'username': self.user,
                                    'post_id': self.post.pk})
        )

        response_data_image = response.context['post'].image
        expected = f'posts/{self.uploaded.name}'

        self.assertEqual(response_data_image, expected)
