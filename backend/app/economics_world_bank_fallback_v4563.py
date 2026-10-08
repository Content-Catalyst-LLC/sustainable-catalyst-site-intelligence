"""Live, source-attributed World Bank country indicator fallback.

Used only when Platform Core economic observations are empty. No invented observations.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

INDICATORS = {
    "NY.GDP.MKTP.CD": ("GDP (current US$)", "USD", "macroeconomics"),
    "NY.GDP.MKTP.KD.ZG": ("GDP growth (annual %)", "%", "macroeconomics"),
    "FP.CPI.TOTL.ZG": ("Inflation, consumer prices (annual %)", "%", "finance"),
    "SP.POP.TOTL": ("Population, total", "people", "demographics"),
    "EN.ATM.CO2E.PC": ("CO2 emissions (metric tons per capita)", "metric tons per capita", "sustainability"),
}
def get_country_records(country: str, indicator_code: str = "", limit: int = 100) -> list[dict]:
    country = (country or "").strip().upper()
    if len(country) != 3 or not country.isalpha():
        return []
    codes = [indicator_code] if indicator_code in INDICATORS else list(INDICATORS)
    if indicator_code and indicator_code not in INDICATORS:
        return []
    output = []
    for code in codes:
        name, unit, family = INDICATORS[code]
        url = f"https://api.worldbank.org/v2/country/{quote(country)}/indicator/{quote(code)}?format=json&per_page=12"
        try:
            req = Request(url, headers={"Accept":"application/json","User-Agent":"Sustainable-Catalyst-Site-Intelligence/4.56.3"})
            with urlopen(req, timeout=6) as response:
                payload = json.load(response)
            rows = payload[1] if isinstance(payload, list) and len(payload)>1 and isinstance(payload[1],list) else []
            for item in rows:
                value = item.get("value")
                if value is None or isinstance(value,bool):
                    continue
                try:
                    numeric = float(value)
                except (ValueError,TypeError):
                    continue
                year = str(item.get("date") or "")
                if not year:
                    continue
                country_name = (item.get("country") or {}).get("value") or country
                output.append({
                    "id":f"world-bank:{country}:{code}:{year}",
                    "source_record_id":f"{country}:{code}:{year}",
                    "source_id":"world-bank",
                    "record_type":"official_statistic",
                    "subject":name,"family":family,
                    "indicator_code":code,"indicator_name":name,
                    "geography_code":country,"geography_name":country_name,
                    "period":year,"period_start":year,"frequency":"annual",
                    "value_number":numeric,"value_text":"","unit":unit,
                    "status":"latest_available","data_status":"ANNUAL",
                    "source_url":f"https://data.worldbank.org/indicator/{quote(code)}?locations={quote(country)}",
                    "attribution":"World Bank Open Data (live fallback; not a Platform Core observation)",
                    "dataset_id":"World Development Indicators",
                    "notes":"Live World Bank API observation. This result has not been ingested into Platform Core.",
                    "published_at":"","retrieved_at":datetime.now(timezone.utc).isoformat(),
                    "connector_id":"world-bank-live-fallback",
                    "family_label":{"macroeconomics":"Macroeconomics","finance":"Financial conditions","demographics":"Population and society","sustainability":"Sustainability and development"}[family]
                })
        except Exception:
            continue
    return sorted(output,key=lambda x:(x["indicator_code"],x["period"]),reverse=True)[:min(max(int(limit),1),300)]
