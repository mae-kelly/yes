<!-- RegionMetrics.svelte - Regional Host Distribution -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';
	
	// Animation states
	let animationFrame = null;
	let rotationAngle = 0;
	
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
		
		// Start animations
		const animate = () => {
			rotationAngle = (rotationAngle + 0.5) % 360;
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});

	$: regions = data.global_surveillance ? 
		Object.entries(data.global_surveillance)
			.filter(([region]) => region.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = regions.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = regions.length > 0 ? Math.max(...regions.map(([,c]) => c)) : 1;
	$: avgHostsPerRegion = regions.length > 0 ? Math.round(totalHosts / regions.length) : 0;
	
	// Regional distribution metrics
	$: topRegion = regions[0] || ['N/A', 0];
	$: regionCoverage = regions.length;
	$: hostConcentration = topRegion[1] > 0 ? ((topRegion[1] / totalHosts) * 100).toFixed(1) : 0;

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
	
	function getRegionColor(index) {
		const colors = ['#BD93F9', '#8BE9FD', '#50FA7B', '#FFB86C', '#FF79C6'];
		return colors[index % colors.length];
	}
	
	function getRegionStatus(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'HIGH DENSITY', color: '#BD93F9' };
		if (percentage >= 50) return { level: 'MODERATE', color: '#8BE9FD' };
		if (percentage >= 25) return { level: 'LOW DENSITY', color: '#50FA7B' };
		return { level: 'MINIMAL', color: '#FFB86C' };
	}
</script>

