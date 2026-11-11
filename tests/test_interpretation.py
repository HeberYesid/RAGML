"""Natural Spanish requests interpreted through the public parser boundary."""

from decimal import Decimal
from pathlib import Path

import pytest

from ragml.contracts import CatalogDataset
from ragml.interpretation import interpret

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "message",
    (
        "¿Se puede confirmar que queda alguna unidad de Cámara Encuentro?",
        "¿Quedan unidades de Cámara Encuentro?",
        "¿Hay alguna unidad de Cámara Encuentro?",
    ),
)
def test_named_stock_questions_use_commercial_records(message: str) -> None:
    catalog = CatalogDataset.model_validate_json((ROOT / "data/sample/catalog.json").read_bytes())

    parsed = interpret(message, catalog)

    assert parsed.intent == "commercial"
    assert parsed.product_ids
    assert parsed.clarification is None


@pytest.mark.parametrize(
    ("budget_sentence", "amount"),
    (
        ("El presupuesto solo del producto es 89000 COP", "89000"),
        ("Mi presupuesto para el producto es de 120.000 COP", "120000"),
        ("Dispongo de un presupuesto total de 100 mil COP", "100000"),
    ),
)
def test_product_budget_and_mass_limit_survive_an_availability_qualifier(
    budget_sentence: str, amount: str
) -> None:
    catalog = CatalogDataset.model_validate_json((ROOT / "data/sample/catalog.json").read_bytes())
    message = (
        "Busco algo para mi espacio de trabajo en Periféricos. "
        f"{budget_sentence} y la masa debe ser como máximo 350 g. "
        "Muéstrame una opción disponible; el envío se considera aparte."
    )

    parsed = interpret(message, catalog)

    assert parsed.budget is not None
    assert parsed.budget.amount == Decimal(amount)
    assert parsed.budget.currency == "COP"
    assert parsed.intent == "recommend"
    assert parsed.category_id == "peripherals"
    assert parsed.clarification is None
    assert any(
        requirement.key == "weight_g"
        and requirement.operator == "max"
        and requirement.value == 350.0
        and requirement.unit == "g"
        for requirement in parsed.mandatory
    )
