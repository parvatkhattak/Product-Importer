// API Base URL
const API_BASE = window.location.origin;

// State
let currentPage = 0;
const pageSize = 50;
let currentEditProductId = null;
let currentEditWebhookId = null;
let confirmCallback = null;
let uploadEventSource = null;

// DOM Elements
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const progressPercent = document.getElementById('progressPercent');
const progressDetails = document.getElementById('progressDetails');

const productsTableBody = document.getElementById('productsTableBody');
const searchInput = document.getElementById('searchInput');
const activeFilter = document.getElementById('activeFilter');
const prevPageBtn = document.getElementById('prevPage');
const nextPageBtn = document.getElementById('nextPage');
const pageInfo = document.getElementById('pageInfo');

const webhooksList = document.getElementById('webhooksList');

// Modals
const productModal = document.getElementById('productModal');
const webhookModal = document.getElementById('webhookModal');
const confirmModal = document.getElementById('confirmModal');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeUpload();
    initializeProducts();
    initializeWebhooks();
    loadProducts();
    loadWebhooks();
});

// ===== FILE UPLOAD =====
function initializeUpload() {
    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--primary-solid)';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '';
        const file = e.dataTransfer.files[0];
        if (file) handleFileUpload(file);
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFileUpload(file);
    });
}

async function handleFileUpload(file) {
    if (!file.name.endsWith('.csv')) {
        showNotification('Please select a CSV file', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        uploadArea.style.display = 'none';
        progressContainer.style.display = 'block';

        // Show simple uploading state
        progressFill.style.width = '50%';
        progressPercent.textContent = '';
        progressText.textContent = 'Uploading...';
        progressDetails.textContent = 'Please wait while we process your file';

        const response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            // Show completion
            progressFill.style.width = '100%';
            progressText.textContent = '✓ Upload Complete!';
            progressDetails.textContent = 'Your file has been imported successfully';

            showNotification('CSV imported successfully!', 'success');

            // Reset and reload after delay
            setTimeout(() => {
                resetUploadUI();
                loadProducts();
            }, 2000);
        } else {
            throw new Error(data.detail || 'Upload failed');
        }
    } catch (error) {
        progressText.textContent = '✗ Upload Failed';
        progressDetails.textContent = error.message;
        showNotification(error.message, 'error');
        setTimeout(resetUploadUI, 3000);
    }
}

function resetUploadUI() {
    uploadArea.style.display = 'block';
    progressContainer.style.display = 'none';
    progressFill.style.width = '0%';
    progressPercent.textContent = '0%';
    progressDetails.textContent = '';
    fileInput.value = '';
}

// ===== PRODUCTS =====
function initializeProducts() {
    document.getElementById('addProductBtn').addEventListener('click', openAddProductModal);
    document.getElementById('bulkDeleteBtn').addEventListener('click', handleBulkDelete);
    document.getElementById('closeProductModal').addEventListener('click', closeProductModal);
    document.getElementById('cancelProductBtn').addEventListener('click', closeProductModal);
    document.getElementById('productForm').addEventListener('submit', handleProductSubmit);

    searchInput.addEventListener('input', debounce(() => {
        currentPage = 0;
        loadProducts();
    }, 500));

    activeFilter.addEventListener('change', () => {
        currentPage = 0;
        loadProducts();
    });

    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 0) {
            currentPage--;
            loadProducts();
        }
    });

    nextPageBtn.addEventListener('click', () => {
        currentPage++;
        loadProducts();
    });

    productModal.addEventListener('click', (e) => {
        if (e.target === productModal) closeProductModal();
    });
}

async function loadProducts() {
    const search = searchInput.value;
    const active = activeFilter.value;
    const skip = currentPage * pageSize;

    const params = new URLSearchParams({
        skip: skip,
        limit: pageSize,
    });

    if (search) params.append('search', search);
    if (active) params.append('active', active);

    try {
        const response = await fetch(`${API_BASE}/api/products?${params}`);
        const data = await response.json();

        renderProducts(data.products);
        updatePagination(data.total, skip);
    } catch (error) {
        showNotification('Failed to load products', 'error');
    }
}

