<!-- /src/App.svelte -->
<script>
  import { onMount } from 'svelte';
  import GlobalView from './components/GlobalView.svelte';
  import InfrastructureType from './components/InfrastructureType.svelte';
  import RegionalCountryView from './components/RegionalCountryView.svelte';
  import BUandApplicationView from './components/BUandApplicationView.svelte';
  import SystemClassification from './components/SystemClassification.svelte';
  import SecurityControlCoverage from './components/SecurityControlCoverage.svelte';
  import LoggingComplianceInGSOandSplunk from './components/LoggingComplianceInGSOandSplunk.svelte';
  import DomainVisibility from './components/DomainVisibility.svelte';
  import LogTypePriority from './components/LogTypePriority.svelte';

  let activeTab = 'global';
  let systemStatus = 'OPERATIONAL';
  let threatLevel = 'ELEVATED';

  const tabs = [
    { id: 'global', label: 'GLOBAL VIEW', icon: '◉', requirement: 'Global % visibility across all assets' },
    { id: 'infrastructure', label: 'INFRASTRUCTURE TYPE', icon: '▣', requirement: '% visibility by host and log type' },
    { id: 'regional', label: 'REGIONAL & COUNTRY', icon: '◈', requirement: 'Geographic visibility breakdown' },
    { id: 'business', label: 'BU & APPLICATION', icon: '◆', requirement: 'Business unit and CIO coverage' },
    { id: 'system', label: 'SYSTEM CLASSIFICATION', icon: '◇', requirement: 'System type and class analysis' },
    { id: 'security', label: 'SECURITY CONTROLS', icon: '◎', requirement: 'EDR, Tanium, DLP agent coverage' },
    { id: 'logging', label: 'LOGGING COMPLIANCE', icon: '◐', requirement: 'GSO and Splunk compliance' },
    { id: 'domain', label: 'DOMAIN VISIBILITY', icon: '◑', requirement: 'Hostname and domain coverage' },
    { id: 'priority', label: 'LOG TYPE PRIORITY', icon: '◒', requirement: 'Critical system log prioritization' }
  ];

  onMount(() => {
    const updateStatus = () => {
      const statuses = ['OPERATIONAL', 'DEGRADED', 'MAINTENANCE'];
      const threats = ['SECURE', 'ELEVATED', 'HIGH', 'CRITICAL'];
      systemStatus = statuses[Math.floor(Math.random() * statuses.length)];
      threatLevel = threats[Math.floor(Math.random() * threats.length)];
    };
    
    setInterval(updateStatus, 8000);
  });

  function getThreatColor(level) {
    switch(level) {
      case 'CRITICAL': return 'var(--danger-crimson)';
      case 'HIGH': return 'var(--plasma-magenta)';
      case 'ELEVATED': return 'var(--toxic-yellow)';
      default: return 'var(--matrix-primary)';
    }
  }

  function getStatusColor(status) {
    switch(status) {
      case 'OPERATIONAL': return 'var(--matrix-primary)';
      case 'DEGRADED': return 'var(--toxic-yellow)';
      case 'MAINTENANCE': return 'var(--neural-cyan)';
      default: return 'var(--matrix-primary)';
    }
  }
</script>

<!-- Neural Background Effects -->
<div class="matrix-rain-container">
  <div class="matrix-column" style="left: 5%; animation-duration: 20s;">01001010</div>
  <div class="matrix-column" style="left: 15%; animation-duration: 15s;">11010011</div>
  <div class="matrix-column" style="left: 25%; animation-duration: 25s;">00110101</div>
  <div class="matrix-column" style="left: 35%; animation-duration: 18s;">10101010</div>
  <div class="matrix-column" style="left: 45%; animation-duration: 22s;">01110010</div>
  <div class="matrix-column" style="left: 55%; animation-duration: 16s;">11001100</div>
  <div class="matrix-column" style="left: 65%; animation-duration: 19s;">00101101</div>
  <div class="matrix-column" style="left: 75%; animation-duration: 24s;">10011001</div>
  <div class="matrix-column" style="left: 85%; animation-duration: 17s;">01010101</div>
  <div class="matrix-column" style="left: 95%; animation-duration: 21s;">11110000</div>
</div>

<div class="hologram-layer"></div>
<div class="ar-overlay"><div class="ar-grid"></div></div>

