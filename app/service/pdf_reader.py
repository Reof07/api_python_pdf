import os
import uuid
import asyncio
import pytesseract
from io import BytesIO
from PIL import Image
from typing import Dict
from fastapi import UploadFile, HTTPException
from langchain_community.document_loaders import PyPDFLoader, PDFPlumberLoader
from langchain_community.document_loaders import UnstructuredXMLLoader


import pandas as pd
import xml.etree.ElementTree as ET
import pandas as pd

from charset_normalizer import from_bytes
import io

from ..utils.utils import get_pdf_page_count, is_pdf_pure, extract_text_with_ocr
from ..utils.utils import get_file_size, save_file_to_temp, preprocess_image
from ..utils.utils import generate_markdown
from ..core.tokenizers import tokenizer
# from ..utils.image import process_text
# from ..utils.image import extract_text_from_image_with_ocr, preprocess_image_from_complex_image
# from ..utils.image import process_text_with_llm


MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

class PDFExtractionService:
    @staticmethod
    async def extract_from_pdf(file: UploadFile) -> Dict:
        """
        Extrae contenido de un archivo PDF, ya sea puro o escaneado.
        Retorna un diccionario con los resultados, incluyendo el conteo de tokens.
        """
        temp_file_path = None
        try:
            # Validar tamaño del archivo
            file_size = await get_file_size(file)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo {file.filename} excede el tamaño máximo permitido (200MB)."
                )

            # Guardar archivo temporalmente
            temp_file_path = await save_file_to_temp(file)

            # Verificar que la extensión sea PDF
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo {file.filename} no es un PDF."
                )

            # Obtener cantidad de páginas
            num_pages = get_pdf_page_count(temp_file_path)

            # Verificar si es un PDF 'puro' (con texto seleccionable)
            pdf_pure = is_pdf_pure(temp_file_path)

            if pdf_pure:
                # Usar PyPDFLoader para PDFs con texto seleccionable
                loader = PyPDFLoader(temp_file_path)
                documents = await asyncio.to_thread(loader.load)
                content = [doc.page_content for doc in documents]
            else:
                # Para PDFs escaneados, usar OCR
                ocr_text = await extract_text_with_ocr(temp_file_path)
                if ocr_text.strip():
                    content = [ocr_text]  # Lista con un solo elemento
                else:
                    # Si OCR no encuentra texto, intentar con PDFPlumber
                    loader = PDFPlumberLoader(temp_file_path)
                    documents = await asyncio.to_thread(loader.load)
                    if documents and any(doc.page_content.strip() for doc in documents):
                        content = [doc.page_content for doc in documents]
                    else:
                        return {
                            "filename": file.filename,
                            "size_bytes": file_size,
                            "page_count": num_pages,
                            "pdf_pure": False,
                            "message": "No se pudo extraer contenido (PDF escaneado sin texto legible)"
                        }

            # Calcular el número total de tokens en el contenido extraído
            total_tokens = sum(len(tokenizer.encode(chunk)) for chunk in content)

            # Devolver la respuesta incluyendo el conteo de tokens
            
            print(generate_markdown(content))
            
            if pdf_pure:
                return {
                    "filename": file.filename,
                    "size_bytes": file_size,
                    "page_count": num_pages,
                    "pdf_pure": True,
                    "content": generate_markdown(content),
                    "token_count": total_tokens
                }
            else:
                if "message" not in locals():  # Si no hay mensaje de error previo
                    return {
                        "filename": file.filename,
                        "size_bytes": file_size,
                        "page_count": num_pages,
                        "pdf_pure": False,
                        "content": content,
                        "token_count": total_tokens,
                        "note": "Extraído con OCR o PDFPlumber"
                    }

        except HTTPException as e:
            return {"filename": file.filename, "error": str(e.detail)}
        except Exception as e:
            return {"filename": file.filename, "error": f"Error inesperado: {str(e)}"}
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                await asyncio.to_thread(os.remove, temp_file_path)


