from __future__ import annotations

from pydantic import BaseModel, Field

from .AbstractBaseResource import AbstractBaseResource
from ..services.MySQLDataService import MySQLDataService

class OrderDetails(BaseModel):
    orderNumber: int
    productCode: str
    quantityOrdered: int
    priceEach: float
    orderLineNumber: int

class OrderDetailsCollection(BaseModel):
    items: list[OrderDetails] = Field(default_factory=list)


class OrderDetailsResource(AbstractBaseResource):
    def __init__(self, config: dict | None = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)
        service_config: dict = {
            "table_name": str(cfg.get("table_name", "orderdetails")),
            "primary_key_field": cfg.get("primary_key_field", ["orderNumber", "productCode"]),
        }
        self._service = MySQLDataService(service_config)

    def get(self, template: dict) -> OrderDetailsCollection:
        rows = self._service.retrieveByTemplate(template)
        return OrderDetailsCollection(
            items=[OrderDetails.model_validate(r) for r in rows]
        )

    def get_by_id(self, id: str) -> OrderDetails:
        row = self._service.retrieveByPrimaryKey(str(id))
        if not row:
            raise ValueError(f"No orderNumber with id {id!r}")
        return OrderDetails.model_validate(row)

    def post(self, new_data: OrderDetails) -> str:
        data = new_data.model_dump()
        return self._service.create(data)

    def delete(self, id: str) -> int:
        return self._service.deleteByPrimaryKey(str(id))

    def put(self, order_number: str, product_code: str, new_data: OrderDetails) -> int:
        composite_key = f"{order_number}::{product_code}"
        data = new_data.model_dump()
        data["orderNumber"] = int(order_number)
        data["productCode"] = product_code
        return self._service.updateByPrimaryKey(composite_key, data)
