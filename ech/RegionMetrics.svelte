<!-- RegionMetrics.svelte - Premium Regional Dashboard -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';
	let hoveredIndex = -1;

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

	$: filteredRegions = data.global_surveillance ? 
		Object.entries(data.global_surveillance)
			.filter(([region]) => region.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredRegions.length > 0 ? Math.max(...filteredRegions.map(([,c]) => c)) : 1;

	function getPercentage(count) {
		if (!data.total_coverage) return 0;
		return ((count / data.total_coverage) * 100).toFixed(2);
	}

	function getThreatLevel(count) {
		const percentage = (count / maxCount) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#FF1744', glow: 'rgba(255, 23, 68, 0.4)' };
		if (percentage >= 50) return { level: 'HIGH', color: '#FFA726', glow: 'rgba(255, 167, 38, 0.4)' };
		if (percentage >= 25) return { level: 'MEDIUM', color: '#FFD600', glow: 'rgba(255, 214, 0, 0.4)' };
		return { level: 'LOW', color: '#00E5FF', glow: 'rgba(0, 229, 255, 0.4)' };
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
	<!-- World Map Visualization -->
	<div class="map-section">
		<div class="map-header">
			<h2 class="section-title">
				<span class="title-icon">🌍</span>
				GLOBAL SURVEILLANCE NETWORK
			</h2>
			<div class="map-stats">
				<div class="stat-item">
					<span class="stat-value">{filteredRegions.length}</span>
					<span class="stat-label">REGIONS</span>
				</div>
				<div class="stat-item">
					<span class="stat-value">{(data.total_coverage || 0).toLocaleString()}</span>
					<span class="stat-label">ASSETS</span>
				</div>
			</div>
		</div>
		<div class="world-map">
			<svg viewBox="0 0 1000 500" class="map-svg">
				<defs>
					<radialGradient id="regionGlow">
						<stop offset="0%" style="stop-color:#00E5FF;stop-opacity:0.8" />
						<stop offset="100%" style="stop-color:#00E5FF;stop-opacity:0" />
					</radialGradient>
				</defs>
				
				<!-- Simplified world map regions -->
				<g class="map-regions">
					{#each filteredRegions as [region, count], i}
						{@const threat = getThreatLevel(count)}
						{@const x = i === 0 ? 200 : i === 1 ? 500 : i === 2 ? 800 : i === 3 ? 350 : 650}
						{@const y = i === 0 ? 200 : i === 1 ? 150 : i === 2 ? 250 : i === 3 ? 350 : 300}
						{@const size = (count / maxCount) * 30 + 10}
						
						<g class="region-marker" on:click={() => drillDownRegion(region, count)}>
							<circle cx="{x}" cy="{y}" r="{size * 2}" 
									fill={threat.color} opacity="0.1"/>
							<circle cx="{x}" cy="{y}" r="{size}" 
									fill={threat.color} opacity="0.3"/>
							<circle cx="{x}" cy="{y}" r="{size/2}" 
									fill={threat.color} opacity="0.8"/>
							<text x="{x}" y="{y - size - 10}" 
								  text-anchor="middle" 
								  fill="#ffffff" 
								  font-size="12" 
								  font-weight="600">
								{region.toUpperCase()}
							</text>
							<text x="{x}" y="{y + 4}" 
								  text-anchor="middle" 
								  fill="#ffffff" 
								  font-size="10" 
								  opacity="0.8">
								{count.toLocaleString()}
							</text>
						</g>
					{/each}
				</g>
				
				<!-- Connection lines -->
				{#if filteredRegions.length > 1}
					{#each filteredRegions as [region1, count1], i}
						{#each filteredRegions.slice(i + 1) as [region2, count2], j}
							{@const x1 = i === 0 ? 200 : i === 1 ? 500 : i === 2 ? 800 : i === 3 ? 350 : 650}
							{@const y1 = i === 0 ? 200 : i === 1 ? 150 : i === 2 ? 250 : i === 3 ? 350 : 300}
							{@const x2 = (i + j + 1) === 0 ? 200 : (i + j + 1) === 1 ? 500 : (i + j + 1) === 2 ? 800 : (i + j + 1) === 3 ? 350 : 650}
							{@const y2 = (i + j + 1) === 0 ? 200 : (i + j + 1) === 1 ? 150 : (i + j + 1) === 2 ? 250 : (i + j + 1) === 3 ? 350 : 300}
							<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
								  stroke="rgba(0, 229, 255, 0.2)" 
								  stroke-width="1" 
								  stroke-dasharray="5,5"/>
						{/each}
					{/each}
				{/if}
			</svg>
		</div>
	</div>

	<!-- Data Grid Section -->
	<div class="data-section">
		<div class="section-header">
			<input 
				type="text" 
				bind:value={searchTerm}
				placeholder="Search regions..."
				class="search-input"
			/>
		</div>
		
		{#if loading && !selectedRegion}
			<div class="loading-state">
				<div class="pulse-loader"></div>
				<p>Scanning global networks...</p>
			</div>
		{:else if selectedRegion}
			<div class="detail-view">
				<div class="detail-header">
					<h3>{selectedRegion.region.toUpperCase()} - {selectedRegion.count.toLocaleString()} ASSETS</h3>
					<button class="close-btn" on:click={closeDetails}>×</button>
				</div>
				<div class="detail-grid">
					<table class="detail-table">
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
									<td class="mono">{host.host}</td>
									<td>{host.country || 'Unknown'}</td>
									<td>{host.infrastructure_type || 'Unknown'}</td>
									<td>
										<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
											{host.present_in_cmdb?.toLowerCase().includes('yes') ? '✓' : '✗'}
										</span>
									</td>
									<td>
										<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'warning'}">
											{host.tanium_coverage?.toLowerCase().includes('tanium') ? '✓' : '✗'}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{:else}
			<div class="regions-grid">
				{#each filteredRegions as [region, count], index}
					{@const threat = getThreatLevel(count)}
					{@const percentage = getPercentage(count)}
					<div class="region-card {hoveredIndex === index ? 'hovered' : ''}"
						on:click={() => drillDownRegion(region, count)}
						on:mouseenter={() => hoveredIndex = index}
						on:mouseleave={() => hoveredIndex = -1}
						style="border-color: {threat.color}20; background: linear-gradient(135deg, {threat.color}05, transparent)">
						
						<div class="card-header">
							<h3 class="region-name">{region.toUpperCase()}</h3>
							<span class="threat-indicator" style="background: {threat.color}; box-shadow: 0 0 20px {threat.glow}">
								{threat.level}
							</span>
						</div>
						
						<div class="card-metrics">
							<div class="metric">
								<span class="metric-value" style="color: {threat.color}">{count.toLocaleString()}</span>
								<span class="metric-label">ASSETS</span>
							</div>
							<div class="metric">
								<span class="metric-value" style="color: {threat.color}">{percentage}%</span>
								<span class="metric-label">COVERAGE</span>
							</div>
						</div>
						
						<div class="card-footer">
							<div class="coverage-bar">
								<div class="coverage-fill" style="width: {(count/maxCount)*100}%; background: {threat.color}"></div>
							</div>
							<div class="activity-indicator">
								<span class="pulse" style="background: {threat.color}"></span>
								<span class="activity-text">MONITORING</span>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>

<style>
	.dashboard-container {
		height: calc(100vh - 80px);
		width: 100%;
		display: grid;
		grid-template-rows: 300px 1fr;
		gap: 1.5rem;
		background: #000000;
		overflow: hidden;
	}

	/* Map Section */
	.map-section {
		background: linear-gradient(135deg, rgba(0, 229, 255, 0.03), transparent);
		border: 1px solid rgba(0, 229, 255, 0.1);
		border-radius: 20px;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
	}

	.map-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.section-title {
		margin: 0;
		font-size: 1.1rem;
		font-weight: 600;
		color: #00E5FF;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.title-icon {
		font-size: 1.5rem;
	}

	.map-stats {
		display: flex;
		gap: 2rem;
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.stat-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #00E5FF;
		text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
	}

	.stat-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}

	.world-map {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}

	.map-svg {
		width: 100%;
		height: 100%;
		max-height: 220px;
	}

	.region-marker {
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.region-marker:hover {
		transform: scale(1.1);
	}

	/* Data Section */
	.data-section {
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 20px;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.section-header {
		margin-bottom: 1.5rem;
	}

	.search-input {
		width: 100%;
		padding: 0.75rem 1rem;
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		color: #ffffff;
		font-size: 0.9rem;
		transition: all 0.3s ease;
	}

	.search-input:focus {
		outline: none;
		border-color: #00E5FF;
		background: rgba(0, 229, 255, 0.05);
	}

	/* Regions Grid */
	.regions-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1rem;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.region-card {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid;
		border-radius: 16px;
		padding: 1.25rem;
		cursor: pointer;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.region-card:hover {
		transform: translateY(-4px);
		box-shadow: 0 12px 32px rgba(0, 0, 0, 0.8);
	}

	.region-card.hovered {
		border-width: 2px;
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.region-name {
		margin: 0;
		font-size: 0.95rem;
		font-weight: 600;
		color: #ffffff;
	}

	.threat-indicator {
		padding: 0.25rem 0.5rem;
		border-radius: 6px;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.card-metrics {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.metric {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}

	.metric-value {
		font-size: 1.25rem;
		font-weight: 600;
	}

	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.card-footer {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.coverage-bar {
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.activity-indicator {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}

	.pulse {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		animation: pulse 2s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.5); opacity: 0.5; }
	}

	.activity-text {
		letter-spacing: 0.05em;
		font-weight: 500;
	}

	/* Loading State */
	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}

	.pulse-loader {
		width: 60px;
		height: 60px;
		border-radius: 50%;
		background: radial-gradient(circle, transparent, #00E5FF);
		animation: pulseLoader 1.5s ease-in-out infinite;
	}

	@keyframes pulseLoader {
		0%, 100% { transform: scale(0.8); opacity: 0.5; }
		50% { transform: scale(1.2); opacity: 1; }
	}

	/* Detail View */
	.detail-view {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		background: rgba(0, 229, 255, 0.05);
		border-radius: 12px;
		margin-bottom: 1rem;
	}

	.detail-header h3 {
		margin: 0;
		font-size: 1rem;
		color: #00E5FF;
	}

	.close-btn {
		background: rgba(255, 23, 68, 0.1);
		border: none;
		color: #FF1744;
		width: 32px;
		height: 32px;
		border-radius: 8px;
		font-size: 1.5rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}

	.close-btn:hover {
		background: rgba(255, 23, 68, 0.2);
		transform: scale(1.1);
	}

	.detail-grid {
		flex: 1;
		overflow: auto;
	}

	.detail-table {
		width: 100%;
		border-collapse: collapse;
	}

	.detail-table th {
		background: rgba(0, 0, 0, 0.4);
		color: rgba(255, 255, 255, 0.6);
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
	}

	.detail-table td {
		padding: 0.75rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.mono {
		font-family: 'SF Mono', monospace;
		color: #00E5FF;
	}

	.status-badge {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border-radius: 6px;
		font-weight: 600;
		font-size: 0.8rem;
	}

	.status-badge.active {
		background: rgba(0, 229, 255, 0.2);
		color: #00E5FF;
	}

	.status-badge.inactive {
		background: rgba(255, 23, 68, 0.2);
		color: #FF1744;
	}

	.status-badge.warning {
		background: rgba(255, 214, 0, 0.2);
		color: #FFD600;
	}

	/* Responsive */
	@media (max-width: 1200px) {
		.regions-grid {
			grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		}
	}

	@media (max-width: 768px) {
		.dashboard-container {
			grid-template-rows: 200px 1fr;
		}

		.regions-grid {
			grid-template-columns: 1fr;
		}

		.map-stats {
			gap: 1rem;
		}

		.stat-value {
			font-size: 1.2rem;
		}
	}

	/* Scrollbar */
	.regions-grid::-webkit-scrollbar,
	.detail-grid::-webkit-scrollbar {
		width: 6px;
	}

	.regions-grid::-webkit-scrollbar-track,
	.detail-grid::-webkit-scrollbar-track {
		background: rgba(255, 255, 255, 0.02);
	}

	.regions-grid::-webkit-scrollbar-thumb,
	.detail-grid::-webkit-scrollbar-thumb {
		background: rgba(0, 229, 255, 0.2);
		border-radius: 3px;
	}

	.regions-grid::-webkit-scrollbar-thumb:hover,
	.detail-grid::-webkit-scrollbar-thumb:hover {
		background: rgba(0, 229, 255, 0.3);
	}
</style>