<!-- RegionMetrics.svelte - Global Surveillance Grid -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';
	let radarAngle = 0;
	let gridPulse = [];

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/region_metrics');
			let result = await response.json();
			data = result;
			loading = false;
			
			// Initialize grid pulse for visualization
			for (let i = 0; i < 16; i++) {
				gridPulse.push(Math.random());
			}
		} catch (err) {
			console.error('Region metrics error:', err);
			loading = false;
		}
		
		// Radar sweep animation
		const radarInterval = setInterval(() => {
			radarAngle = (radarAngle + 2) % 360;
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
		if (percentage >= 30) return { status: 'SECURE', color: '#0a4f3c' };
		if (percentage >= 20) return { status: 'ELEVATED', color: '#ffcc00' };
		if (percentage >= 10) return { status: 'WARNING', color: '#ff9900' };
		return { status: 'CRITICAL', color: '#ff0066' };
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

	function getRegionCoordinates(region) {
		const coords = {
			'NORTH AMERICA': { x: 30, y: 35 },
			'EMEA': { x: 50, y: 40 },
			'APAC': { x: 75, y: 50 },
			'LATAM': { x: 35, y: 65 },
			'OTHER': { x: 50, y: 60 }
		};
		return coords[region.toUpperCase()] || { x: 50, y: 50 };
	}
</script>

<div class="dashboard-container">
	<div class="main-content">
		<!-- Left Panel: Regional Command -->
		<div class="table-panel">
			<div class="panel-header">
				<div class="header-grid">
					<div>
						<h3 class="panel-title">REGIONS</h3>
						<div class="subtitle">GLOBAL SURVEILLANCE NETWORK</div>
					</div>
					<div class="radar-indicator">
						<svg viewBox="0 0 40 40" class="radar-svg">
							<circle cx="20" cy="20" r="18" fill="none" stroke="#0a4f3c" stroke-width="0.5" opacity="0.3"/>
							<circle cx="20" cy="20" r="12" fill="none" stroke="#0a4f3c" stroke-width="0.5" opacity="0.5"/>
							<circle cx="20" cy="20" r="6" fill="none" stroke="#0a4f3c" stroke-width="0.5" opacity="0.7"/>
							<line x1="20" y1="20" x2="20" y2="2" 
								  stroke="#0a4f3c" stroke-width="1" opacity="0.8"
								  transform="rotate({radarAngle} 20 20)">
								<animate attributeName="opacity" values="0.8;0.2;0.8" dur="2s" repeatCount="indefinite"/>
							</line>
							<circle cx="20" cy="20" r="2" fill="#0a4f3c"/>
						</svg>
					</div>
				</div>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="SEARCH REGIONS..."
						class="search-input"
					/>
				</div>
			</div>
			
			{#if loading && !selectedRegion}
				<div class="loading-state">
					<div class="globe-loader">
						<div class="globe-ring"></div>
						<div class="globe-ring"></div>
						<div class="globe-ring"></div>
					</div>
					<p class="loading-text">SCANNING GLOBAL NETWORKS...</p>
				</div>
			{:else if selectedRegion}
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedRegion.region.toUpperCase()}</h4>
						<button class="close-btn" on:click={closeDetails}>
							<svg width="20" height="20" viewBox="0 0 20 20">
								<path d="M2 2L18 18M18 2L2 18" stroke="#ff0066" stroke-width="2"/>
							</svg>
						</button>
					</div>
					<div class="drill-table-container">
						<table class="data-table">
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
								{#each regionDetails as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.country || 'CLASSIFIED'}</td>
										<td>{host.infrastructure_type || 'CLASSIFIED'}</td>
										<td>
											<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'VERIFIED' : 'UNKNOWN'}
											</span>
										</td>
										<td>
											<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
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
					<table class="data-table">
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
							{#each sortedRegions as [region, count]}
								{@const percentage = getPercentage(count)}
								{@const threat = getThreatStatus(percentage)}
								<tr on:click={() => drillDownRegion(region, count)}>
									<td class="region-cell">
										<div class="region-marker" style="background: {threat.color}"></div>
										<span class="region-name">{region.toUpperCase()}</span>
									</td>
									<td class="center asset-cell">
										<span class="asset-count">{count.toLocaleString()}</span>
										<div class="asset-bar" style="width: {(count/maxCount)*100}%"></div>
									</td>
									<td class="center">{percentage}%</td>
									<td class="center">
										<span class="status-badge" style="color: {threat.color}; border-color: {threat.color}">
											{threat.status}
										</span>
									</td>
									<td>
										<div class="grid-visualization">
											<svg viewBox="0 0 60 20" class="grid-svg">
												{#each Array(15) as _, i}
													<rect x="{i * 4}" y="5" width="3" height="{10 * (count/maxCount)}" 
														  fill={threat.color} opacity="{0.3 + (i * 0.05)}"/>
												{/each}
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
				<div class="metric-card">
					<div class="metric-header">
						<span class="metric-icon">◈</span>
						<span class="metric-label">REGIONS</span>
					</div>
					<div class="metric-value">{sortedRegions.length}</div>
					<div class="metric-subtext">ACTIVE ZONES</div>
				</div>
				<div class="metric-card">
					<div class="metric-header">
						<span class="metric-icon">◉</span>
						<span class="metric-label">ASSETS</span>
					</div>
					<div class="metric-value">{(data.total_coverage || 0).toLocaleString()}</div>
					<div class="metric-subtext">MONITORED</div>
				</div>
			</div>

			<!-- Global Surveillance Map -->
			<div class="viz-card">
				<div class="card-header">
					<h4>GLOBAL SURVEILLANCE GRID</h4>
					<div class="card-indicator active"></div>
				</div>
				<div class="world-map">
					<svg viewBox="0 0 100 100" class="map-svg">
						<defs>
							<radialGradient id="regionGlow">
								<stop offset="0%" style="stop-color:#0a4f3c;stop-opacity:0.8" />
								<stop offset="100%" style="stop-color:#0a4f3c;stop-opacity:0" />
							</radialGradient>
							<filter id="glow">
								<feGaussianBlur stdDeviation="2" result="coloredBlur"/>
								<feMerge>
									<feMergeNode in="coloredBlur"/>
									<feMergeNode in="SourceGraphic"/>
								</feMerge>
							</filter>
						</defs>
						
						<!-- Grid lines -->
						{#each Array(10) as _, i}
							<line x1="{i * 10}" y1="0" x2="{i * 10}" y2="100" 
								  stroke="#0a4f3c" stroke-width="0.2" opacity="0.2"/>
							<line x1="0" y1="{i * 10}" x2="100" y2="{i * 10}" 
								  stroke="#0a4f3c" stroke-width="0.2" opacity="0.2"/>
						{/each}
						
						<!-- Region nodes -->
						{#each sortedRegions as [region, count]}
							{@const coords = getRegionCoordinates(region)}
							{@const size = Math.sqrt(count / maxCount) * 15}
							{@const threat = getThreatStatus(getPercentage(count))}
							
							<g class="region-node">
								<circle cx="{coords.x}" cy="{coords.y}" r="{size}" 
										fill="url(#regionGlow)" opacity="0.3"/>
								<circle cx="{coords.x}" cy="{coords.y}" r="{size/2}" 
										fill="none" stroke={threat.color} stroke-width="1" 
										opacity="0.8" filter="url(#glow)"/>
								<circle cx="{coords.x}" cy="{coords.y}" r="2" 
										fill={threat.color}/>
								
								<!-- Pulse animation -->
								<circle cx="{coords.x}" cy="{coords.y}" r="{size/2}" 
										fill="none" stroke={threat.color} stroke-width="1" 
										opacity="0">
									<animate attributeName="r" values="{size/2};{size}" dur="2s" repeatCount="indefinite"/>
									<animate attributeName="opacity" values="0.8;0" dur="2s" repeatCount="indefinite"/>
								</circle>
							</g>
						{/each}
						
						<!-- Connection lines -->
						{#each sortedRegions as [region1, count1], i}
							{#each sortedRegions.slice(i + 1) as [region2, count2]}
								{@const coords1 = getRegionCoordinates(region1)}
								{@const coords2 = getRegionCoordinates(region2)}
								<line x1="{coords1.x}" y1="{coords1.y}" 
									  x2="{coords2.x}" y2="{coords2.y}" 
									  stroke="#0a4f3c" stroke-width="0.3" 
									  opacity="0.2" stroke-dasharray="2,2"/>
							{/each}
						{/each}
					</svg>
				</div>
			</div>

			<!-- Regional Distribution -->
			<div class="viz-card">
				<div class="card-header">
					<h4>ASSET DISTRIBUTION</h4>
					<div class="card-indicator"></div>
				</div>
				<div class="distribution-chart">
					{#each sortedRegions.slice(0, 6) as [region, count]}
						{@const percentage = getPercentage(count)}
						{@const threat = getThreatStatus(percentage)}
						<div class="dist-item">
							<div class="dist-header">
								<span class="dist-region">{region.toUpperCase()}</span>
								<span class="dist-count">{count.toLocaleString()}</span>
							</div>
							<div class="dist-visual">
								<div class="dist-track"></div>
								<div class="dist-fill" 
									 style="width: {(count/maxCount)*100}%; 
											background: linear-gradient(90deg, #0a4f3c, {threat.color})">
									<div class="dist-glow"></div>
								</div>
							</div>
							<div class="dist-stats">
								<span class="dist-percentage">{percentage}%</span>
								<span class="dist-status" style="color: {threat.color}">{threat.status}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Threat Matrix -->
			<div class="viz-card">
				<div class="card-header">
					<h4>THREAT ASSESSMENT</h4>
					<div class="card-indicator active"></div>
				</div>
				<div class="threat-grid">
					{#each sortedRegions.slice(0, 4) as [region, count]}
						{@const percentage = getPercentage(count)}
						{@const threat = getThreatStatus(percentage)}
						<div class="threat-cell" style="border-color: {threat.color}">
							<div class="threat-region">{region.substring(0, 8).toUpperCase()}</div>
							<div class="threat-visual">
								<svg viewBox="0 0 50 50" class="threat-svg">
									<polygon points="25,5 45,25 25,45 5,25" 
											fill="none" stroke={threat.color} stroke-width="1"/>
									<polygon points="25,10 40,25 25,40 10,25" 
											fill={threat.color} opacity="0.2"/>
									<circle cx="25" cy="25" r="5" fill={threat.color} opacity="0.8"/>
								</svg>
							</div>
							<div class="threat-level" style="color: {threat.color}">{threat.status}</div>
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
		background: #000000;
		color: #e0e0e0;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
		padding: 1rem;
	}

	.main-content {
		flex: 1;
		display: flex;
		gap: 1rem;
		overflow: hidden;
	}

	.table-panel {
		flex: 1.5;
		background: linear-gradient(135deg, #0a0a0a 0%, #050505 100%);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		position: relative;
	}

	.panel-header {
		padding: 1.5rem;
		border-bottom: 1px solid #0a4f3c;
		background: rgba(10, 79, 60, 0.02);
		flex-shrink: 0;
	}

	.header-grid {
		display: flex;
		justify-content: space-between;
		align-items: start;
		margin-bottom: 1rem;
	}

	.panel-title {
		margin: 0;
		color: #0a4f3c;
		font-size: 1.2rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-shadow: 0 0 20px rgba(10, 79, 60, 0.5);
	}

	.subtitle {
		font-size: 0.7rem;
		color: #666;
		letter-spacing: 0.2em;
		margin-top: 0.25rem;
	}

	.radar-indicator {
		width: 40px;
		height: 40px;
	}

	.radar-svg {
		width: 100%;
		height: 100%;
		animation: radarGlow 2s ease-in-out infinite;
	}

	@keyframes radarGlow {
		0%, 100% { filter: drop-shadow(0 0 5px rgba(10, 79, 60, 0.5)); }
		50% { filter: drop-shadow(0 0 15px rgba(10, 79, 60, 0.8)); }
	}

	.search-input {
		width: 100%;
		background: #000;
		border: 1px solid #0a4f3c;
		border-radius: 2px;
		padding: 0.6rem 1rem;
		color: #e0e0e0;
		font-size: 0.8rem;
		font-family: inherit;
		letter-spacing: 0.05em;
	}

	.search-input:focus {
		outline: none;
		box-shadow: 0 0 20px rgba(10, 79, 60, 0.3);
		background: rgba(10, 79, 60, 0.02);
	}

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.globe-loader {
		width: 80px;
		height: 80px;
		position: relative;
	}

	.globe-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid #0a4f3c;
		border-radius: 50%;
		opacity: 0.3;
		animation: globeRotate 2s linear infinite;
	}

	.globe-ring:nth-child(2) {
		transform: rotateY(60deg);
		animation-delay: 0.3s;
	}

	.globe-ring:nth-child(3) {
		transform: rotateY(120deg);
		animation-delay: 0.6s;
	}

	@keyframes globeRotate {
		0% { transform: rotateY(0deg) rotateX(0deg); }
		100% { transform: rotateY(360deg) rotateX(360deg); }
	}

	.loading-text {
		color: #0a4f3c;
		font-size: 0.8rem;
		letter-spacing: 0.2em;
	}

	.table-scroll-container {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.8rem;
	}

	.data-table th {
		background: rgba(10, 79, 60, 0.05);
		color: #0a4f3c;
		padding: 1rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 2px solid #0a4f3c;
	}

	.data-table td {
		padding: 0.8rem 1rem;
		border-bottom: 1px solid rgba(10, 79, 60, 0.1);
		color: #b8a678;
	}

	.data-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		position: relative;
	}

	.data-table tbody tr:hover {
		background: rgba(10, 79, 60, 0.05);
	}

	.region-cell {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.region-marker {
		width: 10px;
		height: 10px;
		border-radius: 2px;
		animation: markerPulse 2s ease-in-out infinite;
	}

	@keyframes markerPulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.2); opacity: 0.6; }
	}

	.region-name {
		font-weight: 500;
		color: #e0e0e0;
	}

	.center {
		text-align: center;
	}

	.asset-cell {
		position: relative;
	}

	.asset-count {
		position: relative;
		z-index: 2;
		font-weight: 600;
	}

	.asset-bar {
		position: absolute;
		bottom: 0;
		left: 0;
		height: 2px;
		background: linear-gradient(90deg, #0a4f3c, #0d6b4f);
		opacity: 0.6;
	}

	.status-badge {
		padding: 0.3rem 0.6rem;
		border: 1px solid;
		border-radius: 2px;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
	}

	.grid-visualization {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.grid-svg {
		width: 100%;
		height: 20px;
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.metrics-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.metric-card {
		background: linear-gradient(135deg, #0a0a0a 0%, #050505 100%);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		padding: 1.2rem;
	}

	.metric-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.metric-icon {
		color: #0a4f3c;
		font-size: 1rem;
	}

	.metric-label {
		font-size: 0.7rem;
		color: #666;
		letter-spacing: 0.1em;
	}

	.metric-value {
		font-size: 2rem;
		font-weight: 700;
		color: #0a4f3c;
		text-shadow: 0 0 20px rgba(10, 79, 60, 0.5);
	}

	.metric-subtext {
		font-size: 0.65rem;
		color: #b8a678;
		letter-spacing: 0.05em;
		margin-top: 0.25rem;
	}

	.viz-card {
		background: linear-gradient(135deg, #0a0a0a 0%, #050505 100%);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		padding: 1.5rem;
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.viz-card h4 {
		margin: 0;
		font-size: 0.9rem;
		color: #0a4f3c;
		letter-spacing: 0.1em;
		font-weight: 600;
	}

	.card-indicator {
		width: 6px;
		height: 6px;
		background: #0a4f3c;
		border-radius: 50%;
		animation: indicatorBlink 2s ease-in-out infinite;
	}

	.card-indicator.active {
		background: #ff0066;
		animation-duration: 0.5s;
	}

	@keyframes indicatorBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}

	.world-map {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 200px;
	}

	.map-svg {
		width: 100%;
		height: auto;
	}

	.region-node {
		animation: nodePulse 3s ease-in-out infinite;
	}

	@keyframes nodePulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.8; }
	}

	.distribution-chart {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.dist-item {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.dist-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.dist-region {
		font-size: 0.75rem;
		color: #e0e0e0;
		font-weight: 500;
	}

	.dist-count {
		font-size: 0.75rem;
		color: #b8a678;
	}

	.dist-visual {
		position: relative;
		height: 8px;
	}

	.dist-track {
		position: absolute;
		width: 100%;
		height: 100%;
		background: rgba(10, 79, 60, 0.1);
		border-radius: 4px;
	}

	.dist-fill {
		position: relative;
		height: 100%;
		border-radius: 4px;
		overflow: hidden;
	}

	.dist-glow {
		position: absolute;
		right: 0;
		top: 0;
		width: 20px;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5));
		animation: glowMove 2s linear infinite;
	}

	@keyframes glowMove {
		0% { transform: translateX(-20px); }
		100% { transform: translateX(0); }
	}

	.dist-stats {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.dist-percentage {
		font-size: 0.7rem;
		color: #0a4f3c;
		font-weight: 600;
	}

	.dist-status {
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.threat-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
	}

	.threat-cell {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid;
		border-radius: 4px;
		padding: 1rem;
		text-align: center;
	}

	.threat-region {
		font-size: 0.7rem;
		color: #b8a678;
		margin-bottom: 0.5rem;
		letter-spacing: 0.05em;
	}

	.threat-visual {
		display: flex;
		justify-content: center;
		margin: 0.5rem 0;
	}

	.threat-svg {
		width: 50px;
		height: 50px;
	}

	.threat-level {
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
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
		border-bottom: 2px solid #0a4f3c;
		background: rgba(10, 79, 60, 0.05);
	}

	.drill-header h4 {
		margin: 0;
		color: #0a4f3c;
		font-size: 1.1rem;
		letter-spacing: 0.1em;
	}

	.close-btn {
		background: rgba(255, 0, 102, 0.1);
		border: 1px solid #ff0066;
		width: 35px;
		height: 35px;
		border-radius: 2px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}

	.close-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: scale(1.1);
	}

	.drill-table-container {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}

	.host-cell {
		font-family: 'Courier New', monospace;
		color: #0a4f3c;
		font-weight: 600;
	}

	.status-badge.active {
		background: rgba(10, 79, 60, 0.2);
		color: #0a4f3c;
		border: 1px solid #0a4f3c;
	}

	.status-badge.inactive {
		background: rgba(255, 0, 102, 0.1);
		color: #ff0066;
		border: 1px solid #ff0066;
	}
</style>