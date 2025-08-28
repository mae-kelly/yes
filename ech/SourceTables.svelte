<!-- SourceTables.svelte - Tactical Frequency Analysis -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let pulseArray = [];

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			let result = await response.json();
			data = result;
			loading = false;
			
			// Initialize pulse array for visualization
			if (data.source_intelligence) {
				pulseArray = Object.entries(data.source_intelligence)
					.sort((a, b) => b[1] - a[1])
					.slice(0, 10)
					.map(() => Math.random());
			}
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
		if (percentage >= 75) return { level: 'CRITICAL', color: '#ff0066' };
		if (percentage >= 50) return { level: 'HIGH', color: '#ff9900' };
		if (percentage >= 25) return { level: 'MEDIUM', color: '#ffcc00' };
		return { level: 'LOW', color: '#0a4f3c' };
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
	<div class="main-content">
		<!-- Left Panel: Frequency Matrix -->
		<div class="table-panel">
			<div class="panel-header">
				<div class="header-top">
					<h3 class="panel-title">SOURCE TABLES</h3>
					<div class="header-indicator"></div>
				</div>
				<div class="subtitle">FREQUENCY ANALYSIS MATRIX</div>
				<div class="controls">
					<div class="search-container">
						<input 
							type="text" 
							bind:value={searchTerm}
							placeholder="SEARCH SOURCES..."
							class="search-input"
						/>
						<div class="search-indicator"></div>
					</div>
				</div>
			</div>
			
			{#if loading && !selectedSource}
				<div class="loading-state">
					<div class="loader-container">
						<div class="tactical-loader">
							<div class="loader-ring"></div>
							<div class="loader-ring"></div>
							<div class="loader-ring"></div>
						</div>
					</div>
					<p class="loading-text">ANALYZING SOURCE MATRICES...</p>
				</div>
			{:else if selectedSource}
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedSource.source.toUpperCase()}</h4>
						<button class="close-btn" on:click={closeDetails}>
							<svg width="20" height="20" viewBox="0 0 20 20">
								<path d="M2 2L18 18M18 2L2 18" stroke="#ff0066" stroke-width="2"/>
							</svg>
						</button>
					</div>
					<div class="drill-table-container">
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
										<td>{host.region || 'UNKNOWN'}</td>
										<td>{host.country || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>
											<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'ACTIVE' : 'INACTIVE'}
											</span>
										</td>
										<td>
											<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? 'DEPLOYED' : 'MISSING'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="table-scroll-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>SOURCE TABLE</th>
								<th>FREQUENCY</th>
								<th>COVERAGE</th>
								<th>THREAT LEVEL</th>
								<th>VISIBILITY MATRIX</th>
							</tr>
						</thead>
						<tbody>
							{#each filteredSources as [source, frequency]}
								{@const threat = getThreatLevel(frequency)}
								<tr on:click={() => drillDownSource(source, frequency)}>
									<td class="source-cell">
										<div class="source-indicator" style="background: {threat.color}"></div>
										<span class="source-name">{source.toUpperCase()}</span>
									</td>
									<td class="center frequency-cell">
										<span class="frequency-value">{frequency.toLocaleString()}</span>
										<div class="frequency-bar" style="width: {(frequency/maxFreq)*100}%; background: {threat.color}"></div>
									</td>
									<td class="center">{getPercentage(frequency)}%</td>
									<td class="center">
										<span class="threat-badge" style="color: {threat.color}; border-color: {threat.color}">
											{threat.level}
										</span>
									</td>
									<td>
										<div class="matrix-visualization">
											{#each Array(10) as _, i}
												<div class="matrix-bar" 
													style="height: {(frequency/maxFreq) * (i + 1) * 10}%; 
														  background: {threat.color};
														  opacity: {1 - (i * 0.08)}">
												</div>
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

		<!-- Right Panel: Tactical Visualizations -->
		<div class="viz-panel">
			<!-- Metrics Command -->
			<div class="metrics-command">
				<div class="metric-card primary">
					<div class="metric-inner">
						<div class="metric-value">{filteredSources.length}</div>
						<div class="metric-label">UNIQUE SOURCES</div>
						<div class="metric-graph">
							<svg viewBox="0 0 100 30">
								{#each Array(20) as _, i}
									<rect x="{i * 5}" y="{30 - Math.random() * 30}" 
										  width="3" height="{Math.random() * 30}"
										  fill="#0a4f3c" opacity="{Math.random()}"/>
								{/each}
							</svg>
						</div>
					</div>
				</div>
				<div class="metric-card secondary">
					<div class="metric-inner">
						<div class="metric-value">{(data.total_mentions || 0).toLocaleString()}</div>
						<div class="metric-label">TOTAL MENTIONS</div>
						<div class="metric-graph">
							<svg viewBox="0 0 100 30">
								<polyline points="0,25 10,20 20,22 30,15 40,18 50,10 60,15 70,12 80,20 90,18 100,25" 
										  fill="none" stroke="#0a4f3c" stroke-width="1"/>
							</svg>
						</div>
					</div>
				</div>
			</div>

			<!-- Frequency Spectrum -->
			<div class="viz-card">
				<div class="card-header">
					<h4>FREQUENCY SPECTRUM</h4>
					<div class="card-status"></div>
				</div>
				<div class="spectrum-chart">
					{#each filteredSources.slice(0, 12) as [source, frequency]}
						{@const threat = getThreatLevel(frequency)}
						<div class="spectrum-item">
							<div class="spectrum-label">{source.substring(0, 10).toUpperCase()}</div>
							<div class="spectrum-visual">
								<div class="spectrum-base"></div>
								<div class="spectrum-fill" 
									 style="width: {(frequency/maxFreq)*100}%; 
											background: linear-gradient(90deg, #0a4f3c, {threat.color})">
									<div class="spectrum-pulse"></div>
								</div>
								<span class="spectrum-value">{frequency}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Threat Matrix Grid -->
			<div class="viz-card">
				<div class="card-header">
					<h4>THREAT MATRIX</h4>
					<div class="card-status active"></div>
				</div>
				<div class="threat-matrix">
					<svg viewBox="0 0 200 150" class="matrix-svg">
						<defs>
							<linearGradient id="threatGrad" x1="0%" y1="0%" x2="100%" y2="100%">
								<stop offset="0%" style="stop-color:#0a4f3c;stop-opacity:0.2" />
								<stop offset="100%" style="stop-color:#ff0066;stop-opacity:0.8" />
							</linearGradient>
						</defs>
						
						<!-- Grid lines -->
						{#each Array(5) as _, i}
							<line x1="0" y1="{i * 30}" x2="200" y2="{i * 30}" 
								  stroke="#111" stroke-width="0.5"/>
							<line x1="{i * 40}" y1="0" x2="{i * 40}" y2="150" 
								  stroke="#111" stroke-width="0.5"/>
						{/each}
						
						<!-- Data points -->
						{#each filteredSources.slice(0, 8) as [source, frequency], i}
							{@const x = (i % 4) * 50 + 25}
							{@const y = Math.floor(i / 4) * 50 + 25}
							{@const size = (frequency / maxFreq) * 30}
							<circle cx="{x}" cy="{y}" r="{size}" 
									fill="url(#threatGrad)" opacity="0.6"
									class="matrix-point"/>
							<circle cx="{x}" cy="{y}" r="2" 
									fill="#0a4f3c"/>
						{/each}
						
						<!-- Connection lines -->
						{#each filteredSources.slice(0, 7) as [source, frequency], i}
							{#if i < filteredSources.length - 1}
								{@const x1 = (i % 4) * 50 + 25}
								{@const y1 = Math.floor(i / 4) * 50 + 25}
								{@const x2 = ((i + 1) % 4) * 50 + 25}
								{@const y2 = Math.floor((i + 1) / 4) * 50 + 25}
								<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
									  stroke="#0a4f3c" stroke-width="0.5" opacity="0.3"/>
							{/if}
						{/each}
					</svg>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.dashboard-container {
		height: calc(100vh - 180px);
		display: flex;
		background: #000000;
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
		background: linear-gradient(135deg, #0a0a0a 0%, #050505 100%);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		position: relative;
	}

	.table-panel::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 1px;
		background: linear-gradient(90deg, transparent, #0a4f3c, transparent);
		animation: scan 3s linear infinite;
	}

	@keyframes scan {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100%); }
	}

	.panel-header {
		padding: 1.5rem;
		border-bottom: 1px solid #0a4f3c;
		background: rgba(10, 79, 60, 0.02);
		flex-shrink: 0;
	}

	.header-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.panel-title {
		margin: 0;
		color: #0a4f3c;
		font-size: 1.2rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-shadow: 0 0 20px rgba(10, 79, 60, 0.5);
	}

	.header-indicator {
		width: 10px;
		height: 10px;
		background: #0a4f3c;
		border-radius: 50%;
		animation: pulse 2s ease-in-out infinite;
		box-shadow: 0 0 20px rgba(10, 79, 60, 0.8);
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.5; transform: scale(1.2); }
	}

	.subtitle {
		font-size: 0.7rem;
		color: #666;
		letter-spacing: 0.2em;
		margin-bottom: 1rem;
	}

	.controls {
		display: flex;
		gap: 0.5rem;
	}

	.search-container {
		flex: 1;
		position: relative;
	}

	.search-input {
		width: 100%;
		background: #000;
		border: 1px solid #0a4f3c;
		border-radius: 2px;
		padding: 0.6rem 1rem;
		color: #e0e0e0;
		font-size: 0.8rem;
		font-family: inherit;
		letter-spacing: 0.05em;
		transition: all 0.3s ease;
	}

	.search-input:focus {
		outline: none;
		border-color: #0a4f3c;
		box-shadow: 0 0 20px rgba(10, 79, 60, 0.3);
		background: rgba(10, 79, 60, 0.02);
	}

	.search-indicator {
		position: absolute;
		right: 10px;
		top: 50%;
		transform: translateY(-50%);
		width: 4px;
		height: 4px;
		background: #0a4f3c;
		border-radius: 50%;
		animation: blink 1s ease-in-out infinite;
	}

	@keyframes blink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.2; }
	}

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.loader-container {
		position: relative;
		width: 100px;
		height: 100px;
	}

	.tactical-loader {
		width: 100%;
		height: 100%;
		position: relative;
	}

	.loader-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid transparent;
		border-top-color: #0a4f3c;
		border-radius: 50%;
		animation: loaderSpin 1.5s linear infinite;
	}

	.loader-ring:nth-child(2) {
		width: 80%;
		height: 80%;
		top: 10%;
		left: 10%;
		animation-delay: 0.2s;
		border-top-color: #0d6b4f;
	}

	.loader-ring:nth-child(3) {
		width: 60%;
		height: 60%;
		top: 20%;
		left: 20%;
		animation-delay: 0.4s;
		border-top-color: #0a4f3c;
	}

	@keyframes loaderSpin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.loading-text {
		color: #0a4f3c;
		font-size: 0.8rem;
		letter-spacing: 0.2em;
		animation: textPulse 1.5s ease-in-out infinite;
	}

	@keyframes textPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.table-scroll-container {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.8rem;
	}

	.data-table th {
		background: rgba(10, 79, 60, 0.05);
		color: #0a4f3c;
		padding: 1rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 2px solid #0a4f3c;
	}

	.data-table td {
		padding: 0.8rem 1rem;
		border-bottom: 1px solid rgba(10, 79, 60, 0.1);
		color: #b8a678;
		transition: all 0.2s ease;
	}

	.data-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		position: relative;
	}

	.data-table tbody tr::before {
		content: '';
		position: absolute;
		left: 0;
		top: 0;
		bottom: 0;
		width: 2px;
		background: #0a4f3c;
		transform: scaleY(0);
		transition: transform 0.2s ease;
	}

	.data-table tbody tr:hover::before {
		transform: scaleY(1);
	}

	.data-table tbody tr:hover {
		background: rgba(10, 79, 60, 0.05);
	}

	.data-table tbody tr:hover td {
		color: #e0e0e0;
	}

	.source-cell {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.source-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: indicatorPulse 2s ease-in-out infinite;
	}

	@keyframes indicatorPulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.2); opacity: 0.6; }
	}

	.source-name {
		font-weight: 500;
		color: #e0e0e0;
	}

	.center {
		text-align: center;
	}

	.frequency-cell {
		position: relative;
	}

	.frequency-value {
		position: relative;
		z-index: 2;
		font-weight: 600;
	}

	.frequency-bar {
		position: absolute;
		bottom: 0;
		left: 0;
		height: 2px;
		transition: width 0.3s ease;
		opacity: 0.6;
	}

	.threat-badge {
		padding: 0.3rem 0.6rem;
		border: 1px solid;
		border-radius: 2px;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		display: inline-block;
	}

	.matrix-visualization {
		display: flex;
		align-items: flex-end;
		gap: 2px;
		height: 30px;
	}

	.matrix-bar {
		width: 3px;
		transition: all 0.3s ease;
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.metrics-command {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.metric-card {
		background: linear-gradient(135deg, #0a0a0a 0%, #050505 100%);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		padding: 1.5rem;
		position: relative;
		overflow: hidden;
	}

	.metric-card::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 1px;
		background: linear-gradient(90deg, transparent, #0a4f3c, transparent);
		animation: metricScan 3s linear infinite;
	}

	@keyframes metricScan {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	.metric-inner {
		position: relative;
		z-index: 1;
	}

	.metric-value {
		font-size: 2.5rem;
		font-weight: 700;
		color: #0a4f3c;
		margin-bottom: 0.5rem;
		text-shadow: 0 0 20px rgba(10, 79, 60, 0.5);
	}

	.metric-label {
		font-size: 0.7rem;
		color: #b8a678;
		letter-spacing: 0.2em;
		font-weight: 500;
		margin-bottom: 0.5rem;
	}

	.metric-graph {
		height: 30px;
		opacity: 0.6;
	}

	.metric-graph svg {
		width: 100%;
		height: 100%;
	}

	.viz-card {
		background: linear-gradient(135deg, #0a0a0a 0%, #050505 100%);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		padding: 1.5rem;
		position: relative;
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.viz-card h4 {
		margin: 0;
		font-size: 0.9rem;
		color: #0a4f3c;
		letter-spacing: 0.1em;
		font-weight: 600;
	}

	.card-status {
		width: 6px;
		height: 6px;
		background: #0a4f3c;
		border-radius: 50%;
		animation: statusPulse 2s ease-in-out infinite;
	}

	.card-status.active {
		background: #ff0066;
		animation: statusPulse 0.5s ease-in-out infinite;
	}

	@keyframes statusPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}

	.spectrum-chart {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.spectrum-item {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.spectrum-label {
		font-size: 0.65rem;
		color: #666;
		letter-spacing: 0.05em;
	}

	.spectrum-visual {
		position: relative;
		height: 20px;
		display: flex;
		align-items: center;
	}

	.spectrum-base {
		position: absolute;
		width: 100%;
		height: 4px;
		background: rgba(10, 79, 60, 0.1);
		border-radius: 2px;
	}

	.spectrum-fill {
		position: relative;
		height: 8px;
		border-radius: 4px;
		display: flex;
		align-items: center;
		transition: width 0.5s ease;
	}

	.spectrum-pulse {
		position: absolute;
		right: 0;
		width: 4px;
		height: 100%;
		background: rgba(255, 255, 255, 0.8);
		animation: spectrumPulse 1s ease-in-out infinite;
	}

	@keyframes spectrumPulse {
		0%, 100% { opacity: 0; transform: translateX(0); }
		50% { opacity: 1; transform: translateX(5px); }
	}

	.spectrum-value {
		position: absolute;
		right: 0;
		font-size: 0.65rem;
		color: #b8a678;
		font-weight: 600;
	}

	.threat-matrix {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 150px;
	}

	.matrix-svg {
		width: 100%;
		height: auto;
	}

	.matrix-point {
		animation: matrixPulse 3s ease-in-out infinite;
	}

	@keyframes matrixPulse {
		0%, 100% { opacity: 0.6; }
		50% { opacity: 0.9; }
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
		padding: 1.5rem;
		border-bottom: 2px solid #0a4f3c;
		background: rgba(10, 79, 60, 0.05);
	}

	.drill-header h4 {
		margin: 0;
		color: #0a4f3c;
		font-size: 1.1rem;
		letter-spacing: 0.1em;
	}

	.close-btn {
		background: rgba(255, 0, 102, 0.1);
		border: 1px solid #ff0066;
		width: 35px;
		height: 35px;
		border-radius: 2px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}

	.close-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: scale(1.1);
	}

	.drill-table-container {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}

	.host-cell {
		font-family: 'Courier New', monospace;
		color: #0a4f3c;
		font-weight: 600;
	}

	.status-badge {
		padding: 0.25rem 0.5rem;
		border-radius: 2px;
		font-size: 0.65rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
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
</style>