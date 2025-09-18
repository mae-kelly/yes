<!-- SourceTables.svelte - Source Table Host Distribution -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	
	// Animation states
	let animationFrame = null;
	let pulseValue = 0;
	
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
		
		// Start animations
		const animate = () => {
			pulseValue = (Math.sin(Date.now() * 0.002) + 1) / 2;
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});

	$: filteredSources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = filteredSources.reduce((sum, [_, count]) => sum + count, 0);
	$: maxCount = filteredSources.length > 0 ? Math.max(...filteredSources.map(([,c]) => c)) : 1;
	$: avgHosts = filteredSources.length > 0 ? Math.round(totalHosts / filteredSources.length) : 0;
	
	// Top 5 sources for visualization
	$: topSources = filteredSources.slice(0, 5);
	$: bottomSources = filteredSources.slice(-5).reverse();

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
	
	function getTableHealth(count) {
		const percentage = (count / maxCount) * 100;
		if (percentage >= 75) return { status: 'OPTIMAL', color: '#BD93F9' };
		if (percentage >= 50) return { status: 'ACTIVE', color: '#8BE9FD' };
		if (percentage >= 25) return { status: 'MODERATE', color: '#50FA7B' };
		return { status: 'LOW', color: '#FFB86C' };
	}
</script>

