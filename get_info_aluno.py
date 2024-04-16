from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

from excel import xls
from MySQL import db

# primeira etapa, pegar RA
banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"Yasmin",  # your password
            'db':"neosed"})

plan = xls('Documentação 1ª série.xlsx')

nome = plan.getValCell('1A', 'A%s' % plan.getActiveRow()) 
ra = banco.executarConsulta("select ra from aluno where nome like '%s'" % nome)[0]['ra']

print(ra)

# segunda etapa, acessar site
options = webdriver.ChromeOptions() 
options.add_experimental_option("debuggerAddress","localhost:9014")

driver = webdriver.Chrome(options=options)

driver.execute_script('document.getElementById("txtRa").value = ""')
campo_ra = driver.find_element(By.ID, 'txtRa')
campo_ra.send_keys(ra)
campo_ra.send_keys(Keys.ENTER)

time.sleep(4)
link = driver.find_element(By.XPATH, "//td[@class='colVisualizar']/a")
driver.execute_script(link.get_attribute('onclick'))
time.sleep(8)

aba = driver.find_element(By.ID, "aba5").find_element(By.TAG_NAME, 'a')
driver.execute_script(aba.get_attribute('onclick'))
#driver.execute_script('listarMatriculasFichaAluno(false)')
time.sleep(4)
aba.click()

tabela = driver.find_element(By.ID, 'tabelaDadosMatricula').find_element(By.TAG_NAME, 'tbody')

lista = []

for row in tabela.find_elements(By.TAG_NAME, 'tr'):
    colunas = row.find_elements(By.TAG_NAME, 'td')
    item = {}
    coluna = 0
    for col in colunas:
        if coluna == 0:
            item['ano'] = col.text
        elif coluna == 6:
            item['escola'] = col.text
        elif coluna == 8:
            item['ensino'] = col.text
        elif coluna == 11:
            item['turma'] = col.text

        coluna += 1

    lista.append(item)


last_id = 0

for item in lista:
    if item['ensino'] == '14':
        last_id = lista.index(item)

print(lista[last_id])

if lista[last_id]['escola'] == 'ALICE VILELA GALVAO PROFA EMEF':
    plan.setValCell('1A', 'B%s' % plan.getActiveRow(), 'Fund. Município')
