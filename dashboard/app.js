document.addEventListener('DOMContentLoaded', () => {
    // Check if data is loaded from script
    if (typeof DASHBOARD_DATA !== 'undefined') {
        injectData(DASHBOARD_DATA);
    } else {
        console.error('DASHBOARD_DATA not found. Make sure data.js is included.');
    }
});

function injectData(data) {
    // Header Stats
    document.getElementById('price-val').textContent = `$${data.price.toFixed(2)}`;
    document.getElementById('sentiment-val').textContent = data.sentiment.toUpperCase();

    // Technicals
    document.getElementById('buy-zone-val').textContent = data.technical_stack.buy_zone.toUpperCase() === 'ACTIVE' ? 'YES' : 'NO';
    document.getElementById('ema-val').textContent = `$${data.technical_stack.ema_21.toFixed(2)}`;
    document.getElementById('sma50-val').textContent = `$${data.technical_stack.sma_50.toFixed(2)}`;
    document.getElementById('sma200-val').textContent = `$${data.technical_stack.sma_200.toFixed(2)}`;

    // Physical
    document.getElementById('geo-score').textContent = `${(data.verification.geospatial.score * 100)}%`;
    document.getElementById('geo-status-val').textContent = data.verification.geospatial.status;

    // Insider Table
    const tableBody = document.getElementById('insider-table');
    tableBody.innerHTML = '';

    data.insider_trades.forEach(trade => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${trade.date}</td>
            <td><strong>${trade.insider}</strong></td>
            <td><span class="tag">${trade.type === 'P' ? 'PURCHASE' : 'SALE'}</span></td>
            <td>$${(trade.value / 1000).toFixed(0)}K</td>
        `;
        tableBody.appendChild(row);
    });

    // Commodity
    document.getElementById('benchmark-val').textContent = `$${data.verification.supply_chain.benchmark.toFixed(2)}`;
}
