<!-- SourceTables.svelte - Clean and Readable -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let sourceDetails = [];
	let searchTerm = '';
	
	// Simple animation states
	let animationFrame = null;
	let activityData = [];
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Failed to load source tables:', err);
			loading = false;
		}
		
		// Initialize activity data
		for (let i = 0; i < 50; i++) {
			activityData.push(50 + Math.random() * 30);
		}
		
		// Start simple animation
		const animate = () => {
			activityData = activityData.map((val, i) => 
				50 + Math.sin(Date.now() * 0.001 + i * 0.2) * 20 + Math.random() * 10
			);
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});

	$: sources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = sources.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = sources.length > 0 ? Math.max(...sources.map(([,c]) => c)) : 1;
	$: avgHostsPerSource = sources.length > 0 ? Math.round(totalHosts / sources.length) : 0;
	
	// Key metrics
	$: sourceCount = sources.length;
	$: topSource = sources[0] || ['N/A', 0];
	$: concentration = topSource[1] > 0 ? ((topSource[1] / totalHosts) * 100).toFixed(1) : 0;
	
	// Top performers
	$: topFive = sources.slice(0, 5);

	async function drillDownSource(source, count) {
		selectedSource = { source, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			sourceDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Source drill-down error:', err);
			sourceDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedSource = null;
		sourceDetails = [];
	}
	
	function getSourceStatus(count) {
		let percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'HIGH', color: '#00E5FF', bgColor: 'rgba(0, 229, 255, 0.1)' };
		if (percentage >= 50) return { level: 'MEDIUM', color: '#50FA7B', bgColor: 'rgba(80, 250, 123, 0.1)' };
		if (percentage >= 25) return { level: 'LOW', color: '#FFB86C', bgColor: 'rgba(255, 184, 108, 0.1)' };
		return { level: 'MINIMAL', color: '#FF79C6', bgColor: 'rgba(255, 121, 198, 0.1)' };
	}
	
	function getSourceSize(count) {
		if (count > 10000) return 'LARGE';
		if (count > 5000) return 'MEDIUM';
		if (count > 1000) return 'SMALL';
		return 'MINIMAL';
	}

	function formatNumber(num) {
		return new Intl.NumberFormat('en-US').format(num);
	}

	function truncateText(text, maxLength = 25) {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}
</script>

