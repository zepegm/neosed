from excel import xls

planilha = xls()

for i in range(1, 66):
    texto = planilha.getValCell(f'A{i}')
    print(texto)