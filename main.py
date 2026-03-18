from fastapi import FastAPI,HTTPException
from fastapi.responses import Response
from model import Invoice
import json
import os

def load_data()-> dict[str,dict]:
    
    if not os.path.exists("invoice.json"):
        return {}
    
    # If file is empty, return {}
    if os.path.getsize("invoice.json") == 0:
        return {}
    
    #loads data from json file
    with open('invoice.json','r') as f:
        data=json.load(f)

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

    #check invoice exist
    if invoice_id not in data:
        raise HTTPException(status_code=404, detail=f"Invoice ID '{invoice_id}' not found")
    
    return data[invoice_id]




    




