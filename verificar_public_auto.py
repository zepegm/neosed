from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import subprocess
from MySQL import db


lista = [108573294, 106237811, 109775902, 106495905, 109636701, 108573248, 109636674, 111654371, 105930695, 105930701, 109771877, 109502331, 109599645, 108995744, 108528790, 105440179, 110681287, 109871999, 109079495, 108574566, 49772486, 108573289, 110443243]
banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"Yasmin",  # your password
            'db':"neosed"})

#run in cmd - "C:\Program Files\Google\Chrome\Application\chrome.exe" -remote-debugging-port=9014 --user-data-dir="C:\ChromeData"
#subprocess.run(r'"C:\Program Files\Google\Chrome\Application\chrome.exe" -remote-debugging-port=9014 --user-data-dir="C:\ChromeData"')

#time.sleep(3)

options = webdriver.ChromeOptions() 
options.add_experimental_option("debuggerAddress","localhost:9014")

driver = webdriver.Chrome(options)

#driver.get("https://sed.educacao.sp.gov.br/SedCon/ConsultaPublicacao/Index")

#time.sleep(3)

label = driver.find_element(By.CLASS_NAME, "tit")
txtRgFiltro = driver.find_element(By.ID, 'txtRgFiltro')
txtDigRgFiltro = driver.find_element(By.ID, 'txtDigRgFiltro')
botao = driver.find_element(By.ID, 'btnPesquisar')

for ra in lista:
    aluno = banco.executarConsulta('select nome, rg from aluno where ra = %s' % ra)[0]
    rg = aluno['rg'].replace('.', '')[:-2]

    driver.execute_script("arguments[0].innerText = '%s, RG: %s'" % (aluno['nome'], aluno['rg']), label)
    driver.execute_script("arguments[0].value = '%s'" % rg, txtRgFiltro)
    driver.execute_script("arguments[0].value = '%s'" % aluno['rg'][-1:], txtDigRgFiltro)

    botao.click()

    time.sleep(3)
    
    #print(aluno)


# provar a eficácio do meu programa
driver.execute_script("arguments[0].innerText = 'GIUSEPPE GARCEZ MANZELLA, RG: 49.087.779-5'", label)
driver.execute_script("arguments[0].value = '49087779'", txtRgFiltro)
driver.execute_script("arguments[0].value = '5'", txtDigRgFiltro)

botao.click()