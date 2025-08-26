// =============================================================================
// SecurityControlCoverage.svelte
// =============================================================================
<!-- /client/src/components/SecurityControlCoverage.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;

  async function fetchData() {
    try {
      const response = await fetch('/api/security-control-coverage');
      if (!response.ok) throw new Error('Failed to fetch security data');
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
    <div class="cyber-spinner"></div>
    <div class="loading-text">ANALYZING SECURITY CONTROLS</div>
  </div>
{:else if error}
  <div class="error">
    <div class="error-container">
      <h2 class="error-title">SECURITY SCAN FAILED</h2>
      <p class="error-message">{error}</p>
      <button class="retry-button" on:click={fetchData}>RETRY SCAN</button>
    </div>
  </div>
{:else if data.total_hosts}
  <div class="main-header-title" style="margin-bottom: 25px;">
    SECURITY CONTROL COVERAGE - AGENT-BASED PROTECTION
  </div>

  <div class="metrics-row">
    {#each [['edr', 'EDR PROTECTION', '🛡️'], ['tanium', 'TANIUM COVERAGE', '⚙️'], ['dlp', 'DLP PROTECTION', '🔒']] as [key, label, icon]}
      {@const coverage = data.coverage[key] || {percentage: 0, count: 0}}
      {@const threat = getThreatLevel(coverage.percentage)}
      <div class="metric-card" style="border-color: {threat.color};">
        <div class="metric-ring">
          <div class="icon-circle" style="border-color: {threat.color};">
            <span style="color: {threat.color}; font-size: 18px;">{icon}</span>
          </div>
        </div>
        <div class="metric-content">
          <div class="metric-label" style="color: {threat.color};">{label}</div>
          <div class="metric-value" style="color: {threat.color};">{coverage.percentage}%</div>
          <div class="metric-detail">{formatNumber(coverage.count)} protected assets</div>
        </div>
      </div>
    {/each}
  </div>

  <div class="card" style="margin-top: 30px; padding: 25px;">
    <div class="header-title" style="margin-bottom: 20px;">SECURITY OVERLAP ANALYSIS</div>
    
    <div class="d-grid grid-cols-3 gap-4">
      {#each Object.entries(data.overlaps || {}) as [key, overlap]}
        <div class="coverage-item">
          <div class="coverage-header">
            <span>{key.replace('_', ' + ').toUpperCase()}</span>
            <span style="color: {getThreatLevel(overlap.percentage).color};">{overlap.percentage}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {overlap.percentage}%; background: {getThreatLevel(overlap.percentage).color};"></div>
          </div>
          <div class="text-muted">{formatNumber(overlap.count)} assets</div>
        </div>
      {/each}
    </div>
  </div>
{/if}
