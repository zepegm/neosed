# Inicie o navegador com a porta de depuração (por exemplo, chrome --remote-debugging-port=9222).

import json
import tkinter as tk
from excel import xls
from playwright.sync_api import sync_playwright
from tkinter import simpledialog
from tkinter import messagebox

planilha = xls() # formar conexão com a planilha
ra_aluno = 0

def get_ra():
    # Cria a janela principal
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal

    # Solicita o nome do usuário
    name = simpledialog.askstring("Input", "Por favor, insira seu nome:")

    # Fecha a janela principal
    root.destroy()
    return name


def action1():
    try:
        with sync_playwright() as p:
            # Conectar a um navegador já em execução
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            page = browser.contexts[0].pages[0]  # Obter a página aberta

            dados = page.evaluate('''document.querySelector('#sedUiModalWrapper_1title').innerText''')
            print(dados)
            lista = dados.split('-')

            nome = lista[0][16:].strip()
            print(nome)
            ra = lista[1][7:10] + '.' + lista[1][10:13] + '.' + lista[1][13:16] + '-' + lista[2][0:1]
            data_nascimento = lista[3][18:]
            cidade_nascimento = page.evaluate("document.getElementById('CidadeNascimento').value")
            uf_nascimento = page.evaluate("document.getElementById('UFNascimento').value")
            if (uf_nascimento == 'SP'):
                uf_nascimento = 'SÃO PAULO'
            rg = page.evaluate("document.getElementById('RgAluno').value") + '-' + page.evaluate("document.getElementById('DigRgAluno').value")
            rg = rg[6:8] + '.' + rg[8:11] + '.' + rg[11:]

            planilha.setValCell('E14', nome)
            planilha.setValCell('P15', ra)
            planilha.setValCell('E15', rg)
            planilha.setValCell('G16', data_nascimento)
            planilha.setValCell('P16', cidade_nascimento)
            planilha.setValCell('G17', uf_nascimento)


        messagebox.showinfo("Operação efetuada com sucesso!", "Dados do cabeçalho devidamente inseridos!")

    except:
        messagebox.showinfo("Operação não efetuada!", 'Verifique se a página do SED está aberta e se o RA do aluno está correto!')


def action2():
    try:
        planilha_origem = xls('Converted_data.xlsx')

        ano = planilha_origem.getValCell('V5')
        
        if int(planilha.getValCell('P20')) == int(ano):
            coluna = 'P'
        elif int(planilha.getValCell('R20')) == int(ano):
            coluna = 'R'
        else:
            coluna = 'T'


        lista_notas = []

        linha = 10  # Linha onde começa a tabela de notas
        desc_disc = ''

        while desc_disc != 'None':
            desc_disc = str(planilha_origem.getValCell(f'A{linha}')).replace('LINGUA', 'LÍNGUA').replace('MATEMATICA', 'MATEMÁTICA').replace('EDUCACAO FISICA', 'EDUCAÇÃO FÍSICA').replace('QUIMICA', 'QUÍMICA').replace('FISICA', 'FÍSICA').replace('HISTORIA', 'HISTÓRIA').replace('TECNOLOGIA E INOVACAO', 'TECNOLOGIA E INOVAÇÃO').replace('ORIENTACAO DE ESTUDOS', 'ORIENTAÇÃO DE ESTUDOS')

            if desc_disc != 'None':
                lista_notas.append({'disciplina': desc_disc, 'nota': planilha_origem.getValCell(f'T{linha}')})

            linha += 1


        # agora começar a correr a planilha de destino
        for item in lista_notas:
            for i in range(22, 34):
                if item['disciplina'] == planilha.getValCell(f'H{i}'):
                    planilha.setValCell(f'{coluna}{i}', item['nota'])

            for i in range(35, 42):
                if item['disciplina'] == planilha.getValCell(f'D{i}'):
                    planilha.setValCell(f'{coluna}{i}', item['nota'])                    

        messagebox.showinfo("Operação efetuada com sucesso!", "Dados Transportados com sucesso!")
    except:
        messagebox.showinfo("Operação não efetuada!", 'Erro ao transportar dados! Verifique se a planilha está com o nome "Converted_data.xlsx"')

def action3():
    try:
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

            print(dados)

            if int(planilha.getValCell('P20')) == int(ano):
                coluna = 'P'
            elif int(planilha.getValCell('R20')) == int(ano):
                coluna = 'R'
            else:
                coluna = 'T'

            print(coluna)

            for item in dados:
                if int(ra_aluno) == int(item['RA']):
                    try:
                        planilha.setValCell(f'{coluna}29', item['BIOLOGIA'].replace(',', '.'))
                        #planilha.setValCell(f'{coluna}18', item['ED. FISICA'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}32', item['FILOSOFIA'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}28', item['FISICA'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}31', item['GEOGRAFIA'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}30', item['HISTORIA'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}22', item['LING. PORTUGUESA'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}26', item['MATEMATICA'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}27', item['QUIMICA'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}33', item['SOCIOLOGIA'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}24', item['ARTE'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}23', item['L.ING'].replace(',', '.'))                        
                        planilha.setValCell(f'{coluna}35', item['PROJETO DE VIDA'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}36', item['TEC'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}39', item['ORIE.DE ESTUDOS'].replace(',', '.'))
                        planilha.setValCell(f'{coluna}25', item['ED. FISICA'].replace(',', '.'))
                    except:
                        try:
                            planilha.setValCell(f'{coluna}54', item['Geopolítica '].replace(',', '.'))
                            planilha.setValCell(f'{coluna}55', item['Liderança '].replace(',', '.'))
                            planilha.setValCell(f'{coluna}56', item['Oratória '].replace(',', '.'))
                        except:
                            pass
                    break    

        messagebox.showinfo("Operação realizada com sucesso", "Dados transportados com sucesso!")
    except:
        messagebox.showinfo("Operação não efetuada!", 'Erro ao transportar dados! Verifique se o navegador está devidamente aberto e se o RA do aluno está correto!')

def create_menu(ra_aluno):
    # Cria a janela principal
    root = tk.Tk()
    root.title("Menu Principal")

    # Adiciona um título acima dos botões
    title_label = tk.Label(root, text="Preenchendo automaticamente histórico Escolar:", font=("Helvetica", 16))
    title_label.pack(pady=10)    

    title_label_2 = tk.Label(root, text=f"RA: {ra_aluno}", font=("Helvetica", 16))
    title_label_2.pack(pady=10)    

    # Cria os botões e associa cada um a uma função
    button1 = tk.Button(root, text="Preencher Cabeçalho com Janela Aberta", command=action1)
    button1.pack(pady=10)

    button2 = tk.Button(root, text="Preencher Boletim Automaticamente", command=action2)
    button2.pack(pady=10)

    button3 = tk.Button(root, text="Pegar Dados Direto na Ata Final", command=action3)
    button3.pack(pady=10)

    # Inicia o loop principal da interface gráfica
    root.mainloop()


if __name__ == "__main__":
    ra_aluno = get_ra()

    create_menu(ra_aluno)
