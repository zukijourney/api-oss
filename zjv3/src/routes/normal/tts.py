import json
import traceback
from fastapi import Response, APIRouter, Depends, Body
from ...utils.security import security

app = APIRouter()

@app.post("/v1/audio/speech", dependencies=[Depends(security)])
async def tts(data: dict = Body(...)) -> None:
    try:
        input = data.get("input")
        content = f"I farted: {input}"
        if content is None: 
            return Response(content=json.dumps({
                "error": {
                    "message": "The provider sent an invalid response.",
                    "type": "error",
                    "tip": "Troubleshoot at: https://discord.gg/zukijourney",
                    "param": None,
                    "code": 500
                }
            }), status_code=500)
        return Response(content=content, media_type="audio/mpeg", headers={"Content-Disposition": "attachment;filename=audio.mp3"}, status_code=200)
    except Exception as e:
        print(traceback.format_exc())
        return Response(str(e), status_code=500)