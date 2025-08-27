<!-- Enhanced SourceTables.svelte with rich dashboard layout -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';

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

	function getThreatLevel(frequency) {
		if (!data.total_mentions) return { level: 'LOW', color: '#0096ff', intensity: 0.3 };
		let percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRIT', color: '#ff00ff', intensity: 1.0 };
		if (percentage >= 10) return { level: 'HIGH', color: '#ff0066', intensity: 0.8 };
		if (percentage >= 5) return { level: 'MED', color: '#ffaa00', intensity: 0.6 };
		return { level: 'LOW', color: '#00ffff', intensity: 0.4 };
	}

	function getPercentage(frequency) {
		if (!data.total_mentions) return '0.00';
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

<div class="source-intelligence-dashboard">
	<!-- Dashboard Header with Key Metrics -->
	<div class="dashboard-header">
		<div class="header-grid">
			<div class="metric-card primary">
				<div class="metric-icon">◈</div>
				<div class="metric-content">
					<div class="metric-value">{(data.unique_sources || 0).toLocaleString()}</div>
					<div class="metric-label">UNIQUE SOURCES</div>
				</div>
				<div class="metric-trend">
					<div class="trend-indicator up">↗</div>
					<span class="trend-value">+12%</span>
				</div>
			</div>

			<div class="metric-card secondary">
				<div class="metric-icon">⬢</div>
				<div class="metric-content">
					<div class="metric-value">{(data.total_mentions || 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL MENTIONS</div>
				</div>
				<div class="metric-trend">
					<div class="trend-indicator up">↗</div>
					<span class="trend-value">+8%</span>
				</div>
			</div>

			<div class="metric-card tertiary">
				<div class="metric-icon">◉</div>
				<div class="metric-content">
					<div class="metric-value">{Math.round((data.total_mentions || 0) / (data.unique_sources || 1))}</div>
					<div class="metric-label">AVG/SOURCE</div>
				</div>
				<div class="metric-trend">
					<div class="trend-indicator neutral">→</div>
					<span class="trend-value">STABLE</span>
				</div>
			</div>

			<div class="metric-card quaternary">
				<div class="metric-icon">⚡</div>
				<div class="metric-content">
					<div class="metric-value">{filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'CRIT').length}</div>
					<div class="metric-label">CRITICAL SOURCES</div>
				</div>
				<div class="metric-trend">
					<div class="trend-indicator down">↘</div>
					<span class="trend-value">-3%</span>
				</div>
			</div>
		</div>

		<!-- Search and Controls -->
		<div class="controls-section">
			<div class="search-matrix">
				<div class="search-container">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="SCAN SOURCE TABLES..."
						class="neural-search"
					/>
					<div class="search-scanner"></div>
				</div>
				<button class="refresh-btn" on:click={() => location.reload()}>
					<span class="btn-icon">⟲</span>
					REFRESH
				</button>
			</div>
		</div>
	</div>

	{#if loading && !selectedSource}
		<div class="loading-matrix">
			<div class="neural-core">
				{#each Array(3) as _, i}
					<div class="pulse-ring" style="--delay: {i * 0.2}s; --size: {40 + i * 15}px"></div>
				{/each}
			</div>
			<div class="loading-text">NEURAL SCANNING...</div>
		</div>
	{:else if selectedSource}
		<!-- Drill-down View -->
		<div class="drill-interface">
			<div class="drill-header">
				<div class="drill-info">
					<div class="drill-badge" style="--threat-color: {getThreatLevel(selectedSource.frequency).color}">
						{getThreatLevel(selectedSource.frequency).level}
					</div>
					<h2>{selectedSource.source}</h2>
					<div class="drill-stats">
						<span>FREQ: {selectedSource.frequency.toLocaleString()}</span>
						<span>COV: {getPercentage(selectedSource.frequency)}%</span>
					</div>
				</div>
				<button class="close-drill" on:click={closeDetails}>
					<span>✕</span>
				</button>
			</div>

			{#if loading}
				<div class="scanning-hosts">
					<div class="host-scanner">
						{#each Array(9) as _, i}
							<div class="scan-node" style="animation-delay: {i * 0.1}s"></div>
						{/each}
					</div>
					<p>RETRIEVING HOST MATRIX...</p>
				</div>
			{:else}
				<div class="host-data-table">
					<div class="table-container">
						<table class="cyber-table">
							<thead>
								<tr>
									<th>HOST DESIGNATION</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>INFRA TYPE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each hostDetails.slice(0, 50) as host, i}
									<tr style="animation-delay: {i * 0.02}s">
										<td class="host-cell">{host.host}</td>
										<td>{host.region}</td>
										<td>{host.country}</td>
										<td>{host.infrastructure_type}</td>
										<td>
											<span class="status-chip {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'ACTIVE' : 'OFFLINE'}
											</span>
										</td>
										<td>
											<span class="status-chip {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? 'DEPLOYED' : 'MISSING'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{/if}
		</div>
	{:else}
		<!-- Main Dashboard View -->
		<div class="main-dashboard">
			<!-- Left Panel - Data Table -->
			<div class="data-panel">
				<div class="panel-header">
					<h3>SOURCE INTELLIGENCE MATRIX</h3>
					<div class="panel-controls">
						<span class="record-count">SHOWING {Math.min(filteredSources.length, 20)} OF {filteredSources.length}</span>
					</div>
				</div>

				<div class="source-table-container">
					<table class="source-table">
						<thead>
							<tr>
								<th>SOURCE TABLE</th>
								<th>FREQUENCY</th>
								<th>COVERAGE %</th>
								<th>THREAT</th>
								<th>ACTION</th>
							</tr>
						</thead>
						<tbody>
							{#each filteredSources.slice(0, 20) as [source, frequency], i}
								<tr style="--threat-color: {getThreatLevel(frequency).color}; animation-delay: {i * 0.02}s">
									<td class="source-cell">
										<div class="source-indicator" style="background: {getThreatLevel(frequency).color}"></div>
										<span class="source-name">{source}</span>
									</td>
									<td class="frequency-cell">
										<span class="frequency-value">{frequency.toLocaleString()}</span>
									</td>
									<td class="coverage-cell">
										<div class="coverage-bar">
											<div class="coverage-fill" style="width: {getPercentage(frequency)}%; background: {getThreatLevel(frequency).color};"></div>
										</div>
										<span class="coverage-text">{getPercentage(frequency)}%</span>
									</td>
									<td class="threat-cell">
										<span class="threat-badge" 
											  style="color: {getThreatLevel(frequency).color}; border-color: {getThreatLevel(frequency).color};">
											{getThreatLevel(frequency).level}
										</span>
									</td>
									<td class="action-cell">
										<button class="drill-btn" on:click={() => drillDownSource(source, frequency)}>
											<span class="drill-icon">⚡</span>
											DRILL
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>

			<!-- Right Panel - Analytics and Visualization -->
			<div class="analytics-panel">
				<!-- Distribution Chart -->
				<div class="chart-container">
					<div class="chart-header">
						<h4>THREAT DISTRIBUTION</h4>
						<div class="chart-controls">
							<button class="chart-btn active">PIE</button>
							<button class="chart-btn">BAR</button>
						</div>
					</div>
					
					<div class="threat-chart">
						<div class="chart-visual">
							{#if filteredSources.length > 0}
								{@const criticalSources = filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'CRIT')}
								{@const highSources = filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'HIGH')}
								{@const mediumSources = filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'MED')}
								{@const lowSources = filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'LOW')}
								
								{@const criticalCount = criticalSources.length}
								{@const highCount = highSources.length}
								{@const mediumCount = mediumSources.length}
								{@const lowCount = lowSources.length}
								{@const totalCount = criticalCount + highCount + mediumCount + lowCount}
							
							<div class="pie-chart">
								<div class="pie-slice critical" style="--percentage: {totalCount > 0 ? (criticalCount/totalCount*100).toFixed(1) : 0}%"></div>
								<div class="pie-slice high" style="--percentage: {totalCount > 0 ? (highCount/totalCount*100).toFixed(1) : 0}%"></div>
								<div class="pie-slice medium" style="--percentage: {totalCount > 0 ? (mediumCount/totalCount*100).toFixed(1) : 0}%"></div>
								<div class="pie-slice low" style="--percentage: {totalCount > 0 ? (lowCount/totalCount*100).toFixed(1) : 0}%"></div>
								<div class="pie-center">{totalCount}</div>
							</div>
						{:else}
							<div class="pie-chart">
								<div class="pie-center">0</div>
							</div>
						{/if}
						</div>
						
						<div class="chart-legend">
							{#if filteredSources.length > 0}
								{@const criticalSources = filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'CRIT')}
								{@const highSources = filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'HIGH')}
								{@const mediumSources = filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'MED')}
								{@const lowSources = filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'LOW')}
								
								<div class="legend-item">
									<div class="legend-color critical"></div>
									<span>CRITICAL ({criticalSources.length})</span>
								</div>
								<div class="legend-item">
									<div class="legend-color high"></div>
									<span>HIGH ({highSources.length})</span>
								</div>
								<div class="legend-item">
									<div class="legend-color medium"></div>
									<span>MEDIUM ({mediumSources.length})</span>
								</div>
								<div class="legend-item">
									<div class="legend-color low"></div>
									<span>LOW ({lowSources.length})</span>
								</div>
							{:else}
								<div class="legend-item">
									<div class="legend-color low"></div>
									<span>NO DATA</span>
								</div>
							{/if}
						</div>
					</div>
				</div>

				<!-- Top Sources Ranking -->
				<div class="ranking-container">
					<div class="ranking-header">
						<h4>TOP SOURCE RANKINGS</h4>
						<div class="ranking-filter">
							<select class="cyber-select">
								<option>ALL SOURCES</option>
								<option>CRITICAL ONLY</option>
								<option>HIGH RISK</option>
							</select>
						</div>
					</div>

					<div class="ranking-list">
						{#each filteredSources.slice(0, 10) as [source, frequency], i}
							<div class="rank-item" style="animation-delay: {i * 0.1}s">
								<div class="rank-position">#{i + 1}</div>
								<div class="rank-info">
									<div class="rank-name">{source}</div>
									<div class="rank-stats">
										<span class="rank-freq">{frequency.toLocaleString()}</span>
										<span class="rank-percent">{getPercentage(frequency)}%</span>
									</div>
								</div>
								<div class="rank-bar">
									<div class="bar-fill" style="width: {(frequency/filteredSources[0][1]*100)}%; background: {getThreatLevel(frequency).color};"></div>
								</div>
								<div class="rank-threat">
									<span class="threat-tag" style="color: {getThreatLevel(frequency).color}">
										{getThreatLevel(frequency).level}
									</span>
								</div>
							</div>
						{/each}
					</div>
				</div>

				<!-- System Health Monitor -->
				<div class="health-monitor">
					<div class="monitor-header">
						<h4>SYSTEM HEALTH</h4>
						<div class="health-status">
							<div class="status-light active"></div>
							<span>OPERATIONAL</span>
						</div>
					</div>

					<div class="health-metrics">
						<div class="health-item">
							<div class="health-label">Data Quality</div>
							<div class="health-bar">
								<div class="health-fill" style="width: 92%"></div>
							</div>
							<div class="health-value">92%</div>
						</div>
						<div class="health-item">
							<div class="health-label">Coverage</div>
							<div class="health-bar">
								<div class="health-fill" style="width: 87%"></div>
							</div>
							<div class="health-value">87%</div>
						</div>
						<div class="health-item">
							<div class="health-label">Threat Level</div>
							<div class="health-bar">
								<div class="health-fill critical" style="width: 23%"></div>
							</div>
							<div class="health-value">23%</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.source-intelligence-dashboard {
		width: 100%;
		height: 100%;
		font-family: 'JetBrains Mono', monospace;
		color: #fff;
		display: flex;
		flex-direction: column;
		text-transform: uppercase;
		letter-spacing: 0.02em;
		font-size: 0.7rem;
	}

	.dashboard-header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 255, 255, 0.05));
		border: 1px solid #00ffff;
		border-radius: 8px;
		padding: 1rem;
		margin-bottom: 1rem;
		backdrop-filter: blur(20px);
	}

	.header-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.metric-card {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.02));
		border: 1px solid;
		border-radius: 6px;
		padding: 1rem;
		display: flex;
		align-items: center;
		gap: 0.8rem;
		transition: all 0.3s ease;
		position: relative;
		overflow: hidden;
	}

	.metric-card.primary {
		border-color: #00ffff;
	}

	.metric-card.secondary {
		border-color: #ff00ff;
	}

	.metric-card.tertiary {
		border-color: #00ff85;
	}

	.metric-card.quaternary {
		border-color: #ff0066;
	}

	.metric-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
	}

	.metric-icon {
		font-size: 1.5rem;
		opacity: 0.8;
	}

	.metric-card.primary .metric-icon {
		color: #00ffff;
		text-shadow: 0 0 10px #00ffff;
	}

	.metric-card.secondary .metric-icon {
		color: #ff00ff;
		text-shadow: 0 0 10px #ff00ff;
	}

	.metric-card.tertiary .metric-icon {
		color: #00ff85;
		text-shadow: 0 0 10px #00ff85;
	}

	.metric-card.quaternary .metric-icon {
		color: #ff0066;
		text-shadow: 0 0 10px #ff0066;
	}

	.metric-content {
		flex: 1;
	}

	.metric-value {
		font-size: 1.3rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
		margin-bottom: 0.2rem;
	}

	.metric-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
	}

	.metric-trend {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.2rem;
	}

	.trend-indicator {
		width: 20px;
		height: 20px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.8rem;
		font-weight: bold;
	}

	.trend-indicator.up {
		background: rgba(0, 255, 133, 0.2);
		color: #00ff85;
		border: 1px solid #00ff85;
	}

	.trend-indicator.down {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.trend-indicator.neutral {
		background: rgba(255, 255, 255, 0.1);
		color: #fff;
		border: 1px solid rgba(255, 255, 255, 0.3);
	}

	.trend-value {
		font-size: 0.5rem;
		font-weight: 600;
	}

	.controls-section {
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		padding-top: 1rem;
	}

	.search-matrix {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
	}

	.search-container {
		position: relative;
		flex: 1;
		max-width: 400px;
	}

	.neural-search {
		width: 100%;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 255, 255, 0.05));
		border: 1px solid #00ffff;
		border-radius: 4px;
		padding: 0.6rem 1rem;
		color: #fff;
		font-family: inherit;
		font-size: 0.7rem;
		font-weight: 600;
		outline: none;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.neural-search::placeholder {
		color: rgba(255, 255, 255, 0.4);
		text-shadow: 0 0 4px rgba(0, 255, 255, 0.3);
	}

	.neural-search:focus {
		border-color: #00ffff;
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
	}

	.search-scanner {
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.3), transparent);
		animation: scannerSweep 3s linear infinite;
		pointer-events: none;
		border-radius: 4px;
	}

	.refresh-btn {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.05));
		border: 1px solid #00ffff;
		border-radius: 4px;
		padding: 0.6rem 1rem;
		color: #00ffff;
		font-family: inherit;
		font-size: 0.7rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		text-transform: uppercase;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		letter-spacing: 0.03em;
	}

	.refresh-btn:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 255, 255, 0.1));
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.4);
		transform: translateY(-1px);
	}

	.btn-icon {
		font-size: 0.8rem;
		animation: iconSpin 2s ease-in-out infinite;
	}

	.main-dashboard {
		flex: 1;
		display: grid;
		grid-template-columns: 2fr 1fr;
		gap: 1rem;
		min-height: 0;
	}

	.data-panel, .analytics-panel {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.02));
		border: 1px solid #00ffff;
		border-radius: 8px;
		padding: 1rem;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.panel-header h3 {
		font-size: 0.8rem;
		font-weight: 700;
		color: #00ffff;
		margin: 0;
		text-shadow: 0 0 8px #00ffff;
	}

	.record-count {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.source-table-container {
		flex: 1;
		overflow-y: auto;
	}

	.source-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.65rem;
	}

	.source-table th {
		background: rgba(0, 0, 0, 0.4);
		color: #00ffff;
		font-weight: 600;
		text-align: left;
		padding: 0.8rem 0.5rem;
		font-size: 0.6rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		text-shadow: 0 0 6px #00ffff;
	}

	.source-table td {
		padding: 0.8rem 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		animation: rowSlide 0.5s ease-out;
		animation-fill-mode: both;
	}

	.source-table tr:hover {
		background: linear-gradient(90deg, 
			rgba(0, 255, 255, 0.05), 
			rgba(255, 0, 255, 0.02), 
			transparent);
		box-shadow: inset 2px 0 0 var(--threat-color);
	}

	.source-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 600;
		color: #fff;
	}

	.source-indicator {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		box-shadow: 0 0 8px currentColor;
		animation: indicatorPulse 2s ease-in-out infinite;
		flex-shrink: 0;
	}

	.source-name {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.frequency-cell {
		text-align: center;
	}

	.frequency-value {
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 6px #00ffff;
	}

	.coverage-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.coverage-bar {
		flex: 1;
		height: 8px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
		overflow: hidden;
		border: 1px solid rgba(255, 255, 255, 0.1);
		position: relative;
	}

	.coverage-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 1s ease-out;
		box-shadow: 0 0 10px currentColor;
		position: relative;
		overflow: hidden;
	}

	.coverage-fill::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(255, 255, 255, 0.4), 
			transparent);
		animation: coverageSweep 3s linear infinite;
	}

	.coverage-text {
		font-size: 0.6rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.8);
		min-width: 35px;
		text-align: right;
	}

	.threat-cell {
		text-align: center;
	}

	.threat-badge {
		padding: 0.2rem 0.5rem;
		border: 1px solid;
		border-radius: 3px;
		font-size: 0.5rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.02em;
		background: rgba(0, 0, 0, 0.4);
		text-shadow: 0 0 6px currentColor;
		animation: badgeGlow 3s ease-in-out infinite;
	}

	.action-cell {
		text-align: center;
	}

	.drill-btn {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.05));
		border: 1px solid #00ffff;
		border-radius: 3px;
		padding: 0.3rem 0.6rem;
		color: #00ffff;
		font-family: inherit;
		font-size: 0.6rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		text-transform: uppercase;
		display: flex;
		align-items: center;
		gap: 0.3rem;
		letter-spacing: 0.02em;
	}

	.drill-btn:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 255, 255, 0.1));
		box-shadow: 0 0 12px rgba(0, 255, 255, 0.4);
		transform: translateY(-1px);
		text-shadow: 0 0 6px #00ffff;
	}

	.drill-icon {
		font-size: 0.7rem;
		animation: iconSpark 2s ease-in-out infinite;
	}

	.analytics-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.chart-container, .ranking-container, .health-monitor {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 6px;
		padding: 1rem;
	}

	.chart-header, .ranking-header, .monitor-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.chart-header h4, .ranking-header h4, .monitor-header h4 {
		font-size: 0.7rem;
		font-weight: 700;
		color: #00ffff;
		margin: 0;
		text-shadow: 0 0 6px #00ffff;
	}

	.chart-controls, .ranking-filter {
		display: flex;
		gap: 0.3rem;
	}

	.chart-btn {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 3px;
		padding: 0.3rem 0.5rem;
		color: rgba(255, 255, 255, 0.7);
		font-family: inherit;
		font-size: 0.6rem;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.chart-btn.active, .chart-btn:hover {
		border-color: #00ffff;
		color: #00ffff;
		text-shadow: 0 0 6px #00ffff;
	}

	.threat-chart {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.chart-visual {
		flex: 1;
		display: flex;
		justify-content: center;
	}

	.pie-chart {
		position: relative;
		width: 80px;
		height: 80px;
		border-radius: 50%;
		background: conic-gradient(
			#ff00ff 0% 25%,
			#ff0066 25% 50%, 
			#ffaa00 50% 75%,
			#00ffff 75% 100%
		);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.pie-center {
		width: 40px;
		height: 40px;
		background: rgba(0, 0, 0, 0.8);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		color: #fff;
		font-size: 0.8rem;
	}

	.chart-legend {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.6rem;
	}

	.legend-color {
		width: 10px;
		height: 10px;
		border-radius: 2px;
	}

	.legend-color.critical {
		background: #ff00ff;
		box-shadow: 0 0 6px #ff00ff;
	}

	.legend-color.high {
		background: #ff0066;
		box-shadow: 0 0 6px #ff0066;
	}

	.legend-color.medium {
		background: #ffaa00;
		box-shadow: 0 0 6px #ffaa00;
	}

	.legend-color.low {
		background: #00ffff;
		box-shadow: 0 0 6px #00ffff;
	}

	.ranking-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		max-height: 250px;
		overflow-y: auto;
	}

	.rank-item {
		display: grid;
		grid-template-columns: auto 1fr auto auto;
		gap: 0.8rem;
		align-items: center;
		padding: 0.6rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.01));
		border-radius: 4px;
		animation: rankSlide 0.5s ease-out;
		animation-fill-mode: both;
	}

	.rank-position {
		font-size: 0.7rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 6px #00ffff;
		min-width: 25px;
	}

	.rank-info {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		min-width: 0;
	}

	.rank-name {
		font-size: 0.6rem;
		font-weight: 600;
		color: #fff;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.rank-stats {
		display: flex;
		gap: 0.5rem;
		font-size: 0.5rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.rank-bar {
		width: 60px;
		height: 4px;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 2px;
		overflow: hidden;
		position: relative;
	}

	.bar-fill {
		height: 100%;
		border-radius: 2px;
		transition: width 1s ease-out;
	}

	.rank-threat {
		min-width: 40px;
		text-align: right;
	}

	.threat-tag {
		font-size: 0.5rem;
		font-weight: 700;
		text-shadow: 0 0 4px currentColor;
	}

	.health-monitor {
		flex: 1;
	}

	.health-status {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.6rem;
		color: #00ff85;
	}

	.status-light {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: #00ff85;
		box-shadow: 0 0 8px #00ff85;
		animation: statusPulse 2s ease-in-out infinite;
	}

	.health-metrics {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.health-item {
		display: grid;
		grid-template-columns: auto 1fr auto;
		gap: 0.8rem;
		align-items: center;
	}

	.health-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.7);
		min-width: 60px;
	}

	.health-bar {
		height: 6px;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 3px;
		overflow: hidden;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.health-fill {
		height: 100%;
		background: #00ff85;
		border-radius: 3px;
		transition: width 1s ease-out;
		box-shadow: 0 0 6px rgba(0, 255, 133, 0.5);
	}

	.health-fill.critical {
		background: #ff0066;
		box-shadow: 0 0 6px rgba(255, 0, 102, 0.5);
	}

	.health-value {
		font-size: 0.6rem;
		font-weight: 700;
		color: #fff;
		min-width: 30px;
		text-align: right;
	}

	.cyber-select {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 3px;
		padding: 0.3rem 0.5rem;
		color: rgba(255, 255, 255, 0.8);
		font-family: inherit;
		font-size: 0.6rem;
		outline: none;
	}

	.cyber-select:focus {
		border-color: #00ffff;
		box-shadow: 0 0 8px rgba(0, 255, 255, 0.3);
	}

	/* Loading States */
	.loading-matrix {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.neural-core {
		position: relative;
		width: 100px;
		height: 100px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.pulse-ring {
		position: absolute;
		width: var(--size);
		height: var(--size);
		border: 2px solid #00ffff;
		border-radius: 50%;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: pulseSpin 2s ease-in-out infinite;
		animation-delay: var(--delay);
		opacity: 0.6;
	}

	.loading-text {
		color: #00ffff;
		font-size: 0.8rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-shadow: 0 0 10px #00ffff;
		animation: textGlow 2s ease-in-out infinite;
	}

	/* Drill Interface */
	.drill-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 0, 255, 0.02));
		border: 1px solid #ff00ff;
		border-radius: 8px;
		overflow: hidden;
	}

	.drill-header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(255, 0, 255, 0.05));
		border-bottom: 1px solid #ff00ff;
		padding: 1rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.drill-info {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.drill-badge {
		display: inline-block;
		padding: 0.3rem 0.8rem;
		border: 1px solid var(--threat-color);
		border-radius: 4px;
		background: rgba(0, 0, 0, 0.6);
		color: var(--threat-color);
		font-size: 0.6rem;
		font-weight: 700;
		text-shadow: 0 0 6px var(--threat-color);
		align-self: flex-start;
	}

	.drill-info h2 {
		margin: 0;
		font-size: 1rem;
		color: #fff;
		text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
	}

	.drill-stats {
		display: flex;
		gap: 1rem;
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.close-drill {
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.2), rgba(255, 0, 102, 0.1));
		border: 1px solid #ff0066;
		border-radius: 50%;
		width: 30px;
		height: 30px;
		color: #ff0066;
		font-size: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-drill:hover {
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.3), rgba(255, 0, 102, 0.2));
		box-shadow: 0 0 15px rgba(255, 0, 102, 0.5);
		transform: rotate(90deg);
	}

	.scanning-hosts {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
		color: #ff00ff;
	}

	.host-scanner {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.5rem;
		width: 80px;
		height: 80px;
	}

	.scan-node {
		background: #ff00ff;
		border-radius: 2px;
		animation: nodeFlicker 1.5s ease-in-out infinite;
		opacity: 0.3;
	}

	.host-data-table {
		flex: 1;
		padding: 1rem;
		overflow-y: auto;
	}

	.table-container {
		height: 100%;
		overflow-y: auto;
	}

	.cyber-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.65rem;
	}

	.cyber-table th {
		background: rgba(0, 0, 0, 0.4);
		color: #ff00ff;
		font-weight: 600;
		text-align: left;
		padding: 0.8rem 0.5rem;
		font-size: 0.6rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 0, 255, 0.3);
		text-shadow: 0 0 6px #ff00ff;
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.cyber-table td {
		padding: 0.6rem 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.8);
		animation: rowSlide 0.4s ease-out;
		animation-fill-mode: both;
	}

	.cyber-table tr:hover {
		background: linear-gradient(90deg, 
			rgba(255, 0, 255, 0.05), 
			transparent);
	}

	.host-cell {
		color: #fff;
		font-weight: 600;
	}

	.status-chip {
		padding: 0.2rem 0.4rem;
		border-radius: 3px;
		font-size: 0.5rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.02em;
		border: 1px solid;
		text-align: center;
		display: inline-block;
		min-width: 50px;
	}

	.status-chip.active {
		background: rgba(0, 255, 133, 0.1);
		color: #00ff85;
		border-color: #00ff85;
		text-shadow: 0 0 4px #00ff85;
	}

	.status-chip.inactive {
		background: rgba(255, 0, 102, 0.1);
		color: #ff0066;
		border-color: #ff0066;
		text-shadow: 0 0 4px #ff0066;
	}

	/* Animations */
	@keyframes scannerSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes iconSpin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes iconSpark {
		0%, 100% { text-shadow: 0 0 3px currentColor; }
		50% { text-shadow: 0 0 10px currentColor; }
	}

	@keyframes rowSlide {
		0% { 
			opacity: 0; 
			transform: translateX(-10px);
		}
		100% { 
			opacity: 1; 
			transform: translateX(0);
		}
	}

	@keyframes indicatorPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.6; transform: scale(1.2); }
	}

	@keyframes coverageSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes badgeGlow {
		0%, 100% { box-shadow: 0 0 4px currentColor; }
		50% { box-shadow: 0 0 12px currentColor; }
	}

	@keyframes rankSlide {
		0% { 
			opacity: 0; 
			transform: translateY(20px);
		}
		100% { 
			opacity: 1; 
			transform: translateY(0);
		}
	}

	@keyframes statusPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.1); }
	}

	@keyframes pulseSpin {
		0%, 100% { 
			opacity: 0.3; 
			transform: translate(-50%, -50%) scale(1);
		}
		50% { 
			opacity: 0.8; 
			transform: translate(-50%, -50%) scale(1.1);
		}
	}

	@keyframes textGlow {
		0%, 100% { text-shadow: 0 0 10px #00ffff; }
		50% { text-shadow: 0 0 20px #00ffff; }
	}

	@keyframes nodeFlicker {
		0%, 100% { opacity: 0.3; background: #ff00ff; }
		50% { opacity: 1; background: #fff; }
	}

	/* Responsive Design */
	@media (max-width: 1200px) {
		.main-dashboard {
			grid-template-columns: 1fr;
			grid-template-rows: 2fr 1fr;
		}
		
		.analytics-panel {
			flex-direction: row;
			overflow-x: auto;
		}
		
		.chart-container, .ranking-container, .health-monitor {
			min-width: 250px;
		}
	}

	@media (max-width: 768px) {
		.header-grid {
			grid-template-columns: repeat(2, 1fr);
		}
		
		.search-matrix {
			flex-direction: column;
			gap: 1rem;
		}
		
		.analytics-panel {
			flex-direction: column;
		}
		
		.chart-container, .ranking-container, .health-monitor {
			min-width: unset;
		}
		
		.source-table th,
		.source-table td {
			padding: 0.5rem 0.3rem;
		}
		
		.cyber-table th,
		.cyber-table td {
			padding: 0.5rem 0.3rem;
		}
	}

	@media (max-width: 480px) {
		.metric-card {
			padding: 0.8rem;
		}
		
		.metric-value {
			font-size: 1.1rem;
		}
		
		.dashboard-header {
			padding: 0.8rem;
		}
		
		.source-intelligence-dashboard {
			font-size: 0.65rem;
		}
	}
</style>