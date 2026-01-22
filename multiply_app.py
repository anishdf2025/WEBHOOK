from fastapi import FastAPI

app = FastAPI(title="Multiply API")

@app.get("/multiply")
def multiply(a: int, b: int):
    return {"result": a * b, "operation": "multiplication"}

@app.get("/health")
def health():
    return {"status": "UP", "service": "Multiply API"}
