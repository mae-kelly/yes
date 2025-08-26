
// Enhanced AO1BusinessDashboard.svelte with exportable functions

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
  
  // EXPORTABLE ASYNC FUNCTIONS
  export async function fetchBusinessData() {
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
  
  export async function fetchMissingAssetsForBU(businessUnit) {
    try {
      const response = await fetch(`/api/missing-asset-predictions?business_unit=${encodeURIComponent(businessUnit)}`);
      const data = await response.json();
      return data;
    } catch (err) {
      return [];
    }
  }
  
  // EXPORTABLE UTILITY FUNCTIONS
  export function getStatusColor(percentage) {
    if (percentage >= 90) return 'var(--status-good)';
    if (percentage >= 75) return 'var(--status-improving)';
    if (percentage >= 50) return 'var(--status-warning)';
    return 'var(--status-critical)';
  }
  
  export function getGlowColor(percentage) {
    if (percentage >= 90) return 'var(--glow-cyan)';
    if (percentage >= 75) return 'var(--glow-blue)';
    if (percentage >= 50) return 'var(--glow-magenta)';
    return 'var(--glow-red)';
  }
  
  export function formatNumber(num) {
    return num?.toLocaleString() || '0';
  }
  
  export function getSystemIcon(systemClass) {
    const lowerClass = systemClass?.toLowerCase() || '';
    if (lowerClass.includes('windows server') || lowerClass.includes('linux server')) return Server;
    if (lowerClass.includes('workstation')) return Monitor;
    if (lowerClass.includes('cloud')) return Cloud;
    if (lowerClass.includes('mobile')) return Smartphone;
    if (lowerClass.includes('network')) return Network;
    if (lowerClass.includes('database')) return Database;
    return Server;
  }
  
  export function getInfrastructureIcon(type) {
    switch(type) {
      case 'On-Prem': return Server;
      case 'Cloud': return Cloud;
      case 'SaaS': return Smartphone;
      case 'API': return Network;
      default: return Server;
    }
  }
  
  export function exportBusinessData() {
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
  
  export function exportSystemData() {
    const blob = new Blob([JSON.stringify(systemClassAnalysis, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ao1_system_classification.json';
    a.click();
    URL.revokeObjectURL(url);
  }
  
  // EXPORTABLE DATA
  export { businessUnitAnalysis, systemClassAnalysis, logTypeVisibility, infrastructureBreakdown, loading, error, selectedBusinessUnit };
  
  // Reactive statements
  $: filteredBusinessUnits = businessUnitAnalysis.filter(bu =>
    bu.business_unit_clean?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  $: filteredSystemClasses = systemClassAnalysis.filter(sc =>
    sc.system_class_clean?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  $: totalSystems = systemClassAnalysis.reduce((sum, s) => sum + s.total_hosts_class, 0);
  
  onMount(() => {
    fetchBusinessData();
    refreshInterval = setInterval(fetchBusinessData, 300000);
    
    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  });
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

    <!-- Rest of the component template remains the same but uses CSS variables -->
    <div class="dashboard-content">
      <div class="metrics-row">
        {#each infrastructureBreakdown as infra}
          <div class="metric-card border-cyan">
            <div class="metric-ring">
              <div class="icon-circle animate-pulse" style="border-color: var(--accent-cyan); box-shadow: var(--glow-cyan)">
                <svelte:component this={getInfrastructureIcon(infra.type)} size={20} color="var(--accent-cyan)" />
              </div>
            </div>
            <div class="metric-content">
              <div class="metric-label text-primary">{infra.type.toUpperCase()}</div>
              <div class="metric-value text-primary">{formatNumber(infra.systems)}</div>
              <div class="metric-detail text-secondary">{((infra.systems / totalSystems) * 100).toFixed(1)}% of Infrastructure</div>
            </div>
            <div class="decorative-bar" style="background: var(--accent-cyan)"></div>
          </div>
        {/each}
      </div>

      <div class="data-table card">
        <div class="table-header">
          <h2 class="main-header-title">BUSINESS UNIT COVERAGE MATRIX</h2>
          <button class="nav-tab" style="padding: 4px 8px; font-size: 0.8rem;" on:click={() => selectedBusinessUnit = null}>
            CLEAR SELECTION
          </button>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th class="system-col">BUSINESS UNIT</th>
                <th class="metric-col text-center">TOTAL HOSTS</th>
                <th class="metric-col text-center">CMDB %</th>
                <th class="metric-col text-center">SPLUNK %</th>
                <th class="metric-col text-center">CROWDSTRIKE %</th>
                <th class="status-col text-center">OVERALL SCORE</th>
                <th class="status-col text-center">AI GAPS</th>
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
                  class="transition"
                >
                  <td class="text-primary font-weight-bold">
                    <div class="d-flex align-items-center gap-2">
                      <Building2 size={16} color="var(--accent-cyan)" />
                      {bu.business_unit_clean}
                    </div>
                  </td>
                  <td class="text-center text-secondary">{formatNumber(bu.total_hosts_bu)}</td>
                  <td class="text-center font-weight-bold" style="color: {getStatusColor(bu.cmdb_bu_pct)}">{bu.cmdb_bu_pct}%</td>
                  <td class="text-center font-weight-bold" style="color: {getStatusColor(bu.splunk_bu_pct)}">{bu.splunk_bu_pct}%</td>
                  <td class="text-center font-weight-bold" style="color: {getStatusColor(bu.crowdstrike_bu_pct)}">{bu.crowdstrike_bu_pct}%</td>
                  <td class="text-center font-weight-bold" style="color: {getStatusColor((bu.cmdb_bu_pct + bu.splunk_bu_pct + bu.crowdstrike_bu_pct) / 3)}">
                    {((bu.cmdb_bu_pct + bu.splunk_bu_pct + bu.crowdstrike_bu_pct) / 3).toFixed(1)}%
                  </td>
                  <td class="text-center">
                    <div class="font-weight-bold" style="color: var(--accent-magenta);">
                      {bu.aiPredictions?.length || 0}
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Additional sections would follow the same pattern -->
    </div>
  {/if}
</main>

<style>
  @import '../styles/dashboard.css';
  
  /* Component-specific overrides if needed */
  .selected {
    background: rgba(0, 229, 255, 0.15) !important;
    border-left: 4px solid var(--accent-cyan);
    box-shadow: var(--glow-cyan);
  }
  
  .gap-2 {
    gap: var(--spacing-sm);
  }
</style>