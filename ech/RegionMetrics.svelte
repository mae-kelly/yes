<!-- RegionMetrics.svelte - Optimized -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 8;
	let viewMode = 'table';

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

	$: sortedRegions = data.global_surveillance ? 
		Object.entries(data.global_surveillance)
			.filter(([region]) => region.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: paginatedRegions = sortedRegions.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(sortedRegions.length / itemsPerPage);

	function getThreatLevel(count) {
		if (!data.total_coverage) return { level: 'LOW', color: '#0a4f3c', intensity: 0.3 };
		let percentage = (count / data.total_coverage) * 100;
		if (percentage >= 40) return { level: 'CRITICAL', color: '#ff0066', intensity: 1.0 };
		if (percentage >= 25) return { level: 'HIGH', color: '#ff9900', intensity: 0.8 };
		if (percentage >= 15) return { level: 'MEDIUM', color: '#ffcc00', intensity: 0.6 };
		return { level: 'LOW', color: '#0a4f3c', intensity: 0.4 };
	}

	function getPercentage(count) {
		if (!data.total_coverage) return 0;
		return ((count / data.total_coverage) * 100).toFixed(2);
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

	$: threatDistribution = sortedRegions.reduce((acc, [_, count]) => {
		let level = getThreatLevel(count).level;
		acc[level] = (acc[level] || 0) + 1;
		return acc;
	}, {});

	$: maxCount = sortedRegions.length > 0 ? Math.max(...sortedRegions.map(([,c]) => c)) : 1;
</script>

<div class="region-dashboard">
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search regions..."
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
			
			{#if loading && !selectedRegion}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>Scanning regions...</p>
				</div>
			{:else if selectedRegion}
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedRegion.region.toUpperCase()}</h4>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>COUNTRY</th>
									<th>INFRA</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each regionDetails.slice(0, 6) as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.country || 'Unknown'}</td>
										<td>{host.infrastructure_type || 'Unknown'}</td>
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
				<div class="table-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>REGION</th>
								<th>ASSETS</th>
								<th>COVERAGE</th>
								<th>THREAT</th>
								<th>ACTION</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedRegions as [region, count]}
								{@const threat = getThreatLevel(count)}
								<tr>
									<td class="region-cell">
										<span class="indicator" style="background: {threat.color}"></span>
										<span>{region.toUpperCase()}</span>
									</td>
									<td class="center">{count.toLocaleString()}</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {getPercentage(count)}%; background: {threat.color}"></div>
											</div>
											<span class="coverage-text">{getPercentage(count)}%</span>
										</div>
									</td>
									<td class="center">
										<span class="threat-badge {threat.level.toLowerCase()}">{threat.level}</span>
									</td>
									<td class="center">
										<button class="drill-btn" on:click={() => drillDownRegion(region, count)}>→</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				
				<div class="pagination">
					<button on:click={() => currentPage = Math.max(1, currentPage - 1)} disabled={currentPage === 1}>←</button>
					<span>{currentPage}/{totalPages}</span>
					<button on:click={() => currentPage = Math.min(totalPages, currentPage + 1)} disabled={currentPage === totalPages}>→</button>
				</div>
			{:else}
				<div class="grid-container">
					{#each paginatedRegions.slice(0, 6) as [region, count]}
						{@const threat = getThreatLevel(count)}
						<div class="grid-card" style="--card-color: {threat.color}" on:click={() => drillDownRegion(region, count)}>
							<div class="card-header">
								<span class="threat-indicator {threat.level.toLowerCase()}">{threat.level}</span>
							</div>
							<div class="card-body">
								<div class="region-name">{region.toUpperCase()}</div>
								<div class="region-count">{count.toLocaleString()}</div>
								<div class="progress-bar">
									<div class="progress-fill" style="width: {(count/maxCount)*100}%; background: {threat.color}"></div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Right Panel: Visualizations -->
		<div class="viz-panel">
			<!-- Metrics Row -->
			<div class="metrics-row">
				<div class="metric-card">
					<div class="metric-value">{sortedRegions.length}</div>
					<div class="metric-label">REGIONS</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{(data.total_coverage || 0).toLocaleString()}</div>
					<div class="metric-label">ASSETS</div>
				</div>
			</div>

			<!-- World Map -->
			<div class="viz-card">
				<h4>GLOBAL HEATMAP</h4>
				<div class="world-map">
					<svg viewBox="0 0 300 100">
						<defs>
							<radialGradient id="heatGradient">
								<stop offset="0%" style="stop-color:#0a4f3c;stop-opacity:0.8" />
								<stop offset="100%" style="stop-color:#0a4f3c;stop-opacity:0" />
							</radialGradient>
						</defs>
						{#each sortedRegions.slice(0, 5) as [region, count], i}
							{@const x = 60 * (i + 0.5)}
							{@const y = 50}
							{@const r = Math.sqrt(count / maxCount) * 25}
							<circle cx={x} cy={y} r={r} fill="url(#heatGradient)" opacity="0.6"/>
							<text x={x} y={y + 35} text-anchor="middle" fill="#b8a678" font-size="7">
								{region.substring(0, 6).toUpperCase()}
							</text>
						{/each}
					</svg>
				</div>
			</div>

			<!-- Threat Matrix -->
			<div class="viz-card">
				<h4>THREAT MATRIX</h4>
				<div class="threat-chart">
					{#each Object.entries(threatDistribution) as [level, count]}
						{@const color = level === 'CRITICAL' ? '#ff0066' : 
							level === 'HIGH' ? '#ff9900' : 
							level === 'MEDIUM' ? '#ffcc00' : '#0a4f3c'}
						<div class="threat-row">
							<div class="threat-label">{level}</div>
							<div class="threat-bar-container">
								<div class="threat-bar" style="width: {(count/sortedRegions.length)*100}%; background: {color}"></div>
							</div>
							<div class="threat-count">{count}</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Top Regions -->
			<div class="viz-card">
				<h4>TOP REGIONS</h4>
				<div class="bar-chart">
					{#each sortedRegions.slice(0, 4) as [region, count]}
						{@const threat = getThreatLevel(count)}
						<div class="bar-item">
							<div class="bar-label">{region.toUpperCase()}</div>
							<div class="bar-container">
								<div class="bar-fill" style="width: {(count/maxCount)*100}%; background: {threat.color}"></div>
								<span class="bar-value">{count}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.region-dashboard {
		height: calc(100vh - 100px);
		display: flex;
		background: #000;
		color: #fff;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
	}

	.main-content {
		flex: 1;
		display: flex;
		gap: 0.5rem;
		padding: 0.5rem;
		overflow: hidden;
	}

	.table-panel {
		flex: 2;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #1e3a5f;
		border-radius: 4px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		min-width: 280px;
		max-width: 350px;
	}

	.panel-header {
		padding: 0.5rem;
		border-bottom: 1px solid #1e3a5f;
		background: rgba(0, 0, 0, 0.3);
	}

	.controls {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.search-input {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #1e3a5f;
		border-radius: 3px;
		padding: 0.25rem 0.5rem;
		color: #b8a678;
		font-size: 0.65rem;
	}

	.search-input:focus {
		outline: none;
		border-color: #0a4f3c;
		box-shadow: 0 0 5px rgba(10, 79, 60, 0.3);
	}

	.view-toggle {
		display: flex;
		gap: 0.2rem;
	}

	.toggle-btn {
		background: rgba(0, 0, 0, 0.7);
		border: 1px solid #1e3a5f;
		color: #b8a678;
		padding: 0.2rem 0.4rem;
		border-radius: 3px;
		cursor: pointer;
		font-size: 0.55rem;
		transition: all 0.2s ease;
	}

	.toggle-btn.active {
		background: linear-gradient(135deg, rgba(10, 79, 60, 0.2), rgba(30, 58, 95, 0.15));
		border-color: #0a4f3c;
		color: #fff;
	}

	.table-container {
		flex: 1;
		overflow: auto;
		padding: 0.3rem;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.65rem;
	}

	.data-table th {
		background: rgba(10, 79, 60, 0.1);
		color: #0a4f3c;
		padding: 0.3rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 1px solid #0a4f3c;
	}

	.data-table td {
		padding: 0.25rem 0.3rem;
		border-bottom: 1px solid rgba(30, 58, 95, 0.2);
		color: #b8a678;
	}

	.data-table tr:hover {
		background: rgba(10, 79, 60, 0.05);
	}

	.region-cell {
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}

	.indicator {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.center {
		text-align: center;
	}

	.coverage-cell {
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}

	.coverage-bar {
		flex: 1;
		height: 4px;
		background: rgba(30, 58, 95, 0.3);
		border-radius: 2px;
		overflow: hidden;
		min-width: 40px;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.5s ease;
	}

	.coverage-text {
		font-size: 0.55rem;
		min-width: 35px;
		text-align: right;
		color: #b8a678;
	}

	.threat-badge {
		padding: 0.1rem 0.3rem;
		border-radius: 2px;
		font-size: 0.5rem;
		font-weight: 600;
	}

	.threat-badge.critical {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.threat-badge.high {
		background: rgba(255, 153, 0, 0.2);
		color: #ff9900;
		border: 1px solid #ff9900;
	}

	.threat-badge.medium {
		background: rgba(255, 204, 0, 0.2);
		color: #ffcc00;
		border: 1px solid #ffcc00;
	}

	.threat-badge.low {
		background: rgba(10, 79, 60, 0.2);
		color: #0a4f3c;
		border: 1px solid #0a4f3c;
	}

	.drill-btn {
		background: rgba(10, 79, 60, 0.2);
		border: 1px solid #0a4f3c;
		color: #0a4f3c;
		padding: 0.15rem 0.3rem;
		border-radius: 2px;
		cursor: pointer;
		font-size: 0.6rem;
		transition: all 0.2s ease;
		font-weight: 700;
	}

	.drill-btn:hover {
		background: rgba(10, 79, 60, 0.3);
		box-shadow: 0 0 5px rgba(10, 79, 60, 0.5);
	}

	.grid-container {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.5rem;
		padding: 0.5rem;
	}

	.grid-card {
		background: rgba(0, 0, 0, 0.7);
		border: 1px solid var(--card-color);
		border-radius: 4px;
		padding: 0.5rem;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.grid-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
	}

	.card-header {
		display: flex;
		justify-content: flex-end;
		margin-bottom: 0.3rem;
	}

	.threat-indicator {
		font-size: 0.45rem;
		padding: 0.1rem 0.2rem;
		border-radius: 2px;
		font-weight: 600;
	}

	.card-body {
		text-align: center;
	}

	.region-name {
		font-size: 0.65rem;
		color: #b8a678;
		margin-bottom: 0.2rem;
		font-weight: 600;
	}

	.region-count {
		font-size: 0.9rem;
		font-weight: 700;
		color: var(--card-color);
		margin-bottom: 0.2rem;
	}

	.progress-bar {
		width: 100%;
		height: 3px;
		background: rgba(30, 58, 95, 0.3);
		border-radius: 2px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		transition: width 0.5s ease;
	}

	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 0.5rem;
		padding: 0.3rem;
		border-top: 1px solid #1e3a5f;
		background: rgba(0, 0, 0, 0.3);
	}

	.pagination button {
		background: rgba(10, 79, 60, 0.1);
		border: 1px solid #0a4f3c;
		color: #0a4f3c;
		padding: 0.2rem 0.4rem;
		border-radius: 3px;
		cursor: pointer;
		font-size: 0.55rem;
		font-weight: 600;
	}

	.pagination button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.pagination span {
		font-size: 0.6rem;
		color: #b8a678;
	}

	.metrics-row {
		display: flex;
		gap: 0.4rem;
	}

	.metric-card {
		flex: 1;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid #1e3a5f;
		border-radius: 4px;
		padding: 0.4rem;
		text-align: center;
	}

	.metric-value {
		font-size: 1rem;
		font-weight: 700;
		color: #0a4f3c;
		text-shadow: 0 0 8px rgba(10, 79, 60, 0.3);
	}

	.metric-label {
		font-size: 0.5rem;
		color: #b8a678;
		margin-top: 0.1rem;
		letter-spacing: 0.05em;
	}

	.viz-card {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid #1e3a5f;
		border-radius: 4px;
		padding: 0.5rem;
	}

	.viz-card h4 {
		margin: 0 0 0.4rem 0;
		font-size: 0.6rem;
		color: #0a4f3c;
		letter-spacing: 0.05em;
		text-align: center;
		font-weight: 600;
	}

	.world-map {
		width: 100%;
		display: flex;
		justify-content: center;
	}

	.threat-chart {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.threat-row {
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}

	.threat-label {
		font-size: 0.5rem;
		color: #b8a678;
		min-width: 45px;
		font-weight: 600;
	}

	.threat-bar-container {
		flex: 1;
		height: 6px;
		background: rgba(30, 58, 95, 0.3);
		border-radius: 3px;
		overflow: hidden;
	}

	.threat-bar {
		height: 100%;
		transition: width 0.5s ease;
	}

	.threat-count {
		font-size: 0.5rem;
		color: #b8a678;
		min-width: 15px;
		text-align: right;
	}

	.bar-chart {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.bar-item {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
	}

	.bar-label {
		font-size: 0.5rem;
		color: #b8a678;
		font-weight: 600;
	}

	.bar-container {
		position: relative;
		height: 10px;
		background: rgba(30, 58, 95, 0.3);
		border-radius: 2px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
	}

	.bar-value {
		position: absolute;
		right: 0.2rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.45rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 0 0 3px #000;
	}

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
	}

	.spinner {
		width: 30px;
		height: 30px;
		border: 2px solid #1e3a5f;
		border-top-color: #0a4f3c;
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
		padding: 0.5rem;
		border-bottom: 1px solid #0a4f3c;
		background: rgba(10, 79, 60, 0.05);
	}

	.drill-header h4 {
		margin: 0;
		color: #0a4f3c;
		font-size: 0.7rem;
	}

	.close-btn {
		background: rgba(255, 0, 102, 0.1);
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 20px;
		height: 20px;
		border-radius: 3px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.6rem;
	}

	.host-cell {
		font-family: monospace;
		color: #0a4f3c;
		font-size: 0.6rem;
	}

	.status-badge {
		padding: 0.1rem 0.2rem;
		border-radius: 2px;
		font-size: 0.5rem;
		font-weight: 600;
	}

	.status-badge.active {
		background: rgba(10, 79, 60, 0.2);
		color: #0a4f3c;
		border: 1px solid #0a4f3c;
	}

	.status-badge.inactive {
		background: rgba(255, 0, 102, 0.1);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}
</style>