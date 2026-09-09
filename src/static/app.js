/**
 * Clean & Minimal Developer Console Controller
 * Module 12 Capstone E-Commerce API Explorer
 */

const STATE = {
  activeTab: 'catalog',
  token: null,
  user: {
    email: 'customer@example.com',
    role: 'customer',
    id: 2
  },
  products: [],
  cart: [],
  authMode: 'login'
};

const DEFAULT_CREDENTIALS = {
  customer: {
    email: 'customer@example.com',
    password: 'CustomerPassword123!'
  },
  admin: {
    email: 'admin@example.com',
    password: 'AdminPassword123!'
  }
};

const GRAPHQL_PRESETS = {
  products: `query GetAllProducts {
  products {
    id
    name
    category
    price
  }
}`,
  products_with_stock: `query GetProductDetails {
  products {
    id
    name
    price
    stock
    description
  }
}`,
  orders: `query GetUserOrders {
  orders(userId: 2) {
    id
    totalAmount
    status
    items {
      productId
      quantity
      unitPrice
      subtotal
      product {
        name
        category
      }
    }
  }
}`
};

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  await checkHealth();
  await switchPersona('customer');
  setGraphQLQuery('products');
  loadProducts();
});

// ---------------------------------------------------------------------------
// Health Check & Telemetry
// ---------------------------------------------------------------------------
async function checkHealth() {
  const dot = document.querySelector('.status-dot');
  const text = document.getElementById('health-text');
  const telemetryEl = document.getElementById('telemetry-json');

  try {
    const res = await fetch('/health');
    if (res.ok) {
      const data = await res.json();
      dot.className = 'status-dot';
      text.textContent = 'API Online (200 OK)';
      if (telemetryEl) {
        telemetryEl.textContent = JSON.stringify(data, null, 2);
      }
    } else {
      dot.className = 'status-dot error';
      text.textContent = `Health Error (${res.status})`;
    }
  } catch (err) {
    dot.className = 'status-dot error';
    text.textContent = 'API Disconnected';
    if (telemetryEl) {
      telemetryEl.textContent = 'Error contacting backend service.';
    }
  }
}

// ---------------------------------------------------------------------------
// Persona Switching & Authentication
// ---------------------------------------------------------------------------
async function switchPersona(persona) {
  document.querySelectorAll('.btn-persona').forEach(btn => btn.classList.remove('active'));
  const targetBtn = document.getElementById(`btn-persona-${persona}`);
  if (targetBtn) targetBtn.classList.add('active');

  const creds = DEFAULT_CREDENTIALS[persona];
  if (!creds) return;

  try {
    const res = await fetch('/api/v1/users/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(creds)
    });

    if (!res.ok) {
      const err = await res.json();
      showToast(`Login failed: ${err.error?.message || 'Unauthorized'}`, 'error');
      return;
    }

    const data = await res.json();
    STATE.token = data.access_token;
    STATE.user.email = creds.email;
    STATE.user.role = persona;
    STATE.user.id = (persona === 'admin') ? 1 : 2;

    updateUserUI();
    showToast(`Switched persona to ${persona.toUpperCase()}`);

    // If currently on orders or admin tab, refresh
    if (STATE.activeTab === 'orders') loadOrders();
    if (STATE.activeTab === 'admin') updateAdminTabState();
  } catch (err) {
    showToast(`Error authenticating persona: ${err.message}`, 'error');
  }
}

function updateUserUI() {
  const emailEl = document.getElementById('current-user-email');
  const roleEl = document.getElementById('current-user-role');
  const avatarEl = document.getElementById('user-avatar');
  const authSummaryEl = document.getElementById('summary-auth-user');

  if (emailEl) emailEl.textContent = STATE.user.email;
  if (authSummaryEl) authSummaryEl.textContent = STATE.user.email;
  if (avatarEl) avatarEl.textContent = STATE.user.email.charAt(0).toUpperCase();

  if (roleEl) {
    roleEl.textContent = STATE.user.role.toUpperCase();
    roleEl.className = `role-badge role-${STATE.user.role}`;
  }

  updateAdminTabState();
}

