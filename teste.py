from excel import open_xls
from utilitarios import extrair_numeros
from MySQL import db

banco = db({'host':"neosed.net",    # your host, usually localhost
            'user':"username",         # your username
            'passwd':"password",  # your password
            'db':"neosed"})

horario = banco.executarConsulta('select distinct inicio, fim from hora_aulas where ano = 2025 order by inicio')
intervalos = []

for i in range(0, len(horario)):
    if i == len(horario) - 1:
        break

    if horario[i]['fim'] != horario[i + 1]['inicio']:
        diferenca = horario[i + 1]['inicio'] - horario[i]['fim']
        diferenca_em_minutos = diferenca.total_seconds() / 60
        
        if diferenca_em_minutos < 40:
            intervalo = {
                'horario': horario[i + 1]['inicio'],
                'tipo': 'intervalo',
                'descricao': 'INTERVALO DOS ALUNOS',
            }
            intervalos.append(intervalo)
        elif diferenca_em_minutos < 120:
            intervalo = {
                'horario': horario[i + 1]['inicio'],
                'tipo': 'almoco',
                'descricao': 'ALMOÇO',
            }
            intervalos.append(intervalo)
        

for item in intervalos:
    print(f"Horário: {item['horario']}, Tipo: {item['tipo']}, Descrição: {item['descricao']}")