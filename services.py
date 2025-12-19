import os
from dotenv import load_dotenv
from langchain_cohere import CohereEmbeddings, ChatCohere
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

# --- CONFIGURACIÓN E INICIALIZACIÓN ---

# Ruta donde guardaste la base de datos (Asegúrate de que coincida con tu script de creación)
DB_PATH = "./chroma_db_cohere"

# Verificación de seguridad
load_dotenv()
api_key = os.getenv("COHERE_API_KEY")

# 1. Inicializar Modelos (Se cargan una sola vez al importar el archivo)

# A. Modelo de Embeddings (Para buscar en la base de datos)
embedding_model = CohereEmbeddings(model="embed-multilingual-v3.0")

# B. Cargar Base de Datos Vectorial
if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"⚠️ No se encuentra la base de datos en {DB_PATH}. Ejecuta primero el script de ingestión.")

vectorstore = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embedding_model
)

# C. Definir los LLMs (Cerebro Rápido vs Cerebro Potente)
llm_rapido = ChatCohere(model="command-r-08-2024", temperature=0, max_tokens=5)
llm_potente = ChatCohere(model="command-r-08-2024", temperature=0.3)


# --- FUNCIONES DE SERVICIO ---

def clasificar_intencion(pregunta: str) -> str:
    """
    Usa el modelo RÁPIDO para decidir qué quiere hacer el usuario.
    Categorías:
    - SALUDO: Hola, gracias, chau, buen día.
    - BUSQUEDA: Preguntas sobre recetas, comida, ingredientes.
    - OFF_TOPIC: Política, deportes, código, mecánica.
    """
    prompt_router = PromptTemplate.from_template(
        """Eres el cerebro de un asistente de cocina. Clasifica la siguiente frase del usuario en una de estas 3 categorías:

        1. "SALUDO": Si el usuario saluda, agradece, se despide o hace charla casual (ej: "Hola", "Quién sos").
        2. "BUSQUEDA": Si el usuario pregunta sobre recetas, comida, historia culinaria o ingredientes.
        3. "OFF_TOPIC": Si el usuario habla de temas que NO son cocina ni saludos (ej: fútbol, programación).

        Usuario: {input}

        Responde ÚNICAMENTE con una palabra: SALUDO, BUSQUEDA u OFF_TOPIC."""
    )

    chain = prompt_router | llm_rapido | StrOutputParser()
    
    # Limpiamos la salida para evitar espacios o puntos extra
    intencion = chain.invoke({"input": pregunta}).strip().upper()
    return intencion


def responder_charla_casual(pregunta: str) -> str:
    """
    Responde saludos o preguntas personales sin buscar en la base de datos.
    Usa el modelo rápido para ser veloz.
    """
    prompt_chat = PromptTemplate.from_template(
        """Eres "ChefBot", un asistente experto en gastronomía argentina amigable y servicial.
        El usuario te ha dicho: "{input}"
        
        Respondele de forma breve, carismática y siempre invitándolo a cocinar o preguntar por una receta.
        NO inventes recetas, solo charla."""
    )
    
    chain = prompt_chat | llm_rapido | StrOutputParser()
    return chain.invoke({"input": pregunta})


def buscar_contexto(pregunta: str, k: int = 3):
    """
    Realiza el embedding de la consulta y busca los 'k' fragmentos 
    más similares en la base de datos vectorial.
    """
    # Buscamos directamente los documentos
    docs = vectorstore.similarity_search(pregunta, k=k)
    return docs


def generar_respuesta_rag(pregunta: str) -> str:
    """
    Usa el modelo potente (Command R) para responder basándose 
    en la información recuperada de la base de datos.
    """
    
    # 1. Recuperar contexto (usamos la función anterior)
    docs = buscar_contexto(pregunta)
    contexto_texto = "\n\n".join([d.page_content for d in docs])
    
    # 2. Si no hay contexto relevante (opcional, pero buena práctica)
    if not contexto_texto:
        return "No encontré información suficiente en el libro para responder eso."

    # 3. Crear el Prompt
    template = """Eres un experto Chef Argentino. Responde la pregunta del usuario basándote EXCLUSIVAMENTE en el siguiente contexto extraído del libro 'Gastronomía Regional Argentina'.
    
    - Si la respuesta no está en el contexto, di amablemente que no tienes esa información.
    - Cita el nombre de la receta si aplica.
    - Sé claro y didáctico.
    - No se deben usar emojis en las respuestas.
    - Las respuestas deben ser siempre en español, independientemente del idioma de la pregunta.

    CONTEXTO:
    {context}

    PREGUNTA DEL USUARIO: 
    {question}

    RESPUESTA:"""

    prompt = ChatPromptTemplate.from_template(template)

    # 4. Cadena de generación
    chain = prompt | llm_potente | StrOutputParser()

    # 5. Ejecutar
    respuesta = chain.invoke({
        "context": contexto_texto,
        "question": pregunta
    })
    
    return respuesta


def orquestador_conversacional(pregunta: str) -> dict:
    """
    Función maestra que dirige el tráfico.
    Retorna un diccionario con la respuesta y el tipo de acción que tomó.
    """
    # 1. El Orquestador decide
    intencion = clasificar_intencion(pregunta)
    print(f"🤖 Orquestador detectó intención: {intencion}")

    # 2. Ejecutar acción según la decisión
    if intencion == "SALUDO":
        respuesta = responder_charla_casual(pregunta)
        return {"respuesta": respuesta, "intencion": "Saludo 💬"}
    
    elif intencion == "BUSQUEDA":
        # Llamamos a tu función RAG existente (la que ya tenías)
        respuesta = generar_respuesta_rag(pregunta)
        return {"respuesta": respuesta, "intencion": "Consulta gastronomica 📖"}
    
    else: # OFF_TOPIC
        return {
            "respuesta": "Lo siento, mi delantal es solo para cocinar. Preguntame sobre empanadas, locro o postres argentinos.", 
            "intencion": "Fuera de tema 🚫"
        }