function updateAdminTabState() {
  const notice = document.getElementById('admin-forbidden-notice');
  const roleNotice = document.getElementById('notice-role-name');
  const formBtn = document.getElementById('btn-create-prod');

  if (STATE.user.role !== 'admin') {
    if (notice) notice.style.display = 'block';
    if (roleNotice) roleNotice.textContent = STATE.user.role.toUpperCase();
    if (formBtn) formBtn.textContent = 'Create Product (Will fail with 403)';
  } else {
    if (notice) notice.style.display = 'none';
    if (formBtn) formBtn.textContent = 'Create Product';
  }
}

// ---------------------------------------------------------------------------
// Tab Navigation
// ---------------------------------------------------------------------------
function switchTab(tabId) {
  STATE.activeTab = tabId;

  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

  const btn = document.getElementById(`tab-btn-${tabId}`);
  const pane = document.getElementById(`tab-${tabId}`);

  if (btn) btn.classList.add('active');
  if (pane) pane.classList.add('active');

  if (tabId === 'catalog') loadProducts();
  if (tabId === 'cart') renderCart();
  if (tabId === 'orders') loadOrders();
  if (tabId === 'admin') updateAdminTabState();
  if (tabId === 'docs') checkHealth();
}

// ---------------------------------------------------------------------------
// Product Catalog
// ---------------------------------------------------------------------------
async function loadProducts() {
  const categoryFilter = document.getElementById('catalog-category-filter')?.value;
  let url = '/api/v1/products/';
  if (categoryFilter) {
    url += `?category=${encodeURIComponent(categoryFilter)}`;
  }

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    STATE.products = await res.json();
    renderCatalog();
  } catch (err) {
    const grid = document.getElementById('catalog-grid');
    if (grid) grid.innerHTML = `<div class="empty-state"><p>Error loading catalog: ${err.message}</p></div>`;
  }
}

