from fastapi import FastAPI,HTTPException,Path
from fastapi.responses import Response
from model import Invoice
import json

def load_data():
    
    #loads data from json file
    with open('invoice.json','r') as f:
        data=json.load(f)

    return data

def save_data(data):

    #saves data in json file
    with open('invoice.json','w') as f:
         json.dump(data,f)


app=FastAPI()

@app.get("/")
def home():
    return {"message":"Bill craft invoice generator"}


@app.post("/create")
def create_invoice(invoice:Invoice):
    
    #pydantic model -> dict
    data=invoice.model_dump_json()
    
    #save data
    save_data(data)

    return Response(status_code=201,content="Invoice created succesfully")




    




