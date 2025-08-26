<!-- /src/components/DomainVisibility.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = null;
  let loading = true;
  let error = null;
  let selectedDomain = null;
  let viewMode = 'overview';
  let searchTerm = '';
  let sortBy = 'total';
  let domainThreatSim = [];
  let geoLocations = [];

  async function fetchData() {
    try {
      const response = await fetch('http://localhost:5000/api/domain-visibility');
      if (!response.ok) throw new Error('DOMAIN MATRIX COMPROMISED');
      data = await response.json();
      loading = false;
      initializeDomainSim();
    } catch (err) {
      error = err.message;
      loading = false;
    }
  }

  function initializeDomainSim() {
    const threatTypes = ['DNS_HIJACK', 'SUBDOMAIN_TAKEOVER', 'CERT_EXPIRY', 'ZONE_TRANSFER'];
    const locations = ['US-EAST', 'US-WEST', 'EU-CENTRAL', 'APAC', 'LATAM'];
    
    setInterval(() => {
      if (data?.domain_matrix && Object.keys(data.domain_matrix).length > 0) {
        const domains = Object.keys(data.domain_matrix);
        const randomDomain = domains[Math.floor(Math.random() * domains.length)];
        
        domainThreatSim = [...domainThreatSim.slice(-6), {
          domain: randomDomain.split('.').slice(-2).join('.'),
          threat: threatTypes[Math.floor(Math.random() * threatTypes.length)],
          severity: Math.floor(Math.random() * 5) + 1,
          location: locations[Math.floor(Math.random() * locations.length)],
          timestamp: new Date().toLocaleTimeString()
        }];
      }
      
      if (Math.random() > 0.6) {
        geoLocations = locations.map(loc => ({
          location: loc,
          threats: Math.floor(Math.random() * 10),
          latency: Math.floor(Math.random() * 200) + 50,
          status: Math.random() > 0.2 ? 'SECURE' : 'ALERT'
        }));
      }
    }, 3500);
  }

  onMount(fetchData);

  function getThreatLevel(percentage) {
    if (percentage >= 95) return { color: 'var(--matrix-primary)', status: 'SECURED', level: 'OPTIMAL' };
    if (percentage >= 80) return { color: 'var(--neural-cyan)', status: 'PROTECTED', level: 'GOOD' };
    if (percentage >= 60) return { color: 'var(--toxic-yellow)', status: 'MONITORED', level: 'MEDIUM' };
    if (percentage >= 40) return { color: 'var(--plasma-magenta)', status: 'EXPOSED', level: 'HIGH' };
    return { color: 'var(--danger-crimson)', status: 'COMPROMISED', level: 'CRITICAL' };
  }

  function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  }

  function getFilteredDomains() {
    if (!data?.domain_matrix) return [];
    
    return Object.entries(data.domain_matrix)
      .filter(([domain]) => !searchTerm || domain.toLowerCase().includes(searchTerm.toLowerCase()))
      .map(([domain, stats]) => ({
        domain,
        ...stats,
        threat: getThreatLevel(stats.coverage_score),
        zone_type: getZoneType(domain)
      }))
      .sort((a, b) => {
        const aVal = sortBy === 'domain' ? a.domain : (sortBy === 'total' ? a.total : a[sortBy]?.percentage || a.coverage_score);
        const bVal = sortBy === 'domain' ? b.domain : (sortBy === 'total' ? b.total : b[sortBy]?.percentage || b.coverage_score);
        
        if (typeof aVal === 'string') return aVal.localeCompare(bVal);
        return bVal - aVal;
      });
  }

  function getZoneType(domain) {
    if (domain.includes('1dc')) return 'DATACENTER';
    if (domain.includes('fead')) return 'FEDERATED';
    if (domain.includes('corp')) return 'CORPORATE';
    if (domain.includes('dev')) return 'DEVELOPMENT';
    if (domain.includes('prod')) return 'PRODUCTION';
    return 'STANDARD';
  }

  function getVulnerabilityDomains() {
    if (!data?.vulnerability_zones) return [];
    return Object.entries(data.vulnerability_zones)
      .map(([domain, stats]) => ({
        domain,
        ...stats,
        threat: getThreatLevel(stats.coverage_score)
      }))
      .sort((a, b) => a.coverage_score - b.coverage_score)
      .slice(0, 10);
  }

  function getTopDomains() {
    if (!data?.top_domains) return [];
    return Object.entries(data.top_domains)
      .map(([domain, stats]) => ({
        domain,
        ...stats,
        threat: getThreatLevel(stats.coverage_score)
      }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 15);
  }
</script>

{#if loading}
  <div class="quantum-loader">
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
  </div>
  <div style="text-align: center; margin-top: 30px; color: var(--matrix-primary); font-size: 18px; letter-spacing: 3px; animation: blink-cursor 1s infinite;">
    SCANNING DOMAIN MATRIX...
  </div>
{:else if error}
  <div class="dystopia-modal active">
    <h2 style="color: var(--danger-crimson); font-size: 20px; letter-spacing: 2px; margin-bottom: 20px;">
      DOMAIN MATRIX BREACH
    </h2>
    <p style="color: var(--text-muted); margin-bottom: 20px;">{error}</p>
    <button class="quantum-btn danger" on:click={fetchData}>
      RESTORE DOMAIN GRID
    </button>
  </div>
{:else if data}

  <!-- Command Center -->
  <div class="glitch-field" style="margin-bottom: 30px;">
    <div class="glitch-text" data-text="DOMAIN RECONNAISSANCE MATRIX" style="font-size: 22px; font-weight: bold; letter-spacing: 4px; margin-bottom: 15px;">
      DOMAIN RECONNAISSANCE MATRIX
    </div>
    
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div style="display: flex; gap: 10px;">
        <button class="quantum-btn {viewMode === 'overview' ? 'active' : ''}" on:click={() => viewMode = 'overview'}>OVERVIEW</button>
        <button class="quantum-btn {viewMode === 'zones' ? 'active' : ''}" on:click={() => viewMode = 'zones'}>SECURITY ZONES</button>
        <button class="quantum-btn {viewMode === 'threats' ? 'active' : ''}" on:click={() => viewMode = 'threats'}>THREAT INTEL</button>
        <button class="quantum-btn {viewMode === 'recon' ? 'active' : ''}" on:click={() => viewMode = 'recon'}>DOMAIN RECON</button>
      </div>
      
      <div style="display: flex; gap: 10px; align-items: center;">
        <input 
          bind:value={searchTerm}
          placeholder="SEARCH DOMAINS..."
          style="background: rgba(0, 0, 0, 0.8); border: 1px solid var(--neural-cyan); color: var(--neural-cyan); padding: 8px 12px; font-family: inherit; font-size: 11px; letter-spacing: 1px;"
        />
        <select bind:value={sortBy} style="background: rgba(0, 0, 0, 0.8); border: 1px solid var(--neural-cyan); color: var(--neural-cyan); padding: 8px; font-family: inherit; font-size: 11px;">
          <option value="total">ASSET COUNT</option>
          <option value="coverage_score">COVERAGE</option>
          <option value="splunk">SPLUNK</option>
          <option value="crowdstrike">EDR</option>
          <option value="domain">DOMAIN NAME</option>
        </select>
      </div>
    </div>
  </div>

  {#if viewMode === 'overview'}
    <!-- Executive Domain Summary -->
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px;">
      <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: {getThreatLevel(data.domain_summary['1dc'].coverage_score).color};">
        <div style="font-size: 32px; color: {getThreatLevel(data.domain_summary['1dc'].coverage_score).color}; font-weight: bold; margin-bottom: 8px;">
          {data.domain_summary['1dc'].coverage_score}%
        </div>
        <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px; margin-bottom: 6px;">1DC DOMAINS</div>
        <div style="color: var(--text-muted); font-size: 10px;">{formatNumber(data.domain_summary['1dc'].total)} ASSETS</div>
      </div>

      <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: {getThreatLevel(data.domain_summary.fead.coverage_score).color};">
        <div style="font-size: 32px; color: {getThreatLevel(data.domain_summary.fead.coverage_score).color}; font-weight: bold; margin-bottom: 8px;">
          {data.domain_summary.fead.coverage_score}%
        </div>
        <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px; margin-bottom: 6px;">FEAD DOMAINS</div>
        <div style="color: var(--text-muted); font-size: 10px;">{formatNumber(data.domain_summary.fead.total)} ASSETS</div>
      </div>

      <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: var(--matrix-primary);">
        <div style="font-size: 32px; color: var(--matrix-primary); font-weight: bold; margin-bottom: 8px;">
          {Object.keys(data.domain_matrix || {}).length}
        </div>
        <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px; margin-bottom: 6px;">TOTAL DOMAINS</div>
        <div style="color: var(--text-muted); font-size: 10px;">UNDER SURVEILLANCE</div>
      </div>

      <div class="holo-card-3d" style="padding: 20px; text-align: center; border-color: var(--danger-crimson);">
        <div style="font-size: 32px; color: var(--danger-crimson); font-weight: bold; margin-bottom: 8px;">
          {Object.values(data.vulnerability_zones || {}).filter(d => d.coverage_score < 50).length}
        </div>
        <div style="color: var(--neural-cyan); font-size: 12px; letter-spacing: 2px; margin-bottom: 6px;">HIGH RISK ZONES</div>
        <div style="color: var(--text-muted); font-size: 10px;">IMMEDIATE ATTENTION</div>
      </div>
    </div>

    <!-- Domain Analysis Grid -->
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 30px;">
      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          TOP DOMAIN ASSETS
        </h3>
        
        <div style="max-height: 400px; overflow-y: auto;">
          <div style="display: grid; gap: 8px;">
            {#each getTopDomains() as domain}
              <div 
                style="background: linear-gradient(90deg, rgba(0, 0, 0, 0.8), {domain.threat.color}10); border-left: 4px solid {domain.threat.color}; padding: 12px; cursor: pointer; transition: all 0.3s;"
                class="neural-link"
                on:click={() => selectedDomain = selectedDomain === domain.domain ? null : domain.domain}
              >
                <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 15px; align-items: center;">
                  <div>
                    <div style="color: var(--neural-cyan); font-size: 12px; font-weight: bold; margin-bottom: 3px; word-break: break-all;">
                      {domain.domain}
                    </div>
                    <div style="color: var(--text-muted); font-size: 9px;">
                      {formatNumber(domain.total)} ASSETS • {getZoneType(domain.domain)}
                    </div>
                  </div>
                  
                  <div style="text-align: center;">
                    <div style="color: {domain.threat.color}; font-size: 13px; font-weight: bold;">{domain.coverage_score}%</div>
                    <div style="color: var(--text-muted); font-size: 8px;">COVERAGE</div>
                  </div>
                  
                  <div style="text-align: center;">
                    <div style="color: {getThreatLevel(domain.splunk.percentage).color}; font-size: 13px; font-weight: bold;">{domain.splunk.percentage}%</div>
                    <div style="color: var(--text-muted); font-size: 8px;">SPLUNK</div>
                  </div>
                  
                  <div style="text-align: center;">
                    <div style="color: {domain.threat.color}; font-size: 11px; font-weight: bold; letter-spacing: 1px;">
                      {domain.threat.level}
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>

      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--danger-crimson); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          VULNERABILITY ZONES
        </h3>
        
        <div style="display: grid; gap: 12px; max-height: 400px; overflow-y: auto;">
          {#each getVulnerabilityDomains() as vuln}
            <div style="background: rgba(255, 7, 58, 0.05); border: 1px solid var(--danger-crimson); padding: 12px;">
              <div style="color: var(--danger-crimson); font-size: 11px; font-weight: bold; margin-bottom: 6px; word-break: break-all;">
                {vuln.domain.split('.').slice(-2).join('.')}
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 9px; margin-bottom: 6px;">
                <span style="color: var(--text-muted);">ASSETS: {formatNumber(vuln.total)}</span>
                <span style="color: var(--danger-crimson); font-weight: bold;">GAP: {100 - vuln.coverage_score}%</span>
              </div>
              <div style="background: rgba(0, 0, 0, 0.6); height: 3px; border-radius: 2px; overflow: hidden;">
                <div style="background: var(--danger-crimson); height: 100%; width: {100 - vuln.coverage_score}%; transition: all 0.5s;"></div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>

  {:else if viewMode === 'zones'}
    <!-- Security Zones Analysis -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px;">
      {#each [
        ['DATACENTER ZONES', getFilteredDomains().filter(d => d.zone_type === 'DATACENTER')],
        ['FEDERATED ZONES', getFilteredDomains().filter(d => d.zone_type === 'FEDERATED')],
        ['CORPORATE ZONES', getFilteredDomains().filter(d => d.zone_type === 'CORPORATE')],
        ['PRODUCTION ZONES', getFilteredDomains().filter(d => d.zone_type === 'PRODUCTION')]
      ] as [zoneType, domains]}
        {@const avgCoverage = domains.length > 0 ? domains.reduce((sum, d) => sum + d.coverage_score, 0) / domains.length : 0}
        {@const zoneThreat = getThreatLevel(avgCoverage)}
        <div class="holo-card-3d" style="padding: 20px; border-color: {zoneThreat.color};">
          <h3 style="color: {zoneThreat.color}; font-size: 14px; letter-spacing: 1px; margin-bottom: 15px;">
            {zoneType}
          </h3>
          
          <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 15px;">
            <div style="text-align: center;">
              <div style="color: var(--neural-cyan); font-size: 20px; font-weight: bold;">{domains.length}</div>
              <div style="color: var(--text-muted); font-size: 10px;">DOMAINS</div>
            </div>
            <div style="text-align: center;">
              <div style="color: {zoneThreat.color}; font-size: 20px; font-weight: bold;">{avgCoverage.toFixed(1)}%</div>
              <div style="color: var(--text-muted); font-size: 10px;">AVG COVERAGE</div>
            </div>
          </div>

          <div style="max-height: 200px; overflow-y: auto;">
            {#each domains.slice(0, 8) as domain}
              <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px; margin-bottom: 4px; background: rgba(0, 0, 0, 0.3); font-size: 10px;">
                <span style="color: var(--text-muted); word-break: break-all;">
                  {domain.domain.split('.').slice(-2).join('.')}
                </span>
                <span style="color: {domain.threat.color}; font-weight: bold;">
                  {domain.coverage_score}%
                </span>
              </div>
            {/each}
          </div>

          <div style="margin-top: 15px; text-align: center;">
            <div style="color: {zoneThreat.color}; font-size: 11px; font-weight: bold; letter-spacing: 1px;">
              {zoneThreat.status}
            </div>
          </div>
        </div>
      {/each}
    </div>

  {:else if viewMode === 'threats'}
    <!-- Threat Intelligence Dashboard -->
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 30px;">
      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--danger-crimson); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          DOMAIN THREAT SIMULATION
        </h3>
        
        <div style="max-height: 350px; overflow-y: auto;">
          {#each domainThreatSim as threat}
            <div 
              style="background: {threat.severity > 3 ? 'rgba(255, 7, 58, 0.1)' : 'rgba(255, 44, 196, 0.1)'}; border-left: 3px solid {threat.severity > 3 ? 'var(--danger-crimson)' : 'var(--plasma-magenta)'}; padding: 12px; margin-bottom: 8px;"
            >
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: var(--neural-cyan); font-size: 12px; font-weight: bold; word-break: break-all;">
                  {threat.domain}
                </span>
                <span style="color: {threat.severity > 3 ? 'var(--danger-crimson)' : 'var(--plasma-magenta)'}; font-size: 10px; font-weight: bold;">
                  {threat.threat}
                </span>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 9px; color: var(--text-muted);">
                <span>SEVERITY: {threat.severity}/5</span>
                <span>LOCATION: {threat.location}</span>
                <span>{threat.timestamp}</span>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--toxic-yellow); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          GEO THREAT MAP
        </h3>
        
        <div style="display: grid; gap: 15px;">
          {#each geoLocations as geo}
            <div style="background: rgba(0, 0, 0, 0.4); border: 1px solid {geo.status === 'SECURE' ? 'var(--matrix-primary)' : 'var(--danger-crimson)'}; padding: 15px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: var(--neural-cyan); font-size: 12px; font-weight: bold;">{geo.location}</span>
                <span style="color: {geo.status === 'SECURE' ? 'var(--matrix-primary)' : 'var(--danger-crimson)'}; font-size: 10px; letter-spacing: 1px;">
                  {geo.status}
                </span>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 10px; color: var(--text-muted); margin-bottom: 8px;">
                <span>THREATS: {geo.threats}</span>
                <span>LATENCY: {geo.latency}ms</span>
              </div>
              <div style="background: rgba(0, 0, 0, 0.6); height: 2px; border-radius: 1px; overflow: hidden;">
                <div style="background: {geo.status === 'SECURE' ? 'var(--matrix-primary)' : 'var(--danger-crimson)'}; height: 100%; width: {geo.status === 'SECURE' ? 85 : 45}%; transition: all 0.5s;"></div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>

  {:else if viewMode === 'recon'}
    <!-- Domain Reconnaissance -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        COMPREHENSIVE DOMAIN RECONNAISSANCE
      </h3>
      
      <div style="max-height: 600px; overflow-y: auto;">
        <div style="display: grid; gap: 10px;">
          {#each getFilteredDomains() as domain}
            <div 
              style="background: linear-gradient(90deg, rgba(0, 0, 0, 0.8), {domain.threat.color}08); border-left: 4px solid {domain.threat.color}; padding: 15px; cursor: pointer; transition: all 0.3s;"
              class="neural-link"
              on:click={() => selectedDomain = selectedDomain === domain.domain ? null : domain.domain}
            >
              <div style="display: grid; grid-template-columns: 3fr 1fr 1fr 1fr 1fr 1fr; gap: 15px; align-items: center;">
                <div>
                  <div style="color: var(--neural-cyan); font-size: 12px; font-weight: bold; margin-bottom: 4px; word-break: break-all;">
                    {domain.domain}
                  </div>
                  <div style="color: var(--text-muted); font-size: 9px;">
                    {formatNumber(domain.total)} ASSETS • {domain.zone_type}
                  </div>
                </div>
                
                <div style="text-align: center;">
                  <div style="color: {domain.threat.color}; font-size: 13px; font-weight: bold;">{domain.coverage_score}%</div>
                  <div style="color: var(--text-muted); font-size: 8px;">OVERALL</div>
                </div>
                
                <div style="text-align: center;">
                  <div style="color: {getThreatLevel(domain.splunk.percentage).color}; font-size: 13px; font-weight: bold;">{domain.splunk.percentage}%</div>
                  <div style="color: var(--text-muted); font-size: 8px;">SPLUNK</div>
                </div>
                
                <div style="text-align: center;">
                  <div style="color: {getThreatLevel(domain.cmdb.percentage).color}; font-size: 13px; font-weight: bold;">{domain.cmdb.percentage}%</div>
                  <div style="color: var(--text-muted); font-size: 8px;">CMDB</div>
                </div>
                
                <div style="text-align: center;">
                  <div style="color: {getThreatLevel(domain.crowdstrike.percentage).color}; font-size: 13px; font-weight: bold;">{domain.crowdstrike.percentage}%</div>
                  <div style="color: var(--text-muted); font-size: 8px;">EDR</div>
                </div>
                
                <div style="text-align: center;">
                  <div style="color: {domain.threat.color}; font-size: 10px; font-weight: bold; letter-spacing: 1px;">
                    {domain.threat.level}
                  </div>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}

  <!-- Selected Domain Analysis Modal -->
  {#if selectedDomain && data.domain_matrix[selectedDomain]}
    <div class="dystopia-modal active" style="max-width: 700px;">
      <h2 style="color: var(--matrix-primary); font-size: 18px; letter-spacing: 2px; margin-bottom: 20px;">
        DOMAIN ANALYSIS: {selectedDomain.toUpperCase()}
      </h2>
      
      {@const domainData = data.domain_matrix[selectedDomain]}
      {@const domainThreat = getThreatLevel(domainData.coverage_score)}
      
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px;">
        <div style="text-align: center;">
          <div style="color: var(--neural-cyan); font-size: 18px; font-weight: bold;">{formatNumber(domainData.total)}</div>
          <div style="color: var(--text-muted); font-size: 10px;">TOTAL ASSETS</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {domainThreat.color}; font-size: 18px; font-weight: bold;">{domainData.coverage_score}%</div>
          <div style="color: var(--text-muted); font-size: 10px;">COVERAGE</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {domainThreat.color}; font-size: 14px; font-weight: bold;">{getZoneType(selectedDomain)}</div>
          <div style="color: var(--text-muted); font-size: 10px;">ZONE TYPE</div>
        </div>
        <div style="text-align: center;">
          <div style="color: {domainThreat.color}; font-size: 14px; font-weight: bold;">{domainThreat.status}</div>
          <div style="color: var(--text-muted); font-size: 10px;">STATUS</div>
        </div>
      </div>
      
      <div style="display: grid; gap: 10px; margin-bottom: 20px;">
        {#each [
          ['SPLUNK LOGGING', domainData.splunk],
          ['CROWDSTRIKE EDR', domainData.crowdstrike],
          ['CMDB TRACKING', domainData.cmdb],
          ['TANIUM MANAGEMENT', domainData.tanium]
        ] as [name, stats]}
          {#if stats}
            {@const controlThreat = getThreatLevel(stats.percentage)}
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: rgba(0, 0, 0, 0.4); border-left: 2px solid {controlThreat.color};">
              <div>
                <div style="color: var(--neural-cyan); font-size: 12px; font-weight: bold;">{name}</div>
                <div style="color: var(--text-muted); font-size: 10px;">{formatNumber(stats.count)} assets covered</div>
              </div>
              <div style="text-align: right;">
                <div style="color: {controlThreat.color}; font-size: 14px; font-weight: bold;">{stats.percentage}%</div>
                <div style="color: {controlThreat.color}; font-size: 9px;">{controlThreat.status}</div>
              </div>
            </div>
          {/if}
        {/each}
      </div>
      
      <button class="quantum-btn" style="width: 100%;" on:click={() => selectedDomain = null}>
        CLOSE ANALYSIS
      </button>
    </div>
  {/if}
{/if}