from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model: accepts snake_case fields from Python/ORM, serialises as camelCase for the frontend."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,   # accept both snake_case and camelCase as input
        from_attributes=True,    # allow creation from ORM objects
        serialize_by_alias=True, # output camelCase JSON
    )


class Pagination(CamelModel):
    page: int
    page_size: int   # → serialised as "pageSize"
    total: int
