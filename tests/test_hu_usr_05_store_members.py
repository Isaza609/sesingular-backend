from app.models import Store, StoreMember, User
from app.models.user import UserRole


def test_hu_usr_05_admin_creates_store_member_with_temporary_credentials(api_context):
    client, db, auth, token_for = api_context
    admin = User(id="admin-1", email="admin@example.com", name="Admin", role=UserRole.admin)
    store = Store(id="store-1", slug="nova", name="Nova Ropa")
    db.add_all([admin, store])
    db.commit()

    response = client.post(
        f"/api/v1/admin/stores/{store.id}/members",
        json={"email": "equipo@example.com", "name": "Laura Gomez", "member_role": "staff"},
        headers=token_for(admin.id),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["platform_role"] == "seller"
    assert data["member_role"] == "staff"
    assert data["temporary_password"]
    user = db.get(User, data["user_id"])
    assert user.must_change_password is True
    assert auth.created_users[0]["metadata"]["store_id"] == store.id


def test_hu_usr_05_store_users_share_same_seller_scope(api_context):
    client, db, _auth, token_for = api_context
    store = Store(id="store-1", slug="nova", name="Nova Ropa")
    seller = User(id="seller-1", email="seller@example.com", name="Seller", role=UserRole.seller)
    staff = User(id="staff-1", email="staff@example.com", name="Staff", role=UserRole.seller)
    db.add_all(
        [
            store,
            seller,
            staff,
            StoreMember(store_id=store.id, user_id=seller.id, role="owner"),
            StoreMember(store_id=store.id, user_id=staff.id, role="staff"),
        ]
    )
    db.commit()

    response = client.get("/api/v1/seller/store/members", headers=token_for(staff.id))

    assert response.status_code == 200
    assert {row["user_id"] for row in response.json()} == {"seller-1", "staff-1"}


def test_hu_usr_05_deactivating_team_user_blocks_access_without_deleting_history(api_context):
    client, db, _auth, token_for = api_context
    admin = User(id="admin-1", email="admin@example.com", name="Admin", role=UserRole.admin)
    store = Store(id="store-1", slug="nova", name="Nova Ropa")
    staff = User(id="staff-1", email="staff@example.com", name="Staff", role=UserRole.seller)
    member = StoreMember(store_id=store.id, user_id=staff.id, role="staff")
    db.add_all([admin, store, staff, member])
    db.commit()

    response = client.patch(
        f"/api/v1/admin/stores/{store.id}/members/{staff.id}",
        json={"active": False},
        headers=token_for(admin.id),
    )

    assert response.status_code == 200
    assert response.json()["active"] is False
    assert db.get(StoreMember, member.id) is not None
    assert client.get("/api/v1/seller/dashboard", headers=token_for(staff.id)).status_code == 403


def test_hu_usr_05_seller_can_list_but_not_create_store_members(api_context):
    client, db, _auth, token_for = api_context
    store = Store(id="store-1", slug="nova", name="Nova Ropa")
    seller = User(id="seller-1", email="seller@example.com", name="Seller", role=UserRole.seller)
    db.add_all([store, seller, StoreMember(store_id=store.id, user_id=seller.id, role="owner")])
    db.commit()

    listed = client.get("/api/v1/seller/store/members", headers=token_for(seller.id))
    created = client.post(
        "/api/v1/seller/store/members",
        json={"email": "nuevo@example.com", "name": "Nuevo"},
        headers=token_for(seller.id),
    )

    assert listed.status_code == 200
    assert created.status_code == 405
