from fastapi import FastAPI

app = FastAPI()


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