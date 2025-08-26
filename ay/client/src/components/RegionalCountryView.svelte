// =============================================================================
// RegionalCountryView.svelte
// =============================================================================
<!-- /client/src/components/RegionalCountryView.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;
  let viewMode = 'regions';

  async function fetchData() {
    try {
      const response = await fetch('/api/regional-country-view');
      if (!response.ok) throw new Error('Failed to fetch regional data');
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
    <div class="loading-text">ANALYZING REGIONAL COVERAGE</div>
  </div>
{:else if error}
  <div class="error">
    <div class="error-container">
      <h2 class="error-title">REGIONAL SCAN FAILED</h2>
      <p class="error-message">{error}</p>
      <button class="retry-button" on:click={fetchData}>RETRY SCAN</button>
    </div>
  </div>
{:else}
  <div class="main-header-title" style="margin-bottom: 25px;">
    REGIONAL & COUNTRY VIEW - GEOGRAPHIC VISIBILITY ANALYSIS
  </div>

  <div class="d-flex gap-2" style="margin-bottom: 20px;">
    <button class="nav-tab {viewMode === 'regions' ? 'active' : ''}" on:click={() => viewMode = 'regions'}>REGIONAL VIEW</button>
    <button class="nav-tab {viewMode === 'countries' ? 'active' : ''}" on:click={() => viewMode = 'countries'}>COUNTRY VIEW</button>
  </div>

  {#if viewMode === 'regions'}
    <div class="d-grid grid-cols-2 gap-4">
      {#each Object.entries(data.regions || {}) as [region, stats]}
        {@const threat = getThreatLevel(stats.overall_coverage)}
        <div class="card" style="padding: 25px; border-color: {threat.color};">
          <div class="header-title" style="color: {threat.color}; margin-bottom: 20px;">
            {region.toUpperCase()}
          </div>
          <div class="text-center" style="margin-bottom: 20px;">
            <div style="font-size: 48px; color: {threat.color}; font-weight: bold;">{formatNumber(stats.total)}</div>
            <div class="text-secondary">Total Assets</div>
          </div>
          <div class="d-flex flex-column gap-3">
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
  {:else}
    <div class="card" style="padding: 25px;">
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>COUNTRY</th>
              <th class="text-center">ASSETS</th>
              <th class="text-center">SPLUNK %</th>
              <th class="text-center">CMDB %</th>
              <th class="text-center">EDR %</th>
              <th class="text-center">STATUS</th>
            </tr>
          </thead>
          <tbody>
            {#each Object.entries(data.countries || {}) as [country, stats]}
              {@const threat = getThreatLevel(stats.overall_coverage)}
              <tr>
                <td class="font-weight-bold">{country.toUpperCase()}</td>
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
  {/if}
{/if}
