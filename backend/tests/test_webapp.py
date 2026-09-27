"""Full local route flow; all provider traffic remains mocked or disabled."""
from fastapi.testclient import TestClient
import pytest

from vc_research.webapp import app

HEADERS = {"X-VC-Client": "local-browser"}

@pytest.fixture
def client():
    app.state.report = None
    with TestClient(app) as client:
        yield client


def analyze(client, company="Lumen", **kwargs):
    return client.post('/api/analyze', headers=HEADERS, json={"company": company, **kwargs})


def test_browser_assets_and_offline_report_export(client):
    assert client.get('/').status_code == 200
    assert client.get('/static/app.js').headers['content-type'] in {'application/javascript', 'text/javascript; charset=utf-8', 'text/javascript'}
    res = analyze(client)
    assert res.status_code == 200, res.text
    report = res.json()
    assert report['mode'] == 'demo'
    assert report['usage']['searches'] == report['usage']['model_calls'] == 0
    assert len(report['analysis']['sections']) == 9
    assert len(report['financial_candidates']) == 5
    assert report['financials']['status'] == 'review_required'
    exported = client.get('/api/memo/' + report['run_id'])
    assert exported.status_code == 200
    assert 'SYNTHETIC FIXTURE' in exported.text
    assert 'attachment' in exported.headers['content-disposition']
    assert "script-src 'self'" in res.headers['content-security-policy']


def test_financial_review_updates_same_memo_without_api_calls(client):
    report = analyze(client).json()
    financials = client.post('/api/financials', headers=HEADERS, json={
        "run_id": report['run_id'], "confirmed": True,
        "selections": {"prior_revenue": "C4", "current_revenue": "C5", "gross_profit": "C6", "cash": "C7", "monthly_net_burn": "C8"},
        "bear_multiple": "2", "base_multiple": "3", "bull_multiple": "4"})
    assert financials.status_code == 200, financials.text
    updated = financials.json()
    assert [c['record']['result'] for c in updated['financials']['calculations']] == ['50.0', '80.0', '12.0', '6000000', '9000000', '12000000']
    assert 'ASSUMPTION' in client.get('/api/memo/' + report['run_id']).text
    assert updated['usage']['model_calls'] == 0
    bad = client.post('/api/financials', headers=HEADERS, json={"run_id": report['run_id'], "confirmed":True, "selections":{"current_revenue":"invented"}})
    assert bad.status_code == 422
    assert app.state.report['financials']['status'] == 'calculated'


def test_sparse_report_refuses_finance_and_unknown_company_is_not_fixture(client):
    report = analyze(client, 'Lumen Sparse').json()
    assert report['financials']['status'] == 'unavailable'
    assert report['financial_candidates'] == []
    assert analyze(client, 'A real company').status_code == 422
    assert client.get('/api/memo/' + report['run_id']).status_code == 200


def test_live_requires_per_run_confirmation_and_local_enablement(client, monkeypatch):
    monkeypatch.setenv('VC_ENABLE_LIVE', 'false')
    assert analyze(client, 'https://example.com', mode='live').status_code == 403
    res = analyze(client, 'https://example.com', mode='live', confirm_live=True)
    assert res.status_code == 422
    assert 'disabled' in res.json()['detail']


def test_local_boundary_size_and_concurrency(client):
    assert client.post('/api/analyze', json={"company":"Lumen"}).status_code == 403
    assert client.post('/api/analyze', json={"company":"Lumen"}, headers={**HEADERS,"Origin":"https://other.example"}).status_code == 403
    assert client.get('/', headers={"Host":"attacker.example"}).status_code == 400
    assert client.post('/api/analyze', content='x'*4097, headers=HEADERS).status_code == 413
    app.state.lock.acquire()
    try:
        assert analyze(client).status_code == 409
    finally:
        app.state.lock.release()
    assert analyze(client).status_code == 200


def test_new_report_invalidates_old_financial_review(client):
    old = analyze(client).json()
    analyze(client, 'Lumen Sparse')
    assert client.post('/api/financials', headers=HEADERS, json={"run_id":old['run_id'],"confirmed":True}).status_code == 404
    assert client.get('/api/memo/' + old['run_id']).status_code == 404
