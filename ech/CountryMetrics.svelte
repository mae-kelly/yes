<!-- CountryMetrics.svelte - Country Host Distribution -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';
	
	// Animation states
	let animationFrame = null;
	let waveOffset = 0;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/country_metrics');
			let result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			console.error('Country metrics error:', err);
			loading = false;
		}
		
		// Start animations
		const animate = () => {
			waveOffset = (waveOffset + 1) % 100;
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
	$: avgHostsPerCountry = countries.length > 0 ? Math.round(totalHosts / countries.length) : 0;
	
	// Key metrics
	$: topCountry = countries[0] || ['N/A', 0];
	$: countryCount = countries.length;
	$: globalCoverage = ((countryCount / 195) * 100).toFixed(1); // ~195 countries in the world
	$: concentration = topCountry[1] > 0 ? ((topCountry[1] / totalHosts) * 100).toFixed(1) : 0;
	
	// Top 10 for chart
	$: topTen = countries.slice(0, 10);

	async function drillDownCountry(country, count) {
		selectedCountry = { country, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(country)}`);
			let result = await response.json();
			countryDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Country drill-down error:', err);
			countryDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedCountry = null;
		countryDetails = [];
	}
	
	function getCountryStatus(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#BD93F9', icon: '⚡' };
		if (percentage >= 50) return { level: 'HIGH', color: '#8BE9FD', icon: '◆' };
		if (percentage >= 25) return { level: 'MODERATE', color: '#50FA7B', icon: '●' };
		return { level: 'LOW', color: '#FFB86C', icon: '○' };
	}
	
	function getRegionFromCountry(country) {
		// Simple mapping - in production would use proper geo data
		const regions = {
			'united states': 'AMERICAS',
			'canada': 'AMERICAS',
			'brazil': 'AMERICAS',
			'united kingdom': 'EUROPE',
			'germany': 'EUROPE',
			'france': 'EUROPE',
			'china': 'ASIA',
			'japan': 'ASIA',
			'india': 'ASIA',
			'australia': 'OCEANIA'
		};
		return regions[country.toLowerCase()] || 'OTHER';
	}
</script>

<div class="country-interface">
	<div class="interface-layout">
		<!-- Top Stats -->
		<div class="stats-row">
			<div class="stat-card">
				<div class="stat-icon">🌍</div>
				<div class="stat-content">
					<div class="stat-value" style="color: #BD93F9">{countryCount}</div>
					<div class="stat-label">COUNTRIES</div>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon">💻</div>
				<div class="stat-content">
					<div class="stat-value" style="color: #8BE9FD">{totalHosts.toLocaleString()}</div>
					<div class="stat-label">TOTAL HOSTS</div>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon">📍</div>
				<div class="stat-content">
					<div class="stat-value" style="color: #50FA7B">{topCountry[0].toUpperCase()}</div>
					<div class="stat-label">TOP COUNTRY</div>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon">🌐</div>
				<div class="stat-content">
					<div class="stat-value" style="color: #FFB86C">{globalCoverage}%</div>
					<div class="stat-label">GLOBAL COVERAGE</div>
				</div>
			</div>
			<div class="stat-card">
				<div class="stat-icon">📊</div>
				<div class="stat-content">
					<div class="stat-value" style="color: #FF79C6">{concentration}%</div>
					<div class="stat-label">TOP CONCENTRATION</div>
				</div>
			</div>
		</div>
		
		<!-- Main Content -->
		<div class="content-area">
			<!-- Left: Geo Visualization -->
			<div class="geo-panel">
				<div class="panel-header">
					<h2>GLOBAL HOST INFRASTRUCTURE</h2>
					<input type="text"
						   bind:value={searchTerm}
						   placeholder="Search countries..."
						   class="search-input"/>
				</div>
				
				{#if loading && !selectedCountry}
					<div class="loading-state">
						<div class="world-loader">
							<div class="continent con-1"></div>
							<div class="continent con-2"></div>
							<div class="continent con-3"></div>
						</div>
						<p>MAPPING GLOBAL INFRASTRUCTURE...</p>
					</div>
				{:else if selectedCountry}
					<div class="detail-view">
						<div class="detail-header">
							<div class="country-info">
								<h3>{selectedCountry.country.toUpperCase()}</h3>
								<div class="country-stats">
									<span>{selectedCountry.count.toLocaleString()} HOSTS</span>
									<span>•</span>
									<span>{((selectedCountry.count / totalHosts) * 100).toFixed(2)}% OF TOTAL</span>
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
										<th>INFRASTRUCTURE</th>
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
					<div class="geo-visualization">
						<!-- World Bubble Map -->
						<div class="bubble-map">
							<svg viewBox="0 0 1200 600">
								<defs>
									<linearGradient id="bubbleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
										<stop offset="0%" style="stop-color:#BD93F9;stop-opacity:1" />
										<stop offset="100%" style="stop-color:#8BE9FD;stop-opacity:1" />
									</linearGradient>
								</defs>
								
								<!-- Grid lines -->
								{#each Array(5) as _, i}
									<line x1="0" y1="{i * 150}" x2="1200" y2="{i * 150}" 
										  stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
									<line x1="{i * 300}" y1="0" x2="{i * 300}" y2="600" 
										  stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
								{/each}
								
								<!-- Country bubbles -->
								{#each topTen as [country, count], i}
									{@const x = 150 + (i % 5) * 220}
									{@const y = 200 + Math.floor(i / 5) * 200}
									{@const radius = Math.sqrt(count / maxHosts) * 60}
									{@const status = getCountryStatus(count)}
									
									<g class="country-bubble" on:click={() => drillDownCountry(country, count)}>
										<!-- Outer ring -->
										<circle cx="{x}" cy="{y}" r="{radius + 10}" 
												fill="none" stroke="{status.color}" stroke-width="1" 
												opacity="0.3" stroke-dasharray="5,5">
											<animate attributeName="stroke-dashoffset" 
													 values="0;10" dur="2s" repeatCount="indefinite"/>
										</circle>
										<!-- Main bubble -->
										<circle cx="{x}" cy="{y}" r="{radius}" 
												fill="{status.color}" opacity="0.4"/>
										<!-- Inner core -->
										<circle cx="{x}" cy="{y}" r="{radius * 0.6}" 
												fill="{status.color}" opacity="0.8"/>
										<!-- Country name -->
										<text x="{x}" y="{y - radius - 15}" 
											  text-anchor="middle" fill="#FFFFFF" 
											  font-size="11" font-weight="600">
											{country.substring(0, 20).toUpperCase()}
										</text>
										<!-- Host count -->
										<text x="{x}" y="{y}" 
											  text-anchor="middle" fill="#FFFFFF" 
											  font-size="16" font-weight="700">
											{count.toLocaleString()}
										</text>
										<!-- Icon -->
										<text x="{x}" y="{y + 20}" 
											  text-anchor="middle" fill="#FFFFFF" 
											  font-size="20">
											{status.icon}
										</text>
									</g>
								{/each}
							</svg>
						</div>
						
						<!-- Heatmap Grid -->
						<div class="heatmap-section">
							<h3>HOST DENSITY HEATMAP</h3>
							<div class="heatmap-grid">
								{#each countries.slice(0, 50) as [country, count], i}
									{@const intensity = count / maxHosts}
									{@const status = getCountryStatus(count)}
									<div class="heat-cell"
										 style="background: {status.color}; 
												opacity: {0.2 + intensity * 0.8}"
										 title="{country}: {count} hosts"
										 on:click={() => drillDownCountry(country, count)}>
									</div>
								{/each}
							</div>
						</div>
					</div>
				{/if}
			</div>
			
			<!-- Middle: Charts -->
			<div class="charts-panel">
				<!-- Horizontal Bar Chart -->
				<div class="chart-box">
					<h3>TOP 10 COUNTRIES BY HOST COUNT</h3>
					<div class="h-bar-chart">
						{#each topTen as [country, count], i}
							{@const percentage = (count / maxHosts) * 100}
							{@const status = getCountryStatus(count)}
							<div class="h-bar-item" on:click={() => drillDownCountry(country, count)}>
								<div class="h-bar-rank">#{i + 1}</div>
								<div class="h-bar-country">{country.substring(0, 15).toUpperCase()}</div>
								<div class="h-bar-track">
									<div class="h-bar-fill" 
										 style="width: {percentage}%; 
												background: linear-gradient(90deg, {status.color}40, {status.color})">
										<span class="h-bar-value">{count.toLocaleString()}</span>
									</div>
								</div>
								<div class="h-bar-percent">{((count/totalHosts)*100).toFixed(1)}%</div>
							</div>
						{/each}
					</div>
				</div>
				
				<!-- Regional Distribution -->
				<div class="chart-box">
					<h3>REGIONAL DISTRIBUTION</h3>
					<div class="region-bars">
						{@const regionGroups = countries.reduce((acc, [country, count]) => {
							const region = getRegionFromCountry(country);
							acc[region] = (acc[region] || 0) + count;
							return acc;
						}, {})}
						{#each Object.entries(regionGroups).sort((a, b) => b[1] - a[1]) as [region, count], i}
							{@const maxRegion = Math.max(...Object.values(regionGroups))}
							{@const height = (count / maxRegion) * 100}
							<div class="region-bar">
								<div class="region-column">
									<div class="region-fill" 
										 style="height: {height}%; 
												background: {['#BD93F9', '#8BE9FD', '#50FA7B', '#FFB86C', '#FF79C6'][i % 5]}">
										<span class="region-value">{count.toLocaleString()}</span>
									</div>
								</div>
								<div class="region-label">{region}</div>
							</div>
						{/each}
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
								<th>%</th>
								<th>STATUS</th>
							</tr>
						</thead>
						<tbody>
							{#each countries as [country, count], i}
								{@const percentage = ((count / totalHosts) * 100).toFixed(2)}
								{@const status = getCountryStatus(count)}
								<tr on:click={() => drillDownCountry(country, count)}>
									<td class="rank">{i + 1}</td>
									<td class="country-name">
										<span class="status-icon">{status.icon}</span>
										{country.substring(0, 20).toUpperCase()}
									</td>
									<td class="host-count" style="color: {status.color}">
										{count.toLocaleString()}
									</td>
									<td class="percentage">{percentage}%</td>
									<td>
										<span class="status-badge" 
											  style="background: {status.color}20; 
													 color: {status.color};
													 border: 1px solid {status.color}">
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
	.country-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		overflow: hidden;
	}
	
	.interface-layout {
		height: 100%;
		display: flex;
		flex-direction: column;
		padding: 1rem;
		gap: 1rem;
	}
	
	/* Stats Row */
	.stats-row {
		display: flex;
		gap: 1rem;
	}
	
	.stat-card {
		flex: 1;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		gap: 1rem;
		align-items: center;
	}
	
	.stat-icon {
		font-size: 2rem;
	}
	
	.stat-content {
		flex: 1;
	}
	
	.stat-value {
		font-size: 1.5rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
		margin-bottom: 0.25rem;
	}
	
	.stat-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		font-weight: 600;
	}
	
	/* Content Area */
	.content-area {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 400px 320px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Geo Panel */
	.geo-panel {
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
	
	.geo-visualization {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.bubble-map {
		flex: 2;
	}
	
	.bubble-map svg {
		width: 100%;
		height: 100%;
	}
	
	.country-bubble {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.country-bubble:hover {
		transform: scale(1.1);
	}
	
	.heatmap-section {
		flex: 1;
	}
	
	.heatmap-section h3 {
		margin: 0 0 0.5rem 0;
		font-size: 0.8rem;
		color: #8BE9FD;
		font-weight: 300;
		letter-spacing: 0.1em;
	}
	
	.heatmap-grid {
		display: grid;
		grid-template-columns: repeat(10, 1fr);
		grid-template-rows: repeat(5, 1fr);
		gap: 2px;
		height: 100px;
		background: rgba(0, 0, 0, 0.5);
		padding: 4px;
		border-radius: 8px;
	}
	
	.heat-cell {
		border-radius: 2px;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	.heat-cell:hover {
		transform: scale(1.5);
		z-index: 10;
		box-shadow: 0 0 10px currentColor;
	}
	
	/* Charts Panel */
	.charts-panel {
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
	
	.h-bar-chart {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	
	.h-bar-item {
		display: grid;
		grid-template-columns: 20px 100px 1fr 40px;
		gap: 0.5rem;
		align-items: center;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	.h-bar-item:hover {
		transform: translateX(2px);
	}
	
	.h-bar-rank {
		font-size: 0.65rem;
		color: #BD93F9;
		font-weight: 600;
	}
	
	.h-bar-country {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.h-bar-track {
		height: 18px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.h-bar-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.4rem;
		transition: width 0.5s ease;
		border-radius: 4px;
	}
	
	.h-bar-value {
		font-size: 0.6rem;
		color: #FFFFFF;
		font-weight: 600;
	}
	
	.h-bar-percent {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		text-align: right;
	}
	
	.region-bars {
		flex: 1;
		display: flex;
		align-items: flex-end;
		gap: 0.5rem;
	}
	
	.region-bar {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}
	
	.region-column {
		width: 100%;
		height: 120px;
		display: flex;
		align-items: flex-end;
	}
	
	.region-fill {
		width: 100%;
		display: flex;
		align-items: flex-start;
		justify-content: center;
		padding-top: 0.25rem;
		border-radius: 4px 4px 0 0;
		transition: height 0.5s ease;
	}
	
	.region-value {
		font-size: 0.6rem;
		color: #FFFFFF;
		font-weight: 600;
	}
	
	.region-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		writing-mode: vertical-lr;
		text-align: center;
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
		gap: 0.3rem;
		font-size: 0.65rem;
	}
	
	.status-icon {
		font-size: 0.8rem;
	}
	
	.host-count {
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.percentage {
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.65rem;
	}
	
	.status-badge {
		font-size: 0.55rem;
		padding: 0.15rem 0.3rem;
		border-radius: 3px;
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
	
	.country-info h3 {
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
		position: relative;
		width: 120px;
		height: 120px;
	}
	
	.continent {
		position: absolute;
		background: linear-gradient(135deg, #BD93F9, #8BE9FD);
		border-radius: 50%;
		animation: float 3s ease-in-out infinite;
	}
	
	.con-1 {
		width: 40px;
		height: 40px;
		top: 10px;
		left: 40px;
	}
	
	.con-2 {
		width: 50px;
		height: 50px;
		top: 40px;
		left: 10px;
		animation-delay: 0.5s;
	}
	
	.con-3 {
		width: 30px;
		height: 30px;
		top: 60px;
		left: 60px;
		animation-delay: 1s;
	}
	
	@keyframes float {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-10px); }
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