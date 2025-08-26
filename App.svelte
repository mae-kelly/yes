<!-- /src/App.svelte -->
<script>
  import { onMount, onDestroy } from 'svelte';
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
  let mouseX = 0;
  let mouseY = 0;
  let matrixRain = [];
  let trailElements = [];

  const tabs = [
    { id: 'global', label: 'NEURAL OVERVIEW', icon: '⚡', threat: 'CRITICAL' },
    { id: 'infrastructure', label: 'ASSET MATRIX', icon: '🔬', threat: 'HIGH' },
    { id: 'regional', label: 'SECTOR GRID', icon: '🌐', threat: 'MEDIUM' },
    { id: 'business', label: 'CORP ANALYSIS', icon: '💼', threat: 'HIGH' },
    { id: 'system', label: 'SYS CLASSIFY', icon: '🧠', threat: 'CRITICAL' },
    { id: 'security', label: 'DEFENSE GRID', icon: '🛡️', threat: 'CRITICAL' },
    { id: 'logging', label: 'LOG MATRIX', icon: '📊', threat: 'HIGH' },
    { id: 'domain', label: 'ZONE RECON', icon: '🎯', threat: 'MEDIUM' },
    { id: 'priority', label: 'THREAT RANK', icon: '⚠️', threat: 'HIGH' }
  ];

  function createMatrixRain() {
    const characters = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEF';
    const columns = Math.floor(window.innerWidth / 20);
    
    for (let i = 0; i < columns; i++) {
      matrixRain.push({
        x: i * 20,
        y: Math.random() * window.innerHeight,
        speed: Math.random() * 3 + 1,
        characters: Array.from({length: 20}, () => characters[Math.floor(Math.random() * characters.length)])
      });
    }
  }

  function updateMatrixRain() {
    matrixRain = matrixRain.map(column => ({
      ...column,
      y: column.y + column.speed,
      characters: column.characters.map(() => 
        Math.random() > 0.98 ? 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEF'[Math.floor(Math.random() * 89)] : column.characters[0]
      )
    }));

    matrixRain.forEach(column => {
      if (column.y > window.innerHeight + 100) {
        column.y = -100;
        column.speed = Math.random() * 3 + 1;
      }
    });
  }

  function handleMouseMove(event) {
    mouseX = event.clientX;
    mouseY = event.clientY;
    
    document.documentElement.style.setProperty('--mouse-x', `${mouseX}px`);
    document.documentElement.style.setProperty('--mouse-y', `${mouseY}px`);

    createMouseTrail(mouseX, mouseY);
  }

  function createMouseTrail(x, y) {
    const trail = document.createElement('div');
    trail.className = 'mouse-trail';
    trail.style.left = `${x}px`;
    trail.style.top = `${y}px`;
    document.body.appendChild(trail);
    
    setTimeout(() => {
      if (trail.parentNode) {
        trail.parentNode.removeChild(trail);
      }
    }, 1000);
  }

  let matrixInterval;
  let threatLevel = 'SECURE';
  let systemStatus = 'OPERATIONAL';

  onMount(() => {
    createMatrixRain();
    matrixInterval = setInterval(updateMatrixRain, 100);
    
    const updateThreatLevel = () => {
      const levels = ['SECURE', 'ELEVATED', 'HIGH', 'CRITICAL', 'BREACH'];
      threatLevel = levels[Math.floor(Math.random() * levels.length)];
      systemStatus = Math.random() > 0.8 ? 'DEGRADED' : 'OPERATIONAL';
    };
    
    setInterval(updateThreatLevel, 5000);
  });

  onDestroy(() => {
    if (matrixInterval) clearInterval(matrixInterval);
  });

  function getThreatColor(level) {
    switch(level) {
      case 'CRITICAL': return 'var(--danger-crimson)';
      case 'HIGH': return 'var(--plasma-magenta)';
      case 'MEDIUM': return 'var(--toxic-yellow)';
      default: return 'var(--matrix-primary)';
    }
  }
</script>

<svelte:window on:mousemove={handleMouseMove} />

<!-- Quantum Cursor System -->
<div class="cursor-tracker"></div>

