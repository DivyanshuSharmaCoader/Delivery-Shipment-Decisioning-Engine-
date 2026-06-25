from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from app.utils import decode_access_token
from fastapi import HTTPException, status, Depends
from typing import Annotated

oauth2_scheme_seller = OAuth2PasswordBearer(tokenUrl="/seller/token")
oauth2_scheme_partner = OAuth2PasswordBearer(tokenUrl="/partner/token")

class AccessTokenBearer(HTTPBearer):
    async def __call__(self, request):
        auth_credentials = await super().__call__(request)
        token = auth_credentials.credentials

        token_data = decode_access_token(token)

        if token_data is None:
            raise HTTPException(
                status_code=401,
                detail="Not Authorized!",
            )

        return token_data
access_token_bearer= AccessTokenBearer()

Annotated[dict, Depends(access_token_bearer)]