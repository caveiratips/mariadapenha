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
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.db.models import Count
import pandas as pd
from unidecode import unidecode
from datetime import datetime
import re

def get_choice_key(choices, value, default=None):
    """Função auxiliar para encontrar a chave de uma 'choice' a partir do seu valor de exibição."""
    if pd.isna(value) or not isinstance(value, str):
        return default
    
    value_normalized = unidecode(value.strip().lower())
    for key, display_value in choices:
        if unidecode(display_value.lower()) == value_normalized:
            return key
    return default

def clean_float(value):
    """Extrai um valor float de uma string, mesmo que contenha caracteres extras."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Usa regex para encontrar o primeiro número que parece um float/int
        match = re.search(r'-?\d+\.?\d*', value)
        if match:
            return float(match.group(0))
    return None

@login_required
def importar_dados_view(request):
    if request.method == 'POST':
        if 'excel_file' not in request.FILES:
            messages.error(request, "Nenhum arquivo foi enviado.")
            return render(request, 'importar_dados.html')

        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            messages.error(request, f"Erro ao ler o arquivo Excel: {e}")
            return render(request, 'importar_dados.html')

        vítimas_criadas = 0
        visitas_criadas = 0
        erros = []

        for index, row in df.iterrows():
            try:
                # --- Validação e Limpeza de Dados ---
                numero_processo_raw = row.iloc[3]
                if pd.isna(numero_processo_raw):
                    erros.append(f"Linha {index + 2}: Número do processo está vazio.")
                    continue
                
                # Limpeza rigorosa do número do processo para garantir unicidade
                numero_processo = re.sub(r'\D', '', str(numero_processo_raw))
                if not numero_processo:
                    erros.append(f"Linha {index + 2}: Número do processo inválido após limpeza.")
                    continue

                # Validação de data
                try:
                    data_visita = pd.to_datetime(row.iloc[14]).date()
                except (ValueError, pd.errors.OutOfBoundsDatetime):
                    erros.append(f"Linha {index + 2}: Formato de data inválido ('{row.iloc[14]}').")
                    continue

                # --- Lógica Principal com update_or_create ---
                vitima_situacao_choices = [('ATIVA', 'Ativa'), ('INATIVA', 'Inativa')] # Mantido para compatibilidade com get_choice_key
                
                # Dados que serão usados para criar ou ATUALIZAR a vítima
                vitima_defaults = {
                    'latitude': clean_float(row.iloc[1]),
                    'longitude': clean_float(row.iloc[2]),
                    'municipio': get_choice_key(Vitima.MUNICIPIOS_PE, row.iloc[4], default='AFOGADOS DA INGAZEIRA'),
                    'bairro': str(row.iloc[5]),
                    'rua': str(row.iloc[6]),
                    'zona': get_choice_key(Vitima.ZONA_CHOICES, row.iloc[7], default='U'),
                    'estado': 'Pernambuco',
                    'nome_vitima': str(row.iloc[9]).strip(),
                    'parentesco': get_choice_key(Vitima.PARENTESCO_CHOICES, row.iloc[10], default='OUTRO'),
                    'perfil_vitima': get_choice_key(Vitima.PERFIL_VITIMA_CHOICES, row.iloc[11], default='NAO_INFORMADO'),
                    'cpf': str(row.iloc[12]),
                    'data': data_visita,
                    'nome_agressor': str(row.iloc[15]),
                    'perfil_agressor': get_choice_key(Vitima.PERFIL_AGRESSOR_CHOICES, row.iloc[16], default='NAO_INFORMADO'),
                    'historico': str(row.iloc[17]),
                    'classificacao': get_choice_key(Vitima.CLASSIFICACAO_CHOICES, row.iloc[18], default='MÉDIO'),
                    'tipo_agressao': get_choice_key(Vitima.TIPO_AGRESSÃO_CHOICES, row.iloc[19], default='FISICA'),
                    'situacao_visita': get_choice_key(vitima_situacao_choices, row.iloc[20], default='ATIVA')
                }

                vitima, created = Vitima.objects.update_or_create(
                    numero_processo=numero_processo,
                    defaults=vitima_defaults
                )

                if created:
                    vítimas_criadas += 1
                
                # --- Cria a Visita associada ---
                classificacao_visita = get_choice_key(Visita.CLASSIFICACAO_CHOICES, row.iloc[18], default='MÉDIO')
                
                Visita.objects.create(
                    vitima=vitima,
                    data=data_visita,
                    situacao=get_choice_key(Visita.SITUACAO_CHOICES, row.iloc[20], default='ATIVA'),
                    classificacao=classificacao_visita,
                    historico=str(row.iloc[17])
                )
                visitas_criadas += 1

            except Exception as e:
                erros.append(f"Linha {index + 2}: {e}")

        # --- Feedback para o Usuário ---
        if vítimas_criadas > 0 or visitas_criadas > 0:
            messages.success(request, f"Importação concluída! {vítimas_criadas} vítimas novas criadas e {visitas_criadas} visitas adicionadas.")
        if erros:
            messages.warning(request, f"Ocorreram {len(erros)} erros durante a importação. Detalhes: " + " | ".join(erros))
        if vítimas_criadas == 0 and visitas_criadas == 0 and not erros:
            messages.info(request, "Nenhum dado novo foi importado. O arquivo pode estar vazio ou as vítimas já existiam.")

    return render(request, 'importar_dados.html')

@login_required
def dashboard_view(request):
    total_vitimas = Vitima.objects.count()
    total_visitas = Visita.objects.count()

    # Agregações
    classificacao_counts = Vitima.objects.values('classificacao').annotate(total=Count('classificacao')).order_by('-total')
    situacao_counts = Vitima.objects.values('situacao_visita').annotate(total=Count('situacao_visita')).order_by('-total')
    agressor_preso_counts = Vitima.objects.values('agressor_preso').annotate(total=Count('agressor_preso')).order_by('-total')

    # Calcula porcentagens
    for item in classificacao_counts:
        item['percentual'] = (item['total'] / total_vitimas * 100) if total_vitimas > 0 else 0
    
    for item in situacao_counts:
        item['percentual'] = (item['total'] / total_vitimas * 100) if total_vitimas > 0 else 0

    for item in agressor_preso_counts:
        item['percentual'] = (item['total'] / total_vitimas * 100) if total_vitimas > 0 else 0

    context = {
        'total_vitimas': total_vitimas,
        'total_visitas': total_visitas,
        'classificacao_counts': classificacao_counts,
        'situacao_counts': situacao_counts,
        'agressor_preso_counts': agressor_preso_counts,
    }
    return render(request, 'dashboard.html', context)

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
        
        agressor_preso_status = form.cleaned_data.get('agressor_preso')
        if agressor_preso_status and vitima.agressor_preso != agressor_preso_status:
            vitima.agressor_preso = agressor_preso_status
            vitima.save(update_fields=['agressor_preso'])
            
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

    def form_valid(self, form):
        agressor_preso_status = form.cleaned_data.get('agressor_preso')
        vitima = self.object.vitima
        if agressor_preso_status and vitima.agressor_preso != agressor_preso_status:
            vitima.agressor_preso = agressor_preso_status
            vitima.save(update_fields=['agressor_preso'])

        messages.success(self.request, 'Visita atualizada com sucesso!')
        return super().form_valid(form)

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
