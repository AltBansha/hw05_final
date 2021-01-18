from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


class NewPost_FormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create(username='testuser')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-group',
                                         description='Описание')
        # создадим авторизованного пользователя
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.form_data = {
            'text': 'Тестовая запись',
            'group': cls.group.id
        }

    def test_forms_new_post(self):
        """Тестируем форму новых сообщений на странице New_Post"""

        response = self.authorized_client.post(
            reverse('new_post'),
            data=self.form_data,
            follow=True
        )
        # проверяем правильность redirect после создания нового поста
        self.assertRedirects(response, reverse('index'))

    def test_form_new_post_saved(self):
        """Проверяем, что пост сохранился в базе."""

        self.authorized_client.post(
            reverse('new_post'),
            data=self.form_data,
            follow=True
        )

        self.assertEqual(Post.objects.last().text,
                         NewPost_FormTest.form_data['text'])


class PostEdit_FormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create(username='testuser')

        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-group',
                                         description='Описание')

        cls.post = Post.objects.create(text='Тестовая запись_кусь',
                                       author=cls.user,
                                       group=cls.group)

        # создадим авторизованного пользователя
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.form_data = {
            'text': 'Тестовая запись_брысь',
            'group': cls.group.id
        }

    def test_forms_post_edit(self):
        """Тестируем форму исправления сообщений на странице New_Post"""

        response = self.authorized_client.post(
            reverse('post_edit',
                    kwargs={'username': 'testuser',
                            'post_id': '1'}),
            data=PostEdit_FormTest.form_data,
            follow=True
        )

        self.assertEqual(response.context['post'].text,
                         PostEdit_FormTest.form_data['text'])
