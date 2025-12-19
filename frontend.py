import streamlit as st
import requests

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="ChefBot Argentina 🇦🇷",
    page_icon="👨‍🍳",
    layout="centered"
)

API_URL = "http://127.0.0.1:8000/chat"

# --- 🚀 NUEVO: FUNCIÓN PARA MOSTRAR VALIDACIÓN ---
def mostrar_estado_validacion(intencion, es_verificado):
    """
    Muestra visualmente si la respuesta fue validada contra el libro o no.
    """
    # Solo mostramos el semáforo si es una consulta al libro (no en saludos)
    if "Consulta" in intencion or "Recetas" in intencion or "Libro" in intencion:
        if es_verificado:
            st.success("✅ Verificado: Información fiel al libro.", icon="🛡️")
        else:
            st.warning("⚠️ Advertencia: Posible alucinación. No encontrado en el texto.", icon="🚩")
    
    # Mostramos la fuente siempre
    st.caption(f"ℹ️ Fuente: {intencion}")


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
    
    for ej in ejemplos:
        if st.button(ej):
            st.session_state.input_rapido = ej

    st.divider()
    if st.button("🗑️ Borrar conversación"):
        st.session_state.messages = []
        st.rerun()

# --- 3. ESTADO DE LA SESIÓN ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "input_rapido" in st.session_state:
    prompt_inicial = st.session_state.input_rapido
    del st.session_state.input_rapido 
else:
    prompt_inicial = None

# --- 4. TÍTULO ---
st.title("👨‍🍳 ChefBot Argentina")
st.caption("Tu asistente experto en sabores regionales y recetas autóctonas.")

# --- 5. RENDERIZAR MENSAJES ANTERIORES ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # 🚀 NUEVO: Si es el asistente, mostramos su estado de validación guardado
        if message["role"] == "assistant":
            # Usamos .get() por seguridad (por si hay mensajes viejos sin este campo)
            mostrar_estado_validacion(
                message.get("intencion", ""), 
                message.get("verificado", True)
            )

# --- 6. LÓGICA PRINCIPAL ---
if prompt := (st.chat_input("Preguntame sobre una receta...") or prompt_inicial):
    
    # A. Mostrar mensaje usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B. Llamada a la API
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            with st.spinner("Buscando en el libro de recetas..."):
                payload = {"pregunta": prompt}
                response = requests.post(API_URL, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extraer datos
                    texto_respuesta = data["respuesta"]
                    intencion = data["intencion_detectada"]
                    # 🚀 NUEVO: Capturamos el booleano de validación
                    es_verificado = data["es_respuesta_verificada"]
                    
                    # 1. Mostrar respuesta de texto
                    message_placeholder.markdown(texto_respuesta)
                    
                    # 2. 🚀 NUEVO: Mostrar el semáforo de validación
                    mostrar_estado_validacion(intencion, es_verificado)
                    
                    # 3. Guardar en historial (incluyendo el estado de verificación)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": texto_respuesta,
                        "intencion": intencion,
                        "verificado": es_verificado # <-- Guardamos esto
                    })
                    
                else:
                    message_placeholder.error(f"Error {response.status_code}: No pude conectar con la cocina.")
                    
        except requests.exceptions.ConnectionError:
            message_placeholder.error("🚨 Error de conexión: Asegúrate de que el backend (FastAPI) esté corriendo en el puerto 8000.")
        except Exception as e:
            message_placeholder.error(f"Ocurrió un error inesperado: {str(e)}")
            
    if prompt_inicial:
        st.rerun()