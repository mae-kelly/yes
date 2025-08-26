<!-- /src/components/GlobalView.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;

  async function fetchData() {
    try {
      const response = await fetch('http://localhost:5000/api/global-view');
      if (!response.ok) throw new Error('Failed to fetch global view data');
      data = await response.json();
      loading = false;
    } catch (err) {
      error = err.message;
      loading = false;
    }
  }

  onMount(fetchData);

  function getThreatLevel(percentage) {
    if (percentage >= 90) return { color: 'var(--status-good)', status: 'OPTIMAL' };
    if (percentage >= 75) return { color: 'var(--accent-cyan)', status: 'GOOD' };
    if (percentage >= 50) return { color: 'var(--status-warning)', status: 'MODERATE' };
    if (percentage >= 25) return { color: 'var(--accent-magenta)', status: 'POOR' };
    return { color: 'var(--status-critical)', status: 'CRITICAL' };
  }

  function formatNumber(num) {
    return num?.toLocaleString() || '0';
  }
</script>

{#if loading}
  <div class="loading">
    <div class="cyber-spinner">
      <div class="spinner-inner"></div>
    </div>
    <div class="loading-text">
      ANALYZING GLOBAL INFRASTRUCTURE
      <div class="loading-subtext">Scanning all systems...</div>
    </div>
  </div>
{:else if error}
  <div class="error">
    <div class="error-container">
      <h2 class="error-title" style="color: var(--status-critical);">GLOBAL SCAN FAILED</h2>
      <p class="error-message">{error}</p>
      <button class="retry-button" on:click={fetchData}>RETRY SCAN</button>
    </div>
  </div>
{:else if data.total_hosts}

  <div class="main-header-title" style="margin-bottom: 25px;">
    GLOBAL VIEW - CSOC VISIBILITY ACROSS ALL ASSETS
  </div>

  <div class="metrics-row">
    <div class="metric-card" style="border-color: var(--accent-cyan);">
      <div class="metric-ring">
        <div class="icon-circle" style="border-color: var(--accent-cyan); box-shadow: var(--glow-cyan);">
          <span style="color: var(--accent-cyan); font-size: 18px;">🌐</span>
        </div>
      </div>
      <div class="metric-content">
        <div class="metric-label" style="color: var(--accent-cyan);">TOTAL ASSETS</div>
        <div class="metric-value" style="color: var(--accent-cyan);">{formatNumber(data.total_hosts)}</div>
        <div class="metric-detail">Infrastructure inventory across all environments</div>
      </div>
      <div class="decorative-bar" style="background: var(--accent-cyan);"></div>
    </div>

    <div class="metric-card" style="border-color: {getThreatLevel(data.coverage.splunk.percentage).color};">
      <div class="metric-ring">
        <div class="icon-circle" style="border-color: {getThreatLevel(data.coverage.splunk.percentage).color}; box-shadow: 0 0 15px {getThreatLevel(data.coverage.splunk.percentage).color};">
          <span style="color: {getThreatLevel(data.coverage.splunk.percentage).color}; font-size: 18px;">📊</span>
        </div>
      </div>
      <div class="metric-content">
        <div class="metric-label" style="color: {getThreatLevel(data.coverage.splunk.percentage).color};">SPLUNK COVERAGE</div>
        <div class="metric-value" style="color: {getThreatLevel(data.coverage.splunk.percentage).color};">{data.coverage.splunk.percentage}%</div>
        <div class="metric-detail">{formatNumber(data.coverage.splunk.count)} assets logging to Splunk</div>
      </div>
      <div class="decorative-bar" style="background: {getThreatLevel(data.coverage.splunk.percentage).color};"></div>
    </div>
  </div>

  <div class="metrics-row">
    <div class="metric-card" style="border-color: {getThreatLevel(data.coverage.cmdb.percentage).color};">
      <div class="metric-ring">
        <div class="icon-circle" style="border-color: {getThreatLevel(data.coverage.cmdb.percentage).color}; box-shadow: 0 0 15px {getThreatLevel(data.coverage.cmdb.percentage).color};">
          <span style="color: {getThreatLevel(data.coverage.cmdb.percentage).color}; font-size: 18px;">📋</span>
        </div>
      </div>
      <div class="metric-content">
        <div class="metric-label" style="color: {getThreatLevel(data.coverage.cmdb.percentage).color};">CMDB PRESENCE</div>
        <div class="metric-value" style="color: {getThreatLevel(data.coverage.cmdb.percentage).color};">{data.coverage.cmdb.percentage}%</div>
        <div class="metric-detail">{formatNumber(data.coverage.cmdb.count)} assets documented in CMDB</div>
      </div>
      <div class="decorative-bar" style="background: {getThreatLevel(data.coverage.cmdb.percentage).color};"></div>
    </div>

    <div class="metric-card" style="border-color: {getThreatLevel(data.coverage.crowdstrike.percentage).color};">
      <div class="metric-ring">
        <div class="icon-circle" style="border-color: {getThreatLevel(data.coverage.crowdstrike.percentage).color}; box-shadow: 0 0 15px {getThreatLevel(data.coverage.crowdstrike.percentage).color};">
          <span style="color: {getThreatLevel(data.coverage.crowdstrike.percentage).color}; font-size: 18px;">🛡️</span>
        </div>
      </div>
      <div class="metric-content">
        <div class="metric-label" style="color: {getThreatLevel(data.coverage.crowdstrike.percentage).color};">EDR PROTECTION</div>
        <div class="metric-value" style="color: {getThreatLevel(data.coverage.crowdstrike.percentage).color};">{data.coverage.crowdstrike.percentage}%</div>
        <div class="metric-detail">{formatNumber(data.coverage.crowdstrike.count)} assets with CrowdStrike EDR</div>
      </div>
      <div class="decorative-bar" style="background: {getThreatLevel(data.coverage.crowdstrike.percentage).color};"></div>
    </div>
  </div>

  <div class="metrics-row">
    <div class="metric-card" style="border-color: {getThreatLevel(data.coverage.tanium?.percentage || 0).color};">
      <div class="metric-ring">
        <div class="icon-circle" style="border-color: {getThreatLevel(data.coverage.tanium?.percentage || 0).color}; box-shadow: 0 0 15px {getThreatLevel(data.coverage.tanium?.percentage || 0).color};">
          <span style="color: {getThreatLevel(data.coverage.tanium?.percentage || 0).color}; font-size: 18px;">⚙️</span>
        </div>
      </div>
      <div class="metric-content">
        <div class="metric-label" style="color: {getThreatLevel(data.coverage.tanium?.percentage || 0).color};">TANIUM COVERAGE</div>
        <div class="metric-value" style="color: {getThreatLevel(data.coverage.tanium?.percentage || 0).color};">{data.coverage.tanium?.percentage || 0}%</div>
        <div class="metric-detail">{formatNumber(data.coverage.tanium?.count || 0)} assets with Tanium agent</div>
      </div>
      <div class="decorative-bar" style="background: {getThreatLevel(data.coverage.tanium?.percentage || 0).color};"></div>
    </div>

    <div class="metric-card" style="border-color: {getThreatLevel(data.coverage.apm?.percentage || 0).color};">
      <div class="metric-ring">
        <div class="icon-circle" style="border-color: {getThreatLevel(data.coverage.apm?.percentage || 0).color}; box-shadow: 0 0 15px {getThreatLevel(data.coverage.apm?.percentage || 0).color};">
          <span style="color: {getThreatLevel(data.coverage.apm?.percentage || 0).color}; font-size: 18px;">📈</span>
        </div>
      </div>
      <div class="metric-content">
        <div class="metric-label" style="color: {getThreatLevel(data.coverage.apm?.percentage || 0).color};">APM MONITORING</div>
        <div class="metric-value" style="color: {getThreatLevel(data.coverage.apm?.percentage || 0).color};">{data.coverage.apm?.percentage || 0}%</div>
        <div class="metric-detail">{formatNumber(data.coverage.apm?.count || 0)} assets with APM monitoring</div>
      </div>
      <div class="decorative-bar" style="background: {getThreatLevel(data.coverage.apm?.percentage || 0).color};"></div>
    </div>
  </div>

  <div class="card" style="margin-top: 30px;">
    <div class="card-header">
      <div class="header-title">GLOBAL COVERAGE ANALYSIS</div>
    </div>

    <div class="coverage-indicators">
      {#each Object.entries(data.coverage) as [tool, stats]}
        {@const threat = getThreatLevel(stats.percentage)}
        <div class="coverage-item">
          <div class="coverage-header">
            <span style="color: var(--text-primary); font-size: 14px; font-weight: bold;">
              {tool.toUpperCase().replace('_', ' ')}
            </span>
            <span style="color: {threat.color}; font-size: 14px; font-weight: bold;">
              {stats.percentage}% ({formatNumber(stats.count)} assets)
            </span>
          </div>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              style="width: {stats.percentage}%; background: {threat.color}; --glow-color: {threat.color};"
            ></div>
          </div>
        </div>
      {/each}
    </div>
  </div>

  <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 30px;">
    <div class="card" style="text-align: center;">
      <div class="header-title" style="margin-bottom: 15px; color: var(--status-good);">OPTIMAL COVERAGE</div>
      <div style="font-size: 32px; font-weight: bold; color: var(--status-good); margin-bottom: 10px;">
        {Object.values(data.coverage).filter(c => c.percentage >= 90).length}
      </div>
      <div style="color: var(--text-secondary); font-size: 12px;">Tools with 90%+ coverage</div>
    </div>

    <div class="card" style="text-align: center;">
      <div class="header-title" style="margin-bottom: 15px; color: var(--status-warning);">NEEDS ATTENTION</div>
      <div style="font-size: 32px; font-weight: bold; color: var(--status-warning); margin-bottom: 10px;">
        {Object.values(data.coverage).filter(c => c.percentage < 75).length}
      </div>
      <div style="color: var(--text-secondary); font-size: 12px;">Tools below 75% coverage</div>
    </div>

    <div class="card" style="text-align: center;">
      <div class="header-title" style="margin-bottom: 15px; color: var(--accent-cyan);">AVERAGE COVERAGE</div>
      <div style="font-size: 32px; font-weight: bold; color: var(--accent-cyan); margin-bottom: 10px;">
        {Math.round(Object.values(data.coverage).reduce((sum, c) => sum + c.percentage, 0) / Object.values(data.coverage).length)}%
      </div>
      <div style="color: var(--text-secondary); font-size: 12px;">Overall platform coverage</div>
    </div>
  </div>
{/if}