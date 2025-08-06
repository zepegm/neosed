from sed_api import start_context, get_escolas, get_unidades, get_classes, get_alunos
import openpyxl
import unicodedata

def limpar_texto(texto):
    if isinstance(texto, str):
        texto = unicodedata.normalize("NFKD", texto)  # remove acentos e normaliza
        return texto.replace('\u202f', ' ').strip()
    return texto

# Passo 1: Autenticar com cookie SED
auth = {
    'cookie_SED': 'PBIbKvEDz+SHGRxWFkT4EKgYMqwc+YchGZQu3CAvbdkeX7NH2e3Zag=='
}
context = start_context(auth)

# Passo 2: Obter os dados da unidade
result_escolas = get_escolas(context)

id_escola = result_escolas[0]['id'] if result_escolas else None

if id: 
    result_unidades = get_unidades(context, id_escola)
    id_unidade = result_unidades[0]['id'] if result_unidades else None

    if id_unidade:
        result_classes = get_classes(context, 2025, id_escola, id_unidade)
        for classe in result_classes:
            result_alunos = get_alunos(context, 2025, id_escola, classe['id'])
            #print(result_alunos)

#print(result_escolas)
