from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

fake_db = []

class Item(BaseModel):
    name: str
    price: float
    in_stock: bool = True


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/weather")
async def get_weather():
    return {
        "city": "New York",
        "temperature": 20,
        "description": "sunny"
    }

@app.post("/items")
async def create_item(item: Item):
    fake_db.append(item.dict())
    return {"message": "Item created successfully"}

@app.get("/items")
async def get_items():
    return {"items": fake_db}