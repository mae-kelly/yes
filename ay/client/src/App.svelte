// client/src/App.svelte
<script>
  import { onMount } from 'svelte';
  
  import GlobalView from './components/GlobalView.svelte';
  import InfrastructureType from './components/InfrastructureType.svelte';
  import RegionalCountryView from './components/RegionalCountryView.svelte';
  import BUandApplicationView from './components/BUandApplicationView.svelte';
  import SystemClassification from './components/SystemClassification.svelte';
  import SecurityControlCoverage from './components/SecurityControlCoverage.svelte';
  import DomainVisibility from './components/DomainVisibility.svelte';
  import LoggingComplianceInGSOandSplunk from './components/LoggingComplianceinGSOandSplunk.svelte';
  import LogTypePriority from './components/LogTypePriority.svelte';
  
  let selectedView = 'global';
  let serverStatus = 'checking';
  let currentTime = '';
  
  const dashboardViews = [
    { key: 'global', label: 'GLOBAL VISIBILITY', component: GlobalView },
    { key: 'infrastructure', label: 'INFRASTRUCTURE', component: InfrastructureType },
    { key: 'regional', label: 'REGIONS', component: RegionalCountryView },
    { key: 'business-units', label: 'BUSINESS UNITS', component: BUandApplicationView },
    { key: 'systems', label: 'SYSTEM CLASS', component: SystemClassification },
    { key: 'security', label: 'SECURITY', component: SecurityControlCoverage },
    { key: 'domains', label: 'DOMAINS', component: DomainVisibility },
    { key: 'logging', label: 'LOGGING', component: LoggingComplianceInGSOandSplunk },
    { key: 'priorities', label: 'PRIORITIES', component: LogTypePriority }
  ];
  
  let currentComponent = GlobalView;
  
  function selectView(viewKey) {
    selectedView = viewKey;
    const view = dashboardViews.find(v => v.key === viewKey);
    if (view) {
      currentComponent = view.component;
    }
  }
  
  async function checkServerStatus() {
    try {
      const response = await fetch('/api/health');
      if (response.ok) {
        serverStatus = 'connected';
      } else {
        serverStatus = 'error';
      }
    } catch (error) {
      serverStatus = 'disconnected';
    }
  }
  
  function updateTime() {
    const now = new Date();
    currentTime = now.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  }
  
  onMount(() => {
    checkServerStatus();
    updateTime();
    const interval = setInterval(updateTime, 1000);
    
    return () => clearInterval(interval);
  });
</script>

<div class="dashboard">
  <div class="circuit-overlay"></div>
  
  <header class="dashboard-header">
    <div class="dashboard-title">
      <div class="logo-section">
        <div class="logo-icon">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="15" stroke="url(#gradient)" stroke-width="2"/>
            <path d="M16 8 L8 16 L16 24 L24 16 Z" stroke="url(#gradient)" stroke-width="2" fill="none"/>
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#00e5ff;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#00ffff;stop-opacity:1" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div>
          <h1 class="title-main">SECURITY VISIBILITY MATRIX</h1>
          <div class="subtitle">SYSTEM // SECURITY // MONITORING</div>
        </div>
      </div>
    </div>
    
    <div class="dashboard-controls">
      <div class="search-container">
        <svg class="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1.5"/>
          <path d="M10 10L14 14" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        <input type="text" class="search-input" placeholder="SEARCH SYSTEMS..." />
      </div>
      
      <div class="time-display">{currentTime}</div>
      
      <div class="status-badge" class:connected={serverStatus === 'connected'} 
           class:error={serverStatus === 'error'} 
           class:disconnected={serverStatus === 'disconnected'}>
        {serverStatus === 'connected' ? 'LIVE DATA' : 
         serverStatus === 'error' ? 'PARTIAL' : 
         serverStatus === 'checking' ? 'CONNECTING' : 'OFFLINE'}
      </div>
    </div>
  </header>
  
  <nav class="nav-tabs">
    {#each dashboardViews as view}
      <button 
        class="nav-tab {selectedView === view.key ? 'active' : ''}" 
        on:click={() => selectView(view.key)}
      >
        {view.label}
      </button>
    {/each}
  </nav>
  
  <main class="dashboard-content">
    {#if serverStatus === 'disconnected'}
      <div class="error">
        <div class="error-container">
          <h2 class="error-title">CONNECTION FAILED</h2>
          <p class="error-message">
            Unable to establish connection to backend services.
            Please verify the server is operational on port 5000.
          </p>
          <div class="error-code">
            <code>cd server && python app.py</code>
          </div>
          <button class="retry-button" on:click={checkServerStatus}>
            RECONNECT
          </button>
        </div>
      </div>
    {:else}
      <div class="component-container">
        <svelte:component this={currentComponent} />
      </div>
    {/if}
  </main>
</div>

<style>
  .dashboard {
    position: relative;
    z-index: 2;
    padding: 2rem;
    min-height: 100vh;
  }

  .logo-section {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .logo-icon {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .time-display {
    font-family: var(--font-mono);
    font-size: 0.875rem;
    color: var(--accent-cyan);
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.05em;
  }

  .search-icon {
    color: var(--text-tertiary);
    margin-right: 0.5rem;
  }

  .status-badge.connected {
    background: linear-gradient(135deg, rgba(0, 255, 136, 0.2), rgba(0, 255, 136, 0.1));
    border-color: var(--status-good);
    color: var(--status-good);
  }

  .status-badge.error {
    background: linear-gradient(135deg, rgba(255, 170, 0, 0.2), rgba(255, 170, 0, 0.1));
    border-color: var(--status-warning);
    color: var(--status-warning);
  }

  .status-badge.disconnected {
    background: linear-gradient(135deg, rgba(255, 35, 64, 0.2), rgba(255, 35, 64, 0.1));
    border-color: var(--status-critical);
    color: var(--status-critical);
  }

  .error {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 400px;
  }

  .error-code {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid var(--border-cyan);
    border-radius: 8px;
    padding: 1rem;
    margin: 1.5rem 0;
  }

  .error-code code {
    color: var(--accent-cyan);
    font-family: var(--font-mono);
    font-size: 0.875rem;
  }

  .component-container {
    animation: fadeIn 0.5s ease-out;
  }

  @keyframes fadeIn {
    from { 
      opacity: 0; 
      transform: translateY(10px); 
    }
    to { 
      opacity: 1; 
      transform: translateY(0); 
    }
  }
</style>