from django import forms
from .models import Visita, Vitima, Agressor  # 🔹 Importando corretamente apenas o modelo
from unidecode import unidecode

class VisitaForm(forms.ModelForm):
    agressor_preso = forms.ChoiceField(
        choices=Vitima.AGRESSOR_PRESO_CHOICES,
        required=False,
        label='Agressor Preso?',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Visita
        fields = ['data', 'historico', 'classificacao', 'situacao', 'descumprimento_medida', 'mike', 'desfecho']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'format': 'Y-m-d'}),
            'historico': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'classificacao': forms.Select(attrs={'class': 'form-control'}),
            'situacao': forms.Select(attrs={'class': 'form-control'}),
            'descumprimento_medida': forms.Select(attrs={'class': 'form-control', 'onchange': 'toggleDescumprimentoFields()'}),
            'mike': forms.NumberInput(attrs={'class': 'form-control'}),
            'desfecho': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        vitima = kwargs.pop('vitima', None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            vitima = self.instance.vitima

        if vitima:
            self.fields['agressor_preso'].initial = vitima.agressor_preso
        
        # Lógica para mostrar/ocultar campos 'mike' e 'desfecho'
        # e definir sua obrigatoriedade com base em 'descumprimento_medida'
        
        # Pega o valor de 'descumprimento_medida' dos dados submetidos (se houver) ou da instância
        descumprimento_value = self.data.get('descumprimento_medida') if self.data else None
        if not descumprimento_value and self.instance and self.instance.pk:
            descumprimento_value = self.instance.descumprimento_medida

        if descumprimento_value == 'SIM_COM_CONDUCAO':
            self.fields['mike'].required = True
            self.fields['desfecho'].required = True
            if self.instance and self.instance.pk: # Preenche se for edição
                self.fields['mike'].initial = self.instance.mike
                self.fields['desfecho'].initial = self.instance.desfecho
        else:
            self.fields['mike'].required = False
            self.fields['desfecho'].required = False

class VitimaForm(forms.ModelForm):
    # Campo adicional para o parentesco personalizado (aparece apenas quando "OUTRO" é selecionado)
    outro_parentesco = forms.CharField(
        max_length=50,
        required=False,
        label='Especifique o parentesco',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite o parentesco'})
    )

    class Meta:
        model = Vitima
        fields = [
            'data', 'data_inicial_medida', 'validade_da_medida', 'latitude', 'longitude', 'numero_processo',
            'municipio', 'bairro', 'rua', 'zona', 'nome_vitima', 'data_nascimento', 'parentesco', 'outro_parentesco',
            'perfil_vitima', 'cpf', 'nome_agressor', 'perfil_agressor', 'historico',
            'classificacao', 'tipo_agressao', 'situacao_visita', 'agressor_preso'
        ]
        widgets = {
            'data': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'data_inicial_medida': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'validade_da_medida': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'data_nascimento': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Lógica para popular 'parentesco' e 'outro_parentesco' ao editar
        if self.instance and self.instance.pk:
            current_db_parentesco = self.instance.parentesco
            # Obtém as chaves das opções definidas para o campo 'parentesco'
            parentesco_defined_keys = [key for key, _ in Vitima.PARENTESCO_CHOICES]

            if current_db_parentesco not in parentesco_defined_keys:
                # Se o valor no banco não é uma das chaves pré-definidas,
                # significa que é um valor customizado (ex: "Tio").
                # Então, definimos o dropdown 'parentesco' para 'OUTRO'
                # e preenchemos 'outro_parentesco' com o valor customizado.
                self.initial['parentesco'] = 'OUTRO'
                self.initial['outro_parentesco'] = current_db_parentesco
            # else:
                # Se for um valor pré-definido (incluindo 'OUTRO'),
                # o ModelForm já cuida de popular self.initial['parentesco'].
                # O JavaScript no template cuidará de exibir/ocultar 'outro_parentesco'.
                pass
        
        # A visibilidade do campo 'outro_parentesco' e seu atributo 'required'
        # são controlados pelo JavaScript no template.
        # Remover a manipulação de widget (forms.HiddenInput) daqui simplifica
        # e evita conflitos, especialmente ao re-renderizar o formulário após erros de validação.

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            # Remove caracteres não numéricos do CPF para consistência na busca
            cpf_numerico = ''.join(filter(str.isdigit, cpf))
            
            # Verifica se já existe uma vítima com este CPF
            qs = Vitima.objects.filter(cpf=cpf_numerico)
            
            # Se estiver editando uma vítima existente, exclui ela mesma da verificação
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise forms.ValidationError("Já existe uma vítima cadastrada com este CPF.")
        return cpf

    def save(self, commit=True):
        vitima = super().save(commit=False)
        # Se "OUTRO" for selecionado, salva o valor digitado no campo "parentesco"
        if vitima.parentesco == 'OUTRO':
            vitima.parentesco = self.cleaned_data['outro_parentesco']
        if commit:
            vitima.save()
        return vitima

class AgressorForm(forms.ModelForm):
    class Meta:
        model = Agressor
        fields = '__all__'
