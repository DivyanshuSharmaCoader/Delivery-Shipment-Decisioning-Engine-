from httpx import AsyncClient
from app.utils import generate_url_safe_token, decode_url_safe_token
from app.services.user import password_context

async def test_seller_signup_and_login_flow(client: AsyncClient):
    seller_data = {
        "name": "New Seller Co",
        "email": "newseller@example.com",
        "password": "securepassword123",
        "address": "456 Market St",
        "zip_code": 11001,
    }

    # 1. Signup
    response = await client.post("/seller/signup", json=seller_data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["name"] == seller_data["name"]
    assert res_data["email"] == seller_data["email"]

    # 2. Login before verification should fail (403)
    login_res = await client.post(
        "/seller/token",
        data={"username": seller_data["email"], "password": seller_data["password"]},
    )
    assert login_res.status_code == 403

    # 3. Generate token & verify email
    # Retrieve user from DB or generate token directly for test
    from app.database.session import get_session
    from app.database.models import Seller
    from sqlalchemy import select

    # Let's get seller from DB
    from app.main import app
    session_factory = app.dependency_overrides[get_session]
    async for session in session_factory():
        seller = (await session.scalars(select(Seller).where(Seller.email == seller_data["email"]))).first()
        assert seller is not None
        verify_token = generate_url_safe_token({"email": seller.email, "id": str(seller.id)})
        break

    verify_res = await client.get(f"/seller/verify?token={verify_token}")
    assert verify_res.status_code == 200
    assert verify_res.json()["detail"] == "Account Verified"

    # 4. Login after verification should succeed
    login_res = await client.post(
        "/seller/token",
        data={"username": seller_data["email"], "password": seller_data["password"]},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token is not None

    # 5. Fetch profile
    me_res = await client.get("/seller/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == seller_data["email"]


async def test_delivery_partner_signup_and_flow(client: AsyncClient):
    partner_data = {
        "name": "Express Logistics",
        "email": "expresslogistics@example.com",
        "password": "partnerpassword123",
        "max_handling_capacity": 5,
        "serviceable_zip_codes": [11001, 11002, 11003],
    }

    # 1. Signup
    response = await client.post("/partner/signup", json=partner_data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["name"] == partner_data["name"]
    assert res_data["email"] == partner_data["email"]
    assert res_data["serviceable_zip_codes"] == partner_data["serviceable_zip_codes"]

    # 2. Login before verification should fail (403)
    login_res = await client.post(
        "/partner/token",
        data={"username": partner_data["email"], "password": partner_data["password"]},
    )
    assert login_res.status_code == 403

    # 3. Verify partner email
    from app.database.session import get_session
    from app.database.models import DeliveryPartner
    from sqlalchemy import select
    from app.main import app

    session_factory = app.dependency_overrides[get_session]
    async for session in session_factory():
        partner = (await session.scalars(select(DeliveryPartner).where(DeliveryPartner.email == partner_data["email"]))).first()
        assert partner is not None
        verify_token = generate_url_safe_token({"email": partner.email, "id": str(partner.id)})
        break

    verify_res = await client.get(f"/partner/verify?token={verify_token}")
    assert verify_res.status_code == 200

    # 4. Login after verification
    login_res = await client.post(
        "/partner/token",
        data={"username": partner_data["email"], "password": partner_data["password"]},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # 5. Fetch partner profile
    me_res = await client.get("/partner/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == partner_data["email"]
    assert me_res.json()["serviceable_zip_codes"] == partner_data["serviceable_zip_codes"]

    # 6. Fetch partner shipments
    shipments_res = await client.get("/partner/shipments", headers={"Authorization": f"Bearer {token}"})
    assert shipments_res.status_code == 200
    assert isinstance(shipments_res.json(), list)


async def test_duplicate_email_signup(client: AsyncClient):
    seller_data = {
        "name": "Duplicate Seller",
        "email": "newseller@example.com", # already registered in previous test
        "password": "password123",
        "address": "789 Pine St",
        "zip_code": 11001,
    }

    response = await client.post("/seller/signup", json=seller_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "User with this email already exists"
