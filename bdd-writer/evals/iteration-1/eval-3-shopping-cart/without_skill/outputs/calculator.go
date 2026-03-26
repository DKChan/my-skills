package cart

import (
	"github.com/shopspring/decimal"
)

const (
	// TaxRate 税率（8%）
	TaxRate = 0.08
	// FreeShippingThreshold 免运费门槛
	FreeShippingThreshold = 99.00
	// ShippingFee 运费
	ShippingFee = 10.00
	// MemberDiscountRate 会员折扣率（5%）
	MemberDiscountRate = 0.05
	// BulkDiscountThreshold 批量折扣门槛
	BulkDiscountThreshold = 3
	// BulkDiscountRate 批量折扣率（10%）
	BulkDiscountRate = 0.10
)

// PriceCalculator 价格计算器
type PriceCalculator struct {
	couponRules   map[string]CouponRule
	categoryRules map[string]CategoryRule
}

// CouponRule 优惠券规则
type CouponRule struct {
	Code          string          // 优惠券代码
	DiscountType  string          // 折扣类型: percent/fixed
	DiscountValue decimal.Decimal // 折扣值
	MinPurchase   decimal.Decimal // 最低消费门槛
}

// CategoryRule 分类规则
type CategoryRule struct {
	Category      string          // 分类名称
	DiscountRate  decimal.Decimal // 折扣率
	IsActive      bool            // 是否激活
}

// NewPriceCalculator 创建价格计算器
func NewPriceCalculator() *PriceCalculator {
	return &PriceCalculator{
		couponRules: map[string]CouponRule{
			"SAVE10": {
				Code:          "SAVE10",
				DiscountType:  "percent",
				DiscountValue: decimal.NewFromFloat(0.10),
				MinPurchase:   decimal.NewFromFloat(50.00),
			},
			"SAVE20": {
				Code:          "SAVE20",
				DiscountType:  "percent",
				DiscountValue: decimal.NewFromFloat(0.20),
				MinPurchase:   decimal.NewFromFloat(100.00),
			},
			"FLAT10": {
				Code:          "FLAT10",
				DiscountType:  "fixed",
				DiscountValue: decimal.NewFromFloat(10.00),
				MinPurchase:   decimal.NewFromFloat(30.00),
			},
		},
		categoryRules: map[string]CategoryRule{
			"electronics": {
				Category:     "electronics",
				DiscountRate: decimal.NewFromFloat(0.05),
				IsActive:     true,
			},
			"books": {
				Category:     "books",
				DiscountRate: decimal.NewFromFloat(0.15),
				IsActive:     true,
			},
		},
	}
}

// Calculate 计算购物车总价
func (pc *PriceCalculator) Calculate(cart *ShoppingCart) *PriceResult {
	result := &PriceResult{
		Subtotal:     decimal.Zero,
		Discount:     decimal.Zero,
		Tax:          decimal.Zero,
		ShippingFee:  decimal.Zero,
		Total:        decimal.Zero,
		SavingsItems: []SavingsItem{},
	}

	if len(cart.Items) == 0 {
		return result
	}

	// 计算小计
	for _, item := range cart.Items {
		itemTotal := item.Product.Price.Mul(decimal.NewFromInt(item.Quantity))
		result.Subtotal = result.Subtotal.Add(itemTotal)
	}

	// 计算各类折扣
	pc.applyCategoryDiscounts(cart, result)
	pc.applyBulkDiscounts(cart, result)
	pc.applyMemberDiscount(cart, result)
	pc.applyCoupon(cart, result)

	// 计算税费（折扣后）
	taxableAmount := result.Subtotal.Sub(result.Discount)
	result.Tax = taxableAmount.Mul(decimal.NewFromFloat(TaxRate)).Round(2)

	// 计算运费
	amountAfterDiscount := result.Subtotal.Sub(result.Discount)
	if amountAfterDiscount.GreaterThanOrEqual(decimal.NewFromFloat(FreeShippingThreshold)) {
		result.ShippingFee = decimal.Zero
	} else {
		result.ShippingFee = decimal.NewFromFloat(ShippingFee)
	}

	// 计算最终总价
	result.Total = result.Subtotal.Sub(result.Discount).Add(result.Tax).Add(result.ShippingFee).Round(2)

	return result
}

// applyCategoryDiscounts 应用分类折扣
func (pc *PriceCalculator) applyCategoryDiscounts(cart *ShoppingCart, result *PriceResult) {
	for _, item := range cart.Items {
		if rule, exists := pc.categoryRules[item.Product.Category]; exists && rule.IsActive {
			itemTotal := item.Product.Price.Mul(decimal.NewFromInt(item.Quantity))
			discount := itemTotal.Mul(rule.DiscountRate)
			result.Discount = result.Discount.Add(discount)
			result.SavingsItems = append(result.SavingsItems, SavingsItem{
				Description: "分类折扣(" + item.Product.Category + "): " + item.Product.Name,
				Amount:      discount,
			})
		}
	}
}

// applyBulkDiscounts 应用批量折扣
func (pc *PriceCalculator) applyBulkDiscounts(cart *ShoppingCart, result *PriceResult) {
	for _, item := range cart.Items {
		if item.Quantity >= BulkDiscountThreshold {
			itemTotal := item.Product.Price.Mul(decimal.NewFromInt(item.Quantity))
			discount := itemTotal.Mul(decimal.NewFromFloat(BulkDiscountRate))
			result.Discount = result.Discount.Add(discount)
			result.SavingsItems = append(result.SavingsItems, SavingsItem{
				Description: "批量折扣: " + item.Product.Name,
				Amount:      discount,
			})
		}
	}
}

// applyMemberDiscount 应用会员折扣
func (pc *PriceCalculator) applyMemberDiscount(cart *ShoppingCart, result *PriceResult) {
	if cart.MemberID != "" {
		memberDiscount := result.Subtotal.Mul(decimal.NewFromFloat(MemberDiscountRate))
		result.Discount = result.Discount.Add(memberDiscount)
		result.SavingsItems = append(result.SavingsItems, SavingsItem{
			Description: "会员折扣",
			Amount:      memberDiscount,
		})
	}
}

// applyCoupon 应用优惠券
func (pc *PriceCalculator) applyCoupon(cart *ShoppingCart, result *PriceResult) {
	if cart.Coupon == "" {
		return
	}

	rule, exists := pc.couponRules[cart.Coupon]
	if !exists {
		return
	}

	// 检查最低消费门槛
	amountAfterDiscount := result.Subtotal.Sub(result.Discount)
	if amountAfterDiscount.LessThan(rule.MinPurchase) {
		return
	}

	var couponDiscount decimal.Decimal
	switch rule.DiscountType {
	case "percent":
		couponDiscount = amountAfterDiscount.Mul(rule.DiscountValue)
	case "fixed":
		couponDiscount = rule.DiscountValue
	}

	result.Discount = result.Discount.Add(couponDiscount)
	result.SavingsItems = append(result.SavingsItems, SavingsItem{
		Description: "优惠券: " + cart.Coupon,
		Amount:      couponDiscount,
	})
}