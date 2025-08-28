<!-- SourceTables.svelte - Military Intelligence Tables -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 10;
	let viewMode = 'table';

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
		if (!data.total_mentions) return { level: 'SECURE', color: '#16c784' };
		let percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRITICAL', color: '#dc2626' };
		if (percentage >= 10) return { level: 'HIGH', color: '#ea580c' };
		if (percentage >= 5) return { level: 'MEDIUM', color: '#ca8a04' };
		return { level: 'SECURE', color: '#16c784' };
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

	$: threatDistribution = filteredSources.reduce((acc, [_, frequency]) => {
		let level = getThreatLevel(frequency).level;
		acc[level] = (acc[level] || 0) + 1;
		return acc;
	}, {});
</script>

<div class="military-dashboard">
	<!-- Header Section -->
	<div class="header-section">
		<div class="header-content">
			<div class="title-block">
				<div class="title-icon">
					<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
						<rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
						<line x1="3" y1="9" x2="21" y2="9" stroke="currentColor" stroke-width="2"/>
						<line x1="3" y1="15" x2="21" y2="15" stroke="currentColor" stroke-width="2"/>
						<line x1="9" y1="9" x2="9" y2="21" stroke="currentColor" stroke-width="2"/>
						<line x1="15" y1="9" x2="15" y2="21" stroke="currentColor" stroke-width="2"/>
					</svg>
				</div>
				<div class="title-text">
					<h1>SOURCE INTELLIGENCE</h1>
					<p>Frequency Analysis Matrix</p>
				</div>
			</div>
			<div class="metrics-row">
				<div class="metric-card">
					<div class="metric-value">{filteredSources.length}</div>
					<div class="metric-label">SOURCES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{(data.total_mentions || 0).toLocaleString()}</div>
					<div class="metric-label">MENTIONS</div>
				</div>
				<div class="metric-card primary">
					<div class="metric-value">{filteredSources[0] ? filteredSources[0][0].substring(0, 15).toUpperCase() : 'N/A'}</div>
					<div class="metric-label">PRIMARY</div>
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
				<h3>SOURCE ANALYSIS</h3>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search sources..."
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
			
			{#if loading && !selectedSource}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>SCANNING NETWORK...</p>
				</div>
			{:else if selectedSource}
				<!-- Drill-down View -->
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedSource.source.toUpperCase()}</h4>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="table-container">
						<table class="data-table">
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
											<span>{source.toUpperCase()}</span>
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
											ANALYZE →
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
					{#each paginatedSources as [source, frequency]}
						{@const threat = getThreatLevel(frequency)}
						<div class="grid-card" style="--card-color: {threat.color}" on:click={() => drillDownSource(source, frequency)}>
							<div class="card-header">
								<span class="card-icon">▣</span>
								<span class="threat-indicator {threat.level.toLowerCase()}">{threat.level}</span>
							</div>
							<div class="card-body">
								<div class="source-name">{source.substring(0, 20).toUpperCase()}{source.length > 20 ? '...' : ''}</div>
								<div class="source-count">{frequency.toLocaleString()}</div>
								<div class="progress-bar">
									<div class="progress-fill" style="width: {(frequency/maxFreq)*100}%; background: {threat.color}"></div>
								</div>
								<div class="card-percentage">{getPercentage(frequency)}%</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Right Panel: Visualizations -->
		<div class="viz-panel">
			<!-- Threat Distribution -->
			<div class="viz-card">
				<h4>THREAT MATRIX</h4>
				<div class="threat-chart">
					{#each Object.entries(threatDistribution) as [level, count]}
						{@const color = level === 'CRITICAL' ? '#dc2626' : 
							level === 'HIGH' ? '#ea580c' : 
							level === 'MEDIUM' ? '#ca8a04' : '#16c784'}
						<div class="threat-row">
							<div class="threat-label">{level}</div>
							<div class="threat-bar-container">
								<div class="threat-bar" style="width: {(count/filteredSources.length)*100}%; background: {color}"></div>
							</div>
							<div class="threat-count">{count}</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Top Sources -->
			<div class="viz-card">
				<h4>TOP 5 SOURCES</h4>
				<div class="bar-chart">
					{#each filteredSources.slice(0, 5) as [source, frequency]}
						{@const threat = getThreatLevel(frequency)}
						<div class="bar-item">
							<div class="bar-label">{source.substring(0, 15).toUpperCase()}</div>
							<div class="bar-container">
								<div class="bar-fill" style="width: {(frequency/maxFreq)*100}%; background: linear-gradient(90deg, {threat.color}, {threat.color}dd)"></div>
								<span class="bar-value">{frequency.toLocaleString()}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Activity Matrix -->
			<div class="viz-card">
				<h4>ACTIVITY MATRIX</h4>
				<div class="matrix-grid">
					{#each paginatedSources.slice(0, 9) as [source, frequency]}
						{@const threat = getThreatLevel(frequency)}
						<div class="matrix-cell" style="background: {threat.color}30; border-color: {threat.color}">
							<div class="cell-value">{getPercentage(frequency)}%</div>
							<div class="cell-label">{source.substring(0, 6).toUpperCase()}</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.military-dashboard {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: #000;
		color: #fff;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
	}

	.header-section {
		background: #000;
		border-bottom: 2px solid #16c784;
		padding: 0.8rem 1rem;
		flex-shrink: 0;
	}

	.header-content {
		max-width: 100%;
	}

	.title-block {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		margin-bottom: 0.8rem;
	}

	.title-icon {
		width: 30px;
		height: 30px;
		color: #16c784;
		filter: drop-shadow(0 0 10px #16c784);
		animation: iconPulse 3s ease-in-out infinite;
	}

	.title-icon svg {
		width: 100%;
		height: 100%;
	}

	@keyframes iconPulse {
		0%, 100% { transform: scale(1); filter: drop-shadow(0 0 10px #16c784); }
		50% { transform: scale(1.05); filter: drop-shadow(0 0 20px #16c784); }
	}

	.title-text h1 {
		margin: 0;
		font-size: 1.3rem;
		color: #16c784;
		text-shadow: 0 0 15px #16c784;
		letter-spacing: 0.1em;
		font-weight: 700;
	}

	.title-text p {
		margin: 0.2rem 0 0 0;
		font-size: 0.75rem;
		color: #b8a678;
		text-transform: uppercase;
		letter-spacing: 0.15em;
	}

	.metrics-row {
		display: flex;
		gap: 0.8rem;
	}

	.metric-card {
		flex: 1;
		background: #111;
		border: 1px solid #1e3a5f;
		border-radius: 4px;
		padding: 0.6rem;
		text-align: center;
		transition: all 0.2s ease;
	}

	.metric-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(22, 199, 132, 0.2);
		border-color: #16c784;
	}

	.metric-card.primary {
		border-color: #16c784;
		background: linear-gradient(135deg, #111, #0a1f0a);
	}

	.metric-card.critical {
		border-color: #dc2626;
		background: linear-gradient(135deg, #111, #1f0a0a);
	}

	.metric-value {
		font-size: 1.2rem;
		font-weight: 700;
		color: #16c784;
		text-shadow: 0 0 12px currentColor;
	}

	.metric-label {
		font-size: 0.6rem;
		color: #b8a678;
		margin-top: 0.2rem;
		letter-spacing: 0.1em;
		font-weight: 600;
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
		background: #0a0a0a;
		border: 1px solid #1e3a5f;
		border-radius: 6px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		overflow-y: auto;
		min-width: 300px;
	}

	.panel-header {
		padding: 0.8rem;
		border-bottom: 1px solid #1e3a5f;
		background: #111;
	}

	.panel-header h3 {
		margin: 0 0 0.5rem 0;
		font-size: 0.85rem;
		color: #16c784;
		letter-spacing: 0.1em;
		font-weight: 600;
	}

	.controls {
		display: flex;
		gap: 0.8rem;
		align-items: center;
	}

	.search-input {
		flex: 1;
		background: #000;
		border: 1px solid #1e3a5f;
		border-radius: 4px;
		padding: 0.4rem 0.8rem;
		color: #fff;
		font-size: 0.75rem;
	}

	.search-input:focus {
		outline: none;
		border-color: #16c784;
		box-shadow: 0 0 10px rgba(22, 199, 132, 0.3);
	}

	.view-toggle {
		display: flex;
		gap: 0.2rem;
	}

	.toggle-btn {
		background: #000;
		border: 1px solid #1e3a5f;
		color: #b8a678;
		padding: 0.3rem 0.6rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.65rem;
		transition: all 0.2s ease;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.toggle-btn.active {
		background: #16c784;
		border-color: #16c784;
		color: #000;
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
		background: #111;
		color: #16c784;
		padding: 0.6rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 2px solid #16c784;
	}

	.data-table td {
		padding: 0.5rem 0.6rem;
		border-bottom: 1px solid #1a1a1a;
		color: #fff;
	}

	.data-table tr:hover {
		background: rgba(22, 199, 132, 0.05);
	}

	.source-cell .cell-content {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.indicator {
		width: 8px;
		height: 8px;
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
		background: #1a1a1a;
		border-radius: 3px;
		overflow: hidden;
		min-width: 60px;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 10px currentColor;
	}

	.coverage-text {
		font-size: 0.65rem;
		min-width: 45px;
		text-align: right;
		color: #b8a678;
	}

	.threat-badge {
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		font-size: 0.65rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.threat-badge.critical {
		background: #dc2626;
		color: #fff;
		border: 1px solid #dc2626;
	}

	.threat-badge.high {
		background: #ea580c;
		color: #fff;
		border: 1px solid #ea580c;
	}

	.threat-badge.medium {
		background: #ca8a04;
		color: #fff;
		border: 1px solid #ca8a04;
	}

	.threat-badge.secure {
		background: #16c784;
		color: #000;
		border: 1px solid #16c784;
	}

	.drill-btn {
		background: #16c784;
		border: none;
		color: #000;
		padding: 0.25rem 0.6rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.65rem;
		transition: all 0.2s ease;
		font-weight: 700;
		text-transform: uppercase;
	}

	.drill-btn:hover {
		background: #1e3a5f;
		color: #fff;
		transform: translateX(2px);
	}

	.grid-container {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 0.8rem;
		padding: 0.8rem;
		overflow-y: auto;
		flex: 1;
	}

	.grid-card {
		background: #111;
		border: 2px solid var(--card-color);
		border-radius: 6px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.2s ease;
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
		color: var(--card-color);
	}

	.threat-indicator {
		font-size: 0.6rem;
		padding: 0.15rem 0.4rem;
		border-radius: 3px;
		font-weight: 600;
		text-transform: uppercase;
	}

	.threat-indicator.critical {
		background: #dc2626;
		color: #fff;
	}

	.threat-indicator.high {
		background: #ea580c;
		color: #fff;
	}

	.threat-indicator.medium {
		background: #ca8a04;
		color: #fff;
	}

	.threat-indicator.secure {
		background: #16c784;
		color: #000;
	}

	.card-body {
		text-align: center;
	}

	.source-name {
		font-size: 0.75rem;
		color: #fff;
		margin-bottom: 0.4rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.source-count {
		font-size: 1.3rem;
		font-weight: 700;
		color: var(--card-color);
		text-shadow: 0 0 10px var(--card-color);
		margin-bottom: 0.4rem;
	}

	.progress-bar {
		width: 100%;
		height: 4px;
		background: #1a1a1a;
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
		color: #b8a678;
	}

	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		padding: 0.6rem;
		border-top: 1px solid #1e3a5f;
		background: #111;
	}

	.pagination button {
		background: #16c784;
		border: none;
		color: #000;
		padding: 0.4rem 0.8rem;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.2s ease;
		font-size: 0.7rem;
		font-weight: 700;
	}

	.pagination button:hover:not(:disabled) {
		background: #1e3a5f;
		color: #fff;
		transform: scale(1.05);
	}

	.pagination button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.pagination span {
		font-size: 0.7rem;
		color: #b8a678;
		font-weight: 600;
	}

	.viz-card {
		background: #0a0a0a;
		border: 1px solid #1e3a5f;
		border-radius: 6px;
		padding: 0.8rem;
	}

	.viz-card h4 {
		margin: 0 0 0.8rem 0;
		font-size: 0.7rem;
		color: #16c784;
		letter-spacing: 0.1em;
		text-align: center;
		font-weight: 700;
		text-transform: uppercase;
	}

	.threat-chart {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.threat-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.threat-label {
		font-size: 0.65rem;
		color: #b8a678;
		min-width: 60px;
		font-weight: 600;
	}

	.threat-bar-container {
		flex: 1;
		height: 8px;
		background: #1a1a1a;
		border-radius: 4px;
		overflow: hidden;
	}

	.threat-bar {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 8px currentColor;
	}

	.threat-count {
		font-size: 0.65rem;
		color: #fff;
		min-width: 20px;
		text-align: right;
		font-weight: 700;
	}

	.bar-chart {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.bar-item {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.bar-label {
		font-size: 0.65rem;
		color: #b8a678;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.bar-container {
		position: relative;
		height: 18px;
		background: #1a1a1a;
		border-radius: 4px;
		overflow: hidden;
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

	.bar-value {
		position: absolute;
		right: 0.4rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.6rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 4px #000;
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
		border: 2px solid;
		border-radius: 4px;
		padding: 0.3rem;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.matrix-cell:hover {
		transform: scale(1.05);
		box-shadow: 0 0 15px currentColor;
	}

	.cell-value {
		font-size: 0.7rem;
		font-weight: 700;
		color: #fff;
	}

	.cell-label {
		font-size: 0.5rem;
		color: #b8a678;
		margin-top: 0.1rem;
		letter-spacing: 0.05em;
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
		border: 3px solid #1e3a5f;
		border-top-color: #16c784;
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

	@keyframes shimmer {
		to { left: 100%; }
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
		border-bottom: 2px solid #dc2626;
		background: linear-gradient(135deg, #1f0a0a, #111);
	}

	.drill-header h4 {
		margin: 0;
		color: #dc2626;
		font-size: 0.9rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		font-weight: 700;
	}

	.close-btn {
		background: #dc2626;
		border: none;
		color: #fff;
		width: 28px;
		height: 28px;
		border-radius: 4px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
		font-size: 0.8rem;
		font-weight: 700;
	}

	.close-btn:hover {
		background: #b91c1c;
		transform: rotate(90deg);
	}

	.host-cell {
		font-family: 'Courier New', monospace;
		color: #16c784;
		font-size: 0.7rem;
		font-weight: 600;
	}

	.status-badge {
		padding: 0.15rem 0.3rem;
		border-radius: 3px;
		font-size: 0.6rem;
		font-weight: 700;
	}

	.status-badge.active {
		background: #16c784;
		color: #000;
	}

	.status-badge.inactive {
		background: #dc2626;
		color: #fff;
	}

	::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}

	::-webkit-scrollbar-track {
		background: #0a0a0a;
		border-radius: 4px;
	}

	::-webkit-scrollbar-thumb {
		background: #16c784;
		border-radius: 4px;
	}

	::-webkit-scrollbar-thumb:hover {
		background: #1e3a5f;
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
</style>