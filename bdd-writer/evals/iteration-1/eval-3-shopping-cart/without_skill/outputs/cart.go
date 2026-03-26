package cart

import "github.com/shopspring/decimal"

// Product 表示购物车中的商品
type Product struct {
	ID       string          // 商品ID
	Name     string          // 商品名称
	Price    decimal.Decimal // 单价
	Category string          // 商品分类
}

// CartItem 表示购物车中的商品项
type CartItem struct {
	Product  Product         // 商品信息
	Quantity int64           // 数量
	Discount decimal.Decimal // 单项折扣（百分比，0-1）
}

// ShoppingCart 表示购物车
type ShoppingCart struct {
	Items    []CartItem      // 商品列表
	Coupon   string          // 优惠券代码
	MemberID string          // 会员ID
}

// PriceResult 表示价格计算结果
type PriceResult struct {
	Subtotal     decimal.Decimal // 小计（原价总和）
	Discount     decimal.Decimal // 折扣金额
	Tax          decimal.Decimal // 税费
	ShippingFee  decimal.Decimal // 运费
	Total        decimal.Decimal // 最终总价
	SavingsItems []SavingsItem   // 节省明细
}

// SavingsItem 表示节省明细项
type SavingsItem struct {
	Description string          // 描述
	Amount      decimal.Decimal // 金额
}