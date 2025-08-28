<!-- SourceTables.svelte - Military Intelligence Tables -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 8;
	let viewMode = 'table';

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			let result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			console.error('Source tables error:', err);
			loading = false;
		}
	});

	$: filteredSources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: paginatedSources = filteredSources.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(filteredSources.length / itemsPerPage);
	$: maxFreq = filteredSources.length > 0 ? Math.max(...filteredSources.map(([,f]) => f)) : 1;

	function getThreatLevel(frequency) {
		if (!data.total_mentions) return { level: 'SECURE', color: '#0a4f3c' };
		let percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRITICAL', color: '#ff0066' };
		if (percentage >= 10) return { level: 'HIGH', color: '#ff9900' };
		if (percentage >= 5) return { level: 'MEDIUM', color: '#ffcc00' };
		return { level: 'SECURE', color: '#0a4f3c' };
	}

	function getPercentage(frequency) {
		if (!data.total_mentions) return 0;
		return ((frequency / data.total_mentions) * 100).toFixed(2);
	}

	async function drillDownSource(source, frequency) {
		selectedSource = { source, frequency };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			hostDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Host search error:', err);
			hostDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedSource = null;
		hostDetails = [];
	}

	$: threatDistribution = filteredSources.reduce((acc, [_, frequency]) => {
		let level = getThreatLevel(frequency).level;
		acc[level] = (acc[level] || 0) + 1;
		return acc;
	}, {});
</script>

<div class="military-dashboard">
	<!-- Main Content Area -->
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search sources..."
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
			
			{#if loading && !selectedSource}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>SCANNING NETWORK...</p>
				</div>
			{:else if selectedSource}
				<!-- Drill-down View -->
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedSource.source.toUpperCase()}</h4>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>INFRA</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each hostDetails.slice(0, 6) as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.region || 'Unknown'}</td>
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
				<!-- Main Table -->
				<div class="table-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>SOURCE</th>
								<th>FREQ</th>
								<th>COVERAGE</th>
								<th>THREAT</th>
								<th>ACTION</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedSources as [source, frequency]}
								{@const threat = getThreatLevel(frequency)}
								<tr>
									<td class="source-cell">
										<span class="indicator" style="background: {threat.color}"></span>
										<span>{source.substring(0, 20).toUpperCase()}</span>
									</td>
									<td class="center">{frequency.toLocaleString()}</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {getPercentage(frequency)}%; background: {threat.color}"></div>
											</div>
											<span class="coverage-text">{getPercentage(frequency)}%</span>
										</div>
									</td>
									<td class="center">
										<span class="threat-badge {threat.level.toLowerCase()}">{threat.level}</span>
									</td>
									<td class="center">
										<button class="drill-btn" on:click={() => drillDownSource(source, frequency)}>→</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				
				<!-- Pagination -->
				<div class="pagination">
					<button on:click={() => currentPage = Math.max(1, currentPage - 1)} disabled={currentPage === 1}>←</button>
					<span>{currentPage}/{totalPages}</span>
					<button on:click={() => currentPage = Math.min(totalPages, currentPage + 1)} disabled={currentPage === totalPages}>→</button>
				</div>
			{:else}
				<!-- Grid View -->
				<div class="grid-container">
					{#each paginatedSources.slice(0, 6) as [source, frequency]}
						{@const threat = getThreatLevel(frequency)}
						<div class="grid-card" style="--card-color: {threat.color}" on:click={() => drillDownSource(source, frequency)}>
							<div class="card-header">
								<span class="threat-indicator {threat.level.toLowerCase()}">{threat.level}</span>
							</div>
							<div class="card-body">
								<div class="source-name">{source.substring(0, 15).toUpperCase()}</div>
								<div class="source-count">{frequency.toLocaleString()}</div>
								<div class="progress-bar">
									<div class="progress-fill" style="width: {(frequency/maxFreq)*100}%; background: {threat.color}"></div>
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
					<div class="metric-value">{filteredSources.length}</div>
					<div class="metric-label">SOURCES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{(data.total_mentions || 0).toLocaleString()}</div>
					<div class="metric-label">MENTIONS</div>
				</div>
			</div>

			<!-- Threat Distribution -->
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
								<div class="threat-bar" style="width: {(count/filteredSources.length)*100}%; background: {color}"></div>
							</div>
							<div class="threat-count">{count}</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Top Sources -->
			<div class="viz-card">
				<h4>TOP 5 SOURCES</h4>
				<div class="bar-chart">
					{#each filteredSources.slice(0, 5) as [source, frequency]}
						{@const threat = getThreatLevel(frequency)}
						<div class="bar-item">
							<div class="bar-label">{source.substring(0, 12).toUpperCase()}</div>
							<div class="bar-container">
								<div class="bar-fill" style="width: {(frequency/maxFreq)*100}%; background: {threat.color}"></div>
								<span class="bar-value">{frequency}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.military-dashboard {
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

	.source-cell {
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
		min-width: 30px;
		text-align: right;
		color: #b8a678;
	}

	.threat-badge {
		padding: 0.1rem 0.3rem;
		border-radius: 2px;
		font-size: 0.5rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.02em;
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

	.threat-badge.secure {
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

	.source-name {
		font-size: 0.6rem;
		color: #b8a678;
		margin-bottom: 0.2rem;
		font-weight: 600;
	}

	.source-count {
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
		gap: 0.3rem;
	}

	.bar-item {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
	}

	.bar-label {
		font-size: 0.5rem;
		color: #b8a678;
		font-weight: 600;
	}

	.bar-container {
		position: relative;
		height: 12px;
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
		font-size: 0.5rem;
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
		letter-spacing: 0.05em;
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
		font-weight: 700;
	}

	.host-cell {
		font-family: 'Courier New', monospace;
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

	@media (max-width: 1200px) {
		.viz-panel {
			min-width: 240px;
		}
		
		.grid-container {
			grid-template-columns: 1fr;
		}
	}
</style>