<script>
  import { onMount } from 'svelte';
  
  let selectedView = 'global';
  let serverStatus = 'checking';
  let currentData = {};
  let matrixChars = [];
  let terminalOutput = [];
  
  const views = [
    { key: 'global', label: 'GLOBAL_COVERAGE', endpoint: '/api/global-view' },
    { key: 'domains', label: 'DOMAIN_ANALYSIS', endpoint: '/api/domain-visibility' },
    { key: 'regional', label: 'REGIONAL_MATRIX', endpoint: '/api/regional-country-view' },
    { key: 'organizational', label: 'ORG_METRICS', endpoint: '/api/bu-application-view' },
    { key: 'systems', label: 'SYSTEM_CLASS', endpoint: '/api/system-classification' },
    { key: 'security', label: 'SECURITY_GRID', endpoint: '/api/security-control-coverage' },
    { key: 'logging', label: 'LOG_COMPLIANCE', endpoint: '/api/logging-compliance-gso-splunk' },
    { key: 'priority', label: 'LOG_PRIORITY', endpoint: '/api/log-type-priority' }
  ];
  
  let currentViewData = views[0];
  
  function generateMatrixChars() {
    const chars = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    matrixChars = [];
    
    for (let i = 0; i < 150; i++) {
      matrixChars.push({
        char: chars[Math.floor(Math.random() * chars.length)],
        x: Math.random() * 100,
        y: Math.random() * 100,
        speed: Math.random() * 1.5 + 0.3,
        opacity: Math.random() * 0.8 + 0.2
      });
    }
  }
  
  function animateMatrix() {
    matrixChars = matrixChars.map(char => ({
      ...char,
      y: (char.y + char.speed) % 100,
      char: Math.random() > 0.98 ? 
        'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'[Math.floor(Math.random() * 100)] : 
        char.char,
      opacity: Math.random() > 0.95 ? Math.random() * 0.8 + 0.2 : char.opacity
    }));
  }
  
  async function checkServerStatus() {
    try {
      const response = await fetch('/api/health');
      if (response.ok) {
        const data = await response.json();
        serverStatus = 'connected';
        addTerminalLine(`> MATRIX_CONNECTION_ESTABLISHED`);
        addTerminalLine(`> HOSTS_IN_SYSTEM: ${data.total_hosts}`);
        addTerminalLine(`> DETECTION_PROTOCOLS_ACTIVE`);
      } else {
        serverStatus = 'error';
        addTerminalLine(`> CONNECTION_ERROR`);
      }
    } catch (error) {
      serverStatus = 'disconnected';
      addTerminalLine(`> MATRIX_UNREACHABLE`);
    }
  }
  
  async function loadViewData(viewKey) {
    const view = views.find(v => v.key === viewKey);
    if (!view) return;
    
    addTerminalLine(`> ACCESSING ${view.label}_PROTOCOL...`);
    
    try {
      const response = await fetch(view.endpoint);
      if (response.ok) {
        currentData = await response.json();
        currentViewData = view;
        addTerminalLine(`> DATA_MATRIX_LOADED: ${Object.keys(currentData).length} DIMENSIONS`);
      } else {
        addTerminalLine(`> ACCESS_DENIED: ERROR_${response.status}`);
      }
    } catch (error) {
      addTerminalLine(`> DATA_STREAM_INTERRUPTED`);
    }
  }
  
  function addTerminalLine(text) {
    terminalOutput = [...terminalOutput.slice(-8), text];
  }
  
  function selectView(viewKey) {
    if (selectedView === viewKey) return;
    selectedView = viewKey;
    loadViewData(viewKey);
  }
  
  function getThreatLevel(percentage) {
    if (percentage >= 90) return { color: '#00ff41', status: 'OPTIMAL', glow: '0 0 20px #00ff41' };
    if (percentage >= 75) return { color: '#00ffff', status: 'SECURE', glow: '0 0 20px #00ffff' };
    if (percentage >= 50) return { color: '#ffff00', status: 'CAUTION', glow: '0 0 20px #ffff00' };
    if (percentage >= 25) return { color: '#ff9900', status: 'WARNING', glow: '0 0 20px #ff9900' };
    return { color: '#ff0066', status: 'CRITICAL', glow: '0 0 20px #ff0066' };
  }
  
  function formatNumber(num) {
    return num?.toLocaleString() || '0';
  }
  
  onMount(() => {
    generateMatrixChars();
    checkServerStatus();
    loadViewData('global');
    
    const matrixInterval = setInterval(animateMatrix, 100);
    const statusInterval = setInterval(() => {
      addTerminalLine(`> ${new Date().toISOString().slice(11,19)} STATUS_CHECK`);
    }, 15000);
    
    return () => {
      clearInterval(matrixInterval);
      clearInterval(statusInterval);
    };
  });
