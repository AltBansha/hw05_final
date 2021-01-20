from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    post_list = Post.objects.select_related("group")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {
            "page": page,
            "post_list": post_list,
            "paginator": paginator
        }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 12)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html", {
            "page": page,
            "group": group,
            "posts": posts,
            "paginator": paginator,
        }
    )


def group_list(request):
    groups = Group.objects.all()
    return render(request, "posts/group_list.html", {"groups": groups})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'GET' or not form.is_valid():
        return render(request, "posts/new.html", {"form": form})

    post = form.save(commit=False)
    post.author = request.user
    form.save()
    return redirect("index")


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    post_count = post_list.count()
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    following = (
        request.user.is_authenticated and
        Follow.objects.filter(
            author=author, user=request.user
        ).exists()
    )

    context = {"page": page,
               "author": author,
               "post_count": post_count,
               "paginator": paginator,
               "following": following}
    return render(request, "posts/profile.html", context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    count = Post.objects.filter(author=post.author).count()
    comments = post.comments.all()
    form = CommentForm()
    context = {
        "post": post,
        "author": post.author,
        "count": count,
        "form": form,
        "comments": comments,
    }
    return render(request, "posts/post.html", context)


def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect("post", username=username, post_id=post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if request.method == 'POST' and form.is_valid():
        post = form.save()
        return redirect("post", username=username,
                        post_id=post_id)

    return render(request, "posts/new.html", {"form": form,
                                              "post": post,
                                              "is_edit": True})


@login_required()
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)

    if not form.is_valid():
        return redirect("post", username, post_id)

    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    form.save()

    return redirect("post", username, post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "posts/follow.html",
        {
            "page": page,
            "paginator": paginator
        }
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)

    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("profile", username=username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
