import json
import nltk
import uvicorn
from fastapi.exceptions import HTTPException
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from .routes.normal import root, models, chat, images, cdn, embeddings, tts, audio, status, modules
from .routes.rp import chat as rp_chat, models as rp_models

app = FastAPI(docs_url=None)

@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    return Response(json.dumps(exc.detail), status_code=exc.status_code)

@app.exception_handler(404)
async def error_handler(request: Request, _):
    return Response(content=json.dumps({"error": {"message": f"Invalid URL ({request.method} {request.url.path})", "type": "error", "param": None, "code": 404}}, indent=4), status_code=404)

@app.exception_handler(405)
async def error_handler(request: Request, _):
    return Response(content=json.dumps({"error": {"message": f"Method Not Allowed ({request.method} {request.url.path})", "type": "error", "param": None, "code": 405}}, indent=4), status_code=405)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(root.app)
app.include_router(models.app)
app.include_router(images.app)
app.include_router(chat.app)
app.include_router(cdn.app)
app.include_router(embeddings.app)
app.include_router(tts.app)
app.include_router(audio.app)
app.include_router(rp_chat.app)
app.include_router(rp_models.app)
app.include_router(status.app)
app.include_router(modules.app)

if __name__ == "__main__":
    nltk.download("punkt")
    nltk.download("stopwords")