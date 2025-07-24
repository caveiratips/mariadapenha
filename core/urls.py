from django.urls import path
from django.contrib.auth.views import LogoutView

from .views import (
    VitimaListView, VitimaDetailView, VitimaUpdateView, VitimaDeleteView, VitimaCreateView,
    VisitaListView, VisitaDetailView, VisitaUpdateView, VisitaDeleteView, VisitaCreateView,
    AgressorListView, AgressorCreateView, AgressorUpdateView, AgressorDeleteView, AgressorDetailView, CustomLoginView
)
from .views import importar_dados_view, excluir_tudo_view

urlpatterns = [
    # Home (redirecionando para a lista de vítimas)
    path('', VitimaListView.as_view(), name='home'),
    
    # Rotas para Vítimas
    path('vitimas/', VitimaListView.as_view(), name='vitima-list'),
    path('vitimas/<int:pk>/', VitimaDetailView.as_view(), name='vitima-detail'),
    path('vitimas/editar/<int:pk>/', VitimaUpdateView.as_view(), name='vitima-edit'),
    path('vitimas/excluir/<int:pk>/', VitimaDeleteView.as_view(), name='vitima-delete'),
    path('vitimas/nova/', VitimaCreateView.as_view(), name='vitima-create'),

    # Rotas para Visitas
    path('vitimas/<int:pk>/visitas/', VisitaListView.as_view(), name='visita-list'),
    path('visitas/<int:pk>/', VisitaDetailView.as_view(), name='visita-detail'),
    path('visitas/editar/<int:pk>/', VisitaUpdateView.as_view(), name='visita-edit'),
    path('visitas/excluir/<int:pk>/', VisitaDeleteView.as_view(), name='visita-delete'),
    path('vitimas/<int:pk>/visitas/nova/', VisitaCreateView.as_view(), name='visita-create'),
    path('vitima/<int:pk>/agressores/', AgressorListView.as_view(), name='agressor-list'),

    # Cria um novo agressor para uma vítima
    path('vitima/<int:pk>/agressor/create/', AgressorCreateView.as_view(), name='agressor-create'),
    # Edita um agressor existente
    path('agressor/<int:pk>/edit/', AgressorUpdateView.as_view(), name='agressor-edit'),
    # Deleta um agressor
    path('agressor/<int:pk>/delete/', AgressorDeleteView.as_view(), name='agressor-delete'),
    path('agressor/<int:pk>/', AgressorDetailView.as_view(), name='agressor-detail'),
    
    #pagina de login
    path('login/', CustomLoginView.as_view(), name='login'),
    
    path('logout/', LogoutView.as_view(), name='logout'),
    
]
urlpatterns += [
    path('importar/', importar_dados_view, name='importar_dados'),
    path('excluir-tudo/', excluir_tudo_view, name='excluir_tudo'),
]
