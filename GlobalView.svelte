<!-- /src/components/GlobalView.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = null;
  let loading = true;
  let error = null;
  let selectedRegion = null;
  let selectedMetric = 'coverage_score';
  let realTimeData = [];

  async function fetchData() {
    try {
      const response = await fetch('http://localhost:5000/api/global-view');
      if (!response.ok) throw new Error('NEURAL LINK COMPROMISED');
      data = await response.json();
      loading = false;
      generateRealTimeData();
    } catch (err) {
      error = err.message;
      loading = false;
    }
  }

  function generateRealTimeData() {
    setInterval(() => {
      realTimeData = [...realTimeData.slice(-19), {
        timestamp: new Date().getTime(),
        value: Math.random() * 100,
        threats: Math.floor(Math.random() * 5),
        alerts: Math.floor(Math.random() * 3)
      }];
    }, 2000);
  }

  onMount(fetchData);

  function getThreatLevel(percentage) {
    if (percentage >= 90) return { color: 'var(--matrix-primary)', status: 'OPTIMAL', level: 'SECURE' };
    if (percentage >= 75) return { color: 'var(--neural-cyan)', status: 'GOOD', level: 'ELEVATED' };
    if (percentage >= 50) return { color: 'var(--toxic-yellow)', status: 'WARNING', level: 'HIGH' };
    if (percentage >= 25) return { color: 'var(--plasma-magenta)', status: 'CRITICAL', level: 'CRITICAL' };
    return { color: 'var(--danger-crimson)', status: 'BREACH', level: 'BREACH' };
  }

  function getRegionalData() {
    if (!data?.regional_breakdown) return [];
    return Object.entries(data.regional_breakdown)
      .map(([region, stats]) => ({
        region,
        ...stats,
        threat: getThreatLevel(stats.coverage_score)
      }))
      .sort((a, b) => b.total - a.total);
  }

  function getCriticalGaps() {
    if (!data?.critical_gaps) return [];
    return data.critical_gaps
      .filter(gap => gap.splunk_gap < 60 || gap.cmdb_gap < 60)
      .slice(0, 8);
  }

  function formatNumber(num) {
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
  <div style="text-align: center; margin-top: 30px; color: var(--matrix-primary); font-size: 18px; letter-spacing: 3px; animation: blink-cursor 1s infinite;">
    INITIALIZING NEURAL MATRIX...
  </div>
{:else if error}
  <div class="dystopia-modal active">
    <h2 style="color: var(--danger-crimson); font-size: 20px; letter-spacing: 2px; margin-bottom: 20px;">
      SYSTEM BREACH DETECTED
    </h2>
    <p style="color: var(--text-muted); margin-bottom: 20px;">{error}</p>
    <button class="quantum-btn danger" on:click={fetchData}>
      REINITIALIZE CONNECTION
    </button>
  </div>
{:else if data}
  <!-- CISO Executive Dashboard -->
  <div class="glitch-field" style="margin-bottom: 30px;">
    <div class="glitch-text" data-text="EXECUTIVE THREAT OVERVIEW" style="font-size: 22px; font-weight: bold; letter-spacing: 4px; margin-bottom: 20px;">
      EXECUTIVE THREAT OVERVIEW
    </div>
  </div>

  <!-- Critical Metrics Grid -->
  <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px;">
    <div class="holo-card-3d" style="padding: 25px; text-align: center; border-color: {getThreatLevel(data.matrix_overview.coverage_score).color};">
      <div style="font-size: 36px; color: {getThreatLevel(data.matrix_overview.coverage_score).color}; font-weight: bold; margin-bottom: 10px;">
        {data.matrix_overview.coverage_score}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 14px; letter-spacing: 2px;">OVERALL SECURITY MATRIX</div>
      <div style="color: {getThreatLevel(data.matrix_overview.coverage_score).color}; font-size: 12px; margin-top: 8px; letter-spacing: 1px;">
        {getThreatLevel(data.matrix_overview.coverage_score).status}
      </div>
      <div class="data-viz-container" style="margin-top: 15px; height: 40px;">
        <div class="data-wave"></div>
      </div>
    </div>

    <div class="holo-card-3d" style="padding: 25px; text-align: center; border-color: {getThreatLevel(data.matrix_overview.splunk.percentage).color};">
      <div style="font-size: 36px; color: {getThreatLevel(data.matrix_overview.splunk.percentage).color}; font-weight: bold; margin-bottom: 10px;">
        {data.matrix_overview.splunk.percentage}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 14px; letter-spacing: 2px;">SPLUNK NEURAL GRID</div>
      <div style="color: var(--text-muted); font-size: 11px; margin-top: 8px;">
        {formatNumber(data.matrix_overview.splunk.count)} / {formatNumber(data.matrix_overview.total)} ASSETS
      </div>
    </div>

    <div class="holo-card-3d" style="padding: 25px; text-align: center; border-color: {getThreatLevel(data.matrix_overview.crowdstrike.percentage).color};">
      <div style="font-size: 36px; color: {getThreatLevel(data.matrix_overview.crowdstrike.percentage).color}; font-weight: bold; margin-bottom: 10px;">
        {data.matrix_overview.crowdstrike.percentage}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 14px; letter-spacing: 2px;">CROWDSTRIKE DEFENSE</div>
      <div style="color: var(--text-muted); font-size: 11px; margin-top: 8px;">
        {formatNumber(data.matrix_overview.crowdstrike.count)} ENDPOINTS SECURED
      </div>
    </div>

    <div class="holo-card-3d" style="padding: 25px; text-align: center; border-color: {getThreatLevel(data.matrix_overview.cmdb.percentage).color};">
      <div style="font-size: 36px; color: {getThreatLevel(data.matrix_overview.cmdb.percentage).color}; font-weight: bold; margin-bottom: 10px;">
        {data.matrix_overview.cmdb.percentage}%
      </div>
      <div style="color: var(--neural-cyan); font-size: 14px; letter-spacing: 2px;">ASSET INVENTORY</div>
      <div style="color: var(--text-muted); font-size: 11px; margin-top: 8px;">
        {formatNumber(data.matrix_overview.cmdb.count)} CATALOGUED
      </div>
    </div>
  </div>

  <!-- Advanced Analytics Grid -->
  <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 20px; margin-bottom: 30px;">
    
    <!-- Regional Threat Matrix -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
        <span>🌐</span> REGIONAL THREAT MATRIX
      </h3>
      
      <div style="display: grid; gap: 15px;">
        {#each getRegionalData() as region}
          <div 
            class="neural-link" 
            style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: rgba(0, 0, 0, 0.6); border-left: 3px solid {region.threat.color}; transition: all 0.3s; cursor: pointer;"
            on:click={() => selectedRegion = selectedRegion === region.region ? null : region.region}
          >
            <div>
              <div style="color: var(--neural-cyan); font-size: 14px; font-weight: bold;">{region.region}</div>
              <div style="color: var(--text-muted); font-size: 11px; margin-top: 2px;">{formatNumber(region.total)} Assets</div>
            </div>
            <div style="text-align: right;">
              <div style="color: {region.threat.color}; font-size: 16px; font-weight: bold;">{region.coverage_score}%</div>
              <div style="color: {region.threat.color}; font-size: 10px; letter-spacing: 1px;">{region.threat.level}</div>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Real-time Neural Activity -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        ⚡ LIVE NEURAL ACTIVITY
      </h3>
      
      <div style="height: 200px; position: relative; overflow: hidden;">
        <svg width="100%" height="100%" style="position: absolute;">
          {#each realTimeData as point, i}
            {#if i > 0}
              <line 
                x1="{(i-1) * (100 / 20)}%" 
                y1="{100 - realTimeData[i-1].value}%" 
                x2="{i * (100 / 20)}%" 
                y2="{100 - point.value}%" 
                stroke="var(--matrix-primary)" 
                stroke-width="2"
                opacity="{i / realTimeData.length}"
              />
            {/if}
          {/each}
        </svg>
        
        <div style="position: absolute; bottom: 10px; left: 10px; right: 10px; display: flex; justify-content: space-between; font-size: 10px; color: var(--text-muted);">
          <div>THREATS: {realTimeData[realTimeData.length - 1]?.threats || 0}</div>
          <div>ALERTS: {realTimeData[realTimeData.length - 1]?.alerts || 0}</div>
        </div>
      </div>
    </div>

    <!-- Critical Security Gaps -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--danger-crimson); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        ⚠️ CRITICAL GAPS
      </h3>
      
      <div style="display: grid; gap: 10px; max-height: 200px; overflow-y: auto;">
        {#each getCriticalGaps() as gap}
          <div style="background: rgba(255, 7, 58, 0.1); border: 1px solid var(--danger-crimson); padding: 10px; border-radius: 4px;">
            <div style="color: var(--danger-crimson); font-size: 12px; font-weight: bold; margin-bottom: 4px;">
              {gap.region}
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 10px; color: var(--text-muted);">
              <span>SPLUNK: {gap.splunk_gap}%</span>
              <span>CMDB: {gap.cmdb_gap}%</span>
            </div>
          </div>
        {/each}
      </div>
    </div>
  </div>

  <!-- Infrastructure Breakdown Matrix -->
  <div style="display: grid; grid-template-columns: 3fr 2fr; gap: 20px; margin-bottom: 30px;">
    
    <!-- Infrastructure Heat Map -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        🔬 INFRASTRUCTURE HEAT MAP
      </h3>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; max-height: 300px; overflow-y: auto;">
        {#each Object.entries(data.infrastructure_breakdown || {}).slice(0, 12) as [type, stats]}
          {@const threat = getThreatLevel(stats.coverage_score)}
          <div 
            class="neural-link"
            style="background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), {threat.color}15); border: 1px solid {threat.color}; padding: 15px; text-align: center; transition: all 0.3s; cursor: pointer;"
            on:click={() => selectedMetric = selectedMetric === type ? null : type}
          >
            <div style="color: {threat.color}; font-size: 18px; font-weight: bold; margin-bottom: 8px;">
              {stats.coverage_score}%
            </div>
            <div style="color: var(--neural-cyan); font-size: 11px; letter-spacing: 1px; margin-bottom: 4px;">
              {type.split(' ').slice(0, 2).join(' ').toUpperCase()}
            </div>
            <div style="color: var(--text-muted); font-size: 9px;">
              {formatNumber(stats.total)} ASSETS
            </div>
            <div style="background: {threat.color}; height: 2px; margin-top: 8px; width: {stats.coverage_score}%; transition: all 0.3s;"></div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Security Control Matrix -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        🛡️ SECURITY MATRIX
      </h3>
      
      <div style="display: grid; gap: 12px;">
        {#each [
          ['SPLUNK', data.matrix_overview.splunk],
          ['CROWDSTRIKE', data.matrix_overview.crowdstrike],
          ['TANIUM', data.matrix_overview.tanium],
          ['DLP', data.matrix_overview.dlp],
          ['CMDB', data.matrix_overview.cmdb]
        ] as [name, stats]}
          {@const threat = getThreatLevel(stats.percentage)}
          <div style="background: rgba(0, 0, 0, 0.4); border-left: 3px solid {threat.color}; padding: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 1px;">{name}</span>
              <span style="color: {threat.color}; font-size: 14px; font-weight: bold;">{stats.percentage}%</span>
            </div>
            <div style="background: rgba(0, 0, 0, 0.6); height: 4px; border-radius: 2px; overflow: hidden;">
              <div style="background: {threat.color}; height: 100%; width: {stats.percentage}%; transition: all 0.5s; box-shadow: 0 0 10px {threat.color};"></div>
            </div>
            <div style="color: var(--text-muted); font-size: 10px; margin-top: 4px;">
              {formatNumber(stats.count)} / {formatNumber(data.matrix_overview.total)} COVERED
            </div>
          </div>
        {/each}
      </div>
    </div>
  </div>

  <!-- Country Intelligence Grid -->
  <div class="holo-card-3d" style="padding: 25px; margin-bottom: 30px;">
    <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
      <span>🌍 GLOBAL INTELLIGENCE GRID</span>
      <select 
        bind:value={selectedMetric} 
        style="background: rgba(0, 0, 0, 0.8); border: 1px solid var(--neural-cyan); color: var(--neural-cyan); padding: 6px; font-family: inherit; font-size: 11px;"
      >
        <option value="coverage_score">OVERALL COVERAGE</option>
        <option value="splunk">SPLUNK COVERAGE</option>
        <option value="crowdstrike">EDR COVERAGE</option>
        <option value="cmdb">CMDB COVERAGE</option>
      </select>
    </h3>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; max-height: 250px; overflow-y: auto;">
      {#each Object.entries(data.country_analysis || {}).slice(0, 20) as [country, stats]}
        {@const metricValue = selectedMetric === 'coverage_score' ? stats.coverage_score : stats[selectedMetric]?.percentage || 0}
        {@const threat = getThreatLevel(metricValue)}
        <div 
          style="background: linear-gradient(135deg, rgba(0, 0, 0, 0.7), {threat.color}10); border: 1px solid {threat.color}40; padding: 12px; transition: all 0.3s;"
          class="neural-link"
        >
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="color: var(--neural-cyan); font-size: 11px; font-weight: bold;">{country.toUpperCase()}</span>
            <span style="color: {threat.color}; font-size: 13px; font-weight: bold;">{metricValue}%</span>
          </div>
          <div style="color: var(--text-muted); font-size: 9px; margin-bottom: 6px;">
            {formatNumber(stats.total)} ASSETS
          </div>
          <div style="background: rgba(0, 0, 0, 0.6); height: 3px; border-radius: 2px; overflow: hidden;">
            <div style="background: {threat.color}; height: 100%; width: {metricValue}%; transition: all 0.5s; box-shadow: 0 0 8px {threat.color};"></div>
          </div>
        </div>
      {/each}
    </div>
  </div>

  <!-- Data Center Operations Grid -->
  <div class="holo-card-3d" style="padding: 25px;">
    <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
      🏢 DATA CENTER OPERATIONS MATRIX
    </h3>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px;">
      {#each Object.entries(data.datacenter_grid || {}).slice(0, 15) as [dc, stats]}
        {@const threat = getThreatLevel(stats.coverage_score)}
        <div 
          style="background: radial-gradient(ellipse at center, {threat.color}05, rgba(0, 0, 0, 0.8)); border: 1px solid {threat.color}60; padding: 15px; text-align: center; transition: all 0.3s;"
          class="neural-link"
        >
          <div style="color: {threat.color}; font-size: 16px; font-weight: bold; margin-bottom: 8px;">
            {stats.coverage_score}%
          </div>
          <div style="color: var(--neural-cyan); font-size: 10px; letter-spacing: 1px; margin-bottom: 4px; word-break: break-all;">
            {dc.toUpperCase()}
          </div>
          <div style="color: var(--text-muted); font-size: 9px; margin-bottom: 8px;">
            {formatNumber(stats.total)} SYSTEMS
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 8px;">
            <div style="color: {getThreatLevel(stats.splunk.percentage).color};">SPL: {stats.splunk.percentage}%</div>
            <div style="color: {getThreatLevel(stats.crowdstrike.percentage).color};">EDR: {stats.crowdstrike.percentage}%</div>
          </div>
        </div>
      {/each}
    </div>
  </div>

  {#if selectedRegion && data.regional_breakdown[selectedRegion]}
    <div class="dystopia-modal active" style="max-width: 600px;">
      <h2 style="color: var(--matrix-primary); font-size: 18px; letter-spacing: 2px; margin-bottom: 20px;">
        REGIONAL ANALYSIS: {selectedRegion.toUpperCase()}
      </h2>
      
      {@const regionData = data.regional_breakdown[selectedRegion]}
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 20px;">
        <div style="text-align: center;">
          <div style="color: var(--neural-cyan); font-size: 24px; font-weight: bold;">{formatNumber(regionData.total)}</div>
          <div style="color: var(--text-muted); font-size: 12px;">TOTAL ASSETS</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {getThreatLevel(regionData.coverage_score).color}; font-size: 24px; font-weight: bold;">{regionData.coverage_score}%</div>
          <div style="color: var(--text-muted); font-size: 12px;">COVERAGE SCORE</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {getThreatLevel(regionData.coverage_score).color}; font-size: 14px; font-weight: bold; letter-spacing: 2px;">{getThreatLevel(regionData.coverage_score).level}</div>
          <div style="color: var(--text-muted); font-size: 12px;">THREAT LEVEL</div>
        </div>
      </div>
      
      <div style="display: grid; gap: 10px;">
        {#each [
          ['SPLUNK LOGGING', regionData.splunk],
          ['CROWDSTRIKE EDR', regionData.crowdstrike],
          ['CMDB PRESENCE', regionData.cmdb],
          ['TANIUM AGENT', regionData.tanium]
        ] as [name, stats]}
          {@const threat = getThreatLevel(stats.percentage)}
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: rgba(0, 0, 0, 0.4); border-left: 2px solid {threat.color};">
            <span style="color: var(--neural-cyan); font-size: 12px;">{name}</span>
            <span style="color: {threat.color}; font-size: 12px; font-weight: bold;">{stats.percentage}% ({formatNumber(stats.count)})</span>
          </div>
        {/each}
      </div>
      
      <button class="quantum-btn" style="margin-top: 20px; width: 100%;" on:click={() => selectedRegion = null}>
        CLOSE ANALYSIS
      </button>
    </div>
  {/if}
{/if}