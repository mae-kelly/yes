// /src/components/AO1SystemClassificationDashboard.svelte

<script>
  import { onMount } from 'svelte';
  import { Server, Monitor, Cloud, Smartphone, Network, Database, Download, Search, Shield, AlertTriangle, CheckCircle, Zap } from 'lucide-svelte';
  
  let loading = true;
  let error = null;
  let searchTerm = '';
  let refreshInterval = null;
  let selectedSystemClass = null;
  let viewMode = 'classification';
  
  let systemClassAnalysis = [];
  let securityControlCoverage = {};
  let networkAppliances = [];
  let serverBreakdown = [];
  
  async function fetchSystemClassData() {
    try {
      loading = true;
      
      const [systemClasses] = await Promise.all([
        fetch('/api/system-classification-analysis').then(r => r.json())
      ]);
      
      systemClassAnalysis = systemClasses;
      
      securityControlCoverage = {
        webServers: systemClasses.filter(s => s.system_class_clean?.toLowerCase().includes('web server')),
        windowsServers: systemClasses.filter(s => s.system_class_clean?.toLowerCase().includes('windows server')),
        linuxServers: systemClasses.filter(s => s.system_class_clean?.toLowerCase().includes('linux server')),
        databases: systemClasses.filter(s => s.system_class_clean?.toLowerCase().includes('database')),
        networkAppliances: systemClasses.filter(s => s.system_class_clean?.toLowerCase().includes('network'))
      };
      
      serverBreakdown = [
        { type: 'Windows Server', count: securityControlCoverage.windowsServers.reduce((sum, s) => sum + s.total_hosts_class, 0) },
        { type: 'Linux Server', count: securityControlCoverage.linuxServers.reduce((sum, s) => sum + s.total_hosts_class, 0) },
        { type: 'Web Server', count: securityControlCoverage.webServers.reduce((sum, s) => sum + s.total_hosts_class, 0) },
        { type: 'Database', count: securityControlCoverage.databases.reduce((sum, s) => sum + s.total_hosts_class, 0) },
        { type: 'Network Appliance', count: securityControlCoverage.networkAppliances.reduce((sum, s) => sum + s.total_hosts_class, 0) }
      ];
      
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
  
  onMount(() => {
    fetchSystemClassData();
    refreshInterval = setInterval(fetchSystemClassData, 300000);
    
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
  
  function getServerTypeIcon(type) {
    switch(type) {
      case 'Windows Server': return Server;
      case 'Linux Server': return Server;
      case 'Web Server': return Monitor;
      case 'Database': return Database;
      case 'Network Appliance': return Network;
      default: return Server;
    }
  }
  
  function exportSystemData() {
    const exportData = {
      systemClassifications: systemClassAnalysis,
      securityControlCoverage: securityControlCoverage,
      serverBreakdown: serverBreakdown
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ao1_system_classification_analysis.json';
    a.click();
    URL.revokeObjectURL(url);
  }
  
  function calculateRiskScore(systemClass) {
    const avgCoverage = (systemClass.cmdb_class_pct + systemClass.splunk_class_pct + systemClass.crowdstrike_class_pct) / 3;
    const isServer = systemClass.system_class_clean?.toLowerCase().includes('server');
    const multiplier = isServer ? 1.5 : 1.0;
    
    return Math.min((100 - avgCoverage) * multiplier, 100);
  }
  
  $: filteredSystemClasses = systemClassAnalysis.filter(sc =>
    sc.system_class_clean?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  $: totalSystems = systemClassAnalysis.reduce((sum, s) => sum + s.total_hosts_class, 0);
  $: totalServers = serverBreakdown.reduce((sum, s) => sum + s.count, 0);
</script>

<main class="dashboard">
  <div class="circuit-overlay"></div>
  
  {#if loading}
    <div class="loading">
      <div class="cyber-spinner">
        <div class="spinner-inner"></div>
      </div>
      <div class="loading-text">
        INITIALIZING SYSTEM CLASSIFICATION
        <div class="loading-subtext">Analyzing infrastructure types...</div>
      </div>
    </div>
  {:else if error}
    <div class="error">
      <div class="error-container">
        <div class="error-title" style="color: var(--status-critical);">SYSTEM DATA COMPROMISED</div>
        <div class="error-message">System classification failed: {error}</div>
        <button class="retry-button" on:click={fetchSystemClassData}>RESTORE SYSTEM DATA</button>
      </div>
    </div>
  {:else}
    <div class="dashboard-header">
      <div class="dashboard-title">
        <div class="icon-circle" style="border-color: var(--status-good); box-shadow: var(--glow-cyan)">
          <Server size={20} color="var(--status-good)" />
        </div>
        <h1 class="title-main">AO1 SYSTEM CLASSIFICATION VIEW</h1>
      </div>
      <div class="dashboard-controls">
        <div class="search-container">
          <input 
            class="search-input" 
            bind:value={searchTerm}
            placeholder="SEARCH SYSTEMS..."
          />
        </div>
        <div class="nav-tabs" style="margin: 0;">
          <div 
            class="nav-tab {viewMode === 'classification' ? 'active' : ''}"
            on:click={() => viewMode = 'classification'}
            style="padding: 6px 12px; font-size: 0.8rem; margin: 0; margin-right: 8px;"
          >
            CLASSIFICATION
          </div>
          <div 
            class="nav-tab {viewMode === 'security' ? 'active' : ''}"
            on:click={() => viewMode = 'security'}
            style="padding: 6px 12px; font-size: 0.8rem; margin: 0; margin-right: 8px;"
          >
            SECURITY
          </div>
        </div>
        <button class="retry-button" on:click={exportSystemData} style="padding: 8px 16px; font-size: 0.9rem;">
          <Download size={16} style="margin-right: 4px;" />
          EXPORT
        </button>
      </div>
    </div>

    <div class="dashboard-content">
      {#if viewMode === 'classification'}
        <div class="metrics-row">
          {#each serverBreakdown as server}
            <div class="metric-card" style="border-color: var(--border-cyan)">
              <div class="metric-ring">
                <div class="icon-circle" style="border-color: var(--accent-cyan); box-shadow: var(--glow-cyan)">
                  <svelte:component this={getServerTypeIcon(server.type)} size={20} color="var(--accent-cyan)" />
                </div>
              </div>
              <div class="metric-content">
                <div class="metric-label" style="color: var(--accent-cyan)">{server.type.toUpperCase()}</div>
                <div class="metric-value" style="color: var(--accent-cyan)">{formatNumber(server.count)}</div>
                <div class="metric-detail">{((server.count / totalServers) * 100).toFixed(1)}% of Server Fleet</div>
              </div>
              <div class="decorative-bar" style="background: var(--accent-cyan)"></div>
            </div>
          {/each}
        </div>

        <div class="data-table card">
          <div class="table-header">
            <h2 class="main-header-title">DETAILED SYSTEM CLASSIFICATION COVERAGE</h2>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th class="system-col">SYSTEM CLASSIFICATION</th>
                  <th class="metric-col">HOSTS</th>
                  <th class="metric-col">CMDB %</th>
                  <th class="metric-col">SPLUNK %</th>
                  <th class="metric-col">EDR %</th>
                  <th class="status-col">RISK SCORE</th>
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
                        <span style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                          {sc.system_class_clean}
                        </span>
                      </div>
                    </td>
                    <td class="center" style="color: var(--text-secondary)">{formatNumber(sc.total_hosts_class)}</td>
                    <td class="center" style="color: {getStatusColor(sc.cmdb_class_pct)}">{sc.cmdb_class_pct}%</td>
                    <td class="center" style="color: {getStatusColor(sc.splunk_class_pct)}">{sc.splunk_class_pct}%</td>
                    <td class="center" style="color: {getStatusColor(sc.crowdstrike_class_pct)}">{sc.crowdstrike_class_pct}%</td>
                    <td class="center">
                      {#if calculateRiskScore(sc) > 50}
                        <span style="color: var(--status-critical); font-weight: bold;">{calculateRiskScore(sc).toFixed(0)}%</span>
                      {:else if calculateRiskScore(sc) > 25}
                        <span style="color: var(--status-warning); font-weight: bold;">{calculateRiskScore(sc).toFixed(0)}%</span>
                      {:else}
                        <span style="color: var(--status-good); font-weight: bold;">{calculateRiskScore(sc).toFixed(0)}%</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      {/if}

      {#if viewMode === 'security'}
        <div class="metrics-row">
          <div class="metric-card" style="border-color: var(--status-good)">
            <div class="metric-ring">
              <div class="icon-circle" style="border-color: var(--status-good); box-shadow: var(--glow-cyan)">
                <Shield size={20} color="var(--status-good)" />
              </div>
            </div>
            <div class="metric-content">
              <div class="metric-label" style="color: var(--status-good)">EDR PROTECTED</div>
              <div class="metric-value" style="color: var(--status-good)">
                {formatNumber(systemClassAnalysis.reduce((sum, s) => sum + s.crowdstrike_coverage_class, 0))}
              </div>
              <div class="metric-detail">Axonius Console Stats</div>
            </div>
            <div class="decorative-bar" style="background: var(--status-good)"></div>
          </div>

          <div class="metric-card" style="border-color: var(--status-improving)">
            <div class="metric-ring">
              <div class="icon-circle" style="border-color: var(--status-improving); box-shadow: var(--glow-blue)">
                <Zap size={20} color="var(--status-improving)" />
              </div>
            </div>
            <div class="metric-content">
              <div class="metric-label" style="color: var(--status-improving)">TANIUM COVERAGE</div>
              <div class="metric-value" style="color: var(--status-improving)">
                {formatNumber(systemClassAnalysis.reduce((sum, s) => sum + (s.tanium_coverage_class || 0), 0))}
              </div>
              <div class="metric-detail">Agent-Based Control</div>
            </div>
            <div class="decorative-bar" style="background: var(--status-improving)"></div>
          </div>

          <div class="metric-card" style="border-color: var(--status-warning)">
            <div class="metric-ring">
              <div class="icon-circle" style="border-color: var(--status-warning); box-shadow: var(--glow-magenta)">
                <AlertTriangle size={20} color="var(--status-warning)" />
              </div>
            </div>
            <div class="metric-content">
              <div class="metric-label" style="color: var(--status-warning)">DLP COVERAGE</div>
              <div class="metric-value" style="color: var(--status-warning)">
                {formatNumber(systemClassAnalysis.reduce((sum, s) => sum + (s.dlp_coverage_class || 0), 0))}
              </div>
              <div class="metric-detail">Data Loss Prevention</div>
            </div>
            <div class="decorative-bar" style="background: var(--status-warning)"></div>
          </div>

          <div class="metric-card" style="border-color: var(--status-critical)">
            <div class="metric-ring">
              <div class="icon-circle" style="border-color: var(--status-critical); box-shadow: var(--glow-red)">
                <AlertTriangle size={20} color="var(--status-critical)" />
              </div>
            </div>
            <div class="metric-content">
              <div class="metric-label" style="color: var(--status-critical)">UNPROTECTED SYSTEMS</div>
              <div class="metric-value" style="color: var(--status-critical)">
                {formatNumber(systemClassAnalysis.filter(s => s.crowdstrike_class_pct < 50 && s.splunk_class_pct < 50).reduce((sum, s) => sum + s.total_hosts_class, 0))}
              </div>
              <div class="metric-detail">Critical Security Gaps</div>
            </div>
            <div class="decorative-bar animate-blink" style="background: var(--status-critical)"></div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="header-title">SECURITY CONTROL EFFECTIVENESS BY SYSTEM TYPE</h2>
          </div>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 24px; margin-top: 16px;">
            <div style="background: rgba(0, 229, 255, 0.05); border: 1px solid var(--border-cyan); border-radius: var(--radius-md); padding: var(--spacing-lg);">
              <h3 style="color: var(--text-primary); margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;">
                <Server size={16} color="var(--accent-cyan)" />
                WEB SERVERS
              </h3>
              {#each securityControlCoverage.webServers.slice(0, 5) as webServer}
                <div class="summary-row" style="font-size: 0.9rem;">
                  <span>{webServer.system_class_clean.substring(0, 25)}...</span>
                  <span style="color: {getStatusColor(webServer.splunk_class_pct)}">{webServer.splunk_class_pct}%</span>
                </div>
              {/each}
            </div>

            <div style="background: rgba(0, 149, 255, 0.05); border: 1px solid var(--border-blue); border-radius: var(--radius-md); padding: var(--spacing-lg);">
              <h3 style="color: var(--text-primary); margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;">
                <Database size={16} color="var(--accent-blue)" />
                DATABASE SYSTEMS
              </h3>
              {#each securityControlCoverage.databases.slice(0, 5) as database}
                <div class="summary-row" style="font-size: 0.9rem;">
                  <span>{database.system_class_clean.substring(0, 25)}...</span>
                  <span style="color: {getStatusColor(database.crowdstrike_class_pct)}">{database.crowdstrike_class_pct}%</span>
                </div>
              {/each}
            </div>

            <div style="background: rgba(255, 44, 196, 0.05); border: 1px solid var(--border-magenta); border-radius: var(--radius-md); padding: var(--spacing-lg);">
              <h3 style="color: var(--text-primary); margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;">
                <Network size={16} color="var(--accent-magenta)" />
                NETWORK APPLIANCES
              </h3>
              {#each securityControlCoverage.networkAppliances.slice(0, 5) as network}
                <div class="summary-row" style="font-size: 0.9rem;">
                  <span>{network.system_class_clean.substring(0, 25)}...</span>
                  <span style="color: {getStatusColor(network.cmdb_class_pct)}">{network.cmdb_class_pct}%</span>
                </div>
              {/each}
            </div>
          </div>
        </div>
      {/if}

      {#if selectedSystemClass}
        <div class="card" style="grid-column: span 12; background: rgba(0, 229, 255, 0.05); border: 2px solid var(--accent-cyan);">
          <div class="card-header">
            <h2 class="header-title" style="color: var(--accent-cyan)">SYSTEM CLASS ANALYSIS: {selectedSystemClass}</h2>
            <button class="retry-button" on:click={() => selectedSystemClass = null} style="padding: 4px 8px; font-size: 0.8rem;">CLOSE</button>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; margin-top: 16px;">
            {#each systemClassAnalysis.filter(sc => sc.system_class_clean === selectedSystemClass) as selectedSC}
              <div>
                <h3 style="color: var(--text-primary); margin-bottom: 12px;">Coverage Analysis</h3>
                <div class="coverage-item">
                  <div class="coverage-header">
                    <span>CMDB Present</span>
                    <span style="color: {getStatusColor(selectedSC.cmdb_class_pct)}">{selectedSC.cmdb_class_pct}%</span>
                  </div>
                  <div class="progress-bar">
                    <div 
                      class="progress-fill" 
                      style="width: {selectedSC.cmdb_class_pct}%; background: {getStatusColor(selectedSC.cmdb_class_pct)}; box-shadow: {getGlowColor(selectedSC.cmdb_class_pct)}"
                    ></div>
                  </div>
                </div>
                <div class="coverage-item" style="margin-top: 12px;">
                  <div class="coverage-header">
                    <span>Splunk Logging</span>
                    <span style="color: {getStatusColor(selectedSC.splunk_class_pct)}">{selectedSC.splunk_class_pct}%</span>
                  </div>
                  <div class="progress-bar">
                    <div 
                      class="progress-fill" 
                      style="width: {selectedSC.splunk_class_pct}%; background: {getStatusColor(selectedSC.splunk_class_pct)}; box-shadow: {getGlowColor(selectedSC.splunk_class_pct)}"
                    ></div>
                  </div>
                </div>
                <div class="coverage-item" style="margin-top: 12px;">
                  <div class="coverage-header">
                    <span>CrowdStrike EDR</span>
                    <span style="color: {getStatusColor(selectedSC.crowdstrike_class_pct)}">{selectedSC.crowdstrike_class_pct}%</span>
                  </div>
                  <div class="progress-bar">
                    <div 
                      class="progress-fill" 
                      style="width: {selectedSC.crowdstrike_class_pct}%; background: {getStatusColor(selectedSC.crowdstrike_class_pct)}; box-shadow: {getGlowColor(selectedSC.crowdstrike_class_pct)}"
                    ></div>
                  </div>
                </div>
              </div>
              <div>
                <h3 style="color: var(--text-primary); margin-bottom: 12px;">Asset Metrics</h3>
                <div class="summary-row">
                  <span>Total Systems:</span>
                  <span style="color: var(--accent-cyan)">{formatNumber(selectedSC.total_hosts_class)}</span>
                </div>
                <div class="summary-row">
                  <span>CMDB Mapped:</span>
                  <span style="color: var(--accent-cyan)">{formatNumber(selectedSC.cmdb_coverage_class)}</span>
                </div>
                <div class="summary-row">
                  <span>Splunk Monitored:</span>
                  <span style="color: var(--accent-cyan)">{formatNumber(selectedSC.splunk_coverage_class)}</span>
                </div>
                <div class="summary-row">
                  <span>EDR Protected:</span>
                  <span style="color: var(--accent-cyan)">{formatNumber(selectedSC.crowdstrike_coverage_class)}</span>
                </div>
              </div>
              <div>
                <h3 style="color: var(--text-primary); margin-bottom: 12px;">Risk Assessment</h3>
                <div style="background: rgba(0, 0, 0, 0.2); padding: 16px; border-radius: 8px;">
                  <div class="summary-row">
                    <span>Risk Score:</span>
                    <span style="color: {calculateRiskScore(selectedSC) > 50 ? 'var(--status-critical)' : calculateRiskScore(selectedSC) > 25 ? 'var(--status-warning)' : 'var(--status-good)'}; font-weight: bold; font-size: 1.2rem;">
                      {calculateRiskScore(selectedSC).toFixed(0)}%
                    </span>
                  </div>
                  <div style="margin-top: 12px;">
                    {#if calculateRiskScore(selectedSC) > 50}
                      <div style="color: var(--status-critical); font-size: 0.9rem; margin-bottom: 8px;">
                        <AlertTriangle size={14} style="display: inline; margin-right: 4px;" />
                        Critical security gaps detected
                      </div>
                    {:else if calculateRiskScore(selectedSC) > 25}
                      <div style="color: var(--status-warning); font-size: 0.9rem; margin-bottom: 8px;">
                        <AlertTriangle size={14} style="display: inline; margin-right: 4px;" />
                        Moderate security concerns
                      </div>
                    {:else}
                      <div style="color: var(--status-good); font-size: 0.9rem; margin-bottom: 8px;">
                        <CheckCircle size={14} style="display: inline; margin-right: 4px;" />
                        Adequate security coverage
                      </div>
                    {/if}
                  </div>
                </div>
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