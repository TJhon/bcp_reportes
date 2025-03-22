import fitz
import pandas as pd
import re
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

class ResultGenerator:
    def __init__(self, results_df):
        self.results_df = results_df

    def split_date_description(self, value):
        match = re.match(r"(.*?\s)(VEN|CAJ|POS|TLC|INT|BPT|BPI)(\s.*)", value)
        if match:
            return match.groups()
        return value, '', ''

    def split_desc_tipo_value(self, value):
        match = re.match(r"(.*?)(\b\d{4}\b)(.*)", value)
        if match:
            return match.groups()
        return value, '', ''

    def split_suc_age(self, value):
        match = re.match(r"(.*?\s)(.{3}-.{3})(.*)", value)
        if match:
            return match.groups()
        return value, '', ''

    def split_hora(self, value):
        match = re.search(r"(\S+\s*)(\d{2}:\d{2})?(\s*\S*)", value)
        if match:
            return match.groups()
        return value, '', ''

    def convertir_a_flotante(self, cadena):
        cadena_sin_comas = cadena.replace(",", "").replace("-", "")
        try:
            numero = float(cadena_sin_comas)
            if "-" in cadena:
                numero = -numero
            return numero
        except ValueError:
            return None

    def generate_results(self):
        self.results_df[['antes_codigo', 'codigo', 'despues_codigo']] = self.results_df['details'].apply(
            lambda x: pd.Series(self.split_date_description(x)))
        self.results_df[['date', 'date_v', 'desc']] = self.results_df['antes_codigo'].apply(
            lambda x: pd.Series([x[:5], x[5:-23], x[-23:]]))
        self.results_df.drop(columns=['antes_codigo', 'details'], inplace=True)

        self.results_df[['ref', 'tipo', 'cargo']] = self.results_df['despues_codigo'].apply(
            lambda x: pd.Series(self.split_desc_tipo_value(x)))
        self.results_df.drop(columns=['despues_codigo'], inplace=True)

        self.results_df[['lugar', 'suc_age', 'ref1']] = self.results_df['ref'].apply(
            lambda x: pd.Series(self.split_suc_age(x)))
        self.results_df.drop(columns=['ref'], inplace=True)

        self.results_df[['num_op', 'hora', 'origen']] = self.results_df['ref1'].apply(
            lambda x: pd.Series(self.split_hora(x)))
        self.results_df.drop(columns=['ref1'], inplace=True)

        flotantes = ['saldos', 'cargo']
        for numeric_col in flotantes:
            self.results_df[numeric_col] = self.results_df[numeric_col].apply(self.convertir_a_flotante)

        self.results_df = self.results_df.replace("", None)
        orden = ["date", "date_v", "desc", "codigo", "lugar", "suc_age", "num_op", "hora", "origen", "tipo", "cargo", "saldos"]
        self.results_df = self.results_df[orden]
        self.results_df.columns = ["FECHA PROC.", "FECHA VALOR", "DESCRIPCION", "MED AT*", "LUGAR", "SUC-AGE", "NUM OP", "HORA", "ORIGEN", "TIPO", "CARGO/ABONO", "SALDO CONTABLE"]

        return self.results_df

class DetailsExtractor:
    def __init__(self, df, i_rel, n_pages):
        self.df = df
        self.i_rel = i_rel
        self.n_pages = n_pages

    def detect_num_cuenta(self, text):
        match = re.findall(r'\d+(?:-\d+)+', text)
        return match[0] if match else None

    def detect_type_cuenta(self, text):
        if pd.isna(text) or not isinstance(text, str):
            return None
        text_lower = text.lower()
        if "cuenta" in text_lower:
            cuenta_pos = text_lower.find("cuenta")
            after_cuenta = text[(cuenta_pos + 6):].strip()
            return after_cuenta.capitalize() if after_cuenta else None
        return None

    def detect_dir_cuenta(self, text):
        if pd.isna(text) or not isinstance(text, str):
            return None
        return 1 if "primavera" in text.lower() else None

    def detect_moneda(self, text):
        monedas = {"soles": "Soles", "dolares": "Dólares"}
        return monedas.get(text.lower(), None)

    def extract_details(self):
        details = self.df[~self.df.index.isin(self.i_rel)]
        details['clean_line'] = details['line'].apply(lambda x: str(x).strip().lower())
        detalles_repetidos = details.value_counts('clean_line').reset_index().query('count == @self.n_pages')

        range_details = details[(details['clean_line'].isin(detalles_repetidos['clean_line']))].query('page == 1')
        range_details['acc_num'] = range_details['clean_line'].apply(self.detect_num_cuenta)
        range_details['type_acc'] = range_details['clean_line'].apply(self.detect_type_cuenta)
        range_details['moneda'] = range_details['clean_line'].apply(self.detect_moneda)
        range_details['direccion'] = range_details['clean_line'].apply(self.detect_dir_cuenta)

        i_direccion_ubicacion = range_details.dropna(subset='direccion').nline.values[0]
        name_company = range_details[range_details.nline == i_direccion_ubicacion - 1][['line']].to_dict('records')
        info_details = range_details.dropna(subset=['acc_num', 'type_acc', 'moneda'], how='all')

        info_ref = info_details[['acc_num', 'type_acc', 'moneda']]
        info_ref['acc_name'] = name_company[0].get('line')
        return info_ref.melt(var_name='variable', value_name='valor').dropna().drop_duplicates()

### Uso de las clases

# pdf_processor = PDFProcessor('./pdf_sample/EECC_Dic2022_182.pdf')
# df = pdf_processor.to_pandas()

# data_processor = DataProcessor(df)
# results_df, i_rel = data_processor.process_data()

# result_generator = ResultGenerator(results_df)
# final_results = result_generator.generate_results()

# details_extractor = DetailsExtractor(df, i_rel, pdf_processor.n_pages)
# details_results = details_extractor.extract_details()

# print(final_results)
# print(details_results)