class ImageExtractionService:
    @staticmethod
    async def extract_from_image(file: UploadFile) -> Dict:
        """
        Extrae contenido de un archivo de imagen (PNG, JPEG) usando OCR.
        Retorna un diccionario con los resultados, incluyendo el conteo de tokens.
        """
        temp_file_path = None
        try:
            # Validar tamaño del archivo
            file_size = await get_file_size(file)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo {file.filename} excede el tamaño máximo permitido (200MB)."
                )

            # Guardar archivo temporalmente
            temp_file_path = await save_file_to_temp(file)

            # Abrir imagen usando PIL
            try:
                image = Image.open(temp_file_path)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error al abrir la imagen: {str(e)}")

            # Preprocesar y extraer texto usando OCR
            processed_image = preprocess_image(image)
            ocr_text = pytesseract.image_to_string(processed_image, config="--oem 3 --psm 6")
            if not ocr_text.strip():
                return {
                    "filename": file.filename,
                    "size_bytes": file_size,
                    "message": "No se pudo extraer texto con OCR de la imagen."
                }

            # Calcular el número de tokens en el contenido extraído
            total_tokens = len(tokenizer.encode(ocr_text))

            return {
                "filename": file.filename,
                "size_bytes": file_size,
                "content": ocr_text,
                "token_count": total_tokens,
                "note": "Texto extraído de imagen con OCR"
            }
        except HTTPException as e:
            return {"filename": file.filename, "error": str(e.detail)}
        except Exception as e:
            return {"filename": file.filename, "error": f"Error inesperado: {str(e)}"}
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                await asyncio.to_thread(os.remove, temp_file_path)
                
                
# class XMLExtractionService:
#     @staticmethod
#     async def extract_from_xml(file: UploadFile) -> Dict:
#         """
#         Extrae contenido de un archivo XML usando UnstructuredXMLLoader.
#         Retorna un diccionario con los resultados y conteo de tokens.
#         """
#         temp_file_path = None
#         try:
#             # Validar tamaño del archivo
#             file_size = await get_file_size(file)
#             if file_size > MAX_FILE_SIZE:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"El archivo {file.filename} excede el tamaño máximo permitido (200MB)."
#                 )

#             # Guardar archivo temporalmente
#             temp_file_path = await save_file_to_temp(file)

#             # Utilizar UnstructuredXMLLoader para cargar el XML
#             loader = UnstructuredXMLLoader(temp_file_path)
#             # El loader procesa el XML y devuelve una lista de documentos. Se ejecuta en un hilo aparte.
#             documents = await asyncio.to_thread(loader.load)
#             if not documents or not any(doc.page_content.strip() for doc in documents):
#                 return {
#                     "filename": file.filename,
#                     "size_bytes": file_size,
#                     "message": "No se pudo extraer contenido del XML."
#                 }
#             # Extraer el contenido de cada documento
#             content = [doc.page_content for doc in documents]
#             # Contar tokens usando el mismo tokenizer que para PDF e imágenes
#             total_tokens = sum(len(tokenizer.encode(chunk)) for chunk in content)
            
#             return {
#                 "filename": file.filename,
#                 "size_bytes": file_size,
#                 "content": content,
#                 "token_count": total_tokens,
#                 "note": "Contenido extraído de XML usando UnstructuredXMLLoader"
#             }
#         except HTTPException as e:
#             return {"filename": file.filename, "error": str(e.detail)}
#         except Exception as e:
#             return {"filename": file.filename, "error": f"Error inesperado: {str(e)}"}
#         finally:
#             if temp_file_path and os.path.exists(temp_file_path):
#                 await asyncio.to_thread(os.remove, temp_file_path)



# class XMLExtractionService:
#     @staticmethod
#     async def extract_from_xml(file: UploadFile) -> tuple[BytesIO, str]:
#         # 1) Validaciones
#         if not file.filename.lower().endswith(".xml"):
#             raise HTTPException(400, "Solo .xml")
#         size = await get_file_size(file)
#         if size > MAX_FILE_SIZE:
#             raise HTTPException(400, "Archivo >200MB")

