from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)
from django.utils import timezone
from django.contrib.auth import get_user_model


from .forms import PostForm, CommentForm, ProfileForm
from .models import Category, Post, Comment
from blog.constants import POSTS_ON_CATEGORY

User = get_user_model()

POSTS_PER_PAGE = 10
POSTS_ON_INDEX = 10


def get_posts_queryset():
    return Post.objects.select_related(
        "author",
        "category",
        "location",
    ).filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
    )


def index(request):
    post_list = get_posts_queryset().order_by("-pub_date")
    paginator = Paginator(post_list, POSTS_ON_INDEX)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "blog/index.html",
        {
            "page_obj": page_obj,
            "posts": page_obj,
        },
    )


def category_posts(request, slug):
    category = get_object_or_404(
        Category,
        slug=slug,
        is_published=True,
    )

    posts_qs = (
        get_posts_queryset().filter(category=category).order_by("-pub_date")
    )

    paginator = Paginator(posts_qs, POSTS_ON_CATEGORY)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "category": category,
        "page_obj": page_obj,
        "posts": page_obj,
    }
    return render(request, "blog/category.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    user_is_author = request.user == post.author
    now = timezone.now()

    if not post.is_published and not user_is_author:
        raise Http404("Пост не найден")

    if not post.category.is_published and not user_is_author:
        raise Http404("Пост не найден")

    if post.pub_date > now and not user_is_author:
        raise Http404("Пост не найден")

    comment_form = CommentForm()

    return render(
        request,
        "blog/detail.html",
        {
            "post": post,
            "comment_form": comment_form,
        },
    )


@login_required
def create_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("blog:profile", username=request.user.username)

    return render(request, "blog/create.html", {"form": form})


def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    user = request.user
    if not user.is_authenticated:
        return redirect("login")
    if post.author != request.user:
        return redirect("blog:post_detail", post_id=post.pk)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )

    if form.is_valid():
        form.save()
        return redirect("blog:post_detail", post_id=post.pk)

    return render(
        request,
        "blog/create.html",
        {
            "form": form,
            "post": post,
            "is_edit": True,
        },
    )


def edit_profile(request, username):
    if request.user.username != username:
        return redirect("blog:profile", username=username)

    form = ProfileForm(request.POST or None, instance=request.user)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("blog:profile", username=username)

    return render(request, "blog/edit_profile.html", {"form": form})


def profile(request, username):
    user = get_object_or_404(User, username=username)

    if request.user == user:
        post_list = (
            Post.objects.select_related(
                "author",
                "category",
                "location",
            )
            .filter(author=user)
            .order_by("-pub_date")
        )
    else:
        post_list = (
            Post.objects.select_related(
                "author",
                "category",
                "location",
            )
            .filter(
                author=user,
                is_published=True,
                pub_date__lte=timezone.now(),
                category__is_published=True,
            )
            .order_by("-pub_date")
        )

    paginator = Paginator(post_list, POSTS_ON_INDEX)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "profile": user,
        "page_obj": page_obj,
        "posts": page_obj,
    }
    return render(request, "blog/profile.html", context)


def add_comment(request, post_id):
    post = get_object_or_404(
        Post,
        pk=post_id,
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
    )

    if not request.user.is_authenticated:
        return redirect("login")

    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect("blog:post_detail", post_id=post_id)

    return render(
        request,
        "blog/comment.html",
        {
            "form": form,
            "post": post,
        },
    )


def edit_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user != comment.author:
        return redirect("blog:post_detail", post_id=post_id)

    form = CommentForm(request.POST or None, instance=comment)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("blog:post_detail", post_id=post.id)

    return render(
        request,
        "blog/edit_comment.html",
        {"form": form, "comment": comment, "post": post},
    )


def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    # Только автор может удалять
    if request.user != post.author:
        raise Http404("Пост не найден")

    if request.method == "POST":
        post.delete()
        return redirect("blog:index")

    # GET — показать подтверждение удаления
    return render(request, "blog/delete.html", {"post": post})


def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user != comment.author:
        return redirect("blog:post_detail", post_id=post_id)

    if request.method == "POST":
        comment.delete()
        return redirect("blog:post_detail", post_id=post_id)

    return render(
        request,
        "blog/delete_comment.html",
        {"comment": comment, "post_id": post_id},
    )
