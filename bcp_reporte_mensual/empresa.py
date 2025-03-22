
import pandas as pd
import re


class DetailsEmpresa:
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
        if len(text_lower) > 50: return None
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