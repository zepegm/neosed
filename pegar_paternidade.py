import asyncio
from pyppeteer import launch
from MySQL import db

banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"admin",  # your password
            'db':"neosed"})

turmas = banco.executarConsulta('select * from turma where ano = 2024')

lista_sem_pai = []


async def main():

    browser = await launch(
        executablePath="/usr/bin/google-chrome-stable",
        headless=True,
        dumpio=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
        ],
    )

    page = await browser.newPage()

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

    for turma in turmas:
        alunos = banco.executarConsulta('select * from vinculo_alunos_turmas where num_classe = %s' % turma['num_classe'])

        for aluno in alunos:
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
            await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#txtRa', aluno['ra_aluno']) 
            await page.waitForSelector('.blockUI', {'hidden':True})
            await page.evaluate('''(selector, value) => { document.querySelector(selector).value = value; }''', '#TipoConsultaFichaAluno', 1) 
            await page.click("#btnPesquisar")
            await page.waitForSelector('#tabelaDados', {'visible': True})
            script = await page.evaluate("document.getElementsByClassName('colVisualizar')[1].getElementsByTagName('a')[0].getAttribute('onclick')")
            await page.evaluate(script)
            await page.waitForSelector('#sedUiModalWrapper_1', {'visible': True})

            # pegar dados do aluno para inserir na planilha
            pai = await page.evaluate("document.getElementById('NomePai').value")
            nome = await page.evaluate("document.getElementById('NomeAluno').value")

            print('aluno: %s' % nome)
            print('pai: %s' % pai)
            print('--------------------------------')

            if pai == '':

                lista_sem_pai.append({'aluno':nome, 'pai':pai})


    print(lista_sem_pai)
    await browser.close()



asyncio.get_event_loop().run_until_complete(main())