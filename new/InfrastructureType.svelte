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
    if (percentage >= 90) return { color: 'var(--matrix-primary)', status: 'OPTIMAL' };
    if (percentage >= 75) return { color: 'var(--neural-cyan)', status: 'GOOD' };
    if (percentage >= 50) return { color: 'var(--toxic-yellow)', status: 'MODERATE' };
    if (percentage >= 25) return { color: 'var(--plasma-magenta)', status: 'POOR' };
    return { color: 'var(--danger-crimson)', status: 'CRITICAL' };
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
  <div class="quantum-loader">
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
  </div>
  <div style="text-align: center; margin-top: 30px; color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px;">
    ANALYZING INFRASTRUCTURE MATRIX...
  </div>
{:else if error}
  <div class="dystopia-modal active">
    <h2 style="color: var(--danger-crimson);">INFRASTRUCTURE SCAN FAILED</h2>
    <p style="color: var(--text-muted);">{error}</p>
    <button class="quantum-btn danger" on:click={fetchData}>RETRY SCAN</button>
  </div>
{:else if Object.keys(data).length > 0}

  <!-- AO1 Infrastructure Type Requirement Header -->
  <div class="glitch-text" data-text="INFRASTRUCTURE TYPE VISIBILITY ANALYSIS" style="font-size: 20px; font-weight: bold; letter-spacing: 3px; margin-bottom: 25px;">
    INFRASTRUCTURE TYPE VISIBILITY ANALYSIS
  </div>

  <!-- Controls -->
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
    <div style="display: flex; gap: 10px;">
      <button class="quantum-btn {viewMode === 'table' ? 'active' : ''}" on:click={() => viewMode = 'table'}>
        TABLE VIEW
      </button>
      <button class="quantum-btn {viewMode === 'heatmap' ? 'active' : ''}" on:click={() => viewMode = 'heatmap'}>
        HEATMAP VIEW
      </button>
      <button class="quantum-btn {viewMode === 'gaps' ? 'active' : ''}" on:click={() => viewMode = 'gaps'}>
        COVERAGE GAPS
      </button>
    </div>
    
    <div style="display: flex; gap: 10px; align-items: center;">
      <select bind:value={sortBy} style="background: rgba(0, 0, 0, 0.8); border: 1px solid var(--neural-cyan); color: var(--neural-cyan); padding: 6px; font-family: inherit; font-size: 11px;">
        <option value="total">Asset Count</option>
        <option value="overall_coverage">Overall Coverage</option>
        <option value="splunk_coverage">Splunk Coverage</option>
        <option value="cmdb_coverage">CMDB Coverage</option>
        <option value="edr_coverage">EDR Coverage</option>
        <option value="type">Infrastructure Type</option>
      </select>
      <button class="quantum-btn" style="padding: 6px 12px;" on:click={() => sortOrder = sortOrder === 'desc' ? 'asc' : 'desc'}>
        {sortOrder === 'desc' ? '↓' : '↑'}
      </button>
    </div>
  </div>

  {#if viewMode === 'table'}
    <!-- Comprehensive Infrastructure Table -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        INFRASTRUCTURE TYPE COVERAGE MATRIX
      </h3>
      
      <div style="max-height: 600px; overflow-y: auto;">
        <table style="width: 100%; border-collapse: collapse;">
          <thead>
            <tr style="border-bottom: 2px solid var(--matrix-primary);">
              <th style="text-align: left; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">INFRASTRUCTURE TYPE</th>
              <th style="text-align: center; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">TOTAL ASSETS</th>
              <th style="text-align: center; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">SPLUNK %</th>
              <th style="text-align: center; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">CMDB %</th>
              <th style="text-align: center; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">EDR %</th>
              <th style="text-align: center; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">OVERALL</th>
              <th style="text-align: center; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">STATUS</th>
            </tr>
          </thead>
          <tbody>
            {#each getSortedEntries() as [type, stats]}
              {@const overallThreat = getThreatLevel(stats.overall_coverage)}
              <tr 
                style="border-bottom: 1px solid rgba(0, 255, 65, 0.1); cursor: pointer; transition: all 0.3s; {selectedType === type ? `background: ${overallThreat.color}20; border-left: 4px solid ${overallThreat.color};` : ''}"
                class="neural-link"
                on:click={() => selectedType = selectedType === type ? null : type}
              >
                <td style="padding: 15px; color: var(--matrix-primary); font-size: 11px; font-weight: bold;">
                  {type.toUpperCase()}
                </td>
                <td style="padding: 15px; text-align: center; color: var(--neural-cyan); font-size: 11px;">
                  {formatNumber(stats.total)}
                </td>
                <td style="padding: 15px; text-align: center; color: {getThreatLevel(stats.splunk_coverage).color}; font-size: 11px; font-weight: bold;">
                  {stats.splunk_coverage}%
                </td>
                <td style="padding: 15px; text-align: center; color: {getThreatLevel(stats.cmdb_coverage).color}; font-size: 11px; font-weight: bold;">
                  {stats.cmdb_coverage}%
                </td>
                <td style="padding: 15px; text-align: center; color: {getThreatLevel(stats.edr_coverage).color}; font-size: 11px; font-weight: bold;">
                  {stats.edr_coverage}%
                </td>
                <td style="padding: 15px; text-align: center; color: {overallThreat.color}; font-size: 12px; font-weight: bold;">
                  {stats.overall_coverage}%
                </td>
                <td style="padding: 15px; text-align: center; color: {overallThreat.color}; font-size: 10px; font-weight: bold; letter-spacing: 1px;">
                  {overallThreat.status}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

  {:else if viewMode === 'heatmap'}
    <!-- Infrastructure Heatmap Visualization -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        INFRASTRUCTURE COVERAGE HEATMAP
      </h3>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px;">
        {#each getTopTypes(20) as [type, stats]}
          {@const threat = getThreatLevel(stats.overall_coverage)}
          {@const intensity = stats.overall_coverage / 100}
          <div 
            class="neural-link"
            style="
              background: linear-gradient(135deg, 
                rgba(0, 0, 0, 0.8), 
                {threat.color}{Math.floor(intensity * 60).toString(16).padStart(2, '0')});
              border: 2px solid {threat.color};
              padding: 15px;
              text-align: center;
              cursor: pointer;
              transition: all 0.3s;
              transform: scale({0.9 + intensity * 0.1});
            "
            on:click={() => selectedType = selectedType === type ? null : type}
          >
            <div style="color: {threat.color}; font-size: 16px; font-weight: bold; margin-bottom: 8px; text-shadow: 0 0 10px {threat.color};">
              {stats.overall_coverage}%
            </div>
            <div style="color: var(--neural-cyan); font-size: 9px; margin-bottom: 6px; word-break: break-word; line-height: 1.2;">
              {type.split(' ').slice(0, 3).join(' ').toUpperCase()}
            </div>
            <div style="color: var(--text-muted); font-size: 8px; margin-bottom: 8px;">
              {formatNumber(stats.total)} ASSETS
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 3px; font-size: 8px;">
              <div style="color: {getThreatLevel(stats.splunk_coverage).color};">S:{stats.splunk_coverage}%</div>
              <div style="color: {getThreatLevel(stats.cmdb_coverage).color};">C:{stats.cmdb_coverage}%</div>
              <div style="color: {getThreatLevel(stats.edr_coverage).color};">E:{stats.edr_coverage}%</div>
            </div>
          </div>
        {/each}
      </div>
    </div>

  {:else if viewMode === 'gaps'}
    <!-- Coverage Gaps Analysis -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--danger-crimson); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        INFRASTRUCTURE COVERAGE GAPS - PRIORITY REMEDIATION
      </h3>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
        {#each getCoverageGaps() as [type, stats]}
          <div style="background: rgba(255, 7, 58, 0.05); border: 2px solid var(--danger-crimson); padding: 20px; border-radius: 8px;">
            <div style="color: var(--danger-crimson); font-size: 14px; font-weight: bold; margin-bottom: 10px;">
              {type.toUpperCase()}
            </div>
            <div style="color: var(--text-muted); font-size: 12px; margin-bottom: 15px;">
              {formatNumber(stats.total)} assets • {stats.overall_coverage}% overall coverage
            </div>
            
            <div style="display: grid; gap: 10px;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: var(--text-muted); font-size: 11px;">Splunk Logging Gap:</span>
                <span style="color: var(--danger-crimson); font-size: 12px; font-weight: bold;">
                  {100 - stats.splunk_coverage}% ({formatNumber(stats.total - (stats.total * stats.splunk_coverage / 100))} assets)
                </span>
              </div>
              
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: var(--text-muted); font-size: 11px;">CMDB Documentation Gap:</span>
                <span style="color: var(--danger-crimson); font-size: 12px; font-weight: bold;">
                  {100 - stats.cmdb_coverage}% ({formatNumber(stats.total - (stats.total * stats.cmdb_coverage / 100))} assets)
                </span>
              </div>
              
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: var(--text-muted); font-size: 11px;">EDR Protection Gap:</span>
                <span style="color: var(--danger-crimson); font-size: 12px; font-weight: bold;">
                  {100 - stats.edr_coverage}% ({formatNumber(stats.total - (stats.total * stats.edr_coverage / 100))} assets)
                </span>
              </div>
            </div>

            <div style="margin-top: 15px; padding: 10px; background: rgba(0, 0, 0, 0.6); border: 1px solid var(--danger-crimson); text-align: center;">
              <div style="color: var(--danger-crimson); font-size: 12px; font-weight: bold; letter-spacing: 1px;">
                PRIORITY: {stats.overall_coverage < 30 ? 'IMMEDIATE' : stats.overall_coverage < 50 ? 'HIGH' : 'MEDIUM'}
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Infrastructure Summary Stats -->
  <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 20px;">
    <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: var(--neural-cyan);">
      <div style="font-size: 32px; color: var(--neural-cyan); font-weight: bold; margin-bottom: 8px;">
        {Object.keys(data).length}
      </div>
      <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px;">
        INFRASTRUCTURE TYPES
      </div>
    </div>

    <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: var(--matrix-primary);">
      <div style="font-size: 32px; color: var(--matrix-primary); font-weight: bold; margin-bottom: 8px;">
        {formatNumber(Object.values(data).reduce((sum, stats) => sum + stats.total, 0))}
      </div>
      <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px;">
        TOTAL ASSETS
      </div>
    </div>

    <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: var(--toxic-yellow);">
      <div style="font-size: 32px; color: var(--toxic-yellow); font-weight: bold; margin-bottom: 8px;">
        {Object.values(data).filter(stats => stats.overall_coverage < 60).length}
      </div>
      <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px;">
        COVERAGE GAPS
      </div>
    </div>

    <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: {getThreatLevel(Object.values(data).reduce((sum, stats) => sum + (stats.overall_coverage * stats.total), 0) / Object.values(data).reduce((sum, stats) => sum + stats.total, 0)).color};">
      <div style="font-size: 32px; color: {getThreatLevel(Object.values(data).reduce((sum, stats) => sum + (stats.overall_coverage * stats.total), 0) / Object.values(data).reduce((sum, stats) => sum + stats.total, 0)).color}; font-weight: bold; margin-bottom: 8px;">
        {Math.round(Object.values(data).reduce((sum, stats) => sum + (stats.overall_coverage * stats.total), 0) / Object.values(data).reduce((sum, stats) => sum + stats.total, 0))}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px;">
        WEIGHTED AVERAGE
      </div>
    </div>
  </div>

  <!-- Selected Infrastructure Details -->
  {#if selectedType && data[selectedType]}
    <div class="holo-card-3d" style="margin-top: 20px; padding: 25px; border-color: {getThreatLevel(data[selectedType].overall_coverage).color}; box-shadow: 0 0 30px {getThreatLevel(data[selectedType].overall_coverage).color}40;">
      <h3 style="color: {getThreatLevel(data[selectedType].overall_coverage).color}; font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        DETAILED ANALYSIS: {selectedType.toUpperCase()}
      </h3>
      
      <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; margin-bottom: 25px;">
        <div style="text-align: center;">
          <div style="color: var(--neural-cyan); font-size: 24px; font-weight: bold;">{formatNumber(data[selectedType].total)}</div>
          <div style="color: var(--text-muted); font-size: 11px;">TOTAL ASSETS</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {getThreatLevel(data[selectedType].splunk_coverage).color}; font-size: 24px; font-weight: bold;">{data[selectedType].splunk_coverage}%</div>
          <div style="color: var(--text-muted); font-size: 11px;">SPLUNK LOGS</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {getThreatLevel(data[selectedType].cmdb_coverage).color}; font-size: 24px; font-weight: bold;">{data[selectedType].cmdb_coverage}%</div>
          <div style="color: var(--text-muted); font-size: 11px;">CMDB TRACKED</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {getThreatLevel(data[selectedType].edr_coverage).color}; font-size: 24px; font-weight: bold;">{data[selectedType].edr_coverage}%</div>
          <div style="color: var(--text-muted); font-size: 11px;">EDR PROTECTED</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {getThreatLevel(data[selectedType].overall_coverage).color}; font-size: 24px; font-weight: bold;">{data[selectedType].overall_coverage}%</div>
          <div style="color: var(--text-muted); font-size: 11px;">OVERALL SCORE</div>
        </div>
      </div>

      <!-- Coverage Visualization Bars -->
      <div style="display: grid; gap: 15px;">
        {#each [
          ['SPLUNK LOGGING', data[selectedType].splunk_coverage],
          ['CMDB DOCUMENTATION', data[selectedType].cmdb_coverage],
          ['EDR PROTECTION', data[selectedType].edr_coverage]
        ] as [label, percentage]}
          {@const barThreat = getThreatLevel(percentage)}
          <div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
              <span style="color: var(--neural-cyan); font-size: 12px;">{label}</span>
              <span style="color: {barThreat.color}; font-size: 12px; font-weight: bold;">{percentage}%</span>
            </div>
            <div style="background: rgba(0, 0, 0, 0.6); height: 8px; border-radius: 4px; overflow: hidden;">
              <div style="background: linear-gradient(90deg, {barThreat.color}, {barThreat.color}80); height: 100%; width: {percentage}%; transition: all 1s ease; box-shadow: 0 0 15px {barThreat.color};"></div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
{/if}