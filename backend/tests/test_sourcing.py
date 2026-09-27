from copy import deepcopy
from datetime import date
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from vc_research.sourcing.core import (Mandate, LiveDiscovery, DiscoveryExtraction, build_card, classify,
    cutoff, company_key, deduplicate, discover, domain)
from vc_research.sourcing.offline import OfflineDiscovery
from vc_research.demo.live import RunError
from vc_research.webapp import app

TODAY=date(2026,9,27)
HEADERS={'X-VC-Client':'local-browser'}


def cards():
    report=discover(Mandate(),OfflineDiscovery(),'demo',TODAY)
    return report['candidates']


def provider():
    return LiveDiscovery(env={'VC_ENABLE_LIVE':'true','OPENAI_API_KEY':'fake','TAVILY_API_KEY':'fake'})


@pytest.mark.parametrize('data',[{'stages':['Series Z']},{'freshness':'all'},{'min_total_funding':'-1'},
    {'min_total_funding':'10','max_total_funding':'5'},{'founded_after':2025,'founded_before':2020},
    {'max_latest_round':'NaN'},{'sectors':['x']*21}])
def test_mandate_validation(data):
    with pytest.raises(ValidationError): Mandate(**data)


@pytest.mark.parametrize('mandate,expected',[
    ({'stages':['Seed']},'MEETS MANDATE'),({'stages':['Series A']},'OUTSIDE MANDATE'),
    ({'geographies':['Europe']},'MEETS MANDATE'),({'geographies':['United States']},'OUTSIDE MANDATE'),
    ({'geographies':['Nordics']},'OUTSIDE MANDATE'),({'sectors':['carbon removal']},'POTENTIAL MATCH — INFORMATION MISSING'),
    ({'business_models':['Hardware']},'POTENTIAL MATCH — INFORMATION MISSING'),
    ({'max_total_funding':'2000000'},'OUTSIDE MANDATE'),({'min_total_funding':'3000000','max_total_funding':'3000000'},'MEETS MANDATE'),
    ({'min_latest_round':'3000000'},'OUTSIDE MANDATE'),({'max_latest_round':'2000000'},'MEETS MANDATE'),
    ({'max_total_funding':'4000000','funding_currency':'EUR'},'POTENTIAL MATCH — INFORMATION MISSING'),
    ({'founded_after':2021},'OUTSIDE MANDATE'),({'founded_before':2022},'MEETS MANDATE'),
    ({'excluded_keywords':['distributors']},'OUTSIDE MANDATE'),({'excluded_sectors':['SaaS']},'OUTSIDE MANDATE'),
    ({'excluded_geographies':['Europe']},'OUTSIDE MANDATE'),({'excluded_companies':['lumen.example']},'OUTSIDE MANDATE'),
    ({'excluded_companies':['Lumen Fixture Software Ltd']},'OUTSIDE MANDATE'),
    ({'signal_types':['Product launch']},'OUTSIDE MANDATE'),({'keywords':['regional distributors']},'MEETS MANDATE')])
def test_deterministic_filters(mandate,expected):
    assert classify(cards()[0],Mandate(**mandate),TODAY)['classification']==expected


def test_unknowns_retained_or_excluded_without_inventing_values():
    sparse=cards()[1]
    retained=classify(sparse,Mandate(stages=['Seed'],geographies=['France'],min_total_funding='1',business_models=['B2B']),TODAY)
    assert retained['classification']=='POTENTIAL MATCH — INFORMATION MISSING'
    assert retained['stage'] is retained['geography'] is retained['total_funding'] is None
    excluded=classify(sparse,Mandate(keep_unknown_funding=False),TODAY)
    assert excluded['classification']=='OUTSIDE MANDATE'


def test_signal_freshness_boundaries_and_calendar_year():
    card=cards()[0]
    for days,expected in [('2026-09-20','MEETS MANDATE'),('2026-09-19','OUTSIDE MANDATE'),('2026-09-28','OUTSIDE MANDATE')]:
        assert classify({**card,'signal_date':days},Mandate(freshness='7d'),TODAY)['classification']==expected
    assert cutoff(Mandate(freshness='12m'),date(2024,2,29))==date(2023,2,28)


