export type Product = {
  id: number;
  name: string;
  sku: string;
  barcode: string;
  price: string;
  tax_rate: string;
  stock: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Customer = {
  id: number;
  name: string;
  phone: string;
  address: string;
  created_at: string;
};

export type InvoiceItem = {
  id: number;
  product: number;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: string;
  tax_rate: string;
  line_subtotal: string;
  line_tax: string;
  line_total: string;
};

export type Payment = {
  id: number;
  invoice: number;
  amount: string;
  method: 'cash' | 'upi' | 'card' | 'bank';
  reference: string;
  created_at: string;
};

export type Invoice = {
  id: number;
  number: string;
  customer: number | null;
  customer_name: string;
  customer_phone: string;
  status: 'draft' | 'paid' | 'partial' | 'unpaid' | 'cancelled';
  subtotal: string;
  tax_total: string;
  discount: string;
  total: string;
  paid_amount: string;
  due_amount: string;
  notes: string;
  created_at: string;
  updated_at: string;
  items: InvoiceItem[];
  payments: Payment[];
};

export type Summary = {
  date: string;
  invoice_count: number;
  sales_total: string | number;
  paid_total: string | number;
  due_total: string | number;
  low_stock_count: number;
};

export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type CartLine = {
  product: Product;
  quantity: number;
};
