<!-- /src/components/DomainVisibility.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;

  async function fetchData() {
    try {
      const response = await fetch('http://localhost:5000/api/domain-visibility');
      if (!response.ok) throw new Error('Failed to fetch domain visibility data');
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
      ANALYZING DOMAIN VISIBILITY
      <div class="loading-subtext">Scanning domain coverage...</div>
    </div>
  </div>
{:else if error}
  <div class="error">
    <div class="error-container">
      <h2 class="error-title">DOMAIN SCAN FAILED</h2>
      <p class="error-message">{error}</p>
      <button class="retry-button" on:click={fetchData}>RETRY SCAN</button>
    </div>
  </div>
{:else if data}

  <div class="main-header-title" style="margin-bottom: 25px;">
    DOMAIN VISIBILITY ANALYSIS - 1DC & FEAD COVERAGE
  </div>

  <div class="d-grid grid-cols-2 gap-4" style="margin-bottom: 30px;">
    <div class="card" style="padding: 25px; border-color: var(--accent-cyan);">
      <div class="header-title" style="color: var(--accent-cyan); margin-bottom: 20px;">
        1DC DOMAIN COVERAGE
      </div>
      
      <div class="text-center" style="margin-bottom: 20px;">
        <div style="font-size: 48px; color: var(--accent-cyan); font-weight: bold;">
          {formatNumber(data['1dc']?.total || 0)}
        </div>
        <div class="text-secondary">Total 1DC Assets</div>
      </div>

      <div class="d-flex flex-column gap-3">
        <div class="coverage-item">
          <div class="coverage-header">
            <span>Splunk Logging</span>
            <span style="color: {getThreatLevel(data['1dc']?.splunk_coverage || 0).color};">
              {data['1dc']?.splunk_coverage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data['1dc']?.splunk_coverage || 0}%; background: {getThreatLevel(data['1dc']?.splunk_coverage || 0).color}; --glow-color: {getThreatLevel(data['1dc']?.splunk_coverage || 0).color};"></div>
          </div>
        </div>

        <div class="coverage-item">
          <div class="coverage-header">
            <span>CMDB Documentation</span>
            <span style="color: {getThreatLevel(data['1dc']?.cmdb_coverage || 0).color};">
              {data['1dc']?.cmdb_coverage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data['1dc']?.cmdb_coverage || 0}%; background: {getThreatLevel(data['1dc']?.cmdb_coverage || 0).color}; --glow-color: {getThreatLevel(data['1dc']?.cmdb_coverage || 0).color};"></div>
          </div>
        </div>

        <div class="coverage-item">
          <div class="coverage-header">
            <span>EDR Protection</span>
            <span style="color: {getThreatLevel(data['1dc']?.edr_coverage || 0).color};">
              {data['1dc']?.edr_coverage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data['1dc']?.edr_coverage || 0}%; background: {getThreatLevel(data['1dc']?.edr_coverage || 0).color}; --glow-color: {getThreatLevel(data['1dc']?.edr_coverage || 0).color};"></div>
          </div>
        </div>

        <div class="coverage-item">
          <div class="coverage-header">
            <span>Tanium Coverage</span>
            <span style="color: {getThreatLevel(data['1dc']?.tanium_coverage || 0).color};">
              {data['1dc']?.tanium_coverage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data['1dc']?.tanium_coverage || 0}%; background: {getThreatLevel(data['1dc']?.tanium_coverage || 0).color}; --glow-color: {getThreatLevel(data['1dc']?.tanium_coverage || 0).color};"></div>
          </div>
        </div>
      </div>

      <div class="card text-center" style="margin-top: 20px; padding: 15px; background: rgba(0, 0, 0, 0.6);">
        <div style="color: {getThreatLevel(data['1dc']?.overall_coverage || 0).color}; font-size: 18px; font-weight: bold;">
          OVERALL: {data['1dc']?.overall_coverage || 0}%
        </div>
        <div style="color: {getThreatLevel(data['1dc']?.overall_coverage || 0).color}; font-size: 12px;">
          {getThreatLevel(data['1dc']?.overall_coverage || 0).status}
        </div>
      </div>
    </div>

    <div class="card" style="padding: 25px; border-color: var(--accent-magenta);">
      <div class="header-title" style="color: var(--accent-magenta); margin-bottom: 20px;">
        FEAD DOMAIN COVERAGE
      </div>
      
      <div class="text-center" style="margin-bottom: 20px;">
        <div style="font-size: 48px; color: var(--accent-magenta); font-weight: bold;">
          {formatNumber(data.fead?.total || 0)}
        </div>
        <div class="text-secondary">Total FEAD Assets</div>
      </div>

      <div class="d-flex flex-column gap-3">
        <div class="coverage-item">
          <div class="coverage-header">
            <span>Splunk Logging</span>
            <span style="color: {getThreatLevel(data.fead?.splunk_coverage || 0).color};">
              {data.fead?.splunk_coverage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data.fead?.splunk_coverage || 0}%; background: {getThreatLevel(data.fead?.splunk_coverage || 0).color}; --glow-color: {getThreatLevel(data.fead?.splunk_coverage || 0).color};"></div>
          </div>
        </div>

        <div class="coverage-item">
          <div class="coverage-header">
            <span>CMDB Documentation</span>
            <span style="color: {getThreatLevel(data.fead?.cmdb_coverage || 0).color};">
              {data.fead?.cmdb_coverage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data.fead?.cmdb_coverage || 0}%; background: {getThreatLevel(data.fead?.cmdb_coverage || 0).color}; --glow-color: {getThreatLevel(data.fead?.cmdb_coverage || 0).color};"></div>
          </div>
        </div>

        <div class="coverage-item">
          <div class="coverage-header">
            <span>EDR Protection</span>
            <span style="color: {getThreatLevel(data.fead?.edr_coverage || 0).color};">
              {data.fead?.edr_coverage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data.fead?.edr_coverage || 0}%; background: {getThreatLevel(data.fead?.edr_coverage || 0).color}; --glow-color: {getThreatLevel(data.fead?.edr_coverage || 0).color};"></div>
          </div>
        </div>

        <div class="coverage-item">
          <div class="coverage-header">
            <span>Tanium Coverage</span>
            <span style="color: {getThreatLevel(data.fead?.tanium_coverage || 0).color};">
              {data.fead?.tanium_coverage || 0}%
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {data.fead?.tanium_coverage || 0}%; background: {getThreatLevel(data.fead?.tanium_coverage || 0).color}; --glow-color: {getThreatLevel(data.fead?.tanium_coverage || 0).color};"></div>
          </div>
        </div>
      </div>

      <div class="card text-center" style="margin-top: 20px; padding: 15px; background: rgba(0, 0, 0, 0.6);">
        <div style="color: {getThreatLevel(data.fead?.overall_coverage || 0).color}; font-size: 18px; font-weight: bold;">
          OVERALL: {data.fead?.overall_coverage || 0}%
        </div>
        <div style="color: {getThreatLevel(data.fead?.overall_coverage || 0).color}; font-size: 12px;">
          {getThreatLevel(data.fead?.overall_coverage || 0).status}
        </div>
      </div>
    </div>
  </div>

  <div class="card" style="padding: 25px;">
    <div class="header-title" style="margin-bottom: 20px;">
      DOMAIN COMPARISON MATRIX
    </div>
    
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th class="text-left">DOMAIN</th>
            <th class="text-center">TOTAL ASSETS</th>
            <th class="text-center">SPLUNK %</th>
            <th class="text-center">CMDB %</th>
            <th class="text-center">EDR %</th>
            <th class="text-center">TANIUM %</th>
            <th class="text-center">OVERALL %</th>
            <th class="text-center">STATUS</th>
          </tr>
        </thead>
        <tbody>
          {#each [['1DC', data['1dc']], ['FEAD', data.fead]] as [domain, stats]}
            {#if stats}
              {@const overallThreat = getThreatLevel(stats.overall_coverage)}
              <tr>
                <td class="font-weight-bold" style="color: var(--text-primary);">
                  {domain}
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
                <td class="text-center font-weight-bold" style="color: {getThreatLevel(stats.tanium_coverage).color};">
                  {stats.tanium_coverage}%
                </td>
                <td class="text-center font-weight-bold" style="color: {overallThreat.color};">
                  {stats.overall_coverage}%
                </td>
                <td class="text-center font-weight-bold" style="color: {overallThreat.color}; font-size: 10px;">
                  {overallThreat.status}
                </td>
              </tr>
            {/if}
          {/each}
        </tbody>
      </table>
    </div>
  </div>

  {#if data.all_domains && data.all_domains.length > 0}
    <div class="card" style="margin-top: 20px; padding: 25px;">
      <div class="header-title" style="margin-bottom: 20px;">
        TOP DOMAINS BY ASSET COUNT
      </div>
      
      <div class="d-grid grid-cols-4 gap-3">
        {#each data.all_domains.slice(0, 12) as [domain, count]}
          <div class="card text-center" style="padding: 15px; border-color: var(--text-muted);">
            <div style="font-size: 18px; color: var(--text-primary); font-weight: bold; margin-bottom: 5px;">
              {formatNumber(count)}
            </div>
            <div style="font-size: 10px; color: var(--text-secondary); word-break: break-all;">
              {domain.length > 20 ? domain.substring(0, 20) + '...' : domain}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
{/if}