<!-- /src/components/GlobalView.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = null;
  let loading = true;
  let error = null;

  async function fetchData() {
    try {
      const response = await fetch('http://localhost:5000/api/global-view');
      if (!response.ok) throw new Error('Failed to fetch global view data');
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
</script>

{#if loading}
  <div class="quantum-loader">
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
  </div>
  <div style="text-align: center; margin-top: 30px; color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px;">
    INITIALIZING GLOBAL VIEW...
  </div>
{:else if error}
  <div class="dystopia-modal active">
    <h2 style="color: var(--danger-crimson);">SYSTEM ERROR</h2>
    <p style="color: var(--text-muted);">{error}</p>
    <button class="quantum-btn danger" on:click={fetchData}>RETRY</button>
  </div>
{:else if data}
  <!-- AO1 Requirement: Global View - CSOC able to view x% of all assets globally -->
  <div class="glitch-text" data-text="GLOBAL ASSET VISIBILITY OVERVIEW" style="font-size: 20px; font-weight: bold; letter-spacing: 3px; margin-bottom: 25px;">
    GLOBAL ASSET VISIBILITY OVERVIEW
  </div>

  <!-- Executive Summary Metrics -->
  <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px;">
    <div class="holo-card-3d" style="padding: 25px; text-align: center; border-color: {getThreatLevel(data.global_summary?.splunk_coverage || 0).color};">
      <div style="font-size: 42px; color: {getThreatLevel(data.global_summary?.splunk_coverage || 0).color}; font-weight: bold; margin-bottom: 10px; text-shadow: 0 0 20px {getThreatLevel(data.global_summary?.splunk_coverage || 0).color};">
        {data.global_summary?.splunk_coverage || 0}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 14px; letter-spacing: 2px; margin-bottom: 8px;">
        GLOBAL SPLUNK VISIBILITY
      </div>
      <div style="color: var(--text-muted); font-size: 12px;">
        {formatNumber(data.global_summary?.total_assets * (data.global_summary?.splunk_coverage || 0) / 100)} of {formatNumber(data.global_summary?.total_assets || 0)} assets
      </div>
      <div style="color: {getThreatLevel(data.global_summary?.splunk_coverage || 0).color}; font-size: 11px; margin-top: 8px; letter-spacing: 1px;">
        {getThreatLevel(data.global_summary?.splunk_coverage || 0).status}
      </div>
    </div>

    <div class="holo-card-3d" style="padding: 25px; text-align: center; border-color: {getThreatLevel(data.global_summary?.cmdb_coverage || 0).color};">
      <div style="font-size: 42px; color: {getThreatLevel(data.global_summary?.cmdb_coverage || 0).color}; font-weight: bold; margin-bottom: 10px; text-shadow: 0 0 20px {getThreatLevel(data.global_summary?.cmdb_coverage || 0).color};">
        {data.global_summary?.cmdb_coverage || 0}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 14px; letter-spacing: 2px; margin-bottom: 8px;">
        GLOBAL CMDB COVERAGE
      </div>
      <div style="color: var(--text-muted); font-size: 12px;">
        {formatNumber(data.global_summary?.total_assets * (data.global_summary?.cmdb_coverage || 0) / 100)} assets documented
      </div>
      <div style="color: {getThreatLevel(data.global_summary?.cmdb_coverage || 0).color}; font-size: 11px; margin-top: 8px; letter-spacing: 1px;">
        {getThreatLevel(data.global_summary?.cmdb_coverage || 0).status}
      </div>
    </div>

    <div class="holo-card-3d" style="padding: 25px; text-align: center; border-color: {getThreatLevel(data.global_summary?.edr_coverage || 0).color};">
      <div style="font-size: 42px; color: {getThreatLevel(data.global_summary?.edr_coverage || 0).color}; font-weight: bold; margin-bottom: 10px; text-shadow: 0 0 20px {getThreatLevel(data.global_summary?.edr_coverage || 0).color};">
        {data.global_summary?.edr_coverage || 0}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 14px; letter-spacing: 2px; margin-bottom: 8px;">
        GLOBAL EDR PROTECTION
      </div>
      <div style="color: var(--text-muted); font-size: 12px;">
        {formatNumber(data.global_summary?.total_assets * (data.global_summary?.edr_coverage || 0) / 100)} endpoints secured
      </div>
      <div style="color: {getThreatLevel(data.global_summary?.edr_coverage || 0).color}; font-size: 11px; margin-top: 8px; letter-spacing: 1px;">
        {getThreatLevel(data.global_summary?.edr_coverage || 0).status}
      </div>
    </div>

    <div class="holo-card-3d" style="padding: 25px; text-align: center; border-color: {getThreatLevel(data.global_summary?.overall_visibility || 0).color};">
      <div style="font-size: 42px; color: {getThreatLevel(data.global_summary?.overall_visibility || 0).color}; font-weight: bold; margin-bottom: 10px; text-shadow: 0 0 20px {getThreatLevel(data.global_summary?.overall_visibility || 0).color};">
        {data.global_summary?.overall_visibility || 0}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 14px; letter-spacing: 2px; margin-bottom: 8px;">
        COMPOSITE VISIBILITY
      </div>
      <div style="color: var(--text-muted); font-size: 12px;">
        Combined coverage score
      </div>
      <div style="color: {getThreatLevel(data.global_summary?.overall_visibility || 0).color}; font-size: 11px; margin-top: 8px; letter-spacing: 1px;">
        {getThreatLevel(data.global_summary?.overall_visibility || 0).status}
      </div>
    </div>
  </div>

  <!-- AO1 Requirement: Infrastructure Type - % of visibility by host and log type across infrastructure types -->
  <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 30px;">
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        INFRASTRUCTURE TYPE VISIBILITY BREAKDOWN
      </h3>
      
      <div style="max-height: 400px; overflow-y: auto;">
        <table style="width: 100%; border-collapse: collapse;">
          <thead>
            <tr style="border-bottom: 1px solid var(--matrix-primary);">
              <th style="text-align: left; padding: 10px; color: var(--neural-cyan); font-size: 12px;">INFRASTRUCTURE TYPE</th>
              <th style="text-align: center; padding: 10px; color: var(--neural-cyan); font-size: 12px;">ASSETS</th>
              <th style="text-align: center; padding: 10px; color: var(--neural-cyan); font-size: 12px;">SPLUNK</th>
              <th style="text-align: center; padding: 10px; color: var(--neural-cyan); font-size: 12px;">CMDB</th>
              <th style="text-align: center; padding: 10px; color: var(--neural-cyan); font-size: 12px;">EDR</th>
              <th style="text-align: center; padding: 10px; color: var(--neural-cyan); font-size: 12px;">OVERALL</th>
            </tr>
          </thead>
          <tbody>
            {#each Object.entries(data.infrastructure_breakdown || {}).sort((a, b) => b[1].total - a[1].total) as [type, stats]}
              {@const overallThreat = getThreatLevel(stats.overall_coverage)}
              <tr style="border-bottom: 1px solid rgba(0, 255, 65, 0.1); transition: all 0.3s;" class="neural-link">
                <td style="padding: 12px; color: var(--matrix-primary); font-size: 11px; font-weight: bold;">
                  {type.toUpperCase()}
                </td>
                <td style="padding: 12px; text-align: center; color: var(--neural-cyan); font-size: 11px;">
                  {formatNumber(stats.total)}
                </td>
                <td style="padding: 12px; text-align: center; color: {getThreatLevel(stats.splunk_coverage).color}; font-size: 11px; font-weight: bold;">
                  {stats.splunk_coverage}%
                </td>
                <td style="padding: 12px; text-align: center; color: {getThreatLevel(stats.cmdb_coverage).color}; font-size: 11px; font-weight: bold;">
                  {stats.cmdb_coverage}%
                </td>
                <td style="padding: 12px; text-align: center; color: {getThreatLevel(stats.edr_coverage).color}; font-size: 11px; font-weight: bold;">
                  {stats.edr_coverage}%
                </td>
                <td style="padding: 12px; text-align: center; color: {overallThreat.color}; font-size: 12px; font-weight: bold;">
                  {stats.overall_coverage}%
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Infrastructure Coverage Chart -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        TOP INFRASTRUCTURE COVERAGE
      </h3>
      
      <div style="height: 350px; display: flex; flex-direction: column; justify-content: flex-end; gap: 8px;">
        {#each Object.entries(data.infrastructure_breakdown || {}).sort((a, b) => b[1].total - a[1].total).slice(0, 10) as [type, stats]}
          {@const threat = getThreatLevel(stats.overall_coverage)}
          <div style="display: flex; align-items: center; gap: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
              <span style="color: var(--text-muted); font-size: 11px;">EDR Coverage:</span>
              <span style="color: {getThreatLevel(stats.edr_coverage).color}; font-size: 12px; font-weight: bold;">
                {stats.edr_coverage}%
              </span>
            </div>
            <div style="background: rgba(0, 0, 0, 0.6); height: 4px; border-radius: 2px; overflow: hidden;">
              <div style="background: {getThreatLevel(stats.edr_coverage).color}; height: 100%; width: {stats.edr_coverage}%; transition: all 0.8s; box-shadow: 0 0 8px {getThreatLevel(stats.edr_coverage).color};"></div>
            </div>
          </div>

          <div style="margin-top: 15px; padding: 10px; background: rgba(0, 0, 0, 0.4); border: 1px solid {regionThreat.color}; text-align: center;">
            <div style="color: {regionThreat.color}; font-size: 12px; font-weight: bold; letter-spacing: 1px;">
              REGION STATUS: {regionThreat.status}
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>

  <!-- Critical Coverage Gaps Analysis -->
  <div class="holo-card-3d" style="padding: 25px;">
    <h3 style="color: var(--danger-crimson); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
      CRITICAL VISIBILITY GAPS
    </h3>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
      {#each Object.entries(data.infrastructure_breakdown || {}).filter(([_, stats]) => stats.overall_coverage < 60).sort((a, b) => a[1].overall_coverage - b[1].overall_coverage).slice(0, 6) as [type, stats]}
        <div style="background: rgba(255, 7, 58, 0.1); border: 2px solid var(--danger-crimson); padding: 15px; border-radius: 6px;">
          <div style="color: var(--danger-crimson); font-size: 13px; font-weight: bold; margin-bottom: 8px;">
            {type.toUpperCase()}
          </div>
          <div style="color: var(--text-muted); font-size: 11px; margin-bottom: 10px;">
            {formatNumber(stats.total)} assets with {stats.overall_coverage}% coverage
          </div>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 10px;">
            <div style="text-align: center;">
              <div style="color: {getThreatLevel(stats.splunk_coverage).color}; font-weight: bold;">{stats.splunk_coverage}%</div>
              <div style="color: var(--text-muted);">SPL</div>
            </div>
            <div style="text-align: center;">
              <div style="color: {getThreatLevel(stats.cmdb_coverage).color}; font-weight: bold;">{stats.cmdb_coverage}%</div>
              <div style="color: var(--text-muted);">CMDB</div>
            </div>
            <div style="text-align: center;">
              <div style="color: {getThreatLevel(stats.edr_coverage).color}; font-weight: bold;">{stats.edr_coverage}%</div>
              <div style="color: var(--text-muted);">EDR</div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}width: 120px; color: var(--neural-cyan); font-size: 10px; text-align: right;">
              {type.split(' ').slice(0, 2).join(' ').toUpperCase()}
            </div>
            <div style="flex: 1; height: 20px; background: rgba(0, 0, 0, 0.6); border-radius: 10px; overflow: hidden; position: relative;">
              <div style="height: 100%; width: {stats.overall_coverage}%; background: linear-gradient(90deg, {threat.color}, {threat.color}80); transition: all 1s ease; box-shadow: 0 0 15px {threat.color};"></div>
            </div>
            <div style="width: 60px; text-align: left; color: {threat.color}; font-size: 11px; font-weight: bold;">
              {stats.overall_coverage}%
            </div>
          </div>
        {/each}
      </div>
    </div>
  </div>

  <!-- AO1 Requirement: Regional and Country View - %of visibility by location -->
  <div class="holo-card-3d" style="padding: 25px; margin-bottom: 30px;">
    <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
      REGIONAL VISIBILITY BREAKDOWN
    </h3>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
      {#each Object.entries(data.regional_breakdown || {}).sort((a, b) => b[1].total - a[1].total) as [region, stats]}
        {@const regionThreat = getThreatLevel(stats.overall_coverage)}
        <div style="background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), {regionThreat.color}15); border: 2px solid {regionThreat.color}; padding: 20px; border-radius: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h4 style="color: var(--neural-cyan); font-size: 14px; font-weight: bold; letter-spacing: 1px;">
              {region.toUpperCase()}
            </h4>
            <div style="color: {regionThreat.color}; font-size: 18px; font-weight: bold;">
              {stats.overall_coverage}%
            </div>
          </div>

          <div style="color: var(--text-muted); font-size: 12px; margin-bottom: 15px;">
            Total Assets: {formatNumber(stats.total)}
          </div>

          <div style="display: grid; gap: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="color: var(--text-muted); font-size: 11px;">Splunk Logging:</span>
              <span style="color: {getThreatLevel(stats.splunk_coverage).color}; font-size: 12px; font-weight: bold;">
                {stats.splunk_coverage}%
              </span>
            </div>
            <div style="background: rgba(0, 0, 0, 0.6); height: 4px; border-radius: 2px; overflow: hidden;">
              <div style="background: {getThreatLevel(stats.splunk_coverage).color}; height: 100%; width: {stats.splunk_coverage}%; transition: all 0.8s; box-shadow: 0 0 8px {getThreatLevel(stats.splunk_coverage).color};"></div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
              <span style="color: var(--text-muted); font-size: 11px;">CMDB Presence:</span>
              <span style="color: {getThreatLevel(stats.cmdb_coverage).color}; font-size: 12px; font-weight: bold;">
                {stats.cmdb_coverage}%
              </span>
            </div>
            <div style="background: rgba(0, 0, 0, 0.6); height: 4px; border-radius: 2px; overflow: hidden;">
              <div style="background: {getThreatLevel(stats.cmdb_coverage).color}; height: 100%; width: {stats.cmdb_coverage}%; transition: all 0.8s; box-shadow: 0 0 8px {getThreatLevel(stats.cmdb_coverage).color};"></div>
            </div>

            <div style="