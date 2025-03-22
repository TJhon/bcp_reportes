import streamlit as st
import pandas as pd
from io import BytesIO
import os
import zipfile
from bcp_reporte_mensual import *

# Función para leer el archivo generado y convertirlo en un objeto descargable
def get_downloadable_file(filename):
    with open(filename, "rb") as file:
        file_data = file.read()
    os.remove(filename)  # Eliminar el archivo después de leerlo
    return file_data

# Función para procesar un archivo PDF y devolver los resultados
def process_pdf(uploaded_file):
    pdf_processor = PDFProcessorStreamlit(uploaded_file)
    df = pdf_processor.to_pandas()

    data_processor = DataProcessor(df)
    results_df, i_rel = data_processor.process_data()

    result_generator = MovimientosGenerator(results_df)
    final_results = result_generator.generate_results()

    details_extractor = DetailsEmpresa(df, i_rel, pdf_processor.n_pages)
    details_results = details_extractor.extract_details()

    return final_results, details_results

# Función para generar el archivo XLSX y obtener los datos descargables
def generate_and_get_xlsx(final_results, details_results):
    # Obtener los valores para b1, b2, b3
    b1 = details_results[details_results['variable'] == 'acc_num']['valor'].values[0]
    b2 = details_results[details_results['variable'] == 'moneda']['valor'].values[0]
    b3 = details_results[details_results['variable'] == 'type_acc']['valor'].values[0]

    # Generar el archivo XLSX usando la función existente
    generate_xlsx(final_results, b1, b2, b3)  # Esto guarda el archivo en "output.xlsx"

    # Leer el archivo generado y convertirlo en un objeto descargable
    return get_downloadable_file("output.xlsx")

# Página principal para procesar un solo archivo PDF
def main_page():
    st.title("Procesador de PDFs - Página Principal")
    uploaded_file = st.file_uploader("Sube un archivo PDF", type="pdf")

    if uploaded_file is not None:
        if st.button("Recolectar Datos"):
            # Procesar el PDF
            final_results, details_results = process_pdf(uploaded_file)

            # Mostrar los resultados
            st.subheader("Resultados Finales")
            st.dataframe(final_results)

            st.subheader("Detalles del PDF")
            st.dataframe(details_results)

            # Generar y descargar el archivo XLSX
            xlsx_data = generate_and_get_xlsx(final_results, details_results)
            st.download_button(
                label="Descargar Resultados en XLSX",
                data=xlsx_data,
                file_name="resultados_finales.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Página para procesar múltiples archivos PDF
def multi_file_page():
    st.title("Procesador de PDFs - Múltiples Archivos")
    uploaded_files = st.file_uploader("Sube múltiples archivos PDF", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        if st.button("Procesar y Descargar Todos"):
            progress_bar = st.progress(0)
            total_files = len(uploaded_files)
            results = []

            for i, uploaded_file in enumerate(uploaded_files):
                # Procesar cada PDF
                final_results, details_results = process_pdf(uploaded_file)
                results.append((final_results, details_results))

                # Actualizar la barra de progreso
                progress_bar.progress((i + 1) / total_files)

            # Crear un archivo ZIP con todos los XLSX
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                for idx, (final_results, details_results) in enumerate(results):
                    xlsx_data = generate_and_get_xlsx(final_results, details_results)
                    zip_file.writestr(f"resultados_{idx + 1}.xlsx", xlsx_data)

            zip_buffer.seek(0)
            st.download_button(
                label="Descargar Todos los Resultados en ZIP",
                data=zip_buffer,
                file_name="resultados.zip",
                mime="application/zip"
            )

# Navegación entre páginas
st.sidebar.title("Navegación")
page = st.sidebar.radio("Selecciona una página", ["Página Principal", "Múltiples Archivos"])

if page == "Página Principal":
    main_page()
elif page == "Múltiples Archivos":
    multi_file_page()