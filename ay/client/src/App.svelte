<script>
  console.log('🔍 App.svelte: AO1 Cyber Visibility Dashboard starting...');
  
  import { onMount } from 'svelte';
  import router from 'svelte-spa-router'
  
  // Import all the cybersecurity dashboard components
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
  
  // Route definitions for the cyber visibility dashboard
  const routes = {
    '/': GlobalView,
    '/global': GlobalView,
    '/infrastructure': InfrastructureType,
    '/regional': RegionalCountryView,
    '/business-units': BUandApplicationView,
    '/systems': SystemClassification,
    '/security': SecurityControlCoverage,
    '/domains': DomainVisibility,
    '/logging': LoggingComplianceInGSOandSplunk,
    '/priorities': LogTypePriority
  };
  
  const dashboardViews = [
    { key: 'global', label: 'GLOBAL VIEW', icon: '🌐', component: GlobalView },
    { key: 'infrastructure', label: 'INFRASTRUCTURE', icon: '🏗️', component: InfrastructureType },
    { key: 'regional', label: 'REGIONAL/COUNTRY', icon: '🗺️', component: RegionalCountryView },
    { key: 'business-units', label: 'BUSINESS UNITS', icon: '🏢', component: BUandApplicationView },
    { key: 'systems', label: 'SYSTEM CLASS', icon: '💻', component: SystemClassification },
    { key: 'security', label: 'SECURITY CONTROLS', icon: '🛡️', component: SecurityControlCoverage },
    { key: 'domains', label: 'DOMAIN VISIBILITY', icon: '🔍', component: DomainVisibility },
    { key: 'logging', label: 'LOGGING COMPLIANCE', icon: '📊', component: LoggingComplianceInGSOandSplunk },
    { key: 'priorities', label: 'LOG PRIORITIES', icon: '⚡', component: LogTypePriority }
  ];
  
  let currentComponent = GlobalView;
  
  function selectView(viewKey) {
    selectedView = viewKey;
    const view = dashboardViews.find(v => v.key === viewKey);
    if (view) {
      currentComponent = view.component;
      console.log(`🔍 Switched to ${view.label} dashboard`);
    }
  }
  
  async function checkServerStatus() {
    try {
      const response = await fetch('/api/health');
      if (response.ok) {
        serverStatus = 'connected';
        console.log('✅ Server connection established');
      } else {
        serverStatus = 'error';
        console.log('❌ Server responded with error');
      }
    } catch (error) {
      serverStatus = 'disconnected';
      console.log('❌ Server connection failed:', error);
    }
  }
  
  onMount(() => {
    console.log('✅ AO1 Cyber Visibility Dashboard mounted successfully!');
    checkServerStatus();
    
    return () => {
      console.log('🔍 AO1 Dashboard unmounting...');
    };
  });
</script>

