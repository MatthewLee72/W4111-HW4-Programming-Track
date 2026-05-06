from __future__ import annotations

from pydantic import BaseModel, Field

from .AbstractBaseResource import AbstractBaseResource
from ..services.MySQLDataService import MySQLDataService

from datetime import date

class Order(BaseModel):
    orderNumber: int | None = None
    orderDate: date
    requiredDate: date
    shippedDate: date | None = None
    status: str
    comments: str | None = None
    customerNumber: int

class OrderCollection(BaseModel):
    items: list[Order] = Field(default_factory=list)


class OrderResource(AbstractBaseResource):
    def __init__(self, config: dict | None = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)
        service_config: dict = {
            "table_name": str(cfg.get("table_name", "orders")),
            "primary_key_field": str(cfg.get("primary_key_field", "orderNumber")),
        }
        self._service = MySQLDataService(service_config)

    def get(self, template: dict) -> OrderCollection:
        rows = self._service.retrieveByTemplate(template)
        return OrderCollection(
            items=[Order.model_validate(r) for r in rows]
        )

    def get_by_id(self, id: str) -> Order:
        row = self._service.retrieveByPrimaryKey(str(id))
        if not row:
            raise ValueError(f"No orderNumber with id {id!r}")
        return Order.model_validate(row)

    def post(self, new_data: Order) -> str:
        data = new_data.model_dump(exclude_none=True)
        return self._service.create(data)

    def delete(self, id: str) -> int:
        return self._service.deleteByPrimaryKey(str(id))

    def put(self, order_number: str, new_data: Order) -> int:
        data = new_data.model_dump()
        data["orderNumber"] = order_number
        return self._service.updateByPrimaryKey(order_number, data)
