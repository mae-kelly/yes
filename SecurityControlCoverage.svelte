<!-- /src/components/SecurityControlCoverage.svelte -->
<script>
  import { onMount } from 'svelte';

  let data = null;
  let loading = true;
  let error = null;
  let selectedInfrastructure = null;
  let viewMode = 'effectiveness';

  async function fetchData() {
    try {
      const response = await fetch('http://localhost:5000/api/security-control-coverage');
      if (!response.ok) throw new Error('Defense grid compromised');
      data = await response.json();
      loading = false;
    } catch (err) {
      error = err.message;
      loading = false;
    }
  }

  onMount(fetchData);

  function getThreatColor(score) {
    if (score >= 90) return 'var(--matrix-primary)';
    if (score >= 75) return 'var(--neural-cyan)';
    if (score >= 50) return 'var(--toxic-yellow)';
    if (score >= 25) return 'var(--plasma-magenta)';
    return 'var(--danger-crimson)';
  }

  function formatAssets(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  }

  function getSecurityStackData() {
    if (!data?.security_stack_tiers) return [];
    return data.security_stack_tiers.sort((a, b) => b.asset_count - a.asset_count);
  }

  function getGeographicSecurityMap() {
    if (!data?.geographic_security_map) return [];
    return data.geographic_security_map.slice(0, 20);
  }

  function getThreatSurfaceData() {
    if (!data?.threat_surface) return [];
    return data.threat_surface.sort((a, b) => b.external_exposure - a.external_exposure);
  }
</script>

