from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

app = APIRouter()

@app.route("/", methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
async def root(_):
    return PlainTextResponse("zukijourney: https://discord.gg/zukijourney")