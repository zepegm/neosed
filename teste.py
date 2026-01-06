from sed_api import start_context, get_escolas, get_unidades, get_classes, get_info_aluno, get_alunos_num_classe, consulta_ficha_aluno, get_matriz_curricular, get_grade, get_professor_info
from MySQL import db
import json

# Lê o arquivo JSON
with open("config_db.json") as f:
    config = json.load(f)

# configuração do server principal
banco = db(config)


auth = {'cookie_SED': banco.executarConsultaVetor("select valor from config where id_config = 'credencial'")[0]}

try:
    context = start_context(auth)
    result_escolas = get_escolas(context)

    id_escola = result_escolas[0]['id']
    result_unidades = get_unidades(context, id_escola)
    id_unidade = result_unidades[0]['id']

    # a partir daqui será dividido as tarefas dependendo do objetivo desejado

    result_classes = get_classes(context, 2025, id_escola, id_unidade)
    
    for classe in result_classes:
        if int(classe['id_b']) == 300273230:
            print(classe['id'])

    print("deu certo")
except Exception as e:
    print(e)