<div class="source-interface">
	<div class="interface-grid">
		<!-- Left Panel: Key Metrics -->
		<div class="metrics-panel">
			<div class="metric-card primary">
				<div class="metric-value" style="color: #BD93F9">
					{filteredSources.length}
				</div>
				<div class="metric-label">SOURCE TABLES</div>
				<div class="metric-trend">
					<svg viewBox="0 0 50 20">
						<polyline points="0,15 10,12 20,8 30,10 40,5 50,8" 
								  stroke="#BD93F9" stroke-width="1" fill="none" opacity="0.5"/>
					</svg>
				</div>
			</div>
			
			<div class="metric-card">
				<div class="metric-value" style="color: #8BE9FD">
					{totalHosts.toLocaleString()}
				</div>
				<div class="metric-label">TOTAL HOSTS</div>
			</div>
			
			<div class="metric-card">
				<div class="metric-value" style="color: #50FA7B">
					{avgHosts.toLocaleString()}
				</div>
				<div class="metric-label">AVG HOSTS/TABLE</div>
			</div>
			
			<div class="metric-card">
				<div class="metric-value" style="color: #FFB86C">
					{maxCount.toLocaleString()}
				</div>
				<div class="metric-label">MAX TABLE SIZE</div>
			</div>
		</div>
		
		<!-- Center Panel: Distribution Visualization -->
		<div class="visualization-panel">
			<div class="vis-header">
				<h2>HOST DISTRIBUTION ACROSS SOURCE TABLES</h2>
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="Filter tables..."
					   class="search-input"/>
			</div>
			
			{#if loading && !selectedSource}
				<div class="loading-state">
					<div class="loader-rings">
						<div class="ring r1"></div>
						<div class="ring r2"></div>
						<div class="ring r3"></div>
					</div>
					<p>ANALYZING SOURCE TABLES...</p>
				</div>
			{:else if selectedSource}
				<div class="detail-view">
					<div class="detail-header">
						<div class="detail-title">
							<h3>{selectedSource.source.toUpperCase()}</h3>
							<span class="host-count">{selectedSource.frequency.toLocaleString()} HOSTS</span>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="detail-grid">
						<table class="hosts-table">
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>TYPE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each hostDetails as host}
									<tr>
										<td class="hostname">{host.host}</td>
										<td>{host.region || 'UNKNOWN'}</td>
										<td>{host.country || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>
											<span class="status {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'missing'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '●' : '○'}
											</span>
										</td>
										<td>
											<span class="status {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'missing'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? '●' : '○'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="distribution-view">
					<!-- Bar Chart -->
					<div class="chart-container">
						<div class="chart-title">TOP SOURCE TABLES BY HOST COUNT</div>
						<div class="bar-chart">
							{#each topSources as [source, count], i}
								{@const health = getTableHealth(count)}
								<div class="bar-group">
									<div class="bar-wrapper">
										<div class="bar" 
											 style="height: {(count/maxCount)*100}%; 
													background: linear-gradient(180deg, {health.color}, {health.color}40);
													animation-delay: {i * 0.1}s"
											 on:click={() => drillDownSource(source, count)}>
											<span class="bar-value">{count.toLocaleString()}</span>
										</div>
									</div>
									<div class="bar-label">{source.substring(0, 15).toUpperCase()}</div>
								</div>
							{/each}
						</div>
					</div>
					
					<!-- Heat Map Grid -->
					<div class="heatmap-container">
						<div class="chart-title">SOURCE TABLE DENSITY MAP</div>
						<div class="heatmap-grid">
							{#each filteredSources.slice(0, 30) as [source, count], i}
								{@const intensity = count / maxCount}
								{@const health = getTableHealth(count)}
								<div class="heat-cell"
									 style="background: {health.color}; 
											opacity: {0.3 + intensity * 0.7}"
									 title="{source}: {count} hosts"
									 on:click={() => drillDownSource(source, count)}>
								</div>
							{/each}
						</div>
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Right Panel: Table List -->
		<div class="table-panel">
			<div class="panel-header">
				<h3>ALL SOURCE TABLES</h3>
				<span class="table-count">{filteredSources.length} TABLES</span>
			</div>
			<div class="table-list">
				<table class="source-table">
					<thead>
						<tr>
							<th>TABLE</th>
							<th>HOSTS</th>
							<th>%</th>
							<th>STATUS</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredSources as [source, count], i}
							{@const health = getTableHealth(count)}
							{@const percentage = ((count / totalHosts) * 100).toFixed(1)}
							<tr on:click={() => drillDownSource(source, count)}>
								<td class="table-name">
									<span class="table-indicator" style="background: {health.color}"></span>
									{source.substring(0, 20).toUpperCase()}
								</td>
								<td class="table-count" style="color: {health.color}">
									{count.toLocaleString()}
								</td>
								<td class="table-percent">
									<div class="percent-bar">
										<div class="percent-fill" style="width: {percentage}%; background: {health.color}"></div>
									</div>
									<span>{percentage}%</span>
								</td>
								<td>
									<span class="status-badge" style="color: {health.color}; border-color: {health.color}">
										{health.status}
									</span>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>
</div>

<style>
	.source-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		padding: 1rem;
		overflow: hidden;
	}
	
	.interface-grid {
		height: 100%;
		display: grid;
		grid-template-columns: 200px 1fr 400px;
		gap: 1rem;
	}
	
	/* Metrics Panel */
	.metrics-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.metric-card {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1rem;
		position: relative;
	}
	
	.metric-card.primary {
		background: linear-gradient(135deg, rgba(189, 147, 249, 0.1), transparent);
		border-color: rgba(189, 147, 249, 0.3);
	}
	
	.metric-value {
		font-size: 2rem;
		font-weight: 700;
		margin-bottom: 0.25rem;
		font-family: 'Courier New', monospace;
	}
	
	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}
	
	.metric-trend {
		position: absolute;
		bottom: 0.5rem;
		right: 0.5rem;
		width: 50px;
		height: 20px;
		opacity: 0.5;
	}
	
	/* Visualization Panel */
	.visualization-panel {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 12px;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
	}
	
	.vis-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.vis-header h2 {
		margin: 0;
		font-size: 1rem;
		font-weight: 300;
		letter-spacing: 0.2em;
		color: #8BE9FD;
	}
	
	.search-input {
		padding: 0.5rem 1rem;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(139, 233, 253, 0.3);
		border-radius: 8px;
		color: #FFFFFF;
		font-size: 0.8rem;
		width: 200px;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #8BE9FD;
		background: rgba(139, 233, 253, 0.05);
	}
	
	/* Distribution View */
	.distribution-view {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
	}
	
	.chart-container, .heatmap-container {
		display: flex;
		flex-direction: column;
	}
	
	.chart-title {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		margin-bottom: 1rem;
	}
	
	.bar-chart {
		flex: 1;
		display: flex;
		align-items: flex-end;
		gap: 1rem;
		padding: 1rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 8px;
	}
	
	.bar-group {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}
	
	.bar-wrapper {
		width: 100%;
		height: 200px;
		display: flex;
		align-items: flex-end;
		justify-content: center;
	}
	
	.bar {
		width: 60%;
		min-height: 20px;
		border-radius: 4px 4px 0 0;
		display: flex;
		align-items: flex-start;
		justify-content: center;
		padding-top: 0.5rem;
		cursor: pointer;
		transition: all 0.3s ease;
		animation: barGrow 0.5s ease-out forwards;
		opacity: 0;
	}
	
	@keyframes barGrow {
		to { opacity: 1; }
	}
	
	.bar:hover {
		filter: brightness(1.2);
		transform: translateY(-2px);
	}
	
	.bar-value {
		font-size: 0.75rem;
		font-weight: 600;
		color: #FFFFFF;
	}
	
	.bar-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		text-align: center;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		width: 100%;
	}
	
	.heatmap-grid {
		flex: 1;
		display: grid;
		grid-template-columns: repeat(6, 1fr);
		grid-template-rows: repeat(5, 1fr);
		gap: 3px;
		background: rgba(0, 0, 0, 0.3);
		padding: 1rem;
		border-radius: 8px;
	}
	
	.heat-cell {
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	.heat-cell:hover {
		transform: scale(1.1);
		z-index: 10;
		box-shadow: 0 0 20px currentColor;
	}
	
	/* Table Panel */
	.table-panel {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.panel-header {
		padding: 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.panel-header h3 {
		margin: 0;
		font-size: 0.9rem;
		font-weight: 300;
		letter-spacing: 0.1em;
		color: #BD93F9;
	}
	
	.table-count {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.table-list {
		flex: 1;
		overflow-y: auto;
	}
	
	.source-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.source-table thead {
		position: sticky;
		top: 0;
		background: #000000;
		z-index: 10;
	}
	
	.source-table th {
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.source-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.source-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.05);
	}
	
	.source-table td {
		padding: 0.75rem;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.table-name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.table-indicator {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.table-count {
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.table-percent {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
	}
	
	.percent-bar {
		width: 40px;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.percent-fill {
		height: 100%;
		transition: width 0.3s ease;
	}
	
	.status-badge {
		font-size: 0.65rem;
		padding: 0.2rem 0.4rem;
		border: 1px solid;
		border-radius: 4px;
		font-weight: 600;
		letter-spacing: 0.05em;
	}
	
	/* Detail View */
	.detail-view {
		flex: 1;
		display: flex;
		flex-direction: column;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}
	
	.detail-title h3 {
		margin: 0;
		font-size: 1.2rem;
		color: #BD93F9;
		margin-bottom: 0.25rem;
	}
	
	.host-count {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
	}
	
	.close-btn {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		color: #FFFFFF;
		width: 32px;
		height: 32px;
		border-radius: 8px;
		font-size: 1.2rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}
	
	.close-btn:hover {
		background: rgba(189, 147, 249, 0.2);
		border-color: #BD93F9;
		transform: scale(1.1);
	}
	
	.detail-grid {
		flex: 1;
		overflow-y: auto;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 8px;
		padding: 1rem;
	}
	
	.hosts-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.hosts-table th {
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.9);
	}
	
	.hosts-table td {
		padding: 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.hostname {
		font-family: 'Courier New', monospace;
		color: #8BE9FD;
		font-size: 0.7rem;
	}
	
	.status {
		font-size: 1rem;
	}
	
	.status.active {
		color: #50FA7B;
	}
	
	.status.missing {
		color: #FF5555;
	}
	
	/* Loading State */
	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.loader-rings {
		position: relative;
		width: 80px;
		height: 80px;
	}
	
	.ring {
		position: absolute;
		border: 2px solid;
		border-radius: 50%;
		border-top-color: transparent;
		animation: spin 1s linear infinite;
	}
	
	.ring.r1 {
		inset: 0;
		border-color: #BD93F9;
		border-top-color: transparent;
	}
	
	.ring.r2 {
		inset: 10px;
		border-color: #8BE9FD;
		border-top-color: transparent;
		animation-direction: reverse;
	}
	
	.ring.r3 {
		inset: 20px;
		border-color: #50FA7B;
		border-top-color: transparent;
	}
	
	@keyframes spin {
		to { transform: rotate(360deg); }
	}
	
	.loading-state p {
		color: rgba(255, 255, 255, 0.5);
		font-size: 0.8rem;
		letter-spacing: 0.2em;
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 6px;
		height: 6px;
	}
	
	::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.5);
	}
	
	::-webkit-scrollbar-thumb {
		background: rgba(189, 147, 249, 0.3);
		border-radius: 3px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: rgba(189, 147, 249, 0.5);
	}
</style>