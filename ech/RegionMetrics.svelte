<!-- RegionMetrics.svelte - Enhanced with fixes -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let error = null;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';
	let hoveredRegion = null;
	
	// Animation states
	let animationFrame = null;
	let networkActivity = [];
	let dataFlow = [];
	
	onMount(async () => {
		await loadData();
		initializeAnimations();
	});
	
	async function loadData() {
		loading = true;
		error = null;
		try {
			let response = await fetch('http://localhost:5000/api/region_metrics');
			if (!response.ok) throw new Error('Failed to fetch data');
			data = await response.json();
		} catch (err) {
			console.error('Failed to load region metrics:', err);
			error = 'Unable to load region data. Please try again.';
			// Use mock data for demonstration
			data = generateMockData();
		} finally {
			loading = false;
		}
	}
	
	function generateMockData() {
		return {
			global_surveillance: {
				'North America': 631301,
				'APAC': 73653,
				'EMEA': 58301,
				'LATAM': 34580,
				'Middle East': 28450,
				'Africa': 12890,
				'Oceania': 8650
			}
		};
	}
	
	function initializeAnimations() {
		// Initialize network activity
		for (let i = 0; i < 50; i++) {
			networkActivity.push(50 + Math.sin(i * 0.2) * 20);
			dataFlow.push({ value: 40, peak: false });
		}
		
		const animate = () => {
			// Smooth network activity animation
			networkActivity = networkActivity.map((val, i) => {
				const target = 50 + Math.sin(Date.now() * 0.001 + i * 0.2) * 25 + Math.random() * 10;
				return val * 0.9 + target * 0.1; // Smooth transition
			});
			
			// Generate data flow with occasional peaks
			dataFlow = dataFlow.map((point, i) => ({
				value: 40 + Math.sin(Date.now() * 0.0008 + i * 0.3) * 30,
				peak: Math.random() > 0.98
			}));
			
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	}
	
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
			regionDetails = generateMockHosts(region, Math.min(50, count));
		} finally {
			loading = false;
		}
	}
	
	function generateMockHosts(region, count) {
		const hosts = [];
		const countries = {
			'North America': ['United States', 'Canada', 'Mexico'],
			'EMEA': ['Germany', 'United Kingdom', 'France', 'Italy'],
			'APAC': ['Japan', 'China', 'Singapore', 'Australia'],
			'LATAM': ['Brazil', 'Argentina', 'Chile', 'Colombia']
		};
		
		for (let i = 0; i < count; i++) {
			const regionCountries = countries[region] || ['Unknown'];
			hosts.push({
				host: `${region.toLowerCase().replace(/\s/g, '-')}-srv-${i + 1}.internal`,
				country: regionCountries[Math.floor(Math.random() * regionCountries.length)],
				data_center: `DC-${region.substring(0, 3)}-${Math.floor(Math.random() * 5) + 1}`,
				infrastructure_type: ['Virtual', 'Physical', 'Cloud', 'Container'][Math.floor(Math.random() * 4)],
				business_unit: ['IT', 'Finance', 'Sales', 'Operations'][Math.floor(Math.random() * 4)],
				present_in_cmdb: Math.random() > 0.3 ? 'Yes' : 'No',
				tanium_coverage: Math.random() > 0.4 ? 'Tanium' : 'No Coverage'
			});
		}
		return hosts;
	}
	
	function closeDetails() {
		selectedRegion = null;
		regionDetails = [];
	}
	
	function getRegionStatus(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#FF6B9D', bgColor: '#FF6B9D20' };
		if (percentage >= 50) return { level: 'HIGH', color: '#4ECDC4', bgColor: '#4ECDC420' };
		if (percentage >= 25) return { level: 'MODERATE', color: '#95E77E', bgColor: '#95E77E20' };
		return { level: 'LOW', color: '#FFE66D', bgColor: '#FFE66D20' };
	}
	
	function getRegionSize(count) {
		if (count > 200000) return 'MEGA';
		if (count > 100000) return 'LARGE';
		if (count > 50000) return 'MEDIUM';
		if (count > 10000) return 'SMALL';
		return 'MINIMAL';
	}
	
	function formatNumber(num) {
		return new Intl.NumberFormat('en-US').format(num);
	}
	
	function truncateText(text, maxLength = 20) {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}
	
	// Calculate positions for non-overlapping region nodes
	function calculateNodePosition(index, total) {
		const positions = [
			{ x: 150, y: 100 },  // North America
			{ x: 400, y: 120 },  // Europe
			{ x: 550, y: 100 },  // Asia
			{ x: 200, y: 250 },  // South America
			{ x: 350, y: 200 },  // Middle East
			{ x: 500, y: 250 },  // Africa
			{ x: 650, y: 200 }   // Oceania
		];
		
		if (index < positions.length) {
			return positions[index];
		}
		
		// Fallback for additional regions
		const angle = (index / total) * Math.PI * 2;
		return {
			x: 400 + Math.cos(angle) * 200,
			y: 200 + Math.sin(angle) * 100
		};
	}
