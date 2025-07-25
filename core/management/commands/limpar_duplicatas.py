# core/management/commands/limpar_duplicatas.py
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from unidecode import unidecode
from core.models import Vitima, Visita

def limpar_cpf(cpf):
    """Remove qualquer formatação de um CPF, retornando apenas os dígitos."""
    if not cpf:
        return None
    return re.sub(r'\D', '', cpf)

def normalizar_nome(nome):
    """Normaliza um nome para comparação (minúsculas e sem acentos)."""
    if not nome:
        return ''
    # unidecode remove acentos e caracteres especiais
    return unidecode(nome).strip().lower()

class Command(BaseCommand):
    help = 'Encontra e unifica registros de vítimas duplicados no banco de dados.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando o processo de limpeza de vítimas duplicadas...'))

        # Dicionários para rastrear registros mestres por CPF e por nome
        cpf_map = {}
        nome_map = {}
        
        # Placeholders a serem ignorados para fins de mapeamento
        PLACEHOLDER_CPFS = {'00000000000'}
        PLACEHOLDER_NAMES = {'nan', ''}

        vitimas_a_processar = Vitima.objects.all().order_by('id')
        total_vitimas = vitimas_a_processar.count()
        self.stdout.write(f'Encontradas {total_vitimas} vítimas para processar.')

        for vitima in vitimas_a_processar:
            cpf_limpo = limpar_cpf(vitima.cpf)
            nome_normalizado = normalizar_nome(vitima.nome_vitima)

            vitima_mestre = None

            # 1. Tenta encontrar um mestre pelo CPF, se for um CPF válido
            if cpf_limpo and len(cpf_limpo) == 11 and cpf_limpo not in PLACEHOLDER_CPFS:
                if cpf_limpo in cpf_map:
                    vitima_mestre = cpf_map[cpf_limpo]

            # 2. Se não encontrou por CPF, tenta pelo nome, se for um nome válido
            if not vitima_mestre and nome_normalizado and nome_normalizado not in PLACEHOLDER_NAMES:
                if nome_normalizado in nome_map:
                    vitima_mestre = nome_map[nome_normalizado]
            
            # Se um mestre foi encontrado, esta vítima é uma duplicata e deve ser unificada.
            if vitima_mestre and vitima_mestre.id != vitima.id:
                self.stdout.write(self.style.WARNING(
                    f'Unificando duplicata: ID {vitima.id} ({vitima.nome_vitima}) será unificada com a Mestre ID {vitima_mestre.id} ({vitima_mestre.nome_vitima})'
                ))

                # Move as visitas e outros relacionamentos
                Visita.objects.filter(vitima=vitima).update(vitima=vitima_mestre)
                
                vitima_id_deletada = vitima.id
                vitima.delete()
                self.stdout.write(self.style.SUCCESS(f'  -> Vítima duplicada ID {vitima_id_deletada} excluída.'))
            
            # Se não é uma duplicata, ela se torna um mestre para suas chaves.
            else:
                if cpf_limpo and len(cpf_limpo) == 11 and cpf_limpo not in PLACEHOLDER_CPFS:
                    cpf_map[cpf_limpo] = vitima
                if nome_normalizado and nome_normalizado not in PLACEHOLDER_NAMES:
                    nome_map[nome_normalizado] = vitima

        self.stdout.write(self.style.SUCCESS('Processo de limpeza concluído com sucesso!'))