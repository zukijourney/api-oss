import nltk
from . import exceptions
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from .routes.normal import chat, models
from .routes.others import root, images, cdn, embeddings, tts, audio, admin
from .routes.rp import chat as rp_chat, models as rp_models

app = FastAPI(docs_url=None)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.add_exception_handler(404, exceptions.not_found)
app.add_exception_handler(405, exceptions.method_not_allowed)
app.add_exception_handler(Exception, exceptions.exception_handler)
app.add_exception_handler(ValueError, exceptions.value_error_handler)
app.add_exception_handler(HTTPException, exceptions.http_exception_handler)
app.add_exception_handler(RequestValidationError, exceptions.validation_error_handler)

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
app.include_router(admin.app)

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)