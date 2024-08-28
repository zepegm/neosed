from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


import time
import subprocess
from MySQL import db



banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"Yasmin",  # your password
            'db':"neosed"})

num_classe = 286441977

lista = banco.executarConsulta(r"select ra_aluno, aluno.digito_ra, aluno.nome, DATE_FORMAT(vinculo_alunos_turmas.matricula, '%d/%m/%Y') as matricula, DATE_FORMAT(aluno.nascimento, '%d/%m/%Y') as nasc from vinculo_alunos_turmas inner join aluno on aluno.ra = vinculo_alunos_turmas.ra_aluno where num_classe = " +  str(num_classe) + " and situacao = 1 order by num_chamada")

#run in cmd - "C:\Program Files\Google\Chrome\Application\chrome.exe" -remote-debugging-port=9014 --user-data-dir="C:\ChromeData"
#subprocess.run(r'"C:\Program Files\Google\Chrome\Application\chrome.exe" -remote-debugging-port=9014 --user-data-dir="C:\ChromeData"')

#time.sleep(3)

options = webdriver.ChromeOptions() 
options.add_experimental_option("debuggerAddress","localhost:9014")

driver = webdriver.Chrome(options)

#driver.get("https://sed.educacao.sp.gov.br/SedCon/ConsultaPublicacao/Index")

#time.sleep(3)

txt_RA = driver.find_element(By.ID, 'RA_Numero')
txt_Digito = driver.find_element(By.ID, 'RA_Digito')
txt_Nascimento = driver.find_element(By.ID, 'DataNascimento')


botao = driver.find_element(By.ID, 'btnPesquisar_2025')

for aluno in lista:
    driver.execute_script("arguments[0].value = '%s'" % str(aluno['ra_aluno']).zfill(12), txt_RA)
    driver.execute_script("arguments[0].value = '%s'" % aluno['digito_ra'], txt_Digito)
    driver.execute_script("arguments[0].value = '%s'" % aluno['nasc'], txt_Nascimento)

    botao.click()

    try:
        tabela = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "tabelaDados"))
        )

        ano = int(tabela.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'td')[0].text)

        if ano < 2025:
            print('%s-%s - %s' % (aluno['ra_aluno'], aluno['digito_ra'], aluno['nome']))        

    except:
        driver.quit()

    
    #print(aluno)