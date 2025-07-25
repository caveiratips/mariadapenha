# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Vitima(models.Model):
    # Opções de seleção
    MUNICIPIOS_PE = [
        ('AFOGADOS DA INGAZEIRA', 'Afogados da Ingazeira'),
        ('IGUARACY', 'Iguaracy'),
        ('INGAZEIRA', 'Ingazeira'),
        ('QUIXABA', 'Quixaba'),
        ('CARNAÍBA', 'Carnaíba'),
        ('TABIRA', 'Tabira'),
        ('SOLIDÃO', 'Solidão'),
        ('SANTA TEREZINHA', 'Santa Terezinha'),
        ('SÃO JOSÉ DO EGITO', 'São José do Egito'),
        ('ITAPETIM', 'Itapetim'),
        ('BREJINHO', 'Brejinho'),
        ('TUPARETAMA', 'Tuparetama')
    ]

    ZONA_CHOICES = [
        ('U', 'Urbana'),
        ('R', 'Rural'),
    ]

    PARENTESCO_CHOICES = [
        ('CONJUGE', 'Companheira/Cônjuge'),
        ('EX_CONJUGE', 'Ex-Companheira/Ex-Cônjuge'),
        ('NAMORADA', 'Namorada/Ex-Namorada'),
        ('MAE', 'Mãe'),
        ('IRMA', 'Irmã'),
        ('SOGRA', 'Sogra'),
        ('OUTRO', 'Outro'),
    ]

    PERFIL_VITIMA_CHOICES = [
        ('INDEPENDENTE', 'Independente'),
        ('DEP_ECONOMICA', 'Dependência Econômica'),
        ('DEP_EMOCIONAL', 'Dependência Emocional'),
        ('NAO_INFORMADO', 'Não Informado'),
    ]


    PERFIL_AGRESSOR_CHOICES = [
        ('EMOCIONAL', 'Emocionalmente Instável'),
        ('ALCOOL', 'Usuário de Álcool'),
        ('DROGAS', 'Usuário de Drogas'),
        ('NAO_INFORMADO', 'Não Informado'),
    ]

    CLASSIFICACAO_CHOICES = [
        ('MÉDIO', 'Médio'),
        ('GRAVE', 'Grave'),
        ('GRAVÍSSIMO', 'Gravíssimo'),
    ]

    TIPO_AGRESSÃO_CHOICES = [
        ('FISICA', 'Física'),
        ('PSICOLOGICA', 'Psicológica'),
        ('PATRIMONIAL', 'Patrimonial'),
        ('SEXUAL', 'Sexual'),
        ('MORAL', 'Moral'),
        ('ECONOMICA', 'Econômica'),
    ]
    
    AGRESSOR_PRESO_CHOICES = [
        ('SIM', 'Sim'),
        ('NAO', 'Não'),
        ('NAO_INFORMADO', 'Não Informado'),
    ]
 
    # Campos do modelo
    data = models.DateField(verbose_name="Data do Cadastro")
    data_inicial_medida = models.DateField(verbose_name="Data Inicial da Medida", null=True, blank=True)
    validade_da_medida = models.DateField(verbose_name="Data de Validade da Medida", null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    numero_processo = models.CharField(max_length=50, unique=True)
    municipio = models.CharField(max_length=22, choices=MUNICIPIOS_PE)
    bairro = models.CharField(max_length=100)
    rua = models.CharField(max_length=100)
    zona = models.CharField(max_length=1, choices=ZONA_CHOICES)
    estado = models.CharField(max_length=20, default='Pernambuco', editable=False)
    nome_vitima = models.CharField(max_length=100)
    data_nascimento = models.DateField(verbose_name="Data de Nascimento", null=True, blank=True)
    parentesco = models.CharField(max_length=15, choices=PARENTESCO_CHOICES)
    perfil_vitima = models.CharField(max_length=15, choices=PERFIL_VITIMA_CHOICES)
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True, help_text="CPF deve ser único. Deixe em branco se não houver.")
    nome_agressor = models.CharField(max_length=100)
    perfil_agressor = models.CharField(max_length=15, choices=PERFIL_AGRESSOR_CHOICES)
    historico = models.TextField(verbose_name='Resumo dos Fatos')
    classificacao = models.CharField(max_length=10, choices=CLASSIFICACAO_CHOICES)
    tipo_agressao = models.CharField(max_length=15, choices=TIPO_AGRESSÃO_CHOICES)
    situacao_visita = models.CharField(max_length=7, choices=[('ATIVA', 'Ativa'), ('INATIVA', 'Inativa')], default='ATIVA')
    agressor_preso = models.CharField(
        max_length=15,
        choices=AGRESSOR_PRESO_CHOICES,
        default='NAO_INFORMADO',
        verbose_name='Agressor Preso?'
    )
    data_registro = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(blank=True, null=True)
    
    
    def __str__(self):
        return f"{self.nome_vitima} - {self.get_classificacao_display()} - {self.municipio}"

    def save(self, *args, **kwargs):
        # Limpa o campo parentesco_outro se não for 'Outro'
        if self.parentesco != 'OUTRO':
            self.parentesco_outro = None
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Vítima'
        verbose_name_plural = 'Vítimas'
        ordering = ['-data_registro']
        
    def get_absolute_url(self):
        return reverse('vitima-detail', kwargs={'pk': self.pk})  # Redireciona para os detalhes da vítima    
        
