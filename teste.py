from MySQL import db
import calendar
import locale
from datetime import datetime

locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')

banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"Yasmin",  # your password
            'db':"neosed"})


ano = 2024
mes = 5

qtd_dias = qtd_dias = calendar.monthrange(ano, mes)[1]

dias = []

for i in range(1, qtd_dias + 1):
    date_aux = datetime(ano, mes, i)

    if date_aux.strftime("%a") != 'dom' and date_aux.strftime("%a") != 'sáb': # dias de semana
        evento = banco.executarConsulta("select cat_letivo.descricao, cat_letivo.qtd_letivo from eventos_calendario inner join cat_letivo on cat_letivo.id = eventos_calendario.evento where ('%s' BETWEEN data_inicial and data_final)" % date_aux.strftime("%y-%m-%d"))
       
        if len(evento) > 0: # existe um evento
            if evento[0]['qtd_letivo'] < 1: # significa que é feriado ou dia não letivo
                dias.append({'dia':'%02d' % i, 'Assinatura':evento[0]['descricao'], 'semana':date_aux.strftime("%a"), 'class-bg':'gray', 'class-txt':'black'})
            else:
                dias.append({'dia':'%02d' % i, 'Assinatura':'', 'semana':date_aux.strftime("%a"), 'class-bg':'', 'class-txt':'black'})
        else:
            dias.append({'dia':'%02d' % i, 'Assinatura':'', 'semana':date_aux.strftime("%a"), 'class-bg':'', 'class-txt':'black'})
    else: # sábado e domingo
        evento = banco.executarConsulta("select cat_letivo.descricao, cat_letivo.qtd_letivo from eventos_calendario inner join cat_letivo on cat_letivo.id = eventos_calendario.evento where ('%s' BETWEEN data_inicial and data_final)" % date_aux.strftime("%y-%m-%d"))

        if len(evento) > 0: # existe um evento, talvez seja reposição
            if evento[0]['qtd_letivo'] > 0: # significa que é reposição de dia letivo
                dias.append({'dia':'%02d' % i, 'Assinatura':'', 'semana':date_aux.strftime("%a"), 'class-bg':'', 'class-txt':'red'})
            else:
                dias.append({'dia':'%02d' % i, 'Assinatura':evento[0]['descricao'], 'semana':date_aux.strftime("%a"), 'class-bg':'gray', 'class-txt':'red'})
        else:
            dias.append({'dia':'%02d' % i, 'Assinatura':date_aux.strftime("%A").title(), 'semana':date_aux.strftime("%a"), 'class-bg':'gray', 'class-txt':'red'})


for dia in dias:
    print(dia)
               
