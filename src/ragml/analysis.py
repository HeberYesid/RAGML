"""Reproducible descriptive analysis of validated catalog and document data."""

import argparse
import csv
import json
import math
import statistics
from collections.abc import Mapping
from datetime import datetime
from hashlib import sha256
from pathlib import Path

from ragml.commercial import evaluate_observation
from ragml.contracts import CatalogDataset, CommercialDataset, Contract
from ragml.evidence import SourceManifest
from ragml.ingestion import read_corpus
from ragml.settings import load_settings


class NumericSummary(Contract):
    count: int
    missing: int
    minimum: float | None = None
    q1: float | None = None
    median: float | None = None
    q3: float | None = None
    maximum: float | None = None
    mean: float | None = None
    sample_sd: float | None = None
    iqr: float | None = None
    lower_fence: float | None = None
    upper_fence: float | None = None
    outlier_count: int = 0
    outlier_values: tuple[float, ...] = ()


def describe(values: tuple[float | None, ...]) -> NumericSummary:
    """Use linear quartiles and sample SD; flag IQR outliers only for n >= 4."""
    known = sorted(value for value in values if value is not None)
    if not all(math.isfinite(value) for value in known):
        raise ValueError("nonfinite_analysis_value")
    count = len(known)
    if not count:
        return NumericSummary(count=0, missing=len(values))

    def percentile(fraction: float) -> float:
        position = (count - 1) * fraction
        lower, upper = math.floor(position), math.ceil(position)
        return known[lower] + (known[upper] - known[lower]) * (position - lower)

    q1, q3 = percentile(0.25), percentile(0.75)
    iqr = q3 - q1
    lower_fence, upper_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = tuple(v for v in known if v < lower_fence or v > upper_fence) if count >= 4 else ()
    return NumericSummary(
        count=count,
        missing=len(values) - count,
        minimum=known[0],
        q1=q1,
        median=statistics.median(known),
        q3=q3,
        maximum=known[-1],
        mean=statistics.mean(known),
        sample_sd=statistics.stdev(known) if count >= 2 else None,
        iqr=iqr,
        lower_fence=lower_fence if count >= 4 else None,
        upper_fence=upper_fence if count >= 4 else None,
        outlier_count=len(outliers),
        outlier_values=outliers,
    )


class CategorySummary(Contract):
    category_id: str
    name: str
    products: int
    variants: int
    prices: NumericSummary


class AttributeSummary(Contract):
    category_id: str
    key: str
    label: str
    unit: str | None
    value_type: str
    total_products: int
    known: int
    explicit_null: int
    absent: int
    numeric: NumericSummary | None = None


class CommercialRow(Contract):
    variant_id: str
    product_id: str
    category_id: str
    price_status: str
    observed_price_amount: str | None
    fresh_price_amount: float | None
    stock_status: str
    availability: str | None
    quantity: int | None


class DocumentRow(Contract):
    source_id: str
    scope: str
    characters: int
    words: int
    chunks: int


class OutlierRow(Contract):
    category_id: str
    variable: str
    entity_id: str
    value: float
    unit: str | None
    lower_fence: float
    upper_fence: float


class AnalysisReport(Contract):
    schema_version: str = "0.1"
    store_id: str
    data_mode: str
    catalog_revision: str
    commercial_revision: str
    source_revision: str
    evaluated_at: datetime
    currency: str
    counts: dict[str, int]
    input_sha256: dict[str, str]
    categories: tuple[CategorySummary, ...]
    attributes: tuple[AttributeSummary, ...]
    commerce: tuple[CommercialRow, ...]
    documents: tuple[DocumentRow, ...]
    fresh_prices: NumericSummary
    price_statuses: dict[str, int]
    stock_states: dict[str, int]
    document_lengths: NumericSummary
    chunk_lengths: NumericSummary
    outliers: tuple[OutlierRow, ...]


