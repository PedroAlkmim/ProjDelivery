from app.schemas.comum import Email, Entrada, Saida


class LoginIn(Entrada):
    email: Email
    senha: str

    model_config = {
        "json_schema_extra": {
            "example": {"email": "cliente@email.com", "senha": "123456"}
        }
    }


class TokenOut(Saida):
    access_token: str
    token_type: str = "bearer"
    perfil: str
    id_usuario: int
    id_perfil: int
    nome: str


class SessaoOut(Saida):
    id_usuario: int
    nome: str
    email: str
    perfil: str
    id_perfil: int
