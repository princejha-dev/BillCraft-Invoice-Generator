from fastapi import FastAPI,HTTPException,Path
from pydantic import ValidationError
from fastapi.responses import Response
from model import Invoice, InvoiceUpadte
import json
import os

def load_data()-> dict[str,dict]:  
    if not os.path.exists("invoice.json"):
        return {}
    
    # If file is empty, return {}
    if os.path.getsize("invoice.json") == 0:
        return {}
    
    try:
        #loads data from json file
        with open('invoice.json','r') as f:
           data=json.load(f)
    except json.JSONDecodeError:
        return {}

    return data

def save_data(data):
    #saves data in json file
    with open('invoice.json','w') as f:
         json.dump(data,f,indent=4)


app=FastAPI()

@app.get("/")
def home():
    return {"message":"Bill craft invoice generator"}


@app.post("/create")
def create_invoice(invoice:Invoice):

    #load data
    data=load_data()
    
    #pydantic model -> dict
    invoice_dict=invoice.model_dump(mode="json")

    invoice_id=invoice_dict["invoice_id"]
    
    #check data if already exits
    if invoice_id in data:
        raise HTTPException(status_code=400, detail=f"Invoice ID '{invoice_id}' already exists")
          
    data[invoice_id]=invoice_dict
    
    #save data
    save_data(data)

    return Response(status_code=201,content="Invoice created succesfully")


@app.get("/get_invoice/{invoice_id}")
def get_invoice(invoice_id:str):

    #load data
    data=load_data()

    #check invoice exist or not
    if invoice_id not in data:
        raise HTTPException(status_code=404, detail=f"Invoice ID '{invoice_id}' not found")
    
    return data[invoice_id]


@app.put("/update/{invoice_id}", status_code=200)
def update_invoice(invoice_id: str, invoice_data: InvoiceUpadte ):

    data = load_data()

    # check invoice exists
    if invoice_id not in data:
        raise HTTPException(status_code=404, detail=f"Invoice ID '{invoice_id}' not found")
    
    existing_data = data[invoice_id]

    # extract user updated data (only provided fields)
    updated_data = invoice_data.model_dump(exclude_unset=True)
    existing_data.update(updated_data)

    #re-validatate full object 
    try:
        validate_invoice=Invoice(**existing_data)
    except ValidationError as e:
        raise HTTPException(status_code=400,detail=e.errors())
        
    
    data[invoice_id] = validate_invoice.model_dump(mode="json")

    # save data
    save_data(data)

    return {"message": "Invoice updated successfully", "invoice": data[invoice_id]}



@app.delete("/delete/{invoice_id}", status_code=200)
def delete_invoice(invoice_id: str = Path(..., description="Invoice ID to delete", examples=["1"])):
    data = load_data()

    if invoice_id not in data:
        raise HTTPException(status_code=404, detail=f"Invoice ID '{invoice_id}' not found")

    del data[invoice_id]
    save_data(data)

    return {"message": "Invoice successfully deleted from database"}





    





    




