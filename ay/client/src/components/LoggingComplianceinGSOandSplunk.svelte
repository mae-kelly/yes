// =============================================================================
// LoggingComplianceInGSOandSplunk.svelte
// =============================================================================
<!-- /client/src/components/LoggingComplianceInGSOandSplunk.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;

  async function fetchData() {
    try {
      const response = await fetch('/api/logging-compliance-gso-splunk');
      if (!response.ok) throw new Error('Failed to fetch logging data');
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
    <div class="loading-text">ANALYZING LOGGING COMPLIANCE</div>
  </div>
{:else if error}
  <div class="error">
    <div class="error-container">
      <h2 class="error-title">LOGGING SCAN FAILED</h2>
      <p class="error-message">{error}</p>
      <button class="retry-button" on:click={fetchData}>RETRY SCAN</button>
    </div>
  </div>
{:else if data.summary}
  <div class="main-header-title" style="margin-bottom: 25px;">
    LOGGING COMPLIANCE IN GSO & SPLUNK PLATFORMS
  </div>

  <div class="metrics-row">
    {#each [['splunk_coverage', 'SPLUNK LOGGING', '📊'], ['chronicle_coverage', 'CHRONICLE LOGGING', '📝'], ['dual_platform', 'DUAL PLATFORM', '🔄'], ['no_logging', 'NO LOGGING', '⚠️']] as [key, label, icon]}
      {@const coverage = data.summary[key] || {percentage: 0, count: 0}}
      {@const threat = key === 'no_logging' ? {color: 'var(--status-critical)'} : getThreatLevel(coverage.percentage)}
      <div class="metric-card" style="border-color: {threat.color};">
        <div class="metric-ring">
          <div class="icon-circle" style="border-color: {threat.color};">
            <span style="color: {threat.color}; font-size: 18px;">{icon}</span>
          </div>
        </div>
        <div class="metric-content">
          <div class="metric-label" style="color: {threat.color};">{label}</div>
          <div class="metric-value" style="color: {threat.color};">{coverage.percentage}%</div>
          <div class="metric-detail">{formatNumber(coverage.count)} assets</div>
        </div>
      </div>
    {/each}
  </div>

  <div class="card" style="margin-top: 30px; padding: 25px;">
    <div class="header-title" style="margin-bottom: 20px;">REGIONAL LOGGING COMPLIANCE</div>
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>REGION</th>
            <th class="text-center">ASSETS</th>
            <th class="text-center">SPLUNK %</th>
            <th class="text-center">CHRONICLE %</th>
            <th class="text-center">COMPLIANCE</th>
            <th class="text-center">STATUS</th>
          </tr>
        </thead>
        <tbody>
          {#each Object.entries(data.regional_compliance || {}) as [region, stats]}
            {@const threat = getThreatLevel(stats.overall_compliance)}
            <tr>
              <td class="font-weight-bold">{region.toUpperCase()}</td>
              <td class="text-center">{formatNumber(stats.total)}</td>
              <td class="text-center" style="color: {getThreatLevel(stats.splunk_percentage).color};">{stats.splunk_percentage}%</td>
              <td class="text-center" style="color: {getThreatLevel(stats.chronicle_percentage).color};">{stats.chronicle_percentage}%</td>
              <td class="text-center" style="color: {threat.color};">{stats.overall_compliance}%</td>
              <td class="text-center" style="color: {threat.color};">{threat.status}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
{/if}