/**
 * InsightOps – Dashboard JavaScript
 * Fetches pre-computed JSON data and renders all charts & tables.
 */

/* ═══════════════════════════════════════
   PLOTLY GLOBAL THEME
═══════════════════════════════════════ */
const THEME = {
  bg:      '#161b22',
  paper:   '#161b22',
  text:    '#e6edf3',
  muted:   '#8b949e',
  grid:    '#21262d',
  accent:  '#58a6ff',
  accent2: '#3fb950',
  warning: '#d29922',
  danger:  '#f85149',
  purple:  '#bc8cff',
  palette: ['#58a6ff', '#3fb950', '#bc8cff', '#f0c040', '#f85149', '#79c0ff', '#56d364', '#d2a8ff'],
};

const plotlyLayout = (extra = {}) => ({
  paper_bgcolor: THEME.paper,
  plot_bgcolor:  THEME.bg,
  font: { family: 'Inter, sans-serif', color: THEME.text, size: 12 },
  margin: { t: 20, r: 20, b: 40, l: 50 },
  xaxis: { gridcolor: THEME.grid, zerolinecolor: THEME.grid, tickfont: { color: THEME.muted } },
  yaxis: { gridcolor: THEME.grid, zerolinecolor: THEME.grid, tickfont: { color: THEME.muted } },
  legend: { bgcolor: 'transparent', font: { color: THEME.text } },
  ...extra,
});

const plotlyConfig = { responsive: true, displayModeBar: false };

/* ═══════════════════════════════════════
   UTILITIES
═══════════════════════════════════════ */
const fmt = {
  currency: v => v == null ? '—' : '$' + Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 }),
  pct:      v => v == null ? '—' : Number(v).toFixed(1) + '%',
  int:      v => v == null ? '—' : Number(v).toLocaleString('en-US'),
};

function el(id) { return document.getElementById(id); }

/* ═══════════════════════════════════════
   NAVIGATION
═══════════════════════════════════════ */
const PAGE_TITLES = {
  overview:   'Executive Overview',
  products:   'Product Performance',
  customers:  'Customer Insights',
  operations: 'Operations Dashboard',
};

function navigateTo(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  el('page-' + pageId).classList.add('active');
  el('nav-' + pageId).classList.add('active');
  el('topbarTitle').textContent = PAGE_TITLES[pageId];

  // Close sidebar on mobile after navigation
  if (window.innerWidth < 640) {
    el('sidebar').classList.remove('open');
  }
}

document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => navigateTo(btn.dataset.page));
});

el('menuToggle').addEventListener('click', () => {
  el('sidebar').classList.toggle('open');
});

/* ═══════════════════════════════════════
   RENDER: KPI CARDS
═══════════════════════════════════════ */
function renderKPIs(kpis) {
  el('kpiRevenue').textContent = fmt.currency(kpis.total_revenue);
  el('kpiProfit').textContent  = fmt.currency(kpis.total_profit);
  el('kpiMargin').textContent  = fmt.pct(kpis.profit_margin);
  el('kpiSuccess').textContent = fmt.pct(kpis.order_success_rate);
  el('kpiSuccessSub').textContent =
    fmt.int(kpis.successful_orders) + ' / ' + fmt.int(kpis.total_orders) + ' orders';
}

/* ═══════════════════════════════════════
   RENDER: REVENUE & PROFIT TRENDS
═══════════════════════════════════════ */
function renderTrends(trends) {
  const traces = [
    {
      x: trends.year_month, y: trends.revenue,
      name: 'Revenue',
      type: 'scatter', mode: 'lines+markers',
      line: { color: THEME.accent, width: 2.5 },
      marker: { size: 5, color: THEME.accent },
      fill: 'tozeroy',
      fillcolor: 'rgba(88,166,255,0.08)',
    },
    {
      x: trends.year_month, y: trends.profit,
      name: 'Profit',
      type: 'scatter', mode: 'lines+markers',
      line: { color: THEME.accent2, width: 2.5 },
      marker: { size: 5, color: THEME.accent2 },
    },
  ];

  const layout = plotlyLayout({
    hovermode: 'x unified',
    yaxis: { tickprefix: '$', gridcolor: THEME.grid, tickfont: { color: THEME.muted } },
    legend: { orientation: 'h', y: 1.08, bgcolor: 'transparent', font: { color: THEME.text } },
  });

  Plotly.newPlot('chartTrends', traces, layout, plotlyConfig);
}

