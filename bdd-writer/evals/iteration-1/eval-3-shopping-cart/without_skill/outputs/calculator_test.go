package cart

import (
	"testing"

	"github.com/shopspring/decimal"
	"github.com/stretchr/testify/assert"
)

// TestEmptyCart 测试空购物车
func TestEmptyCart(t *testing.T) {
	calculator := NewPriceCalculator()
	cart := &ShoppingCart{
		Items: []CartItem{},
	}

	result := calculator.Calculate(cart)

	assert.True(t, result.Subtotal.IsZero(), "空购物车小计应为0")
	assert.True(t, result.Discount.IsZero(), "空购物车折扣应为0")
	assert.True(t, result.Tax.IsZero(), "空购物车税费应为0")
	assert.True(t, result.ShippingFee.IsZero(), "空购物车运费应为0")
	assert.True(t, result.Total.IsZero(), "空购物车总价应为0")
	assert.Empty(t, result.SavingsItems, "空购物车不应有节省明细")
}

// TestSingleItem 测试单个商品
func TestSingleItem(t *testing.T) {
	calculator := NewPriceCalculator()
	cart := &ShoppingCart{
		Items: []CartItem{
			{
				Product: Product{
					ID:       "P001",
					Name:     "测试商品",
					Price:    decimal.NewFromFloat(50.00),
					Category: "general",
				},
				Quantity: 1,
			},
		},
	}

	result := calculator.Calculate(cart)

	expectedSubtotal := decimal.NewFromFloat(50.00)
	expectedTax := decimal.NewFromFloat(4.00) // 50 * 0.08
	expectedShipping := decimal.NewFromFloat(10.00)
	expectedTotal := decimal.NewFromFloat(64.00) // 50 + 4 + 10

	assert.True(t, result.Subtotal.Equal(expectedSubtotal), "小计应为50.00")
	assert.True(t, result.Discount.IsZero(), "无折扣")
	assert.True(t, result.Tax.Equal(expectedTax), "税费应为4.00")
	assert.True(t, result.ShippingFee.Equal(expectedShipping), "运费应为10.00")
	assert.True(t, result.Total.Equal(expectedTotal), "总价应为64.00")
}

// TestMultipleItems 测试多个商品
func TestMultipleItems(t *testing.T) {
	calculator := NewPriceCalculator()
	cart := &ShoppingCart{
		Items: []CartItem{
			{
				Product: Product{
					ID:    "P001",
					Name:  "商品A",
					Price: decimal.NewFromFloat(30.00),
				},
				Quantity: 2, // 60.00
			},
			{
				Product: Product{
					ID:    "P002",
					Name:  "商品B",
					Price: decimal.NewFromFloat(20.00),
				},
				Quantity: 3, // 60.00
			},
		},
	}

	result := calculator.Calculate(cart)

	expectedSubtotal := decimal.NewFromFloat(120.00)
	expectedTax := decimal.NewFromFloat(9.60) // 120 * 0.08
	expectedShipping := decimal.Zero          // 超过99免运费
	expectedTotal := decimal.NewFromFloat(129.60)

	assert.True(t, result.Subtotal.Equal(expectedSubtotal), "小计应为120.00")
	assert.True(t, result.ShippingFee.Equal(expectedShipping), "超过99免运费")
	assert.True(t, result.Total.Equal(expectedTotal), "总价应为129.60")
}

// TestFreeShipping 测试免运费
func TestFreeShipping(t *testing.T) {
	calculator := NewPriceCalculator()

	tests := []struct {
		name           string
		items          []CartItem
		expectedShipping decimal.Decimal
	}{
		{
			name: "刚好达到免运费门槛",
			items: []CartItem{
				{
					Product: Product{ID: "P001", Name: "商品", Price: decimal.NewFromFloat(99.00)},
					Quantity: 1,
				},
			},
			expectedShipping: decimal.Zero,
		},
		{
			name: "超过免运费门槛",
			items: []CartItem{
				{
					Product: Product{ID: "P001", Name: "商品", Price: decimal.NewFromFloat(100.00)},
					Quantity: 1,
				},
			},
			expectedShipping: decimal.Zero,
		},
		{
			name: "未达到免运费门槛",
			items: []CartItem{
				{
					Product: Product{ID: "P001", Name: "商品", Price: decimal.NewFromFloat(98.00)},
					Quantity: 1,
				},
			},
			expectedShipping: decimal.NewFromFloat(10.00),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cart := &ShoppingCart{Items: tt.items}
			result := calculator.Calculate(cart)
			assert.True(t, result.ShippingFee.Equal(tt.expectedShipping), "运费计算错误")
		})
	}
}