function renderProducts(products) {
    if (!products || products.length === 0) {
        productsTableBody.innerHTML = '<tr><td colspan="6" class="loading">No products found</td></tr>';
        return;
    }

    productsTableBody.innerHTML = products.map(product => `
        <tr>
            <td><strong>${escapeHtml(product.sku)}</strong></td>
            <td>${escapeHtml(product.name)}</td>
            <td>${escapeHtml(product.description || '-')}</td>
            <td>$${parseFloat(product.price).toFixed(2)}</td>
            <td>
                <span class="badge ${product.active ? 'badge-active' : 'badge-inactive'}">
                    ${product.active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <button class="action-btn" onclick="editProduct(${product.id})">✏️ Edit</button>
                <button class="action-btn" onclick="deleteProduct(${product.id})">🗑️ Delete</button>
            </td>
        </tr>
    `).join('');
}

function updatePagination(total, skip) {
    const currentPageNum = Math.floor(skip / pageSize) + 1;
    const totalPages = Math.ceil(total / pageSize);

    pageInfo.textContent = `Page ${currentPageNum} of ${totalPages || 1}`;
    prevPageBtn.disabled = currentPage === 0;
    nextPageBtn.disabled = skip + pageSize >= total;
}

function openAddProductModal() {
    currentEditProductId = null;
    document.getElementById('modalTitle').textContent = 'Add Product';
    document.getElementById('productForm').reset();
    document.getElementById('productActive').checked = true;
    productModal.classList.add('active');
}

async function editProduct(id) {
    try {
        const response = await fetch(`${API_BASE}/api/products/${id}`);
        const product = await response.json();

        currentEditProductId = id;
        document.getElementById('modalTitle').textContent = 'Edit Product';
        document.getElementById('productSku').value = product.sku;
        document.getElementById('productName').value = product.name;
        document.getElementById('productDescription').value = product.description || '';
        document.getElementById('productPrice').value = product.price;
        document.getElementById('productActive').checked = product.active;

        productModal.classList.add('active');
    } catch (error) {
        showNotification('Failed to load product', 'error');
    }
}

async function handleProductSubmit(e) {
    e.preventDefault();

    const data = {
        sku: document.getElementById('productSku').value,
        name: document.getElementById('productName').value,
        description: document.getElementById('productDescription').value || null,
        price: parseFloat(document.getElementById('productPrice').value),
        active: document.getElementById('productActive').checked
    };

    try {
        const url = currentEditProductId
            ? `${API_BASE}/api/products/${currentEditProductId}`
            : `${API_BASE}/api/products`;

        const method = currentEditProductId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showNotification(
                currentEditProductId ? 'Product updated!' : 'Product created!',
                'success'
            );
            closeProductModal();
            loadProducts();
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Operation failed', 'error');
        }
    } catch (error) {
        showNotification('Operation failed', 'error');
    }
}

