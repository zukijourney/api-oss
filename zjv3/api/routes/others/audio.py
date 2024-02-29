from fastapi import APIRouter, File, UploadFile, Depends
from ...providers.openai import openai
from ...utils.security import user_checks

app = APIRouter()

@app.post("/v1/audio/transcriptions", dependencies=[Depends(user_checks)])
async def audio(_, file: UploadFile = File(...)) -> None:
    text = await openai(await file.read())
    return {"text": text}