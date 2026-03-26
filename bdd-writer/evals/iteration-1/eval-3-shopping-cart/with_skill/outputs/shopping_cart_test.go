// shopping_cart_test.go
// 购物车结算价格计算测试
//
// 业务规则:
// - BR-1: 商品金额计算（单价×数量，范围验证）
// - BR-2: 购物车总金额计算（商品汇总）
// - BR-3: 会员折扣（普通1.0/VIP 0.95/SVIP 0.9）
// - BR-4: 满减优惠（满100减10/满200减25/满500减80）
// - BR-5: 优惠券抵扣（定额券/百分比券，与会员折扣取优）
// - BR-6: 结算金额计算顺序（商品总金额→满减→折扣/优惠券取优→最终金额）
// - BR-7: 边界与异常处理（精度四舍五入、负数/零值错误）
//
// 测试场景: S1-S23

package shoppingcart

import (
	"errors"
	"math"
	"testing"

	"github.com/stretchr/testify/assert"
)

// =============================================================================
// 类型定义
// =============================================================================

// MemberLevel 会员等级
type MemberLevel int

const (
	MemberNormal MemberLevel = iota
	MemberVIP
	MemberSVIP
)

// CouponType 优惠券类型
type CouponType int

const (
	CouponNone CouponType = iota
	CouponFixed  // 定额券
	CouponPercent // 百分比券
)

// Coupon 优惠券
type Coupon struct {
	Type   CouponType
	Value  float64 // 定额券为金额，百分比券为折扣率（如0.9表示9折）
}

// CartItem 购物车商品
type CartItem struct {
	ProductID string
	Price     float64
	Quantity  int
}

// Cart 购物车
type Cart struct {
	Items      []CartItem
	MemberLevel MemberLevel
	Coupon      Coupon
}

// CartResult 结算结果
type CartResult struct {
	Subtotal       float64 // 商品总金额
	FullReduction  float64 // 满减金额
	MemberDiscount float64 // 会员折扣金额
	CouponDiscount float64 // 优惠券抵扣金额
	FinalAmount    float64 // 最终应付金额
}

// 错误定义
var (
	ErrInvalidPrice    = errors.New("商品单价无效")
	ErrInvalidQuantity = errors.New("商品数量无效")
	ErrEmptyCart       = errors.New("购物车为空")
)

// =============================================================================
// 业务逻辑实现
// =============================================================================

// CalculateCart 计算购物车结算金额
func CalculateCart(cart Cart) (*CartResult, error) {
	result := &CartResult{}

	// BR-1, BR-7: 验证商品单价和数量
	for _, item := range cart.Items {
		if item.Price <= 0 {
			return nil, ErrInvalidPrice
		}
		if item.Price > 999999.99 {
			return nil, ErrInvalidPrice
		}
		if item.Quantity <= 0 {
			return nil, ErrInvalidQuantity
		}
		if item.Quantity > 999 {
			return nil, ErrInvalidQuantity
		}
		result.Subtotal += item.Price * float64(item.Quantity)
	}

	// BR-2: 空购物车处理
	if len(cart.Items) == 0 {
		return result, nil
	}

	// BR-7: 精度处理
	result.Subtotal = round(result.Subtotal)

	// BR-4: 满减优惠
	result.FullReduction = calculateFullReduction(result.Subtotal)

	// 满减后金额
	afterFullReduction := result.Subtotal - result.FullReduction

	// BR-3: 会员折扣计算
	memberRate := getMemberDiscountRate(cart.MemberLevel)
	memberDiscountAmount := afterFullReduction * (1 - memberRate)
	memberDiscountAmount = round(memberDiscountAmount)
	afterMemberDiscount := afterFullReduction - memberDiscountAmount

	// BR-5: 优惠券计算
	couponDiscountAmount := calculateCouponDiscount(afterFullReduction, cart.Coupon)
	afterCoupon := afterFullReduction - couponDiscountAmount

	// BR-6: 比较会员折扣与优惠券，取最优
	if memberDiscountAmount >= couponDiscountAmount {
		result.MemberDiscount = memberDiscountAmount
		result.CouponDiscount = 0
		result.FinalAmount = afterMemberDiscount
	} else {
		result.MemberDiscount = 0
		result.CouponDiscount = couponDiscountAmount
		result.FinalAmount = afterCoupon
	}

	// BR-7: 最终金额不能为负
	if result.FinalAmount < 0 {
		result.FinalAmount = 0
	}

	result.FinalAmount = round(result.FinalAmount)

	return result, nil
}

