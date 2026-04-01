# testar a sed_api

import json
from sed_api import start_context, get_escolas, get_unidades, get_classes, get_alunos_num_classe, get_alunos_codigo, get_info_aluno
from MySQL import db

# Lê o arquivo JSON
with open("config_db.json") as f:
    config = json.load(f)

# configuração do server principal
banco = db(config)

auth = {'cookie_SED': banco.executarConsultaVetor("select valor from config where id_config = 'credencial'")[0]}

context = start_context(auth)
result_escolas = get_escolas(context)

id_escola = result_escolas[0]['id']
result_unidades = get_unidades(context, id_escola)
id_unidade = result_unidades[0]['id']

print(id_unidade)

# buscar aluno no banco
#ra_aluno = '000113751898'

# buscar codigo da turma da aluna
#info_turma = banco.executarConsulta("select ano, id_oculto from turma inner join vinculo_alunos_turmas on vinculo_alunos_turmas.num_classe = turma.num_classe and vinculo_alunos_turmas.ra_aluno = %s" % ra_aluno)[0]

#print(info_turma)

#codigos_alunos = get_alunos_codigo(context, info_turma['ano'], id_escola, info_turma['id_oculto'])

#codigo = codigos_alunos[ra_aluno]

#dados_aluno = get_info_aluno(context, codigo)

#print(dados_aluno)