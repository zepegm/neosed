
from excel import xls
from MySQL import db
from sed_api import get_escolas, start_context, get_alunos_num_classe, consulta_ficha_aluno, get_info_aluno
import json
import os
import sys

linhas_disc = {'ARTE':19, 'BIOLOGIA':23, 'ED. FISICA':20, 'FILOSOFIA':26, 'FISICA':24, 'GEOGRAFIA':27, 'HISTORIA':28, 'L. EST. INGLES':21, 'L.ING':21, 'LING. PORTUGUESA':17, 'MATEMATICA':22, 'ORIE.DE ESTUDOS':42, 'P EXPERIMENTAIS I':34, 'PROJETO DE VIDA':31, 'QUIMICA':25, 'SOCIOLOGIA':29, 'TEC':32, 'PRATICAS EXPERIMENTAIS':35, 'REDAÇÃO E LEITURA':36, 'Redação e Leitura':18, 'ESPORTE-MÚSICA-ARTE':37, 'EDUCAÇÃO FINANCEIRA':38, 'INGLÊS':33, 'Arte e Mídias Digitais':47, 'Filosofia e Sociedade Moderna':51, 'Liderança':48, 'Oratória':50, 'ORIENTAÇÃO DE ESTUDO – LÍNGUA PORTUGUESA':39, 'ORIENTAÇÃO DE ESTUDO – MATEMÁTICA':40, 'ROBOTICA':41, 'Geopolítica':49}

# Lê o arquivo JSON
with open("config_db.json") as f:
    config = json.load(f)

# configuração do server principal
banco = db(config)

num_classe = 291001485
id_oculto = banco.executarConsultaVetor(f"select id_oculto from turma where num_classe = {num_classe}")[0]
planilha = xls("C:\\Users\\giuseppe.manzella\\OneDrive - Secretaria da Educação do Estado de São Paulo (1)\\Formandos 2025\\Fundamental\\Histórico Escolar  9º Ano A.xlsx") # formar conexão com a planilha
indice_planilha = planilha.getActiveSheet()
ra_aluno = "000" + planilha.getValCell('M13', indice_planilha)[:-2].replace('.', '')  # obter o RA do aluno

def mostrar_menu():
    print("\n--- Menu de Escolha ---")
    print("1. Preencher Cabeçalho do Histórico")
    print("2. Preencher info básica da planilha vizinha")
    print("3. Reiniciar Programa")
    print("4. Sair")
    print("-----------------------")

def teste():
    print(' ----- Lista de planilhas ----- ')
    conteudo = os.listdir(r'C:\Users\giuseppe.manzella\Downloads\planilhas')
    print("Conteúdo do diretório:")
    
    for i in range(len(conteudo)):
        print(str(i) + ' - ' + conteudo[i])

    escolha = int(input('Digite o número da planilha que deseja abrir: '))
    try:
        nome_arquivo = conteudo[escolha]
        print('Você escolheu o arquivo: ' + nome_arquivo)
    except IndexError:
        print('Escolha inválida. Tente novamente.')
        return


