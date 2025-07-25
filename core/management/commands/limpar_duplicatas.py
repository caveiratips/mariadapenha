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
        
        vitimas_a_processar = Vitima.objects.all().order_by('id')
        total_vitimas = vitimas_a_processar.count()
        self.stdout.write(f'Encontradas {total_vitimas} vítimas para processar.')

        for vitima in vitimas_a_processar:
            # Limpa e normaliza os dados da vítima atual
            cpf_limpo = limpar_cpf(vitima.cpf)
            nome_normalizado = normalizar_nome(vitima.nome_vitima)

            vitima_mestre = None
            chave_duplicata = None
            tipo_duplicata = None

            # 1. Tenta encontrar duplicata pelo CPF (mais confiável)
            if cpf_limpo and len(cpf_limpo) == 11:
                if cpf_limpo in cpf_map:
                    vitima_mestre = cpf_map[cpf_limpo]
                    chave_duplicata = cpf_limpo
                    tipo_duplicata = "CPF"
                else:
                    cpf_map[cpf_limpo] = vitima

            # 2. Se não encontrou por CPF, tenta pelo nome normalizado
            if not vitima_mestre and nome_normalizado:
                if nome_normalizado in nome_map:
                    vitima_mestre = nome_map[nome_normalizado]
                    chave_duplicata = nome_normalizado
                    tipo_duplicata = "Nome"
                else:
                    nome_map[nome_normalizado] = vitima
            
            # Se encontramos uma duplicata (vitima_mestre existe e é diferente da vítima atual)
            if vitima_mestre and vitima_mestre.id != vitima.id:
                self.stdout.write(self.style.WARNING(
                    f'Unificando duplicata: ID {vitima.id} ({vitima.nome_vitima}) será unificada com a Mestre ID {vitima_mestre.id} ({vitima_mestre.nome_vitima}) '
                    f'baseado em {tipo_duplicata}: "{chave_duplicata}"'
                ))

                # Move as visitas da vítima duplicada para a vítima mestre
                visitas_movidas = Visita.objects.filter(vitima=vitima).update(vitima=vitima_mestre)
                if visitas_movidas > 0:
                    self.stdout.write(self.style.SUCCESS(f'  -> {visitas_movidas} visita(s) movida(s).'))

                # Exclui o registro da vítima duplicada
                vitima.delete()
                self.stdout.write(self.style.SUCCESS(f'  -> Vítima duplicada ID {vitima.id} excluída.'))

        self.stdout.write(self.style.SUCCESS('Processo de limpeza concluído com sucesso!'))