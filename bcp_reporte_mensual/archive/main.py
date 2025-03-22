import fitz  # PyMuPDF
import os

def desbloquear_pdf(input_pdf, output_pdf, password):
    # Abrir el PDF original
    doc = fitz.open(input_pdf)

    # Verificar si el PDF está encriptado
    if doc.is_encrypted:
        # Intentar desbloquear el PDF con la contraseña proporcionada
        if doc.authenticate(password):
            print("PDF desbloqueado correctamente.")
        else:
            print("Contraseña incorrecta o no se pudo desbloquear el PDF.")
            return

    # Crear un nuevo documento PDF para guardar las páginas desbloqueadas
    new_doc = fitz.open()

    # Copiar todas las páginas excepto la última al nuevo documento
    for page_num in range(len(doc) - 1):
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

    # Guardar el nuevo PDF
    new_doc.save(output_pdf)
    print(f"Nuevo PDF creado: {output_pdf}")

def pdf_to_text(input_pdf, output_folder):
    doc = fitz.open(input_pdf)
    text = ""
    # Extraer texto de todas las páginas excepto la última
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()

    # Crear la carpeta de salida si no existe
    os.makedirs(output_folder, exist_ok=True)

    # Guardar el texto en un archivo dentro de la carpeta especificada
    output_text_path = os.path.join(output_folder, "output_text1.txt")
    with open(output_text_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Texto guardado en: {output_text_path}")

# Ruta del PDF original
input_pdf = r"pdf_to_excel\pdf_sample\EECC_Feb2023_182.pdf"
# Ruta del nuevo PDF
output_pdf = "pdf_to_excel/1.pdf"
# Contraseña (si el PDF está protegido)
password = "tu_contraseña"  # Cambia esto por la contraseña correcta

# Llamar a la función para desbloquear y crear el nuevo PDF
desbloquear_pdf(input_pdf, output_pdf, password)

# Carpeta donde se guardará el archivo de texto
output_folder = "pdf_to_text_output"

# Extraer texto del PDF y guardarlo en un archivo dentro de la carpeta especificada
pdf_to_text(output_pdf, output_folder)
