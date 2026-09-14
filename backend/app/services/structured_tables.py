from __future__ import annotations

from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field


class LineItemInput(BaseModel):
    sku: str = Field(description="SKU or product identifier code")
    description: str = Field(description="Item name or detailed product description")
    quantity: int = Field(ge=1, description="Number of units ordered")
    unit_price: float = Field(ge=0, description="Unit price per item")


class LineItemTableData(BaseModel):
    items: list[LineItemInput] = Field(default_factory=list)
    tax_rate_percent: float = Field(default=10.0, description="Applicable tax percentage")


class ComputedLineItem(BaseModel):
    sku: str
    description: str
    quantity: int
    unit_price: Decimal
    total: Decimal


class LineItemSummary(BaseModel):
    items: list[ComputedLineItem]
    subtotal: Decimal
    tax: Decimal
    grand_total: Decimal


def compute_line_items(data: LineItemTableData) -> LineItemSummary:
    computed_items: list[ComputedLineItem] = []
    subtotal = Decimal("0.00")

    for item in data.items:
        qty = Decimal(str(item.quantity))
        u_price = Decimal(f"{item.unit_price:.2f}")
        item_total = (qty * u_price).quantize(Decimal("0.01"))
        subtotal += item_total
        computed_items.append(
            ComputedLineItem(
                sku=item.sku,
                description=item.description,
                quantity=item.quantity,
                unit_price=u_price,
                total=item_total,
            )
        )

    tax_rate = Decimal(str(data.tax_rate_percent)) / Decimal("100")
    tax = (subtotal * tax_rate).quantize(Decimal("0.01"))
    grand_total = subtotal + tax

    return LineItemSummary(
        items=computed_items,
        subtotal=subtotal,
        tax=tax,
        grand_total=grand_total,
    )


class PaymentMilestoneInput(BaseModel):
    milestone_number: int = Field(description="Milestone sequence number")
    description: str = Field(description="Milestone deliverable or phase description")
    percentage: float = Field(description="Percentage of total payment allocated to milestone")
    due_condition: str = Field(description="Completion trigger or due date condition")


class PaymentScheduleData(BaseModel):
    total_contract_value: float = Field(default=50000.0, description="Total project or contract value")
    milestones: list[PaymentMilestoneInput] = Field(default_factory=list)


class ComputedMilestone(BaseModel):
    milestone_number: int
    description: str
    percentage: float
    amount: Decimal
    due_condition: str


class PaymentScheduleSummary(BaseModel):
    total_contract_value: Decimal
    milestones: list[ComputedMilestone]


def compute_payment_schedule(data: PaymentScheduleData) -> PaymentScheduleSummary:
    val = Decimal(f"{data.total_contract_value:.2f}")
    if not data.milestones:
        return PaymentScheduleSummary(total_contract_value=val, milestones=[])

    raw_percentages = [Decimal(str(m.percentage)) for m in data.milestones]
    total_pct = sum(raw_percentages)

    # Normalize percentages to 100% if LLM output does not sum to 100%
    normalized_percentages: list[float] = []
    if total_pct > Decimal("0") and total_pct != Decimal("100"):
        running_pct = Decimal("0")
        for i, raw_pct in enumerate(raw_percentages):
            if i == len(raw_percentages) - 1:
                final_pct = Decimal("100.00") - running_pct
                normalized_percentages.append(float(final_pct))
            else:
                norm = ((raw_pct / total_pct) * Decimal("100")).quantize(Decimal("0.01"))
                running_pct += norm
                normalized_percentages.append(float(norm))
    else:
        normalized_percentages = [float(p) for p in raw_percentages]

    computed: list[ComputedMilestone] = []
    allocated_total = Decimal("0.00")

    for i, m in enumerate(data.milestones):
        pct_float = normalized_percentages[i]
        pct_dec = Decimal(str(pct_float)) / Decimal("100")

        if i == len(data.milestones) - 1:
            amt = val - allocated_total
        else:
            amt = (val * pct_dec).quantize(Decimal("0.01"))
            allocated_total += amt

        computed.append(
            ComputedMilestone(
                milestone_number=m.milestone_number,
                description=m.description,
                percentage=pct_float,
                amount=amt,
                due_condition=m.due_condition,
            )
        )

    return PaymentScheduleSummary(
        total_contract_value=val,
        milestones=computed,
    )