<!-- Matrix Rain Effect -->
<div class="matrix-rain-container">
  {#each matrixRain as column}
    <div class="matrix-column" style="left: {column.x}px; transform: translateY({column.y}px);">
      {#each column.characters.slice(0, 15) as char, i}
        <div style="opacity: {1 - (i * 0.08)}; color: {i === 0 ? 'var(--neural-cyan)' : 'var(--matrix-primary)'}">{char}</div>
      {/each}
    </div>
  {/each}
</div>

<!-- Holographic Depth Layers -->
<div class="hologram-layer"></div>
<div class="ar-overlay">
  <div class="ar-grid"></div>
</div>

<!-- Threat Detection System -->
<div class="threat-detector">
  <div class="radar">
    <div class="radar-sweep"></div>
  </div>
</div>

<!-- Main Neural Interface -->
<div class="neural-window" style="width: 100vw; height: 100vh; border-radius: 0; margin: 0; padding: 0;">
  <div class="neural-scan"></div>
  
  <!-- Classification Header -->
  <div style="position: fixed; top: 15px; left: 20px; z-index: var(--z-interface); display: flex; align-items: center; gap: 20px;">
    <div class="glitch-text" data-text="AO1-LOG-VISIBILITY-NEURAL-MATRIX" style="font-size: 24px; font-weight: bold; letter-spacing: 3px; color: var(--matrix-primary);">
      AO1-LOG-VISIBILITY-NEURAL-MATRIX
    </div>
    <div style="color: {threatLevel === 'CRITICAL' ? 'var(--danger-crimson)' : threatLevel === 'HIGH' ? 'var(--plasma-magenta)' : 'var(--matrix-primary)'}; font-size: 14px; letter-spacing: 2px; animation: blink-cursor 1s infinite;">
      THREAT: {threatLevel} | STATUS: {systemStatus}
    </div>
  </div>

  <!-- System Stats -->
  <div style="position: fixed; top: 60px; right: 240px; z-index: var(--z-interface); font-size: 12px; color: var(--neural-cyan); letter-spacing: 1px;">
    <div>UPTIME: 99.97% | LATENCY: 12ms</div>
    <div>NEURAL CORES: 16 | MEMORY: 2.1TB</div>
  </div>

  <!-- Neural Navigation Interface -->
  <nav style="position: fixed; top: 100px; left: 20px; right: 20px; z-index: var(--z-interface); display: flex; gap: 8px; flex-wrap: wrap;">
    {#each tabs as tab}
      <button
        class="quantum-btn {activeTab === tab.id ? 'active' : ''} {tab.threat === 'CRITICAL' ? 'danger' : ''}"
        style="padding: 12px 24px; font-size: 11px; border: 1px solid {getThreatColor(tab.threat)}; color: {activeTab === tab.id ? 'var(--void-black)' : getThreatColor(tab.threat)}; background: {activeTab === tab.id ? getThreatColor(tab.threat) : 'transparent'}; position: relative;"
        on:click={() => activeTab = tab.id}
      >
        <span style="margin-right: 8px; font-size: 14px;">{tab.icon}</span>
        {tab.label}
        <span style="position: absolute; top: -8px; right: -8px; background: {getThreatColor(tab.threat)}; color: var(--void-black); font-size: 8px; padding: 2px 4px; border-radius: 2px;">
          {tab.threat}
        </span>
      </button>
    {/each}
  </nav>

  <!-- Biometric Scanner -->
  <div style="position: fixed; top: 100px; right: 20px; width: 200px; z-index: var(--z-interface);">
    <div class="biometric-input" placeholder="NEURAL SEARCH..." style="font-size: 12px; padding: 10px; background: rgba(0, 0, 0, 0.9); border: 1px solid var(--neural-cyan);">
      <div class="scan-line"></div>
    </div>
  </div>

  <!-- Main Content Matrix -->
  <div class="holo-card-3d" style="position: absolute; top: 180px; left: 20px; right: 20px; bottom: 20px; padding: 30px; overflow-y: auto; background: linear-gradient(135deg, rgba(0, 0, 0, 0.98), rgba(0, 255, 65, 0.02)); border: 2px solid var(--matrix-primary); backdrop-filter: blur(10px);">
    
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
  <div style="position: fixed; bottom: 0; left: 0; right: 0; height: 30px; background: linear-gradient(90deg, rgba(0, 0, 0, 0.95), rgba(0, 255, 65, 0.1), rgba(0, 0, 0, 0.95)); border-top: 1px solid var(--matrix-primary); display: flex; align-items: center; justify-content: space-between; padding: 0 20px; font-size: 10px; color: var(--neural-cyan); letter-spacing: 1px; z-index: var(--z-interface);">
    <div>NEURAL LINK ESTABLISHED | CLEARANCE LEVEL: OMEGA | SESSION: {new Date().getTime()}</div>
    <div style="display: flex; gap: 20px;">
      <div>CPU: 23%</div>
      <div>RAM: 67%</div>
      <div>NET: 1.2GB/s</div>
      <div style="color: var(--matrix-primary);">◉ CONNECTED</div>
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

  :global(.quantum-btn.active) {
    animation: quantum-glitch 0.5s infinite;
    box-shadow: 
      0 0 30px currentColor,
      inset 0 0 20px rgba(255, 255, 255, 0.1);
  }

  :global(.holo-card-3d:hover) {
    --rotate-x: 2deg;
    --rotate-y: 3deg;
  }

  :global(*::-webkit-scrollbar) {
    width: 8px;
    height: 8px;
  }

  :global(*::-webkit-scrollbar-track) {
    background: rgba(0, 0, 0, 0.8);
    border: 1px solid var(--matrix-primary);
  }

  :global(*::-webkit-scrollbar-thumb) {
    background: linear-gradient(180deg, var(--matrix-primary), var(--neural-cyan));
    border: 1px solid var(--void-black);
    box-shadow: 0 0 10px var(--matrix-primary);
  }

  :global(*::-webkit-scrollbar-thumb:hover) {
    background: linear-gradient(180deg, var(--neural-cyan), var(--plasma-magenta));
    box-shadow: 0 0 20px var(--neural-cyan);
  }

  @keyframes quantum-glitch {
    0%, 100% { transform: translate(0, 0); }
    20% { transform: translate(-1px, 1px); }
    40% { transform: translate(-1px, -1px); }
    60% { transform: translate(1px, 1px); }
    80% { transform: translate(1px, -1px); }
  }
</style>