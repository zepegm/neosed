#get boletim

from excel import xls
from MySQL import db
from sed_api import get_escolas, start_context, get_alunos_codigo, get_alunos, consulta_ficha_aluno, get_info_aluno, get_info_boletim
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

codigo_aluno = '10064667'

info = get_info_aluno(context, codigo_aluno)

print(codigo_aluno)