{#if loading}
  <div class="quantum-loader">
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
    <div class="quantum-ring"></div>
  </div>
{:else if error}
  <div class="dystopia-modal active">
    <h2 style="color: var(--danger-crimson);">DEFENSE BREACH</h2>
    <p>{error}</p>
    <button class="quantum-btn danger" on:click={fetchData}>RESTORE DEFENSES</button>
  </div>
{:else if data}
  <!-- Security Control Effectiveness -->
  <div style="margin-bottom: 20px;">
    <div style="display: flex; gap: 10px; margin-bottom: 20px;">
      <button class="quantum-btn {viewMode === 'effectiveness' ? 'active' : ''}" on:click={() => viewMode = 'effectiveness'}>
        CONTROL EFFECTIVENESS
      </button>
      <button class="quantum-btn {viewMode === 'geographic' ? 'active' : ''}" on:click={() => viewMode = 'geographic'}>
        GEOGRAPHIC SECURITY
      </button>
      <button class="quantum-btn {viewMode === 'threat_surface' ? 'active' : ''}" on:click={() => viewMode = 'threat_surface'}>
        THREAT SURFACE
      </button>
      <button class="quantum-btn {viewMode === 'stack_analysis' ? 'active' : ''}" on:click={() => viewMode = 'stack_analysis'}>
        SECURITY STACK
      </button>
    </div>
  </div>

  {#if viewMode === 'effectiveness'}
    <!-- Security Control Effectiveness by Infrastructure Type -->
    <div class="holo-card-3d" style="padding: 25px; margin-bottom: 20px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        SECURITY CONTROL EFFECTIVENESS BY INFRASTRUCTURE
      </h3>
      
      <div style="max-height: 500px; overflow-y: auto;">
        {#each data.control_effectiveness as control}
          <div 
            style="background: linear-gradient(90deg, rgba(0,0,0,0.8), {getThreatColor(control.security_score)}10); border-left: 4px solid {getThreatColor(control.security_score)}; padding: 15px; margin-bottom: 8px; cursor: pointer;"
            class="neural-link"
            on:click={() => selectedInfrastructure = selectedInfrastructure === control.infrastructure ? null : control.infrastructure}
          >
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr; gap: 15px; align-items: center;">
              <div>
                <div style="color: var(--neural-cyan); font-size: 13px; font-weight: bold;">{control.infrastructure}</div>
                <div style="color: var(--text-muted); font-size: 10px;">{formatAssets(control.total_assets)} assets</div>
              </div>
              <div style="text-align: center;">
                <div style="color: {getThreatColor(control.edr_coverage)}; font-size: 13px; font-weight: bold;">{control.edr_coverage}%</div>
                <div style="color: var(--text-muted); font-size: 9px;">EDR</div>
              </div>
              <div style="text-align: center;">
                <div style="color: {getThreatColor(control.tanium_coverage)}; font-size: 13px; font-weight: bold;">{control.tanium_coverage}%</div>
                <div style="color: var(--text-muted); font-size: 9px;">TANIUM</div>
              </div>
              <div style="text-align: center;">
                <div style="color: {getThreatColor(control.dlp_coverage)}; font-size: 13px; font-weight: bold;">{control.dlp_coverage}%</div>
                <div style="color: var(--text-muted); font-size: 9px;">DLP</div>
              </div>
              <div style="text-align: center;">
                <div style="color: {getThreatColor(control.logging_coverage)}; font-size: 13px; font-weight: bold;">{control.logging_coverage}%</div>
                <div style="color: var(--text-muted); font-size: 9px;">LOGS</div>
              </div>
              <div style="text-align: center;">
                <div style="color: {getThreatColor(control.security_score)}; font-size: 15px; font-weight: bold;">{control.security_score}%</div>
                <div style="color: var(--text-muted); font-size: 9px;">COMPOSITE</div>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>

  {:else if viewMode === 'geographic'}
    <!-- Geographic Security Coverage Map -->
    <div class="holo-card-3d" style="padding: 25px; margin-bottom: 20px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        GLOBAL SECURITY COVERAGE MAP
      </h3>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px;">
        {#each getGeographicSecurityMap() as location}
          <div style="background: linear-gradient(135deg, rgba(0,0,0,0.8), {getThreatColor(location.composite_security_score)}15); border: 1px solid {getThreatColor(location.composite_security_score)}; padding: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
              <div>
                <div style="color: var(--neural-cyan); font-size: 12px; font-weight: bold;">{location.country}</div>
                <div style="color: var(--text-muted); font-size: 10px;">{location.region}</div>
              </div>
              <div style="text-align: right;">
                <div style="color: {getThreatColor(location.composite_security_score)}; font-size: 16px; font-weight: bold;">
                  {location.composite_security_score}%
                </div>
                <div style="color: var(--text-muted); font-size: 9px;">security score</div>
              </div>
            </div>
            
            <div style="margin-bottom: 10px;">
              <div style="color: var(--text-muted); font-size: 10px; margin-bottom: 6px;">
                {formatAssets(location.asset_count)} assets • {location.infrastructure_diversity} infra types
              </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; font-size: 9px;">
              <div style="text-align: center;">
                <div style="color: {getThreatColor(location.edr_coverage)}; font-weight: bold;">{location.edr_coverage}%</div>
                <div style="color: var(--text-muted);">EDR</div>
              </div>
              <div style="text-align: center;">
                <div style="color: {getThreatColor(location.tanium_coverage)}; font-weight: bold;">{location.tanium_coverage}%</div>
                <div style="color: var(--text-muted);">TANIUM</div>
              </div>
              <div style="text-align: center;">
                <div style="color: {getThreatColor(location.logging_coverage)}; font-weight: bold;">{location.logging_coverage}%</div>
                <div style="color: var(--text-muted);">LOGS</div>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>

  {:else if viewMode === 'threat_surface'}
    <!-- Threat Surface Analysis -->
    <div class="holo-card-3d" style="padding: 25px; margin-bottom: 20px;">
      <h3 style="color: var(--danger-crimson); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        EXTERNAL THREAT SURFACE ANALYSIS
      </h3>
      
      <div style="display: grid; gap: 10px; max-height: 500px; overflow-y: auto;">
        {#each getThreatSurfaceData() as surface}
          <div style="background: {surface.threat_level === 'critical' ? 'rgba(255, 7, 58, 0.1)' : surface.threat_level === 'medium' ? 'rgba(255, 44, 196, 0.1)' : 'rgba(0, 255, 65, 0.1)'}; border-left: 4px solid {surface.threat_level === 'critical' ? 'var(--danger-crimson)' : surface.threat_level === 'medium' ? 'var(--plasma-magenta)' : 'var(--matrix-primary)'}; padding: 15px;">
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 15px; align-items: center;">
              <div>
                <div style="color: var(--neural-cyan); font-size: 13px; font-weight: bold; margin-bottom: 4px;">
                  {surface.system_type}
                </div>
                <div style="color: var(--text-muted); font-size: 10px;">
                  {formatAssets(surface.total_systems)} systems
                </div>
              </div>
              
              <div style="text-align: center;">
                <div style="color: {surface.external_exposure > 0 ? 'var(--danger-crimson)' : 'var(--matrix-primary)'}; font-size: 14px; font-weight: bold;">
                  {surface.external_exposure}
                </div>
                <div style="color: var(--text-muted); font-size: 9px;">external</div>
              </div>
              
              <div style="text-align: center;">
                <div style="color: {getThreatColor(surface.exposure_ratio)}; font-size: 14px; font-weight: bold;">
                  {surface.exposure_ratio}%
                </div>
                <div style="color: var(--text-muted); font-size: 9px;">exposure</div>
              </div>
              
              <div style="text-align: center;">
                <div style="color: {getThreatColor(surface.edr_protection)}; font-size: 14px; font-weight: bold;">
                  {surface.edr_protection}%
                </div>
                <div style="color: var(--text-muted); font-size: 9px;">protected</div>
              </div>
              
              <div style="text-align: center;">
                <div style="color: {surface.threat_level === 'critical' ? 'var(--danger-crimson)' : surface.threat_level === 'medium' ? 'var(--plasma-magenta)' : 'var(--matrix-primary)'}; font-size: 11px; font-weight: bold; letter-spacing: 1px;">
                  {surface.threat_level.toUpperCase()}
                </div>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>

  {:else if viewMode === 'stack_analysis'}
    <!-- Security Stack Tier Analysis -->
    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          SECURITY STACK DISTRIBUTION
        </h3>
        
        <div style="display: grid; gap: 15px;">
          {#each getSecurityStackData() as tier}
            {@const tierColor = tier.tier === 'full_stack' ? 'var(--matrix-primary)' : tier.tier === 'core_security' ? 'var(--neural-cyan)' : tier.tier === 'basic_security' ? 'var(--toxic-yellow)' : tier.tier === 'logging_only' ? 'var(--plasma-magenta)' : 'var(--danger-crimson)'}
            <div style="background: linear-gradient(90deg, rgba(0,0,0,0.8), {tierColor}15); border-left: 4px solid {tierColor}; padding: 20px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h4 style="color: {tierColor}; font-size: 14px; font-weight: bold; letter-spacing: 1px;">
                  {tier.tier.replace(/_/g, ' ').toUpperCase()}
                </h4>
                <div style="color: {tierColor}; font-size: 18px; font-weight: bold;">
                  {tier.tier_percentage}%
                </div>
              </div>
              
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div>
                  <div style="color: var(--neural-cyan); font-size: 16px; font-weight: bold;">{formatAssets(tier.asset_count)}</div>
                  <div style="color: var(--text-muted); font-size: 10px;">assets in tier</div>
                </div>
                <div>
                  <div style="color: {getThreatColor(tier.data_quality)}; font-size: 16px; font-weight: bold;">{tier.data_quality}%</div>
                  <div style="color: var(--text-muted); font-size: 10px;">data quality</div>
                </div>
              </div>
              
              <div style="background: rgba(0,0,0,0.6); height: 6px; border-radius: 3px; overflow: hidden;">
                <div style="background: {tierColor}; height: 100%; width: {tier.tier_percentage}%; transition: all 0.8s; box-shadow: 0 0 10px {tierColor};"></div>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <!-- Security Metrics Breakdown -->
      <div class="holo-card-3d" style="padding: 25px;">
        <h3 style="color: var(--neural-cyan); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
          CONTROL METRICS
        </h3>
        
        <div style="display: grid; gap: 15px;">
          {#each [
            ['EDR DEPLOYMENT', getSecurityStackData().reduce((sum, t) => sum + (t.tier.includes('security') || t.tier === 'full_stack' ? t.asset_count : 0), 0)],
            ['TANIUM MANAGED', getSecurityStackData().reduce((sum, t) => sum + (t.tier === 'full_stack' || t.tier === 'core_security' ? t.asset_count : 0), 0)],
            ['DLP PROTECTED', getSecurityStackData().reduce((sum, t) => sum + (t.tier === 'full_stack' ? t.asset_count : 0), 0)],
            ['UNPROTECTED', getSecurityStackData().find(t => t.tier === 'unprotected')?.asset_count || 0]
          ] as [label, count], i}
            {@const total = getSecurityStackData().reduce((sum, t) => sum + t.asset_count, 0)}
            {@const percentage = total > 0 ? (count / total) * 100 : 0}
            {@const color = i === 3 ? 'var(--danger-crimson)' : getThreatColor(percentage)}
            <div style="background: rgba(0,0,0,0.4); border: 1px solid {color}; padding: 15px; text-align: center;">
              <div style="color: {color}; font-size: 18px; font-weight: bold; margin-bottom: 6px;">
                {formatAssets(count)}
              </div>
              <div style="color: var(--neural-cyan); font-size: 11px; letter-spacing: 1px; margin-bottom: 4px;">
                {label}
              </div>
              <div style="color: var(--text-muted); font-size: 9px;">
                {percentage.toFixed(1)}% of fleet
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>

  {:else if viewMode === 'geographic'}
    <!-- Geographic Security Distribution -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--matrix-primary); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        REGIONAL SECURITY COVERAGE ANALYSIS
      </h3>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px;">
        {#each getGeographicSecurityMap() as location}
          <div style="background: linear-gradient(135deg, rgba(0,0,0,0.8), {getThreatColor(location.composite_security_score)}10); border: 1px solid {getThreatColor(location.composite_security_score)}; padding: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
              <div>
                <div style="color: var(--neural-cyan); font-size: 13px; font-weight: bold;">{location.country}</div>
                <div style="color: var(--text-muted); font-size: 10px;">{location.region}</div>
              </div>
              <div style="text-align: right;">
                <div style="color: {getThreatColor(location.composite_security_score)}; font-size: 16px; font-weight: bold;">
                  {location.composite_security_score}%
                </div>
                <div style="color: var(--text-muted); font-size: 9px;">security</div>
              </div>
            </div>
            
            <div style="margin-bottom: 12px;">
              <div style="color: var(--text-muted); font-size: 10px; margin-bottom: 8px;">
                {formatAssets(location.asset_count)} assets • {location.infrastructure_diversity} infra types
              </div>
            </div>
            
            <div style="display: grid; gap: 6px;">
              {#each [
                ['EDR Coverage', location.edr_coverage],
                ['Tanium Coverage', location.tanium_coverage],
                ['Logging Coverage', location.logging_coverage]
              ] as [metric, value]}
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 10px;">
                  <span style="color: var(--text-muted);">{metric}</span>
                  <span style="color: {getThreatColor(value)}; font-weight: bold;">{value}%</span>
                </div>
                <div style="background: rgba(0,0,0,0.6); height: 2px; margin-bottom: 4px;">
                  <div style="background: {getThreatColor(value)}; height: 100%; width: {value}%; transition: all 0.5s;"></div>
                </div>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    </div>

  {:else if viewMode === 'threat_surface'}
    <!-- Threat Surface Exposure -->
    <div class="holo-card-3d" style="padding: 25px;">
      <h3 style="color: var(--danger-crimson); font-size: 16px; letter-spacing: 2px; margin-bottom: 20px;">
        EXTERNAL THREAT SURFACE EXPOSURE
      </h3>
      
      <div style="display: grid; gap: 10px; max-height: 500px; overflow-y: auto;">
        {#each getThreatSurfaceData() as surface}
          <div style="background: {surface.threat_level === 'critical' ? 'rgba(255, 7, 58, 0.1)' : surface.threat_level === 'medium' ? 'rgba(255, 44, 196, 0.1)' : 'rgba(0, 255, 65, 0.1)'}; border-left: 4px solid {surface.threat_level === 'critical' ? 'var(--danger-crimson)' : surface.threat_level === 'medium' ? 'var(--plasma-magenta)' : 'var(--matrix-primary)'}; padding: 15px;">
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 12px; align-items: center;">
              <div>
                <div style="color: var(--neural-cyan); font-size: 13px; font-weight: bold; margin-bottom: 4px;">
                  {surface.system_type}
                </div>
                <div style="color: var(--text-muted); font-size: 10px;">
                  {formatAssets(surface.total_systems)} systems
                </div>
              </div>
              
              <div style="text-align: center;">
                <div style="color: {surface.external_exposure > 0 ? 'var(--danger-crimson)' : 'var(--matrix-primary)'}; font-size: 15px; font-weight: bold;">
                  {surface.external_exposure}
                </div>
                <div style="color: var(--text-muted); font-size: 9px;">external</div>
              </div>
              
              <div style="text-align: center;">
                <div style="color: {getThreatColor(100 - surface.exposure_ratio)}; font-size: 14px; font-weight: bold;">
                  {surface.exposure_ratio}%
                </div>
                <div style="color: var(--text-muted); font-size: 9px;">exposure</div>
              </div>
              
              <div style="text-align: center;">
                <div style="color: {getThreatColor(surface.edr_protection)}; font-size: 14px; font-weight: bold;">
                  {surface.edr_protection}%
                </div>
                <div style="color: var(--text-muted); font-size: 9px;">protected</div>
              </div>
              
              <div style="text-align: center;">
                <div style="color: {surface.threat_level === 'critical' ? 'var(--danger-crimson)' : surface.threat_level === 'medium' ? 'var(--plasma-magenta)' : 'var(--matrix-primary)'}; font-size: 11px; font-weight: bold; letter-spacing: 1px;">
                  {surface.threat_level.toUpperCase()}
                </div>
              </div>
            </div>
            
            <div style="margin-top: 10px; display: flex; justify-content: space-between; font-size: 10px;">
              <span style="color: var(--text-muted);">Internal: {surface.internal_exposure}</span>
              <span style="color: {getThreatColor(surface.monitoring_coverage)};">Monitored: {surface.monitoring_coverage}%</span>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Selected Infrastructure Deep Dive Modal -->
  {#if selectedInfrastructure}
    {@const infraData = data.control_effectiveness.find(c => c.infrastructure === selectedInfrastructure)}
    {#if infraData}
      <div class="dystopia-modal active" style="max-width: 700px;">
        <h2 style="color: var(--matrix-primary); font-size: 18px; letter-spacing: 2px; margin-bottom: 20px;">
          INFRASTRUCTURE DEEP DIVE: {selectedInfrastructure.toUpperCase()}
        </h2>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px;">
          <div style="text-align: center;">
            <div style="color: var(--neural-cyan); font-size: 20px; font-weight: bold;">{formatAssets(infraData.total_assets)}</div>
            <div style="color: var(--text-muted); font-size: 11px;">TOTAL ASSETS</div>
          </div>
          <div style="text-align: center;">
            <div style="color: {getThreatColor(infraData.security_score)}; font-size: 20px; font-weight: bold;">{infraData.security_score}%</div>
            <div style="color: var(--text-muted); font-size: 11px;">SECURITY SCORE</div>
          </div>
          <div style="text-align: center;">
            <div style="color: {getThreatColor(infraData.data_quality)}; font-size: 20px; font-weight: bold;">{infraData.data_quality}%</div>
            <div style="color: var(--text-muted); font-size: 11px;">DATA QUALITY</div>
          </div>
        </div>
        
        <div style="display: grid; gap: 10px; margin-bottom: 20px;">
          {#each [
            ['EDR COVERAGE', infraData.edr_coverage],
            ['TANIUM COVERAGE', infraData.tanium_coverage],
            ['DLP COVERAGE', infraData.dlp_coverage],
            ['LOGGING COVERAGE', infraData.logging_coverage]
          ] as [control, coverage]}
            {@const controlThreat = getThreatColor(coverage)}
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: rgba(0,0,0,0.4); border-left: 2px solid {controlThreat};">
              <span style="color: var(--neural-cyan); font-size: 12px;">{control}</span>
              <span style="color: {controlThreat}; font-size: 14px; font-weight: bold;">{coverage}%</span>
            </div>
          {/each}
        </div>
        
        <button class="quantum-btn" style="width: 100%;" on:click={() => selectedInfrastructure = null}>
          CLOSE ANALYSIS
        </button>
      </div>
    {/if}
  {/if}
{/if}