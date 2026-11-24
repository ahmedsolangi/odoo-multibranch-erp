"""Educational Odoo 19 ORM example for a database with the Inventory app.

Call from an Odoo environment with warehouse and stock read access. The
function reads standard records and keeps the caller's active company scope.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from odoo.api import Environment


def warehouse_availability(
    env: Environment, warehouse_id: int
) -> dict[int, dict[str, float]]:
    """Return quantity summaries keyed by product variant ID.

    Values are in each variant's own unit of measure. Products with no
    matching quants have no entry. Shared and transit locations are excluded.
    """
    warehouse = env["stock.warehouse"].search([
        ("id", "=", warehouse_id),
        ("company_id", "in", env.companies.ids),
    ], limit=1)
    if not warehouse or not warehouse.lot_stock_id:
        raise ValueError("Choose a visible warehouse with a stock location.")

    rows = env["stock.quant"]._read_group(
        [
            ("company_id", "=", warehouse.company_id.id),
            ("location_id", "child_of", warehouse.lot_stock_id.id),
            ("location_id.usage", "=", "internal"),
        ],
        groupby=["product_id"],
        aggregates=["quantity:sum", "reserved_quantity:sum"],
    )
    result = {}
    for product, on_hand, reserved in rows:
        result[product.id] = {
            "on_hand": product.uom_id.round(on_hand),
            "reserved": product.uom_id.round(reserved),
            "available": product.uom_id.round(on_hand - reserved),
        }
    return result
