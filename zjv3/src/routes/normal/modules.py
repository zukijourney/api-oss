from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

app = APIRouter()

@app.route("/unf/api/modules", methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
@app.route("/unf/chat/completions/api/modules", methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
@app.route("/v1/api/modules", methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
@app.route("/v1/chat/completions/api/modules", methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
async def modules(_):
    return PlainTextResponse("big chungus")