<div class="dashboard">
  <!-- Circuit Overlay Background -->
  <div class="circuit-overlay"></div>
  
  <!-- Dashboard Header -->
  <header class="dashboard-header">
    <div class="dashboard-title">
      <div class="icon-circle" style="border-color: var(--accent-cyan); margin-right: 15px;">
        <span style="color: var(--accent-cyan); font-size: 18px;">🔒</span>
      </div>
      <div>
        <h1 class="title-main" style="margin: 0; color: var(--accent-cyan);">
          AO1 LOG VISIBILITY MEASUREMENT DASHBOARD
        </h1>
        <div style="color: var(--text-secondary); font-size: 0.9rem; margin-top: 5px;">
          Comprehensive Cybersecurity Operations Center (CSOC) Visibility Analysis
        </div>
      </div>
    </div>
    
    <div class="dashboard-controls">
      <div class="search-container">
        <input type="text" class="search-input" placeholder="SEARCH ASSETS..." />
      </div>
      
      <div class="status-badge" style="background: {serverStatus === 'connected' ? 'var(--status-good)' : serverStatus === 'error' ? 'var(--status-warning)' : 'var(--status-critical)'}; color: var(--primary-color); padding: 8px 16px; border-radius: 4px;">
        {serverStatus === 'connected' ? '🟢 CONNECTED' : serverStatus === 'error' ? '🟡 PARTIAL' : serverStatus === 'checking' ? '🔄 CHECKING' : '🔴 OFFLINE'}
      </div>
    </div>
  </header>
  
  <!-- Navigation Tabs -->
  <nav class="nav-tabs" style="margin: 20px 0;">
    {#each dashboardViews as view}
      <button 
        class="nav-tab {selectedView === view.key ? 'active' : ''}" 
        on:click={() => selectView(view.key)}
      >
        <span class="nav-tab-icon">{view.icon}</span>
        {view.label}
      </button>
    {/each}
  </nav>
  
  <!-- Main Dashboard Content -->
  <main class="dashboard-content">
    <div style="grid-column: span 12; position: relative;">
      {#if serverStatus === 'disconnected'}
        <div class="error">
          <div class="error-container">
            <h2 class="error-title" style="color: var(--status-critical);">🚨 BACKEND CONNECTION FAILED</h2>
            <p class="error-message">
              Unable to connect to the Flask API server. Please ensure the server is running on port 5000.
            </p>
            <div style="margin: 20px 0; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 8px;">
              <strong>To start the backend server:</strong><br/>
              <code style="color: var(--accent-cyan);">cd server && python app.py</code>
            </div>
            <button class="retry-button" on:click={checkServerStatus}>RETRY CONNECTION</button>
          </div>
        </div>
      {:else}
        <!-- Dynamic Component Rendering -->
        <div class="component-container" style="animation: fadeIn 0.5s ease-out;">
          <svelte:component this={currentComponent} />
        </div>
      {/if}
    </div>
  </main>
  
  <!-- Footer Stats -->
  <footer style="margin-top: 30px; padding: 20px 0; border-top: 1px solid var(--border-cyan);">
    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; color: var(--text-secondary);">
      <div>
        🔍 Real-time cybersecurity visibility across enterprise infrastructure
      </div>
      <div>
        Last updated: {new Date().toLocaleTimeString()} | Status: 
        <span style="color: {serverStatus === 'connected' ? 'var(--status-good)' : 'var(--status-critical)'};">
          {serverStatus.toUpperCase()}
        </span>
      </div>
    </div>
  </footer>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background: var(--gradient-primary);
    font-family: var(--font-mono);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
  }

  .dashboard {
    width: 100%;
    min-height: 100vh;
    padding: var(--spacing-md);
    position: relative;
    background: var(--gradient-primary);
  }

  .circuit-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      linear-gradient(to right, rgba(0, 229, 255, 0.08) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(0, 229, 255, 0.08) 1px, transparent 1px);
    background-size: 40px 40px;
    opacity: 0.3;
    pointer-events: none;
    z-index: 0;
  }

  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    position: relative;
    z-index: 2;
  }

  .dashboard-title {
    display: flex;
    align-items: center;
  }

  .dashboard-controls {
    display: flex;
    gap: var(--spacing-md);
    align-items: center;
  }

  .search-container {
    display: flex;
    align-items: center;
    background: rgba(0, 229, 255, 0.1);
    border: 2px solid var(--border-cyan);
    border-radius: var(--radius-md);
    padding: 8px var(--spacing-md);
    width: 200px;
  }

  .search-input {
    background: transparent;
    border: none;
    color: var(--text-primary);
    font-size: 0.9rem;
    font-family: var(--font-mono);
    width: 100%;
    outline: none;
    letter-spacing: 1px;
  }

  .search-input::placeholder {
    color: var(--text-muted);
  }

  .nav-tabs {
    display: flex;
    gap: var(--spacing-sm);
    margin-bottom: 0;
    flex-wrap: wrap;
    position: relative;
    z-index: 2;
  }

  .nav-tab {
    padding: var(--spacing-sm) var(--spacing-md);
    background: rgba(5, 16, 32, 0.6);
    border: 1px solid var(--border-cyan);
    border-radius: var(--radius-md);
    font-size: 0.85rem;
    color: var(--text-secondary);
    cursor: pointer;
    transition: var(--transition-normal);
    display: flex;
    align-items: center;
    font-family: var(--font-mono);
    font-weight: var(--font-weight-medium);
    letter-spacing: 1px;
  }

  .nav-tab:hover {
    background: rgba(0, 229, 255, 0.1);
    color: var(--text-primary);
    border-color: var(--accent-cyan);
  }

  .nav-tab.active {
    background: rgba(0, 229, 255, 0.2);
    color: var(--accent-cyan);
    border-color: var(--accent-cyan);
    box-shadow: var(--glow-cyan);
  }

  .nav-tab-icon {
    margin-right: var(--spacing-xs);
    font-size: 1rem;
  }

  .dashboard-content {
    position: relative;
    z-index: 2;
    min-height: 400px;
  }

  .component-container {
    background: rgba(5, 16, 32, 0.4);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    border: 1px solid var(--border-cyan);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  }

  .error {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 400px;
  }

  .error-container {
    background: rgba(5, 15, 25, 0.8);
    border: 2px solid var(--status-critical);
    box-shadow: 0 0 20px rgba(255, 35, 64, 0.3);
    border-radius: var(--radius-lg);
    padding: var(--spacing-2xl);
    max-width: 600px;
    text-align: center;
  }

  .error-title {
    font-size: 1.5rem;
    font-weight: var(--font-weight-bold);
    margin-bottom: var(--spacing-md);
  }

  .error-message {
    color: var(--text-secondary);
    margin-bottom: var(--spacing-lg);
    line-height: 1.6;
  }

  .retry-button {
    background: var(--tertiary-color);
    border: 2px solid var(--status-good);
    color: var(--status-good);
    padding: var(--spacing-md) var(--spacing-xl);
    font-family: var(--font-mono);
    font-weight: var(--font-weight-bold);
    font-size: 1rem;
    cursor: pointer;
    transition: var(--transition-normal);
    letter-spacing: 2px;
    border-radius: var(--radius-md);
    box-shadow: var(--glow-cyan);
  }

  .retry-button:hover {
    background: rgba(0, 229, 255, 0.1);
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 229, 255, 0.4);
  }

  .status-badge {
    font-size: 0.8rem;
    font-weight: var(--font-weight-bold);
    letter-spacing: 1px;
  }

  .title-main {
    font-size: 1.8rem;
    font-weight: var(--font-weight-bold);
    letter-spacing: 2px;
    text-shadow: 0 0 10px rgba(0, 229, 255, 0.4);
  }

  .icon-circle {
    width: 40px;
    height: 40px;
    border-radius: var(--radius-circle);
    background: transparent;
    border: 2px solid var(--accent-cyan);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--glow-cyan);
  }

  @keyframes fadeIn {
    from { 
      opacity: 0; 
      transform: translateY(20px); 
    }
    to { 
      opacity: 1; 
      transform: translateY(0); 
    }
  }

  /* Responsive Design */
  @media (max-width: 1200px) {
    .nav-tabs {
      gap: var(--spacing-xs);
    }
    
    .nav-tab {
      font-size: 0.75rem;
      padding: var(--spacing-xs) var(--spacing-sm);
    }
  }

  @media (max-width: 768px) {
    .dashboard-header {
      flex-direction: column;
      gap: var(--spacing-md);
    }
    
    .nav-tabs {
      justify-content: center;
    }
    
    .search-container {
      width: 100%;
      max-width: 250px;
    }
  }
</style>