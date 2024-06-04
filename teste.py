import calendar
from datetime import datetime
import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')

# montando calendário padrão

ano = 2024

calendario = []
letivos = 0

# percorrendo todo os meses do ano
for i in range(1, 13):
    qtd_dias = calendar.monthrange(ano, i)[1]

    dias = []

    for j in range(1, qtd_dias + 1):
        date_aux = datetime(ano, i, j)
        dias.append({'dia':j, 'semana':date_aux.strftime("%a")})

        if date_aux.strftime("%a") != 'dom' and date_aux.strftime("%a") != 'sáb':
            letivos += 1

    #desc_mes = datetime(ano, i, 1)

    calendario.append({'dias':dias, 'descricao':calendar.month_name[i].title()})

print(calendario)
print(letivos)