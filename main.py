from fastapi import FastAPI, HTTPException
import uvicorn

from schemas import ConsultaRequest, ConsultaResponse
import services

# --- 1. CONFIGURACIÓN DE LA APP ---
app = FastAPI(
    title="API ChefBot Argentina 🇦🇷",
    description="API de RAG con Orquestador Inteligente y Validación de Fidelidad.",
    version="1.0"
)

# --- 2. ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "online", "mensaje": "Bienvenido a la API de Gastronomía. Usa /docs para probar."}

@app.post("/chat", response_model=ConsultaResponse)
async def chat_endpoint(consulta: ConsultaRequest):
    """
    Endpoint inteligente:
    - Detecta intención (Saludo vs Búsqueda).
    - Si busca, hace RAG + Validación (Groundedness).
    - Retorna respuesta formateada.
    """
    try:
        print(f"--> Pregunta recibida: {consulta.pregunta}")
        
        # Llamamos al Orquestador en services.py
        resultado = services.orquestador_conversacional(consulta.pregunta)
        
        # Construimos la respuesta validadapara el frontend
        return ConsultaResponse(
            respuesta=resultado["respuesta"],
            intencion_detectada=resultado["intencion"],
            es_respuesta_verificada=resultado["validado"]
        )

    except Exception as e:
        print(f"❌ Error en el servidor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)