def test_normalization_deduplication_and_conflicts():
    assert company_key(' Example, Inc. ')==company_key('example')
    assert domain('https://www.LUMEN.example/path?x=1')=='lumen.example'
    a=cards()[0]
    b=deepcopy(a); b['website']='https://www.lumen.example/other'; b['stage']='Series A'
    merged,count=deduplicate([a,b])
    assert count==1 and merged[0]['stage'] is None and 'stage' in merged[0]['conflicts']
    c=deepcopy(a); c['website']='https://different.example'
    assert len(deduplicate([a,c])[0])==2  # Namesakes are not silently merged.


def test_evidence_integrity_and_grounded_why():
    sources,raw=OfflineDiscovery().discover(Mandate(),TODAY)
    source_map={s['id']:s for s in sources}
    candidate=raw.candidates[0].model_copy(deep=True)
    candidate.signal.quote='A fabricated funding announcement'
    assert build_card(candidate,source_map)[0] is None
    candidate=raw.candidates[0].model_copy(deep=True)
    candidate.signal.date_text='2026-09-27'
    assert build_card(candidate,source_map)[0] is None
    for card in cards():
        assert card['signal'] in card['why_surfaced']
        assert '%' not in card['classification']
        for evidence in card['evidence']:
            assert evidence['quote'] in source_map[evidence['source_id']]['text']
            assert evidence['source_url'].startswith('https://')


def test_unbacked_fields_become_unknown():
    sources,raw=OfflineDiscovery().discover(Mandate(),TODAY)
    candidate=raw.candidates[0].model_copy(deep=True)
    candidate.stage.value='Series A'
    candidate.website='https://invented.example/'
    candidate.total_funding.amount='999'
    card,_=build_card(candidate,{s['id']:s for s in sources})
    assert card['stage'] is card['website'] is card['total_funding'] is None


def test_new_live_discovery_always_searches_and_batches_once(monkeypatch):
    searches,models=[],[]
    for _ in range(2):
        p=provider()
        def post(url,payload,key):
            searches.append(payload)
            return {'results':[{'url':'https://example.com/','content':'No verified dated company signals','title':'Source'}]}
        def complete(schema,prompt,data):
            p.reserve('model',.01)
            models.append(data)
            return DiscoveryExtraction(candidates=[])
        monkeypatch.setattr(p,'post',post)
        monkeypatch.setattr(p,'complete',complete)
        result=discover(Mandate(),p,'live',TODAY)
        assert result['candidates']==[] and result['usage']['searches']==3 and result['usage']['model_calls']==1
        with pytest.raises(RunError): p.reserve('model',.01)
        with pytest.raises(RunError): p.reserve('search',.01)
    assert len(searches)==6 and len(models)==2
    assert all(q['max_results']==10 and q['start_date']=='2026-08-28' and not q['auto_parameters'] for q in searches)
    with pytest.raises(RunError): provider().reserve('search',.101)


def test_sourcing_route_isolated_from_analysis_and_mode_gates(monkeypatch):
    import vc_research.webapp as webapp
    app.state.report=None
    monkeypatch.setattr(webapp,'run_analysis',lambda *args:pytest.fail('Sourcing must not analyze shortlist companies'))
    monkeypatch.setenv('VC_ENABLE_LIVE','false')
    with TestClient(app) as client:
        body={'mandate':{},'mode':'demo'}
        r=client.post('/api/discover',headers=HEADERS,json=body)
        assert r.status_code==200
        result=r.json()
        assert len(result['candidates'])==2 and result['usage']['model_calls']==0
        assert result['duplicates_removed']==1 and app.state.report is None
        assert all(c['handoff']['mode']=='demo' for c in result['candidates'])
        assert client.post('/api/discover',headers=HEADERS,json={**body,'mode':'live'}).status_code==403
        assert client.post('/api/discover',headers=HEADERS,json={**body,'mode':'live','confirm_live':True}).status_code==422
        assert client.post('/api/discover',json=body).status_code==403


def test_offline_handoff_reuses_existing_analysis():
    with TestClient(app) as client:
        sourcing=client.post('/api/discover',headers=HEADERS,json={'mandate':{}}).json()
        for card in sourcing['candidates']:
            result=client.post('/api/analyze',headers=HEADERS,json=card['handoff'])
            assert result.status_code==200,result.text
            assert result.json()['mode']=='demo'
            assert len(result.json()['analysis']['sections'])==9
            assert result.json()['usage']['searches']==0
