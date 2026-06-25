import type { Customer, Invoice, Page, Payment, Product, Summary } from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(JSON.stringify(body));
  }
  return response.json() as Promise<T>;
}

export const api = {
  summary: () => request<Summary>('/summary/'),
  products: (search = '') => request<Page<Product>>(`/products/?active=true&ordering=name&search=${encodeURIComponent(search)}`),
  createProduct: (data: Omit<Product, 'id' | 'created_at' | 'updated_at'>) =>
    request<Product>('/products/', { method: 'POST', body: JSON.stringify(data) }),
  customers: (search = '') => request<Page<Customer>>(`/customers/?search=${encodeURIComponent(search)}`),
  createCustomer: (data: Omit<Customer, 'id' | 'created_at'>) =>
    request<Customer>('/customers/', { method: 'POST', body: JSON.stringify(data) }),
  invoices: () => request<Page<Invoice>>('/invoices/?ordering=-created_at'),
  invoice: (id: number) => request<Invoice>(`/invoices/${id}/`),
  createInvoice: (data: {
    customer_id?: number | null;
    customer_name: string;
    customer_phone: string;
    discount: string;
    notes: string;
    paid_amount: string;
    payment_method: 'cash' | 'upi' | 'card' | 'bank';
    payment_reference: string;
    items: { product_id: number; quantity: number }[];
  }) => request<Invoice>('/invoices/', { method: 'POST', body: JSON.stringify(data) }),
  createPayment: (data: {
    invoice: number;
    amount: string;
    method: 'cash' | 'upi' | 'card' | 'bank';
    reference: string;
  }) => request<Payment>('/payments/', { method: 'POST', body: JSON.stringify(data) })
};
