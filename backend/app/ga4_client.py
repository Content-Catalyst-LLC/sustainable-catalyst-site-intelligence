from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional

from .config import Settings, get_settings
from .models import GA4ReportRow
from .sample_data import sample_event_rows, sample_page_rows


class GA4Client:
    """Small wrapper around the Google Analytics Data API.

    The backend works in demo mode when GA4 credentials are not present. This
    keeps local development and Render smoke tests from failing before the
    service account is configured.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None
        self._credentials = None

    @property
    def enabled(self) -> bool:
        return self.settings.ga4_enabled

    def _build_client(self):
        if self._client is not None:
            return self._client
        if not self.enabled:
            return None

        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.oauth2 import service_account

        if self.settings.google_application_credentials_json:
            info = json.loads(self.settings.google_application_credentials_json)
            self._credentials = service_account.Credentials.from_service_account_info(info)
            self._client = BetaAnalyticsDataClient(credentials=self._credentials)
        elif self.settings.google_application_credentials_file:
            self._credentials = service_account.Credentials.from_service_account_file(
                self.settings.google_application_credentials_file
            )
            self._client = BetaAnalyticsDataClient(credentials=self._credentials)
        else:
            # Allows GOOGLE_APPLICATION_CREDENTIALS to be used by the library.
            self._client = BetaAnalyticsDataClient()
        return self._client


    def diagnostics(self) -> Dict[str, Any]:
        """Return protected GA4 setup diagnostics without exposing private keys."""
        result: Dict[str, Any] = {
            "enabled": self.enabled,
            "property_id": self.settings.ga4_property_id,
            "property_id_numeric": str(self.settings.ga4_property_id or "").isdigit(),
            "credential_source": "none",
            "json_parse_ok": None,
            "client_email": None,
            "project_id": None,
            "run_report_ok": None,
            "error_type": None,
            "error_message": None,
        }
        if not self.enabled:
            result["run_report_ok"] = False
            result["error_message"] = "GA4 is disabled because demo mode is enabled or property/credentials are missing."
            return result
        try:
            if self.settings.google_application_credentials_json:
                result["credential_source"] = "SC_SI_GOOGLE_APPLICATION_CREDENTIALS_JSON"
                info = json.loads(self.settings.google_application_credentials_json)
                result["json_parse_ok"] = True
                result["client_email"] = info.get("client_email")
                result["project_id"] = info.get("project_id")
            elif self.settings.google_application_credentials_file:
                result["credential_source"] = "SC_SI_GOOGLE_APPLICATION_CREDENTIALS_FILE"
                result["json_parse_ok"] = "file"
            else:
                result["credential_source"] = "application_default_credentials"
                result["json_parse_ok"] = "default"
            rows = self.run_report(["pagePath"], ["screenPageViews"], "7daysAgo", "today", limit=1)
            result["run_report_ok"] = True
            result["sample_rows"] = len(rows)
            return result
        except Exception as exc:  # noqa: BLE001 - diagnostics should report setup failures.
            result["run_report_ok"] = False
            result["error_type"] = exc.__class__.__name__
            result["error_message"] = str(exc)
            return result

    def run_report(
        self,
        dimensions: Iterable[str],
        metrics: Iterable[str],
        start_date: str = "28daysAgo",
        end_date: str = "today",
        limit: Optional[int] = None,
    ) -> List[GA4ReportRow]:
        if not self.enabled:
            if "eventName" in set(dimensions):
                return sample_event_rows()
            return sample_page_rows()

        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

        client = self._build_client()
        request = RunReportRequest(
            property=f"properties/{self.settings.ga4_property_id}",
            dimensions=[Dimension(name=name) for name in dimensions],
            metrics=[Metric(name=name) for name in metrics],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            limit=limit or self.settings.max_ga4_rows,
        )
        response = client.run_report(request)
        output: List[GA4ReportRow] = []
        dim_names = [header.name for header in response.dimension_headers]
        metric_names = [header.name for header in response.metric_headers]
        for row in response.rows:
            dims = {name: row.dimension_values[idx].value for idx, name in enumerate(dim_names)}
            vals = {}
            for idx, name in enumerate(metric_names):
                raw = row.metric_values[idx].value
                try:
                    vals[name] = float(raw)
                except ValueError:
                    vals[name] = 0.0
            output.append(GA4ReportRow(dimensions=dims, metrics=vals))
        return output

    def page_report(self, start_date: str, end_date: str) -> List[GA4ReportRow]:
        return self.run_report(
            dimensions=["pagePath", "pageTitle"],
            metrics=["screenPageViews", "activeUsers", "eventCount", "engagementRate", "averageSessionDuration"],
            start_date=start_date,
            end_date=end_date,
        )

    def event_report(self, start_date: str, end_date: str) -> List[GA4ReportRow]:
        return self.run_report(
            dimensions=["pagePath", "eventName"],
            metrics=["eventCount"],
            start_date=start_date,
            end_date=end_date,
        )


@lru_cache(maxsize=1)
def get_ga4_client() -> GA4Client:
    return GA4Client(get_settings())