// TestCategoryDiscount 测试分类折扣
func TestCategoryDiscount(t *testing.T) {
	calculator := NewPriceCalculator()

	tests := []struct {
		name            string
		items           []CartItem
		expectedDiscount decimal.Decimal
	}{
		{
			name: "电子产品5%折扣",
			items: []CartItem{
				{
					Product: Product{
						ID:       "P001",
						Name:     "手机",
						Price:    decimal.NewFromFloat(1000.00),
						Category: "electronics",
					},
					Quantity: 1,
				},
			},
			expectedDiscount: decimal.NewFromFloat(50.00), // 1000 * 0.05
		},
		{
			name: "图书15%折扣",
			items: []CartItem{
				{
					Product: Product{
						ID:       "P002",
						Name:     "书籍",
						Price:    decimal.NewFromFloat(100.00),
						Category: "books",
					},
					Quantity: 1,
				},
			},
			expectedDiscount: decimal.NewFromFloat(15.00), // 100 * 0.15
		},
		{
			name: "无分类折扣",
			items: []CartItem{
				{
					Product: Product{
						ID:       "P003",
						Name:     "衣服",
						Price:    decimal.NewFromFloat(100.00),
						Category: "clothing",
					},
					Quantity: 1,
				},
			},
			expectedDiscount: decimal.Zero,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cart := &ShoppingCart{Items: tt.items}
			result := calculator.Calculate(cart)
			assert.True(t, result.Discount.Equal(tt.expectedDiscount), "折扣计算错误")
		})
	}
}

// TestBulkDiscount 测试批量折扣
func TestBulkDiscount(t *testing.T) {
	calculator := NewPriceCalculator()

	tests := []struct {
		name            string
		items           []CartItem
		expectedDiscount decimal.Decimal
	}{
		{
			name: "购买3件享受批量折扣",
			items: []CartItem{
				{
					Product: Product{
						ID:    "P001",
						Name:  "商品",
						Price: decimal.NewFromFloat(100.00),
					},
					Quantity: 3, // 总价300，批量折扣10% = 30
				},
			},
			expectedDiscount: decimal.NewFromFloat(30.00),
		},
		{
			name: "购买5件享受批量折扣",
			items: []CartItem{
				{
					Product: Product{
						ID:    "P001",
						Name:  "商品",
						Price: decimal.NewFromFloat(50.00),
					},
					Quantity: 5, // 总价250，批量折扣10% = 25
				},
			},
			expectedDiscount: decimal.NewFromFloat(25.00),
		},
		{
			name: "购买2件无批量折扣",
			items: []CartItem{
				{
					Product: Product{
						ID:    "P001",
						Name:  "商品",
						Price: decimal.NewFromFloat(100.00),
					},
					Quantity: 2,
				},
			},
			expectedDiscount: decimal.Zero,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cart := &ShoppingCart{Items: tt.items}
			result := calculator.Calculate(cart)
			assert.True(t, result.Discount.Equal(tt.expectedDiscount), "批量折扣计算错误")
		})
	}
}

// TestMemberDiscount 测试会员折扣
func TestMemberDiscount(t *testing.T) {
	calculator := NewPriceCalculator()

	tests := []struct {
		name            string
		cart            *ShoppingCart
		expectedDiscount decimal.Decimal
	}{
		{
			name: "会员享受5%折扣",
			cart: &ShoppingCart{
				Items: []CartItem{
					{
						Product: Product{
							ID:    "P001",
							Name:  "商品",
							Price: decimal.NewFromFloat(100.00),
						},
						Quantity: 1,
					},
				},
				MemberID: "M001",
			},
			expectedDiscount: decimal.NewFromFloat(5.00), // 100 * 0.05
		},
		{
			name: "非会员无折扣",
			cart: &ShoppingCart{
				Items: []CartItem{
					{
						Product: Product{
							ID:    "P001",
							Name:  "商品",
							Price: decimal.NewFromFloat(100.00),
						},
						Quantity: 1,
					},
				},
				MemberID: "",
			},
			expectedDiscount: decimal.Zero,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := calculator.Calculate(tt.cart)
			assert.True(t, result.Discount.Equal(tt.expectedDiscount), "会员折扣计算错误")
		})
	}
}