function renderCatalog() {
  const grid = document.getElementById('catalog-grid');
  const search = document.getElementById('catalog-search')?.value.toLowerCase() || '';

  if (!grid) return;

  const filtered = STATE.products.filter(p => {
    return p.name.toLowerCase().includes(search) || 
           (p.description && p.description.toLowerCase().includes(search)) ||
           p.category.toLowerCase().includes(search);
  });

  if (filtered.length === 0) {
    grid.innerHTML = `<div class="empty-state" style="grid-column: 1/-1;"><p>No products match your search query.</p></div>`;
    return;
  }

  grid.innerHTML = filtered.map(p => {
    const stockClass = p.stock === 0 ? 'out' : p.stock < 10 ? 'low' : '';
    const stockLabel = p.stock === 0 ? 'Out of Stock' : `${p.stock} in stock`;
    const isOut = p.stock === 0;

    return `
      <div class="product-card" id="product-card-${p.id}">
        <div class="product-top">
          <div>
            <span class="product-category-tag">${escapeHtml(p.category)}</span>
            <h3 class="product-name">${escapeHtml(p.name)}</h3>
          </div>
        </div>
        <p class="product-desc">${escapeHtml(p.description || 'No description available.')}</p>
        <div class="product-bottom">
          <div>
            <div class="product-price">$${p.price.toFixed(2)}</div>
            <span class="stock-badge ${stockClass}">● ${stockLabel}</span>
          </div>
          <div class="product-actions">
            <input type="number" id="qty-${p.id}" class="qty-input" value="1" min="1" max="${p.stock}" ${isOut ? 'disabled' : ''}>
            <button class="btn btn-primary btn-sm" onclick="addToCart(${p.id})" ${isOut ? 'disabled' : ''}>
              Add to Cart
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ---------------------------------------------------------------------------
// Cart & Checkout
// ---------------------------------------------------------------------------
function addToCart(productId) {
  const product = STATE.products.find(p => p.id === productId);
  if (!product) return;

  const qtyInput = document.getElementById(`qty-${productId}`);
  const qty = parseInt(qtyInput?.value || '1', 10);

  if (qty <= 0 || isNaN(qty)) {
    showToast('Please enter a valid quantity.', 'error');
    return;
  }

  const existing = STATE.cart.find(item => item.productId === productId);
  const currentInCart = existing ? existing.quantity : 0;

  if (currentInCart + qty > product.stock) {
    showToast(`Cannot add ${qty} units. Only ${product.stock} available in stock.`, 'error');
    return;
  }

  if (existing) {
    existing.quantity += qty;
  } else {
    STATE.cart.push({
      productId: product.id,
      name: product.name,
      price: product.price,
      quantity: qty,
      stock: product.stock
    });
  }

  updateCartBadge();
  showToast(`Added ${qty} × ${product.name} to cart.`);
}

function updateCartBadge() {
  const badge = document.getElementById('nav-cart-badge');
  const count = STATE.cart.reduce((sum, item) => sum + item.quantity, 0);
  if (badge) badge.textContent = count;
}

function renderCart() {
  const tbody = document.getElementById('cart-items-tbody');
  const emptyMsg = document.getElementById('cart-empty-message');
  const tableWrapper = document.getElementById('cart-table-wrapper');
  const checkoutBtn = document.getElementById('btn-checkout');
  const itemsCountEl = document.getElementById('summary-items-count');
  const grandTotalEl = document.getElementById('summary-grand-total');

  if (STATE.cart.length === 0) {
    if (emptyMsg) emptyMsg.style.display = 'block';
    if (tableWrapper) tableWrapper.style.display = 'none';
    if (checkoutBtn) checkoutBtn.disabled = true;
    if (itemsCountEl) itemsCountEl.textContent = '0 items';
    if (grandTotalEl) grandTotalEl.textContent = '$0.00';
    return;
  }

  if (emptyMsg) emptyMsg.style.display = 'none';
  if (tableWrapper) tableWrapper.style.display = 'block';
  if (checkoutBtn) checkoutBtn.disabled = false;

  let totalItems = 0;
  let grandTotal = 0;

  tbody.innerHTML = STATE.cart.map((item, idx) => {
    const subtotal = item.price * item.quantity;
    totalItems += item.quantity;
    grandTotal += subtotal;

    return `
      <tr>
        <td><strong>${escapeHtml(item.name)}</strong></td>
        <td>$${item.price.toFixed(2)}</td>
        <td>
          <div style="display: flex; gap: 4px; align-items: center;">
            <button class="btn-xs" onclick="changeCartQty(${idx}, -1)">-</button>
            <span style="font-family: var(--font-mono); padding: 0 4px;">${item.quantity}</span>
            <button class="btn-xs" onclick="changeCartQty(${idx}, 1)">+</button>
          </div>
        </td>
        <td style="font-family: var(--font-mono); font-weight: 600;">$${subtotal.toFixed(2)}</td>
        <td>
          <button class="btn btn-secondary btn-xs" onclick="removeFromCart(${idx})">Remove</button>
        </td>
      </tr>
    `;
  }).join('');

  if (itemsCountEl) itemsCountEl.textContent = `${totalItems} items`;
  if (grandTotalEl) grandTotalEl.textContent = `$${grandTotal.toFixed(2)}`;
}

function changeCartQty(index, delta) {
  const item = STATE.cart[index];
  if (!item) return;

  const newQty = item.quantity + delta;
  if (newQty <= 0) {
    removeFromCart(index);
    return;
  }

  if (newQty > item.stock) {
    showToast(`Only ${item.stock} units available in inventory.`, 'error');
    return;
  }

  item.quantity = newQty;
  updateCartBadge();
  renderCart();
}

function removeFromCart(index) {
  STATE.cart.splice(index, 1);
  updateCartBadge();
  renderCart();
}

function clearCart() {
  STATE.cart = [];
  updateCartBadge();
  renderCart();
  const receiptBox = document.getElementById('checkout-receipt');
  if (receiptBox) receiptBox.style.display = 'none';
  showToast('Cart cleared.');
}

async function performCheckout() {
  if (STATE.cart.length === 0) {
    showToast('Your cart is empty.', 'error');
    return;
  }

  if (!STATE.token) {
    showToast('You must be logged in to place an order.', 'error');
    return;
  }

  const payload = {
    items: STATE.cart.map(item => ({
      product_id: item.productId,
      quantity: item.quantity
    }))
  };

  const checkoutBtn = document.getElementById('btn-checkout');
  if (checkoutBtn) checkoutBtn.disabled = true;

  try {
    const res = await fetch('/api/v1/orders/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${STATE.token}`
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
      showToast(`Checkout Error: ${data.error?.message || 'Failed to place order.'}`, 'error');
      if (checkoutBtn) checkoutBtn.disabled = false;
      return;
    }

    // Success! Show receipt
    STATE.cart = [];
    updateCartBadge();
    renderCart();

    const receiptBox = document.getElementById('checkout-receipt');
    const receiptJson = document.getElementById('receipt-json');
    if (receiptBox && receiptJson) {
      receiptJson.textContent = JSON.stringify(data, null, 2);
      receiptBox.style.display = 'block';
    }

    showToast(`Order #${data.id} confirmed successfully! Total: $${data.total_amount.toFixed(2)}`);
    loadProducts(); // Refresh stocks
  } catch (err) {
    showToast(`Network error: ${err.message}`, 'error');
    if (checkoutBtn) checkoutBtn.disabled = false;
  }
}

