from sed_api import start_context, get_matriz_curricular, get_grade, get_professor_info
import openpyxl
import unicodedata

def limpar_texto(texto):
    if isinstance(texto, str):
        texto = unicodedata.normalize("NFKD", texto)  # remove acentos e normaliza
        return texto.replace('\u202f', ' ').strip()
    return texto

# Passo 1: Autenticar com cookie SED
auth = {
    'cookie_SED': '64sKQsADm2f7lqx8006QHLMx974K5funMHKQZg=='
}
context = start_context(auth)

dados_prof = get_professor_info(context, '27632200886', '')

print(dados_prof)