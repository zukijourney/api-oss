from fastapi import Response, HTTPException, Request
from fastapi.exceptions import RequestValidationError
import ujson

async def exception_handler(_, exc: Exception):
    return Response(content=ujson.dumps({"error": {"message": str(exc).replace("Value error, ", ""), "type": "error", "param": None, "code": 500}}, escape_forward_slashes=False, indent=4), media_type="application/json", status_code=500)

async def http_exception_handler(_, exc: HTTPException):
    return Response(ujson.dumps(exc.detail, indent=4, escape_forward_slashes=False), media_type="application/json", status_code=exc.status_code)

async def method_not_allowed(request: Request, _):
    return Response(content=ujson.dumps({"error": {"message": f"Method Not Allowed ({request.method} {request.url.path})", "type": "error", "param": None, "code": 405}}, indent=4,escape_forward_slashes=False), media_type="application/json", status_code=405)

async def validation_error_handler(_, exc: RequestValidationError):
    message = list(exc.errors())[0]['msg']
    return Response(content=ujson.dumps({"error": {"message": message.replace("Value error, ", ""), "type": "error", "param": None, "code": 400}}, indent=4, escape_forward_slashes=False), media_type="application/json", status_code=400)

async def value_error_handler(_, exc: ValueError):
    return Response(content=ujson.dumps({"error": {"message": str(exc).replace("Value error, ", ""), "type": "error", "param": None, "code": 400}}, indent=4, escape_forward_slashes=False), media_type="application/json", status_code=400)

async def not_found(request: Request, _):
    message = f"Invalid URL ({request.method} {request.url.path})" if not request.url.path.startswith("/cdn/") else "The requested image was not found in our CDN."
    return Response(content=ujson.dumps({"error": {"message": message, "type": "error", "param": None, "code": 404}}, indent=4, escape_forward_slashes=False), media_type="application/json", status_code=404)