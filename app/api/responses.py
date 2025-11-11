from fastapi.responses import JSONResponse
from typing import Dict, Any


def success_response(message: str, data: Any = None, status_code: int = 200) -> JSONResponse:
    response = {"success": True, "message": message}
    if data is not None:
        response["data"] = data
    return JSONResponse(content=response, status_code=status_code)


def error_response(message: str, details: Dict = None, status_code: int = 400) -> JSONResponse:
    response = {"success": False, "message": message}
    if details:
        response["details"] = details
    return JSONResponse(content=response, status_code=status_code)


class APIMessages:
    TRANSACTION_CREATED = "Transação criada com sucesso"
    TRANSACTION_UPDATED = "Transação atualizada com sucesso"
    TRANSACTION_DELETED = "Transação deletada com sucesso"
    TRANSACTION_NOT_FOUND = "Transação não encontrada"
    UNAUTHORIZED_ACCESS = "Você não tem permissão para acessar este recurso"
    
    USER_REGISTERED = "Usuário registrado com sucesso"
    USER_LOGGED_IN = "Login realizado com sucesso"
    INVALID_CREDENTIALS = "Usuário ou senha incorretos"
    INVALID_TOKEN = "Token inválido ou expirado"
    INVALID_INVITE_CODE = "Código de convite inválido"
    USERNAME_TAKEN = "Nome de usuário já cadastrado"
    EMAIL_TAKEN = "E-mail já cadastrado"
    
    INVITE_CODE_GENERATED = "Código de convite gerado com sucesso"
