import asyncio
from pyppeteer import launch
from MySQL import db
from excel import xls
import html_to_json

ra_aluno = 107911715

rows_notas = [{'disc':'ARTE', 'linha':18}, {'disc':'BIOLOGIA', 'linha':21}, {'disc':'ED. FISICA', 'linha':19}, {'disc':'FILOSOFIA', 'linha':26}, {'disc':'FISICA', 'linha':22}, {'disc':'GEOGRAFIA', 'linha':25}, {'disc':'HISTORIA', 'linha':24}, {'disc':'L.ING', 'linha':17}, {'disc':'L. EST. INGLES', 'linha':17}, {'disc':'LIN PORT LIT', 'linha':16}, {'disc':'LING. PORTUGUESA', 'linha':16}, {'disc':'MATEMATICA', 'linha':20}, {'disc':'PROJETO DE VIDA', 'linha':29}, {'disc':'QUIMICA', 'linha':23}, {'disc':'SOCIOLOGIA', 'linha':27}, {'disc':'TEC', 'linha':30}]

planilha = xls() # formar conexão com a planilha
banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"admin",  # your password
            'db':"neosed"})



async def main():
    browser = await launch({'headless': False})
    page = await browser.newPage()
    await page.setViewport({"width": 1366, "height": 768})

    # efetuar login na SED
    await page.goto('https://sed.educacao.sp.gov.br/')
    await page.waitForSelector('#name', {'visible': True}) 
    await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#name', 'rgxxxxx')
    await page.evaluate('''(selector, value) => {
        document.querySelector(selector).value = value;
    }''', '#senha', 'pssword')  
    await page.evaluate("() => document.querySelector('#botaoEntrar').removeAttribute('disabled')")
    await page.click("#botaoEntrar")
    await page.waitForSelector('#ambientes-aprendizagem', {'visible': True}) 
    await page.screenshot({'path': 'static/images/etapas_navegacao/ETAPA 1.png'})
    print('Etapa 1 Concluída! - Login Efetuado com sucesso!')

    # abrir a ficha do aluno e pegar informações
    await page.goto("https://sed.educacao.sp.gov.br/NCA/FichaAluno/Index", {'timeout':60000, 'waitUntil':'domcontentloaded'})
    await page.evaluate('''() => {
        const element = document.querySelector('.blockOverlay');
        if (element) {
            element.remove();
        }
    }''')
    await page.evaluate('''() => {
        const element = document.querySelector('.blockPage');
        if (element) {
            element.remove();
        }
    }''')
    await page.waitForSelector('#btnPesquisar', {'visible': True})
    await page.evaluate("() => document.querySelector('#fieldSetRA').removeAttribute('style')")
    await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#txtRa', ra_aluno) 
    await page.waitForSelector('.blockUI', {'hidden':True})
    await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#TipoConsultaFichaAluno', 1) 
    await page.click("#btnPesquisar")
    await page.waitForSelector('#tabelaDados', {'visible': True})
    script = await page.evaluate("document.getElementsByClassName('colVisualizar')[1].getElementsByTagName('a')[0].getAttribute('onclick')")
    await page.evaluate(script)
    await page.waitForSelector('#sedUiModalWrapper_1', {'visible': True})

    # pegar dados do aluno para inserir na planilha
    dados = await page.evaluate("document.getElementById('sedUiModalWrapper_1title').textContent")
    lista = dados.split('-')

    nome = lista[0][16:].strip()
    ra = lista[1][7:10] + '.' + lista[1][10:13] + '.' + lista[1][13:16] + '-' + lista[2][0:1]
    data_nascimento = lista[3][18:]
    alt = data_nascimento[6:] + '-' + data_nascimento[3:5] + '-' + data_nascimento[0:2]
    cidade_nascimento = await page.evaluate("document.getElementById('CidadeNascimento').value")
    uf_nascimento = await page.evaluate("document.getElementById('UFNascimento').value")
    if (uf_nascimento == 'SP'):
        uf_nascimento = 'SÃO PAULO'
    rg = await page.evaluate("document.getElementById('RgAluno').value") + '-' + await page.evaluate("document.getElementById('DigRgAluno').value")
    rg = rg[6:8] + '.' + rg[8:11] + '.' + rg[11:]


    planilha.setValCell('E10', nome)
    planilha.setValCell('O10', rg)
    planilha.setValCell('S10', ra)
    planilha.setValCell('G11', cidade_nascimento)
    planilha.setValCell('O11', uf_nascimento)
    planilha.setValCell('F12', alt)
    planilha.setValCell('S11', 'BRASIL')

    #await page.waitFor(2000)

    await page.evaluate("listarMatriculasFichaAluno(false)")

    #await page.waitFor(5000)

    await page.click("#aba5")

    await page.waitForSelector('#tabelaDadosMatricula')

    tamanho_tabela = int(await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data().length"))

    anos = []

    for i in range(tamanho_tabela):
        tipo_ensino = int(await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][8]" % i))
        
        if tipo_ensino == 2 or tipo_ensino == 5:
            status = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][17]" % i)
            
            if status == '<span>Aprovado</span>':
                escola = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][6]" % i)
                escola = escola.replace('ALICE VILELA GALVAO PROFA', 'EE PROFª ALICE VILELA GALVÃO')
                serie = int(await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][10]" % i))
                ano = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][0]" % i)
                turma = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][11]" % i)
                municipio = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][2]" % i)

                match(serie):
                    case 1:
                        coluna = 'P'
                        linha = 45
                    case 2:
                        coluna = 'R'
                        linha = 46
                    case 3:
                        coluna = 'T'
                        linha = 47

                anos.append({'ano':ano, 'turma':turma, 'coluna':coluna})                        

                match(tipo_ensino):
                    case 2:
                        desc_serie = str(serie) + 'ª Série'
                    case 5:
                        desc_serie = str(serie) + 'º Termo'

                planilha.setValCell(coluna + '14', ano)
                planilha.setValCell(coluna + '15', desc_serie)
                planilha.setValCell('I%s' % linha, escola)
                planilha.setValCell('Q%s' % linha, municipio)
                planilha.setValCell('U%s' % linha, 'SP')

        elif tipo_ensino == 14:
            status = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][17]" % i)
            if status == '<span>Aprovado</span>':
                serie = int(await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][10]" % i))
                if serie == 9:
                    ano = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][0]" % i)
                    escola = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][6]" % i)
                    escola = escola.replace("ALICE VILELA GALVAO PROFA EMEF", 'EMEF PROFª ALICE VILELA GALVÃO')
                    planilha.setValCell('G43', ano)
                    planilha.setValCell('I43', escola)


    print('ETAPA 2 Concluída! Dados iniciais do aluno puxados com sucesso!')
    
    await page.screenshot({'path': 'static/images/etapas_navegacao/ETAPA 2.png'})
    

    await page.goto('https://sed.educacao.sp.gov.br/ataresultadofinal/Index', {'waitUntil': 'networkidle0' })

    for ano in anos:
        await page.evaluate('''() => {
            $("#filt-anoLetivo").val('');
        }''')

        await page.type('#filt-anoLetivo', ano['ano'])

        await page.keyboard.press("Tab")

        await page.waitForFunction("document.querySelectorAll('.filter-option-inner-inner')[4].innerText == 'ALICE VILELA GALVAO PROFA - 13134'")

        #await page.waitForFunction('document.querySelectorAll("#filt-tipoEnsino option")[8].innerText == "ENSINO MÉDIO"')

        await page.waitForFunction('document.querySelectorAll(".blockUI").length == 0')

        await page.click("#filt-grupotipoEnsino button")

        await page.keyboard.type('ENSINO M')

        await page.keyboard.down('ArrowDown')

        await page.keyboard.press('Enter')

        await page.waitForFunction('document.querySelectorAll(".blockUI").length == 0')

        await page.click("#filt-grupoturma button")

        await page.keyboard.type(ano['turma'])

        await page.keyboard.press('Enter')

        await page.waitForFunction('document.querySelectorAll(".blockUI").length == 0')

        await page.click("#btnPesquisar")

        await page.waitForFunction('document.querySelectorAll(".blockUI").length == 0')
        
        tabela = await page.evaluate('''() => {
            let table = $("#tabela").DataTable();

            table.order( [1,'asc'] ).draw();

            var columnNames = table.columns().header().toArray().map(header => $(header).text());

            var dataDictList = table.rows().data().toArray().map(row => {
                let rowData = {};
                columnNames.forEach((colName, index) => {
                    rowData[colName] = row[index];
                });
                return rowData;
            });    

            return Promise.resolve(dataDictList);
        }''')

        for item in tabela:
            if int(item['RA']) == ra_aluno:
                for disc in rows_notas:
                    try:
                        planilha.setValCell(ano['coluna'] + str(disc['linha']), item[disc['disc']])
                    except:
                        print(item)


        print('ETAPA 3 Concluída! Dados iniciais do aluno puxados com sucesso!')
        print(ano['turma'])
    
        await page.screenshot({'path': 'static/images/etapas_navegacao/ETAPA 3.png'})        


    
    

    #await page.screenshot({'path': 'screenshot.png'})
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())