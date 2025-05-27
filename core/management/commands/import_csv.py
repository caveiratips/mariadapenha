import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from core.models import Vitima, Visita
from django.utils.text import normalize, slugify

class Command(BaseCommand):
    help = 'Importa dados de um CSV para os modelos Vitima e Visita'

    def handle(self, *args, **kwargs):
        with open(r'C:\Users\Carlos Estácio\Desktop\mpenha\mariadapenha\core\management\commands\bancodados.csv', 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Pula o cabeçalho

            for row_num, row in enumerate(csv_reader, start=1):
                try:
                    nome_vitima = row[9].strip()
                    
                    # Verifica se a vítima já existe pelo nome
                    vitima, created = Vitima.objects.get_or_create(
                        nome_vitima=nome_vitima,  # Verificação feita apenas pelo nome
                        defaults={
                            'data': datetime.strptime(row[14], '%d/%m/%Y').date(),
                            'validade_da_medida': datetime.strptime(row[14], '%d/%m/%Y').date(),
                            'latitude': float(row[1]),
                            'longitude': float(row[2]),
                            'numero_processo': row[3],
                            'municipio': row[4],
                            'bairro': row[5],
                            'rua': row[6],
                            'zona': row[7],
                            'estado': 'Pernambuco',
                            'cpf': row[12],  # CPF será salvo, mas não usado na verificação
                            'perfil_vitima': row[11],
                            'nome_agressor': row[15],
                            'perfil_agressor': row[16],
                            'historico': row[17],
                            'classificacao': row[18],
                            'tipo_agressao': row[19],
                            'situacao_visita': row[20]
                        }
                    )

                    # Tratamento do parentesco
                    parentesco_valor = row[10].strip()
                    parentesco_opcoes = [choice[0] for choice in Vitima.PARENTESCO_CHOICES]
                    
                    if not created:  # Atualiza apenas se já existir
                        if parentesco_valor in parentesco_opcoes:
                            vitima.parentesco = parentesco_valor
                            vitima.parentesco_outro = None
                        else:
                            vitima.parentesco = 'OUTRO'
                            vitima.parentesco_outro = parentesco_valor
                        vitima.save()

                except IntegrityError as e:
                    self.stdout.write(self.style.ERROR(
                        f'Linha {row_num}: Erro de integridade - {str(e)}'
                    ))
                    continue
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'Linha {row_num}: Erro ao processar vítima - {str(e)}'
                    ))
                    continue

                # Cria a visita
                try:
                    Visita.objects.create(
                        vitima=vitima,
                        data=datetime.strptime(row[14], '%d/%m/%Y').date(),
                        historico=row[17],
                        classificacao=row[18],
                        situacao=row[20]
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f'Linha {row_num}: Visita cadastrada para {vitima.nome_vitima}'
                    ))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'Linha {row_num}: Erro ao criar visita - {str(e)}'
                    ))

        self.stdout.write(self.style.SUCCESS('Importação concluída!'))