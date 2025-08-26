<script>
  import { onMount } from 'svelte';
  
  let serverStatus = 'checking';
  let apiResults = {};
  let currentView = 'health';
  let debugLogs = [];
  
  const endpoints = [
    { name: 'health', url: '/api/health', description: 'Server health check' },
    { name: 'global', url: '/api/global-view', description: 'Global coverage metrics' },
    { name: 'domain', url: '/api/domain-visibility', description: 'Domain analysis' },
    { name: 'regional', url: '/api/regional-country-view', description: 'Regional breakdown' },
    { name: 'business', url: '/api/bu-application-view', description: 'Business units' },
    { name: 'systems', url: '/api/system-classification', description: 'System classification' },
    { name: 'security', url: '/api/security-control-coverage', description: 'Security coverage' },
    { name: 'logging', url: '/api/logging-compliance-gso-splunk', description: 'Logging compliance' },
    { name: 'priority', url: '/api/log-type-priority', description: 'Log priorities' }
  ];
  
  function log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    debugLogs = [...debugLogs, { timestamp, message, type }];
    console.log(`[${timestamp}] ${message}`);
  }
  
  async function testEndpoint(endpoint) {
    log(`Testing ${endpoint.name}: ${endpoint.url}`, 'info');
    
    try {
      const startTime = Date.now();
      const response = await fetch(endpoint.url);
      const duration = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        apiResults[endpoint.name] = {
          status: 'success',
          data: data,
          duration: duration,
          timestamp: new Date().toISOString()
        };
        log(`✅ ${endpoint.name} - ${response.status} (${duration}ms)`, 'success');
      } else {
        const errorText = await response.text();
        apiResults[endpoint.name] = {
          status: 'error',
          error: `HTTP ${response.status}: ${errorText}`,
          duration: duration,
          timestamp: new Date().toISOString()
        };
        log(`❌ ${endpoint.name} - HTTP ${response.status} (${duration}ms)`, 'error');
      }
    } catch (error) {
      apiResults[endpoint.name] = {
        status: 'failed',
        error: error.message,
        timestamp: new Date().toISOString()
      };
      log(`💥 ${endpoint.name} - ${error.message}`, 'error');
    }
  }
  
  async function testAllEndpoints() {
    log('Starting API endpoint tests...', 'info');
    apiResults = {};
    
    for (const endpoint of endpoints) {
      await testEndpoint(endpoint);
      await new Promise(resolve => setTimeout(resolve, 100)); // Small delay between requests
    }
    
    log('All endpoint tests completed', 'info');
  }
  
  async function checkDatabaseConnection() {
    log('Checking database connection...', 'info');
    
    try {
      const response = await fetch('/api/health');
      if (response.ok) {
        const data = await response.json();
        serverStatus = 'connected';
        log(`Database connected: ${data.total_hosts} hosts found`, 'success');
        
        if (data.detection_test) {
          log('Detection rules test:', 'info');
          Object.entries(data.detection_test).forEach(([key, count]) => {
            log(`  ${key}: ${count} hosts`, 'info');
          });
        }
      } else {
        serverStatus = 'error';
        log(`Health check failed: ${response.status}`, 'error');
      }
    } catch (error) {
      serverStatus = 'disconnected';
      log(`Connection failed: ${error.message}`, 'error');
    }
  }
  
  function clearLogs() {
    debugLogs = [];
  }
  
  function exportResults() {
    const results = {
      timestamp: new Date().toISOString(),
      serverStatus: serverStatus,
      apiResults: apiResults,
      debugLogs: debugLogs
    };
    
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cmdb_debug_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
  
  onMount(() => {
    log('Debug app started', 'info');
    checkDatabaseConnection();
  });
</script>

<div class="debug-container">
  <header class="debug-header">
    <h1>CMDB API Debug Tool</h1>
    <div class="status">
      Server: <span class="status-{serverStatus}">{serverStatus}</span>
    </div>
  </header>
  
  <nav class="debug-nav">
    <button on:click={() => currentView = 'health'} class:active={currentView === 'health'}>
      Health Check
    </button>
    <button on:click={() => currentView = 'endpoints'} class:active={currentView === 'endpoints'}>
      API Tests
    </button>
    <button on:click={() => currentView = 'logs'} class:active={currentView === 'logs'}>
      Debug Logs ({debugLogs.length})
    </button>
  </nav>
  
  <main class="debug-content">
    {#if currentView === 'health'}
      <div class="section">
        <h2>Database Health Check</h2>
        <button on:click={checkDatabaseConnection} class="btn-primary">
          Refresh Health Check
        </button>
        
        {#if apiResults.health}
          <div class="health-results">
            <h3>Connection Status: {apiResults.health.status}</h3>
            
            {#if apiResults.health.data}
              <div class="health-data">
                <p><strong>Total Hosts:</strong> {apiResults.health.data.total_hosts?.toLocaleString()}</p>
                <p><strong>Database:</strong> {apiResults.health.data.database}</p>
                
                {#if apiResults.health.data.detection_test}
                  <h4>Detection Rules Test:</h4>
                  <ul>
                    {#each Object.entries(apiResults.health.data.detection_test) as [rule, count]}
                      <li>{rule}: <strong>{count.toLocaleString()}</strong> hosts</li>
                    {/each}
                  </ul>
                {/if}
              </div>
            {/if}
            
            {#if apiResults.health.error}
              <div class="error">
                <strong>Error:</strong> {apiResults.health.error}
              </div>
            {/if}
          </div>
        {/if}
      </div>
      
    {:else if currentView === 'endpoints'}
      <div class="section">
        <h2>API Endpoint Tests</h2>
        <button on:click={testAllEndpoints} class="btn-primary">
          Test All Endpoints
        </button>
        
        <div class="endpoints-grid">
          {#each endpoints as endpoint}
            <div class="endpoint-card">
              <div class="endpoint-header">
                <h3>{endpoint.name}</h3>
                <button on:click={() => testEndpoint(endpoint)} class="btn-small">
                  Test
                </button>
              </div>
              
              <p class="endpoint-url">{endpoint.url}</p>
              <p class="endpoint-desc">{endpoint.description}</p>
              
              {#if apiResults[endpoint.name]}
                {@const result = apiResults[endpoint.name]}
                <div class="endpoint-result status-{result.status}">
                  <p><strong>Status:</strong> {result.status}</p>
                  {#if result.duration}
                    <p><strong>Duration:</strong> {result.duration}ms</p>
                  {/if}
                  
                  {#if result.data}
                    <details>
                      <summary>View Data ({Object.keys(result.data).length} keys)</summary>
                      <pre>{JSON.stringify(result.data, null, 2)}</pre>
                    </details>
                  {/if}
                  
                  {#if result.error}
                    <p class="error"><strong>Error:</strong> {result.error}</p>
                  {/if}
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </div>
      
    {:else if currentView === 'logs'}
      <div class="section">
        <h2>Debug Logs</h2>
        <div class="log-controls">
          <button on:click={clearLogs} class="btn-secondary">
            Clear Logs
          </button>
          <button on:click={exportResults} class="btn-primary">
            Export Debug Data
          </button>
        </div>
        
        <div class="log-container">
          {#each debugLogs as logEntry}
            <div class="log-entry log-{logEntry.type}">
              <span class="log-timestamp">{logEntry.timestamp}</span>
              <span class="log-message">{logEntry.message}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </main>
</div>

<style>
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  
  .debug-container {
    font-family: 'Courier New', monospace;
    background: #1a1a1a;
    color: #e0e0e0;
    min-height: 100vh;
    padding: 20px;
  }
  
  .debug-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #2d2d2d;
    padding: 15px 20px;
    border-radius: 8px;
    margin-bottom: 20px;
  }
  
  .debug-header h1 {
    color: #00ff41;
    font-size: 24px;
  }
  
  .status {
    font-size: 14px;
  }
  
  .status-connected {
    color: #00ff41;
    font-weight: bold;
  }
  
  .status-error {
    color: #ff6b6b;
    font-weight: bold;
  }
  
  .status-disconnected {
    color: #ff6b6b;
    font-weight: bold;
  }
  
  .debug-nav {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
  }
  
  .debug-nav button {
    background: #2d2d2d;
    border: 1px solid #444;
    color: #e0e0e0;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.2s;
  }
  
  .debug-nav button:hover {
    background: #3d3d3d;
    border-color: #666;
  }
  
  .debug-nav button.active {
    background: #00ff41;
    color: #000;
    border-color: #00ff41;
  }
  
  .debug-content {
    background: #2d2d2d;
    border-radius: 8px;
    padding: 20px;
  }
  
  .section h2 {
    color: #00ffff;
    margin-bottom: 20px;
    font-size: 20px;
  }
  
  .btn-primary {
    background: #00ff41;
    color: #000;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-family: inherit;
    font-weight: bold;
    margin-bottom: 20px;
  }
  
  .btn-primary:hover {
    background: #00cc33;
  }
  
  .btn-secondary {
    background: #666;
    color: #fff;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
  }
  
  .btn-secondary:hover {
    background: #777;
  }
  
  .btn-small {
    background: #444;
    color: #fff;
    border: 1px solid #666;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-size: 12px;
  }
  
  .btn-small:hover {
    background: #555;
  }
  
  .health-results {
    background: #1a1a1a;
    padding: 20px;
    border-radius: 6px;
    border-left: 4px solid #00ff41;
  }
  
  .health-data ul {
    list-style: none;
    padding-left: 20px;
  }
  
  .health-data li {
    margin: 5px 0;
  }
  
  .endpoints-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 20px;
    margin-top: 20px;
  }
  
  .endpoint-card {
    background: #1a1a1a;
    border: 1px solid #444;
    border-radius: 6px;
    padding: 15px;
  }
  
  .endpoint-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  
  .endpoint-header h3 {
    color: #00ffff;
    font-size: 16px;
  }
  
  .endpoint-url {
    font-family: monospace;
    color: #999;
    font-size: 12px;
    margin-bottom: 5px;
  }
  
  .endpoint-desc {
    font-size: 14px;
    margin-bottom: 15px;
  }
  
  .endpoint-result {
    background: #333;
    padding: 10px;
    border-radius: 4px;
    border-left: 4px solid #666;
  }
  
  .endpoint-result.status-success {
    border-left-color: #00ff41;
  }
  
  .endpoint-result.status-error {
    border-left-color: #ff6b6b;
  }
  
  .endpoint-result.status-failed {
    border-left-color: #ff6b6b;
  }
  
  .endpoint-result p {
    margin: 5px 0;
    font-size: 12px;
  }
  
  .endpoint-result details {
    margin-top: 10px;
  }
  
  .endpoint-result pre {
    background: #1a1a1a;
    padding: 10px;
    border-radius: 4px;
    font-size: 11px;
    overflow: auto;
    max-height: 200px;
  }
  
  .error {
    color: #ff6b6b;
  }
  
  .log-controls {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
  }
  
  .log-container {
    background: #1a1a1a;
    border: 1px solid #444;
    border-radius: 6px;
    height: 400px;
    overflow-y: auto;
    padding: 10px;
  }
  
  .log-entry {
    display: flex;
    gap: 15px;
    padding: 5px 0;
    border-bottom: 1px solid #333;
    font-size: 12px;
  }
  
  .log-timestamp {
    color: #999;
    min-width: 80px;
  }
  
  .log-message {
    flex: 1;
  }
  
  .log-info .log-message {
    color: #e0e0e0;
  }
  
  .log-success .log-message {
    color: #00ff41;
  }
  
  .log-error .log-message {
    color: #ff6b6b;
  }
</style>