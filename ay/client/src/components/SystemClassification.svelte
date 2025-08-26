// =============================================================================
// SystemClassification.svelte
// =============================================================================
<!-- /client/src/components/SystemClassification.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;
  let viewMode = 'systems';

  async function fetchData() {
    try {
      const response = await fetch('/api/system-classification');
      if (!response.ok) throw new Error('Failed to fetch system data');
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
    <div class="loading-text">ANALYZING SYSTEM CLASSIFICATIONS</div>
  </div>
{:else if error}
  <div class="error">
    <div class="error-container">
      <h2 class="error-title">SYSTEM SCAN FAILED</h2>
      <p class="error-message">{error}</p>
      <button class="retry-button" on:click={fetchData}>RETRY SCAN</button>
    </div>
  </div>
{:else}
  <div class="main-header-title" style="margin-bottom: 25px;">
    SYSTEM CLASSIFICATION VISIBILITY ANALYSIS
  </div>

  <div class="d-flex gap-2" style="margin-bottom: 20px;">
    <button class="nav-tab {viewMode === 'systems' ? 'active' : ''}" on:click={() => viewMode = 'systems'}>SYSTEM TYPES</button>
    <button class="nav-tab {viewMode === 'classes' ? 'active' : ''}" on:click={() => viewMode = 'classes'}>CLASS ANALYSIS</button>
  </div>

  {#if viewMode === 'systems'}
    <div class="card" style="padding: 25px;">
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>SYSTEM TYPE</th>
              <th class="text-center">ASSETS</th>
              <th class="text-center">SPLUNK %</th>
              <th class="text-center">CMDB %</th>
              <th class="text-center">EDR %</th>
              <th class="text-center">STATUS</th>
            </tr>
          </thead>
          <tbody>
            {#each Object.entries(data.system_classifications || {}) as [system, stats]}
              {@const threat = getThreatLevel(stats.overall_coverage)}
              <tr>
                <td class="font-weight-bold">{system.length > 25 ? system.substring(0, 25) + '...' : system.toUpperCase()}</td>
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
    <div class="d-grid grid-cols-3 gap-4">
      {#each Object.entries(data.classes || {}) as [classNum, stats]}
        {@const threat = getThreatLevel(stats.overall_coverage)}
        <div class="card" style="padding: 20px; border-color: {threat.color};">
          <div class="text-center" style="margin-bottom: 15px;">
            <div style="font-size: 32px; color: {threat.color}; font-weight: bold;">CLASS {classNum}</div>
            <div class="text-secondary">{formatNumber(stats.total)} Assets</div>
          </div>
          <div class="d-flex flex-column gap-2">
            {#each [['Splunk', stats.splunk_coverage], ['CMDB', stats.cmdb_coverage], ['EDR', stats.edr_coverage]] as [label, percentage]}
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
      {/each}
    </div>
  {/if}
{/if}