/* ═══════════════════════════════════════
   RENDER: AUTOMATED INSIGHTS
═══════════════════════════════════════ */
const insightIcon = { warning: '⚠️', alert: '🚨', info: 'ℹ️', recommendation: '💡', success: '✅' };

function renderInsights(insights) {
  el('insightCount').textContent = insights.length + ' insights';

  const container = el('insightsContainer');
  if (!insights.length) {
    container.innerHTML = '<p class="empty-state">No insights generated.</p>';
    return;
  }

  container.innerHTML = insights.slice(0, 6).map(i => `
    <div class="insight-item insight-${i.severity}">
      <span class="insight-icon">${insightIcon[i.type] || '•'}</span>
      <div class="insight-body">
        <strong>${i.title}</strong>
        <span>${i.message}</span>
      </div>
    </div>
  `).join('');
}

/* ═══════════════════════════════════════
   RENDER: SCATTER (Revenue vs Profit)
═══════════════════════════════════════ */
function renderScatter(cats) {
  const trace = {
    x: cats.revenue, y: cats.profit,
    mode: 'markers+text',
    text: cats.category,
    textposition: 'top center',
    textfont: { size: 10, color: THEME.muted },
    marker: {
      size: cats.orders.map(o => Math.sqrt(o) * 1.5 + 8),
      color: cats.margin,
      colorscale: [
        [0, THEME.danger], [0.5, THEME.warning], [1, THEME.accent2]
      ],
      showscale: true,
      colorbar: {
        title: { text: 'Margin %', font: { color: THEME.muted } },
        tickfont: { color: THEME.muted },
        bgcolor: 'transparent',
        outlinecolor: THEME.grid,
      },
      line: { width: 1, color: 'rgba(255,255,255,0.15)' },
    },
    hovertemplate: '<b>%{text}</b><br>Revenue: $%{x:,.0f}<br>Profit: $%{y:,.0f}<extra></extra>',
  };

  const layout = plotlyLayout({
    xaxis: { title: 'Total Revenue ($)', tickprefix: '$', gridcolor: THEME.grid, tickfont: { color: THEME.muted } },
    yaxis: { title: 'Total Profit ($)', tickprefix: '$', gridcolor: THEME.grid, tickfont: { color: THEME.muted } },
    height: 420,
  });

  Plotly.newPlot('chartScatter', [trace], layout, plotlyConfig);
}

/* ═══════════════════════════════════════
   RENDER: TOP CATEGORIES BAR
═══════════════════════════════════════ */
function renderTopCategories(cats) {
  const top10 = {
    category: cats.category.slice(0, 10),
    revenue:  cats.revenue.slice(0, 10),
    margin:   cats.margin.slice(0, 10),
  };

  const trace = {
    x: top10.revenue,
    y: top10.category,
    orientation: 'h',
    type: 'bar',
    marker: {
      color: top10.margin,
      colorscale: [[0, THEME.danger], [0.5, THEME.warning], [1, THEME.accent2]],
      showscale: false,
    },
    hovertemplate: '<b>%{y}</b><br>Revenue: $%{x:,.0f}<extra></extra>',
  };

  const layout = plotlyLayout({
    xaxis: { tickprefix: '$', gridcolor: THEME.grid, tickfont: { color: THEME.muted } },
    yaxis: { automargin: true, tickfont: { color: THEME.muted } },
    margin: { t: 10, r: 20, b: 40, l: 160 },
  });

  Plotly.newPlot('chartTopCategories', [trace], layout, plotlyConfig);
}

/* ═══════════════════════════════════════
   RENDER: LOW MARGIN TABLE
═══════════════════════════════════════ */
function renderLowMarginTable(cats) {
  const lowMargin = cats.category
    .map((c, i) => ({ category: c, revenue: cats.revenue[i], margin: cats.margin[i] }))
    .filter(r => r.margin < 10)
    .sort((a, b) => a.margin - b.margin);

  el('lowMarginCount').textContent = lowMargin.length + ' categories';

  const container = el('lowMarginTable');
  if (!lowMargin.length) {
    container.innerHTML = '<p class="empty-state" style="color:var(--accent2)">✅ All categories have healthy margins</p>';
    return;
  }

  container.innerHTML = `
    <table>
      <thead><tr><th>Category</th><th>Revenue</th><th>Margin</th></tr></thead>
      <tbody>
        ${lowMargin.map(r => `
          <tr>
            <td>${r.category}</td>
            <td>${fmt.currency(r.revenue)}</td>
            <td style="color:${r.margin < 5 ? 'var(--danger)' : 'var(--warning)'}">${fmt.pct(r.margin)}</td>
          </tr>`).join('')}
      </tbody>
    </table>`;
}

