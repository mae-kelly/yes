<!-- SourceTables.svelte - Intelligence Matrix -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 12;
	let viewMode = 'grid';

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
	$: maxFreq = filteredSources.length > 0 ? Math.max(...filteredSources.map(([,f]) => f)) : 1;

	function getThreatLevel(frequency) {
		if (!data.total_mentions) return { level: 'LOW', color: '#00ffea', intensity: 0.3 };
		let percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRITICAL', color: '#ff3366', intensity: 1.0 };
		if (percentage >= 10) return { level: 'HIGH', color: '#ff9f00', intensity: 0.8 };
		if (percentage >= 5) return { level: 'MEDIUM', color: '#ffea00', intensity: 0.6 };
		return { level: 'LOW', color: '#00ffea', intensity: 0.4 };
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
</script>

<div class="intel-container">
	<!-- Header Section -->
	<div class="intel-header">
		<div class="header-left">
			<div class="section-icon">◆</div>
			<div class="section-info">
				<h2>SOURCE INTELLIGENCE</h2>
				<p>FREQUENCY ANALYSIS MATRIX</p>
			</div>
		</div>
		
		<div class="header-stats">
			<div class="stat">
				<div class="stat-value">{(data.unique_sources || 0).toLocaleString()}</div>
				<div class="stat-label">SOURCES</div>
			</div>
			<div class="stat">
				<div class="stat-value">{(data.total_mentions || 0).toLocaleString()}</div>
				<div class="stat-label">MENTIONS</div>
			</div>
			<div class="stat">
				<div class="stat-value">{Math.round((data.total_mentions || 0) / (data.unique_sources || 1))}</div>
				<div class="stat-label">AVG/SOURCE</div>
			</div>
		</div>
	</div>

	<!-- Control Bar -->
	<div class="control-bar">
		<div class="search-box">
			<span class="search-icon">◎</span>
			<input 
				type="text" 
				bind:value={searchTerm}
				placeholder="Search intelligence..."
				class="search-input"
			/>
		</div>
		
		<div class="view-controls">
			<button class="view-btn {viewMode === 'grid' ? 'active' : ''}" on:click={() => viewMode = 'grid'}>
				MATRIX
			</button>
			<button class="view-btn {viewMode === 'table' ? 'active' : ''}" on:click={() => viewMode = 'table'}>
				TABLE
			</button>
			<button class="view-btn {viewMode === 'chart' ? 'active' : ''}" on:click={() => viewMode = 'chart'}>
				ANALYTICS
			</button>
		</div>
	</div>

	<!-- Content Area -->
	<div class="content-area">
		{#if loading && !selectedSource}
			<div class="loading-state">
				<div class="loader">
					<div class="loader-ring"></div>
					<div class="loader-core">◈</div>
				</div>
				<p>ANALYZING INTELLIGENCE...</p>
			</div>
		{:else if selectedSource}
			<!-- Drill-down View -->
			<div class="drill-panel">
				<div class="drill-header">
					<div class="drill-title">
						<span class="drill-icon">◈</span>
						<h3>{selectedSource.source.toUpperCase()}</h3>
						<span class="drill-badge">{selectedSource.frequency} INSTANCES</span>
					</div>
					<button class="close-btn" on:click={closeDetails}>✕</button>
				</div>
				
				<div class="drill-table">
					<table>
						<thead>
							<tr>
								<th>HOST ID</th>
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
									<td class="host-cell">
										<span class="host-icon">▸</span>
										{host.host}
									</td>
									<td>{host.region || 'Unknown'}</td>
									<td>{host.country || 'Unknown'}</td>
									<td>{host.infrastructure_type || 'Unknown'}</td>
									<td>
										<span class="badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
											{host.present_in_cmdb?.toLowerCase().includes('yes') ? '✓' : '✗'}
										</span>
									</td>
									<td>
										<span class="badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
											{host.tanium_coverage?.toLowerCase().includes('tanium') ? '✓' : '✗'}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{:else if viewMode === 'grid'}
			<!-- Matrix Grid -->
			<div class="intel-grid">
				{#each paginatedSources as [source, frequency]}
					{@const threat = getThreatLevel(frequency)}
					<div class="intel-card" 
						style="--card-color: {threat.color}"
						on:click={() => drillDownSource(source, frequency)}>
						<div class="card-header">
							<span class="card-icon">◈</span>
							<span class="threat-level {threat.level.toLowerCase()}">{threat.level}</span>
						</div>
						<div class="card-body">
							<div class="source-name">{source.toUpperCase()}</div>
							<div class="frequency-display">
								<span class="frequency-value">{frequency.toLocaleString()}</span>
								<span class="frequency-label">INSTANCES</span>
							</div>
							<div class="meter">
								<div class="meter-fill" style="width: {(frequency/maxFreq)*100}%"></div>
							</div>
							<div class="card-footer">
								<span class="percentage">{getPercentage(frequency)}%</span>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{:else if viewMode === 'table'}
			<!-- Table View -->
			<div class="data-table">
				<table>
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
								<td>
									<div class="source-cell">
										<span class="cell-icon" style="color: {threat.color}">◈</span>
										{source.toUpperCase()}
									</div>
								</td>
								<td class="center">{frequency.toLocaleString()}</td>
								<td>
									<div class="coverage-cell">
										<div class="coverage-bar">
											<div class="coverage-fill" style="width: {getPercentage(frequency)}%; background: {threat.color}"></div>
										</div>
										<span>{getPercentage(frequency)}%</span>
									</div>
								</td>
								<td class="center">
									<span class="threat-badge {threat.level.toLowerCase()}">{threat.level}</span>
								</td>
								<td class="center">
									<button class="action-btn" on:click={() => drillDownSource(source, frequency)}>
										ANALYZE →
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{:else}
			<!-- Analytics View -->
			<div class="analytics-view">
				<div class="chart-panel">
					<h3>THREAT DISTRIBUTION</h3>
					<div class="donut-chart">
						<!-- Chart visualization here -->
					</div>
				</div>
				
				<div class="chart-panel">
					<h3>TOP SOURCES</h3>
					<div class="bar-chart">
						{#each filteredSources.slice(0, 5) as [source, frequency]}
							{@const threat = getThreatLevel(frequency)}
							<div class="bar-item">
								<div class="bar-label">{source.toUpperCase()}</div>
								<div class="bar-container">
									<div class="bar-fill" 
										style="width: {(frequency/maxFreq)*100}%; background: {threat.color}">
										<span class="bar-value">{frequency}</span>
									</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		{/if}
		
		<!-- Pagination -->
		{#if !selectedSource && viewMode !== 'chart' && totalPages > 1}
			<div class="pagination">
				<button 
					class="page-btn"
					on:click={() => currentPage = Math.max(1, currentPage - 1)}
					disabled={currentPage === 1}>
					◀
				</button>
				<div class="page-info">
					<span>{currentPage}</span>
					<span>/</span>
					<span>{totalPages}</span>
				</div>
				<button 
					class="page-btn"
					on:click={() => currentPage = Math.min(totalPages, currentPage + 1)}
					disabled={currentPage === totalPages}>
					▶
				</button>
			</div>
		{/if}
	</div>
</div>

<style>
	.intel-container {
		height: calc(100vh - 80px);
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
		color: #fff;
		font-family: 'JetBrains Mono', monospace;
	}

	/* Header */
	.intel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 20px 24px;
		background: rgba(0, 0, 0, 0.6);
		border-bottom: 1px solid rgba(0, 255, 159, 0.2);
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 16px;
	}

	.section-icon {
		font-size: 32px;
		color: #00ff9f;
		text-shadow: 0 0 20px rgba(0, 255, 159, 0.6);
	}

	.section-info h2 {
		margin: 0;
		font-size: 20px;
		color: #00ff9f;
		font-weight: 700;
		letter-spacing: 1px;
	}

	.section-info p {
		margin: 2px 0 0 0;
		font-size: 11px;
		color: rgba(255, 255, 255, 0.5);
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	.header-stats {
		display: flex;
		gap: 32px;
	}

	.stat {
		text-align: center;
	}

	.stat-value {
		font-size: 24px;
		font-weight: 700;
		color: #00ffea;
		text-shadow: 0 0 10px currentColor;
	}

	.stat-label {
		font-size: 10px;
		color: rgba(255, 255, 255, 0.4);
		text-transform: uppercase;
		letter-spacing: 1px;
		margin-top: 4px;
	}

	/* Control Bar */
	.control-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 16px 24px;
		background: rgba(0, 0, 0, 0.4);
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.search-box {
		position: relative;
		display: flex;
		align-items: center;
		max-width: 400px;
		flex: 1;
	}

	.search-icon {
		position: absolute;
		left: 12px;
		color: #00ffea;
		font-size: 16px;
	}

	.search-input {
		width: 100%;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 234, 0.2);
		border-radius: 4px;
		padding: 10px 12px 10px 40px;
		color: #fff;
		font-size: 13px;
		font-family: inherit;
	}

	.search-input:focus {
		outline: none;
		border-color: #00ffea;
		box-shadow: 0 0 12px rgba(0, 255, 234, 0.2);
	}

	.view-controls {
		display: flex;
		gap: 4px;
	}

	.view-btn {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		color: rgba(255, 255, 255, 0.5);
		padding: 8px 16px;
		border-radius: 4px;
		cursor: pointer;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 1px;
		transition: all 0.2s ease;
	}

	.view-btn:hover {
		background: rgba(0, 255, 159, 0.1);
		border-color: #00ff9f;
		color: #00ff9f;
	}

	.view-btn.active {
		background: rgba(0, 255, 159, 0.15);
		border-color: #00ff9f;
		color: #00ff9f;
		box-shadow: 0 2px 8px rgba(0, 255, 159, 0.2);
	}

	/* Content Area */
	.content-area {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: 20px;
		overflow: hidden;
		min-height: 0;
	}

	/* Loading */
	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 20px;
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
		border: 2px solid rgba(0, 255, 159, 0.2);
		border-top-color: #00ff9f;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.loader-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 24px;
		color: #00ff9f;
		animation: pulse 2s ease-in-out infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@keyframes pulse {
		0%, 100% { opacity: 0.5; }
		50% { opacity: 1; }
	}

	/* Grid View */
	.intel-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
		gap: 16px;
		flex: 1;
		overflow-y: auto;
		padding-right: 8px;
	}

	.intel-card {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid var(--card-color);
		border-radius: 4px;
		padding: 16px;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.intel-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 20px color-mix(in srgb, var(--card-color) 30%, transparent);
		background: rgba(0, 0, 0, 0.9);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 12px;
	}

	.card-icon {
		font-size: 20px;
		color: var(--card-color);
		filter: drop-shadow(0 0 8px var(--card-color));
	}

	.threat-level {
		font-size: 10px;
		padding: 4px 8px;
		border-radius: 2px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.threat-level.critical {
		background: rgba(255, 51, 102, 0.2);
		color: #ff3366;
		border: 1px solid #ff3366;
	}

	.threat-level.high {
		background: rgba(255, 159, 0, 0.2);
		color: #ff9f00;
		border: 1px solid #ff9f00;
	}

	.threat-level.medium {
		background: rgba(255, 234, 0, 0.2);
		color: #ffea00;
		border: 1px solid #ffea00;
	}

	.threat-level.low {
		background: rgba(0, 255, 234, 0.2);
		color: #00ffea;
		border: 1px solid #00ffea;
	}

	.card-body {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.source-name {
		font-size: 14px;
		font-weight: 600;
		color: #fff;
		letter-spacing: 0.5px;
	}

	.frequency-display {
		display: flex;
		align-items: baseline;
		gap: 8px;
	}

	.frequency-value {
		font-size: 28px;
		font-weight: 700;
		color: var(--card-color);
		text-shadow: 0 0 12px var(--card-color);
	}

	.frequency-label {
		font-size: 10px;
		color: rgba(255, 255, 255, 0.4);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.meter {
		width: 100%;
		height: 4px;
		background: rgba(0, 0, 0, 0.6);
		border-radius: 2px;
		overflow: hidden;
	}

	.meter-fill {
		height: 100%;
		background: linear-gradient(90deg, var(--card-color), color-mix(in srgb, var(--card-color) 60%, transparent));
		transition: width 0.5s ease;
		box-shadow: 0 0 8px var(--card-color);
	}

	.card-footer {
		display: flex;
		justify-content: flex-end;
	}

	.percentage {
		font-size: 12px;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
	}

	/* Table View */
	.data-table {
		flex: 1;
		overflow: auto;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(0, 255, 159, 0.2);
		border-radius: 4px;
	}

	.data-table table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0;
	}

	.data-table th {
		background: rgba(0, 0, 0, 0.8);
		color: #00ff9f;
		padding: 12px;
		text-align: left;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 1px;
		text-transform: uppercase;
		border-bottom: 1px solid rgba(0, 255, 159, 0.2);
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.data-table td {
		padding: 12px;
		color: rgba(255, 255, 255, 0.8);
		font-size: 12px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}

	.data-table tr:hover {
		background: rgba(0, 255, 159, 0.05);
	}

	.source-cell {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.cell-icon {
		font-size: 16px;
	}

	.center {
		text-align: center;
	}

	.coverage-cell {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.coverage-bar {
		flex: 1;
		height: 6px;
		background: rgba(0, 0, 0, 0.6);
		border-radius: 3px;
		overflow: hidden;
		min-width: 100px;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.5s ease;
	}

	.threat-badge {
		padding: 4px 10px;
		border-radius: 2px;
		font-size: 10px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.threat-badge.critical {
		background: rgba(255, 51, 102, 0.2);
		color: #ff3366;
		border: 1px solid #ff3366;
	}

	.threat-badge.high {
		background: rgba(255, 159, 0, 0.2);
		color: #ff9f00;
		border: 1px solid #ff9f00;
	}

	.threat-badge.medium {
		background: rgba(255, 234, 0, 0.2);
		color: #ffea00;
		border: 1px solid #ffea00;
	}

	.threat-badge.low {
		background: rgba(0, 255, 234, 0.2);
		color: #00ffea;
		border: 1px solid #00ffea;
	}

	.action-btn {
		background: rgba(0, 255, 159, 0.1);
		border: 1px solid #00ff9f;
		color: #00ff9f;
		padding: 6px 12px;
		border-radius: 2px;
		cursor: pointer;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.5px;
		transition: all 0.2s ease;
	}

	.action-btn:hover {
		background: rgba(0, 255, 159, 0.2);
		transform: translateX(2px);
		box-shadow: 0 0 12px rgba(0, 255, 159, 0.3);
	}

	/* Analytics View */
	.analytics-view {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 20px;
		overflow: auto;
	}

	.chart-panel {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(0, 255, 159, 0.2);
		border-radius: 4px;
		padding: 20px;
	}

	.chart-panel h3 {
		margin: 0 0 16px 0;
		color: #00ff9f;
		font-size: 14px;
		letter-spacing: 1px;
	}

	.bar-chart {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.bar-item {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.bar-label {
		font-size: 11px;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
	}

	.bar-container {
		position: relative;
		height: 20px;
		background: rgba(0, 0, 0, 0.6);
		border-radius: 2px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding-right: 8px;
		transition: width 0.5s ease;
	}

	.bar-value {
		font-size: 11px;
		font-weight: 600;
		color: #fff;
		text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
	}

	/* Drill Panel */
	.drill-panel {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 51, 102, 0.3);
		border-radius: 4px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.drill-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 16px 20px;
		background: rgba(255, 51, 102, 0.05);
		border-bottom: 1px solid rgba(255, 51, 102, 0.2);
	}

	.drill-title {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.drill-icon {
		font-size: 20px;
		color: #ff3366;
		filter: drop-shadow(0 0 8px #ff3366);
	}

	.drill-title h3 {
		margin: 0;
		color: #ff3366;
		font-size: 16px;
		letter-spacing: 1px;
	}

	.drill-badge {
		padding: 4px 10px;
		background: rgba(255, 51, 102, 0.1);
		border: 1px solid rgba(255, 51, 102, 0.3);
		border-radius: 2px;
		color: #ff3366;
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.5px;
	}

	.close-btn {
		width: 28px;
		height: 28px;
		background: transparent;
		border: 1px solid #ff3366;
		color: #ff3366;
		border-radius: 2px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
		font-size: 16px;
	}

	.close-btn:hover {
		background: rgba(255, 51, 102, 0.2);
		transform: rotate(90deg);
	}

	.drill-table {
		flex: 1;
		overflow: auto;
		padding: 20px;
	}

	.drill-table table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0 8px;
	}

	.drill-table th {
		background: rgba(255, 51, 102, 0.05);
		color: #ff3366;
		padding: 10px;
		text-align: left;
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 1px;
		text-transform: uppercase;
		border: 1px solid rgba(255, 51, 102, 0.2);
	}

	.drill-table td {
		padding: 10px;
		color: rgba(255, 255, 255, 0.8);
		font-size: 12px;
		background: rgba(0, 0, 0, 0.3);
		border-top: 1px solid rgba(255, 255, 255, 0.05);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}

	.drill-table td:first-child {
		border-left: 1px solid rgba(255, 255, 255, 0.05);
	}

	.drill-table td:last-child {
		border-right: 1px solid rgba(255, 255, 255, 0.05);
	}

	.host-cell {
		display: flex;
		align-items: center;
		gap: 6px;
		font-family: 'Courier New', monospace;
		color: #00ffea;
	}

	.host-icon {
		color: #ff3366;
		font-size: 12px;
	}

	.badge {
		padding: 2px 6px;
		border-radius: 2px;
		font-size: 10px;
		font-weight: 600;
	}

	.badge.active {
		background: rgba(0, 255, 159, 0.2);
		color: #00ff9f;
		border: 1px solid #00ff9f;
	}

	.badge.inactive {
		background: rgba(255, 51, 102, 0.2);
		color: #ff3366;
		border: 1px solid #ff3366;
	}

	/* Pagination */
	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 16px;
		padding: 16px 0 0 0;
		margin-top: auto;
	}

	.page-btn {
		width: 32px;
		height: 32px;
		background: rgba(0, 255, 159, 0.1);
		border: 1px solid rgba(0, 255, 159, 0.3);
		color: #00ff9f;
		border-radius: 2px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
		font-size: 14px;
	}

	.page-btn:hover:not(:disabled) {
		background: rgba(0, 255, 159, 0.2);
		transform: scale(1.1);
		box-shadow: 0 0 12px rgba(0, 255, 159, 0.3);
	}

	.page-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.page-info {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 6px 12px;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(0, 255, 159, 0.2);
		border-radius: 2px;
		color: #00ff9f;
		font-size: 12px;
		font-weight: 600;
	}

	/* Scrollbar */
	::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}

	::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.3);
		border-radius: 4px;
	}

	::-webkit-scrollbar-thumb {
		background: linear-gradient(180deg, #00ff9f, #00ffea);
		border-radius: 4px;
	}

	::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(180deg, #00ffea, #00ff9f);
	}

	/* Responsive */
	@media (max-width: 1200px) {
		.intel-grid {
			grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		}
		
		.analytics-view {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 768px) {
		.intel-header {
			flex-direction: column;
			gap: 16px;
			align-items: flex-start;
		}
		
		.control-bar {
			flex-direction: column;
			gap: 12px;
		}
		
		.search-box {
			max-width: 100%;
		}
		
		.intel-grid {
			grid-template-columns: 1fr;
		}
	}
</style>