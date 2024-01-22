from django.conf import settings
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Count
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from taggit.models import Tag

from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post
from django.shortcuts import render, get_object_or_404


# class PostListView(ListView):
#     model = Post
#     context_object_name = "posts"
#     paginate_by = 3
#     template_name = "blog/post/list.html"


def post_list(request, tag_slug=None):
    posts_list = Post.published.all()

    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts_list = posts_list.filter(tags__in=[tag])

    paginator = Paginator(posts_list, 3)
    page_number = request.GET.get('page', 1)
    posts = paginator.get_page(page_number)
    return render(request,
                  'blog/post/list.html',
                  {'posts': posts,
                   "tag": tag})


def post_detail(request, year, month, day, post):
    single_post = get_object_or_404(
        Post,
        status=Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day,
    )

    comments = single_post.comments.filter(active=True)
    form = CommentForm()

    post_tags_ids = single_post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=single_post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(request, "blog/post/detail.html", {"post": single_post,
                                                     "comments": comments,
                                                     "form": form,
                                                     "similar_posts": similar_posts})


def post_share(request, post_id):
    # Извлечь пост по его идентификатору id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False

    if request.method == "POST":
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())

            subject = f"{cd['name']} recommends you read {post.title}"
            message = (
                f"Read {post.title} at {post_url}\n\n"
                f"{cd['name']}'s ({cd['email']}) comments: {cd['comments']}"
            )
            send_mail(subject, message, settings.EMAIL_HOST_USER, [cd["to"]])
            sent = True
    else:
        form = EmailPostForm()
    return render(
        request, "blog/post/share.html", {"post": post, "form": form, "sent": sent}
    )


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    comment_post = request.POST.copy()

    if request.user.is_authenticated:
        comment_post['name'] = request.user.username
        comment_post['email'] = request.user.email

    form = CommentForm(data=comment_post)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    return render(
        request,
        "blog/post/comment.html",
        {"post": post, "form": form, "comment": comment},
    )


def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + \
                            SearchVector('body', weight='B')

            search_query = SearchQuery(query)
            results = Post.published.annotate(search=search_vector,
                                              rank=SearchRank(search_vector, search_query)
                                              ).filter(search=query).order_by('-rank')

    return render(request, 'blog/post/search.html', {'form': form, 'query': query, 'results': results})
