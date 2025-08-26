<!-- /src/components/InfrastructureType.svelte -->
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
      const response = await fetch('http://localhost:5000/api/infrastructure-type');
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
      const aVal = sortBy === 'type' ? a[0] : (sortBy === 'total' ? a[1].total : a[1][sortBy] || 0);
      const bVal = sortBy === 'type' ? b[0] : (sortBy === 'total' ? b[1].total : b[1][sortBy] || 0);
      
      if (typeof aVal === 'string') {
        return sortOrder === 'desc' ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
      }
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });
  }

  function getTopTypes(limit = 12) {
    return Object.entries(data)
      .sort((a, b) => b[1].total - a[1].total)
      .slice(0, limit);
  }

  function getCoverageGaps() {
    return Object.entries(data)
      .filter(([_, stats]) => stats.overall_coverage < 60)
      .sort((a, b) => a[1].overall_coverage - b[1].overall_coverage)
      .slice(0, 8);
  }
</script>

{#if loading}
  <div class="loading">
    <div class="cyber-spinner">
      <div class="spinner-inner"></div>
    </div>
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
      <button class="nav-tab {viewMode === 'table' ? 'active' : ''}" on:click={() => viewMode = 'table'}>
        TABLE VIEW
      </button>
      <button class="nav-tab {viewMode === 'heatmap' ? 'active' : ''}" on:click={() => viewMode = 'heatmap'}>
        HEATMAP VIEW
      </button>
      <button class="nav-tab {viewMode === 'gaps' ? 'active' : ''}" on:click={() => viewMode = 'gaps'}>
        COVERAGE GAPS
      </button>
    </div>
    
    <div class="d-flex gap-2 align-items-center">
      <select bind:value={sortBy} class="search-input" style="width: auto; padding: 6px;">
        <option value="total">Asset Count</option>
        <option value="overall_coverage">Overall Coverage</option>
        <option value="splunk_coverage">Splunk Coverage</option>
        <option value="cmdb_coverage">CMDB Coverage</option>
        <option value="edr_coverage">EDR Coverage</option>
        <option value="type">Infrastructure Type</option>
      </select>
      <button class="nav-tab" style="padding: 6px 12px;" on:click={() => sortOrder = sortOrder === 'desc' ? 'asc' : 'desc'}>
        {sortOrder === 'desc' ? '↓' : '↑'}
      </button>
    </div>
  </div>

  {#if viewMode === 'table'}
    <div class="card" style="padding: 25px;">
      <h3 class="header-title" style="margin-bottom: 20px;">
        INFRASTRUCTURE TYPE COVERAGE MATRIX
      </h3>
      
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th class="text-left">INFRASTRUCTURE TYPE</th>
              <th class="text-center">TOTAL ASSETS</th>
              <th class="text-center">SPLUNK %</th>
              <th class="text-center">CMDB %</th>
              <th class="text-center">EDR %</th>
              <th class="text-center">OVERALL</th>
              <th class="text-center">STATUS</th>
            </tr>
          </thead>
          <tbody>
            {#each getSortedEntries() as [type, stats]}
              {@const overallThreat = getThreatLevel(stats.overall_coverage)}
              <tr 
                class="transition {selectedType === type ? 'selected' : ''}"
                style="--status-color: {overallThreat.color}"
                on:click={() => selectedType = selectedType === type ? null : type}
              >
                <td class="font-weight-bold">
                  {type.toUpperCase()}
                </td>
                <td class="text-center">
                  {formatNumber(stats.total)}
                </td>
                <td class="text-center font-weight-bold" style="color: {getThreatLevel(stats.splunk_coverage).color};">
                  {stats.splunk_coverage}%
                </td>
                <td class="text-center font-weight-bold" style="color: {getThreatLevel(stats.cmdb_coverage).color};">
                  {stats.cmdb_coverage}%
                </td>
                <td class="text-center font-weight-bold" style="color: {getThreatLevel(stats.edr_coverage).color};">
                  {stats.edr_coverage}%
                </td>
                <td class="text-center font-weight-bold" style="color: {overallThreat.color};">
                  {stats.overall_coverage}%
                </td>
                <td class="text-center font-weight-bold" style="color: {overallThreat.color}; font-size: 10px;">
                  {overallThreat.status}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

  {:else if viewMode === 'heatmap'}
    <div class="card" style="padding: 25px;">
      <h3 class="header-title" style="margin-bottom: 20px;">
        INFRASTRUCTURE COVERAGE HEATMAP
      </h3>
      
      <div class="d-grid grid-cols-4 gap-3">
        {#each getTopTypes(20) as [type, stats]}
          {@const threat = getThreatLevel(stats.overall_coverage)}
          {@const intensity = stats.overall_coverage / 100}
          <div 
            class="card transition"
            style="
              background: linear-gradient(135deg, 
                var(--secondary-color), 
                {threat.color}40);
              border: 2px solid {threat.color};
              padding: 15px;
              text-align: center;
              cursor: pointer;
              transform: scale({0.9 + intensity * 0.1});
            "
            on:click={() => selectedType = selectedType === type ? null : type}
          >
            <div class="metric-value" style="color: {threat.color}; margin-bottom: 8px;">
              {stats.overall_coverage}%
            </div>
            <div style="color: var(--text-secondary); font-size: 9px; margin-bottom: 6px; word-break: break-word;">
              {type.split(' ').slice(0, 3).join(' ').toUpperCase()}
            </div>
            <div class="metric-detail" style="margin-bottom: 8px;">
              {formatNumber(stats.total)} ASSETS
            </div>
            <div class="d-grid grid-cols-3 gap-1" style="font-size: 8px;">
              <div style="color: {getThreatLevel(stats.splunk_coverage).color};">S:{stats.splunk_coverage}%</div>
              <div style="color: {getThreatLevel(stats.cmdb_coverage).color};">C:{stats.cmdb_coverage}%</div>
              <div style="color: {getThreatLevel(stats.edr_coverage).color};">E:{stats.edr_coverage}%</div>
            </div>
          </div>
        {/each}
      </div>
    </div>

  {:else if viewMode === 'gaps'}
    <div class="card" style="padding: 25px;">
      <h3 style="color: var(--status-critical); font-size: 16px; margin-bottom: 20px;">
        INFRASTRUCTURE COVERAGE GAPS - PRIORITY REMEDIATION
      </h3>
      
      <div class="d-grid grid-cols-2 gap-4">
        {#each getCoverageGaps() as [type, stats]}
          <div class="card" style="background: rgba(255, 35, 64, 0.05); border: 2px solid var(--status-critical); padding: 20px;">
            <div style="color: var(--status-critical); font-size: 14px; font-weight: bold; margin-bottom: 10px;">
              {type.toUpperCase()}
            </div>
            <div class="metric-detail" style="margin-bottom: 15px;">
              {formatNumber(stats.total)} assets • {stats.overall_coverage}% overall coverage
            </div>
            
            <div class="d-flex flex-column gap-2">
              <div class="d-flex justify-content-between align-items-center">
                <span class="text-muted" style="font-size: 11px;">Splunk Logging Gap:</span>
                <span style="color: var(--status-critical); font-size: 12px; font-weight: bold;">
                  {100 - stats.splunk_coverage}% ({formatNumber(Math.floor(stats.total - (stats.total * stats.splunk_coverage / 100)))} assets)
                </span>
              </div>
              
              <div class="d-flex justify-content-between align-items-center">
                <span class="text-muted" style="font-size: 11px;">CMDB Documentation Gap:</span>
                <span style="color: var(--status-critical); font-size: 12px; font-weight: bold;">
                  {100 - stats.cmdb_coverage}% ({formatNumber(Math.floor(stats.total - (stats.total * stats.cmdb_coverage / 100)))} assets)
                </span>
              </div>
              
              <div class="d-flex justify-content-between align-items-center">
                <span class="text-muted" style="font-size: 11px;">EDR Protection Gap:</span>
                <span style="color: var(--status-critical); font-size: 12px; font-weight: bold;">
                  {100 - stats.edr_coverage}% ({formatNumber(Math.floor(stats.total - (stats.total * stats.edr_coverage / 100)))} assets)
                </span>
              </div>
            </div>

            <div class="card text-center" style="margin-top: 15px; padding: 10px; background: rgba(0, 0, 0, 0.6); border: 1px solid var(--status-critical);">
              <div style="color: var(--status-critical); font-size: 12px; font-weight: bold;">
                PRIORITY: {stats.overall_coverage < 30 ? 'IMMEDIATE' : stats.overall_coverage < 50 ? 'HIGH' : 'MEDIUM'}
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <div class="d-grid grid-cols-4 gap-4" style="margin-top: 20px;">
    <div class="card text-center" style="padding: 20px; border-color: var(--accent-cyan);">
      <div style="font-size: 32px; color: var(--accent-cyan); font-weight: bold; margin-bottom: 8px;">
        {Object.keys(data).length}
      </div>
      <div style="color: var(--accent-cyan); font-size: 12px;">
        INFRASTRUCTURE TYPES
      </div>
    </div>

    <div class="card text-center" style="padding: 20px; border-color: var(--status-good);">
      <div style="font-size: 32px; color: var(--status-good); font-weight: bold; margin-bottom: 8px;">
        {formatNumber(Object.values(data).reduce((sum, stats) => sum + stats.total, 0))}
      </div>
      <div style="color: var(--status-good); font-size: 12px;">
        TOTAL ASSETS
      </div>
    </div>

    <div class="card text-center" style="padding: 20px; border-color: var(--status-warning);">
      <div style="font-size: 32px; color: var(--status-warning); font-weight: bold; margin-bottom: 8px;">
        {Object.values(data).filter(stats => stats.overall_coverage < 60).length}
      </div>
      <div style="color: var(--status-warning); font-size: 12px;">
        COVERAGE GAPS
      </div>
    </div>

    <div class="card text-center" style="padding: 20px; border-color: {getThreatLevel(Math.round(Object.values(data).reduce((sum, stats) => sum + (stats.overall_coverage * stats.total), 0) / Object.values(data).reduce((sum, stats) => sum + stats.total, 0))).color};">
      <div style="font-size: 32px; color: {getThreatLevel(Math.round(Object.values(data).reduce((sum, stats) => sum + (stats.overall_coverage * stats.total), 0) / Object.values(data).reduce((sum, stats) => sum + stats.total, 0))).color}; font-weight: bold; margin-bottom: 8px;">
        {Math.round(Object.values(data).reduce((sum, stats) => sum + (stats.overall_coverage * stats.total), 0) / Object.values(data).reduce((sum, stats) => sum + stats.total, 0))}%
      </div>
      <div style="color: var(--text-secondary); font-size: 12px;">
        WEIGHTED AVERAGE
      </div>
    </div>
  </div>

  {#if selectedType && data[selectedType]}
    <div class="card" style="margin-top: 20px; padding: 25px; border-color: {getThreatLevel(data[selectedType].overall_coverage).color}; box-shadow: 0 0 30px {getThreatLevel(data[selectedType].overall_coverage).color}40;">
      <h3 style="color: {getThreatLevel(data[selectedType].overall_coverage).color}; font-size: 16px; margin-bottom: 20px;">
        DETAILED ANALYSIS: {selectedType.toUpperCase()}
      </h3>
      
      <div class="d-grid grid-cols-5 gap-4" style="margin-bottom: 25px;">
        <div class="text-center">
          <div class="metric-value" style="color: var(--accent-cyan);">{formatNumber(data[selectedType].total)}</div>
          <div class="metric-detail">TOTAL ASSETS</div>
        </div>
        <div class="text-center">
          <div class="metric-value" style="color: {getThreatLevel(data[selectedType].splunk_coverage).color};">{data[selectedType].splunk_coverage}%</div>
          <div class="metric-detail">SPLUNK LOGS</div>
        </div>
        <div class="text-center">
          <div class="metric-value" style="color: {getThreatLevel(data[selectedType].cmdb_coverage).color};">{data[selectedType].cmdb_coverage}%</div>
          <div class="metric-detail">CMDB TRACKED</div>
        </div>
        <div class="text-center">
          <div class="metric-value" style="color: {getThreatLevel(data[selectedType].edr_coverage).color};">{data[selectedType].edr_coverage}%</div>
          <div class="metric-detail">EDR PROTECTED</div>
        </div>
        <div class="text-center">
          <div class="metric-value" style="color: {getThreatLevel(data[selectedType].overall_coverage).color};">{data[selectedType].overall_coverage}%</div>
          <div class="metric-detail">OVERALL SCORE</div>
        </div>
      </div>

      <div class="d-flex flex-column gap-3">
        {#each [
          ['SPLUNK LOGGING', data[selectedType].splunk_coverage],
          ['CMDB DOCUMENTATION', data[selectedType].cmdb_coverage],
          ['EDR PROTECTION', data[selectedType].edr_coverage]
        ] as [label, percentage]}
          {@const barThreat = getThreatLevel(percentage)}
          <div>
            <div class="d-flex justify-content-between" style="margin-bottom: 6px;">
              <span style="color: var(--text-secondary); font-size: 12px;">{label}</span>
              <span style="color: {barThreat.color}; font-size: 12px; font-weight: bold;">{percentage}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" style="width: {percentage}%; background: {barThreat.color}; --glow-color: {barThreat.color};"></div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
{/if}