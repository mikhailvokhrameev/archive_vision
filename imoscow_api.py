from fastapi import FastAPI

app = FastAPI(title="My Test Hack API")

@app.get("/")
def read_root():
    
    return {"hack": "imoscow"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    """
    Принимает ID элемента и опциональный параметр q.
    """
    return {"item_id": item_id, "q": q}
