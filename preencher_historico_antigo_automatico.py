import asyncio
from pyppeteer import launch
from MySQL import db
from excel import xls
import html_to_json

ra_aluno = 49772486

planilha = xls() # formar conexão com a planilha
banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"Yasmin",  # your password
            'db':"neosed"})



async def main():
    browser = await launch()
    page = await browser.newPage()
    await page.setViewport({"width": 1366, "height": 768})

    # efetuar login na SED
    await page.goto('https://sed.educacao.sp.gov.br/')
    await page.waitForSelector('#name', {'visible': True}) 
    await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#name', 'rg490877795sp')    
    await page.evaluate('''(selector, value) => {
        document.querySelector(selector).value = value;
    }''', '#senha', 'BGarden@FF8')  
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


    planilha.setValCell('D10', nome)
    planilha.setValCell('N10', rg)
    planilha.setValCell('R10', ra)
    planilha.setValCell('F11', cidade_nascimento)
    planilha.setValCell('N11', uf_nascimento)
    planilha.setValCell('E12', alt)
    planilha.setValCell('R11', 'BRASIL')

    #await page.waitFor(2000)

    await page.evaluate("listarMatriculasFichaAluno(false)")

    #await page.waitFor(5000)

    await page.click("#aba5")

    await page.waitForSelector('#tabelaDadosMatricula')

    tamanho_tabela = int(await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data().length"))



    for i in range(tamanho_tabela):
        tipo_ensino = int(await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][8]" % i))
        
        if tipo_ensino == 2 or tipo_ensino == 5:
            status = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][17]" % i)
            
            if status == '<span>Aprovado</span>':
                escola = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][6]" % i)
                escola = escola.replace('ALICE VILELA GALVAO PROFA', 'EE PROFª ALICE VILELA GALVÃO')
                serie = int(await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][10]" % i))
                ano = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][0]" % i)
                municipio = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][2]" % i)

                match(serie):
                    case 1:
                        coluna = 'O'
                        linha = 41
                    case 2:
                        coluna = 'Q'
                        linha = 42
                    case 3:
                        coluna = 'S'
                        linha = 43

                match(tipo_ensino):
                    case 2:
                        desc_serie = str(serie) + 'ª Série'
                    case 5:
                        desc_serie = str(serie) + 'º Termo'

                planilha.setValCell(coluna + '14', ano)
                planilha.setValCell(coluna + '15', desc_serie)
                planilha.setValCell('H%s' % linha, escola)
                planilha.setValCell('P%s' % linha, municipio)
                planilha.setValCell('T%s' % linha, 'SP')

        elif tipo_ensino == 14:
            status = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][17]" % i)
            if status == '<span>Aprovado</span>':
                serie = int(await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][10]" % i))
                if serie == 9:
                    ano = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][0]" % i)
                    escola = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][6]" % i)
                    escola = escola.replace("ALICE VILELA GALVAO PROFA EMEF", 'EMEF PROFª ALICE VILELA GALVÃO')
                    planilha.setValCell('F39', ano)
                    planilha.setValCell('H39', escola)


    print('ETAPA 2 Concluída! Dados iniciais do aluno puxados com sucesso!')
    
    await page.screenshot({'path': 'static/images/etapas_navegacao/ETAPA 2.png'})
    


    
    

    #await page.screenshot({'path': 'screenshot.png'})
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())