// ---------------------------------------------------------------------------
// Orders & BOLA Check
// ---------------------------------------------------------------------------
async function loadOrders() {
  const container = document.getElementById('orders-list-container');
  if (!container) return;

  if (!STATE.token) {
    container.innerHTML = `<div class="empty-state"><p>Please authenticate first.</p></div>`;
    return;
  }

  container.innerHTML = `<div class="loading-state">Loading order history for ${escapeHtml(STATE.user.email)}...</div>`;

  try {
    const res = await fetch('/api/v1/orders/', {
      headers: {
        'Authorization': `Bearer ${STATE.token}`
      }
    });

    if (!res.ok) {
      const err = await res.json();
      container.innerHTML = `<div class="empty-state"><p>Error fetching orders: ${escapeHtml(err.error?.message || res.statusText)}</p></div>`;
      return;
    }

    const orders = await res.json();

    if (orders.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <p>No orders found for this user account.</p>
          <button class="btn btn-primary" onclick="switchTab('catalog')">Place Your First Order</button>
        </div>
      `;
      return;
    }

    container.innerHTML = orders.map(order => `
      <div class="order-card">
        <div class="order-card-header">
          <div>
            <span class="order-id-label">Order #${order.id}</span>
            <span style="font-size: 11px; color: var(--text-muted); margin-left: 8px;">User ID: ${order.user_id}</span>
          </div>
          <span class="role-badge role-customer">${order.status}</span>
        </div>
        <ul class="order-items-list">
          ${order.items.map(item => `
            <li class="order-item-row">
              <span>Product ID ${item.product_id} (×${item.quantity} @ $${item.unit_price.toFixed(2)})</span>
              <span style="font-family: var(--font-mono); font-weight: 500;">$${item.subtotal.toFixed(2)}</span>
            </li>
          `).join('')}
        </ul>
        <div class="summary-divider"></div>
        <div class="order-item-row" style="font-size: 13px; font-weight: 600; color: var(--text-primary);">
          <span>Total Order Value</span>
          <span style="font-family: var(--font-mono); color: var(--accent-success);">$${order.total_amount.toFixed(2)}</span>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><p>Error: ${err.message}</p></div>`;
  }
}

// ---------------------------------------------------------------------------
// Admin Product Creation
// ---------------------------------------------------------------------------
async function handleCreateProduct(e) {
  e.preventDefault();

  const payload = {
    name: document.getElementById('prod-name').value.trim(),
    category: document.getElementById('prod-category').value,
    price: parseFloat(document.getElementById('prod-price').value),
    stock: parseInt(document.getElementById('prod-stock').value, 10),
    description: document.getElementById('prod-desc').value.trim()
  };

  try {
    const res = await fetch('/api/v1/products/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${STATE.token}`
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
      showToast(`Admin Error (${res.status}): ${data.error?.message || 'Access Forbidden'}`, 'error');
      return;
    }

    showToast(`Product '${data.name}' created with ID #${data.id}!`);
    document.getElementById('admin-product-form').reset();
    loadProducts();
  } catch (err) {
    showToast(`Network error: ${err.message}`, 'error');
  }
}

