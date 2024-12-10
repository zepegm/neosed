import asyncio
import pandas as pd
from pyppeteer import launch

async def main():

    # percorrer planilha
    sheets_dict = pd.read_excel('lista_turmas.xlsx')

    dicionario = sheets_dict.to_dict(orient='records')    

    browser = await launch({'headless': False})
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

    for item in dicionario:
        print(item)






asyncio.get_event_loop().run_until_complete(main())