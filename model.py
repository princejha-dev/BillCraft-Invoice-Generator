from pydantic import BaseModel,Field,computed_field
import datetime
from typing import Annotated,List,Optional


#Desginging overall schema of database(Json file)

#business model
class Business(BaseModel):
    business_name:str
    gst:str

#customer model
class Customer(BaseModel):
    customer_name:str
    address:str


#Items (product) model
class Item(BaseModel):
    product_name:str
    quantity:Annotated[int,Field(ge=0)]
    price:Annotated[float,Field(ge=0)]


#tax model
class Tax(BaseModel):
    sgst:float
    cgst:float


#invoice model
class Invoice(BaseModel):
    invoice_id:str
    invoice_no:str
    date:datetime.date

    business:Business
    customer:Customer

    items:List[Item]
    tax:Tax

    discount: float = Field(default=0, ge=0)
    
    #calculating subtotal , tax , total 
    @computed_field
    @property
    def subtotal(self)->float:

        return sum(item.quantity * item.price for item in self.items)
    
    @computed_field
    @property
    def tax_amount(self)->float:

     return self.subtotal*(self.tax.sgst + self.tax.cgst)/100
    
    @computed_field
    @property
    def total(self) -> float:
        discount_value = (self.subtotal * self.discount) / 100
        return (self.subtotal + self.tax_amount) - discount_value

#invoice update model
class InvoiceUpadte(BaseModel):
    invoice_no:Optional[str]=None
    date: Optional[datetime.date] = None
    business: Optional[Business]=None
    customer: Optional[Customer]=None
    items: Optional[list[Item]]=None
    tax:Optional[Tax]=None
    discount: Optional[float]=Field(default=None,ge=0)

