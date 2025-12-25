/**
 * Dashboard Async Loading Module
 * Handles asynchronous data loading with skeleton screens and error handling
 */

class DashboardLoader {
    constructor() {
        this.startDate = null;
        this.endDate = null;
        this.loadingTimeout = 30000; // 30 second timeout
        this.errors = {};
    }

    /**
     * Initialize the dashboard loader
     */
    init() {
        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');
        const filterForm = document.getElementById('dashboard-filter-form');

        if (startDateInput && endDateInput) {
            this.startDate = startDateInput.value;
            this.endDate = endDateInput.value;
        }

        // Attach event listeners to filter inputs
       /* if (startDateInput) {
            startDateInput.addEventListener('change', () => this.handleFilterChange());
        }
        if (endDateInput) {
            endDateInput.addEventListener('change', () => this.handleFilterChange());
        }*/

        // Attach form submission handler
        if (filterForm) {
            filterForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFilterChange();
            });
        }

        // Load initial data
        this.loadAllData();
    }

    /**
     * Handle filter date changes
     */
    handleFilterChange() {
        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');

        this.startDate = startDateInput.value;
        this.endDate = endDateInput.value;
        this.errors = {}; // Clear previous errors

        // Clear error messages
        document.querySelectorAll('.error-message').forEach(msg => msg.remove());

        this.loadAllData();
    }

    /**
     * Load all dashboard data with proper sequencing
     * Balance difference loads first, then transactions and crypto in parallel
     */
    async loadAllData() {
        // Show all skeleton loaders
        this.showSkeletons();

        try {
            // Load balance difference first (highest priority)
            await this.loadBalanceDifference();

            // Load transactions and crypto variation in parallel
            await Promise.all([
                this.loadTransactions(),
                this.loadCryptoVariation()
            ]);

            // Calculate and display total profit
            this.calculateTotalProfit();
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showErrorMessage('Failed to load dashboard data. Please try again.');
        }
    }

    /**
     * Show skeleton loaders for all sections
     */
    showSkeletons() {
        this.showBalanceSkeleton();
        this.showTransactionsSkeleton();
        this.showCryptoVariationSkeleton();
    }

    /**
     * Load balance difference data
     */
    async loadBalanceDifference() {
        const container = document.getElementById('balance-difference-container');
        if (!container) return;

        try {
            const response = await this.fetchWithTimeout(
                `/dashboard/api/balance?start_date=${this.startDate}&end_date=${this.endDate}`,
                this.loadingTimeout
            );

            if (!response.success) {
                throw new Error(response.error || 'Failed to load balance data');
            }

            const data = response.data;
            this.renderBalanceDifference(data);
            delete this.errors.balance;
        } catch (error) {
            console.error('Error loading balance difference:', error);
            this.errors.balance = error.message;
            this.showBalanceError(error.message);
        }
    }

    /**
     * Load investor transactions data
     */
    async loadTransactions() {
        const container = document.getElementById('transactions-container');
        if (!container) return;

        try {
            const response = await this.fetchWithTimeout(
                `/dashboard/api/transactions?start_date=${this.startDate}&end_date=${this.endDate}`,
                this.loadingTimeout
            );

            if (!response.success) {
                throw new Error(response.error || 'Failed to load transactions data');
            }

            const data = response.data;
            this.renderTransactions(data);
            delete this.errors.transactions;
        } catch (error) {
            console.error('Error loading transactions:', error);
            this.errors.transactions = error.message;
            this.showTransactionsError(error.message);
        }
    }

    /**
     * Load crypto variation data
     */
    async loadCryptoVariation() {
        const container = document.getElementById('crypto-variation-container');
        if (!container) return;

        try {
            const response = await this.fetchWithTimeout(
                `/dashboard/api/crypto-variation?start_date=${this.startDate}&end_date=${this.endDate}`,
                this.loadingTimeout
            );

            if (!response.success) {
                throw new Error(response.error || 'Failed to load crypto variation data');
            }

            const data = response.data;
            this.renderCryptoVariation(data);
            delete this.errors.crypto;
        } catch (error) {
            console.error('Error loading crypto variation:', error);
            this.errors.crypto = error.message;
            this.showCryptoVariationError(error.message);
        }
    }

    /**
     * Fetch with timeout support
     */
    async fetchWithTimeout(url, timeout = 30000) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(url, {
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timeout - calculation took too long');
            }
            throw error;
        }
    }

    /**
     * Render balance difference data
     */
    renderBalanceDifference(data) {
        const balanceSummary = document.getElementById('balance-summary-card');
        const balanceDetails = document.getElementById('balance-details-container');

        if (balanceSummary) {
            const balanceDiff = parseFloat(data.balance_difference);
            const isPositive = balanceDiff >= 0;
            const textColor = isPositive ? 'text-success' : 'text-danger';
            const iconColor = isPositive ? 'success' : 'danger';
            const iconName = isPositive ? 'arrow-up-circle' : 'arrow-down-circle';

            balanceSummary.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="text-muted text-uppercase small mb-2">Balance Difference</h6>
                        <h3 class="mb-0 ${textColor}">
                            ${this.formatCurrency(balanceDiff)}
                        </h3>
                    </div>
                    <div class="bg-primary bg-opacity-10 rounded p-2">
                        <i class="bi bi-wallet2 text-primary fs-4"></i>
                    </div>
                </div>
                <small class="text-muted d-block mt-2">End: ${this.formatCurrency(data.end_balance_sum)}</small>
            `;
        }

        if (balanceDetails) {
            balanceDetails.innerHTML = `
                <div class="row g-3">
                    <div class="col-md-4">
                        <div class="p-3 bg-light rounded">
                            <small class="text-muted d-block mb-1">Start Balance</small>
                            <h5 class="mb-0">${this.formatCurrency(data.start_balance_sum)}</h5>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="p-3 bg-light rounded">
                            <small class="text-muted d-block mb-1">End Balance</small>
                            <h5 class="mb-0">${this.formatCurrency(data.end_balance_sum)}</h5>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="p-3 bg-light rounded">
                            <small class="text-muted d-block mb-1">Difference</small>
                            <h5 class="mb-0 ${parseFloat(data.balance_difference) >= 0 ? 'text-success' : 'text-danger'}">
                                ${this.formatCurrency(data.balance_difference)}
                            </h5>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Render investor transactions data
     */
    renderTransactions(data) {
        const transactionsSummary = document.getElementById('transactions-summary-card');
        const transactionsTable = document.getElementById('transactions-table-container');
        const transactionsFooter = document.getElementById('transactions-footer');

        if (transactionsSummary) {
            const transDiff = parseFloat(data.transactions_difference);
            const isPositive = transDiff >= 0;

            transactionsSummary.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="text-muted text-uppercase small mb-2">Transactions</h6>
                        <h3 class="mb-0 ${isPositive ? 'text-success' : 'text-danger'}">
                            ${this.formatCurrency(transDiff)}
                        </h3>
                    </div>
                    <div class="bg-info bg-opacity-10 rounded p-2">
                        <i class="bi bi-arrow-left-right text-info fs-4"></i>
                    </div>
                </div>
                <small class="text-muted d-block mt-2">${data.investor_transactions.length} transaction(s)</small>
            `;
        }

        if (transactionsTable) {
            const transactions = data.investor_transactions;

            if (transactions.length === 0) {
                transactionsTable.innerHTML = `
                    <div class="text-center py-5 text-muted">
                        <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                        <p>No transactions found for the selected period</p>
                    </div>
                `;
            } else {
                let tableHTML = `
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th class="border-0">ID</th>
                                    <th class="border-0">Date/Time</th>
                                    <th class="border-0">Type</th>
                                    <th class="border-0 text-end">Cash Amount</th>
                                    <th class="border-0">Currency</th>
                                    <th class="border-0 text-end">Kind Amount</th>
                                    <th class="border-0">Kind Currency</th>
                                    <th class="border-0">Investor</th>
                                    <th class="border-0 text-end">NAV</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                transactions.forEach(tx => {
                    const typeColor = tx.transaction_type === 'Deposit' ? 'success' : tx.transaction_type === 'Withdrawal' ? 'danger' : 'info';
                    tableHTML += `
                        <tr>
                            <td><span class="badge bg-secondary">#${tx.id}</span></td>
                            <td>${tx.effective_datetime}</td>
                            <td>
                                <span class="badge bg-${typeColor}">
                                    ${tx.transaction_type}
                                </span>
                            </td>
                            <td class="text-end fw-semibold">${this.formatCurrency(tx.cash_amount)}</td>
                            <td><span class="badge bg-secondary">${tx.cash_currency_code}</span></td>
                            <td class="text-end">${tx.kind_amount ? this.formatNumber(tx.kind_amount, 4) : '-'}</td>
                            <td><span class="badge bg-secondary">${tx.kind_currency_code || '-'}</span></td>
                            <td>${tx.investor_alias || '-'}</td>
                            <td class="text-end">${tx.transaction_nav ? this.formatNumber(tx.transaction_nav, 4) : '-'}</td>
                        </tr>
                    `;
                });

                tableHTML += `
                            </tbody>
                        </table>
                    </div>
                `;

                transactionsTable.innerHTML = tableHTML;
            }
        }

        if (transactionsFooter) {
            const transDiff = parseFloat(data.transactions_difference);
            transactionsFooter.innerHTML = `
                <small class="text-muted">
                    <strong>Total Difference:</strong> 
                    <span class="${transDiff >= 0 ? 'text-success' : 'text-danger'}">
                        ${this.formatCurrency(transDiff)}
                    </span>
                </small>
            `;
        }
    }

    /**
     * Render crypto variation data
     */
    renderCryptoVariation(data) {
        const cryptoSummary = document.getElementById('crypto-summary-card');
        const cryptoTable = document.getElementById('crypto-variation-table-container');
        const cryptoFooter = document.getElementById('crypto-variation-footer');

        if (cryptoSummary) {
            const cryptoVar = parseFloat(data.total_variation);
            const isPositive = cryptoVar >= 0;

            cryptoSummary.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="text-muted text-uppercase small mb-2">Crypto Variation</h6>
                        <h3 class="mb-0 ${isPositive ? 'text-success' : 'text-danger'}">
                            ${this.formatCurrency(cryptoVar)}
                        </h3>
                    </div>
                    <div class="bg-warning bg-opacity-10 rounded p-2">
                        <i class="bi bi-currency-bitcoin text-warning fs-4"></i>
                    </div>
                </div>
                <small class="text-muted d-block mt-2">${data.variations_by_currency.length} currency(ies)</small>
            `;
        }

        if (cryptoTable) {
            const variations = data.variations_by_currency;

            if (variations.length === 0) {
                cryptoTable.innerHTML = `
                    <div class="text-center py-5 text-muted">
                        <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                        <p>No crypto variations found for the selected period</p>
                    </div>
                `;
            } else {
                let tableHTML = `
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th class="border-0">Currency</th>
                                    <th class="border-0 text-end">Amount</th>
                                    <th class="border-0 text-end">Start Price</th>
                                    <th class="border-0 text-end">End Price</th>
                                    <th class="border-0 text-end">Price Change</th>
                                    <th class="border-0 text-end">Variation</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                variations.forEach(variation => {
                    const priceChange = variation.end_price - variation.start_price;
                    const pricePct = variation.start_price > 0 
                        ? ((variation.end_price - variation.start_price) / variation.start_price * 100)
                        : 0;
                    const priceColor = priceChange >= 0 ? 'text-success' : 'text-danger';
                    const variationColor = variation.variation >= 0 ? 'text-success' : 'text-danger';

                    tableHTML += `
                        <tr>
                            <td>
                                <span class="badge bg-warning text-dark">${variation.currency_code}</span>
                            </td>
                            <td class="text-end">${this.formatNumber(variation.amount, 4)}</td>
                            <td class="text-end">${this.formatCurrency(variation.start_price)}</td>
                            <td class="text-end">${this.formatCurrency(variation.end_price)}</td>
                            <td class="text-end">
                                <span class="${priceColor}">
                                    ${this.formatCurrency(priceChange)}
                                    <small>(${this.formatNumber(pricePct, 2)}%)</small>
                                </span>
                            </td>
                            <td class="text-end fw-semibold ${variationColor}">
                                ${this.formatCurrency(variation.variation)}
                            </td>
                        </tr>
                    `;
                });

                tableHTML += `
                            </tbody>
                        </table>
                    </div>
                `;

                cryptoTable.innerHTML = tableHTML;
            }
        }

        if (cryptoFooter) {
            const cryptoVar = parseFloat(data.total_variation);
            cryptoFooter.innerHTML = `
                <small class="text-muted">
                    <strong>Total Variation:</strong> 
                    <span class="${cryptoVar >= 0 ? 'text-success' : 'text-danger'}">
                        ${this.formatCurrency(cryptoVar)}
                    </span>
                </small>
            `;
        }
    }

    /**
     * Calculate and display total profit
     */
    calculateTotalProfit() {
        const balanceElement = document.getElementById('balance-summary-card');
        const transElement = document.getElementById('transactions-summary-card');
        const cryptoElement = document.getElementById('crypto-summary-card');
        const totalProfitCard = document.getElementById('total-profit-card');

        if (!balanceElement || !transElement || !cryptoElement || !totalProfitCard) {
            return;
        }

        // Extract values from rendered HTML
        const balanceText = balanceElement.querySelector('h3');
        const transText = transElement.querySelector('h3');
        const cryptoText = cryptoElement.querySelector('h3');

        if (!balanceText || !transText || !cryptoText) {
            return;
        }

        const balance = this.parseCurrency(balanceText.textContent);
        const trans = this.parseCurrency(transText.textContent);
        const crypto = this.parseCurrency(cryptoText.textContent);

        const totalProfit = balance - trans - crypto;
        const isPositive = totalProfit >= 0;
        const textColor = isPositive ? 'text-success' : 'text-danger';
        const iconColor = isPositive ? 'success' : 'danger';
        const iconName = isPositive ? 'arrow-up-circle' : 'arrow-down-circle';

        totalProfitCard.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h6 class="text-muted text-uppercase small mb-2">Total Profit</h6>
                    <h3 class="mb-0 ${textColor}">
                        ${this.formatCurrency(totalProfit)}
                    </h3>
                </div>
                <div class="bg-${iconColor} bg-opacity-10 rounded p-2">
                    <i class="bi bi-${iconName} text-${iconColor} fs-4"></i>
                </div>
            </div>
            <small class="text-muted d-block mt-2">Balance Diff - Transactions - Crypto Variation</small>
        `;
    }

    /**
     * Show skeleton for balance section
     */
    showBalanceSkeleton() {
        const balanceSummary = document.getElementById('balance-summary-card');
        const balanceDetails = document.getElementById('balance-details-container');

        if (balanceSummary) {
            balanceSummary.innerHTML = `
                <div class="skeleton-card" style="height: 120px;"></div>
            `;
        }

        if (balanceDetails) {
            balanceDetails.innerHTML = `
                <div class="row g-3">
                    <div class="col-md-4">
                        <div class="p-3 bg-light rounded">
                            <div class="skeleton skeleton-text" style="margin-bottom: 1rem;"></div>
                            <div class="skeleton skeleton-heading" style="width: 100%;"></div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="p-3 bg-light rounded">
                            <div class="skeleton skeleton-text" style="margin-bottom: 1rem;"></div>
                            <div class="skeleton skeleton-heading" style="width: 100%;"></div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="p-3 bg-light rounded">
                            <div class="skeleton skeleton-text" style="margin-bottom: 1rem;"></div>
                            <div class="skeleton skeleton-heading" style="width: 100%;"></div>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Show skeleton for transactions section
     */
    showTransactionsSkeleton() {
        const transactionsSummary = document.getElementById('transactions-summary-card');
        const transactionsTable = document.getElementById('transactions-table-container');

        if (transactionsSummary) {
            transactionsSummary.innerHTML = `
                <div class="skeleton-card" style="height: 120px;"></div>
            `;
        }

        if (transactionsTable) {
            transactionsTable.innerHTML = `
                <div class="skeleton skeleton-table-row">
                    <div class="skeleton-table-cell"></div>
                    <div class="skeleton-table-cell"></div>
                    <div class="skeleton-table-cell"></div>
                </div>
                <div class="skeleton skeleton-table-row">
                    <div class="skeleton-table-cell"></div>
                    <div class="skeleton-table-cell"></div>
                    <div class="skeleton-table-cell"></div>
                </div>
                <div class="skeleton skeleton-table-row">
                    <div class="skeleton-table-cell"></div>
                    <div class="skeleton-table-cell"></div>
                    <div class="skeleton-table-cell"></div>
                </div>
            `;
        }
    }

    /**
     * Show skeleton for crypto variation section
     */
    showCryptoVariationSkeleton() {
        const cryptoSummary = document.getElementById('crypto-summary-card');
        const cryptoTable = document.getElementById('crypto-variation-table-container');

        if (cryptoSummary) {
            cryptoSummary.innerHTML = `
                <div class="skeleton-card" style="height: 120px;"></div>
            `;
        }

        if (cryptoTable) {
            cryptoTable.innerHTML = `
                <div class="skeleton skeleton-table-row">
                    <div class="skeleton-table-cell"></div>
                    <div class="skeleton-table-cell"></div>
                    <div class="skeleton-table-cell"></div>
                </div>
                <div class="skeleton skeleton-table-row">
                    <div class="skeleton-table-cell"></div>
                    <div class="skeleton-table-cell"></div>
                    <div class="skeleton-table-cell"></div>
                </div>
                <div class="skeleton skeleton-table-row">
                    <div class="skeleton-table-cell"></div>
                    <div class="skeleton-table-cell"></div>
                    <div class="skeleton-table-cell"></div>
                </div>
            `;
        }
    }

    /**
     * Show error in balance section
     */
    showBalanceError(errorMsg) {
        const balanceSummary = document.getElementById('balance-summary-card');
        const balanceDetails = document.getElementById('balance-details-container');

        const errorHTML = `
            <div class="alert alert-danger mb-0 d-flex align-items-center">
                <i class="bi bi-exclamation-circle me-2"></i>
                <div>
                    <strong>Balance Data Error:</strong> ${errorMsg}
                </div>
            </div>
        `;

        if (balanceSummary) balanceSummary.innerHTML = errorHTML;
        if (balanceDetails) balanceDetails.innerHTML = errorHTML;
    }

    /**
     * Show error in transactions section
     */
    showTransactionsError(errorMsg) {
        const transactionsSummary = document.getElementById('transactions-summary-card');
        const transactionsTable = document.getElementById('transactions-table-container');

        const errorHTML = `
            <div class="alert alert-danger mb-0 d-flex align-items-center">
                <i class="bi bi-exclamation-circle me-2"></i>
                <div>
                    <strong>Transactions Error:</strong> ${errorMsg}
                </div>
            </div>
        `;

        if (transactionsSummary) transactionsSummary.innerHTML = errorHTML;
        if (transactionsTable) transactionsTable.innerHTML = errorHTML;
    }

    /**
     * Show error in crypto variation section
     */
    showCryptoVariationError(errorMsg) {
        const cryptoSummary = document.getElementById('crypto-summary-card');
        const cryptoTable = document.getElementById('crypto-variation-table-container');

        const errorHTML = `
            <div class="alert alert-danger mb-0 d-flex align-items-center">
                <i class="bi bi-exclamation-circle me-2"></i>
                <div>
                    <strong>Crypto Variation Error:</strong> ${errorMsg}
                </div>
            </div>
        `;

        if (cryptoSummary) cryptoSummary.innerHTML = errorHTML;
        if (cryptoTable) cryptoTable.innerHTML = errorHTML;
    }

    /**
     * Show error message at top of page
     */
    showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger error-message';
        errorDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi bi-exclamation-triangle me-2 fs-5"></i>
                <div>
                    <strong>Error:</strong> ${message}
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        document.body.appendChild(errorDiv);

        // Auto-dismiss after 8 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.classList.add('fade-out');
                setTimeout(() => errorDiv.remove(), 300);
            }
        }, 8000);
    }

    /**
     * Format currency values
     */
    formatCurrency(value) {
        const num = parseFloat(value);
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(num);
    }

    /**
     * Format number with fixed decimals
     */
    formatNumber(value, decimals = 2) {
        const num = parseFloat(value);
        return num.toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    /**
     * Parse currency string back to number
     */
    parseCurrency(str) {
        // Remove currency symbol and commas
        return parseFloat(str.replace(/[^\d.-]/g, ''));
    }
}

// Initialize dashboard loader on page load
document.addEventListener('DOMContentLoaded', function() {
    const loader = new DashboardLoader();
    loader.init();
});