def analyze_dataset(
    catalog: CatalogDataset,
    commercial: CommercialDataset,
    manifest: SourceManifest,
    document_texts: Mapping[str, str],
    *,
    evaluated_at: datetime,
    input_sha256: dict[str, str] | None = None,
) -> AnalysisReport:
    """Analyze one validated revision without altering data or invoking a model."""
    if evaluated_at.utcoffset() is None:
        raise ValueError("analysis_clock_requires_timezone")
    commercial.validate_for_catalog(catalog)
    manifest.validate_for_catalog(catalog)
    active = {source.source_id: source for source in manifest.sources if source.active}
    if set(document_texts) != set(active):
        raise ValueError("analysis_document_set_mismatch")
    for source_id, text in document_texts.items():
        if sha256(text.encode("utf-8")).hexdigest() != active[source_id].content_hash:
            raise ValueError("analysis_document_hash_mismatch")
    if any(chunk.text not in document_texts[chunk.source_id] for chunk in manifest.chunks):
        raise ValueError("analysis_chunk_not_in_source")

    products = {product.product_id: product for product in catalog.products}
    snapshots = {snapshot.variant_id: snapshot for snapshot in commercial.snapshots}
    price_statuses = dict.fromkeys(("fresh", "unknown", "stale", "not_yet_valid", "not_found"), 0)
    stock_states = dict.fromkeys(
        ("in_stock", "out_of_stock", "unknown", "stale", "not_yet_valid", "not_found"), 0
    )
    rows = []
    for variant in catalog.variants:
        snapshot = snapshots.get(variant.variant_id)
        price_status = stock_status = "not_found"
        observed_amount = None
        fresh_amount = None
        availability = None
        quantity = None
        if snapshot is not None:
            price = evaluate_observation(snapshot.price, evaluated_at)
            stock = evaluate_observation(snapshot.stock, evaluated_at)
            price_status, stock_status = price.status, stock.status
            if snapshot.price.value is not None:
                observed_amount = str(snapshot.price.value.amount)
            if price.value is not None:
                fresh_amount = float(price.value.amount)
            if stock.value is not None:
                availability, quantity = stock.value.availability, stock.value.quantity
        price_statuses[price_status] += 1
        stock_states[
            availability if stock_status == "fresh" and availability else stock_status
        ] += 1
        rows.append(
            CommercialRow(
                variant_id=variant.variant_id,
                product_id=variant.product_id,
                category_id=products[variant.product_id].category_id,
                price_status=price_status,
                observed_price_amount=observed_amount,
                fresh_price_amount=fresh_amount,
                stock_status=stock_status,
                availability=availability,
                quantity=quantity,
            )
        )

    categories = []
    attributes = []
    outliers = []

    def record_outliers(
        category_id: str,
        variable: str,
        unit: str | None,
        values: tuple[tuple[str, float | None], ...],
        summary: NumericSummary,
    ) -> None:
        if summary.lower_fence is None or summary.upper_fence is None:
            return
        for entity_id, value in values:
            if value is not None and (value < summary.lower_fence or value > summary.upper_fence):
                outliers.append(
                    OutlierRow(
                        category_id=category_id,
                        variable=variable,
                        entity_id=entity_id,
                        value=value,
                        unit=unit,
                        lower_fence=summary.lower_fence,
                        upper_fence=summary.upper_fence,
                    )
                )

    for category in catalog.profile.categories:
        members = tuple(p for p in catalog.products if p.category_id == category.category_id)
        category_commerce = tuple(row for row in rows if row.category_id == category.category_id)
        price_values = tuple((row.variant_id, row.fresh_price_amount) for row in category_commerce)
        prices = describe(tuple(value for _, value in price_values))
        record_outliers(
            category.category_id, "fresh_price", catalog.profile.currency, price_values, prices
        )
        categories.append(
            CategorySummary(
                category_id=category.category_id,
                name=category.name,
                products=len(members),
                variants=len(category_commerce),
                prices=prices,
            )
        )
        for definition in category.attribute_definitions:
            present = {
                p.product_id: next((a for a in p.attributes if a.key == definition.key), None)
                for p in members
            }
            absent = sum(attribute is None for attribute in present.values())
            nulls = sum(
                attribute is not None and attribute.value is None for attribute in present.values()
            )
            numeric = None
            if definition.value_type == "number":
                values = tuple(
                    (
                        product_id,
                        float(attribute.value)
                        if attribute is not None
                        and isinstance(attribute.value, int | float)
                        and not isinstance(attribute.value, bool)
                        else None,
                    )
                    for product_id, attribute in present.items()
                )
                numeric = describe(tuple(value for _, value in values))
                record_outliers(
                    category.category_id, definition.key, definition.unit, values, numeric
                )
            attributes.append(
                AttributeSummary(
                    category_id=category.category_id,
                    key=definition.key,
                    label=definition.label,
                    unit=definition.unit,
                    value_type=definition.value_type,
                    total_products=len(members),
                    known=len(members) - absent - nulls,
                    explicit_null=nulls,
                    absent=absent,
                    numeric=numeric,
                )
            )

    documents = tuple(
        DocumentRow(
            source_id=source_id,
            scope=source.scope.kind,
            characters=len(document_texts[source_id]),
            words=len(document_texts[source_id].split()),
            chunks=sum(chunk.source_id == source_id for chunk in manifest.chunks),
        )
        for source_id, source in active.items()
    )
    return AnalysisReport(
        store_id=catalog.profile.store_id,
        data_mode=catalog.profile.data_mode,
        catalog_revision=catalog.profile.revision,
        commercial_revision=commercial.revision,
        source_revision=manifest.revision,
        evaluated_at=evaluated_at,
        currency=catalog.profile.currency,
        counts={
            "categories": len(catalog.profile.categories),
            "products": len(catalog.products),
            "variants": len(catalog.variants),
            "commercial_records": len(commercial.snapshots),
            "sources": len(manifest.sources),
            "chunks": len(manifest.chunks),
        },
        input_sha256=input_sha256 or {},
        categories=tuple(categories),
        attributes=tuple(attributes),
        commerce=tuple(rows),
        documents=documents,
        fresh_prices=describe(tuple(row.fresh_price_amount for row in rows)),
        price_statuses=price_statuses,
        stock_states=stock_states,
        document_lengths=describe(tuple(float(row.characters) for row in documents)),
        chunk_lengths=describe(tuple(float(len(chunk.text)) for chunk in manifest.chunks)),
        outliers=tuple(outliers),
    )