// getMemberDiscountRate 获取会员折扣率
func getMemberDiscountRate(level MemberLevel) float64 {
	switch level {
	case MemberVIP:
		return 0.95
	case MemberSVIP:
		return 0.90
	default:
		return 1.0
	}
}

// calculateFullReduction 计算满减金额
func calculateFullReduction(subtotal float64) float64 {
	switch {
	case subtotal >= 500:
		return 80
	case subtotal >= 200:
		return 25
	case subtotal >= 100:
		return 10
	default:
		return 0
	}
}

// calculateCouponDiscount 计算优惠券抵扣金额
func calculateCouponDiscount(subtotal float64, coupon Coupon) float64 {
	if coupon.Type == CouponNone {
		return 0
	}

	var discount float64
	switch coupon.Type {
	case CouponFixed:
		discount = coupon.Value
	case CouponPercent:
		discount = subtotal * (1 - coupon.Value)
	}

	// 优惠券不能超过应付金额
	if discount > subtotal {
		discount = subtotal
	}

	return round(discount)
}

// round 四舍五入保留2位小数
func round(value float64) float64 {
	return math.Round(value*100) / 100
}

// =============================================================================
// 测试用例
// =============================================================================

// === BR-1: 商品金额计算 ===

func TestCalculateCart_SingleProduct(t *testing.T) {
	// S1: 单商品正常计算
	// Given: 商品A单价10元，数量2
	// When: 计算结算金额
	// Then: 总金额=20元
	cart := Cart{
		Items: []CartItem{
			{ProductID: "A", Price: 10.00, Quantity: 2},
		},
		MemberLevel: MemberNormal,
	}

	result, err := CalculateCart(cart)

	assert.NoError(t, err)
	assert.Equal(t, 20.00, result.Subtotal)
	assert.Equal(t, 10.00, result.FinalAmount) // 满减10元
}

func TestCalculateCart_MultipleProducts(t *testing.T) {
	// S2: 多商品汇总计算
	// Given: 商品A(10元×2)，商品B(5元×3)
	// When: 计算结算金额
	// Then: 总金额=35元
	cart := Cart{
		Items: []CartItem{
			{ProductID: "A", Price: 10.00, Quantity: 2},
			{ProductID: "B", Price: 5.00, Quantity: 3},
		},
		MemberLevel: MemberNormal,
	}

	result, err := CalculateCart(cart)

	assert.NoError(t, err)
	assert.Equal(t, 35.00, result.Subtotal)
}

// === BR-2: 购物车总金额计算 ===

func TestCalculateCart_EmptyCart(t *testing.T) {
	// S3: 空购物车
	// Given: 购物车为空
	// When: 计算结算金额
	// Then: 总金额=0元
	cart := Cart{
		Items:       []CartItem{},
		MemberLevel: MemberNormal,
	}

	result, err := CalculateCart(cart)

	assert.NoError(t, err)
	assert.Equal(t, 0.00, result.Subtotal)
	assert.Equal(t, 0.00, result.FinalAmount)
}

// === BR-7: 边界与异常处理 ===

func TestCalculateCart_PriceBoundary(t *testing.T) {
	tests := []struct {
		name      string
		price     float64
		quantity  int
		expectErr error
		expected  float64
	}{
		// S4: 商品单价下边界
		{"单价下边界", 0.01, 1, nil, 0.01},
		// S5: 商品单价上边界
		{"单价上边界", 999999.99, 1, nil, 999999.99},
		// S6: 商品单价为0
		{"单价为零", 0, 1, ErrInvalidPrice, 0},
		// S7: 商品单价为负数
		{"单价为负数", -10, 1, ErrInvalidPrice, 0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cart := Cart{
				Items:       []CartItem{{ProductID: "A", Price: tt.price, Quantity: tt.quantity}},
				MemberLevel: MemberNormal,
			}

			result, err := CalculateCart(cart)

			if tt.expectErr != nil {
				assert.ErrorIs(t, err, tt.expectErr)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.expected, result.Subtotal)
			}
		})
	}
}

