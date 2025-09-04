<!-- SourceTables.svelte - Premium Full-Screen Analysis -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let hoveredIndex = -1;

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
	
	$: maxFreq = filteredSources.length > 0 ? Math.max(...filteredSources.map(([,f]) => f)) : 1;

	function getPercentage(frequency) {
		if (!data.total_mentions) return 0;
		return ((frequency / data.total_mentions) * 100).toFixed(2);
	}

	function getThreatLevel(frequency) {
		const percentage = (frequency / maxFreq) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#FF1744' };
		if (percentage >= 50) return { level: 'HIGH', color: '#FFA726' };
		if (percentage >= 25) return { level: 'MEDIUM', color: '#FFD600' };
		return { level: 'LOW', color: '#00E5FF' };
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
</script>

<div class="dashboard-container">
	<!-- Left Panel: Main Table -->
	<div class="main-panel">
		<div class="panel-header">
			<div class="header-top">
				<h2 class="panel-title">
					<span class="title-icon">◈</span>
					SOURCE TABLE FREQUENCY ANALYSIS
				</h2>
				<div class="header-stats">
					<div class="stat-badge">
						<span class="stat-value">{filteredSources.length}</span>
						<span class="stat-label">Sources</span>
					</div>
					<div class="stat-badge">
						<span class="stat-value">{(data.total_mentions || 0).toLocaleString()}</span>
						<span class="stat-label">Mentions</span>
					</div>
				</div>
			</div>
			<div class="search-bar">
				<svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<circle cx="11" cy="11" r="8"></circle>
					<path d="m21 21-4.35-4.35"></path>
				</svg>
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
				<div class="loader">
					<div class="loader-ring"></div>
					<div class="loader-ring"></div>
					<div class="loader-ring"></div>
				</div>
				<p>Analyzing source matrices...</p>
			</div>
		{:else if selectedSource}
			<div class="detail-view">
				<div class="detail-header">
					<h3>{selectedSource.source.toUpperCase()}</h3>
					<button class="close-btn" on:click={closeDetails}>
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="18" y1="6" x2="6" y2="18"></line>
							<line x1="6" y1="6" x2="18" y2="18"></line>
						</svg>
					</button>
				</div>
				<div class="detail-content">
					<table class="detail-table">
						<thead>
							<tr>
								<th>HOST</th>
								<th>REGION</th>
								<th>COUNTRY</th>
								<th>INFRASTRUCTURE</th>
								<th>CMDB</th>
								<th>TANIUM</th>
							</tr>
						</thead>
						<tbody>
							{#each hostDetails as host}
								<tr>
									<td class="host-cell">{host.host}</td>
									<td>{host.region || 'Unknown'}</td>
									<td>{host.country || 'Unknown'}</td>
									<td>{host.infrastructure_type || 'Unknown'}</td>
									<td>
										<span class="badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'success' : 'danger'}">
											{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'YES' : 'NO'}
										</span>
									</td>
									<td>
										<span class="badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'success' : 'warning'}">
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
			<div class="table-container">
				<table class="data-table">
					<thead>
						<tr>
							<th>SOURCE TABLE</th>
							<th>FREQUENCY</th>
							<th>COVERAGE</th>
							<th>THREAT LEVEL</th>
							<th>VISIBILITY</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredSources as [source, frequency], index}
							{@const threat = getThreatLevel(frequency)}
							<tr class="table-row {hoveredIndex === index ? 'hovered' : ''}"
								on:click={() => drillDownSource(source, frequency)}
								on:mouseenter={() => hoveredIndex = index}
								on:mouseleave={() => hoveredIndex = -1}>
								<td class="source-cell">
									<div class="source-indicator" style="background: {threat.color}"></div>
									<span>{source.toUpperCase()}</span>
								</td>
								<td class="numeric">{frequency.toLocaleString()}</td>
								<td class="coverage-cell">
									<div class="progress-bar">
										<div class="progress-fill" style="width: {(frequency/maxFreq)*100}%; background: {threat.color}"></div>
									</div>
									<span class="percentage">{getPercentage(frequency)}%</span>
								</td>
								<td>
									<span class="threat-badge" style="color: {threat.color}; border-color: {threat.color}">
										{threat.level}
									</span>
								</td>
								<td>
									<div class="visibility-bars">
										{#each Array(10) as _, i}
											<div class="bar" style="opacity: {(frequency/maxFreq) > (i/10) ? 1 : 0.2}; background: {threat.color}"></div>
										{/each}
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>

	<!-- Right Panel: Analytics -->
	<div class="analytics-panel">
		<!-- Top Sources Card -->
		<div class="card">
			<h3 class="card-title">TOP SOURCES</h3>
			<div class="top-sources">
				{#each filteredSources.slice(0, 5) as [source, frequency], i}
					{@const threat = getThreatLevel(frequency)}
					<div class="top-source-item">
						<span class="rank">#{i + 1}</span>
						<div class="source-info">
							<span class="source-name">{source.substring(0, 20).toUpperCase()}</span>
							<div class="source-bar">
								<div class="bar-fill" style="width: {(frequency/maxFreq)*100}%; background: {threat.color}"></div>
							</div>
						</div>
						<span class="source-count" style="color: {threat.color}">{frequency}</span>
					</div>
				{/each}
			</div>
		</div>

		<!-- Distribution Chart -->
		<div class="card">
			<h3 class="card-title">DISTRIBUTION ANALYSIS</h3>
			<div class="distribution-chart">
				<svg viewBox="0 0 200 150" class="chart-svg">
					{#each filteredSources.slice(0, 8) as [source, frequency], i}
						{@const x = (i % 4) * 50 + 25}
						{@const y = Math.floor(i / 4) * 50 + 25}
						{@const size = (frequency / maxFreq) * 15 + 5}
						{@const threat = getThreatLevel(frequency)}
						
						<circle cx="{x}" cy="{y}" r="{size}" 
								fill={threat.color} opacity="0.3"/>
						<circle cx="{x}" cy="{y}" r="{size/2}" 
								fill={threat.color} opacity="0.8"/>
						<circle cx="{x}" cy="{y}" r="2" fill="#ffffff"/>
					{/each}
				</svg>
			</div>
		</div>

		<!-- Metrics Grid -->
		<div class="metrics-grid">
			<div class="metric-card">
				<div class="metric-value">{filteredSources.length}</div>
				<div class="metric-label">Total Sources</div>
			</div>
			<div class="metric-card">
				<div class="metric-value">{(data.total_mentions || 0).toLocaleString()}</div>
				<div class="metric-label">Total Mentions</div>
			</div>
		</div>
	</div>
</div>

<style>
	.dashboard-container {
		height: calc(100vh - 80px);
		width: 100%;
		display: grid;
		grid-template-columns: 1fr 400px;
		gap: 1.5rem;
		padding: 0;
		background: #000000;
		overflow: hidden;
	}

	/* Main Panel */
	.main-panel {
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 20px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.panel-header {
		padding: 1.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		background: rgba(0, 0, 0, 0.3);
	}

	.header-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.panel-title {
		margin: 0;
		font-size: 1.1rem;
		font-weight: 600;
		color: #00E5FF;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.title-icon {
		font-size: 1.5rem;
		text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
	}

	.header-stats {
		display: flex;
		gap: 1rem;
	}

	.stat-badge {
		background: rgba(0, 229, 255, 0.1);
		border: 1px solid rgba(0, 229, 255, 0.3);
		border-radius: 12px;
		padding: 0.5rem 1rem;
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.stat-value {
		font-size: 1.25rem;
		font-weight: 600;
		color: #00E5FF;
	}

	.stat-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		text-transform: uppercase;
	}

	/* Search Bar */
	.search-bar {
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
		background: rgba(255, 255, 255, 0.05);
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

	/* Table Container */
	.table-container {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
	}

	.data-table th {
		background: rgba(0, 0, 0, 0.4);
		color: rgba(255, 255, 255, 0.6);
		padding: 1rem;
		text-align: left;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.data-table td {
		padding: 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.8);
		font-size: 0.85rem;
	}

	.table-row {
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.table-row:hover {
		background: rgba(0, 229, 255, 0.05);
	}

	.source-cell {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-weight: 500;
	}

	.source-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.numeric {
		font-family: 'SF Mono', monospace;
		color: #00E5FF;
	}

	.coverage-cell {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.progress-bar {
		width: 80px;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		transition: width 0.3s ease;
	}

	.percentage {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.6);
		min-width: 45px;
		text-align: right;
	}

	.threat-badge {
		padding: 0.25rem 0.5rem;
		border: 1px solid;
		border-radius: 6px;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.visibility-bars {
		display: flex;
		gap: 2px;
		height: 20px;
		align-items: center;
	}

	.visibility-bars .bar {
		width: 3px;
		height: 100%;
		border-radius: 1px;
		transition: all 0.3s ease;
	}

	/* Analytics Panel */
	.analytics-panel {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.card {
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 16px;
		padding: 1.5rem;
	}

	.card-title {
		margin: 0 0 1rem 0;
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
		letter-spacing: 0.1em;
	}

	/* Top Sources */
	.top-sources {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.top-source-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem;
		background: rgba(255, 255, 255, 0.03);
		border-radius: 8px;
	}

	.rank {
		font-weight: 600;
		color: #00E5FF;
		min-width: 30px;
	}

	.source-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.source-name {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.source-bar {
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		transition: width 0.3s ease;
	}

	.source-count {
		font-size: 0.85rem;
		font-weight: 600;
		min-width: 50px;
		text-align: right;
	}

	/* Distribution Chart */
	.distribution-chart {
		height: 150px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.chart-svg {
		width: 100%;
		height: 100%;
	}

	/* Metrics Grid */
	.metrics-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.metric-card {
		background: rgba(0, 229, 255, 0.05);
		border: 1px solid rgba(0, 229, 255, 0.2);
		border-radius: 12px;
		padding: 1rem;
		text-align: center;
	}

	.metric-value {
		font-size: 1.5rem;
		font-weight: 600;
		color: #00E5FF;
		margin-bottom: 0.25rem;
	}

	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	/* Loading State */
	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1.5rem;
	}

	.loader {
		position: relative;
		width: 60px;
		height: 60px;
	}

	.loader-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid transparent;
		border-top-color: #00E5FF;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.loader-ring:nth-child(2) {
		width: 80%;
		height: 80%;
		top: 10%;
		left: 10%;
		animation-delay: 0.2s;
	}

	.loader-ring:nth-child(3) {
		width: 60%;
		height: 60%;
		top: 20%;
		left: 20%;
		animation-delay: 0.4s;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* Detail View */
	.detail-view {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		border-bottom: 1px solid rgba(0, 229, 255, 0.2);
		background: rgba(0, 229, 255, 0.05);
	}

	.detail-header h3 {
		margin: 0;
		color: #00E5FF;
		font-size: 1.1rem;
	}

	.close-btn {
		background: rgba(255, 23, 68, 0.1);
		border: 1px solid #FF1744;
		color: #FF1744;
		width: 36px;
		height: 36px;
		border-radius: 8px;
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

	.detail-content {
		flex: 1;
		overflow: auto;
		padding: 1rem;
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
	}

	.detail-table td {
		padding: 0.75rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		font-size: 0.8rem;
	}

	.host-cell {
		font-family: 'SF Mono', monospace;
		color: #00E5FF;
	}

	.badge {
		padding: 0.2rem 0.4rem;
		border-radius: 4px;
		font-size: 0.65rem;
		font-weight: 600;
		text-transform: uppercase;
	}

	.badge.success {
		background: rgba(0, 229, 255, 0.2);
		color: #00E5FF;
		border: 1px solid #00E5FF;
	}

	.badge.warning {
		background: rgba(255, 214, 0, 0.2);
		color: #FFD600;
		border: 1px solid #FFD600;
	}

	.badge.danger {
		background: rgba(255, 23, 68, 0.2);
		color: #FF1744;
		border: 1px solid #FF1744;
	}

	/* Responsive */
	@media (max-width: 1400px) {
		.dashboard-container {
			grid-template-columns: 1fr;
		}

		.analytics-panel {
			display: grid;
			grid-template-columns: repeat(3, 1fr);
			grid-template-rows: auto;
			overflow: visible;
		}

		.card:first-child {
			grid-column: span 2;
		}
	}

	@media (max-width: 768px) {
		.analytics-panel {
			grid-template-columns: 1fr;
		}

		.card:first-child {
			grid-column: span 1;
		}

		.header-top {
			flex-direction: column;
			gap: 1rem;
			align-items: flex-start;
		}
	}
</style>