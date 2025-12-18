import os
import getpass
from langchain_chroma import Chroma
from langchain_cohere import CohereEmbeddings, ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# --- CONFIGURACIÓN ---
# Asegúrate de que esta ruta sea LA MISMA que usaste en el script anterior
DB_PATH = "./chroma_db_cohere" 

# Configurar API Key
if "COHERE_API_KEY" not in os.environ:
    os.environ["COHERE_API_KEY"] = getpass.getpass("Tu API Key de Cohere: ")

# --- PASO 1: RECONECTAR A LA BASE DE DATOS (Lo que te faltaba) ---
print("Cargando base de datos vectorial desde disco...")

# Necesitamos definir el modelo de embedding de nuevo para que Chroma sepa cómo leer los números
embedding_model = CohereEmbeddings(model="embed-multilingual-v3.0")

# Aquí cargamos la DB existente en lugar de crearla de cero
vectorstore = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embedding_model
)

print("¡Base de datos cargada!")

# --- PASO 2: DEFINIR MODELOS LLM ---

# El Portero (Rápido)
llm_filtro = ChatCohere(
    model="command-r-08-2024", 
    temperature=0
)

# El Cerebro (Potente)
llm_generador = ChatCohere(
    model="command-r-plus-08-2024",
    temperature=0.3
)

# --- PASO 3: CADENAS (CHAINS) ---

# Cadena de Filtro
prompt_filtro = ChatPromptTemplate.from_template(
    """Eres un clasificador de preguntas.
    Analiza si la siguiente pregunta está relacionada con: comida, recetas, ingredientes, cocina argentina o gastronomía.
    
    Pregunta: {pregunta}
    
    Responde SOLO "SI" o "NO"."""
)
chain_filtro = prompt_filtro | llm_filtro | StrOutputParser()

# Cadena RAG
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

template_rag = """Eres un experto chef de Argentina. Usa el siguiente contexto para responder.
Si no sabes la respuesta basándote en el contexto, dilo honestamente.

Contexto:
{context}

Pregunta: {question}

Respuesta detallada:"""

prompt_rag = ChatPromptTemplate.from_template(template_rag)

chain_rag = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt_rag
    | llm_generador
    | StrOutputParser()
)

# --- PASO 4: FUNCIÓN PRINCIPAL ---

def procesar_pregunta(pregunta_usuario):
    print(f"\nUsuario dice: '{pregunta_usuario}'")
    
    # 1. Filtro
    print(">> Verificando tema...")
    decision = chain_filtro.invoke({"pregunta": pregunta_usuario}).strip().upper()
    
    if "NO" in decision:
        return "🚫 Lo siento, solo puedo responder sobre Gastronomía Regional Argentina."
    
    # 2. RAG
    print(">> Buscando recetas y cocinando respuesta...")
    respuesta = chain_rag.invoke(pregunta_usuario)
    return respuesta

# --- EJECUCIÓN ---
if __name__ == "__main__":
    while True:
        pregunta = input("\nPregúntame algo de comida (o escribe 'salir'): ")
        if pregunta.lower() == "salir":
            break
        
        respuesta = procesar_pregunta(pregunta)
        print(f"\nChef Bot:\n{respuesta}")