#         tmp = await save_file_to_temp(file)
#         try:
#             # 2) Parseo
#             tree = await asyncio.to_thread(ET.parse, tmp)
#             root = tree.getroot()  # <registro_catastral>

#             data = []
#             for predio in root.findall("predio"):
#                 row = {}
#                 # campos directos
#                 for tag in [
#                     "departamento","municipio","codigo_predial_nacional",
#                     "codigo_predial_anterior","codigo_homologado",
#                     "matricula_inmobiliaria","direccion",
#                     "area_terreno","area_construida",
#                     "destino_economico","condicion_predio",
#                     "tipo_predio","tipo_derecho"
#                 ]:
#                     elem = predio.find(tag)
#                     row[tag] = elem.text if elem is not None else ""

#                 # avaluos
#                 av = predio.find("avaluos_catastrales/avaluo_catastral")
#                 if av is not None:
#                     row["avaluo"]   = av.findtext("avaluo","")
#                     row["vigencia"] = av.findtext("vigencia","")
#                 else:
#                     row["avaluo"] = row["vigencia"] = ""

#                 # interesados (natural o juridica)
#                 intr = predio.find("interesados")
#                 if intr is not None:
#                     pj = intr.find("persona_juridica")
#                     pn = intr.find("persona_natural")
#                     if pj is not None:
#                         row["tipo_interesado"]     = "juridica"
#                         row["doc_tipo"]            = pj.findtext("documento","")
#                         row["doc_numero"]          = pj.findtext("numero_documento","")
#                         row["razon_social"]        = pj.findtext("razon_social","")
#                         # campos de persona natural vacíos
#                         row.update({k:"" for k in ["primer_nombre","segundo_nombre","primer_apellido","segundo_apellido"]})
#                     elif pn is not None:
#                         row["tipo_interesado"]     = "natural"
#                         row["doc_tipo"]            = pn.findtext("documento","")
#                         row["doc_numero"]          = pn.findtext("numero_documento","")
#                         row["primer_nombre"]       = pn.findtext("primer_nombre","")
#                         row["segundo_nombre"]      = pn.findtext("segundo_nombre","")
#                         row["primer_apellido"]     = pn.findtext("primer_apellido","")
#                         row["segundo_apellido"]    = pn.findtext("segundo_apellido","")
#                         # campos de persona juridica vacíos
#                         row["razon_social"] = ""
#                     else:
#                         # sin interesado
#                         row.update({
#                             "tipo_interesado":"", "doc_tipo":"", "doc_numero":"",
#                             "razon_social":"","primer_nombre":"","segundo_nombre":"",
#                             "primer_apellido":"","segundo_apellido":""
#                         })
#                 data.append(row)

#             if not data:
#                 raise HTTPException(400, "No hay <predio> en el XML")

#             # 3) DataFrame con headers limpios
#             df = pd.DataFrame(data)

#             # 4) Excel en memoria
#             output = BytesIO()
#             with pd.ExcelWriter(output, engine="openpyxl") as w:
#                 df.to_excel(w, index=False, sheet_name="Datos")
#             output.seek(0)

#             fname = os.path.splitext(file.filename)[0] + ".xlsx"
#             return output, fname

#         except ET.ParseError as e:
#             raise HTTPException(400, f"XML mal formado: {e}")
#         finally:
#             if os.path.exists(tmp):
#                 await asyncio.to_thread(os.remove, tmp)


