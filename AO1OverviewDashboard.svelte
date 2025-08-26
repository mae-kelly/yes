
// ================================================================
// Enhanced AO1OverviewDashboard.svelte with exportable functions
// ================================================================

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
  
  // EXPORTABLE ASYNC FUNCTIONS
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
  
  export function calculateTotalRisk() {
    if (!overallCoverage.total_hosts) return 0;
    const avgCoverage = (
      (overallCoverage.splunk_coverage_pct || 0) +
      (overallCoverage.cmdb_coverage_pct || 0) +
      (overallCoverage.crowdstrike_coverage_pct || 0)
    ) / 3;
    return 100 - avgCoverage;
  }
  
  export function getMetricStatus(metric) {
    if (metric >= 90) return { color: 'var(--status-good)', status: 'EXCELLENT' };
    if (metric >= 75) return { color: 'var(--status-improving)', status: 'GOOD' };
    if (metric >= 50) return { color: 'var(--status-warning)', status: 'NEEDS ATTENTION' };
    return { color: 'var(--status-critical)', status: 'CRITICAL' };
  }
  
  // EXPORTABLE DATA
  export { overallCoverage, domainAnalysis, visibilityFactors, loading, error };
  
  onMount(() => {
    fetchOverviewData();
    refreshInterval = setInterval(fetchOverviewData, 300000);
    
    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  });
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
        <div class="error-title text-critical">VISIBILITY COMPROMISED</div>
        <div class="error-message">Log visibility analysis failed: {error}</div>
        <button class="retry-button" on:click={fetchOverviewData}>RESTORE VISIBILITY</button>
      </div>
    </div>
  {:else}
    <div class="dashboard-content">
      <div class="metrics-row">
        <div class="metric-card border-cyan">
          <div class="metric-ring">
            <div class="icon-circle shadow-glow-cyan" style="border-color: {getStatusColor(overallCoverage.splunk_coverage_pct)}">
              <BarChart3 size={20} color={getStatusColor(overallCoverage.splunk_coverage_pct)} />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: {getStatusColor(overallCoverage.splunk_coverage_pct)}">SPLUNK LOGGING</div>
            <div class="metric-value" style="color: {getStatusColor(overallCoverage.splunk_coverage_pct)}">{formatNumber(overallCoverage.total_splunk_logging)}</div>
            <div class="metric-detail text-secondary">{overallCoverage.splunk_coverage_pct}% of {formatNumber(overallCoverage.total_hosts)} Assets</div>
          </div>
          <div class="decorative-bar" style="background: {getStatusColor(overallCoverage.splunk_coverage_pct)}"></div>
        </div>

        <div class="metric-card border-cyan">
          <div class="metric-ring">
            <div class="icon-circle shadow-glow-cyan" style="border-color: {getStatusColor(overallCoverage.cmdb_coverage_pct)}">
              <Database size={20} color={getStatusColor(overallCoverage.cmdb_coverage_pct)} />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: {getStatusColor(overallCoverage.cmdb_coverage_pct)}">CMDB PRESENT</div>
            <div class="metric-value" style="color: {getStatusColor(overallCoverage.cmdb_coverage_pct)}">{formatNumber(overallCoverage.total_cmdb_present)}</div>
            <div class="metric-detail text-secondary">{overallCoverage.cmdb_coverage_pct}% Asset Visibility</div>
          </div>
          <div class="decorative-bar" style="background: {getStatusColor(overallCoverage.cmdb_coverage_pct)}"></div>
        </div>

        <div class="metric-card border-cyan">
          <div class="metric-ring">
            <div class="icon-circle shadow-glow-cyan" style="border-color: {getStatusColor(overallCoverage.crowdstrike_coverage_pct)}">
              <Shield size={20} color={getStatusColor(overallCoverage.crowdstrike_coverage_pct)} />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: {getStatusColor(overallCoverage.crowdstrike_coverage_pct)}">CROWDSTRIKE AGENT</div>
            <div class="metric-value" style="color: {getStatusColor(overallCoverage.crowdstrike_coverage_pct)}">{formatNumber(overallCoverage.total_crowdstrike)}</div>
            <div class="metric-detail text-secondary">{overallCoverage.crowdstrike_coverage_pct}% Coverage</div>
          </div>
          <div class="decorative-bar" style="background: {getStatusColor(overallCoverage.crowdstrike_coverage_pct)}"></div>
        </div>

        <div class="metric-card border-cyan">
          <div class="metric-ring">
            <div class="icon-circle shadow-glow-cyan" style="border-color: {getStatusColor(overallCoverage.tanium_coverage_pct)}">
              <Settings size={20} color={getStatusColor(overallCoverage.tanium_coverage_pct)} />
            </div>
          </div>
          <div class="metric-content">
            <div class="metric-label" style="color: {getStatusColor(overallCoverage.tanium_coverage_pct)}">TANIUM COVERAGE</div>
            <div class="metric-value" style="color: {getStatusColor(overallCoverage.tanium_coverage_pct)}">{formatNumber(overallCoverage.total_tanium)}</div>
            <div class="metric-detail text-secondary">{overallCoverage.tanium_coverage_pct}% Deployment</div>
          </div>
          <div class="decorative-bar" style="background: {getStatusColor(overallCoverage.tanium_coverage_pct)}"></div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="header-title">DOMAIN VISIBILITY ANALYSIS</h2>
        </div>
        <div class="distribution-stats">
          {#each domainAnalysis as domain}
            <div class="stat-box bg-secondary border-cyan rounded p-4">
              <div class="stat-label text-primary font-weight-bold">{domain.analysis_type.replace(' Analysis', '').toUpperCase()}</div>
              <div class="stat-value text-primary">{formatNumber(domain.total_hosts)}</div>
              <div class="coverage-indicators gap-3">
                <div class="coverage-item">
                  <div class="coverage-header d-flex justify-content-between">
                    <span class="text-secondary">Splunk Logging</span>
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
                  <div class="coverage-header d-flex justify-content-between">
                    <span class="text-secondary">CMDB Present</span>
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