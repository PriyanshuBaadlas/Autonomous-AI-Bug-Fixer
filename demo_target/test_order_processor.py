import pytest
from order_processor import (
    CustomerTier,
    DiscountType,
    OrderItem,
    Coupon,
    Order,
    OrderProcessor
)


@pytest.fixture
def processor():
    return OrderProcessor()


def test_order_subtotal_calculation(processor):
    order = Order(
        order_id="ORD-001",
        customer_id="CUST-1",
        customer_tier=CustomerTier.STANDARD,
        items=[
            OrderItem(item_id="1", name="Keyboard", price=45.0, quantity=2),
            OrderItem(item_id="2", name="Mousepad", price=10.0, quantity=1),
        ]
    )
    assert processor.calculate_subtotal(order) == 100.0


def test_empty_order_raises_value_error(processor):
    order = Order(
        order_id="ORD-002",
        customer_id="CUST-2",
        customer_tier=CustomerTier.STANDARD,
        items=[]
    )
    with pytest.raises(ValueError, match="Cannot process order with no items"):
        processor.process_order(order)


def test_invalid_order_item_price_raises_error():
    with pytest.raises(ValueError, match="Price cannot be negative"):
        OrderItem(item_id="1", name="Defective Item", price=-15.0, quantity=1)


def test_tier_discount_for_vip(processor):
    order = Order(
        order_id="ORD-003",
        customer_id="CUST-3",
        customer_tier=CustomerTier.VIP,
        items=[
            OrderItem(item_id="1", name="Monitor", price=200.0, quantity=1)
        ]
    )
    subtotal = processor.calculate_subtotal(order)
    tier_discount = processor.calculate_tier_discount(order.customer_tier, subtotal)
    assert tier_discount == 20.0  # 10% of 200.0


def test_coupon_fixed_discount_with_min_order(processor):
    coupon = Coupon(
        code="SAVE15",
        discount_type=DiscountType.FIXED,
        value=15.0,
        min_order_amount=50.0
    )
    # Below min order
    assert processor.calculate_coupon_discount(coupon, 40.0) == 0.0
    # Above min order
    assert processor.calculate_coupon_discount(coupon, 80.0) == 15.0


def test_free_shipping_eligibility(processor):
    # Equal to threshold gets free shipping
    assert processor.calculate_shipping(100.0) == 0.0
    # Below threshold incurs flat rate
    assert processor.calculate_shipping(99.99) == 10.0


def test_process_order_tax_and_total_calculation(processor):
    """
    Validates complete invoice calculation including tax on discounted amount.
    Subtotal: $100.00
    VIP Discount (10%): $10.00
    Net Taxable Amount: $90.00
    CA Tax (8.25% on $90.00): $7.43
    Shipping: $10.00 (taxable amount $90.00 < $100.00)
    Final Total: $90.00 + $7.43 + $10.00 = $107.43
    """
    order = Order(
        order_id="ORD-100",
        customer_id="CUST-10",
        customer_tier=CustomerTier.VIP,
        items=[
            OrderItem(item_id="1", name="Wireless Headset", price=50.0, quantity=2)
        ],
        shipping_state="CA"
    )

    invoice = processor.process_order(order)

    assert invoice.subtotal == 100.0
    assert invoice.tier_discount == 10.0
    assert invoice.taxable_amount == 90.0
    # With the bug, tax is 8.25 (calculated on subtotal 100.0) instead of 7.43 (taxable_amount 90.0)
    assert invoice.tax == 7.43
    assert invoice.shipping_fee == 10.0
    assert invoice.final_total == 107.43
