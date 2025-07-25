# core/management/commands/padronizar_status.py
from django.core.management.base import BaseCommand
from django.db.models import Value, F
from django.db.models.functions import Upper
from core.models import Vitima, Visita

class Command(BaseCommand):
    help = 'Padroniza os campos de status para maiúsculas (ATIVA/INATIVA) nos modelos Vitima e Visita.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando a padronização dos status...'))

        # Padroniza Vitima.situacao_visita
        vitimas_atualizadas = Vitima.objects.exclude(
            situacao_visita__in=['ATIVA', 'INATIVA']
        ).update(situacao_visita=Upper('situacao_visita'))
        
        if vitimas_atualizadas > 0:
            self.stdout.write(self.style.SUCCESS(f'{vitimas_atualizadas} registros de vítimas foram padronizados.'))
        else:
            self.stdout.write(self.style.NOTICE('Nenhum registro de vítima precisou ser atualizado.'))

        # Padroniza Visita.situacao
        visitas_atualizadas = Visita.objects.exclude(
            situacao__in=['ATIVA', 'INATIVA']
        ).update(situacao=Upper('situacao'))

        if visitas_atualizadas > 0:
            self.stdout.write(self.style.SUCCESS(f'{visitas_atualizadas} registros de visitas foram padronizados.'))
        else:
            self.stdout.write(self.style.NOTICE('Nenhum registro de visita precisou ser atualizado.'))

        self.stdout.write(self.style.SUCCESS('Padronização de status concluída com sucesso!'))