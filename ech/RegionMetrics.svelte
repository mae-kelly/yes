<!-- RegionMetrics.svelte - Premium Global Surveillance Grid -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';
	let radarAngle = 0;
	let hoveredIndex = -1;
	let pulseRadius = 0;

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/region_metrics');
			let result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			console.error('Region metrics error:', err);
			loading = false;
		}
		
		// Radar sweep animation
		const radarInterval = setInterval(() => {
			radarAngle = (radarAngle + 2) % 360;
			pulseRadius = (pulseRadius + 1) % 50;
		}, 50);
		
		return () => clearInterval(radarInterval);
	});

	$: sortedRegions = data.global_surveillance ? 
		Object.entries(data.global_surveillance)
			.filter(([region]) => region.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];

	$: maxCount = sortedRegions.length > 0 ? Math.max(...sortedRegions.map(([,c]) => c)) : 1;

	function getPercentage(count) {
		if (!data.total_coverage) return 0;
		return ((count / data.total_coverage) * 100).toFixed(2);
	}

	function getThreatStatus(percentage) {
		if (percentage >= 30) return { status: 'SECURE', color: '#00E676', glow: 'rgba(0, 230, 118, 0.4)' };
		if (percentage >= 20) return { status: 'ELEVATED', color: '#FFD600', glow: 'rgba(255, 214, 0, 0.4)' };
		if (percentage >= 10) return { status: 'WARNING', color: '#FF6E40', glow: 'rgba(255, 110, 64, 0.4)' };
		return { status: 'CRITICAL', color: '#FF1744', glow: 'rgba(255, 23, 68, 0.4)' };
	}

	function getRegionCoordinates(region) {
		const coords = {
			'NORTH AMERICA': { x: 25, y: 35, size: 'large' },
			'EMEA': { x: 50, y: 30, size: 'large' },
			'APAC': { x: 75, y: 45, size: 'large' },
			'LATAM': hostile 35, y: 65, size: 'medium' },
			'OTHER': { x: 50, y: 70, size: 'small' }
		};
		return coords[region.toUpperCase()] || { x: 50, y: 50, size: 'small' };
	}

	async function drillDownRegion(region, count) {
		selectedRegion = { region, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(region)}`);
			let result = await response.json();
			regionDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Region drill-down error:', err);
			regionDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedRegion = null;
		regionDetails = [];
	}
</script>

<div class="dashboard-container">
	<!-- Premium Background Effects -->
	<div class="background-effects">
		<div class="gradient-orb orb-1"></div>
		<div class="gradient-orb orb-2"></div>
		<div class="gradient-orb orb-3"></div>
		<div class="grid-overlay"></div>
		<div class="scan-line" style="transform: rotate({radarAngle}deg)"></div>
	</div>

	<div class="main-content">
		<!-- Left Panel: Regional Command -->
		<div class="table-panel glass-panel">
			<div class="panel-header">
				<div class="header-content">
					<div class="title-group">
						<h3 class="panel-title">
							<span class="title-icon">🌍</span>
							REGIONS
						</h3>
						<div class="subtitle">GLOBAL SURVEILLANCE NETWORK</div>
					</div>
					<div class="radar-widget">
						<svg viewBox="0 0 60 60" class="radar-svg">
							<defs>
								<radialGradient id="radarGradient">
									<stop offset="0%" style="stop-color:#00E5FF;stop-opacity:0.8" />
									<stop offset="100%" style="stop-color:#00E5FF;stop-opacity:0" />
								</radialGradient>
							</defs>
							<circle cx="30" cy="30" r="28" fill="none" stroke="rgba(0,229,255,0.1)" stroke-width="1"/>
							<circle cx="30" cy="30" r="20" fill="none" stroke="rgba(0,229,255,0.15)" stroke-width="1"/>
							<circle cx="30" cy="30" r="12" fill="none" stroke="rgba(0,229,255,0.2)" stroke-width="1"/>
							<circle cx="30" cy="30" r="4" fill="none" stroke="rgba(0,229,255,0.25)" stroke-width="1"/>
							
							<!-- Radar sweep -->
							<line x1="30" y1="30" x2="30" y2="2" 
								  stroke="url(#radarGradient)" stroke-width="2"
								  transform="rotate({radarAngle} 30 30)" opacity="0.8"/>
							
							<!-- Center dot -->
							<circle cx="30" cy="30" r="3" fill="#00E5FF">
								<animate attributeName="r" values="3;5;3" dur="2s" repeatCount="indefinite"/>
							</circle>
							
							<!-- Pulse ring -->
							<circle cx="30" cy="30" r={pulseRadius} fill="none" 
									stroke="#00E5FF" stroke-width="1" 
									opacity={1 - (pulseRadius / 50)}/>
						</svg>
					</div>
				</div>
				<div class="search-wrapper">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search regions..."
						class="search-input premium-input"
					/>
					<div class="search-icon">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<circle cx="11" cy="11" r="8"></circle>
							<path d="m21 21-4.35-4.35"></path>
						</svg>
					</div>
				</div>
			</div>
			
			{#if loading && !selectedRegion}
				<div class="loading-state">
					<div class="globe-loader">
						<div class="globe-container">
							<div class="globe-ring ring-1"></div>
							<div class="globe-ring ring-2"></div>
							<div class="globe-ring ring-3"></div>
							<div class="globe-core">🌍</div>
						</div>
					</div>
					<p class="loading-text">SCANNING GLOBAL NETWORKS</p>
				</div>
			{:else if selectedRegion}
				<div class="drill-view">
					<div class="drill-header glass-header">
						<div class="drill-title">
							<span class="drill-icon">▸</span>
							<h4>{selectedRegion.region.toUpperCase()}</h4>
							<span class="drill-badge">{selectedRegion.count.toLocaleString()} assets</span>
						</div>
						<button class="close-btn premium-btn" on:click={closeDetails}>
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<line x1="18" y1="6" x2="6" y2="18"></line>
								<line x1="6" y1="6" x2="18" y2="18"></line>
							</svg>
						</button>
					</div>
					<div class="drill-table-container">
						<table class="data-table premium-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>COUNTRY</th>
									<th>INFRASTRUCTURE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each regionDetails as host, index}
									<tr class="table-row {hoveredIndex === index ? 'hovered' : ''}"
										on:mouseenter={() => hoveredIndex = index}
										on:mouseleave={() => hoveredIndex = -1}>
										<td class="host-cell">{host.host}</td>
										<td>{host.country || 'CLASSIFIED'}</td>
										<td>{host.infrastructure_type || 'CLASSIFIED'}</td>
										<td>
											<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'badge-success' : 'badge-danger'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'VERIFIED' : 'UNKNOWN'}
											</span>
										</td>
										<td>
											<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'badge-success' : 'badge-warning'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? 'SECURED' : 'EXPOSED'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="table-scroll-container">
					<table class="data-table premium-table">
						<thead>
							<tr>
								<th>REGION</th>
								<th>ASSETS</th>
								<th>COVERAGE</th>
								<th>STATUS</th>
								<th>SURVEILLANCE GRID</th>
							</tr>
						</thead>
						<tbody>
							{#each sortedRegions as [region, count], index}
								{@const percentage = getPercentage(count)}
								{@const threat = getThreatStatus(percentage)}
								<tr class="table-row {hoveredIndex === index ? 'hovered' : ''}"
									on:click={() => drillDownRegion(region, count)}
									on:mouseenter={() => hoveredIndex = index}
									on:mouseleave={() => hoveredIndex = -1}>
									<td class="region-cell">
										<div class="region-marker" style="background: {threat.color}; box-shadow: 0 0 15px {threat.glow}"></div>
										<span class="region-name">{region.toUpperCase()}</span>
										<div class="region-flag">
											{#if region.includes('AMERICA')}🇺🇸{/if}
											{#if region.includes('EMEA')}🇪🇺{/if}
											{#if region.includes('APAC')}🇯🇵{/if}
											{#if region.includes('LATAM')}🇧🇷{/if}
										</div>
									</td>
									<td class="asset-cell">
										<div class="asset-content">
											<span class="asset-count">{count.toLocaleString()}</span>
											<div class="asset-bar-container">
												<div class="asset-bar" style="width: {(count/maxCount)*100}%; background: linear-gradient(90deg, {threat.color}, {threat.glow})"></div>
											</div>
										</div>
									</td>
									<td class="coverage-cell">
										<div class="coverage-display">
											<span class="coverage-value">{percentage}%</span>
											<svg width="32" height="32" class="coverage-chart">
												<circle cx="16" cy="16" r="14" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="2"/>
												<circle cx="16" cy="16" r="14" fill="none" stroke={threat.color} stroke-width="2"
													stroke-dasharray="{percentage} 100" transform="rotate(-90 16 16)"/>
											</svg>
										</div>
									</td>
									<td class="status-cell">
										<span class="status-badge-large" style="background: linear-gradient(135deg, {threat.color}22, {threat.color}44); border-color: {threat.color}; color: {threat.color}">
											<span class="status-icon">
												{#if threat.status === 'SECURE'}✓{/if}
												{#if threat.status === 'ELEVATED'}⚠{/if}
												{#if threat.status === 'WARNING'}⚡{/if}
												{#if threat.status === 'CRITICAL'}⚠️{/if}
											</span>
											{threat.status}
										</span>
									</td>
									<td class="grid-cell">
										<div class="grid-visualization">
											<svg viewBox="0 0 80 30" class="grid-svg">
												{#each Array(20) as _, i}
													<rect x="{i * 4}" y="{30 - (count/maxCount) * 25 * Math.sin(i * 0.5)}" 
														  width="3" height="{(count/maxCount) * 25 * Math.sin(i * 0.5)}"
														  fill={threat.color} opacity="{0.3 + (i * 0.035)}"/>
												{/each}
												<path d="M 0 15 Q 20 {15 - (count/maxCount) * 10} 40 15 T 80 15" 
													  fill="none" stroke={threat.color} stroke-width="1" opacity="0.8"/>
											</svg>
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>

		<!-- Right Panel: Tactical Map -->
		<div class="viz-panel">
			<!-- Global Metrics -->
			<div class="metrics-row">
				<div class="metric-card glass-card">
					<div class="metric-icon-wrapper">
						<div class="metric-icon">🌍</div>
					</div>
					<div class="metric-content">
						<div class="metric-value">{sortedRegions.length}</div>
						<div class="metric-label">ACTIVE REGIONS</div>
					</div>
					<div class="metric-graph">
						<svg viewBox="0 0 100 40">
							{#each sortedRegions as [region, count], i}
								<circle cx="{10 + i * 20}" cy="20" r="{3 + (count/maxCount) * 5}" 
										fill="#00E5FF" opacity="{0.3 + (count/maxCount) * 0.7}"/>
							{/each}
						</svg>
					</div>
				</div>
				
				<div class="metric-card glass-card">
					<div class="metric-icon-wrapper">
						<div class="metric-icon">📡</div>
					</div>
					<div class="metric-content">
						<div class="metric-value">{(data.total_coverage || 0).toLocaleString()}</div>
						<div class="metric-label">TOTAL COVERAGE</div>
					</div>
					<div class="metric-graph">
						<svg viewBox="0 0 100 40">
							<polyline points="0,35 20,25 40,30 60,15 80,20 100,10" 
									  fill="none" stroke="url(#coverageGradient)" stroke-width="2"/>
							<defs>
								<linearGradient id="coverageGradient" x1="0%" y1="0%" x2="100%" y2="0%">
									<stop offset="0%" style="stop-color:#00E676;stop-opacity:0.3" />
									<stop offset="50%" style="stop-color:#00E5FF;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#7C4DFF;stop-opacity:0.3" />
								</linearGradient>
							</defs>
						</svg>
					</div>
				</div>
			</div>

			<!-- Global Surveillance Map -->
			<div class="viz-card glass-card">
				<div class="card-header">
					<h4>GLOBAL SURVEILLANCE GRID</h4>
					<div class="card-status-indicator active"></div>
				</div>
				<div class="world-map">
					<svg viewBox="0 0 100 100" class="map-svg">
						<defs>
							<radialGradient id="regionGlow">
								<stop offset="0%" style="stop-color:#00E5FF;stop-opacity:0.8" />
								<stop offset="100%" style="stop-color:#00E5FF;stop-opacity:0" />
							</radialGradient>
							<filter id="glow">
								<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
								<feMerge>
									<feMergeNode in="coloredBlur"/>
									<feMergeNode in="SourceGraphic"/>
								</feMerge>
							</filter>
						</defs>
						
						<!-- Animated grid background -->
						<pattern id="gridPattern" width="10" height="10" patternUnits="userSpaceOnUse">
							<path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(0,229,255,0.1)" stroke-width="0.5"/>
						</pattern>
						<rect width="100" height="100" fill="url(#gridPattern)" opacity="0.5"/>
						
						<!-- World map outline (simplified) -->
						<path d="M 15 40 Q 25 35 35 40 L 40 35 Q 50 30 60 35 L 65 40 Q 75 38 85 42 
								 L 85 55 Q 75 58 65 55 L 60 60 Q 50 65 40 60 L 35 55 Q 25 58 15 55 Z" 
							  fill="none" stroke="rgba(0,229,255,0.2)" stroke-width="1"/>
						
						<!-- Region nodes -->
						{#each sortedRegions as [region, count]}
							{@const coords = getRegionCoordinates(region)}
							{@const threat = getThreatStatus(getPercentage(count))}
							{@const nodeSize = coords.size === 'large' ? 8 : coords.size === 'medium' ? 6 : 4}
							
							<g class="region-node">
								<!-- Connection lines to center -->
								<line x1="50" y1="50" x2="{coords.x}" y2="{coords.y}" 
									  stroke="rgba(0,229,255,0.1)" stroke-width="0.5" stroke-dasharray="2,3"/>
								
								<!-- Outer glow -->
								<circle cx="{coords.x}" cy="{coords.y}" r="{nodeSize * 2}" 
										fill="url(#regionGlow)" opacity="0.3"/>
								
								<!-- Main node -->
								<circle cx="{coords.x}" cy="{coords.y}" r="{nodeSize}" 
										fill={threat.color} opacity="0.8" filter="url(#glow)"/>
								
								<!-- Inner core -->
								<circle cx="{coords.x}" cy="{coords.y}" r="2" 
										fill="#ffffff"/>
								
								<!-- Pulse animation -->
								<circle cx="{coords.x}" cy="{coords.y}" r="{nodeSize}" 
										fill="none" stroke={threat.color} stroke-width="1" opacity="0">
									<animate attributeName="r" values="{nodeSize};{nodeSize * 2};{nodeSize}" dur="3s" repeatCount="indefinite"/>
									<animate attributeName="opacity" values="0.8;0;0.8" dur="3s" repeatCount="indefinite"/>
								</circle>
								
								<!-- Label -->
								<text x="{coords.x}" y="{coords.y - nodeSize - 5}" 
									  text-anchor="middle" fill="rgba(255,255,255,0.6)" 
									  font-size="6" font-weight="600">{region.substring(0, 3)}</text>
							</g>
						{/each}
						
						<!-- Central command node -->
						<circle cx="50" cy="50" r="5" fill="#00E5FF" opacity="0.8"/>
						<circle cx="50" cy="50" r="3" fill="#ffffff"/>
					</svg>
				</div>
			</div>

			<!-- Regional Distribution -->
			<div class="viz-card glass-card">
				<div class="card-header">
					<h4>ASSET DISTRIBUTION</h4>
					<div class="card-status-indicator"></div>
				</div>
				<div class="distribution-chart">
					{#each sortedRegions.slice(0, 5) as [region, count]}
						{@const percentage = getPercentage(count)}
						{@const threat = getThreatStatus(percentage)}
						<div class="dist-item">
							<div class="dist-header">
								<div class="dist-region">
									<span class="dist-icon" style="color: {threat.color}">●</span>
									{region.toUpperCase()}
								</div>
								<span class="dist-count">{count.toLocaleString()}</span>
							</div>
							<div class="dist-visual">
								<div class="dist-track"></div>
								<div class="dist-fill" 
									 style="width: {(count/maxCount)*100}%; 
											background: linear-gradient(90deg, {threat.color}, transparent)">
									<div class="dist-glow"></div>
								</div>
							</div>
							<div class="dist-stats">
								<span class="dist-percentage" style="color: {threat.color}">{percentage}%</span>
								<span class="dist-status">{threat.status}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Threat Assessment Matrix -->
			<div class="viz-card glass-card">
				<div class="card-header">
					<h4>THREAT ASSESSMENT</h4>
					<div class="card-status-indicator active"></div>
				</div>
				<div class="threat-grid">
					{#each sortedRegions.slice(0, 4) as [region, count]}
						{@const percentage = getPercentage(count)}
						{@const threat = getThreatStatus(percentage)}
						<div class="threat-cell" style="border-color: {threat.color}; background: linear-gradient(135deg, {threat.color}11, transparent)">
							<div class="threat-region">{region.substring(0, 8).toUpperCase()}</div>
							<div class="threat-visual">
								<svg viewBox="0 0 60 60" class="threat-svg">
									<defs>
										<linearGradient id="threatGrad{region}" x1="0%" y1="0%" x2="100%" y2="100%">
											<stop offset="0%" style="stop-color:{threat.color};stop-opacity:0.8" />
											<stop offset="100%" style="stop-color:{threat.color};stop-opacity:0.2" />
										</linearGradient>
									</defs>
									<polygon points="30,10 50,30 30,50 10,30" 
											fill="url(#threatGrad{region})" stroke={threat.color} stroke-width="1"/>
									<circle cx="30" cy="30" r="8" fill={threat.color} opacity="0.6"/>
									<circle cx="30" cy="30" r="3" fill="#ffffff"/>
								</svg>
							</div>
							<div class="threat-level" style="color: {threat.color}">{threat.status}</div>
							<div class="threat-metric">{percentage}%</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.dashboard-container {
		height: calc(100vh - 180px);
		display: flex;
		position: relative;
		background: #000000;
		color: #ffffff;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
		overflow: hidden;
		padding: 1.5rem;
	}

	.background-effects {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 0;
	}

	.gradient-orb {
		position: absolute;
		border-radius: 50%;
		filter: blur(100px);
		opacity: 0.3;
		animation: orbFloat 25s infinite ease-in-out;
	}

	.orb-1 {
		width: 500px;
		height: 500px;
		background: radial-gradient(circle, #00E5FF 0%, transparent 70%);
		top: -150px;
		right: -150px;
		animation-duration: 20s;
	}

	.orb-2 {
		width: 400px;
		height: 400px;
		background: radial-gradient(circle, #00E676 0%, transparent 70%);
		bottom: -100px;
		left: -100px;
		animation-duration: 25s;
		animation-delay: -7s;
	}

	.orb-3 {
		width: 300px;
		height: 300px;
		background: radial-gradient(circle, #7C4DFF 0%, transparent 70%);
		top: 40%;
		left: 40%;
		animation-duration: 30s;
		animation-delay: -12s;
	}

	.scan-line {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 100%;
		height: 1px;
		background: linear-gradient(90deg, transparent, rgba(0,229,255,0.3), transparent);
		transform-origin: center;
		pointer-events: none;
	}

	@keyframes orbFloat {
		0%, 100% { transform: translate(0, 0) scale(1); }
		25% { transform: translate(30px, -50px) scale(1.05); }
		50% { transform: translate(-40px, 30px) scale(0.95); }
		75% { transform: translate(50px, 40px) scale(1.08); }
	}

	.grid-overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background-image: 
			linear-gradient(rgba(0,229,255,0.02) 1px, transparent 1px),
			linear-gradient(90deg, rgba(0,229,255,0.02) 1px, transparent 1px);
		background-size: 40px 40px;
		animation: gridMove 15s linear infinite;
	}

	@keyframes gridMove {
		0% { transform: translate(0, 0); }
		100% { transform: translate(40px, 40px); }
	}

	.main-content {
		flex: 1;
		display: flex;
		gap: 1.5rem;
		overflow: hidden;
		position: relative;
		z-index: 1;
	}

	.glass-panel, .glass-card, .glass-header {
		background: rgba(255, 255, 255, 0.03);
		backdrop-filter: blur(20px);
		-webkit-backdrop-filter: blur(20px);
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.table-panel {
		flex: 1.5;
		border-radius: 24px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: 
			0 20px 60px rgba(0, 0, 0, 0.5),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
	}

	.panel-header {
		padding: 2rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.08);
		background: rgba(0, 0, 0, 0.3);
		flex-shrink: 0;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1.5rem;
	}

	.title-group {
		flex: 1;
	}

	.panel-title {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 600;
		background: linear-gradient(135deg, #ffffff 0%, #00E5FF 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.title-icon {
		font-size: 1.8rem;
		filter: saturate(1.5);
	}

	.subtitle {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.2em;
		margin-top: 0.5rem;
		font-weight: 500;
	}

	.radar-widget {
		width: 60px;
		height: 60px;
	}

	.radar-svg {
		width: 100%;
		height: 100%;
		filter: drop-shadow(0 0 10px rgba(0,229,255,0.3));
	}

	.search-wrapper {
		position: relative;
		width: 100%;
	}

	.premium-input {
		width: 100%;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 0.875rem 1rem 0.875rem 2.75rem;
		color: #ffffff;
		font-size: 0.9rem;
		font-family: inherit;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.premium-input:focus {
		outline: none;
		border-color: #00E5FF;
		background: rgba(0, 229, 255, 0.05);
		box-shadow: 0 0 0 3px rgba(0, 229, 255, 0.1);
	}

	.search-icon {
		position: absolute;
		left: 1rem;
		top: 50%;
		transform: translateY(-50%);
		color: rgba(255, 255, 255, 0.5);
		pointer-events: none;
	}

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
		padding: 3rem;
	}

	.globe-loader {
		width: 120px;
		height: 120px;
		position: relative;
	}

	.globe-container {
		width: 100%;
		height: 100%;
		position: relative;
		animation: globalRotate 10s linear infinite;
	}

	@keyframes globalRotate {
		0% { transform: rotateY(0deg) rotateX(10deg); }
		100% { transform: rotateY(360deg) rotateX(10deg); }
	}

	.globe-ring {
		position: absolute;
		border: 2px solid;
		border-radius: 50%;
		animation: ringRotate 3s linear infinite;
	}

	.ring-1 {
		width: 100%;
		height: 100%;
		border-color: rgba(0,229,255,0.4);
	}

	.ring-2 {
		width: 80%;
		height: 80%;
		top: 10%;
		left: 10%;
		border-color: rgba(0,230,118,0.4);
		animation-direction: reverse;
		animation-duration: 4s;
	}

	.ring-3 {
		width: 60%;
		height: 60%;
		top: 20%;
		left: 20%;
		border-color: rgba(124,77,255,0.4);
		animation-duration: 5s;
	}

	.globe-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 3rem;
		animation: corePulse 2s ease-in-out infinite;
	}

	@keyframes ringRotate {
		0% { transform: rotateY(0deg); }
		100% { transform: rotateY(360deg); }
	}

	@keyframes corePulse {
		0%, 100% { transform: translate(-50%, -50%) scale(1); }
		50% { transform: translate(-50%, -50%) scale(1.1); }
	}

	.loading-text {
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.85rem;
		letter-spacing: 0.3em;
		font-weight: 500;
		animation: textFade 1.5s ease-in-out infinite;
	}

	@keyframes textFade {
		0%, 100% { opacity: 0.6; }
		50% { opacity: 1; }
	}

	.table-scroll-container {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
		padding: 0 1rem;
	}

	.table-scroll-container::-webkit-scrollbar {
		width: 6px;
	}

	.table-scroll-container::-webkit-scrollbar-track {
		background: rgba(255, 255, 255, 0.02);
		border-radius: 3px;
	}

	.table-scroll-container::-webkit-scrollbar-thumb {
		background: linear-gradient(180deg, rgba(0,229,255,0.2), rgba(0,229,255,0.1));
		border-radius: 3px;
	}

	.premium-table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0;
		font-size: 0.875rem;
	}

	.premium-table th {
		background: rgba(0, 0, 0, 0.4);
		color: rgba(255, 255, 255, 0.6);
		padding: 1rem;
		text-align: left;
		font-weight: 600;
		font-size: 0.75rem;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.premium-table td {
		padding: 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.8);
		transition: all 0.2s ease;
	}

	.table-row {
		cursor: pointer;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		position: relative;
	}

	.table-row:hover {
		background: rgba(0, 229, 255, 0.05);
	}

	.table-row.hovered td {
		color: #ffffff;
	}

	.region-cell {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		min-width: 180px;
	}

	.region-marker {
		width: 10px;
		height: 10px;
		border-radius: 2px;
		transform: rotate(45deg);
		flex-shrink: 0;
		animation: markerPulse 2s ease-in-out infinite;
	}

	@keyframes markerPulse {
		0%, 100% { transform: rotate(45deg) scale(1); }
		50% { transform: rotate(45deg) scale(1.2); }
	}

	.region-name {
		font-weight: 500;
		flex: 1;
	}

	.region-flag {
		font-size: 1.2rem;
		margin-left: auto;
	}

	.asset-cell {
		min-width: 120px;
	}

	.asset-content {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.asset-count {
		font-weight: 600;
		font-size: 0.9rem;
		color: #ffffff;
	}

	.asset-bar-container {
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		overflow: hidden;
		width: 80px;
	}

	.asset-bar {
		height: 100%;
		transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.coverage-cell {
		min-width: 100px;
	}

	.coverage-display {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.coverage-value {
		font-weight: 600;
		min-width: 45px;
	}

	.coverage-chart {
		flex-shrink: 0;
	}

	.status-cell {
		min-width: 120px;
	}

	.status-badge-large {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.875rem;
		border: 1px solid;
		border-radius: 8px;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.status-icon {
		font-size: 1rem;
	}

	.grid-cell {
		min-width: 100px;
	}

	.grid-visualization {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0.5rem 0;
	}

	.grid-svg {
		width: 80px;
		height: 30px;
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.viz-panel::-webkit-scrollbar {
		width: 6px;
	}

	.viz-panel::-webkit-scrollbar-track {
		background: rgba(255, 255, 255, 0.02);
		border-radius: 3px;
	}

	.viz-panel::-webkit-scrollbar-thumb {
		background: linear-gradient(180deg, rgba(0,229,255,0.2), rgba(0,229,255,0.1));
		border-radius: 3px;
	}

	.metrics-row {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1.5rem;
	}

	.metric-card {
		border-radius: 16px;
		padding: 1.5rem;
		position: relative;
		overflow: hidden;
		box-shadow: 
			0 10px 40px rgba(0, 0, 0, 0.3),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
		min-height: 120px;
	}

	.metric-icon-wrapper {
		position: absolute;
		top: 1.5rem;
		right: 1.5rem;
		width: 48px;
		height: 48px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 229, 255, 0.1);
		border-radius: 12px;
	}

	.metric-icon {
		font-size: 1.8rem;
		filter: saturate(1.5);
	}

	.metric-content {
		position: relative;
		z-index: 1;
	}

	.metric-value {
		font-size: 2rem;
		font-weight: 700;
		background: linear-gradient(135deg, #ffffff 0%, #00E5FF 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		margin-bottom: 0.25rem;
	}

	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.15em;
		font-weight: 600;
	}

	.metric-graph {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		height: 40px;
		opacity: 0.5;
		padding: 0 1rem;
	}

	.metric-graph svg {
		width: 100%;
		height: 100%;
	}

	.viz-card {
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 
			0 10px 40px rgba(0, 0, 0, 0.3),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.viz-card h4 {
		margin: 0;
		font-size: 0.875rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.7);
		letter-spacing: 0.1em;
	}

	.card-status-indicator {
		width: 6px;
		height: 6px;
		background: rgba(0, 229, 255, 0.5);
		border-radius: 50%;
		animation: statusBlink 2s ease-in-out infinite;
	}

	.card-status-indicator.active {
		background: #00E676;
		animation: statusBlink 0.5s ease-in-out infinite;
		box-shadow: 0 0 10px rgba(0, 230, 118, 0.5);
	}

	@keyframes statusBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}

	.world-map {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 200px;
		padding: 1rem;
	}

	.map-svg {
		width: 100%;
		max-width: 300px;
		height: auto;
	}

	.region-node {
		animation: nodeBreathe 4s ease-in-out infinite;
	}

	@keyframes nodeBreathe {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.8; }
	}

	.distribution-chart {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.dist-item {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.dist-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.dist-region {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.8rem;
		font-weight: 500;
		color: rgba(255, 255, 255, 0.9);
	}

	.dist-icon {
		font-size: 0.6rem;
	}

	.dist-count {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.dist-visual {
		position: relative;
		height: 6px;
	}

	.dist-track {
		position: absolute;
		width: 100%;
		height: 100%;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 6px;
	}

	.dist-fill {
		position: relative;
		height: 100%;
		border-radius: 6px;
		overflow: hidden;
	}

	.dist-glow {
		position: absolute;
		right: 0;
		top: 50%;
		transform: translateY(-50%);
		width: 20px;
		height: 200%;
		background: rgba(255, 255, 255, 0.5);
		filter: blur(10px);
		animation: glowMove 2s ease-in-out infinite;
	}

	@keyframes glowMove {
		0%, 100% { opacity: 0; transform: translateY(-50%) translateX(-10px); }
		50% { opacity: 1; transform: translateY(-50%) translateX(0); }
	}

	.dist-stats {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.dist-percentage {
		font-size: 0.75rem;
		font-weight: 600;
	}

	.dist-status {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.threat-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
	}

	.threat-cell {
		padding: 1rem;
		border: 1px solid;
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		transition: all 0.3s ease;
	}

	.threat-cell:hover {
		transform: translateY(-2px);
		box-shadow: 0 10px 30px rgba(0,0,0,0.3);
	}

	.threat-region {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
		font-weight: 600;
	}

	.threat-visual {
		display: flex;
		justify-content: center;
		margin: 0.5rem 0;
	}

	.threat-svg {
		width: 60px;
		height: 60px;
	}

	.threat-level {
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.threat-metric {
		font-size: 0.9rem;
		font-weight: 700;
		color: rgba(255, 255, 255, 0.9);
	}

	.drill-view {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.drill-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		background: rgba(0, 229, 255, 0.03);
	}

	.drill-title {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.drill-icon {
		font-size: 1.5rem;
		color: #00E5FF;
		animation: drillPulse 1s ease-in-out infinite;
	}

	@keyframes drillPulse {
		0%, 100% { transform: translateX(0); }
		50% { transform: translateX(5px); }
	}

	.drill-header h4 {
		margin: 0;
		font-size: 1.125rem;
		font-weight: 600;
		color: #ffffff;
	}

	.drill-badge {
		background: rgba(0, 229, 255, 0.1);
		border: 1px solid rgba(0, 229, 255, 0.3);
		border-radius: 100px;
		padding: 0.25rem 0.75rem;
		font-size: 0.75rem;
		color: #00E5FF;
		font-weight: 600;
	}

	.premium-btn {
		background: rgba(255, 23, 68, 0.1);
		border: 1px solid rgba(255, 23, 68, 0.3);
		width: 36px;
		height: 36px;
		border-radius: 12px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #FF1744;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.premium-btn:hover {
		background: rgba(255, 23, 68, 0.2);
		transform: scale(1.05);
		box-shadow: 0 0 20px rgba(255, 23, 68, 0.3);
	}

	.drill-table-container {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}

	.host-cell {
		font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
		color: #00E5FF;
		font-weight: 500;
		font-size: 0.875rem;
	}

	.status-badge {
		padding: 0.25rem 0.625rem;
		border-radius: 6px;
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		display: inline-block;
	}

	.badge-success {
		background: rgba(0, 230, 118, 0.15);
		color: #00E676;
		border: 1px solid rgba(0, 230, 118, 0.3);
	}

	.badge-warning {
		background: rgba(255, 214, 0, 0.15);
		color: #FFD600;
		border: 1px solid rgba(255, 214, 0, 0.3);
	}

	.badge-danger {
		background: rgba(255, 23, 68, 0.15);
		color: #FF1744;
		border: 1px solid rgba(255, 23, 68, 0.3);
	}
</style>