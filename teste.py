from sed_api import start_context, get_matriz_curricular, get_grade
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

matriz = get_matriz_curricular(context, 2025, 291001493)

grade = get_grade(context, 291001493)

print(grade)
