from excel import open_xls
from utilitarios import extrair_numeros
from MySQL import db

banco = db({'host':"neosed.net",    # your host, usually localhost
            'user':"username",         # your username
            'passwd':"password",  # your password
            'db':"neosed"})

excel = open_xls(r'C:\Users\giuseppe.manzella\Documents\GitHub\neosed\staticFiles\uploads\mapao.xlsx')

total_linha = excel.getTotalRows()
total_coluna = int(excel.getTotalColumns() / 4)

linha_inicial = 11
coluna_inicial = 1

for i in range(1, total_coluna + 1):
    item = {'disc': extrair_numeros(excel.getCell(linha_inicial, coluna_inicial))}
    
    if item['disc'].isnumeric():
        ad = int(excel.getCell(total_linha, coluna_inicial).replace('Aulas Dadas: ', ''))
        
        if ad > 0:
            item['AD'] = ad

            # percorrer a lista
            notas = {}
            
            for j in range(linha_inicial + 2, total_linha + 1):
                notas[excel.getCell(j, coluna_inicial)] = {'N':excel.getCell(j, coluna_inicial + 1), 'F':excel.getCell(j, coluna_inicial + 2), 'AC':excel.getCell(j, coluna_inicial + 3)}

            item['notas'] = notas

            item['abv'] = banco.executarConsulta('select abv from disciplinas where codigo_disciplina = %s' % item['disc'])[0]['abv']
            print(item['abv'])

    coluna_inicial += 4