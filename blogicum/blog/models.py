from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class PublishedModel(models.Model):
    """Абстрактная модель — публикация + дата создания."""

    is_published = models.BooleanField(
        default=True,
        verbose_name="Опубликовано",
        help_text="Снимите галочку, чтобы скрыть публикацию.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Добавлено",
    )

    class Meta:
        abstract = True


class Category(PublishedModel):
    title = models.CharField(max_length=256, verbose_name="Заголовок")
    slug = models.SlugField(
        unique=True,
        verbose_name="Идентификатор",
        help_text="Разрешены латиница, цифры, дефис и подчёркивание.",
    )
    description = models.TextField(verbose_name="Описание")

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "Категории"
        ordering = ("title",)

    def __str__(self):
        return self.title[:30]


class Location(PublishedModel):
    name = models.CharField(max_length=256, verbose_name="Название места")

    class Meta:
        verbose_name = "местоположение"
        verbose_name_plural = "Местоположения"
        ordering = ("name",)

    def __str__(self):
        return self.name[:30]


class Post(PublishedModel):
    image = models.ImageField(upload_to="posts_images/", blank=True, null=True)
    title = models.CharField(max_length=256, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст")
    pub_date = models.DateTimeField(
        verbose_name="Дата и время публикации",
        help_text=(
            "Если установить дату в будущем — можно делать "
            "отложенные публикации."
        ),
        default=timezone.now,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор публикации",
        related_name="posts",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name="Категория",
        related_name="posts",
        null=True,
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        verbose_name="Местоположение",
        related_name="posts",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "публикация"
        verbose_name_plural = "Публикации"
        ordering = ("-pub_date",)

    def __str__(self):
        return self.title[:30]


class Comment(models.Model):
    text = models.TextField("Текст комментария")
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Публикация",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Комментарий от {self.author} к посту {self.post}"
