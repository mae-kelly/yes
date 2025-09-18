<!-- CountryMetrics.svelte - Fixed Version -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';
	let viewMode = 'map';
	
	// Animation states
	let animationFrame = null;
	let pulsePhase = 0;
	let globalActivity = [];
	let trafficFlow = [];
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/country_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Failed to load country metrics:', err);
			// Use realistic fallback data
			data = {
				global_intelligence: {
					'UNITED STATES': 579543,
					'INDIA': 64023,
					'GERMANY': 26268,
					'BRAZIL': 16601,
					'GLOBAL': 16378,
					'ARGENTINA': 11436,
					'UNITED KINGDOM': 9858,
					'AUSTRALIA': 6966,
					'NEW ZEALAND': 4204,
					'POLAND': 3024,
					'CANADA': 1372,
					'IRELAND': 1043,
					'COSTA RICA': 2443,
					'SLOVAKIA': 1152
				}
			};
			loading = false;
		}
		
		// Start animations with better performance
		const animate = () => {
			pulsePhase = (pulsePhase + 0.02) % (Math.PI * 2);
			
			// Generate global activity patterns
			globalActivity = Array(50).fill(0).map((_, i) => 
				50 + Math.sin(Date.now() * 0.001 + i * 0.15) * 25 + Math.random() * 10
			);
			
			// Generate traffic flow
			trafficFlow = Array(40).fill(0).map((_, i) => ({
				value: 45 + Math.sin(Date.now() * 0.0008 + i * 0.2) * 35,
				surge: Math.random() > 0.98
			}));
			
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});

	// Format large numbers properly
	function formatNumber(num) {
		if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
		if (num >= 1000) return (num / 1000).toFixed(0) + 'K';
		return num.toLocaleString();
	}

	// Truncate long names
	function truncateName(name, maxLength = 20) {
		if (name.length <= maxLength) return name;
		return name.substring(0, maxLength - 3) + '...';
	}

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
			countryDetails = [];
		}
		loading = false;
	}

	function closeDetails() {
		selectedCountry = null;
		countryDetails = [];
	}
	
	function getCountryStatus(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#BD93F9' };
		if (percentage >= 50) return { level: 'HIGH', color: '#8BE9FD' };
		if (percentage >= 25) return { level: 'MODERATE', color: '#50FA7B' };
		return { level: 'LOW', color: '#FFB86C' };
	}
	
	function getCountrySize(count) {
		if (count > 100000) return 'SUPERPOWER';
		if (count > 50000) return 'MAJOR';
		if (count > 10000) return 'SIGNIFICANT';
		if (count > 5000) return 'MODERATE';
		if (count > 1000) return 'EMERGING';
		return 'MINIMAL';
	}

	// Better positioning for country bubbles
	function getCountryPosition(index, total) {
		const cols = 5;
		const rows = Math.ceil(total / cols);
		const col = index % cols;
		const row = Math.floor(index / cols);
		const xSpacing = 140;
		const ySpacing = 120;
		const xOffset = 80;
		const yOffset = 80;
		
		return {
			x: xOffset + col * xSpacing,
			y: yOffset + row * ySpacing
		};
	}
</script>

