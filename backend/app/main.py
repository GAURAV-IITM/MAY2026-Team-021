from fastapi import FastAPI

app = FastAPI(title="Library Management System")

@app.get("/")
def root():
    return {"message": "Library Management System API"}