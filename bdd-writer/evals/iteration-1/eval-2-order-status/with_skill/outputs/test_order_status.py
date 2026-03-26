"""
订单状态测试

业务规则:
- BR-1: 订单状态枚举 - pending_payment/paid/shipped/completed/cancelled
- BR-2: 订单初始状态 - 新建订单必须为 pending_payment
- BR-3: 状态转换规则 - 支付 - 仅 pending_payment 可支付
- BR-4: 状态转换规则 - 发货 - 仅 paid 可发货
- BR-5: 状态转换规则 - 完成确认 - 仅 shipped 可完成
- BR-6: 状态转换规则 - 取消 - 仅 pending_payment 可取消
- BR-7: 终态不可变 - completed/cancelled 不能再变更
- BR-8: 状态查询 - 支持按状态筛选和查询单个订单状态

测试场景:
- S1-S5: 正向状态转换场景
- S6-S9: 非法状态转换场景
- S10: 非法状态值场景
- S11-S12: 查询场景
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass


class OrderStatus(str, Enum):
    """订单状态枚举"""

    PENDING_PAYMENT = "pending_payment"  # 待支付
    PAID = "paid"  # 已支付
    SHIPPED = "shipped"  # 已发货
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class OrderStatusError(Exception):
    """订单状态错误"""

    pass


class Order:
    """订单实体"""

    def __init__(self, order_id: int, status: OrderStatus | None = None) -> None:
        if status is not None and status not in OrderStatus:
            raise OrderStatusError(f"非法订单状态: {status}")
        self.order_id = order_id
        # BR-2: 新建订单初始状态必须为 pending_payment
        self._status = status if status is not None else OrderStatus.PENDING_PAYMENT

    @property
    def status(self) -> OrderStatus:
        """获取当前状态"""
        return self._status

    def pay(self) -> None:
        """
        支付操作
        BR-3: 仅待支付状态可支付
        """
        if self._status != OrderStatus.PENDING_PAYMENT:
            raise OrderStatusError(f"当前状态 [{self._status.value}] 不允许支付操作")
        self._status = OrderStatus.PAID

    def ship(self) -> None:
        """
        发货操作
        BR-4: 仅已支付状态可发货
        """
        if self._status != OrderStatus.PAID:
            raise OrderStatusError(f"当前状态 [{self._status.value}] 不允许发货操作")
        self._status = OrderStatus.SHIPPED

    def complete(self) -> None:
        """
        确认收货操作
        BR-5: 仅已发货状态可确认完成
        """
        if self._status != OrderStatus.SHIPPED:
            raise OrderStatusError(f"当前状态 [{self._status.value}] 不允许完成确认操作")
        self._status = OrderStatus.COMPLETED

    def cancel(self) -> None:
        """
        取消订单操作
        BR-6: 仅待支付状态可取消
        """
        if self._status != OrderStatus.PENDING_PAYMENT:
            raise OrderStatusError(f"当前状态 [{self._status.value}] 不允许取消操作")
        self._status = OrderStatus.CANCELLED

    def is_terminal(self) -> bool:
        """检查是否为终态"""
        return self._status in (OrderStatus.COMPLETED, OrderStatus.CANCELLED)


class OrderRepository:
    """订单仓储（模拟）"""

    def __init__(self) -> None:
        self._orders: dict[int, Order] = {}

    def save(self, order: Order) -> None:
        """保存订单"""
        self._orders[order.order_id] = order

    def find_by_id(self, order_id: int) -> Order | None:
        """根据ID查询订单"""
        return self._orders.get(order_id)

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        """根据状态筛选订单"""
        return [order for order in self._orders.values() if order.status == status]


# ============================================================
# BR-2: 订单初始状态测试
# ============================================================


class TestOrderCreation:
    """订单创建测试 - 验证 BR-2"""

    def test_new_order_has_pending_payment_status(self) -> None:
        """S1: 新建订单初始状态为待支付 (BR-2)"""
        # Arrange & Act
        order = Order(order_id=1)

        # Assert
        assert order.status == OrderStatus.PENDING_PAYMENT
        assert order.status.value == "pending_payment"

    def test_create_order_with_explicit_pending_payment_status(self) -> None:
        """显式指定待支付状态创建订单 (BR-2)"""
        # Arrange & Act
        order = Order(order_id=1, status=OrderStatus.PENDING_PAYMENT)

        # Assert
        assert order.status == OrderStatus.PENDING_PAYMENT

    def test_create_order_with_invalid_status_raises_error(self) -> None:
        """S10: 非法状态值创建订单失败 (BR-1)"""
        # Arrange
        invalid_status = "invalid_status"  # type: ignore

        # Act & Assert
        with pytest.raises(OrderStatusError, match="非法订单状态"):
            Order(order_id=1, status=invalid_status)  # type: ignore


# ============================================================
# BR-3: 状态转换规则 - 支付测试
# ============================================================


class TestPaymentOperation:
    """支付操作测试 - 验证 BR-3"""

    def test_pending_payment_order_can_be_paid(self) -> None:
        """S2: 待支付订单支付成功后变为已支付 (BR-3)"""
        # Arrange
        order = Order(order_id=1)

        # Act
        order.pay()

        # Assert
        assert order.status == OrderStatus.PAID

    @pytest.mark.parametrize(
        "initial_status,operation",
        [
            (OrderStatus.PAID, "pay"),
            (OrderStatus.SHIPPED, "pay"),
            (OrderStatus.COMPLETED, "pay"),
            (OrderStatus.CANCELLED, "pay"),
        ],
    )
    def test_non_pending_payment_order_cannot_be_paid(
        self, initial_status: OrderStatus, operation: str
    ) -> None:
        """S7: 非待支付状态执行支付操作失败 (BR-3)"""
        # Arrange
        order = Order(order_id=1, status=initial_status)

        # Act & Assert
        with pytest.raises(OrderStatusError, match="不允许支付操作"):
            order.pay()
        assert order.status == initial_status


# ============================================================
# BR-4: 状态转换规则 - 发货测试
# ============================================================


class TestShipOperation:
    """发货操作测试 - 验证 BR-4"""

    def test_paid_order_can_be_shipped(self) -> None:
        """S4: 已支付订单发货后变为已发货 (BR-4)"""
        # Arrange
        order = Order(order_id=1, status=OrderStatus.PAID)

        # Act
        order.ship()

        # Assert
        assert order.status == OrderStatus.SHIPPED

    @pytest.mark.parametrize(
        "initial_status",
        [
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.SHIPPED,
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
        ],
    )
    def test_non_paid_order_cannot_be_shipped(self, initial_status: OrderStatus) -> None:
        """非已支付状态执行发货操作失败 (BR-4)"""
        # Arrange
        order = Order(order_id=1, status=initial_status)

        # Act & Assert
        with pytest.raises(OrderStatusError, match="不允许发货操作"):
            order.ship()
        assert order.status == initial_status


# ============================================================
# BR-5: 状态转换规则 - 完成确认测试
# ============================================================


class TestCompleteOperation:
    """完成确认操作测试 - 验证 BR-5"""

    def test_shipped_order_can_be_completed(self) -> None:
        """S5: 已发货订单确认收货后变为已完成 (BR-5)"""
        # Arrange
        order = Order(order_id=1, status=OrderStatus.SHIPPED)

        # Act
        order.complete()

        # Assert
        assert order.status == OrderStatus.COMPLETED

    @pytest.mark.parametrize(
        "initial_status",
        [
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.PAID,
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
        ],
    )
    def test_non_shipped_order_cannot_be_completed(self, initial_status: OrderStatus) -> None:
        """非已发货状态执行完成确认操作失败 (BR-5)"""
        # Arrange
        order = Order(order_id=1, status=initial_status)

        # Act & Assert
        with pytest.raises(OrderStatusError, match="不允许完成确认操作"):
            order.complete()
        assert order.status == initial_status


# ============================================================
# BR-6: 状态转换规则 - 取消测试
# ============================================================


class TestCancelOperation:
    """取消操作测试 - 验证 BR-6"""

    def test_pending_payment_order_can_be_cancelled(self) -> None:
        """S3: 待支付订单取消后变为已取消 (BR-6)"""
        # Arrange
        order = Order(order_id=1)

        # Act
        order.cancel()

        # Assert
        assert order.status == OrderStatus.CANCELLED

    @pytest.mark.parametrize(
        "initial_status",
        [
            OrderStatus.PAID,
            OrderStatus.SHIPPED,
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
        ],
    )
    def test_non_pending_payment_order_cannot_be_cancelled(
        self, initial_status: OrderStatus
    ) -> None:
        """S6: 非待支付状态执行取消操作失败 (BR-6)"""
        # Arrange
        order = Order(order_id=1, status=initial_status)

        # Act & Assert
        with pytest.raises(OrderStatusError, match="不允许取消操作"):
            order.cancel()
        assert order.status == initial_status


# ============================================================
# BR-7: 终态不可变测试
# ============================================================


class TestTerminalState:
    """终态测试 - 验证 BR-7"""

    def test_completed_is_terminal_state(self) -> None:
        """已完成是终态 (BR-7)"""
        order = Order(order_id=1, status=OrderStatus.COMPLETED)
        assert order.is_terminal() is True

    def test_cancelled_is_terminal_state(self) -> None:
        """已取消是终态 (BR-7)"""
        order = Order(order_id=1, status=OrderStatus.CANCELLED)
        assert order.is_terminal() is True

    @pytest.mark.parametrize("initial_status", [OrderStatus.COMPLETED, OrderStatus.CANCELLED])
    @pytest.mark.parametrize(
        "operation,expected_error",
        [
            ("pay", "不允许支付操作"),
            ("ship", "不允许发货操作"),
            ("complete", "不允许完成确认操作"),
            ("cancel", "不允许取消操作"),
        ],
    )
    def test_terminal_state_cannot_be_changed(
        self, initial_status: OrderStatus, operation: str, expected_error: str
    ) -> None:
        """S8/S9: 终态订单不能执行任何状态变更操作 (BR-7)"""
        # Arrange
        order = Order(order_id=1, status=initial_status)

        # Act & Assert
        with pytest.raises(OrderStatusError, match=expected_error):
            getattr(order, operation)()
        assert order.status == initial_status


# ============================================================
# BR-8: 状态查询测试
# ============================================================


class TestOrderQuery:
    """订单查询测试 - 验证 BR-8"""

    def test_query_order_status(self) -> None:
        """S12: 查询订单当前状态 (BR-8)"""
        # Arrange
        repo = OrderRepository()
        order = Order(order_id=1, status=OrderStatus.PAID)
        repo.save(order)

        # Act
        found_order = repo.find_by_id(1)

        # Assert
        assert found_order is not None
        assert found_order.status == OrderStatus.PAID

    def test_filter_orders_by_status(self) -> None:
        """S11: 按状态筛选订单列表 (BR-8)"""
        # Arrange
        repo = OrderRepository()
        repo.save(Order(order_id=1, status=OrderStatus.PAID))
        repo.save(Order(order_id=2, status=OrderStatus.PENDING_PAYMENT))
        repo.save(Order(order_id=3, status=OrderStatus.PAID))
        repo.save(Order(order_id=4, status=OrderStatus.COMPLETED))

        # Act
        paid_orders = repo.find_by_status(OrderStatus.PAID)

        # Assert
        assert len(paid_orders) == 2
        assert all(order.status == OrderStatus.PAID for order in paid_orders)
        assert {order.order_id for order in paid_orders} == {1, 3}

    def test_query_non_existent_order(self) -> None:
        """查询不存在的订单返回 None (BR-8)"""
        # Arrange
        repo = OrderRepository()

        # Act
        found_order = repo.find_by_id(999)

        # Assert
        assert found_order is None


# ============================================================
# 完整状态转换流程测试
# ============================================================


class TestOrderStatusFlow:
    """订单状态完整流程测试"""

    def test_complete_order_flow(self) -> None:
        """完整订单流程: 待支付 -> 已支付 -> 已发货 -> 已完成"""
        # Arrange
        order = Order(order_id=1)

        # Assert initial state
        assert order.status == OrderStatus.PENDING_PAYMENT

        # Act: 支付
        order.pay()
        assert order.status == OrderStatus.PAID

        # Act: 发货
        order.ship()
        assert order.status == OrderStatus.SHIPPED

        # Act: 确认收货
        order.complete()
        assert order.status == OrderStatus.COMPLETED

        # Assert: 终态
        assert order.is_terminal() is True

    def test_cancel_order_flow(self) -> None:
        """取消订单流程: 待支付 -> 已取消"""
        # Arrange
        order = Order(order_id=1)

        # Assert initial state
        assert order.status == OrderStatus.PENDING_PAYMENT

        # Act: 取消
        order.cancel()
        assert order.status == OrderStatus.CANCELLED

        # Assert: 终态
        assert order.is_terminal() is True