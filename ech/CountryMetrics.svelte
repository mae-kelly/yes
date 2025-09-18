<!-- CountryMetrics.svelte - Fixed with better visualization -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let error = null;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';
	let viewMode = 'map';
	let hoveredCountry = null;
	
	// Animation states
	let animationFrame = null;
	let globalActivity = [];
	let trafficFlow = [];
	
	onMount(async () => {
		await loadData();
		initializeAnimations();
	});
	
	async function loadData() {
		loading = true;
		error = null;
		try {
			let response = await fetch('http://localhost:5000/api/country_metrics');
			if (!response.ok) throw new Error('Failed to fetch data');
			data = await response.json();
		} catch (err) {
			console.error('Failed to load country metrics:', err);
			error = 'Unable to load country data. Please try again.';
			// Use mock data for demonstration
			data = generateMockData();
		} finally {
			loading = false;
		}
	}
	
	function generateMockData() {
		return {
			global_intelligence: {
				'United States': 579543,
				'India': 84823,
				'Germany': 36589,
				'Brazil': 16401,
				'Japan': 14576,
				'United Kingdom': 12456,
				'Australia': 8965,
				'Canada': 7854,
				'France': 6543,
				'China': 5432,
				'Singapore': 4321,
				'Netherlands': 3210,
				'Spain': 2987,
				'Italy': 2765,
				'Mexico': 2543,
				'South Korea': 2321,
				'Sweden': 2109,
				'Poland': 1987,
				'Ireland': 1765,
				'Switzerland': 1543
			}
		};
	}
	
	function initializeAnimations() {
		// Initialize smooth activity patterns
		for (let i = 0; i < 50; i++) {
			globalActivity.push(50 + Math.sin(i * 0.2) * 20);
			trafficFlow.push({ value: 45, surge: false });
		}
		
		const animate = () => {
			// Update global activity with smooth transitions
			globalActivity = globalActivity.map((val, i) => {
				const target = 50 + Math.sin(Date.now() * 0.001 + i * 0.2) * 25 + Math.random() * 10;
				return val * 0.9 + target * 0.1;
			});
			
			// Update traffic flow
			trafficFlow = trafficFlow.map((point, i) => ({
				value: 40 + Math.sin(Date.now() * 0.0008 + i * 0.25) * 35,
				surge: Math.random() > 0.98
			}));
			
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	}
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});

	$: countries = data.global_intelligence ? 
		Object.entries(data.global_intelligence)
			.filter(([country]) => country.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = countries.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = countries.length > 0 ? Math.max(...countries.map(([,c]) => c)) : 1;
	$: avgHosts = countries.length > 0 ? Math.round(totalHosts / countries.length) : 0;
	
	// Key metrics
	$: countryCount = countries.length;
	$: topCountry = countries[0] || ['N/A', 0];
	$: concentration = topCountry[1] > 0 ? ((topCountry[1] / totalHosts) * 100).toFixed(1) : 0;
	$: globalCoverage = ((countryCount / 195) * 100).toFixed(1);
	
	// Top performers
	$: topTen = countries.slice(0, 10);

	async function selectCountry(country, count) {
		selectedCountry = { country, count };
		loading = true;
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(country)}`);
			let result = await response.json();
			countryDetails = result.hosts || [];
		} catch (err) {
			console.error('Failed to load country details:', err);
			countryDetails = generateMockHosts(country, Math.min(50, count));
		} finally {
			loading = false;
		}
	}
	
	function generateMockHosts(country, count) {
		const hosts = [];
		for (let i = 0; i < count; i++) {
			hosts.push({
				host: `${country.toLowerCase().replace(/\s/g, '-')}-srv-${i + 1}.internal`,
				region: getRegionForCountry(country),
				country: country,
				data_center: `DC-${country.substring(0, 2).toUpperCase()}-${Math.floor(Math.random() * 5) + 1}`,
				infrastructure_type: ['Virtual', 'Physical', 'Cloud', 'Container'][Math.floor(Math.random() * 4)],
				business_unit: ['IT', 'Finance', 'Sales', 'Operations'][Math.floor(Math.random() * 4)],
				present_in_cmdb: Math.random() > 0.3 ? 'Yes' : 'No',
				tanium_coverage: Math.random() > 0.4 ? 'Tanium' : 'No Coverage'
			});
		}
		return hosts;
	}
	
	function getRegionForCountry(country) {
		const regions = {
			'United States': 'North America',
			'Canada': 'North America',
			'Mexico': 'North America',
			'Brazil': 'LATAM',
			'Germany': 'EMEA',
			'United Kingdom': 'EMEA',
			'France': 'EMEA',
			'Japan': 'APAC',
			'China': 'APAC',
			'India': 'APAC',
			'Australia': 'APAC'
		};
		return regions[country] || 'Global';
	}

	function closeDetails() {
		selectedCountry = null;
		countryDetails = [];
	}
	
	function getCountryStatus(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#FF6B9D', bgColor: '#FF6B9D20' };
		if (percentage >= 50) return { level: 'HIGH', color: '#4ECDC4', bgColor: '#4ECDC420' };
		if (percentage >= 25) return { level: 'MODERATE', color: '#95E77E', bgColor: '#95E77E20' };
		return { level: 'LOW', color: '#FFE66D', bgColor: '#FFE66D20' };
	}
	
	function getCountrySize(count) {
		if (count > 100000) return 'SUPERPOWER';
		if (count > 50000) return 'MAJOR';
		if (count > 10000) return 'SIGNIFICANT';
		if (count > 1000) return 'MODERATE';
		if (count > 100) return 'EMERGING';
		return 'MINIMAL';
	}
	
	function formatNumber(num) {
		return new Intl.NumberFormat('en-US').format(num);
	}
	
	function truncateText(text, maxLength = 20) {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}
	
	// Calculate grid positions for countries to avoid overlap
	function calculateCountryPosition(index, total) {
		const cols = 5;
		const rows = Math.ceil(total / cols);
		const col = index % cols;
		const row = Math.floor(index / cols);
		
		// Stagger rows for better visual distribution
		const offsetX = row % 2 === 0 ? 0 : 40;
		
		return {
			x: 100 + col * 140 + offsetX,
			y: 80 + row * 100
		};
	}
	
	// Scale bubble size logarithmically to prevent extreme size differences
	function calculateBubbleRadius(count) {
		const logCount = Math.log10(count + 1);
		const logMax = Math.log10(maxHosts + 1);
		return 20 + (logCount / logMax) * 30;
	}
</script>

<div class="country-interface">
	<!-- Top Metrics -->
	<div class="metrics-header">
		<div class="metric-card">
			<div class="metric-icon">🗺️</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FF6B9D">{countryCount}</div>
				<div class="metric-label">COUNTRIES</div>
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
			<div class="metric-icon">🏆</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #95E77E; font-size: 1rem" title={topCountry[0]}>
					{truncateText(topCountry[0], 18).toUpperCase()}
				</div>
				<div class="metric-label">TOP COUNTRY</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">🌐</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FFE66D">{globalCoverage}%</div>
				<div class="metric-label">GLOBAL COVERAGE</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📊</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #C77DFF">{concentration}%</div>
				<div class="metric-label">TOP CONCENTRATION</div>
			</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content-layout">
		<!-- Left: Country Visualization -->
		<div class="country-panel">
			<div class="panel-header">
				<h2>GLOBAL INFRASTRUCTURE MAP</h2>
				<div class="controls">
					<input type="text"
						   bind:value={searchTerm}
						   placeholder="Search countries..."
						   class="search-input"/>
					<div class="view-tabs">
						<button class="tab {viewMode === 'map' ? 'active' : ''}" on:click={() => viewMode = 'map'}>MAP</button>
						<button class="tab {viewMode === 'grid' ? 'active' : ''}" on:click={() => viewMode = 'grid'}>GRID</button>
						<button class="tab {viewMode === 'list' ? 'active' : ''}" on:click={() => viewMode = 'list'}>LIST</button>
					</div>
				</div>
			</div>
			
			{#if loading && !selectedCountry}
				<div class="loading-state">
					<div class="world-loader">
						<div class="continent cont-1"></div>
						<div class="continent cont-2"></div>
						<div class="continent cont-3"></div>
					</div>
					<p>SCANNING GLOBAL NETWORK...</p>
				</div>
			{:else if error && !selectedCountry}
				<div class="error-state">
					<div class="error-icon">⚠️</div>
					<p>{error}</p>
					<button class="retry-btn" on:click={loadData}>RETRY</button>
				</div>
			{:else if selectedCountry}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedCountry.country.toUpperCase()}</h3>
							<div class="country-stats">
								<span>{formatNumber(selectedCountry.count)} HOSTS</span>
								<span>•</span>
								<span>{((selectedCountry.count/totalHosts)*100).toFixed(2)}% OF GLOBAL</span>
								<span>•</span>
								<span>{getCountrySize(selectedCountry.count)} PRESENCE</span>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="hosts-container">
						<table class="hosts-table">
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>REGION</th>
									<th>DATA CENTER</th>
									<th>TYPE</th>
									<th>DIVISION</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each countryDetails as host}
									<tr>
										<td class="hostname" title={host.host}>{truncateText(host.host, 25)}</td>
										<td>{host.region || 'UNKNOWN'}</td>
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
			{:else if viewMode === 'map'}
				<div class="map-visualization">
					<svg viewBox="0 0 800 400">
						<rect width="800" height="400" fill="rgba(0,0,0,0.3)" rx="10"/>
						
						<!-- Grid lines -->
						<g class="grid-lines" opacity="0.05">
							{#each Array(8) as _, i}
								<line x1="0" y1="{i * 50}" x2="800" y2="{i * 50}" stroke="#4ECDC4" stroke-width="0.5"/>
								<line x1="{i * 100}" y1="0" x2="{i * 100}" y2="400" stroke="#4ECDC4" stroke-width="0.5"/>
							{/each}
						</g>
						
						{#each countries.slice(0, 20) as [country, count], i}
							{@const pos = calculateCountryPosition(i, Math.min(20, countries.length))}
							{@const status = getCountryStatus(count)}
							{@const radius = calculateBubbleRadius(count)}
							
							<g class="country-node" 
							   on:click={() => selectCountry(country, count)}
							   on:mouseenter={() => hoveredCountry = country}
							   on:mouseleave={() => hoveredCountry = null}>
								<!-- Outer glow -->
								<circle cx="{pos.x}" cy="{pos.y}" r="{radius + 8}"
										fill="{status.color}" 
										opacity="0.15"/>
								<!-- Middle ring -->
								<circle cx="{pos.x}" cy="{pos.y}" r="{radius}"
										fill="{status.color}"
										opacity="0.3"/>
								<!-- Inner core -->
								<circle cx="{pos.x}" cy="{pos.y}" r="{radius * 0.7}"
										fill="{status.color}"
										opacity="0.6"/>
								<!-- Country name -->
								<text x="{pos.x}" y="{pos.y - radius - 8}"
									  text-anchor="middle" 
									  fill="#FFFFFF" 
									  font-size="9"
									  font-weight="600">
									{truncateText(country, 15).toUpperCase()}
								</text>
								<!-- Host count -->
								<text x="{pos.x}" y="{pos.y + 3}"
									  text-anchor="middle" 
									  fill="#FFFFFF" 
									  font-size="11" 
									  font-weight="700">
									{count >= 1000 ? `${(count/1000).toFixed(0)}K` : count}
								</text>
								<!-- Additional info on hover -->
								{#if hoveredCountry === country}
									<text x="{pos.x}" y="{pos.y + 16}"
										  text-anchor="middle" 
										  fill="{status.color}" 
										  font-size="8" 
										  font-weight="500">
										{((count/totalHosts)*100).toFixed(1)}%
									</text>
								{/if}
							</g>
						{/each}
						
						<!-- Connection mesh for top countries -->
						{#each countries.slice(0, 5) as [country1, count1], i}
							{#each countries.slice(i + 1, 5) as [country2, count2], j}
								{@const pos1 = calculateCountryPosition(i, Math.min(20, countries.length))}
								{@const pos2 = calculateCountryPosition(i + j + 1, Math.min(20, countries.length))}
								<line x1="{pos1.x}" y1="{pos1.y}" x2="{pos2.x}" y2="{pos2.y}"
									  stroke="rgba(78, 205, 196, 0.15)" 
									  stroke-width="1"
									  stroke-dasharray="3,3">
									<animate attributeName="stroke-dashoffset"
											 values="0;-6" dur="2s" repeatCount="indefinite"/>
								</line>
							{/each}
						{/each}
					</svg>
				</div>
			{:else if viewMode === 'grid'}
				<div class="grid-visualization">
					{#each countries.slice(0, 24) as [country, count]}
						{@const status = getCountryStatus(count)}
						<div class="country-card" 
							 style="border-color: {status.color}; background: {status.bgColor}"
							 on:click={() => selectCountry(country, count)}>
							<div class="card-header" style="background: {status.color}30">
								<span class="country-flag">🏴</span>
								<span class="country-name" title={country}>{truncateText(country, 12)}</span>
							</div>
							<div class="card-body">
								<div class="card-metric">
									<span class="metric-number" style="color: {status.color}">
										{formatNumber(count)}
									</span>
									<span class="metric-label">HOSTS</span>
								</div>
								<div class="card-bar">
									<div class="bar-fill" 
										 style="width: {Math.min(100, (count/maxHosts)*100)}%; 
												background: {status.color}"></div>
								</div>
								<div class="card-footer">
									<span class="size-label">{getCountrySize(count)}</span>
									<span class="percent-label">{((count/totalHosts)*100).toFixed(1)}%</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{:else if viewMode === 'list'}
				<div class="list-visualization">
					<table class="country-list-table">
						<thead>
							<tr>
								<th>RANK</th>
								<th>COUNTRY</th>
								<th>HOSTS</th>
								<th>% OF TOTAL</th>
								<th>SIZE</th>
								<th>STATUS</th>
							</tr>
						</thead>
						<tbody>
							{#each countries as [country, count], i}
								{@const status = getCountryStatus(count)}
								<tr on:click={() => selectCountry(country, count)}>
									<td class="rank">#{i + 1}</td>
									<td class="country-name">
										<span class="status-indicator" style="background: {status.color}"></span>
										{country.toUpperCase()}
									</td>
									<td class="host-count" style="color: {status.color}">
										{formatNumber(count)}
									</td>
									<td class="percent">{((count/totalHosts)*100).toFixed(2)}%</td>
									<td>
										<span class="size-badge" style="color: {status.color}">
											{getCountrySize(count)}
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
			{/if}
			
			<!-- Global Activity Graph -->
			<div class="global-activity">
				<svg viewBox="0 0 200 50">
					<defs>
						<linearGradient id="trafficGradient" x1="0%" y1="0%" x2="0%" y2="100%">
							<stop offset="0%" style="stop-color:#4ECDC4;stop-opacity:0.8" />
							<stop offset="100%" style="stop-color:#4ECDC4;stop-opacity:0" />
						</linearGradient>
					</defs>
					<polyline points="{globalActivity.map((val, i) => `${i * 4},${50 - val * 0.4}`).join(' ')}"
							  fill="none" 
							  stroke="#4ECDC4" 
							  stroke-width="2"
							  opacity="1"/>
					<polygon points="{globalActivity.map((val, i) => `${i * 4},${50 - val * 0.4}`).join(' ')} 200,50 0,50"
							 fill="url(#trafficGradient)" 
							 opacity="0.3"/>
					{#each trafficFlow as point, i}
						{#if point.surge}
							<circle cx="{i * 5}" cy="{50 - point.value * 0.5}" 
									r="3" fill="#FF6B9D" opacity="1">
								<animate attributeName="r" values="3;6;3" dur="1s" />
								<animate attributeName="opacity" values="1;0.3;1" dur="1s" />
							</circle>
						{/if}
					{/each}
				</svg>
				<div class="activity-label">GLOBAL TRAFFIC FLOW</div>
			</div>
		</div>
		
		<!-- Middle: Analytics -->
		<div class="analytics-panel">
			<!-- Top 10 Countries Chart -->
			<div class="chart-box">
				<h3>TOP 10 COUNTRIES BY HOSTS</h3>
				<div class="distribution-bars">
					{#each topTen as [country, count], i}
						{@const percentage = Math.min(100, (count / maxHosts) * 100)}
						{@const status = getCountryStatus(count)}
						<div class="dist-item" on:click={() => selectCountry(country, count)}>
							<div class="dist-rank">#{i + 1}</div>
							<div class="dist-name" title={country}>{truncateText(country, 12).toUpperCase()}</div>
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
			
			<!-- Distribution Statistics -->
			<div class="chart-box">
				<h3>DISTRIBUTION STATISTICS</h3>
				<div class="coverage-stats">
					<div class="coverage-item">
						<span class="coverage-label">Countries >10K hosts</span>
						<span class="coverage-value" style="color: #FF6B9D">
							{countries.filter(([_,c]) => c > 10000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Countries >5K hosts</span>
						<span class="coverage-value" style="color: #4ECDC4">
							{countries.filter(([_,c]) => c > 5000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Countries >1K hosts</span>
						<span class="coverage-value" style="color: #95E77E">
							{countries.filter(([_,c]) => c > 1000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Average per country</span>
						<span class="coverage-value" style="color: #FFE66D">
							{formatNumber(avgHosts)}
						</span>
					</div>
				</div>
			</div>
		</div>
		
		<!-- Right: Quick Access -->
		<div class="quick-access-panel">
			<div class="panel-header">
				<h3>QUICK ACCESS</h3>
				<span class="country-count">{countries.length} TOTAL</span>
			</div>
			<div class="quick-list">
				{#each countries.slice(0, 15) as [country, count], i}
					{@const status = getCountryStatus(count)}
					<div class="quick-item" 
						 style="border-left: 3px solid {status.color}"
						 on:click={() => selectCountry(country, count)}>
						<div class="quick-rank">#{i + 1}</div>
						<div class="quick-name" title={country}>{truncateText(country, 18)}</div>
						<div class="quick-count" style="color: {status.color}">{formatNumber(count)}</div>
					</div>
				{/each}
			</div>
		</div>
	</div>
</div>

<style>
	.country-interface {
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
	
	/* Country Panel */
	.country-panel {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(189, 147, 249, 0.2);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		position: relative;
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
	
	.controls {
		display: flex;
		gap: 1rem;
		align-items: center;
	}
	
	.search-input {
		padding: 0.5rem 1rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(139, 233, 253, 0.3);
		border-radius: 8px;
		color: #FFFFFF;
		font-size: 0.8rem;
		width: 180px;
		transition: all 0.3s ease;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #4ECDC4;
		background: rgba(0, 0, 0, 0.8);
	}
	
	.view-tabs {
		display: flex;
		gap: 2px;
		background: rgba(0, 0, 0, 0.5);
		padding: 3px;
		border-radius: 8px;
	}
	
	.tab {
		padding: 0.4rem 1rem;
		background: transparent;
		border: none;
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.7rem;
		font-weight: 600;
		cursor: pointer;
		border-radius: 6px;
		transition: all 0.2s;
	}
	
	.tab:hover {
		background: rgba(139, 233, 253, 0.1);
		color: rgba(255, 255, 255, 0.9);
	}
	
	.tab.active {
		background: rgba(78, 205, 196, 0.2);
		color: #4ECDC4;
	}
	
	/* Map Visualization */
	.map-visualization {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1rem;
		overflow: auto;
	}
	
	.map-visualization svg {
		width: 100%;
		height: 100%;
		min-height: 400px;
	}
	
	.grid-lines {
		pointer-events: none;
	}
	
	.country-node {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.country-node:hover {
		transform: scale(1.15);
		filter: brightness(1.3);
	}
	
	/* Grid Visualization */
	.grid-visualization {
		flex: 1;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
		gap: 1rem;
		padding: 0.5rem;
		overflow-y: auto;
	}
	
	.country-card {
		border: 1px solid;
		border-radius: 10px;
		overflow: hidden;
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.country-card:hover {
		transform: translateY(-4px) scale(1.02);
		box-shadow: 0 8px 20px rgba(139, 233, 253, 0.3);
	}
	
	.card-header {
		padding: 0.6rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.country-flag {
		font-size: 1.2rem;
	}
	
	.country-name {
		font-size: 0.7rem;
		font-weight: 600;
		color: #FFFFFF;
		text-transform: uppercase;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.card-body {
		padding: 0.8rem;
	}
	
	.card-metric {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin-bottom: 0.5rem;
	}
	
	.metric-number {
		font-size: 1.2rem;
		font-weight: 700;
		font-family: 'SF Mono', 'Monaco', monospace;
	}
	
	.metric-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}
	
	.card-bar {
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
		margin: 0.5rem 0;
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.card-footer {
		display: flex;
		justify-content: space-between;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.size-label {
		font-weight: 600;
		text-transform: uppercase;
	}
	
	.percent-label {
		font-family: 'SF Mono', 'Monaco', monospace;
	}
	
	/* List Visualization */
	.list-visualization {
		flex: 1;
		overflow-y: auto;
		padding: 0.5rem;
	}
	
	.country-list-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.country-list-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.95);
		z-index: 10;
	}
	
	.country-list-table th {
		padding: 0.8rem 0.5rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.country-list-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.country-list-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.08);
		transform: translateX(2px);
	}
	
	.country-list-table td {
		padding: 0.6rem 0.5rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.85);
	}
	
	.rank {
		color: #FF6B9D;
		font-weight: 700;
		font-size: 0.75rem;
	}
	
	.country-list-table .country-name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
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
	
	.percent {
		font-family: 'SF Mono', 'Monaco', monospace;
		color: rgba(255, 255, 255, 0.7);
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
	
	/* Global Activity */
	.global-activity {
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
	
	.global-activity svg {
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
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.dist-item {
		display: grid;
		grid-template-columns: 30px 110px 1fr 50px;
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
		white-space: nowrap;
	}
	
	.dist-percent {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		text-align: right;
		font-weight: 600;
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
	
	/* Quick Access Panel */
	.quick-access-panel {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(189, 147, 249, 0.2);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		padding: 1rem;
	}
	
	.country-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
	}
	
	.quick-list {
		flex: 1;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-top: 1rem;
	}
	
	.quick-item {
		display: grid;
		grid-template-columns: 30px 1fr auto;
		gap: 0.5rem;
		align-items: center;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 6px;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	.quick-item:hover {
		background: rgba(139, 233, 253, 0.1);
		transform: translateX(4px);
	}
	
	.quick-rank {
		font-size: 0.65rem;
		color: #FF6B9D;
		font-weight: 700;
	}
	
	.quick-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.9);
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.quick-count {
		font-size: 0.8rem;
		font-weight: 700;
		font-family: 'SF Mono', 'Monaco', monospace;
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
	
	.country-stats {
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
	
	.world-loader {
		display: flex;
		gap: 1.5rem;
		align-items: center;
	}
	
	.continent {
		width: 40px;
		height: 40px;
		background: linear-gradient(135deg, #FF6B9D, #4ECDC4);
		border-radius: 50%;
		animation: globePulse 2s ease-in-out infinite;
	}
	
	.cont-1 {
		animation-delay: 0s;
	}
	
	.cont-2 {
		width: 50px;
		height: 50px;
		animation-delay: 0.3s;
	}
	
	.cont-3 {
		width: 35px;
		height: 35px;
		animation-delay: 0.6s;
	}
	
	@keyframes globePulse {
		0%, 100% { opacity: 0.3; transform: scale(0.8); }
		50% { opacity: 1; transform: scale(1); }
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
		
		.grid-visualization {
			grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
		}
	}
	
	@media (max-width: 1200px) {
		.content-layout {
			grid-template-columns: 1fr;
			grid-template-rows: 1fr auto;
		}
		
		.analytics-panel {
			display: grid;
			grid-template-columns: 1fr 1fr;
		}
		
		.quick-access-panel {
			display: none;
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
		
		.grid-visualization {
			grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
		}
		
		.controls {
			flex-direction: column;
			align-items: stretch;
		}
		
		.search-input {
			width: 100%;
		}
	}
</style>