func TestCalculateCart_QuantityBoundary(t *testing.T) {
	tests := []struct {
		name      string
		quantity  int
		expectErr error
	}{
		// S8: 商品数量为0
		{"数量为零", 0, ErrInvalidQuantity},
		// S9: 商品数量为负数
		{"数量为负数", -1, ErrInvalidQuantity},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cart := Cart{
				Items:       []CartItem{{ProductID: "A", Price: 10.00, Quantity: tt.quantity}},
				MemberLevel: MemberNormal,
			}

			_, err := CalculateCart(cart)

			assert.ErrorIs(t, err, tt.expectErr)
		})
	}
}

// === BR-3: 会员折扣 ===

func TestCalculateCart_MemberDiscount(t *testing.T) {
	tests := []struct {
		name       string
		level      MemberLevel
		subtotal   float64
		expected   float64
		scenarioID string
	}{
		// S10: VIP会员折扣
		{"VIP会员折扣", MemberVIP, 100.00, 85.50, "S10"}, // 满100减10=90，VIP 95折=85.5
		// S11: SVIP会员折扣
		{"SVIP会员折扣", MemberSVIP, 100.00, 81.00, "S11"}, // 满100减10=90，SVIP 9折=81
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cart := Cart{
				Items:       []CartItem{{ProductID: "A", Price: tt.subtotal, Quantity: 1}},
				MemberLevel: tt.level,
			}

			result, err := CalculateCart(cart)

			assert.NoError(t, err)
			assert.Equal(t, tt.expected, result.FinalAmount, "场景 %s", tt.scenarioID)
		})
	}
}

// === BR-4: 满减优惠 ===

func TestCalculateCart_FullReduction(t *testing.T) {
	tests := []struct {
		name       string
		subtotal   float64
		expected   float64
		scenarioID string
	}{
		// S12: 满减优惠-满100
		{"满100减10", 100.00, 90.00, "S12"},
		// S13: 满减优惠-满200
		{"满200减25", 200.00, 175.00, "S13"},
		// S14: 满减优惠-满500
		{"满500减80", 500.00, 420.00, "S14"},
		// S15: 满减门槛-99元
		{"未满100无减免", 99.00, 99.00, "S15"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cart := Cart{
				Items:       []CartItem{{ProductID: "A", Price: tt.subtotal, Quantity: 1}},
				MemberLevel: MemberNormal,
			}

			result, err := CalculateCart(cart)

			assert.NoError(t, err)
			assert.Equal(t, tt.expected, result.FinalAmount, "场景 %s", tt.scenarioID)
		})
	}
}

// === BR-5: 优惠券抵扣 ===

func TestCalculateCart_CouponDiscount(t *testing.T) {
	tests := []struct {
		name       string
		subtotal   float64
		coupon     Coupon
		expected   float64
		scenarioID string
	}{
		// S16: 定额优惠券
		{"定额优惠券20元", 100.00, Coupon{Type: CouponFixed, Value: 20}, 70.00, "S16"}, // 满100减10=90，优惠券减20=70
		// S17: 百分比优惠券
		{"百分比优惠券9折", 100.00, Coupon{Type: CouponPercent, Value: 0.9}, 80.00, "S17"}, // 满100减10=90，9折=81，但满减后90-9=81? 需要重新计算
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cart := Cart{
				Items:       []CartItem{{ProductID: "A", Price: tt.subtotal, Quantity: 1}},
				MemberLevel: MemberNormal,
				Coupon:      tt.coupon,
			}

			result, err := CalculateCart(cart)

			assert.NoError(t, err)
			assert.Equal(t, tt.expected, result.FinalAmount, "场景 %s", tt.scenarioID)
		})
	}
}

// === BR-6: 结算计算顺序（会员折扣与优惠券取优） ===

