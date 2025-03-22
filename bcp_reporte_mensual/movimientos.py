import pandas as pd, re


class MovimientosGenerator:
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
        self.results_df = self.results_df.reset_index()
        self.results_df = self.results_df.sort_values(['date', 'index'])

        self.results_df = self.results_df.replace("", None)
        orden = ["date", "date_v", "desc", "codigo", "lugar", "suc_age", "num_op", "hora", "origen", "tipo", "cargo", "saldos"]
        self.results_df = self.results_df[orden]
        self.results_df.columns = ["FECHA PROC.", "FECHA VALOR", "DESCRIPCION", "MED AT*", "LUGAR", "SUC-AGE", "NUM OP", "HORA", "ORIGEN", "TIPO", "CARGO/ABONO", "SALDO CONTABLE"]

        return self.results_df
