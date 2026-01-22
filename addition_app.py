from fastapi import FastAPI

app = FastAPI(title="Addition API")

@app.get("/addition")
def addition(a: int, b: int):
    return {"result": a + b, "operation": "addition"}

@app.get("/health")
def health():
    return {"status": "UP", "service": "Addition API"}