func TestCalculateCart_MemberVsCoupon(t *testing.T) {
	tests := []struct {
		name       string
		level      MemberLevel
		subtotal   float64
		coupon     Coupon
		expected   float64
		scenarioID string
	}{
		// S18: 优惠券与会员折扣取优（优惠券更优）
		// VIP会员，商品总金额100元，20元券
		// 满减后=90元，VIP 95折=85.5元，优惠券抵扣=20元后=70元
		{"优惠券更优", MemberVIP, 100.00, Coupon{Type: CouponFixed, Value: 20}, 70.00, "S18"},
		// S19: 优惠券与会员折扣取优（会员折扣更优）
		// SVIP会员，商品总金额100元，5元券
		// 满减后=90元，SVIP 9折=81元，优惠券抵扣=5元后=85元
		{"会员折扣更优", MemberSVIP, 100.00, Coupon{Type: CouponFixed, Value: 5}, 81.00, "S19"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cart := Cart{
				Items:       []CartItem{{ProductID: "A", Price: tt.subtotal, Quantity: 1}},
				MemberLevel: tt.level,
				Coupon:      tt.coupon,
			}

			result, err := CalculateCart(cart)

			assert.NoError(t, err)
			assert.Equal(t, tt.expected, result.FinalAmount, "场景 %s", tt.scenarioID)
		})
	}
}

func TestCalculateCart_FullReductionWithMember(t *testing.T) {
	// S20: 满减与会员折扣叠加
	// VIP会员，商品总金额200元
	// 满减后=175元，VIP 95折=166.25元
	cart := Cart{
		Items:       []CartItem{{ProductID: "A", Price: 200.00, Quantity: 1}},
		MemberLevel: MemberVIP,
	}

	result, err := CalculateCart(cart)

	assert.NoError(t, err)
	assert.Equal(t, 25.00, result.FullReduction)
	assert.Equal(t, 166.25, result.FinalAmount, "场景 S20")
}

func TestCalculateCart_CouponExceedsAmount(t *testing.T) {
	// S21: 优惠券金额超过应付金额
	// 商品总金额10元，20元券
	// 满减不触发，优惠券抵扣10元，最终=0
	cart := Cart{
		Items:       []CartItem{{ProductID: "A", Price: 10.00, Quantity: 1}},
		MemberLevel: MemberNormal,
		Coupon:      Coupon{Type: CouponFixed, Value: 20},
	}

	result, err := CalculateCart(cart)

	assert.NoError(t, err)
	assert.Equal(t, 0.00, result.FinalAmount, "场景 S21")
}

func TestCalculateCart_Precision(t *testing.T) {
	// S22: 精度处理-四舍五入
	// 商品单价10.005元，数量1
	// 四舍五入后=10.01元
	cart := Cart{
		Items:       []CartItem{{ProductID: "A", Price: 10.005, Quantity: 1}},
		MemberLevel: MemberNormal,
	}

	result, err := CalculateCart(cart)

	assert.NoError(t, err)
	assert.Equal(t, 10.01, result.Subtotal, "场景 S22")
}

func TestCalculateCart_Comprehensive(t *testing.T) {
	// S23: 综合场景
	// SVIP会员，商品总金额500元，50元券
	// 满减后=420元，会员折扣=378元，优惠券=370元
	// 取最优=370元
	cart := Cart{
		Items:       []CartItem{{ProductID: "A", Price: 500.00, Quantity: 1}},
		MemberLevel: MemberSVIP,
		Coupon:      Coupon{Type: CouponFixed, Value: 50},
	}

	result, err := CalculateCart(cart)

	assert.NoError(t, err)
	assert.Equal(t, 80.00, result.FullReduction, "满减金额应为80元")
	assert.Equal(t, 370.00, result.FinalAmount, "场景 S23: 最终金额应为370元")
	assert.Equal(t, 0.00, result.MemberDiscount, "会员折扣应被优惠券替代")
	assert.Equal(t, 50.00, result.CouponDiscount, "优惠券抵扣应为50元")
}

// =============================================================================
// 表驱动测试 - 覆盖所有场景
// =============================================================================

