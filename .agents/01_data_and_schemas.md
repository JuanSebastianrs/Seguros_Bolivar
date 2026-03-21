# 📄 ESPECIFICACIÓN DE DATOS Y CONTRATOS (01_data_and_schemas) - REVISADO

## 🎯 Objetivo
Definir estrictamente los contratos de Pydantic V2 y la configuración YAML, asegurando el cumplimiento de los bonos y los formatos exactos de salida.

## 1. Contratos Pydantic (app/api/schemas.py)

### Modelo de Entrada (SolicitudInput)
class SolicitudInput(BaseModel):
    compania: str
    solicitud_id: str
    solicitud_descripcion: str # Alias de solicitud_descripcion si es necesario

### Modelo de Salida (SolicitudOutput)
IMPORTANTE: Respeta las mayúsculas exactas usando serialization_alias.

class SolicitudOutput(BaseModel):
    compania: str
    solicitud_id: str
    # Nota la S mayúscula en el requerimiento 
    solicitud_fecha: str = Field(..., serialization_alias="Solicitud_fecha") 
    solicitud_tipo: str
    solicitud_prioridad: str
    solicitud_id_cliente: str # Ej: "CC"
    solicitud_tipo_id_cliente: str # Ej: "102045678"
    # Solo presente en GESTIÓN EXTERNA
    solicitud_id_plataforma_externa: str | None = None 
    proximo_paso: str
    justificacion: str
    estado: str

## 2. Base de Datos Simulada (data/tenants_config.yaml)
Se incorporan los métodos de prioridad y categorías exactas.

# data/tenants_config.yaml
empresas:
  "GASES DEL ORINOCO":
    metodo_prioridad: "ia"
    campos_obligatorios: ["cedula", "nombre", "problema"]
    categorias:
      - "Incidente técnico"  # Nombre exacto del output
      - "Reclamo de facturación"
      - "Consulta administrativa"
    reglas_enrutamiento:
      "Incidente técnico":
        "Alta": "GESTIÓN EXTERNA"
        "Media": "GESTIÓN EXTERNA"
        "Baja": "RESPUESTA DIRECTA"

  "MENSAJERIA DEL VALLE":
    metodo_prioridad: "externo" # Bono +6%: Llama a adaptador especializado
    campos_obligatorios: ["tipo_documento", "numero_documento", "tipo_solicitud"]
    categorias:
      - "Retraso de envío"
      - "Dañado en tránsito"
    reglas_enrutamiento:
      "Retraso de envío":
        "Alta": "GESTIÓN EXTERNA"

    "LOGISTICA ANDINA":
        metodo_prioridad: "ia"
        campos_obligatorios: ["placa_vehiculo", "novedad"]
        categorias:
        - "Falla mecánica"
        - "Reporte de accidente"
        - "Retraso en ruta"
        reglas_enrutamiento:
        "Falla mecánica":
            "Alta": "GESTIÓN EXTERNA"
            "Media": "GESTIÓN EXTERNA"
            "Baja": "RESPUESTA DIRECTA"
        "Reporte de accidente":
            "Alta": "GESTIÓN EXTERNA"
            "Media": "GESTIÓN EXTERNA"

  "TECH SOLUTIONS":
    metodo_prioridad: "ia"
    campos_obligatorios: ["email_usuario", "error_code"]
    categorias:
      - "Caída de servicio"
      - "Soporte Nivel 1"
      - "Cambio de contraseña"
    reglas_enrutamiento:
      "Caída de servicio":
        "Alta": "GESTIÓN EXTERNA"
        "Media": "GESTIÓN EXTERNA"
      "Cambio de contraseña":
        "Alta": "RESPUESTA DIRECTA"
        "Media": "RESPUESTA DIRECTA"
        "Baja": "RESPUESTA DIRECTA"

---

## 📝 Tarea para Antigravity
Crea app/api/schemas.py usando Pydantic V2. Usa Field(..., serialization_alias=...) para garantizar que el JSON de salida tenga las mayúsculas/minúsculas exactas del ejemplo de la prueba.

Crea data/tenants_config.yaml. Asegúrate de que el campo metodo_prioridad exista para diferenciar entre lógica de LLM y servicios externos.