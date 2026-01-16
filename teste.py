from sed_api import start_context, get_matriz_curricular
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
    matriz = get_matriz_curricular(context, 2026, 300205120)

    print(matriz)
except Exception as e:
    print(e)