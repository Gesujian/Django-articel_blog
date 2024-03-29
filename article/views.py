from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from django.conf import settings

from .models import ArticleColumn, ArticlePost, Comment
from .forms import ArticleColumnForm, ArticlePostForm, CommentForm

import redis


r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


# Create your views here.
@login_required(login_url='/account/login/')
@csrf_exempt
def article_column(request):
    if request.method == "GET":
        columns = ArticleColumn.objects.filter(user=request.user)
        column_form = ArticleColumnForm()
        return render(request, 'article/column/article_column.html', 
                      {'columns': columns, 
                       'column_form': column_form
                      })
    if request.method == "POST":
        column_name = request.POST["column"]
        columns = ArticleColumn.objects.filter(user_id=request.user.id, 
                                               column=column_name)
        if columns:
            return HttpResponse("2")
        else:
            ArticleColumn.objects.create(user=request.user, column=column_name)
            return HttpResponse("1")


@login_required(login_url='/account/login/')
@require_POST
@csrf_exempt
def delete_column(request):
    column_id = request.POST['column_id']
    try:
        line = ArticleColumn.objects.get(id=column_id)
        line.delete()
        return HttpResponse("1")
    except:
        return HttpResponse("0")
    
    
@login_required(login_url='/account/login/')
@require_POST
@csrf_exempt
def rename_article_column(request):
    column_name = request.POST['column_name']
    column_id = request.POST['column_id']
    columns = ArticleColumn.objects.filter(user_id=request.user.id, 
                                           column=column_name)
    if columns:
        return HttpResponse("2")
    else:
        try:
            line = ArticleColumn.objects.get(id=column_id)
            line.column = column_name
            line.save()
            return HttpResponse("1")
        except:
            return HttpResponse("0")
    
    
@login_required(login_url='/account/login/')
@csrf_exempt
def article_post(request):
    if request.method == "POST":
        article_post_form = ArticlePostForm(data=request.POST)
        if article_post_form.is_valid():
            cd = article_post_form.cleaned_data
            try:
                new_article = article_post_form.save(commit=False)
                new_article.author = request.user
                new_article.column = request.user.article_column.get(id=request.POST['column_id'])
                new_article.save()
                return HttpResponse("1")
            except:
                return HttpResponse("2")
        else:
            return HttpResponse("3")
    else:
        article_post_form = ArticlePostForm()
        article_columns = request.user.article_column.all()
        return render(request, "article/column/article_post.html", 
                      {"article_post_form": article_post_form,
                       "article_columns": article_columns})


@login_required(login_url='/account/login/')
def article_list(request):
    articles_list = ArticlePost.objects.filter(author=request.user)
    paginator = Paginator(articles_list, 10)  # 规定每页最多4个
    page = request.GET.get("page")
    total_page = range(1, paginator.num_pages+1)
    try:
        current_page = paginator.page(page)
        articles = current_page.object_list
    except PageNotAnInteger:
        current_page = paginator.page(1)
        articles = current_page.object_list
    except EmptyPage:
        current_page = paginator.page(paginator.num_pages)
        articles = current_page.object_list
    
    return render(request, "article/column/article_list.html", 
                    {"articles":articles, 
                     "page":current_page,
                     "total_page":total_page})
    
    
@login_required(login_url='/account/login/')
def article_detail(request, id, slug):
    article = get_object_or_404(ArticlePost, id=id, slug=slug)
    return render(request, "article/column/article_detail.html", {"article":article})


def list_article_detail(request, id, slug):
    article = get_object_or_404(ArticlePost, id=id, slug=slug)
    total_views = r.incr("article:{}:views".format(article.id))
    r.zincrby('article_ranking', value=article.id, amount=1)
    
    article_ranking = r.zrange('article_ranking', 0, -1,desc=True)[:10]
    article_ranking_ids = [int(id) for id in article_ranking]
    most_viewed = list(ArticlePost.objects.filter(id__in=article_ranking_ids))
    most_viewed.sort(key=lambda x: article_ranking_ids.index(x.id))
    
    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.article = article
            new_comment.save()
    else:
        comment_form = CommentForm()
            
    return render(request, "article/list/list_article_detail.html", 
                    {"article":article,
                     "total_views":total_views,
                     "most_viewed":most_viewed,
                     "comment_form":comment_form})


                
@login_required(login_url='/account/login/')
@require_POST
@csrf_exempt
def delete_article(request):
    article_id = request.POST['article_id']
    try:
        article = ArticlePost.objects.get(id=article_id)
        article.delete()
        return HttpResponse("1")
    except:
        return HttpResponse("2")
        
        
@login_required(login_url='/account/login/')
@csrf_exempt
def redit_article(request, article_id):
    if request.method == "GET":
        article_columns = request.user.article_column.all()
        article = ArticlePost.objects.get(id=article_id)
        this_article_form = ArticlePostForm(initial={"title": article.title})
        this_article_column = article.column
        print(this_article_column)
        return render(request, "article/column/redit_article.html",
                      {
                        "article": article,
                        "article_columns": article_columns,
                        "this_article_column": this_article_column,
                        "this_article_form": this_article_form
                        
                      })
    if request.method == "POST":
        redit_article = ArticlePost.objects.get(id=article_id)
        try:
            redit_article.column = request.user.article_column.get(id=request.POST["column_id"])
            redit_article.title = request.POST["title"]
            redit_article.body = request.POST["body"]
            redit_article.save()
            return HttpResponse("1")
        except:
            return HttpResponse("2")
            

def article_titles(request, username=None):
    if username:
        user = User.objects.get(username=username)
        article_titles =ArticlePost.objects.filter(author=user)
        try:
            userinfo = user.userinfo
        except:
            userinfo = None
    else:
        article_titles = ArticlePost.objects.all()
        userinfo = None
    paginator = Paginator(article_titles, 10)
    page = request.GET.get('page')
    total_page = range(1, paginator.num_pages+1)
    try:
        current_page = paginator.page(page)
        articles = current_page.object_list
    except PageNotAnInteger:
        current_page = paginator.page(1)
        articles = current_page.object_list
    except EmptyPage:
        current_page = paginator.page(paginator.num_pages)
        articles = current_page.object_list
    return render(request, "article/column/article_titles.html",                      
                    {"articles":articles, 
                     "page":current_page, 
                     "total_page":total_page, 
                     "userinfo":userinfo
                    })


@login_required(login_url='/account/login/')
@require_POST
@csrf_exempt
def like_article(request):
    article_id = request.POST.get("id")
    action = request.POST.get("action")
    if article_id and action:
        try:
            article = ArticlePost.objects.get(id=article_id)
            if action == "like":
                article.users_like.add(request.user)
                return HttpResponse("1")
            else:
                article.users_like.remove(request.user)
                return HttpResponse("2")
        except:
            return HttpResponse("no")
            


