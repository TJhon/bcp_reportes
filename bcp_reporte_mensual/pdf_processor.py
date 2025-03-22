import fitz
import os, pandas as pd
from dataclasses import dataclass


@dataclass
class PDFProcessor:
    pdf_path: str
    password: str = None

    def desbloquear(self):
        doc = fitz.open(self.pdf_path)

        if doc.is_encrypted:
            if doc.authenticate(self.password):
                print("PDF desbloqueado correctamente.")
            else:
                print("Contraseña incorrecta o no se pudo desbloquear el PDF.")
                return

        new_doc = fitz.open()
        for page_num in range(len(doc) - 1):
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        self.new_pdf = new_doc
        self.n_pages = len(doc) - 1

    def extract_text_to_df(self):
        doc = self.new_pdf
        data = []

        for page_num in range(len(doc)):
            n_line = 1
            page = doc.load_page(page_num)
            text = page.get_text("text")

            lines = text.split('\n')
            for line in lines:
                data.append({'page': page_num + 1, 'nline': n_line, 'line': line})
                n_line += 1

        return pd.DataFrame(data)

    def to_pandas(self):
        self.desbloquear()
        return self.extract_text_to_df()

import fitz  # PyMuPDF
import pandas as pd
from dataclasses import dataclass
from io import BytesIO

@dataclass
class PDFProcessorStreamlit:
    pdf_file: BytesIO  # Cambia esto para aceptar un archivo en memoria
    password: str = None

    def desbloquear(self):
        # Usar el archivo en memoria directamente
        doc = fitz.open(stream=self.pdf_file.read(), filetype="pdf")

        if doc.is_encrypted:
            if doc.authenticate(self.password):
                print("PDF desbloqueado correctamente.")
            else:
                print("Contraseña incorrecta o no se pudo desbloquear el PDF.")
                return

        new_doc = fitz.open()
        for page_num in range(len(doc) - 1):
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        self.new_pdf = new_doc
        self.n_pages = len(doc) - 1

    def extract_text_to_df(self):
        doc = self.new_pdf
        data = []

        for page_num in range(len(doc)):
            n_line = 1
            page = doc.load_page(page_num)
            text = page.get_text("text")

            lines = text.split('\n')
            for line in lines:
                data.append({'page': page_num + 1, 'nline': n_line, 'line': line})
                n_line += 1

        return pd.DataFrame(data)

    def to_pandas(self):
        self.desbloquear()
        return self.extract_text_to_df()

class DataProcessor:
    def __init__(self, df):
        self.df = df

    def process_data(self):
        self.df['is_date'] = self.df['line'].str.strip().str.match(r'^\d{2}-\d{2}').astype(int)
        self.df['is_saldo'] = self.df['line'].str.strip().str.match(r'(\d+,)*\d+\.\d{2}-?$').astype(int)
        group_page = self.df.groupby('page')
        details_dict = dict()
        saldo_dict = dict()
        i_rel = []

        for _n, group_df in group_page:
            details_df = group_df.query('is_date == 1')
            i_rel.extend(details_df.index.values)
            max_details = details_df.nline.max()
            saldo_f = group_df[(group_df['is_saldo'] == 1) & (group_df['nline'] > max_details)]
            i_rel.extend(saldo_f.index.values)
            details_dict[_n] = details_df.line.values
            saldo_dict[_n] = saldo_f.line.values

        details = []
        saldos = []
        for i in range(self.df['page'].max()):
            details.extend(details_dict[i + 1])
            saldos.extend(saldo_dict[i + 1])

        return pd.DataFrame({"details": details, "saldos": saldos}), i_rel





# @dataclass
# class PDFprocessor:
#     pdf_path: str
#     password: str = None

#     def desbloquear(self):
#         doc = fitz.open(self.pdf_path)

#         if doc.is_encrypted:
#             # Intentar desbloquear el PDF con la contraseña proporcionada
#             if doc.authenticate(self.password):
#                 print("PDF desbloqueado correctamente.")
#             else:
#                 print("Contraseña incorrecta o no se pudo desbloquear el PDF.")
#                 return

#         # Crear un nuevo documento PDF para guardar las páginas desbloqueadas
#         new_doc = fitz.open()

#         # Copiar todas las páginas excepto la última al nuevo documento
#         for page_num in range(len(doc) - 1):
#             new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

#         self.new_pdf = new_doc
#         self.n_pages = len(doc) - 1
#     def extract_text_to_df(self):
#         doc = self.new_pdf
#         data = []

#         # Iterar sobre cada página del documento
#         for page_num in range(len(doc)):
#             n_line = 1
#             page = doc.load_page(page_num)
#             text = page.get_text("text")

#             # Dividir el texto en líneas y agregar al DataFrame
#             lines = text.split('\n')
#             for line in lines:
#                 data.append({'page': page_num + 1, 
#                              'nline': n_line,'line': line})
#                 n_line += 1

#         # Crear un DataFrame con los datos extraídos
#         df = pd.DataFrame(data)
#         return df
#     def to_pandas(self):
#         self.desbloquear()
#         df = self.extract_text_to_df()
#         return df

# df = PDFprocessor('./pdf_sample/EECC_Abr2023_182.pdf').to_pandas()
# print(df)