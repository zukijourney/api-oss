import json
import yaml
from ...database import DatabaseManager
from fastapi import APIRouter, Request, Response, Body, HTTPException

app = APIRouter()

with open('secrets/values.yml', 'r') as f:
    admin_key = yaml.safe_load(f)['admin_key']

@app.post('/core/{action:str}')
async def admin(request: Request, action: str, data: dict = Body(...)) -> None:
    if request.headers.get('Authorization', '').replace('Bearer ', '') != admin_key:
        raise HTTPException(detail={'success': False, 'error': 'Invalid admin key.'}, status_code=401)

    user_id = data.get('id', None)
    key = data.get('key', None)
    banned = data.get('banned', None)
    premium = data.get('premium', None)
    subscriber = data.get('subscriber', None)

    if not user_id and action == 'register':
        raise HTTPException(detail={'success': False, 'error': 'Invalid payload.'}, status_code=400)
    elif (not banned and not premium and not subscriber) and action == 'update':
        raise HTTPException(detail={'success': False, 'error': 'Invalid payload.'}, status_code=400)
    elif (not key and not user_id) and (action != 'register' and action != 'update'):
        raise HTTPException(detail={'success': False, 'error': 'Invalid payload.'}, status_code=400)

    if action == 'register':
        return await register_key(user_id)
    elif action == 'check':
        return await check_key(user_id, key)
    elif action == 'delete':
        return await delete_key(user_id, key)
    elif action == 'update':
        return await update_key(user_id, key, banned, premium, subscriber)

    raise HTTPException(detail={'success': False, 'error': 'Invalid action.'}, status_code=400)

async def register_key(user_id):
    check_id = await DatabaseManager.id_check(user_id)

    if not check_id:
        data = await DatabaseManager.create_account(user_id)
        return Response(json.dumps({'success': True, 'key': data}, indent=4),
                        media_type='application/json', status_code=200)
    else:
        raise HTTPException(detail={'success': False, 'error': 'The key for the specified ID already exists.'}, status_code=400)

async def check_key(user_id, key):
    if not user_id:
        check_key = await DatabaseManager.key_check(key)
    else:
        check_key = None
        check_id = await DatabaseManager.id_check(user_id)

    if (not check_key and key) and (not check_id and user_id):
        return Response(json.dumps({'present': False}, indent=4), media_type='application/json', status_code=200)
    else:
        return Response(json.dumps({'present': True, 'key': check_key}, indent=4), media_type='application/json', status_code=200)

async def delete_key(user_id, key):
    if not user_id:
        check_key = await DatabaseManager.key_check(key)
    else:
        check_key = None
        check_id = await DatabaseManager.id_check(user_id)

    if (not check_key and key) or (not check_id and user_id):
        raise HTTPException(detail={'success': False, 'error': 'The key for the specified ID does not exist.'}, status_code=400)
    else:
        await DatabaseManager.delete_account(check_key if check_key else check_id)
        return Response(json.dumps({'success': True, 'info': 'Successfully deleted key.'}, indent=4),
                        media_type='application/json', status_code=200)

async def update_key(user_id, key, banned, premium, subscriber):
    if not user_id:
        check_key = await DatabaseManager.key_check(key)
    else:
        check_key = None
        check_id = await DatabaseManager.id_check(user_id)

    if (not check_key and key) or (not check_id and user_id):
        raise HTTPException(detail={'success': False, 'error': 'The key for the specified ID does not exist.'}, status_code=400)
    else:
        if banned:
            await DatabaseManager.ban_update(check_key if check_key else check_id)
        elif premium:
            print(premium)
            await DatabaseManager.premium_update(check_key if check_key else check_id, premium)
        elif subscriber:
            print(subscriber)
            await DatabaseManager.subscriber_update(check_key if check_key else check_id, subscriber)

        return Response(json.dumps({'success': True, 'info': 'Successfully updated key.'}, indent=4), media_type='application/json', status_code=200)