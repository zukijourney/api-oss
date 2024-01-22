from fastapi import APIRouter, Response
import json

app = APIRouter()

@app.route("/models",methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
@app.route("/v1/models",methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
@app.route("/v1/chat/completions/models",methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
@app.route("/v1/chat/completions/v1/chat/completions/models",methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
@app.route("/models/images", methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
@app.route("/models", methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
@app.route("/v1/models/images", methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
@app.route("/v1/models", methods=["GET", "POST", "PUT", "PATCH", "HEAD"])
async def models(_):
    return Response(json.dumps(json.load(open('data/models/normal/models.json')), indent=4))