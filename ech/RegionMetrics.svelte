<!-- RegionMetrics.svelte - Enhanced with Moving Graph -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';
	
	// Animation states
	let animationFrame = null;
	let pulsePhase = 0;
	let networkActivity = [];
	let dataFlow = [];
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/region_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Failed to load region metrics:', err);
			loading = false;
		}
		
		// Start animations
		const animate = () => {
			pulsePhase = (pulsePhase + 0.02) % (Math.PI * 2);
			
			// Generate network activity patterns
			networkActivity = Array(50).fill(0).map((_, i) => 
				50 + Math.sin(Date.now() * 0.002 + i * 0.2) * 30 + Math.random() * 20
			);
			
			// Generate data flow
			dataFlow = Array(30).fill(0).map((_, i) => ({
				value: 40 + Math.sin(Date.now() * 0.001 + i * 0.3) * 35,
				peak: Math.random() > 0.95
			}));
			
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
	$: avgHosts = regions.length > 0 ? Math.round(totalHosts / regions.length) : 0;
	
	// Key metrics
	$: regionCount = regions.length;
	$: topRegion = regions[0] || ['N/A', 0];
	$: coverage = topRegion[1] > 0 ? ((topRegion[1] / totalHosts) * 100).toFixed(1) : 0;
	$: globalSpread = ((regionCount / 7) * 100).toFixed(1); // Assume 7 major regions
	
	// Top performers
	$: topFive = regions.slice(0, 5);
	
	async function selectRegion(region, count) {
		selectedRegion = { region, count };
		loading = true;
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(region)}`);
			let result = await response.json();
			regionDetails = result.hosts || [];
		} catch (err) {
			console.error('Failed to load region details:', err);
			regionDetails = [];
		}
		loading = false;
	}
	
	function closeDetails() {
		selectedRegion = null;
		regionDetails = [];
	}
	
	function getRegionStatus(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#BD93F9' };
		if (percentage >= 50) return { level: 'HIGH', color: '#8BE9FD' };
		if (percentage >= 25) return { level: 'MODERATE', color: '#50FA7B' };
		return { level: 'LOW', color: '#FFB86C' };
	}
	
	function getRegionSize(count) {
		if (count > 20000) return 'MEGA';
		if (count > 10000) return 'LARGE';
		if (count > 5000) return 'MEDIUM';
		if (count > 1000) return 'SMALL';
		return 'MINIMAL';
	}
</script>

<div class="region-interface">
	<!-- Top Metrics -->
	<div class="metrics-header">
		<div class="metric-card">
			<div class="metric-icon">🌍</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #BD93F9">{regionCount}</div>
				<div class="metric-label">REGIONS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">💻</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #8BE9FD">{totalHosts.toLocaleString()}</div>
				<div class="metric-label">TOTAL HOSTS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📍</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #50FA7B; font-size: 1.2rem">
					{topRegion[0].substring(0, 25).toUpperCase()}
				</div>
				<div class="metric-label">TOP REGION</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">🌐</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FFB86C">{globalSpread}%</div>
				<div class="metric-label">GLOBAL SPREAD</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📊</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FF79C6">{avgHosts.toLocaleString()}</div>
				<div class="metric-label">AVG HOSTS/REGION</div>
			</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content-layout">
		<!-- Left: Region Network -->
		<div class="region-panel">
			<div class="panel-header">
				<h2>GLOBAL REGIONAL NETWORK</h2>
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="Search regions..."
					   class="search-input"/>
			</div>
			
			{#if loading && !selectedRegion}
				<div class="loading-state">
					<div class="region-loader">
						<div class="globe-ring ring-1"></div>
						<div class="globe-ring ring-2"></div>
						<div class="globe-ring ring-3"></div>
						<div class="globe-core"></div>
					</div>
					<p>SCANNING REGIONAL INFRASTRUCTURE...</p>
				</div>
			{:else if selectedRegion}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedRegion.region.toUpperCase()}</h3>
							<div class="region-stats">
								<span>{selectedRegion.count.toLocaleString()} HOSTS</span>
								<span>•</span>
								<span>{((selectedRegion.count / totalHosts) * 100).toFixed(2)}% OF GLOBAL</span>
								<span>•</span>
								<span>{getRegionSize(selectedRegion.count)} REGION</span>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="hosts-container">
						<table class="hosts-table">
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>COUNTRY</th>
									<th>DATA CENTER</th>
									<th>TYPE</th>
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
										<td>{host.data_center || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>{host.business_unit || 'UNKNOWN'}</td>
										<td>
											<span class="status-dot {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												●
											</span>
										</td>
										<td>
											<span class="status-dot {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												●
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="region-visualization">
					<!-- Global Map Visualization -->
					<div class="global-map">
						<svg viewBox="0 0 800 400">
							<!-- World map background -->
							<rect width="800" height="400" fill="rgba(0,0,0,0.3)" rx="10"/>
							
							<!-- Region nodes positioned globally -->
							{#each regions.slice(0, 10) as [region, count], i}
								{@const status = getRegionStatus(count)}
								{@const radius = Math.sqrt(count / maxHosts) * 50}
								{@const x = 100 + (i % 4) * 180}
								{@const y = 100 + Math.floor(i / 4) * 120}
								
								<g class="region-node-group" on:click={() => selectRegion(region, count)}>
									<!-- Pulse effect -->
									<circle cx="{x}" cy="{y}" r="{radius + 10}"
											fill="{status.color}" 
											opacity="{0.1 + Math.sin(pulsePhase + i) * 0.1}"/>
									<circle cx="{x}" cy="{y}" r="{radius}"
											fill="{status.color}" 
											opacity="0.3"/>
									<circle cx="{x}" cy="{y}" r="{radius * 0.7}"
											fill="{status.color}" 
											opacity="0.6"/>
									
									<!-- Region label -->
									<text x="{x}" y="{y - radius - 10}" 
										  text-anchor="middle" 
										  fill="#FFFFFF" 
										  font-size="10" 
										  font-weight="600">
										{region.substring(0, 15).toUpperCase()}
									</text>
									
									<!-- Host count -->
									<text x="{x}" y="{y + 5}" 
										  text-anchor="middle" 
										  fill="#FFFFFF" 
										  font-size="14" 
										  font-weight="700">
										{count.toLocaleString()}
									</text>
								</g>
							{/each}
							
							<!-- Connection lines between regions -->
							{#each regions.slice(0, 10) as [region1, count1], i}
								{#each regions.slice(i + 1, 10) as [region2, count2], j}
									{#if Math.random() > 0.6}
										{@const x1 = 100 + (i % 4) * 180}
										{@const y1 = 100 + Math.floor(i / 4) * 120}
										{@const x2 = 100 + ((i + j + 1) % 4) * 180}
										{@const y2 = 100 + Math.floor((i + j + 1) / 4) * 120}
										<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
											  stroke="rgba(139, 233, 253, 0.2)" 
											  stroke-width="1"
											  stroke-dasharray="5,5">
											<animate attributeName="stroke-dashoffset"
													 values="0;-10" dur="2s" repeatCount="indefinite"/>
										</line>
									{/if}
								{/each}
							{/each}
						</svg>
					</div>
					
					<!-- Network Activity Graph -->
					<div class="network-activity">
						<svg viewBox="0 0 200 50">
							<polyline points="{networkActivity.map((val, i) => `${i * 4},${50 - val * 0.5}`).join(' ')}"
									  fill="none" 
									  stroke="#8BE9FD" 
									  stroke-width="1"
									  opacity="0.8"/>
							{#each dataFlow as point, i}
								{#if point.peak}
									<circle cx="{i * 6.7}" cy="{50 - point.value * 0.5}" 
											r="2" fill="#FF79C6" opacity="0.8"/>
								{/if}
							{/each}
						</svg>
						<div class="activity-label">REGIONAL NETWORK ACTIVITY</div>
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Middle: Analytics -->
		<div class="analytics-panel">
			<!-- Distribution Chart -->
			<div class="chart-box">
				<h3>HOST DISTRIBUTION BY REGION</h3>
				<div class="distribution-bars">
					{#each topFive as [region, count], i}
						{@const percentage = (count / maxHosts) * 100}
						{@const status = getRegionStatus(count)}
						<div class="dist-item" on:click={() => selectRegion(region, count)}>
							<div class="dist-rank">#{i + 1}</div>
							<div class="dist-name">{region.substring(0, 12).toUpperCase()}</div>
							<div class="dist-bar">
								<div class="dist-fill" 
									 style="width: {percentage}%; 
											background: linear-gradient(90deg, {status.color}40, {status.color})">
									<span class="dist-value">{count.toLocaleString()}</span>
								</div>
							</div>
							<div class="dist-percent">{((count/totalHosts)*100).toFixed(1)}%</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Regional Size Distribution -->
			<div class="chart-box">
				<h3>REGIONAL SIZE DISTRIBUTION</h3>
				<div class="size-chart">
					{@const sizeGroups = regions.reduce((acc, [reg, count]) => {
						const size = getRegionSize(count);
						acc[size] = (acc[size] || 0) + 1;
						return acc;
					}, {})}
					{#each Object.entries(sizeGroups) as [size, count], i}
						{@const colors = ['#BD93F9', '#8BE9FD', '#50FA7B', '#FFB86C', '#FF79C6']}
						<div class="size-item">
							<div class="size-label">{size}</div>
							<div class="size-count" style="color: {colors[i % 5]}">{count}</div>
							<div class="size-bar">
								<div class="size-fill" 
									 style="height: {(count / regionCount) * 100}%; 
											background: {colors[i % 5]}">
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Coverage Stats -->
			<div class="chart-box">
				<h3>REGIONAL STATISTICS</h3>
				<div class="coverage-stats">
					<div class="coverage-item">
						<span class="coverage-label">Regions with >5K hosts</span>
						<span class="coverage-value" style="color: #BD93F9">
							{regions.filter(([_, c]) => c > 5000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Regions with >10K hosts</span>
						<span class="coverage-value" style="color: #8BE9FD">
							{regions.filter(([_, c]) => c > 10000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Regions with >20K hosts</span>
						<span class="coverage-value" style="color: #50FA7B">
							{regions.filter(([_, c]) => c > 20000).length}
						</span>
					</div>
				</div>
			</div>
		</div>
		
		<!-- Right: Region List -->
		<div class="list-panel">
			<div class="panel-header">
				<h3>ALL REGIONS</h3>
				<span class="region-count">{regions.length} TOTAL</span>
			</div>
			<div class="region-list">
				<table class="regions-table">
					<thead>
						<tr>
							<th>#</th>
							<th>REGION</th>
							<th>HOSTS</th>
							<th>SIZE</th>
							<th>STATUS</th>
						</tr>
					</thead>
					<tbody>
						{#each regions as [region, count], i}
							{@const status = getRegionStatus(count)}
							{@const size = getRegionSize(count)}
							<tr on:click={() => selectRegion(region, count)}>
								<td class="rank">{i + 1}</td>
								<td class="region-name">
									<span class="status-indicator" style="background: {status.color}"></span>
									{region.substring(0, 25).toUpperCase()}
								</td>
								<td class="host-count" style="color: {status.color}">
									{count.toLocaleString()}
								</td>
								<td>
									<span class="size-badge" style="color: {status.color}">
										{size}
									</span>
								</td>
								<td>
									<span class="status-badge" style="color: {status.color}; border-color: {status.color}">
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

<style>
	.region-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		display: flex;
		flex-direction: column;
		padding: 1rem;
		gap: 1rem;
		overflow: hidden;
	}
	
	/* Metrics Header */
	.metrics-header {
		display: flex;
		gap: 1rem;
	}
	
	.metric-card {
		flex: 1;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		gap: 1rem;
		align-items: center;
	}
	
	.metric-icon {
		font-size: 2rem;
	}
	
	.metric-content {
		flex: 1;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
		margin-bottom: 0.25rem;
	}
	
	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		font-weight: 600;
	}
	
	/* Content Layout */
	.content-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 380px 320px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Region Panel */
	.region-panel {
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
		width: 180px;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #8BE9FD;
	}
	
	.region-visualization {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		position: relative;
	}
	
	/* Global Map */
	.global-map {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 8px;
		padding: 1rem;
	}
	
	.global-map svg {
		width: 100%;
		height: 100%;
	}
	
	.region-node-group {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.region-node-group:hover {
		transform: scale(1.1);
	}
	
	/* Network Activity */
	.network-activity {
		position: absolute;
		bottom: 20px;
		left: 20px;
		right: 20px;
		height: 60px;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(139, 233, 253, 0.3);
		padding: 5px;
		border-radius: 10px;
	}
	
	.network-activity svg {
		width: 100%;
		height: 100%;
	}
	
	.activity-label {
		position: absolute;
		top: 5px;
		left: 10px;
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}
	
	/* Analytics Panel */
	.analytics-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chart-box {
		flex: 1;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
	}
	
	.chart-box h3 {
		margin: 0 0 1rem 0;
		font-size: 0.75rem;
		color: #8BE9FD;
		font-weight: 300;
		letter-spacing: 0.1em;
	}
	
	.distribution-bars {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.dist-item {
		display: grid;
		grid-template-columns: 25px 100px 1fr 45px;
		gap: 0.5rem;
		align-items: center;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	.dist-item:hover {
		transform: translateX(2px);
	}
	
	.dist-rank {
		font-size: 0.65rem;
		color: #BD93F9;
		font-weight: 600;
	}
	
	.dist-name {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.dist-bar {
		height: 18px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.dist-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.4rem;
		transition: width 0.5s ease;
	}
	
	.dist-value {
		font-size: 0.6rem;
		color: #FFFFFF;
		font-weight: 600;
	}
	
	.dist-percent {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		text-align: right;
	}
	
	/* Size Chart */
	.size-chart {
		display: flex;
		align-items: flex-end;
		justify-content: space-around;
		height: 100px;
	}
	
	.size-item {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.3rem;
	}
	
	.size-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		writing-mode: vertical-lr;
		text-align: center;
	}
	
	.size-count {
		font-size: 0.9rem;
		font-weight: 700;
	}
	
	.size-bar {
		width: 30px;
		height: 60px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px 4px 0 0;
		display: flex;
		align-items: flex-end;
	}
	
	.size-fill {
		width: 100%;
		border-radius: 4px 4px 0 0;
		transition: height 0.5s ease;
	}
	
	/* Coverage Stats */
	.coverage-stats {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.coverage-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 6px;
	}
	
	.coverage-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.coverage-value {
		font-size: 1rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
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
		font-size: 0.6rem;
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
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank {
		color: #BD93F9;
		font-weight: 600;
		font-size: 0.65rem;
	}
	
	.region-name {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.65rem;
	}
	
	.status-indicator {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.host-count {
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.size-badge {
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}
	
	.status-badge {
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
		margin: 0 0 0.25rem 0;
		font-size: 1.1rem;
		color: #BD93F9;
	}
	
	.region-stats {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		display: flex;
		gap: 0.5rem;
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
	}
	
	.hosts-container {
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
		padding: 0.5rem;
		text-align: left;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		letter-spacing: 0.05em;
	}
	
	.hosts-table td {
		padding: 0.5rem;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.hostname {
		font-family: 'Courier New', monospace;
		color: #8BE9FD;
		font-size: 0.6rem;
	}
	
	.status-dot {
		font-size: 0.8rem;
	}
	
	.status-dot.active {
		color: #50FA7B;
	}
	
	.status-dot.inactive {
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
	
	.region-loader {
		position: relative;
		width: 100px;
		height: 100px;
	}
	
	.globe-ring {
		position: absolute;
		border: 2px solid;
		border-radius: 50%;
		animation: ringRotate 2s linear infinite;
	}
	
	.ring-1 {
		width: 100px;
		height: 100px;
		border-color: #BD93F9;
		animation-duration: 3s;
	}
	
	.ring-2 {
		width: 70px;
		height: 70px;
		top: 15px;
		left: 15px;
		border-color: #8BE9FD;
		animation-duration: 2s;
		animation-direction: reverse;
	}
	
	.ring-3 {
		width: 40px;
		height: 40px;
		top: 30px;
		left: 30px;
		border-color: #50FA7B;
		animation-duration: 1s;
	}
	
	.globe-core {
		position: absolute;
		width: 20px;
		height: 20px;
		top: 40px;
		left: 40px;
		background: linear-gradient(135deg, #FF79C6, #FFB86C);
		border-radius: 50%;
		animation: corePulse 2s ease-in-out infinite;
	}
	
	@keyframes ringRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	@keyframes corePulse {
		0%, 100% { transform: scale(1); opacity: 0.8; }
		50% { transform: scale(1.2); opacity: 1; }
	}
	
	.loading-state p {
		color: rgba(255, 255, 255, 0.5);
		font-size: 0.8rem;
		letter-spacing: 0.2em;
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 6px;
	}
	
	::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.5);
	}
	
	::-webkit-scrollbar-thumb {
		background: rgba(189, 147, 249, 0.3);
		border-radius: 3px;
	}