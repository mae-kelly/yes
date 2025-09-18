<!-- SourceTables.svelte - Production Ready -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let sourceDetails = [];
	let searchTerm = '';
	let sortColumn = 'count';
	let sortDirection = 'desc';
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Failed to load source tables:', err);
			loading = false;
		}
	});
	
	$: sources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => {
				if (sortColumn === 'name') {
					return sortDirection === 'asc' ? 
						a[0].localeCompare(b[0]) : 
						b[0].localeCompare(a[0]);
				}
				return sortDirection === 'asc' ? a[1] - b[1] : b[1] - a[1];
			}) : [];
	
	$: totalHosts = sources.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = sources.length > 0 ? Math.max(...sources.map(([,c]) => c)) : 1;
	$: avgHosts = sources.length > 0 ? Math.round(totalHosts / sources.length) : 0;
	
	// Chart data
	$: topFive = sources.slice(0, 5);
	$: distribution = sources.reduce((acc, [_, count]) => {
		if (count > 10000) acc.high++;
		else if (count > 5000) acc.medium++;
		else if (count > 1000) acc.low++;
		else acc.minimal++;
		return acc;
	}, { high: 0, medium: 0, low: 0, minimal: 0 });
	
	function handleSort(column) {
		if (sortColumn === column) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = column;
			sortDirection = 'desc';
		}
	}
	
	async function selectSource(source, count) {
		selectedSource = { source, count };
		loading = true;
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			sourceDetails = result.hosts || [];
		} catch (err) {
			console.error('Failed to load source details:', err);
		}
		loading = false;
	}
	
	function closeDetails() {
		selectedSource = null;
		sourceDetails = [];
	}
</script>

