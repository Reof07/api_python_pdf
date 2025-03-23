import openai
import json
import pytesseract
import os
from PIL import Image
from io import BytesIO
from pdf2image import convert_from_path
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.utilities import SQLDatabase
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    model="gpt-4o-mini-2024-07-18",
    openai_api_key=OPENAI_API_KEY
)

def get_engine_for_mysql_db():
    """Crea un motor de SQLAlchemy para una base de datos MySQL local."""
    user = "py_vivienda_com"
    password = "0dbn4tP8h):d"
    host = "woobsing-dev-ohio-mysql-8-0-26.cmxlnwygo8jr.us-east-2.rds.amazonaws.com"
    port = 3306
    database = "extracto_archivointeligente_com"

    # URL de conexión
    connection_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return create_engine(
        connection_url,
    )

# Crear el motor
engine = get_engine_for_mysql_db()

# Crear el objeto SQLDatabase
db = SQLDatabase(engine)

# Crear el toolkit para acceder a la base de datos
sql_toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Obtener las herramientas de la base de datos a partir del toolkit
tools = sql_toolkit.get_tools()

# Función para extraer el esquema que tiene que llenar
def get_schema(document_type):
    with engine.connect() as connection:

        query = text("SELECT `schema`, `prompt` from document_schema WHERE document_type = :document_type")

        resultado = connection.execute(query, {"document_type": document_type})

        rows = resultado.fetchall()

        result = []
        for row in rows:
            result.append({"schema": row[0], "prompt": row[1]})

        return result

# Función para extraer texto de un PDF o imagen utilizando OCR
def extract_text_ocr(upload_file):
    file_bytes = upload_file.file.read()

    file_stream = BytesIO(file_bytes)

    file_extension = os.path.splitext(upload_file.filename)[1].lower()

    pdf_content = ""

    if file_extension == ".pdf":
        try:
            images = convert_from_path(file_stream)
            for image in images:
                text = pytesseract.image_to_string(image)
                pdf_content += text + "\n"
        except Exception as e:
            raise ValueError(f"Error al convertir el PDF a imagen: {e}")
    elif file_extension in [".jpg", ".jpeg", ".png"]:
        try:
            image = Image.open(file_stream)
            text = pytesseract.image_to_string(image)
            pdf_content += text + "\n"
        except Exception as e:
            raise ValueError(f"Error al procesar la imagen: {e}")
    else:
        raise ValueError("El archivo proporcionado no es un PDF ni una imagen compatible")

    return pdf_content

# Función para insertar el resultado
def insert_schemas_for_documents(document_data):
    try:
        with engine.connect() as connection:

            query = text("""
                INSERT INTO document_extraction (document_path, document_type, document_schema, ocr, response)
                VALUES (:document_path, :document_type, :document_schema, :ocr, :response)
            """)

            for data in document_data:
                data['document_schema'] = json.dumps(data['document_schema'])
                data['response'] = json.dumps(data['response'])
                connection.execute(query, data)

            connection.commit()
            return "Resultado insertado correctamente."
    except SQLAlchemyError as e:
        print(f"Error al insertar el documento: {e}")
        return False

def data_extraction(document_type: int, file):
    schema = get_schema(document_type)
    for item in schema:
        schema = item["schema"]
        template = item["prompt"]

    pdf_content = extract_text_ocr(file)

    # Crear el prompt template con un placeholder para el contenido del PDF
    prompt = PromptTemplate(
        input_variables=["pdf_content", "schema"],
        template=template
    )

    formatted_prompt = prompt.format(
        pdf_content=pdf_content,
        schema=schema,
    )

    # Crear la instancia del modelo OpenAI
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18", openai_api_key=OPENAI_API_KEY)

    # Llamar al modelo de OpenAI con el prompt generado
    response = model.invoke([{"role": "user", "content": formatted_prompt}])

    response_content = response.content

    response_content_clean = response_content.replace("\n", " ").strip()

    schema_clean = json.loads(schema)

    response_content_clean = response_content_clean.replace("```json", "").replace("```", "").strip()

    try:
        parsed_response = json.loads(response_content_clean)
    except json.JSONDecodeError:
        print("La respuesta no es un JSON válido.")

    # Guardar el resultado
    document_data = [
        {
            "document_type": document_type,
            "document_schema": schema_clean,
            "document_path": file.filename,
            "ocr": pdf_content,
            "response": parsed_response
        }
    ]

    result = insert_schemas_for_documents(document_data)
    return parsed_response