<!-- Main Neural Interface Container -->
<div class="neural-window" style="width: 100vw; height: 100vh; margin: 0; padding: 0; border-radius: 0;">
  <div class="neural-scan"></div>
  
  <!-- Classification Header -->
  <div style="position: fixed; top: 0; left: 0; right: 0; background: linear-gradient(90deg, rgba(0, 0, 0, 0.95), rgba(0, 255, 65, 0.1), rgba(0, 0, 0, 0.95)); border-bottom: 1px solid var(--matrix-primary); padding: 15px 25px; z-index: var(--z-interface); display: flex; justify-content: space-between; align-items: center;">
    <div>
      <div class="glitch-text" data-text="AO1 LOG VISIBILITY MEASUREMENT SYSTEM" style="font-size: 20px; font-weight: bold; letter-spacing: 3px;">
        AO1 LOG VISIBILITY MEASUREMENT SYSTEM
      </div>
      <div style="color: var(--neural-cyan); font-size: 11px; letter-spacing: 2px; margin-top: 3px;">
        CSOC THREAT DETECTION & RESPONSE CAPABILITY ANALYSIS
      </div>
    </div>
    
    <div style="display: flex; align-items: center; gap: 20px; font-size: 12px;">
      <div style="display: flex; align-items: center; gap: 8px;">
        <div style="width: 8px; height: 8px; background: {getStatusColor(systemStatus)}; border-radius: 50%; animation: pulse 2s infinite;"></div>
        <span style="color: {getStatusColor(systemStatus)}; letter-spacing: 1px;">STATUS: {systemStatus}</span>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <div style="width: 8px; height: 8px; background: {getThreatColor(threatLevel)}; border-radius: 50%; animation: blink-cursor 1s infinite;"></div>
        <span style="color: {getThreatColor(threatLevel)}; letter-spacing: 1px;">THREAT: {threatLevel}</span>
      </div>
      <div style="color: var(--neural-cyan); letter-spacing: 1px;">
        SESSION: {new Date().getTime().toString().slice(-6)}
      </div>
    </div>
  </div>

  <!-- Navigation Matrix -->
  <nav style="position: fixed; top: 80px; left: 25px; right: 25px; z-index: var(--z-interface); display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
    {#each tabs as tab}
      <button
        class="quantum-btn {activeTab === tab.id ? 'active' : ''}"
        style="
          padding: 12px 20px; 
          font-size: 10px; 
          border: 1px solid {activeTab === tab.id ? 'var(--matrix-primary)' : 'rgba(0, 255, 65, 0.3)'}; 
          color: {activeTab === tab.id ? 'var(--void-black)' : 'var(--matrix-primary)'}; 
          background: {activeTab === tab.id ? 'var(--matrix-primary)' : 'transparent'};
          position: relative;
          overflow: hidden;
        "
        on:click={() => activeTab = tab.id}
      >
        <div style="display: flex; align-items: center; gap: 8px; position: relative; z-index: 2;">
          <span style="font-size: 14px;">{tab.icon}</span>
          <div style="text-align: left;">
            <div style="font-weight: bold; letter-spacing: 1px;">{tab.label}</div>
            <div style="font-size: 8px; opacity: 0.7; margin-top: 2px; color: {activeTab === tab.id ? 'rgba(0, 0, 0, 0.7)' : 'var(--neural-cyan)'};">
              {tab.requirement}
            </div>
          </div>
        </div>
        
        {#if activeTab === tab.id}
          <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(45deg, transparent 30%, rgba(0, 255, 255, 0.2) 50%, transparent 70%); animation: quantum-sweep 2s linear infinite;"></div>
        {/if}
      </button>
    {/each}
  </nav>

  <!-- Main Content Neural Grid -->
  <div style="position: absolute; top: 200px; left: 25px; right: 25px; bottom: 40px; background: linear-gradient(135deg, rgba(0, 0, 0, 0.98), rgba(0, 255, 65, 0.02)); border: 2px solid var(--matrix-primary); backdrop-filter: blur(10px); overflow-y: auto; padding: 25px;">
    {#if activeTab === 'global'}
      <GlobalView />
    {:else if activeTab === 'infrastructure'}
      <InfrastructureType />
    {:else if activeTab === 'regional'}
      <RegionalCountryView />
    {:else if activeTab === 'business'}
      <BUandApplicationView />
    {:else if activeTab === 'system'}
      <SystemClassification />
    {:else if activeTab === 'security'}
      <SecurityControlCoverage />
    {:else if activeTab === 'logging'}
      <LoggingComplianceInGSOandSplunk />
    {:else if activeTab === 'domain'}
      <DomainVisibility />
    {:else if activeTab === 'priority'}
      <LogTypePriority />
    {/if}
  </div>

  <!-- Neural Status Bar -->
  <div style="position: fixed; bottom: 0; left: 0; right: 0; height: 35px; background: linear-gradient(90deg, rgba(0, 0, 0, 0.95), rgba(0, 255, 65, 0.1), rgba(0, 0, 0, 0.95)); border-top: 1px solid var(--matrix-primary); display: flex; align-items: center; justify-content: space-between; padding: 0 25px; font-size: 10px; color: var(--neural-cyan); letter-spacing: 1px; z-index: var(--z-interface);">
    <div style="display: flex; gap: 25px;">
      <div>NEURAL LINK: ESTABLISHED</div>
      <div>CLEARANCE: OMEGA-7</div>
      <div>ANALYZING: AO1 VISIBILITY MATRIX</div>
    </div>
    <div style="display: flex; gap: 20px;">
      <div>CPU: 23%</div>
      <div>RAM: 67%</div>
      <div>NET: 1.2GB/s</div>
      <div style="color: var(--matrix-primary); display: flex; align-items: center; gap: 5px;">
        <div style="width: 6px; height: 6px; background: var(--matrix-primary); border-radius: 50%; animation: pulse 2s infinite;"></div>
        CONNECTED
      </div>
    </div>
  </div>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    overflow: hidden;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    background: var(--void-black);
    color: var(--matrix-primary);
  }

  @keyframes quantum-sweep {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
  }

  @keyframes blink-cursor {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }

  @keyframes danger-breathe {
    0%, 100% { box-shadow: 0 0 20px rgba(255, 7, 58, 0.3); }
    50% { box-shadow: 0 0 40px rgba(255, 7, 58, 0.6); }
  }
</style>