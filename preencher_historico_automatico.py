from excel import xls
from MySQL import db
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select


planilha = xls() # formar conexão com a planilha
banco = db({'host':"localhost",    # your host, usually localhost
            'user':"root",         # your username
            'passwd':"admin",  # your password
            'db':"neosed"})

options = webdriver.ChromeOptions() 
options.add_experimental_option("debuggerAddress","localhost:9014")

driver = webdriver.Chrome(options)

serie = planilha.getValCell("V19") # pegar série

if serie == 'Total de Aulas':
    serie = planilha.getValCell("T19") 

t4em = {1100:22, 1400:23, 8467:23, 8567:23, 52005:23, 1813:24, 1900:25, 2700:26, 2800:27, 2600:28, 2400:29, 2200:30, 2100:31, 3100:32, 2300:33, 50428:39, 50429:40, 50430:41}
t4em_desc = {'ARTE':24, 'ED. FISICA':25, 'BIOLOGIA':29, 'FILOSOFIA':32, 'FISICA':28, 'GEOGRAFIA':31, 'HISTORIA':30, 'L.ING':23, 'LING. PORTUGUESA':22, 'MATEMATICA':26, 'QUIMICA':27, 'SOCIOLOGIA':33}

em3_2023 = {1100:22, 1813:23, 1900:24, 1400:25, 8467:25, 8567:25, 52005:25, 2700:26, 2400:27, 2600:28, 2800:29, 3100:30, 2100:31, 2200:32, 2300:33, 8427:38, 8441:35, 8465:44, 8466:36}
em3_2023_desc = {'ARTE':23, 'ED. FISICA':24, 'BIOLOGIA':27, 'FILOSOFIA':30, 'FISICA':28, 'GEOGRAFIA':31, 'HISTORIA':32, 'L.ING':25, 'LING. PORTUGUESA':22, 'MATEMATICA':26, 'QUIMICA':29, 'SOCIOLOGIA':33, 'ORIE.DE ESTUDOS':38, 'PROJETO DE VIDA':35, 'TEC':36}

# pegar os dados do aluno e preencher o cabeçalho
if driver.title == 'Ficha do Aluno':
    dados = driver.find_element(By.ID, 'sedUiModalWrapper_1title').text
    lista = dados.split('-')

    nome = lista[0][16:].strip()
    ra = lista[1][7:10] + '.' + lista[1][10:13] + '.' + lista[1][13:16] + '-' + lista[2][0:1]
    data_nascimento = lista[3][18:]
    alt = data_nascimento[6:] + '-' + data_nascimento[3:5] + '-' + data_nascimento[0:2]
    cidade_nascimento = driver.find_element(By.ID, 'CidadeNascimento').get_attribute("value")
    uf_nascimento = driver.find_element(By.ID, 'UFNascimento').get_attribute("value")
    if (uf_nascimento == 'SP'):
        uf_nascimento = 'SÃO PAULO'
    rg = driver.find_element(By.ID, 'RgAluno').get_attribute('value') + '-' + driver.find_element(By.ID, 'DigRgAluno').get_attribute('value')
    rg = rg[6:8] + '.' + rg[8:11] + '.' + rg[11:]


    planilha.setValCell('E14', nome)
    planilha.setValCell('E15', rg)
    planilha.setValCell('P15', ra)
    planilha.setValCell('P16', cidade_nascimento)
    planilha.setValCell('G17', uf_nascimento)
    planilha.setValCell('G16', alt)




