#get boletim

from excel import xls
from MySQL import db
from sed_api import get_escolas, start_context, get_alunos_num_classe, consulta_ficha_aluno, get_info_aluno, get_info_boletim
import json
import os
import sys

# Lê o arquivo JSON
with open("config_db.json") as f:
    config = json.load(f)

# configuração do server principal
banco = db(config)

auth = {'cookie_SED': banco.executarConsultaVetor("select valor from config where id_config = 'credencial'")[0]}
context = start_context(auth)

ano = '2023'
ra_aluno = '000114312625'
digito_ra = '7'

result_boletim = get_info_boletim(context, ra_aluno, digito_ra, ano)

disciplinas = result_boletim['oBoletim']['TpsEnsino'][0]['Unidades'][0]['Disciplinas']

for disc in disciplinas:
    print(disc['CdDisciplina'])
