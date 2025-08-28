<!-- SourceTables.svelte - Enhanced Source Analysis -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';

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
	
	$: maxFreq = filteredSources.length > 0 ? Math.max(...filteredSources.map(([,f]) => f)) : 1;

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
</script>

<div class="dashboard-container">
	<!-- Main Content Area -->
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<h3 class="panel-title">
					<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<rect x="3" y="3" width="7" height="7" />
						<rect x="14" y="3" width="7" height="7" />
						<rect x="3" y="14" width="7" height="7" />
						<rect x="14" y="14" width="7" height="7" />
					</svg>
					Source Table Frequency Analysis
				</h3>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search sources..."
						class="search-input"
					/>
				</div>
			</div>
			
			{#if loading && !selectedSource}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>ANALYZING SOURCE TABLES...</p>
				</div>
			{:else if selectedSource}
				<!-- Drill-down View -->
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedSource.source.toUpperCase()}</h4>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="drill-table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>INFRASTRUCTURE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each hostDetails as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.region || 'Unknown'}</td>
										<td>{host.country || 'Unknown'}</td>
										<td>{host.infrastructure_type || 'Unknown'}</td>
										<td>
											<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'YES' : 'NO'}
											</span>
										</td>
										<td>
											<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? 'YES' : 'NO'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<!-- Main Table -->
				<div class="table-scroll-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>SOURCE TABLE</th>
								<th>FREQUENCY</th>
								<th>COVERAGE %</th>
								<th>VISIBILITY BAR</th>
							</tr>
						</thead>
						<tbody>
							{#each filteredSources as [source, frequency]}
								<tr on:click={() => drillDownSource(source, frequency)}>
									<td class="source-cell">
										<span class="source-name">{source.toUpperCase()}</span>
									</td>
									<td class="center">{frequency.toLocaleString()}</td>
									<td class="center">{getPercentage(frequency)}%</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {(frequency/maxFreq)*100}%"></div>
											</div>
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>

		<!-- Right Panel: Visualizations -->
		<div class="viz-panel">
			<!-- Metrics Row -->
			<div class="metrics-row">
				<div class="metric-card">
					<div class="metric-value">{filteredSources.length}</div>
					<div class="metric-label">UNIQUE SOURCES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{(data.total_mentions || 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL MENTIONS</div>
				</div>
			</div>

			<!-- Source Distribution Chart -->
			<div class="viz-card">
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
					</svg>
					TOP SOURCE TABLES
				</h4>
				<div class="bar-chart">
					{#each filteredSources.slice(0, 8) as [source, frequency]}
						<div class="bar-item">
							<div class="bar-label">{source.substring(0, 20).toUpperCase()}</div>
							<div class="bar-container">
								<div class="bar-fill" style="width: {(frequency/maxFreq)*100}%"></div>
								<span class="bar-value">{frequency}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Frequency Distribution -->
			<div class="viz-card">
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
					</svg>
					FREQUENCY DISTRIBUTION
				</h4>
				<div class="distribution-chart">
					{#each filteredSources.slice(0, 5) as [source, frequency], i}
						<div class="dist-item">
							<div class="dist-rank">#{i + 1}</div>
							<div class="dist-details">
								<div class="dist-name">{source.substring(0, 15).toUpperCase()}</div>
								<div class="dist-bar">
									<div class="dist-fill" style="width: {(frequency/maxFreq)*100}%"></div>
								</div>
								<div class="dist-percent">{getPercentage(frequency)}%</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.dashboard-container {
		height: calc(100vh - 80px);
		display: flex;
		background: #0a0a0a;
		color: #e0e0e0;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
		padding: 1rem;
	}

	.main-content {
		flex: 1;
		display: flex;
		gap: 1rem;
		overflow: hidden;
	}

	.table-panel {
		flex: 1.5;
		background: #0f0f0f;
		border: 1px solid #1a1a1a;
		border-radius: 8px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.panel-header {
		padding: 1rem 1.5rem;
		border-bottom: 1px solid #1a1a1a;
		background: #0f0f0f;
		flex-shrink: 0;
	}

	.panel-title {
		margin: 0 0 1rem 0;
		color: #0a4f3c;
		font-size: 1rem;
		font-weight: 500;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.icon {
		width: 20px;
		height: 20px;
		color: #0a4f3c;
	}

	.icon-small {
		width: 16px;
		height: 16px;
		color: #0a4f3c;
		display: inline-block;
		vertical-align: middle;
		margin-right: 0.3rem;
	}

	.controls {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.search-input {
		flex: 1;
		background: #0a0a0a;
		border: 1px solid #1a1a1a;
		border-radius: 4px;
		padding: 0.5rem 0.75rem;
		color: #e0e0e0;
		font-size: 0.85rem;
		font-family: inherit;
	}

	.search-input:focus {
		outline: none;
		border-color: #0a4f3c;
	}

	.table-scroll-container {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
	}

	.drill-table-container {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.85rem;
	}

	.data-table th {
		background: #0f0f0f;
		color: #0a4f3c;
		padding: 0.75rem;
		text-align: left;
		font-weight: 500;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 2px solid #0a4f3c;
	}

	.data-table td {
		padding: 0.75rem;
		border-bottom: 1px solid #1a1a1a;
		color: #b8a678;
	}

	.data-table tbody tr {
		cursor: pointer;
		transition: background 0.2s ease;
	}

	.data-table tbody tr:hover {
		background: rgba(10, 79, 60, 0.05);
	}

	.source-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.source-name {
		font-weight: 500;
		color: #e0e0e0;
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
		height: 6px;
		background: #1a1a1a;
		border-radius: 3px;
		overflow: hidden;
	}

	.coverage-fill {
		height: 100%;
		background: linear-gradient(90deg, #0a4f3c, #0d6b4f);
		transition: width 0.3s ease;
	}

	.metrics-row {
		display: flex;
		gap: 1rem;
	}

	.metric-card {
		flex: 1;
		background: #0f0f0f;
		border: 1px solid #1a1a1a;
		border-radius: 8px;
		padding: 1.5rem;
		text-align: center;
	}

	.metric-value {
		font-size: 2rem;
		font-weight: 600;
		color: #0a4f3c;
		margin-bottom: 0.5rem;
	}

	.metric-label {
		font-size: 0.7rem;
		color: #b8a678;
		letter-spacing: 0.1em;
		font-weight: 500;
	}

	.viz-card {
		background: #0f0f0f;
		border: 1px solid #1a1a1a;
		border-radius: 8px;
		padding: 1.5rem;
	}

	.viz-card h4 {
		margin: 0 0 1rem 0;
		font-size: 0.85rem;
		color: #0a4f3c;
		letter-spacing: 0.05em;
		font-weight: 500;
	}

	.bar-chart {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.bar-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.bar-label {
		font-size: 0.75rem;
		color: #b8a678;
		font-weight: 500;
	}

	.bar-container {
		position: relative;
		height: 20px;
		background: #1a1a1a;
		border-radius: 4px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		background: linear-gradient(90deg, #0a4f3c, #0d6b4f);
		transition: width 0.3s ease;
	}

	.bar-value {
		position: absolute;
		right: 0.5rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.7rem;
		font-weight: 500;
		color: #e0e0e0;
	}

	.distribution-chart {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.dist-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.dist-rank {
		width: 30px;
		height: 30px;
		background: rgba(10, 79, 60, 0.1);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.75rem;
		font-weight: 600;
		color: #0a4f3c;
	}

	.dist-details {
		flex: 1;
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.dist-name {
		min-width: 120px;
		font-size: 0.75rem;
		color: #e0e0e0;
		font-weight: 500;
	}

	.dist-bar {
		flex: 1;
		height: 4px;
		background: #1a1a1a;
		border-radius: 2px;
		overflow: hidden;
	}

	.dist-fill {
		height: 100%;
		background: #0a4f3c;
		transition: width 0.3s ease;
	}

	.dist-percent {
		min-width: 50px;
		text-align: right;
		font-size: 0.7rem;
		color: #b8a678;
		font-weight: 500;
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
		border: 3px solid #1a1a1a;
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
		padding: 1rem 1.5rem;
		border-bottom: 1px solid #0a4f3c;
		background: rgba(10, 79, 60, 0.05);
	}

	.drill-header h4 {
		margin: 0;
		color: #0a4f3c;
		font-size: 1rem;
	}

	.close-btn {
		background: rgba(255, 0, 102, 0.1);
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 30px;
		height: 30px;
		border-radius: 4px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1rem;
		font-weight: 600;
	}

	.host-cell {
		font-family: 'Courier New', monospace;
		color: #0a4f3c;
		font-weight: 500;
	}

	.status-badge {
		padding: 0.2rem 0.4rem;
		border-radius: 3px;
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
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