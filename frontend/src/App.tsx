import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import Inventory2Icon from '@mui/icons-material/Inventory2';
import PaymentsIcon from '@mui/icons-material/Payments';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import SaveIcon from '@mui/icons-material/Save';
import SearchIcon from '@mui/icons-material/Search';
import VisibilityIcon from '@mui/icons-material/Visibility';
import {
  Alert,
  AppBar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  InputAdornment,
  MenuItem,
  Stack,
  Tab,
  Tabs,
  TextField,
  Toolbar,
  Tooltip,
  Typography
} from '@mui/material';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import { api } from './api';
import type { CartLine, Customer, Invoice, Product, Summary } from './types';

const money = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });

function n(value: string | number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function App() {
  const [tab, setTab] = useState(0);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [cart, setCart] = useState<CartLine[]>([]);
  const [search, setSearch] = useState('');
  const [customerSearch, setCustomerSearch] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [discount, setDiscount] = useState('0');
  const [paidAmount, setPaidAmount] = useState('0');
  const [paymentMethod, setPaymentMethod] = useState<'cash' | 'upi' | 'card' | 'bank'>('cash');
  const [paymentReference, setPaymentReference] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [productOpen, setProductOpen] = useState(false);
  const [customerOpen, setCustomerOpen] = useState(false);
  const [invoiceOpen, setInvoiceOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [newPaymentAmount, setNewPaymentAmount] = useState('');
  const [newPaymentMethod, setNewPaymentMethod] = useState<'cash' | 'upi' | 'card' | 'bank'>('cash');
  const [newPaymentReference, setNewPaymentReference] = useState('');
  const [newProduct, setNewProduct] = useState({ name: '', sku: '', barcode: '', price: '', tax_rate: '0', stock: '0', is_active: true });
  const [newCustomer, setNewCustomer] = useState({ name: '', phone: '', address: '' });

  const totals = useMemo(() => {
    const subtotal = cart.reduce((sum, line) => sum + n(line.product.price) * line.quantity, 0);
    const tax = cart.reduce((sum, line) => sum + (n(line.product.price) * line.quantity * n(line.product.tax_rate)) / 100, 0);
    const total = Math.max(subtotal + tax - n(discount), 0);
    const due = Math.max(total - n(paidAmount), 0);
    return { subtotal, tax, total, due };
  }, [cart, discount, paidAmount]);

  async function loadDashboard() {
    const [summaryData, invoicesData] = await Promise.all([api.summary(), api.invoices()]);
    setSummary(summaryData);
    setInvoices(invoicesData.results);
  }

  async function loadProducts(term = search) {
    const data = await api.products(term);
    setProducts(data.results);
  }

  async function loadCustomers(term = customerSearch) {
    const data = await api.customers(term);
    setCustomers(data.results);
  }

  useEffect(() => {
    loadDashboard().catch((err: unknown) => setError(String(err)));
    loadProducts('').catch((err: unknown) => setError(String(err)));
    loadCustomers('').catch((err: unknown) => setError(String(err)));
  }, []);

  useEffect(() => {
    const handle = window.setTimeout(() => loadProducts(search).catch((err: unknown) => setError(String(err))), 180);
    return () => window.clearTimeout(handle);
  }, [search]);

  useEffect(() => {
    const handle = window.setTimeout(() => loadCustomers(customerSearch).catch((err: unknown) => setError(String(err))), 180);
    return () => window.clearTimeout(handle);
  }, [customerSearch]);

  function addToCart(product: Product) {
    if (product.stock <= 0) return;
    setCart((current) => {
      const existing = current.find((line) => line.product.id === product.id);
      if (existing) {
        return current.map((line) => (line.product.id === product.id ? { ...line, quantity: Math.min(line.quantity + 1, product.stock) } : line));
      }
      return [...current, { product, quantity: 1 }];
    });
  }

  function setQuantity(productId: number, quantity: number) {
    setCart((current) =>
      current
        .map((line) => (line.product.id === productId ? { ...line, quantity: Math.max(1, Math.min(quantity, line.product.stock)) } : line))
        .filter((line) => line.quantity > 0)
    );
  }

  async function submitInvoice() {
    setError('');
    setSuccess('');
    if (!cart.length) {
      setError('Add at least one product.');
      return;
    }
    const invoice = await api.createInvoice({
      customer_id: selectedCustomer?.id ?? null,
      customer_name: selectedCustomer?.name ?? customerName,
      customer_phone: selectedCustomer?.phone ?? customerPhone,
      discount,
      notes,
      paid_amount: paidAmount,
      payment_method: paymentMethod,
      payment_reference: paymentReference,
      items: cart.map((line) => ({ product_id: line.product.id, quantity: line.quantity }))
    });
    setSuccess(`Invoice ${invoice.number} saved.`);
    setCart([]);
    setSelectedCustomer(null);
    setCustomerName('');
    setCustomerPhone('');
    setDiscount('0');
    setPaidAmount('0');
    setPaymentReference('');
    setNotes('');
    await Promise.all([loadDashboard(), loadProducts()]);
  }

  async function submitProduct(event: FormEvent) {
    event.preventDefault();
    await api.createProduct({
      ...newProduct,
      price: Number(newProduct.price).toFixed(2),
      tax_rate: Number(newProduct.tax_rate).toFixed(2),
      stock: Number(newProduct.stock)
    });
    setProductOpen(false);
    setNewProduct({ name: '', sku: '', barcode: '', price: '', tax_rate: '0', stock: '0', is_active: true });
    await loadProducts();
  }

  async function submitCustomer(event: FormEvent) {
    event.preventDefault();
    const customer = await api.createCustomer(newCustomer);
    setSelectedCustomer(customer);
    setCustomerOpen(false);
    setNewCustomer({ name: '', phone: '', address: '' });
    await loadCustomers();
  }

  async function openInvoice(invoice: Invoice) {
    setError('');
    setSuccess('');
    const freshInvoice = await api.invoice(invoice.id);
    setSelectedInvoice(freshInvoice);
    setNewPaymentAmount(n(freshInvoice.due_amount) > 0 ? freshInvoice.due_amount : '');
    setNewPaymentMethod('cash');
    setNewPaymentReference('');
    setInvoiceOpen(true);
  }

  async function submitPayment(event: FormEvent) {
    event.preventDefault();
    if (!selectedInvoice) return;
    const amount = n(newPaymentAmount);
    const due = n(selectedInvoice.due_amount);
    if (amount <= 0) {
      setError('Payment amount must be greater than 0.');
      return;
    }
    if (amount > due) {
      setError(`Payment cannot exceed remaining due ${money.format(due)}.`);
      return;
    }
    await api.createPayment({
      invoice: selectedInvoice.id,
      amount: amount.toFixed(2),
      method: newPaymentMethod,
      reference: newPaymentReference
    });
    const freshInvoice = await api.invoice(selectedInvoice.id);
    setSelectedInvoice(freshInvoice);
    setNewPaymentAmount(n(freshInvoice.due_amount) > 0 ? freshInvoice.due_amount : '');
    setNewPaymentReference('');
    setSuccess(`Payment added for ${freshInvoice.number}.`);
    await loadDashboard();
  }

  return (
    <Box className="app-shell">
      <AppBar position="sticky" color="inherit" elevation={0}>
        <Toolbar className="toolbar">
          <ReceiptLongIcon color="primary" />
          <Typography variant="h6" fontWeight={800} flex={1}>
            Shubh Bill
          </Typography>
          <Chip size="small" color="primary" label={summary ? money.format(n(summary.sales_total)) : money.format(0)} />
        </Toolbar>
        <Tabs value={tab} onChange={(_, value: number) => setTab(value)} variant="fullWidth">
          <Tab label="Bill" />
          <Tab label="Stock" />
          <Tab label="Sales" />
        </Tabs>
      </AppBar>

      <Container maxWidth="lg" className="main">
        {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}
        {success && <Alert severity="success" onClose={() => setSuccess('')}>{success}</Alert>}

        {tab === 0 && (
          <Box className="billing-grid">
            <Stack spacing={1.5}>
              <TextField
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search product, SKU, barcode"
                InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> }}
              />
              <Box className="product-list">
                {products.map((product) => (
                  <Card key={product.id} className="product-row">
                    <CardContent>
                      <Box flex={1} minWidth={0}>
                        <Typography fontWeight={800} noWrap>{product.name}</Typography>
                        <Typography variant="body2" color="text.secondary">{product.sku} · Stock {product.stock}</Typography>
                      </Box>
                      <Typography fontWeight={800}>{money.format(n(product.price))}</Typography>
                      <Button variant="contained" startIcon={<AddIcon />} disabled={product.stock <= 0} onClick={() => addToCart(product)}>
                        Add
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            </Stack>

            <Stack spacing={1.5}>
              <Card>
                <CardContent>
                  <Stack spacing={1.25}>
                    <Box display="flex" gap={1}>
                      <TextField
                        fullWidth
                        value={customerSearch}
                        onChange={(event) => setCustomerSearch(event.target.value)}
                        placeholder="Customer search"
                      />
                      <Tooltip title="New customer">
                        <IconButton color="primary" onClick={() => setCustomerOpen(true)}><PersonAddIcon /></IconButton>
                      </Tooltip>
                    </Box>
                    <Box className="customer-strip">
                      {customers.map((customer) => (
                        <Chip
                          key={customer.id}
                          label={`${customer.name}${customer.phone ? ` · ${customer.phone}` : ''}`}
                          color={selectedCustomer?.id === customer.id ? 'primary' : 'default'}
                          onClick={() => {
                            setSelectedCustomer(customer);
                            setCustomerName(customer.name);
                            setCustomerPhone(customer.phone);
                          }}
                        />
                      ))}
                    </Box>
                    {!selectedCustomer && (
                      <Box display="grid" gridTemplateColumns="1fr 1fr" gap={1}>
                        <TextField label="Name" value={customerName} onChange={(event) => setCustomerName(event.target.value)} />
                        <TextField label="Phone" value={customerPhone} onChange={(event) => setCustomerPhone(event.target.value)} />
                      </Box>
                    )}
                  </Stack>
                </CardContent>
              </Card>

              <Card>
                <CardContent>
                  <Stack spacing={1.25}>
                    <Typography fontWeight={900}>Cart</Typography>
                    {cart.map((line) => (
                      <Box key={line.product.id} className="cart-row">
                        <Box minWidth={0}>
                          <Typography fontWeight={700} noWrap>{line.product.name}</Typography>
                          <Typography variant="body2" color="text.secondary">{money.format(n(line.product.price))}</Typography>
                        </Box>
                        <TextField
                          type="number"
                          value={line.quantity}
                          onChange={(event) => setQuantity(line.product.id, Number(event.target.value))}
                          inputProps={{ min: 1, max: line.product.stock }}
                          className="qty"
                        />
                        <Typography fontWeight={800}>{money.format(n(line.product.price) * line.quantity)}</Typography>
                        <IconButton color="error" onClick={() => setCart((current) => current.filter((item) => item.product.id !== line.product.id))}>
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    ))}
                    <Divider />
                    <Box className="totals">
                      <span>Subtotal</span><strong>{money.format(totals.subtotal)}</strong>
                      <span>Tax</span><strong>{money.format(totals.tax)}</strong>
                      <span>Discount</span><TextField type="number" value={discount} onChange={(event) => setDiscount(event.target.value)} />
                      <span>Total</span><strong>{money.format(totals.total)}</strong>
                      <span>Paid</span><TextField type="number" value={paidAmount} onChange={(event) => setPaidAmount(event.target.value)} />
                      <span>Due</span><strong>{money.format(totals.due)}</strong>
                    </Box>
                    <Box display="grid" gridTemplateColumns="1fr 1fr" gap={1}>
                      <TextField select label="Payment" value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value as typeof paymentMethod)}>
                        <MenuItem value="cash">Cash</MenuItem>
                        <MenuItem value="upi">UPI</MenuItem>
                        <MenuItem value="card">Card</MenuItem>
                        <MenuItem value="bank">Bank</MenuItem>
                      </TextField>
                      <TextField label="Reference" value={paymentReference} onChange={(event) => setPaymentReference(event.target.value)} />
                    </Box>
                    <TextField label="Notes" value={notes} onChange={(event) => setNotes(event.target.value)} multiline minRows={2} />
                    <Button variant="contained" size="large" startIcon={<SaveIcon />} onClick={() => submitInvoice().catch((err: unknown) => setError(String(err)))}>
                      Save Invoice
                    </Button>
                  </Stack>
                </CardContent>
              </Card>
            </Stack>
          </Box>
        )}

        {tab === 1 && (
          <Stack spacing={1.5}>
            <Button variant="contained" startIcon={<Inventory2Icon />} onClick={() => setProductOpen(true)}>New Product</Button>
            {products.map((product) => (
              <Card key={product.id}>
                <CardContent className="stock-row">
                  <Box minWidth={0}>
                    <Typography fontWeight={800} noWrap>{product.name}</Typography>
                    <Typography color="text.secondary">{product.sku} · {product.barcode || 'No barcode'}</Typography>
                  </Box>
                  <Typography>{money.format(n(product.price))}</Typography>
                  <Chip label={`Stock ${product.stock}`} color={product.stock <= 5 ? 'warning' : 'default'} />
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}

        {tab === 2 && (
          <Stack spacing={1.5}>
            <Box className="summary-grid">
              <Card><CardContent><Typography color="text.secondary">Invoices</Typography><Typography variant="h5">{summary?.invoice_count ?? 0}</Typography></CardContent></Card>
              <Card><CardContent><Typography color="text.secondary">Paid</Typography><Typography variant="h5">{money.format(n(summary?.paid_total ?? 0))}</Typography></CardContent></Card>
              <Card><CardContent><Typography color="text.secondary">Due</Typography><Typography variant="h5">{money.format(n(summary?.due_total ?? 0))}</Typography></CardContent></Card>
              <Card><CardContent><Typography color="text.secondary">Low Stock</Typography><Typography variant="h5">{summary?.low_stock_count ?? 0}</Typography></CardContent></Card>
            </Box>
            {invoices.map((invoice) => (
              <Card key={invoice.id} className="clickable-card" onClick={() => openInvoice(invoice).catch((err: unknown) => setError(String(err)))}>
                <CardContent className="invoice-row">
                  <Box minWidth={0}>
                    <Typography fontWeight={800}>{invoice.number}</Typography>
                    <Typography color="text.secondary">{invoice.customer_name || 'Walk-in'} · {new Date(invoice.created_at).toLocaleString()}</Typography>
                  </Box>
                  <Chip label={invoice.status} color={invoice.status === 'paid' ? 'success' : invoice.status === 'partial' ? 'warning' : 'default'} />
                  <Box textAlign="right">
                    <Typography fontWeight={900}>{money.format(n(invoice.total))}</Typography>
                    <Typography variant="body2" color="text.secondary">Due {money.format(n(invoice.due_amount))}</Typography>
                  </Box>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<VisibilityIcon />}
                    onClick={(event) => {
                      event.stopPropagation();
                      openInvoice(invoice).catch((err: unknown) => setError(String(err)));
                    }}
                  >
                    View / Payment
                  </Button>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}
      </Container>

      <Dialog open={productOpen} onClose={() => setProductOpen(false)} fullWidth maxWidth="xs">
        <Box component="form" onSubmit={(event) => submitProduct(event).catch((err: unknown) => setError(String(err)))}>
          <DialogTitle>New Product</DialogTitle>
          <DialogContent className="dialog-form">
            <TextField required label="Name" value={newProduct.name} onChange={(event) => setNewProduct({ ...newProduct, name: event.target.value })} />
            <TextField required label="SKU" value={newProduct.sku} onChange={(event) => setNewProduct({ ...newProduct, sku: event.target.value })} />
            <TextField label="Barcode" value={newProduct.barcode} onChange={(event) => setNewProduct({ ...newProduct, barcode: event.target.value })} />
            <TextField required type="number" label="Price" value={newProduct.price} onChange={(event) => setNewProduct({ ...newProduct, price: event.target.value })} />
            <TextField type="number" label="Tax %" value={newProduct.tax_rate} onChange={(event) => setNewProduct({ ...newProduct, tax_rate: event.target.value })} />
            <TextField required type="number" label="Stock" value={newProduct.stock} onChange={(event) => setNewProduct({ ...newProduct, stock: event.target.value })} />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setProductOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained">Save</Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog open={customerOpen} onClose={() => setCustomerOpen(false)} fullWidth maxWidth="xs">
        <Box component="form" onSubmit={(event) => submitCustomer(event).catch((err: unknown) => setError(String(err)))}>
          <DialogTitle>New Customer</DialogTitle>
          <DialogContent className="dialog-form">
            <TextField required label="Name" value={newCustomer.name} onChange={(event) => setNewCustomer({ ...newCustomer, name: event.target.value })} />
            <TextField label="Phone" value={newCustomer.phone} onChange={(event) => setNewCustomer({ ...newCustomer, phone: event.target.value })} />
            <TextField label="Address" multiline minRows={3} value={newCustomer.address} onChange={(event) => setNewCustomer({ ...newCustomer, address: event.target.value })} />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCustomerOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained">Save</Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog open={invoiceOpen} onClose={() => setInvoiceOpen(false)} fullWidth maxWidth="sm">
        {selectedInvoice && (
          <Box component="form" onSubmit={(event) => submitPayment(event).catch((err: unknown) => setError(String(err)))}>
            <DialogTitle>
              <Box display="flex" alignItems="center" gap={1}>
                <ReceiptLongIcon color="primary" />
                <Box>
                  <Typography variant="h6" fontWeight={900}>{selectedInvoice.number}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {selectedInvoice.customer_name || 'Walk-in'} Â· {new Date(selectedInvoice.created_at).toLocaleString()}
                  </Typography>
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent className="dialog-form">
              <Box className="payment-summary">
                <Box><Typography color="text.secondary">Total</Typography><Typography fontWeight={900}>{money.format(n(selectedInvoice.total))}</Typography></Box>
                <Box><Typography color="text.secondary">Paid</Typography><Typography fontWeight={900}>{money.format(n(selectedInvoice.paid_amount))}</Typography></Box>
                <Box><Typography color="text.secondary">Due</Typography><Typography fontWeight={900}>{money.format(n(selectedInvoice.due_amount))}</Typography></Box>
                <Chip label={selectedInvoice.status} color={selectedInvoice.status === 'paid' ? 'success' : selectedInvoice.status === 'partial' ? 'warning' : 'default'} />
              </Box>

              {n(selectedInvoice.due_amount) > 0 ? (
                <Box className="payment-entry">
                  <TextField
                    required
                    type="number"
                    label="Payment amount"
                    value={newPaymentAmount}
                    onChange={(event) => setNewPaymentAmount(event.target.value)}
                    inputProps={{ min: 0.01, max: n(selectedInvoice.due_amount), step: 0.01 }}
                  />
                  <TextField select label="Method" value={newPaymentMethod} onChange={(event) => setNewPaymentMethod(event.target.value as typeof newPaymentMethod)}>
                    <MenuItem value="cash">Cash</MenuItem>
                    <MenuItem value="upi">UPI</MenuItem>
                    <MenuItem value="card">Card</MenuItem>
                    <MenuItem value="bank">Bank</MenuItem>
                  </TextField>
                  <TextField
                    label="Reference"
                    value={newPaymentReference}
                    onChange={(event) => setNewPaymentReference(event.target.value)}
                    className="payment-reference"
                  />
                </Box>
              ) : (
                <Alert severity="success">This invoice is fully paid. No further payment is due.</Alert>
              )}

              <Divider />
              <Typography fontWeight={900}>Payment history</Typography>
              {selectedInvoice.payments.length ? (
                <Stack spacing={1}>
                  {selectedInvoice.payments.map((payment, index) => (
                    <Box key={payment.id} className="payment-row">
                      <Box minWidth={0}>
                        <Typography fontWeight={800}>#{selectedInvoice.payments.length - index} {payment.method.toUpperCase()}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {new Date(payment.created_at).toLocaleString()}{payment.reference ? ` Â· ${payment.reference}` : ''}
                        </Typography>
                      </Box>
                      <Typography fontWeight={900}>{money.format(n(payment.amount))}</Typography>
                    </Box>
                  ))}
                </Stack>
              ) : (
                <Typography color="text.secondary">No payment received yet.</Typography>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setInvoiceOpen(false)}>Close</Button>
              {n(selectedInvoice.due_amount) > 0 && (
                <Button type="submit" variant="contained" startIcon={<PaymentsIcon />}>Add Payment</Button>
              )}
            </DialogActions>
          </Box>
        )}
      </Dialog>
    </Box>
  );
}

export default App;