class XMLExtractionService:
    @staticmethod
    async def extract_from_xml(file: UploadFile) -> tuple[BytesIO, str]:
        if not file.filename.lower().endswith(".xml"):
            raise HTTPException(400, "Solo se permiten archivos .xml")

        size = await get_file_size(file)
        if size > MAX_FILE_SIZE:
            raise HTTPException(400, "El archivo excede el tamaño permitido")

        tmp = await save_file_to_temp(file)

        try:
            # Parsear XML
            tree = await asyncio.to_thread(ET.parse, tmp)
            root = tree.getroot()

            data = []

            for predio in root.findall("predio"):
                row = {}

                # Campos directos (todos los hijos de <predio> excepto los compuestos)
                for child in predio:
                    if child.tag in ["avaluos_catastrales", "interesados"]:
                        continue
                    row[child.tag] = child.text if child.text else ""

                # Avaluo
                av = predio.find("avaluos_catastrales/avaluo_catastral")
                if av is not None:
                    for av_item in av:
                        row[f"avaluo_{av_item.tag}"] = av_item.text if av_item.text else ""

                # Interesado
                intr = predio.find("interesados")
                if intr is not None:
                    pj = intr.find("persona_juridica")
                    pn = intr.find("persona_natural")
                    if pj is not None:
                        row["tipo_interesado"] = "juridica"
                        for child in pj:
                            row[f"interesado_juridica_{child.tag}"] = child.text if child.text else ""
                    elif pn is not None:
                        row["tipo_interesado"] = "natural"
                        for child in pn:
                            row[f"interesado_natural_{child.tag}"] = child.text if child.text else ""
                    else:
                        row["tipo_interesado"] = "desconocido"

                data.append(row)

            if not data:
                raise HTTPException(400, "No se encontraron predios en el XML.")

            # Crear DataFrame
            df = pd.DataFrame(data)

            # Generar Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as w:
                df.to_excel(w, index=False, sheet_name="Datos")
            output.seek(0)

            filename = os.path.splitext(file.filename)[0] + ".xlsx"
            return output, filename

        except ET.ParseError as e:
            raise HTTPException(400, f"XML mal formado: {e}")
        except Exception as e:
            raise HTTPException(500, f"Error procesando XML: {e}")
        finally:
            if os.path.exists(tmp):
                await asyncio.to_thread(os.remove, tmp)


class CSVExtractionService:
    @staticmethod
    async def extract_from_csv(file: UploadFile) -> Dict:
        temp_file_path = None
        excel_path = None
        try:
            # 1. Validar extensión
            if not file.filename.endswith(".csv"):
                return {"error": "El archivo debe ser un CSV"}

            # 2. Validar tamaño del archivo
            file_size = await get_file_size(file)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo {file.filename} excede el tamaño máximo permitido (200MB)."
                )

            # 3. Guardar archivo temporal
            temp_file_path = await save_file_to_temp(file)

            # 4. Detectar codificación
            with open(temp_file_path, 'rb') as f:
                file_content = f.read()
                
            detected = from_bytes(file_content).best()
            encoding = detected.encoding if detected else 'utf-8'

            # 5. Leer CSV con manejo de errores
            try:
                # Intentar con detección automática de delimitador
                df = pd.read_csv(
                    temp_file_path,
                    encoding='latin1',
                    sep='|',            # Detecta delimitador
                    engine='python',     # Motor más flexible
                    # on_bad_lines='warn', # Saltar líneas problemáticas
                    skip_blank_lines=True,
                    dtype=str            # Evitar inferencia de tipos
                )
            except UnicodeDecodeError:
                # Fallback a codificación ISO-8859-1
                df = pd.read_csv(
                    temp_file_path,
                    encoding='ISO-8859-1',
                    sep='|',
                    engine='python',
                    on_bad_lines='warn',
                    dtype=str
                )

            # 6. Crear archivo Excel
            excel_filename = f"{uuid.uuid4().hex}.xlsx"
            excel_path = os.path.join("archivos", excel_filename)
            os.makedirs("archivos", exist_ok=True)
            
            df.to_excel(excel_path, index=False)

            return {
                "filename": file.filename,
                "size_bytes": file_size,
                "excel_path": excel_path,
                "note": "Archivo CSV convertido exitosamente a Excel"
            }

        except HTTPException as e:
            return {"error": e.detail}
        except pd.errors.ParserError as e:
            return {"error": f"Formato CSV inválido: {str(e)}"}
        except Exception as e:
            return {"error": f"Error inesperado: {str(e)}"}
        finally:
            # 7. Limpiar archivo temporal
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
                