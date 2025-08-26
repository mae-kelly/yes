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
    if (percentage >= 90) return 'var(--status-secure)';
    if (percentage >= 75) return 'var(--status-adequate)';
    if (percentage >= 50) return 'var(--status-warning)';
    return 'var(--status-critical)';
  }

  function getStatusLabel(percentage) {
    if (percentage >= 90) return 'SECURE';
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
            <circle cx="40" cy="40" r="35" stroke="var(--glass-border)" stroke-width="3" fill="none"/>
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

<style>
  .stats-overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: var(--bg-glass);
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 1.5rem;
    display: flex;
    gap: 1.5rem;
    align-items: center;
    transition: all 0.3s ease;
  }

  .stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0, 217, 255, 0.15);
    border-color: rgba(0, 217, 255, 0.3);
  }

  .stat-card.primary {
    grid-column: span 2;
    background: linear-gradient(135deg, rgba(0, 217, 255, 0.1), rgba(0, 217, 255, 0.05));
    border-color: rgba(0, 217, 255, 0.3);
  }

  .stat-icon {
    color: var(--cyan-primary);
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 217, 255, 0.1);
    border-radius: 12px;
  }

  .circular-progress {
    position: relative;
    width: 80px;
    height: 80px;
  }

  .progress-text {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .progress-value {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .stat-content {
    flex: 1;
  }

  .stat-label {
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-tertiary);
    margin-bottom: 0.25rem;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 600;
    background: linear-gradient(135deg, var(--cyan-primary), var(--cyan-glow));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
  }

  .stat-detail, .stat-count {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
  }

  .stat-status {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.5rem;
  }

  .detailed-metrics {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  .card-title {
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--cyan-primary);
    margin-bottom: 1.5rem;
  }

  .coverage-grid {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .coverage-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .coverage-name {
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
  }

  .coverage-percentage {
    font-size: 0.875rem;
    font-weight: 600;
  }

  .coverage-stats {
    font-size: 0.75rem;
    color: var(--text-tertiary);
    margin-top: 0.5rem;
  }

  .security-summary {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 2rem;
  }

  .security-score {
    text-align: center;
    padding: 1.5rem;
    background: linear-gradient(135deg, rgba(0, 217, 255, 0.1), transparent);
    border-radius: 12px;
    border: 1px solid rgba(0, 217, 255, 0.2);
  }

  .score-value {
    font-size: 2.5rem;
    font-weight: 600;
    background: linear-gradient(135deg, var(--cyan-primary), var(--cyan-glow));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .score-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-tertiary);
    margin-top: 0.5rem;
  }

  .security-breakdown {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    justify-content: center;
  }

  .breakdown-item {
    display: flex;
    justify-content: space-between;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 8px;
    border: 1px solid var(--glass-border);
  }

  .breakdown-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
  }

  .breakdown-value {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  @media (max-width: 1024px) {
    .stat-card.primary {
      grid-column: span 1;
    }
    
    .detailed-metrics {
      grid-template-columns: 1fr;
    }
  }
</style>