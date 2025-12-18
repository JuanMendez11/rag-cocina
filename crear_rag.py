import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_cohere import CohereEmbeddings

# --- CONFIGURACIÓN ---
PDF_PATH = "documents/gastronomia-regional-argentina.pdf"
DB_PATH = "./chroma_db_cohere"  # Carpeta nueva para no mezclar con la anterior

# 1. CONFIGURAR API KEY
# Si no la tienes en tus variables de entorno, pídela aquí:
load_dotenv()
api_key = os.getenv("COHERE_API_KEY")

def main():
    # --- PASO 1: CARGAR EL LIBRO ---
    if not os.path.exists(PDF_PATH):
        print(f"Error: No encuentro el archivo {PDF_PATH}")
        return

    print(f"--- Paso 1: Cargando {PDF_PATH} ...")
    loader = PyPDFLoader(PDF_PATH)
    docs = loader.load()
    print(f"   > Se cargaron {len(docs)} páginas.")

    # --- PASO 2: LIMPIEZA DE DATOS ---
    print("--- Paso 2: Limpiando encabezados repetitivos ...")
    for doc in docs:
        texto = doc.page_content
        # Eliminamos el ruido específico de este PDF
        texto = texto.replace("GASTRONOMIA REGIONAL ARGENTINA", "")
        texto = texto.replace("FEHGRA", "")
        texto = texto.replace("Federación Empresaria Hotelera Gastronómica", "")
        doc.page_content = texto

    # --- PASO 3: DIVIDIR (CHUNKING PARA COHERE) ---
    # Cohere prefiere chunks más densos (aprox 1000-1500 caracteres)
    print("--- Paso 3: Dividiendo texto (Estrategia Cohere: 1500 chars) ...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,     # Optimizado para embed-multilingual-v3.0
        chunk_overlap=300,   # Margen para no cortar frases
        separators=["\n\n", "\n", " ", ""]
    )
    
    splits = text_splitter.split_documents(docs)
    print(f"   > Se generaron {len(splits)} fragmentos.")

    # --- PASO 4: EMBEDDING Y GUARDADO ---
    print("--- Paso 4: Vectorizando con Cohere (embed-multilingual-v3.0) ...")
    
    # Inicializamos el modelo de Cohere
    embedding_model = CohereEmbeddings(
        model="embed-multilingual-v3.0"  # El mejor para español
    )

    # Si la DB ya existe, la borramos para re-hacerla limpia (opcional)
    if os.path.exists(DB_PATH):
        import shutil
        shutil.rmtree(DB_PATH)
        print("   > Base de datos anterior eliminada.")

    # Creación de la base de datos
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embedding_model,
        persist_directory=DB_PATH
    )
    
    print(f"¡ÉXITO! Base de datos guardada en: {DB_PATH}")
if __name__ == "__main__":
    main()