<div class="country-interface">
	<!-- Top Metrics -->
	<div class="metrics-header">
		<div class="metric-card">
			<div class="metric-icon">🗺️</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #BD93F9">{countryCount}</div>
				<div class="metric-label">COUNTRIES</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">💻</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #8BE9FD">{formatNumber(totalHosts)}</div>
				<div class="metric-label">TOTAL HOSTS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">🏆</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #50FA7B; font-size: 0.9rem" title="{topCountry[0]}">
					{truncateName(topCountry[0], 18).toUpperCase()}
				</div>
				<div class="metric-label">TOP COUNTRY</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">🌐</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FFB86C">{globalCoverage}%</div>
				<div class="metric-label">GLOBAL COVERAGE</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📊</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FF79C6">{concentration}%</div>
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
										<td class="hostname" title="{host.host}">{truncateName(host.host, 25)}</td>
										<td>{host.region || 'UNKNOWN'}</td>
										<td title="{host.data_center || 'UNKNOWN'}">{truncateName(host.data_center || 'UNKNOWN', 15)}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td title="{host.business_unit || 'UNKNOWN'}">{truncateName(host.business_unit || 'UNKNOWN', 15)}</td>
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
					<svg viewBox="0 0 800 500">
						<rect width="800" height="500" fill="rgba(0,0,0,0.2)" rx="10"/>
						
						<!-- Grid for better alignment -->
						<g opacity="0.05">
							{#each Array(10) as _, i}
								<line x1="{i * 80}" y1="0" x2="{i * 80}" y2="500" stroke="#8BE9FD" stroke-width="0.5"/>
							{/each}
							{#each Array(6) as _, i}
								<line x1="0" y1="{i * 100}" x2="800" y2="{i * 100}" stroke="#8BE9FD" stroke-width="0.5"/>
							{/each}
						</g>
						
						<!-- Country bubbles with proper spacing -->
						{#each topTen as [country, count], i}
							{@const status = getCountryStatus(count)}
							{@const pos = getCountryPosition(i, topTen.length)}
							{@const baseRadius = Math.sqrt(count / maxHosts) * 40}
							{@const radius = Math.min(50, Math.max(20, baseRadius))}
							
							<g class="country-node" on:click={() => selectCountry(country, count)}>
								<!-- Outer glow -->
								<circle cx="{pos.x}" cy="{pos.y}" r="{radius + 10}"
										fill="{status.color}" 
										opacity="{0.1 + Math.sin(pulsePhase + i) * 0.05}"/>
								<!-- Main circle -->
								<circle cx="{pos.x}" cy="{pos.y}" r="{radius}"
										fill="{status.color}"
										opacity="0.25"
										stroke="{status.color}"
										stroke-width="1"/>
								<!-- Inner circle -->
								<circle cx="{pos.x}" cy="{pos.y}" r="{radius * 0.7}"
										fill="{status.color}"
										opacity="0.5"/>
								<!-- Country name -->
								<text x="{pos.x}" y="{pos.y - radius - 8}"
									  text-anchor="middle" 
									  fill="#FFFFFF" 
									  font-size="9"
									  font-weight="600"
									  style="text-shadow: 0 0 5px rgba(0,0,0,0.8)">
									{truncateName(country, 12).toUpperCase()}
								</text>
								<!-- Host count -->
								<text x="{pos.x}" y="{pos.y + 4}"
									  text-anchor="middle" 
									  fill="#FFFFFF" 
									  font-size="12" 
									  font-weight="700"
									  style="text-shadow: 0 0 5px rgba(0,0,0,0.8)">
									{formatNumber(count)}
								</text>
								<!-- Rank -->
								<text x="{pos.x}" y="{pos.y + radius + 15}"
									  text-anchor="middle" 
									  fill="{status.color}" 
									  font-size="8"
									  font-weight="600">
									#{i + 1}
								</text>
							</g>
						{/each}
						
						<!-- Minimal connection lines -->
						{#if topTen[0]}
							{#each topTen.slice(1, 4) as [country, count], j}
								{@const pos1 = getCountryPosition(0, topTen.length)}
								{@const pos2 = getCountryPosition(j + 1, topTen.length)}
								<line x1="{pos1.x}" y1="{pos1.y}" x2="{pos2.x}" y2="{pos2.y}"
									  stroke="rgba(139, 233, 253, 0.1)" 
									  stroke-width="0.5"
									  stroke-dasharray="3,3">
									<animate attributeName="stroke-dashoffset"
											 values="0;-6" dur="2s" repeatCount="indefinite"/>
								</line>
							{/each}
						{/if}
					</svg>
				</div>
			{:else if viewMode === 'grid'}
				<div class="grid-visualization">
					<div class="country-grid">
						{#each countries.slice(0, 20) as [country, count], i}
							{@const status = getCountryStatus(count)}
							<div class="country-card" 
								 style="border-color: {status.color}"
								 on:click={() => selectCountry(country, count)}>
								<div class="card-header" style="background: {status.color}20">
									<span class="card-rank">#{i + 1}</span>
									<span class="card-status">{status.level}</span>
								</div>
								<div class="card-body">
									<div class="card-country" title="{country}">{truncateName(country, 15).toUpperCase()}</div>
									<div class="card-hosts" style="color: {status.color}">{formatNumber(count)}</div>
									<div class="card-bar">
										<div class="bar-fill" style="width: {(count/maxHosts)*100}%; background: {status.color}"></div>
									</div>
									<div class="card-stats">
										<span>{((count/totalHosts)*100).toFixed(1)}%</span>
										<span>{getCountrySize(count)}</span>
									</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{:else if viewMode === 'list'}
				<div class="list-visualization">
					<table class="countries-list-table">
						<thead>
							<tr>
								<th>#</th>
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
								{@const size = getCountrySize(count)}
								<tr on:click={() => selectCountry(country, count)}>
									<td class="rank">{i + 1}</td>
									<td class="country-name" title="{country}">
										<span class="status-indicator" style="background: {status.color}"></span>
										{truncateName(country, 25).toUpperCase()}
									</td>
									<td class="host-count" style="color: {status.color}">
										{formatNumber(count)}
									</td>
									<td>{((count/totalHosts)*100).toFixed(1)}%</td>
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
			{/if}
			
			<!-- Global Activity Graph -->
			<div class="global-activity">
				<svg viewBox="0 0 200 50">
					<polyline points="{globalActivity.map((val, i) => `${i * 4},${50 - val * 0.5}`).join(' ')}"
							  fill="none" 
							  stroke="#8BE9FD" 
							  stroke-width="2"
							  opacity="0.9"/>
					<polyline points="{globalActivity.map((val, i) => `${i * 4},${50 - val * 0.5}`).join(' ')}"
							  fill="none" 
							  stroke="#8BE9FD" 
							  stroke-width="4"
							  opacity="0.3"
							  filter="blur(2px)"/>
					{#each trafficFlow as point, i}
						{#if point.surge}
							<circle cx="{i * 5}" cy="{50 - point.value * 0.5}" 
									r="2" fill="#FF79C6" opacity="0.8">
								<animate attributeName="r" values="2;4;2" dur="0.5s" repeatCount="1"/>
							</circle>
						{/if}
					{/each}
				</svg>
				<div class="activity-label">GLOBAL TRAFFIC FLOW</div>
			</div>
		</div>
		
		<!-- Right: Quick Access List -->
		<div class="quick-access-panel">
			<div class="panel-header">
				<h3>TOP 10 COUNTRIES</h3>
				<span class="country-total">{countries.length} TOTAL</span>
			</div>
			<div class="country-list">
				<table class="countries-table">
					<thead>
						<tr>
							<th>#</th>
							<th>COUNTRY</th>
							<th>HOSTS</th>
						</tr>
					</thead>
					<tbody>
						{#each topTen as [country, count], i}
							{@const status = getCountryStatus(count)}
							<tr on:click={() => selectCountry(country, count)}>
								<td class="rank">#{i + 1}</td>
								<td class="country-name" title="{country}">
									{truncateName(country, 20).toUpperCase()}
								</td>
								<td class="host-count" style="color: {status.color}">
									{formatNumber(count)}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			
			<!-- Distribution Statistics -->
			<div class="distribution-stats">
				<h4>DISTRIBUTION STATISTICS</h4>
				<div class="stat-item">
					<span>Countries >100K hosts</span>
					<span style="color: #BD93F9">{countries.filter(([_,c]) => c > 100000).length}</span>
				</div>
				<div class="stat-item">
					<span>Countries >50K hosts</span>
					<span style="color: #8BE9FD">{countries.filter(([_,c]) => c > 50000).length}</span>
				</div>
				<div class="stat-item">
					<span>Countries >10K hosts</span>
					<span style="color: #50FA7B">{countries.filter(([_,c]) => c > 10000).length}</span>
				</div>
				<div class="stat-item">
					<span>Countries >5K hosts</span>
					<span style="color: #FFB86C">{countries.filter(([_,c]) => c > 5000).length}</span>
				</div>
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
	}
	
	.metric-card {
		flex: 1;
		background: rgba(255, 255, 255,