# Inicie o navegador com a porta de depuração (por exemplo, chrome --remote-debugging-port=9222).

import json
from excel import xls
from playwright.sync_api import sync_playwright

ra_aluno = 108598427


planilha = xls() # formar conexão com a planilha


with sync_playwright() as p:
    # Conectar a um navegador já em execução
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = browser.contexts[0].pages[0]  # Obter a página aberta

    ano = page.evaluate('''document.querySelector('#filt-anoLetivo').value''')
    
    json_data = page.evaluate('''
        const table = $('#tabela').DataTable();
        const headers = table.columns().header().toArray().map(header => $(header).text());
        const data = table.rows().data().toArray();
        const jsonData = data.map(row => {
            let rowData = {};
            headers.forEach((header, index) => {
                rowData[header] = row[index];
            });
            return rowData;
        });
        JSON.stringify(jsonData);
    ''')

    dados = json.loads(json_data)

    if int(planilha.getValCell('O14')) == int(ano):
        coluna = 'O'
    elif int(planilha.getValCell('Q14')) == int(ano):
        coluna = 'Q'
    else:
        coluna = 'S'


    for item in dados:
        if ra_aluno == int(item['RA']):
            planilha.setValCell(f'{coluna}17', item['ARTE'].replace(',', '.'))
            planilha.setValCell(f'{coluna}20', item['BIOLOGIA'].replace(',', '.'))
            planilha.setValCell(f'{coluna}18', item['ED. FISICA'].replace(',', '.'))
            planilha.setValCell(f'{coluna}25', item['FILOSOFIA'].replace(',', '.'))
            planilha.setValCell(f'{coluna}21', item['FISICA'].replace(',', '.'))
            planilha.setValCell(f'{coluna}24', item['GEOGRAFIA'].replace(',', '.'))
            planilha.setValCell(f'{coluna}23', item['HISTORIA'].replace(',', '.'))
            planilha.setValCell(f'{coluna}28', item['L. EST. INGLES'].replace(',', '.'))
            planilha.setValCell(f'{coluna}16', item['LIN PORT LIT'].replace(',', '.'))
            planilha.setValCell(f'{coluna}19', item['MATEMATICA'].replace(',', '.'))
            planilha.setValCell(f'{coluna}22', item['QUIMICA'].replace(',', '.'))
            planilha.setValCell(f'{coluna}26', item['SOCIOLOGIA'].replace(',', '.'))
            break
