"""Exact fixture replay. Unknown inputs abstain; no networking or live fallback."""
import hashlib
from pydantic import model_validator
from ..domain.common import Contract, Text
from .contracts import (ModelRequest, ProviderUsage, Result, SearchData, SearchRequest, T)


class LiveOperationsDisabled(RuntimeError):
    pass


def require_demo(mode: str):
    if mode != "demo":
        raise LiveOperationsDisabled("Live operations are disabled until the Step 2 admission gateway exists")


def fingerprint(request: ModelRequest | SearchRequest) -> str:
    # Run identity/time are not semantic fixture keys. All task/model/schema/input
    # and search query/window/options remain part of the match. Not a live cache.
    content = request.model_dump_json(exclude={"context", "requested_at"})
    return hashlib.sha256(content.encode()).hexdigest()


class SearchFixture(Contract):
    request: SearchRequest
    response: Result[SearchData]

    @model_validator(mode="after")
    def demo_only(self):
        if self.request.context.mode != "demo" or (
            self.response.data and self.response.data.mode != "demo"):
            raise ValueError("fixtures must be demo-only")
        if self.response.data and len(self.response.data.hits) > self.request.max_results:
            raise ValueError("search fixture exceeds requested result limit")
        if self.response.usage.basis != "fixture":
            raise ValueError("fixture usage must be labeled")
        return self


class ModelFixture(Contract):
    request: ModelRequest
    status: str
    output_json: Text | None = None
    reason: Text | None = None

    @model_validator(mode="after")
    def demo_only(self):
        if self.request.context.mode != "demo":
            raise ValueError("fixtures must be demo-only")
        if self.status not in {"success", "partial", "abstained", "failed"}:
            raise ValueError("invalid provider status")
        if (self.status in {"success", "partial"}) != (self.output_json is not None):
            raise ValueError("fixture status and output disagree")
        if self.status != "success" and not self.reason:
            raise ValueError("non-success fixture requires reason")
        return self


class FixtureSearchProvider:
    def __init__(self, cases: tuple[SearchFixture, ...]):
        self._cases = {fingerprint(c.request): c for c in cases}
        if len(self._cases) != len(cases):
            raise ValueError("duplicate search fixture identity")

    def search(self, request: SearchRequest) -> Result[SearchData]:
        require_demo(request.context.mode)
        case = self._cases.get(fingerprint(request))
        if case is None:
            return Result[SearchData](status="abstained", reason="Query is outside demo fixtures",
                                      usage=ProviderUsage(basis="fixture", estimated_cost="0"))
        return case.response


class FixtureModelProvider:
    def __init__(self, cases: tuple[ModelFixture, ...]):
        self._cases = {fingerprint(c.request): c for c in cases}
        if len(self._cases) != len(cases):
            raise ValueError("duplicate model fixture identity")

    def complete(self, request: ModelRequest, output_type: type[T]) -> Result[T]:
        require_demo(request.context.mode)
        case = self._cases.get(fingerprint(request))
        usage = ProviderUsage(basis="fixture", estimated_cost="0")
        if case is None:
            return Result[T](status="abstained", reason="Input/version is outside demo fixtures", usage=usage)
        # Malformed recorded output raises validation error. No automatic repair,
        # spending, dynamic code, or substitution of a different case.
        data = output_type.model_validate_json(case.output_json) if case.output_json else None
        return Result[T](status=case.status, data=data, reason=case.reason, usage=usage)
