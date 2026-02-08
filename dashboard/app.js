document.addEventListener('DOMContentLoaded', () => {
    if (typeof DASHBOARD_DATA !== 'undefined') {
        injectData(DASHBOARD_DATA);
    } else {
        console.error('DASHBOARD_DATA not found.');
    }
});

function injectData(data) {
    // 1. Header & Technical Hero
    document.getElementById('price-val').textContent = `$${data.price.toFixed(2)}`;
    document.getElementById('sentiment-val').textContent = data.sentiment.toUpperCase();
    document.getElementById('buy-zone-val').textContent = data.technical_stack.buy_zone.toUpperCase();
    document.getElementById('ema-val').textContent = `$${data.technical_stack.ema_21.toFixed(2)}`;
    document.getElementById('atr-val').textContent = `$${data.technical_stack.atr.toFixed(2)}`;

    // 2. Technical Levels (Pivots & Fib)
    const pivotList = document.getElementById('pivot-list');
    Object.entries(data.technical_stack.pivots).forEach(([label, val]) => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${label}</span><strong>$${val.toFixed(2)}</strong>`;
        pivotList.appendChild(li);
    });

    const fibList = document.getElementById('fib-list');
    data.technical_stack.fibonacci.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${item.level}</span><strong>$${item.price.toFixed(2)}</strong>`;
        fibList.appendChild(li);
    });

    // 3. Geospatial Timeline
    document.getElementById('geo-score').textContent = `${(data.verification.geospatial.score * 100)}%`;
    document.getElementById('site-name').textContent = data.verification.geospatial.site.toUpperCase();
    document.getElementById('site-coords').textContent = data.verification.geospatial.coords;

    const timeline = document.getElementById('geo-timeline');
    data.verification.geospatial.timeline.forEach(step => {
        const div = document.createElement('div');
        div.className = 'tm-item';
        div.innerHTML = `<p class="tm-date">${step.date} | ${step.event}</p><p class="tm-detail">${step.detail}</p>`;
        timeline.appendChild(div);
    });

    // 4. Insider & SEC
    const insiderTable = document.getElementById('insider-table');
    data.insider_trades.forEach(trade => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${trade.date}</td><td>$${(trade.value / 1000).toFixed(0)}K</td><td>${trade.type}</td>`;
        insiderTable.appendChild(row);
    });

    document.getElementById('sec-ops').textContent = data.sec_insights.operations;
    document.getElementById('sec-risks').textContent = data.sec_insights.risk_factors;

    // 5. Supply & News
    document.getElementById('benchmark-val').textContent = `$${data.verification.supply_chain.benchmark.toFixed(2)}`;

    const badgeContainer = document.getElementById('verification-badges');
    Object.entries(data.verification.supply_chain.claims).forEach(([key, val]) => {
        const badge = document.createElement('div');
        badge.className = 'badge';
        badge.innerHTML = `✓ ${val}`;
        badgeContainer.appendChild(badge);
    });

    const newsList = document.getElementById('news-list');
    data.headlines.forEach(news => {
        const item = document.createElement('div');
        item.className = 'news-item';
        item.innerHTML = `<h5>${news.title}</h5><p>${news.date} • ${news.summary}</p>`;
        newsList.appendChild(item);
    });
}
