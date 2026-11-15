import os
import tempfile
from pathlib import Path

# Must be set before importing app modules/config.
_tmp = tempfile.TemporaryDirectory()
os.environ['DATABASE_URL'] = f'sqlite:///{Path(_tmp.name) / "test.db"}'
os.environ['SEED_DEMO'] = 'false'
os.environ['ENABLE_SCHEDULER'] = 'false'
os.environ['SECRET_KEY'] = 'test-secret-unit-tests-only-longer-than-32-characters'

from fastapi.testclient import TestClient
from app.main import app
from app.services import run_monitor_check
import app.services as services
import asyncio


def auth(client, email='alice@example.org'):
    response = client.post('/api/auth/register', json={'name': 'Alice', 'email': email, 'password': 'StrongPass123!'})
    assert response.status_code == 201, response.text
    return {'Authorization': 'Bearer ' + response.json()['access_token']}


def test_auth_and_isolation():
    with TestClient(app) as client:
        assert client.get('/health').json()['status'] == 'ok'
        assert client.get('/api/monitors').status_code == 401
        headers = auth(client)
        bad = client.post('/api/monitors', headers=headers, json={'name': 'Bad', 'url': 'http://127.0.0.1/admin'})
        assert bad.status_code == 422
        result = client.post('/api/monitors', headers=headers, json={'name': 'Public endpoint', 'url': 'https://example.com'})
        assert result.status_code == 201, result.text
        monitor_id = result.json()['id']
        assert len(client.get('/api/monitors', headers=headers).json()) == 1
        other = auth(client, 'bob@example.org')
        assert client.get(f'/api/monitors/{monitor_id}', headers=other).status_code == 404
        assert len(client.get('/api/monitors', headers=other).json()) == 0
        assert client.post('/api/auth/login', json={'email': 'alice@example.org', 'password': 'incorrect'}).status_code == 401


def test_incident_lifecycle_and_public_status():
    with TestClient(app) as client:
        headers = auth(client, 'ops@example.org')
        result = client.post('/api/monitors', headers=headers, json={'name': 'Critical API', 'url': 'https://example.org'})
        monitor_id = result.json()['id']
        original = services.probe
        async def down(*args):
            return False, 503, 43.2, 'Expected HTTP 200; received 503'
        async def up(*args):
            return True, 200, 35.1, None
        try:
            services.probe = down
            asyncio.run(run_monitor_check(monitor_id))
            asyncio.run(run_monitor_check(monitor_id))
            incidents = client.get('/api/incidents', headers=headers).json()
            assert len(incidents) == 1 and incidents[0]['status'] == 'OPEN'
            ack = client.post(f'/api/incidents/{incidents[0]["id"]}/acknowledge', headers=headers)
            assert ack.status_code == 200 and ack.json()['acknowledged_at']
            services.probe = up
            asyncio.run(run_monitor_check(monitor_id))
            assert client.get('/api/incidents', headers=headers).json()[0]['status'] == 'RESOLVED'
            assert client.get('/api/dashboard', headers=headers).json()['uptime_pct'] == 33.33
            assert len(client.get('/api/notifications', headers=headers).json()) == 2
            slug = client.get('/api/auth/me', headers=headers).json()['public_slug']
            public = client.get(f'/api/public/status/{slug}').json()
            assert public['overall_state'] == 'OPERATIONAL'
            assert public['monitors'][0]['name'] == 'Critical API'
        finally:
            services.probe = original


def test_edit_pause_and_delete():
    with TestClient(app) as client:
        headers = auth(client, 'edit@example.org')
        monitor_id = client.post('/api/monitors', headers=headers, json={'name': 'Test API', 'url': 'https://example.com'}).json()['id']
        assert client.patch(f'/api/monitors/{monitor_id}', headers=headers, json={'is_paused': True}).json()['is_paused']
        assert client.post(f'/api/monitors/{monitor_id}/check', headers=headers).status_code == 409
        assert client.delete(f'/api/monitors/{monitor_id}', headers=headers).status_code == 204
        assert client.get(f'/api/monitors/{monitor_id}', headers=headers).status_code == 404


def test_security_filters_and_sla_csv():
    with TestClient(app) as client:
        headers = auth(client, 'security@example.org')
        for blocked in ('http://localhost:8000/health', 'http://192.168.1.5', 'http://169.254.169.254/latest/meta-data', 'file:///etc/passwd', 'http://[::1]/'):
            res = client.post('/api/monitors', headers=headers, json={'name': 'Blocked', 'url': blocked})
            assert res.status_code == 422, (blocked, res.text)
        first = client.post('/api/monitors', headers=headers, json={'name': 'Public API', 'url': 'https://example.com', 'sla_target': 99.95})
        second = client.post('/api/monitors', headers=headers, json={'name': 'Private API', 'url': 'https://example.org', 'is_public': False})
        assert first.status_code == 201 and second.status_code == 201
        slug = client.get('/api/auth/me', headers=headers).json()['public_slug']
        public = client.get(f'/api/public/status/{slug}').json()
        assert len(public['monitors']) == 1
        assert public['monitors'][0]['name'] == 'Public API'
        csv = client.get('/api/reports/sla.csv?days=30', headers=headers)
        assert csv.status_code == 200
        assert 'Public API' in csv.text and 'Private API' in csv.text
        assert '99.95' in csv.text
        assert client.get('/api/reports/sla.csv').status_code == 401
        assert client.get('/api/dashboard?range=invalid', headers=headers).status_code == 422
