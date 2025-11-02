from django.urls import path
from . import views

urlpatterns = [
    path('', views.BookListView.as_view(), name='book-list'),
    path('create/', views.BookCreateView.as_view(), name='book-create'),
    path('search/', views.BookSearchView.as_view(), name='book-search'),
    path('<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('<int:pk>/update/', views.BookUpdateView.as_view(), name='book-update'),
    path('<int:pk>/delete/', views.BookDeleteView.as_view(), name='book-delete'),
]