<!-- /src/App.svelte -->
<script>
  import { Router, link, push } from 'svelte-spa-router';
  import GlobalView from './components/GlobalView.svelte';
  import InfrastructureType from './components/InfrastructureType.svelte';
  import RegionalCountryView from './components/RegionalCountryView.svelte';
  import BUandApplicationView from './components/BUandApplicationView.svelte';
  import SystemClassification from './components/SystemClassification.svelte';
  import SecurityControlCoverage from './components/SecurityControlCoverage.svelte';
  import DomainVisibility from './components/DomainVisibility.svelte';
  import LoggingComplianceInGSOandSplunk from './components/LoggingComplianceInGSOandSplunk.svelte';
  import LogTypePriority from './components/LogTypePriority.svelte';

  let currentRoute = '/';

  const routes = {
    '/': GlobalView,
    '/infrastructure': InfrastructureType,
    '/regional': RegionalCountryView,
    '/business': BUandApplicationView,
    '/system': SystemClassification,
    '/security': SecurityControlCoverage,
    '/domain': DomainVisibility,
    '/logging': LoggingComplianceInGSOandSplunk,
    '/priority': LogTypePriority
  };

  const navItems = [
    { path: '/', label: 'Global View', icon: '🌐' },
    { path: '/infrastructure', label: 'Infrastructure Type', icon: '🏗️' },
    { path: '/regional', label: 'Regional & Country', icon: '🗺️' },
    { path: '/business', label: 'BU & Application', icon: '🏢' },
    { path: '/system', label: 'System Classification', icon: '⚙️' },
    { path: '/security', label: 'Security Control Coverage', icon: '🔒' },
    { path: '/domain', label: 'Domain Visibility', icon: '🌍' },
    { path: '/logging', label: 'Logging Compliance', icon: '📝' },
    { path: '/priority', label: 'Log Type Priority', icon: '📊' }
  ];

  function handleRouteChange(e) {
    currentRoute = e.detail.location;
  }
</script>

<svelte:head>
  <title>AO1 Log Visibility Measurement Dashboard</title>
</svelte:head>

<div class="dashboard">
  <div class="circuit-overlay"></div>
  
  <div class="dashboard-header">
    <div class="dashboard-title">
      <div class="icon-circle">
        <span style="color: var(--status-good); font-size: 18px;">⚡</span>
      </div>
      <h1 class="title-main">AO1 LOG VISIBILITY MEASUREMENT</h1>
    </div>
    
    <div class="search-container">
      <input 
        type="text" 
        class="search-input" 
        placeholder="SEARCH ASSETS..."
      />
    </div>
  </div>

  <nav class="nav-tabs">
    {#each navItems as item}
      <button 
        class="nav-tab {currentRoute === item.path ? 'active' : ''}"
        on:click={() => push(item.path)}
      >
        <span class="nav-tab-icon">{item.icon}</span>
        {item.label}
      </button>
    {/each}
  </nav>

  <div class="dashboard-content">
    <Router {routes} on:routeEvent={handleRouteChange} />
  </div>
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
    height: 100vh;
    padding: var(--spacing-md);
    display: flex;
    flex-direction: column;
    overflow: auto;
    position: relative;
    background: var(--gradient-primary);
  }
  
  .dashboard-content {
    flex: 1;
    margin-top: var(--spacing-md);
    position: relative;
    z-index: 2;
  }
</style>