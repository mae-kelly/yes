<!-- /src/components/SecurityControlCoverage.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = null;
  let loading = true;
  let error = null;
  let selectedAgent = null;
  let selectedOverlap = null;
  let viewMode = 'overview';
  let threatSimulation = [];
  let attackVectors = [];

  async function fetchData() {
    try {
      const response = await fetch('http://localhost:5000/api/security-control-coverage');
      if (!response.ok) throw new Error('DEFENSE GRID COMPROMISED');
      data = await response.json();
      loading = false;
      initializeThreatSim();
    } catch (err) {
      error = err.message;
      loading = false;
    }
  }

  function initializeThreatSim() {
    const threats = ['MALWARE', 'APT', 'INSIDER', 'PHISHING', 'RANSOMWARE', 'DDoS'];
    const vectors = ['EMAIL', 'WEB', 'USB', 'NETWORK', 'SOCIAL', 'SUPPLY_CHAIN'];
    
    setInterval(() => {
      threatSimulation = [...threatSimulation.slice(-9), {
        id: Date.now(),
        type: threats[Math.floor(Math.random() * threats.length)],
        severity: Math.floor(Math.random() * 5) + 1,
        blocked: Math.random() > 0.3,
        timestamp: new Date().toLocaleTimeString()
      }];
      
      if (Math.random() > 0.7) {
        attackVectors = [...attackVectors.slice(-4), {
          vector: vectors[Math.floor(Math.random() * vectors.length)],
          attempts: Math.floor(Math.random() * 100),
          blocked: Math.floor(Math.random() * 80)
        }];
      }
    }, 3000);
  }

  onMount(fetchData);

  function getThreatLevel(percentage) {
    if (percentage >= 95) return { color: 'var(--matrix-primary)', status: 'FORTRESS', level: 'MAXIMUM' };
    if (percentage >= 85) return { color: 'var(--neural-cyan)', status: 'PROTECTED', level: 'HIGH' };
    if (percentage >= 70) return { color: 'var(--toxic-yellow)', status: 'DEFENDED', level: 'MEDIUM' };
    if (percentage >= 50) return { color: 'var(--plasma-magenta)', status: 'VULNERABLE', level: 'LOW' };
    return { color: 'var(--danger-crimson)', status: 'EXPOSED', level: 'CRITICAL' };
  }

  function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  }

  function getAgentDeploymentData() {
    if (!data?.agent_deployment) return [];
    return Object.entries(data.agent_deployment)
      .map(([agent, stats]) => ({
        agent: agent.replace(/_/g, ' ').toUpperCase(),
        ...stats,
        threat: getThreatLevel(stats.coverage_score)
      }))
      .sort((a, b) => b.total - a.total);
  }

  function getSecurityGaps() {
    if (!data?.security_gaps) return [];
    return data.security_gaps
      .filter(gap => gap.risk_level === 'high')
      .slice(0, 10);
  }
</script>

