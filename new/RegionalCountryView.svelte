<!-- /src/components/RegionalCountryView.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = null;
  let loading = true;
  let error = null;
  let viewMode = 'regions';
  let selectedLocation = null;

  async function fetchData() {
    try {
      const response = await fetch('http://localhost:5000/api/regional-country-view');
      if (!response.ok) throw new Error('Failed to fetch regional data');
      data = await response.json();
      loading = false;
    } catch (err) {
      error = err.message;
      loading = false;
    }
  }

  onMount(fetchData);

  function getThreatLevel(percentage) {
    if (percentage >= 90) return { color: 'var(--matrix-primary)', status: 'OPTIMAL' };
    if (percentage >= 75) return { color: 'var(--neural-cyan)', status: 'GOOD' };
    if (percentage >= 50) return { color: 'var(--toxic-yellow)', status: 'MODERATE' };
    if (percentage >= 25) return { color: 'var(--plasma-magenta)', status: 'POOR' };
    return { color: 'var(--danger-crimson)', status: 'CRITICAL' };
  }

  function formatNumber(num) {
    return num?.toLocaleString() || '0';
  }

  function standardizeRegion(region) {
    const regionLower = region?.toLowerCase() || '';
    if (regionLower.includes('north america') || regionLower.includes('us') || regionLower.includes('united states') || regionLower.includes('canada')) {
      return 'North America';
    } else if (regionLower.includes('latam') || regionLower.includes('latin america') || regionLower.includes('south america')) {
      return 'LATAM';
    } else if (regionLower.includes('emea') || regionLower.includes('europe') || regionLower.includes('middle east') || regionLower.includes('africa')) {
      return 'EMEA';
    } else if (regionLower.includes('apac') || regionLower.includes('asia') || regionLower.includes('pacific')) {
      return 'APAC';
    }
    return region;
  }

  function getStandardizedRegions() {
    if (!data?.regions) return {};
    const standardized = {};
    
    Object.entries(data.regions).forEach(([region, stats]) => {
      const stdRegion = standardizeRegion(region);
      if (!standardized[stdRegion]) {
        standardized[stdRegion] = {
          total: 0,
          splunk: 0,
          cmdb: 0,
          edr: 0
        };
      }
      standardized[stdRegion].total += stats.total;
      standardized[stdRegion].splunk += stats.splunk;
      standardized[stdRegion].cmdb += stats.cmdb;
      standardized[stdRegion].edr += stats.edr;
    });
    
    Object.values(standardized).forEach(stats => {
      if (stats.total > 0) {
        stats.splunk_coverage = Math.round((stats.splunk / stats.total) * 100 * 10) / 10;
        stats.cmdb_coverage = Math.round((stats.cmdb / stats.total) * 100 * 10) / 10;
        stats.edr_coverage = Math.round((stats.edr / stats.total) * 100 * 10) / 10;
        stats.overall_coverage = Math.round(((stats.splunk + stats.cmdb + stats.edr) / (3 * stats.total)) * 100 * 10) / 10;
      }
    });
    
    return standardized;
  }

  function getTopCountries(limit = 15) {
    if (!data?.countries) return [];
    return Object.entries(data.countries)
      .map(([country, stats]) => ({
        country,
        ...stats,
        splunk_coverage: stats.total > 0 ? Math.round((stats.splunk / stats.total) * 100 * 10) / 10 : 0,
        cmdb_coverage: stats.total > 0 ? Math.round((stats.cmdb / stats.total) * 100 * 10) / 10 : 0,
        edr_coverage: stats.total > 0 ? Math.round((stats.edr / stats.total) * 100 * 10) / 10 : 0,
        overall_coverage: stats.total > 0 ? Math.round(((stats.splunk + stats.cmdb + stats.edr) / (3 * stats.total)) * 100 * 10) / 10 : 0
      }))
      .sort((a, b) => b.total - a.total)
      .slice(0, limit);
  }

  function getTopDatacenters(limit = 12) {
    if (!data?.datacenters) return [];
    return Object.entries(data.datacenters)
      .map(([dc, stats]) => ({
        datacenter: dc,
        ...stats,
        splunk_coverage: stats.total > 0 ? Math.round((stats.splunk / stats.total) * 100 * 10) / 10 : 0,
        cmdb_coverage: stats.total > 0 ? Math.round((stats.cmdb / stats.total) * 100 * 10) / 10 : 0,
        edr_coverage: stats.total > 0 ? Math.round((stats.edr / stats.total) * 100 * 10) / 10 : 0,
        overall_coverage: stats.total > 0 ? Math.round(((stats.splunk + stats.cmdb + stats.edr) / (3 * stats.total)) * 100 * 10) / 10 : 0
      }))
      .filter(item => item.total > 5)
      .sort((a, b) => b.total - a.total)
      .slice(0, limit);
  }
