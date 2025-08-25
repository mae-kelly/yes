// /src/components/AO1OverviewDashboard.svelte

<script>
  import { onMount } from 'svelte';
  import { BarChart3, Database, Shield, Settings, TrendingUp, Brain, AlertTriangle, CheckCircle } from 'lucide-svelte';
  
  export let searchTerm = '';
  
  let loading = true;
  let error = null;
  let refreshInterval = null;
  
  let overallCoverage = {};
  let domainAnalysis = [];
  let visibilityFactors = [];
  
  export async function fetchOverviewData() {
    try {
      loading = true;
      
      const [overall, domains, factors] = await Promise.all([
        fetch('/api/overall-coverage-totals').then(r => r.json()),
        fetch('/api/domain-analysis').then(r => r.json()),
        fetch('/api/visibility-factor-metrics').then(r => r.json())
      ]);
      
      overallCoverage = overall;
      domainAnalysis = domains;
      visibilityFactors = factors;
      
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
  
  onMount(() => {
    fetchOverviewData();
    refreshInterval = setInterval(fetchOverviewData, 300000);
    
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
  
  export { overallCoverage, domainAnalysis, visibilityFactors, loading, error };
</script>

<main class="dashboard-section">
  {#if loading}
    <div class="loading">
      <div class="cyber-spinner">
        <div class="spinner-inner"></div>
      </div>
      <div class="loading-text">
        INITIALIZING AO1 LOG VISIBILITY MEASUREMENT
        <div class="loading-subtext">Analyzing coverage metrics...</div>
      </div>
    </div>
  {:else if error}
    <div class="error">
      <div class="error-container">
        <div class="error-title" style="color: var(--status-critical);">VISIBILITY COMPROMISED</div>
        <div class="error-message">Log visibility analysis failed: {error}</div>
        <button class="retry-button" on:click={fetchOverviewData}>RESTORE VISIBILITY</button>
      </div>
    </div>
  {:else}
    <div class="dashboard-content">
      <div class="metrics-row">
        <div class="metric-card" style="border-color: {getStatusColor(overallCoverage.splunk_coverage_pct)}">
          <div class="metric-ring">
            <div class="icon-circle" style="border-color: {getStatusColor(overallCoverage.splunk_coverage_pct)}; box-shadow: {getGlowColor(overallCoverage.splunk_coverage_pct)}">
              <BarChart3 size={20} color={getStatusColor(overallCoverage.splunk_coverage_pct)} />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: {getStatusColor(overallCoverage.splunk_coverage_pct)}">SPLUNK LOGGING</div>
            <div class="metric-value" style="color: {getStatusColor(overallCoverage.splunk_coverage_pct)}">{formatNumber(overallCoverage.total_splunk_logging)}</div>
            <div class="metric-detail">{overallCoverage.splunk_coverage_pct}% of {formatNumber(overallCoverage.total_hosts)} Assets</div>
          </div>
          <div class="decorative-bar" style="background: {getStatusColor(overallCoverage.splunk_coverage_pct)}"></div>
        </div>

        <div class="metric-card" style="border-color: {getStatusColor(overallCoverage.cmdb_coverage_pct)}">
          <div class="metric-ring">
            <div class="icon-circle" style="border-color: {getStatusColor(overallCoverage.cmdb_coverage_pct)}; box-shadow: {getGlowColor(overallCoverage.cmdb_coverage_pct)}">
              <Database size={20} color={getStatusColor(overallCoverage.cmdb_coverage_pct)} />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: {getStatusColor(overallCoverage.cmdb_coverage_pct)}">CMDB PRESENT</div>
            <div class="metric-value" style="color: {getStatusColor(overallCoverage.cmdb_coverage_pct)}">{formatNumber(overallCoverage.total_cmdb_present)}</div>
            <div class="metric-detail">{overallCoverage.cmdb_coverage_pct}% Asset Visibility</div>
          </div>
          <div class="decorative-bar" style="background: {getStatusColor(overallCoverage.cmdb_coverage_pct)}"></div>
        </div>

        <div class="metric-card" style="border-color: {getStatusColor(overallCoverage.crowdstrike_coverage_pct)}">
          <div class="metric-ring">
            <div class="icon-circle" style="border-color: {getStatusColor(overallCoverage.crowdstrike_coverage_pct)}; box-shadow: {getGlowColor(overallCoverage.crowdstrike_coverage_pct)}">
              <Shield size={20} color={getStatusColor(overallCoverage.crowdstrike_coverage_pct)} />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: {getStatusColor(overallCoverage.crowdstrike_coverage_pct)}">CROWDSTRIKE AGENT</div>
            <div class="metric-value" style="color: {getStatusColor(overallCoverage.crowdstrike_coverage_pct)}">{formatNumber(overallCoverage.total_crowdstrike)}</div>
            <div class="metric-detail">{overallCoverage.crowdstrike_coverage_pct}% Coverage</div>
          </div>
          <div class="decorative-bar" style="background: {getStatusColor(overallCoverage.crowdstrike_coverage_pct)}"></div>
        </div>

        <div class="metric-card" style="border-color: {getStatusColor(overallCoverage.tanium_coverage_pct)}">
          <div class="metric-ring">
            <div class="icon-circle" style="border-color: {getStatusColor(overallCoverage.tanium_coverage_pct)}; box-shadow: {getGlowColor(overallCoverage.tanium_coverage_pct)}">
              <Settings size={20} color={getStatusColor(overallCoverage.tanium_coverage_pct)} />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: {getStatusColor(overallCoverage.tanium_coverage_pct)}">TANIUM COVERAGE</div>
            <div class="metric-value" style="color: {getStatusColor(overallCoverage.tanium_coverage_pct)}">{formatNumber(overallCoverage.total_tanium)}</div>
            <div class="metric-detail">{overallCoverage.tanium_coverage_pct}% Deployment</div>
          </div>
          <div class="decorative-bar" style="background: {getStatusColor(overallCoverage.tanium_coverage_pct)}"></div>
        </div>
      </div>

      <div class="metrics-row">
        <div class="metric-card" style="border-color: {getStatusColor(overallCoverage.apm_coverage_pct)}">
          <div class="metric-ring">
            <div class="icon-circle" style="border-color: {getStatusColor(overallCoverage.apm_coverage_pct)}; box-shadow: {getGlowColor(overallCoverage.apm_coverage_pct)}">
              <TrendingUp size={20} color={getStatusColor(overallCoverage.apm_coverage_pct)} />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: {getStatusColor(overallCoverage.apm_coverage_pct)}">APM MONITORING</div>
            <div class="metric-value" style="color: {getStatusColor(overallCoverage.apm_coverage_pct)}">{formatNumber(overallCoverage.total_apm)}</div>
            <div class="metric-detail">{overallCoverage.apm_coverage_pct}% Application Coverage</div>
          </div>
          <div class="decorative-bar" style="background: {getStatusColor(overallCoverage.apm_coverage_pct)}"></div>
        </div>

        <div class="metric-card" style="border-color: var(--accent-cyan)">
          <div class="metric-ring">
            <div class="icon-circle animate-pulse" style="border-color: var(--accent-cyan); box-shadow: var(--glow-cyan)">
              <Brain size={20} color="var(--accent-cyan)" />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: var(--accent-cyan)">AI PREDICTED MISSING</div>
            <div class="metric-value" style="color: var(--accent-cyan)">{formatNumber(overallCoverage.ai_predicted_missing)}</div>
            <div class="metric-detail">Neural Network Discoveries</div>
          </div>
          <div class="decorative-bar animate-pulse" style="background: var(--accent-cyan)"></div>
        </div>

        <div class="metric-card" style="border-color: {overallCoverage.high_risk_predictions > 0 ? 'var(--status-critical)' : 'var(--status-good)'}">
          <div class="metric-ring">
            <div class="icon-circle" style="border-color: {overallCoverage.high_risk_predictions > 0 ? 'var(--status-critical)' : 'var(--status-good)'}; box-shadow: {overallCoverage.high_risk_predictions > 0 ? 'var(--glow-red)' : 'var(--glow-cyan)'}">
              {#if overallCoverage.high_risk_predictions > 0}
                <AlertTriangle size={20} color="var(--status-critical)" />
              {:else}
                <CheckCircle size={20} color="var(--status-good)" />
              {/if}
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: {overallCoverage.high_risk_predictions > 0 ? 'var(--status-critical)' : 'var(--status-good)'}">HIGH RISK PREDICTIONS</div>
            <div class="metric-value" style="color: {overallCoverage.high_risk_predictions > 0 ? 'var(--status-critical)' : 'var(--status-good)'}">{formatNumber(overallCoverage.high_risk_predictions)}</div>
            <div class="metric-detail">Critical Visibility Gaps</div>
          </div>
          <div class="decorative-bar" style="background: {overallCoverage.high_risk_predictions > 0 ? 'var(--status-critical)' : 'var(--status-good)'}"></div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="header-title">DOMAIN VISIBILITY ANALYSIS</h2>
        </div>
        <div class="distribution-stats">
          {#each domainAnalysis as domain}
            <div class="stat-box">
              <div class="stat-label">{domain.analysis_type.replace(' Analysis', '').toUpperCase()}</div>
              <div class="stat-value" style="color: var(--status-good)">{formatNumber(domain.total_hosts)}</div>
              <div class="coverage-indicators">
                <div class="coverage-item">
                  <div class="coverage-header">
                    <span>Splunk Logging</span>
                    <span style="color: {getStatusColor(domain.splunk_pct)}">{domain.splunk_pct}%</span>
                  </div>
                  <div class="progress-bar">
                    <div 
                      class="progress-fill" 
                      style="width: {domain.splunk_pct}%; background: {getStatusColor(domain.splunk_pct)}; box-shadow: {getGlowColor(domain.splunk_pct)}"
                    ></div>
                  </div>
                </div>
                <div class="coverage-item">
                  <div class="coverage-header">
                    <span>CMDB Present</span>
                    <span style="color: {getStatusColor(domain.cmdb_pct)}">{domain.cmdb_pct}%</span>
                  </div>
                  <div class="progress-bar">
                    <div 
                      class="progress-fill" 
                      style="width: {domain.cmdb_pct}%; background: {getStatusColor(domain.cmdb_pct)}; box-shadow: {getGlowColor(domain.cmdb_pct)}"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</main>

<style>
  @import '../styles/dashboard.css';
  
  .dashboard-section {
    width: 100%;
    height: 100%;
  }
</style>

// /src/components/AO1RegionalDashboard.svelte

<script>
  import { onMount } from 'svelte';
  import { Globe, MapPin, Building, Users } from 'lucide-svelte';
  
  export let searchTerm = '';
  
  let loading = true;
  let error = null;
  let refreshInterval = null;
  
  let regionalAnalysis = [];
  let cioAnalysis = [];
  
  export async function fetchRegionalData() {
    try {
      loading = true;
      
      const [regional, cio] = await Promise.all([
        fetch('/api/regional-analysis').then(r => r.json()),
        fetch('/api/cio-analysis').then(r => r.json())
      ]);
      
      regionalAnalysis = regional;
      cioAnalysis = cio;
      
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
  
  onMount(() => {
    fetchRegionalData();
    refreshInterval = setInterval(fetchRegionalData, 300000);
    
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
  
  function formatNumber(num) {
    return num?.toLocaleString() || '0';
  }
  
  function getRegionIcon(region) {
    switch(region) {
      case 'North America': return MapPin;
      case 'EMEA': return Globe;
      case 'APAC': return Building;
      case 'LATAM': return Users;
      default: return Globe;
    }
  }
  
  $: filteredRegional = regionalAnalysis.filter(region =>
    region.standardized_region?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  $: filteredCIO = cioAnalysis.filter(cio =>
    cio.cio?.toLowerCase().includes(searchTerm.toLowerCase())
  );
</script>

<main class="dashboard-section">
  {#if loading}
    <div class="loading">
      <div class="cyber-spinner">
        <div class="spinner-inner"></div>
      </div>
      <div class="loading-text">
        INITIALIZING REGIONAL ANALYSIS
        <div class="loading-subtext">Mapping global visibility...</div>
      </div>
    </div>
  {:else if error}
    <div class="error">
      <div class="error-container">
        <div class="error-title" style="color: var(--status-critical);">REGIONAL DATA COMPROMISED</div>
        <div class="error-message">Regional analysis failed: {error}</div>
        <button class="retry-button" on:click={fetchRegionalData}>RESTORE REGIONAL DATA</button>
      </div>
    </div>
  {:else}
    <div class="dashboard-content">
      <div class="data-table card">
        <div class="table-header">
          <h2 class="main-header-title">REGIONAL COVERAGE ANALYSIS</h2>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th class="system-col">REGION</th>
                <th class="metric-col">TOTAL HOSTS</th>
                <th class="metric-col">CMDB %</th>
                <th class="metric-col">SPLUNK %</th>
                <th class="metric-col">CROWDSTRIKE %</th>
              </tr>
            </thead>
            <tbody>
              {#each filteredRegional as region}
                <tr>
                  <td style="color: var(--text-primary); font-weight: var(--font-weight-bold)">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <svelte:component this={getRegionIcon(region.standardized_region)} size={16} color="var(--accent-cyan)" />
                      {region.standardized_region}
                    </div>
                  </td>
                  <td class="center" style="color: var(--text-secondary)">{formatNumber(region.total_hosts_region)}</td>
                  <td class="center" style="color: {getStatusColor(region.cmdb_region_pct)}">{region.cmdb_region_pct}%</td>
                  <td class="center" style="color: {getStatusColor(region.splunk_region_pct)}">{region.splunk_region_pct}%</td>
                  <td class="center" style="color: {getStatusColor(region.crowdstrike_region_pct)}">{region.crowdstrike_region_pct}%</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>

      <div class="data-table card">
        <div class="table-header">
          <h2 class="main-header-title">CIO ORGANIZATIONAL COVERAGE</h2>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th class="system-col">CIO ORGANIZATION</th>
                <th class="metric-col">TOTAL HOSTS</th>
                <th class="metric-col">SPLUNK %</th>
                <th class="metric-col">CMDB %</th>
                <th class="metric-col">CROWDSTRIKE %</th>
              </tr>
            </thead>
            <tbody>
              {#each filteredCIO.slice(0, 20) as cio}
                <tr>
                  <td style="color: var(--text-primary); font-weight: var(--font-weight-bold)">
                    <div style="display: flex; align-items: center; gap: 8px;">
                      <Users size={16} color="var(--accent-blue)" />
                      {cio.cio}
                    </div>
                  </td>
                  <td class="center" style="color: var(--text-secondary)">{formatNumber(cio.total_hosts_cio)}</td>
                  <td class="center" style="color: {getStatusColor(cio.splunk_cio_pct)}">{cio.splunk_cio_pct}%</td>
                  <td class="center" style="color: {getStatusColor(cio.cmdb_cio_pct)}">{cio.cmdb_cio_pct}%</td>
                  <td class="center" style="color: {getStatusColor(cio.crowdstrike_cio_pct)}">{cio.crowdstrike_cio_pct}%</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  {/if}
</main>

<style>
  @import '../styles/dashboard.css';
  
  .dashboard-section {
    width: 100%;
    height: 100%;
  }
</style>

// /src/components/AO1AIDashboard.svelte

<script>
  import { onMount } from 'svelte';
  import { Brain, Target, AlertTriangle, Zap, Download, Play } from 'lucide-svelte';
  
  export let searchTerm = '';
  
  let loading = true;
  let error = null;
  let selectedAsset = null;
  let refreshInterval = null;
  
  let aiInsights = {};
  let missingAssets = [];
  let drillDownData = {};
  
  export async function fetchAIData() {
    try {
      loading = true;
      
      const [insights, missing] = await Promise.all([
        fetch('/api/ai-visibility-insights').then(r => r.json()).catch(() => ({})),
        fetch('/api/missing-asset-predictions').then(r => r.json()).catch(() => [])
      ]);
      
      aiInsights = insights;
      missingAssets = missing;
      
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
  
  onMount(() => {
    fetchAIData();
    refreshInterval = setInterval(fetchAIData, 300000);
    
    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  });
  
  function handleAssetDrillDown(asset) {
    selectedAsset = asset;
    drillDownData = {
      asset: asset,
      relatedAssets: missingAssets.filter(a => 
        a.business_unit === asset.business_unit && a.predicted_hostname !== asset.predicted_hostname
      ).slice(0, 10),
      riskFactors: calculateRiskFactors(asset)
    };
  }
  
  function calculateRiskFactors(asset) {
    let factors = [];
    
    if (asset.existence_probability > 0.9) factors.push({ factor: 'High AI Confidence', weight: 0.3, color: 'var(--status-critical)' });
    if (asset.predicted_role === 'Server') factors.push({ factor: 'Critical Infrastructure', weight: 0.4, color: 'var(--status-critical)' });
    if (asset.business_unit && asset.business_unit.toLowerCase().includes('prod')) factors.push({ factor: 'Production Environment', weight: 0.3, color: 'var(--status-warning)' });
    if (asset.predicted_hostname.includes('.com')) factors.push({ factor: 'External Exposure', weight: 0.2, color: 'var(--status-warning)' });
    
    return factors;
  }
  
  function getStatusColor(percentage) {
    if (percentage >= 90) return 'var(--status-good)';
    if (percentage >= 75) return 'var(--status-improving)';
    if (percentage >= 50) return 'var(--status-warning)';
    return 'var(--status-critical)';
  }
  
  function getRiskColor(riskLevel) {
    switch(riskLevel?.toUpperCase()) {
      case 'CRITICAL': return 'var(--status-critical)';
      case 'HIGH': return 'var(--status-warning)';
      case 'MEDIUM': return 'var(--status-improving)';
      default: return 'var(--status-good)';
    }
  }
  
  function formatNumber(num) {
    return num?.toLocaleString() || '0';
  }
  
  function trainAIModel() {
    fetch('/api/train-visibility-ai')
      .then(response => response.json())
      .then(data => {
        console.log('AI Training initiated:', data);
        setTimeout(fetchAIData, 5000);
      })
      .catch(err => console.error('Training failed:', err));
  }
  
  function exportData() {
    const blob = new Blob([JSON.stringify(missingAssets, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ao1_ai_predictions.json';
    a.click();
    URL.revokeObjectURL(url);
  }
  
  $: filteredMissingAssets = missingAssets.filter(asset => 
    asset.predicted_hostname?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    asset.business_unit?.toLowerCase().includes(searchTerm.toLowerCase())
  );
</script>

<main class="dashboard-section">
  {#if loading}
    <div class="loading">
      <div class="cyber-spinner">
        <div class="spinner-inner"></div>
      </div>
      <div class="loading-text">
        INITIALIZING AI THREAT PREDICTION ENGINE
        <div class="loading-subtext">Neural networks analyzing asset patterns...</div>
      </div>
    </div>
  {:else if error}
    <div class="error">
      <div class="error-container">
        <div class="error-title" style="color: var(--status-critical);">AI SYSTEM FAILURE</div>
        <div class="error-message">Neural network analysis compromised: {error}</div>
        <button class="retry-button" on:click={fetchAIData}>RESTORE AI SYSTEMS</button>
      </div>
    </div>
  {:else}
    <div class="dashboard-content">
      <div class="metrics-row">
        <div class="metric-card" style="border-color: {aiInsights.total_predicted_assets > 50 ? 'var(--status-critical)' : 'var(--status-warning)'}">
          <div class="metric-ring">
            <div class="icon-circle animate-pulse" style="border-color: var(--accent-cyan); box-shadow: var(--glow-cyan)">
              <Target size={20} color="var(--accent-cyan)" />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: var(--accent-cyan)">PREDICTED MISSING</div>
            <div class="metric-value" style="color: var(--accent-cyan)">{formatNumber(aiInsights.total_predicted_assets || 0)}</div>
            <div class="metric-detail">AI-Discovered Assets</div>
          </div>
          <div class="decorative-bar animate-pulse" style="background: var(--accent-cyan)"></div>
        </div>

        <div class="metric-card" style="border-color: var(--status-critical)">
          <div class="metric-ring">
            <div class="icon-circle animate-blink" style="border-color: var(--status-critical); box-shadow: var(--glow-red)">
              <AlertTriangle size={20} color="var(--status-critical)" />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: var(--status-critical)">CRITICAL VISIBILITY GAPS</div>
            <div class="metric-value" style="color: var(--status-critical)">{formatNumber(aiInsights.critical_visibility_gaps?.length || 0)}</div>
            <div class="metric-detail">High-Risk Predictions</div>
          </div>
          <div class="decorative-bar animate-blink" style="background: var(--status-critical)"></div>
        </div>

        <div class="metric-card" style="border-color: var(--status-improving)">
          <div class="metric-ring">
            <div class="icon-circle" style="border-color: var(--status-improving); box-shadow: var(--glow-blue)">
              <Brain size={20} color="var(--status-improving)" />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: var(--status-improving)">PATTERN FAMILIES</div>
            <div class="metric-value" style="color: var(--status-improving)">{formatNumber(aiInsights.pattern_coverage || 0)}</div>
            <div class="metric-detail">Naming Patterns Detected</div>
          </div>
          <div class="decorative-bar" style="background: var(--status-improving)"></div>
        </div>

        <div class="metric-card" style="border-color: var(--accent-magenta)">
          <div class="metric-ring">
            <div class="icon-circle" style="border-color: var(--accent-magenta); box-shadow: var(--glow-magenta)">
              <Zap size={20} color="var(--accent-magenta)" />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: var(--accent-magenta)">AI ACCURACY</div>
            <div class="metric-value" style="color: var(--accent-magenta)">{aiInsights.avg_existence_probability ? (aiInsights.avg_existence_probability * 100).toFixed(1) : 0}%</div>
            <div class="metric-detail">Neural Network Precision</div>
          </div>
          <div class="decorative-bar" style="background: var(--accent-magenta)"></div>
        </div>
      </div>

      <div class="data-table card">
        <div class="table-header">
          <h2 class="main-header-title">AI-PREDICTED MISSING ASSETS</h2>
          <div style="display: flex; gap: 8px;">
            <button class="retry-button" on:click={trainAIModel} style="padding: 6px 12px; font-size: 0.8rem;">
              <Play size={14} style="margin-right: 4px;" />
              TRAIN
            </button>
            <button class="retry-button" on:click={exportData} style="padding: 6px 12px; font-size: 0.8rem;">
              <Download size={14} style="margin-right: 4px;" />
              EXPORT
            </button>
          </div>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>PREDICTED HOSTNAME</th>
                <th>BUSINESS UNIT</th>
                <th>ASSET ROLE</th>
                <th>AI CONFIDENCE</th>
                <th>RISK SCORE</th>
                <th>PATTERN FAMILY</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {#each filteredMissingAssets.slice(0, 30) as asset}
                <tr 
                  class:selected={selectedAsset === asset}
                  style="background: {asset.visibility_risk_score > 0.8 ? 'rgba(255, 35, 64, 0.1)' : asset.visibility_risk_score > 0.5 ? 'rgba(255, 44, 196, 0.1)' : 'rgba(0, 149, 255, 0.05)'}"
                  on:click={() => handleAssetDrillDown(asset)}
                >
                  <td style="color: var(--text-primary); font-weight: var(--font-weight-bold)">{asset.predicted_hostname}</td>
                  <td style="color: var(--text-secondary)">{asset.business_unit || 'Unknown'}</td>
                  <td style="color: var(--text-secondary)">{asset.predicted_role}</td>
                  <td class="center">
                    <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                      <div class="progress-bar" style="width: 60px;">
                        <div 
                          class="progress-fill" 
                          style="width: {asset.existence_probability * 100}%; background: {getStatusColor(asset.existence_probability * 100)}; box-shadow: {getStatusColor(asset.existence_probability * 100) === 'var(--status-good)' ? 'var(--glow-cyan)' : 'var(--glow-red)'}"
                        ></div>
                      </div>
                      <span style="color: {getStatusColor(asset.existence_probability * 100)}; font-weight: bold; font-size: 0.9rem;">
                        {(asset.existence_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td class="center" style="color: {getRiskColor(asset.visibility_risk_score > 0.8 ? 'HIGH' : 'MEDIUM')}; font-weight: bold">
                    {(asset.visibility_risk_score * 100).toFixed(0)}%
                  </td>
                  <td style="color: var(--text-muted); font-size: 0.8rem">{asset.pattern_family}</td>
                  <td class="center">
                    <button 
                      class="nav-tab" 
                      style="padding: 4px 8px; font-size: 0.7rem; margin: 0;"
                      on:click|stopPropagation={() => handleAssetDrillDown(asset)}
                    >
                      ANALYZE
                    </button>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>

      {#if selectedAsset}
        <div class="card" style="background: rgba(0, 229, 255, 0.05); border: 2px solid var(--accent-cyan); margin-top: 16px;">
          <div class="card-header">
            <h2 class="header-title" style="color: var(--accent-cyan)">DEEP ASSET ANALYSIS: {selectedAsset.predicted_hostname}</h2>
            <button class="retry-button" on:click={() => selectedAsset = null} style="padding: 4px 8px; font-size: 0.8rem;">CLOSE</button>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; margin-top: 16px;">
            <div>
              <h3 style="color: var(--text-primary); margin-bottom: 12px;">Risk Factors</h3>
              {#each calculateRiskFactors(selectedAsset) as factor}
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 8px; background: rgba(0, 0, 0, 0.2); border-radius: 4px;">
                  <span style="color: var(--text-secondary); font-size: 0.9rem;">{factor.factor}</span>
                  <span style="color: {factor.color}; font-weight: bold;">{(factor.weight * 100).toFixed(0)}%</span>
                </div>
              {/each}
            </div>
            <div>
              <h3 style="color: var(--text-primary); margin-bottom: 12px;">Asset Properties</h3>
              <div class="summary-row" style="font-size: 0.9rem;">
                <span>Business Unit:</span>
                <span style="color: var(--accent-cyan)">{selectedAsset.business_unit}</span>
              </div>
              <div class="summary-row" style="font-size: 0.9rem;">
                <span>Asset Role:</span>
                <span style="color: var(--accent-cyan)">{selectedAsset.predicted_role}</span>
              </div>
              <div class="summary-row" style="font-size: 0.9rem;">
                <span>AI Confidence:</span>
                <span style="color: var(--accent-cyan)">{(selectedAsset.existence_probability * 100).toFixed(1)}%</span>
              </div>
            </div>
            <div>
              <h3 style="color: var(--text-primary); margin-bottom: 12px;">Predicted Log Types</h3>
              <div style="display: flex; flex-direction: column; gap: 6px;">
                {#each selectedAsset.predicted_log_types || [] as logType}
                  <div style="background: rgba(0, 229, 255, 0.1); padding: 6px 12px; border-radius: 4px; font-size: 0.9rem;">
                    {logType}
                  </div>
                {/each}
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</main>

<style>
  @import '../styles/dashboard.css';
  
  .dashboard-section {
    width: 100%;
    height: 100%;
  }
</style>

// /src/components/AO1MainDashboard.svelte

<script>
  import { onMount } from 'svelte';
  import AO1OverviewDashboard from './AO1OverviewDashboard.svelte';
  import AO1AIDashboard from './AO1AIDashboard.svelte';
  import AO1RegionalDashboard from './AO1RegionalDashboard.svelte';
  import AO1BusinessDashboard from './AO1BusinessDashboard.svelte';
  import AO1SystemClassificationDashboard from './AO1SystemClassificationDashboard.svelte';
  import { BarChart3, Brain, Globe, Building2, Server, Search } from 'lucide-svelte';
  
  let activeTab = 'overview';
  let searchTerm = '';
  let refreshing = false;
  
  function handleTabChange(tab) {
    activeTab = tab;
  }
  
  async function handleGlobalRefresh() {
    refreshing = true;
    
    const refreshPromises = [];
    
    switch(activeTab) {
      case 'overview':
        refreshPromises.push(overviewComponent?.fetchOverviewData());
        break;
      case 'ai':
        refreshPromises.push(aiComponent?.fetchAIData());
        break;
      case 'regional':
        refreshPromises.push(regionalComponent?.fetchRegionalData());
        break;
      case 'business':
        refreshPromises.push(businessComponent?.fetchBusinessData());
        break;
      case 'systems':
        refreshPromises.push(systemsComponent?.fetchSystemData());
        break;
    }
    
    await Promise.all(refreshPromises);
    refreshing = false;
  }
  
  let overviewComponent;
  let aiComponent;
  let regionalComponent;
  let businessComponent;
  let systemsComponent;
</script>

<main class="dashboard">
  <div class="circuit-overlay"></div>
  
  <div class="dashboard-header">
    <div class="dashboard-title">
      <div class="icon-circle animate-pulse" style="background: linear-gradient(45deg, var(--accent-cyan), var(--accent-blue))">
        <BarChart3 size={20} color="white" />
      </div>
      <h1 class="title-main">AO1 LOG VISIBILITY MEASUREMENT SYSTEM</h1>
    </div>
    <div class="dashboard-controls">
      <div class="search-container">
        <input 
          class="search-input" 
          bind:value={searchTerm}
          placeholder="SEARCH ASSETS..."
        />
      </div>
      <button 
        class="retry-button" 
        on:click={handleGlobalRefresh} 
        disabled={refreshing}
        style="padding: 8px 16px; font-size: 0.9rem;"
      >
        <Search size={16} style="margin-right: 4px;" />
        {refreshing ? 'REFRESHING...' : 'REFRESH'}
      </button>
    </div>
  </div>

  <div class="nav-tabs">
    <div 
      class="nav-tab {activeTab === 'overview' ? 'active' : ''}"
      on:click={() => handleTabChange('overview')}
    >
      <span class="nav-tab-icon"><BarChart3 size={16} /></span>
      OVERVIEW
    </div>
    <div 
      class="nav-tab {activeTab === 'ai' ? 'active' : ''}"
      on:click={() => handleTabChange('ai')}
    >
      <span class="nav-tab-icon"><Brain size={16} /></span>
      AI PREDICTIONS
    </div>
    <div 
      class="nav-tab {activeTab === 'regional' ? 'active' : ''}"
      on:click={() => handleTabChange('regional')}
    >
      <span class="nav-tab-icon"><Globe size={16} /></span>
      REGIONAL
    </div>
    <div 
      class="nav-tab {activeTab === 'business' ? 'active' : ''}"
      on:click={() => handleTabChange('business')}
    >
      <span class="nav-tab-icon"><Building2 size={16} /></span>
      BUSINESS UNITS
    </div>
    <div 
      class="nav-tab {activeTab === 'systems' ? 'active' : ''}"
      on:click={() => handleTabChange('systems')}
    >
      <span class="nav-tab-icon"><Server size={16} /></span>
      SYSTEMS
    </div>
  </div>

  <div class="dashboard-content">
    {#if activeTab === 'overview'}
      <AO1OverviewDashboard bind:this={overviewComponent} {searchTerm} />
    {/if}

    {#if activeTab === 'ai'}
      <AO1AIDashboard bind:this={aiComponent} {searchTerm} />
    {/if}

    {#if activeTab === 'regional'}
      <AO1RegionalDashboard bind:this={regionalComponent} {searchTerm} />
    {/if}

    {#if activeTab === 'business'}
      <AO1BusinessDashboard bind:this={businessComponent} {searchTerm} />
    {/if}

    {#if activeTab === 'systems'}
      <AO1SystemClassificationDashboard bind:this={systemsComponent} {searchTerm} />
    {/if}
  </div>
</main>

<style>
  @import '../styles/dashboard.css';
</style>