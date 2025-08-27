<!-- SourceTables.svelte - Enhanced with perfect screen fit -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 10;

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

	function getThreatLevel(frequency) {
		if (!data.total_mentions) return { level: 'LOW', color: '#0096ff', intensity: 0.3 };
		let percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRIT', color: '#ff00ff', intensity: 1.0 };
		if (percentage >= 10) return { level: 'HIGH', color: '#ff0066', intensity: 0.8 };
		if (percentage >= 5) return { level: 'MED', color: '#ffaa00', intensity: 0.6 };
		return { level: 'LOW', color: '#00ffff', intensity: 0.4 };
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

	$: threatDistribution = filteredSources.reduce((acc, [_, freq]) => {
		const level = getThreatLevel(freq).level;
		acc[level] = (acc[level] || 0) + 1;
		return acc;
	}, {});
</script>

<div class="dashboard-container">
	<!-- Header Section -->
	<div class="header-section">
		<div class="header-content">
			<div class="title-block">
				<h1>SOURCE INTELLIGENCE</h1>
				<p>Comma-Separated Frequency Analysis</p>
			</div>
			<div class="metrics-row">
				<div class="metric-card">
					<div class="metric-value">{(data.unique_sources || 0).toLocaleString()}</div>
					<div class="metric-label">UNIQUE SOURCES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{(data.total_mentions || 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL MENTIONS</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Math.round((data.total_mentions || 0) / (data.unique_sources || 1))}</div>
					<div class="metric-label">AVG/SOURCE</div>
				</div>
				<div class="metric-card critical">
					<div class="metric-value">{Object.values(threatDistribution).reduce((a,b) => a+b, 0)}</div>
					<div class="metric-label">MONITORED</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content Area -->
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<h3>SOURCE TABLE ANALYSIS</h3>
				<div class="search-bar">
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
					<p>Analyzing sources...</p>
				</div>
			{:else if selectedSource}
				<!-- Drill-down View -->
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedSource.source}</h4>
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
								{#each hostDetails as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.region}</td>
										<td>{host.country}</td>
										<td>{host.infrastructure_type}</td>
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
								<th>SOURCE</th>
								<th>FREQUENCY</th>
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
										<div class="cell-content">
											<span class="indicator" style="background: {threat.color}"></span>
											<span>{source}</span>
										</div>
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
										<button class="drill-btn" on:click={() => drillDownSource(source, frequency)}>
											DRILL →
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				
				<!-- Pagination -->
				<div class="pagination">
					<button 
						on:click={() => currentPage = Math.max(1, currentPage - 1)}
						disabled={currentPage === 1}
					>
						←
					</button>
					<span>Page {currentPage} of {totalPages}</span>
					<button 
						on:click={() => currentPage = Math.min(totalPages, currentPage + 1)}
						disabled={currentPage === totalPages}
					>
						→
					</button>
				</div>
			{/if}
		</div>

		<!-- Right Panel: Visualizations -->
		<div class="viz-panel">
			<!-- Threat Distribution Chart -->
			<div class="viz-card">
				<h4>THREAT DISTRIBUTION</h4>
				<div class="donut-chart">
					<svg viewBox="0 0 200 200">
						{#if Object.keys(threatDistribution).length > 0}
							{@const total = Object.values(threatDistribution).reduce((a, b) => a + b, 0)}
							{@const radius = 60}
							{@const circumference = 2 * Math.PI * radius}
							{#each Object.entries(threatDistribution) as [level, count], i}
								{@const percentage = (count / total) * 100}
								{@const strokeDasharray = (percentage / 100) * circumference}
								{@const rotation = Object.entries(threatDistribution)
									.slice(0, i)
									.reduce((acc, [_, c]) => acc + (c / total) * 360, -90)}
								{@const color = level === 'CRIT' ? '#ff00ff' : 
									level === 'HIGH' ? '#ff0066' : 
									level === 'MED' ? '#ffaa00' : '#00ffff'}
								<circle
									cx="100"
									cy="100"
									r={radius}
									fill="none"
									stroke={color}
									stroke-width="30"
									stroke-dasharray="{strokeDasharray} {circumference}"
									transform="rotate({rotation} 100 100)"
									opacity="0.8"
								/>
							{/each}
						{/if}
						<text x="100" y="100" text-anchor="middle" fill="white" font-size="24" font-weight="bold">
							{Object.values(threatDistribution).reduce((a, b) => a + b, 0)}
						</text>
						<text x="100" y="115" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="10">
							SOURCES
						</text>
					</svg>
				</div>
				<div class="legend">
					{#each Object.entries(threatDistribution) as [level, count]}
						{@const color = level === 'CRIT' ? '#ff00ff' : 
							level === 'HIGH' ? '#ff0066' : 
							level === 'MED' ? '#ffaa00' : '#00ffff'}
						<div class="legend-item">
							<span class="legend-color" style="background: {color}"></span>
							<span>{level}: {count}</span>
						</div>
					{/each}
				</div>
			</div>

			<!-- Top Sources -->
			<div class="viz-card">
				<h4>TOP 5 SOURCES</h4>
				<div class="bar-chart">
					{#each filteredSources.slice(0, 5) as [source, frequency]}
						{@const maxFreq = filteredSources[0]?.[1] || 1}
						{@const threat = getThreatLevel(frequency)}
						<div class="bar-item">
							<div class="bar-label">{source}</div>
							<div class="bar-container">
								<div class="bar-fill" 
									style="width: {(frequency/maxFreq)*100}%; background: {threat.color}">
								</div>
								<span class="bar-value">{frequency}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Coverage Matrix -->
			<div class="viz-card">
				<h4>COVERAGE MATRIX</h4>
				<div class="matrix-grid">
					{#each paginatedSources.slice(0, 9) as [source, frequency]}
						{@const threat = getThreatLevel(frequency)}
						<div class="matrix-cell" style="background: {threat.color}20; border-color: {threat.color}">
							<div class="cell-value">{getPercentage(frequency)}%</div>
							<div class="cell-label">{source.substring(0, 8)}</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.dashboard-container {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
		color: #fff;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
	}

	.header-section {
		background: rgba(0, 0, 0, 0.6);
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		padding: 1rem 1.5rem;
		backdrop-filter: blur(10px);
	}

	.header-content {
		max-width: 100%;
	}

	.title-block h1 {
		margin: 0;
		font-size: 1.5rem;
		color: #00ffff;
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}

	.title-block p {
		margin: 0.2rem 0 0 0;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.metrics-row {
		display: flex;
		gap: 1rem;
		margin-top: 1rem;
	}

	.metric-card {
		flex: 1;
		background: rgba(0, 255, 255, 0.05);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 8px;
		padding: 0.8rem;
		text-align: center;
	}

	.metric-card.critical {
		background: rgba(255, 0, 255, 0.05);
		border-color: rgba(255, 0, 255, 0.3);
	}

	.metric-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 10px currentColor;
	}

	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.3rem;
		letter-spacing: 0.05em;
	}

	.main-content {
		flex: 1;
		display: flex;
		gap: 1rem;
		padding: 1rem;
		overflow: hidden;
		min-height: 0;
	}

	.table-panel {
		flex: 2;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(0, 255, 255, 0.2);
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
	}

	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		border-bottom: 1px solid rgba(0, 255, 255, 0.2);
	}

	.panel-header h3 {
		margin: 0;
		font-size: 0.9rem;
		color: #00ffff;
		letter-spacing: 0.05em;
	}

	.search-bar {
		width: 300px;
	}

	.search-input {
		width: 100%;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 4px;
		padding: 0.5rem;
		color: #fff;
		font-size: 0.8rem;
	}

	.search-input:focus {
		outline: none;
		border-color: #00ffff;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
	}

	.table-container {
		flex: 1;
		overflow: auto;
		padding: 0.5rem;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.8rem;
	}

	.data-table th {
		background: rgba(0, 255, 255, 0.1);
		color: #00ffff;
		padding: 0.8rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.data-table td {
		padding: 0.6rem 0.8rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.8);
	}

	.data-table tr:hover {
		background: rgba(0, 255, 255, 0.05);
	}

	.source-cell .cell-content {
		display: flex;
		align-items: center;
		gap: 0.5rem;
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
		gap: 0.5rem;
	}

	.coverage-bar {
		flex: 1;
		height: 6px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 3px;
		overflow: hidden;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.3s ease;
	}

	.coverage-text {
		font-size: 0.7rem;
		min-width: 45px;
		text-align: right;
	}

	.threat-badge {
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		font-size: 0.7rem;
		font-weight: 600;
	}

	.threat-badge.crit {
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
	}

	.threat-badge.high {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.threat-badge.med {
		background: rgba(255, 170, 0, 0.2);
		color: #ffaa00;
		border: 1px solid #ffaa00;
	}

	.threat-badge.low {
		background: rgba(0, 255, 255, 0.2);
		color: #00ffff;
		border: 1px solid #00ffff;
	}

	.drill-btn {
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid #00ffff;
		color: #00ffff;
		padding: 0.3rem 0.8rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.7rem;
		transition: all 0.3s ease;
	}

	.drill-btn:hover {
		background: rgba(0, 255, 255, 0.2);
		transform: translateX(2px);
	}

	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		border-top: 1px solid rgba(0, 255, 255, 0.2);
	}

	.pagination button {
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid #00ffff;
		color: #00ffff;
		padding: 0.5rem 1rem;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.pagination button:hover:not(:disabled) {
		background: rgba(0, 255, 255, 0.2);
	}

	.pagination button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.viz-card {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 8px;
		padding: 1rem;
	}

	.viz-card h4 {
		margin: 0 0 1rem 0;
		font-size: 0.8rem;
		color: #00ffff;
		letter-spacing: 0.05em;
	}

	.donut-chart {
		width: 100%;
		max-width: 200px;
		margin: 0 auto;
	}

	.legend {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-top: 1rem;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.7rem;
	}

	.legend-color {
		width: 12px;
		height: 12px;
		border-radius: 2px;
	}

	.bar-chart {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.bar-item {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.bar-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.bar-container {
		position: relative;
		height: 20px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		transition: width 0.3s ease;
	}

	.bar-value {
		position: absolute;
		right: 0.5rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.6rem;
		font-weight: 600;
	}

	.matrix-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.5rem;
	}

	.matrix-cell {
		aspect-ratio: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		border: 1px solid;
		border-radius: 4px;
		padding: 0.5rem;
	}

	.cell-value {
		font-size: 0.8rem;
		font-weight: 600;
	}

	.cell-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.2rem;
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
		border: 3px solid rgba(0, 255, 255, 0.2);
		border-top-color: #00ffff;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
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
		padding: 1rem;
		border-bottom: 1px solid rgba(255, 0, 255, 0.3);
		background: rgba(255, 0, 255, 0.05);
	}

	.drill-header h4 {
		margin: 0;
		color: #ff00ff;
		font-size: 1rem;
	}

	.close-btn {
		background: transparent;
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 30px;
		height: 30px;
		border-radius: 50%;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.3s ease;
	}

	.close-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: rotate(90deg);
	}

	.host-cell {
		font-family: monospace;
		color: #00ffff;
	}

	.status-badge {
		padding: 0.2rem 0.4rem;
		border-radius: 4px;
		font-size: 0.7rem;
		font-weight: 600;
	}

	.status-badge.active {
		background: rgba(0, 255, 133, 0.2);
		color: #00ff85;
		border: 1px solid #00ff85;
	}

	.status-badge.inactive {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	/* Responsive */
	@media (max-width: 1200px) {
		.main-content {
			flex-direction: column;
		}
		
		.viz-panel {
			flex-direction: row;
			overflow-x: auto;
		}
		
		.viz-card {
			min-width: 300px;
		}
	}

	@media (max-width: 768px) {
		.metrics-row {
			flex-wrap: wrap;
		}
		
		.metric-card {
			min-width: calc(50% - 0.5rem);
		}
		
		.search-bar {
			width: 100%;
		}
	}
</style>