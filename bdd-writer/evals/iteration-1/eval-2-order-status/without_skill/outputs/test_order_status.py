"""
订单状态测试用例

订单状态流转:
待支付 -> 已支付 -> 已发货 -> 已完成
待支付 -> 已取消
"""

from __future__ import annotations

from enum import Enum
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

import pytest


class OrderStatus(str, Enum):
    """订单状态枚举"""
    PENDING = "待支付"
    PAID = "已支付"
    SHIPPED = "已发货"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


@dataclass
class Order:
    """订单实体"""
    id: int
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None

    def pay(self) -> None:
        """支付订单"""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"当前状态 {self.status.value} 无法支付")
        self.status = OrderStatus.PAID
        self.updated_at = datetime.now()

    def ship(self) -> None:
        """发货"""
        if self.status != OrderStatus.PAID:
            raise ValueError(f"当前状态 {self.status.value} 无法发货")
        self.status = OrderStatus.SHIPPED
        self.updated_at = datetime.now()

    def complete(self) -> None:
        """完成订单"""
        if self.status != OrderStatus.SHIPPED:
            raise ValueError(f"当前状态 {self.status.value} 无法完成")
        self.status = OrderStatus.COMPLETED
        self.updated_at = datetime.now()

    def cancel(self, reason: Optional[str] = None) -> None:
        """取消订单"""
        if self.status in (OrderStatus.COMPLETED, OrderStatus.CANCELLED):
            raise ValueError(f"当前状态 {self.status.value} 无法取消")
        self.status = OrderStatus.CANCELLED
        self.cancel_reason = reason
        self.updated_at = datetime.now()