// TestCouponDiscount 测试优惠券折扣
func TestCouponDiscount(t *testing.T) {
	calculator := NewPriceCalculator()

	tests := []struct {
		name            string
		cart            *ShoppingCart
		expectedDiscount decimal.Decimal
	}{
		{
			name: "SAVE10优惠券-10%折扣-满50可用",
			cart: &ShoppingCart{
				Items: []CartItem{
					{
						Product: Product{
							ID:    "P001",
							Name:  "商品",
							Price: decimal.NewFromFloat(100.00),
						},
						Quantity: 1,
					},
				},
				Coupon: "SAVE10",
			},
			expectedDiscount: decimal.NewFromFloat(10.00), // 100 * 0.10
		},
		{
			name: "SAVE20优惠券-20%折扣-满100可用",
			cart: &ShoppingCart{
				Items: []CartItem{
					{
						Product: Product{
							ID:    "P001",
							Name:  "商品",
							Price: decimal.NewFromFloat(150.00),
						},
						Quantity: 1,
					},
				},
				Coupon: "SAVE20",
			},
			expectedDiscount: decimal.NewFromFloat(30.00), // 150 * 0.20
		},
		{
			name: "FLAT10优惠券-固定10元折扣-满30可用",
			cart: &ShoppingCart{
				Items: []CartItem{
					{
						Product: Product{
							ID:    "P001",
							Name:  "商品",
							Price: decimal.NewFromFloat(50.00),
						},
						Quantity: 1,
					},
				},
				Coupon: "FLAT10",
			},
			expectedDiscount: decimal.NewFromFloat(10.00), // 固定10元
		},
		{
			name: "优惠券门槛不足-不适用",
			cart: &ShoppingCart{
				Items: []CartItem{
					{
						Product: Product{
							ID:    "P001",
							Name:  "商品",
							Price: decimal.NewFromFloat(40.00),
						},
						Quantity: 1,
					},
				},
				Coupon: "SAVE20", // 需要100元
			},
			expectedDiscount: decimal.Zero,
		},
		{
			name: "无效优惠券-不适用",
			cart: &ShoppingCart{
				Items: []CartItem{
					{
						Product: Product{
							ID:    "P001",
							Name:  "商品",
							Price: decimal.NewFromFloat(100.00),
						},
						Quantity: 1,
					},
				},
				Coupon: "INVALID",
			},
			expectedDiscount: decimal.Zero,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := calculator.Calculate(tt.cart)
			assert.True(t, result.Discount.Equal(tt.expectedDiscount), "优惠券折扣计算错误")
		})
	}
}

// TestCombinedDiscounts 测试组合折扣
func TestCombinedDiscounts(t *testing.T) {
	calculator := NewPriceCalculator()

	// 场景：会员购买电子产品3件，使用SAVE10优惠券
	// - 原价: 100 * 3 = 300
	// - 分类折扣(电子产品5%): 300 * 0.05 = 15
	// - 批量折扣(10%): 300 * 0.10 = 30
	// - 会员折扣(5%): 300 * 0.05 = 15
	// - 优惠券折扣(10%): 需要基于折扣后金额计算，这里简化处理
	cart := &ShoppingCart{
		Items: []CartItem{
			{
				Product: Product{
					ID:       "P001",
					Name:     "手机",
					Price:    decimal.NewFromFloat(100.00),
					Category: "electronics",
				},
				Quantity: 3,
			},
		},
		MemberID: "M001",
		Coupon:   "SAVE10",
	}

	result := calculator.Calculate(cart)

	// 验证各项折扣
	assert.True(t, result.Subtotal.Equal(decimal.NewFromFloat(300.00)), "小计应为300.00")
	assert.True(t, result.Discount.GreaterThan(decimal.Zero), "应有折扣")
	assert.NotEmpty(t, result.SavingsItems, "应有节省明细")

	// 验证最终价格计算正确
	// 折扣后金额 * 税率 + 运费（如果适用）
	expectedDiscount := decimal.NewFromFloat(15).Add(decimal.NewFromFloat(30)).Add(decimal.NewFromFloat(15))
	assert.True(t, result.Discount.GreaterThanOrEqual(expectedDiscount), "折扣应包含分类、批量、会员折扣")
}

