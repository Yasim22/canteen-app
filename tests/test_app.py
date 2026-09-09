import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import create_app


@pytest.fixture
def client(monkeypatch):
    sent = []
    # Replace the real SMS function so tests never touch the network
    monkeypatch.setattr("app.send_sms",
                        lambda to, msg: sent.append((to, msg)) or True)
    app = create_app({"TESTING": True,
                      "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.test_client() as c:
        c.sent = sent
        yield c


def test_menu_page_loads(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Jollof" in r.data


def test_place_order_creates_order_and_sends_sms(client):
    r = client.post("/order", data={"customer_name": "Kofi",
                                    "phone": "0244123456", "qty_1": "2"})
    assert r.status_code == 302
    assert len(client.sent) == 1
    assert client.sent[0][0] == "+233244123456"
    assert "GHS 70.00" in client.sent[0][1]


def test_order_without_items_rejected(client):
    client.post("/order", data={"customer_name": "Ama", "phone": "0244123456"})
    assert len(client.sent) == 0


def test_staff_page_requires_login(client):
    r = client.get("/staff")
    assert r.status_code == 302
    assert "/staff/login" in r.headers["Location"]


def test_mark_ready_sends_sms(client):
    client.post("/order", data={"customer_name": "Kofi",
                                "phone": "0244123456", "qty_2": "1"})
    client.post("/staff/login", data={"password": "staff123"})
    client.post("/staff/order/1/ready")
    assert "READY" in client.sent[-1][1]