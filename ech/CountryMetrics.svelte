<!-- CountryMetrics.svelte - Enhanced with Perfect Screen Fit -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 10;
	let viewMode = 'table';

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
	});

	$: sortedCountries = data.global_intelligence ? 
		Object.entries(data.global_intelligence)
			.filter(([country]) => country.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: paginatedCountries = sortedCountries.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(sortedCountries.length / itemsPerPage);

	$: maxCount = sortedCountries.length > 0 ? Math.max(...sortedCountries.map(([,c]) => c)) : 1;

	function getThreatLevel(count) {
		if (!data.total_countries) return { level: 'LOW', color: '#00ffff', intensity: 0.3 };
		let percentage = (count / maxCount) * 100;
		if (percentage >= 60) return { level: 'CRITICAL', color: '#ff00ff', intensity: 1.0 };
		if (percentage >= 40) return { level: 'HIGH', color: '#ff0066', intensity: 0.8 };
		if (percentage >= 20) return { level: 'MEDIUM', color: '#ffaa00', intensity: 0.6 };
		return { level: 'LOW', color: '#00ffff', intensity: 0.4 };
	}

	function getPercentage(count) {
		let total = Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
	}

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

	$: threatDistribution = sortedCountries.reduce((acc, [_, count]) => {
		let level = getThreatLevel(count).level;
		acc[level] = (acc[level] || 0) + 1;
		return acc;
	}, {});
</script>

<div class="dashboard-container">
	<!-- Header Section -->
	<div class="header-section">
		<div class="header-content">
			<div class="title-block">
				<div class="title-icon">🌍</div>
				<div class="title-text">
					<h1>GLOBAL SURVEILLANCE</h1>
					<p>Country Distribution Matrix</p>
				</div>
			</div>
			<div class="metrics-row">
				<div class="metric-card">
					<div class="metric-value">{(data.total_countries || 0).toLocaleString()}</div>
					<div class="metric-label">COUNTRIES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL ASSETS</div>
				</div>
				<div class="metric-card primary">
					<div class="metric-value">{sortedCountries[0] ? sortedCountries[0][0].toUpperCase() : 'N/A'}</div>
					<div class="metric-label">PRIMARY</div>
				</div>
				<div class="metric-card critical">
					<div class="metric-value">{threatDistribution['CRITICAL'] || 0}</div>
					<div class="metric-label">CRITICAL</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content Area -->
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<h3>COUNTRY ANALYSIS</h3>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search countries..."
						class="search-input"
					/>
					<div class="view-toggle">
						<button class="toggle-btn {viewMode === 'table' ? 'active' : ''}" on:click={() => viewMode = 'table'}>
							TABLE
						</button>
						<button class="toggle-btn {viewMode === 'grid' ? 'active' : ''}" on:click={() => viewMode = 'grid'}>
							GRID
						</button>
					</div>
				</div>
			</div>
			
			{#if loading && !selectedCountry}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>Scanning global network...</p>
				</div>
			{:else if selectedCountry}
				<!-- Drill-down View -->
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedCountry.country.toUpperCase()}</h4>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>REGION</th>
									<th>INFRASTRUCTURE</th>
									<th>DATACENTER</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each countryDetails as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.region || 'Unknown'}</td>
										<td>{host.infrastructure_type || 'Unknown'}</td>
										<td>{host.data_center || 'N/A'}</td>
										<td>
											<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '✓' : '✗'}
											</span>
										</td>
										<td>
											<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? '✓' : '✗'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else if viewMode === 'table'}
				<!-- Main Table -->
				<div class="table-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>COUNTRY</th>
								<th>ASSETS</th>
								<th>COVERAGE</th>
								<th>THREAT</th>
								<th>ACTION</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedCountries as [country, count]}
								<tr>
									<td class="country-cell">
										<div class="cell-content">
											<span class="indicator" style="background: {getThreatLevel(count).color}"></span>
											<span>{country.toUpperCase()}</span>
										</div>
									</td>
									<td class="center">{count.toLocaleString()}</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {getPercentage(count)}%; background: {getThreatLevel(count).color}"></div>
											</div>
											<span class="coverage-text">{getPercentage(count)}%</span>
										</div>
									</td>
									<td class="center">
										<span class="threat-badge {getThreatLevel(count).level.toLowerCase()}">{getThreatLevel(count).level}</span>
									</td>
									<td class="center">
										<button class="drill-btn" on:click={() => drillDownCountry(country, count)}>
											ANALYZE →
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				
				<!-- Pagination -->
				<div class="pagination">
					<button 
						on:click={() => currentPage = Math.max(1, currentPage - 1)}
						disabled={currentPage === 1}
					>
						←
					</button>
					<span>Page {currentPage} of {totalPages}</span>
					<button 
						on:click={() => currentPage = Math.min(totalPages, currentPage + 1)}
						disabled={currentPage === totalPages}
					>
						→
					</button>
				</div>
			{:else}
				<!-- Grid View -->
				<div class="grid-container">
					{#each paginatedCountries as [country, count]}
						<div class="grid-card" style="--card-color: {getThreatLevel(count).color}" on:click={() => drillDownCountry(country, count)}>
							<div class="card-header">
								<span class="card-icon">🌐</span>
								<span class="threat-indicator {getThreatLevel(count).level.toLowerCase()}">{getThreatLevel(count).level}</span>
							</div>
							<div class="card-body">
								<div class="country-name">{country.toUpperCase()}</div>
								<div class="country-count">{count.toLocaleString()}</div>
								<div class="progress-bar">
									<div class="progress-fill" style="width: {(count/maxCount)*100}%; background: {getThreatLevel(count).color}"></div>
								</div>
								<div class="card-percentage">{getPercentage(count)}%</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Right Panel: Visualizations -->
		<div class="viz-panel">
			<!-- World Heat Map -->
			<div class="viz-card">
				<h4>GLOBAL HEATMAP</h4>
				<div class="world-map">
					<svg viewBox="0 0 300 150">
						<defs>
							<radialGradient id="heat">
								<stop offset="0%" style="stop-color:#ff00ff;stop-opacity:0.8" />
								<stop offset="100%" style="stop-color:#ff00ff;stop-opacity:0" />
							</radialGradient>
						</defs>
						{#each sortedCountries.slice(0, 8) as [country, count], i}
							<circle 
								cx={50 + (i % 4) * 70} 
								cy={50 + Math.floor(i / 4) * 60} 
								r={Math.sqrt((count/maxCount)) * 25} 
								fill="url(#heat)" 
								opacity="0.7"
							/>
							<text 
								x={50 + (i % 4) * 70} 
								y={50 + Math.floor(i / 4) * 60 + 35} 
								text-anchor="middle" 
								fill="#00ffff" 
								font-size="8"
							>
								{country.substring(0, 6).toUpperCase()}
							</text>
						{/each}
					</svg>
				</div>
			</div>

			<!-- Threat Distribution -->
			<div class="viz-card">
				<h4>THREAT DISTRIBUTION</h4>
				<div class="donut-chart">
					<svg viewBox="0 0 200 200">
						{#if Object.keys(threatDistribution).length > 0}
							{#each Object.entries(threatDistribution) as [level, count], i}
								<circle
									cx="100"
									cy="100"
									r={60 - i * 10}
									fill="none"
									stroke={level === 'CRITICAL' ? '#ff00ff' : level === 'HIGH' ? '#ff0066' : level === 'MEDIUM' ? '#ffaa00' : '#00ffff'}
									stroke-width="8"
									stroke-dasharray={`${(count / sortedCountries.length) * 377} 377`}
									transform="rotate(-90 100 100)"
									opacity="0.8"
								/>
							{/each}
						{/if}
						<text x="100" y="100" text-anchor="middle" fill="white" font-size="24" font-weight="bold">
							{sortedCountries.length}
						</text>
						<text x="100" y="115" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="10">
							COUNTRIES
						</text>
					</svg>
				</div>
			</div>

			<!-- Top Countries Bar Chart -->
			<div class="viz-card">
				<h4>TOP 5 COUNTRIES</h4>
				<div class="bar-chart">
					{#each sortedCountries.slice(0, 5) as [country, count]}
						<div class="bar-item">
							<div class="bar-label">{country.toUpperCase()}</div>
							<div class="bar-container">
								<div class="bar-fill" 
									style="width: {(count/maxCount)*100}%; background: linear-gradient(90deg, {getThreatLevel(count).color}, {getThreatLevel(count).color}80)">
								</div>
								<span class="bar-value">{count.toLocaleString()}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Activity Matrix -->
			<div class="viz-card">
				<h4>ACTIVITY MATRIX</h4>
				<div class="matrix-grid">
					{#each paginatedCountries.slice(0, 9) as [country, count]}
						<div class="matrix-cell" style="background: {getThreatLevel(count).color}20; border-color: {getThreatLevel(count).color}">
							<div class="cell-value">{getPercentage(count)}%</div>
							<div class="cell-label">{country.substring(0, 3).toUpperCase()}</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.dashboard-container {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
		color: #fff;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
	}

	.header-section {
		background: rgba(0, 0, 0, 0.8);
		border-bottom: 2px solid rgba(255, 0, 255, 0.3);
		padding: 0.8rem 1rem;
		backdrop-filter: blur(10px);
		flex-shrink: 0;
	}

	.header-content {
		max-width: 100%;
	}

	.title-block {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		margin-bottom: 0.6rem;
	}

	.title-icon {
		font-size: 1.5rem;
		filter: hue-rotate(280deg) saturate(2);
		animation: iconFloat 3s ease-in-out infinite;
	}

	.title-text h1 {
		margin: 0;
		font-size: 1.2rem;
		color: #ff00ff;
		text-shadow: 0 0 10px rgba(255, 0, 255, 0.5);
		letter-spacing: 0.1em;
	}

	.title-text p {
		margin: 0.2rem 0 0 0;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.metrics-row {
		display: flex;
		gap: 0.8rem;
	}

	.metric-card {
		flex: 1;
		background: rgba(255, 0, 255, 0.05);
		border: 1px solid rgba(255, 0, 255, 0.3);
		border-radius: 6px;
		padding: 0.5rem;
		text-align: center;
		transition: all 0.3s ease;
	}

	.metric-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(255, 0, 255, 0.2);
	}

	.metric-card.primary {
		background: rgba(0, 255, 133, 0.05);
		border-color: rgba(0, 255, 133, 0.3);
	}

	.metric-card.critical {
		background: rgba(255, 0, 102, 0.05);
		border-color: rgba(255, 0, 102, 0.3);
	}

	.metric-value {
		font-size: 1.1rem;
		font-weight: 700;
		color: #ff00ff;
		text-shadow: 0 0 10px currentColor;
	}

	.metric-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.2rem;
		letter-spacing: 0.05em;
	}

	.main-content {
		flex: 1;
		display: flex;
		gap: 0.8rem;
		padding: 0.8rem;
		overflow: hidden;
		min-height: 0;
	}

	.table-panel {
		flex: 2;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 8px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		overflow-y: auto;
		min-width: 300px;
	}

	.panel-header {
		padding: 0.8rem;
		border-bottom: 1px solid rgba(255, 0, 255, 0.2);
		background: rgba(0, 0, 0, 0.3);
	}

	.panel-header h3 {
		margin: 0 0 0.5rem 0;
		font-size: 0.8rem;
		color: #ff00ff;
		letter-spacing: 0.05em;
	}

	.controls {
		display: flex;
		gap: 0.8rem;
		align-items: center;
	}

	.search-input {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 0, 255, 0.3);
		border-radius: 4px;
		padding: 0.3rem 0.6rem;
		color: #fff;
		font-size: 0.7rem;
	}

	.search-input:focus {
		outline: none;
		border-color: #ff00ff;
		box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
	}

	.view-toggle {
		display: flex;
		gap: 0.2rem;
	}

	.toggle-btn {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 0, 255, 0.3);
		color: rgba(255, 255, 255, 0.7);
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.6rem;
		transition: all 0.3s ease;
	}

	.toggle-btn.active {
		background: rgba(255, 0, 255, 0.1);
		border-color: #ff00ff;
		color: #ff00ff;
	}

	.table-container {
		flex: 1;
		overflow: auto;
		padding: 0.5rem;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.7rem;
	}

	.data-table th {
		background: rgba(255, 0, 255, 0.1);
		color: #ff00ff;
		padding: 0.5rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.data-table td {
		padding: 0.4rem 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.8);
	}

	.data-table tr:hover {
		background: rgba(255, 0, 255, 0.05);
	}

	.country-cell .cell-content {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.indicator {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
		animation: pulse 2s infinite;
	}

	.center {
		text-align: center;
	}

	.coverage-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.coverage-bar {
		flex: 1;
		height: 5px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 3px;
		overflow: hidden;
		min-width: 60px;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 10px currentColor;
	}

	.coverage-text {
		font-size: 0.65rem;
		min-width: 40px;
		text-align: right;
	}

	.threat-badge {
		padding: 0.15rem 0.4rem;
		border-radius: 3px;
		font-size: 0.6rem;
		font-weight: 600;
	}

	.threat-badge.critical {
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
	}

	.threat-badge.high {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.threat-badge.medium {
		background: rgba(255, 170, 0, 0.2);
		color: #ffaa00;
		border: 1px solid #ffaa00;
	}

	.threat-badge.low {
		background: rgba(0, 255, 255, 0.2);
		color: #00ffff;
		border: 1px solid #00ffff;
	}

	.drill-btn {
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid #ff00ff;
		color: #ff00ff;
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.6rem;
		transition: all 0.3s ease;
	}

	.drill-btn:hover {
		background: rgba(255, 0, 255, 0.2);
		transform: translateX(2px);
		box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
	}

	.grid-container {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		gap: 0.6rem;
		padding: 0.6rem;
		overflow-y: auto;
		flex: 1;
	}

	.grid-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid var(--card-color);
		border-radius: 6px;
		padding: 0.8rem;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.grid-card:hover {
		transform: translateY(-3px);
		box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 20px var(--card-color);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.card-icon {
		font-size: 1rem;
	}

	.threat-indicator {
		font-size: 0.5rem;
		padding: 0.1rem 0.3rem;
		border-radius: 3px;
		font-weight: 600;
	}

	.threat-indicator.critical {
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
	}

	.threat-indicator.high {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.threat-indicator.medium {
		background: rgba(255, 170, 0, 0.2);
		color: #ffaa00;
		border: 1px solid #ffaa00;
	}

	.threat-indicator.low {
		background: rgba(0, 255, 255, 0.2);
		color: #00ffff;
		border: 1px solid #00ffff;
	}

	.card-body {
		text-align: center;
	}

	.country-name {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.9);
		margin-bottom: 0.3rem;
		font-weight: 600;
	}

	.country-count {
		font-size: 1.1rem;
		font-weight: 700;
		color: var(--card-color);
		text-shadow: 0 0 10px var(--card-color);
		margin-bottom: 0.3rem;
	}

	.progress-bar {
		width: 100%;
		height: 3px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 2px;
		overflow: hidden;
		margin-bottom: 0.2rem;
	}

	.progress-fill {
		height: 100%;
		transition: width 0.5s ease;
	}

	.card-percentage {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		padding: 0.6rem;
		border-top: 1px solid rgba(255, 0, 255, 0.2);
		background: rgba(0, 0, 0, 0.3);
	}

	.pagination button {
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid #ff00ff;
		color: #ff00ff;
		padding: 0.3rem 0.6rem;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.3s ease;
		font-size: 0.65rem;
	}

	.pagination button:hover:not(:disabled) {
		background: rgba(255, 0, 255, 0.2);
		transform: scale(1.05);
	}

	.pagination button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.pagination span {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.viz-card {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 6px;
		padding: 0.6rem;
		animation: vizEntrance 0.6s ease-out;
	}

	.viz-card h4 {
		margin: 0 0 0.5rem 0;
		font-size: 0.65rem;
		color: #ff00ff;
		letter-spacing: 0.05em;
		text-align: center;
	}

	.world-map {
		width: 100%;
		display: flex;
		justify-content: center;
	}

	.donut-chart {
		width: 100%;
		max-width: 180px;
		margin: 0 auto;
	}

	.bar-chart {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.bar-item {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.bar-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.bar-container {
		position: relative;
		height: 16px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 3px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
		position: relative;
		overflow: hidden;
	}

	.bar-fill::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
		animation: shimmer 2s infinite;
	}

	.bar-value {
		position: absolute;
		right: 0.3rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.55rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
	}

	.matrix-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.3rem;
	}

	.matrix-cell {
		aspect-ratio: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		border: 1px solid;
		border-radius: 3px;
		padding: 0.3rem;
	}

	.cell-value {
		font-size: 0.6rem;
		font-weight: 600;
		color: #fff;
	}

	.cell-label {
		font-size: 0.45rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.1rem;
	}

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 3px solid rgba(255, 0, 255, 0.2);
		border-top-color: #ff00ff;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.drill-view {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.drill-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.8rem;
		border-bottom: 1px solid rgba(255, 0, 102, 0.3);
		background: rgba(255, 0, 102, 0.05);
	}

	.drill-header h4 {
		margin: 0;
		color: #ff0066;
		font-size: 0.8rem;
	}

	.close-btn {
		background: transparent;
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.3s ease;
		font-size: 0.7rem;
	}

	.close-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: rotate(90deg);
	}

	.host-cell {
		font-family: monospace;
		color: #00ffff;
		font-size: 0.7rem;
	}

	.status-badge {
		padding: 0.1rem 0.3rem;
		border-radius: 3px;
		font-size: 0.6rem;
		font-weight: 600;
	}

	.status-badge.active {
		background: rgba(0, 255, 133, 0.2);
		color: #00ff85;
		border: 1px solid #00ff85;
	}

	.status-badge.inactive {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	@keyframes shimmer {
		to { left: 100%; }
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-3px); }
	}

	@keyframes vizEntrance {
		from { opacity: 0; transform: translateX(20px); }
		to { opacity: 1; transform: translateX(0); }
	}

	@media (max-width: 1200px) {
		.main-content {
			flex-direction: column;
		}
		
		.viz-panel {
			flex-direction: row;
			overflow-x: auto;
			min-width: auto;
		}
		
		.viz-card {
			min-width: 250px;
		}
	}
</style>