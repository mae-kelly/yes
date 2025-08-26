<!-- /client/src/App.svelte -->
<script>
  import router from 'page';
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
  let currentComponent = GlobalView;

  const routes = {
    '/': { component: GlobalView, label: 'Global View', icon: '🌐' },
    '/infrastructure': { component: InfrastructureType, label: 'Infrastructure Type', icon: '🏗️' },
    '/regional': { component: RegionalCountryView, label: 'Regional & Country', icon: '🗺️' },
    '/business': { component: BUandApplicationView, label: 'BU & Application', icon: '🏢' },
    '/system': { component: SystemClassification, label: 'System Classification', icon: '⚙️' },
    '/security': { component: SecurityControlCoverage, label: 'Security Control Coverage', icon: '🔒' },
    '/domain': { component: DomainVisibility, label: 'Domain Visibility', icon: '🌍' },
    '/logging': { component: LoggingComplianceInGSOandSplunk, label: 'Logging Compliance', icon: '📝' },
    '/priority': { component: LogTypePriority, label: 'Log Type Priority', icon: '📊' }
  };

  function navigateTo(path) {
    currentRoute = path;
    currentComponent = routes[path].component;
    window.history.pushState({}, '', path);
  }

  // Handle browser back/forward buttons
  window.addEventListener('popstate', () => {
    const path = window.location.pathname;
    if (routes[path]) {
      currentRoute = path;
      currentComponent = routes[path].component;
    }
  });
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
    {#each Object.entries(routes) as [path, route]}
      <button 
        class="nav-tab {currentRoute === path ? 'active' : ''}"
        on:click={() => navigateTo(path)}
      >
        <span class="nav-tab-icon">{route.icon}</span>
        {route.label}
      </button>
    {/each}
  </nav>

  <div class="dashboard-content">
    <svelte:component this={currentComponent} />
  </div>
</div>