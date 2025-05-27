from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView
from .models import Vitima, Visita, Agressor
from .forms import VisitaForm, VitimaForm
from unidecode import unidecode
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
# Lista todas as vítimas


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'  # Template para a página de login
    redirect_authenticated_user = True  # Redireciona usuários já autenticados
    success_url = reverse_lazy('vitima-list')  
    
class VitimaListView(LoginRequiredMixin, ListView):
    model = Vitima
    template_name = 'vitima_list.html'
    context_object_name = 'vitimas'
    paginate_by = 10  # 🔹 Número de itens por página


    def get_queryset(self):
        queryset = super().get_queryset().order_by('-data_registro')
        search_query = self.request.GET.get('q', '').strip()
        municipio_filter = self.request.GET.get('municipio', '').strip()
        classificacao_filter = self.request.GET.get('classificacao', '').strip()
        status_filter = self.request.GET.get('status', '').strip()

        # Filtro para a busca de 'search_query' - Remover acentos e normalizar
        if search_query:
            search_query_normalized = unidecode(search_query.replace('_', ' ')).lower()
            queryset = queryset.filter(
                Q(nome_vitima__icontains=search_query_normalized) | 
                Q(cpf__icontains=search_query_normalized)
            )

        # Filtrando por municipio (com normalização no Python)
        if municipio_filter:
            municipio_filter_normalized = unidecode(municipio_filter.lower())
            queryset = [
                item for item in queryset
                if unidecode(item.municipio.lower()) == municipio_filter_normalized
            ]

        # Filtrando por 'classificacao' com a normalização
        if classificacao_filter:
            classificacao_filter_normalized = unidecode(classificacao_filter.replace('_', ' ')).lower()
            queryset = [
                item for item in queryset
                if unidecode(item.classificacao.lower()) == classificacao_filter_normalized
            ]

        # Filtrando por 'status' com a normalização
        if status_filter:
            status_filter_normalized = unidecode(status_filter.replace('_', ' ')).lower()
            queryset = [
                item for item in queryset
                if unidecode(item.situacao_visita.lower()) == status_filter_normalized
            ]

        return queryset


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mantendo os dados existentes para os filtros
        context.update({
            'municipios': Vitima.MUNICIPIOS_PE,
            'classificacoes': Vitima.CLASSIFICACAO_CHOICES,
            'status_options': [('ATIVA', 'Ativo'), ('INATIVA', 'Inativo')],
            'current_filters': self.request.GET.copy()  # 🔹 Para manter os filtros na paginação
        })
        return context

# Detalhes de uma vítima específica
class VitimaDetailView(LoginRequiredMixin, DetailView):
    model = Vitima
    template_name = 'vitima_detail.html'
    context_object_name = 'vitima'

# Editar uma vítima (CORRIGIDO)
class VitimaUpdateView(LoginRequiredMixin, UpdateView):
    model = Vitima
    form_class = VitimaForm  # 🔹 Usa o VitimaForm personalizado
    template_name = 'vitima_form.html'
    success_url = reverse_lazy('vitima-list')  # 🔹 Redireciona para a lista após salvar

# Excluir uma vítima
class VitimaDeleteView(LoginRequiredMixin, DeleteView):
    model = Vitima
    template_name = 'vitima_confirm_delete.html'
    success_url = reverse_lazy('vitima-list')

# Criar nova vítima
class VitimaCreateView(LoginRequiredMixin, CreateView):
    model = Vitima
    form_class = VitimaForm  # Use o formulário personalizado
    template_name = 'vitima_form.html'
    success_url = reverse_lazy('vitima-list')  # Redireciona após salvar
    
    def form_valid(self, form):
        # Adiciona uma mensagem de sucesso
        messages.success(self.request, 'Vítima cadastrada com sucesso!')
        return super().form_valid(form)

# ----------------- VISITAS -------------------

# Listar visitas de uma vítima específica
class VisitaListView(LoginRequiredMixin, ListView):
    model = Visita
    template_name = 'visita_list.html'
    context_object_name = 'visitas'

    def get_queryset(self):
        vitima = get_object_or_404(Vitima, pk=self.kwargs['pk'])
        return Visita.objects.filter(vitima=vitima)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vitima'] = get_object_or_404(Vitima, pk=self.kwargs['pk'])  # 🔹 Corrigido
        return context

