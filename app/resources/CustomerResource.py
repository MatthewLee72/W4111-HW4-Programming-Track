from __future__ import annotations


from pydantic import BaseModel, Field

from .AbstractBaseResource import AbstractBaseResource
from ..services.MySQLDataService import MySQLDataService

class Customer(BaseModel):
    customerNumber: int | None = None
    customerName: str
    contactLastName: str
    contactFirstName: str
    phone: str
    addressLine1: str
    addressLine2: str | None = None
    city: str 
    state: str | None = None
    postalCode: str | None = None
    country: str
    salesRepEmployeeNumber: int | None = None
    creditLimit: float | None = None

class CustomerCollection(BaseModel):
    items: list[Customer] = Field(default_factory=list)


class CustomerResource(AbstractBaseResource):
    def __init__(self, config: dict | None = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)
        service_config: dict = {
            "table_name": str(cfg.get("table_name", "customers")),
            "primary_key_field": str(cfg.get("primary_key_field", "customerNumber")),
        }
        self._service = MySQLDataService(service_config)

    def get(self, template: dict) -> CustomerCollection:
        rows = self._service.retrieveByTemplate(template)
        return CustomerCollection(
            items=[Customer.model_validate(r) for r in rows]
        )

    def get_by_id(self, id: str) -> Customer:
        row = self._service.retrieveByPrimaryKey(str(id))
        if not row:
            raise ValueError(f"No customerNumber with id {id!r}")
        return Customer.model_validate(row)

    def post(self, new_data: Customer) -> str:
        data = new_data.model_dump(exclude_none=True)
        return self._service.create(data)

    def delete(self, id: str) -> int:
        return self._service.deleteByPrimaryKey(str(id))

    def put(self, customer_number: str, new_data: Customer) -> int:
        data = new_data.model_dump()
        data["customerNumber"] = customer_number
        return self._service.updateByPrimaryKey(customer_number, data)
