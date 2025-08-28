<!-- SourceTables.svelte - Enhanced Infrastructure Matrix Style -->
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
		if (!data.total_mentions) return { level: 'LOW', color: '#00ffff', intensity: 0.3 };
		let percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRITICAL', color: '#ff00ff', intensity: 1.0 };
		if (percentage >= 10) return { level: 'HIGH', color: '#ff0066', intensity: 0.8 };
		if (percentage >= 5) return { level: 'MEDIUM', color: '#ffaa00', intensity: 0.6 };
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

<div class="matrix-container">
	<!-- Enhanced Header -->
	<div class="matrix-header">
		<div class="header-grid">
			<div class="title-section">
				<div class="matrix-icon">◈</div>
				<div class="title-content">
					<h1>SOURCE INTELLIGENCE MATRIX</h1>
					<p>Comma-Separated Frequency Analysis</p>
				</div>
			</div>
			
			<div class="stats-grid">
				<div class="stat-card">
					<div class="stat-value">{(data.unique_sources || 0).toLocaleString()}</div>
					<div class="stat-label">UNIQUE SOURCES</div>
					<div class="stat-indicator" style="background: #00ffff"></div>
				</div>
				<div class="stat-card">
					<div class="stat-value">{(data.total_mentions || 0).toLocaleString()}</div>
					<div class="stat-label">TOTAL MENTIONS</div>
					<div class="stat-indicator" style="background: #00ff85"></div>
				</div>
				<div class="stat-card">
					<div class="stat-value">{Math.round((data.total_mentions || 0) / (data.unique_sources || 1))}</div>
					<div class="stat-label">AVG/SOURCE</div>
					<div class="stat-indicator" style="background: #ffaa00"></div>
				</div>
				<div class="stat-card critical">
					<div class="stat-value">{threatDistribution['CRITICAL'] || 0}</div>
					<div class="stat-label">CRITICAL</div>
					<div class="stat-indicator" style="background: #ff00ff"></div>
				</div>
			</div>
		</div>
	</div>

	<!-- Control Panel -->
	<div class="control-panel">
		<div class="search-section">
			<div class="search-wrapper">
				<span class="search-icon">⚡</span>
				<input 
					type="text" 
					bind:value={searchTerm}
					placeholder="Neural search..."
					class="search-input"
				/>
			</div>
		</div>
		<div class="view-controls">
			<button class="view-btn {viewMode === 'grid' ? 'active' : ''}" on:click={() => viewMode = 'grid'}>
				<span class="btn-icon">◈</span> MATRIX
			</button>
			<button class="view-btn {viewMode === 'table' ? 'active' : ''}" on:click={() => viewMode = 'table'}>
				<span class="btn-icon">☰</span> TABLE
			</button>
			<button class="view-btn {viewMode === 'chart' ? 'active' : ''}" on:click={() => viewMode = 'chart'}>
				<span class="btn-icon">📊</span> ANALYTICS
			</button>
		</div>
	</div>

	<!-- Main Content Area -->
	<div class="content-area">
		{#if loading && !selectedSource}
			<div class="loading-state">
				<div class="neural-loader">
					<div class="loader-ring"></div>
					<div class="loader-core">◈</div>
				</div>
				<p>Analyzing neural pathways...</p>
			</div>
		{:else if selectedSource}
			<!-- Drill-down View -->
			<div class="drill-panel">
				<div class="drill-header">
					<div class="drill-title">
						<span class="drill-icon">◈</span>
						<h3>{selectedSource.source.toUpperCase()}</h3>
						<span class="drill-badge">{selectedSource.frequency} MENTIONS</span>
					</div>
					<button class="close-btn" on:click={closeDetails}>
						<span>✕</span>
					</button>
				</div>
				<div class="drill-content">
					<table class="drill-table">
						<thead>
							<tr>
								<th>HOST IDENTIFIER</th>
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
										<span class="host-icon">▶</span>
										{host.host}
									</td>
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
		{:else if viewMode === 'grid'}
			<!-- Matrix Grid View -->
			<div class="matrix-grid">
				{#each paginatedSources as [source, frequency]}
					{@const threat = getThreatLevel(frequency)}
					<div class="matrix-card" 
						style="--card-color: {threat.color}; --card-intensity: {threat.intensity}"
						on:click={() => drillDownSource(source, frequency)}>
						<div class="card-header">
							<span class="card-icon">◈</span>
							<span class="threat-level {threat.level.toLowerCase()}">{threat.level}</span>
						</div>
						<div class="card-body">
							<div class="source-name">{source.toUpperCase()}</div>
							<div class="frequency-display">
								<span class="frequency-value">{frequency.toLocaleString()}</span>
								<span class="frequency-label">MENTIONS</span>
							</div>
							<div class="visual-meter">
								<div class="meter-fill" style="width: {(frequency/maxFreq)*100}%"></div>
							</div>
							<div class="card-stats">
								<span class="stat-item">
									<span class="stat-icon">◉</span>
									{getPercentage(frequency)}%
								</span>
							</div>
						</div>
						<div class="card-glow"></div>
					</div>
				{/each}
			</div>
		{:else if viewMode === 'table'}
			<!-- Table View -->
			<div class="data-table-container">
				<table class="data-table">
					<thead>
						<tr>
							<th>SOURCE</th>
							<th>FREQUENCY</th>
							<th>COVERAGE</th>
							<th>THREAT LEVEL</th>
							<th>ACTION</th>
						</tr>
					</thead>
					<tbody>
						{#each paginatedSources as [source, frequency]}
							{@const threat = getThreatLevel(frequency)}
							<tr class="table-row">
								<td class="source-cell">
									<span class="cell-icon" style="color: {threat.color}">◈</span>
									<span>{source.toUpperCase()}</span>
								</td>
								<td class="center">
									<span class="frequency-badge">{frequency.toLocaleString()}</span>
								</td>
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
									<button class="action-btn" on:click={() => drillDownSource(source, frequency)}>
										ANALYZE <span class="action-arrow">→</span>
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
				<div class="chart-container">
					<h3>THREAT DISTRIBUTION</h3>
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
									{@const color = level === 'CRITICAL' ? '#ff00ff' : 
										level === 'HIGH' ? '#ff0066' : 
										level === 'MEDIUM' ? '#ffaa00' : '#00ffff'}
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
								{filteredSources.length}
							</text>
							<text x="100" y="115" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="10">
								SOURCES
							</text>
						</svg>
					</div>
				</div>
				<div class="top-sources">
					<h3>TOP 5 SOURCES</h3>
					{#each filteredSources.slice(0, 5) as [source, frequency]}
						{@const threat = getThreatLevel(frequency)}
						<div class="source-bar">
							<div class="source-label">{source.toUpperCase()}</div>
							<div class="bar-container">
								<div class="bar-fill" 
									style="width: {(frequency/maxFreq)*100}%; background: linear-gradient(90deg, {threat.color}, {threat.color}80)">
									<span class="bar-value">{frequency}</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
		
		<!-- Pagination -->
		{#if !selectedSource && viewMode !== 'chart'}
			<div class="pagination">
				<button 
					class="page-btn"
					on:click={() => currentPage = Math.max(1, currentPage - 1)}
					disabled={currentPage === 1}
				>
					<span>◀</span>
				</button>
				<div class="page-info">
					<span class="page-current">{currentPage}</span>
					<span class="page-separator">/</span>
					<span class="page-total">{totalPages}</span>
				</div>
				<button 
					class="page-btn"
					on:click={() => currentPage = Math.min(totalPages, currentPage + 1)}
					disabled={currentPage === totalPages}
				>
					<span>▶</span>
				</button>
			</div>
		{/if}
	</div>
</div>

<style>
	.matrix-container {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, rgba(0,0,0,0.95) 0%, rgba(26,13,46,0.95) 100%);
		color: #fff;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
	}

	/* Enhanced Header */
	.matrix-header {
		background: rgba(0, 0, 0, 0.8);
		border-bottom: 2px solid rgba(0, 255, 255, 0.3);
		padding: 1rem 1.5rem;
		backdrop-filter: blur(10px);
	}

	.header-grid {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 2rem;
	}

	.title-section {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.matrix-icon {
		font-size: 2.5rem;
		color: #00ffff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
		animation: iconPulse 3s ease-in-out infinite;
	}

	@keyframes iconPulse {
		0%, 100% { transform: scale(1); opacity: 0.9; }
		50% { transform: scale(1.1); opacity: 1; }
	}

	.title-content h1 {
		margin: 0;
		font-size: 1.3rem;
		color: #00ffff;
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.title-content p {
		margin: 0.2rem 0 0 0;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.stats-grid {
		display: flex;
		gap: 1.5rem;
	}

	.stat-card {
		background: rgba(0, 255, 255, 0.05);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 8px;
		padding: 0.8rem 1.2rem;
		text-align: center;
		position: relative;
		overflow: hidden;
		transition: all 0.3s ease;
	}

	.stat-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(0, 255, 255, 0.2);
	}

	.stat-card.critical {
		background: rgba(255, 0, 255, 0.05);
		border-color: rgba(255, 0, 255, 0.3);
	}

	.stat-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 10px currentColor;
	}

	.stat-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.2rem;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}

	.stat-indicator {
		position: absolute;
		bottom: 0;
		left: 0;
		width: 100%;
		height: 3px;
		opacity: 0.8;
	}

	/* Control Panel */
	.control-panel {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
		background: rgba(0, 0, 0, 0.6);
		border-bottom: 1px solid rgba(0, 255, 255, 0.2);
	}

	.search-section {
		flex: 1;
		max-width: 400px;
	}

	.search-wrapper {
		position: relative;
		display: flex;
		align-items: center;
	}

	.search-icon {
		position: absolute;
		left: 1rem;
		color: #00ffff;
		font-size: 1.2rem;
		animation: searchPulse 2s ease-in-out infinite;
	}

	@keyframes searchPulse {
		0%, 100% { opacity: 0.6; }
		50% { opacity: 1; }
	}

	.search-input {
		width: 100%;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 8px;
		padding: 0.8rem 1rem 0.8rem 3rem;
		color: #fff;
		font-size: 0.8rem;
		transition: all 0.3s ease;
	}

	.search-input:focus {
		outline: none;
		border-color: #00ffff;
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
		background: rgba(0, 0, 0, 0.9);
	}

	.search-input::placeholder {
		color: rgba(255, 255, 255, 0.3);
	}

	.view-controls {
		display: flex;
		gap: 0.5rem;
	}

	.view-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		color: rgba(255, 255, 255, 0.6);
		padding: 0.6rem 1rem;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.3s ease;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.view-btn:hover {
		background: rgba(0, 255, 255, 0.1);
		border-color: rgba(0, 255, 255, 0.3);
		color: #00ffff;
		transform: translateY(-2px);
	}

	.view-btn.active {
		background: rgba(0, 255, 255, 0.15);
		border-color: #00ffff;
		color: #00ffff;
		box-shadow: 0 4px 15px rgba(0, 255, 255, 0.3);
	}

	.btn-icon {
		font-size: 1rem;
	}

	/* Content Area */
	.content-area {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: 1.5rem;
		overflow: hidden;
		min-height: 0;
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

	.neural-loader {
		position: relative;
		width: 80px;
		height: 80px;
	}

	.loader-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 3px solid rgba(0, 255, 255, 0.1);
		border-top-color: #00ffff;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.loader-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 2rem;
		color: #00ffff;
		animation: pulse 2s ease-in-out infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@keyframes pulse {
		0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(0.9); }
		50% { opacity: 1; transform: translate(-50%, -50%) scale(1.1); }
	}

	/* Matrix Grid */
	.matrix-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1.2rem;
		flex: 1;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.matrix-card {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.7));
		border: 2px solid var(--card-color);
		border-radius: 12px;
		padding: 1.2rem;
		cursor: pointer;
		transition: all 0.3s ease;
		position: relative;
		overflow: hidden;
	}

	.matrix-card:hover {
		transform: translateY(-5px) scale(1.02);
		box-shadow: 
			0 10px 30px rgba(0, 0, 0, 0.5),
			0 0 30px color-mix(in srgb, var(--card-color) 40%, transparent);
	}

	.card-glow {
		position: absolute;
		top: -50%;
		left: -50%;
		width: 200%;
		height: 200%;
		background: radial-gradient(circle, var(--card-color), transparent);
		opacity: 0;
		transition: opacity 0.3s ease;
		pointer-events: none;
		filter: blur(40px);
	}

	.matrix-card:hover .card-glow {
		opacity: calc(var(--card-intensity) * 0.3);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.8rem;
	}

	.card-icon {
		font-size: 1.5rem;
		color: var(--card-color);
		filter: drop-shadow(0 0 10px var(--card-color));
	}

	.threat-level {
		font-size: 0.6rem;
		padding: 0.3rem 0.6rem;
		border-radius: 6px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.threat-level.critical {
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
	}

	.threat-level.high {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.threat-level.medium {
		background: rgba(255, 170, 0, 0.2);
		color: #ffaa00;
		border: 1px solid #ffaa00;
	}

	.threat-level.low {
		background: rgba(0, 255, 255, 0.2);
		color: #00ffff;
		border: 1px solid #00ffff;
	}

	.card-body {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.source-name {
		font-size: 0.9rem;
		font-weight: 600;
		color: #fff;
		letter-spacing: 0.05em;
	}

	.frequency-display {
		display: flex;
		align-items: baseline;
		gap: 0.5rem;
	}

	.frequency-value {
		font-size: 1.8rem;
		font-weight: 700;
		color: var(--card-color);
		text-shadow: 0 0 15px var(--card-color);
	}

	.frequency-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.visual-meter {
		width: 100%;
		height: 6px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 3px;
		overflow: hidden;
		position: relative;
	}

	.meter-fill {
		height: 100%;
		background: linear-gradient(90deg, var(--card-color), color-mix(in srgb, var(--card-color) 60%, transparent));
		transition: width 0.5s ease;
		box-shadow: 0 0 10px var(--card-color);
	}

	.card-stats {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.stat-item {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.7);
	}

	.stat-icon {
		color: var(--card-color);
		font-size: 0.6rem;
	}

	/* Table View */
	.data-table-container {
		flex: 1;
		overflow: auto;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 12px;
		padding: 1rem;
	}

	.data-table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0 0.5rem;
	}

	.data-table thead th {
		background: rgba(0, 255, 255, 0.1);
		color: #00ffff;
		padding: 1rem;
		text-align: left;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		border: 1px solid rgba(0, 255, 255, 0.2);
	}

	.data-table thead th:first-child {
		border-top-left-radius: 8px;
		border-bottom-left-radius: 8px;
	}

	.data-table thead th:last-child {
		border-top-right-radius: 8px;
		border-bottom-right-radius: 8px;
	}

	.table-row {
		background: rgba(0, 0, 0, 0.3);
		transition: all 0.3s ease;
	}

	.table-row:hover {
		background: rgba(0, 255, 255, 0.05);
		transform: translateX(5px);
	}

	.data-table td {
		padding: 0.8rem 1rem;
		color: rgba(255, 255, 255, 0.8);
		font-size: 0.8rem;
		border-top: 1px solid rgba(255, 255, 255, 0.05);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}

	.data-table td:first-child {
		border-left: 1px solid rgba(255, 255, 255, 0.05);
		border-top-left-radius: 8px;
		border-bottom-left-radius: 8px;
	}

	.data-table td:last-child {
		border-right: 1px solid rgba(255, 255, 255, 0.05);
		border-top-right-radius: 8px;
		border-bottom-right-radius: 8px;
	}

	.source-cell {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		font-weight: 600;
	}

	.cell-icon {
		font-size: 1.2rem;
		filter: drop-shadow(0 0 5px currentColor);
	}

	.center {
		text-align: center;
	}

	.frequency-badge {
		display: inline-block;
		padding: 0.4rem 0.8rem;
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 6px;
		color: #00ffff;
		font-weight: 600;
	}

	.coverage-cell {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.coverage-bar {
		flex: 1;
		height: 8px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
		overflow: hidden;
		min-width: 100px;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 10px currentColor;
	}

	.coverage-text {
		min-width: 50px;
		text-align: right;
		font-weight: 600;
	}

	.threat-badge {
		padding: 0.4rem 0.8rem;
		border-radius: 6px;
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
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

	.action-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.05));
		border: 1px solid #00ffff;
		color: #00ffff;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		transition: all 0.3s ease;
	}

	.action-btn:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 255, 255, 0.1));
		transform: translateX(3px);
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
	}

	.action-arrow {
		font-size: 0.9rem;
		transition: transform 0.3s ease;
	}

	.action-btn:hover .action-arrow {
		transform: translateX(3px);
	}

	/* Analytics View */
	.analytics-view {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		overflow: auto;
	}

	.chart-container, .top-sources {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 12px;
		padding: 1.5rem;
	}

	.chart-container h3, .top-sources h3 {
		margin: 0 0 1.5rem 0;
		color: #00ffff;
		font-size: 0.9rem;
		text-align: center;
		letter-spacing: 0.1em;
	}

	.donut-chart {
		width: 100%;
		max-width: 300px;
		margin: 0 auto;
	}

	.source-bar {
		margin-bottom: 1.2rem;
	}

	.source-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
		margin-bottom: 0.4rem;
		font-weight: 600;
	}

	.bar-container {
		position: relative;
		height: 24px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 6px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding-right: 0.5rem;
		position: relative;
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
		font-size: 0.7rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 0 0 5px rgba(0, 0, 0, 0.8);
	}

	/* Drill Panel */
	.drill-panel {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 2px solid rgba(255, 0, 102, 0.3);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.drill-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
		background: rgba(255, 0, 102, 0.05);
		border-bottom: 1px solid rgba(255, 0, 102, 0.2);
	}

	.drill-title {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.drill-icon {
		font-size: 1.5rem;
		color: #ff0066;
		filter: drop-shadow(0 0 10px #ff0066);
	}

	.drill-title h3 {
		margin: 0;
		color: #ff0066;
		font-size: 1rem;
		letter-spacing: 0.05em;
	}

	.drill-badge {
		padding: 0.4rem 0.8rem;
		background: rgba(255, 0, 102, 0.1);
		border: 1px solid rgba(255, 0, 102, 0.3);
		border-radius: 6px;
		color: #ff0066;
		font-size: 0.7rem;
		font-weight: 600;
	}

	.close-btn {
		width: 32px;
		height: 32px;
		background: transparent;
		border: 2px solid #ff0066;
		color: #ff0066;
		border-radius: 50%;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.3s ease;
		font-size: 1.2rem;
	}

	.close-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: rotate(90deg);
		box-shadow: 0 0 20px rgba(255, 0, 102, 0.4);
	}

	.drill-content {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}

	.drill-table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0 0.5rem;
	}

	.drill-table thead th {
		background: rgba(255, 0, 102, 0.05);
		color: #ff0066;
		padding: 0.8rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		border: 1px solid rgba(255, 0, 102, 0.2);
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.drill-table tbody tr {
		background: rgba(0, 0, 0, 0.3);
		transition: all 0.3s ease;
	}

	.drill-table tbody tr:hover {
		background: rgba(255, 0, 102, 0.05);
	}

	.drill-table td {
		padding: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
		font-size: 0.75rem;
		border-top: 1px solid rgba(255, 255, 255, 0.05);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}

	.host-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-family: monospace;
		color: #00ffff;
	}

	.host-icon {
		color: #ff0066;
		font-size: 0.8rem;
	}

	.status-badge {
		padding: 0.3rem 0.6rem;
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

	/* Pagination */
	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		padding: 1rem 0;
		margin-top: auto;
	}

	.page-btn {
		width: 40px;
		height: 40px;
		background: rgba(0, 255, 255, 0.1);
		border: 2px solid rgba(0, 255, 255, 0.3);
		color: #00ffff;
		border-radius: 8px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.3s ease;
		font-size: 1.2rem;
	}

	.page-btn:hover:not(:disabled) {
		background: rgba(0, 255, 255, 0.2);
		transform: scale(1.1);
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
	}

	.page-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.page-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 8px;
	}

	.page-current {
		font-size: 1.2rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 10px #00ffff;
	}

	.page-separator {
		color: rgba(255, 255, 255, 0.3);
	}

	.page-total {
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.9rem;
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
		background: linear-gradient(180deg, #00ffff, #ff00ff);
		border-radius: 4px;
	}

	::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(180deg, #ff00ff, #00ffff);
	}

	/* Responsive */
	@media (max-width: 1400px) {
		.matrix-grid {
			grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		}
		
		.stats-grid {
			gap: 1rem;
		}
		
		.stat-card {
			padding: 0.6rem 1rem;
		}
		
		.stat-value {
			font-size: 1.2rem;
		}
	}

	@media (max-width: 1200px) {
		.header-grid {
			flex-direction: column;
			align-items: flex-start;
		}
		
		.analytics-view {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 768px) {
		.control-panel {
			flex-direction: column;
			gap: 1rem;
			align-items: stretch;
		}
		
		.search-section {
			max-width: 100%;
		}
		
		.view-controls {
			justify-content: center;
		}
		
		.matrix-grid {
			grid-template-columns: 1fr;
		}
		
		.stats-grid {
			flex-wrap: wrap;
		}
		
		.stat-card {
			min-width: calc(50% - 0.5rem);
		}
	}