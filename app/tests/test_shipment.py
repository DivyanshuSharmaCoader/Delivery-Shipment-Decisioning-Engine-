from httpx import AsyncClient
from app.utils import print_label
from app.tests import example

base_url = "/shipment/"


async def test_submit_shipment_auth(client: AsyncClient):
    response = await client.post(
        base_url,
        json={},
    )

    assert response.status_code == 401


async def test_submit_shipment(client: AsyncClient, seller_token: str):
    response = await client.post(
        base_url,
        json = example.SHIPMENT,
        headers = {"Authorization": f"Bearer {seller_token}"},
    )
    print(response.json())
    assert response.status_code == 201
    shipment_id = response.json()["id"]

    response = await client.get(
        base_url,
        params = {"id": shipment_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pickup_location"] == example.SELLER["zip_code"]
    # Check that the first event location is the seller's zip_code (pickup_location)
    assert len(data["timeline"]) > 0
    assert data["timeline"][0]["location"] == example.SELLER["zip_code"]


async def test_cancel_shipment_destination_update(client: AsyncClient, seller_token: str):
    # 1. Submit a shipment
    response = await client.post(
        base_url,
        json = example.SHIPMENT,
        headers = {"Authorization": f"Bearer {seller_token}"},
    )
    assert response.status_code == 201
    shipment_id = response.json()["id"]

    # 2. Cancel the shipment
    response = await client.get(
        f"{base_url}cancel",
        params = {"id": shipment_id},
        headers = {"Authorization": f"Bearer {seller_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    
    # 3. Verify destination has updated to seller's zip code
    assert data["destination"] == example.SELLER["zip_code"]