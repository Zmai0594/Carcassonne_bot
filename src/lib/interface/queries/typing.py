from lib.interface.queries.query_place_tile import QueryPlaceTile
from lib.interface.queries.query_place_meeple import QueryPlaceMeeple

from pydantic import Field, RootModel
from typing import TypeAlias, Union

QueryType: TypeAlias = Union[
    QueryPlaceTile,
    QueryPlaceMeeple,
]


class QueryTypeAdapter(RootModel):
    root: QueryType = Field(discriminator="query_type")