// ---------------------------------------------------------------------------
// GraphQL Studio
// ---------------------------------------------------------------------------
function setGraphQLQuery(key) {
  const query = GRAPHQL_PRESETS[key] || '';
  const input = document.getElementById('graphql-query-input');
  if (input) input.value = query;
}

async function executeGraphQL() {
  const query = document.getElementById('graphql-query-input')?.value.trim();
  const output = document.getElementById('graphql-response-output');
  const tag = document.getElementById('graphql-status-tag');

  if (!query) {
    showToast('Please provide a GraphQL query document.', 'error');
    return;
  }

  tag.textContent = 'Executing...';
  const startTime = performance.now();

  try {
    const headers = { 'Content-Type': 'application/json' };
    if (STATE.token) headers['Authorization'] = `Bearer ${STATE.token}`;

    const res = await fetch('/graphql', {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({ query: query })
    });

    const elapsed = Math.round(performance.now() - startTime);
    const data = await res.json();

    tag.textContent = `${res.status} OK (${elapsed}ms)`;
    if (output) output.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    tag.textContent = 'Error';
    if (output) output.textContent = `GraphQL Execution Error:\n${err.message}`;
  }
}

// ---------------------------------------------------------------------------
// Custom Auth Modal
// ---------------------------------------------------------------------------
function openAuthModal() {
  const modal = document.getElementById('auth-modal');
  if (modal) modal.style.display = 'flex';
}

function closeAuthModal() {
  const modal = document.getElementById('auth-modal');
  if (modal) modal.style.display = 'none';
}

function toggleAuthMode(mode) {
  STATE.authMode = mode;
  document.getElementById('auth-tab-login').classList.toggle('active', mode === 'login');
  document.getElementById('auth-tab-register').classList.toggle('active', mode === 'register');

  document.getElementById('auth-name-group').style.display = (mode === 'register') ? 'block' : 'none';
  document.getElementById('auth-role-group').style.display = (mode === 'register') ? 'block' : 'none';
  document.getElementById('btn-auth-submit').textContent = (mode === 'register') ? 'Create Account' : 'Login';
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const email = document.getElementById('auth-email').value.trim();
  const password = document.getElementById('auth-password').value;

  if (STATE.authMode === 'register') {
    const fullName = document.getElementById('auth-name').value.trim();
    const role = document.getElementById('auth-role').value;

    try {
      const res = await fetch('/api/v1/users/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          full_name: fullName,
          password: password,
          role: role
        })
      });

      const data = await res.json();
      if (!res.ok) {
        showToast(`Registration failed: ${data.error?.message || 'Error'}`, 'error');
        return;
      }

      showToast('Registration successful! Logging in...');
    } catch (err) {
      showToast(`Error: ${err.message}`, 'error');
      return;
    }
  }

  // Perform Login
  try {
    const res = await fetch('/api/v1/users/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, password: password })
    });

    const data = await res.json();
    if (!res.ok) {
      showToast(`Login failed: ${data.error?.message || 'Invalid credentials'}`, 'error');
      return;
    }

    STATE.token = data.access_token;
    STATE.user.email = email;
    STATE.user.role = (email.includes('admin')) ? 'admin' : 'customer';

    // Fetch user profile from /me
    try {
      const meRes = await fetch('/api/v1/users/me', {
        headers: { 'Authorization': `Bearer ${STATE.token}` }
      });
      if (meRes.ok) {
        const meData = await meRes.json();
        STATE.user.role = meData.role;
        STATE.user.id = meData.id;
      }
    } catch (_) {}

    updateUserUI();
    closeAuthModal();
    showToast(`Logged in as ${email}`);
  } catch (err) {
    showToast(`Network error: ${err.message}`, 'error');
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, function(m) {
    return {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    }[m];
  });
}