{#if loading}
  <div class="quantum-loader">
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
  </div>
  <div style="text-align: center; margin-top: 30px; color: var(--matrix-primary); font-size: 18px; letter-spacing: 3px; animation: blink-cursor 1s infinite;">
    INITIALIZING DEFENSE MATRIX...
  </div>
{:else if error}
  <div class="dystopia-modal active">
    <h2 style="color: var(--danger-crimson); font-size: 20px; letter-spacing: 2px; margin-bottom: 20px;">
      DEFENSE GRID FAILURE
    </h2>
    <p style="color: var(--text-muted); margin-bottom: 20px;">{error}</p>
    <button class="quantum-btn danger" on:click={fetchData}>
      RESTORE DEFENSES
    </button>
  </div>
{:else if data}

  <!-- Command Center Header -->
  <div class="glitch-field" style="margin-bottom: 30px;">
    <div class="glitch-text" data-text="CYBERSECURITY DEFENSE MATRIX" style="font-size: 22px; font-weight: bold; letter-spacing: 4px; margin-bottom: 15px;">
      CYBERSECURITY DEFENSE MATRIX
    </div>
    <div style="display: flex; gap: 15px;">
      <button class="quantum-btn {viewMode === 'overview' ? 'active' : ''}" on:click={() => viewMode = 'overview'}>
        OVERVIEW
      </button>
      <button class="quantum-btn {viewMode === 'agents' ? 'active' : ''}" on:click={() => viewMode = 'agents'}>
        AGENT DEPLOYMENT
      </button>
      <button class="quantum-btn {viewMode === 'threats' ? 'active' : ''}" on:click={() => viewMode = 'threats'}>
        THREAT SIMULATION
      </button>
      <button class="quantum-btn {viewMode === 'gaps' ? 'active' : ''}" on:click={() => viewMode = 'gaps'}>
        SECURITY GAPS
      </button>
    </div>
  </div>

  {#if viewMode === 'overview'}
    <!-- Executive Security Dashboard -->
    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; margin-bottom: 30px;">
      {#each [
        ['OVERALL SECURITY', data.control_matrix.coverage_score, 'COMPOSITE'],
        ['EDR COVERAGE', data.control_matrix.crowdstrike.percentage, 'ENDPOINT'],
        ['TANIUM AGENTS', data.control_matrix.tanium.percentage, 'SYSTEM'],
        ['DLP PROTECTION', data.control_matrix.dlp.percentage, 'DATA'],
        ['APM MONITORING', data.control_matrix.apm.percentage, 'APPLICATION']
      ] as [label, value, type]}
        {@const threat = getThreatLevel(value)}
        <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: {threat.color};">
          <div style="font-size: 32px; color: {threat.color}; font-weight: bold; margin-bottom: 10px;">
            {value}%
          </div>
          <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px; margin-bottom: 8px;">
            {label}
          </div>
          <div style="color: {threat.color}; font-size: 10px; letter-spacing: 1px; margin-bottom: 10px;">
            {threat.status}
          </div>
          <div style="color: var(--text-muted); font-size: 9px;">
            {type} LAYER
          </div>
          <div class="data-viz-container" style="margin-top: 12px; height: 30px;">
            <div class="data-wave" style="background: linear-gradient(0deg, {threat.color}30, transparent);"></div>
          </div>
        </div>
      {/each}
    </div>

    <!-- Coverage Overlap Analysis -->
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 30px;">
      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          DEFENSE LAYER OVERLAPS
        </h3>
        
        <div style="display: grid; gap: 15px;">
          {#each [
            ['FULL STACK PROTECTION', data.coverage_overlaps.full_stack, 'ALL CONTROLS'],
            ['TRIPLE COVERAGE', data.coverage_overlaps.triple_coverage, 'LOG + CMDB + EDR'],
            ['EDR + LOGGING', data.coverage_overlaps.dual_edr_logging, 'ENDPOINT + LOGS'],
            ['TANIUM + LOGGING', data.coverage_overlaps.dual_tanium_logging, 'AGENT + LOGS'],
            ['NO COVERAGE', data.coverage_overlaps.no_coverage, 'ZERO PROTECTION']
          ] as [name, count, description]}
            {@const percentage = (count / data.deployment_metrics.total_controlled) * 100}
            {@const threat = name === 'NO COVERAGE' ? {color: 'var(--danger-crimson)', status: 'CRITICAL'} : getThreatLevel(percentage)}
            <div 
              style="background: rgba(0, 0, 0, 0.4); border-left: 3px solid {threat.color}; padding: 15px; cursor: pointer; transition: all 0.3s;"
              class="neural-link"
              on:click={() => selectedOverlap = selectedOverlap === name ? null : name}
            >
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: var(--neural-cyan); font-size: 13px; font-weight: bold;">{name}</span>
                <span style="color: {threat.color}; font-size: 15px; font-weight: bold;">{formatNumber(count)}</span>
              </div>
              <div style="color: var(--text-muted); font-size: 11px; margin-bottom: 8px;">
                {description} • {percentage.toFixed(1)}% OF ASSETS
              </div>
              <div style="background: rgba(0, 0, 0, 0.6); height: 4px; border-radius: 2px; overflow: hidden;">
                <div style="background: {threat.color}; height: 100%; width: {percentage}%; transition: all 0.5s; box-shadow: 0 0 10px {threat.color};"></div>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          DEPLOYMENT METRICS
        </h3>
        
        <div style="display: grid; gap: 20px;">
          <div style="text-align: center;">
            <div style="color: var(--neural-cyan); font-size: 28px; font-weight: bold; margin-bottom: 5px;">
              {formatNumber(data.deployment_metrics.total_controlled)}
            </div>
            <div style="color: var(--text-muted); font-size: 12px; letter-spacing: 1px;">
              CONTROLLED ASSETS
            </div>
          </div>
          
          <div style="text-align: center;">
            {@const securityThreat = getThreatLevel(data.deployment_metrics.security_score)}
            <div style="color: {securityThreat.color}; font-size: 28px; font-weight: bold; margin-bottom: 5px;">
              {data.deployment_metrics.security_score}%
            </div>
            <div style="color: var(--text-muted); font-size: 12px; letter-spacing: 1px;">
              SECURITY SCORE
            </div>
            <div style="color: {securityThreat.color}; font-size: 10px; letter-spacing: 2px; margin-top: 5px;">
              {securityThreat.status}
            </div>
          </div>

          <div style="text-align: center;">
            <div style="color: {data.deployment_metrics.threat_level === 'optimal' ? 'var(--matrix-primary)' : 'var(--danger-crimson)'}; font-size: 16px; font-weight: bold; letter-spacing: 2px; margin-bottom: 5px;">
              {data.deployment_metrics.threat_level.toUpperCase()}
            </div>
            <div style="color: var(--text-muted); font-size: 12px; letter-spacing: 1px;">
              THREAT LEVEL
            </div>
          </div>
        </div>
      </div>
    </div>

  {:else if viewMode === 'agents'}
    <!-- Agent Deployment Matrix -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px;">
      {#each getAgentDeploymentData() as agent}
        <div 
          class="holo-card-3d"
          style="padding: 25px; border-color: {agent.threat.color}; cursor: pointer; transition: all 0.3s;"
          on:click={() => selectedAgent = selectedAgent === agent.agent ? null : agent.agent}
        >
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h3 style="color: var(--neural-cyan); font-size: 14px; letter-spacing: 1px;">{agent.agent}</h3>
            <div style="color: {agent.threat.color}; font-size: 20px; font-weight: bold;">
              {agent.coverage_score}%
            </div>
          </div>
          
          <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 15px;">
            <div style="text-align: center;">
              <div style="color: var(--neural-cyan); font-size: 18px; font-weight: bold;">{formatNumber(agent.total)}</div>
              <div style="color: var(--text-muted); font-size: 10px;">TOTAL ASSETS</div>
            </div>
            <div style="text-align: center;">
              <div style="color: {agent.threat.color}; font-size: 18px; font-weight: bold;">{agent.threat.level}</div>
              <div style="color: var(--text-muted); font-size: 10px;">PROTECTION</div>
            </div>
          </div>

          <div style="display: grid; gap: 8px;">
            {#each [
              ['SPLUNK', agent.splunk.percentage],
              ['CMDB', agent.cmdb.percentage],
              ['EDR', agent.crowdstrike.percentage]
            ] as [name, pct]}
              {@const ctrlThreat = getThreatLevel(pct)}
              <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px;">
                <span style="color: var(--text-muted);">{name}</span>
                <span style="color: {ctrlThreat.color}; font-weight: bold;">{pct}%</span>
              </div>
            {/each}
          </div>

          <div style="background: {agent.threat.color}; height: 3px; margin-top: 15px; width: {agent.coverage_score}%; transition: all 0.5s; box-shadow: 0 0 15px {agent.threat.color};"></div>
        </div>
      {/each}
    </div>

  {:else if viewMode === 'threats'}
    <!-- Threat Simulation Dashboard -->
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 30px;">
      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--danger-crimson); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          LIVE THREAT SIMULATION
        </h3>
        
        <div style="max-height: 300px; overflow-y: auto;">
          {#each threatSimulation as threat}
            <div 
              style="background: {threat.blocked ? 'rgba(0, 255, 65, 0.1)' : 'rgba(255, 7, 58, 0.1)'}; border-left: 3px solid {threat.blocked ? 'var(--matrix-primary)' : 'var(--danger-crimson)'}; padding: 12px; margin-bottom: 8px;"
            >
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="color: var(--neural-cyan); font-size: 13px; font-weight: bold;">{threat.type}</span>
                <span style="color: {threat.blocked ? 'var(--matrix-primary)' : 'var(--danger-crimson)'}; font-size: 11px; letter-spacing: 1px;">
                  {threat.blocked ? 'BLOCKED' : 'DETECTED'}
                </span>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 10px; color: var(--text-muted);">
                <span>SEVERITY: {threat.severity}/5</span>
                <span>{threat.timestamp}</span>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--plasma-magenta); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          ATTACK VECTORS
        </h3>
        
        <div style="display: grid; gap: 15px;">
          {#each attackVectors as vector}
            {@const blockRate = (vector.blocked / vector.attempts) * 100}
            {@const threat = getThreatLevel(blockRate)}
            <div style="background: rgba(0, 0, 0, 0.4); border: 1px solid {threat.color}; padding: 15px;">
              <div style="color: var(--neural-cyan); font-size: 13px; font-weight: bold; margin-bottom: 8px;">
                {vector.vector}
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 11px;">
                <span style="color: var(--text-muted);">ATTEMPTS: {vector.attempts}</span>
                <span style="color: {threat.color};">BLOCKED: {blockRate.toFixed(1)}%</span>
              </div>
              <div style="background: rgba(0, 0, 0, 0.6); height: 3px; border-radius: 2px; overflow: hidden;">
                <div style="background: {threat.color}; height: 100%; width: {blockRate}%; transition: all 0.5s;"></div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>

  {:else if viewMode === 'gaps'}
    <!-- Security Gaps Analysis -->
    <div class="holo-card-3d" style="padding: 25px; margin-bottom: 30px;">
      <h3 style="color: var(--danger-crimson); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        HIGH-RISK SECURITY GAPS
      </h3>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
        {#each getSecurityGaps() as gap}
          <div style="background: rgba(255, 7, 58, 0.05); border: 2px solid var(--danger-crimson); padding: 20px;">
            <div style="color: var(--danger-crimson); font-size: 16px; font-weight: bold; margin-bottom: 10px;">
              {gap.infrastructure.toUpperCase()}
            </div>
            <div style="color: var(--text-muted); font-size: 12px; margin-bottom: 15px;">
              {formatNumber(gap.total_assets)} ASSETS AT RISK
            </div>
            
            <div style="display: grid; gap: 10px;">
              <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span style="color: var(--neural-cyan);">EDR COVERAGE:</span>
                <span style="color: {getThreatLevel(gap.edr_coverage).color}; font-weight: bold;">{gap.edr_coverage}%</span>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span style="color: var(--neural-cyan);">TANIUM COVERAGE:</span>
                <span style="color: {getThreatLevel(gap.tanium_coverage).color}; font-weight: bold;">{gap.tanium_coverage}%</span>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 11px;">
                <span style="color: var(--neural-cyan);">RISK LEVEL:</span>
                <span style="color: var(--danger-crimson); font-weight: bold; letter-spacing: 1px;">{gap.risk_level.toUpperCase()}</span>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Selected Agent Details Modal -->
  {#if selectedAgent}
    <div class="dystopia-modal active" style="max-width: 700px;">
      <h2 style="color: var(--matrix-primary); font-size: 18px; letter-spacing: 2px; margin-bottom: 20px;">
        AGENT ANALYSIS: {selectedAgent}
      </h2>
      
      {@const agentData = getAgentDeploymentData().find(a => a.agent === selectedAgent)}
      {#if agentData}
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px;">
          <div style="text-align: center;">
            <div style="color: var(--neural-cyan); font-size: 20px; font-weight: bold;">{formatNumber(agentData.total)}</div>
            <div style="color: var(--text-muted); font-size: 11px;">DEPLOYMENTS</div>
          </div>
          <div style="text-align: center;">
            <div style="color: {agentData.threat.color}; font-size: 20px; font-weight: bold;">{agentData.coverage_score}%</div>
            <div style="color: var(--text-muted); font-size: 11px;">COVERAGE</div>
          </div>
          <div style="text-align: center;">
            <div style="color: {agentData.threat.color}; font-size: 16px; font-weight: bold;">{agentData.threat.level}</div>
            <div style="color: var(--text-muted); font-size: 11px;">PROTECTION</div>
          </div>
          <div style="text-align: center;">
            <div style="color: {agentData.threat.color}; font-size: 14px; font-weight: bold;">{agentData.threat.status}</div>
            <div style="color: var(--text-muted); font-size: 11px;">STATUS</div>
          </div>
        </div>
        
        <div style="display: grid; gap: 12px;">
          {#each [
            ['SPLUNK INTEGRATION', agentData.splunk],
            ['CMDB REGISTRATION', agentData.cmdb],
            ['EDR CORRELATION', agentData.crowdstrike],
            ['TANIUM SYNERGY', agentData.tanium]
          ] as [name, stats]}
            {@const threat = getThreatLevel(stats.percentage)}
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: rgba(0, 0, 0, 0.4); border-left: 2px solid {threat.color};">
              <div>
                <div style="color: var(--neural-cyan); font-size: 12px; font-weight: bold;">{name}</div>
                <div style="color: var(--text-muted); font-size: 10px;">{formatNumber(stats.count)} assets</div>
              </div>
              <div style="text-align: right;">
                <div style="color: {threat.color}; font-size: 14px; font-weight: bold;">{stats.percentage}%</div>
                <div style="color: {threat.color}; font-size: 9px;">{threat.status}</div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
      
      <button class="quantum-btn" style="margin-top: 20px; width: 100%;" on:click={() => selectedAgent = null}>
        CLOSE ANALYSIS
      </button>
    </div>
  {/if}
{/if}