def _write_csv(path: Path, headers: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_tables(report: AnalysisReport, output_dir: Path) -> None:
    """Write a new, exclusive export directory; never overwrite an earlier run."""
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "summary.json").write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    category_rows: list[dict[str, object]] = []
    for category in report.categories:
        category_rows.append(
            {
                "category_id": category.category_id,
                "name": category.name,
                "products": category.products,
                "variants": category.variants,
                **{
                    f"price_{key}": value
                    for key, value in category.prices.model_dump().items()
                    if key != "outlier_values"
                },
            }
        )
    price_headers = tuple(
        f"price_{key}" for key in NumericSummary.model_fields if key != "outlier_values"
    )
    _write_csv(
        output_dir / "categories.csv",
        ("category_id", "name", "products", "variants", *price_headers),
        category_rows,
    )
    attribute_rows: list[dict[str, object]] = []
    for attribute in report.attributes:
        attribute_rows.append(
            {
                **attribute.model_dump(exclude={"numeric"}),
                **{
                    f"numeric_{key}": value
                    for key, value in (
                        attribute.numeric.model_dump().items() if attribute.numeric else {}
                    )
                    if key != "outlier_values"
                },
            }
        )
    _write_csv(
        output_dir / "attributes.csv",
        (
            "category_id",
            "key",
            "label",
            "unit",
            "value_type",
            "total_products",
            "known",
            "explicit_null",
            "absent",
            *(f"numeric_{key}" for key in NumericSummary.model_fields if key != "outlier_values"),
        ),
        attribute_rows,
    )
    for filename, records, model in (
        ("commercial", report.commerce, CommercialRow),
        ("documents", report.documents, DocumentRow),
        ("outliers", report.outliers, OutlierRow),
    ):
        _write_csv(
            output_dir / f"{filename}.csv",
            tuple(model.model_fields),
            [row.model_dump() for row in records],
        )


