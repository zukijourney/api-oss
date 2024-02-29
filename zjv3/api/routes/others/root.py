from fastapi import APIRouter, Response
import json

app = APIRouter()

@app.route("/", methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
async def root(_) -> None:
    return Response(json.dumps({
        "message": "Welcome to the Zukijourney API!",
        "invite": "discord.gg/zukijourney"
    }, indent=4), media_type="application/json")