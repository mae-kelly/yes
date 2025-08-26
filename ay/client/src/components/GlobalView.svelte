// client/src/components/GlobalView.svelte
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;

  async function fetchData() {
    try {
      const response = await fetch('/api/global-view');
      if (!response.ok) throw new Error('Failed to fetch global view data');
      data = await response.json();
      loading = false;
    } catch (err) {
      error = err.message;
      loading = false;
    }
  }

  onMount(fetchData);

  function getStatusColor(percentage) {
    if (percentage >= 90) return 'var(--status-good)';
    if (percentage >= 75) return 'var(--status-adequate)';
    if (percentage >= 50) return 'var(--status-warning)';
    return 'var(--status-critical)';
  }

  function getStatusLabel(percentage) {
    if (percentage >= 90) return 'OPTIMAL';
    if (percentage >= 75) return 'ADEQUATE';
    if (percentage >= 50) return 'WARNING';
    return 'CRITICAL';
  }

  function formatNumber(num) {
    return num?.toLocaleString() || '0';
  }
</script>

{#if loading}
  <div class="loading">
    <div class="cyber-spinner"></div>
    <div class="loading-text">
      INITIALIZING SECURITY MATRIX
      <div class="loading-subtext">Scanning all systems...</div>
    </div>
  </div>
{:else if error}
  <div class="error">
    <div class="error-container">
      <h2 class="error-title">SCAN FAILED</h2>
      <p class="error-message">{error}</p>
      <button class="retry-button" on:click={fetchData}>RETRY SCAN</button>
    </div>
  </div>
{:else if data.total_hosts}
  <div class="main-header-title" style="margin-bottom: 2rem;">
    GLOBAL SECURITY POSTURE ANALYSIS
  </div>

  <div class="stats-overview">
    <div class="stat-card primary">
      <div class="stat-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
          <path d="M9 9h6M9 15h6" stroke="currentColor" stroke-width="2"/>
        </svg>
      </div>
      <div class="stat-content">
        <div class="stat-label">TOTAL SYSTEMS</div>
        <div class="stat-value">{formatNumber(data.total_hosts)}</div>
        <div class="stat-detail">Active infrastructure assets</div>
      </div>
    </div>

    {#each Object.entries(data.coverage) as [key, stats]}
      <div class="stat-card">
        <div class="circular-progress">
          <svg width="80" height="80">
            <circle cx="40" cy="40" r="35" stroke="var(--border-dark)" stroke-width="3" fill="none"/>
            <circle 
              cx="40" cy="40" r="35" 
              stroke={getStatusColor(stats.percentage)}
              stroke-width="3" 
              fill="none"
              stroke-dasharray={`${stats.percentage * 2.2} 220`}
              stroke-dashoffset="0"
              transform="rotate(-90 40 40)"
              style="transition: stroke-dasharray 0.6s ease"
            />
          </svg>
          <div class="progress-text">
            <div class="progress-value">{stats.percentage}%</div>
          </div>
        </div>
        <div class="stat-content">
          <div class="stat-label">{key.toUpperCase().replace('_', ' ')}</div>
          <div class="stat-count">{formatNumber(stats.count)} systems</div>
          <div class="stat-status" style="color: {getStatusColor(stats.percentage)}">
            {getStatusLabel(stats.percentage)}
          </div>
        </div>
      </div>
    {/each}
  </div>

  <div class="detailed-metrics">
    <div class="card">
      <h3 class="card-title">COVERAGE ANALYSIS</h3>
      <div class="coverage-grid">
        {#each Object.entries(data.coverage) as [tool, stats]}
          <div class="coverage-item">
            <div class="coverage-header">
              <span class="coverage-name">{tool.toUpperCase().replace('_', ' ')}</span>
              <span class="coverage-percentage" style="color: {getStatusColor(stats.percentage)}">
                {stats.percentage}%
              </span>
            </div>
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                style="width: {stats.percentage}%; background: linear-gradient(90deg, {getStatusColor(stats.percentage)}, {getStatusColor(stats.percentage)}88);"
              ></div>
            </div>
            <div class="coverage-stats">
              <span>{formatNumber(stats.count)} of {formatNumber(data.total_hosts)} systems</span>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <div class="card">
      <h3 class="card-title">SECURITY POSTURE</h3>
      <div class="security-summary">
        <div class="security-score">
          <div class="score-value">
            {Math.round(Object.values(data.coverage).reduce((sum, c) => sum + c.percentage, 0) / Object.values(data.coverage).length)}%
          </div>
          <div class="score-label">Overall Coverage</div>
        </div>
        <div class="security-breakdown">
          <div class="breakdown-item">
            <span class="breakdown-label">Optimal Coverage (90%+)</span>
            <span class="breakdown-value">{Object.values(data.coverage).filter(c => c.percentage >= 90).length}</span>
          </div>
          <div class="breakdown-item">
            <span class="breakdown-label">Needs Attention (<75%)</span>
            <span class="breakdown-value" style="color: var(--status-warning)">
              {Object.values(data.coverage).filter(c => c.percentage < 75).length}
            </span>
          </div>
          <div class="breakdown-item">
            <span class="breakdown-label">Critical Gaps (<50%)</span>
            <span class="breakdown-value" style="color: var(--status-critical)">
              {Object.values(data.coverage).filter(c => c.percentage < 50).length}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}