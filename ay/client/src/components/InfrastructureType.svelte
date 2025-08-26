<!-- /client/src/components/InfrastructureType.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;
  let selectedType = null;
  let sortBy = 'total';
  let sortOrder = 'desc';
  let viewMode = 'table';

  async function fetchData() {
    try {
      const response = await fetch('/api/infrastructure-type');
      if (!response.ok) throw new Error('Failed to fetch infrastructure data');
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

  function getSortedEntries() {
    return Object.entries(data).sort((a, b) => {
      const aVal = sortBy === 'type' ? a[0] : a[1][sortBy] || 0;
      const bVal = sortBy === 'type' ? b[0] : b[1][sortBy] || 0;
      
      if (typeof aVal === 'string') {
        return sortOrder === 'desc' ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
      }
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });
  }
</script>

{#if loading}
  <div class="loading">
    <div class="cyber-spinner"></div>
    <div class="loading-text">
      ANALYZING INFRASTRUCTURE MATRIX
      <div class="loading-subtext">Scanning infrastructure types...</div>
    </div>
  </div>
{:else if error}
  <div class="error">
    <div class="error-container">
      <h2 class="error-title">INFRASTRUCTURE SCAN FAILED</h2>
      <p class="error-message">{error}</p>
      <button class="retry-button" on:click={fetchData}>RETRY SCAN</button>
    </div>
  </div>
{:else if Object.keys(data).length > 0}
  <div class="main-header-title" style="margin-bottom: 25px;">
    INFRASTRUCTURE TYPE VISIBILITY ANALYSIS
  </div>

  <div class="d-flex justify-content-between align-items-center" style="margin-bottom: 20px;">
    <div class="d-flex gap-2">
      <button class="nav-tab {viewMode === 'table' ? 'active' : ''}" on:click={() => viewMode = 'table'}>TABLE VIEW</button>
      <button class="nav-tab {viewMode === 'heatmap' ? 'active' : ''}" on:click={() => viewMode = 'heatmap'}>HEATMAP VIEW</button>
    </div>
  </div>

  {#if viewMode === 'table'}
    <div class="card" style="padding: 25px;">
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>INFRASTRUCTURE TYPE</th>
              <th class="text-center">TOTAL ASSETS</th>
              <th class="text-center">SPLUNK %</th>
              <th class="text-center">CMDB %</th>
              <th class="text-center">EDR %</th>
              <th class="text-center">STATUS</th>
            </tr>
          </thead>
          <tbody>
            {#each getSortedEntries() as [type, stats]}
              {#if stats}
                <tr on:click={() => selectedType = selectedType === type ? null : type}>
                  <td class="font-weight-bold">{type.toUpperCase()}</td>
                  <td class="text-center">{formatNumber(stats.total)}</td>
                  <td class="text-center font-weight-bold" style="color: {getThreatLevel(stats.splunk_coverage).color};">{stats.splunk_coverage}%</td>
                  <td class="text-center font-weight-bold" style="color: {getThreatLevel(stats.cmdb_coverage).color};">{stats.cmdb_coverage}%</td>
                  <td class="text-center font-weight-bold" style="color: {getThreatLevel(stats.edr_coverage).color};">{stats.edr_coverage}%</td>
                  <td class="text-center font-weight-bold" style="color: {getThreatLevel(stats.overall_coverage).color};">{getThreatLevel(stats.overall_coverage).status}</td>
                </tr>
              {/if}
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {:else}
    <div class="d-grid grid-cols-4 gap-3">
      {#each Object.entries(data).slice(0, 20) as [type, stats]}
        {#if stats}
          <div class="card text-center" style="padding: 20px; border-color: {getThreatLevel(stats.overall_coverage).color};">
            <div style="font-size: 24px; color: {getThreatLevel(stats.overall_coverage).color}; font-weight: bold; margin-bottom: 10px;">
              {stats.overall_coverage}%
            </div>
            <div style="font-size: 10px; margin-bottom: 10px;">{type.toUpperCase()}</div>
            <div class="text-muted">{formatNumber(stats.total)} assets</div>
          </div>
        {/if}
      {/each}
    </div>
  {/if}
{/if}