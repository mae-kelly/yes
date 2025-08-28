<!-- RegionMetrics.svelte - Enhanced Regional Analysis -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';
	let viewMode = 'globe'; // 'globe', 'table', 'radar'

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

	function getRegionStatus(count) {
		const percentage = (count / maxCount) * 100;
		if (percentage >= 80) return { status: 'DOMINANT', color: '#00ff88', icon: '◆' };
		if (percentage >= 60) return { status: 'STRONG', color: '#00ffff', icon: '▲' };
		if (percentage >= 40) return { status: 'MODERATE', color: '#ffcc00', icon: '●' };
		if (percentage >= 20) return { status: 'EMERGING', color: '#ff9900', icon: '■' };
		return { status: 'MINIMAL', color: '#ff0066', icon: '▼' };
	}

	function getRegionCode(region) {
		const codes = {
			'North America': 'NA',
			'EMEA': 'EU',
			'APAC': 'AP',
			'LATAM': 'LA',
			'Unknown': 'XX'
		};
		return codes[region] || region.substring(0, 2).toUpperCase();
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

	// Calculate angles for radar chart
	$: radarData = sortedRegions.slice(0, 8).map((item, i) => {
		const angle = (i / 8) * Math.PI * 2 - Math.PI / 2;
		const radius = (item[1] / maxCount) * 150;
		return {
			region: item[0],
			count: item[1],
			x: 200 + Math.cos(angle) * radius,
			y: 200 + Math.sin(angle) * radius,
			angle,
			radius
		};
	});
</script>

<div class="dashboard-container">
	<!-- Header Section -->
	<div class="module-header">
		<div class="header-content">
			<div class="module-title">
				<svg class="module-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="12" cy="12" r="10" />
					<path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
				</svg>
				<h1>REGIONS</h1>
				<span class="module-subtitle">// GLOBAL SURVEILLANCE NETWORK</span>
			</div>
			
			<div class="header-metrics">
				<div class="metric-badge">
					<span class="metric-icon">🌍</span>
					<span class="metric-value">{sortedRegions.length}</span>
					<span class="metric-label">REGIONS</span>
				</div>
				<div class="metric-badge">
					<span class="metric-icon">◆</span>
					<span class="metric-value">{(data.total_coverage || 0).toLocaleString()}</span>
					<span class="metric-label">ASSETS</span>
				</div>
				<div class="metric-badge">
					<span class="metric-icon">▲</span>
					<span class="metric-value">{maxCount.toLocaleString()}</span>
					<span class="metric-label">PEAK</span>
				</div>
			</div>
		</div>
		
		<div class="controls-bar">
			<input 
				type="text" 
				bind:value={searchTerm}
				placeholder="Search regions..."
				class="search-input"
			/>
			<div class="view-toggles">
				<button class="view-btn {viewMode === 'globe' ? 'active' : ''}" on:click={() => viewMode = 'globe'}>
					<span class="btn-icon">🌍</span> GLOBE
				</button>
				<button class="view-btn {viewMode === 'table' ? 'active' : ''}" on:click={() => viewMode = 'table'}>
					<span class="btn-icon">▦</span> TABLE
				</button>
				<button class="view-btn {viewMode === 'radar' ? 'active' : ''}" on:click={() => viewMode = 'radar'}>
					<span class="btn-icon">◈</span> RADAR
				</button>
			</div>
		</div>
	</div>

	<!-- Main Content Area -->
	<div class="main-content">
		{#if loading && !selectedRegion}
			<div class="loading-state">
				<div class="globe-loader">
					<div class="globe-ring"></div>
					<div class="globe-ring"></div>
					<div class="globe-ring"></div>
				</div>
				<p>ESTABLISHING SATELLITE UPLINK...</p>
			</div>
		{:else if selectedRegion}
			<!-- Drill-down View -->
			<div class="drill-view">
				<div class="drill-header">
					<div class="drill-title">
						<span class="drill-icon">🌍</span>
						<h3>{selectedRegion.region.toUpperCase()}</h3>
						<span class="drill-stats">// {selectedRegion.count.toLocaleString()} ASSETS</span>
					</div>
					<button class="close-btn" on:click={closeDetails}>
						<span>✕</span>
					</button>
				</div>
				
				<div class="drill-table-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>HOST IDENTIFIER</th>
								<th>COUNTRY</th>
								<th>INFRASTRUCTURE</th>
								<th>CMDB</th>
								<th>TANIUM</th>
							</tr>
						</thead>
						<tbody>
							{#each regionDetails as host}
								<tr>
									<td class="host-cell">
										<span class="host-icon">▸</span>
										{host.host}
									</td>
									<td>{host.country || 'Unknown'}</td>
									<td>{host.infrastructure_type || 'Unknown'}</td>
									<td>
										<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
											{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◉' : '○'}
										</span>
									</td>
									<td>
										<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
											{host.tanium_coverage?.toLowerCase().includes('tanium') ? '◉' : '○'}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{:else if viewMode === 'globe'}
			<!-- Globe View -->
			<div class="globe-view">
				<div class="globe-container">
					<svg viewBox="0 0 800 600" class="world-map">
						<defs>
							<radialGradient id="globeGrad">
								<stop offset="0%" style="stop-color:#00ffff;stop-opacity:0.3" />
								<stop offset="100%" style="stop-color:#00ffff;stop-opacity:0" />
							</radialGradient>
						</defs>
						
						<!-- World Grid -->
						<g class="grid-lines">
							{#each Array(6) as _, i}
								<line x1="0" y1={100 + i * 100} x2="800" y2={100 + i * 100} stroke="#0a4f3c" stroke-width="0.5" opacity="0.3"/>
								<line x1={133 + i * 133} y1="0" x2={133 + i * 133} y2="600" stroke="#0a4f3c" stroke-width="0.5" opacity="0.3"/>
							{/each}
						</g>
						
						<!-- Region Zones -->
						{#each sortedRegions as [region, count], i}
							{@const status = getRegionStatus(count)}
							{@const x = region.includes('America') ? 200 : 
									   region.includes('EMEA') ? 400 : 
									   region.includes('APAC') ? 600 : 
									   region.includes('LATAM') ? 250 : 400}
							{@const y = region.includes('America') ? 200 : 
									   region.includes('EMEA') ? 250 : 
									   region.includes('APAC') ? 300 : 
									   region.includes('LATAM') ? 400 : 450}
							{@const size = Math.sqrt(count / maxCount) * 120 + 40}
							
							<g class="region-zone" on:click={() => drillDownRegion(region, count)}>
								<circle cx={x} cy={y} r={size} fill="url(#globeGrad)" stroke={status.color} stroke-width="2" opacity="0.8">
									<animate attributeName="r" values="{size};{size + 5};{size}" dur="3s" repeatCount="indefinite"/>
								</circle>
								<circle cx={x} cy={y} r="5" fill={status.color}/>
								<text x={x} y={y - size - 10} text-anchor="middle" fill={status.color} font-size="14" font-weight="600">
									{getRegionCode(region)}
								</text>
								<text x={x} y={y + 20} text-anchor="middle" fill="#b8a678" font-size="10">
									{count.toLocaleString()}
								</text>
								<text x={x} y={y + 35} text-anchor="middle" fill="#666" font-size="9">
									{getPercentage(count)}%
								</text>
							</g>
						{/each}
						
						<!-- Connection Lines -->
						<g class="connections">
							{#each sortedRegions as [region, count], i}
								{#if i < sortedRegions.length - 1}
									{@const x1 = region.includes('America') ? 200 : 
											    region.includes('EMEA') ? 400 : 
											    region.includes('APAC') ? 600 : 250}
									{@const y1 = region.includes('America') ? 200 : 
											    region.includes('EMEA') ? 250 : 
											    region.includes('APAC') ? 300 : 400}
									{@const nextRegion = sortedRegions[i + 1][0]}
									{@const x2 = nextRegion.includes('America') ? 200 : 
											    nextRegion.includes('EMEA') ? 400 : 
											    nextRegion.includes('APAC') ? 600 : 250}
									{@const y2 = nextRegion.includes('America') ? 200 : 
											    nextRegion.includes('EMEA') ? 250 : 
											    nextRegion.includes('APAC') ? 300 : 400}
									
									<line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#0a4f3c" stroke-width="0.5" opacity="0.3" stroke-dasharray="5,5">
										<animate attributeName="stroke-dashoffset" values="0;10" dur="1s" repeatCount="indefinite"/>
									</line>
								{/if}
							{/each}
						</g>
					</svg>
				</div>
				
				<div class="region-cards">
					{#each sortedRegions as [region, count]}
						{@const status = getRegionStatus(count)}
						<div class="region-card" style="border-color: {status.color}">
							<div class="card-header">
								<span class="card-icon" style="color: {status.color}">{status.icon}</span>
								<span class="card-name">{region}</span>
							</div>
							<div class="card-metrics">
								<div class="card-stat">
									<span class="stat-value">{count.toLocaleString()}</span>
									<span class="stat-label">ASSETS</span>
								</div>
								<div class="card-stat">
									<span class="stat-value">{getPercentage(count)}%</span>
									<span class="stat-label">COVERAGE</span>
								</div>
							</div>
							<div class="card-status" style="color: {status.color}">{status.status}</div>
						</div>
					{/each}
				</div>
			</div>
		{:else if viewMode === 'table'}
			<!-- Table View -->
			<div class="table-view">
				<table class="data-table">
					<thead>
						<tr>
							<th>STATUS</th>
							<th>REGION</th>
							<th>CODE</th>
							<th>ASSET COUNT</th>
							<th>PERCENTAGE</th>
							<th>DISTRIBUTION</th>
						</tr>
					</thead>
					<tbody>
						{#each sortedRegions as [region, count]}
							{@const status = getRegionStatus(count)}
							<tr on:click={() => drillDownRegion(region, count)}>
								<td class="status-cell">
									<span class="status-icon" style="color: {status.color}">{status.icon}</span>
								</td>
								<td class="region-cell">
									<span class="region-name">{region.toUpperCase()}</span>
								</td>
								<td class="center">{getRegionCode(region)}</td>
								<td class="center">{count.toLocaleString()}</td>
								<td class="center">{getPercentage(count)}%</td>
								<td>
									<div class="coverage-cell">
										<div class="coverage-bar">
											<div class="coverage-fill" style="width: {(count/maxCount)*100}%; background: {status.color}"></div>
										</div>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{:else if viewMode === 'radar'}
			<!-- Radar View -->
			<div class="radar-view">
				<div class="radar-container">
					<svg viewBox="0 0 400 400" class="radar-chart">
						<!-- Radar Grid -->
						<g class="radar-grid">
							{#each [150, 120, 90, 60, 30] as radius}
								<circle cx="200" cy="200" r={radius} fill="none" stroke="#0a4f3c" stroke-width="0.5" opacity="0.3"/>
							{/each}
							
							{#each Array(8) as _, i}
								{@const angle = (i / 8) * Math.PI * 2}
								{@const x2 = 200 + Math.cos(angle) * 150}
								{@const y2 = 200 + Math.sin(angle) * 150}
								<line x1="200" y1="200" x2={x2} y2={y2} stroke="#0a4f3c" stroke-width="0.5" opacity="0.3"/>
							{/each}
						</g>
						
						<!-- Data Polygon -->
						<polygon 
							points={radarData.map(d => `${d.x},${d.y}`).join(' ')}
							fill="#00ff88" 
							fill-opacity="0.2" 
							stroke="#00ff88" 
							stroke-width="2"
						/>
						
						<!-- Data Points -->
						{#each radarData as point}
							{@const status = getRegionStatus(point.count)}
							<circle cx={point.x} cy={point.y} r="6" fill={status.color} stroke="#000" stroke-width="1">
								<animate attributeName="r" values="6;8;6" dur="2s" repeatCount="indefinite"/>
							</circle>
							<text x={point.x} y={point.y - 15} text-anchor="middle" fill={status.color} font-size="10" font-weight="600">
								{point.region.substring(0, 6)}
							</text>
						{/each}
						
						<!-- Center Point -->
						<circle cx="200" cy="200" r="3" fill="#00ffff"/>
						
						<!-- Scanning Line -->
						<line x1="200" y1="200" x2="200" y2="50" stroke="#00ffff" stroke-width="1" opacity="0.5" class="radar-sweep">
							<animateTransform
								attributeName="transform"
								attributeType="XML"
								type="rotate"
								from="0 200 200"
								to="360 200 200"
								dur="4s"
								repeatCount="indefinite"/>
						</line>
					</svg>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.dashboard-container {
		height: calc(100vh - 130px);
		display: flex;
		flex-direction: column;
		background: #0a0a0a;
		color: #e0e0e0;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
	}

	.module-header {
		background: linear-gradient(180deg, #0f0f0f 0%, #0a0a0a 100%);
		border-bottom: 1px solid #0a4f3c;
		padding: 1rem 1.5rem;
		flex-shrink: 0;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.module-title {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.module-icon {
		width: 32px;
		height: 32px;
		color: #00ffff;
		filter: drop-shadow(0 0 10px rgba(0, 255, 255, 0.5));
	}

	.module-title h1 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 700;
		background: linear-gradient(135deg, #00ffff, #00ff88);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		letter-spacing: 0.1em;
	}

	.module-subtitle {
		color: #666;
		font-size: 0.75rem;
		font-weight: 400;
		letter-spacing: 0.2em;
	}

	.header-metrics {
		display: flex;
		gap: 2rem;
	}

	.metric-badge {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 0.5rem 1rem;
		background: rgba(0, 255, 255, 0.05);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
	}

	.metric-icon {
		font-size: 1rem;
		margin-bottom: 0.25rem;
	}

	.metric-value {
		font-size: 1.25rem;
		font-weight: 600;
		color: #00ffff;
	}

	.metric-label {
		font-size: 0.6rem;
		color: #666;
		letter-spacing: 0.1em;
	}

	.controls-bar {
		display: flex;
		gap: 1rem;
		align-items: center;
	}

	.search-input {
		flex: 1;
		max-width: 400px;
		background: #000;
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		padding: 0.5rem 1rem;
		color: #e0e0e0;
		font-family: inherit;
		font-size: 0.85rem;
	}

	.search-input:focus {
		outline: none;
		border-color: #00ffff;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
	}

	.view-toggles {
		display: flex;
		gap: 0.5rem;
	}

	.view-btn {
		background: #000;
		border: 1px solid #0a4f3c;
		color: #666;
		padding: 0.5rem 1rem;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.2s ease;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-family: inherit;
		font-size: 0.75rem;
		letter-spacing: 0.05em;
	}

	.view-btn:hover {
		border-color: #00ffff;
		color: #00ffff;
		background: rgba(0, 255, 255, 0.05);
	}

	.view-btn.active {
		background: rgba(0, 255, 255, 0.1);
		border-color: #00ffff;
		color: #00ffff;
	}

	.btn-icon {
		font-size: 1rem;
	}

	.main-content {
		flex: 1;
		overflow: hidden;
		padding: 1rem;
	}

	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
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
		border: 2px solid transparent;
		border-top-color: #00ffff;
		border-radius: 50%;
		animation: globeSpin 1.5s linear infinite;
	}

	.globe-ring:nth-child(2) {
		width: 60px;
		height: 60px;
		top: 10px;
		left: 10px;
		border-top-color: #00ff88;
		animation-duration: 2s;
		animation-direction: reverse;
	}

	.globe-ring:nth-child(3) {
		width: 40px;
		height: 40px;
		top: 20px;
		left: 20px;
		border-top-color: #ff00ff;
		animation-duration: 2.5s;
	}

	@keyframes globeSpin {
		to { transform: rotate(360deg); }
	}

	.globe-view {
		height: 100%;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow: auto;
	}

	.globe-container {
		background: #0f0f0f;
		border: 1px solid #1a1a1a;
		border-radius: 8px;
		padding: 2rem;
		overflow: hidden;
	}

	.world-map {
		width: 100%;
		height: auto;
	}

	.region-zone {
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.region-zone:hover {
		opacity: 0.8;
		filter: brightness(1.2);
	}

	.region-cards {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 1rem;
	}

	.region-card {
		background: #0f0f0f;
		border: 1px solid;
		border-radius: 8px;
		padding: 1rem;
		transition: all 0.2s ease;
	}

	.region-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 20px rgba(0, 255, 255, 0.2);
	}

	.card-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.75rem;
	}

	.card-icon {
		font-size: 1.2rem;
	}

	.card-name {
		font-size: 0.9rem;
		color: #e0e0e0;
		font-weight: 500;
	}

	.card-metrics {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.75rem;
	}

	.card-stat {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.stat-value {
		font-size: 1rem;
		font-weight: 600;
		color: #00ffff;
	}

	.stat-label {
		font-size: 0.6rem;
		color: #666;
		letter-spacing: 0.1em;
		margin-top: 0.25rem;
	}

	.card-status {
		text-align: center;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.1em;
	}

	.table-view {
		height: 100%;
		overflow: auto;
		background: #0f0f0f;
		border: 1px solid #1a1a1a;
		border-radius: 8px;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.85rem;
	}

	.data-table th {
		background: #0f0f0f;
		color: #00ffff;
		padding: 0.75rem;
		text-align: left;
		font-weight: 500;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 2px solid #0a4f3c;
	}

	.data-table td {
		padding: 0.75rem;
		border-bottom: 1px solid #1a1a1a;
		color: #b8a678;
	}

	.data-table tbody tr {
		cursor: pointer;
		transition: background 0.2s ease;
	}

	.data-table tbody tr:hover {
		background: rgba(0, 255, 255, 0.03);
	}

	.status-cell {
		text-align: center;
	}

	.status-icon {
		font-size: 1rem;
	}

	.region-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.region-name {
		font-weight: 500;
		color: #e0e0e0;
	}

	.center {
		text-align: center;
	}

	.coverage-cell {
		display: flex;
		align-items: center;
	}

	.coverage-bar {
		flex: 1;
		height: 6px;
		background: #1a1a1a;
		border-radius: 3px;
		overflow: hidden;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.3s ease;
		box-shadow: 0 0 10px currentColor;
	}

	.radar-view {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #0f0f0f;
		border: 1px solid #1a1a1a;
		border-radius: 8px;
	}

	.radar-container {
		width: 100%;
		max-width: 600px;
		aspect-ratio: 1;
	}

	.radar-chart {
		width: 100%;
		height: 100%;
	}

	.drill-view {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: #0f0f0f;
		border: 1px solid #0a4f3c;
		border-radius: 8px;
		overflow: hidden;
	}

	.drill-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
		background: rgba(0, 255, 255, 0.05);
		border-bottom: 2px solid #0a4f3c;
	}

	.drill-title {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.drill-icon {
		font-size: 1.5rem;
	}

	.drill-title h3 {
		margin: 0;
		color: #00ffff;
		font-size: 1.2rem;
		letter-spacing: 0.1em;
	}

	.drill-stats {
		color: #666;
		font-size: 0.75rem;
		font-weight: 400;
	}

	.close-btn {
		background: rgba(255, 0, 102, 0.1);
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 36px;
		height: 36px;
		border-radius: 4px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.2rem;
		font-weight: 600;
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
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-family: 'Courier New', monospace;
		color: #00ffff;
		font-weight: 500;
	}

	.host-icon {
		color: #0a4f3c;
	}

	.status-badge {
		font-size: 1rem;
		transition: all 0.2s ease;
	}

	.status-badge.active {
		color: #00ff88;
		filter: drop-shadow(0 0 5px currentColor);
	}

	.status-badge.inactive {
		color: #ff0066;
		opacity: 0.5;
	}
</style>