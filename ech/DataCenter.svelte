<!-- DataCenter.svelte - Optimized -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCenter = null;
	let centerDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 8;
	let viewMode = 'table';

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
	
	$: paginatedCenters = filteredCenters.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(filteredCenters.length / itemsPerPage);
	$: maxCount = filteredCenters.length > 0 ? Math.max(...filteredCenters.map(([,c]) => c)) : 1;

	function getThreatLevel(count) {
		if (!maxCount) return { level: 'LOW', color: '#0a4f3c' };
		let percentage = (count / maxCount) * 100;
		if (percentage >= 60) return { level: 'CRITICAL', color: '#ff0066' };
		if (percentage >= 40) return { level: 'HIGH', color: '#ff9900' };
		if (percentage >= 20) return { level: 'MEDIUM', color: '#ffcc00' };
		return { level: 'LOW', color: '#0a4f3c' };
	}

	function getPercentage(count) {
		let total = Object.values(data.facility_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
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

	$: threatDistribution = filteredCenters.reduce((acc, [_, count]) => {
		let level = getThreatLevel(count).level;
		acc[level] = (acc[level] || 0) + 1;
		return acc;
	}, {});
</script>

<div class="dashboard-container">
	<div class="main-content">
		<!-- Left Panel -->
		<div class="table-panel">
			<div class="panel-header">
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search facilities..."
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
			
			{#if loading && !selectedCenter}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>Scanning facilities...</p>
				</div>
			{:else if selectedCenter}
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedCenter.center.toUpperCase()}</h4>
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
								{#each centerDetails.slice(0, 6) as host}
									<tr>
										<td class="host-cell">{host.host.substring(0, 20)}</td>
										<td>{host.region || '-'}</td>
										<td>{host.country || '-'}</td>
										<td>{host.infrastructure_type || '-'}</td>
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
								<th>DATA CENTER</th>
								<th>ASSETS</th>
								<th>COVERAGE</th>
								<th>THREAT</th>
								<th>ACTION</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedCenters as [center, count]}
								<tr>
									<td class="center-cell">
										<span class="indicator" style="background: {getThreatLevel(count).color}"></span>
										<span>{center.substring(0, 20).toUpperCase()}</span>
									</td>
									<td class="center">{count.toLocaleString()}</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {getPercentage(count)}%; background: {getThreatLevel(count).color}"></div>
											</div>
											<span class="coverage-text">{getPercentage(count)}%</span>
										</div>
									</td>
									<td class="center">
										<span class="threat-badge {getThreatLevel(count).level.toLowerCase()}">{getThreatLevel(count).level}</span>
									</td>
									<td class="center">
										<button class="drill-btn" on:click={() => drillDownCenter(center, count)}>→</button>
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
					{#each paginatedCenters.slice(0, 6) as [center, count]}
						<div class="grid-card" style="--card-color: {getThreatLevel(count).color}" on:click={() => drillDownCenter(center, count)}>
							<div class="card-header">
								<span class="threat-indicator {getThreatLevel(count).level.toLowerCase()}">{getThreatLevel(count).level}</span>
							</div>
							<div class="card-body">
								<div class="center-name">{center.substring(0, 12).toUpperCase()}</div>
								<div class="center-count">{count.toLocaleString()}</div>
								<div class="progress-bar">
									<div class="progress-fill" style="width: {(count/maxCount)*100}%; background: {getThreatLevel(count).color}"></div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Right Panel -->
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

			<!-- Threat Distribution -->
			<div class="viz-card">
				<h4>THREAT MATRIX</h4>
				<div class="threat-chart">
					{#each Object.entries(threatDistribution) as [level, count]}
						{@const color = level === 'CRITICAL' ? '#ff0066' : level === 'HIGH' ? '#ff9900' : level === 'MEDIUM' ? '#ffcc00' : '#0a4f3c'}
						<div class="threat-row">
							<div class="threat-label">{level}</div>
							<div class="threat-bar-container">
								<div class="threat-bar" style="width: {(count/filteredCenters.length)*100}%; background: {color}"></div>
							</div>
							<div class="threat-count">{count}</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Top Facilities -->
			<div class="viz-card">
				<h4>TOP FACILITIES</h4>
				<div class="bar-chart">
					{#each filteredCenters.slice(0, 4) as [center, count]}
						<div class="bar-item">
							<div class="bar-label">{center.substring(0, 10).toUpperCase()}</div>
							<div class="bar-container">
								<div class="bar-fill" style="width: {(count/maxCount)*100}%; background: {getThreatLevel(count).color}"></div>
								<span class="bar-value">{count}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Network Status -->
			<div class="viz-card">
				<h4>NETWORK STATUS</h4>
				<div class="network-grid">
					{#each filteredCenters.slice(0, 4) as [center, count]}
						<div class="network-node">
							<div class="node-core" style="--node-color: {getThreatLevel(count).color}">
								<div class="pulse-ring"></div>
								<div class="node-value">{count}</div>
							</div>
							<div class="node-label">{center.substring(0, 4).toUpperCase()}</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.dashboard-container {
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
		min-width: 260px;
		max-width: 320px;
	}

	.panel-header {
		padding: 0.4rem;
		border-bottom: 1px solid #1e3a5f;
		background: rgba(0, 0, 0, 0.3);
	}

	.controls {
		display: flex;
		gap: 0.4rem;
		align-items: center;
	}

	.search-input {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #1e3a5f;
		border-radius: 3px;
		padding: 0.2rem 0.4rem;
		color: #b8a678;
		font-size: 0.6rem;
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
		padding: 0.15rem 0.3rem;
		border-radius: 3px;
		cursor: pointer;
		font-size: 0.5rem;
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
		font-size: 0.6rem;
	}

	.data-table th {
		background: rgba(10, 79, 60, 0.1);
		color: #0a4f3c;
		padding: 0.25rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.03em;
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.data-table td {
		padding: 0.2rem 0.25rem;
		border-bottom: 1px solid rgba(30, 58, 95, 0.2);
		color: #b8a678;
	}

	.data-table tr:hover {
		background: rgba(10, 79, 60, 0.05);
	}

	.center-cell {
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}

	.indicator {
		width: 5px;
		height: 5px;
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
		height: 3px;
		background: rgba(30, 58, 95, 0.3);
		border-radius: 2px;
		overflow: hidden;
		min-width: 35px;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.5s ease;
	}

	.coverage-text {
		font-size: 0.5rem;
		min-width: 30px;
		text-align: right;
	}

	.threat-badge {
		padding: 0.1rem 0.25rem;
		border-radius: 2px;
		font-size: 0.45rem;
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
		padding: 0.1rem 0.25rem;
		border-radius: 2px;
		cursor: pointer;
		font-size: 0.5rem;
		font-weight: 700;
	}

	.drill-btn:hover {
		background: rgba(10, 79, 60, 0.3);
		box-shadow: 0 0 5px rgba(10, 79, 60, 0.5);
	}

	.grid-container {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.4rem;
		padding: 0.4rem;
	}

	.grid-card {
		background: rgba(0, 0, 0, 0.7);
		border: 1px solid var(--card-color);
		border-radius: 3px;
		padding: 0.4rem;
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
		margin-bottom: 0.2rem;
	}

	.threat-indicator {
		font-size: 0.4rem;
		padding: 0.05rem 0.15rem;
		border-radius: 2px;
		font-weight: 600;
	}

	.threat-indicator.critical { background: rgba(255, 0, 102, 0.2); color: #ff0066; border: 1px solid #ff0066; }
	.threat-indicator.high { background: rgba(255, 153, 0, 0.2); color: #ff9900; border: 1px solid #ff9900; }
	.threat-indicator.medium { background: rgba(255, 204, 0, 0.2); color: #ffcc00; border: 1px solid #ffcc00; }
	.threat-indicator.low { background: rgba(10, 79, 60, 0.2); color: #0a4f3c; border: 1px solid #0a4f3c; }

	.card-body {
		text-align: center;
	}

	.center-name {
		font-size: 0.55rem;
		color: #b8a678;
		margin-bottom: 0.2rem;
		font-weight: 600;
	}

	.center-count {
		font-size: 0.8rem;
		font-weight: 700;
		color: var(--card-color);
		margin-bottom: 0.2rem;
	}

	.progress-bar {
		width: 100%;
		height: 2px;
		background: rgba(30, 58, 95, 0.3);
		border-radius: 1px;
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
		gap: 0.4rem;
		padding: 0.25rem;
		border-top: 1px solid #1e3a5f;
		background: rgba(0, 0, 0, 0.3);
	}

	.pagination button {
		background: rgba(10, 79, 60, 0.1);
		border: 1px solid #0a4f3c;
		color: #0a4f3c;
		padding: 0.15rem 0.3rem;
		border-radius: 3px;
		cursor: pointer;
		font-size: 0.5rem;
		font-weight: 600;
	}

	.pagination button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.pagination span {
		font-size: 0.55rem;
		color: #b8a678;
	}

	.metrics-row {
		display: flex;
		gap: 0.3rem;
	}

	.metric-card {
		flex: 1;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid #1e3a5f;
		border-radius: 3px;
		padding: 0.3rem;
		text-align: center;
	}

	.metric-value {
		font-size: 0.9rem;
		font-weight: 700;
		color: #0a4f3c;
		text-shadow: 0 0 8px rgba(10, 79, 60, 0.3);
	}

	.metric-label {
		font-size: 0.45rem;
		color: #b8a678;
		margin-top: 0.1rem;
		letter-spacing: 0.03em;
	}

	.viz-card {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid #1e3a5f;
		border-radius: 3px;
		padding: 0.4rem;
	}

	.viz-card h4 {
		margin: 0 0 0.3rem 0;
		font-size: 0.55rem;
		color: #0a4f3c;
		letter-spacing: 0.03em;
		text-align: center;
		font-weight: 600;
	}

	.threat-chart {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.threat-row {
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}

	.threat-label {
		font-size: 0.45rem;
		color: #b8a678;
		min-width: 40px;
		font-weight: 600;
	}

	.threat-bar-container {
		flex: 1;
		height: 5px;
		background: rgba(30, 58, 95, 0.3);
		border-radius: 2px;
		overflow: hidden;
	}

	.threat-bar {
		height: 100%;
		transition: width 0.5s ease;
	}

	.threat-count {
		font-size: 0.45rem;
		color: #b8a678;
		min-width: 12px;
		text-align: right;
	}

	.bar-chart {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.bar-item {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
	}

	.bar-label {
		font-size: 0.45rem;
		color: #b8a678;
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
		font-size: 0.4rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 0 0 2px #000;
	}

	.network-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.4rem;
		padding: 0.3rem;
	}

	.network-node {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.2rem;
	}

	.node-core {
		position: relative;
		width: 35px;
		height: 35px;
		border: 2px solid var(--node-color);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		background: radial-gradient(circle, var(--node-color), transparent);
	}

	.pulse-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid var(--node-color);
		border-radius: 50%;
		animation: nodePulse 2s ease-out infinite;
	}

	@keyframes nodePulse {
		0% { transform: scale(1); opacity: 1; }
		100% { transform: scale(1.3); opacity: 0; }
	}

	.node-value {
		font-size: 0.55rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 8px var(--node-color);
	}

	.node-label {
		font-size: 0.4rem;
		color: #b8a678;
		text-align: center;
	}

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.4rem;
	}

	.spinner {
		width: 25px;
		height: 25px;
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
		padding: 0.4rem;
		border-bottom: 1px solid #0a4f3c;
		background: rgba(10, 79, 60, 0.05);
	}

	.drill-header h4 {
		margin: 0;
		color: #0a4f3c;
		font-size: 0.65rem;
	}

	.close-btn {
		background: rgba(255, 0, 102, 0.1);
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 18px;
		height: 18px;
		border-radius: 2px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.5rem;
	}

	.host-cell {
		font-family: monospace;
		color: #0a4f3c;
		font-size: 0.55rem;
	}

	.status-badge {
		padding: 0.05rem 0.15rem;
		border-radius: 2px;
		font-size: 0.45rem;
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