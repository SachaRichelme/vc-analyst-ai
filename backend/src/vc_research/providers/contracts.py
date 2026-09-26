from typing import Generic, Literal, Protocol, TypeVar
from uuid import UUID
from pydantic import AnyHttpUrl, BaseModel, model_validator
from ..domain.common import Contract, Count, Mode, Nonnegative, PositiveCount, Text, Timestamp
from ..domain.research import Task

T = TypeVar("T", bound=BaseModel)


class ProviderUsage(Contract):
    input_tokens: Count = 0
    output_tokens: Count = 0
    search_requests: Count = 0
    documents_processed: Count = 0
    estimated_cost: Nonnegative | None = None
    basis: Literal["unreported", "fixture", "provider_reported"] = "unreported"
    rate_card_version: Text | None = None


class Result(Contract, Generic[T]):
    status: Literal["success", "partial", "abstained", "failed"]
    data: T | None = None
    reason: Text | None = None
    usage: ProviderUsage

    @model_validator(mode="after")
    def coherent(self):
        if self.status in {"success", "partial"} and self.data is None:
            raise ValueError("successful/partial response must preserve data")
        if self.status in {"abstained", "failed"} and self.data is not None:
            raise ValueError("use partial status for retained data")
        if self.status != "success" and not self.reason:
            raise ValueError("non-success response requires explanation")
        return self


class RequestContext(Contract):
    run_id: UUID
    company_id: UUID | None = None
    mode: Mode
    operation_key: Text


class SearchRequest(Contract):
    context: RequestContext
    query: Text
    requested_at: Timestamp
    published_after: Timestamp | None = None
    max_results: PositiveCount
    # Database-only discovery cannot satisfy this external-provider contract.
    require_fresh_external: Literal[True] = True

    @model_validator(mode="after")
    def valid_window(self):
        if self.published_after and self.published_after > self.requested_at:
            raise ValueError("search window starts in future")
        return self


class SearchHit(Contract):
    url: AnyHttpUrl
    title: Text
    snippet: Text
    published_at: Timestamp | None = None
    date_basis: Literal["unknown", "publication", "announcement", "event"] = "unknown"

    @model_validator(mode="after")
    def date_basis_known(self):
        if (self.published_at is None) != (self.date_basis == "unknown"):
            raise ValueError("date and date basis must both be known or both unknown")
        return self


class SearchData(Contract):
    mode: Mode
    external_attempted: bool
    fetched_at: Timestamp
    hits: tuple[SearchHit, ...]

    @model_validator(mode="after")
    def demo_is_not_fresh(self):
        if self.mode == "demo" and self.external_attempted:
            raise ValueError("demo cannot claim a live external request")
        return self


class ModelRequest(Contract):
    context: RequestContext
    task: Task
    model: Text
    model_revision: Text | None = None
    prompt_version: Text
    output_schema_version: Text
    input_text: Text
    max_output_tokens: PositiveCount


class SearchProvider(Protocol):
    def search(self, request: SearchRequest) -> Result[SearchData]: ...


class ModelProvider(Protocol):
    def complete(self, request: ModelRequest, output_type: type[T]) -> Result[T]: ...


class ExistingKnowledge(Protocol):
    """Local memory contract kept distinct from fresh external discovery."""
    def company_ids_for_query(self, query: str) -> tuple[UUID, ...]: ...
