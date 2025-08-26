// =============================================================================
// DomainVisibility.svelte  
// =============================================================================
<!-- /client/src/components/DomainVisibility.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = {};
  let loading = true;
  let error = null;

  async function fetchData() {
    try {
      const response = await fetch('/api/domain-visibility');
      if (!response.ok) throw new Error('Failed to fetch domain data');
      data = await response.json();
      loading = false;
    } catch (err) {
      error = err.message;
      loading = false;
    }
  }

  onMount(fetchData);

  function getThreatLevel(percentage) {
    if (percentage >= 90) return { color: 'var(--status-good)', status: 'OPTIMAL' };
    if (percentage >= 75) return { color: 'var(--accent-cyan)', status: 'GOOD' };
    if (percentage >= 50) return { color: 'var(--status-warning)', status: 'MODERATE' };
    if (percentage >= 25) return { color: 'var(--accent-magenta)', status: 'POOR' };
    return { color: 'var(--status-critical)', status: 'CRITICAL' };
  }

  function formatNumber(num) {
    return num?.toLocaleString() || '0';
  }
</script>

{#if loading}
  <div class="loading">
    <div class="cyber-spinner"></div>
    <div class="loading-text">ANALYZING DOMAIN VISIBILITY</div>
  </div>
{:else if error}
  <div class="error">
    <div class="error-container">
      <h2 class="error-title">DOMAIN SCAN FAILED</h2>
      <p class="error-message">{error}</p>
      <button class="retry-button" on:click={fetchData}>RETRY SCAN</button>
    </div>
  </div>
{:else}
  <div class="main-header-title" style="margin-bottom: 25px;">
    DOMAIN VISIBILITY ANALYSIS - 1DC & FEAD COVERAGE
  </div>

  <div class="d-grid grid-cols-2 gap-4">
    {#each [['1dc', '1DC DOMAIN'], ['fead', 'FEAD DOMAIN']] as [key, title]}
      {@const domainData = data[key]}
      {@const threat = getThreatLevel(domainData?.overall_coverage || 0)}
      <div class="card" style="padding: 25px; border-color: {threat.color};">
        <div class="header-title" style="color: {threat.color}; margin-bottom: 20px;">
          {title} COVERAGE
        </div>
        
        <div class="text-center" style="margin-bottom: 20px;">
          <div style="font-size: 48px; color: {threat.color}; font-weight: bold;">
            {formatNumber(domainData?.total || 0)}
          </div>
          <div class="text-secondary">Total Assets</div>
        </div>

        <div class="d-flex flex-column gap-3">
          {#each [['Splunk Coverage', domainData?.splunk_coverage || 0], ['CMDB Coverage', domainData?.cmdb_coverage || 0], ['EDR Coverage', domainData?.edr_coverage || 0]] as [label, percentage]}
            <div class="coverage-item">
              <div class="coverage-header">
                <span>{label}</span>
                <span style="color: {getThreatLevel(percentage).color};">{percentage}%</span>
              </div>
              <div class="progress-bar">
                <div class="progress-fill" style="width: {percentage}%; background: {getThreatLevel(percentage).color};"></div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/each}
  </div>
{/if}
