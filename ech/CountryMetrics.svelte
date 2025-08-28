<!-- CountryMetrics.svelte - Enhanced Country Analysis -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';

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
	
	$: maxCount = sortedCountries.length > 0 ? Math.max(...sortedCountries.map(([,c]) => c)) : 1;

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
</script>

<div class="dashboard-container">
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<h3 class="panel-title">
					<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"/>
					</svg>
					Country Asset Distribution
				</h3>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search countries..."
						class="search-input"
					/>
				</div>
			</div>
			
			{#if loading && !selectedCountry}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>ANALYZING COUNTRY DATA...</p>
				</div>
			{:else if selectedCountry}
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedCountry.country.toUpperCase()}</h4>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="drill-table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>REGION</th>
									<th>INFRASTRUCTURE</th>
									<th>DATA CENTER</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each countryDetails as host}
									<tr>
										<td class="host-cell">{host.host.substring(0, 30)}</td>
										<td>{host.region || '-'}</td>
										<td>{host.infrastructure_type || '-'}</td>
										<td>{host.data_center || '-'}</td>
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
								<th>COUNTRY</th>
								<th>ASSETS</th>
								<th>PERCENTAGE</th>
								<th>DISTRIBUTION</th>
							</tr>
						</thead>
						<tbody>
							{#each sortedCountries as [country, count]}
								<tr on:click={() => drillDownCountry(country, count)}>
									<td class="country-cell">
										<span class="country-name">{country.substring(0, 30).toUpperCase()}</span>
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
					<div class="metric-value">{(data.total_countries || 0)}</div>
					<div class="metric-label">COUNTRIES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL ASSETS</div>
				</div>
			</div>

			<!-- Top Countries -->
			<div class="viz-card">
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
					</svg>
					TOP COUNTRIES BY ASSETS
				</h4>
				<div class="bar-chart">
					{#each sortedCountries.slice(0, 8) as [country, count]}
						<div class="bar-item">
							<div class="bar-label">{country.substring(0, 20).toUpperCase()}</div>
							<div class="bar-container">
								<div class="bar-fill" style="width: {(count/maxCount)*100}%"></div>
								<span class="bar-value">{count}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Geographic Distribution -->
			<div class="viz-card">
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
					</svg>
					ASSET CONCENTRATION
				</h4>
				<div class="concentration-list">
					{#each sortedCountries.slice(0, 5) as [country, count], i}
						<div class="concentration-item">
							<div class="rank">#{i + 1}</div>
							<div class="country-info">
								<div class="country-label">{country.toUpperCase()}</div>
								<div class="country-stats">
									<span class="stat-value">{count.toLocaleString()} assets</span>
									<span class="stat-separator">•</span>
									<span class="stat-percent">{getPercentage(count)}%</span>
								</div>
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

	.country-cell {
		display: flex;
		align-items: center;
	}

	.country-name {
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

	.concentration-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.concentration-item {
		display: flex;
		align-items: center;
		gap: 1rem;
		background: #0a0a0a;
		border: 1px solid #1a1a1a;
		border-radius: 6px;
		padding: 0.75rem;
		transition: all 0.2s ease;
	}

	.concentration-item:hover {
		border-color: #0a4f3c;
		background: rgba(10, 79, 60, 0.02);
	}

	.rank {
		width: 32px;
		height: 32px;
		background: rgba(10, 79, 60, 0.1);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.8rem;
		font-weight: 600;
		color: #0a4f3c;
	}

	.country-info {
		flex: 1;
	}

	.country-label {
		font-size: 0.8rem;
		color: #e0e0e0;
		font-weight: 500;
		margin-bottom: 0.25rem;
	}

	.country-stats {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.7rem;
		color: #b8a678;
	}

	.stat-separator {
		color: #1a1a1a;
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