<div class="container">
	<header class="header">
		<div class="header-content">
			<h1 class="title">SOURCE TABLES</h1>
			<div class="header-controls">
				<input 
					type="text" 
					bind:value={searchTerm}
					placeholder="Search tables..."
					class="search-input"
				/>
				<div class="metrics">
					<div class="metric">
						<span class="metric-value">{sources.length}</span>
						<span class="metric-label">Tables</span>
					</div>
					<div class="metric">
						<span class="metric-value">{totalHosts.toLocaleString()}</span>
						<span class="metric-label">Total Hosts</span>
					</div>
					<div class="metric">
						<span class="metric-value">{avgHosts.toLocaleString()}</span>
						<span class="metric-label">Avg/Table</span>
					</div>
				</div>
			</div>
		</div>
	</header>

	<div class="main-content">
		<div class="table-section">
			{#if selectedSource}
				<div class="detail-view">
					<div class="detail-header">
						<h2>{selectedSource.source}</h2>
						<button class="close-btn" on:click={closeDetails}>×</button>
					</div>
					<table class="data-table">
						<thead>
							<tr>
								<th>Hostname</th>
								<th>Region</th>
								<th>Country</th>
								<th>Infrastructure</th>
								<th>CMDB</th>
								<th>Tanium</th>
							</tr>
						</thead>
						<tbody>
							{#each sourceDetails as host}
								<tr>
									<td class="mono">{host.host}</td>
									<td>{host.region || '-'}</td>
									<td>{host.country || '-'}</td>
									<td>{host.infrastructure_type || '-'}</td>
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
								Table Name
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
							<th>Percentage</th>
							<th>Status</th>
						</tr>
					</thead>
					<tbody>
						{#each sources as [source, count], i}
							<tr on:click={() => selectSource(source, count)}>
								<td class="source-name">{source}</td>
								<td class="mono">{count.toLocaleString()}</td>
								<td>
									<div class="percentage">
										<div class="percentage-bar">
											<div class="percentage-fill" style="width: {(count/maxHosts)*100}%"></div>
										</div>
										<span class="percentage-text">{((count/totalHosts)*100).toFixed(1)}%</span>
									</div>
								</td>
								<td>
									<span class="status-badge {count > 10000 ? 'critical' : count > 5000 ? 'high' : count > 1000 ? 'medium' : 'low'}">
										{count > 10000 ? 'CRITICAL' : count > 5000 ? 'HIGH' : count > 1000 ? 'MEDIUM' : 'LOW'}
									</span>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			{/if}
		</div>

		<div class="charts-section">
			<!-- Chart 1: Top 5 Sources -->
			<div class="chart-container">
				<h3 class="chart-title">TOP SOURCES</h3>
				<div class="chart-content">
					{#each topFive as [source, count], i}
						<div class="chart-bar-item">
							<span class="bar-label">{source.substring(0, 15)}</span>
							<div class="bar-track">
								<div class="bar-fill" style="width: {(count/maxHosts)*100}%"></div>
							</div>
							<span class="bar-value">{count.toLocaleString()}</span>
						</div>
					{/each}
				</div>
			</div>

			<!-- Chart 2: Distribution -->
			<div class="chart-container">
				<h3 class="chart-title">DISTRIBUTION</h3>
				<div class="chart-content">
					<div class="distribution-chart">
						<div class="dist-item">
							<span class="dist-label">Critical (>10k)</span>
							<span class="dist-value">{distribution.high}</span>
						</div>
						<div class="dist-item">
							<span class="dist-label">High (5k-10k)</span>
							<span class="dist-value">{distribution.medium}</span>
						</div>
						<div class="dist-item">
							<span class="dist-label">Medium (1k-5k)</span>
							<span class="dist-value">{distribution.low}</span>
						</div>
						<div class="dist-item">
							<span class="dist-label">Low (<1k)</span>
							<span class="dist-value">{distribution.minimal}</span>
						</div>
					</div>
				</div>
			</div>

			<!-- Chart 3: Coverage -->
			<div class="chart-container">
				<h3 class="chart-title">COVERAGE ANALYSIS</h3>
				<div class="chart-content">
					<div class="coverage-stats">
						<div class="coverage-item">
							<div class="coverage-circle">
								<svg viewBox="0 0 36 36">
									<path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
										  fill="none"
										  stroke="#1a1a1a"
										  stroke-width="2"/>
									<path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
										  fill="none"
										  stroke="#8BE9FD"
										  stroke-width="2"
										  stroke-dasharray="{(topFive.reduce((sum, [_, c]) => sum + c, 0) / totalHosts * 100)}, 100"/>
									<text x="18" y="20" text-anchor="middle" class="coverage-text">
										{((topFive.reduce((sum, [_, c]) => sum + c, 0) / totalHosts * 100)).toFixed(0)}%
									</text>
								</svg>
							</div>
							<span class="coverage-label">Top 5 Coverage</span>
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

	.source-name {
		font-weight: 300;
	}

	.mono {
		font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
		color: #8BE9FD;
	}

	.percentage {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.percentage-bar {
		width: 100px;
		height: 4px;
		background: #1a1a1a;
		border-radius: 2px;
		overflow: hidden;
	}

	.percentage-fill {
		height: 100%;
		background: linear-gradient(90deg, #8BE9FD, #BD93F9);
		transition: width 0.3s;
	}

	.percentage-text {
		font-size: 0.75rem;
		color: #666;
		min-width: 45px;
		text-align: right;
	}

	.status-badge {
		display: inline-block;
		padding: 0.25rem 0.75rem;
		border-radius: 4px;
		font-size: 0.75rem;
		font-weight: 500;
		letter-spacing: 0.05em;
	}

	.status-badge.critical {
		background: rgba(189, 147, 249, 0.1);
		color: #BD93F9;
		border: 1px solid rgba(189, 147, 249, 0.2);
	}

	.status-badge.high {
		background: rgba(139, 233, 253, 0.1);
		color: #8BE9FD;
		border: 1px solid rgba(139, 233, 253, 0.2);
	}

	.status-badge.medium {
		background: rgba(80, 250, 123, 0.1);
		color: #50FA7B;
		border: 1px solid rgba(80, 250, 123, 0.2);
	}

	.status-badge.low {
		background: rgba(255, 184, 108, 0.1);
		color: #FFB86C;
		border: 1px solid rgba(255, 184, 108, 0.2);
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

	.chart-bar-item {
		display: grid;
		grid-template-columns: 80px 1fr 60px;
		gap: 0.75rem;
		align-items: center;
		margin-bottom: 0.75rem;
	}

	.bar-label {
		font-size: 0.75rem;
		color: #666;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.bar-track {
		height: 20px;
		background: #1a1a1a;
		border-radius: 2px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		background: linear-gradient(90deg, #8BE9FD, #BD93F9);
		transition: width 0.3s;
	}

	.bar-value {
		font-size: 0.75rem;
		color: #8BE9FD;
		text-align: right;
	}

	.distribution-chart {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.dist-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem;
		background: #000000;
		border: 1px solid #1a1a1a;
		border-radius: 4px;
	}

	.dist-label {
		font-size: 0.875rem;
		color: #FFFFFF;
	}

	.dist-value {
		font-size: 1.25rem;
		font-weight: 300;
		color: #8BE9FD;
	}

	.coverage-stats {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.coverage-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
	}

	.coverage-circle {
		width: 120px;
		height: 120px;
	}

	.coverage-circle svg {
		transform: rotate(-90deg);
	}

	.coverage-text {
		font-size: 1.5rem;
		font-weight: 300;
		fill: #8BE9FD;
		transform: rotate(90deg);
		transform-origin: center;
	}

	.coverage-label {
		font-size: 0.875rem;
		color: #666;
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