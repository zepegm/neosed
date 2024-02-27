import asyncio
from pyppeteer import launch

async def generate_pdf(url, pdf_path):
    browser = await launch()
    page = await browser.newPage()
    
    await page.goto(url, {'waitUntil':'networkidle2'})
    #await page.setViewport({'width': 800, 'height': 600})
    #await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'margin':{'top':18}})
    await page.pdf({'path': pdf_path, 'format':'A4', 'scale':1, 'printBackground':True})
    #await page.pdf({'path': pdf_path, 'width ':'100', 'height':'900'})
    

    
    await browser.close()

    return pdf_path

# Run the function
def get_pdf():
    return asyncio.get_event_loop().run_until_complete(generate_pdf('http://localhost/render_lista?tipo=turma&num_classe=280612383', 'static/docs/lista.pdf'))


get_pdf()