/* ═══════════════════════════════════════
   RENDER: SEGMENT PIE
═══════════════════════════════════════ */
function renderSegmentPie(segs) {
  const colorMap = { New: THEME.accent, Returning: THEME.accent2, VIP: THEME.purple };
  const colors = segs.segment.map(s => colorMap[s] || THEME.accent);

  const trace = {
    labels: segs.segment, values: segs.customer_count,
    type: 'pie', hole: 0.45,
    marker: { colors, line: { color: '#161b22', width: 2 } },
    textfont: { color: THEME.text },
    hovertemplate: '<b>%{label}</b><br>Customers: %{value:,}<br>%{percent}<extra></extra>',
  };

  const layout = plotlyLayout({
    margin: { t: 10, r: 20, b: 20, l: 20 },
    legend: { font: { color: THEME.text }, bgcolor: 'transparent' },
  });

  Plotly.newPlot('chartSegmentPie', [trace], layout, plotlyConfig);
}

/* ═══════════════════════════════════════
   RENDER: SEGMENT REVENUE BAR
═══════════════════════════════════════ */
function renderSegmentRevenue(segs) {
  const colorMap = { New: THEME.accent, Returning: THEME.accent2, VIP: THEME.purple };
  const colors = segs.segment.map(s => colorMap[s] || THEME.accent);

  const trace = {
    x: segs.segment, y: segs.revenue,
    type: 'bar',
    marker: { color: colors, borderRadius: 4 },
    hovertemplate: '<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>',
  };

  const layout = plotlyLayout({
    yaxis: { tickprefix: '$', gridcolor: THEME.grid, tickfont: { color: THEME.muted } },
    xaxis: { gridcolor: THEME.grid, tickfont: { color: THEME.muted } },
    showlegend: false,
  });

  Plotly.newPlot('chartSegmentRevenue', [trace], layout, plotlyConfig);
}

/* ═══════════════════════════════════════
   RENDER: SEGMENT TABLE
═══════════════════════════════════════ */
function renderSegmentsTable(segs) {
  const segBadge = s => `<span class="badge-segment badge-${s.toLowerCase()}">${s}</span>`;

  el('segmentsTable').innerHTML = `
    <table>
      <thead><tr><th>Segment</th><th>Customers</th><th>Orders</th><th>Revenue</th><th>Avg Order</th></tr></thead>
      <tbody>
        ${segs.segment.map((s, i) => `
          <tr>
            <td>${segBadge(s)}</td>
            <td>${fmt.int(segs.customer_count[i])}</td>
            <td>${fmt.int(segs.order_count[i])}</td>
            <td>${fmt.currency(segs.revenue[i])}</td>
            <td>${fmt.currency(segs.avg_order_value[i])}</td>
          </tr>`).join('')}
      </tbody>
    </table>`;
}

/* ═══════════════════════════════════════
   RENDER: TOP CUSTOMERS TABLE
═══════════════════════════════════════ */
function renderTopCustomersTable(customers) {
  const segBadge = s => s ? `<span class="badge-segment badge-${s.toLowerCase()}">${s}</span>` : '—';

  el('topCustomersTable').innerHTML = `
    <table>
      <thead><tr><th>#</th><th>Customer ID</th><th>Segment</th><th>Country</th><th>Orders</th><th>Revenue</th><th>Avg Order</th></tr></thead>
      <tbody>
        ${customers.map((c, i) => `
          <tr>
            <td style="color:var(--text-muted)">${i + 1}</td>
            <td style="font-family:monospace;font-size:11px">${(c.customer_id || '').substring(0, 12)}…</td>
            <td>${segBadge(c.segment)}</td>
            <td>${c.country || '—'}</td>
            <td>${fmt.int(c.order_count)}</td>
            <td>${fmt.currency(c.total_revenue)}</td>
            <td>${fmt.currency(c.avg_order_value)}</td>
          </tr>`).join('')}
      </tbody>
    </table>`;
}

