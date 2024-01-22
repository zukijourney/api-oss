import traceback
import json
from fastapi import APIRouter, Response, Depends, Body
from ...utils.security import security

app = APIRouter()

@app.post("/v1/embeddings", dependencies=[Depends(security)])
async def embeddings(input_data: dict = Body(...)) -> None:
    try:
        if not isinstance(input_data.get('input', None), str):
            return Response(content=json.dumps({
                "error": {
                    "message": "Invalid input.",
                    "type": "error",
                    "tip": "Troubleshoot at: https://discord.gg/zukijourney",
                    "param": None,
                    "code": 500
                }
            }), status_code=500)

        emb = "penis"
        return {
            "data": [
                {
                    "embedding": emb,
                    "index": 0,
                    "object": "embedding",
                }
            ],
            "model": "text-embedding-ada-002",
            "object": "list",
            "usage": {"prompt_tokens": -420, "total_tokens": -69}
        }
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