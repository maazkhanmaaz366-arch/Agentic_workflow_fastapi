async def test_read_root(client):
    response = await client.get('/')
    assert response.status_code == 200

    data = response.json()
    assert "version" in data
    assert "project" in data
    assert data["message"] == "Welcome to the user Management System"

async def test_login_invalid_password(client):
    payload = {
        "email": "notreal@example.com",
        "password": "wrongpassword123"
    }
    response = await client.post("/users/login", json=payload)
    
    # Must reject with 401 Unauthorized
    assert response.status_code == 401
    assert response.json()["detail"] == "wrong password or email"

async def test_get_me_unautherized(client):
    response = await client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

async def test_category(client):
    response = await client.get("/products/status")
    assert response.status_code == 200
    assert isinstance(response.json(),list)
    
async def test_middleware_headers(client):
    response = await client.get("/")
    assert response.status_code == 200
    
    # Verify our custom middleware headers exist
    assert "x-process-time" in response.headers
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) == 8
