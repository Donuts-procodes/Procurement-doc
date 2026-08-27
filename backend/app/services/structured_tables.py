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
    computed: list[ComputedMilestone] = []

    for m in data.milestones:
        pct = Decimal(str(m.percentage)) / Decimal("100")
        amt = (val * pct).quantize(Decimal("0.01"))
        computed.append(
            ComputedMilestone(
                milestone_number=m.milestone_number,
                description=m.description,
                percentage=m.percentage,
                amount=amt,
                due_condition=m.due_condition,
            )
        )

    return PaymentScheduleSummary(
        total_contract_value=val,
        milestones=computed,
    )
