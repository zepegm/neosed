# Inicie o navegador com a porta de depuração (por exemplo, "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\temp\chrome-playwright).

import json
import tkinter as tk
import subprocess
import time
from MySQL import db
from excel import xls
from playwright.sync_api import sync_playwright
from tkinter import simpledialog
from tkinter import messagebox

planilha = xls() # formar conexão com a planilha
# testar a bendita conexão
print(planilha.getValCell('A1')) # deve retornar o valor da célula A1
# se não retornar, verificar se o Excel está aberto e se a planilha está ativa
ra_aluno = 0

banco = db({'host':"neosed.net",    # your host, usually localhost
            'user':"username",         # your username
            'passwd':"password",  # your password
            'db':"neosed"})

def get_ra():
    # Cria a janela principal
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal

    # Solicita o nome do usuário
    name = simpledialog.askstring("Input", "Por favor, insira o RA do aluno (somente números e sem dígito):")

    # Fecha a janela principal
    root.destroy()
    return name

def action0():
    try:
        from playwright.sync_api import sync_playwright

        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        user_data_dir = r"C:\temp\chrome-playwright"

        subprocess.Popen([
            chrome_path,
            "--remote-debugging-port=9222",
            f"--user-data-dir={user_data_dir}"
        ])

        time.sleep(2)  # aguarda Chrome iniciar

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")

            context = browser.contexts[0]
            page = context.pages[0]  # usa a aba já aberta

            page.goto("https://sed.educacao.sp.gov.br/", wait_until="networkidle")
            page.fill('#name', 'rgxxxxx')
            page.fill('#senha', 'pssword')
            page.click('#botaoEntrar')

            # aguarda algo específico da próxima página, se necessário
            # page.wait_for_selector('#elemento_pos_login')

    except Exception as e:
        print(f"Erro: {e}")
        messagebox.showinfo("Operação não efetuada!", 'Verifique se já está logado no SED e se o RA do aluno está correto!')



def action1():
    try:
        with sync_playwright() as p:
            # Conectar a um navegador já em execução
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            page = browser.contexts[0].pages[0]  # Obter a página aberta

            page.goto("https://sed.educacao.sp.gov.br/NCA/FichaAluno/Index", wait_until="networkidle")

            print("Nova página carregada:", page.url)

            page.select_option('#TipoConsultaFichaAluno', label='RA')

            page.evaluate('''$("#fieldSetRA").removeAttr('style');''')

            page.fill('#txtRa', ra_aluno)

            page.click('#btnPesquisar')

            # Aguarda a tabela de dados ser carregada
            page.wait_for_selector('#tabelaDados')
          

            # Localiza o elemento <a> com a função onclick desejada
            el = page.locator('td.colVisualizar a[onclick*="DadosFichaAluno"]')

            # Extrai o conteúdo do atributo onclick
            onclick_code = el.get_attribute("onclick")

            # Executa esse código no contexto da página
            page.evaluate(onclick_code)

            page.wait_for_selector("#sedUiModalWrapper_1")

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

            page.evaluate("listarMatriculasFichaAluno(false)")

            #await page.waitFor(5000)

            page.click("#aba5")

            page.wait_for_selector('#tabelaDadosMatricula')

            tamanho_tabela = int(page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data().length"))

            anos = []

            for i in range(tamanho_tabela):
                tipo_ensino = int(page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][8]" % i))
                
                if tipo_ensino in (2, 5, 101):
                    status = page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][17]" % i)

                    print(status)
                    
                    if status == '<span>Aprovado</span>':
                        escola = page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][6]" % i)
                        escola = escola.replace('ALICE VILELA GALVAO PROFA', 'EE PROFª ALICE VILELA GALVÃO')
                        serie = int(page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][10]" % i))
                        ano = page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][0]" % i)
                        turma = page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][11]" % i)
                        municipio = page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][2]" % i)

                        match(serie):
                            case 1:
                                coluna = 'P'
                                linha = 49
                            case 2:
                                coluna = 'R'
                                linha = 50
                            case 3:
                                coluna = 'T'
                                linha = 51

                        anos.append({'ano':ano, 'turma':turma, 'coluna':coluna})                        

                        match(tipo_ensino):
                            case 2:
                                desc_serie = str(serie) + 'ª Série'
                            case 5:
                                desc_serie = str(serie) + 'º Termo'
                            case 101: # Novo Ensino Médio 
                                desc_serie = str(serie) + 'ª Série'

                        planilha.setValCell(coluna + '20', ano)
                        planilha.setValCell(coluna + '19', desc_serie)
                        planilha.setValCell('I%s' % linha, escola)
                        planilha.setValCell('R%s' % linha, municipio)
                        planilha.setValCell('w%s' % linha, 'SP')

                elif tipo_ensino in (4, 14):
                    status = page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][17]" % i)
                    if status == '<span>Aprovado</span>':
                        serie = int(page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][10]" % i))
                        if serie in (9, 12):
                            ano = page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][0]" % i)
                            escola = page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][6]" % i)
                            escola = escola.replace("ALICE VILELA GALVAO PROFA EMEF", 'EMEF PROFª ALICE VILELA GALVÃO').replace("OTTON FERNANDES BARBOSA PROF EMEIEF", 'EMEIEF PROF. OTTON FERNANDES BARBOSA')
                            municipio = page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][2]" % i)
                            planilha.setValCell('G47', ano)
                            planilha.setValCell('I47', escola)
                            planilha.setValCell('R47', municipio)


        messagebox.showinfo("Operação efetuada com sucesso!", "Dados do cabeçalho devidamente inseridos!")

    except Exception as e:
        # Se ocorrer um erro, exibe uma mensagem de erro
        print("Erro ao obter dados do navegador:", e)
        # Exibe uma mensagem de erro na interface gráfica
        messagebox.showinfo("Operação não efetuada!", 'Verifique se a página do SED está aberta e se o RA do aluno está correto!')


