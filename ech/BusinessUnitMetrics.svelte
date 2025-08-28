<!-- BusinessUnitMetrics.svelte - Enhanced Business Division Analysis -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedBU = null;
	let buDetails = [];
	let searchTerm = '';

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/business_unit_metrics');
			let result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			console.error('Business unit metrics error:', err);
			loading = false;
		}
	});

	$: filteredBUs = data.business_intelligence ? 
		Object.entries(data.business_intelligence)
			.filter(([bu]) => bu.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredBUs.length > 0 ? Math.max(...filteredBUs.map(([,c]) => c)) : 1;

	function getPercentage(count) {
		let total = Object.values(data.business_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
	}

	function getOperationalHealth(count) {
		const percentage = (count / maxCount) * 100;
		if (percentage >= 60) return { status: 'OPTIMAL', color: '#0a4f3c' };
		if (percentage >= 40) return { status: 'GOOD', color: '#ffcc00' };
		if (percentage >= 20) return { status: 'FAIR', color: '#ff9900' };
		return { status: 'CRITICAL', color: '#ff0066' };
	}

	async function drillDownBU(bu, count) {
		selectedBU = { bu, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(bu)}`);
			let result = await response.json();
			buDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('BU drill-down error:', err);
			buDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedBU = null;
		buDetails = [];
	}
</script>

<div class="dashboard-container">
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<h3 class="panel-title">
					<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
					</svg>
					Business Division Analysis
				</h3>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search divisions..."
						class="search-input"
					/>
				</div>
			</div>
			
			{#if loading && !selectedBU}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>ANALYZING DIVISIONS...</p>
				</div>
			{:else if selectedBU}
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedBU.bu.toUpperCase()}</h4>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="drill-table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>REGION</th>
									<th>INFRASTRUCTURE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each buDetails as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.region || 'Unknown'}</td>
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
				<div class="table-scroll-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>DIVISION</th>
								<th>ASSETS</th>
								<th>COVERAGE</th>
								<th>HEALTH STATUS</th>
							</tr>
						</thead>
						<tbody>
							{#each filteredBUs as [bu, count]}
								{@const health = getOperationalHealth(count)}
								<tr on:click={() => drillDownBU(bu, count)}>
									<td class="bu-cell">
										<svg class="status-icon" viewBox="0 0 12 12">
											<rect x="2" y="2" width="8" height="8" fill={health.color} opacity="0.3"/>
											<rect x="4" y="4" width="4" height="4" fill={health.color}/>
										</svg>
										<span class="bu-name">{bu.substring(0, 35).toUpperCase()}</span>
									</td>
									<td class="center">{count.toLocaleString()}</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {(count/maxCount)*100}%; background: {health.color}"></div>
											</div>
											<span class="coverage-text">{getPercentage(count)}%</span>
										</div>
									</td>
									<td class="center">
										<span class="health-badge" style="color: {health.color}; border-color: {health.color}">{health.status}</span>
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
					<div class="metric-value">{filteredBUs.length}</div>
					<div class="metric-label">DIVISIONS</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Object.values(data.business_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL ASSETS</div>
				</div>
			</div>

			<!-- Division Performance -->
			<div class="viz-card">
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
					</svg>
					TOP PERFORMING DIVISIONS
				</h4>
				<div class="performance-list">
					{#each filteredBUs.slice(0, 8) as [bu, count]}
						{@const health = getOperationalHealth(count)}
						<div class="perf-item">
							<div class="perf-rank" style="border-color: {health.color}">
								<svg viewBox="0 0 24 24" fill={health.color}>
									<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
								</svg>
							</div>
							<div class="perf-details">
								<div class="perf-name">{bu.substring(0, 25).toUpperCase()}</div>
								<div class="perf-stats">
									<span>{count.toLocaleString()} assets</span>
									<span class="separator">•</span>
									<span>{getPercentage(count)}%</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Division Health Matrix -->
			<div class="viz-card">
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
					</svg>
					OPERATIONAL METRICS
				</h4>
				<div class="health-grid">
					{#each filteredBUs.slice(0, 6) as [bu, count]}
						{@const health = getOperationalHealth(count)}
						{@const percentage = getPercentage(count)}
						<div class="health-card" style="border-color: {health.color}">
							<div class="health-value" style="color: {health.color}">{percentage}%</div>
							<div class="health-label">{bu.substring(0, 10).toUpperCase()}</div>
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

	.bu-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.status-icon {
		width: 12px;
		height: 12px;
		flex-shrink: 0;
	}

	.bu-name {
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
		min-width: 60px;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.3s ease;
	}

	.coverage-text {
		font-size: 0.7rem;
		min-width: 45px;
		text-align: right;
		color: #b8a678;
	}

	.health-badge {
		padding: 0.25rem 0.5rem;
		border: 1px solid;
		border-radius: 4px;
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
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

	.performance-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.perf-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem;
		background: #0a0a0a;
		border-radius: 4px;
		transition: all 0.2s ease;
	}

	.perf-item:hover {
		background: rgba(10, 79, 60, 0.05);
	}

	.perf-rank {
		width: 24px;
		height: 24px;
		border: 1px solid;
		border-radius: 4px;
		padding: 4px;
	}

	.perf-rank svg {
		width: 100%;
		height: 100%;
	}

	.perf-details {
		flex: 1;
	}

	.perf-name {
		font-size: 0.75rem;
		color: #e0e0e0;
		font-weight: 500;
		margin-bottom: 0.2rem;
	}

	.perf-stats {
		font-size: 0.65rem;
		color: #b8a678;
	}

	.separator {
		margin: 0 0.3rem;
		color: #1a1a1a;
	}

	.health-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.75rem;
	}

	.health-card {
		background: #0a0a0a;
		border: 1px solid;
		border-radius: 6px;
		padding: 1rem;
		text-align: center;
	}

	.health-value {
		font-size: 1.2rem;
		font-weight: 600;
		margin-bottom: 0.25rem;
	}

	.health-label {
		font-size: 0.6rem;
		color: #b8a678;
		text-transform: uppercase;
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