</script>

{#if loading}
  <div class="quantum-loader">
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
  </div>
  <div style="text-align: center; margin-top: 30px; color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px;">
    SCANNING GLOBAL LOCATIONS...
  </div>
{:else if error}
  <div class="dystopia-modal active">
    <h2 style="color: var(--danger-crimson);">GEOLOCATION SCAN FAILED</h2>
    <p style="color: var(--text-muted);">{error}</p>
    <button class="quantum-btn danger" on:click={fetchData}>RETRY SCAN</button>
  </div>
{:else if data}

  <!-- AO1 Requirement: Regional and Country view - Visibility statement on % of visibility by "location" -->
  <div class="glitch-text" data-text="REGIONAL & COUNTRY VISIBILITY ANALYSIS" style="font-size: 20px; font-weight: bold; letter-spacing: 3px; margin-bottom: 25px;">
    REGIONAL & COUNTRY VISIBILITY ANALYSIS
  </div>

  <!-- View Mode Controls -->
  <div style="display: flex; gap: 10px; margin-bottom: 25px;">
    <button class="quantum-btn {viewMode === 'regions' ? 'active' : ''}" on:click={() => viewMode = 'regions'}>
      GLOBAL REGIONS
    </button>
    <button class="quantum-btn {viewMode === 'countries' ? 'active' : ''}" on:click={() => viewMode = 'countries'}>
      COUNTRY BREAKDOWN
    </button>
    <button class="quantum-btn {viewMode === 'datacenters' ? 'active' : ''}" on:click={() => viewMode = 'datacenters'}>
      DATA CENTERS
    </button>
    <button class="quantum-btn {viewMode === 'cloud' ? 'active' : ''}" on:click={() => viewMode = 'cloud'}>
      CLOUD REGIONS
    </button>
  </div>

  {#if viewMode === 'regions'}
    <!-- Regional Coverage Matrix -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin-bottom: 30px;">
      {#each Object.entries(getStandardizedRegions()) as [region, stats]}
        {@const regionThreat = getThreatLevel(stats.overall_coverage)}
        <div 
          class="holo-card-3d neural-link" 
          style="padding: 25px; border-color: {regionThreat.color}; cursor: pointer; transition: all 0.3s;"
          on:click={() => selectedLocation = selectedLocation === region ? null : region}
        >
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h4 style="color: var(--neural-cyan); font-size: 16px; font-weight: bold; letter-spacing: 1px;">
              {region}
            </h4>
            <div style="color: {regionThreat.color}; font-size: 24px; font-weight: bold; text-shadow: 0 0 15px {regionThreat.color};">
              {stats.overall_coverage}%
            </div>
          </div>

          <div style="color: var(--text-muted); font-size: 13px; margin-bottom: 20px; text-align: center;">
            {formatNumber(stats.total)} Total Assets Under Management
          </div>

          <div style="display: grid; gap: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: rgba(0, 0, 0, 0.4); border-left: 3px solid {getThreatLevel(stats.splunk_coverage).color};">
              <span style="color: var(--text-muted); font-size: 11px;">Splunk Logging Coverage:</span>
              <span style="color: {getThreatLevel(stats.splunk_coverage).color}; font-size: 12px; font-weight: bold;">
                {stats.splunk_coverage}% ({formatNumber(stats.splunk)} assets)
              </span>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: rgba(0, 0, 0, 0.4); border-left: 3px solid {getThreatLevel(stats.cmdb_coverage).color};">
              <span style="color: var(--text-muted); font-size: 11px;">CMDB Documentation:</span>
              <span style="color: {getThreatLevel(stats.cmdb_coverage).color}; font-size: 12px; font-weight: bold;">
                {stats.cmdb_coverage}% ({formatNumber(stats.cmdb)} assets)
              </span>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: rgba(0, 0, 0, 0.4); border-left: 3px solid {getThreatLevel(stats.edr_coverage).color};">
              <span style="color: var(--text-muted); font-size: 11px;">EDR Protection:</span>
              <span style="color: {getThreatLevel(stats.edr_coverage).color}; font-size: 12px; font-weight: bold;">
                {stats.edr_coverage}% ({formatNumber(stats.edr)} assets)
              </span>
            </div>
          </div>

          <div style="margin-top: 15px; padding: 10px; background: rgba(0, 0, 0, 0.6); border: 1px solid {regionThreat.color}; text-align: center;">
            <div style="color: {regionThreat.color}; font-size: 12px; font-weight: bold; letter-spacing: 1px;">
              REGIONAL STATUS: {regionThreat.status}
            </div>
          </div>
        </div>
      {/each}
    </div>

  {:else if viewMode === 'countries'}
    <!-- Country-level Analysis -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        COUNTRY-LEVEL VISIBILITY ASSESSMENT
      </h3>
      
      <div style="max-height: 500px; overflow-y: auto;">
        <table style="width: 100%; border-collapse: collapse;">
          <thead>
            <tr style="border-bottom: 2px solid var(--matrix-primary);">
              <th style="text-align: left; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">COUNTRY</th>
              <th style="text-align: center; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">ASSETS</th>
              <th style="text-align: center; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">SPLUNK</th>
              <th style="text-align: center; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">CMDB</th>
              <th style="text-align: center; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">EDR</th>
              <th style="text-align: center; padding: 12px; color: var(--neural-cyan); font-size: 12px; position: sticky; top: 0; background: rgba(0, 0, 0, 0.9);">OVERALL</th>
            </tr>
          </thead>
          <tbody>
            {#each getTopCountries(25) as country}
              {@const countryThreat = getThreatLevel(country.overall_coverage)}
              <tr 
                style="border-bottom: 1px solid rgba(0, 255, 65, 0.1); cursor: pointer; transition: all 0.3s; {selectedLocation === country.country ? `background: ${countryThreat.color}20; border-left: 4px solid ${countryThreat.color};` : ''}"
                class="neural-link"
                on:click={() => selectedLocation = selectedLocation === country.country ? null : country.country}
              >
                <td style="padding: 15px; color: var(--matrix-primary); font-size: 11px; font-weight: bold;">
                  {country.country.toUpperCase()}
                </td>
                <td style="padding: 15px; text-align: center; color: var(--neural-cyan); font-size: 11px;">
                  {formatNumber(country.total)}
                </td>
                <td style="padding: 15px; text-align: center; color: {getThreatLevel(country.splunk_coverage).color}; font-size: 11px; font-weight: bold;">
                  {country.splunk_coverage}%
                </td>
                <td style="padding: 15px; text-align: center; color: {getThreatLevel(country.cmdb_coverage).color}; font-size: 11px; font-weight: bold;">
                  {country.cmdb_coverage}%
                </td>
                <td style="padding: 15px; text-align: center; color: {getThreatLevel(country.edr_coverage).color}; font-size: 11px; font-weight: bold;">
                  {country.edr_coverage}%
                </td>
                <td style="padding: 15px; text-align: center; color: {countryThreat.color}; font-size: 12px; font-weight: bold;">
                  {country.overall_coverage}%
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

  {:else if viewMode === 'datacenters'}
    <!-- Data Center Analysis -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        DATA CENTER VISIBILITY MATRIX
      </h3>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px;">
        {#each getTopDatacenters() as dc}
          {@const dcThreat = getThreatLevel(dc.overall_coverage)}
          <div 
            class="holo-card-3d neural-link"
            style="padding: 20px; border-color: {dcThreat.color}; cursor: pointer; transition: all 0.3s;"
            on:click={() => selectedLocation = selectedLocation === dc.datacenter ? null : dc.datacenter}
          >
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
              <h4 style="color: var(--neural-cyan); font-size: 13px; font-weight: bold; letter-spacing: 1px; word-break: break-all;">
                {dc.datacenter.toUpperCase()}
              </h4>
              <div style="color: {dcThreat.color}; font-size: 20px; font-weight: bold;">
                {dc.overall_coverage}%
              </div>
            </div>

            <div style="color: var(--text-muted); font-size: 12px; margin-bottom: 15px; text-align: center;">
              {formatNumber(dc.total)} Assets
            </div>

            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; text-align: center; font-size: 10px;">
              <div>
                <div style="color: {getThreatLevel(dc.splunk_coverage).color}; font-weight: bold;">{dc.splunk_coverage}%</div>
                <div style="color: var(--text-muted);">SPLUNK</div>
              </div>
              <div>
                <div style="color: {getThreatLevel(dc.cmdb_coverage).color}; font-weight: bold;">{dc.cmdb_coverage}%</div>
                <div style="color: var(--text-muted);">CMDB</div>
              </div>
              <div>
                <div style="color: {getThreatLevel(dc.edr_coverage).color}; font-weight: bold;">{dc.edr_coverage}%</div>
                <div style="color: var(--text-muted);">EDR</div>
              </div>
            </div>

            <div style="margin-top: 15px; text-align: center;">
              <div style="color: {dcThreat.color}; font-size: 11px; font-weight: bold; letter-spacing: 1px;">
                {dcThreat.status}
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>

  {:else if viewMode === 'cloud'}
    <!-- Cloud Region Analysis -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        CLOUD REGION COVERAGE MATRIX
      </h3>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px;">
        {#each Object.entries(data.cloud_regions || {}).filter(([_, stats]) => stats.total > 1).sort((a, b) => b[1].total - a[1].total).slice(0, 20) as [cloudRegion, stats]}
          {@const cloudThreat = getThreatLevel(stats.overall_coverage)}
          <div style="background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), {cloudThreat.color}10); border: 1px solid {cloudThreat.color}; padding: 15px; border-radius: 6px;">
            <div style="color: var(--neural-cyan); font-size: 12px; font-weight: bold; margin-bottom: 8px; word-break: break-all;">
              {cloudRegion.toUpperCase()}
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
              <span style="color: var(--text-muted); font-size: 11px;">Assets:</span>
              <span style="color: var(--neural-cyan); font-size: 11px; font-weight: bold;">{formatNumber(stats.total)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
              <span style="color: var(--text-muted); font-size: 10px;">Overall Coverage:</span>
              <span style="color: {cloudThreat.color}; font-size: 12px; font-weight: bold;">{stats.overall_coverage}%</span>
            </div>
            <div style="background: rgba(0, 0, 0, 0.6); height: 4px; border-radius: 2px; overflow: hidden;">
              <div style="background: {cloudThreat.color}; height: 100%; width: {stats.overall_coverage}%; transition: all 0.8s; box-shadow: 0 0 8px {cloudThreat.color};"></div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Selected Location Details -->
  {#if selectedLocation}
    <div class="dystopia-modal active" style="max-width: 700px;">
      <h2 style="color: var(--matrix-primary); font-size: 18px; letter-spacing: 2px; margin-bottom: 20px;">
        LOCATION ANALYSIS: {selectedLocation.toUpperCase()}
      </h2>
      
      {#if viewMode === 'regions' && getStandardizedRegions()[selectedLocation]}
        {@const locationData = getStandardizedRegions()[selectedLocation]}
        {@const locationThreat = getThreatLevel(locationData.overall_coverage)}
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px;">
          <div style="text-align: center;">
            <div style="color: var(--neural-cyan); font-size: 20px; font-weight: bold;">{formatNumber(locationData.total)}</div>
            <div style="color: var(--text-muted); font-size: 11px;">TOTAL ASSETS</div>
          </div>
          <div style="text-align: center;">
            <div style="color: {locationThreat.color}; font-size: 20px; font-weight: bold;">{locationData.overall_coverage}%</div>
            <div style="color: var(--text-muted); font-size: 11px;">COVERAGE</div>
          </div>
          <div style="text-align: center;">
            <div style="color: {locationThreat.color}; font-size: 16px; font-weight: bold;">{locationThreat.status}</div>
            <div style="color: var(--text-muted); font-size: 11px;">STATUS</div>
          </div>
          <div style="text-align: center;">
            <div style="color: {100 - locationData.overall_coverage > 30 ? 'var(--danger-crimson)' : 'var(--matrix-primary)'}; font-size: 20px; font-weight: bold;">
              {formatNumber(locationData.total - Math.round((locationData.splunk + locationData.cmdb + locationData.edr) / 3))}
            </div>
            <div style="color: var(--text-muted); font-size: 11px;">BLIND SPOTS</div>
          </div>
        </div>
        
        <div style="display: grid; gap: 12px;">
          {#each [
            ['SPLUNK LOGGING', locationData.splunk, locationData.splunk_coverage],
            ['CMDB PRESENCE', locationData.cmdb, locationData.cmdb_coverage],
            ['EDR PROTECTION', locationData.edr, locationData.edr_coverage]
          ] as [name, count, percentage]}
            {@const controlThreat = getThreatLevel(percentage)}
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: rgba(0, 0, 0, 0.4); border-left: 3px solid {controlThreat.color};">
              <div>
                <div style="color: var(--neural-cyan); font-size: 13px; font-weight: bold;">{name}</div>
                <div style="color: var(--text-muted); font-size: 10px;">{formatNumber(count)} of {formatNumber(locationData.total)} assets</div>
              </div>
              <div style="text-align: right;">
                <div style="color: {controlThreat.color}; font-size: 16px; font-weight: bold;">{percentage}%</div>
                <div style="color: {controlThreat.color}; font-size: 9px; letter-spacing: 1px;">{controlThreat.status}</div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
      
      <button class="quantum-btn" style="margin-top: 20px; width: 100%;" on:click={() => selectedLocation = null}>
        CLOSE ANALYSIS
      </button>
    </div>
  {/if}
{/if}