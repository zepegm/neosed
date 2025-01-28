import fitz  # PyMuPDF
import pandas as pd
import json

def extract_table_from_pdf(pdf_path, page_number):
    # Abre o PDF
    pdf_document = fitz.open(pdf_path)
    page = pdf_document.load_page(page_number - 1)  # Carrega a página (0-indexed)

    # Extrai o texto da página
    text = page.get_text("text")

    # Processa o texto para extrair a tabela
    rows = text.split('\n')
    table_data = [row.split() for row in rows if row.strip()]

    # Converte a tabela em um DataFrame do pandas
    df = pd.DataFrame(table_data[1:], columns=table_data[0])

    # Converte o DataFrame em JSON
    json_data = df.to_json(orient='records', force_ascii=False)

    return json_data

# Exemplo de uso
pdf_path = 'static/docs/boletim_SED.pdf'
page_number = 1  # Número da página onde a tabela está localizada
json_data = extract_table_from_pdf(pdf_path, page_number)
print(json_data)