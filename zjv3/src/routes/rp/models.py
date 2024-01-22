from fastapi import APIRouter, Response
import json

app = APIRouter()

@app.route("/unf/models", methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
async def models(_):
    return Response(json.dumps(json.load(open('data/models/rp/models.json')), indent=4))