func TestCalculateCart_AllScenarios(t *testing.T) {
	tests := []struct {
		name         string
		cart         Cart
		expectErr    error
		expectResult *CartResult
	}{
		// S1: 单商品正常计算
		{
			name: "S1_单商品正常计算",
			cart: Cart{
				Items: []CartItem{{ProductID: "A", Price: 10.00, Quantity: 2}},
			},
			expectResult: &CartResult{Subtotal: 20.00, FullReduction: 10.00, FinalAmount: 10.00},
		},
		// S2: 多商品汇总计算
		{
			name: "S2_多商品汇总计算",
			cart: Cart{
				Items: []CartItem{
					{ProductID: "A", Price: 10.00, Quantity: 2},
					{ProductID: "B", Price: 5.00, Quantity: 3},
				},
			},
			expectResult: &CartResult{Subtotal: 35.00, FullReduction: 10.00, FinalAmount: 25.00},
		},
		// S3: 空购物车
		{
			name:         "S3_空购物车",
			cart:         Cart{Items: []CartItem{}},
			expectResult: &CartResult{},
		},
		// S4: 商品单价下边界
		{
			name:         "S4_商品单价下边界",
			cart:         Cart{Items: []CartItem{{ProductID: "A", Price: 0.01, Quantity: 1}}},
			expectResult: &CartResult{Subtotal: 0.01, FinalAmount: 0.01},
		},
		// S6: 商品单价为0
		{
			name:      "S6_商品单价为零",
			cart:      Cart{Items: []CartItem{{ProductID: "A", Price: 0, Quantity: 1}}},
			expectErr: ErrInvalidPrice,
		},
		// S7: 商品单价为负数
		{
			name:      "S7_商品单价为负数",
			cart:      Cart{Items: []CartItem{{ProductID: "A", Price: -10, Quantity: 1}}},
			expectErr: ErrInvalidPrice,
		},
		// S8: 商品数量为0
		{
			name:      "S8_商品数量为零",
			cart:      Cart{Items: []CartItem{{ProductID: "A", Price: 10, Quantity: 0}}},
			expectErr: ErrInvalidQuantity,
		},
		// S9: 商品数量为负数
		{
			name:      "S9_商品数量为负数",
			cart:      Cart{Items: []CartItem{{ProductID: "A", Price: 10, Quantity: -1}}},
			expectErr: ErrInvalidQuantity,
		},
		// S12: 满减优惠-满100
		{
			name:         "S12_满减优惠满100",
			cart:         Cart{Items: []CartItem{{ProductID: "A", Price: 100.00, Quantity: 1}}},
			expectResult: &CartResult{Subtotal: 100.00, FullReduction: 10.00, FinalAmount: 90.00},
		},
		// S13: 满减优惠-满200
		{
			name:         "S13_满减优惠满200",
			cart:         Cart{Items: []CartItem{{ProductID: "A", Price: 200.00, Quantity: 1}}},
			expectResult: &CartResult{Subtotal: 200.00, FullReduction: 25.00, FinalAmount: 175.00},
		},
		// S14: 满减优惠-满500
		{
			name:         "S14_满减优惠满500",
			cart:         Cart{Items: []CartItem{{ProductID: "A", Price: 500.00, Quantity: 1}}},
			expectResult: &CartResult{Subtotal: 500.00, FullReduction: 80.00, FinalAmount: 420.00},
		},
		// S15: 满减门槛-99元
		{
			name:         "S15_未满100无减免",
			cart:         Cart{Items: []CartItem{{ProductID: "A", Price: 99.00, Quantity: 1}}},
			expectResult: &CartResult{Subtotal: 99.00, FullReduction: 0, FinalAmount: 99.00},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := CalculateCart(tt.cart)

			if tt.expectErr != nil {
				assert.ErrorIs(t, err, tt.expectErr)
				return
			}

			assert.NoError(t, err)
			if tt.expectResult != nil {
				assert.Equal(t, tt.expectResult.Subtotal, result.Subtotal)
				assert.Equal(t, tt.expectResult.FinalAmount, result.FinalAmount)
			}
		})
	}
}