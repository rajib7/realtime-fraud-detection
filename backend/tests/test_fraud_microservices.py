"""End-to-end backend tests for real-time fraud detection microservices (Iteration 2 - with Auth/RBAC).

All protected endpoints now require Bearer JWT. Admin token is used for most
tests; analyst/viewer tokens are used for role-guard tests.
"""
from __future__ import annotations

import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@fraudops.io", "password": "admin123"}
ANALYST = {"email": "analyst@fraudops.io", "password": "analyst123"}
VIEWER = {"email": "viewer@fraudops.io", "password": "viewer123"}


def _login(creds):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{API}/auth/login", json=creds)
    assert r.status_code == 200, f"login failed for {creds['email']}: {r.status_code} {r.text}"
    body = r.json()
    token = body["access_token"]
    # Clear cookie to isolate Bearer auth path
    s.cookies.clear()
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s, body


@pytest.fixture(scope="session")
def anon():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def admin():
    s, body = _login(ADMIN)
    return s, body


@pytest.fixture(scope="session")
def analyst():
    s, body = _login(ANALYST)
    return s, body


@pytest.fixture(scope="session")
def viewer():
    s, body = _login(VIEWER)
    return s, body


# --- Public / unauth ---------------------------------------------------------
class TestPublicEndpoints:
    def test_root_public(self, anon):
        r = anon.get(f"{API}/")
        assert r.status_code == 200
        d = r.json()
        assert d["version"] == "1.1.0"
        for svc in ["auth", "transaction-service", "fraud-scoring-service", "alert-service", "simulator", "metrics"]:
            assert svc in d["services"]
        for topic in ["transactions.raw", "fraud.scores", "alerts.raised"]:
            assert topic in d["topics"]

    def test_health_public(self, anon):
        r = anon.get(f"{API}/health")
        assert r.status_code == 200
        assert r.json()["status"] == "UP"

    def test_metrics_requires_auth(self, anon):
        r = anon.get(f"{API}/metrics")
        assert r.status_code == 401

    def test_tx_recent_requires_auth(self, anon):
        r = anon.get(f"{API}/tx/transactions/recent")
        assert r.status_code == 401

    def test_simulator_start_requires_auth(self, anon):
        r = anon.post(f"{API}/simulator/start", json={})
        assert r.status_code == 401


# --- Auth flows --------------------------------------------------------------
class TestAuthFlow:
    def test_login_admin_ok(self):
        r = requests.post(f"{API}/auth/login", json=ADMIN)
        assert r.status_code == 200
        d = r.json()
        assert d["token_type"] == "Bearer"
        assert d["user"]["role"] == "admin"
        assert d["user"]["email"] == "admin@fraudops.io"
        assert isinstance(d["access_token"], str) and len(d["access_token"]) > 10

    def test_login_wrong_password_401(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN["email"], "password": "nope"})
        assert r.status_code == 401

    def test_login_analyst_role(self):
        r = requests.post(f"{API}/auth/login", json=ANALYST)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "analyst"

    def test_login_viewer_role(self):
        r = requests.post(f"{API}/auth/login", json=VIEWER)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "viewer"

    def test_me_with_admin_bearer(self, admin):
        s, _ = admin
        r = s.get(f"{API}/auth/me")
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "admin"

    def test_register_new_viewer_then_conflict(self):
        email = f"TEST_reg_{uuid.uuid4().hex[:8]}@example.com"
        payload = {"email": email, "password": "secret123", "name": "Reg Test"}
        r1 = requests.post(f"{API}/auth/register", json=payload)
        assert r1.status_code == 200, r1.text
        d = r1.json()
        assert d["user"]["role"] == "viewer"
        assert isinstance(d["access_token"], str) and len(d["access_token"]) > 10
        # token works
        me = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {d['access_token']}"})
        assert me.status_code == 200
        # duplicate -> 409
        r2 = requests.post(f"{API}/auth/register", json=payload)
        assert r2.status_code == 409


