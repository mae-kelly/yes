<!-- /src/components/InfrastructureType.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;
  let selectedInfra = null;
  let viewMode = 'matrix';
  let sortBy = 'total';
  let sortOrder = 'desc';
  let filterTier = 'all';
  let riskSimulation = [];

  async function fetchData() {
    try {
      const response = await fetch('http://localhost:5000/api/infrastructure-type');
      if (!response.ok) throw new Error('ASSET MATRIX CORRUPTED');
      data = await response.json();
      loading = false;
      startRiskSim();
    } catch (err) {
      error = err.message;
      loading = false;
    }
  }

  function startRiskSim() {
    const riskTypes = ['MALWARE', 'BREACH', 'OUTAGE', 'COMPLIANCE'];
    setInterval(() => {
      if (Object.keys(data.infrastructure_matrix || {}).length > 0) {
        const infrastructures = Object.keys(data.infrastructure_matrix);
        const randomInfra = infrastructures[Math.floor(Math.random() * infrastructures.length)];
        
        riskSimulation = [...riskSimulation.slice(-7), {
          infrastructure: randomInfra,
          risk: riskTypes[Math.floor(Math.random() * riskTypes.length)],
          severity: Math.floor(Math.random() * 5) + 1,
          probability: Math.floor(Math.random() * 100),
          timestamp: new Date().toLocaleTimeString()
        }];
      }
    }, 4000);
  }

  onMount(fetchData);

  function getThreatLevel(percentage) {
    if (percentage >= 90) return { color: 'var(--matrix-primary)', status: 'OPTIMAL', tier: 'TIER-1' };
    if (percentage >= 75) return { color: 'var(--neural-cyan)', status: 'PROTECTED', tier: 'TIER-2' };
    if (percentage >= 60) return { color: 'var(--toxic-yellow)', status: 'MONITORED', tier: 'TIER-3' };
    if (percentage >= 40) return { color: 'var(--plasma-magenta)', status: 'VULNERABLE', tier: 'TIER-4' };
    return { color: 'var(--danger-crimson)', status: 'CRITICAL', tier: 'TIER-5' };
  }

  function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  }

  function getSortedInfrastructure() {
    if (!data.infrastructure_matrix) return [];
    
    return Object.entries(data.infrastructure_matrix)
      .map(([type, stats]) => ({
        type,
        ...stats,
        threat: getThreatLevel(stats.coverage_score),
        risk_score: calculateRiskScore(stats)
      }))
      .filter(item => filterTier === 'all' || item.threat.tier === filterTier)
      .sort((a, b) => {
        const aVal = sortBy === 'risk_score' ? a.risk_score : (sortBy === 'total' ? a.total : a[sortBy]?.percentage || 0);
        const bVal = sortBy === 'risk_score' ? b.risk_score : (sortBy === 'total' ? b.total : b[sortBy]?.percentage || 0);
        return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
      });
  }

  function calculateRiskScore(stats) {
    const coverageWeight = 0.4;
    const volumeWeight = 0.3;
    const criticalityWeight = 0.3;
    
    const coverageScore = 100 - stats.coverage_score;
    const volumeScore = Math.min((stats.total / 10000) * 100, 100);
    const criticalityScore = getCriticalityScore(stats.type || '');
    
    return Math.round((coverageScore * coverageWeight) + (volumeScore * volumeWeight) + (criticalityScore * criticalityWeight));
  }

  function getCriticalityScore(type) {
    const critical = ['database', 'domain controller', 'exchange', 'active directory'];
    const high = ['server', 'firewall', 'load balancer', 'router'];
    const medium = ['workstation', 'desktop', 'laptop'];
    const low = ['printer', 'camera', 'phone'];
    
    const typeLower = type.toLowerCase();
    if (critical.some(c => typeLower.includes(c))) return 100;
    if (high.some(h => typeLower.includes(h))) return 75;
    if (medium.some(m => typeLower.includes(m))) return 50;
    if (low.some(l => typeLower.includes(l))) return 25;
    return 60;
  }

  function getTierAnalysis() {
    if (!data.tier_analysis) return [];
    
    return Object.entries(data.tier_analysis).map(([tier, stats]) => ({
      tier: tier.replace('tier_', 'TIER ').replace('_', ' ').toUpperCase(),
      ...stats,
      threat: getThreatLevel(stats.coverage_score)
    }));
  }

  function getCriticalAssets() {
    if (!data.critical_assets) return [];
    
    return Object.entries(data.critical_assets)
      .map(([type, stats]) => ({
        type,
        ...stats,
        threat: getThreatLevel(stats.coverage_score)
      }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 8);
  }
</script>

{#if loading}
  <div class="quantum-loader">
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
  </div>
  <div style="text-align: center; margin-top: 30px; color: var(--matrix-primary); font-size: 18px; letter-spacing: 3px; animation: blink-cursor 1s infinite;">
    SCANNING ASSET MATRIX...
  </div>
{:else if error}
  <div class="dystopia-modal active">
    <h2 style="color: var(--danger-crimson); font-size: 20px; letter-spacing: 2px; margin-bottom: 20px;">
      ASSET MATRIX FAILURE
    </h2>
    <p style="color: var(--text-muted); margin-bottom: 20px;">{error}</p>
    <button class="quantum-btn danger" on:click={fetchData}>
      REINITIALIZE MATRIX
    </button>
  </div>
{:else if Object.keys(data).length > 0}

  <!-- Command Interface -->
  <div class="glitch-field" style="margin-bottom: 30px;">
    <div class="glitch-text" data-text="INFRASTRUCTURE ASSET MATRIX" style="font-size: 22px; font-weight: bold; letter-spacing: 4px; margin-bottom: 15px;">
      INFRASTRUCTURE ASSET MATRIX
    </div>
    
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div style="display: flex; gap: 10px;">
        <button class="quantum-btn {viewMode === 'matrix' ? 'active' : ''}" on:click={() => viewMode = 'matrix'}>MATRIX VIEW</button>
        <button class="quantum-btn {viewMode === 'tiers' ? 'active' : ''}" on:click={() => viewMode = 'tiers'}>TIER ANALYSIS</button>
        <button class="quantum-btn {viewMode === 'risk' ? 'active' : ''}" on:click={() => viewMode = 'risk'}>RISK SIMULATION</button>
        <button class="quantum-btn {viewMode === 'critical' ? 'active' : ''}" on:click={() => viewMode = 'critical'}>CRITICAL ASSETS</button>
      </div>
      
      <div style="display: flex; gap: 10px; align-items: center;">
        <select bind:value={filterTier} style="background: rgba(0, 0, 0, 0.8); border: 1px solid var(--neural-cyan); color: var(--neural-cyan); padding: 6px; font-family: inherit; font-size: 11px;">
          <option value="all">ALL TIERS</option>
          <option value="TIER-1">TIER-1</option>
          <option value="TIER-2">TIER-2</option>
          <option value="TIER-3">TIER-3</option>
          <option value="TIER-4">TIER-4</option>
          <option value="TIER-5">TIER-5</option>
        </select>
        
        <select bind:value={sortBy} style="background: rgba(0, 0, 0, 0.8); border: 1px solid var(--neural-cyan); color: var(--neural-cyan); padding: 6px; font-family: inherit; font-size: 11px;">
          <option value="total">ASSET COUNT</option>
          <option value="coverage_score">COVERAGE</option>
          <option value="risk_score">RISK SCORE</option>
          <option value="splunk">SPLUNK</option>
          <option value="crowdstrike">EDR</option>
        </select>
        
        <button class="quantum-btn" style="padding: 6px 12px;" on:click={() => sortOrder = sortOrder === 'desc' ? 'asc' : 'desc'}>
          {sortOrder === 'desc' ? '↓' : '↑'}
        </button>
      </div>
    </div>
  </div>

  {#if data.deployment_stats}
    <!-- Executive Summary -->
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px;">
      <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: var(--neural-cyan);">
        <div style="font-size: 32px; color: var(--neural-cyan); font-weight: bold; margin-bottom: 8px;">
          {data.deployment_stats.total_types}
        </div>
        <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px;">INFRASTRUCTURE TYPES</div>
        <div style="color: var(--text-muted); font-size: 10px; margin-top: 6px;">CATALOGUED</div>
      </div>

      <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: var(--danger-crimson);">
        <div style="font-size: 32px; color: var(--danger-crimson); font-weight: bold; margin-bottom: 8px;">
          {data.deployment_stats.high_risk_types}
        </div>
        <div style="color: var(--danger-crimson); font-size: 12px; letter-spacing: 2px;">HIGH RISK TYPES</div>
        <div style="color: var(--text-muted); font-size: 10px; margin-top: 6px;">CRITICAL/BREACH</div>
      </div>

      <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: var(--plasma-magenta);">
        <div style="font-size: 32px; color: var(--plasma-magenta); font-weight: bold; margin-bottom: 8px;">
          {data.deployment_stats.coverage_gaps}
        </div>
        <div style="color: var(--plasma-magenta); font-size: 12px; letter-spacing: 2px;">COVERAGE GAPS</div>
        <div style="color: var(--text-muted); font-size: 10px; margin-top: 6px;">&lt;50% COVERAGE</div>
      </div>

      <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: var(--matrix-primary);">
        <div style="font-size: 32px; color: var(--matrix-primary); font-weight: bold; margin-bottom: 8px;">
          {Object.values(data.infrastructure_matrix || {}).reduce((sum, item) => sum + item.total, 0) > 0 ? 
           Math.round(Object.values(data.infrastructure_matrix || {}).reduce((sum, item) => sum + (item.coverage_score * item.total), 0) / 
           Object.values(data.infrastructure_matrix || {}).reduce((sum, item) => sum + item.total, 0)) : 0}%
        </div>
        <div style="color: var(--matrix-primary); font-size: 12px; letter-spacing: 2px;">WEIGHTED AVERAGE</div>
        <div style="color: var(--text-muted); font-size: 10px; margin-top: 6px;">COVERAGE SCORE</div>
      </div>
    </div>
  {/if}

  {#if viewMode === 'matrix'}
    <!-- Infrastructure Matrix Grid -->
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          INFRASTRUCTURE DEPLOYMENT MATRIX
        </h3>
        
        <div style="max-height: 400px; overflow-y: auto;">
          {#each riskSimulation as risk}
            <div 
              style="background: {risk.severity > 3 ? 'rgba(255, 7, 58, 0.1)' : 'rgba(255, 44, 196, 0.1)'}; border-left: 3px solid {risk.severity > 3 ? 'var(--danger-crimson)' : 'var(--plasma-magenta)'}; padding: 12px; margin-bottom: 8px;"
            >
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: var(--neural-cyan); font-size: 13px; font-weight: bold;">
                  {risk.infrastructure.split(' ').slice(0, 2).join(' ').toUpperCase()}
                </span>
                <span style="color: {risk.severity > 3 ? 'var(--danger-crimson)' : 'var(--plasma-magenta)'}; font-size: 11px; font-weight: bold;">
                  {risk.risk}
                </span>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 10px; color: var(--text-muted); margin-bottom: 4px;">
                <span>SEVERITY: {risk.severity}/5</span>
                <span>PROBABILITY: {risk.probability}%</span>
              </div>
              <div style="font-size: 9px; color: var(--text-muted); text-align: right;">
                {risk.timestamp}
              </div>
            </div>
          {/each}
        </div>
      </div>

      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--toxic-yellow); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          VULNERABILITY MATRIX
        </h3>
        
        <div style="display: grid; gap: 15px;">
          {#each getSortedInfrastructure().filter(i => i.coverage_score < 60).slice(0, 6) as vuln}
            <div style="background: rgba(223, 255, 0, 0.05); border: 1px solid var(--toxic-yellow); padding: 12px;">
              <div style="color: var(--toxic-yellow); font-size: 11px; font-weight: bold; margin-bottom: 6px;">
                {vuln.type.split(' ').slice(0, 2).join(' ').toUpperCase()}
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 9px;">
                <div style="color: var(--text-muted);">ASSETS: {formatNumber(vuln.total)}</div>
                <div style="color: var(--danger-crimson);">GAP: {100 - vuln.coverage_score}%</div>
              </div>
              <div style="background: rgba(0, 0, 0, 0.6); height: 2px; margin-top: 6px; border-radius: 1px; overflow: hidden;">
                <div style="background: var(--danger-crimson); height: 100%; width: {100 - vuln.coverage_score}%; transition: all 0.5s;"></div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>

  {:else if viewMode === 'critical'}
    <!-- Critical Assets Analysis -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--danger-crimson); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        MISSION-CRITICAL INFRASTRUCTURE ANALYSIS
      </h3>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px;">
        {#each getCriticalAssets() as asset}
          <div 
            style="background: linear-gradient(135deg, rgba(255, 7, 58, 0.05), rgba(0, 0, 0, 0.9)); border: 2px solid {asset.threat.color}; padding: 20px; transition: all 0.3s;"
            class="neural-link"
          >
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
              <h4 style="color: {asset.threat.color}; font-size: 14px; font-weight: bold; letter-spacing: 1px;">
                {asset.type.toUpperCase()}
              </h4>
              <div style="color: {asset.threat.color}; font-size: 18px; font-weight: bold;">
                {asset.coverage_score}%
              </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 15px;">
              <div style="text-align: center;">
                <div style="color: var(--neural-cyan); font-size: 16px; font-weight: bold;">{formatNumber(asset.total)}</div>
                <div style="color: var(--text-muted); font-size: 9px;">ASSETS</div>
              </div>
              <div style="text-align: center;">
                <div style="color: {asset.threat.color}; font-size: 14px; font-weight: bold;">{asset.threat.status}</div>
                <div style="color: var(--text-muted); font-size: 9px;">STATUS</div>
              </div>
              <div style="text-align: center;">
                <div style="color: {asset.threat.color}; font-size: 14px; font-weight: bold;">{calculateRiskScore(asset)}</div>
                <div style="color: var(--text-muted); font-size: 9px;">RISK</div>
              </div>
            </div>

            <div style="display: grid; gap: 8px;">
              {#each [
                ['SPLUNK LOGS', asset.splunk.percentage],
                ['EDR COVERAGE', asset.crowdstrike.percentage],
                ['CMDB TRACKING', asset.cmdb.percentage],
                ['TANIUM MGMT', asset.tanium.percentage]
              ] as [control, pct]}
                {@const controlThreat = getThreatLevel(pct)}
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px; background: rgba(0, 0, 0, 0.3); border-left: 2px solid {controlThreat.color};">
                  <span style="color: var(--text-muted); font-size: 10px;">{control}</span>
                  <span style="color: {controlThreat.color}; font-size: 11px; font-weight: bold;">{pct}%</span>
                </div>
              {/each}
            </div>

            <div style="margin-top: 15px; padding: 8px; background: rgba(0, 0, 0, 0.4); border: 1px solid {asset.threat.color}; text-align: center;">
              <div style="color: {asset.threat.color}; font-size: 11px; font-weight: bold; letter-spacing: 2px;">
                THREAT LEVEL: {asset.threat.status}
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Selected Infrastructure Details Modal -->
  {#if selectedInfra && data.infrastructure_matrix[selectedInfra]}
    <div class="dystopia-modal active" style="max-width: 800px;">
      <h2 style="color: var(--matrix-primary); font-size: 18px; letter-spacing: 2px; margin-bottom: 20px;">
        INFRASTRUCTURE ANALYSIS: {selectedInfra.toUpperCase()}
      </h2>
      
      {@const infraData = data.infrastructure_matrix[selectedInfra]}
      {@const infraThreat = getThreatLevel(infraData.coverage_score)}
      {@const riskScore = calculateRiskScore({...infraData, type: selectedInfra})}
      
      <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 25px;">
        <div style="text-align: center;">
          <div style="color: var(--neural-cyan); font-size: 20px; font-weight: bold;">{formatNumber(infraData.total)}</div>
          <div style="color: var(--text-muted); font-size: 11px;">TOTAL ASSETS</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {infraThreat.color}; font-size: 20px; font-weight: bold;">{infraData.coverage_score}%</div>
          <div style="color: var(--text-muted); font-size: 11px;">COVERAGE</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {infraThreat.color}; font-size: 16px; font-weight: bold;">{infraThreat.tier}</div>
          <div style="color: var(--text-muted); font-size: 11px;">TIER</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {riskScore > 70 ? 'var(--danger-crimson)' : riskScore > 40 ? 'var(--plasma-magenta)' : 'var(--matrix-primary)'}; font-size: 20px; font-weight: bold;">{riskScore}</div>
          <div style="color: var(--text-muted); font-size: 11px;">RISK SCORE</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {infraThreat.color}; font-size: 14px; font-weight: bold;">{infraThreat.status}</div>
          <div style="color: var(--text-muted); font-size: 11px;">STATUS</div>
        </div>
      </div>
      
      <div style="display: grid; gap: 12px; margin-bottom: 20px;">
        {#each [
          ['SPLUNK LOGGING', infraData.splunk],
          ['CROWDSTRIKE EDR', infraData.crowdstrike],
          ['CMDB PRESENCE', infraData.cmdb],
          ['TANIUM AGENT', infraData.tanium],
          ['DLP PROTECTION', infraData.dlp],
          ['APM MONITORING', infraData.apm]
        ] as [name, stats]}
          {#if stats}
            {@const controlThreat = getThreatLevel(stats.percentage)}
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: rgba(0, 0, 0, 0.4); border-left: 3px solid {controlThreat.color};">
              <div>
                <div style="color: var(--neural-cyan); font-size: 13px; font-weight: bold;">{name}</div>
                <div style="color: var(--text-muted); font-size: 10px;">{formatNumber(stats.count)} of {formatNumber(infraData.total)} assets</div>
              </div>
              <div style="text-align: right;">
                <div style="color: {controlThreat.color}; font-size: 16px; font-weight: bold;">{stats.percentage}%</div>
                <div style="color: {controlThreat.color}; font-size: 9px; letter-spacing: 1px;">{controlThreat.status}</div>
              </div>
            </div>
          {/if}
        {/each}
      </div>

      <div style="background: rgba(0, 0, 0, 0.6); border: 1px solid {infraThreat.color}; padding: 15px; margin-bottom: 20px;">
        <h4 style="color: {infraThreat.color}; font-size: 14px; letter-spacing: 1px; margin-bottom: 10px;">
          SECURITY ASSESSMENT
        </h4>
        <div style="display: grid; gap: 8px; font-size: 12px;">
          <div style="display: flex; justify-content: space-between;">
            <span style="color: var(--text-muted);">Overall Security Posture:</span>
            <span style="color: {infraThreat.color}; font-weight: bold;">{infraThreat.status}</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: var(--text-muted);">Risk Classification:</span>
            <span style="color: {riskScore > 70 ? 'var(--danger-crimson)' : riskScore > 40 ? 'var(--plasma-magenta)' : 'var(--matrix-primary)'}; font-weight: bold;">
              {riskScore > 70 ? 'HIGH RISK' : riskScore > 40 ? 'MEDIUM RISK' : 'LOW RISK'}
            </span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: var(--text-muted);">Recommended Action:</span>
            <span style="color: {infraData.coverage_score < 60 ? 'var(--danger-crimson)' : 'var(--matrix-primary)'}; font-weight: bold;">
              {infraData.coverage_score < 60 ? 'IMMEDIATE ATTENTION' : 'MONITOR'}
            </span>
          </div>
        </div>
      </div>
      
      <button class="quantum-btn" style="width: 100%;" on:click={() => selectedInfra = null}>
        CLOSE ANALYSIS
      </button>
    </div>
  {/if}
{/if}: 500px; overflow-y: auto;">
          <div style="display: grid; gap: 8px;">
            {#each getSortedInfrastructure() as infra}
              <div 
                style="background: linear-gradient(90deg, rgba(0, 0, 0, 0.8), {infra.threat.color}10); border-left: 4px solid {infra.threat.color}; padding: 15px; cursor: pointer; transition: all 0.3s;"
                class="neural-link"
                on:click={() => selectedInfra = selectedInfra === infra.type ? null : infra.type}
              >
                <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 15px; align-items: center;">
                  <div>
                    <div style="color: var(--neural-cyan); font-size: 13px; font-weight: bold; margin-bottom: 4px;">
                      {infra.type.toUpperCase()}
                    </div>
                    <div style="color: var(--text-muted); font-size: 10px;">
                      {formatNumber(infra.total)} ASSETS • {infra.threat.tier}
                    </div>
                  </div>
                  
                  <div style="text-align: center;">
                    <div style="color: {infra.threat.color}; font-size: 14px; font-weight: bold;">{infra.coverage_score}%</div>
                    <div style="color: var(--text-muted); font-size: 9px;">COVERAGE</div>
                  </div>
                  
                  <div style="text-align: center;">
                    <div style="color: {getThreatLevel(infra.splunk.percentage).color}; font-size: 14px; font-weight: bold;">{infra.splunk.percentage}%</div>
                    <div style="color: var(--text-muted); font-size: 9px;">SPLUNK</div>
                  </div>
                  
                  <div style="text-align: center;">
                    <div style="color: {getThreatLevel(infra.crowdstrike.percentage).color}; font-size: 14px; font-weight: bold;">{infra.crowdstrike.percentage}%</div>
                    <div style="color: var(--text-muted); font-size: 9px;">EDR</div>
                  </div>
                  
                  <div style="text-align: center;">
                    <div style="color: {infra.risk_score > 70 ? 'var(--danger-crimson)' : infra.risk_score > 40 ? 'var(--plasma-magenta)' : 'var(--matrix-primary)'}; font-size: 14px; font-weight: bold;">
                      {infra.risk_score}
                    </div>
                    <div style="color: var(--text-muted); font-size: 9px;">RISK</div>
                  </div>
                </div>
                
                <div style="background: rgba(0, 0, 0, 0.4); height: 3px; margin-top: 10px; border-radius: 2px; overflow: hidden;">
                  <div style="background: {infra.threat.color}; height: 100%; width: {infra.coverage_score}%; transition: all 0.5s; box-shadow: 0 0 8px {infra.threat.color};"></div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>

      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--plasma-magenta); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          HIGH-RISK ASSETS
        </h3>
        
        <div style="display: grid; gap: 12px;">
          {#each getSortedInfrastructure().filter(i => i.risk_score > 60).slice(0, 8) as infra}
            <div style="background: rgba(255, 44, 196, 0.05); border: 1px solid var(--plasma-magenta); padding: 12px;">
              <div style="color: var(--plasma-magenta); font-size: 12px; font-weight: bold; margin-bottom: 6px;">
                {infra.type.split(' ').slice(0, 3).join(' ').toUpperCase()}
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 10px; margin-bottom: 6px;">
                <span style="color: var(--text-muted);">ASSETS: {formatNumber(infra.total)}</span>
                <span style="color: var(--danger-crimson); font-weight: bold;">RISK: {infra.risk_score}</span>
              </div>
              <div style="color: var(--text-muted); font-size: 9px;">
                COVERAGE: {infra.coverage_score}% • {infra.threat.status}
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>

  {:else if viewMode === 'tiers'}
    <!-- Tier Analysis -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px;">
      {#each getTierAnalysis() as tier}
        <div class="holo-card-3d" style="padding: 25px; border-color: {tier.threat.color};">
          <h3 style="color: {tier.threat.color}; font-size: 16px; letter-spacing: 2px; margin-bottom: 15px;">
            {tier.tier}
          </h3>
          
          <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
            <div style="text-align: center;">
              <div style="color: var(--neural-cyan); font-size: 24px; font-weight: bold;">{formatNumber(tier.total)}</div>
              <div style="color: var(--text-muted); font-size: 11px;">ASSETS</div>
            </div>
            <div style="text-align: center;">
              <div style="color: {tier.threat.color}; font-size: 24px; font-weight: bold;">{tier.coverage_score}%</div>
              <div style="color: var(--text-muted); font-size: 11px;">COVERAGE</div>
            </div>
          </div>

          <div style="display: grid; gap: 10px;">
            {#each [
              ['SPLUNK', tier.splunk.percentage],
              ['EDR', tier.crowdstrike.percentage],
              ['CMDB', tier.cmdb.percentage],
              ['TANIUM', tier.tanium.percentage]
            ] as [name, pct]}
              {@const ctrlThreat = getThreatLevel(pct)}
              <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px;">
                <span style="color: var(--text-muted);">{name}</span>
                <span style="color: {ctrlThreat.color}; font-weight: bold;">{pct}%</span>
              </div>
            {/each}
          </div>

          <div style="margin-top: 15px; text-align: center;">
            <div style="color: {tier.threat.color}; font-size: 12px; font-weight: bold; letter-spacing: 1px;">
              {tier.threat.status}
            </div>
          </div>
        </div>
      {/each}
    </div>

  {:else if viewMode === 'risk'}
    <!-- Risk Simulation -->
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--danger-crimson); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          LIVE RISK SIMULATION
        </h3>
        
        <div style="max-height