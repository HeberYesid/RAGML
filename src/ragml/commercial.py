"""Read-only JSON commercial adapter with explicit per-field freshness."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol

from pydantic import AwareDatetime

from ragml.contracts import (
    CatalogDataset,
    CommercialDataset,
    Contract,
    DataMode,
    Identifier,
    Money,
    Observation,
    Stock,
)


class ValueView[T](Contract):
    status: Literal["fresh", "unknown", "stale", "not_yet_valid"]
    value: T | None
    source_updated_at: AwareDatetime
    expires_at: AwareDatetime
    source_ref: Identifier


class CommercialLookup(Contract):
    store_id: Identifier
    variant_id: Identifier
    lookup_status: Literal["found", "not_found", "unavailable"]
    checked_at: AwareDatetime
    data_mode: DataMode
    revision: Identifier | None = None
    snapshot_id: Identifier | None = None
    source_id: Identifier | None = None
    price: ValueView[Money] | None = None
    stock: ValueView[Stock] | None = None
    error_code: Literal["source_unavailable", "invalid_source"] | None = None


class CommercialPort(Protocol):
    def lookup(
        self, store_id: str, variant_ids: tuple[str, ...], evaluated_at: datetime
    ) -> tuple[CommercialLookup, ...]: ...


def evaluate_observation[T](observation: Observation[T], evaluated_at: datetime) -> ValueView[T]:
    if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
        raise ValueError("Evaluation time must include a timezone")
    status: Literal["fresh", "unknown", "stale", "not_yet_valid"]
    if evaluated_at < observation.source_updated_at:
        status = "not_yet_valid"
    elif evaluated_at >= observation.expires_at:
        status = "stale"
    elif observation.value is None:
        status = "unknown"
    else:
        status = "fresh"
    return ValueView[T](
        status=status,
        value=observation.value if status == "fresh" else None,
        source_updated_at=observation.source_updated_at,
        expires_at=observation.expires_at,
        source_ref=observation.source_ref,
    )


class JsonCommercialAdapter:
    """Reload a complete local revision on each query; never fall back to stale data."""

    def __init__(self, path: Path, catalog: CatalogDataset) -> None:
        self.path = path
        self.catalog = catalog

    def lookup(
        self, store_id: str, variant_ids: tuple[str, ...], evaluated_at: datetime
    ) -> tuple[CommercialLookup, ...]:
        if store_id != self.catalog.profile.store_id:
            raise ValueError("Query store does not match the configured adapter")
        if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
            raise ValueError("Evaluation time must include a timezone")
        evaluated_at = evaluated_at.astimezone(UTC)
        known_variants = {v.variant_id for v in self.catalog.variants}
        if any(v not in known_variants for v in variant_ids):
            raise ValueError("Query references an unknown catalog variant")
        try:
            dataset = CommercialDataset.model_validate_json(self.path.read_text(encoding="utf-8"))
            dataset.validate_for_catalog(self.catalog)
        except OSError:
            return self._unavailable(variant_ids, evaluated_at, "source_unavailable")
        except ValueError:
            return self._unavailable(variant_ids, evaluated_at, "invalid_source")
        snapshots = {snapshot.variant_id: snapshot for snapshot in dataset.snapshots}
        results = []
        for variant_id in dict.fromkeys(variant_ids):
            snapshot = snapshots.get(variant_id)
            results.append(
                CommercialLookup(
                    store_id=store_id,
                    variant_id=variant_id,
                    lookup_status="found" if snapshot is not None else "not_found",
                    checked_at=evaluated_at,
                    data_mode=dataset.data_mode,
                    revision=dataset.revision,
                    snapshot_id=snapshot.snapshot_id if snapshot else None,
                    source_id=snapshot.source_id if snapshot else None,
                    price=evaluate_observation(snapshot.price, evaluated_at) if snapshot else None,
                    stock=evaluate_observation(snapshot.stock, evaluated_at) if snapshot else None,
                )
            )
        return tuple(results)

    def _unavailable(
        self,
        variant_ids: tuple[str, ...],
        evaluated_at: datetime,
        error_code: Literal["source_unavailable", "invalid_source"],
    ) -> tuple[CommercialLookup, ...]:
        return tuple(
            CommercialLookup(
                store_id=self.catalog.profile.store_id,
                variant_id=variant_id,
                lookup_status="unavailable",
                checked_at=evaluated_at,
                data_mode=self.catalog.profile.data_mode,
                error_code=error_code,
            )
            for variant_id in dict.fromkeys(variant_ids)
        )