def reiniciar_programa():
    """Reinicia o script atual, substituindo o processo."""
    print("Reiniciando...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

def write_head():
    auth = {'cookie_SED': banco.executarConsultaVetor("select valor from config where id_config = 'credencial'")[0]}
    context = start_context(auth)
    result_escolas = get_escolas(context)

    id_escola = result_escolas[0]['id']

    alunos = get_alunos_num_classe(context, 2025, id_escola, id_oculto)
    codigos_alunos = consulta_ficha_aluno(context, num_classe)

    for aluno in alunos:
        if aluno['ra'] == ra_aluno:
            print(f"Aluno encontrado: {aluno['nome']}")
            planilha.setValCell('C13', aluno['nome'], indice_planilha)  # Nome do aluno
            planilha.setValCell('E15', aluno['nascimento_data'], indice_planilha)  # Nome do aluno

            # pegar outros detalhes
            aluno_add = {'id':codigos_alunos[aluno['ra']], 'ra':aluno['ra'], 'digito':aluno['ra_dígito'], 'nome':aluno['nome'], 'nascimento':aluno['nascimento_data'].strftime("%d/%m/%Y"), 'matricula':aluno['inicio_matricula'].strftime("%d/%m/%Y"), 'num_chamada':aluno['numero'], 'serie':aluno['serie'], 'desc_sit':aluno['situação'], 'situacao':'Concluinte', 'fim_mat':aluno['fim_matricula'].strftime("%d/%m/%Y"), 'sexo':'M', 'rg':'', 'cpf':'', 'rm':''}
            info_aluno = get_info_aluno(context, aluno_add['id'])
            
            if info_aluno['rg_uf'] is not None:
                if (info_aluno['rg_uf'] == 'SP'):
                    aluno_add['rg'] = info_aluno['rg'][6:8] + '.' + info_aluno['rg'][8:11] + '.' + info_aluno['rg'][11:] + '-' + info_aluno['rg_dígito']
                else:
                    aluno_add['rg'] = info_aluno['rg'] + '-' + info_aluno['rg_dígito'] + '/' + info_aluno['rg_uf']

                if aluno_add['rg'] == '-/':
                    aluno_add['rg'] = ''

            print(info_aluno)
            

            planilha.setValCell('I13', aluno_add['rg'], indice_planilha)  # RG do aluno
            planilha.setValCell('I13', info_aluno['nascimento_uf'], indice_planilha)  # UR do RG do aluno
            planilha.setValCell('E14', info_aluno['nascimento_cidade'], indice_planilha)  # UR do RG do aluno
            planilha.setValCell('M14', 'BRASIL', indice_planilha)  # UR do RG do aluno

def write_notas():
    print(' ----- Lista de planilhas ----- ')
    conteudo = os.listdir(r'C:\Users\giuseppe.manzella\Downloads\planilhas')
    print("Conteúdo do diretório:")
    
    for i in range(len(conteudo)):
        print(str(i) + ' - ' + conteudo[i])

    escolha = int(input('Digite o número da planilha que deseja abrir: '))
    try:
        nome_arquivo = conteudo[escolha]
        print('Você escolheu o arquivo: ' + nome_arquivo)
    except IndexError:
        print('Escolha inválida. Tente novamente.')
        return

    planilha_notas = xls("C:\\Users\\giuseppe.manzella\\Downloads\\planilhas\\" + nome_arquivo)

    ano = int(planilha_notas.getValCell('B5', 1))

    coluna_nota = 'T'

    if ano == int(planilha.getValCell('G63', indice_planilha)):
        coluna_nota = 'P'
    elif ano == int(planilha.getValCell('G64', indice_planilha)):
        coluna_nota = 'R'
    
    total = int(planilha_notas.getCountA("A12:A200", 1))
    total_disc = int(planilha_notas.getCountA("D11:XFD11", 1))

    for linha in range(12, total + 12):
        if int(ra_aluno) == int(planilha_notas.getValCell("A" + str(linha), 1).split('-')[0]):
            for coluna in range(1, total_disc):
                disc = planilha_notas.getValCellNumbes(1, 'D11', 1, coluna)
                nota = planilha_notas.getValCellNumbes(1, 'D' + str(linha), 1, coluna)
                try:
                    #linha_destino = linhas_disc[disc]
                    endereco_destino = coluna_nota + str(linhas_disc[disc])
                    #print(endereco_destino)
                    planilha.setValCell(endereco_destino, nota, indice_planilha)
                except:
                    pass

    planilha_notas.close()
            
def write_info_basic():
    # preencher anos
    for i in range(1, 10):
        ano = planilha.getValCellNumbes("E61", i, 1, indice_planilha + 1)
        planilha.setValCellNumbers("E59", ano, i, 1, indice_planilha)

# Loop principal do programa
while True:
    mostrar_menu()
    escolha = input("Digite o número da sua escolha: ")

    if escolha == '1':
        write_head()
    elif escolha == '2':
        write_info_basic()
    elif escolha == '3':
        reiniciar_programa()
    elif escolha == '4':
        print("Saindo do programa. Até mais!")
        break  # Interrompe o loop e sai do programa        
    else:
        print("\nEscolha inválida. Por favor, digite um número de 1 a 3.")



