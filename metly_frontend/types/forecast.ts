export interface Forecast {
  date: string;
  amount: number;
  is_forecast: boolean;
  subcategory_name?: string | null;
}
