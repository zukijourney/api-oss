from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

app = APIRouter()

@app.route("/status", methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
async def status(_):
    return PlainTextResponse("It works!")