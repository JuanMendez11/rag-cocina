# ChefBot: Asistente Inteligente de Gastronomía Argentina (RAG)

Juan Ignacio Mendez

**ChefBot** es un sistema de **Retrieval-Augmented Generation (RAG)** diseñado para actuar como un experto culinario. Utiliza un modelo de lenguaje grande (LLM) conectado a una base de conocimiento específica (el libro *"Gastronomía Regional Argentina"*) para responder preguntas sobre recetas, ingredientes y cultura, evitando alucinaciones y garantizando fidelidad a la fuente.

La solución implementa una arquitectura de microservicios con un **Frontend** interactivo (Streamlit), una **API** robusta (FastAPI) y un motor de **Inteligencia Artificial** modular (LangChain + Cohere).

---
## Estructura del proyecto
```
📁 /
├── 📄 documents/gastronomia-regional-argentina.pdf  # Fuente de conocimiento
├── 📂 chroma_db_cohere/                   # Base de datos vectorial generada
├── 📄 crear_db.py                        # Script de ingestión (PDF -> Vectores)
├── 📄 services.py                         # Lógica de negocio (Orquestador, RAG, Filtros)
├── 📄 main.py                             # API FastAPI
├── 📄 frontend.py                         # Interfaz de usuario Streamlit
├── 📄 requirements.txt                    # Dependencias
└── 📄 README.md                           # Documentación
```


## Ejecucion
Para utilizar el sistema RAG, clona el repositorio y crea un entorno virtual. Una vez creado, actívalo (en Windows usa `.\venv\Scripts\activate` y en Linux/Mac `source venv/bin/activate`) e instala las librerías necesarias ejecutando `pip install -r requirements.txt`.

Para generar la base de datos vectorial con la documentación, ejecuta `python crear_db.py` (o python3 en Linux/Mac).

Finalmente, carga la API ejecutando `python main.py`. Para iniciar la interfaz de usuario, abre una segunda terminal en la carpeta del proyecto, activa el entorno virtual y ejecuta `streamlit run frontend.py`.


## Aspectos tecnicos

ChefBot utiliza de base de conocimiento el libro *"Gastronomía Regional Argentina"*. Para poder pasar todo este conocimiento a una base de datos vectorizada, primero eliminamos el "ruido" del documento ,y depues tuvimos que hacer chunks con el `RecursiveCharacterTextSplitter` de langchain, ajustando con los parametros `chunk_size=1500` y `chunk_overlap=300`, con la idea de que cada receta quede contenida integramente en un solo chunk.

Una vez que obtuvimos los chunks, los pasamos por un modelo de embedding para poder guardarlos en una base vectorial. En este caso se utilizo el modelo **embed-multilingual-v3.0** de Cohere, pues es de los mejores modelos en castellano y nos devuelve vectores de una dimension respetable. La base de datos vectorizada que elegimos fue la de Chromadb, ya que la usamos durante el curso y se manipula facilmente desde langchain.

Para los LLMs, optamos por el modelo **command-r-08-2024** de Cohere, es de los mejores en castellano y nos permite cargarle un contexto de hasta 128k. En este proyecto se usa de dos formas diferentes:
- Como filtro para captar la intencion de quien usa el RAG. De este modo su salida esta limitada a un maximo de 5 tokens.
- Para generar la respuesta del RAG con el contexto ya cargado.

El sistema no es un simple chat lineal; utiliza un **Orquestador Semántico** para decidir cómo procesar cada consulta.

### Flujo de Datos:
1.  **Usuario:** Realiza una consulta en la interfaz web.
2.  **Orquestador (Router):** Un LLM rápido analiza la intención:
    * *Saludo/Charla:* Responde directamente (Baja latencia).
    * *Consulta Gastronómica:* Activa el pipeline RAG.
    * *Off-Topic:* Bloquea la consulta.
3.  **RAG Pipeline (Si aplica):**
    * **Retrieval:** Busca los 5 fragmentos más relevantes en ChromaDB.
    * **Generación:** Un LLM potente (`Command R`) redacta la respuesta usando el contexto.
    * **Auditoría (Groundedness):** Un LLM juez verifica si la respuesta es fiel al libro antes de entregarla.
4.  **Frontend:** Muestra la respuesta y los metadatos de validación.


### Resumen stack tecnológico

* **Lenguaje:** Python 3.10+
* **Framework de IA:** LangChain
* **LLMs:** Cohere (`command-r-08-2024`)
* **Embeddings:** Cohere (`embed-multilingual-v3.0`)
* **Vector Database:** ChromaDB (Persistente)
* **Backend API:** FastAPI
* **Frontend UI:** Streamlit