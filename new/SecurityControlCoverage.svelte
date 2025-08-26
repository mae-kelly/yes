<!-- /src/components/SecurityControlCoverage.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;

  async function fetchData() {
    try {
      const response = await fetch('http://localhost:5000/api/security-control-coverage');
      if (!response.ok) throw new Error('Failed to fetch security control data');
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
    <div class="cyber-spinner">
      <div class="spinner-inner"></div>
    </div>
    <div class="loading-text">
      ANALYZING SECURITY CONTROLS
      <div class="loading-subtext">Scanning agent deployment...</div>
    </div>
  </div>
{:else if error}
  <div class="error">
    <div class="error-container">
      <h2 class="error-title">SECURITY CONTROL SCAN FAILED</h2>
      <p class="error-message">{error}</p>
      <button class="retry-button" on:click={fetchData}>RETRY SCAN</button>
    </div>
  </div>
{:else if data.total_hosts}

  <div class="main-header-title" style="margin-bottom: 25px;">
    SECURITY CONTROL COVERAGE - AGENT-BASED PROTECTION
  </div>

  <div class="metrics-row">
    <div class="metric-card" style="border-color: {getThreatLevel(data.coverage.edr.percentage).color};">
      <div class="metric-ring">
        <div class="icon-circle" style="border-color: {getThreatLevel(data.coverage.edr.percentage).color}; box-shadow: 0 0 15px {getThreatLevel(data.coverage.edr.percentage).color};">
          <span style="color: {getThreatLevel(data.coverage.edr.percentage).color}; font-size: 18px;">🛡️</span>
        </div>
      </div>
      <div class="metric-content">
        <div class="metric-label" style="color: {getThreatLevel(data.coverage.edr.percentage).color};">EDR PROTECTION</div>
        <div class="metric-value" style="color: {getThreatLevel(data.coverage.edr.percentage).color};">{data.coverage.edr.percentage}%</div>
        <div class="metric-detail">{formatNumber(data.coverage.edr.count)} assets with CrowdStrike</div>
      </div>
      <div class="decorative-bar" style="background: {getThreatLevel(data.coverage.edr.percentage).color};"></div>
    </div>

    <div class="metric-card" style="border-color: {getThreatLevel(data.coverage.tanium.percentage).color};">
      <div class="metric-ring">
        <div class="icon-circle" style="border-color: {getThreatLevel(data.coverage.tanium.percentage).color}; box-shadow: 0 0 15px {getThreatLevel(data.coverage.tanium.percentage).color};">
          <span style="color: {getThreatLevel(data.coverage.tanium.percentage).color}; font-size: 18px;">⚙️</span>
        </div>
      </div>
      <div class="metric-content">
        <div class="metric-label" style="color: {getThreatLevel(data.coverage.tanium.percentage).color};">TANIUM COVERAGE</div>
        <div class="metric-value" style="color: {getThreatLevel(data.coverage.tanium.percentage).color};">{data.coverage.tanium.percentage}%</div>
        <div class="metric-detail">{formatNumber(data.coverage.tanium.count)} assets with Tanium agent</div>
      </div>
      <div class="decorative-bar" style="background: {getThreatLevel(data.coverage.tanium.percentage).color};"></div>
    </div>
  </div>

  <div class="metrics-row">
    <div class="metric-card" style="border-color: {getThreatLevel(data.coverage.dlp?.percentage || 0).color};">
      <div class="metric-ring">
        <div class="icon-circle" style="border-color: {getThreatLevel(data.coverage.dlp?.percentage || 0).color}; box-shadow: 0 0 15px {getThreatLevel(data.coverage.dlp?.percentage || 0).color};">
          <span style="color: {getThreatLevel(data.coverage.dlp?.percentage || 0).color}; font-size: 18px;">🔒</span>
        </div>
      </div>
      <div class="metric-content">
        <div class="metric-label" style="color: {getThreatLevel(data.coverage.dlp?.percentage || 0).color};">DLP PROTECTION</div>
        <div class="metric-value" style="color: {getThreatLevel(data.coverage.dlp?.percentage || 0).color};">{data.coverage.dlp?.percentage || 0}%</div>
        <div class="metric-detail">{formatNumber(data.coverage.dlp?.count || 0)} assets with DLP agent</div>
      </div>
      <div class="decorative-bar" style="background: {getThreatLevel(data.coverage.dlp?.percentage || 0).color};"></div>
    </div>

    <div class="metric-card" style="border-color: {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color};">
      <div class="metric-ring">
        <div class="icon-circle" style="border-color: {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color}; box-shadow: 0 0 15px {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color};">
          <span style="color: {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color}; font-size: 18px;">🎯</span>
        </div>
      </div>
      <div class="metric-content">
        <div class="metric-label" style="color: {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color};">TRIPLE COVERAGE</div>
        <div class="metric-value" style="color: {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color};">{data.overlaps?.triple_coverage?.percentage || 0}%</div>
        <div class="metric-detail">{formatNumber(data.overlaps?.triple_coverage?.count || 0)} assets fully protected</div>
      </div>
      <div class="decorative-bar" style="background: {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color};"></div>
    </div>
  </div>

  <div class="card" style="margin-top: 30px; padding: 25px;">
    <div class="header-title" style="margin-bottom: 20px;">
      SECURITY CONTROL MATRIX
    </div>
    
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th class="text-left">CONTROL TYPE</th>
            <th class="text-center">COVERAGE COUNT</th>
            <th class="text-center">COVERAGE %</th>
            <th class="text-center">CMDB OVERLAP</th>
            <th class="text-center">SPLUNK OVERLAP</th>
            <th class="text-center">STATUS</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="font-weight-bold">EDR (CrowdStrike)</td>
            <td class="text-center">{formatNumber(data.coverage.edr.count)}</td>
            <td class="text-center font-weight-bold" style="color: {getThreatLevel(data.coverage.edr.percentage).color};">
              {data.coverage.edr.percentage}%
            </td>
            <td class="text-center font-weight-bold" style="color: {getThreatLevel(data.overlaps?.edr_cmdb?.percentage || 0).color};">
              {data.overlaps?.edr_cmdb?.percentage || 0}%
            </td>
            <td class="text-center font-weight-bold" style="color: {getThreatLevel(data.overlaps?.edr_splunk?.percentage || 0).color};">
              {data.overlaps?.edr_splunk?.percentage || 0}%
            </td>
            <td class="text-center font-weight-bold" style="color: {getThreatLevel(data.coverage.edr.percentage).color}; font-size: 10px;">
              {getThreatLevel(data.coverage.edr.percentage).status}
            </td>
          </tr>
          
          <tr>
            <td class="font-weight-bold">Tanium Agent</td>
            <td class="text-center">{formatNumber(data.coverage.tanium.count)}</td>
            <td class="text-center font-weight-bold" style="color: {getThreatLevel(data.coverage.tanium.percentage).color};">
              {data.coverage.tanium.percentage}%
            </td>
            <td class="text-center font-weight-bold" style="color: {getThreatLevel(data.overlaps?.tanium_cmdb?.percentage || 0).color};">
              {data.overlaps?.tanium_cmdb?.percentage || 0}%
            </td>
            <td class="text-center font-weight-bold" style="color: {getThreatLevel(data.overlaps?.tanium_splunk?.percentage || 0).color};">
              {data.overlaps?.tanium_splunk?.percentage || 0}%
            </td>
            <td class="text-center font-weight-bold" style="color: {getThreatLevel(data.coverage.tanium.percentage).color}; font-size: 10px;">
              {getThreatLevel(data.coverage.tanium.percentage).status}
            </td>
          </tr>
          
          <tr>
            <td class="font-weight-bold">DLP Agent</td>
            <td class="text-center">{formatNumber(data.coverage.dlp?.count || 0)}</td>
            <td class="text-center font-weight-bold" style="color: {getThreatLevel(data.coverage.dlp?.percentage || 0).color};">
              {data.coverage.dlp?.percentage || 0}%
            </td>
            <td class="text-center">-</td>
            <td class="text-center">-</td>
            <td class="text-center font-weight-bold" style="color: {getThreatLevel(data.coverage.dlp?.percentage || 0).color}; font-size: 10px;">
              {getThreatLevel(data.coverage.dlp?.percentage || 0).status}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <div class="d-grid grid-cols-2 gap-4" style="margin-top: 30px;">
    <div class="card" style="padding: 25px;">
      <div class="header-title" style="margin-bottom: 20px;">
        TANIUM INTEGRATION ANALYSIS
      </div>
      
      <div class="d-flex flex-column gap-3">
        <div class="coverage-item">
          <div class="coverage-header">
            <span>Tanium + CMDB Coverage</span>
            <span style="color: {getThreatLevel(data.overlaps?.tanium_cmdb?.percentage || 0).color};">
              {data.overlaps?.tanium_cmdb?.percentage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data.overlaps?.tanium_cmdb?.percentage || 0}%; background: {getThreatLevel(data.overlaps?.tanium_cmdb?.percentage || 0).color}; --glow-color: {getThreatLevel(data.overlaps?.tanium_cmdb?.percentage || 0).color};"></div>
          </div>
          <div class="metric-detail">{formatNumber(data.overlaps?.tanium_cmdb?.count || 0)} assets with both</div>
        </div>

        <div class="coverage-item">
          <div class="coverage-header">
            <span>Tanium + Splunk Coverage</span>
            <span style="color: {getThreatLevel(data.overlaps?.tanium_splunk?.percentage || 0).color};">
              {data.overlaps?.tanium_splunk?.percentage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data.overlaps?.tanium_splunk?.percentage || 0}%; background: {getThreatLevel(data.overlaps?.tanium_splunk?.percentage || 0).color}; --glow-color: {getThreatLevel(data.overlaps?.tanium_splunk?.percentage || 0).color};"></div>
          </div>
          <div class="metric-detail">{formatNumber(data.overlaps?.tanium_splunk?.count || 0)} assets with both</div>
        </div>

        <div class="coverage-item">
          <div class="coverage-header">
            <span>Tanium + CrowdStrike</span>
            <span style="color: {getThreatLevel(data.overlaps?.tanium_crowdstrike?.percentage || 0).color};">
              {data.overlaps?.tanium_crowdstrike?.percentage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data.overlaps?.tanium_crowdstrike?.percentage || 0}%; background: {getThreatLevel(data.overlaps?.tanium_crowdstrike?.percentage || 0).color}; --glow-color: {getThreatLevel(data.overlaps?.tanium_crowdstrike?.percentage || 0).color};"></div>
          </div>
          <div class="metric-detail">{formatNumber(data.overlaps?.tanium_crowdstrike?.count || 0)} assets with both</div>
        </div>
      </div>
    </div>

    <div class="card" style="padding: 25px;">
      <div class="header-title" style="margin-bottom: 20px;">
        EDR INTEGRATION ANALYSIS
      </div>
      
      <div class="d-flex flex-column gap-3">
        <div class="coverage-item">
          <div class="coverage-header">
            <span>EDR + CMDB Coverage</span>
            <span style="color: {getThreatLevel(data.overlaps?.edr_cmdb?.percentage || 0).color};">
              {data.overlaps?.edr_cmdb?.percentage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data.overlaps?.edr_cmdb?.percentage || 0}%; background: {getThreatLevel(data.overlaps?.edr_cmdb?.percentage || 0).color}; --glow-color: {getThreatLevel(data.overlaps?.edr_cmdb?.percentage || 0).color};"></div>
          </div>
          <div class="metric-detail">{formatNumber(data.overlaps?.edr_cmdb?.count || 0)} assets with both</div>
        </div>

        <div class="coverage-item">
          <div class="coverage-header">
            <span>EDR + Splunk Coverage</span>
            <span style="color: {getThreatLevel(data.overlaps?.edr_splunk?.percentage || 0).color};">
              {data.overlaps?.edr_splunk?.percentage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data.overlaps?.edr_splunk?.percentage || 0}%; background: {getThreatLevel(data.overlaps?.edr_splunk?.percentage || 0).color}; --glow-color: {getThreatLevel(data.overlaps?.edr_splunk?.percentage || 0).color};"></div>
          </div>
          <div class="metric-detail">{formatNumber(data.overlaps?.edr_splunk?.count || 0)} assets with both</div>
        </div>

        <div class="coverage-item">
          <div class="coverage-header">
            <span>Triple Coverage (All 3)</span>
            <span style="color: {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color};">
              {data.overlaps?.triple_coverage?.percentage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data.overlaps?.triple_coverage?.percentage || 0}%; background: {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color}; --glow-color: {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color};"></div>
          </div>
          <div class="metric-detail">{formatNumber(data.overlaps?.triple_coverage?.count || 0)} fully protected assets</div>
        </div>
      </div>
    </div>
  </div>

  <div class="d-grid grid-cols-4 gap-4" style="margin-top: 30px;">
    <div class="card text-center" style="padding: 20px; border-color: var(--accent-cyan);">
      <div style="font-size: 32px; color: var(--accent-cyan); font-weight: bold; margin-bottom: 8px;">
        {formatNumber(data.total_hosts)}
      </div>
      <div style="color: var(--accent-cyan); font-size: 12px;">
        TOTAL ASSETS
      </div>
    </div>

    <div class="card text-center" style="padding: 20px; border-color: var(--status-good);">
      <div style="font-size: 32px; color: var(--status-good); font-weight: bold; margin-bottom: 8px;">
        {Math.round((data.coverage.edr.percentage + data.coverage.tanium.percentage + (data.coverage.dlp?.percentage || 0)) / 3)}%
      </div>
      <div style="color: var(--status-good); font-size: 12px;">
        AVG CONTROL COVERAGE
      </div>
    </div>

    <div class="card text-center" style="padding: 20px; border-color: var(--status-warning);">
      <div style="font-size: 32px; color: var(--status-warning); font-weight: bold; margin-bottom: 8px;">
        {formatNumber(data.total_hosts - data.overlaps?.triple_coverage?.count || 0)}
      </div>
      <div style="color: var(--status-warning); font-size: 12px;">
        INCOMPLETE COVERAGE
      </div>
    </div>

    <div class="card text-center" style="padding: 20px; border-color: {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color};">
      <div style="font-size: 32px; color: {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color}; font-weight: bold; margin-bottom: 8px;">
        {data.overlaps?.triple_coverage?.percentage || 0}%
      </div>
      <div style="color: {getThreatLevel(data.overlaps?.triple_coverage?.percentage || 0).color}; font-size: 12px;">
        FULL PROTECTION
      </div>
    </div>
  </div>
{/if}