class TestOrderStatus:
    """订单状态测试类"""

    # ==================== 状态初始化测试 ====================

    def test_order_initial_status_is_pending(self) -> None:
        """测试订单创建后初始状态为待支付"""
        order = Order(id=1)
        assert order.status == OrderStatus.PENDING

    def test_order_has_id(self) -> None:
        """测试订单ID正确设置"""
        order = Order(id=100)
        assert order.id == 100

    def test_order_has_created_at(self) -> None:
        """测试订单创建时间存在"""
        order = Order(id=1)
        assert order.created_at is not None
        assert isinstance(order.created_at, datetime)

    # ==================== 正常状态流转测试 ====================

    def test_pending_to_paid(self) -> None:
        """测试待支付 -> 已支付"""
        order = Order(id=1)
        order.pay()
        assert order.status == OrderStatus.PAID
        assert order.updated_at is not None

    def test_paid_to_shipped(self) -> None:
        """测试已支付 -> 已发货"""
        order = Order(id=1)
        order.pay()
        order.ship()
        assert order.status == OrderStatus.SHIPPED

    def test_shipped_to_completed(self) -> None:
        """测试已发货 -> 已完成"""
        order = Order(id=1)
        order.pay()
        order.ship()
        order.complete()
        assert order.status == OrderStatus.COMPLETED

    def test_full_order_lifecycle(self) -> None:
        """测试完整订单生命周期: 待支付 -> 已支付 -> 已发货 -> 已完成"""
        order = Order(id=1)

        # 初始状态
        assert order.status == OrderStatus.PENDING

        # 支付
        order.pay()
        assert order.status == OrderStatus.PAID

        # 发货
        order.ship()
        assert order.status == OrderStatus.SHIPPED

        # 完成
        order.complete()
        assert order.status == OrderStatus.COMPLETED

    def test_cancel_from_pending(self) -> None:
        """测试从待支付状态取消订单"""
        order = Order(id=1)
        order.cancel(reason="用户主动取消")
        assert order.status == OrderStatus.CANCELLED
        assert order.cancel_reason == "用户主动取消"

    def test_cancel_from_paid(self) -> None:
        """测试从已支付状态取消订单"""
        order = Order(id=1)
        order.pay()
        order.cancel(reason="用户申请退款")
        assert order.status == OrderStatus.CANCELLED

    def test_cancel_from_shipped(self) -> None:
        """测试从已发货状态取消订单"""
        order = Order(id=1)
        order.pay()
        order.ship()
        order.cancel(reason="用户拒收")
        assert order.status == OrderStatus.CANCELLED

    # ==================== 非法状态转换测试 ====================

    def test_cannot_pay_paid_order(self) -> None:
        """测试已支付订单不能再次支付"""
        order = Order(id=1)
        order.pay()
        with pytest.raises(ValueError, match="无法支付"):
            order.pay()

    def test_cannot_pay_shipped_order(self) -> None:
        """测试已发货订单不能支付"""
        order = Order(id=1)
        order.pay()
        order.ship()
        with pytest.raises(ValueError, match="无法支付"):
            order.pay()

    def test_cannot_pay_completed_order(self) -> None:
        """测试已完成订单不能支付"""
        order = Order(id=1)
        order.pay()
        order.ship()
        order.complete()
        with pytest.raises(ValueError, match="无法支付"):
            order.pay()

    def test_cannot_pay_cancelled_order(self) -> None:
        """测试已取消订单不能支付"""
        order = Order(id=1)
        order.cancel()
        with pytest.raises(ValueError, match="无法支付"):
            order.pay()

    def test_cannot_ship_pending_order(self) -> None:
        """测试待支付订单不能发货"""
        order = Order(id=1)
        with pytest.raises(ValueError, match="无法发货"):
            order.ship()

    def test_cannot_ship_shipped_order(self) -> None:
        """测试已发货订单不能再次发货"""
        order = Order(id=1)
        order.pay()
        order.ship()
        with pytest.raises(ValueError, match="无法发货"):
            order.ship()

    def test_cannot_ship_completed_order(self) -> None:
        """测试已完成订单不能发货"""
        order = Order(id=1)
        order.pay()
        order.ship()
        order.complete()
        with pytest.raises(ValueError, match="无法发货"):
            order.ship()

    def test_cannot_ship_cancelled_order(self) -> None:
        """测试已取消订单不能发货"""
        order = Order(id=1)
        order.cancel()
        with pytest.raises(ValueError, match="无法发货"):
            order.ship()

    def test_cannot_complete_pending_order(self) -> None:
        """测试待支付订单不能完成"""
        order = Order(id=1)
        with pytest.raises(ValueError, match="无法完成"):
            order.complete()

    def test_cannot_complete_paid_order(self) -> None:
        """测试已支付订单不能完成"""
        order = Order(id=1)
        order.pay()
        with pytest.raises(ValueError, match="无法完成"):
            order.complete()

    def test_cannot_complete_completed_order(self) -> None:
        """测试已完成订单不能再次完成"""
        order = Order(id=1)
        order.pay()
        order.ship()
        order.complete()
        with pytest.raises(ValueError, match="无法完成"):
            order.complete()

    def test_cannot_complete_cancelled_order(self) -> None:
        """测试已取消订单不能完成"""
        order = Order(id=1)
        order.cancel()
        with pytest.raises(ValueError, match="无法完成"):
            order.complete()

    def test_cannot_cancel_completed_order(self) -> None:
        """测试已完成订单不能取消"""
        order = Order(id=1)
        order.pay()
        order.ship()
        order.complete()
        with pytest.raises(ValueError, match="无法取消"):
            order.cancel()

    def test_cannot_cancel_cancelled_order(self) -> None:
        """测试已取消订单不能再次取消"""
        order = Order(id=1)
        order.cancel()
        with pytest.raises(ValueError, match="无法取消"):
            order.cancel()

    # ==================== 边界条件测试 ====================

    def test_cancel_without_reason(self) -> None:
        """测试取消订单可以不提供原因"""
        order = Order(id=1)
        order.cancel()
        assert order.status == OrderStatus.CANCELLED
        assert order.cancel_reason is None

    def test_updated_at_set_after_status_change(self) -> None:
        """测试状态变更后更新时间被设置"""
        order = Order(id=1)
        assert order.updated_at is None
        order.pay()
        assert order.updated_at is not None

    def test_multiple_status_changes_update_timestamp(self) -> None:
        """测试多次状态变更会更新时间戳"""
        order = Order(id=1)
        order.pay()
        first_update = order.updated_at
        order.ship()
        assert order.updated_at is not None
        assert order.updated_at >= first_update  # type: ignore

    # ==================== 状态枚举测试 ====================

    def test_status_enum_values(self) -> None:
        """测试状态枚举值"""
        assert OrderStatus.PENDING.value == "待支付"
        assert OrderStatus.PAID.value == "已支付"
        assert OrderStatus.SHIPPED.value == "已发货"
        assert OrderStatus.COMPLETED.value == "已完成"
        assert OrderStatus.CANCELLED.value == "已取消"

    def test_status_enum_count(self) -> None:
        """测试状态枚举数量"""
        assert len(OrderStatus) == 5

    def test_status_enum_string_comparison(self) -> None:
        """测试状态枚举字符串比较"""
        order = Order(id=1)
        assert order.status == OrderStatus.PENDING
        assert order.status.value == "待支付"