def action2():
    # dados padrões
    coluna = {1:'P', 2:'R', 3:'T'}
    linhas_disc = {1100:22, 1400:23, 8467:23, 1813:24, 1900:25, 2100:31, 2200:30, 2300:33, 2400:29, 2600:28, 2700:26, 2800:27, 3100:32, 50428:37, 50429:36, 50430:38}

    try:        
        for i in range(1, 4):
            # pegar turma da i série
            turma = banco.executarConsulta("select num_classe from vinculo_alunos_turmas where ra_aluno = %s and serie = %s and situacao = 6" % (ra_aluno, i))

            if len(turma) > 0:
                # pegar turma if vinculada (se houver)
                turma_if = banco.executarConsulta("select num_classe_if from vinculo_if where num_classe_em = %s" % turma[0]['num_classe'])

                if len(turma_if) > 0:
                    notas = banco.executarConsulta("select * from conceito_final where num_classe in (%s, %s) and ra_aluno = %s" % (turma[0]['num_classe'], turma_if[0]['num_classe_if'], ra_aluno))
                else:
                    notas = banco.executarConsulta("select * from conceito_final where num_classe = %s and ra_aluno = %s" % (turma[0]['num_classe'], ra_aluno))

                for item in notas:
                    try:
                        planilha.setValCell(f'{coluna[i]}{linhas_disc[item["disciplina"]]}', item['media'])
                    except KeyError:
                        print(f"Disciplina {item['disciplina']} não encontrada para a série {i}. Verifique se a disciplina está mapeada corretamente.")
                        continue


        messagebox.showinfo("Operação efetuada com sucesso!", "Dados Transportados com sucesso!")
    except Exception as e:
        print(e)
        messagebox.showinfo("Operação não efetuada!", 'Verificar erro: %s' % e)

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
                if int(ra_aluno) == int(item['RA'].replace('-', '')):
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
    except Exception as e:
        print(e)
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
    button0 = tk.Button(root, text="Abrir Navegador e Logar na SED", command=action0)
    button0.pack(pady=10)

    button1 = tk.Button(root, text="Preencher Cabeçalho com Janela Aberta", command=action1)
    button1.pack(pady=10)

    button2 = tk.Button(root, text="Preencher Com Notas do Banco Automaticamente", command=action2)
    button2.pack(pady=10)

    button3 = tk.Button(root, text="Pegar Dados Direto na Ata Final", command=action3)
    button3.pack(pady=10)

    # Inicia o loop principal da interface gráfica
    root.mainloop()


if __name__ == "__main__":
    ra_aluno = get_ra()

    create_menu(ra_aluno)
