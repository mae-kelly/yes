<!-- ech/SourceTables.svelte -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let sortField = 'frequency';
	let sortDirection = 'desc';

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
			.sort((a, b) => {
				if (sortField === 'frequency') {
					return sortDirection === 'desc' ? b[1] - a[1] : a[1] - b[1];
				} else {
					return sortDirection === 'desc' ? 
						b[0].localeCompare(a[0]) : a[0].localeCompare(b[0]);
				}
			}) : [];

	function getThreatLevel(frequency) {
		if (!data.total_mentions) return { level: 'LOW', color: '#0096ff', intensity: 0.3 };
		let percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRITICAL', color: '#ff00ff', intensity: 1.0 };
		if (percentage >= 10) return { level: 'HIGH', color: '#ff0066', intensity: 0.8 };
		if (percentage >= 5) return { level: 'MEDIUM', color: '#ffaa00', intensity: 0.6 };
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

	function sortBy(field) {
		if (sortField === field) {
			sortDirection = sortDirection === 'desc' ? 'asc' : 'desc';
		} else {
			sortField = field;
			sortDirection = 'desc';
		}
	}

	function closeDetails() {
		selectedSource = null;
		hostDetails = [];
	}
</script>

<div class="source-intelligence-matrix">
	<div class="matrix-header">
		<div class="header-glow"></div>
		<div class="header-content">
			<div class="intel-title">
				<span class="title-icon">◈</span>
				<div class="title-text">
					<h2>Source Intelligence Analysis</h2>
					<p>Log source frequency and coverage mapping</p>
				</div>
			</div>
			
			<div class="intel-metrics">
				<div class="metric-node">
					<div class="metric-ring"></div>
					<div class="metric-data">
						<span class="metric-value">{(data.unique_sources || 0).toLocaleString()}</span>
						<span class="metric-label">SOURCES</span>
					</div>
				</div>
				
				<div class="metric-node">
					<div class="metric-ring"></div>
					<div class="metric-data">
						<span class="metric-value">{(data.total_mentions || 0).toLocaleString()}</span>
						<span class="metric-label">MENTIONS</span>
					</div>
				</div>
			</div>
		</div>
	</div>

	<div class="control-panel">
		<div class="search-terminal">
			<input 
				type="text" 
				bind:value={searchTerm}
				placeholder="SEARCH SOURCE TABLES..."
				class="terminal-input"
			/>
			<div class="search-scanner"></div>
		</div>
		
		<div class="view-controls">
			<button class="control-btn {!selectedSource ? 'active' : ''}" on:click={closeDetails}>
				TABLE VIEW
			</button>
			{#if selectedSource}
				<button class="control-btn active">
					DRILL-DOWN: {selectedSource.source}
				</button>
			{/if}
		</div>
	</div>

	{#if loading && !selectedSource}
		<div class="loading-matrix">
			<div class="matrix-loader">
				<div class="loader-grid">
					{#each Array(16) as _, i}
						<div class="grid-cell" style="animation-delay: {i * 0.1}s"></div>
					{/each}
				</div>
			</div>
			<p class="loading-text">SCANNING SOURCE INTELLIGENCE...</p>
		</div>
	{:else if selectedSource}
		<div class="drill-down-view">
			<div class="drill-header">
				<div class="selected-source">
					<div class="source-badge" style="--badge-color: {getThreatLevel(selectedSource.frequency).color}">
						<span class="badge-level">{getThreatLevel(selectedSource.frequency).level}</span>
					</div>
					<div class="source-info">
						<h3>{selectedSource.source}</h3>
						<div class="source-stats">
							<span>Frequency: {selectedSource.frequency.toLocaleString()}</span>
							<span>Coverage: {getPercentage(selectedSource.frequency)}%</span>
						</div>
					</div>
				</div>
				
				<button class="close-btn" on:click={closeDetails}>✕</button>
			</div>

			{#if loading}
				<div class="loading-hosts">
					<div class="host-scanner"></div>
					<p>RETRIEVING HOST DETAILS...</p>
				</div>
			{:else}
				<div class="host-table-container">
					<table class="cyber-table host-table">
						<thead>
							<tr class="table-header">
								<th>HOST</th>
								<th>REGION</th>
								<th>COUNTRY</th>
								<th>INFRASTRUCTURE</th>
								<th>DATA CENTER</th>
								<th>CMDB STATUS</th>
								<th>TANIUM</th>
							</tr>
						</thead>
						<tbody>
							{#each hostDetails.slice(0, 100) as host}
								<tr class="host-row">
									<td class="host-name">{host.host}</td>
									<td class="host-region">{host.region}</td>
									<td class="host-country">{host.country}</td>
									<td class="host-infra">{host.infrastructure_type}</td>
									<td class="host-dc">{host.data_center}</td>
									<td class="host-cmdb">
										<span class="status-indicator {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
											{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'ACTIVE' : 'INACTIVE'}
										</span>
									</td>
									<td class="host-tanium">
										<span class="status-indicator {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
											{host.tanium_coverage?.toLowerCase().includes('tanium') ? 'COVERED' : 'NOT COVERED'}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	{:else}
		<div class="data-table-container">
			<table class="cyber-table source-table">
				<thead>
					<tr class="table-header">
						<th class="sortable" on:click={() => sortBy('source')}>
							SOURCE TABLE
							{#if sortField === 'source'}
								<span class="sort-indicator">{sortDirection === 'desc' ? '↓' : '↑'}</span>
							{/if}
						</th>
						<th class="sortable" on:click={() => sortBy('frequency')}>
							FREQUENCY
							{#if sortField === 'frequency'}
								<span class="sort-indicator">{sortDirection === 'desc' ? '↓' : '↑'}</span>
							{/if}
						</th>
						<th>COVERAGE %</th>
						<th>THREAT LEVEL</th>
						<th>ACTIONS</th>
					</tr>
				</thead>
				<tbody>
					{#each filteredSources.slice(0, 50) as [source, frequency]}
						<tr class="source-row" style="--threat-color: {getThreatLevel(frequency).color}">
							<td class="source-name">
								<div class="name-container">
									<div class="name-indicator"></div>
									{source}
								</div>
							</td>
							<td class="source-frequency">
								<span class="frequency-value">{frequency.toLocaleString()}</span>
							</td>
							<td class="source-coverage">
								<div class="coverage-bar">
									<div class="coverage-fill" style="width: {getPercentage(frequency)}%; background: {getThreatLevel(frequency).color};"></div>
									<span class="coverage-text">{getPercentage(frequency)}%</span>
								</div>
							</td>
							<td class="source-threat">
								<span class="threat-badge {getThreatLevel(frequency).level.toLowerCase()}" style="--threat-color: {getThreatLevel(frequency).color}">
									{getThreatLevel(frequency).level}
								</span>
							</td>
							<td class="source-actions">
								<button class="drill-btn" on:click={() => drillDownSource(source, frequency)}>
									<span class="btn-icon">⚡</span>
									DRILL DOWN
								</button>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}

	<div class="matrix-footer">
		<div class="footer-stats">
			<span>Displaying {filteredSources.length} of {data.unique_sources || 0} sources</span>
			<span>Total coverage: {((data.total_mentions || 0) / (data.unique_sources || 1)).toFixed(0)} avg mentions/source</span>
		</div>
		<div class="neural-signature">
			◈ NEURAL PROTOCOL ACTIVE
		</div>
	</div>
</div>

<style>
	.source-intelligence-matrix {
		width: 100%;
		height: 100%;
		font-family: 'JetBrains Mono', monospace;
		color: #ffffff;
		display: flex;
		flex-direction: column;
		background: transparent;
	}

	.matrix-header {
		position: relative;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(0, 255, 255, 0.05) 50%,
			rgba(0, 0, 0, 0.8) 100%);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 12px;
		margin-bottom: 1.5rem;
		overflow: hidden;
	}

	.header-glow {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: linear-gradient(45deg, 
			rgba(0, 255, 255, 0.1), 
			rgba(255, 0, 255, 0.05),
			rgba(0, 255, 255, 0.1));
		animation: headerGlow 4s ease-in-out infinite;
		pointer-events: none;
	}

	.header-content {
		position: relative;
		z-index: 2;
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem 2rem;
	}

	.intel-title {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.title-icon {
		font-size: 2rem;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
		animation: iconPulse 3s ease-in-out infinite;
	}

	.title-text h2 {
		margin: 0;
		font-size: 1.4rem;
		font-weight: 700;
		color: #ffffff;
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
	}

	.title-text p {
		margin: 0.3rem 0 0 0;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 300;
	}

	.intel-metrics {
		display: flex;
		gap: 2rem;
	}

	.metric-node {
		position: relative;
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem 1.5rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.05));
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 8px;
		backdrop-filter: blur(10px);
	}

	.metric-ring {
		width: 12px;
		height: 12px;
		border: 2px solid rgba(0, 255, 255, 0.8);
		border-radius: 50%;
		animation: ringPulse 2s ease-in-out infinite;
	}

	.metric-data {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.metric-value {
		font-size: 1.2rem;
		font-weight: 700;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}

	.metric-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 400;
		letter-spacing: 0.05em;
	}

	.control-panel {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		gap: 2rem;
	}

	.search-terminal {
		position: relative;
		flex: 1;
		max-width: 400px;
	}

	.terminal-input {
		width: 100%;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 255, 255, 0.05));
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 6px;
		padding: 0.8rem 1rem;
		color: #ffffff;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.9rem;
		backdrop-filter: blur(10px);
		transition: all 0.3s ease;
	}

	.terminal-input::placeholder {
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.05em;
	}

	.terminal-input:focus {
		outline: none;
		border-color: rgba(0, 255, 255, 0.8);
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
		text-shadow: 0 0 8px rgba(0, 255, 255, 0.3);
	}

	.search-scanner {
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.2), transparent);
		animation: scannerSweep 3s linear infinite;
		border-radius: 6px;
		pointer-events: none;
	}

	.view-controls {
		display: flex;
		gap: 0.5rem;
	}

	.control-btn {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 6px;
		padding: 0.6rem 1.2rem;
		color: rgba(255, 255, 255, 0.7);
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.7rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.3s ease;
		letter-spacing: 0.02em;
	}

	.control-btn:hover,
	.control-btn.active {
		border-color: rgba(0, 255, 255, 0.6);
		color: rgba(0, 255, 255, 0.9);
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
	}

	.loading-matrix {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 300px;
		gap: 2rem;
	}

	.matrix-loader {
		position: relative;
		width: 80px;
		height: 80px;
	}

	.loader-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		grid-template-rows: repeat(4, 1fr);
		gap: 2px;
		width: 100%;
		height: 100%;
	}

	.grid-cell {
		background: rgba(0, 255, 255, 0.3);
		animation: cellFlicker 1.5s ease-in-out infinite;
	}

	.loading-text {
		color: rgba(0, 255, 255, 0.8);
		font-size: 1rem;
		font-weight: 500;
		letter-spacing: 0.1em;
		animation: textGlow 2s ease-in-out infinite;
	}

	.data-table-container {
		flex: 1;
		overflow: auto;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.02));
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 12px;
		padding: 0;
	}

	.cyber-table {
		width: 100%;
		border-collapse: collapse;
		font-family: 'JetBrains Mono', monospace;
	}

	.table-header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(0, 255, 255, 0.1));
		border-bottom: 2px solid rgba(0, 255, 255, 0.3);
	}

	.table-header th {
		padding: 1rem 1.5rem;
		text-align: left;
		font-size: 0.8rem;
		font-weight: 700;
		color: rgba(0, 255, 255, 0.9);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		position: relative;
	}

	.sortable {
		cursor: pointer;
		user-select: none;
		transition: all 0.2s ease;
	}

	.sortable:hover {
		color: #ffffff;
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.6);
	}

	.sort-indicator {
		margin-left: 0.5rem;
		color: rgba(255, 0, 255, 0.8);
	}

	.source-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.3s ease;
		position: relative;
	}

	.source-row:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.05), rgba(255, 0, 255, 0.02));
		box-shadow: inset 3px 0 0 var(--threat-color);
	}

	.source-row td {
		padding: 1rem 1.5rem;
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.8);
		vertical-align: middle;
	}

	.source-name {
		font-weight: 600;
		color: #ffffff;
	}

	.name-container {
		display: flex;
		align-items: center;
		gap: 0.8rem;
	}

	.name-indicator {
		width: 6px;
		height: 6px;
		background: var(--threat-color);
		border-radius: 50%;
		animation: indicatorPulse 2s ease-in-out infinite;
	}

	.frequency-value {
		font-weight: 700;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 8px rgba(0, 255, 255, 0.3);
	}

	.coverage-bar {
		position: relative;
		width: 100px;
		height: 20px;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 10px;
		overflow: hidden;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.coverage-fill {
		height: 100%;
		border-radius: 10px;
		transition: width 1s ease-out;
		box-shadow: 0 0 10px currentColor;
	}

	.coverage-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 0.7rem;
		font-weight: 600;
		color: #ffffff;
		text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
	}

	.threat-badge {
		padding: 0.3rem 0.8rem;
		border-radius: 4px;
		font-size: 0.7rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border: 1px solid var(--threat-color);
		background: rgba(0, 0, 0, 0.4);
		color: var(--threat-color);
		text-shadow: 0 0 8px var(--threat-color);
	}

	.drill-btn {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.05));
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 6px;
		padding: 0.5rem 1rem;
		color: rgba(0, 255, 255, 0.9);
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.7rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}

	.drill-btn:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 255, 255, 0.1));
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
		transform: translateY(-1px);
	}

	.btn-icon {
		font-size: 0.8rem;
		animation: iconSpark 2s ease-in-out infinite;
	}

	.drill-down-view {
		flex: 1;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 0, 255, 0.02));
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 12px;
		overflow: hidden;
	}

	.drill-header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(255, 0, 255, 0.05));
		border-bottom: 1px solid rgba(255, 0, 255, 0.3);
		padding: 1.5rem 2rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.selected-source {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.source-badge {
		padding: 0.5rem 1rem;
		border: 2px solid var(--badge-color);
		border-radius: 6px;
		background: rgba(0, 0, 0, 0.6);
		text-align: center;
	}

	.badge-level {
		font-size: 0.7rem;
		font-weight: 700;
		color: var(--badge-color);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		text-shadow: 0 0 10px var(--badge-color);
	}

	.source-info h3 {
		margin: 0;
		font-size: 1.2rem;
		color: #ffffff;
		text-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
	}

	.source-stats {
		display: flex;
		gap: 1.5rem;
		margin-top: 0.5rem;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.close-btn {
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.2), rgba(255, 0, 102, 0.1));
		border: 1px solid rgba(255, 0, 102, 0.5);
		border-radius: 50%;
		width: 40px;
		height: 40px;
		color: rgba(255, 0, 102, 0.9);
		font-family: 'JetBrains Mono', monospace;
		font-size: 1.2rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-btn:hover {
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.3), rgba(255, 0, 102, 0.2));
		box-shadow: 0 0 20px rgba(255, 0, 102, 0.4);
		transform: rotate(90deg);
	}

	.loading-hosts {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 200px;
		gap: 1rem;
		color: rgba(255, 0, 255, 0.8);
	}

	.host-scanner {
		width: 40px;
		height: 40px;
		border: 3px solid rgba(255, 0, 255, 0.2);
		border-top: 3px solid rgba(255, 0, 255, 0.8);
		border-radius: 50%;
		animation: scan 1s linear infinite;
	}

	.host-table-container {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}

	.host-table .table-header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(255, 0, 255, 0.1));
		border-bottom: 2px solid rgba(255, 0, 255, 0.3);
	}

	.host-table .table-header th {
		color: rgba(255, 0, 255, 0.9);
	}

	.host-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.2s ease;
	}

	.host-row:hover {
		background: linear-gradient(135deg, rgba(255, 0, 255, 0.05), rgba(0, 255, 255, 0.02));
	}

	.host-row td {
		padding: 0.8rem 1.5rem;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.7);
	}

	.host-name {
		color: #ffffff;
		font-weight: 600;
	}

	.status-indicator {
		padding: 0.2rem 0.6rem;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.02em;
	}

	.status-indicator.active {
		background: rgba(0, 255, 133, 0.1);
		color: #00ff85;
		border: 1px solid #00ff85;
		text-shadow: 0 0 8px #00ff85;
	}

	.status-indicator.inactive {
		background: rgba(255, 0, 102, 0.1);
		color: #ff0066;
		border: 1px solid #ff0066;
		text-shadow: 0 0 8px #ff0066;
	}

	.matrix-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 0;
		margin-top: 1.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}

	.footer-stats {
		display: flex;
		gap: 2rem;
	}

	.neural-signature {
		color: rgba(0, 255, 255, 0.7);
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	@keyframes headerGlow {
		0%, 100% { opacity: 0.3; }
		50% { opacity: 0.6; }
	}

	@keyframes iconPulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.1); }
	}

	@keyframes ringPulse {
		0%, 100% { 
			border-color: rgba(0, 255, 255, 0.8); 
			box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
		}
		50% { 
			border-color: rgba(0, 255, 255, 1); 
			box-shadow: 0 0 20px rgba(0, 255, 255, 0.6);
		}
	}

	@keyframes scannerSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes cellFlicker {
		0%, 100% { opacity: 0.3; background: rgba(0, 255, 255, 0.3); }
		50% { opacity: 1; background: rgba(0, 255, 255, 0.8); }
	}

	@keyframes textGlow {
		0%, 100% { text-shadow: 0 0 10px rgba(0, 255, 255, 0.5); }
		50% { text-shadow: 0 0 20px rgba(0, 255, 255, 0.8); }
	}

	@keyframes indicatorPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.6; transform: scale(1.2); }
	}

	@keyframes iconSpark {
		0%, 100% { text-shadow: 0 0 5px rgba(0, 255, 255, 0.5); }
		50% { text-shadow: 0 0 15px rgba(0, 255, 255, 0.8); }
	}

	@keyframes scan {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@media (max-width: 1200px) {
		.header-content {
			flex-direction: column;
			gap: 1rem;
		}

		.control-panel {
			flex-direction: column;
			gap: 1rem;
		}
	}

	@media (max-width: 768px) {
		.cyber-table {
			font-size: 0.7rem;
		}

		.cyber-table th,
		.cyber-table td {
			padding: 0.6rem 0.8rem;
		}

		.drill-header {
			flex-direction: column;
			gap: 1rem;
			align-items: flex-start;
		}
	}
</style>