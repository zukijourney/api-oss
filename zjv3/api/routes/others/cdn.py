import aiofiles
import json
import io
from curl_cffi.requests import AsyncSession
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse

app = APIRouter()

@app.get('/cdn/{image_uuid:str}')
async def cdn(image_uuid: str) -> None:
    try:
        async with aiofiles.open('data/images/list.json') as f:
            images = json.loads(await f.read())
    except:
        images = {}

    if not images.get(image_uuid, None):
        return Response(content=json.dumps({
            'error': {
                'message': 'The requested image was not found in our CDN.',
                'type': 'error',
                'param': None,
                'code': 404
            }
        }), status_code=404)

    try:
        async with AsyncSession(impersonate='chrome107') as session:
            r = await session.get(images.get(image_uuid))
            r.raise_for_status()
            image_content = r.content
    except:
        url = 'https://images.saatchiart.com/saatchi/160112/art/229190/104231-IBVCMQZI-7.jpg'
        async with AsyncSession(impersonate='chrome107') as session:
            r = await session.get(url)
            image_content = r.content
    
    return StreamingResponse(io.BytesIO(image_content), media_type=f'image/png', status_code=200)