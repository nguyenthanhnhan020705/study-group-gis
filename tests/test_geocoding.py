import asyncio
from dataclasses import replace

import httpx
import pytest

from app.core.config import Settings


def candidate(**changes):
    return {"lat": 10.85, "lon": 106.76, "formatted": "Đường kiểm thử, Việt Nam", "country_code": "vn", "result_type": "street", "rank": {"confidence": 0.95}, **changes}


def run_lookup(handler, students=None, **settings):
    from app.services.geocoding_service import GeocodingService
    from app.schemas.geocoding import GeocodeInput
    config = replace(Settings(cors_origins=(), geoapify_api_key="test-secret"), geocoding_interval=0, **settings)
    service = GeocodingService(config, transport=httpx.MockTransport(handler))
    rows = students or [{"student_id": "S1", "address": "Đường kiểm thử"}]
    return asyncio.run(service.batch([GeocodeInput(**row) for row in rows]))


def test_candidates_are_review_only_and_requests_stay_in_vietnam():
    def handler(request):
        assert request.url.params["filter"] == "countrycode:vn"
        assert request.url.params["apiKey"] == "test-secret"
        assert request.url.params["format"] == "json"
        return httpx.Response(200, json={"results": [candidate(), candidate(formatted="Đường khác")]})
    result = run_lookup(handler)[0]
    assert result.status == "needs_review"
    assert len(result.candidates) == 2
    assert all(c.eligible for c in result.candidates)
    assert "test-secret" not in result.model_dump_json()


@pytest.mark.parametrize("changes", [
    {"result_type": "city"}, {"result_type": "house"}, {"lat": 21.03},
    {"country_code": "us"}, {"rank": {"confidence": 0.1}}, {"rank": {}},
    {"lat": None}, {"lon": "not a number"}, {"lat": True},
])
def test_coarse_low_confidence_or_invalid_candidates_cannot_be_confirmed(changes):
    result = run_lookup(lambda request: httpx.Response(200, json={"results": [candidate(**changes)]}))[0]
    assert not any(c.eligible for c in result.candidates)
    assert result.status == "needs_review"


def test_no_results_does_not_invent_coordinates():
    result = run_lookup(lambda request: httpx.Response(200, json={"results": []}))[0]
    assert result.candidates == [] and result.status == "needs_review"


@pytest.mark.parametrize("code", [401, 403, 429, 500])
def test_provider_errors_are_sanitized(code):
    result = run_lookup(lambda request: httpx.Response(code, text="test-secret upstream private detail"))[0]
    assert result.status == "error"
    assert "test-secret" not in result.model_dump_json()
    assert "private detail" not in result.model_dump_json()
    assert result.error_code


def test_timeout_is_safe():
    def handler(request):
        raise httpx.ReadTimeout("https://provider/?apiKey=test-secret", request=request)
    result = run_lookup(handler)[0]
    assert result.error_code == "timeout"
    assert "test-secret" not in result.model_dump_json()


def test_duplicate_addresses_are_called_once_but_keep_both_students():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"results": [candidate()]})
    rows = [{"student_id": "S1", "address": "Đường A"}, {"student_id": "S2", "address": " Đường  A "}]
    results = run_lookup(handler, rows)
    assert len(calls) == 1
    assert [row.student_id for row in results] == ["S1", "S2"]


def test_bad_provider_json_is_controlled():
    result = run_lookup(lambda request: httpx.Response(200, text="not json"))[0]
    assert result.status == "error" and not result.candidates


def test_rate_limit_stops_remaining_batch_and_rejects_immediate_retry():
    from app.services.geocoding_service import GeocodingService, GeocodeProblem
    from app.schemas.geocoding import GeocodeInput
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(429)
    service = GeocodingService(replace(Settings(cors_origins=(), geoapify_api_key="test-secret"), geocoding_interval=0), transport=httpx.MockTransport(handler))
    rows = [GeocodeInput(student_id="S1", address="A"), GeocodeInput(student_id="S2", address="B")]
    async def scenario():
        results = await service.batch(rows)
        assert all(row.error_code == "rate_limit" for row in results)
        assert not service.busy
        with pytest.raises(GeocodeProblem) as caught:
            await service.batch(rows)
        assert caught.value.status_code == 429
    asyncio.run(scenario())
    assert len(calls) == 1


def test_concurrent_job_is_rejected_and_lock_released():
    from app.services.geocoding_service import GeocodingService, GeocodeProblem
    from app.schemas.geocoding import GeocodeInput
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        async def handler(request):
            entered.set()
            await release.wait()
            return httpx.Response(200, json={"results": []})
        service = GeocodingService(Settings(cors_origins=(), geoapify_api_key="test-secret"), transport=httpx.MockTransport(handler))
        rows = [GeocodeInput(student_id="S1", address="A")]
        first = asyncio.create_task(service.batch(rows))
        await entered.wait()
        try:
            with pytest.raises(GeocodeProblem) as caught:
                await service.batch(rows)
            assert caught.value.status_code == 429
        finally:
            release.set()
            await first
        assert not service.busy
    asyncio.run(scenario())