<div class="region-interface">
	<div class="interface-layout">
		<!-- Top Metrics Bar -->
		<div class="metrics-bar">
			<div class="metric-item">
				<span class="metric-label">TOTAL REGIONS</span>
				<span class="metric-value" style="color: #BD93F9">{regionCoverage}</span>
			</div>
			<div class="metric-item">
				<span class="metric-label">TOTAL HOSTS</span>
				<span class="metric-value" style="color: #8BE9FD">{totalHosts.toLocaleString()}</span>
			</div>
			<div class="metric-item">
				<span class="metric-label">TOP REGION</span>
				<span class="metric-value" style="color: #50FA7B">{topRegion[0].toUpperCase()}</span>
			</div>
			<div class="metric-item">
				<span class="metric-label">CONCENTRATION</span>
				<span class="metric-value" style="color: #FFB86C">{hostConcentration}%</span>
			</div>
			<div class="metric-item">
				<span class="metric-label">AVG HOSTS/REGION</span>
				<span class="metric-value" style="color: #FF79C6">{avgHostsPerRegion.toLocaleString()}</span>
			</div>
		</div>
		
		<!-- Main Content Grid -->
		<div class="content-grid">
			<!-- Left Panel: World Map Visualization -->
			<div class="map-panel">
				<div class="panel-header">
					<h2>GLOBAL HOST DISTRIBUTION</h2>
					<input type="text"
						   bind:value={searchTerm}
						   placeholder="Search regions..."
						   class="search-input"/>
				</div>
				
				{#if loading && !selectedRegion}
					<div class="loading-state">
						<div class="globe-loader" style="transform: rotateY({rotationAngle}deg)">
							<div class="globe-ring ring-1"></div>
							<div class="globe-ring ring-2"></div>
							<div class="globe-ring ring-3"></div>
						</div>
						<p>SCANNING REGIONAL INFRASTRUCTURE...</p>
					</div>
				{:else if selectedRegion}
					<div class="detail-view">
						<div class="detail-header">
							<div>
								<h3>{selectedRegion.region.toUpperCase()}</h3>
								<span class="detail-stats">{selectedRegion.count.toLocaleString()} HOSTS</span>
							</div>
							<button class="close-btn" on:click={closeDetails}>✕</button>
						</div>
						<div class="hosts-grid">
							<table class="hosts-table">
								<thead>
									<tr>
										<th>HOSTNAME</th>
										<th>COUNTRY</th>
										<th>INFRASTRUCTURE</th>
										<th>DIVISION</th>
										<th>CMDB</th>
										<th>TANIUM</th>
									</tr>
								</thead>
								<tbody>
									{#each regionDetails as host}
										<tr>
											<td class="hostname">{host.host}</td>
											<td>{host.country || 'UNKNOWN'}</td>
											<td>{host.infrastructure_type || 'UNKNOWN'}</td>
											<td>{host.business_unit || 'UNKNOWN'}</td>
											<td>
												<span class="indicator {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
													{host.present_in_cmdb?.toLowerCase().includes('yes') ? '●' : '○'}
												</span>
											</td>
											<td>
												<span class="indicator {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
													{host.tanium_coverage?.toLowerCase().includes('tanium') ? '●' : '○'}
												</span>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				{:else}
					<div class="map-visualization">
						<!-- World Map SVG -->
						<svg viewBox="0 0 1000 500" class="world-map">
							<defs>
								<radialGradient id="regionGlow">
									<stop offset="0%" style="stop-color:#BD93F9;stop-opacity:0.8" />
									<stop offset="100%" style="stop-color:#BD93F9;stop-opacity:0" />
								</radialGradient>
							</defs>
							
							<!-- Simplified world regions -->
							{#each regions.slice(0, 10) as [region, count], i}
								{@const x = 100 + (i % 5) * 180}
								{@const y = 150 + Math.floor(i / 5) * 200}
								{@const radius = Math.sqrt(count / maxHosts) * 50}
								{@const color = getRegionColor(i)}
								
								<g class="region-node" on:click={() => drillDownRegion(region, count)}>
									<!-- Outer glow -->
									<circle cx="{x}" cy="{y}" r="{radius * 2}" 
											fill="{color}" opacity="0.1"/>
									<!-- Middle ring -->
									<circle cx="{x}" cy="{y}" r="{radius * 1.5}" 
											fill="none" stroke="{color}" stroke-width="1" opacity="0.3"/>
									<!-- Core -->
									<circle cx="{x}" cy="{y}" r="{radius}" 
											fill="{color}" opacity="0.6"/>
									<!-- Label -->
									<text x="{x}" y="{y - radius - 10}" 
										  text-anchor="middle" fill="#FFFFFF" font-size="11" font-weight="600">
										{region.toUpperCase()}
									</text>
									<text x="{x}" y="{y + 5}" 
										  text-anchor="middle" fill="#FFFFFF" font-size="14" font-weight="700">
										{count.toLocaleString()}
									</text>
								</g>
							{/each}
							
							<!-- Connection lines -->
							{#if regions.length > 1}
								{#each regions.slice(0, 10) as [region1, count1], i}
									{#each regions.slice(i + 1, 10) as [region2, count2], j}
										{@const x1 = 100 + (i % 5) * 180}
										{@const y1 = 150 + Math.floor(i / 5) * 200}
										{@const x2 = 100 + ((i + j + 1) % 5) * 180}
										{@const y2 = 150 + Math.floor((i + j + 1) / 5) * 200}
										<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
											  stroke="rgba(139, 233, 253, 0.1)" stroke-width="1"/>
									{/each}
								{/each}
							{/if}
						</svg>
					</div>
				{/if}
			</div>
			
			<!-- Middle Panel: Charts -->
			<div class="charts-panel">
				<!-- Pie Chart -->
				<div class="chart-container">
					<h3>REGIONAL DISTRIBUTION</h3>
					<div class="pie-chart">
						<svg viewBox="0 0 200 200">
							{#each regions.slice(0, 5) as [region, count], i}
								{@const total = regions.slice(0, 5).reduce((sum, [_, c]) => sum + c, 0)}
								{@const percentage = (count / total) * 100}
								{@const startAngle = regions.slice(0, i).reduce((sum, [_, c]) => sum + (c / total) * 360, 0)}
								{@const endAngle = startAngle + (percentage / 100) * 360}
								{@const color = getRegionColor(i)}
								
								<!-- Calculate path for pie slice -->
								{@const startRad = (startAngle * Math.PI) / 180}
								{@const endRad = (endAngle * Math.PI) / 180}
								{@const x1 = 100 + 80 * Math.cos(startRad)}
								{@const y1 = 100 + 80 * Math.sin(startRad)}
								{@const x2 = 100 + 80 * Math.cos(endRad)}
								{@const y2 = 100 + 80 * Math.sin(endRad)}
								{@const largeArc = percentage > 50 ? 1 : 0}
								
								<path d="M 100 100 L {x1} {y1} A 80 80 0 {largeArc} 1 {x2} {y2} Z"
									  fill="{color}" opacity="0.8" stroke="#000000" stroke-width="2"
									  class="pie-slice" on:click={() => drillDownRegion(region, count)}/>
								
								<!-- Label -->
								{@const labelAngle = (startAngle + endAngle) / 2}
								{@const labelRad = (labelAngle * Math.PI) / 180}
								{@const labelX = 100 + 50 * Math.cos(labelRad)}
								{@const labelY = 100 + 50 * Math.sin(labelRad)}
								<text x="{labelX}" y="{labelY}" text-anchor="middle" 
									  fill="#FFFFFF" font-size="10" font-weight="600">
									{percentage.toFixed(0)}%
								</text>
							{/each}
						</svg>
					</div>
					<div class="chart-legend">
						{#each regions.slice(0, 5) as [region, count], i}
							{@const color = getRegionColor(i)}
							<div class="legend-item">
								<span class="legend-color" style="background: {color}"></span>
								<span class="legend-label">{region.toUpperCase()}</span>
							</div>
						{/each}
					</div>
				</div>
				
				<!-- Bar Chart -->
				<div class="chart-container">
					<h3>TOP REGIONS BY HOST COUNT</h3>
					<div class="bar-chart">
						{#each regions.slice(0, 8) as [region, count], i}
							{@const percentage = (count / maxHosts) * 100}
							{@const status = getRegionStatus(count)}
							<div class="bar-row">
								<span class="bar-label">{region.substring(0, 12).toUpperCase()}</span>
								<div class="bar-track">
									<div class="bar-fill" 
										 style="width: {percentage}%; background: {status.color}">
										<span class="bar-value">{count.toLocaleString()}</span>
									</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
			
			<!-- Right Panel: Region List -->
			<div class="list-panel">
				<div class="panel-header">
					<h3>ALL REGIONS</h3>
					<span class="region-count">{regions.length} ACTIVE</span>
				</div>
				<div class="region-list">
					<table class="regions-table">
						<thead>
							<tr>
								<th>RANK</th>
								<th>REGION</th>
								<th>HOSTS</th>
								<th>%</th>
								<th>STATUS</th>
							</tr>
						</thead>
						<tbody>
							{#each regions as [region, count], i}
								{@const percentage = ((count / totalHosts) * 100).toFixed(1)}
								{@const status = getRegionStatus(count)}
								<tr on:click={() => drillDownRegion(region, count)}>
									<td class="rank">#{i + 1}</td>
									<td class="region-name">
										<span class="region-dot" style="background: {getRegionColor(i)}"></span>
										{region.toUpperCase()}
									</td>
									<td class="host-count" style="color: {status.color}">
										{count.toLocaleString()}
									</td>
									<td class="percentage">{percentage}%</td>
									<td>
										<span class="status-tag" style="color: {status.color}; border-color: {status.color}">
											{status.level}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.region-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.interface-layout {
		height: 100%;
		display: flex;
		flex-direction: column;
		padding: 1rem;
		gap: 1rem;
	}
	
	/* Metrics Bar */
	.metrics-bar {
		display: flex;
		justify-content: space-between;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 12px;
		padding: 1rem 2rem;
	}
	
	.metric-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}
	
	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		font-weight: 600;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
	}
	
	/* Content Grid */
	.content-grid {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 350px 300px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Map Panel */
	.map-panel {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
	}
	
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.panel-header h2, .panel-header h3 {
		margin: 0;
		font-size: 0.9rem;
		font-weight: 300;
		letter-spacing: 0.1em;
		color: #BD93F9;
	}
	
	.search-input {
		padding: 0.4rem 0.8rem;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(139, 233, 253, 0.3);
		border-radius: 6px;
		color: #FFFFFF;
		font-size: 0.75rem;
		width: 150px;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #8BE9FD;
		background: rgba(139, 233, 253, 0.05);
	}
	
	.map-visualization {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.world-map {
		width: 100%;
		height: 100%;
	}
	
	.region-node {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.region-node:hover {
		transform: scale(1.1);
	}
	
	/* Charts Panel */
	.charts-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chart-container {
		flex: 1;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
	}
	
	.chart-container h3 {
		margin: 0 0 1rem 0;
		font-size: 0.8rem;
		font-weight: 300;
		letter-spacing: 0.1em;
		color: #8BE9FD;
	}
	
	.pie-chart {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.pie-chart svg {
		width: 100%;
		height: 100%;
		max-height: 200px;
	}
	
	.pie-slice {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.pie-slice:hover {
		opacity: 1 !important;
		filter: brightness(1.2);
	}
	
	.chart-legend {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		justify-content: center;
		margin-top: 0.5rem;
	}
	
	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.legend-color {
		width: 10px;
		height: 10px;
		border-radius: 2px;
	}
	
	.bar-chart {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.bar-row {
		display: grid;
		grid-template-columns: 100px 1fr;
		gap: 0.5rem;
		align-items: center;
	}
	
	.bar-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
		text-align: right;
	}
	
	.bar-track {
		height: 20px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		display: flex;
		align-items: center;
		padding: 0 0.5rem;
		transition: width 0.5s ease;
		border-radius: 4px;
	}
	
	.bar-value {
		font-size: 0.65rem;
		color: #FFFFFF;
		font-weight: 600;
	}
	
	/* List Panel */
	.list-panel {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.region-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.region-list {
		flex: 1;
		overflow-y: auto;
	}
	
	.regions-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.regions-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.9);
		z-index: 10;
	}
	
	.regions-table th {
		padding: 0.5rem;
		text-align: left;
		font-size: 0.65rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.regions-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.regions-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.05);
	}
	
	.regions-table td {
		padding: 0.6rem 0.5rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank {
		color: #BD93F9;
		font-weight: 600;
	}
	
	.region-name {
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}
	
	.region-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
	}
	
	.host-count {
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.percentage {
		color: rgba(255, 255, 255, 0.6);
	}
	
	.status-tag {
		font-size: 0.6rem;
		padding: 0.15rem 0.3rem;
		border: 1px solid;
		border-radius: 4px;
		font-weight: 600;
		letter-spacing: 0.03em;
	}
	
	/* Detail View */
	.detail-view {
		flex: 1;
		display: flex;
		flex-direction: column;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: start;
		margin-bottom: 1rem;
	}
	
	.detail-header h3 {
		margin: 0;
		font-size: 1.1rem;
		color: #BD93F9;
		margin-bottom: 0.25rem;
	}
	
	.detail-stats {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.6);
	}
	
	.close-btn {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		color: #FFFFFF;
		width: 28px;
		height: 28px;
		border-radius: 6px;
		font-size: 1rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}
	
	.close-btn:hover {
		background: rgba(189, 147, 249, 0.2);
		border-color: #BD93F9;
		transform: scale(1.1);
	}
	
	.hosts-grid {
		flex: 1;
		overflow-y: auto;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 8px;
		padding: 1rem;
	}
	
	.hosts-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.hosts-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.9);
		z-index: 10;
	}
	
	.hosts-table th {
		padding: 0.6rem;
		text-align: left;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.hosts-table td {
		padding: 0.6rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.hostname {
		font-family: 'Courier New', monospace;
		color: #8BE9FD;
		font-size: 0.65rem;
	}
	
	.indicator {
		font-size: 0.9rem;
	}
	
	.indicator.active {
		color: #50FA7B;
	}
	
	.indicator.inactive {
		color: #FF5555;
	}
	
	/* Loading State */
	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.globe-loader {
		position: relative;
		width: 100px;
		height: 100px;
		transform-style: preserve-3d;
	}
	
	.globe-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid;
		border-radius: 50%;
		animation: globeSpin 2s linear infinite;
	}
	
	.ring-1 {
		border-color: #BD93F9;
		transform: rotateY(0deg);
	}
	
	.ring-2 {
		border-color: #8BE9FD;
		transform: rotateY(60deg);
	}
	
	.ring-3 {
		border-color: #50FA7B;
		transform: rotateY(120deg);
	}
	
	@keyframes globeSpin {
		to { transform: rotateY(360deg); }
	}
	
	.loading-state p {
		color: rgba(255, 255, 255, 0.5);
		font-size: 0.8rem;
		letter-spacing: 0.2em;
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 6px;
		height: 6px;
	}
	
	::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.5);
	}
	
	::-webkit-scrollbar-thumb {
		background: rgba(189, 147, 249, 0.3);
		border-radius: 3px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: rgba(189, 147, 249, 0.5);
	}
</style>