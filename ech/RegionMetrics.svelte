<!-- RegionMetrics.svelte - Enhanced Regional Analysis -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';

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

	$: maxCount = sortedRegions.length > 0 ? Math.max(...sortedRegions.map(([,c]) => c)) : 1;

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

	// Calculate regional distribution percentages
	$: regionalDistribution = sortedRegions.reduce((acc, [region, count]) => {
		const percentage = getPercentage(count);
		return { ...acc, [region]: percentage };
	}, {});
</script>

<div class="dashboard-container">
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<h3 class="panel-title">
					<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<circle cx="12" cy="12" r="10" />
						<path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
					</svg>
					Regional Asset Distribution
				</h3>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search regions..."
						class="search-input"
					/>
				</div>
			</div>
			
			{#if loading && !selectedRegion}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>SCANNING REGIONAL DATA...</p>
				</div>
			{:else if selectedRegion}
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedRegion.region.toUpperCase()}</h4>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="drill-table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>COUNTRY</th>
									<th>INFRASTRUCTURE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each regionDetails as host}
									<tr>
										<td class="host-cell">{host.host}</td>
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
				<div class="table-scroll-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>REGION</th>
								<th>ASSET COUNT</th>
								<th>PERCENTAGE</th>
								<th>DISTRIBUTION</th>
							</tr>
						</thead>
						<tbody>
							{#each sortedRegions as [region, count]}
								<tr on:click={() => drillDownRegion(region, count)}>
									<td class="region-cell">
										<span class="region-name">{region.toUpperCase()}</span>
									</td>
									<td class="center">{count.toLocaleString()}</td>
									<td class="center">{getPercentage(count)}%</td>
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
					<div class="metric-value">{sortedRegions.length}</div>
					<div class="metric-label">REGIONS</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{(data.total_coverage || 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL ASSETS</div>
				</div>
			</div>

			<!-- Regional Breakdown -->
			<div class="viz-card">
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
					</svg>
					REGIONAL DISTRIBUTION
				</h4>
				<div class="region-chart">
					{#each sortedRegions.slice(0, 6) as [region, count]}
						<div class="region-item">
							<div class="region-header">
								<span class="region-label">{region.toUpperCase()}</span>
								<span class="region-count">{count.toLocaleString()}</span>
							</div>
							<div class="region-bar">
								<div class="region-fill" style="width: {(count/maxCount)*100}%"></div>
							</div>
							<div class="region-percentage">{getPercentage(count)}%</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Asset Concentration Map -->
			<div class="viz-card">
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/>
					</svg>
					CONCENTRATION ANALYSIS
				</h4>
				<div class="concentration-grid">
					{#each sortedRegions.slice(0, 4) as [region, count]}
						{@const percentage = getPercentage(count)}
						<div class="concentration-card">
							<div class="conc-region">{region.substring(0, 8).toUpperCase()}</div>
							<div class="conc-visual">
								<svg viewBox="0 0 100 100">
									<circle cx="50" cy="50" r="40" fill="none" stroke="#1a1a1a" stroke-width="8"/>
									<circle 
										cx="50" 
										cy="50" 
										r="40" 
										fill="none" 
										stroke="#0a4f3c" 
										stroke-width="8"
										stroke-dasharray={`${percentage * 2.5} ${250 - percentage * 2.5}`}
										stroke-dashoffset="0"
										transform="rotate(-90 50 50)"
									/>
									<text x="50" y="50" text-anchor="middle" dominant-baseline="middle" fill="#e0e0e0" font-size="16" font-weight="600">
										{percentage}%
									</text>
								</svg>
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

	.region-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.region-name {
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

	.region-chart {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.region-item {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.region-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.region-label {
		font-size: 0.75rem;
		color: #e0e0e0;
		font-weight: 500;
	}

	.region-count {
		font-size: 0.75rem;
		color: #b8a678;
	}

	.region-bar {
		height: 8px;
		background: #1a1a1a;
		border-radius: 4px;
		overflow: hidden;
	}

	.region-fill {
		height: 100%;
		background: linear-gradient(90deg, #0a4f3c, #0d6b4f);
		transition: width 0.3s ease;
	}

	.region-percentage {
		font-size: 0.7rem;
		color: #0a4f3c;
		font-weight: 600;
		text-align: right;
	}

	.concentration-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
	}

	.concentration-card {
		background: #0a0a0a;
		border: 1px solid #1a1a1a;
		border-radius: 6px;
		padding: 1rem;
		text-align: center;
	}

	.conc-region {
		font-size: 0.75rem;
		color: #b8a678;
		margin-bottom: 0.5rem;
		font-weight: 500;
	}

	.conc-visual {
		width: 80px;
		height: 80px;
		margin: 0 auto;
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