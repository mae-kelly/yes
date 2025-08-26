// =============================================================================
// LogTypePriority.svelte
// =============================================================================
<!-- /client/src/components/LogTypePriority.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;

  async function fetchData() {
    try {
      const response = await fetch('/api/log-type-priority');
      if (!response.ok) throw new Error('Failed to fetch priority data');
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

  function getPriorityIcon(category) {
    const icons = { 'Network': '🌐', 'Endpoint': '💻', 'Cloud': '☁️', 'Application': '📱', 'Identity': '🔐' };
    return icons[category] || '📊';
  }
</script>

{#if loading}
  <div class="loading">
    <div class="cyber-spinner"></div>
    <div class="loading-text">ANALYZING LOG TYPE PRIORITIES</div>
  </div>
{:else if error}
  <div class="error">
    <div class="error-container">
      <h2 class="error-title">LOG PRIORITY SCAN FAILED</h2>
      <p class="error-message">{error}</p>
      <button class="retry-button" on:click={fetchData}>RETRY SCAN</button>
    </div>
  </div>
{:else}
  <div class="main-header-title" style="margin-bottom: 25px;">
    LOG TYPE PRIORITY MATRIX - CRITICAL SOURCE COVERAGE
  </div>

  <div class="d-grid grid-cols-2 gap-4" style="margin-bottom: 30px;">
    {#each Object.entries(data) as [category, stats]}
      {@const threat = getThreatLevel(stats.overall_priority)}
      <div class="card" style="padding: 25px; border-color: {threat.color};">
        <div class="d-flex align-items-center" style="margin-bottom: 20px;">
          <div class="icon-circle" style="border-color: {threat.color}; margin-right: 15px;">
            <span style="color: {threat.color}; font-size: 18px;">{getPriorityIcon(category)}</span>
          </div>
          <div>
            <div class="header-title" style="color: {threat.color};">{category.toUpperCase()}</div>
            <div class="text-secondary">{formatNumber(stats.total)} Assets</div>
          </div>
        </div>

        <div class="d-flex flex-column gap-3">
          {#each [['Splunk Coverage', stats.splunk_coverage], ['Chronicle Coverage', stats.chronicle_coverage]] as [label, percentage]}
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

        <div class="card text-center" style="margin-top: 20px; padding: 15px; background: rgba(0, 0, 0, 0.6);">
          <div style="color: {threat.color}; font-size: 18px; font-weight: bold;">PRIORITY: {stats.overall_priority}%</div>
          <div style="color: {threat.color}; font-size: 12px;">{threat.status}</div>
        </div>
      </div>
    {/each}
  </div>

  <div class="card" style="padding: 25px;">
    <div class="header-title" style="margin-bottom: 20px;">LOG TYPE PRIORITY MATRIX</div>
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>LOG CATEGORY</th>
            <th class="text-center">ASSETS</th>
            <th class="text-center">SPLUNK %</th>
            <th class="text-center">CHRONICLE %</th>
            <th class="text-center">PRIORITY</th>
            <th class="text-center">STATUS</th>
          </tr>
        </thead>
        <tbody>
          {#each Object.entries(data).sort((a, b) => b[1].overall_priority - a[1].overall_priority) as [category, stats]}
            {@const threat = getThreatLevel(stats.overall_priority)}
            <tr>
              <td class="d-flex align-items-center font-weight-bold">
                <span style="margin-right: 10px;">{getPriorityIcon(category)}</span>
                {category.toUpperCase()}
              </td>
              <td class="text-center">{formatNumber(stats.total)}</td>
              <td class="text-center" style="color: {getThreatLevel(stats.splunk_coverage).color};">{stats.splunk_coverage}%</td>
              <td class="text-center" style="color: {getThreatLevel(stats.chronicle_coverage).color};">{stats.chronicle_coverage}%</td>
              <td class="text-center" style="color: {threat.color};">{stats.overall_priority}%</td>
              <td class="text-center" style="color: {threat.color};">{threat.status}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
{/if}
              <th class="text-center">EDR %</th>
              <th class="text-center">STATUS</th>
            </tr>
          </thead>
          <tbody>
            {#each getSortedEntries() as [type, stats]}
              {@const threat = getThreatLevel(stats.overall_coverage)}
              <tr on:click={() => selectedType = selectedType === type ? null : type}>
                <td class="font-weight-bold">{type.toUpperCase()}</td>
                <td class="text-center">{formatNumber(stats.total)}</td>
                <td class="text-center font-weight-bold" style="color: {getThreatLevel(stats.splunk_coverage).color};">{stats.splunk_coverage}%</td>
                <td class="text-center font-weight-bold" style="color: {getThreatLevel(stats.cmdb_coverage).color};">{stats.cmdb_coverage}%</td>
                <td class="text-center font-weight-bold" style="color: {getThreatLevel(stats.edr_coverage).color};">{stats.edr_coverage}%</td>
                <td class="text-center font-weight-bold" style="color: {threat.color};">{threat.status}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {:else}
    <div class="d-grid grid-cols-4 gap-3">
      {#each Object.entries(data).slice(0, 20) as [type, stats]}
        {@const threat = getThreatLevel(stats.overall_coverage)}
        <div class="card text-center" style="padding: 20px; border-color: {threat.color};">
          <div style="font-size: 24px; color: {threat.color}; font-weight: bold; margin-bottom: 10px;">
            {stats.overall_coverage}%
          </div>
          <div style="font-size: 10px; margin-bottom: 10px;">{type.toUpperCase()}</div>
          <div class="text-muted">{formatNumber(stats.total)} assets</div>
        </div>
      {/each}
    </div>
  {/if}
{/if}
