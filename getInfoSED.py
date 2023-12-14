from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager
#from read_csv import getValue, save
import time

def buscarCPF(RA, cont):

    userdatadir = 'C:/Users/giuseppe.manzella/AppData/Local/Google/Chrome/User Data'    
    options = webdriver.ChromeOptions() 
    options.add_argument(f"--user-data-dir={userdatadir}")

    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    driver.implicitly_wait(0.5)

    #launch URL
    driver.get("https://sed.educacao.sp.gov.br/NCA/FichaAluno/Index")
    time.sleep(8)

    lista = []

    try:
        driver.execute_script("document.getElementById('fieldSetRA').style.display = '';")
        driver.execute_script("document.getElementById('TipoConsultaFichaAluno').value = '1';")

        for item in RA:
            driver.execute_script('document.getElementById("txtRa").value = ""')
            ra = driver.find_element(By.ID, 'txtRa')
            ra.send_keys(item)
            ra.send_keys(Keys.RETURN)
            time.sleep(4)

            # pegar o código
            link = driver.find_element(By.XPATH, "//td[@class='colVisualizar']/a")
            driver.execute_script(link.get_attribute('onclick'))

            time.sleep(8)

            cpf = driver.find_element(By.ID, 'CpfAluno')
            rg = driver.find_element(By.ID, 'RgAluno')
            digito = driver.find_element(By.ID, 'DigRgAluno')
            driver.find_element(By.ID, 'sedUiModalWrapper_' + str(cont) + 'close').click()
            
            desc_rg = rg.get_attribute('value')

            info = {'cpf':cpf.get_attribute('value'), 'rg':'%s.%s.%s' % (desc_rg[-8:-6], desc_rg[-6:-3], desc_rg[-3:]) + '-' + digito.get_attribute('value')}
            print(info)
            lista.append(info)
            cont += 1
    except:
        print("Loading took too much time!")
    
    return lista
