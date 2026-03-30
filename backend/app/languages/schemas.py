from app.base_schema import CamelModel


class LanguageOut(CamelModel):
    id: int
    code: str
    name: str
    flag: str | None
