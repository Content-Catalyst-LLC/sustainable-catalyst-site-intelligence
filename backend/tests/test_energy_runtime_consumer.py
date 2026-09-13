from app.energy_runtime_consumer import framework, consume, TARGET_KEY, CONSUMER_CONTRACT

def packet():
    sections=['identity', 'technologies_and_resources', 'global_context', 'provenance', 'review']
    payload={k: ({"study_id":"study:test","question":"Compare pathways"} if k=="identity" else ([{"source_ref":"source:test"}] if k=="provenance" else {} if k not in ("sustainability_indicators","uncertainty") else [])) for k in sections}
    return {"schema":"sc-energy-runtime-handoff/1.0","version":"1.5.0","packet":{"handoff_id":"es-test","source":{"product":"Library","subsystem":"Energy Systems Intelligence","version":"1.5.0"},"target":{"key":TARGET_KEY,"product":'Site Intelligence',"consumer_contract":CONSUMER_CONTRACT},"contract_refs":["integrated-energy-study-contract"],"payload":payload}}

def test_framework_contract():
    x=framework(); assert x["ok"] is True; assert x["target_key"]=='site-intelligence'; assert x["consumer_version"]=='4.41.0'; assert x["capabilities"]["automatic_execution"] is False; assert x["capabilities"]["persistence"] is False

def test_consume_builds_ephemeral_receipt():
    x=consume(packet()); assert x["accepted"] is True; assert x["execution"]["performed"] is False; assert x["persistence"]["performed"] is False; assert len(x["receipt_fingerprint"])==64