match serie:
    case '4º Termo':        
        # pegar todas as séries dos alunos
        ra_aluno = int(planilha.getValCell('P15').replace('.', '')[:-2])
        notas = banco.executarConsulta('select disciplina, media, serie from conceito_final inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = conceito_final.ra_aluno and conceito_final.num_classe = vinculo_alunos_turmas.num_classe where conceito_final.ra_aluno = %s order by serie, disciplina' % ra_aluno)
        
        for nota in notas:

            coluna = 'A'

            match nota['serie']:
                case 1:
                    coluna = 'P'
                case 2:
                    coluna = 'R'
                case 3:
                    coluna = 'T'
                case 4:
                    coluna = 'V'

            endereco = '%s%s' % (coluna, t4em[nota['disciplina']])
            planilha.setValCell(endereco, nota['media'])

        # após tudo isso verificar se o site com o resultado final está aberto e puxar as notas de lá
        if driver.title == 'Ata Resultado Final':
                select = Select(driver.find_element(By.ID, 'filt-turma'))
                selected_option = select.first_selected_option
                turma = selected_option.text

                coluna = "P"

                if turma[0:1] == '2':
                    coluna = 'R'
                elif turma[0:1] == '3':
                    coluna = 'T'
                elif turma[0:1] == '4':
                    coluna = 'V'

                tabela = driver.find_element(By.ID, 'tabela')

                dados = []
                cont = 0

                for row in tabela.find_element(By.CLASS_NAME, 'odd').find_elements(By.TAG_NAME, 'td'):
                    dados.append({'nota':row.text})

                cont = 0

                for row in tabela.find_element(By.TAG_NAME, 'thead').find_elements(By.TAG_NAME, 'th'):
                    if row.text in t4em_desc:
                        print(coluna + str(t4em_desc[row.text]))
                        planilha.setValCell(coluna + str(t4em_desc[row.text]), dados[cont]['nota'].replace(',00', ''))

                    else:
                        print('afs')

                    cont += 1


                nome = dados[2]['nota']
            
        
    case '3º Termo':       
        # pegar todas as séries dos alunos
        ra_aluno = int(planilha.getValCell('P15').replace('.', '')[:-2])
        notas = banco.executarConsulta('select disciplina, media, serie from conceito_final inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = conceito_final.ra_aluno and conceito_final.num_classe = vinculo_alunos_turmas.num_classe where conceito_final.ra_aluno = %s order by serie, disciplina' % ra_aluno)
        
        for nota in notas:

            coluna = 'A'

            match nota['serie']:
                case 1:
                    coluna = 'P'
                case 2:
                    coluna = 'R'
                case 3:
                    coluna = 'T'
                case 4:
                    coluna = 'V'

            endereco = '%s%s' % (coluna, t4em[nota['disciplina']])
            planilha.setValCell(endereco, nota['media'])

        # após tudo isso verificar se o site com o resultado final está aberto e puxar as notas de lá
        if driver.title == 'Ata Resultado Final':
                select = Select(driver.find_element(By.ID, 'filt-turma'))
                selected_option = select.first_selected_option
                turma = selected_option.text

                coluna = "P"

                if turma[0:1] == '2':
                    coluna = 'R'
                elif turma[0:1] == '3':
                    coluna = 'T'
                elif turma[0:1] == '4':
                    coluna = 'V'

                tabela = driver.find_element(By.ID, 'tabela')

                dados = []
                cont = 0

                for row in tabela.find_element(By.CLASS_NAME, 'odd').find_elements(By.TAG_NAME, 'td'):
                    dados.append({'nota':row.text})

                cont = 0

                for row in tabela.find_element(By.TAG_NAME, 'thead').find_elements(By.TAG_NAME, 'th'):
                    if row.text in t4em_desc:
                        print(coluna + str(t4em_desc[row.text]))
                        planilha.setValCell(coluna + str(t4em_desc[row.text]), dados[cont]['nota'].replace(',00', ''))

                    else:
                        print('afs')

                    cont += 1


                nome = dados[2]['nota']        

    case '3ª Série':       
        # pegar todas as séries dos alunos
        ra_aluno = int(planilha.getValCell('P15').replace('.', '')[:-2])
        notas = banco.executarConsulta('select disciplina, media, serie from conceito_final inner join vinculo_alunos_turmas on vinculo_alunos_turmas.ra_aluno = conceito_final.ra_aluno and conceito_final.num_classe = vinculo_alunos_turmas.num_classe where conceito_final.ra_aluno = %s order by serie, disciplina' % ra_aluno)
        
        print(notas)

        for nota in notas:

            coluna = 'A'

            match nota['serie']:
                case 1:
                    coluna = 'P'
                case 2:
                    coluna = 'R'
                case 3:
                    coluna = 'T'
                case 4:
                    coluna = 'V'

            endereco = '%s%s' % (coluna, em3_2023[nota['disciplina']])
            print(endereco)
            planilha.setValCell(endereco, nota['media'])

        # após tudo isso verificar se o site com o resultado final está aberto e puxar as notas de lá
        if driver.title == 'Ata Resultado Final':
                select = Select(driver.find_element(By.ID, 'filt-turma'))
                selected_option = select.first_selected_option
                turma = selected_option.text

                coluna = "P"

                if turma[0:1] == '2':
                    coluna = 'R'
                elif turma[0:1] == '3':
                    coluna = 'T'
                elif turma[0:1] == '4':
                    coluna = 'V'

                tabela = driver.find_element(By.ID, 'tabela')

                dados = []
                cont = 0

                for row in tabela.find_element(By.CLASS_NAME, 'odd').find_elements(By.TAG_NAME, 'td'):
                    dados.append({'nota':row.text})

                cont = 0

                for row in tabela.find_element(By.TAG_NAME, 'thead').find_elements(By.TAG_NAME, 'th'):
                    if row.text in em3_2023_desc:
                        print(coluna + str(em3_2023_desc[row.text]))
                        planilha.setValCell(coluna + str(em3_2023_desc[row.text]), dados[cont]['nota'].replace(',00', ''))

                    else:
                        print('afs')

                    cont += 1


                nome = dados[2]['nota']        


