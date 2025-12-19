from pydantic import BaseModel

class ConsultaRequest(BaseModel):
    pregunta: str

class ConsultaResponse(BaseModel):
    respuesta: str
    intencion_detectada: str
    es_respuesta_verificada: bool