</script>

<div class="matrix-container">
  <!-- Matrix Rain Background -->
  <div class="matrix-rain">
    {#each matrixChars as char}
      <div class="matrix-char" style="left: {char.x}%; top: {char.y}%; opacity: {char.opacity};">{char.char}</div>
    {/each}
  </div>
  
  <!-- Scanlines Effect -->
  <div class="scanlines"></div>
  
  <!-- Main Interface -->
  <div class="interface">
    <!-- Header -->
    <header class="matrix-header">
      <div class="system-title">
        <span class="matrix-text">UNIVERSAL_CMDB_MATRIX</span>
        <div class="subtitle">REAL_TIME_CYBERSECURITY_GRID</div>
      </div>
      
      <div class="system-status">
        <div class="status-indicator" class:online={serverStatus === 'connected'} class:offline={serverStatus !== 'connected'}>
          <span class="status-dot"></span>
          {serverStatus === 'connected' ? 'MATRIX_ONLINE' : serverStatus === 'checking' ? 'CONNECTING' : 'OFFLINE'}
        </div>
        <div class="timestamp">{new Date().toISOString().slice(0,19)}Z</div>
      </div>
    </header>
    
    <!-- Navigation Matrix -->
    <nav class="nav-matrix">
      {#each views as view}
        <button 
          class="nav-node" 
          class:active={selectedView === view.key}
          on:click={() => selectView(view.key)}
        >
          <div class="node-border"></div>
          <span class="node-text">{view.label}</span>
        </button>
      {/each}
    </nav>
    
    <!-- Terminal Output -->
    <div class="terminal-output">
      {#each terminalOutput as line}
        <div class="terminal-line">{line}</div>
      {/each}
    </div>
    
    <!-- Main Data Display -->
    <main class="data-matrix">
      {#if serverStatus === 'disconnected'}
        <div class="error-matrix">
          <div class="error-code">MATRIX_DISCONNECTED</div>
          <div class="error-msg">UNABLE_TO_ACCESS_CYBERSECURITY_GRID</div>
          <button class="retry-btn" on:click={checkServerStatus}>RECONNECT_TO_MATRIX</button>
        </div>
        
      {:else if selectedView === 'global'}
        <div class="metrics-grid">
          <div class="grid-title">GLOBAL_COVERAGE_ANALYSIS</div>
          
          {#if currentData.coverage}
            <div class="coverage-matrix">
              <div class="total-hosts">
                TOTAL_ENTITIES: <span class="highlight">{formatNumber(currentData.total_hosts)}</span>
              </div>
              
              <div class="metrics-grid-container">
                {#each Object.entries(currentData.coverage) as [key, metric]}
                  {@const threat = getThreatLevel(metric.percentage)}
                  <div class="metric-cell" style="border-color: {threat.color};">
                    <div class="cell-header" style="color: {threat.color}; text-shadow: {threat.glow};">
                      {key.toUpperCase().replace(/_/g, '_')}
                    </div>
                    <div class="cell-value" style="color: {threat.color}; text-shadow: {threat.glow};">
                      {formatNumber(metric.count)}
                    </div>
                    <div class="cell-percentage" style="color: {threat.color};">
                      {metric.percentage}%
                    </div>
                    <div class="cell-status" style="color: {threat.color};">
                      {threat.status}
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        </div>
        
      {:else if selectedView === 'domains'}
        <div class="metrics-grid">
          <div class="grid-title">DOMAIN_ANALYSIS_MATRIX</div>
          
          <div class="domain-analysis">
            {#each ['1dc', 'fead'] as domain}
              {#if currentData[domain]}
                {@const domainData = currentData[domain]}
                {@const threat = getThreatLevel(domainData.overall_coverage)}
                <div class="domain-block" style="border-color: {threat.color};">
                  <div class="domain-title" style="color: {threat.color}; text-shadow: {threat.glow};">
                    {domain.toUpperCase()}_DOMAIN
                  </div>
                  <div class="domain-total">
                    HOSTS: <span style="color: {threat.color};">{formatNumber(domainData.total)}</span>
                  </div>
                  
                  <div class="coverage-bars">
                    {#each [['SPLUNK', domainData.splunk_coverage], ['CMDB', domainData.cmdb_coverage], ['CROWDSTRIKE', domainData.crowdstrike_coverage]] as [tool, percentage]}
                      {@const toolThreat = getThreatLevel(percentage)}
                      <div class="coverage-bar">
                        <span class="bar-label">{tool}</span>
                        <div class="bar-container">
                          <div class="bar-fill" style="width: {percentage}%; background: {toolThreat.color}; box-shadow: {toolThreat.glow};"></div>
                        </div>
                        <span class="bar-value" style="color: {toolThreat.color};">{percentage}%</span>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            {/each}
          </div>
        </div>
        
      {:else if selectedView === 'regional'}
        <div class="metrics-grid">
          <div class="grid-title">REGIONAL_COVERAGE_MATRIX</div>
          
          {#if currentData.regions}
            <div class="regional-grid">
              {#each Object.entries(currentData.regions) as [region, stats]}
                {@const threat = getThreatLevel(stats.overall_coverage)}
                <div class="region-cell" style="border-color: {threat.color};">
                  <div class="region-header" style="color: {threat.color}; text-shadow: {threat.glow};">
                    {region.toUpperCase()}
                  </div>
                  <div class="region-count">{formatNumber(stats.total)} HOSTS</div>
                  <div class="mini-bars">
                    <div class="mini-bar" style="width: {stats.cmdb_coverage}%; background: {getThreatLevel(stats.cmdb_coverage).color};"></div>
                    <div class="mini-bar" style="width: {stats.splunk_coverage}%; background: {getThreatLevel(stats.splunk_coverage).color};"></div>
                    <div class="mini-bar" style="width: {stats.crowdstrike_coverage}%; background: {getThreatLevel(stats.crowdstrike_coverage).color};"></div>
                  </div>
                  <div class="region-status" style="color: {threat.color};">
                    {threat.status}
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
        
      {:else if selectedView === 'security'}
        <div class="metrics-grid">
          <div class="grid-title">SECURITY_CONTROL_MATRIX</div>
          
          {#if currentData.individual_coverage}
            <div class="security-matrix">
              <div class="matrix-row">
                {#each Object.entries(currentData.individual_coverage) as [tool, data]}
                  {@const threat = getThreatLevel(data.percentage)}
                  <div class="security-cell" style="border-color: {threat.color};">
                    <div class="tool-name" style="color: {threat.color}; text-shadow: {threat.glow};">
                      {tool.toUpperCase()}
                    </div>
                    <div class="tool-count" style="color: {threat.color};">
                      {formatNumber(data.count)}
                    </div>
                    <div class="tool-percentage" style="color: {threat.color};">
                      {data.percentage}%
                    </div>
                  </div>
                {/each}
              </div>
              
              {#if currentData.overlap_analysis}
                <div class="overlap-title">OVERLAP_ANALYSIS</div>
                <div class="overlap-grid">
                  {#each Object.entries(currentData.overlap_analysis) as [overlap, data]}
                    {@const threat = getThreatLevel(data.percentage)}
                    <div class="overlap-cell" style="border-color: {threat.color};">
                      <div class="overlap-name" style="color: {threat.color};">
                        {overlap.toUpperCase().replace(/_/g, '_')}
                      </div>
                      <div class="overlap-value" style="color: {threat.color};">
                        {formatNumber(data.count)} ({data.percentage}%)
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          {/if}
        </div>
        
      {:else}
        <div class="loading-matrix">
          <div class="loading-text">LOADING_DATA_STREAM...</div>
          <div class="loading-bars">
            <div class="loading-bar"></div>
            <div class="loading-bar"></div>
            <div class="loading-bar"></div>
          </div>
        </div>
      {/if}
    </main>
  </div>
</div>

<style>
  .matrix-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: #000000;
    color: #00ff41;
    font-family: 'Courier New', monospace;
    overflow: hidden;
  }
  
  .matrix-rain {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
    pointer-events: none;
  }
  
  .matrix-char {
    position: absolute;
    color: #00ff41;
    font-size: 12px;
    font-weight: bold;
    text-shadow: 0 0 5px #00ff41;
  }
  
  .scanlines {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0, 255, 65, 0.03) 2px,
      rgba(0, 255, 65, 0.03) 4px
    );
    z-index: 2;
    pointer-events: none;
  }
  
  .interface {
    position: relative;
    z-index: 3;
    height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 10px;
    background: rgba(0, 0, 0, 0.8);
  }
  
  .matrix-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #00ff41;
    padding-bottom: 10px;
    margin-bottom: 15px;
  }
  
  .matrix-text {
    font-size: 24px;
    font-weight: bold;
    text-shadow: 0 0 10px #00ff41;
    letter-spacing: 2px;
  }
  
  .subtitle {
    font-size: 12px;
    color: #00ffff;
    letter-spacing: 1px;
  }
  
  .system-status {
    text-align: right;
  }
  
  .status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: bold;
  }
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ff0066;
  }
  
  .status-indicator.online .status-dot {
    background: #00ff41;
    box-shadow: 0 0 10px #00ff41;
  }
  
  .timestamp {
    font-size: 10px;
    color: #888;
    margin-top: 5px;
  }
  
  .nav-matrix {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 15px;
  }
  
  .nav-node {
    position: relative;
    background: rgba(0, 255, 65, 0.1);
    border: 1px solid #00ff41;
    color: #00ff41;
    padding: 8px;
    font-size: 11px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s;
    font-family: 'Courier New', monospace;
  }
  
  .nav-node:hover {
    background: rgba(0, 255, 65, 0.2);
    box-shadow: 0 0 15px rgba(0, 255, 65, 0.5);
  }
  
  .nav-node.active {
    background: rgba(0, 255, 65, 0.3);
    box-shadow: 0 0 20px rgba(0, 255, 65, 0.8);
  }
  
  .node-text {
    position: relative;
    z-index: 2;
  }
  
  .terminal-output {
    height: 120px;
    background: rgba(0, 0, 0, 0.9);
    border: 1px solid #00ff41;
    padding: 8px;
    margin-bottom: 15px;
    overflow-y: auto;
    font-size: 11px;
  }
  
  .terminal-line {
    color: #00ff41;
    margin-bottom: 2px;
    text-shadow: 0 0 5px #00ff41;
  }
  
  .data-matrix {
    flex: 1;
    background: rgba(0, 0, 0, 0.9);
    border: 1px solid #00ff41;
    padding: 15px;
    overflow-y: auto;
  }
  
  .metrics-grid {
    width: 100%;
  }
  
  .grid-title {
    font-size: 18px;
    font-weight: bold;
    text-align: center;
    margin-bottom: 20px;
    color: #00ffff;
    text-shadow: 0 0 10px #00ffff;
    letter-spacing: 2px;
  }
  
  .total-hosts {
    text-align: center;
    font-size: 16px;
    margin-bottom: 20px;
  }
  
  .highlight {
    color: #00ffff;
    font-weight: bold;
    text-shadow: 0 0 10px #00ffff;
  }
  
  .metrics-grid-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
  }
  
  .metric-cell {
    background: rgba(0, 0, 0, 0.8);
    border: 2px solid;
    padding: 15px;
    text-align: center;
  }
  
  .cell-header {
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 8px;
  }
  
  .cell-value {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 5px;
  }
  
  .cell-percentage {
    font-size: 14px;
    margin-bottom: 5px;
  }
  
  .cell-status {
    font-size: 11px;
    font-weight: bold;
  }
  
  .domain-analysis {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
  
  .domain-block {
    background: rgba(0, 0, 0, 0.8);
    border: 2px solid;
    padding: 20px;
  }
  
  .domain-title {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 10px;
    text-align: center;
  }
  
  .domain-total {
    text-align: center;
    margin-bottom: 20px;
    font-size: 14px;
  }
  
  .coverage-bars {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .coverage-bar {
    display: grid;
    grid-template-columns: 80px 1fr 50px;
    gap: 10px;
    align-items: center;
    font-size: 11px;
  }
  
  .bar-container {
    height: 12px;
    background: rgba(255, 255, 255, 0.1);
    position: relative;
  }
  
  .bar-fill {
    height: 100%;
    transition: all 0.3s;
  }
  
  .regional-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 15px;
  }
  
  .region-cell {
    background: rgba(0, 0, 0, 0.8);
    border: 2px solid;
    padding: 15px;
    text-align: center;
  }
  
  .region-header {
    font-size: 14px;
    font-weight: bold;
    margin-bottom: 8px;
  }
  
  .region-count {
    font-size: 12px;
    margin-bottom: 10px;
  }
  
  .mini-bars {
    display: flex;
    flex-direction: column;
    gap: 3px;
    margin-bottom: 10px;
  }
  
  .mini-bar {
    height: 4px;
    background: #00ff41;
  }
  
  .security-matrix {
    width: 100%;
  }
  
  .matrix-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    margin-bottom: 30px;
  }
  
  .security-cell {
    background: rgba(0, 0, 0, 0.8);
    border: 2px solid;
    padding: 15px;
    text-align: center;
  }
  
  .tool-name {
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 8px;
  }
  
  .tool-count {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 5px;
  }
  
  .overlap-title {
    font-size: 14px;
    font-weight: bold;
    margin-bottom: 15px;
    color: #ffff00;
    text-align: center;
  }
  
  .overlap-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
  }
  
  .overlap-cell {
    background: rgba(0, 0, 0, 0.8);
    border: 2px solid;
    padding: 12px;
    text-align: center;
  }
  
  .overlap-name {
    font-size: 11px;
    font-weight: bold;
    margin-bottom: 5px;
  }
  
  .error-matrix {
    text-align: center;
    padding: 50px;
  }
  
  .error-code {
    font-size: 24px;
    color: #ff0066;
    font-weight: bold;
    margin-bottom: 20px;
    text-shadow: 0 0 10px #ff0066;
  }
  
  .error-msg {
    font-size: 14px;
    margin-bottom: 30px;
  }
  
  .retry-btn {
    background: rgba(255, 0, 102, 0.2);
    border: 2px solid #ff0066;
    color: #ff0066;
    padding: 12px 24px;
    font-family: 'Courier New', monospace;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .retry-btn:hover {
    background: rgba(255, 0, 102, 0.3);
    box-shadow: 0 0 15px #ff0066;
  }
  
  .loading-matrix {
    text-align: center;
    padding: 50px;
  }
  
  .loading-text {
    font-size: 16px;
    margin-bottom: 20px;
    color: #00ffff;
  }
  
  .loading-bars {
    display: flex;
    justify-content: center;
    gap: 5px;
  }
  
  .loading-bar {
    width: 4px;
    height: 20px;
    background: #00ff41;
    animation: pulse 1.5s infinite;
  }
  
  .loading-bar:nth-child(2) {
    animation-delay: 0.5s;
  }
  
  .loading-bar:nth-child(3) {
    animation-delay: 1s;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 1; }
  }
  
  /* Responsive adjustments */
  @media (max-width: 1024px) {
    .nav-matrix {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .matrix-row {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .domain-analysis {
      grid-template-columns: 1fr;
    }
  }
  
  @media (max-width: 768px) {
    .matrix-text {
      font-size: 18px;
    }
    
    .nav-matrix {
      grid-template-columns: 1fr;
    }
    
    .metrics-grid-container {
      grid-template-columns: 1fr;
    }
  }
</style>