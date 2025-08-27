<!-- InfrastructureType.svelte - Enhanced with Perfect Screen Fit -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedInfra = null;
	let infraDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 12;
	let viewMode = 'table';

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/infrastructure_type');
			let result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			console.error('Infrastructure type error:', err);
			loading = false;
		}
	});

	$: sortedInfra = data.infrastructure_matrix ? 
		Object.entries(data.infrastructure_matrix)
			.filter(([infra]) => infra.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: paginatedInfra = sortedInfra.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(sortedInfra.length / itemsPerPage);

	$: maxCount = sortedInfra.length > 0 ? Math.max(...sortedInfra.map(([,count]) => count)) : 1;

	function getThreatLevel(count) {
		if (!maxCount) return { level: 'LOW', color: '#00ffff', intensity: 0.3 };
		let percentage = (count / maxCount) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#ff00ff', intensity: 1.0 };
		if (percentage >= 50) return { level: 'HIGH', color: '#ff0066', intensity: 0.8 };
		if (percentage >= 25) return { level: 'MEDIUM', color: '#ffaa00', intensity: 0.6 };
		return { level: 'LOW', color: '#00ffff', intensity: 0.4 };
	}

	function getPercentage(count) {
		let total = Object.values(data.infrastructure_matrix || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
	}

	async function drillDownInfra(infra, count) {
		selectedInfra = { infra, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/infrastructure_type/breakdown?type=${encodeURIComponent(infra)}`);
			let result = await response.json();
			infraDetails = result.details || [];
			loading = false;
		} catch (err) {
			console.error('Infrastructure drill-down error:', err);
			infraDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedInfra = null;
		infraDetails = [];
	}

	$: threatDistribution = sortedInfra.reduce((acc, [_, count]) => {
		let level = getThreatLevel(count).level;
		acc[level] = (acc[level] || 0) + 1;
		return acc;
	}, {});

	$: categoryBreakdown = sortedInfra.reduce((acc, [infra, count]) => {
		let category = 'Other';
		let infraLower = infra.toLowerCase();
		if (infraLower.includes('cloud')) category = 'Cloud';
		else if (infraLower.includes('on-prem') || infraLower.includes('server')) category = 'On-Premise';
		else if (infraLower.includes('saas')) category = 'SaaS';
		else if (infraLower.includes('api')) category = 'API';
		
		acc[category] = (acc[category] || 0) + count;
		return acc;
	}, {});
</script>

<div class="infra-dashboard">
	<!-- Header Section -->
	<div class="header-section">
		<div class="header-content">
			<div class="title-block">
				<h1><span class="icon">⬢</span> INFRASTRUCTURE MATRIX</h1>
				<p>Pipe-Separated Classification Analysis</p>
			</div>
			<div class="metrics-row">
				<div class="metric-card">
					<div class="metric-value">{sortedInfra.length}</div>
					<div class="metric-label">TYPES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Object.values(data.infrastructure_matrix || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL ASSETS</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Object.keys(categoryBreakdown).length}</div>
					<div class="metric-label">CATEGORIES</div>
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
		<!-- Left Panel: Table & Grid Toggle -->
		<div class="table-panel">
			<div class="panel-header">
				<h3>INFRASTRUCTURE ANALYSIS</h3>
				<div class="controls">
					<div class="search-bar">
						<input 
							type="text" 
							bind:value={searchTerm}
							placeholder="Search infrastructure..."
							class="search-input"
						/>
					</div>
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
			
			{#if loading && !selectedInfra}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>Analyzing infrastructure...</p>
				</div>
			{:else if selectedInfra}
				<!-- Drill-down View -->
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedInfra.infra}</h4>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>ATTRIBUTE</th>
									<th>VALUE</th>
									<th>STATUS</th>
								</tr>
							</thead>
							<tbody>
								<tr>
									<td>Total Assets</td>
									<td class="value-cell">{selectedInfra.count.toLocaleString()}</td>
									<td><span class="status-badge active">ACTIVE</span></td>
								</tr>
								<tr>
									<td>Coverage</td>
									<td class="value-cell">{getPercentage(selectedInfra.count)}%</td>
									<td><span class="status-badge {getThreatLevel(selectedInfra.count).level.toLowerCase()}">{getThreatLevel(selectedInfra.count).level}</span></td>
								</tr>
								<tr>
									<td>Category</td>
									<td class="value-cell">
										{selectedInfra.infra.toLowerCase().includes('cloud') ? 'Cloud' :
										 selectedInfra.infra.toLowerCase().includes('on-prem') ? 'On-Premise' :
										 selectedInfra.infra.toLowerCase().includes('saas') ? 'SaaS' : 'Other'}
									</td>
									<td><span class="status-badge active">CLASSIFIED</span></td>
								</tr>
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
								<th>INFRASTRUCTURE</th>
								<th>COUNT</th>
								<th>COVERAGE</th>
								<th>THREAT</th>
								<th>ACTION</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedInfra as [infra, count]}
								{@const threat = getThreatLevel(count)}
								<tr>
									<td class="infra-cell">
										<div class="cell-content">
											<span class="indicator" style="background: {threat.color}"></span>
											<span>{infra}</span>
										</div>
									</td>
									<td class="center">{count.toLocaleString()}</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {(count/maxCount)*100}%; background: {threat.color}"></div>
											</div>
											<span class="coverage-text">{getPercentage(count)}%</span>
										</div>
									</td>
									<td class="center">
										<span class="threat-badge {threat.level.toLowerCase()}">{threat.level}</span>
									</td>
									<td class="center">
										<button class="drill-btn" on:click={() => drillDownInfra(infra, count)}>
											DRILL →
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<!-- Grid View -->
				<div class="grid-container">
					{#each paginatedInfra as [infra, count]}
						{@const threat = getThreatLevel(count)}
						<div class="grid-card" style="--card-color: {threat.color}" on:click={() => drillDownInfra(infra, count)}>
							<div class="card-header">
								<span class="card-icon">⬢</span>
								<span class="threat-indicator {threat.level.toLowerCase()}">{threat.level}</span>
							</div>
							<div class="card-body">
								<div class="infra-name">{infra}</div>
								<div class="infra-count">{count.toLocaleString()}</div>
								<div class="progress-bar">
									<div class="progress-fill" style="width: {(count/maxCount)*100}%; background: {threat.color}"></div>
								</div>
								<div class="card-percentage">{getPercentage(count)}%</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
			
			<!-- Pagination -->
			{#if !selectedInfra}
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
			<!-- Category Distribution -->
			<div class="viz-card">
				<h4>CATEGORY DISTRIBUTION</h4>
				<div class="donut-chart">
					<svg viewBox="0 0 200 200">
						{#if Object.keys(categoryBreakdown).length > 0}
							{@const total = Object.values(categoryBreakdown).reduce((a, b) => a + b, 0)}
							{@const radius = 60}
							{@const circumference = 2 * Math.PI * radius}
							{#each Object.entries(categoryBreakdown) as [category, count], i}
								{@const percentage = (count / total) * 100}
								{@const strokeDasharray = (percentage / 100) * circumference}
								{@const rotation = Object.entries(categoryBreakdown)
									.slice(0, i)
									.reduce((acc, [_, c]) => acc + (c / total) * 360, -90)}
								{@const color = category === 'Cloud' ? '#00ffff' : 
									category === 'On-Premise' ? '#ff00ff' : 
									category === 'SaaS' ? '#ffaa00' : '#0096ff'}
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
							{Object.keys(categoryBreakdown).length}
						</text>
						<text x="100" y="115" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="10">
							CATEGORIES
						</text>
					</svg>
				</div>
				<div class="legend">
					{#each Object.entries(categoryBreakdown) as [category, count]}
						{@const color = category === 'Cloud' ? '#00ffff' : 
							category === 'On-Premise' ? '#ff00ff' : 
							category === 'SaaS' ? '#ffaa00' : '#0096ff'}
						<div class="legend-item">
							<span class="legend-color" style="background: {color}"></span>
							<span>{category}: {count.toLocaleString()}</span>
						</div>
					{/each}
				</div>
			</div>

			<!-- Top Infrastructure -->
			<div class="viz-card">
				<h4>TOP 5 INFRASTRUCTURE</h4>
				<div class="bar-chart">
					{#each sortedInfra.slice(0, 5) as [infra, count]}
						{@const maxFreq = sortedInfra[0]?.[1] || 1}
						{@const threat = getThreatLevel(count)}
						<div class="bar-item">
							<div class="bar-label">{infra.substring(0, 20)}{infra.length > 20 ? '...' : ''}</div>
							<div class="bar-container">
								<div class="bar-fill" 
									style="width: {(count/maxFreq)*100}%; background: linear-gradient(90deg, {threat.color}, {threat.color}80)">
								</div>
								<span class="bar-value">{count.toLocaleString()}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Threat Matrix -->
			<div class="viz-card">
				<h4>THREAT MATRIX</h4>
				<div class="threat-grid">
					{#each Object.entries(threatDistribution) as [level, count]}
						{@const color = level === 'CRITICAL' ? '#ff00ff' : 
							level === 'HIGH' ? '#ff0066' : 
							level === 'MEDIUM' ? '#ffaa00' : '#00ffff'}
						<div class="threat-cell" style="--threat-color: {color}">
							<div class="threat-level">{level}</div>
							<div class="threat-count">{count}</div>
							<div class="threat-bar">
								<div class="threat-fill" style="width: {(count/sortedInfra.length)*100}%; background: {color}"></div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.infra-dashboard {
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
		padding: 0.8rem 1.2rem;
		backdrop-filter: blur(10px);
		flex-shrink: 0;
	}

	.header-content {
		max-width: 100%;
	}

	.title-block h1 {
		margin: 0;
		font-size: 1.3rem;
		color: #00ffff;
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.1em;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.icon {
		font-size: 1.5rem;
		animation: iconRotate 8s linear infinite;
	}

	@keyframes iconRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.title-block p {
		margin: 0.2rem 0 0 0;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.metrics-row {
		display: flex;
		gap: 0.8rem;
		margin-top: 0.8rem;
	}

	.metric-card {
		flex: 1;
		background: rgba(0, 255, 255, 0.05);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 6px;
		padding: 0.6rem;
		text-align: center;
		transition: all 0.3s ease;
	}

	.metric-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 255, 255, 0.2);
	}

	.metric-card.critical {
		background: rgba(255, 0, 255, 0.05);
		border-color: rgba(255, 0, 255, 0.3);
	}

	.metric-value {
		font-size: 1.3rem;
		font-weight: 700;
		color: #00ffff;
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
		gap: 0.8rem;
		overflow-y: auto;
		min-width: 320px;
	}

	.panel-header {
		padding: 0.8rem;
		border-bottom: 1px solid rgba(0, 255, 255, 0.2);
		background: rgba(0, 0, 0, 0.3);
	}

	.panel-header h3 {
		margin: 0 0 0.5rem 0;
		font-size: 0.85rem;
		color: #00ffff;
		letter-spacing: 0.05em;
	}

	.controls {
		display: flex;
		gap: 0.8rem;
		align-items: center;
	}

	.search-bar {
		flex: 1;
	}

	.search-input {
		width: 100%;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 4px;
		padding: 0.4rem 0.8rem;
		color: #fff;
		font-size: 0.75rem;
	}

	.search-input:focus {
		outline: none;
		border-color: #00ffff;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
	}

	.view-toggle {
		display: flex;
		gap: 0.2rem;
	}

	.toggle-btn {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 255, 0.3);
		color: rgba(255, 255, 255, 0.7);
		padding: 0.3rem 0.8rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.7rem;
		transition: all 0.3s ease;
	}

	.toggle-btn.active {
		background: rgba(0, 255, 255, 0.1);
		border-color: #00ffff;
		color: #00ffff;
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
		background: rgba(0, 255, 255, 0.1);
		color: #00ffff;
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
		background: rgba(0, 255, 255, 0.05);
	}

	.infra-cell .cell-content {
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
	}

	.threat-badge {
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		font-size: 0.65rem;
		font-weight: 600;
		text-transform: uppercase;
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
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid #00ffff;
		color: #00ffff;
		padding: 0.25rem 0.6rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.65rem;
		transition: all 0.3s ease;
	}

	.drill-btn:hover {
		background: rgba(0, 255, 255, 0.2);
		transform: translateX(2px);
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
	}

	.grid-container {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 0.8rem;
		padding: 0.8rem;
		overflow-y: auto;
		flex: 1;
	}

	.grid-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid var(--card-color);
		border-radius: 8px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		animation: cardEntrance 0.4s ease-out;
	}

	.grid-card:hover {
		transform: translateY(-3px);
		box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5), 0 0 20px var(--card-color);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.8rem;
	}

	.card-icon {
		font-size: 1.2rem;
		color: var(--card-color);
		animation: iconSpin 4s linear infinite;
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

	.infra-name {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.9);
		margin-bottom: 0.5rem;
		font-weight: 600;
	}

	.infra-count {
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--card-color);
		text-shadow: 0 0 10px var(--card-color);
		margin-bottom: 0.5rem;
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
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		padding: 0.8rem;
		border-top: 1px solid rgba(0, 255, 255, 0.2);
		background: rgba(0, 0, 0, 0.3);
	}

	.pagination button {
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid #00ffff;
		color: #00ffff;
		padding: 0.4rem 0.8rem;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.3s ease;
		font-size: 0.7rem;
	}

	.pagination button:hover:not(:disabled) {
		background: rgba(0, 255, 255, 0.2);
		transform: scale(1.05);
	}

	.pagination button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.pagination span {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.viz-card {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 8px;
		padding: 0.8rem;
		animation: vizEntrance 0.6s ease-out;
	}

	.viz-card h4 {
		margin: 0 0 0.8rem 0;
		font-size: 0.75rem;
		color: #00ffff;
		letter-spacing: 0.05em;
		text-align: center;
	}

	.donut-chart {
		width: 100%;
		max-width: 180px;
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
		width: 10px;
		height: 10px;
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
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.bar-container {
		position: relative;
		height: 18px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
		overflow: hidden;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
		position: relative;
		overflow: hidden;
	}

	.bar-fill::after {
		content: '';
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
		right: 0.3rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.6rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
	}

	.threat-grid {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.threat-cell {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		position: relative;
		overflow: hidden;
	}

	.threat-cell::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		width: 3px;
		height: 100%;
		background: var(--threat-color);
	}

	.threat-level {
		font-size: 0.65rem;
		font-weight: 600;
		color: var(--threat-color);
		min-width: 60px;
	}

	.threat-count {
		font-size: 0.9rem;
		font-weight: 700;
		color: #fff;
		min-width: 30px;
		text-align: center;
	}

	.threat-bar {
		flex: 1;
		height: 4px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 2px;
		overflow: hidden;
	}

	.threat-fill {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 8px currentColor;
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

	@keyframes cardEntrance {
		from {
			opacity: 0;
			transform: translateY(20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	@keyframes vizEntrance {
		from {
			opacity: 0;
			transform: translateX(20px);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}

	@keyframes iconSpin {
		from { transform: rotate(0deg); }
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
		padding: 0.8rem;
		border-bottom: 1px solid rgba(255, 0, 255, 0.3);
		background: rgba(255, 0, 255, 0.05);
	}

	.drill-header h4 {
		margin: 0;
		color: #ff00ff;
		font-size: 0.9rem;
		text-transform: uppercase;
	}

	.close-btn {
		background: transparent;
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 28px;
		height: 28px;
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

	.value-cell {
		font-family: monospace;
		color: #00ffff;
		font-weight: 600;
	}

	.status-badge {
		padding: 0.15rem 0.4rem;
		border-radius: 3px;
		font-size: 0.65rem;
		font-weight: 600;
		text-transform: uppercase;
	}

	.status-badge.active {
		background: rgba(0, 255, 133, 0.2);
		color: #00ff85;
		border: 1px solid #00ff85;
	}

	.status-badge.critical {
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
	}

	.status-badge.high {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.status-badge.medium {
		background: rgba(255, 170, 0, 0.2);
		color: #ffaa00;
		border: 1px solid #ffaa00;
	}

	.status-badge.low {
		background: rgba(0, 255, 255, 0.2);
		color: #00ffff;
		border: 1px solid #00ffff;
	}

	/* Responsive adjustments */
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
		
		.search-bar {
			width: 100%;
		}
		
		.grid-container {
			grid-template-columns: 1fr;
		}
	}
</style>