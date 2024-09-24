import asyncio
from pyppeteer import launch

async def main(ra_aluno):
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
    cidade_nascimento = await page.evaluate("document.getElementById('CidadeNascimento').value")
    uf_nascimento = await page.evaluate("document.getElementById('UFNascimento').value")
    rg = await page.evaluate("document.getElementById('RgAluno').value") + '-' + await page.evaluate("document.getElementById('DigRgAluno').value")
    rg = rg[6:8] + '.' + rg[8:11] + '.' + rg[11:]
    cpf = await page.evaluate("document.getElementById('CpfAluno').value")
    sexo = await page.evaluate("document.getElementById('Sexo').value")
    sexo = sexo[0:1]
    pai = await page.evaluate("document.getElementById('NomePai').value")
    mae = await page.evaluate("document.getElementById('NomeMae').value")

    endereco = await page.evaluate("document.getElementById('Endereco').value")
    endereco = endereco.title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ') 
    num_casa = await page.evaluate("document.getElementById('EnderecoNR').value")
    endereco += ', %s' % num_casa
    comp = await page.evaluate("document.getElementById('EnderecoComplemento').value")
    endereco += ', %s' % comp
    bairro = await page.evaluate("document.getElementById('EnderecoBairro').value")
    endereco += ', %s' % bairro.title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ') 
    cidade_endereco = await page.evaluate("document.getElementById('EnderecoCidade').value")
    endereco += ', %s' % cidade_endereco.title().replace('Da ', 'da ').replace("De ", "de ").replace("Do ", 'do ').replace("Dos ", 'dos ') 
    estado_endereco = await page.evaluate("document.getElementById('EnderecoUF').value")
    endereco += '/%s' % estado_endereco
    


    print(ra)
    print(rg)
    print(cpf)
    print(nome)
    print(sexo)
    print(cidade_nascimento)
    print(uf_nascimento)
    print(data_nascimento)
    print(pai)
    print(mae)
    print(endereco)




asyncio.get_event_loop().run_until_complete(main(109789948))