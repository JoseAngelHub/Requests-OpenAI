from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from utils.api_handler import create_ac, process_invoice_data
from utils.token import get_token
import core.logger as R

R.Logger('logs')

router = APIRouter()

class Supplier(BaseModel):
    name: str
    cif: str
    address: str
    postal_code: str
    city: str

class Invoice(BaseModel):
    supplier: Supplier
    packing_list_no: str
    date: str

class Product(BaseModel):
    reference: str
    description: str
    quantity: str
    price: str
    discount: str

class DataPayload(BaseModel):
    invoice: Invoice
    products: List[Product]

@router.post("/save_data")
def save_data(payload: DataPayload):
    """
    Este endpoint recibe un JSON (ya validado por Pydantic) 
    y lo inserta en la base de datos.
    """
    try:
        data_dict = payload.model_dump()

        token, token_exp = get_token()
        processed_data = process_invoice_data(token, data_dict)

        if not processed_data:
            raise HTTPException(status_code=500, detail="Error procesando los datos de la factura.")

        response_data = create_ac(token, processed_data)

        R.info("Datos insertados correctamente en la BD.")
        return {
            "status": "success",
            "message": "Data inserted successfully",
            "data": data_dict
        }

    except Exception as e:
        R.error(f"Error al insertar datos en la BD: {e}")
        raise HTTPException(status_code=500, detail=str(e))