def render_charts(report: AnalysisReport, manifest: SourceManifest, output_dir: Path) -> None:
    """Render statistical figures with the optional Matplotlib dependency."""
    from matplotlib import rc_context
    from matplotlib.figure import Figure
    from matplotlib.ticker import MaxNLocator

    names = [category.name for category in report.categories]
    note = (
        f"Datos sintéticos · revisión {report.catalog_revision} · "
        f"reloj de referencia {report.evaluated_at.isoformat()}"
    )
    with rc_context(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titlesize": 15,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
        }
    ):
        figure = Figure(figsize=(11.6, 5.5))
        axis = figure.add_subplot()
        positions = list(range(len(names)))
        axis.barh(
            [v - 0.19 for v in positions],
            [c.products for c in report.categories],
            height=0.36,
            color="#194F90",
            label="Productos base",
        )
        axis.barh(
            [v + 0.19 for v in positions],
            [c.variants for c in report.categories],
            height=0.36,
            color="#42A596",
            label="Variantes",
        )
        axis.set_yticks(positions, names)
        axis.set_xlabel("Cantidad de registros")
        axis.set_title("Cobertura del catálogo por categoría", loc="left", pad=18)
        axis.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))
        axis.grid(axis="x", alpha=0.15)
        figure.subplots_adjust(left=0.23, right=0.78, bottom=0.17, top=0.85)
        figure.text(0.02, 0.025, note, fontsize=8, color="#555555")
        for suffix in ("png", "svg"):
            figure.savefig(output_dir / f"categories.{suffix}", dpi=180)

        figure = Figure(figsize=(11.6, 5.8))
        axis = figure.add_subplot()
        available = [category for category in report.categories if category.prices.count]
        price_sets = [
            [
                row.fresh_price_amount / 1000
                for row in report.commerce
                if row.category_id == category.category_id and row.fresh_price_amount is not None
            ]
            for category in available
        ]
        if available:
            axis.boxplot(
                price_sets,
                orientation="horizontal",
                tick_labels=[c.name for c in available],
                showmeans=True,
                patch_artist=True,
                boxprops={"facecolor": "#DDEAF5", "edgecolor": "#194F90"},
                medianprops={"color": "#C55F27", "linewidth": 2},
            )
        else:
            axis.text(
                0.5,
                0.5,
                "Sin precios vigentes al reloj declarado",
                ha="center",
                transform=axis.transAxes,
            )
        axis.set_xlabel(f"Precio simulado en miles de {report.currency}")
        axis.set_title("Distribución de precios vigentes simulados", loc="left", pad=18)
        axis.grid(axis="x", alpha=0.15)
        figure.subplots_adjust(left=0.23, right=0.96, bottom=0.19, top=0.85)
        figure.text(
            0.02,
            0.065,
            "Cajas Q1–Q3 · línea: mediana · triángulo: media · puntos: posibles atípicos IQR",
            fontsize=9,
        )
        figure.text(0.02, 0.025, note, fontsize=8, color="#555555")
        for suffix in ("png", "svg"):
            figure.savefig(output_dir / f"prices.{suffix}", dpi=180)

        figure = Figure(figsize=(11.6, 5.5))
        axis = figure.add_subplot()
        null_rates, absent_rates = [], []
        for category in report.categories:
            attributes = [a for a in report.attributes if a.category_id == category.category_id]
            denominator = sum(a.total_products for a in attributes)
            null_rates.append(
                100 * sum(a.explicit_null for a in attributes) / denominator if denominator else 0
            )
            absent_rates.append(
                100 * sum(a.absent for a in attributes) / denominator if denominator else 0
            )
        axis.barh(names, null_rates, color="#C55F27", label="Null explícito")
        axis.barh(names, absent_rates, left=null_rates, color="#D9B24A", label="Campo omitido")
        axis.set_xlabel("Porcentaje de combinaciones producto base × atributo definido")
        axis.set_title("Información no disponible en atributos", loc="left", pad=18)
        axis.set_xlim(
            0,
            max(
                100, max((a + b for a, b in zip(null_rates, absent_rates, strict=True)), default=0)
            ),
        )
        axis.legend(loc="lower right")
        axis.grid(axis="x", alpha=0.15)
        figure.subplots_adjust(left=0.23, right=0.96, bottom=0.19, top=0.85)
        figure.text(
            0.02,
            0.065,
            "Los atributos opcionales omitidos pueden no aplicar; no se imputan ni se consideran errores automáticamente.",
            fontsize=9,
        )
        figure.text(0.02, 0.025, note, fontsize=8, color="#555555")
        for suffix in ("png", "svg"):
            figure.savefig(output_dir / f"missingness.{suffix}", dpi=180)

        figure = Figure(figsize=(11.6, 5.5))
        prices_axis, stock_axis = figure.add_subplot(121), figure.add_subplot(122)
        price_labels = {
            "fresh": "Vigente",
            "unknown": "Desconocido",
            "stale": "Vencido",
            "not_yet_valid": "Futuro",
            "not_found": "Sin registro",
        }
        stock_labels = {
            "in_stock": "Disponible",
            "out_of_stock": "Agotado",
            "unknown": "Desconocido",
            "stale": "Vencido",
            "not_yet_valid": "Futuro",
            "not_found": "Sin registro",
        }
        for axis, statuses, labels, title, color in (
            (prices_axis, report.price_statuses, price_labels, "Estado del precio", "#194F90"),
            (stock_axis, report.stock_states, stock_labels, "Estado de existencias", "#42A596"),
        ):
            bars = axis.barh(
                [labels[key] for key in statuses], list(statuses.values()), color=color
            )
            axis.bar_label(bars, padding=4)
            axis.set_xlim(0, max(statuses.values(), default=0) * 1.2 + 1)
            axis.set_xlabel("Variantes")
            axis.set_title(title, loc="left", pad=16)
            axis.xaxis.set_major_locator(MaxNLocator(integer=True))
            axis.grid(axis="x", alpha=0.15)
        figure.subplots_adjust(left=0.12, right=0.96, bottom=0.17, top=0.85, wspace=0.6)
        figure.text(0.02, 0.025, note, fontsize=8, color="#555555")
        for suffix in ("png", "svg"):
            figure.savefig(output_dir / f"commerce.{suffix}", dpi=180)

        figure = Figure(figsize=(11.6, 5.5))
        document_axis, chunk_axis = figure.add_subplot(121), figure.add_subplot(122)
        for axis, values, title, color in (
            (
                document_axis,
                [row.characters for row in report.documents],
                "Longitud de documentos",
                "#194F90",
            ),
            (
                chunk_axis,
                [len(chunk.text) for chunk in manifest.chunks],
                "Longitud de fragmentos",
                "#42A596",
            ),
        ):
            axis.hist(values, bins=min(12, max(1, len(values))), color=color, edgecolor="white")
            axis.set_xlabel("Caracteres Unicode")
            axis.set_ylabel("Cantidad")
            axis.set_title(title, loc="left", pad=16)
            axis.yaxis.set_major_locator(MaxNLocator(integer=True))
            axis.grid(axis="y", alpha=0.15)
        figure.subplots_adjust(left=0.09, right=0.96, bottom=0.19, top=0.85, wspace=0.35)
        figure.text(
            0.02,
            0.065,
            "Los caracteres describen tamaño textual; no equivalen a tokens del modelo.",
            fontsize=9,
        )
        figure.text(0.02, 0.025, note, fontsize=8, color="#555555")
        for suffix in ("png", "svg"):
            figure.savefig(output_dir / f"lengths.{suffix}", dpi=180)


