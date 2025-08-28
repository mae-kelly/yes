<!-- SourceTables.svelte - Enhanced Source Analysis -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let viewMode = 'table'; // 'table', 'matrix', 'flow'

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
	$: totalMentions = filteredSources.reduce((sum, [,freq]) => sum + freq, 0);

	function getPercentage(frequency) {
		if (!data.total_mentions) return 0;
		return ((frequency / data.total_mentions) * 100).toFixed(2);
	}

	function getHealthStatus(frequency) {
		const percentage = (frequency / maxFreq) * 100;
		if (percentage >= 80) return { status: 'OPTIMAL', color: '#00ff88', icon: '◆' };
		if (percentage >= 60) return { status: 'HIGH', color: '#00ffff', icon: '▲' };
		if (percentage >= 40) return { status: 'MEDIUM', color: '#ffcc00', icon: '●' };
		if (percentage >= 20) return { status: 'LOW', color: '#ff9900', icon: '■' };
		return { status: 'CRITICAL', color: '#ff0066', icon: '▼' };
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

	// Calculate source distribution for visualization
	$: sourceDistribution = filteredSources.slice(0, 10).map(([source, freq]) => {
		const health = getHealthStatus(freq);
		return {
			source,
			frequency: freq,
			percentage: getPercentage(freq),
			health
		};
	});
</script>

<div class="dashboard-container">
	<!-- Header Section -->
	<div class="module-header">
		<div class="header-content">
			<div class="module-title">
				<svg class="module-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<rect x="3" y="3" width="7" height="7" />
					<rect x="14" y="3" width="7" height="7" />
					<rect x="3" y="14" width="7" height="7" />
					<rect x="14" y="14" width="7" height="7" />
				</svg>
				<h1>SOURCE TABLES</h1>
				<span class="module-subtitle">// FREQUENCY INTELLIGENCE MATRIX</span>
			</div>
			
			<div class="header-metrics">
				<div class="metric-badge">
					<span class="metric-icon">◈</span>
					<span class="metric-value">{filteredSources.length}</span>
					<span class="metric-label">SOURCES</span>
				</div>
				<div class="metric-badge">
					<span class="metric-icon">◆</span>
					<span class="metric-value">{totalMentions.toLocaleString()}</span>
					<span class="metric-label">MENTIONS</span>
				</div>
				<div class="metric-badge">
					<span class="metric-icon">▲</span>
					<span class="metric-value">{maxFreq.toLocaleString()}</span>
					<span class="metric-label">MAX FREQ</span>
				</div>
			</div>
		</div>
		
		<div class="controls-bar">
			<input 
				type="text" 
				bind:value={searchTerm}
				placeholder="Search source tables..."
				class="search-input"
			/>
			<div class="view-toggles">
				<button class="view-btn {viewMode === 'table' ? 'active' : ''}" on:click={() => viewMode = 'table'}>
					<span class="btn-icon">▦</span> TABLE
				</button>
				<button class="view-btn {viewMode === 'matrix' ? 'active' : ''}" on:click={() => viewMode = 'matrix'}>
					<span class="btn-icon">◫</span> MATRIX
				</button>
				<button class="view-btn {viewMode === 'flow' ? 'active' : ''}" on:click={() => viewMode = 'flow'}>
					<span class="btn-icon">⬢</span> FLOW
				</button>
			</div>
		</div>
	</div>

	<!-- Main Content Area -->
	<div class="main-content">
		{#if loading && !selectedSource}
			<div class="loading-state">
				<div class="loader-ring">
					<div class="ring-segment"></div>
					<div class="ring-segment"></div>
					<div class="ring-segment"></div>
				</div>
				<p>SCANNING SOURCE FREQUENCY PATTERNS...</p>
			</div>
		{:else if selectedSource}
			<!-- Drill-down View -->
			<div class="drill-view">
				<div class="drill-header">
					<div class="drill-title">
						<span class="drill-icon">◆</span>
						<h3>{selectedSource.source.toUpperCase()}</h3>
						<span class="drill-stats">// {selectedSource.frequency} MENTIONS</span>
					</div>
					<button class="close-btn" on:click={closeDetails}>
						<span>✕</span>
					</button>
				</div>
				
				<div class="drill-metrics">
					<div class="drill-metric">
						<span class="metric-value">{hostDetails.length}</span>
						<span class="metric-label">ASSOCIATED HOSTS</span>
					</div>
					<div class="drill-metric">
						<span class="metric-value">{getPercentage(selectedSource.frequency)}%</span>
						<span class="metric-label">COVERAGE</span>
					</div>
					<div class="drill-metric">
						<span class="metric-value" style="color: {getHealthStatus(selectedSource.frequency).color}">
							{getHealthStatus(selectedSource.frequency).status}
						</span>
						<span class="metric-label">STATUS</span>
					</div>
				</div>
				
				<div class="drill-table-container">
					<table class="data-table">
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
										<span class="host-icon">▸</span>
										{host.host}
									</td>
									<td>{host.region || 'Unknown'}</td>
									<td>{host.country || 'Unknown'}</td>
									<td>{host.infrastructure_type || 'Unknown'}</td>
									<td>
										<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
											{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◉' : '○'}
										</span>
									</td>
									<td>
										<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
											{host.tanium_coverage?.toLowerCase().includes('tanium') ? '◉' : '○'}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{:else if viewMode === 'table'}
			<!-- Table View -->
			<div class="split-view">
				<div class="table-section">
					<table class="data-table">
						<thead>
							<tr>
								<th>STATUS</th>
								<th>SOURCE TABLE</th>
								<th>FREQUENCY</th>
								<th>COVERAGE</th>
								<th>VISIBILITY</th>
							</tr>
						</thead>
						<tbody>
							{#each filteredSources as [source, frequency]}
								{@const health = getHealthStatus(frequency)}
								<tr on:click={() => drillDownSource(source, frequency)}>
									<td class="status-cell">
										<span class="status-icon" style="color: {health.color}">{health.icon}</span>
									</td>
									<td class="source-cell">
										<span class="source-name">{source.toUpperCase()}</span>
									</td>
									<td class="center">{frequency.toLocaleString()}</td>
									<td class="center">{getPercentage(frequency)}%</td>
									<td>
										<div class="visibility-bar">
											<div class="visibility-fill" style="width: {(frequency/maxFreq)*100}%; background: {health.color}"></div>
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				
				<div class="viz-section">
					<!-- Frequency Wave Chart -->
					<div class="viz-card">
						<h4>FREQUENCY WAVE PATTERN</h4>
						<svg viewBox="0 0 400 200" class="wave-chart">
							<defs>
								<linearGradient id="waveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
									<stop offset="0%" style="stop-color:#00ffff;stop-opacity:0.8" />
									<stop offset="100%" style="stop-color:#00ffff;stop-opacity:0.1" />
								</linearGradient>
							</defs>
							
							{#each sourceDistribution as item, i}
								{@const x = (i / (sourceDistribution.length - 1)) * 380 + 10}
								{@const y = 180 - (item.frequency / maxFreq) * 160}
								
								{#if i === 0}
									<path d="M10,180 L{x},{y}" fill="none" stroke="#00ffff" stroke-width="2" opacity="0.8"/>
								{:else}
									{@const prevX = ((i-1) / (sourceDistribution.length - 1)) * 380 + 10}
									{@const prevY = 180 - (sourceDistribution[i-1].frequency / maxFreq) * 160}
									<path d="M{prevX},{prevY} L{x},{y}" fill="none" stroke="#00ffff" stroke-width="2" opacity="0.8"/>
								{/if}
								
								<circle cx={x} cy={y} r="4" fill={item.health.color} stroke="none">
									<animate attributeName="r" values="4;6;4" dur="2s" repeatCount="indefinite"/>
								</circle>
							{/each}
							
							<!-- Grid lines -->
							<line x1="10" y1="180" x2="390" y2="180" stroke="#111" stroke-width="1"/>
							<line x1="10" y1="20" x2="10" y2="180" stroke="#111" stroke-width="1"/>
						</svg>
					</div>
					
					<!-- Distribution Bars -->
					<div class="viz-card">
						<h4>TOP SOURCE DISTRIBUTION</h4>
						<div class="distribution-bars">
							{#each sourceDistribution.slice(0, 5) as item}
								<div class="dist-row">
									<div class="dist-label">{item.source.substring(0, 12)}</div>
									<div class="dist-bar-container">
										<div class="dist-bar" style="width: {item.percentage}%; background: {item.health.color}">
											<span class="dist-value">{item.frequency}</span>
										</div>
									</div>
									<div class="dist-percent">{item.percentage}%</div>
								</div>
							{/each}
						</div>
					</div>
				</div>
			</div>
		{:else if viewMode === 'matrix'}
			<!-- Matrix View -->
			<div class="matrix-view">
				<div class="matrix-grid">
					{#each filteredSources.slice(0, 30) as [source, frequency]}
						{@const health = getHealthStatus(frequency)}
						<div class="matrix-cell" 
							 style="background: {health.color}20; border-color: {health.color}"
							 on:click={() => drillDownSource(source, frequency)}>
							<div class="matrix-icon">{health.icon}</div>
							<div class="matrix-source">{source.substring(0, 10)}</div>
							<div class="matrix-freq">{frequency}</div>
						</div>
					{/each}
				</div>
			</div>
		{:else if viewMode === 'flow'}
			<!-- Flow View -->
			<div class="flow-view">
				<div class="flow-container">
					{#each sourceDistribution as item, i}
						<div class="flow-node" style="left: {20 + (i % 4) * 200}px; top: {50 + Math.floor(i / 4) * 150}px">
							<div class="node-core" style="border-color: {item.health.color}">
								<span class="node-icon" style="color: {item.health.color}">{item.health.icon}</span>
								<span class="node-value">{item.frequency}</span>
							</div>
							<div class="node-label">{item.source}</div>
							<div class="node-metric">{item.percentage}%</div>
							
							{#if i < sourceDistribution.length - 1}
								<svg class="flow-line" style="position: absolute; top: 50%; left: 100%; width: 200px; height: 150px; pointer-events: none;">
									<path d="M0,0 Q100,50 200,{Math.random() * 100 - 50}" 
										  fill="none" 
										  stroke="{item.health.color}" 
										  stroke-width="1" 
										  opacity="0.3"/>
								</svg>
							{/if}
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.dashboard-container {
		height: calc(100vh - 130px);
		display: flex;
		flex-direction: column;
		background: #0a0a0a;
		color: #e0e0e0;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
	}

	.module-header {
		background: linear-gradient(180deg, #0f0f0f 0%, #0a0a0a 100%);
		border-bottom: 1px solid #0a4f3c;
		padding: 1rem 1.5rem;
		flex-shrink: 0;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.module-title {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.module-icon {
		width: 32px;
		height: 32px;
		color: #00ff88;
		filter: drop-shadow(0 0 10px rgba(0, 255, 136, 0.5));
	}

	.module-title h1 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 700;
		background: linear-gradient(135deg, #00ff88, #00ffff);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		letter-spacing: 0.1em;
	}

	.module-subtitle {
		color: #666;
		font-size: 0.75rem;
		font-weight: 400;
		letter-spacing: 0.2em;
	}

	.header-metrics {
		display: flex;
		gap: 2rem;
	}

	.metric-badge {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 0.5rem 1rem;
		background: rgba(0, 255, 136, 0.05);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
	}

	.metric-icon {
		font-size: 1rem;
		color: #00ff88;
		margin-bottom: 0.25rem;
	}

	.metric-value {
		font-size: 1.25rem;
		font-weight: 600;
		color: #00ffff;
	}

	.metric-label {
		font-size: 0.6rem;
		color: #666;
		letter-spacing: 0.1em;
	}

	.controls-bar {
		display: flex;
		gap: 1rem;
		align-items: center;
	}

	.search-input {
		flex: 1;
		max-width: 400px;
		background: #000;
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		padding: 0.5rem 1rem;
		color: #e0e0e0;
		font-family: inherit;
		font-size: 0.85rem;
	}

	.search-input:focus {
		outline: none;
		border-color: #00ffff;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
	}

	.view-toggles {
		display: flex;
		gap: 0.5rem;
	}

	.view-btn {
		background: #000;
		border: 1px solid #0a4f3c;
		color: #666;
		padding: 0.5rem 1rem;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.2s ease;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-family: inherit;
		font-size: 0.75rem;
		letter-spacing: 0.05em;
	}

	.view-btn:hover {
		border-color: #00ffff;
		color: #00ffff;
		background: rgba(0, 255, 255, 0.05);
	}

	.view-btn.active {
		background: rgba(0, 255, 136, 0.1);
		border-color: #00ff88;
		color: #00ff88;
	}

	.btn-icon {
		font-size: 1rem;
	}

	.main-content {
		flex: 1;
		overflow: hidden;
		padding: 1rem;
	}

	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		gap: 2rem;
	}

	.loader-ring {
		width: 60px;
		height: 60px;
		position: relative;
		animation: rotate 2s linear infinite;
	}

	.ring-segment {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid transparent;
		border-top-color: #00ff88;
		border-radius: 50%;
		animation: pulse 1.5s ease-in-out infinite;
	}

	.ring-segment:nth-child(2) {
		transform: rotate(120deg);
		border-top-color: #00ffff;
		animation-delay: 0.5s;
	}

	.ring-segment:nth-child(3) {
		transform: rotate(240deg);
		border-top-color: #ff00ff;
		animation-delay: 1s;
	}

	@keyframes rotate {
		to { transform: rotate(360deg); }
	}

	@keyframes pulse {
		0%, 100% { opacity: 0.3; }
		50% { opacity: 1; }
	}

	.split-view {
		display: flex;
		gap: 1rem;
		height: 100%;
	}

	.table-section {
		flex: 1.5;
		overflow-y: auto;
		background: #0f0f0f;
		border: 1px solid #1a1a1a;
		border-radius: 8px;
	}

	.viz-section {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.85rem;
	}

	.data-table th {
		background: #0f0f0f;
		color: #00ff88;
		padding: 0.75rem;
		text-align: left;
		font-weight: 500;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 2px solid #0a4f3c;
	}

	.data-table td {
		padding: 0.75rem;
		border-bottom: 1px solid #1a1a1a;
		color: #b8a678;
		transition: all 0.2s ease;
	}

	.data-table tbody tr {
		cursor: pointer;
		transition: background 0.2s ease;
	}

	.data-table tbody tr:hover {
		background: rgba(0, 255, 136, 0.03);
	}

	.status-cell {
		text-align: center;
	}

	.status-icon {
		font-size: 1rem;
	}

	.source-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.source-name {
		font-weight: 500;
		color: #e0e0e0;
	}

	.center {
		text-align: center;
	}

	.visibility-bar {
		height: 6px;
		background: #1a1a1a;
		border-radius: 3px;
		overflow: hidden;
	}

	.visibility-fill {
		height: 100%;
		transition: width 0.3s ease;
		box-shadow: 0 0 10px currentColor;
	}

	.viz-card {
		background: #0f0f0f;
		border: 1px solid #1a1a1a;
		border-radius: 8px;
		padding: 1rem;
	}

	.viz-card h4 {
		margin: 0 0 1rem 0;
		font-size: 0.85rem;
		color: #00ff88;
		letter-spacing: 0.1em;
		font-weight: 500;
	}

	.wave-chart {
		width: 100%;
		height: 200px;
	}

	.distribution-bars {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.dist-row {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.dist-label {
		min-width: 100px;
		font-size: 0.75rem;
		color: #b8a678;
		text-align: right;
	}

	.dist-bar-container {
		flex: 1;
		height: 20px;
		background: #1a1a1a;
		border-radius: 4px;
		position: relative;
		overflow: hidden;
	}

	.dist-bar {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding-right: 0.5rem;
		transition: width 0.3s ease;
	}

	.dist-value {
		font-size: 0.7rem;
		color: #000;
		font-weight: 600;
	}

	.dist-percent {
		min-width: 50px;
		font-size: 0.75rem;
		color: #00ffff;
		text-align: right;
	}

	.matrix-view {
		height: 100%;
		overflow: auto;
	}

	.matrix-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
		gap: 0.75rem;
		padding: 1rem;
	}

	.matrix-cell {
		aspect-ratio: 1;
		background: rgba(0, 255, 136, 0.05);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.2s ease;
		padding: 0.5rem;
	}

	.matrix-cell:hover {
		transform: scale(1.05);
		box-shadow: 0 0 15px currentColor;
	}

	.matrix-icon {
		font-size: 1.5rem;
		margin-bottom: 0.25rem;
	}

	.matrix-source {
		font-size: 0.65rem;
		color: #b8a678;
		margin-bottom: 0.25rem;
		text-align: center;
	}

	.matrix-freq {
		font-size: 0.75rem;
		color: #00ffff;
		font-weight: 600;
	}

	.flow-view {
		height: 100%;
		overflow: auto;
		position: relative;
	}

	.flow-container {
		position: relative;
		min-height: 600px;
		padding: 2rem;
	}

	.flow-node {
		position: absolute;
		display: flex;
		flex-direction: column;
		align-items: center;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.flow-node:hover {
		transform: scale(1.1);
		z-index: 10;
	}

	.node-core {
		width: 80px;
		height: 80px;
		border: 2px solid;
		border-radius: 50%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.8);
		margin-bottom: 0.5rem;
	}

	.node-icon {
		font-size: 1.2rem;
		margin-bottom: 0.25rem;
	}

	.node-value {
		font-size: 0.85rem;
		color: #e0e0e0;
		font-weight: 600;
	}

	.node-label {
		font-size: 0.7rem;
		color: #b8a678;
		text-align: center;
		max-width: 100px;
	}

	.node-metric {
		font-size: 0.65rem;
		color: #00ffff;
		margin-top: 0.25rem;
	}

	.drill-view {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: #0f0f0f;
		border: 1px solid #0a4f3c;
		border-radius: 8px;
		overflow: hidden;
	}

	.drill-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
		background: rgba(0, 255, 136, 0.05);
		border-bottom: 2px solid #0a4f3c;
	}

	.drill-title {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.drill-icon {
		font-size: 1.5rem;
		color: #00ff88;
	}

	.drill-title h3 {
		margin: 0;
		color: #00ff88;
		font-size: 1.2rem;
		letter-spacing: 0.1em;
	}

	.drill-stats {
		color: #666;
		font-size: 0.75rem;
		font-weight: 400;
	}

	.close-btn {
		background: rgba(255, 0, 102, 0.1);
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 36px;
		height: 36px;
		border-radius: 4px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.2rem;
		font-weight: 600;
		transition: all 0.2s ease;
	}

	.close-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: scale(1.1);
	}

	.drill-metrics {
		display: flex;
		gap: 2rem;
		padding: 1rem 1.5rem;
		background: rgba(0, 0, 0, 0.5);
		border-bottom: 1px solid #1a1a1a;
	}

	.drill-metric {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}

	.drill-metric .metric-value {
		font-size: 1.5rem;
		font-weight: 600;
		color: #00ffff;
	}

	.drill-metric .metric-label {
		font-size: 0.65rem;
		color: #666;
		letter-spacing: 0.1em;
		text-transform: uppercase;
	}

	.drill-table-container {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}

	.host-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-family: 'Courier New', monospace;
		color: #00ffff;
		font-weight: 500;
	}

	.host-icon {
		color: #0a4f3c;
	}

	.status-badge {
		font-size: 1rem;
		transition: all 0.2s ease;
	}

	.status-badge.active {
		color: #00ff88;
		filter: drop-shadow(0 0 5px currentColor);
	}

	.status-badge.inactive {
		color: #ff0066;
		opacity: 0.5;
	}