# --- RBAC guards -------------------------------------------------------------
class TestRBAC:
    def test_admin_can_start_stop_inject(self, admin):
        s, _ = admin
        r = s.post(f"{API}/simulator/start", json={"tps": 5, "fraud_bias": 0.25})
        assert r.status_code == 200
        assert r.json()["running"] is True

        r_inj = s.post(f"{API}/simulator/inject-fraud?count=2")
        assert r_inj.status_code == 200
        injected = r_inj.json()["injected"]
        assert len(injected) == 2

        r_stop = s.post(f"{API}/simulator/stop")
        assert r_stop.status_code == 200
        assert r_stop.json()["running"] is False

    def test_viewer_cannot_start_but_can_read_metrics(self, viewer):
        s, _ = viewer
        r = s.post(f"{API}/simulator/start", json={})
        assert r.status_code == 403
        r_m = s.get(f"{API}/metrics")
        assert r_m.status_code == 200

    def test_viewer_cannot_ack(self, viewer, admin):
        # produce an alert (using admin)
        sa, _ = admin
        sa.post(f"{API}/simulator/inject-fraud?count=1")
        alert_id = None
        for _ in range(20):
            items = sa.get(f"{API}/alerts/recent?limit=50").json()["items"]
            if items:
                alert_id = items[0]["alert_id"]
                break
            time.sleep(0.3)
        assert alert_id, "no alerts available"

        sv, _ = viewer
        r = sv.post(f"{API}/alerts/{alert_id}/ack")
        assert r.status_code == 403

    def test_analyst_cannot_start_but_can_ack(self, analyst, admin):
        # ensure at least one alert
        sa, _ = admin
        sa.post(f"{API}/simulator/inject-fraud?count=1")
        alert_id = None
        for _ in range(20):
            items = sa.get(f"{API}/alerts/recent?limit=50").json()["items"]
            # find an unack'd one
            for it in items:
                if not it.get("acknowledged"):
                    alert_id = it["alert_id"]
                    break
            if alert_id:
                break
            time.sleep(0.3)
        assert alert_id, "no unacked alert available"

        san, _ = analyst
        r_start = san.post(f"{API}/simulator/start", json={})
        assert r_start.status_code == 403

        r_ack = san.post(f"{API}/alerts/{alert_id}/ack")
        assert r_ack.status_code == 200
        assert r_ack.json()["ok"] is True

    def test_ack_unknown_alert_404(self, admin):
        s, _ = admin
        r = s.post(f"{API}/alerts/does_not_exist/ack")
        assert r.status_code == 404
        detail = r.json().get("detail", "").lower()
        assert "not found" in detail


# --- Alerts rehydration ------------------------------------------------------
class TestRehydration:
    def test_alerts_recent_has_history(self, admin):
        s, _ = admin
        r = s.get(f"{API}/alerts/recent?limit=200")
        assert r.status_code == 200
        d = r.json()
        # rehydration + prior tests should ensure > 0
        assert d["total"] > 0, "no historical alerts (rehydration or seeding failed)"
        assert isinstance(d["items"], list)


# --- Transaction / scoring / event flow (with auth) --------------------------
class TestTransactionAndScoring:
    def test_create_tx_and_recent(self, admin):
        s, _ = admin
        payload = {
            "user_id": "TEST_u1",
            "amount": 42.5,
            "currency": "USD",
            "merchant": "TEST_grocer",
            "merchant_category": "grocery",
            "country": "US",
        }
        r = s.post(f"{API}/tx/transactions", json=payload)
        assert r.status_code == 200, r.text
        tx_id = r.json()["tx_id"]
        assert tx_id.startswith("tx_")

        found = False
        for _ in range(10):
            r2 = s.get(f"{API}/tx/transactions/recent?limit=100")
            assert r2.status_code == 200
            if any(it["tx_id"] == tx_id for it in r2.json()["items"]):
                found = True
                break
            time.sleep(0.2)
        assert found

    def test_high_risk_scoring(self, admin):
        s, _ = admin
        r = s.post(f"{API}/fraud/score", json={
            "amount": 5000, "merchant_category": "crypto_exchange", "hour": 3,
            "is_foreign": True, "cross_border": True,
            "velocity_1h": 8, "distinct_countries_24h": 4,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["risk_level"] == "fraud"
        assert d["decision"] == "block"

    def test_low_risk_scoring(self, admin):
        s, _ = admin
        r = s.post(f"{API}/fraud/score", json={
            "amount": 25, "merchant_category": "grocery", "hour": 13,
            "is_foreign": False, "cross_border": False,
            "velocity_1h": 1, "distinct_countries_24h": 1,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["risk_level"] == "safe"
        assert d["decision"] == "approve"

    def test_metrics_shape(self, admin):
        s, _ = admin
        r = s.get(f"{API}/metrics")
        assert r.status_code == 200
        m = r.json()
        for k in ["tps", "avg_latency_ms", "p95_latency_ms", "fraud_rate_pct",
                  "total_processed", "total_alerts", "tps_sparkline",
                  "latency_sparkline", "topics"]:
            assert k in m
        assert len(m["tps_sparkline"]) == 20
        assert len(m["latency_sparkline"]) == 20


# --- Cleanup -----------------------------------------------------------------
def test_zzz_stop_simulator(admin):
    s, _ = admin
    s.post(f"{API}/simulator/stop")
    r = s.get(f"{API}/simulator/status")
    assert r.status_code == 200
    assert r.json()["running"] is False
