import json
from MySQL import db
from sed_api import start_context, get_escolas, get_unidades, get_classes, get_info_aluno, get_alunos_num_classe, consulta_ficha_aluno, get_matriz_curricular, get_grade, get_professor_info

# Lê o arquivo JSON
with open("config_db.json") as f:
    config = json.load(f)

# configuração do server principal
banco = db(config)

auth = {'cookie_SED': banco.executarConsultaVetor("select valor from config where id_config = 'credencial'")[0]}
context = start_context(auth)

# pegar turmas
turmas = banco.executarConsulta("select * from turma where ano = 2025 and tipo_ensino in (1, 3) order by tipo_ensino, nome_turma")

# pegar lista de alunos por turma
for turma in turmas:
    #alunos = banco.executarConsulta(f"select ra_aluno, nome from vinculo_alunos_turmas inner join aluno on aluno.ra = ra_aluno where num_classe = {turma['num_classe']} and situacao = 1 order by nome")
    
    # agora que eu tenho o aluno e seu RA preciso puxar as informações da SED
    result_escolas = get_escolas(context)
    id_escola = result_escolas[0]['id']
    alunos = get_alunos_num_classe(context, 2025, id_escola, turma['id_oculto'])
    codigos_alunos = consulta_ficha_aluno(context, turma['num_classe'])

    print('Turma:', turma['nome_turma'], ' - Alunos encontrados na SED:', len(alunos))

    for aluno in alunos:
        aluno_add = {'id':codigos_alunos[aluno['ra']], 'ra':aluno['ra'], 'digito':aluno['ra_dígito'], 'nome':aluno['nome'], 'nascimento':aluno['nascimento_data'].strftime("%d/%m/%Y"), 'matricula':aluno['inicio_matricula'].strftime("%d/%m/%Y"), 'num_chamada':aluno['numero'], 'serie':aluno['serie'], 'desc_sit':aluno['situação'], 'fim_mat':aluno['fim_matricula'].strftime("%d/%m/%Y"), 'sexo':'M', 'rg':'', 'cpf':'', 'rm':''}
        info_aluno = get_info_aluno(context, aluno_add['id'])

        if info_aluno['nome_pai'] == '':
            print(aluno['nome'] + " - RA: " + aluno['ra']  + " - Nome do Pai AUSENTE!")
        else:
            print(aluno['nome'] + " - RA: " + aluno['ra']  + " - Nome do Pai: " + info_aluno['nome_pai'])