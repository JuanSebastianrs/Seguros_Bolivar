"""
Excepciones personalizadas del dominio.

Estas excepciones representan errores de negocio que burbujean
desde el dominio hacia la capa de API para ser convertidos en
respuestas HTTP apropiadas.
"""


class CompanyNotFoundError(Exception):
    """La compañía solicitada no está parametrizada en el sistema."""

    def __init__(self, compania: str):
        self.compania = compania
        super().__init__(
            f"La compañía '{compania}' no se encuentra registrada en el sistema."
        )


class DuplicateRequestError(Exception):
    """La solicitud ya fue procesada previamente (control de duplicados)."""

    def __init__(self, solicitud_id: str):
        self.solicitud_id = solicitud_id
        super().__init__(
            f"La solicitud '{solicitud_id}' ya fue procesada anteriormente."
        )


class ExternalPlatformError(Exception):
    """Error al comunicarse con la plataforma externa del cliente."""

    def __init__(self, detail: str = "Error de comunicación con plataforma externa"):
        self.detail = detail
        super().__init__(detail)


class LLMOutputError(Exception):
    """El LLM retornó un output inválido que no pasa la validación Pydantic."""

    def __init__(self, provider: str, detail: str):
        self.provider = provider
        self.detail = detail
        super().__init__(
            f"Output inválido del proveedor '{provider}': {detail}"
        )
