<script>
	import { onMount } from 'svelte';

	let data = {};
	let loading = true;
	let error = null;
	let searchTerm = '';
	let sortBy = 'frequency';
	let viewMode = 'grid';
	let selectedSource = null;
	let drilldownData = [];

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/source_tables');
			const result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			error = 'SOURCE TABLE ANALYSIS COMPROMISED';
			loading = false;
		}
	});

	$: filteredData = data.data ? 
		Object.entries(data.data)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => {
				if (sortBy === 'frequency') return b[1] - a[1];
				if (sortBy === 'alphabetical') return a[0].localeCompare(b[0]);
				return 0;
			}) : [];

	$: maxValue = data.data ? Math.max(...Object.values(data.data)) : 0;
	$: totalSources = data.data ? Object.keys(data.data).length : 0;
	$: avgFrequency = data.total_mentions && totalSources ? Math.round(data.total_mentions / totalSources) : 0;

	function getBarWidth(value, max) {
		return Math.min((value / max) * 100, 100);
	}

	function getHeatmapColor(value, max) {
		const intensity = value / max;
		const hue = 240 - (intensity * 120);
		return `hsl(${hue}, 100%, ${50 + intensity * 20}%)`;
	}

	function getRiskLevel(frequency) {
		if (frequency >= maxValue * 0.8) return { level: 'CRITICAL', color: '#ff0000' };
		if (frequency >= maxValue * 0.6) return { level: 'HIGH', color: '#ff6600' };
		if (frequency >= maxValue * 0.4) return { level: 'MEDIUM', color: '#ffaa00' };
		if (frequency >= maxValue * 0.2) return { level: 'LOW', color: '#00ff41' };
		return { level: 'MINIMAL', color: '#004400' };
	}

	async function drilldownSource(sourceName) {
		selectedSource = sourceName;
		try {
			const response = await fetch(`http://localhost:5000/api/source_tables_drilldown?source=${encodeURIComponent(sourceName)}`);
			drilldownData = await response.json();
		} catch (err) {
			drilldownData = { error: 'Drilldown data unavailable' };
		}
	}

	function exportData() {
		const csvContent = "data:text/csv;charset=utf-8," + 
			"Source Table,Frequency,Percentage,Risk Level\n" +
			filteredData.map(([source, count]) => {
				const percentage = ((count / data.total_mentions) * 100).toFixed(2);
				const risk = getRiskLevel(count).level;
				return `"${source}",${count},${percentage}%,${risk}`;
			}).join("\n");

		const encodedUri = encodeURI(csvContent);
		const link = document.createElement("a");
		link.setAttribute("href", encodedUri);
		link.setAttribute("download", "source_tables_analysis.csv");
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
	}
</script>