async function deleteProduct(id) {
    showConfirmation(
        'Are you sure you want to delete this product?',
        async () => {
            try {
                const response = await fetch(`${API_BASE}/api/products/${id}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    showNotification('Product deleted!', 'success');
                    loadProducts();
                } else {
                    showNotification('Delete failed', 'error');
                }
            } catch (error) {
                showNotification('Delete failed', 'error');
            }
        }
    );
}

async function handleBulkDelete() {
    showConfirmation(
        '⚠️ Are you sure you want to delete ALL products? This action cannot be undone!',
        async () => {
            try {
                const response = await fetch(`${API_BASE}/api/products`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    const data = await response.json();
                    showNotification(`Deleted ${data.deleted} products`, 'success');
                    currentPage = 0;
                    loadProducts();
                } else {
                    showNotification('Bulk delete failed', 'error');
                }
            } catch (error) {
                showNotification('Bulk delete failed', 'error');
            }
        }
    );
}

function closeProductModal() {
    productModal.classList.remove('active');
    currentEditProductId = null;
}

// ===== WEBHOOKS =====
function initializeWebhooks() {
    document.getElementById('addWebhookBtn').addEventListener('click', openAddWebhookModal);
    document.getElementById('closeWebhookModal').addEventListener('click', closeWebhookModal);
    document.getElementById('cancelWebhookBtn').addEventListener('click', closeWebhookModal);
    document.getElementById('webhookForm').addEventListener('submit', handleWebhookSubmit);

    webhookModal.addEventListener('click', (e) => {
        if (e.target === webhookModal) closeWebhookModal();
    });
}

async function loadWebhooks() {
    try {
        const response = await fetch(`${API_BASE}/api/webhooks`);
        const webhooks = await response.json();
        renderWebhooks(webhooks);
    } catch (error) {
        showNotification('Failed to load webhooks', 'error');
    }
}

function renderWebhooks(webhooks) {
    if (!webhooks || webhooks.length === 0) {
        webhooksList.innerHTML = '<p class="loading">No webhooks configured</p>';
        return;
    }

    webhooksList.innerHTML = webhooks.map(webhook => `
        <div class="webhook-item">
            <div class="webhook-header">
                <div class="webhook-info">
                    <div class="webhook-url">${escapeHtml(webhook.url)}</div>
                    <div class="webhook-event">Event: ${escapeHtml(webhook.event_type)}</div>
                    <span class="badge ${webhook.enabled ? 'badge-active' : 'badge-inactive'}">
                        ${webhook.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                </div>
                <div class="webhook-actions">
                    <button class="action-btn" onclick="testWebhook(${webhook.id})">🧪 Test</button>
                    <button class="action-btn" onclick="editWebhook(${webhook.id})">✏️ Edit</button>
                    <button class="action-btn" onclick="deleteWebhook(${webhook.id})">🗑️ Delete</button>
                </div>
            </div>
        </div>
    `).join('');
}

function openAddWebhookModal() {
    currentEditWebhookId = null;
    document.getElementById('webhookForm').reset();
    document.getElementById('webhookEnabled').checked = true;
    webhookModal.classList.add('active');
}

async function editWebhook(id) {
    try {
        const response = await fetch(`${API_BASE}/api/webhooks/${id}`);
        const webhook = await response.json();

        currentEditWebhookId = id;
        document.getElementById('webhookUrl').value = webhook.url;
        document.getElementById('webhookEvent').value = webhook.event_type;
        document.getElementById('webhookEnabled').checked = webhook.enabled;

        webhookModal.classList.add('active');
    } catch (error) {
        showNotification('Failed to load webhook', 'error');
    }
}

async function handleWebhookSubmit(e) {
    e.preventDefault();

    const data = {
        url: document.getElementById('webhookUrl').value,
        event_type: document.getElementById('webhookEvent').value,
        enabled: document.getElementById('webhookEnabled').checked
    };

    try {
        const url = currentEditWebhookId
            ? `${API_BASE}/api/webhooks/${currentEditWebhookId}`
            : `${API_BASE}/api/webhooks`;

        const method = currentEditWebhookId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showNotification(
                currentEditWebhookId ? 'Webhook updated!' : 'Webhook created!',
                'success'
            );
            closeWebhookModal();
            loadWebhooks();
        } else {
            showNotification('Operation failed', 'error');
        }
    } catch (error) {
        showNotification('Operation failed', 'error');
    }
}

async function testWebhook(id) {
    try {
        showNotification('Testing webhook...', 'info');

        const response = await fetch(`${API_BASE}/api/webhooks/${id}/test`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            showNotification(
                `Webhook test successful! (${result.status_code}, ${result.response_time.toFixed(2)}s)`,
                'success'
            );
        } else {
            showNotification(`Webhook test failed: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification('Webhook test failed', 'error');
    }
}

async function deleteWebhook(id) {
    showConfirmation(
        'Are you sure you want to delete this webhook?',
        async () => {
            try {
                const response = await fetch(`${API_BASE}/api/webhooks/${id}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    showNotification('Webhook deleted!', 'success');
                    loadWebhooks();
                } else {
                    showNotification('Delete failed', 'error');
                }
            } catch (error) {
                showNotification('Delete failed', 'error');
            }
        }
    );
}

function closeWebhookModal() {
    webhookModal.classList.remove('active');
    currentEditWebhookId = null;
}

// ===== CONFIRMATION MODAL =====
function showConfirmation(message, callback) {
    document.getElementById('confirmMessage').textContent = message;
    confirmCallback = callback;
    confirmModal.classList.add('active');
}

document.getElementById('closeConfirmModal').addEventListener('click', closeConfirmModal);
document.getElementById('cancelConfirmBtn').addEventListener('click', closeConfirmModal);
document.getElementById('confirmActionBtn').addEventListener('click', () => {
    if (confirmCallback) confirmCallback();
    closeConfirmModal();
});

confirmModal.addEventListener('click', (e) => {
    if (e.target === confirmModal) closeConfirmModal();
});

function closeConfirmModal() {
    confirmModal.classList.remove('active');
    confirmCallback = null;
}

// ===== UTILITIES =====
function showNotification(message, type = 'info') {
    // Simple console notification for now
    console.log(`[${type.toUpperCase()}] ${message}`);

    // Could implement toast notifications here
    if (type === 'error') {
        alert(`Error: ${message}`);
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make functions global for onclick handlers
window.editProduct = editProduct;
window.deleteProduct = deleteProduct;
window.editWebhook = editWebhook;
window.testWebhook = testWebhook;
window.deleteWebhook = deleteWebhook;
