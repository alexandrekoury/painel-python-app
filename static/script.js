// Sidebar toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }
    
    // Restore sidebar state from localStorage
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
        sidebar.classList.add('collapsed');
    }
});

function deleteInvestor(investorId, investorAlias) {
    if (confirm(`Are you sure you want to delete ${investorAlias}?`)) {
        fetch(`/investor/delete/${investorId}`, { method: 'POST' })
            .then(response => window.location.reload())
            .catch(error => console.error('Error:', error));
    }
}


function deleteTransaction(transactionId) {
    console.log('clicked!')
    if (confirm(`Are you sure you want to delete transaction ${transactionId}?`)) {
        fetch(`/investor/delete/${investorId}`, { method: 'POST' })
            .then(response => window.location.reload())
            .catch(error => console.error('Error:', error));
    }
}