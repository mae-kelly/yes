<!-- CIOMetrics.svelte - Optimized -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCio = null;
	let cioDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 8;
	let hoveredCio = null;

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/cio_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('CIO metrics error:', err);
			loading = false;
		}
	});

	$: sortedCios = data.operative_intelligence ? 
		Object.entries(data.operative_intelligence)
			.filter(([cio]) => cio.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: paginatedCios = sortedCios.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(sortedCios.length / itemsPerPage);
	$: maxAssets = sortedCios.length > 0 ? Math.max(...sortedCios.map(([,count]) => count)) : 1;

	function getExecutiveLevel(count) {
		if (!maxAssets) return { level: 'ANALYST', color: '#0a4f3c', icon: '📊' };
		let percentage = (count / maxAssets) * 100;
		if (percentage >= 70) return { level: 'C-SUITE', color: '#ff0066', icon: '👔' };
		if (percentage >= 40) return { level: 'VP', color: '#ff9900', icon: '💼' };
		if (percentage >= 20) return { level: 'DIRECTOR', color: '#ffcc00', icon: '📋' };
		return { level: 'ANALYST', color: '#0a4f3c', icon: '📊' };
	}

	function getPercentage(count) {
		let total = Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
	}

	async function drillDownCio(cio, count) {
		selectedCio = { cio, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(cio)}`);
			let result = await response.json();
			cioDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('CIO drill-down error:', err);
			cioDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedCio = null;
		cioDetails = [];
	}

	$: executiveDistribution = sortedCios.reduce((acc, [_, count]) => {
		let level = getExecutiveLevel(count).level;
		acc[level] = (acc[level] || 0) + 1;
		return acc;
	}, {});

	$: topExecutives = sortedCios.slice(0, 5);
</script>

<div class="cio-dashboard">
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search executives..."
						class="search-input"
					/>
				</div>
			</div>
			
			{#if loading && !selectedCio}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>Scanning executives...</p>
				</div>
			{:else if selectedCio}
				<!-- Drill-down View -->
				<div class="drill-view">
					<div class="drill-header">
						<div class="exec-profile">
							<span class="profile-icon">{getExecutiveLevel(selectedCio.count).icon}</span>
							<h4>{selectedCio.cio.toUpperCase()}</h4>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="drill-stats">
						<div class="stat-item">
							<span class="stat-value">{selectedCio.count.toLocaleString()}</span>
							<span class="stat-label">Assets</span>
						</div>
						<div class="stat-item">
							<span class="stat-value">{getPercentage(selectedCio.count)}%</span>
							<span class="stat-label">Coverage</span>
						</div>
						<div class="stat-item">
							<span class="stat-value">{getExecutiveLevel(selectedCio.count).level}</span>
							<span class="stat-label">Level</span>
						</div>
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
								{#each cioDetails.slice(0, 6) as host}
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
				<!-- Main Table View -->
				<div class="table-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>EXECUTIVE</th>
								<th>LEVEL</th>
								<th>ASSETS</th>
								<th>COVERAGE</th>
								<th>RISK</th>
								<th>ACTION</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedCios as [cio, count]}
								{@const exec = getExecutiveLevel(count)}
								<tr on:mouseenter={() => hoveredCio = cio} on:mouseleave={() => hoveredCio = null}>
									<td class="exec-cell">
										<span class="exec-icon">{exec.icon}</span>
										<span>{cio.substring(0, 20).toUpperCase()}</span>
									</td>
									<td class="center">
										<span class="level-badge {exec.level.toLowerCase()}">{exec.level}</span>
									</td>
									<td class="center">{count.toLocaleString()}</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {getPercentage(count)}%; background: {exec.color}"></div>
											</div>
											<span class="coverage-text">{getPercentage(count)}%</span>
										</div>
									</td>
									<td class="center">
										<span class="risk-badge {exec.level === 'C-SUITE' ? 'low' : exec.level === 'VP' ? 'medium' : 'high'}">
											{exec.level === 'C-SUITE' ? 'LOW' : exec.level === 'VP' ? 'MED' : 'HIGH'}
										</span>
									</td>
									<td class="center">
										<button class="drill-btn" on:click={() => drillDownCio(cio, count)}>→</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
			
			<!-- Pagination -->
			{#if !selectedCio}
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
					<div class="metric-value">{sortedCios.length}</div>
					<div class="metric-label">EXECUTIVES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="metric-label">ASSETS</div>
				</div>
			</div>

			<!-- Executive Hierarchy -->
			<div class="viz-card">
				<h4>HIERARCHY</h4>
				<div class="hierarchy-chart">
					{#each Object.entries(executiveDistribution) as [level, count]}
						{@const levelData = level === 'C-SUITE' ? {color: '#ff0066', icon: '👔'} :
							level === 'VP' ? {color: '#ff9900', icon: '💼'} :
							level === 'DIRECTOR' ? {color: '#ffcc00', icon: '📋'} :
							{color: '#0a4f3c', icon: '📊'}}
						<div class="hierarchy-level">
							<div class="level-header">
								<span class="level-icon">{levelData.icon}</span>
								<span class="level-name">{level}</span>
							</div>
							<div class="level-bar-container">
								<div class="level-bar" style="width: {(count/sortedCios.length)*100}%; background: {levelData.color}"></div>
							</div>
							<div class="level-count">{count}</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Top Executives -->
			<div class="viz-card">
				<h4>TOP EXECUTIVES</h4>
				<div class="bar-chart">
					{#each topExecutives.slice(0, 4) as [cio, count]}
						{@const exec = getExecutiveLevel(count)}
						<div class="bar-item">
							<div class="bar-label">
								<span class="bar-icon">{exec.icon}</span>
								<span>{cio.substring(0, 12)}</span>
							</div>
							<div class="bar-container">
								<div class="bar-fill" style="width: {(count/maxAssets)*100}%; background: {exec.color}"></div>
								<span class="bar-value">{count}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Portfolio Distribution -->
			<div class="viz-card">
				<h4>PORTFOLIO</h4>
				<div class="donut-chart">
					<svg viewBox="0 0 150 150">
						{#if sortedCios.length > 0}
							{@const total = Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0)}
							{@const radius = 45}
							{@const circumference = 2 * Math.PI * radius}
							{#each sortedCios.slice(0, 5) as [cio, count], i}
								{@const percentage = (count / total) * 100}
								{@const strokeDasharray = (percentage / 100) * circumference}
								{@const rotation = sortedCios.slice(0, i)
									.reduce((acc, [_, c]) => acc + (c / total) * 360, -90)}
								{@const exec = getExecutiveLevel(count)}
								<circle
									cx="75"
									cy="75"
									r={radius}
									fill="none"
									stroke={exec.color}
									stroke-width="20"
									stroke-dasharray="{strokeDasharray} {circumference}"
									transform="rotate({rotation} 75 75)"
									opacity="0.8"
								/>
							{/each}
						{/if}
						<text x="75" y="72" text-anchor="middle" fill="#b8a678" font-size="18" font-weight="bold">
							{sortedCios.length}
						</text>
						<text x="75" y="85" text-anchor="middle" fill="#b8a678" font-size="8">
							EXECS
						</text>
					</svg>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.cio-dashboard {
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

	.exec-cell {
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}

	.exec-icon {
		font-size: 0.8rem;
	}

	.center {
		text-align: center;
	}

	.level-badge {
		padding: 0.1rem 0.3rem;
		border-radius: 2px;
		font-size: 0.5rem;
		font-weight: 600;
	}

	.level-badge.c-suite {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.level-badge.vp {
		background: rgba(255, 153, 0, 0.2);
		color: #ff9900;
		border: 1px solid #ff9900;
	}

	.level-badge.director {
		background: rgba(255, 204, 0, 0.2);
		color: #ffcc00;
		border: 1px solid #ffcc00;
	}

	.level-badge.analyst {
		background: rgba(10, 79, 60, 0.2);
		color: #0a4f3c;
		border: 1px solid #0a4f3c;
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
		min-width: 35px;
		text-align: right;
		color: #b8a678;
	}

	.risk-badge {
		padding: 0.1rem 0.3rem;
		border-radius: 2px;
		font-size: 0.5rem;
		font-weight: 600;
	}

	.risk-badge.low {
		background: rgba(10, 79, 60, 0.2);
		color: #0a4f3c;
		border: 1px solid #0a4f3c;
	}

	.risk-badge.medium {
		background: rgba(255, 204, 0, 0.2);
		color: #ffcc00;
		border: 1px solid #ffcc00;
	}

	.risk-badge.high {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
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

	.exec-profile {
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}

	.profile-icon {
		font-size: 1rem;
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

	.drill-stats {
		display: flex;
		gap: 0.8rem;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.3);
		border-bottom: 1px solid rgba(30, 58, 95, 0.2);
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		align-items: center;
	}

	.stat-value {
		font-size: 0.8rem;
		font-weight: 600;
		color: #0a4f3c;
		text-shadow: 0 0 5px rgba(10, 79, 60, 0.3);
	}

	.stat-label {
		font-size: 0.5rem;
		color: #b8a678;
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

	.hierarchy-chart {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.hierarchy-level {
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}

	.level-header {
		display: flex;
		align-items: center;
		gap: 0.2rem;
		min-width: 70px;
	}

	.level-icon {
		font-size: 0.7rem;
	}

	.level-name {
		font-size: 0.5rem;
		color: #b8a678;
	}

	.level-bar-container {
		flex: 1;
		height: 5px;
		background: rgba(30, 58, 95, 0.3);
		border-radius: 2px;
		overflow: hidden;
	}

	.level-bar {
		height: 100%;
		transition: width 0.5s ease;
	}

	.level-count {
		font-size: 0.5rem;
		color: #b8a678;
		min-width: 15px;
		text-align: right;
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
		display: flex;
		align-items: center;
		gap: 0.2rem;
		font-size: 0.5rem;
		color: #b8a678;
	}

	.bar-icon {
		font-size: 0.6rem;
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
		font-size: 0.45rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 0 0 3px #000;
	}

	.donut-chart {
		width: 100%;
		max-width: 150px;
		margin: 0 auto;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@media (max-width: 1200px) {
		.viz-panel {
			min-width: 240px;
		}
	}
</style>