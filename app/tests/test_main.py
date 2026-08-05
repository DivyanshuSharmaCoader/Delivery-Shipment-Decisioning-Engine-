from httpx import AsyncClient

from app.utils import print_label
from app.tests import example


# async def test_app(client: AsyncClient):
#     await client.get("/")

#     response = await client.get(
#         "/shipment/?id=55e7e265-9a01-4402-94be-ad831d461e1f"
#     )

#     print_label(response.json())

#     assert response.status_code == 200
#     assert response.json() == {
#         "detail": "55e7e265-9a01-4402-94be-ad831d461e1f"
#     }


async def test_seller_login(client: AsyncClient):
    response = await client.post(
        "/seller/token",
        data = {
            "grant_type": "password",
            "username": example.SELLER["email"],
            "password": example.SELLER["password"],
        }
    )
    print_label(response.json())