def write_readme(report: AnalysisReport, output_dir: Path, charts: bool) -> None:
    price = report.fresh_prices
    known = sum(a.known for a in report.attributes)
    nulls = sum(a.explicit_null for a in report.attributes)
    absent = sum(a.absent for a in report.attributes)

    def number(value: float | None) -> str:
        return f"{value:,.2f}" if value is not None else "No disponible"

    coverage_rows = "\n".join(
        f"| {c.name} | {c.products} | {c.variants} | {c.prices.count} | {number(c.prices.mean)} | {number(c.prices.median)} |"
        for c in report.categories
    )
    figure_lines = (
        "\n".join(
            f"![{caption}]({stem}.png)\n"
            for stem, caption in (
                ("categories", "Cobertura del catálogo"),
                ("prices", "Distribución de precios simulados"),
                ("missingness", "Información no disponible"),
                ("commerce", "Estados comerciales simulados"),
                ("lengths", "Tamaño de documentos y fragmentos"),
            )
        )
        if charts
        else "No se generaron gráficos en esta ejecución (--no-charts)."
    )
    content = f"""# Exploración del conjunto de datos de Nexo Demo

Este análisis describe la revisión `{report.catalog_revision}` del catálogo de demostración. Los productos, atributos, precios y existencias son sintéticos; estas cifras no describen una tienda ni una muestra de clientes reales. No se invocaron modelos ni se abrieron casos de evaluación reservados.

El reloj comercial declarado es **{report.evaluated_at.isoformat()}**. La vigencia de precios y existencias se calcula en ese instante de simulación, no en la fecha de lectura del informe. La procedencia de cada entrada está identificada por SHA256 en `summary.json`.

## Resultados descriptivos

Se analizaron {report.counts["categories"]} categorías, {report.counts["products"]} productos base, {report.counts["variants"]} variantes, {report.counts["commercial_records"]} registros comerciales, {report.counts["sources"]} fuentes y {report.counts["chunks"]} fragmentos.

| Categoría | Productos | Variantes | Precios vigentes | Media COP | Mediana COP |
| --- | ---: | ---: | ---: | ---: | ---: |
{coverage_rows}

Hay {price.count} precios vigentes simulados utilizables. Su media global es {number(price.mean)} {report.currency}, mediana {number(price.median)}, mínimo {number(price.minimum)}, máximo {number(price.maximum)} y desviación estándar muestral {number(price.sample_sd)}. Los {price.missing} registros restantes se excluyen de estos cálculos por su estado; nunca se convierten en precio cero. La distribución global reúne categorías con niveles de precio distintos, por lo que la tabla y el gráfico por categoría son necesarios para interpretarla. En estas tablas la coma separa miles y el punto indica decimales; los CSV conservan valores numéricos sin separador de miles.

Los estados de precio son `{report.price_statuses}`. Los estados de existencias son `{report.stock_states}`. Un estado disponible con cantidad desconocida no se transforma en cero unidades; esa cantidad permanece vacía en `commercial.csv`.

Al considerar todas las combinaciones entre producto base y atributo definido en su categoría, se observan {known} valores conocidos, {nulls} valores `null` explícitos y {absent} campos omitidos. Los atributos opcionales omitidos pueden no aplicar al tipo concreto de producto. No se presupone que sean errores ni se inventa información para completarlos. Los atributos de las variantes no se duplican como observaciones técnicas independientes.

La longitud media de los documentos es {number(report.document_lengths.mean)} caracteres y la de los fragmentos {number(report.chunk_lengths.mean)}. Sus medianas son {number(report.document_lengths.median)} y {number(report.chunk_lengths.median)}, respectivamente. Estas longitudes no son conteos de tokens.

## Preparación y tratamiento de datos

1. Se validan los contratos, tipos, unidades, relaciones entre producto y variante, ámbito de las fuentes, hashes y pertenencia literal de los fragmentos. Un defecto de integridad detiene la exportación.
2. Se conserva la distinción entre valor desconocido, campo opcional ausente, precio vencido y artículo agotado. La estadística de precios usa únicamente observaciones vigentes y conocidas al reloj declarado.
3. Los atributos numéricos se resumen por categoría, clave y unidad a nivel de producto base. No se mezclan centímetros, gramos, vatios ni otras magnitudes en una misma media.
4. Se emplean cuartiles con interpolación lineal sobre la posición `(n-1) p` y desviación estándar muestral para `n >= 2`. Para muestras vacías o insuficientes se conserva `null`, sin inventar ceros.
5. Se marcan posibles atípicos fuera de `[Q1 - 1.5 IQR, Q3 + 1.5 IQR]` únicamente cuando `n >= 4`, por categoría y variable. Hay {len(report.outliers)} observaciones marcadas en `outliers.csv`. Se conservan todas: un valor extremo puede ser válido y requiere revisión del contexto.
6. No se codifican categorías como números ordinales ni se escalan precios para este resumen descriptivo. La representación semántica y normalización de embeddings pertenecen a la ingesta RAG, no a una transformación de estas variables comerciales.
7. El equipo no entrena un predictor supervisado con estas filas. Por tanto, un reparto aleatorio entrenamiento/prueba del catálogo no sería una evaluación de ese tipo de modelo. El proyecto mantiene casos de ajuste y finales separados para evaluar recuperación y comportamiento del asistente; este análisis no evalúa sus respuestas.

## Gráficos

{figure_lines}

## Reproducción y archivos

Desde la raíz del proyecto, después de instalar el extra `analysis`:

```powershell
.\\.venv\\Scripts\\python.exe -m ragml.analysis --output-dir docs/analysis/nueva-ejecucion
```

El directorio de salida debe ser nuevo. Puede especificarse `--evaluated-at` con una fecha ISO 8601 que incluya zona horaria. `--no-charts` exporta solo datos y tablas cuando Matplotlib no está disponible.

`summary.json` conserva datos, estadísticas, versiones, reloj y huellas de entrada. `categories.csv`, `attributes.csv`, `commercial.csv`, `documents.csv` y `outliers.csv` permiten revisar cada grupo de resultados. Las figuras se guardan en PNG y SVG. Los CSV usan UTF-8 con BOM y conservan vacíos para valores no disponibles; las etiquetas y decimales no deben interpretarse como datos comerciales reales.

La distribución equilibrada por categoría es una decisión del generador, no un hallazgo sobre ventas o demanda. La muestra pequeña y sintética impide generalizar estos patrones a mercados reales o afirmar utilidad del asistente para usuarios.
"""
    (output_dir / "README.md").write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--evaluated-at", help="Explicit ISO 8601 reference clock including timezone"
    )
    parser.add_argument(
        "--no-charts", action="store_true", help="Export tables without optional Matplotlib"
    )
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.project_dir)
        root = settings.project_dir
        corpus = read_corpus(
            root, settings.catalog_path, settings.source_manifest, settings.commercial_path
        )
        commercial = CommercialDataset.model_validate_json(
            settings.resolve_path(settings.commercial_path).read_bytes()
        )
        metadata_path = (
            settings.resolve_path(settings.catalog_path).parent / "package-metadata.json"
        )
        if args.evaluated_at:
            evaluated_at = datetime.fromisoformat(args.evaluated_at)
        elif corpus.catalog.profile.data_mode == "demo" and metadata_path.is_file():
            metadata = json.loads(metadata_path.read_bytes())
            if (metadata.get("store_id"), metadata.get("revision"), metadata.get("data_mode")) != (
                corpus.catalog.profile.store_id,
                corpus.catalog.profile.revision,
                "demo",
            ):
                raise ValueError("analysis_demo_clock_scope_mismatch")
            evaluated_at = datetime.fromisoformat(metadata["recommended_test_time"])
        else:
            raise ValueError("analysis_requires_explicit_reference_clock")
        paths = [
            settings.resolve_path(path)
            for path in (settings.catalog_path, settings.commercial_path, settings.source_manifest)
        ]
        if metadata_path.is_file():
            paths.append(metadata_path)
        paths.extend(
            (root / source.locator).resolve() for source in corpus.manifest.sources if source.active
        )
        hashes = {
            path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
            for path in paths
        }
        texts = {
            source.source_id: (root / source.locator).read_bytes().decode("utf-8")
            for source in corpus.manifest.sources
            if source.active
        }
        report = analyze_dataset(
            corpus.catalog,
            commercial,
            corpus.manifest,
            texts,
            evaluated_at=evaluated_at,
            input_sha256=hashes,
        )
        if not args.no_charts:
            import importlib.util

            if importlib.util.find_spec("matplotlib") is None:
                raise ImportError("Install the optional analysis extra to render charts")
        write_tables(report, args.output_dir.resolve())
        if not args.no_charts:
            render_charts(report, corpus.manifest, args.output_dir.resolve())
        write_readme(report, args.output_dir.resolve(), not args.no_charts)
        print(
            json.dumps(
                {
                    "status": "exported",
                    "output_dir": str(args.output_dir.resolve()),
                    "charts": not args.no_charts,
                    "counts": report.counts,
                },
                ensure_ascii=False,
            )
        )
        return 0
    except (OSError, ValueError, KeyError, ImportError) as error:
        print(json.dumps({"status": "failed", "error": type(error).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
