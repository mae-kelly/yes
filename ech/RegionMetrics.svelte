<!-- RegionMetrics.svelte - Production Ready -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';
	let sortColumn = 'count';
	let sortDirection = 'desc';
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/region_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Failed to load region metrics:', err);
			loading = false;
		}
	});
	
	$: regions = data.global_surveillance ? 
		Object.entries(data.global_surveillance)
			.filter(([region]) => region.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => {
				if (sortColumn === 'name') {
					return sortDirection === 'asc' ? 
						a[0].localeCompare(b[0]) : 
						b[0].localeCompare(a[0]);
				}
				return sortDirection === 'asc' ? a[1] - b[1] : b[1] - a[1];
			}) : [];
	
	$: totalHosts = regions.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = regions.length > 0 ? Math.max(...regions.map(([,c]) => c)) : 1;
	$: avgHosts = regions.length > 0 ? Math.round(totalHosts / regions.length) : 0;
	
	// Chart data
	$: topFive = regions.slice(0, 5);
	$: bottomFive = regions.slice(-5);
	
	function handleSort(column) {
		if (sortColumn === column) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = column;
			sortDirection = 'desc';
		}
	}
	
	async function selectRegion(region, count) {
		selectedRegion = { region, count };
		loading = true;
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(region)}`);
			let result = await response.json();
			regionDetails = result.hosts || [];
		} catch (err) {
			console.error('Failed to load region details:', err);
		}
		loading = false;
	}
	
	function closeDetails() {
		selectedRegion = null;
		regionDetails = [];
	}
	
	function getRegionColor(percentage) {
		if (percentage >= 20) return '#BD93F9';
		if (percentage >= 15) return '#8BE9FD';
		if (percentage >= 10) return '#50FA7B';
		if (percentage >= 5) return '#FFB86C';
		return '#666';
	}
</script>

<div class="container">
	<header class="header">
		<div class="header-content">
			<h1 class="title">REGIONAL DISTRIBUTION</h1>
			<div class="header-controls">
				<input 
					type="text" 
					bind:value={searchTerm}
					placeholder="Search regions..."
					class="search-input"
				/>
				<div class="metrics">
					<div class="metric">
						<span class="metric-value">{regions.length}</span>
						<span class="metric-label">Regions</span>
					</div>
					<div class="metric">
						<span class="metric-value">{totalHosts.toLocaleString()}</span>
						<span class="metric-label">Total Hosts</span>
					</div>
					<div class="metric">
						<span class="metric-value">{avgHosts.toLocaleString()}</span>
						<span class="metric-label">Avg/Region</span>
					</div>
				</div>
			</div>
		</div>
	</header>

	<div class="main-content">
		<div class="table-section">
			{#if selectedRegion}
				<div class="detail-view">
					<div class="detail-header">
						<h2>{selectedRegion.region}</h2>
						<button class="close-btn" on:click={closeDetails}>×</button>
					</div>
					<table class="data-table">
						<thead>
							<tr>
								<th>Hostname</th>
								<th>Country</th>
								<th>Infrastructure</th>
								<th>Business Unit</th>
								<th>CMDB</th>
								<th>Tanium</th>
							</tr>
						</thead>
						<tbody>
							{#each regionDetails as host}
								<tr>
									<td class="mono">{host.host}</td>
									<td>{host.country || '-'}</td>
									<td>{host.infrastructure_type || '-'}</td>
									<td>{host.business_unit || '-'}</td>
									<td>
										<span class="status {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : ''}">
											{host.present_in_cmdb?.toLowerCase().includes('yes') ? '●' : '○'}
										</span>
									</td>
									<td>
										<span class="status {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : ''}">
											{host.tanium_coverage?.toLowerCase().includes('tanium') ? '●' : '○'}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<table class="data-table">
					<thead>
						<tr>
							<th class="sortable" on:click={() => handleSort('name')}>
								Region
								{#if sortColumn === 'name'}
									<span class="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
								{/if}
							</th>
							<th class="sortable" on:click={() => handleSort('count')}>
								Host Count
								{#if sortColumn === 'count'}
									<span class="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
								{/if}
							</th>
							<th>Global Share</th>
							<th>Density</th>
						</tr>
					</thead>
					<tbody>
						{#each regions as [region, count], i}
							{#if region && count}
								<tr on:click={() => selectRegion(region, count)}>
									<td class="region-name">{region}</td>
									<td class="mono">{count.toLocaleString()}</td>
									<td>
										<div class="share">
											<div class="share-bar">
												<div class="share-fill" 
													 style="width: {(count/totalHosts)*100}%; 
															background: {getRegionColor((count/totalHosts)*100)}">
												</div>
											</div>
											<span class="share-text">{((count/totalHosts)*100).toFixed(1)}%</span>
										</div>
									</td>
									<td>
										<div class="density-indicator">
											<span class="density-dot" style="background: {getRegionColor((count/totalHosts)*100)}"></span>
											<span class="density-label">
												{(count/totalHosts)*100 >= 20 ? 'CRITICAL' : 
												 (count/totalHosts)*100 >= 15 ? 'HIGH' : 
												 (count/totalHosts)*100 >= 10 ? 'MODERATE' : 
												 (count/totalHosts)*100 >= 5 ? 'LOW' : 'MINIMAL'}
											</span>
										</div>
									</td>
								</tr>
							{/if}
						{/each}
					</tbody>
				</table>
			{/if}
		</div>

		<div class="charts-section">
			<!-- Chart 1: Top Regions -->
			<div class="chart-container">
				<h3 class="chart-title">TOP REGIONS</h3>
				<div class="chart-content">
					{#each topFive as [region, count]}
						<div class="region-item">
							<div class="region-info">
								<span class="region-label">{region}</span>
								<span class="region-count">{count.toLocaleString()}</span>
							</div>
							<div class="region-bar">
								<div class="region-fill" 
									 style="width: {(count/maxHosts)*100}%; 
											background: {getRegionColor((count/totalHosts)*100)}">
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Chart 2: Distribution Map -->
			<div class="chart-container">
				<h3 class="chart-title">GEOGRAPHIC SPREAD</h3>
				<div class="chart-content">
					<div class="map-grid">
						{#each regions.slice(0, 12) as [region, count]}
							<div class="map-cell" 
								 style="background: {getRegionColor((count/totalHosts)*100)}; 
										opacity: {0.2 + (count/maxHosts) * 0.8}">
								<span class="map-value">{((count/totalHosts)*100).toFixed(0)}%</span>
							</div>
						{/each}
					</div>
				</div>
			</div>

			<!-- Chart 3: Coverage Metrics -->
			<div class="chart-container">
				<h3 class="chart-title">COVERAGE METRICS</h3>
				<div class="chart-content">
					<div class="metric-list">
						<div class="metric-item">
							<span class="metric-name">Top Region</span>
							<span class="metric-val">{topFive[0] ? topFive[0][0] : 'N/A'}</span>
						</div>
						<div class="metric-item">
							<span class="metric-name">Top 3 Coverage</span>
							<span class="metric-val">
								{((topFive.slice(0, 3).reduce((sum, [_, c]) => sum + c, 0) / totalHosts * 100)).toFixed(1)}%
							</span>
						</div>
						<div class="metric-item">
							<span class="metric-name">Concentration</span>
							<span class="metric-val">
								{topFive[0] ? ((topFive[0][1] / totalHosts * 100)).toFixed(1) + '%' : '0%'}
							</span>
						</div>
						<div class="metric-item">
							<span class="metric-name">Active Regions</span>
							<span class="metric-val">{regions.filter(([_, c]) => c > 1000).length}</span>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.container {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.header {
		border-bottom: 1px solid #1a1a1a;
		padding: 1.5rem 2rem;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.title {
		font-size: 1.25rem;
		font-weight: 200;
		letter-spacing: 0.2em;
		color: #FFFFFF;
		margin: 0;
	}

	.header-controls {
		display: flex;
		align-items: center;
		gap: 2rem;
	}

	.search-input {
		background: #0a0a0a;
		border: 1px solid #1a1a1a;
		border-radius: 4px;
		padding: 0.5rem 1rem;
		color: #FFFFFF;
		font-size: 0.875rem;
		width: 250px;
		transition: border-color 0.2s;
	}

	.search-input:focus {
		outline: none;
		border-color: #8BE9FD;
	}

	.metrics {
		display: flex;
		gap: 2rem;
	}

	.metric {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.metric-value {
		font-size: 1.25rem;
		font-weight: 300;
		color: #8BE9FD;
	}

	.metric-label {
		font-size: 0.75rem;
		color: #666;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		margin-top: 0.25rem;
	}

	.main-content {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 320px;
		min-height: 0;
	}

	.table-section {
		border-right: 1px solid #1a1a1a;
		overflow-y: auto;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
	}

	.data-table thead {
		position: sticky;
		top: 0;
		background: #000000;
		border-bottom: 1px solid #1a1a1a;
		z-index: 10;
	}

	.data-table th {
		padding: 1rem;
		text-align: left;
		font-size: 0.75rem;
		font-weight: 400;
		color: #666;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.data-table th.sortable {
		cursor: pointer;
		transition: color 0.2s;
	}

	.data-table th.sortable:hover {
		color: #8BE9FD;
	}

	.sort-indicator {
		margin-left: 0.5rem;
		color: #8BE9FD;
	}

	.data-table tbody tr {
		border-bottom: 1px solid #0a0a0a;
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.data-table tbody tr:hover {
		background: #0a0a0a;
	}

	.data-table td {
		padding: 1rem;
		font-size: 0.875rem;
		color: #FFFFFF;
	}

	.region-name {
		font-weight: 300;
	}

	.mono {
		font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
		color: #8BE9FD;
	}

	.share {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.share-bar {
		width: 100px;
		height: 4px;
		background: #1a1a1a;
		border-radius: 2px;
		overflow: hidden;
	}

	.share-fill {
		height: 100%;
		transition: width 0.3s;
	}

	.share-text {
		font-size: 0.75rem;
		color: #666;
		min-width: 45px;
		text-align: right;
	}

	.density-indicator {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.density-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.density-label {
		font-size: 0.75rem;
		color: #666;
		letter-spacing: 0.05em;
	}

	.status {
		font-size: 0.875rem;
	}

	.status.active {
		color: #50FA7B;
	}

	.charts-section {
		background: #0a0a0a;
		display: flex;
		flex-direction: column;
	}

	.chart-container {
		flex: 1;
		border-bottom: 1px solid #1a1a1a;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
	}

	.chart-container:last-child {
		border-bottom: none;
	}

	.chart-title {
		font-size: 0.75rem;
		font-weight: 400;
		color: #666;
		letter-spacing: 0.1em;
		margin: 0 0 1rem 0;
	}

	.chart-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}

	.region-item {
		margin-bottom: 0.75rem;
	}

	.region-info {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.25rem;
	}

	.region-label {
		font-size: 0.75rem;
		color: #FFFFFF;
	}

	.region-count {
		font-size: 0.75rem;
		color: #8BE9FD;
	}

	.region-bar {
		height: 16px;
		background: #1a1a1a;
		border-radius: 2px;
		overflow: hidden;
	}

	.region-fill {
		height: 100%;
		transition: width 0.3s;
	}

	.map-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		grid-template-rows: repeat(3, 1fr);
		gap: 4px;
		height: 120px;
	}

	.map-cell {
		border-radius: 2px;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: opacity 0.3s;
	}

	.map-value {
		font-size: 0.625rem;
		color: #FFFFFF;
		font-weight: 500;
	}

	.metric-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.metric-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem;
		background: #000000;
		border: 1px solid #1a1a1a;
		border-radius: 4px;
	}

	.metric-name {
		font-size: 0.875rem;
		color: #666;
	}

	.metric-val {
		font-size: 1rem;
		font-weight: 300;
		color: #8BE9FD;
	}

	.detail-view {
		padding: 1.5rem;
	}

	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.detail-header h2 {
		font-size: 1.125rem;
		font-weight: 300;
		color: #8BE9FD;
		margin: 0;
	}

	.close-btn {
		background: transparent;
		border: 1px solid #1a1a1a;
		color: #666;
		width: 32px;
		height: 32px;
		border-radius: 4px;
		font-size: 1.25rem;
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-btn:hover {
		border-color: #8BE9FD;
		color: #8BE9FD;
	}

	/* Scrollbar */
	::-webkit-scrollbar {
		width: 8px;
	}

	::-webkit-scrollbar-track {
		background: #0a0a0a;
	}

	::-webkit-scrollbar-thumb {
		background: #1a1a1a;
		border-radius: 4px;
	}

	::-webkit-scrollbar-thumb:hover {
		background: #2a2a2a;
	}
</style>