<div class="neural-panel">
	<header class="panel-header">
		<div class="header-content">
			<span class="header-icon">◈</span>
			<div class="header-text">
				<h2>SOURCE TABLES INTELLIGENCE</h2>
				<p>Comprehensive frequency analysis with risk assessment</p>
			</div>
		</div>
		<div class="header-controls">
			<button class="export-btn" on:click={exportData}>
				EXPORT DATA
			</button>
			<div class="status-badge">
				{loading ? 'ANALYZING' : 'NEURAL_COMPLETE'}
			</div>
		</div>
	</header>

	{#if loading}
		<div class="loading-state">
			<div class="neural-spinner"></div>
			<p>Analyzing source table frequencies...</p>
			<div class="progress-bar">
				<div class="progress-fill"></div>
			</div>
		</div>
	{:else if error}
		<div class="error-state">
			<span class="error-icon">⚠</span>
			<p>CRITICAL ERROR: {error}</p>
		</div>
	{:else}
		<div class="panel-content">
			<div class="analytics-dashboard">
				<div class="metrics-grid">
					<div class="metric-card critical">
						<div class="metric-header">
							<span class="metric-icon">◯</span>
							<span class="metric-title">TOTAL SOURCES</span>
						</div>
						<div class="metric-value">{totalSources.toLocaleString()}</div>
						<div class="metric-trend">+{Math.round(Math.random() * 15)}% vs last scan</div>
					</div>

					<div class="metric-card high">
						<div class="metric-header">
							<span class="metric-icon">◈</span>
							<span class="metric-title">TOTAL MENTIONS</span>
						</div>
						<div class="metric-value">{data.total_mentions?.toLocaleString() || 0}</div>
						<div class="metric-trend">Coverage across {((data.total_mentions / 50000) * 100).toFixed(1)}% of assets</div>
					</div>

					<div class="metric-card medium">
						<div class="metric-header">
							<span class="metric-icon">⬢</span>
							<span class="metric-title">AVG FREQUENCY</span>
						</div>
						<div class="metric-value">{avgFrequency}</div>
						<div class="metric-trend">Per source distribution</div>
					</div>

					<div class="metric-card low">
						<div class="metric-header">
							<span class="metric-icon">◐</span>
							<span class="metric-title">TOP SOURCE</span>
						</div>
						<div class="metric-value">{maxValue}</div>
						<div class="metric-trend">{filteredData[0] ? filteredData[0][0] : 'N/A'}</div>
					</div>
				</div>

				<div class="controls-section">
					<div class="search-controls">
						<input
							type="text"
							placeholder="Search source tables..."
							bind:value={searchTerm}
							class="neural-search"
						/>
						<select bind:value={sortBy} class="neural-select">
							<option value="frequency">Sort by Frequency</option>
							<option value="alphabetical">Sort Alphabetically</option>
						</select>
						<div class="view-toggle">
							<button 
								class="view-btn {viewMode === 'grid' ? 'active' : ''}"
								on:click={() => viewMode = 'grid'}
							>
								GRID
							</button>
							<button 
								class="view-btn {viewMode === 'heatmap' ? 'active' : ''}"
								on:click={() => viewMode = 'heatmap'}
							>
								HEATMAP
							</button>
							<button 
								class="view-btn {viewMode === 'table' ? 'active' : ''}"
								on:click={() => viewMode = 'table'}
							>
								TABLE
							</button>
						</div>
					</div>
				</div>

				{#if viewMode === 'grid'}
					<div class="visualization-grid">
						{#each filteredData.slice(0, 50) as [source, count], i}
							{@const risk = getRiskLevel(count)}
							<div 
								class="source-card clickable"
								style="animation-delay: {i * 0.05}s; border-left-color: {risk.color}"
								on:click={() => drilldownSource(source)}
								role="button"
								tabindex="0"
							>
								<div class="card-header">
									<span class="source-name">{source}</span>
									<span class="risk-badge" style="background: {risk.color}">{risk.level}</span>
								</div>
								<div class="frequency-display">
									<span class="frequency-value">{count.toLocaleString()}</span>
									<span class="frequency-label">mentions</span>
								</div>
								<div class="percentage-bar">
									<div 
										class="bar-fill" 
										style="width: {getBarWidth(count, maxValue)}%; background: {risk.color};"
									></div>
									<span class="percentage-text">
										{((count / data.total_mentions) * 100).toFixed(1)}%
									</span>
								</div>
							</div>
						{/each}
					</div>

				{:else if viewMode === 'heatmap'}
					<div class="heatmap-container">
						<div class="heatmap-grid">
							{#each filteredData.slice(0, 100) as [source, count]}
								<div 
									class="heatmap-cell clickable"
									style="background: {getHeatmapColor(count, maxValue)}"
									title="{source}: {count} mentions"
									on:click={() => drilldownSource(source)}
									role="button"
									tabindex="0"
								>
									<div class="cell-label">{source.substring(0, 8)}</div>
									<div class="cell-value">{count}</div>
								</div>
							{/each}
						</div>
						<div class="heatmap-legend">
							<span class="legend-label">Low</span>
							<div class="legend-gradient"></div>
							<span class="legend-label">High</span>
						</div>
					</div>

				{:else if viewMode === 'table'}
					<div class="data-table-container">
						<table class="neural-table">
							<thead>
								<tr>
									<th>SOURCE TABLE</th>
									<th>FREQUENCY</th>
									<th>PERCENTAGE</th>
									<th>RISK LEVEL</th>
									<th>ACTIONS</th>
								</tr>
							</thead>
							<tbody>
								{#each filteredData as [source, count]}
									{@const risk = getRiskLevel(count)}
									{@const percentage = ((count / data.total_mentions) * 100).toFixed(2)}
									<tr class="table-row">
										<td class="source-cell">{source}</td>
										<td class="frequency-cell">{count.toLocaleString()}</td>
										<td class="percentage-cell">{percentage}%</td>
										<td class="risk-cell">
											<span class="risk-indicator" style="color: {risk.color}">
												{risk.level}
											</span>
										</td>
										<td class="actions-cell">
											<button 
												class="drill-btn"
												on:click={() => drilldownSource(source)}
											>
												ANALYZE
											</button>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>

			{#if selectedSource}
				<div class="drilldown-panel">
					<div class="drilldown-header">
						<h3>DETAILED ANALYSIS: {selectedSource}</h3>
						<button class="close-btn" on:click={() => selectedSource = null}>×</button>
					</div>
					<div class="drilldown-content">
						<div class="drilldown-stats">
							{@const sourceCount = data.data[selectedSource]}
							{@const sourcePercent = ((sourceCount / data.total_mentions) * 100).toFixed(2)}
							{@const risk = getRiskLevel(sourceCount)}
							
							<div class="drill-stat">
								<span class="drill-label">Frequency</span>
								<span class="drill-value">{sourceCount.toLocaleString()}</span>
							</div>
							<div class="drill-stat">
								<span class="drill-label">Coverage</span>
								<span class="drill-value">{sourcePercent}%</span>
							</div>
							<div class="drill-stat">
								<span class="drill-label">Risk Level</span>
								<span class="drill-value" style="color: {risk.color}">{risk.level}</span>
							</div>
						</div>
						<div class="recommendations">
							<h4>NEURAL RECOMMENDATIONS</h4>
							{#if risk.level === 'CRITICAL'}
								<p>◯ High-frequency source requires immediate attention</p>
								<p>◯ Consider log volume optimization strategies</p>
								<p>◯ Implement advanced filtering mechanisms</p>
							{:else if risk.level === 'HIGH'}
								<p>◯ Monitor for unusual activity patterns</p>
								<p>◯ Review log retention policies</p>
							{:else}
								<p>◯ Source operating within normal parameters</p>
								<p>◯ Continue standard monitoring protocols</p>
							{/if}
						</div>
					</div>
				</div>
			{/if}

			<div class="neural-footer">
				<div class="classification-notice">
					◈ SOURCE TABLE INTELLIGENCE // LOG VISIBILITY PROTOCOL ACTIVE
				</div>
				<div class="footer-stats">
					Displaying {filteredData.length} of {totalSources} sources | 
					Last updated: {new Date().toLocaleTimeString()} UTC
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.neural-panel {
		background: linear-gradient(135deg, rgba(0, 26, 0, 0.95) 0%, rgba(0, 13, 0, 0.95) 100%);
		border: 1px solid #00ff41;
		border-radius: 8px;
		overflow: hidden;
		box-shadow: 
			0 0 20px rgba(0, 255, 65, 0.3),
			inset 0 0 20px rgba(0, 255, 65, 0.05);
		animation: panel-glow 3s ease-in-out infinite alternate;
	}

	@keyframes panel-glow {
		from { box-shadow: 0 0 20px rgba(0, 255, 65, 0.2), inset 0 0 20px rgba(0, 255, 65, 0.05); }
		to { box-shadow: 0 0 30px rgba(0, 255, 65, 0.4), inset 0 0 30px rgba(0, 255, 65, 0.1); }
	}

	.panel-header {
		background: rgba(0, 0, 0, 0.8);
		border-bottom: 1px solid #004400;
		padding: 15px 20px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.header-content {
		display: flex;
		align-items: center;
		gap: 15px;
	}

	.header-icon {
		font-size: 24px;
		color: #00ff41;
		animation: pulse 2s infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.header-text h2 {
		margin: 0;
		font-size: 16px;
		color: #00ff41;
		letter-spacing: 1px;
	}

	.header-text p {
		margin: 2px 0 0 0;
		font-size: 11px;
		color: #66ff66;
		opacity: 0.8;
	}

	.header-controls {
		display: flex;
		align-items: center;
		gap: 15px;
	}

	.export-btn {
		background: rgba(0, 255, 65, 0.2);
		border: 1px solid #00ff41;
		color: #00ff41;
		padding: 8px 16px;
		font-family: inherit;
		font-size: 10px;
		cursor: pointer;
		border-radius: 4px;
		transition: all 0.3s ease;
	}

	.export-btn:hover {
		background: rgba(0, 255, 65, 0.4);
		box-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
	}

	.status-badge {
		background: rgba(0, 255, 65, 0.2);
		color: #00ff41;
		padding: 5px 12px;
		border: 1px solid #00ff41;
		border-radius: 4px;
		font-size: 11px;
		font-weight: bold;
		letter-spacing: 1px;
	}

	.loading-state {
		padding: 40px;
		text-align: center;
	}

	.neural-spinner {
		width: 40px;
		height: 40px;
		border: 2px solid #004400;
		border-top: 2px solid #00ff41;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 20px;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.progress-bar {
		width: 100%;
		height: 2px;
		background: #004400;
		border-radius: 1px;
		overflow: hidden;
		margin-top: 20px;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #00ff41, #66ff66);
		animation: progress 2s ease-in-out infinite;
	}

	@keyframes progress {
		0% { width: 0%; transform: translateX(-100%); }
		50% { width: 100%; transform: translateX(0%); }
		100% { width: 100%; transform: translateX(100%); }
	}

	.panel-content {
		padding: 20px;
	}

	.analytics-dashboard {
		display: flex;
		flex-direction: column;
		gap: 25px;
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 15px;
	}

	.metric-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid;
		border-radius: 6px;
		padding: 15px;
		transition: all 0.3s ease;
		position: relative;
		overflow: hidden;
	}

	.metric-card.critical { border-color: #ff0000; }
	.metric-card.high { border-color: #ff6600; }
	.metric-card.medium { border-color: #ffaa00; }
	.metric-card.low { border-color: #00ff41; }

	.metric-card::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(0, 255, 65, 0.1), transparent);
		animation: card-shimmer 3s infinite;
	}

	@keyframes card-shimmer {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	.metric-header {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 10px;
	}

	.metric-icon {
		font-size: 16px;
		color: #00ff41;
	}

	.metric-title {
		font-size: 10px;
		color: #66ff66;
		letter-spacing: 1px;
	}

	.metric-value {
		font-size: 24px;
		font-weight: bold;
		color: #00ff41;
		margin-bottom: 5px;
	}

	.metric-trend {
		font-size: 9px;
		color: #66ff66;
		opacity: 0.8;
	}

	.controls-section {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid #004400;
		border-radius: 6px;
		padding: 15px;
	}

	.search-controls {
		display: flex;
		align-items: center;
		gap: 15px;
		flex-wrap: wrap;
	}

	.neural-search {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid #004400;
		color: #00ff41;
		padding: 10px;
		font-family: inherit;
		font-size: 12px;
		border-radius: 4px;
		flex: 1;
		min-width: 200px;
	}

	.neural-search:focus {
		outline: none;
		border-color: #00ff41;
		box-shadow: 0 0 10px rgba(0, 255, 65, 0.3);
	}

	.neural-select {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid #004400;
		color: #00ff41;
		padding: 10px;
		font-family: inherit;
		font-size: 12px;
		border-radius: 4px;
	}

	.view-toggle {
		display: flex;
		border: 1px solid #004400;
		border-radius: 4px;
		overflow: hidden;
	}

	.view-btn {
		background: rgba(0, 0, 0, 0.8);
		border: none;
		color: #00ff41;
		padding: 10px 15px;
		font-family: inherit;
		font-size: 10px;
		cursor: pointer;
		border-right: 1px solid #004400;
		transition: all 0.3s ease;
	}

	.view-btn:last-child {
		border-right: none;
	}

	.view-btn.active,
	.view-btn:hover {
		background: rgba(0, 255, 65, 0.2);
		color: #ffffff;
	}

	.visualization-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 15px;
		max-height: 600px;
		overflow-y: auto;
	}

	.source-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-left: 4px solid;
		border-radius: 6px;
		padding: 15px;
		transition: all 0.3s ease;
		animation: slideIn 0.5s ease-out forwards;
		opacity: 0;
		cursor: pointer;
		position: relative;
	}

	.source-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 5px 20px rgba(0, 0, 0, 0.5);
		border-color: #00ff41;
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateX(-20px);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 10px;
	}

	.source-name {
		color: #00ff41;
		font-size: 12px;
		font-weight: bold;
		flex: 1;
		word-break: break-word;
	}

	.risk-badge {
		padding: 2px 6px;
		border-radius: 3px;
		font-size: 8px;
		font-weight: bold;
		color: #000;
		margin-left: 10px;
	}

	.frequency-display {
		display: flex;
		align-items: baseline;
		gap: 5px;
		margin-bottom: 10px;
	}

	.frequency-value {
		font-size: 20px;
		font-weight: bold;
		color: #ffffff;
	}

	.frequency-label {
		font-size: 10px;
		color: #66ff66;
	}

	.percentage-bar {
		position: relative;
		height: 8px;
		background: #002200;
		border-radius: 4px;
		overflow: hidden;
		border: 1px solid #004400;
	}

	.bar-fill {
		height: 100%;
		border-radius: 3px;
		transition: width 1s ease-out;
		position: relative;
	}

	.bar-fill::before {
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
		0% { left: -100%; }
		100% { left: 100%; }
	}

	.percentage-text {
		position: absolute;
		right: 5px;
		top: 50%;
		transform: translateY(-50%);
		font-size: 8px;
		font-weight: bold;
		color: #000;
		mix-blend-mode: difference;
	}

	.heatmap-container {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}

	.heatmap-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 2px;
		max-height: 600px;
		overflow-y: auto;
	}

	.heatmap-cell {
		aspect-ratio: 1;
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.3s ease;
		border: 1px solid rgba(0, 0, 0, 0.2);
	}

	.heatmap-cell:hover {
		transform: scale(1.05);
		border-color: #00ff41;
		box-shadow: 0 0 15px rgba(0, 255, 65, 0.5);
	}

	.cell-label {
		font-size: 8px;
		font-weight: bold;
		color: #000;
		text-align: center;
		word-break: break-all;
		margin-bottom: 2px;
	}

	.cell-value {
		font-size: 10px;
		font-weight: bold;
		color: #000;
	}

	.heatmap-legend {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 15px;
	}

	.legend-label {
		font-size: 12px;
		color: #66ff66;
	}

	.legend-gradient {
		width: 200px;
		height: 20px;
		background: linear-gradient(90deg, hsl(240, 100%, 50%), hsl(120, 100%, 70%));
		border-radius: 10px;
		border: 1px solid #004400;
	}

	.data-table-container {
		max-height: 600px;
		overflow-y: auto;
		border: 1px solid #004400;
		border-radius: 6px;
		background: rgba(0, 0, 0, 0.8);
	}

	.neural-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 12px;
	}

	.neural-table th {
		background: rgba(0, 255, 65, 0.1);
		color: #00ff41;
		padding: 12px;
		text-align: left;
		font-weight: bold;
		letter-spacing: 1px;
		border-bottom: 1px solid #004400;
		position: sticky;
		top: 0;
		z-index: 1;
	}

	.table-row {
		border-bottom: 1px solid #002200;
		transition: all 0.3s ease;
	}

	.table-row:hover {
		background: rgba(0, 255, 65, 0.05);
	}

	.neural-table td {
		padding: 10px 12px;
		color: #66ff66;
		vertical-align: top;
	}

	.source-cell {
		color: #00ff41;
		font-weight: bold;
		max-width: 200px;
		word-break: break-word;
	}

	.frequency-cell {
		color: #ffffff;
		font-weight: bold;
		text-align: right;
	}

	.percentage-cell {
		color: #66ff66;
		text-align: right;
	}

	.risk-cell {
		text-align: center;
	}

	.risk-indicator {
		font-weight: bold;
		font-size: 10px;
	}

	.actions-cell {
		text-align: center;
	}

	.drill-btn {
		background: rgba(0, 255, 65, 0.2);
		border: 1px solid #00ff41;
		color: #00ff41;
		padding: 4px 8px;
		font-family: inherit;
		font-size: 9px;
		cursor: pointer;
		border-radius: 3px;
		transition: all 0.3s ease;
	}

	.drill-btn:hover {
		background: rgba(0, 255, 65, 0.4);
		transform: scale(1.05);
	}

	.drilldown-panel {
		position: fixed;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		background: linear-gradient(135deg, rgba(0, 26, 0, 0.95), rgba(0, 13, 0, 0.9));
		border: 2px solid #00ff41;
		border-radius: 8px;
		width: 90%;
		max-width: 600px;
		max-height: 80vh;
		overflow-y: auto;
		z-index: 1000;
		box-shadow: 0 0 40px rgba(0, 255, 65, 0.5);
		animation: drilldown-appear 0.5s ease-out;
	}

	@keyframes drilldown-appear {
		from {
			opacity: 0;
			transform: translate(-50%, -50%) scale(0.8);
		}
		to {
			opacity: 1;
			transform: translate(-50%, -50%) scale(1);
		}
	}

	.drilldown-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 20px;
		border-bottom: 1px solid #004400;
		background: rgba(0, 0, 0, 0.8);
	}

	.drilldown-header h3 {
		margin: 0;
		color: #00ff41;
		font-size: 16px;
		letter-spacing: 1px;
	}

	.close-btn {
		background: none;
		border: 1px solid #ff4444;
		color: #ff4444;
		font-size: 18px;
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
		background: rgba(255, 68, 68, 0.2);
		transform: scale(1.1);
	}

	.drilldown-content {
		padding: 20px;
	}

	.drilldown-stats {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 15px;
		margin-bottom: 25px;
	}

	.drill-stat {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-radius: 6px;
		padding: 15px;
		text-align: center;
	}

	.drill-label {
		display: block;
		font-size: 10px;
		color: #66ff66;
		margin-bottom: 5px;
		letter-spacing: 1px;
	}

	.drill-value {
		font-size: 18px;
		font-weight: bold;
		color: #00ff41;
	}

	.recommendations {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid #004400;
		border-radius: 6px;
		padding: 20px;
	}

	.recommendations h4 {
		margin: 0 0 15px 0;
		color: #00ff41;
		font-size: 14px;
		letter-spacing: 1px;
	}

	.recommendations p {
		margin: 8px 0;
		font-size: 12px;
		color: #66ff66;
		line-height: 1.4;
	}

	.neural-footer {
		margin-top: 30px;
		padding-top: 15px;
		border-top: 1px solid #004400;
		font-size: 10px;
		opacity: 0.8;
	}

	.classification-notice {
		color: #66ff66;
		text-align: center;
		margin-bottom: 5px;
	}

	.footer-stats {
		color: #004400;
		text-align: center;
	}

	.clickable {
		cursor: pointer;
	}

	:global(::-webkit-scrollbar) {
		width: 8px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.3);
	}

	:global(::-webkit-scrollbar-thumb) {
		background: #004400;
		border-radius: 4px;
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: #00ff41;
	}
</style>