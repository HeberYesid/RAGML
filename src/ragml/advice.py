"""Deterministic advice rules; no model calls or natural-language parsing."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from ragml.commercial import CommercialLookup, CommercialPort, ValueView
from ragml.contracts import (
    AttributeValue,
    CatalogDataset,
    Category,
    Contract,
    Identifier,
    Money,
    Stock,
    Variant,
)
from ragml.conversation import CommercialCitation, SessionRequirement, SessionState


class AttributeConstraint(SessionRequirement):
    """A validated recommendation constraint that can be retained in a session."""


class AdviceRequest(Contract):
    category_id: Identifier
    budget: Money | None = None
    mandatory: tuple[AttributeConstraint, ...] = ()
    preferences: tuple[AttributeConstraint, ...] = ()


class AdviceIssue(Contract):
    code: Identifier
    attribute_key: Identifier | None = None


class CandidateDecision(Contract):
    product_id: Identifier
    variant_id: Identifier
    price: Money | None
    stock: Stock | None
    issues: tuple[AdviceIssue, ...]
    commercial: CommercialLookup | None
    attributes: tuple[AttributeValue, ...]
    preference_matches: tuple[Identifier, ...] = ()

    @property
    def eligible(self) -> bool:
        return not self.issues


class AdviceResult(Contract):
    status: Literal["recommended", "no_matches", "clarification_required"]
    recommended_variant_ids: tuple[Identifier, ...]
    decisions: tuple[CandidateDecision, ...]
    citations: tuple[CommercialCitation, ...]
    warnings: tuple[Identifier, ...] = ()


class ComparisonRow(Contract):
    key: Identifier
    label: Identifier
    unit: Identifier | None
    values: tuple[AttributeValue | None, ...]


class ComparisonResult(Contract):
    status: Literal["ready", "incomplete"]
    category_id: Identifier
    decisions: tuple[CandidateDecision, ...]
    rows: tuple[ComparisonRow, ...]
    citations: tuple[CommercialCitation, ...]


class CategoryTransition(Contract):
    request: AdviceRequest
    pending_mandatory: tuple[AttributeConstraint, ...]
    pending_preferences: tuple[AttributeConstraint, ...]

    @property
    def needs_clarification(self) -> bool:
        return bool(self.pending_mandatory or self.pending_preferences)


def _current_value[T](view: ValueView[T] | None, evaluated_at: datetime) -> T | None:
    if (
        view is not None
        and view.status == "fresh"
        and view.source_updated_at <= evaluated_at < view.expires_at
    ):
        return view.value
    return None


def _matches(constraint: AttributeConstraint, attribute: AttributeValue | None) -> bool:
    if attribute is None or attribute.value is None or attribute.unit != constraint.unit:
        return False
    actual, target = attribute.value, constraint.value
    numeric = (
        isinstance(actual, int | float)
        and not isinstance(actual, bool)
        and isinstance(target, int | float)
        and not isinstance(target, bool)
    )
    if constraint.operator == "eq":
        return (numeric or type(actual) is type(target)) and actual == target
    if not numeric:
        return False
    # Runtime types were narrowed semantically; numeric constraints are validated by the caller.
    if isinstance(actual, int | float) and isinstance(target, int | float):
        return actual >= target if constraint.operator == "min" else actual <= target
    return False


def _validate_constraints(category: Category, constraints: tuple[AttributeConstraint, ...]) -> None:
    definitions = {d.key: d for d in category.attribute_definitions}
    for constraint in constraints:
        definition = definitions.get(constraint.key)
        if definition is None or definition.unit != constraint.unit:
            raise ValueError("Unknown constraint attribute or incompatible unit")
        value = constraint.value
        valid_type = {
            "text": isinstance(value, str),
            "choice": isinstance(value, str) and value in definition.choices,
            "number": isinstance(value, int | float) and not isinstance(value, bool),
            "boolean": isinstance(value, bool),
        }[definition.value_type]
        if not valid_type or (constraint.operator != "eq" and definition.value_type != "number"):
            raise ValueError("Invalid constraint type or operator")


def change_advice_category(
    catalog: CatalogDataset,
    previous: AdviceRequest,
    category_id: str,
) -> CategoryTransition:
    """Return compatible constraints and an explicit queue for user clarification.

    The caller must resolve pending constraints before recommending from the new request.
    No currency or unit conversion, persistence, or conversation interpretation occurs here.
    """
    categories = {c.category_id: c for c in catalog.profile.categories}
    if previous.category_id not in categories or category_id not in categories:
        raise ValueError("Unknown category")
    old_category, new_category = categories[previous.category_id], categories[category_id]
    _validate_constraints(old_category, previous.mandatory + previous.preferences)
    old_definitions = {d.key: d for d in old_category.attribute_definitions}
    new_definitions = {d.key: d for d in new_category.attribute_definitions}

    def compatible(constraint: AttributeConstraint) -> bool:
        old, new = old_definitions[constraint.key], new_definitions.get(constraint.key)
        return new is not None and (old.value_type, old.unit, old.choices, old.label) == (
            new.value_type,
            new.unit,
            new.choices,
            new.label,
        )

    return CategoryTransition(
        request=AdviceRequest(
            category_id=category_id,
            budget=previous.budget,
            mandatory=tuple(c for c in previous.mandatory if compatible(c)),
            preferences=tuple(c for c in previous.preferences if compatible(c)),
        ),
        pending_mandatory=tuple(c for c in previous.mandatory if not compatible(c)),
        pending_preferences=tuple(c for c in previous.preferences if not compatible(c)),
    )


def resolve_presented_variant(
    catalog: CatalogDataset,
    state: SessionState,
    *,
    session_id: UUID,
    position: int,
) -> Variant | None:
    """Resolve a one-based ordinal in an already owner-authorized session.

    Ownership must be enforced by SessionRepository.load before calling this helper.
    An absent, repeated, or removed selection requires clarification (None).
    """
    if (
        state.session_id != session_id
        or state.store_id != catalog.profile.store_id
        or state.profile_revision != catalog.profile.revision
    ):
        raise ValueError("Invalid session scope or profile revision")
    presented = state.presented_variants
    if (
        isinstance(position, bool)
        or not isinstance(position, int)
        or position < 1
        or position > len(presented)
        or len(set(presented)) != len(presented)
    ):
        return None
    variants = {v.variant_id: v for v in catalog.variants}
    if any(key not in variants for key in presented):
        return None
    return variants[presented[position - 1]]


def _commercial_citations(lookup: CommercialLookup) -> tuple[CommercialCitation, ...]:
    if lookup.source_id is None or lookup.revision is None or lookup.snapshot_id is None:
        return ()
    citations = []
    for field in ("price", "stock"):
        view = lookup.price if field == "price" else lookup.stock
        if view is not None and view.status == "fresh" and view.value is not None:
            citations.append(
                CommercialCitation(
                    citation_id=f"{field}:{lookup.variant_id}",
                    store_id=lookup.store_id,
                    source_id=lookup.source_id,
                    source_version=lookup.revision,
                    snapshot_id=lookup.snapshot_id,
                    variant_id=lookup.variant_id,
                    field="price" if field == "price" else "stock",
                    source_updated_at=view.source_updated_at,
                    expires_at=view.expires_at,
                )
            )
    return tuple(citations)


class Advisor:
    """Apply constraints to catalog variants and refresh commerce on every call."""

    def __init__(self, catalog: CatalogDataset, commercial: CommercialPort) -> None:
        self.catalog = catalog
        self.commercial = commercial

    def recommend(
        self,
        request: AdviceRequest,
        evaluated_at: datetime,
        *,
        variant_ids: tuple[str, ...] | None = None,
    ) -> AdviceResult:
        if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
            raise ValueError("Evaluation time must include a timezone")
        category = next(
            (c for c in self.catalog.profile.categories if c.category_id == request.category_id),
            None,
        )
        if category is None:
            raise ValueError("Unknown category")
        _validate_constraints(category, request.mandatory + request.preferences)
        if request.budget and request.budget.currency != self.catalog.profile.currency:
            return AdviceResult(
                status="clarification_required",
                recommended_variant_ids=(),
                decisions=(),
                citations=(),
                warnings=("budget_currency_mismatch",),
            )
        products = {p.product_id: p for p in self.catalog.products}
        variants = tuple(
            v
            for v in self.catalog.variants
            if products[v.product_id].category_id == request.category_id
        )
        if variant_ids is not None:
            if len(set(variant_ids)) != len(variant_ids) or not set(variant_ids) <= {
                v.variant_id for v in variants
            }:
                raise ValueError("Invalid variant selection for category")
            by_id = {v.variant_id: v for v in variants}
            variants = tuple(by_id[key] for key in variant_ids)
        supplied = self.commercial.lookup(
            self.catalog.profile.store_id, tuple(v.variant_id for v in variants), evaluated_at
        )
        expected_ids = {v.variant_id for v in variants}
        if (
            len({v.variant_id for v in supplied}) != len(supplied)
            or any(
                v.store_id != self.catalog.profile.store_id
                or v.data_mode != self.catalog.profile.data_mode
                or v.variant_id not in expected_ids
                or v.checked_at > evaluated_at
                for v in supplied
            )
            or len({v.revision for v in supplied if v.revision is not None}) > 1
        ):
            raise ValueError("Commercial results violate the query scope or revision")
        lookups = {item.variant_id: item for item in supplied}
        decisions: list[CandidateDecision] = []
        citations: list[CommercialCitation] = []
        for variant in variants:
            lookup = lookups.get(variant.variant_id)
            verified = (
                lookup is not None
                and lookup.lookup_status == "found"
                and lookup.source_id is not None
                and lookup.revision is not None
                and lookup.snapshot_id is not None
            )
            price = _current_value(lookup.price, evaluated_at) if verified and lookup else None
            stock = _current_value(lookup.stock, evaluated_at) if verified and lookup else None
            issues = []
            if price is None:
                issues.append(AdviceIssue(code="price_unconfirmed"))
            elif price.currency != self.catalog.profile.currency:
                issues.append(AdviceIssue(code="currency_mismatch"))
                price = None
            elif request.budget and price.amount > request.budget.amount:
                issues.append(AdviceIssue(code="over_budget"))
            if stock is None:
                issues.append(AdviceIssue(code="stock_unconfirmed"))
            elif stock.availability == "out_of_stock":
                issues.append(AdviceIssue(code="out_of_stock"))
            attributes = {a.key: a for a in products[variant.product_id].attributes}
            attributes.update({a.key: a for a in variant.attributes})
            for requirement in request.mandatory:
                attribute = attributes.get(requirement.key)
                if not _matches(requirement, attribute):
                    issues.append(
                        AdviceIssue(
                            code="requirement_unknown"
                            if attribute is None or attribute.value is None
                            else "requirement_not_met",
                            attribute_key=requirement.key,
                        )
                    )
            decision = CandidateDecision(
                product_id=variant.product_id,
                variant_id=variant.variant_id,
                price=price,
                stock=stock,
                issues=tuple(issues),
                commercial=lookup,
                attributes=tuple(attributes.values()),
                preference_matches=tuple(
                    dict.fromkeys(
                        preference.key
                        for preference in request.preferences
                        if _matches(preference, attributes.get(preference.key))
                    )
                ),
            )
            decisions.append(decision)
            if decision.eligible and lookup is not None:
                citations.extend(_commercial_citations(lookup))
        eligible = sorted(
            (d for d in decisions if d.eligible),
            key=lambda d: (
                -len(d.preference_matches),
                d.price.amount if d.price else 0,
                d.variant_id,
            ),
        )
        return AdviceResult(
            status="recommended" if eligible else "no_matches",
            recommended_variant_ids=tuple(d.variant_id for d in eligible),
            decisions=tuple(decisions),
            citations=tuple(citations),
        )

    def compare(self, variant_ids: tuple[str, ...], evaluated_at: datetime) -> ComparisonResult:
        """Compare selected variants from one category, without inferring a winner."""
        if len(variant_ids) < 2 or len(set(variant_ids)) != len(variant_ids):
            raise ValueError("Comparison requires at least two distinct variants")
        variants = {v.variant_id: v for v in self.catalog.variants}
        products = {p.product_id: p for p in self.catalog.products}
        if any(key not in variants for key in variant_ids):
            raise ValueError("Comparison references an unknown variant")
        categories = {products[variants[key].product_id].category_id for key in variant_ids}
        if len(categories) != 1:
            raise ValueError("Comparison requires a single category")
        category_id = next(iter(categories))
        category = next(c for c in self.catalog.profile.categories if c.category_id == category_id)
        advice = self.recommend(
            AdviceRequest(category_id=category_id), evaluated_at, variant_ids=variant_ids
        )
        attributes = []
        for key in variant_ids:
            variant = variants[key]
            merged = {a.key: a for a in products[variant.product_id].attributes}
            merged.update({a.key: a for a in variant.attributes})
            attributes.append(merged)
        rows = tuple(
            ComparisonRow(
                key=definition.key,
                label=definition.label,
                unit=definition.unit,
                values=tuple(values.get(definition.key) for values in attributes),
            )
            for definition in category.attribute_definitions
        )
        incomplete = any(
            value is None or value.value is None for row in rows for value in row.values
        ) or any(d.price is None or d.stock is None for d in advice.decisions)
        citations = tuple(
            citation
            for decision in advice.decisions
            if decision.commercial is not None
            for citation in _commercial_citations(decision.commercial)
            if (citation.field == "price" and decision.price is not None)
            or (citation.field == "stock" and decision.stock is not None)
        )
        return ComparisonResult(
            status="incomplete" if incomplete else "ready",
            category_id=category_id,
            decisions=advice.decisions,
            rows=rows,
            citations=citations,
        )
