# testar a sed_api

import json
from sed_api import start_context, get_escolas, get_unidades, get_classes, get_alunos_num_classe
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

result_classes = get_classes(context, 2026, id_escola, id_unidade)

turmas = banco.executarConsulta('select num_classe, id_oculto, nome_turma, duracao.descricao as desc_duracao from turma inner join duracao on duracao.id = turma.duracao where ano = %s order by duracao, tipo_ensino, nome_turma' % 2026)
for turma in turmas:
    #socketio.emit('update_info', '<b>Atualizando dados da %s - %s (%s)</b>' % (turma['nome_turma'], turma['desc_duracao'], ano))
    result = get_alunos_num_classe(context, 2026, id_escola, turma['id_oculto'])
    print('--------------------------------')
    print(result)