# Detalhes de uma visita
class VisitaDetailView(LoginRequiredMixin, DetailView):
    model = Visita
    template_name = 'visita_detail.html'
    context_object_name = 'visita'

# Criar uma nova visita para uma vítima específica
class VisitaCreateView(LoginRequiredMixin, CreateView):
    model = Visita
    template_name = 'visita_form.html'
    form_class = VisitaForm  # 🔹 Usa o formulário personalizado

    def form_valid(self, form):
        vitima = get_object_or_404(Vitima, pk=self.kwargs['pk'])
        form.instance.vitima = vitima
        messages.success(self.request, 'Visita cadastrada com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        # Redireciona para a página de detalhes da vítima após salvar a visita
        return reverse_lazy('vitima-detail', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vitima'] = get_object_or_404(Vitima, pk=self.kwargs['pk'])
        return context

# Editar uma visita
class VisitaUpdateView(LoginRequiredMixin, UpdateView):
    model = Visita
    form_class = VisitaForm
    template_name = 'visita_form.html'

    def get_success_url(self):
        return reverse_lazy('visita-detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vitima'] = self.object.vitima
        return context

# Excluir uma visita
class VisitaDeleteView(LoginRequiredMixin, DeleteView):
    model = Visita
    template_name = 'visita_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('vitima-detail', kwargs={'pk': self.object.vitima.pk})

#view para agressor (no caso da vitima ter mais de um agressor)


# Lista todos os agressores de uma vítima
class AgressorListView(LoginRequiredMixin, ListView):
    model = Agressor
    template_name = 'vitima_detail.html'  # Usa o mesmo template da vítima
    context_object_name = 'agressores'

    def get_queryset(self):
        # Filtra os agressores pela vítima específica
        vitima_id = self.kwargs['pk']
        return Agressor.objects.filter(vitima_id=vitima_id)

    def get_context_data(self, **kwargs):
        # Adiciona a vítima ao contexto para usar no template
        context = super().get_context_data(**kwargs)
        context['vitima'] = Vitima.objects.get(pk=self.kwargs['pk'])
        return context

# Cria um novo agressor para uma vítima
class AgressorCreateView(LoginRequiredMixin, CreateView):
    model = Agressor
    fields = ['data_inicial_medida', 'data_final_medida', 'numero_processo', 'nome_agressor', 'parentesco', 'perfil_agressor', 'tipo_agressao', 'resumo_dos_fatos']
    template_name = 'agressor_form.html'

    def form_valid(self, form):
        # Associa o agressor à vítima antes de salvar
        form.instance.vitima_id = self.kwargs['pk']
        messages.success(self.request, 'Agressor cadastrado com sucesso!')
        return super().form_valid(form)

    def get_success_url(self):
        # Redireciona para a página de detalhes da vítima após salvar
        return reverse_lazy('vitima-detail', kwargs={'pk': self.kwargs['pk']})

# Edita um agressor existente
class AgressorUpdateView(LoginRequiredMixin, UpdateView):
    model = Agressor
    fields = ['data_inicial_medida', 'data_final_medida', 'numero_processo', 'nome_agressor', 'parentesco', 'perfil_agressor', 'tipo_agressao', 'resumo_dos_fatos']
    template_name = 'agressor_form.html'

    def get_success_url(self):
        # Redireciona para a página de detalhes da vítima após salvar
        return reverse_lazy('vitima-detail', kwargs={'pk': self.object.vitima.pk})

# Deleta um agressor
class AgressorDeleteView(LoginRequiredMixin, DeleteView):
    model = Agressor
    template_name = 'agressor_confirm_delete.html'

    def get_success_url(self):
        # Redireciona para a página de detalhes da vítima após deletar
        return reverse_lazy('vitima-detail', kwargs={'pk': self.object.vitima.pk})
    
class AgressorDetailView(LoginRequiredMixin, DetailView):
    model = Agressor
    template_name = 'agressor_detail.html'  # Nome do template para visualizar o agressor
    context_object_name = 'agressor'  # Nome do objeto no contexto do template    
