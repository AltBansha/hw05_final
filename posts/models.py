from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField('Заголовок',
                             max_length=200,
                             help_text='Укажите заголовок')
    slug = models.SlugField(unique=True,
                            max_length=100)
    description = models.TextField('Описание',
                                   max_length=400,
                                   help_text='Описание группы. '
                                             'Не более 400 символов.')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Текст записи',
                            help_text='Укажите текст Вашей записи.')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="posts")
    group = models.ForeignKey(Group,
                              verbose_name='Название группы',
                              on_delete=models.SET_NULL,
                              related_name="posts",
                              blank=True,
                              null=True,
                              help_text=('Выберете группу, в которой хотите '
                                         'опубликовать Вашу запись.'))
    image = models.ImageField('Изображение',
                              upload_to='posts/',
                              blank=True,
                              null=True)

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments',)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField(verbose_name="Поле для комментария",
                            help_text='Ваш комментарий')
    created = models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             blank=False,
                             null=False,
                             related_name="follower")
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="following")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "author"],
                                    name="unique_follow")
        ]

    def __str__(self):
        return self.author.username
