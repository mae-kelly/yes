<!-- DataCenter.svelte - Enhanced Data Center Analysis -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCenter = null;
	let centerDetails = [];
	let searchTerm = '';

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/data_center_metrics');
			let result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			console.error('Data center error:', err);
			loading = false;
		}
	});

	$: filteredCenters = data.facility_intelligence ? 
		Object.entries(data.facility_intelligence)
			.filter(([center]) => center.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredCenters.length > 0 ? Math.max(...filteredCenters.map(([,c]) => c)) : 1;

	function getPercentage(count) {
		let total = Object.values(data.facility_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
	}

	function getUtilization(count) {
		// Simulated utilization based on asset count
		return Math.min(95, (count / maxCount) * 100).toFixed(1);
	}

	async function drillDownCenter(center, count) {
		selectedCenter = { center, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(center)}`);
			let result = await response.json();
			centerDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Center drill-down error:', err);
			centerDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedCenter = null;
		centerDetails = [];
	}
</script>

<div class="dashboard-container">
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<h3 class="panel-title">
					<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
					</svg>
					Data Center Infrastructure
				</h3>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search facilities..."
						class="search-input"
					/>
				</div>
			</div>
			
			{#if loading && !selectedCenter}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>SCANNING FACILITIES...</p>
				</div>
			{:else if selectedCenter}
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedCenter.center.toUpperCase()}</h4>
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
								{#each centerDetails as host}
									<tr>
										<td class="host-cell">{host.host.substring(0, 30)}</td>
										<td>{host.region || '-'}</td>
										<td>{host.country || '-'}</td>
										<td>{host.infrastructure_type || '-'}</td>
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
								<th>DATA CENTER</th>
								<th>ASSETS</th>
								<th>UTILIZATION</th>
								<th>CAPACITY</th>
							</tr>
						</thead>
						<tbody>
							{#each filteredCenters as [center, count]}
								<tr on:click={() => drillDownCenter(center, count)}>
									<td class="center-cell">
										<svg class="status-icon" viewBox="0 0 12 12">
											<circle cx="6" cy="6" r="5" fill="#0a4f3c" opacity="0.3"/>
											<circle cx="6" cy="6" r="3" fill="#0a4f3c"/>
										</svg>
										<span class="center-name">{center.substring(0, 30).toUpperCase()}</span>
									</td>
									<td class="center">{count.toLocaleString()}</td>
									<td class="center">{getUtilization(count)}%</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {(count/maxCount)*100}%"></div>
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
			<!-- Metrics -->
			<div class="metrics-row">
				<div class="metric-card">
					<div class="metric-value">{filteredCenters.length}</div>
					<div class="metric-label">FACILITIES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Math.round(Object.values(data.facility_intelligence || {}).reduce((a, b) => a + b, 0) / filteredCenters.length || 0)}</div>
					<div class="metric-label">AVG/CENTER</div>
				</div>
			</div>

			<!-- Facility Status -->
			<div class="viz-card">
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/>
					</svg>
					FACILITY STATUS
				</h4>
				<div class="status-grid">
					{#each filteredCenters.slice(0, 6) as [center, count]}
						{@const utilization = getUtilization(count)}
						<div class="status-card">
							<div class="status-header">
								<span class="status-name">{center.substring(0, 8).toUpperCase()}</span>
								<span class="status-indicator {utilization > 80 ? 'high' : utilization > 50 ? 'medium' : 'low'}"></span>
							</div>
							<div class="status-value">{count}</div>
							<div class="status-label">ASSETS</div>
							<div class="utilization-bar">
								<div class="utilization-fill" style="width: {utilization}%"></div>
							</div>
							<div class="utilization-text">{utilization}% UTILIZED</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Top Facilities -->
			<div class="viz-card">
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M13 10V3L4 14h7v7l9-11h-7z"/>
					</svg>
					CAPACITY ANALYSIS
				</h4>
				<div class="bar-chart">
					{#each filteredCenters.slice(0, 5) as [center, count]}
						<div class="bar-item">
							<div class="bar-label">{center.substring(0, 15).toUpperCase()}</div>
							<div class="bar-container">
								<div class="bar-fill" style="width: {(count/maxCount)*100}%"></div>
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

	.center-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.status-icon {
		width: 12px;
		height: 12px;
		flex-shrink: 0;
	}

	.center-name {
		font-weight: 500;
		color: #e0e0e0;
	}

	.center {
		text-align: center;
	}

	.coverage-cell {
		display: flex;
		align-items: center;
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

	.status-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.75rem;
	}

	.status-card {
		background: #0a0a0a;
		border: 1px solid #1a1a1a;
		border-radius: 6px;
		padding: 1rem;
		text-align: center;
	}

	.status-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.status-name {
		font-size: 0.7rem;
		color: #b8a678;
		font-weight: 500;
	}

	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: #0a4f3c;
	}

	.status-indicator.high {
		background: #ff9900;
	}

	.status-indicator.medium {
		background: #ffcc00;
	}

	.status-indicator.low {
		background: #0a4f3c;
	}

	.status-value {
		font-size: 1.2rem;
		font-weight: 600;
		color: #0a4f3c;
		margin-bottom: 0.25rem;
	}

	.status-label {
		font-size: 0.65rem;
		color: #b8a678;
		margin-bottom: 0.5rem;
	}

	.utilization-bar {
		width: 100%;
		height: 3px;
		background: #1a1a1a;
		border-radius: 2px;
		overflow: hidden;
		margin-bottom: 0.25rem;
	}

	.utilization-fill {
		height: 100%;
		background: #0a4f3c;
		transition: width 0.3s ease;
	}

	.utilization-text {
		font-size: 0.6rem;
		color: #0a4f3c;
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