# core/models.py
class Visita(models.Model):
    CLASSIFICACAO_CHOICES = [
        ('MÉDIO', 'Médio'),
        ('GRAVE', 'Grave'),
        ('GRAVÍSSIMO', 'Gravíssimo'),
    ]

    SITUACAO_CHOICES = [
        ('ATIVA', 'Ativa'),
        ('INATIVA', 'Inativa'),
    ]
    
    DESCUMPRIMENTO_CHOICES = [
        ('SIM_COM_CONDUCAO', 'Sim (com condução a DP)'),
        ('SIM_SEM_CONDUCAO', 'Sim (Sem condução a DP)'),
        ('NAO', 'Não'),
        ('NAO_INFORMADO', 'Não Informado'),
    ]

    DESFECHO_CHOICES = [
        ('APFD', 'APFD'),
        ('TCO', 'TCO'),
        ('IP', 'IP'),
    ]

    descumprimento_medida = models.CharField(
        max_length=20, # Ajustado para acomodar 'SIM_COM_CONDUCAO' etc.
        choices=DESCUMPRIMENTO_CHOICES,
        default='NAO_INFORMADO',
        verbose_name='Descumprimento de Medida'
    )
    mike = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Mike'
    )
    
    desfecho = models.CharField(
        max_length=4,
        choices=DESFECHO_CHOICES,
        null=True,
        blank=True,
        verbose_name='Desfecho'
    )

    vitima = models.ForeignKey(
        Vitima,
        on_delete=models.CASCADE,
        related_name='visitas'
    )
    data = models.DateField()
    historico = models.TextField(verbose_name='Histórico da Visita')
    classificacao = models.CharField(
        max_length=10,
        choices=CLASSIFICACAO_CHOICES,
        verbose_name='Classificação'
    )
    situacao = models.CharField(
        max_length=7,
        choices=SITUACAO_CHOICES,
        default='ATIVA',
        verbose_name='Situação'
    )
    
    def save(self, *args, **kwargs):
        # Salva a visita sem normalizar os valores
        super().save(*args, **kwargs)
        
        # Atualiza a situação da vítima com base na última visita
        vitima = self.vitima
        latest_visita = vitima.visitas.order_by('-data', '-id').first()
        if latest_visita:
            vitima.situacao_visita = latest_visita.situacao
            vitima.classificacao = latest_visita.classificacao
            vitima.save()

    def delete(self, *args, **kwargs):
        vitima = self.vitima
        super().delete(*args, **kwargs)
        
        ultima_visita = vitima.visitas.order_by('-data', '-id').first()
        
        if ultima_visita:
            vitima.situacao_visita = ultima_visita.situacao
            vitima.classificacao = ultima_visita.classificacao
        else:
            # Usa os valores padrão definidos no modelo Vitima
            vitima.situacao_visita = vitima.situacao_visita
            vitima.classificacao = vitima.classificacao
        
        vitima.save()

    class Meta:
        verbose_name = 'Visita'
        verbose_name_plural = 'Visitas'
        ordering = ['-data']

    def __str__(self):
        return f"Visita em {self.data} - {self.get_classificacao_display()}"
    
    
class Agressor(models.Model):
    # Chave estrangeira para o modelo Vitima
    vitima = models.ForeignKey(
        Vitima,
        on_delete=models.CASCADE,
        related_name='agressores',  # Nome para acessar os agressores de uma vítima
        verbose_name='Vítima'
    )

    # Campos do modelo
    data_inicial_medida = models.DateField(verbose_name='Data Inicial da Medida')
    data_final_medida = models.DateField(verbose_name='Data Final da Medida', null=True, blank=True)
    numero_processo = models.CharField(max_length=50, unique=True, verbose_name='Número do Processo')
    nome_agressor = models.CharField(max_length=100, verbose_name='Nome do Agressor')
    parentesco = models.CharField(max_length=15, choices=Vitima.PARENTESCO_CHOICES, verbose_name='Parentesco')
    perfil_agressor = models.CharField(max_length=15, choices=Vitima.PERFIL_AGRESSOR_CHOICES, verbose_name='Perfil do Agressor')
    tipo_agressao = models.CharField(max_length=15, choices=Vitima.TIPO_AGRESSÃO_CHOICES, verbose_name='Tipo de Agressão')
    resumo_dos_fatos = models.TextField(verbose_name='Resumo dos Fatos')

    def __str__(self):
        return f"{self.nome_agressor} - {self.numero_processo}"

    class Meta:
        verbose_name = 'Agressor'
        verbose_name_plural = 'Agressores'
        ordering = ['-data_inicial_medida']  # Ordena por data inicial da medida (mais recente primeiro) 
