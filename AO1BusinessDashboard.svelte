// /src/components/AO1BusinessDashboard.svelte

<script>
  import { onMount } from 'svelte';
  import { Building2, Server, Monitor, Cloud, Smartphone, Network, Database, Download, Search, Users, Target } from 'lucide-svelte';
  
  let loading = true;
  let error = null;
  let searchTerm = '';
  let refreshInterval = null;
  let selectedBusinessUnit = null;
  let selectedSystemClass = null;
  
  let businessUnitAnalysis = [];
  let systemClassAnalysis = [];
  let logTypeVisibility = [];
  let infrastructureBreakdown = [];
  
  async function fetchBusinessData() {
    try {
      loading = true;
      
      const [businessUnits, systemClasses, logTypes] = await Promise.all([
        fetch('/api/business-unit-analysis').then(r => r.json()),
        fetch('/api/system-classification-analysis').then(r => r.json()),
        fetch('/api/log-type-visibility').then(r => r.json())
      ]);
      
      businessUnitAnalysis = businessUnits;
      systemClassAnalysis = systemClasses;
      logTypeVisibility = logTypes;
      
      infrastructureBreakdown = [
        { type: 'On-Prem', systems: systemClasses.filter(s => s.system_class_clean?.toLowerCase().includes('server')).reduce((sum, s) => sum + s.total_hosts_class, 0) },
        { type: 'Cloud', systems: systemClasses.filter(s => s.system_class_clean?.toLowerCase().includes('cloud')).reduce((sum, s) => sum + s.total_hosts_class, 0) },
        { type: 'SaaS', systems: systemClasses.filter(s => s.system_class_clean?.toLowerCase().includes('saas')).reduce((sum, s) => sum + s.total_hosts_class, 0) },
        { type: 'API', systems: systemClasses.filter(s => s.system_class_clean?.toLowerCase().includes('api')).reduce((sum, s) => sum + s.total_hosts_class, 0) }
      ];
      
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
  
  onMount(() => {
    fetchBusinessData();
    refreshInterval = setInterval(fetchBusinessData, 300000);
    
    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  });
  
  function getStatusColor(percentage) {
    if (percentage >= 90) return 'var(--status-good)';
    if (percentage >= 75) return 'var(--status-improving)';
    if (percentage >= 50) return 'var(--status-warning)';
    return 'var(--status-critical)';
  }
  
  function getGlowColor(percentage) {
    if (percentage >= 90) return 'var(--glow-cyan)';
    if (percentage >= 75) return 'var(--glow-blue)';
    if (percentage >= 50) return 'var(--glow-magenta)';
    return 'var(--glow-red)';
  }
  
  function formatNumber(num) {
    return num?.toLocaleString() || '0';
  }
  
  function getSystemIcon(systemClass) {
    const lowerClass = systemClass?.toLowerCase() || '';
    if (lowerClass.includes('windows server') || lowerClass.includes('linux server')) return Server;
    if (lowerClass.includes('workstation')) return Monitor;
    if (lowerClass.includes('cloud')) return Cloud;
    if (lowerClass.includes('mobile')) return Smartphone;
    if (lowerClass.includes('network')) return Network;
    if (lowerClass.includes('database')) return Database;
    return Server;
  }
  
  function getInfrastructureIcon(type) {
    switch(type) {
      case 'On-Prem': return Server;
      case 'Cloud': return Cloud;
      case 'SaaS': return Smartphone;
      case 'API': return Network;
      default: return Server;
    }
  }
  
  function exportBusinessData() {
    const exportData = {
      businessUnits: businessUnitAnalysis,
      systemClasses: systemClassAnalysis,
      logTypes: logTypeVisibility
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ao1_business_analysis.json';
    a.click();
    URL.revokeObjectURL(url);
  }
  
  function exportSystemData() {
    const blob = new Blob([JSON.stringify(systemClassAnalysis, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ao1_system_classification.json';
    a.click();
    URL.revokeObjectURL(url);
  }
  
  async function fetchMissingAssetsForBU(businessUnit) {
    try {
      const response = await fetch(`/api/missing-asset-predictions?business_unit=${encodeURIComponent(businessUnit)}`);
      const data = await response.json();
      return data;
    } catch (err) {
      return [];
    }
  }
  
  $: filteredBusinessUnits = businessUnitAnalysis.filter(bu =>
    bu.business_unit_clean?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  $: filteredSystemClasses = systemClassAnalysis.filter(sc =>
    sc.system_class_clean?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  $: totalSystems = systemClassAnalysis.reduce((sum, s) => sum + s.total_hosts_class, 0);
</script>

<main class="dashboard">
  <div class="circuit-overlay"></div>
  
  {#if loading}
    <div class="loading">
      <div class="cyber-spinner">
        <div class="spinner-inner"></div>
      </div>
      <div class="loading-text">
        INITIALIZING BUSINESS UNIT ANALYSIS
        <div class="loading-subtext">Analyzing organizational coverage...</div>
      </div>
    </div>
  {:else if error}
    <div class="error">
      <div class="error-container">
        <div class="error-title" style="color: var(--status-critical);">BUSINESS DATA COMPROMISED</div>
        <div class="error-message">Business unit analysis failed: {error}</div>
        <button class="retry-button" on:click={fetchBusinessData}>RESTORE BUSINESS DATA</button>
      </div>
    </div>
  {:else}
    <div class="dashboard-header">
      <div class="dashboard-title">
        <div class="icon-circle" style="border-color: var(--status-good); box-shadow: var(--glow-cyan)">
          <Building2 size={20} color="var(--status-good)" />
        </div>
        <h1 class="title-main">AO1 BUSINESS UNIT & APPLICATION VIEW</h1>
      </div>
      <div class="dashboard-controls">
        <div class="search-container">
          <input 
            class="search-input" 
            bind:value={searchTerm}
            placeholder="SEARCH UNITS..."
          />
        </div>
        <button class="retry-button" on:click={exportBusinessData} style="padding: 8px 16px; font-size: 0.9rem;">
          <Download size={16} style="margin-right: 4px;" />
          EXPORT
        </button>
      </div>
    </div>

    <div class="dashboard-content">
      <div class="metrics-row">
        {#each infrastructureBreakdown as infra}
          <div class="metric-card" style="border-color: var(--border-cyan)">
            <div class="metric-ring">
              <div class="icon-circle" style="border-color: var(--accent-cyan); box-shadow: var(--glow-cyan)">
                <svelte:component this={getInfrastructureIcon(infra.type)} size={20} color="var(--accent-cyan)" />
              </div>
            </div>
            <div class="metric-content">
              <div class="metric-label" style="color: var(--accent-cyan)">{infra.type.toUpperCase()}</div>
              <div class="metric-value" style="color: var(--accent-cyan)">{formatNumber(infra.systems)}</div>
              <div class="metric-detail">{((infra.systems / totalSystems) * 100).toFixed(1)}% of Infrastructure</div>
            </div>
            <div class="decorative-bar" style="background: var(--accent-cyan)"></div>
          </div>
        {/each}
      </div>

      <div class="data-table card">
        <div class="table-header">
          <h2 class="main-header-title">BUSINESS UNIT COVERAGE MATRIX</h2>
          <div style="display: flex; gap: 8px;">
            <button class="nav-tab" style="padding: 4px 8px; font-size: 0.8rem;" on:click={() => selectedBusinessUnit = null}>
              CLEAR SELECTION
            </button>
          </div>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th class="system-col">BUSINESS UNIT</th>
                <th class="metric-col">TOTAL HOSTS</th>
                <th class="metric-col">CMDB %</th>
                <th class="metric-col">SPLUNK %</th>
                <th class="metric-col">CROWDSTRIKE %</th>
                <th class="status-col">OVERALL SCORE</th>
                <th class="status-col">AI GAPS</th>
              </tr>
            </thead>
            <tbody>
              {#each filteredBusinessUnits.slice(0, 25) as bu}
                <tr 
                  class:selected={selectedBusinessUnit === bu.business_unit_clean}
                  on:click={async () => {
                    selectedBusinessUnit = bu.business_unit_clean;
                    bu.aiPredictions = await fetchMissingAssetsForBU(bu.business_unit_clean);
                  }}
                  style="cursor: pointer;"
                >
                  <td style="color: var(--text-primary); font-weight: var(--font-weight-bold)">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <Building2 size={16} color="var(--accent-cyan)" />
                      {bu.business_unit_clean}
                    </div>
                  </td>
                  <td class="center" style="color: var(--text-secondary)">{formatNumber(bu.total_hosts_bu)}</td>
                  <td class="center" style="color: {getStatusColor(bu.cmdb_bu_pct)}">{bu.cmdb_bu_pct}%</td>
                  <td class="center" style="color: {getStatusColor(bu.splunk_bu_pct)}">{bu.splunk_bu_pct}%</td>
                  <td class="center" style="color: {getStatusColor(bu.crowdstrike_bu_pct)}">{bu.crowdstrike_bu_pct}%</td>
                  <td class="center" style="color: {getStatusColor((bu.cmdb_bu_pct + bu.splunk_bu_pct + bu.crowdstrike_bu_pct) / 3)}; font-weight: bold">
                    {((bu.cmdb_bu_pct + bu.splunk_bu_pct + bu.crowdstrike_bu_pct) / 3).toFixed(1)}%
                  </td>
                  <td class="center">
                    <div style="color: var(--accent-magenta); font-weight: bold;">
                      {bu.aiPredictions?.length || 0}
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>

      <div class="data-table card">
        <div class="table-header">
          <h2 class="main-header-title">SYSTEM CLASSIFICATION COVERAGE</h2>
          <button class="retry-button" on:click={exportSystemData} style="padding: 6px 12px; font-size: 0.8rem;">
            <Download size={14} style="margin-right: 4px;" />
            EXPORT
          </button>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th class="system-col">SYSTEM CLASSIFICATION</th>
                <th class="metric-col">TOTAL HOSTS</th>
                <th class="metric-col">CMDB %</th>
                <th class="metric-col">SPLUNK %</th>
                <th class="metric-col">CROWDSTRIKE %</th>
                <th class="status-col">RISK LEVEL</th>
              </tr>
            </thead>
            <tbody>
              {#each filteredSystemClasses.slice(0, 30) as sc}
                <tr 
                  class:selected={selectedSystemClass === sc.system_class_clean}
                  on:click={() => selectedSystemClass = sc.system_class_clean}
                  style="cursor: pointer;"
                >
                  <td style="color: var(--text-primary); font-weight: var(--font-weight-bold)">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <svelte:component this={getSystemIcon(sc.system_class_clean)} size={16} color="var(--accent-blue)" />
                      <span style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        {sc.system_class_clean}
                      </span>
                    </div>
                  </td>
                  <td class="center" style="color: var(--text-secondary)">{formatNumber(sc.total_hosts_class)}</td>
                  <td class="center" style="color: {getStatusColor(sc.cmdb_class_pct)}">{sc.cmdb_class_pct}%</td>
                  <td class="center" style="color: {getStatusColor(sc.splunk_class_pct)}">{sc.splunk_class_pct}%</td>
                  <td class="center" style="color: {getStatusColor(sc.crowdstrike_class_pct)}">{sc.crowdstrike_class_pct}%</td>
                  <td class="center">
                    {#if (sc.cmdb_class_pct + sc.splunk_class_pct + sc.crowdstrike_class_pct) / 3 < 50}
                      <span style="color: var(--status-critical); font-weight: bold;">HIGH</span>
                    {:else if (sc.cmdb_class_pct + sc.splunk_class_pct + sc.crowdstrike_class_pct) / 3 < 75}
                      <span style="color: var(--status-warning); font-weight: bold;">MEDIUM</span>
                    {:else}
                      <span style="color: var(--status-good); font-weight: bold;">LOW</span>
                    {/if}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="header-title">LOG TYPE VISIBILITY BY ROLE</h2>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 16px;">
          {#each logTypeVisibility as logType}
            <div style="background: rgba(0, 229, 255, 0.05); border: 1px solid var(--border-cyan); border-radius: var(--radius-md); padding: var(--spacing-lg);">
              <h3 style="color: var(--text-primary); margin: 0 0 16px 0; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                <Monitor size={16} color="var(--accent-cyan)" />
                {logType.predicted_log_type}
              </h3>
              <div class="summary-row">
                <span>Total Assets:</span>
                <span style="color: var(--accent-cyan)">{formatNumber(logType.total_assets)}</span>
              </div>
              <div class="summary-row">
                <span>Splunk Visible:</span>
                <span style="color: {getStatusColor(logType.splunk_coverage_pct)}">{formatNumber(logType.splunk_visibility)}</span>
              </div>
              <div class="summary-row">
                <span>GSO Visible:</span>
                <span style="color: {getStatusColor(logType.gso_coverage_pct)}">{formatNumber(logType.gso_visibility)}</span>
              </div>
              
              <div class="coverage-item" style="margin-top: 16px;">
                <div class="coverage-header">
                  <span>Splunk Coverage</span>
                  <span style="color: {getStatusColor(logType.splunk_coverage_pct)}">{logType.splunk_coverage_pct}%</span>
                </div>
                <div class="progress-bar">
                  <div 
                    class="progress-fill" 
                    style="width: {logType.splunk_coverage_pct}%; background: {getStatusColor(logType.splunk_coverage_pct)}; box-shadow: {getGlowColor(logType.splunk_coverage_pct)}"
                  ></div>
                </div>
              </div>
              
              <div class="coverage-item" style="margin-top: 12px;">
                <div class="coverage-header">
                  <span>GSO Coverage</span>
                  <span style="color: {getStatusColor(logType.gso_coverage_pct)}">{logType.gso_coverage_pct}%</span>
                </div>
                <div class="progress-bar">
                  <div 
                    class="progress-fill" 
                    style="width: {logType.gso_coverage_pct}%; background: {getStatusColor(logType.gso_coverage_pct)}; box-shadow: {getGlowColor(logType.gso_coverage_pct)}"
                  ></div>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>

      {#if selectedBusinessUnit}
        <div class="card" style="grid-column: span 12; background: rgba(0, 229, 255, 0.05); border: 2px solid var(--accent-cyan);">
          <div class="card-header">
            <h2 class="header-title" style="color: var(--accent-cyan)">BUSINESS UNIT DEEP DIVE: {selectedBusinessUnit}</h2>
            <button class="retry-button" on:click={() => selectedBusinessUnit = null} style="padding: 4px 8px; font-size: 0.8rem;">CLOSE</button>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; margin-top: 16px;">
            {#each businessUnitAnalysis.filter(bu => bu.business_unit_clean === selectedBusinessUnit) as selectedBU}
              <div>
                <h3 style="color: var(--text-primary); margin-bottom: 12px;">Coverage Metrics</h3>
                <div class="summary-row">
                  <span>CMDB Coverage:</span>
                  <span style="color: {getStatusColor(selectedBU.cmdb_bu_pct)}">{selectedBU.cmdb_bu_pct}%</span>
                </div>
                <div class="summary-row">
                  <span>Splunk Coverage:</span>
                  <span style="color: {getStatusColor(selectedBU.splunk_bu_pct)}">{selectedBU.splunk_bu_pct}%</span>
                </div>
                <div class="summary-row">
                  <span>CrowdStrike Coverage:</span>
                  <span style="color: {getStatusColor(selectedBU.crowdstrike_bu_pct)}">{selectedBU.crowdstrike_bu_pct}%</span>
                </div>
              </div>
              <div>
                <h3 style="color: var(--text-primary); margin-bottom: 12px;">Asset Counts</h3>
                <div class="summary-row">
                  <span>Total Hosts:</span>
                  <span style="color: var(--accent-cyan)">{formatNumber(selectedBU.total_hosts_bu)}</span>
                </div>
                <div class="summary-row">
                  <span>CMDB Present:</span>
                  <span style="color: var(--accent-cyan)">{formatNumber(selectedBU.cmdb_coverage_bu)}</span>
                </div>
                <div class="summary-row">
                  <span>Splunk Logged:</span>
                  <span style="color: var(--accent-cyan)">{formatNumber(selectedBU.splunk_coverage_bu)}</span>
                </div>
                <div class="summary-row">
                  <span>CrowdStrike Protected:</span>
                  <span style="color: var(--accent-cyan)">{formatNumber(selectedBU.crowdstrike_coverage_bu)}</span>
                </div>
              </div>
              <div>
                <h3 style="color: var(--text-primary); margin-bottom: 12px;">AI Predictions</h3>
                {#if selectedBU.aiPredictions}
                  <div class="summary-row">
                    <span>Predicted Missing:</span>
                    <span style="color: var(--accent-magenta)">{selectedBU.aiPredictions.length}</span>
                  </div>
                  <div class="summary-row">
                    <span>High Risk:</span>
                    <span style="color: var(--status-critical)">{selectedBU.aiPredictions.filter(p => p.visibility_risk_score > 0.8).length}</span>
                  </div>
                {:else}
                  <button class="nav-tab" style="padding: 6px 12px; font-size: 0.8rem;" 
                    on:click={async () => {
                      selectedBU.aiPredictions = await fetchMissingAssetsForBU(selectedBU.business_unit_clean);
                      businessUnitAnalysis = businessUnitAnalysis;
                    }}>
                    <Target size={14} style="margin-right: 4px;" />
                    RUN AI ANALYSIS
                  </button>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {/if}
</main>

<style>
  @import '../styles/dashboard.css';
</style>