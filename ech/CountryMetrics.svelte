<!-- CountryMetrics.svelte - Matching Data Center Aesthetic -->
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
		if (percentage >= 75) return { level: 'CRITICAL', color: '#BD93F9', icon: '🔴' };
		if (percentage >= 50) return { level: 'HIGH', color: '#8BE9FD', icon: '🟢' };
		if (percentage >= 25) return { level: 'MODERATE', color: '#50FA7B', icon: '🟡' };
		return { level: 'LOW', color: '#FFB86C', icon: '⚪' };
	}
</script>

<div class="country-interface">
	<!-- Top Metrics -->
	<div class="metrics-ribbon">
		<div class="metric-box">
			<div class="metric-label">COUNTRIES</div>
			<div class="metric-value" style="color: #BD93F9">{countryCount}</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">TOTAL HOSTS</div>
			<div class="metric-value" style="color: #8BE9FD">{totalHosts.toLocaleString()}</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">TOP COUNTRY</div>
			<div class="metric-value" style="color: #50FA7B; font-size: 1.2rem">
				{topCountry[0].substring(0, 20).toUpperCase()}
			</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">GLOBAL COVERAGE</div>
			<div class="metric-value" style="color: #FFB86C">{globalCoverage}%</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">TOP CONCENTRATION</div>
			<div class="metric-value" style="color: #FF79C6">{concentration}%</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content-layout">
		<!-- Left: Country Visualization -->
		<div class="network-panel">
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
								<span>{selectedCountry.count.toLocaleString()} HOSTS</span>
								<span>•</span>
								<span>{((selectedCountry.count/totalHosts)*100).toFixed(2)}% OF GLOBAL</span>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="hosts-list">
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
											<span class="status-ind {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												●
											</span>
										</td>
										<td>
											<span class="status-ind {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
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
						{#each countries.slice(0, 20) as [country, count], i}
							{@const status = getCountryStatus(count)}
							{@const radius = Math.sqrt(count/maxHosts) * 50}
							<g class="country-node" on:click={() => selectCountry(country, count)}>
								<circle 
									cx="{100 + (i % 5) * 180}" 
									cy="{100 + Math.floor(i / 5) * 100}"
									r="{radius}"
									fill="{status.color}"
									opacity="{0.3 + Math.sin(pulsePhase + i) * 0.2}"/>
								<circle 
									cx="{100 + (i % 5) * 180}" 
									cy="{100 + Math.floor(i / 5) * 100}"
									r="{radius * 0.7}"
									fill="{status.color}"
									opacity="0.6"/>
								<text 
									x="{100 + (i % 5) * 180}" 
									y="{85 + Math.floor(i / 5) * 100}"
									text-anchor="middle" 
									fill="#FFFFFF" 
									font-size="10"
									font-weight="600">
									{country.substring(0, 15).toUpperCase()}
								</text>
								<text 
									x="{100 + (i % 5) * 180}" 
									y="{105 + Math.floor(i / 5) * 100}"
									text-anchor="middle" 
									fill="#FFFFFF" 
									font-size="14" 
									font-weight="700">
									{count.toLocaleString()}
								</text>
							</g>
						{/each}
					</svg>
				</div>
			{:else if viewMode === 'grid'}
				<div class="grid-visualization">
					{#each countries.slice(0, 20) as [country, count], i}
						{@const status = getCountryStatus(count)}
						{@const percentage = (count / maxHosts) * 100}
						<div class="grid-card" on:click={() => selectCountry(country, count)}>
							<div class="card-header" style="background: {status.color}20">
								<span class="card-rank">#{i + 1}</span>
								<span class="card-icon">{status.icon}</span>
							</div>
							<div class="card-body">
								<div class="card-name">{country.substring(0, 20).toUpperCase()}</div>
								<div class="card-value" style="color: {status.color}">
									{count.toLocaleString()}
								</div>
								<div class="card-bar">
									<div class="bar-fill" style="width: {percentage}%; background: {status.color}"></div>
								</div>
								<div class="card-footer">
									<span>{percentage.toFixed(0)}%</span>
									<span>{status.level}</span>
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
								<th>STATUS</th>
							</tr>
						</thead>
						<tbody>
							{#each countries as [country, count], i}
								{@const status = getCountryStatus(count)}
								<tr on:click={() => selectCountry(country, count)}>
									<td class="rank">#{i + 1}</td>
									<td class="country-name">
										<span class="status-dot" style="color: {status.color}">●</span>
										{country.toUpperCase()}
									</td>
									<td class="value" style="color: {status.color}">
										{count.toLocaleString()}
									</td>
									<td>{((count/totalHosts)*100).toFixed(2)}%</td>
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
		</div>
		
		<!-- Middle: Analytics -->
		<div class="charts-section">
			<!-- Top Countries Chart -->
			<div class="chart-panel">
				<h3>TOP 10 COUNTRIES</h3>
				<div class="top-countries">
					{#each countries.slice(0, 10) as [country, count], i}
						{@const percentage = (count / maxHosts) * 100}
						{@const status = getCountryStatus(count)}
						<div class="country-bar" on:click={() => selectCountry(country, count)}>
							<div class="bar-info">
								<span class="bar-rank" style="color: {status.color}">#{i + 1}</span>
								<span class="bar-name">{country.substring(0, 12).toUpperCase()}</span>
							</div>
							<div class="bar-track">
								<div class="bar-progress" 
									 style="width: {percentage}%; 
											background: linear-gradient(90deg, {status.color}40, {status.color})">
									<span class="bar-count">{count.toLocaleString()}</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Statistics Panel -->
			<div class="chart-panel">
				<h3>DISTRIBUTION STATISTICS</h3>
				<div class="stat-grid">
					<div class="stat-item">
						<div class="stat-label">Countries >10K hosts</div>
						<div class="stat-value" style="color: #BD93F9">
							{countries.filter(([_,c]) => c > 10000).length}
						</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">Countries >5K hosts</div>
						<div class="stat-value" style="color: #8BE9FD">
							{countries.filter(([_,c]) => c > 5000).length}
						</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">Countries >1K hosts</div>
						<div class="stat-value" style="color: #50FA7B">
							{countries.filter(([_,c]) => c > 1000).length}
						</div>
					</div>
					<div class="stat-item">
						<div class="stat-label">Average per country</div>
						<div class="stat-value" style="color: #FFB86C">
							{avgHosts.toLocaleString()}
						</div>
					</div>
				</div>
			</div>
		</div>
		
		<!-- Right: Quick Stats -->
		<div class="list-panel">
			<div class="panel-header">
				<h3>QUICK ACCESS</h3>
				<span class="country-count">{countries.length} TOTAL</span>
			</div>
			<div class="quick-list">
				{#each countries.slice(0, 15) as [country, count], i}
					{@const status = getCountryStatus(count)}
					<div class="quick-item" on:click={() => selectCountry(country, count)}>
						<span class="quick-rank" style="color: {status.color}">#{i + 1}</span>
						<span class="quick-name">{country.substring(0, 15).toUpperCase()}</span>
						<span class="quick-count" style="color: {status.color}">{count.toLocaleString()}</span>
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
	
	/* Metrics Ribbon */
	.metrics-ribbon {
		display: flex;
		gap: 1rem;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
	}
	
	.metric-box {
		flex: 1;
		text-align: center;
		padding: 0 1rem;
		border-right: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.metric-box:last-child {
		border-right: none;
	}
	
	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		font-weight: 600;
		margin-bottom: 0.5rem;
	}
	
	.metric-value {
		font-size: 1.8rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
	}
	
	/* Content Layout */
	.content-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 380px 250px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Network Panel */
	.network-panel {
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
	
	/* Grid Visualization */
	.grid-visualization {
		flex: 1;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
		gap: 0.75rem;
		padding: 0.5rem;
		overflow-y: auto;
	}
	
	.grid-card {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(139, 233, 253, 0.2);
		border-radius: 8px;
		cursor: pointer;
		overflow: hidden;
		transition: all 0.3s;
	}
	
	.grid-card:hover {
		transform: scale(1.05);
		border-color: #8BE9FD;
		background: rgba(139, 233, 253, 0.05);
	}
	
	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem;
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.card-rank {
		color: #FFFFFF;
	}
	
	.card-icon {
		font-size: 0.8rem;
	}
	
	.card-body {
		padding: 0.75rem;
	}
	
	.card-name {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
		margin-bottom: 0.5rem;
	}
	
	.card-value {
		font-size: 1.2rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
		margin-bottom: 0.5rem;
	}
	
	.card-bar {
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
		margin-bottom: 0.5rem;
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s;
	}
	
	.card-footer {
		display: flex;
		justify-content: space-between;
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
	}
	
	/* List Visualization */
	.list-visualization {
		flex: 1;
		overflow-y: auto;
	}
	
	.country-list-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.country-list-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.9);
		z-index: 10;
	}
	
	.country-list-table th {
		padding: 0.75rem;
		text-align: left;
		font-size: 0.65rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.country-list-table tbody tr {
		cursor: pointer;
		transition: all 0.2s;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.country-list-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.05);
	}
	
	.country-list-table td {
		padding: 0.75rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank {
		color: #BD93F9;
		font-weight: 600;
	}
	
	.country-name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.status-dot {
		font-size: 0.8rem;
	}
	
	.value {
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.status-badge {
		font-size: 0.6rem;
		padding: 0.2rem 0.4rem;
		border: 1px solid;
		border-radius: 4px;
		font-weight: 600;
		letter-spacing: 0.03em;
	}
	
	/* Charts Section */
	.charts-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chart-panel {
		flex: 1;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
	}
	
	.chart-panel h3 {
		margin: 0 0 1rem 0;
		font-size: 0.75rem;
		color: #8BE9FD;
		font-weight: 300;
		letter-spacing: 0.1em;
	}
	
	.top-countries {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.country-bar {
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.country-bar:hover {
		transform: translateX(2px);
	}
	
	.bar-info {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		margin-bottom: 0.25rem;
	}
	
	.bar-rank {
		font-size: 0.65rem;
		font-weight: 600;
	}
	
	.bar-name {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.bar-track {
		height: 18px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.bar-progress {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.5rem;
		transition: width 0.5s ease;
	}
	
	.bar-count {
		font-size: 0.6rem;
		color: #FFFFFF;
		font-weight: 600;
	}
	
	.stat-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.75rem;
	}
	
	.stat-item {
		background: rgba(0, 0, 0, 0.5);
		border-radius: 6px;
		padding: 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.stat-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
	}
	
	.stat-value {
		font-size: 1.5rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
	}
	
	/* Quick List Panel */
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
	
	.quick-list {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
	}
	
	.quick-item {
		display: grid;
		grid-template-columns: 30px 1fr auto;
		gap: 0.5rem;
		align-items: center;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 4px;
		margin-bottom: 0.5rem;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.quick-item:hover {
		background: rgba(139, 233, 253, 0.05);
		transform: translateX(2px);
	}
	
	.quick-rank {
		font-size: 0.65rem;
		font-weight: 600;
	}
	
	.quick-name {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.quick-count {
		font-size: 0.7rem;
		font-weight: 600;
		font-family: 'Courier New', monospace;
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
	
	.hosts-list {
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
	
	.status-ind {
		font-size: 0.8rem;
	}
	
	.status-ind.active {
		color: #50FA7B;
	}
	
	.status-ind.inactive {
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
	
	::-webkit-scrollbar-thumb:hover {
		background: rgba(189, 147, 249, 0.5);
	}
</style>