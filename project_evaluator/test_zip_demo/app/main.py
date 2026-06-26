from fastapi import FastAPI, HTTPException
from app.models import Item
from app.db import get_items, add_item

app = FastAPI(title="Inventory API")

@app.get("/items")
def list_items():
    return get_items()

@app.post("/items")
def create_item(item: Item):
    return add_item(item)

@app.get("/items/{item_id}")
def get_item(item_id: int):
    items = get_items()
    for i in items:
        if i["id"] == item_id:
            return i
    raise HTTPException(status_code=404, detail="Item not found")
