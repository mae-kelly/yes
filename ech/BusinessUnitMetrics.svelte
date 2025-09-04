<!-- BusinessUnitMetrics.svelte - Premium Business Division Analytics -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedBU = null;
	let buDetails = [];
	let searchTerm = '';
	let chartType = 'treemap'; // 'treemap' or 'hierarchy'

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
	
	$: maxCount = filteredBUs.length > 0 ? Math.max(...filteredBUs.map(([,c]) => c)) : 1;

	function getPercentage(count) {
		let total = Object.values(data.business_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
	}

	function getOperationalHealth(count) {
		const percentage = (count / maxCount) * 100;
		if (percentage >= 60) return { status: 'OPTIMAL', color: '#00E5FF', icon: '✓' };
		if (percentage >= 40) return { status: 'GOOD', color: '#00C853', icon: '●' };
		if (percentage >= 20) return { status: 'FAIR', color: '#FFA726', icon: '▲' };
		return { status: 'CRITICAL', color: '#FF1744', icon: '⚠' };
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
</script>

<div class="dashboard-container">
	<!-- Header with Controls -->
	<div class="header-section">
		<div class="header-left">
			<h2 class="main-title">
				<span class="title-icon">👥</span>
				BUSINESS DIVISION INTELLIGENCE
			</h2>
			<div class="subtitle">Organizational Asset Distribution</div>
		</div>
		
		<div class="header-center">
			<div class="search-wrapper">
				<svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<circle cx="11" cy="11" r="8"></circle>
					<path d="m21 21-4.35-4.35"></path>
				</svg>
				<input 
					type="text" 
					bind:value={searchTerm}
					placeholder="Search divisions..."
					class="search-input"
				/>
			</div>
		</div>
		
		<div class="header-right">
			<div class="view-selector">
				<button class="view-btn {chartType === 'treemap' ? 'active' : ''}" 
						on:click={() => chartType = 'treemap'}>
					Treemap
				</button>
				<button class="view-btn {chartType === 'hierarchy' ? 'active' : ''}" 
						on:click={() => chartType = 'hierarchy'}>
					Hierarchy
				</button>
			</div>
		</div>
	</div>

	<!-- Main Content Area -->
	<div class="content-area">
		<!-- Visualization Panel -->
		<div class="visualization-panel">
			{#if loading && !selectedBU}
				<div class="loading-state">
					<div class="org-loader">
						<div class="org-node"></div>
						<div class="org-node"></div>
						<div class="org-node"></div>
					</div>
					<p>Analyzing organizational structure...</p>
				</div>
			{:else if selectedBU}
				<div class="detail-view">
					<div class="detail-header">
						<div class="detail-info">
							<h3>{selectedBU.bu.toUpperCase()}</h3>
							<div class="detail-stats">
								<span class="stat-badge">{selectedBU.count.toLocaleString()} assets</span>
								<span class="stat-badge">{getPercentage(selectedBU.count)}% of total</span>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>×</button>
					</div>
					<div class="detail-table-wrapper">
						<table class="detail-table">
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
								{#each buDetails as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.region || 'Unknown'}</td>
										<td>{host.infrastructure_type || 'Unknown'}</td>
										<td>
											<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'success' : 'danger'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '✓' : '✗'}
											</span>
										</td>
										<td>
											<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'success' : 'warning'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? '✓' : '✗'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else if chartType === 'treemap'}
				<div class="treemap-container">
					{#each filteredBUs.slice(0, 12) as [bu, count]}
						{@const health = getOperationalHealth(count)}
						{@const percentage = getPercentage(count)}
						{@const size = (count / maxCount) * 100}
						<div class="treemap-item" 
							 style="flex: {size}; background: linear-gradient(135deg, {health.color}20, {health.color}10)"
							 on:click={() => drillDownBU(bu, count)}>
							<div class="treemap-content">
								<span class="treemap-icon" style="color: {health.color}">{health.icon}</span>
								<div class="treemap-name">{bu.substring(0, 25).toUpperCase()}</div>
								<div class="treemap-value" style="color: {health.color}">{count.toLocaleString()}</div>
								<div class="treemap-percent">{percentage}%</div>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="hierarchy-container">
					<div class="hierarchy-root">
						<div class="root-node">
							<span class="node-title">ORGANIZATION</span>
							<span class="node-count">{Object.values(data.business_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</span>
						</div>
					</div>
					<div class="hierarchy-branches">
						{#each filteredBUs.slice(0, 8) as [bu, count]}
							{@const health = getOperationalHealth(count)}
							<div class="branch" on:click={() => drillDownBU(bu, count)}>
								<div class="branch-line"></div>
								<div class="branch-node" style="border-color: {health.color}; background: {health.color}10">
									<span class="node-icon" style="color: {health.color}">{health.icon}</span>
									<span class="node-name">{bu.substring(0, 20).toUpperCase()}</span>
									<span class="node-value" style="color: {health.color}">{count.toLocaleString()}</span>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>

		<!-- Metrics Panel -->
		<div class="metrics-panel">
			<!-- Summary Cards -->
			<div class="summary-cards">
				<div class="summary-card">
					<div class="card-icon">👥</div>
					<div class="card-content">
						<div class="card-value">{filteredBUs.length}</div>
						<div class="card-label">DIVISIONS</div>
					</div>
				</div>
				<div class="summary-card">
					<div class="card-icon">💻</div>
					<div class="card-content">
						<div class="card-value">
							{Object.values(data.business_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}
						</div>
						<div class="card-label">TOTAL ASSETS</div>
					</div>
				</div>
			</div>

			<!-- Top Divisions List -->
			<div class="top-divisions">
				<h3 class="section-title">TOP DIVISIONS</h3>
				<div class="divisions-list">
					{#each filteredBUs.slice(0, 10) as [bu, count], i}
						{@const health = getOperationalHealth(count)}
						<div class="division-item" on:click={() => drillDownBU(bu, count)}>
							<span class="division-rank" style="color: {health.color}">#{i + 1}</span>
							<div class="division-info">
								<div class="division-name">{bu.substring(0, 30).toUpperCase()}</div>
								<div class="division-bar">
									<div class="bar-fill" style="width: {(count/maxCount)*100}%; background: {health.color}"></div>
								</div>
							</div>
							<div class="division-stats">
								<span class="asset-count" style="color: {health.color}">{count.toLocaleString()}</span>
								<span class="asset-percent">{getPercentage(count)}%</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Health Distribution -->
			<div class="health-distribution">
				<h3 class="section-title">HEALTH DISTRIBUTION</h3>
				<div class="health-chart">
					{@const healthGroups = filteredBUs.reduce((acc, [bu, count]) => {
						const health = getOperationalHealth(count).status;
						acc[health] = (acc[health] || 0) + 1;
						return acc;
					}, {})}
					{#each Object.entries(healthGroups) as [status, count]}
						{@const color = status === 'OPTIMAL' ? '#00E5FF' : 
										status === 'GOOD' ? '#00C853' : 
										status === 'FAIR' ? '#FFA726' : '#FF1744'}
						<div class="health-bar">
							<span class="health-label">{status}</span>
							<div class="health-progress">
								<div class="progress-fill" 
									 style="width: {(count/filteredBUs.length)*100}%; background: {color}">
								</div>
							</div>
							<span class="health-count">{count}</span>
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
		width: 100%;
		display: flex;
		flex-direction: column;
		background: #000000;
		overflow: hidden;
	}

	/* Header Section */
	.header-section {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		background: linear-gradient(135deg, rgba(0, 229, 255, 0.05), transparent);
		border-bottom: 1px solid rgba(0, 229, 255, 0.1);
	}

	.header-left {
		flex: 0 0 auto;
	}

	.main-title {
		margin: 0;
		font-size: 1.25rem;
		font-weight: 600;
		color: #00E5FF;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.title-icon {
		font-size: 1.5rem;
	}

	.subtitle {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.5);
		margin-top: 0.25rem;
		letter-spacing: 0.1em;
	}

	.header-center {
		flex: 1;
		max-width: 400px;
		margin: 0 2rem;
	}

	.search-wrapper {
		position: relative;
		width: 100%;
	}

	.search-icon {
		position: absolute;
		left: 1rem;
		top: 50%;
		transform: translateY(-50%);
		color: rgba(255, 255, 255, 0.4);
	}

	.search-input {
		width: 100%;
		padding: 0.75rem 1rem 0.75rem 3rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		color: #ffffff;
		font-size: 0.9rem;
		transition: all 0.3s ease;
	}

	.search-input:focus {
		outline: none;
		border-color: #00E5FF;
		background: rgba(0, 229, 255, 0.05);
	}

	.header-right {
		flex: 0 0 auto;
	}

	.view-selector {
		display: flex;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		overflow: hidden;
	}

	.view-btn {
		padding: 0.5rem 1rem;
		background: transparent;
		border: none;
		color: rgba(255, 255, 255, 0.6);
		cursor: pointer;
		font-size: 0.85rem;
		transition: all 0.2s ease;
	}

	.view-btn:hover {
		background: rgba(255, 255, 255, 0.05);
	}

	.view-btn.active {
		background: rgba(0, 229, 255, 0.2);
		color: #00E5FF;
	}

	/* Content Area */
	.content-area {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 400px;
		gap: 1.5rem;
		padding: 1.5rem;
		overflow: hidden;
	}

	/* Visualization Panel */
	.visualization-panel {
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 20px;
		padding: 1.5rem;
		overflow: auto;
	}

	/* Treemap View */
	.treemap-container {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		min-height: 100%;
	}

	.treemap-item {
		min-width: 150px;
		min-height: 120px;
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.treemap-item:hover {
		transform: scale(1.05);
		z-index: 10;
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
	}

	.treemap-content {
		text-align: center;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.treemap-icon {
		font-size: 1.5rem;
	}

	.treemap-name {
		font-size: 0.75rem;
		font-weight: 600;
		color: #ffffff;
		line-height: 1.2;
	}

	.treemap-value {
		font-size: 1.1rem;
		font-weight: 700;
	}

	.treemap-percent {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
	}

	/* Hierarchy View */
	.hierarchy-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 2rem;
		min-height: 100%;
	}

	.hierarchy-root {
		margin-bottom: 3rem;
	}

	.root-node {
		background: linear-gradient(135deg, #00E5FF, #7C4DFF);
		padding: 1.5rem 3rem;
		border-radius: 16px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		box-shadow: 0 10px 40px rgba(0, 229, 255, 0.3);
	}

	.node-title {
		font-size: 0.9rem;
		font-weight: 600;
		color: #ffffff;
		letter-spacing: 0.1em;
	}

	.node-count {
		font-size: 1.5rem;
		font-weight: 700;
		color: #ffffff;
	}

	.hierarchy-branches {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		width: 100%;
		position: relative;
	}

	.branch {
		position: relative;
	}

	.branch-line {
		position: absolute;
		top: -3rem;
		left: 50%;
		width: 1px;
		height: 3rem;
		background: rgba(255, 255, 255, 0.2);
	}

	.branch-node {
		background: rgba(0, 0, 0, 0.8);
		border: 2px solid;
		border-radius: 12px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.branch-node:hover {
		transform: translateY(-4px);
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
	}

	.node-icon {
		font-size: 1.2rem;
	}

	.node-name {
		font-size: 0.75rem;
		font-weight: 600;
		color: #ffffff;
		text-align: center;
	}

	.node-value {
		font-size: 1rem;
		font-weight: 700;
	}

	/* Metrics Panel */
	.metrics-panel {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		overflow-y: auto;
	}

	/* Summary Cards */
	.summary-cards {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.summary-card {
		background: linear-gradient(135deg, rgba(0, 229, 255, 0.1), rgba(0, 229, 255, 0.05));
		border: 1px solid rgba(0, 229, 255, 0.2);
		border-radius: 16px;
		padding: 1.5rem;
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.card-icon {
		font-size: 2rem;
		filter: saturate(1.5);
	}

	.card-content {
		flex: 1;
		text-align: center;
	}

	.card-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #00E5FF;
		margin-bottom: 0.25rem;
	}

	.card-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}

	/* Top Divisions */
	.top-divisions {
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 16px;
		padding: 1.5rem;
	}

	.section-title {
		margin: 0 0 1rem 0;
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
		letter-spacing: 0.1em;
	}

	.divisions-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.division-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem;
		background: rgba(255, 255, 255, 0.03);
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.division-item:hover {
		background: rgba(0, 229, 255, 0.05);
		transform: translateX(4px);
	}

	.division-rank {
		font-weight: 700;
		min-width: 30px;
	}

	.division-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.division-name {
		font-size: 0.75rem;
		color: #ffffff;
		font-weight: 500;
	}

	.division-bar {
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		transition: width 0.3s ease;
	}

	.division-stats {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 0.1rem;
	}

	.asset-count {
		font-size: 0.85rem;
		font-weight: 600;
	}

	.asset-percent {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
	}

	/* Health Distribution */
	.health-distribution {
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 16px;
		padding: 1.5rem;
	}

	.health-chart {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.health-bar {
		display: grid;
		grid-template-columns: 60px 1fr 40px;
		align-items: center;
		gap: 0.75rem;
	}

	.health-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 500;
	}

	.health-progress {
		height: 6px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		transition: width 0.5s ease;
	}

	.health-count {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
		text-align: right;
	}

	/* Loading State */
	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		gap: 2rem;
	}

	.org-loader {
		display: flex;
		gap: 1rem;
		align-items: center;
	}

	.org-node {
		width: 20px;
		height: 20px;
		background: #00E5FF;
		border-radius: 50%;
		animation: orgPulse 1.5s ease-in-out infinite;
	}

	.org-node:nth-child(2) {
		animation-delay: 0.3s;
	}

	.org-node:nth-child(3) {
		animation-delay: 0.6s;
	}

	@keyframes orgPulse {
		0%, 100% { transform: scale(1); opacity: 0.5; }
		50% { transform: scale(1.5); opacity: 1; }
	}

	/* Detail View */
	.detail-view {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		background: linear-gradient(135deg, rgba(0, 229, 255, 0.1), transparent);
		border-radius: 12px;
		margin-bottom: 1rem;
	}

	.detail-info h3 {
		margin: 0;
		font-size: 1rem;
		color: #00E5FF;
		margin-bottom: 0.5rem;
	}

	.detail-stats {
		display: flex;
		gap: 0.75rem;
	}

	.stat-badge {
		background: rgba(0, 229, 255, 0.2);
		border: 1px solid #00E5FF;
		padding: 0.25rem 0.5rem;
		border-radius: 6px;
		font-size: 0.7rem;
		color: #00E5FF;
	}

	.close-btn {
		background: rgba(255, 23, 68, 0.1);
		border: none;
		color: #FF1744;
		width: 32px;
		height: 32px;
		border-radius: 8px;
		font-size: 1.5rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}

	.close-btn:hover {
		background: rgba(255, 23, 68, 0.2);
		transform: scale(1.1);
	}

	.detail-table-wrapper {
		flex: 1;
		overflow: auto;
	}

	.detail-table {
		width: 100%;
		border-collapse: collapse;
	}

	.detail-table th {
		background: rgba(0, 0, 0, 0.4);
		color: rgba(255, 255, 255, 0.6);
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
	}

	.detail-table td {
		padding: 0.75rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.host-cell {
		font-family: 'SF Mono', monospace;
		color: #00E5FF;
	}

	.status-badge {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 20px;
		height: 20px;
		border-radius: 4px;
		font-weight: 600;
		font-size: 0.75rem;
	}

	.status-badge.success {
		background: rgba(0, 229, 255, 0.2);
		color: #00E5FF;
	}

	.status-badge.danger {
		background: rgba(255, 23, 68, 0.2);
		color: #FF1744;
	}

	.status-badge.warning {
		background: rgba(255, 214, 0, 0.2);
		color: #FFD600;
	}

	/* Responsive */
	@media (max-width: 1200px) {
		.content-area {
			grid-template-columns: 1fr;
		}
		
		.metrics-panel {
			display: grid;
			grid-template-columns: repeat(3, 1fr);
			gap: 1rem;
		}
	}

	@media (max-width: 768px) {
		.header-section {
			flex-direction: column;
			gap: 1rem;
		}
		
		.metrics-panel {
			grid-template-columns: 1fr;
		}
	}

	/* Scrollbar */
	::-webkit-scrollbar {
		width: 6px;
	}

	::-webkit-scrollbar-track {
		background: rgba(255, 255, 255, 0.02);
	}

	::-webkit-scrollbar-thumb {
		background: rgba(0, 229, 255, 0.2);
		border-radius: 3px;
	}
</style>