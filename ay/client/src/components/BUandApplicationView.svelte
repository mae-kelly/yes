<!-- /client/src/components/BUandApplicationView.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;
  let viewMode = 'business_units';

  async function fetchData() {
    try {
      const response = await fetch('/api/bu-application-view');
      if (!response.ok) throw new Error('Failed to fetch business unit data');
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
    <div class="loading-text">ANALYZING BUSINESS UNITS</div>
  </div>
{:else if error}
  <div class="error">
    <div class="error-container">
      <h2 class="error-title">BUSINESS UNIT SCAN FAILED</h2>
      <p class="error-message">{error}</p>
      <button class="retry-button" on:click={fetchData}>RETRY SCAN</button>
    </div>
  </div>
{:else}
  <div class="main-header-title" style="margin-bottom: 25px;">
    BUSINESS UNIT & APPLICATION VISIBILITY ANALYSIS
  </div>

  <div class="d-flex gap-2" style="margin-bottom: 20px;">
    <button class="nav-tab {viewMode === 'business_units' ? 'active' : ''}" on:click={() => viewMode = 'business_units'}>BUSINESS UNITS</button>
    <button class="nav-tab {viewMode === 'cio' ? 'active' : ''}" on:click={() => viewMode = 'cio'}>CIO ANALYSIS</button>
    <button class="nav-tab {viewMode === 'apm' ? 'active' : ''}" on:click={() => viewMode = 'apm'}>APM COVERAGE</button>
  </div>

  {#if viewMode === 'business_units'}
    <div class="card" style="padding: 25px;">
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>BUSINESS UNIT</th>
              <th class="text-center">ASSETS</th>
              <th class="text-center">SPLUNK %</th>
              <th class="text-center">CMDB %</th>
              <th class="text-center">EDR %</th>
              <th class="text-center">STATUS</th>
            </tr>
          </thead>
          <tbody>
            {#each Object.entries(data.business_units || {}) as [bu, stats]}
              {@const threat = getThreatLevel(stats.overall_coverage)}
              <tr>
                <td class="font-weight-bold">{bu.length > 30 ? bu.substring(0, 30) + '...' : bu.toUpperCase()}</td>
                <td class="text-center">{formatNumber(stats.total)}</td>
                <td class="text-center" style="color: {getThreatLevel(stats.splunk_coverage).color};">{stats.splunk_coverage}%</td>
                <td class="text-center" style="color: {getThreatLevel(stats.cmdb_coverage).color};">{stats.cmdb_coverage}%</td>
                <td class="text-center" style="color: {getThreatLevel(stats.edr_coverage).color};">{stats.edr_coverage}%</td>
                <td class="text-center" style="color: {threat.color};">{threat.status}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {:else if viewMode === 'cio'}
    <div class="card" style="padding: 25px;">
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>CIO</th>
              <th class="text-center">ASSETS</th>
              <th class="text-center">SPLUNK %</th>
              <th class="text-center">CMDB %</th>
              <th class="text-center">EDR %</th>
              <th class="text-center">STATUS</th>
            </tr>
          </thead>
          <tbody>
            {#each Object.entries(data.cio || {}) as [cio, stats]}
              {@const threat = getThreatLevel(stats.overall_coverage)}
              <tr>
                <td class="font-weight-bold">{cio.toUpperCase()}</td>
                <td class="text-center">{formatNumber(stats.total)}</td>
                <td class="text-center" style="color: {getThreatLevel(stats.splunk_coverage).color};">{stats.splunk_coverage}%</td>
                <td class="text-center" style="color: {getThreatLevel(stats.cmdb_coverage).color};">{stats.cmdb_coverage}%</td>
                <td class="text-center" style="color: {getThreatLevel(stats.edr_coverage).color};">{stats.edr_coverage}%</td>
                <td class="text-center" style="color: {threat.color};">{threat.status}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {:else}
    <div class="card" style="padding: 25px;">
      <div class="header-title" style="margin-bottom: 20px;">APM MONITORING COVERAGE</div>
      
      {@const apmThreat = getThreatLevel(data.apm_coverage?.overall_coverage || 0)}
      <div class="metric-card" style="border-color: {apmThreat.color};">
        <div class="metric-content">
          <div class="metric-label" style="color: {apmThreat.color};">APM MONITORED APPLICATIONS</div>
          <div class="metric-value" style="color: {apmThreat.color};">{formatNumber(data.apm_coverage?.total || 0)}</div>
          <div class="metric-detail">Applications with APM monitoring</div>
        </div>
      </div>

      <div class="d-flex flex-column gap-3" style="margin-top: 20px;">
        {#each [['APM + Splunk', data.apm_coverage?.splunk_coverage || 0], ['APM + CMDB', data.apm_coverage?.cmdb_coverage || 0], ['APM + EDR', data.apm_coverage?.edr_coverage || 0]] as [label, percentage]}
          <div class="coverage-item">
            <div class="coverage-header">
              <span>{label}</span>
              <span style="color: {getThreatLevel(percentage).color};">{percentage}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" style="width: {percentage}%; background: {getThreatLevel(percentage).color};"></div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
{/if}