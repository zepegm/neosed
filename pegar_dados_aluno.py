import asyncio
import pandas as pd
from pyppeteer import launch
from bs4 import BeautifulSoup


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
    await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#name', 'rgxxxxx')    
    await page.evaluate('''(selector, value) => {
        document.querySelector(selector).value = value;
    }''', '#senha', 'pssword')  
    await page.evaluate("() => document.querySelector('#botaoEntrar').removeAttribute('disabled')")
    await page.click("#botaoEntrar")
    await page.waitForSelector('#ambientes-aprendizagem', {'visible': True}) 
    await page.screenshot({'path': 'static/images/etapas_navegacao/ETAPA 1.png'})
    print('Etapa 1 Concluída! - Login Efetuado com sucesso!')

    for item in dicionario:

        print('------------------ Verificando classe: %s' % item['Num_Classe'])

        await page.goto('https://sed.educacao.sp.gov.br//NCA/FichaAluno/Index')
        await page.waitForSelector('.blockUI', {'hidden':True})
        await page.evaluate('''$("#fieldSetClasse").removeAttr('style');''')
        await page.evaluate('''$("#TipoConsultaFichaAluno").val(5);''')
        await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#txtNumeroClasse', item['Num_Classe'])
        await page.waitForSelector('.blockUI', {'hidden':True})
        await page.evaluate('''CarregarPesquisaFichaAluno()''')
        await page.waitForSelector('#tabelaDados')

        # Obter o conteúdo HTML do elemento
        element = await page.querySelector('#tabelaDados')
        html_content = await page.evaluate('(element) => element.outerHTML', element)
        soup = BeautifulSoup(html_content, 'html.parser')
        links = soup.find_all('td', class_='colVisualizar')
        for link in links:
            a_tag = link.find('a')
            if a_tag and a_tag.has_attr('onclick'):  # Verificar se a tag <a> tem o atributo "onclick"
                if a_tag['onclick'][0:1] == 'D':

                    await page.goto('https://sed.educacao.sp.gov.br//NCA/FichaAluno/Index')
                    await page.waitForSelector('.blockUI', {'hidden':True})
                    await page.evaluate('''$("#fieldSetClasse").removeAttr('style');''')
                    await page.evaluate('''$("#TipoConsultaFichaAluno").val(5);''')
                    await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#txtNumeroClasse', item['Num_Classe'])
                    await page.waitForSelector('.blockUI', {'hidden':True})
                    await page.evaluate('''CarregarPesquisaFichaAluno()''')
                    await page.waitForSelector('#tabelaDados')


                    await page.waitForSelector('.blockUI', {'hidden':True})
                    txt_script = a_tag['onclick'].strip()
                    await page.evaluate(txt_script)
                    await page.waitForSelector("#dtAlteracaoAluno")
                    await page.waitForSelector('.blockUI', {'hidden':True})

                    await page.evaluate("listarMatriculasFichaAluno(false)")
                    #await page.click("#aba5")

                    await page.waitForSelector('#tabelaDadosMatricula')

                    tamanho_tabela = int(await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data().length"))
                    for i in range(tamanho_tabela):
                        sit = await page.evaluate("$('#tabelaDadosMatricula').DataTable().rows().data()[%s][17]" % i)
                        if 'arcial' in sit:
                            print(txt_script)
                            print('---------------')
                                    


        






asyncio.get_event_loop().run_until_complete(main())