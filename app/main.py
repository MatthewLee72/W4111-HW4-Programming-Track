from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pymysql

if __package__ in (None, ""):
    # Supports running this file directly (e.g., PyCharm "main.py" debug config).
    sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.resources.CustomerResource import (
    Customer,
    CustomerCollection,
    CustomerResource,
)
from app.resources.OrderResource import (
    Order,
    OrderCollection,
    OrderResource,
)
from app.resources.OrderDetailsResource import (
    OrderDetails,
    OrderDetailsCollection,
    OrderDetailsResource,
)


def _get_app_name() -> str:
    # Keep settings minimal in this starter; use environment variables when needed.
    return os.getenv("APP_NAME", "Starter FastAPI App")


app = FastAPI(title=_get_app_name(), version="0.1.0")

@app.exception_handler(pymysql.err.IntegrityError)
def integrity_error_handler(request: Request, exc: pymysql.err.IntegrityError):
    return JSONResponse(
        status_code=409,
        content={"detail": "Database integrity conflict (e.g., duplicate key or foreign key constraint)"},
    )

customer_resource = CustomerResource()
order_resource = OrderResource()
order_details_resource = OrderDetailsResource()


class EchoRequest(BaseModel):
    message: str


@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {"message": "Hello from FastAPI"}


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/echo", tags=["echo"])
def echo(payload: EchoRequest) -> EchoRequest:
    return payload

@app.get("/customers", tags=["customers"])
def get_customers(
    customerNumber: int | None = None
) -> CustomerCollection:
    template: dict = {}
    if customerNumber is not None:
        template["customerNumber"] = customerNumber
    return customer_resource.get(template)


@app.post("/customers", tags=["customers"])
def create_customer(new_data: Customer) -> str:
    new_id = customer_resource.post(new_data)
    return str(new_id)

@app.get("/customers/{customer_number}", tags=["customers"])
def get_customer_by_id(customer_number: str) -> Customer:
    try:
        return customer_resource.get_by_id(customer_number)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

@app.put("/customers/{customer_number}", tags=["customers"])
def update_customer(
    customer_number: str, new_data: Customer
) -> dict[str, int]:
    try:
        updated = customer_resource.put(customer_number, new_data)
        if updated == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"updated": updated}


@app.delete("/customers/{customer_number}", tags=["customers"])
def delete_customer(customer_number: str) -> dict[str, int]:
    deleted = customer_resource.delete(customer_number)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"deleted": deleted}

@app.get("/orders", tags=["orders"])
def get_orders(
    orderNumber: int | None = None,
    customerNumber: int | None = None,
) -> OrderCollection:
    template: dict = {}
    if orderNumber is not None:
        template["orderNumber"] = orderNumber
    if customerNumber is not None:
        template["customerNumber"] = customerNumber
    return order_resource.get(template)

@app.post("/orders", tags=["orders"])
def create_order(new_data: Order) -> str:
    new_id = order_resource.post(new_data)
    return str(new_id)

@app.get("/orders/{order_number}", tags=["orders"])
def get_order_by_id(order_number: str) -> Order:
    try:
        return order_resource.get_by_id(order_number)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

@app.put("/orders/{order_number}", tags=["orders"])
def update_order(
    order_number: str, new_data: Order
) -> dict[str, int]:
    try:
        updated = order_resource.put(order_number, new_data)
        if updated == 0:
            raise HTTPException(status_code=404, detail="Order not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"updated": updated}

@app.delete("/orders/{order_number}", tags=["orders"])
def delete_order(order_number: str) -> dict[str, int]:
    deleted = order_resource.delete(order_number)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"deleted": deleted}

@app.get("/orderdetails", tags=["orderdetails"])
def get_order_details(
    orderNumber: int | None = None,
    productCode: str | None = None,
) -> OrderDetailsCollection:
    template: dict = {}
    if orderNumber is not None:
        template["orderNumber"] = orderNumber
    if productCode is not None:
        template["productCode"] = productCode
    return order_details_resource.get(template)


@app.post("/orderdetails", tags=["orderdetails"])
def create_order_detail_collection(new_data: OrderDetails) -> str:
    new_id = order_details_resource.post(new_data)
    return str(new_id)


@app.get("/orders/{order_number}/orderdetails", tags=["orderdetails"])
def get_order_details_for_order(order_number: str) -> OrderDetailsCollection:
    return order_details_resource.get({"orderNumber": int(order_number)})

@app.get("/orders/{order_number}/orderdetails/{product_code}", tags=["orderdetails"])
def get_order_detail_by_id(order_number: str, product_code: str) -> OrderDetails:
    composite_key = f"{order_number}::{product_code}"
    try:
        return order_details_resource.get_by_id(composite_key)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.put("/orders/{order_number}/orderdetails/{product_code}", tags=["orderdetails"])
def update_order_detail(
    order_number: str, product_code: str, new_data: OrderDetails
) -> dict[str, int]:
    try:
        updated = order_details_resource.put(order_number, product_code, new_data)
        if updated == 0:
            raise HTTPException(status_code=404, detail="Order detail not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"updated": updated}


@app.delete("/orders/{order_number}/orderdetails/{product_code}", tags=["orderdetails"])
def delete_order_detail(order_number: str, product_code: str) -> dict[str, int]:
    composite_key = f"{order_number}::{product_code}"
    deleted = order_details_resource.delete(composite_key)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Order detail not found")
    return {"deleted": deleted}

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(app, host=host, port=port)

