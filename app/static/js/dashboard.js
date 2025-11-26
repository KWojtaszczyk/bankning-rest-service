async function loadDashboardData() {
    await Promise.all([
        loadAccounts(),
        loadTransactions()
    ]);
}

async function loadAccounts() {
    const response = await authenticatedFetch('/accounts');
    const accounts = await response.json();
    state.accounts = accounts;

    const listContainer = document.getElementById('accounts-list');
    const selectContainer = document.getElementById('transfer-from');

    listContainer.innerHTML = '';
    selectContainer.innerHTML = '';

    let totalBalance = 0;

    accounts.forEach(acc => {
        totalBalance += parseFloat(acc.balance);

        // Add to list
        const card = document.createElement('div');
        card.className = 'account-card';
        card.innerHTML = `
            <div class="acc-type">${acc.account_type}</div>
            <div class="acc-balance">$${parseFloat(acc.balance).toFixed(2)}</div>
            <div class="acc-number">**** ${acc.account_number.slice(-4)}</div>
        `;
        listContainer.appendChild(card);

        // Add to dropdown
        const option = document.createElement('option');
        option.value = acc.id;
        option.textContent = `${acc.account_type} - $${parseFloat(acc.balance).toFixed(2)}`;
        selectContainer.appendChild(option);
    });

    document.getElementById('total-balance').textContent = `$${totalBalance.toFixed(2)}`;
}

async function loadTransactions() {
    const response = await authenticatedFetch('/transactions?limit=5');
    const transactions = await response.json();

    const tbody = document.getElementById('transactions-list');
    tbody.innerHTML = '';

    transactions.forEach(tx => {
        const row = document.createElement('tr');
        const isCredit = tx.amount > 0; // Assuming positive is credit, negative is debit logic if applicable
        // Adjust logic based on your API response structure for debit/credit

        row.innerHTML = `
            <td>${tx.transaction_type}</td>
            <td>${tx.description || 'No description'}</td>
            <td>${new Date(tx.created_at).toLocaleDateString()}</td>
            <td style="color: ${isCredit ? 'var(--success)' : 'white'}">
                $${Math.abs(tx.amount).toFixed(2)}
            </td>
            <td><span class="status-badge status-completed">Completed</span></td>
        `;
        tbody.appendChild(row);
    });
}

// Transfer Handler
document.getElementById('transfer-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const fromAccountId = document.getElementById('transfer-from').value;
    const toAccountId = document.getElementById('transfer-to').value;
    const amount = parseFloat(document.getElementById('transfer-amount').value);

    if (!fromAccountId) {
        alert('Please select an account to transfer from');
        return;
    }

    try {
        const response = await authenticatedFetch('/transactions/transfer', {
            method: 'POST',
            body: JSON.stringify({
                from_account_id: parseInt(fromAccountId),
                to_account_id: parseInt(toAccountId),
                amount: amount,
                description: "Web transfer"
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Transfer failed');
        }

        alert('Transfer successful!');
        document.getElementById('transfer-form').reset();
        await loadDashboardData(); // Refresh data

    } catch (error) {
        alert(error.message);
    }
});
