<!-- /src/components/GlobalView.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = null;
  let loading = true;
  let error = null;
  let selectedRegion = null;
  let heatmapView = 'risk_score';

  async function fetchData() {
    try {
      const response = await fetch('http://localhost:5000/api/global-view');
      if (!response.ok) throw new Error('Neural matrix compromised');
      data = await response.json();
      loading = false;
    } catch (err) {
      error = err.message;
      loading = false;
    }
  }

  onMount(fetchData);

  function getThreatColor(score) {
    if (score >= 90) return 'var(--matrix-primary)';
    if (score >= 75) return 'var(--neural-cyan)';
    if (score >= 50) return 'var(--toxic-yellow)';
    if (score >= 25) return 'var(--plasma-magenta)';
    return 'var(--danger-crimson)';
  }

  function formatAssets(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  }
</script>

{#if loading}
  <div class="quantum-loader">
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
  </div>
{:else if error}
  <div class="dystopia-modal active">
    <h2 style="color: var(--danger-crimson);">SYSTEM BREACH</h2>
    <p>{error}</p>
    <button class="quantum-btn danger" on:click={fetchData}>RECONNECT</button>
  </div>
{:else if data}
  <!-- Global Visibility Overview -->
  <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px;">
    <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: {getThreatColor(data.executive_summary.visibility_score)};">
      <div style="font-size: 36px; color: {getThreatColor(data.executive_summary.visibility_score)}; font-weight: bold;">
        {data.executive_summary.visibility_score}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px;">GLOBAL VISIBILITY</div>
      <div style="color: var(--text-muted); font-size: 10px;">{formatAssets(data.executive_summary.total_assets)} assets</div>
    </div>

    <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: {getThreatColor(data.executive_summary.security_posture)};">
      <div style="font-size: 36px; color: {getThreatColor(data.executive_summary.security_posture)}; font-weight: bold;">
        {data.executive_summary.security_posture}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px;">SECURITY POSTURE</div>
      <div style="color: var(--text-muted); font-size: 10px;">protection rate</div>
    </div>

    <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: var(--matrix-primary);">
      <div style="font-size: 36px; color: var(--matrix-primary); font-weight: bold;">
        {formatAssets(data.executive_summary.triple_coverage)}
      </div>
      <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px;">FULL COVERAGE</div>
      <div style="color: var(--text-muted); font-size: 10px;">complete protection</div>
    </div>

    <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: var(--danger-crimson);">
      <div style="font-size: 36px; color: var(--danger-crimson); font-weight: bold;">
        {formatAssets(data.executive_summary.blind_spots)}
      </div>
      <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px;">BLIND SPOTS</div>
      <div style="color: var(--text-muted); font-size: 10px;">zero coverage</div>
    </div>
  </div>

  <!-- Infrastructure Coverage Matrix by Host/Log Type -->
  <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px;">
    <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: {getThreatColor(data.coverage_breakdown.splunk.percentage)};">
      <div style="font-size: 28px; color: {getThreatColor(data.coverage_breakdown.splunk.percentage)}; font-weight: bold;">
        {data.coverage_breakdown.splunk.percentage}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 11px; letter-spacing: 1px;">SPLUNK LOGGING</div>
      <div style="color: var(--text-muted); font-size: 9px;">{formatAssets(data.coverage_breakdown.splunk.count)} hosts</div>
    </div>

    <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: {getThreatColor(data.coverage_breakdown.edr.percentage)};">
      <div style="font-size: 28px; color: {getThreatColor(data.coverage_breakdown.edr.percentage)}; font-weight: bold;">
        {data.coverage_breakdown.edr.percentage}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 11px; letter-spacing: 1px;">EDR COVERAGE</div>
      <div style="color: var(--text-muted); font-size: 9px;">{formatAssets(data.coverage_breakdown.edr.count)} endpoints</div>
    </div>

    <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: {getThreatColor(data.coverage_breakdown.tanium.percentage)};">
      <div style="font-size: 28px; color: {getThreatColor(data.coverage_breakdown.tanium.percentage)}; font-weight: bold;">
        {data.coverage_breakdown.tanium.percentage}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 11px; letter-spacing: 1px;">TANIUM AGENTS</div>
      <div style="color: var(--text-muted); font-size: 9px;">{formatAssets(data.coverage_breakdown.tanium.count)} managed</div>
    </div>

    <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: {getThreatColor(data.coverage_breakdown.cmdb.percentage)};">
      <div style="font-size: 28px; color: {getThreatColor(data.coverage_breakdown.cmdb.percentage)}; font-weight: bold;">
        {data.coverage_breakdown.cmdb.percentage}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 11px; letter-spacing: 1px;">CMDB TRACKED</div>
      <div style="color: var(--text-muted); font-size: 9px;">{formatAssets(data.coverage_breakdown.cmdb.count)} documented</div>
    </div>
  </div>

  <!-- Infrastructure Risk Heatmap -->
  <div class="holo-card-3d" style="padding: 25px; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px;">INFRASTRUCTURE THREAT HEATMAP</h3>
      <select bind:value={heatmapView} style="background: rgba(0,0,0,0.8); border: 1px solid var(--neural-cyan); color: var(--neural-cyan); padding: 6px;">
        <option value="risk_score">Risk Exposure</option>
        <option value="splunk_coverage">Splunk Coverage</option>
        <option value="edr_coverage">EDR Protection</option>
        <option value="quality_score">Data Quality</option>
      </select>
    </div>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; max-height: 300px; overflow-y: auto;">
      {#each data.infrastructure_heatmap.slice(0, 40) as cell}
        {@const value = cell[heatmapView] || 0}
        {@const intensity = heatmapView === 'risk_score' ? value / 100 : (100 - value) / 100}
        <div 
          style="
            background: linear-gradient(135deg, rgba(0,0,0,0.8), {getThreatColor(heatmapView === 'risk_score' ? 100-value : value)}{Math.floor(intensity * 30).toString(16).padStart(2, '0')});
            border: 1px solid {getThreatColor(heatmapView === 'risk_score' ? 100-value : value)};
            padding: 10px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
          "
          class="neural-link"
        >
          <div style="color: {getThreatColor(heatmapView === 'risk_score' ? 100-value : value)}; font-size: 14px; font-weight: bold;">
            {value.toFixed(1)}{heatmapView.includes('coverage') || heatmapView === 'quality_score' ? '%' : ''}
          </div>
          <div style="color: var(--neural-cyan); font-size: 9px; margin: 3px 0;">{cell.infrastructure.split(' ').slice(0,2).join(' ')}</div>
          <div style="color: var(--text-muted); font-size: 8px;">{cell.region}</div>
          <div style="color: var(--text-muted); font-size: 8px;">{formatAssets(cell.asset_count)} assets</div>
        </div>
      {/each}
    </div>
  </div>

  <!-- Discovery Timeline Analytics -->
  <div class="holo-card-3d" style="padding: 25px; margin-bottom: 20px;">
    <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
      ASSET DISCOVERY TIMELINE
    </h3>
    
    <div style="height: 150px; position: relative; background: rgba(0,0,0,0.6); border: 1px solid var(--matrix-primary);">
      <svg width="100%" height="100%">
        {#each data.discovery_timeline as point, i}
          {@const x = (point.hour / 23) * 100}
          {@const y = 100 - ((point.discoveries / Math.max(...data.discovery_timeline.map(p => p.discoveries))) * 80)}
          <rect x="{x - 1}%" y="{y}%" width="2%" height="{100 - y}%" fill="var(--matrix-primary)" opacity="0.7"/>
          <circle cx="{x}%" cy="{y}%" r="2" fill="var(--neural-cyan)"/>
        {/each}
      </svg>
    </div>
    
    <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin-top: 15px; font-size: 10px;">
      <div style="text-align: center; color: var(--neural-cyan);">
        PEAK: {Math.max(...data.discovery_timeline.map(p => p.discoveries))} discoveries
      </div>
      <div style="text-align: center; color: var(--text-muted);">
        AVG QUALITY: {(data.discovery_timeline.reduce((sum, p) => sum + p.quality_score, 0) / data.discovery_timeline.length).toFixed(1)}
      </div>
      <div style="text-align: center; color: var(--matrix-primary);">
        TOTAL DISCOVERIES: {data.discovery_timeline.reduce((sum, p) => sum + p.discoveries, 0)}
      </div>
    </div>
  </div>

  <!-- Business Risk Analysis -->
  <div class="holo-card-3d" style="padding: 25px;">
    <h3 style="color: var(--plasma-magenta); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
      BUSINESS UNIT RISK MATRIX
    </h3>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; max-height: 300px; overflow-y: auto;">
      {#each data.business_risk_analysis.slice(0, 12) as unit}
        <div style="background: rgba(255, 44, 196, 0.05); border: 1px solid {getThreatColor(100 - unit.risk_score)}; padding: 15px;">
          <div style="color: var(--neural-cyan); font-size: 13px; font-weight: bold; margin-bottom: 8px;">
            {unit.business_unit}
          </div>
          
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px; font-size: 11px;">
            <div style="color: var(--text-muted);">Assets: {formatAssets(unit.asset_count)}</div>
            <div style="color: {getThreatColor(100 - unit.risk_score)};">Risk: {unit.risk_score.toFixed(1)}</div>
            <div style="color: {getThreatColor(unit.logging_coverage)};">Log: {unit.logging_coverage}%</div>
            <div style="color: {getThreatColor(unit.security_coverage)};">Sec: {unit.security_coverage}%</div>
          </div>
          
          <div style="color: var(--text-muted); font-size: 10px; margin-bottom: 8px;">
            {unit.geographic_footprint} countries • {unit.infrastructure_complexity} infra types
          </div>
          
          <div style="background: rgba(0,0,0,0.6); height: 3px; border-radius: 2px;">
            <div style="background: {getThreatColor(100 - unit.risk_score)}; height: 100%; width: {100 - unit.risk_score}%; transition: all 0.5s;"></div>
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}