</script>

<div class="region-interface">
	<!-- Top Metrics -->
	<div class="metrics-header">
		<div class="metric-card">
			<div class="metric-icon">🌍</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FF6B9D">{regionCount}</div>
				<div class="metric-label">REGIONS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">💻</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #4ECDC4">{formatNumber(totalHosts)}</div>
				<div class="metric-label">TOTAL HOSTS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📍</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #95E77E; font-size: 1rem" title={topRegion[0]}>
					{truncateText(topRegion[0], 18).toUpperCase()}
				</div>
				<div class="metric-label">TOP REGION</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">🌐</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FFE66D">{globalSpread}%</div>
				<div class="metric-label">GLOBAL SPREAD</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📊</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #C77DFF">{formatNumber(avgHosts)}</div>
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
			{:else if error && !selectedRegion}
				<div class="error-state">
					<div class="error-icon">⚠️</div>
					<p>{error}</p>
					<button class="retry-btn" on:click={loadData}>RETRY</button>
				</div>
			{:else if selectedRegion}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedRegion.region.toUpperCase()}</h3>
							<div class="region-stats">
								<span>{formatNumber(selectedRegion.count)} HOSTS</span>
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
										<td class="hostname" title={host.host}>{truncateText(host.host, 25)}</td>
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
							
							<!-- Grid lines for better visual reference -->
							<g class="grid-lines" opacity="0.1">
								{#each Array(8) as _, i}
									<line x1="0" y1="{i * 50}" x2="800" y2="{i * 50}" stroke="#4ECDC4" stroke-width="0.5"/>
									<line x1="{i * 100}" y1="0" x2="{i * 100}" y2="400" stroke="#4ECDC4" stroke-width="0.5"/>
								{/each}
							</g>
							
							<!-- Region nodes with proper positioning -->
							{#each regions as [region, count], i}
								{@const pos = calculateNodePosition(i, regions.length)}
								{@const status = getRegionStatus(count)}
								{@const radius = Math.sqrt(count / maxHosts) * 40 + 20}
								
								<g class="region-node-group" 
								   on:click={() => selectRegion(region, count)}
								   on:mouseenter={() => hoveredRegion = region}
								   on:mouseleave={() => hoveredRegion = null}>
									<!-- Outer glow -->
									<circle cx="{pos.x}" cy="{pos.y}" r="{radius + 10}"
											fill="{status.color}" 
											opacity="0.1"/>
									<!-- Middle ring -->
									<circle cx="{pos.x}" cy="{pos.y}" r="{radius}"
											fill="{status.color}" 
											opacity="0.3"/>
									<!-- Inner core -->
									<circle cx="{pos.x}" cy="{pos.y}" r="{radius * 0.7}"
											fill="{status.color}" 
											opacity="0.5"/>
									
									<!-- Region label -->
									<text x="{pos.x}" y="{pos.y - radius - 15}" 
										  text-anchor="middle" 
										  fill="#FFFFFF" 
										  font-size="11" 
										  font-weight="600">
										{region.toUpperCase()}
									</text>
									
									<!-- Host count -->
									<text x="{pos.x}" y="{pos.y + 5}" 
										  text-anchor="middle" 
										  fill="#FFFFFF" 
										  font-size="14" 
										  font-weight="700">
										{formatNumber(count)}
									</text>
									
									<!-- Percentage -->
									{#if hoveredRegion === region}
										<text x="{pos.x}" y="{pos.y + 20}" 
											  text-anchor="middle" 
											  fill="{status.color}" 
											  font-size="10" 
											  font-weight="500">
											{((count / totalHosts) * 100).toFixed(1)}%
										</text>
									{/if}
								</g>
							{/each}
							
							<!-- Connection lines between major regions -->
							{#each regions as [region1, count1], i}
								{#each regions.slice(i + 1) as [region2, count2], j}
									{#if i < 3 && j < 2}
										{@const pos1 = calculateNodePosition(i, regions.length)}
										{@const pos2 = calculateNodePosition(i + j + 1, regions.length)}
										<line x1="{pos1.x}" y1="{pos1.y}" 
											  x2="{pos2.x}" y2="{pos2.y}"
											  stroke="rgba(78, 205, 196, 0.2)" 
											  stroke-width="1"
											  stroke-dasharray="5,5">
											<animate attributeName="stroke-dashoffset"
													 values="0;-10" dur="3s" repeatCount="indefinite"/>
										</line>
									{/if}
								{/each}
							{/each}
						</svg>
					</div>
					
					<!-- Network Activity Graph -->
					<div class="network-activity">
						<svg viewBox="0 0 200 50">
							<defs>
								<linearGradient id="networkGradient" x1="0%" y1="0%" x2="0%" y2="100%">
									<stop offset="0%" style="stop-color:#4ECDC4;stop-opacity:0.8" />
									<stop offset="100%" style="stop-color:#4ECDC4;stop-opacity:0" />
								</linearGradient>
							</defs>
							<polyline points="{networkActivity.map((val, i) => `${i * 4},${50 - val * 0.4}`).join(' ')}"
									  fill="none" 
									  stroke="#4ECDC4" 
									  stroke-width="2"
									  opacity="1"/>
							<polygon points="{networkActivity.map((val, i) => `${i * 4},${50 - val * 0.4}`).join(' ')} 200,50 0,50"
									 fill="url(#networkGradient)" 
									 opacity="0.3"/>
							{#each dataFlow as point, i}
								{#if point.peak}
									<circle cx="{i * 6.7}" cy="{50 - point.value * 0.5}" 
											r="3" fill="#FF6B9D" opacity="1">
										<animate attributeName="r" values="3;6;3" dur="1s" />
										<animate attributeName="opacity" values="1;0.3;1" dur="1s" />
									</circle>
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
						{@const percentage = Math.min(100, (count / maxHosts) * 100)}
						{@const status = getRegionStatus(count)}
						<div class="dist-item" on:click={() => selectRegion(region, count)}>
							<div class="dist-rank">#{i + 1}</div>
							<div class="dist-name" title={region}>{truncateText(region, 12).toUpperCase()}</div>
							<div class="dist-bar">
								<div class="dist-fill" 
									 style="width: {percentage}%; 
											background: linear-gradient(90deg, {status.color}40, {status.color})">
									<span class="dist-value">{formatNumber(count)}</span>
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
					{#each ['MEGA', 'LARGE', 'MEDIUM', 'SMALL', 'MINIMAL'] as size, i}
						{@const count = regions.filter(([_, c]) => getRegionSize(c) === size).length}
						{@const colors = ['#FF6B9D', '#4ECDC4', '#95E77E', '#FFE66D', '#C77DFF']}
						<div class="size-item">
							<div class="size-label">{size}</div>
							<div class="size-count" style="color: {colors[i]}">{count}</div>
							<div class="size-bar">
								<div class="size-fill" 
									 style="height: {regionCount > 0 ? (count / regionCount) * 100 : 0}%; 
											background: {colors[i]}">
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
						<span class="coverage-label">Regions with >50K hosts</span>
						<span class="coverage-value" style="color: #FF6B9D">
							{regions.filter(([_, c]) => c > 50000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Regions with >100K hosts</span>
						<span class="coverage-value" style="color: #4ECDC4">
							{regions.filter(([_, c]) => c > 100000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Regions with >200K hosts</span>
						<span class="coverage-value" style="color: #95E77E">
							{regions.filter(([_, c]) => c > 200000).length}
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
								<td class="region-name" title={region}>
									<span class="status-indicator" style="background: {status.color}"></span>
									{truncateText(region, 20).toUpperCase()}
								</td>
								<td class="host-count" style="color: {status.color}">
									{formatNumber(count)}
								</td>
								<td>
									<span class="size-badge" style="color: {status.color}">
										{size}
									</span>
								</td>
								<td>
									<span class="status-badge" 
										  style="color: {status.color}; 
												 border-color: {status.color};
												 background: {status.bgColor}">
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
		flex-shrink: 0;
	}
	
	.metric-card {
		flex: 1;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(139, 233, 253, 0.2);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		gap: 1rem;
		align-items: center;
		transition: all 0.3s ease;
	}
	
	.metric-card:hover {
		background: rgba(255, 255, 255, 0.05);
		transform: translateY(-2px);
	}
	
	.metric-icon {
		font-size: 2rem;
		filter: saturate(1.5);
	}
	
	.metric-content {
		flex: 1;
		min-width: 0;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: 700;
		font-family: 'SF Mono', 'Monaco', monospace;
		margin-bottom: 0.25rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
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
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(189, 147, 249, 0.2);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		flex-shrink: 0;
	}
	
	.panel-header h2, .panel-header h3 {
		margin: 0;
		font-size: 0.9rem;
		font-weight: 400;
		letter-spacing: 0.1em;
		color: #FF6B9D;
	}
	
	.search-input {
		padding: 0.5rem 1rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(139, 233, 253, 0.3);
		border-radius: 8px;
		color: #FFFFFF;
		font-size: 0.8rem;
		width: 200px;
		transition: all 0.3s ease;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #4ECDC4;
		background: rgba(0, 0, 0, 0.8);
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
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.2));
		border-radius: 10px;
		padding: 1rem;
		border: 1px solid rgba(139, 233, 253, 0.1);
	}
	
	.global-map svg {
		width: 100%;
		height: 100%;
		max-height: 400px;
	}
	
	.grid-lines {
		pointer-events: none;
	}
	
	.region-node-group {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.region-node-group:hover {
		transform: scale(1.1);
		filter: brightness(1.3);
	}
	
	/* Network Activity */
	.network-activity {
		position: absolute;
		bottom: 20px;
		left: 20px;
		right: 20px;
		height: 80px;
		background: linear-gradient(to bottom, rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.6));
		border: 1px solid rgba(139, 233, 253, 0.3);
		padding: 8px;
		border-radius: 10px;
		overflow: hidden;
	}
	
	.network-activity svg {
		width: 100%;
		height: 100%;
	}
	
	.activity-label {
		position: absolute;
		top: 8px;
		left: 12px;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
		font-weight: 600;
	}
	
	/* Analytics Panel */
	.analytics-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chart-box {
		flex: 1;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(139, 233, 253, 0.2);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
	}
	
	.chart-box h3 {
		margin: 0 0 1rem 0;
		font-size: 0.8rem;
		color: #4ECDC4;
		font-weight: 400;
		letter-spacing: 0.1em;
	}
	
	.distribution-bars {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	
	.dist-item {
		display: grid;
		grid-template-columns: 30px 100px 1fr 50px;
		gap: 0.5rem;
		align-items: center;
		cursor: pointer;
		transition: all 0.2s ease;
		padding: 0.2rem;
		border-radius: 4px;
	}
	
	.dist-item:hover {
		background: rgba(139, 233, 253, 0.05);
		transform: translateX(2px);
	}
	
	.dist-rank {
		font-size: 0.7rem;
		color: #FF6B9D;
		font-weight: 700;
	}
	
	.dist-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.9);
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.dist-bar {
		height: 20px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.dist-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.5rem;
		transition: width 0.5s ease;
		border-radius: 4px;
	}
	
	.dist-value {
		font-size: 0.65rem;
		color: #FFFFFF;
		font-weight: 700;
		text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
	}
	
	.dist-percent {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		text-align: right;
		font-weight: 600;
	}
	
	/* Size Chart */
	.size-chart {
		display: flex;
		align-items: flex-end;
		justify-content: space-around;
		height: 120px;
		padding: 0.5rem 0;
	}
	
	.size-item {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.4rem;
	}
	
	.size-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.7);
		writing-mode: vertical-lr;
		text-align: center;
		font-weight: 600;
	}
	
	.size-count {
		font-size: 1rem;
		font-weight: 700;
	}
	
	.size-bar {
		width: 35px;
		height: 70px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px 4px 0 0;
		display: flex;
		align-items: flex-end;
		overflow: hidden;
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
		gap: 0.8rem;
	}
	
	.coverage-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.6rem;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 8px;
		transition: all 0.2s ease;
	}
	
	.coverage-item:hover {
		background: rgba(0, 0, 0, 0.6);
		transform: translateX(2px);
	}
	
	.coverage-label {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
		font-weight: 500;
	}
	
	.coverage-value {
		font-size: 1.1rem;
		font-weight: 700;
		font-family: 'SF Mono', 'Monaco', monospace;
	}
	
	/* List Panel */
	.list-panel {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(189, 147, 249, 0.2);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.region-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
	}
	
	.region-list {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
	}
	
	.regions-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.regions-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.95);
		z-index: 10;
	}
	
	.regions-table th {
		padding: 0.6rem 0.5rem;
		text-align: left;
		font-size: 0.65rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.regions-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.regions-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.08);
		transform: translateX(2px);
	}
	
	.regions-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.85);
	}
	
	.rank {
		color: #FF6B9D;
		font-weight: 700;
		font-size: 0.7rem;
		width: 30px;
	}
	
	.region-name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.host-count {
		font-family: 'SF Mono', 'Monaco', monospace;
		font-weight: 700;
	}
	
	.size-badge {
		font-size: 0.65rem;
		font-weight: 700;
		letter-spacing: 0.05em;
	}
	
	.status-badge {
		font-size: 0.6rem;
		padding: 0.2rem 0.4rem;
		border: 1px solid;
		border-radius: 6px;
		font-weight: 700;
		letter-spacing: 0.03em;
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
		align-items: start;
		margin-bottom: 1rem;
		flex-shrink: 0;
	}
	
	.detail-header h3 {
		margin: 0 0 0.25rem 0;
		font-size: 1.1rem;
		color: #FF6B9D;
		font-weight: 600;
	}
	
	.region-stats {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
		display: flex;
		gap: 0.5rem;
		font-weight: 500;
	}
	
	.close-btn {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.3);
		color: #FFFFFF;
		width: 32px;
		height: 32px;
		border-radius: 8px;
		font-size: 1.1rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}
	
	.close-btn:hover {
		background: rgba(255, 121, 198, 0.2);
		border-color: #FF6B9D;
		transform: rotate(90deg);
	}
	
	.hosts-container {
		flex: 1;
		overflow-y: auto;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 10px;
		padding: 1rem;
	}
	
	.hosts-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.hosts-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.95);
		z-index: 10;
	}
	
	.hosts-table th {
		padding: 0.6rem 0.5rem;
		text-align: left;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
		letter-spacing: 0.05em;
		font-weight: 600;
	}
	
	.hosts-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.85);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.hostname {
		font-family: 'SF Mono', 'Monaco', monospace;
		color: #4ECDC4;
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.status-dot {
		font-size: 0.9rem;
		display: inline-block;
		text-align: center;
	}
	
	.status-dot.active {
		color: #95E77E;
		text-shadow: 0 0 8px #95E77E;
	}
	
	.status-dot.inactive {
		color: #FF5555;
		opacity: 0.6;
	}
	
	/* Loading State */
	.loading-state, .error-state {
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
		border-color: #FF6B9D;
		animation-duration: 3s;
	}
	
	.ring-2 {
		width: 70px;
		height: 70px;
		top: 15px;
		left: 15px;
		border-color: #4ECDC4;
		animation-duration: 2s;
		animation-direction: reverse;
	}
	
	.ring-3 {
		width: 40px;
		height: 40px;
		top: 30px;
		left: 30px;
		border-color: #95E77E;
		animation-duration: 1s;
	}
	
	.globe-core {
		position: absolute;
		width: 20px;
		height: 20px;
		top: 40px;
		left: 40px;
		background: linear-gradient(135deg, #FFE66D, #C77DFF);
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
	
	.loading-state p, .error-state p {
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.9rem;
		letter-spacing: 0.2em;
		font-weight: 600;
	}
	
	.error-icon {
		font-size: 3rem;
	}
	
	.retry-btn {
		padding: 0.6rem 1.5rem;
		background: linear-gradient(135deg, #FF6B9D, #FF6B9D80);
		border: 1px solid #FF6B9D;
		color: #FFFFFF;
		border-radius: 8px;
		font-size: 0.8rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.retry-btn:hover {
		background: linear-gradient(135deg, #FF6B9D, #FF6B9DCC);
		transform: translateY(-2px);
		box-shadow: 0 4px 15px rgba(255, 107, 157, 0.4);
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}
	
	::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb {
		background: linear-gradient(to bottom, #FF6B9D, #4ECDC4);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(to bottom, #FF6B9DCC, #4ECDC4CC);
	}
	
	/* Responsive Design */
	@media (max-width: 1400px) {
		.content-layout {
			grid-template-columns: 1fr 300px 280px;
		}
	}
	
	@media (max-width: 1200px) {
		.content-layout {
			grid-template-columns: 1fr;
			grid-template-rows: auto 1fr auto;
		}
		
		.analytics-panel {
			display: grid;
			grid-template-columns: repeat(3, 1fr);
		}
	}
	
	@media (max-width: 768px) {
		.metrics-header {
			flex-wrap: wrap;
		}
		
		.metric-card {
			min-width: calc(50% - 0.5rem);
		}
		
		.analytics-panel {
			grid-template-columns: 1fr;
		}
	}
</style>