<div class="source-interface">
	<!-- Clean Header with Key Metrics -->
	<div class="metrics-header">
		<div class="metric-card">
			<div class="metric-icon">📊</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #00E5FF">{sourceCount}</div>
				<div class="metric-label">DATA SOURCES</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">💻</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #50FA7B">{formatNumber(totalHosts)}</div>
				<div class="metric-label">TOTAL HOSTS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">🔝</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FFB86C; font-size: 1rem" title={topSource[0]}>
					{truncateText(topSource[0], 20).toUpperCase()}
				</div>
				<div class="metric-label">LARGEST SOURCE</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📈</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FF79C6">{concentration}%</div>
				<div class="metric-label">CONCENTRATION</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">⚖️</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #BD93F9">{formatNumber(avgHostsPerSource)}</div>
				<div class="metric-label">AVG PER SOURCE</div>
			</div>
		</div>
	</div>
	
	<!-- Main Content Grid -->
	<div class="content-layout">
		<!-- Left: Source Visualization -->
		<div class="source-panel">
			<div class="panel-header">
				<h2>Source Distribution</h2>
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="Search sources..."
					   class="search-input"/>
			</div>
			
			{#if loading && !selectedSource}
				<div class="loading-state">
					<div class="loader-animation">
						<div class="load-bar"></div>
						<div class="load-bar"></div>
						<div class="load-bar"></div>
					</div>
					<p>Loading source data...</p>
				</div>
			{:else if selectedSource}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedSource.source.toUpperCase()}</h3>
							<div class="source-stats">
								<span>{formatNumber(selectedSource.count)} hosts</span>
								<span>•</span>
								<span>{((selectedSource.count / totalHosts) * 100).toFixed(2)}% of total</span>
								<span>•</span>
								<span>{getSourceSize(selectedSource.count)} source</span>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="hosts-container">
						<table class="hosts-table">
							<thead>
								<tr>
									<th>Hostname</th>
									<th>Region</th>
									<th>Country</th>
									<th>Data Center</th>
									<th>Type</th>
									<th>CMDB</th>
									<th>Security</th>
								</tr>
							</thead>
							<tbody>
								{#each sourceDetails as host}
									<tr>
										<td class="hostname" title={host.host}>{truncateText(host.host, 30)}</td>
										<td>{host.region || 'Unknown'}</td>
										<td>{host.country || 'Unknown'}</td>
										<td>{host.data_center || 'Unknown'}</td>
										<td>{host.infrastructure_type || 'Unknown'}</td>
										<td>
											<span class="status-indicator {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '✓' : '✗'}
											</span>
										</td>
										<td>
											<span class="status-indicator {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? '✓' : '✗'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="source-visualization">
					<!-- Clean Tree Structure -->
					<div class="tree-container">
						<div class="tree-root">
							<div class="root-node">
								<div class="node-label">All Sources</div>
								<div class="node-count">{formatNumber(totalHosts)} hosts</div>
							</div>
						</div>
						<div class="tree-branches">
							{#each topFive as [source, count], i}
								{@const status = getSourceStatus(count)}
								<div class="source-node" 
									 style="border-color: {status.color}; background: {status.bgColor}"
									 on:click={() => drillDownSource(source, count)}>
									<div class="node-rank">#{i + 1}</div>
									<div class="node-name" title={source}>{truncateText(source, 18)}</div>
									<div class="node-count" style="color: {status.color}">{formatNumber(count)}</div>
									<div class="node-percent">{((count / totalHosts) * 100).toFixed(1)}%</div>
									<div class="node-bar">
										<div class="bar-fill" 
											 style="width: {((count / totalHosts) * 100)}%; background: {status.color}">
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
					
					<!-- Activity Chart -->
					<div class="activity-chart">
						<h4>Source Activity</h4>
						<svg viewBox="0 0 200 60">
							<polyline points="{activityData.map((val, i) => `${i * 4},${60 - val * 0.6}`).join(' ')}"
									  fill="none" 
									  stroke="#00E5FF" 
									  stroke-width="2"
									  opacity="0.8"/>
						</svg>
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Right: Source List -->
		<div class="list-panel">
			<div class="panel-header">
				<h3>All Sources</h3>
				<span class="source-count">{sources.length} sources</span>
			</div>
			<div class="source-list">
				<table class="sources-table">
					<thead>
						<tr>
							<th>Rank</th>
							<th>Source Name</th>
							<th>Host Count</th>
							<th>Percentage</th>
							<th>Size</th>
						</tr>
					</thead>
					<tbody>
						{#each sources as [source, count], i}
							{@const status = getSourceStatus(count)}
							<tr on:click={() => drillDownSource(source, count)}>
								<td class="rank">#{i + 1}</td>
								<td class="source-name" title={source}>
									<span class="status-dot" style="background: {status.color}"></span>
									{truncateText(source, 25)}
								</td>
								<td class="host-count" style="color: {status.color}">
									{formatNumber(count)}
								</td>
								<td class="percentage">
									{((count / totalHosts) * 100).toFixed(1)}%
								</td>
								<td>
									<span class="size-badge" style="color: {status.color}; border-color: {status.color}">
										{getSourceSize(count)}
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
		background: transparent;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		overflow: hidden;
	}
	
	/* Clean Metrics Header */
	.metrics-header {
		display: flex;
		gap: 1rem;
		flex-shrink: 0;
	}
	
	.metric-card {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 10px;
		padding: 1.2rem;
		display: flex;
		gap: 1rem;
		align-items: center;
		transition: all 0.2s ease;
		backdrop-filter: blur(10px);
	}
	
	.metric-card:hover {
		background: rgba(0, 0, 0, 0.8);
		border-color: rgba(0, 229, 255, 0.3);
		transform: translateY(-1px);
	}
	
	.metric-icon {
		font-size: 2rem;
		opacity: 0.8;
	}
	
	.metric-content {
		flex: 1;
		min-width: 0;
	}
	
	.metric-value {
		font-size: 1.6rem;
		font-weight: 600;
		font-family: 'SF Mono', 'Monaco', monospace;
		margin-bottom: 0.3rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
		font-weight: 500;
		text-transform: uppercase;
	}
	
	/* Content Layout */
	.content-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 400px;
		gap: 1.5rem;
		min-height: 0;
	}
	
	/* Source Panel */
	.source-panel {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		backdrop-filter: blur(10px);
		overflow: hidden;
	}
	
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		flex-shrink: 0;
	}
	
	.panel-header h2, .panel-header h3 {
		margin: 0;
		font-size: 1.1rem;
		font-weight: 500;
		color: #ffffff;
	}
	
	.search-input {
		padding: 0.6rem 1rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 8px;
		color: #ffffff;
		font-size: 0.9rem;
		width: 220px;
		transition: all 0.3s ease;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #00E5FF;
		background: rgba(0, 0, 0, 0.9);
		box-shadow: 0 0 0 2px rgba(0, 229, 255, 0.2);
	}

	.search-input::placeholder {
		color: rgba(255, 255, 255, 0.4);
	}
	
	/* Source Visualization */
	.source-visualization {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		overflow: hidden;
	}
	
	.tree-container {
		flex: 1;
		overflow: hidden;
	}
	
	.tree-root {
		text-align: center;
		margin-bottom: 2rem;
	}
	
	.root-node {
		display: inline-block;
		background: rgba(0, 229, 255, 0.1);
		border: 2px solid #00E5FF;
		border-radius: 12px;
		padding: 1rem 2rem;
	}
	
	.tree-branches {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
		justify-content: center;
	}
	
	.source-node {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid;
		border-radius: 10px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		min-width: 180px;
		text-align: center;
	}
	
	.source-node:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
	}
	
	.node-label, .node-name {
		font-size: 0.9rem;
		color: #ffffff;
		margin-bottom: 0.5rem;
		font-weight: 500;
	}
	
	.node-count {
		font-size: 1.2rem;
		font-weight: 600;
		font-family: 'SF Mono', 'Monaco', monospace;
		margin-bottom: 0.3rem;
	}
	
	.node-rank {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		margin-bottom: 0.5rem;
	}
	
	.node-percent {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.7);
		margin-bottom: 0.5rem;
	}
	
	.node-bar {
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
		border-radius: 2px;
	}
	
	/* Activity Chart */
	.activity-chart {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 10px;
		padding: 1rem;
		height: 120px;
	}
	
	.activity-chart h4 {
		margin: 0 0 0.5rem 0;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.8);
		font-weight: 500;
	}
	
	.activity-chart svg {
		width: 100%;
		height: 70px;
	}
	
	/* List Panel */
	.list-panel {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		backdrop-filter: blur(10px);
		overflow: hidden;
		padding: 1.5rem;
	}
	
	.source-count {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 500;
	}
	
	.source-list {
		flex: 1;
		overflow-y: auto;
		margin-top: 1rem;
	}
	
	.sources-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.sources-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.95);
		z-index: 10;
	}
	
	.sources-table th {
		padding: 0.8rem 0.5rem;
		text-align: left;
		font-size: 0.8rem;
		font-weight: 500;
		color: rgba(255, 255, 255, 0.7);
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.sources-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.sources-table tbody tr:hover {
		background: rgba(0, 229, 255, 0.05);
	}
	
	.sources-table td {
		padding: 0.7rem 0.5rem;
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.9);
	}
	
	.rank {
		color: #00E5FF;
		font-weight: 600;
		font-size: 0.8rem;
		width: 60px;
	}
	
	.source-name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 500;
	}
	
	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.host-count {
		font-family: 'SF Mono', 'Monaco', monospace;
		font-weight: 600;
	}
	
	.percentage {
		font-family: 'SF Mono', 'Monaco', monospace;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.size-badge {
		font-size: 0.7rem;
		padding: 0.2rem 0.5rem;
		border: 1px solid;
		border-radius: 6px;
		font-weight: 600;
		text-transform: uppercase;
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
		align-items: start;
		margin-bottom: 1.5rem;
		flex-shrink: 0;
	}
	
	.detail-header h3 {
		margin: 0 0 0.5rem 0;
		font-size: 1.3rem;
		color: #00E5FF;
		font-weight: 500;
	}
	
	.source-stats {
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.7);
		display: flex;
		gap: 0.5rem;
		font-weight: 400;
	}
	
	.close-btn {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.3);
		color: #ffffff;
		width: 36px;
		height: 36px;
		border-radius: 8px;
		font-size: 1.2rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}
	
	.close-btn:hover {
		background: rgba(0, 229, 255, 0.2);
		border-color: #00E5FF;
	}
	
	.hosts-container {
		flex: 1;
		overflow-y: auto;
		background: rgba(0, 0, 0, 0.8);
		border-radius: 10px;
		padding: 1rem;
	}
	
	.hosts-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.hosts-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.95);
		z-index: 10;
	}
	
	.hosts-table th {
		padding: 0.8rem 0.5rem;
		text-align: left;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.7);
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
		font-weight: 500;
	}
	
	.hosts-table td {
		padding: 0.7rem 0.5rem;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.9);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.hostname {
		font-family: 'SF Mono', 'Monaco', monospace;
		color: #00E5FF;
		font-size: 0.75rem;
		font-weight: 500;
	}
	
	.status-indicator {
		font-size: 0.9rem;
		font-weight: 600;
		padding: 0.2rem 0.4rem;
		border-radius: 4px;
		text-align: center;
		min-width: 24px;
	}
	
	.status-indicator.active {
		color: #50FA7B;
		background: rgba(80, 250, 123, 0.1);
	}
	
	.status-indicator.inactive {
		color: #FF5555;
		background: rgba(255, 85, 85, 0.1);
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
	
	.loader-animation {
		display: flex;
		gap: 0.5rem;
		align-items: flex-end;
	}
	
	.load-bar {
		width: 8px;
		background: #00E5FF;
		border-radius: 4px;
		animation: loadPulse 1.5s ease-in-out infinite;
	}
	
	.load-bar:nth-child(1) {
		height: 30px;
		animation-delay: 0s;
	}
	
	.load-bar:nth-child(2) {
		height: 40px;
		animation-delay: 0.3s;
	}
	
	.load-bar:nth-child(3) {
		height: 25px;
		animation-delay: 0.6s;
	}
	
	@keyframes loadPulse {
		0%, 100% { opacity: 0.3; transform: scaleY(0.8); }
		50% { opacity: 1; transform: scaleY(1); }
	}
	
	.loading-state p {
		color: rgba(255, 255, 255, 0.6);
		font-size: 1rem;
		font-weight: 400;
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 6px;
		height: 6px;
	}
	
	::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.3);
		border-radius: 3px;
	}
	
	::-webkit-scrollbar-thumb {
		background: rgba(0, 229, 255, 0.3);
		border-radius: 3px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: rgba(0, 229, 255, 0.5);
	}
	
	/* Responsive Design */
	@media (max-width: 1200px) {
		.content-layout {
			grid-template-columns: 1fr;
			grid-template-rows: 1fr auto;
		}
		
		.list-panel {
			max-height: 300px;
		}
	}
	
	@media (max-width: 768px) {
		.metrics-header {
			flex-wrap: wrap;
		}
		
		.metric-card {
			min-width: calc(50% - 0.5rem);
		}
		
		.metric-value {
			font-size: 1.3rem;
		}
		
		.search-input {
			width: 100%;
		}
		
		.panel-header {
			flex-direction: column;
			gap: 1rem;
			align-items: stretch;
		}
	}
</style>