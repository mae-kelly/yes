<!-- CountryMetrics.svelte - Enhanced with Moving Graph -->
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
			loading = false;
		}
		
		// Start animations
		const animate = () => {
			pulsePhase = (pulsePhase + 0.02) % (Math.PI * 2);
			
			// Generate global activity patterns
			globalActivity = Array(50).fill(0).map((_, i) => 
				50 + Math.sin(Date.now() * 0.002 + i * 0.2) * 30 + Math.random() * 20
			);
			
			// Generate traffic flow
			trafficFlow = Array(40).fill(0).map((_, i) => ({
				value: 45 + Math.sin(Date.now() * 0.001 + i * 0.25) * 40,
				surge: Math.random() > 0.98
			}));
			
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	});
	
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
	$: topFive = countries.slice(0, 5);

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
		if (count > 15000) return 'SUPERPOWER';
		if (count > 10000) return 'MAJOR';
		if (count > 5000) return 'SIGNIFICANT';
		if (count > 1000) return 'MODERATE';
		if (count > 100) return 'EMERGING';
		return 'MINIMAL';
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
				<div class="metric-value" style="color: #8BE9FD">{totalHosts.toLocaleString()}</div>
				<div class="metric-label">TOTAL HOSTS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">🏆</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #50FA7B; font-size: 1.2rem">
					{topCountry[0].substring(0, 25).toUpperCase()}
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
						<button class="tab {viewMode === 'tree' ? 'active' : ''}" on:click={() => viewMode = 'tree'}>TREE</button>
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
								<span>{selectedCountry.count.toLocaleString()} HOSTS</span>
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
										<td class="hostname">{host.host}</td>
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
					<svg viewBox="0 0 1000 500">
						<rect width="1000" height="500" fill="rgba(0,0,0,0.2)" rx="10"/>
						
						{#each countries.slice(0, 20) as [country, count], i}
							{@const status = getCountryStatus(count)}
							{@const radius = Math.sqrt(count/maxHosts) * 50}
							{@const x = 100 + (i % 5) * 180}
							{@const y = 100 + Math.floor(i / 5) * 100}
							
							<g class="country-node" on:click={() => selectCountry(country, count)}>
								<circle cx="{x}" cy="{y}" r="{radius + 15}"
										fill="{status.color}" 
										opacity="{0.1 + Math.sin(pulsePhase + i) * 0.1}"/>
								<circle cx="{x}" cy="{y}" r="{radius}"
										fill="{status.color}"
										opacity="0.3"/>
								<circle cx="{x}" cy="{y}" r="{radius * 0.7}"
										fill="{status.color}"
										opacity="0.6"/>
								<text x="{x}" y="{y - radius - 10}"
									  text-anchor="middle" 
									  fill="#FFFFFF" 
									  font-size="10"
									  font-weight="600">
									{country.substring(0, 15).toUpperCase()}
								</text>
								<text x="{x}" y="{y + 5}"
									  text-anchor="middle" 
									  fill="#FFFFFF" 
									  font-size="14" 
									  font-weight="700">
									{count.toLocaleString()}
								</text>
							</g>
						{/each}
						
						<!-- Connection mesh -->
						{#each countries.slice(0, 20) as [country1, count1], i}
							{#each countries.slice(i + 1, 20) as [country2, count2], j}
								{#if Math.random() > 0.8}
									{@const x1 = 100 + (i % 5) * 180}
									{@const y1 = 100 + Math.floor(i / 5) * 100}
									{@const x2 = 100 + ((i + j + 1) % 5) * 180}
									{@const y2 = 100 + Math.floor((i + j + 1) / 5) * 100}
									<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
										  stroke="rgba(139, 233, 253, 0.2)" 
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
			{:else if viewMode === 'tree'}
				<div class="tree-visualization">
					<div class="tree-container">
						<div class="tree-root">
							<div class="root-node">
								<div class="node-icon">🌍</div>
								<div class="node-label">GLOBAL NETWORK</div>
								<div class="node-count">{totalHosts.toLocaleString()} HOSTS</div>
							</div>
						</div>
						<div class="tree-branches">
							{#each topFive as [country, count], i}
								{@const status = getCountryStatus(count)}
								{@const percentage = ((count / totalHosts) * 100).toFixed(1)}
								<div class="branch-container">
									<div class="branch-line"></div>
									<div class="country-branch-node" 
										 style="border-color: {status.color}"
										 on:click={() => selectCountry(country, count)}>
										<div class="node-header" style="background: {status.color}20">
											<span class="node-rank">#{i + 1}</span>
										</div>
										<div class="node-body">
											<div class="node-name">{country.substring(0, 20).toUpperCase()}</div>
											<div class="node-metrics">
												<span class="node-hosts" style="color: {status.color}">
													{count.toLocaleString()}
												</span>
												<span class="node-percent">{percentage}%</span>
											</div>
											<div class="node-bar">
												<div class="bar-fill" style="width: {percentage}%; background: {status.color}"></div>
											</div>
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
					
					<!-- Bubble Chart -->
					<div class="bubble-chart">
						<svg viewBox="0 0 400 200">
							{#each countries.slice(5, 20) as [country, count], i}
								{@const radius = Math.sqrt(count / maxHosts) * 30}
								{@const x = 40 + (i % 5) * 75}
								{@const y = 40 + Math.floor(i / 5) * 60}
								{@const status = getCountryStatus(count)}
								
								<g class="bubble-group" on:click={() => selectCountry(country, count)}>
									<circle cx="{x}" cy="{y}" r="{radius}" 
											fill="{status.color}" opacity="0.3"/>
									<circle cx="{x}" cy="{y}" r="{radius * 0.7}" 
											fill="{status.color}" opacity="0.6"/>
									<text x="{x}" y="{y}" text-anchor="middle" 
										  fill="#FFFFFF" font-size="8" font-weight="600">
										{count.toLocaleString()}
									</text>
								</g>
							{/each}
						</svg>
					</div>
				</div>
			{/if}
			
			<!-- Global Activity Graph -->
			<div class="global-activity">
				<svg viewBox="0 0 200 50">
					<polyline points="{globalActivity.map((val, i) => `${i * 4},${50 - val * 0.5}`).join(' ')}"
							  fill="none" 
							  stroke="#8BE9FD" 
							  stroke-width="1"
							  opacity="0.8"/>
					{#each trafficFlow as point, i}
						{#if point.surge}
							<circle cx="{i * 5}" cy="{50 - point.value * 0.5}" 
									r="2" fill="#FF79C6" opacity="0.8"/>
						{/if}
					{/each}
				</svg>
				<div class="activity-label">GLOBAL TRAFFIC FLOW</div>
			</div>
		</div>
		
		<!-- Middle: Analytics -->
		<div class="analytics-panel">
			<!-- Distribution Chart -->
			<div class="chart-box">
				<h3>HOST DISTRIBUTION BY COUNTRY</h3>
				<div class="distribution-bars">
					{#each topFive as [country, count], i}
						{@const percentage = (count / maxHosts) * 100}
						{@const status = getCountryStatus(count)}
						<div class="dist-item" on:click={() => selectCountry(country, count)}>
							<div class="dist-rank">#{i + 1}</div>
							<div class="dist-name">{country.substring(0, 12).toUpperCase()}</div>
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
			
			<!-- Size Distribution -->
			<div class="chart-box">
				<h3>COUNTRY SIZE DISTRIBUTION</h3>
				<div class="size-chart">
					{@const sizeGroups = countries.reduce((acc, [country, count]) => {
						const size = getCountrySize(count);
						acc[size] = (acc[size] || 0) + 1;
						return acc;
					}, {})}
					{#each Object.entries(sizeGroups) as [size, count], i}
						{@const colors = ['#BD93F9', '#8BE9FD', '#50FA7B', '#FFB86C', '#FF79C6', '#F1FA8C']}
						<div class="size-item">
							<div class="size-label">{size}</div>
							<div class="size-count" style="color: {colors[i % 6]}">{count}</div>
							<div class="size-bar">
								<div class="size-fill" 
									 style="height: {(count / countryCount) * 100}%; 
											background: {colors[i % 6]}">
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Statistics -->
			<div class="chart-box">
				<h3>DISTRIBUTION STATISTICS</h3>
				<div class="coverage-stats">
					<div class="coverage-item">
						<span class="coverage-label">Countries >10K hosts</span>
						<span class="coverage-value" style="color: #BD93F9">
							{countries.filter(([_,c]) => c > 10000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Countries >5K hosts</span>
						<span class="coverage-value" style="color: #8BE9FD">
							{countries.filter(([_,c]) => c > 5000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Countries >1K hosts</span>
						<span class="coverage-value" style="color: #50FA7B">
							{countries.filter(([_,c]) => c > 1000).length}
						</span>
					</div>
				</div>
			</div>
		</div>
		
		<!-- Right: Country List -->
		<div class="list-panel">
			<div class="panel-header">
				<h3>ALL COUNTRIES</h3>
				<span class="country-count">{countries.length} TOTAL</span>
			</div>
			<div class="country-list">
				<table class="countries-table">
					<thead>
						<tr>
							<th>#</th>
							<th>COUNTRY</th>
							<th>HOSTS</th>
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
								<td class="country-name">
									<span class="status-indicator" style="background: {status.color}"></span>
									{country.substring(0, 25).toUpperCase()}
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
	
	/* Country Panel */
	.country-panel {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		position: relative;
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
	
	.controls {
		display: flex;
		gap: 1rem;
		align-items: center;
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
	
	.view-tabs {
		display: flex;
		gap: 2px;
		background: rgba(0, 0, 0, 0.5);
		padding: 2px;
		border-radius: 6px;
	}
	
	.tab {
		padding: 0.4rem 0.8rem;
		background: transparent;
		border: none;
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.65rem;
		font-weight: 600;
		cursor: pointer;
		border-radius: 4px;
		transition: all 0.2s;
	}
	
	.tab:hover {
		background: rgba(139, 233, 253, 0.1);
		color: rgba(255, 255, 255, 0.9);
	}
	
	.tab.active {
		background: rgba(139, 233, 253, 0.2);
		color: #8BE9FD;
	}
	
	/* Map Visualization */
	.map-visualization {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.map-visualization svg {
		width: 100%;
		height: 100%;
	}
	
	.country-node {
		cursor: pointer;
		transition: transform 0.3s;
	}
	
	.country-node:hover {
		transform: scale(1.1);
	}
	
	/* Tree Visualization */
	.tree-visualization {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.tree-container {
		flex: 1;
	}
	
	.tree-root {
		display: flex;
		justify-content: center;
		margin-bottom: 2rem;
	}
	
	.root-node {
		background: rgba(189, 147, 249, 0.1);
		border: 2px solid #BD93F9;
		border-radius: 10px;
		padding: 1rem 2rem;
		text-align: center;
	}
	
	.node-icon {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}
	
	.node-label {
		font-size: 0.8rem;
		color: #BD93F9;
		font-weight: 600;
		letter-spacing: 0.1em;
	}
	
	.node-count {
		font-size: 1rem;
		color: #FFFFFF;
		font-weight: 700;
		margin-top: 0.25rem;
	}
	
	.tree-branches {
		display: flex;
		justify-content: space-around;
		position: relative;
	}
	
	.branch-container {
		position: relative;
		flex: 1;
		max-width: 150px;
	}
	
	.branch-line {
		position: absolute;
		top: -2rem;
		left: 50%;
		width: 1px;
		height: 2rem;
		background: rgba(139, 233, 253, 0.3);
	}
	
	.country-branch-node {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.3s ease;
		overflow: hidden;
	}
	
	.country-branch-node:hover {
		transform: scale(1.05);
		background: rgba(139, 233, 253, 0.05);
	}
	
	.node-header {
		padding: 0.3rem;
		text-align: center;
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.node-rank {
		color: #FFFFFF;
	}
	
	.node-body {
		padding: 0.5rem;
	}
	
	.node-name {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.9);
		margin-bottom: 0.3rem;
		text-align: center;
	}
	
	.node-metrics {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.3rem;
		font-size: 0.7rem;
	}
	
	.node-hosts {
		font-weight: 700;
		font-family: 'Courier New', monospace;
	}
	
	.node-percent {
		color: rgba(255, 255, 255, 0.6);
	}
	
	.node-bar {
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	/* Bubble Chart */
	.bubble-chart {
		height: 140px;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 8px;
		padding: 0.5rem;
	}
	
	.bubble-chart svg {
		width: 100%;
		height: 100%;
	}
	
	.bubble-group {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.bubble-group:hover {
		transform: scale(1.1);
	}
	
	/* Global Activity */
	.global-activity {
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
	
	.global-activity svg {
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
		font-size: 0.5rem;
		color: rgba(255, 255, 255, 0.6);
		writing-mode: vertical-lr;
		text-align: center;
	}
	
	.size-count {
		font-size: 0.9rem;
		font-weight: 700;
	}
	
	.size-bar {
		width: 25px;
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
	
	.country-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.country-list {
		flex: 1;
		overflow-y: auto;
	}
	
	.countries-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.countries-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.9);
		z-index: 10;
	}
	
	.countries-table th {
		padding: 0.5rem;
		text-align: left;
		font-size: 0.6rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.countries-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.countries-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.05);
	}
	
	.countries-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank {
		color: #BD93F9;
		font-weight: 600;
		font-size: 0.65rem;
	}
	
	.country-name {
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
	
	.country-stats {
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
	
	.world-loader {
		display: flex;
		gap: 1.5rem;
		align-items: center;
	}
	
	.continent {
		width: 40px;
		height: 40px;
		background: linear-gradient(135deg, #BD93F9, #8BE9FD);
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
</style>