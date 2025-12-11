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