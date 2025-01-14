from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.urls import reverse
from . forms import BookReviewForm
from . import models


def index(request):
    book_count = models.Book.objects.count()
    book_instance_count = models.BookInstance.objects.count()
    available_bi_count = models.BookInstance.objects.filter(status='a').count()
    author_count = models.Author.objects.count()
    request.session['visit_count'] = request.session.get('visit_count', 0) + 1
    return render(request, 'library/index.html', {
        'book_count': book_count,
        'book_instance_count': book_instance_count,
        'available_bi_count': available_bi_count,
        'author_count': author_count,
    })


def authors(request):
    queryset = models.Author.objects
    query = request.GET.get('search')
    if query:
        queryset = queryset.filter(
            Q(first_name__istartswith=query) | Q(last_name__istartswith=query)
        )
    paginator = Paginator(queryset.all(), 4)
    page_number = request.GET.get('page')
    authors = paginator.get_page(page_number)
    return render(request, 'library/authors.html', {
        'authors': authors,
    })

def author(request, author_id):
    author = get_object_or_404(models.Author, id=author_id)
    return render(request, 'library/author.html', {
        'author': author,
    })


class BookListView(generic.ListView):
    model = models.Book
    paginate_by = 6
    template_name = 'library/book_list.html'

    def get_queryset(self):
        qs =  super().get_queryset()
        genre_id = self.request.GET.get('genre_id')
        if genre_id:
            qs = qs.filter(genre=genre_id)
        query = self.request.GET.get('search')
        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(author__last_name__startswith=query)
            )
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        genres = models.Genre.objects.all()
        context.update({'genres': genres})
        genre_id = self.request.GET.get('genre_id')
        if genre_id:
            genre = get_object_or_404(models.Genre, id=genre_id)
            context.update({'current_genre': genre})
        return context


class BookDetailView(generic.edit.FormMixin, generic.DetailView):
    model = models.Book
    template_name = 'library/book_detail.html'
    form_class = BookReviewForm

    def get_success_url(self) -> str:
        return reverse('book', kwargs={'pk': self.get_object().id})

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        
    def get_initial(self):
        initial = super().get_initial()
        initial['book'] = self.get_object()
        initial['reviewer'] = self.request.user
        return initial
    
    def form_valid(self, form):
        form.instance.book = self.object
        form.instance.reviewer = self.request.user
        form.save()
        messages.success(self.request, 'Review posted successfully')
        return super().form_valid(form)


class UserBookInstnceListView(LoginRequiredMixin, generic.ListView):
    model = models.BookInstance
    template_name = 'library/user_bookinstance_list.html'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(reader=self.request.user)
        return qs