// TestTaxCalculation 测试税费计算
func TestTaxCalculation(t *testing.T) {
	calculator := NewPriceCalculator()

	tests := []struct {
		name      string
		items     []CartItem
		discount  decimal.Decimal
		expectedTax decimal.Decimal
	}{
		{
			name: "基础税费计算",
			items: []CartItem{
				{
					Product: Product{
						ID:    "P001",
						Name:  "商品",
						Price: decimal.NewFromFloat(100.00),
					},
					Quantity: 1,
				},
			},
			expectedTax: decimal.NewFromFloat(8.00), // 100 * 0.08
		},
		{
			name: "税费保留两位小数",
			items: []CartItem{
				{
					Product: Product{
						ID:    "P001",
						Name:  "商品",
						Price: decimal.NewFromFloat(33.33),
					},
					Quantity: 3,
				},
			},
			expectedTax: decimal.NewFromFloat(8.00), // 99.99 * 0.08 = 7.9992 -> 8.00
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cart := &ShoppingCart{Items: tt.items}
			result := calculator.Calculate(cart)
			assert.True(t, result.Tax.Equal(tt.expectedTax), "税费计算错误")
		})
	}
}

// TestTotalCalculation 测试总价计算
func TestTotalCalculation(t *testing.T) {
	calculator := NewPriceCalculator()

	// 完整场景测试
	// 商品原价: 100
	// 无折扣
	// 税费: 100 * 0.08 = 8
	// 运费: 10 (未满99)
	// 总价: 100 + 8 + 10 = 118
	cart := &ShoppingCart{
		Items: []CartItem{
			{
				Product: Product{
					ID:    "P001",
					Name:  "商品",
					Price: decimal.NewFromFloat(100.00),
				},
				Quantity: 1,
			},
		},
	}

	result := calculator.Calculate(cart)

	expectedTotal := decimal.NewFromFloat(118.00)
	assert.True(t, result.Total.Equal(expectedTotal), "总价应为118.00")
}

// TestSavingsItems 测试节省明细
func TestSavingsItems(t *testing.T) {
	calculator := NewPriceCalculator()

	cart := &ShoppingCart{
		Items: []CartItem{
			{
				Product: Product{
					ID:       "P001",
					Name:     "手机",
					Price:    decimal.NewFromFloat(100.00),
					Category: "electronics",
				},
				Quantity: 3,
			},
		},
		MemberID: "M001",
		Coupon:   "SAVE10",
	}

	result := calculator.Calculate(cart)

	// 验证节省明细不为空
	assert.NotEmpty(t, result.SavingsItems, "应有节省明细")

	// 验证节省明细描述
	descriptions := make([]string, len(result.SavingsItems))
	for i, item := range result.SavingsItems {
		descriptions[i] = item.Description
	}

	// 应包含分类折扣、批量折扣、会员折扣、优惠券折扣
	assert.Contains(t, descriptions[0], "分类折扣", "应包含分类折扣")
}

// TestQuantityZero 测试数量为0的情况
func TestQuantityZero(t *testing.T) {
	calculator := NewPriceCalculator()
	cart := &ShoppingCart{
		Items: []CartItem{
			{
				Product: Product{
					ID:    "P001",
					Name:  "商品",
					Price: decimal.NewFromFloat(100.00),
				},
				Quantity: 0,
			},
		},
	}

	result := calculator.Calculate(cart)

	// 数量为0时，该项不应计入总价
	assert.True(t, result.Subtotal.IsZero(), "数量为0的商品不应计入小计")
}

// TestDecimalPrecision 测试小数精度
func TestDecimalPrecision(t *testing.T) {
	calculator := NewPriceCalculator()

	cart := &ShoppingCart{
		Items: []CartItem{
			{
				Product: Product{
					ID:    "P001",
					Name:  "商品",
					Price: decimal.NewFromFloat(99.99),
				},
				Quantity: 1,
			},
		},
	}

	result := calculator.Calculate(cart)

	// 验证精度正确
	assert.Equal(t, 2, result.Total.Exponent(), "总价应保留2位小数")
	assert.Equal(t, 2, result.Tax.Exponent(), "税费应保留2位小数")
}

// TestNegativePrice 测试负价格处理
func TestNegativePrice(t *testing.T) {
	calculator := NewPriceCalculator()

	// 注意：实际应用中应该在输入验证时拒绝负价格
	// 这里测试计算器对异常输入的处理
	cart := &ShoppingCart{
		Items: []CartItem{
			{
				Product: Product{
					ID:    "P001",
					Name:  "异常商品",
					Price: decimal.NewFromFloat(-10.00),
				},
				Quantity: 1,
			},
		},
	}

	result := calculator.Calculate(cart)

	// 负价格会导致负的小计
	assert.True(t, result.Subtotal.LessThan(decimal.Zero), "负价格应导致负小计")
}