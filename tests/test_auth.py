import pytest
from app.models.user import User
from app.models.store import Store
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hashing_and_verification():
    raw_pwd = "SuperSecretPassword123!"
    hashed = hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_token_generation_and_decoding():
    payload = {"sub": "42", "role": "vendor", "store_id": 5}
    token = create_access_token(payload)
    assert isinstance(token, str)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "42"
    assert decoded["role"] == "vendor"
    assert decoded["store_id"] == 5


def test_admin_and_vendor_login_flow(client, db):
    # Setup Store
    store = Store(name="Downtown Flagship", address="100 Main St")
    db.add(store)
    db.commit()
    db.refresh(store)

    # Setup Admin
    admin = User(
        email="admin@nexpire.org",
        hashed_password=hash_password("AdminPassword123!"),
        role="admin",
        full_name="Platform Admin",
        is_active=True,
    )
    # Setup Vendor
    vendor = User(
        email="vendor@store.com",
        hashed_password=hash_password("VendorPassword123!"),
        role="vendor",
        full_name="Store Manager",
        store_id=store.id,
        is_active=True,
    )
    db.add_all([admin, vendor])
    db.commit()

    # 1. Successful Admin Login
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@nexpire.org", "password": "AdminPassword123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "admin"
    assert data["user"]["email"] == "admin@nexpire.org"

    admin_token = data["access_token"]

    # 2. Successful Vendor Login
    res_v = client.post(
        "/api/v1/auth/login",
        json={"email": "vendor@store.com", "password": "VendorPassword123!"},
    )
    assert res_v.status_code == 200
    data_v = res_v.json()
    assert data_v["user"]["role"] == "vendor"
    assert data_v["user"]["store_id"] == store.id

    # 3. Invalid Password
    res_bad = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@nexpire.org", "password": "WrongPassword"},
    )
    assert res_bad.status_code == 401
    assert "Invalid email or password" in res_bad.json()["detail"]

    # 4. Unknown Email
    res_unk = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@nexpire.org", "password": "AnyPassword"},
    )
    assert res_unk.status_code == 401

    # 5. Access /me with Admin Token
    res_me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "admin@nexpire.org"

    # 6. Access /me with missing token
    res_no_auth = client.get("/api/v1/auth/me")
    assert res_no_auth.status_code == 401


def test_customer_otp_flow(client, db):
    phone = "+919876543210"

    # 1. Send OTP
    res_send = client.post(
        "/api/v1/auth/customer/send-otp",
        json={"phone_number": phone},
    )
    assert res_send.status_code == 200
    send_data = res_send.json()
    assert send_data["success"] is True
    assert send_data["phone_number"] == phone

    # 2. Verify with invalid OTP
    res_bad_otp = client.post(
        "/api/v1/auth/customer/verify-otp",
        json={"phone_number": phone, "otp_code": "000000"},
    )
    assert res_bad_otp.status_code == 400
    assert "Invalid or expired" in res_bad_otp.json()["detail"]

    # 3. Verify with developer mock OTP 123456
    res_verify = client.post(
        "/api/v1/auth/customer/verify-otp",
        json={"phone_number": phone, "otp_code": "123456", "full_name": "Test Customer"},
    )
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert "access_token" in verify_data
    assert verify_data["user"]["role"] == "customer"
    assert verify_data["user"]["phone_number"] == phone
    assert verify_data["user"]["full_name"] == "Test Customer"

    cust_token = verify_data["access_token"]

    # 4. Access /me with customer token
    res_me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert res_me.status_code == 200
    assert res_me.json()["phone_number"] == phone
    assert res_me.json()["role"] == "customer"
