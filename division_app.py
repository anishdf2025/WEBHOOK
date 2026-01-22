from fastapi import FastAPI, HTTPException

app = FastAPI(title="Division API")

@app.get("/division")
def division(a: int, b: int):
    if b == 0:
        raise HTTPException(status_code=400, detail="Division by zero")
    return {"result": a / b, "operation": "division"}

@app.get("/health")
def health():
    return {"status": "UP", "service": "Division API"}