/* ═══════════════════════════════════════
   RENDER: CHANNEL REVENUE BAR
═══════════════════════════════════════ */
function renderChannelRevenue(channels) {
  const trace = {
    x: channels.channel, y: channels.revenue,
    type: 'bar',
    marker: {
      color: THEME.palette,
      borderRadius: 4,
    },
    hovertemplate: '<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>',
  };

  const layout = plotlyLayout({
    yaxis: { tickprefix: '$', gridcolor: THEME.grid, tickfont: { color: THEME.muted } },
    xaxis: { gridcolor: THEME.grid, tickfont: { color: THEME.muted } },
    showlegend: false,
  });

  Plotly.newPlot('chartChannelRevenue', [trace], layout, plotlyConfig);
}

/* ═══════════════════════════════════════
   RENDER: CHANNEL FAILURE RATE BAR
═══════════════════════════════════════ */
function renderChannelFailure(channels) {
  const trace = {
    x: channels.channel, y: channels.failure_rate,
    type: 'bar',
    marker: {
      color: channels.failure_rate.map(v =>
        v > 10 ? THEME.danger : v > 5 ? THEME.warning : THEME.accent2),
      borderRadius: 4,
    },
    hovertemplate: '<b>%{x}</b><br>Failure Rate: %{y:.1f}%<extra></extra>',
  };

  const layout = plotlyLayout({
    yaxis: { ticksuffix: '%', gridcolor: THEME.grid, tickfont: { color: THEME.muted } },
    xaxis: { gridcolor: THEME.grid, tickfont: { color: THEME.muted } },
    showlegend: false,
  });

  Plotly.newPlot('chartChannelFailure', [trace], layout, plotlyConfig);
}

/* ═══════════════════════════════════════
   RENDER: CHANNEL TABLE
═══════════════════════════════════════ */
function renderChannelTable(channels) {
  el('channelTable').innerHTML = `
    <table>
      <thead><tr><th>Channel</th><th>Total Orders</th><th>Successful</th><th>Revenue</th><th>Failure Rate</th></tr></thead>
      <tbody>
        ${channels.channel.map((ch, i) => {
          const rate = channels.failure_rate[i];
          const rateColor = rate > 10 ? 'var(--danger)' : rate > 5 ? 'var(--warning)' : 'var(--accent2)';
          return `<tr>
            <td><strong>${ch}</strong></td>
            <td>${fmt.int(channels.total_orders[i])}</td>
            <td>${fmt.int(channels.successful_orders[i])}</td>
            <td>${fmt.currency(channels.revenue[i])}</td>
            <td style="color:${rateColor};font-weight:600">${fmt.pct(rate)}</td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>`;
}

/* ═══════════════════════════════════════
   RENDER: OPERATIONAL ALERTS
═══════════════════════════════════════ */
function renderOperationalAlerts(channels) {
  const highFailure = channels.channel
    .map((ch, i) => ({ channel: ch, rate: channels.failure_rate[i] }))
    .filter(c => c.rate > 5);

  const container = el('operationalAlerts');

  if (!highFailure.length) {
    container.innerHTML = `
      <div class="alert-item">
        <span class="alert-icon alert-success">✅</span>
        <span>All channels operating within acceptable failure rates (&lt;5%)</span>
      </div>`;
    return;
  }

  container.innerHTML = highFailure.map(c => `
    <div class="alert-item">
      <span class="alert-icon alert-danger">🚨</span>
      <span>
        <strong>${c.channel}</strong> channel has
        <span style="color:var(--danger);font-weight:600">${fmt.pct(c.rate)}</span>
        payment failure rate — above 5% threshold
      </span>
    </div>`).join('');
}

/* ═══════════════════════════════════════
   BOOT: FETCH DATA & RENDER
═══════════════════════════════════════ */
async function boot() {
  try {
    const res = await fetch('data/dashboard_data.json');
    if (!res.ok) throw new Error('Data not available');
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    // Overview
    renderKPIs(data.kpis);
    renderTrends(data.trends);
    renderInsights(data.insights);

    // Products
    renderScatter(data.categories);
    renderTopCategories(data.categories);
    renderLowMarginTable(data.categories);

    // Customers
    renderSegmentPie(data.segments);
    renderSegmentRevenue(data.segments);
    renderSegmentsTable(data.segments);
    renderTopCustomersTable(data.top_customers);

    // Operations
    renderChannelRevenue(data.channels);
    renderChannelFailure(data.channels);
    renderChannelTable(data.channels);
    renderOperationalAlerts(data.channels);

    // Hide loader
    el('loadingOverlay').classList.add('hidden');

  } catch (err) {
    console.error(err);
    el('loadingOverlay').classList.add('hidden');
    el('errorState').classList.remove('hidden');
  }
}

boot();
