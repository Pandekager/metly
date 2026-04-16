export interface ProductAnalytics {
  product_id: string;
  product_name: string;
  subcategory_name: string;
  units_sold: number;
  total_revenue: number;
  order_count: number;
}

export interface ProductTrend {
  product_name: string;
  month: string;
  units_sold: number;
  revenue: number;
}

export interface ProductAnalyticsResponse {
  top_products: ProductAnalytics[];
  sales_trends: ProductTrend[];
}

export interface ProductBusinessAdvice {
  response_text: string;
}
