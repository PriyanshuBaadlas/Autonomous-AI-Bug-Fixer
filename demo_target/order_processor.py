"""
Order Processing and Pricing Engine for E-Commerce Platform.
Handles tiered customer discounts, promotional coupon codes,
jurisdiction-based sales tax, and shipping fee calculations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict


class CustomerTier(str, Enum):
    STANDARD = "standard"
    VIP = "vip"
    PLATINUM = "platinum"


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


@dataclass
class OrderItem:
    item_id: str
    name: str
    price: float
    quantity: int

    def __post_init__(self):
        if self.price < 0:
            raise ValueError(f"Price cannot be negative: {self.price}")
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be greater than zero: {self.quantity}")

    @property
    def total_price(self) -> float:
        return round(self.price * self.quantity, 2)


@dataclass
class Coupon:
    code: str
    discount_type: DiscountType
    value: float
    min_order_amount: float = 0.0


@dataclass
class Order:
    order_id: str
    customer_id: str
    customer_tier: CustomerTier
    items: List[OrderItem] = field(default_factory=list)
    coupon: Optional[Coupon] = None
    shipping_state: str = "CA"


@dataclass
class OrderInvoice:
    order_id: str
    subtotal: float
    tier_discount: float
    coupon_discount: float
    total_discount: float
    taxable_amount: float
    tax: float
    shipping_fee: float
    final_total: float


class OrderProcessor:
    """Processes customer orders, applying discounts, tax, and shipping."""

    STATE_TAX_RATES: Dict[str, float] = {
        "CA": 0.0825,   # 8.25%
        "NY": 0.08875,  # 8.875%
        "TX": 0.0625,   # 6.25%
        "DEFAULT": 0.05  # 5.0%
    }

    TIER_DISCOUNT_RATES: Dict[CustomerTier, float] = {
        CustomerTier.STANDARD: 0.0,
        CustomerTier.VIP: 0.10,       # 10% discount
        CustomerTier.PLATINUM: 0.20,  # 20% discount
    }

    SHIPPING_FLAT_RATE: float = 10.0
    FREE_SHIPPING_THRESHOLD: float = 100.0

    def calculate_subtotal(self, order: Order) -> float:
        if not order.items:
            raise ValueError("Cannot process order with no items")
        subtotal = sum(item.total_price for item in order.items)
        return round(subtotal, 2)

    def calculate_tier_discount(self, tier: CustomerTier, subtotal: float) -> float:
        rate = self.TIER_DISCOUNT_RATES.get(tier, 0.0)
        return round(subtotal * rate, 2)

    def calculate_coupon_discount(self, coupon: Optional[Coupon], current_subtotal: float) -> float:
        if not coupon:
            return 0.0
        if current_subtotal < coupon.min_order_amount:
            return 0.0

        if coupon.discount_type == DiscountType.PERCENTAGE:
            discount = current_subtotal * (coupon.value / 100.0)
        elif coupon.discount_type == DiscountType.FIXED:
            discount = coupon.value
        else:
            discount = 0.0

        return round(min(discount, current_subtotal), 2)

    def calculate_tax(self, taxable_amount: float, state: str) -> float:
        rate = self.STATE_TAX_RATES.get(state.upper(), self.STATE_TAX_RATES["DEFAULT"])
        return round(taxable_amount * rate, 2)

    def calculate_shipping(self, discounted_amount: float) -> float:
        if discounted_amount >= self.FREE_SHIPPING_THRESHOLD:
            return 0.0
        return self.SHIPPING_FLAT_RATE

    def process_order(self, order: Order) -> OrderInvoice:
        subtotal = self.calculate_subtotal(order)
        tier_discount = self.calculate_tier_discount(order.customer_tier, subtotal)
        
        remaining_after_tier = max(0.0, subtotal - tier_discount)
        coupon_discount = self.calculate_coupon_discount(order.coupon, remaining_after_tier)
        
        total_discount = round(tier_discount + coupon_discount, 2)
        taxable_amount = round(max(0.0, subtotal - total_discount), 2)

        # INTENTIONAL BUG:
        # Sales tax is calculated on gross subtotal instead of taxable_amount!
        # Customers are overcharged on tax when discounts are applied.
        tax = self.calculate_tax(subtotal, order.shipping_state)

        shipping_fee = self.calculate_shipping(taxable_amount)
        final_total = round(taxable_amount + tax + shipping_fee, 2)

        return OrderInvoice(
            order_id=order.order_id,
            subtotal=subtotal,
            tier_discount=tier_discount,
            coupon_discount=coupon_discount,
            total_discount=total_discount,
            taxable_amount=taxable_amount,
            tax=tax,
            shipping_fee=shipping_fee,
            final_total=final_total
        )
