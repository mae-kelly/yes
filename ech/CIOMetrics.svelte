<!-- CIOMetrics.svelte - Enhanced Executive Analysis -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCio = null;
	let cioDetails = [];
	let searchTerm = '';

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
	
	$: maxAssets = sortedCios.length > 0 ? Math.max(...sortedCios.map(([,count]) => count)) : 1;

	function getExecutiveLevel(count) {
		if (!maxAssets) return { level: 'ANALYST', color: '#b8a678', icon: '▪' };
		let percentage = (count / maxAssets) * 100;
		if (percentage >= 70) return { level: 'C-SUITE', color: '#ff0066', icon: '◆' };
		if (percentage >= 40) return { level: 'VP', color: '#ff9900', icon: '▲' };
		if (percentage >= 20) return { level: 'DIRECTOR', color: '#ffcc00', icon: '●' };
		return { level: 'ANALYST', color: '#0a4f3c', icon: '▪' };
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
</script>

<div class="dashboard-container">
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<h3 class="panel-title">
					<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
					</svg>
					Executive Leadership Analysis
				</h3>
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
					<p>SCANNING EXECUTIVE DATA...</p>
				</div>
			{:else if selectedCio}
				<div class="drill-view">
					<div class="drill-header">
						<div class="exec-profile">
							<span class="profile-icon" style="color: {getExecutiveLevel(selectedCio.count).color}">
								{getExecutiveLevel(selectedCio.count).icon}
							</span>
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
								{#each cioDetails as host}
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
				<!-- Main Table View -->
				<div class="table-scroll-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>EXECUTIVE</th>
								<th>LEVEL</th>
								<th>ASSETS</th>
								<th>COVERAGE</th>
							</tr>
						</thead>
						<tbody>
							{#each sortedCios as [cio, count]}
								{@const exec = getExecutiveLevel(count)}
								<tr on:click={() => drillDownCio(cio, count)}>
									<td class="exec-cell">
										<span class="exec-icon" style="color: {exec.color}">{exec.icon}</span>
										<span class="exec-name">{cio.substring(0, 30).toUpperCase()}</span>
									</td>
									<td class="center">
										<span class="level-badge" style="color: {exec.color}; border-color: {exec.color}">{exec.level}</span>
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
					<div class="metric-value">{sortedCios.length}</div>
					<div class="metric-label">EXECUTIVES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL ASSETS</div>
				</div>
			</div>

			<!-- Executive Hierarchy -->
			<div class="viz-card">
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
					</svg>
					ORGANIZATIONAL HIERARCHY
				</h4>
				<div class="hierarchy-chart">
					{#each Object.entries(executiveDistribution) as [level, count]}
						{@const levelData = level === 'C-SUITE' ? {color: '#ff0066', icon: '◆'} :
							level === 'VP' ? {color: '#ff9900', icon: '▲'} :
							level === 'DIRECTOR' ? {color: '#ffcc00', icon: '●'} :
							{color: '#0a4f3c', icon: '▪'}}
						<div class="hierarchy-level">
							<div class="level-header">
								<span class="level-icon" style="color: {levelData.color}">{levelData.icon}</span>
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
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>
					</svg>
					TOP EXECUTIVES
				</h4>
				<div class="exec-list">
					{#each sortedCios.slice(0, 6) as [cio, count]}
						{@const exec = getExecutiveLevel(count)}
						<div class="exec-item">
							<div class="exec-rank">
								<span style="color: {exec.color}">{exec.icon}</span>
							</div>
							<div class="exec-details">
								<div class="exec-item-name">{cio.substring(0, 20).toUpperCase()}</div>
								<div class="exec-bar-container">
									<div class="exec-bar" style="width: {(count/maxAssets)*100}%; background: {exec.color}"></div>
								</div>
								<div class="exec-stats">
									<span>{count.toLocaleString()} assets</span>
									<span class="separator">•</span>
									<span>{getPercentage(count)}%</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Portfolio Distribution -->
			<div class="viz-card">
				<h4>
					<svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
					</svg>
					ASSET DISTRIBUTION
				</h4>
				<div class="distribution-chart">
					<svg viewBox="0 0 200 200">
						{#if sortedCios.length > 0}
							{@const total = Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0)}
							{@const radius = 70}
							{@const circumference = 2 * Math.PI * radius}
							{#each sortedCios.slice(0, 5) as [cio, count], i}
								{@const percentage = (count / total) * 100}
								{@const strokeDasharray = (percentage / 100) * circumference}
								{@const rotation = sortedCios.slice(0, i)
									.reduce((acc, [_, c]) => acc + (c / total) * 360, -90)}
								{@const exec = getExecutiveLevel(count)}
								<circle
									cx="100"
									cy="100"
									r={radius}
									fill="none"
									stroke={exec.color}
									stroke-width="30"
									stroke-dasharray="{strokeDasharray} {circumference}"
									transform="rotate({rotation} 100 100)"
									opacity="0.8"
								/>
							{/each}
						{/if}
						<text x="100" y="95" text-anchor="middle" fill="#e0e0e0" font-size="24" font-weight="bold">
							{sortedCios.length}
						</text>
						<text x="100" y="115" text-anchor="middle" fill="#b8a678" font-size="12">
							EXECUTIVES
						</text>
					</svg>
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

	.exec-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.exec-icon {
		font-size: 1rem;
	}

	.exec-name {
		font-weight: 500;
		color: #e0e0e0;
	}

	.center {
		text-align: center;
	}

	.level-badge {
		padding: 0.25rem 0.5rem;
		border: 1px solid;
		border-radius: 4px;
		font-size: 0.7rem;
		font-weight: 600;
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

	.exec-profile {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.profile-icon {
		font-size: 1.5rem;
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

	.drill-stats {
		display: flex;
		gap: 2rem;
		padding: 1rem 1.5rem;
		background: rgba(0, 0, 0, 0.3);
		border-bottom: 1px solid #1a1a1a;
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		align-items: center;
	}

	.stat-value {
		font-size: 1.2rem;
		font-weight: 600;
		color: #0a4f3c;
	}

	.stat-label {
		font-size: 0.65rem;
		color: #b8a678;
		text-transform: uppercase;
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

	.hierarchy-chart {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.hierarchy-level {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.level-header {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		min-width: 90px;
	}

	.level-icon {
		font-size: 1rem;
	}

	.level-name {
		font-size: 0.65rem;
		color: #b8a678;
		font-weight: 500;
	}

	.level-bar-container {
		flex: 1;
		height: 6px;
		background: #1a1a1a;
		border-radius: 3px;
		overflow: hidden;
	}

	.level-bar {
		height: 100%;
		transition: width 0.3s ease;
	}

	.level-count {
		font-size: 0.65rem;
		color: #b8a678;
		min-width: 20px;
		text-align: right;
	}

	.exec-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.exec-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem;
		background: #0a0a0a;
		border-radius: 4px;
		transition: all 0.2s ease;
	}

	.exec-item:hover {
		background: rgba(10, 79, 60, 0.05);
	}

	.exec-rank {
		font-size: 1.2rem;
		width: 24px;
		text-align: center;
	}

	.exec-details {
		flex: 1;
	}

	.exec-item-name {
		font-size: 0.75rem;
		color: #e0e0e0;
		font-weight: 500;
		margin-bottom: 0.3rem;
	}

	.exec-bar-container {
		height: 4px;
		background: #1a1a1a;
		border-radius: 2px;
		overflow: hidden;
		margin-bottom: 0.3rem;
	}

	.exec-bar {
		height: 100%;
		transition: width 0.3s ease;
	}

	.exec-stats {
		font-size: 0.65rem;
		color: #b8a678;
	}

	.separator {
		margin: 0 0.3rem;
		color: #1a1a1a;
	}

	.distribution-chart {
		width: 100%;
		max-width: 200px;
		margin: 0 auto;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}
</style>