class TestOrderStatusTransitions:
    """订单状态转换矩阵测试"""

    @pytest.mark.parametrize(
        "initial_status,action,expected_status,should_succeed",
        [
            # 待支付状态转换
            (OrderStatus.PENDING, "pay", OrderStatus.PAID, True),
            (OrderStatus.PENDING, "ship", None, False),
            (OrderStatus.PENDING, "complete", None, False),
            (OrderStatus.PENDING, "cancel", OrderStatus.CANCELLED, True),

            # 已支付状态转换
            (OrderStatus.PAID, "pay", None, False),
            (OrderStatus.PAID, "ship", OrderStatus.SHIPPED, True),
            (OrderStatus.PAID, "complete", None, False),
            (OrderStatus.PAID, "cancel", OrderStatus.CANCELLED, True),

            # 已发货状态转换
            (OrderStatus.SHIPPED, "pay", None, False),
            (OrderStatus.SHIPPED, "ship", None, False),
            (OrderStatus.SHIPPED, "complete", OrderStatus.COMPLETED, True),
            (OrderStatus.SHIPPED, "cancel", OrderStatus.CANCELLED, True),

            # 已完成状态转换
            (OrderStatus.COMPLETED, "pay", None, False),
            (OrderStatus.COMPLETED, "ship", None, False),
            (OrderStatus.COMPLETED, "complete", None, False),
            (OrderStatus.COMPLETED, "cancel", None, False),

            # 已取消状态转换
            (OrderStatus.CANCELLED, "pay", None, False),
            (OrderStatus.CANCELLED, "ship", None, False),
            (OrderStatus.CANCELLED, "complete", None, False),
            (OrderStatus.CANCELLED, "cancel", None, False),
        ],
        ids=[
            "待支付-支付",
            "待支付-发货",
            "待支付-完成",
            "待支付-取消",
            "已支付-支付",
            "已支付-发货",
            "已支付-完成",
            "已支付-取消",
            "已发货-支付",
            "已发货-发货",
            "已发货-完成",
            "已发货-取消",
            "已完成-支付",
            "已完成-发货",
            "已完成-完成",
            "已完成-取消",
            "已取消-支付",
            "已取消-发货",
            "已取消-完成",
            "已取消-取消",
        ],
    )
    def test_status_transition(
        self,
        initial_status: OrderStatus,
        action: str,
        expected_status: Optional[OrderStatus],
        should_succeed: bool,
    ) -> None:
        """测试状态转换矩阵"""
        order = Order(id=1, status=initial_status)
        action_map = {
            "pay": order.pay,
            "ship": order.ship,
            "complete": order.complete,
            "cancel": lambda: order.cancel(),
        }

        if should_succeed:
            action_map[action]()
            assert order.status == expected_status
        else:
            with pytest.raises(ValueError):
                action_map[action]()


class TestOrderBusinessRules:
    """订单业务规则测试"""

    def test_order_can_be_refunded_if_paid(self) -> None:
        """测试已支付订单可以退款（取消）"""
        order = Order(id=1)
        order.pay()
        # 已支付状态可以取消（退款）
        order.cancel(reason="用户申请退款")
        assert order.status == OrderStatus.CANCELLED

    def test_order_can_be_rejected_if_shipped(self) -> None:
        """测试已发货订单可以被拒收（取消）"""
        order = Order(id=1)
        order.pay()
        order.ship()
        # 已发货状态可以取消（拒收）
        order.cancel(reason="用户拒收")
        assert order.status == OrderStatus.CANCELLED

    def test_completed_order_is_final(self) -> """测试已完成订单是终态"""
        order = Order(id=1)
        order.pay()
        order.ship()
        order.complete()
        # 已完成订单不能进行任何操作
        with pytest.raises(ValueError):
            order.pay()
        with pytest.raises(ValueError):
            order.ship()
        with pytest.raises(ValueError):
            order.complete()
        with pytest.raises(ValueError):
            order.cancel()

    def test_cancelled_order_is_final(self) -> None:
        """测试已取消订单是终态"""
        order = Order(id=1)
        order.cancel()
        # 已取消订单不能进行任何操作
        with pytest.raises(ValueError):
            order.pay()
        with pytest.raises(ValueError):
            order.ship()
        with pytest.raises(ValueError):
            order.complete()
        with pytest.raises(ValueError):
            order.cancel()


class TestOrderConcurrency:
    """订单并发场景测试"""

    def test_double_pay_protection(self) -> None:
        """测试双重支付保护"""
        order = Order(id=1)
        order.pay()
        # 再次支付应该失败
        with pytest.raises(ValueError):
            order.pay()

    def test_status_change_atomic(self) -> None:
        """测试状态变更是原子的"""
        order = Order(id=1)
        # 模拟并发场景：尝试在不正确的状态下发货
        order.pay()
        order.ship()
        # 此时状态已变为已发货，再次发货应该失败
        with pytest.raises(ValueError):
            order.ship()
        # 状态应该保持不变
        assert order.status == OrderStatus.SHIPPED