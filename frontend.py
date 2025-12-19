import streamlit as st
import requests

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="ChefBot Argentina 🇦🇷",
    page_icon="👨‍🍳",
    layout="centered"
)

# Definir la URL de tu API (Backend)
# Asumimos que corre en local. Si usas Docker o nube, cambia esto.
API_URL = "http://127.0.0.1:8000/chat"

# --- 2. BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1830/1830839.png", width=100)
    st.header("Cocina Regional 🇦🇷")
    st.markdown("Este bot es experto en gastronomía argentina.")
    
    st.divider()
    
    st.subheader("💡 Sugerencias:")
    ejemplos = [
        "¿Cómo se hace el locro?",
        "Receta de empanadas salteñas",
        "¿Qué es el charqui?",
        "Hola, ¿quién sos?",
        "Postres de la zona de Cuyo"
    ]
    
    # Botones para preguntas rápidas
    for ej in ejemplos:
        if st.button(ej):
            # Hack para que el botón envíe el texto al chat
            st.session_state.input_rapido = ej

    st.divider()
    # Botón para limpiar historial
    if st.button("🗑️ Borrar conversación"):
        st.session_state.messages = []
        st.rerun()

# --- 3. ESTADO DE LA SESIÓN (HISTORIAL) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Manejo del input desde los botones de sugerencia
if "input_rapido" in st.session_state:
    prompt_inicial = st.session_state.input_rapido
    del st.session_state.input_rapido # Limpiar para la próxima
else:
    prompt_inicial = None

# --- 4. TÍTULO PRINCIPAL ---
st.title("👨‍🍳 ChefBot Argentina")
st.caption("Tu asistente experto en sabores regionales y recetas autóctonas.")

# --- 5. RENDERIZAR MENSAJES ANTERIORES ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Si el mensaje tiene info extra (fuente), la mostramos discreta
        if "fuente" in message and message["fuente"]:
            st.caption(f"ℹ️ Fuente: {message['fuente']}")

# --- 6. CAJA DE TEXTO Y LÓGICA PRINCIPAL ---
# Aceptamos input del usuario o de los botones de sugerencia
if prompt := (st.chat_input("Preguntame sobre una receta...") or prompt_inicial):
    
    # A. Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B. Llamada a la API (Backend)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            with st.spinner("Buscando en el libro de recetas..."):
                # Petición POST a tu FastAPI
                payload = {"pregunta": prompt}
                response = requests.post(API_URL, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extraer datos según tu esquema Pydantic
                    texto_respuesta = data["respuesta"]
                    intencion = data["intencion_detectada"]
                    
                    # Mostrar respuesta
                    message_placeholder.markdown(texto_respuesta)
                    st.caption(f"Intencion: {intencion}")
                    
                    # Guardar en historial
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": texto_respuesta,
                        "intencion": intencion
                    })
                    
                else:
                    error_msg = f"Error {response.status_code}: No pude conectar con la cocina."
                    message_placeholder.error(error_msg)
                    
        except requests.exceptions.ConnectionError:
            message_placeholder.error("🚨 Error de conexión: Asegúrate de que el backend (FastAPI) esté corriendo en el puerto 8000.")
        except Exception as e:
            message_placeholder.error(f"Ocurrió un error inesperado: {str(e)}")
            
    # Si vino de un botón, forzamos la recarga para limpiar el estado
    if prompt_inicial:
        st.rerun()