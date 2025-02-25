from fastapi import Depends
from .dependencies import authentication, validate_request_body, validate_user_access

DEPENDENCIES = [
    Depends(authentication),
    Depends(validate_user_access),
    Depends(validate_request_body)
]