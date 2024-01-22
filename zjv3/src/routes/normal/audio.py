import traceback
import json
from fastapi import APIRouter, File, UploadFile, Response, Depends
from ...providers import cf
from ...utils.security import security

app = APIRouter()

@app.post("/v1/audio/transcriptions", dependencies=[Depends(security)])
async def audio(_, file: UploadFile = File(...)) -> None:
    try:
        text = await cf.whisper(await file.read())
        return {"text": text}
    except Exception as e:
        print(traceback.format_exc())
        return Response(content=json.dumps({
            "error": {
                "message": str(e),
                "type": "error",
                "tip": "Troubleshoot at: https://discord.gg/zukijourney",
                "param": None,
                "code": 500
            }
        }), status_code=500)