import asyncio
from pyppeteer import launch

ra_aluno = 49772486

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
        const element = document.querySelector('.blockUI');
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

    await page.screenshot({'path': 'static/images/etapas_navegacao/ETAPA 2.png'})
    

    #await page.screenshot({'path': 'screenshot.png'})
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())