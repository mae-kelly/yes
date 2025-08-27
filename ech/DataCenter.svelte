<!-- DataCenter.svelte - Enhanced with Perfect Screen Fit -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCenter = null;
	let centerDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 10;
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
		if (!maxCount) return { level: 'LOW', color: '#00ffff', intensity: 0.3 };
		let percentage = (count / maxCount) * 100;
		if (percentage >= 60) return { level: 'CRITICAL', color: '#ff00ff', intensity: 1.0 };
		if (percentage >= 40) return { level: 'HIGH', color: '#ff0066', intensity: 0.8 };
		if (percentage >= 20) return { level: 'MEDIUM', color: '#ffaa00', intensity: 0.6 };
		return { level: 'LOW', color: '#00ffff', intensity: 0.4 };
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
	<!-- Header Section -->
	<div class="header-section">
		<div class="header-content">
			<div class="title-block">
				<div class="hexagon-icon">⬡</div>
				<div class="title-text">
					<h1>FACILITY INTELLIGENCE</h1>
					<p>First Word Data Center Analysis</p>
				</div>
			</div>
			<div class="metrics-row">
				<div class="metric-card">
					<div class="metric-value">{filteredCenters.length}</div>
					<div class="metric-label">FACILITIES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Object.values(data.facility_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL ASSETS</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Math.round(Object.values(data.facility_intelligence || {}).reduce((a, b) => a + b, 0) / filteredCenters.length || 0)}</div>
					<div class="metric-label">AVG/CENTER</div>
				</div>
				<div class="metric-card critical">
					<div class="metric-value">{threatDistribution['CRITICAL'] || 0}</div>
					<div class="metric-label">CRITICAL</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content Area -->
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<h3>DATA CENTER ANALYSIS</h3>
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
					<p>Scanning facility network...</p>
				</div>
			{:else if selectedCenter}
				<!-- Drill-down View -->
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
								{#each centerDetails as host}
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
										<div class="cell-content">
											<span class="indicator" style="background: {getThreatLevel(count).color}"></span>
											<span>{center.toUpperCase()}</span>
										</div>
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
										<button class="drill-btn" on:click={() => drillDownCenter(center, count)}>
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
			{:else}
				<!-- Grid View -->
				<div class="grid-container">
					{#each paginatedCenters as [center, count]}
						<div class="grid-card" style="--card-color: {getThreatLevel(count).color}" on:click={() => drillDownCenter(center, count)}>
							<div class="card-header">
								<span class="card-icon">🏢</span>
								<span class="threat-indicator {getThreatLevel(count).level.toLowerCase()}">{getThreatLevel(count).level}</span>
							</div>
							<div class="card-body">
								<div class="center-name">{center.toUpperCase()}</div>
								<div class="center-count">{count.toLocaleString()}</div>
								<div class="progress-bar">
									<div class="progress-fill" style="width: {(count/maxCount)*100}%; background: {getThreatLevel(count).color}"></div>
								</div>
								<div class="card-percentage">{getPercentage(count)}%</div>
							</div>
						</div>
					{/each}
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
							<defs>
								<filter id="glow">
									<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
									<feMerge>
										<feMergeNode in="coloredBlur"/>
										<feMergeNode in="SourceGraphic"/>
									</feMerge>
								</filter>
							</defs>
							{#each Object.entries(threatDistribution) as [level, count], i}
								<circle
									cx="100"
									cy="100"
									r={60 - i * 10}
									fill="none"
									stroke={level === 'CRITICAL' ? '#ff00ff' : level === 'HIGH' ? '#ff0066' : level === 'MEDIUM' ? '#ffaa00' : '#00ffff'}
									stroke-width="15"
									stroke-dasharray={`${(count / filteredCenters.length) * 377} 377`}
									transform="rotate(-90 100 100)"
									opacity="0.8"
									filter="url(#glow)"
								/>
							{/each}
						{/if}
						<text x="100" y="100" text-anchor="middle" fill="white" font-size="28" font-weight="bold">
							{filteredCenters.length}
						</text>
						<text x="100" y="115" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="10">
							CENTERS
						</text>
					</svg>
				</div>
				<div class="legend">
					{#each Object.entries(threatDistribution) as [level, count]}
						<div class="legend-item">
							<span class="legend-color" style="background: {level === 'CRITICAL' ? '#ff00ff' : level === 'HIGH' ? '#ff0066' : level === 'MEDIUM' ? '#ffaa00' : '#00ffff'}"></span>
							<span>{level}: {count}</span>
						</div>
					{/each}
				</div>
			</div>

			<!-- Top Data Centers -->
			<div class="viz-card">
				<h4>TOP 5 FACILITIES</h4>
				<div class="bar-chart">
					{#each filteredCenters.slice(0, 5) as [center, count]}
						<div class="bar-item">
							<div class="bar-label">{center.toUpperCase()}</div>
							<div class="bar-container">
								<div class="bar-fill" style="width: {(count/maxCount)*100}%; background: linear-gradient(90deg, {getThreatLevel(count).color}, {getThreatLevel(count).color}80)">
									<div class="bar-shimmer"></div>
								</div>
								<span class="bar-value">{count.toLocaleString()}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Facility Matrix -->
			<div class="viz-card">
				<h4>FACILITY MATRIX</h4>
				<div class="matrix-grid">
					{#each paginatedCenters.slice(0, 9) as [center, count]}
						<div class="matrix-cell" style="background: {getThreatLevel(count).color}20; border-color: {getThreatLevel(count).color}">
							<div class="cell-value">{getPercentage(count)}%</div>
							<div class="cell-label">{center.substring(0, 8)}</div>
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
							<div class="node-label">{center.substring(0, 6).toUpperCase()}</div>
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
		border-bottom: 1px solid rgba(0, 150, 255, 0.3);
		padding: 0.8rem 1rem;
		backdrop-filter: blur(10px);
		flex-shrink: 0;
	}

	.header-content {
		max-width: 100%;
	}

	.title-block {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		margin-bottom: 0.6rem;
	}

	.hexagon-icon {
		font-size: 1.8rem;
		color: #0096ff;
		text-shadow: 0 0 15px #0096ff;
		animation: hexRotate 8s linear infinite;
	}

	@keyframes hexRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.title-text h1 {
		margin: 0;
		font-size: 1.2rem;
		color: #0096ff;
		text-shadow: 0 0 10px rgba(0, 150, 255, 0.5);
		letter-spacing: 0.1em;
	}

	.title-text p {
		margin: 0.2rem 0 0 0;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.metrics-row {
		display: flex;
		gap: 0.8rem;
	}

	.metric-card {
		flex: 1;
		background: rgba(0, 150, 255, 0.05);
		border: 1px solid rgba(0, 150, 255, 0.3);
		border-radius: 6px;
		padding: 0.5rem;
		text-align: center;
		transition: all 0.3s ease;
	}

	.metric-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 150, 255, 0.2);
	}

	.metric-card.critical {
		background: rgba(255, 0, 255, 0.05);
		border-color: rgba(255, 0, 255, 0.3);
	}

	.metric-value {
		font-size: 1.3rem;
		font-weight: 700;
		color: #0096ff;
		text-shadow: 0 0 10px currentColor;
	}

	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.2rem;
		letter-spacing: 0.05em;
	}

	.main-content {
		flex: 1;
		display: flex;
		gap: 0.8rem;
		padding: 0.8rem;
		overflow: hidden;
		min-height: 0;
	}

	.table-panel {
		flex: 2;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(0, 150, 255, 0.2);
		border-radius: 8px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		overflow-y: auto;
		min-width: 320px;
	}

	.panel-header {
		padding: 0.8rem;
		border-bottom: 1px solid rgba(0, 150, 255, 0.2);
		background: rgba(0, 0, 0, 0.3);
	}

	.panel-header h3 {
		margin: 0 0 0.5rem 0;
		font-size: 0.85rem;
		color: #0096ff;
		letter-spacing: 0.05em;
	}

	.controls {
		display: flex;
		gap: 0.8rem;
		align-items: center;
	}

	.search-input {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 150, 255, 0.3);
		border-radius: 4px;
		padding: 0.4rem 0.8rem;
		color: #fff;
		font-size: 0.75rem;
	}

	.search-input:focus {
		outline: none;
		border-color: #0096ff;
		box-shadow: 0 0 10px rgba(0, 150, 255, 0.3);
	}

	.view-toggle {
		display: flex;
		gap: 0.2rem;
	}

	.toggle-btn {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 150, 255, 0.3);
		color: rgba(255, 255, 255, 0.7);
		padding: 0.3rem 0.6rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.65rem;
		transition: all 0.3s ease;
	}

	.toggle-btn.active {
		background: rgba(0, 150, 255, 0.1);
		border-color: #0096ff;
		color: #0096ff;
	}

	.table-container {
		flex: 1;
		overflow: auto;
		padding: 0.5rem;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.75rem;
	}

	.data-table th {
		background: rgba(0, 150, 255, 0.1);
		color: #0096ff;
		padding: 0.6rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.data-table td {
		padding: 0.5rem 0.6rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.8);
	}

	.data-table tr:hover {
		background: rgba(0, 150, 255, 0.05);
	}

	.center-cell .cell-content {
		display: flex;
		align-items: center;
		gap: 0.5rem;
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
		gap: 0.5rem;
	}

	.coverage-bar {
		flex: 1;
		height: 6px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 3px;
		overflow: hidden;
		min-width: 60px;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.5s ease;
		position: relative;
		box-shadow: 0 0 10px currentColor;
	}

	.coverage-text {
		font-size: 0.65rem;
		min-width: 45px;
		text-align: right;
	}

	.threat-badge {
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		font-size: 0.65rem;
		font-weight: 600;
	}

	.threat-badge.critical {
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
	}

	.threat-badge.high {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.threat-badge.medium {
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
		background: rgba(0, 150, 255, 0.1);
		border: 1px solid #0096ff;
		color: #0096ff;
		padding: 0.25rem 0.6rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.65rem;
		transition: all 0.3s ease;
	}

	.drill-btn:hover {
		background: rgba(0, 150, 255, 0.2);
		transform: translateX(2px);
		box-shadow: 0 0 10px rgba(0, 150, 255, 0.3);
	}

	.grid-container {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 0.8rem;
		padding: 0.8rem;
		overflow-y: auto;
	}

	.grid-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid var(--card-color);
		border-radius: 8px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.grid-card:hover {
		transform: translateY(-3px);
		box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 20px var(--card-color);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.6rem;
	}

	.card-icon {
		font-size: 1.2rem;
	}

	.threat-indicator {
		font-size: 0.6rem;
		padding: 0.15rem 0.4rem;
		border-radius: 3px;
		font-weight: 600;
	}

	.threat-indicator.critical {
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
	}

	.threat-indicator.high {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.threat-indicator.medium {
		background: rgba(255, 170, 0, 0.2);
		color: #ffaa00;
		border: 1px solid #ffaa00;
	}

	.threat-indicator.low {
		background: rgba(0, 255, 255, 0.2);
		color: #00ffff;
		border: 1px solid #00ffff;
	}

	.card-body {
		text-align: center;
	}

	.center-name {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.9);
		margin-bottom: 0.4rem;
		font-weight: 600;
	}

	.center-count {
		font-size: 1.3rem;
		font-weight: 700;
		color: var(--card-color);
		text-shadow: 0 0 10px var(--card-color);
		margin-bottom: 0.4rem;
	}

	.progress-bar {
		width: 100%;
		height: 4px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 2px;
		overflow: hidden;
		margin-bottom: 0.3rem;
	}

	.progress-fill {
		height: 100%;
		transition: width 0.5s ease;
	}

	.card-percentage {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		padding: 0.8rem;
		border-top: 1px solid rgba(0, 150, 255, 0.2);
		background: rgba(0, 0, 0, 0.3);
	}

	.pagination button {
		background: rgba(0, 150, 255, 0.1);
		border: 1px solid #0096ff;
		color: #0096ff;
		padding: 0.4rem 0.8rem;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.3s ease;
		font-size: 0.7rem;
	}

	.pagination button:hover:not(:disabled) {
		background: rgba(0, 150, 255, 0.2);
		transform: scale(1.05);
	}

	.pagination button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.pagination span {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.viz-card {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(0, 150, 255, 0.2);
		border-radius: 8px;
		padding: 0.8rem;
	}

	.viz-card h4 {
		margin: 0 0 0.8rem 0;
		font-size: 0.7rem;
		color: #0096ff;
		letter-spacing: 0.05em;
		text-align: center;
	}

	.donut-chart {
		width: 100%;
		max-width: 200px;
		margin: 0 auto;
	}

	.legend {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		margin-top: 0.8rem;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.legend-color {
		width: 12px;
		height: 12px;
		border-radius: 2px;
		flex-shrink: 0;
	}

	.bar-chart {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.bar-item {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.bar-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.bar-container {
		position: relative;
		height: 18px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
		position: relative;
	}

	.bar-shimmer {
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
		animation: shimmer 2s infinite;
	}

	@keyframes shimmer {
		to { left: 100%; }
	}

	.bar-value {
		position: absolute;
		right: 0.4rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.6rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
	}

	.matrix-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.4rem;
	}

	.matrix-cell {
		aspect-ratio: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		border: 1px solid;
		border-radius: 4px;
		padding: 0.3rem;
	}

	.cell-value {
		font-size: 0.7rem;
		font-weight: 600;
		color: #fff;
	}

	.cell-label {
		font-size: 0.5rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.1rem;
	}

	.network-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.8rem;
		padding: 0.5rem;
	}

	.network-node {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.3rem;
	}

	.node-core {
		position: relative;
		width: 50px;
		height: 50px;
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
		100% { transform: scale(1.5); opacity: 0; }
	}

	.node-value {
		font-size: 0.8rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 10px var(--node-color);
	}

	.node-label {
		font-size: 0.55rem;
		color: rgba(255, 255, 255, 0.6);
		text-align: center;
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
		border: 3px solid rgba(0, 150, 255, 0.2);
		border-top-color: #0096ff;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
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
		padding: 0.8rem;
		border-bottom: 1px solid rgba(255, 0, 102, 0.3);
		background: rgba(255, 0, 102, 0.05);
	}

	.drill-header h4 {
		margin: 0;
		color: #ff0066;
		font-size: 0.9rem;
	}

	.close-btn {
		background: transparent;
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.3s ease;
		font-size: 0.8rem;
	}

	.close-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: rotate(90deg);
	}

	.host-cell {
		font-family: monospace;
		color: #00ffff;
		font-size: 0.7rem;
	}

	.status-badge {
		padding: 0.15rem 0.3rem;
		border-radius: 3px;
		font-size: 0.6rem;
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

	@media (max-width: 1200px) {
		.main-content {
			flex-direction: column;
		}
		
		.viz-panel {
			flex-direction: row;
			overflow-x: auto;
			min-width: auto;
		}
		
		.viz-card {
			min-width: 280px;
		}
	}

	@media (max-width: 768px) {
		.metrics-row {
			flex-wrap: wrap;
		}
		
		.metric-card {
			min-width: calc(50% - 0.4rem);
		}
		
		.controls {
			flex-direction: column;
		}
		
		.grid-container {
			grid-template-columns: 1fr;
		}
	}
</style>