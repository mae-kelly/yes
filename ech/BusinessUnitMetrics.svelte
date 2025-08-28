<!-- BusinessUnitMetrics.svelte - Optimized Divisions -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedBU = null;
	let buDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 8;

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
	
	$: paginatedBUs = filteredBUs.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(filteredBUs.length / itemsPerPage);
	$: maxCount = filteredBUs.length > 0 ? Math.max(...filteredBUs.map(([,c]) => c)) : 1;

	function getThreatLevel(count) {
		if (!maxCount) return { level: 'LOW', color: '#0a4f3c' };
		let percentage = (count / maxCount) * 100;
		if (percentage >= 60) return { level: 'CRITICAL', color: '#ff0066' };
		if (percentage >= 40) return { level: 'HIGH', color: '#ff9900' };
		if (percentage >= 20) return { level: 'MEDIUM', color: '#ffcc00' };
		return { level: 'LOW', color: '#0a4f3c' };
	}

	function getPercentage(count) {
		let total = Object.values(data.business_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
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

	$: categoryBreakdown = filteredBUs.reduce((acc, [bu, count]) => {
		let category = 'Other';
		let buLower = bu.toLowerCase();
		if (buLower.includes('technology') || buLower.includes('it')) category = 'Technology';
		else if (buLower.includes('operations')) category = 'Operations';
		else if (buLower.includes('security')) category = 'Security';
		else if (buLower.includes('finance')) category = 'Finance';
		else if (buLower.includes('marketing')) category = 'Marketing';
		
		acc[category] = (acc[category] || 0) + count;
		return acc;
	}, {});
</script>

<div class="bu-dashboard">
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
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
					<p>Analyzing divisions...</p>
				</div>
			{:else if selectedBU}
				<!-- Drill-down View -->
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedBU.bu.toUpperCase()}</h4>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>REGION</th>
									<th>INFRA</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each buDetails.slice(0, 8) as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.region || 'Unknown'}</td>
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
			{:else}
				<!-- Main Table -->
				<div class="table-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>DIVISION</th>
								<th>ASSETS</th>
								<th>COVERAGE</th>
								<th>PRIORITY</th>
								<th>ACTION</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedBUs as [bu, count]}
								<tr>
									<td class="bu-cell">
										<span class="indicator" style="background: {getThreatLevel(count).color}"></span>
										<span>{bu.substring(0, 25)}</span>
									</td>
									<td class="center">{count.toLocaleString()}</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {(count/maxCount)*100}%; background: {getThreatLevel(count).color}"></div>
											</div>
											<span class="coverage-text">{getPercentage(count)}%</span>
										</div>
									</td>
									<td class="center">
										<span class="threat-badge {getThreatLevel(count).level.toLowerCase()}">{getThreatLevel(count).level}</span>
									</td>
									<td class="center">
										<button class="drill-btn" on:click={() => drillDownBU(bu, count)}>→</button>
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
					<div class="metric-label">ASSETS</div>
				</div>
			</div>

			<!-- Category Distribution -->
			<div class="viz-card">
				<h4>CATEGORY DISTRIBUTION</h4>
				<div class="donut-chart">
					<svg viewBox="0 0 160 160">
						{#if Object.keys(categoryBreakdown).length > 0}
							{#each Object.entries(categoryBreakdown) as [category, count], i}
								<circle
									cx="80"
									cy="80"
									r={50 - i * 7}
									fill="none"
									stroke={category === 'Technology' ? '#0a4f3c' : 
										category === 'Operations' ? '#1e3a5f' : 
										category === 'Security' ? '#ff0066' :
										category === 'Finance' ? '#ffcc00' : '#b8a678'}
									stroke-width="12"
									stroke-dasharray={`${(count / Object.values(categoryBreakdown).reduce((a,b) => a+b, 0) * 314)} 314`}
									transform="rotate(-90 80 80)"
									opacity="0.8"
								/>
							{/each}
						{/if}
						<text x="80" y="75" text-anchor="middle" fill="#b8a678" font-size="18" font-weight="bold">
							{filteredBUs.length}
						</text>
						<text x="80" y="90" text-anchor="middle" fill="rgba(184, 166, 120, 0.6)" font-size="8">
							DIVISIONS
						</text>
					</svg>
				</div>
			</div>

			<!-- Top Business Units -->
			<div class="viz-card">
				<h4>TOP 5 DIVISIONS</h4>
				<div class="bar-chart">
					{#each filteredBUs.slice(0, 5) as [bu, count]}
						<div class="bar-item">
							<div class="bar-label">{bu.substring(0, 20)}</div>
							<div class="bar-container">
								<div class="bar-fill" style="width: {(count/maxCount)*100}%; background: {getThreatLevel(count).color}"></div>
								<span class="bar-value">{count}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Activity Matrix -->
			<div class="viz-card">
				<h4>ACTIVITY MATRIX</h4>
				<div class="matrix-grid">
					{#each paginatedBUs.slice(0, 6) as [bu, count]}
						<div class="matrix-cell" style="background: {getThreatLevel(count).color}20; border-color: {getThreatLevel(count).color}">
							<div class="cell-value">{getPercentage(count)}%</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.bu-dashboard {
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
	}

	.data-table td {
		padding: 0.25rem 0.3rem;
		border-bottom: 1px solid rgba(30, 58, 95, 0.2);
		color: #b8a678;
	}

	.data-table tr:hover {
		background: rgba(10, 79, 60, 0.05);
	}

	.bu-cell {
		display: flex;
		align-items: center;
		gap: 0.3rem;
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
		gap: 0.3rem;
	}

	.coverage-bar {
		flex: 1;
		height: 4px;
		background: rgba(30, 58, 95, 0.3);
		border-radius: 2px;
		overflow: hidden;
		min-width: 50px;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.5s ease;
	}

	.coverage-text {
		font-size: 0.55rem;
		min-width: 35px;
		text-align: right;
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
	}

	.donut-chart {
		width: 100%;
		max-width: 160px;
		margin: 0 auto;
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
		position: relative;
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

	.matrix-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.3rem;
	}

	.matrix-cell {
		aspect-ratio: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		border: 1px solid;
		border-radius: 2px;
		padding: 0.2rem;
	}

	.cell-value {
		font-size: 0.5rem;
		font-weight: 600;
		color: #fff;
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

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}
</style>