<!-- SourceTables.svelte - Matching Data Center Aesthetic -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let sourceDetails = [];
	let searchTerm = '';
	let sortColumn = 'count';
	let sortDirection = 'desc';
	
	// Animation states
	let animationFrame = null;
	let pulsePhase = 0;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Failed to load source tables:', err);
			loading = false;
		}
		
		// Start animations
		const animate = () => {
			pulsePhase = (pulsePhase + 0.02) % (Math.PI * 2);
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
			.sort((a, b) => {
				if (sortColumn === 'name') {
					return sortDirection === 'asc' ? 
						a[0].localeCompare(b[0]) : 
						b[0].localeCompare(a[0]);
				}
				return sortDirection === 'asc' ? a[1] - b[1] : b[1] - a[1];
			}) : [];
	
	$: totalHosts = sources.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = sources.length > 0 ? Math.max(...sources.map(([,c]) => c)) : 1;
	$: avgHosts = sources.length > 0 ? Math.round(totalHosts / sources.length) : 0;
	
	// Key metrics
	$: sourceCount = sources.length;
	$: topSource = sources[0] || ['N/A', 0];
	$: utilization = topSource[1] > 0 ? ((topSource[1] / totalHosts) * 100).toFixed(1) : 0;
	
	function handleSort(column) {
		if (sortColumn === column) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = column;
			sortDirection = 'desc';
		}
	}
	
	async function selectSource(source, count) {
		selectedSource = { source, count };
		loading = true;
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			sourceDetails = result.hosts || [];
		} catch (err) {
			console.error('Failed to load source details:', err);
			sourceDetails = [];
		}
		loading = false;
	}
	
	function closeDetails() {
		selectedSource = null;
		sourceDetails = [];
	}
	
	function getSourceStatus(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#BD93F9', icon: '🔴' };
		if (percentage >= 50) return { level: 'HIGH', color: '#8BE9FD', icon: '🟢' };
		if (percentage >= 25) return { level: 'MODERATE', color: '#50FA7B', icon: '🟡' };
		return { level: 'LOW', color: '#FFB86C', icon: '⚪' };
	}
</script>

<div class="source-interface">
	<!-- Top Metrics -->
	<div class="metrics-ribbon">
		<div class="metric-box">
			<div class="metric-label">SOURCE TABLES</div>
			<div class="metric-value" style="color: #BD93F9">{sourceCount}</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">TOTAL HOSTS</div>
			<div class="metric-value" style="color: #8BE9FD">{totalHosts.toLocaleString()}</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">TOP SOURCE</div>
			<div class="metric-value" style="color: #50FA7B; font-size: 1.2rem">
				{topSource[0].substring(0, 20).toUpperCase()}
			</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">AVG HOSTS/TABLE</div>
			<div class="metric-value" style="color: #FFB86C">{avgHosts.toLocaleString()}</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">TOP UTILIZATION</div>
			<div class="metric-value" style="color: #FF79C6">{utilization}%</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content-layout">
		<!-- Left: Source Visualization -->
		<div class="network-panel">
			<div class="panel-header">
				<h2>SOURCE TABLE TOPOLOGY</h2>
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="Search sources..."
					   class="search-input"/>
			</div>
			
			{#if loading && !selectedSource}
				<div class="loading-state">
					<div class="source-loader">
						<div class="data-block block-1"></div>
						<div class="data-block block-2"></div>
						<div class="data-block block-3"></div>
					</div>
					<p>SCANNING SOURCE TABLES...</p>
				</div>
			{:else if selectedSource}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedSource.source.toUpperCase()}</h3>
							<div class="source-stats">
								<span>{selectedSource.count.toLocaleString()} HOSTS</span>
								<span>•</span>
								<span>{((selectedSource.count/totalHosts)*100).toFixed(2)}% OF TOTAL</span>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="hosts-list">
						<table class="hosts-table">
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>TYPE</th>
									<th>DIVISION</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each sourceDetails as host}
									<tr>
										<td class="hostname">{host.host}</td>
										<td>{host.region || 'UNKNOWN'}</td>
										<td>{host.country || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>{host.business_unit || 'UNKNOWN'}</td>
										<td>
											<span class="status-ind {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												●
											</span>
										</td>
										<td>
											<span class="status-ind {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												●
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="network-visualization">
					<!-- Source Grid -->
					<div class="source-grid">
						{#each sources.slice(0, 12) as [source, count], i}
							{@const status = getSourceStatus(count)}
							{@const percentage = (count / maxHosts) * 100}
							<div class="source-node" on:click={() => selectSource(source, count)}>
								<div class="source-icon">
									<div class="data-stack">
										<div class="data-light" style="background: {status.color}; 
																	   opacity: {0.3 + Math.sin(pulsePhase + i) * 0.3}"></div>
										<div class="data-light" style="background: {status.color}; 
																	   opacity: {0.3 + Math.sin(pulsePhase + i + 1) * 0.3}"></div>
										<div class="data-light" style="background: {status.color}; 
																	   opacity: {0.3 + Math.sin(pulsePhase + i + 2) * 0.3}"></div>
									</div>
								</div>
								<div class="source-name">{source.substring(0, 15).toUpperCase()}</div>
								<div class="source-hosts">{count.toLocaleString()} HOSTS</div>
								<div class="source-capacity">
									<div class="capacity-bar">
										<div class="capacity-fill" style="width: {percentage}%; background: {status.color}"></div>
									</div>
									<span class="capacity-text">{percentage.toFixed(0)}%</span>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Middle: Charts -->
		<div class="charts-section">
			<!-- Distribution Chart -->
			<div class="chart-panel">
				<h3>TABLE SIZE DISTRIBUTION</h3>
				<div class="distribution-chart">
					{#each sources.slice(0, 8) as [source, count], i}
						{@const percentage = (count / maxHosts) * 100}
						{@const status = getSourceStatus(count)}
						<div class="dist-item">
							<div class="dist-label">{source.substring(0, 10).toUpperCase()}</div>
							<div class="dist-gauge">
								<svg viewBox="0 0 100 100">
									<circle cx="50" cy="50" r="35" fill="none" 
											stroke="rgba(255,255,255,0.1)" stroke-width="8"/>
									<circle cx="50" cy="50" r="35" fill="none"
											stroke="{status.color}" stroke-width="8"
											stroke-dasharray="{percentage * 2.2} 220"
											stroke-linecap="round"
											transform="rotate(-90 50 50)"/>
									<text x="50" y="50" text-anchor="middle" dy="5"
										  fill="{status.color}" font-size="16" font-weight="600">
										{percentage.toFixed(0)}%
									</text>
								</svg>
							</div>
							<div class="dist-hosts">{count}</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Load Distribution -->
			<div class="chart-panel">
				<h3>HOST DISTRIBUTION</h3>
				<div class="load-bars">
					{#each sources.slice(0, 10) as [source, count], i}
						{@const percentage = (count / maxHosts) * 100}
						{@const status = getSourceStatus(count)}
						<div class="load-bar-item" on:click={() => selectSource(source, count)}>
							<div class="load-label">{source.substring(0, 8).toUpperCase()}</div>
							<div class="load-track">
								<div class="load-fill" 
									 style="width: {percentage}%; 
											background: linear-gradient(90deg, {status.color}40, {status.color})">
									<span class="load-value">{count}</span>
								</div>
							</div>
							<div class="load-icon">{status.icon}</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
		
		<!-- Right: Source List -->
		<div class="list-panel">
			<div class="panel-header">
				<h3>ALL SOURCES</h3>
				<span class="source-count">{sources.length} ACTIVE</span>
			</div>
			<div class="source-list">
				<table class="sources-table">
					<thead>
						<tr>
							<th>#</th>
							<th class="sortable" on:click={() => handleSort('name')}>
								SOURCE
								{#if sortColumn === 'name'}
									<span class="sort-icon">{sortDirection === 'asc' ? '↑' : '↓'}</span>
								{/if}
							</th>
							<th class="sortable" on:click={() => handleSort('count')}>
								HOSTS
								{#if sortColumn === 'count'}
									<span class="sort-icon">{sortDirection === 'asc' ? '↑' : '↓'}</span>
								{/if}
							</th>
							<th>LOAD</th>
							<th>STATUS</th>
						</tr>
					</thead>
					<tbody>
						{#each sources as [source, count], i}
							{@const status = getSourceStatus(count)}
							{@const percentage = (count / maxHosts) * 100}
							<tr on:click={() => selectSource(source, count)}>
								<td class="rank">{i + 1}</td>
								<td class="table-name">
									<span class="status-dot" style="color: {status.color}">●</span>
									{source.substring(0, 20).toUpperCase()}
								</td>
								<td class="host-count" style="color: {status.color}">
									{count.toLocaleString()}
								</td>
								<td>
									<div class="mini-bar">
										<div class="mini-fill" style="width: {percentage}%; background: {status.color}"></div>
									</div>
								</td>
								<td>
									<span class="status-label" style="color: {status.color}">
										{status.level}
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
		display: flex;
		flex-direction: column;
		padding: 1rem;
		gap: 1rem;
		overflow: hidden;
	}
	
	/* Metrics Ribbon */
	.metrics-ribbon {
		display: flex;
		gap: 1rem;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
	}
	
	.metric-box {
		flex: 1;
		text-align: center;
		padding: 0 1rem;
		border-right: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.metric-box:last-child {
		border-right: none;
	}
	
	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		font-weight: 600;
		margin-bottom: 0.5rem;
	}
	
	.metric-value {
		font-size: 1.8rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
	}
	
	/* Content Layout */
	.content-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 380px 300px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Network Panel */
	.network-panel {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 12px;
		padding: 1rem;
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
	
	.panel-header h2, .panel-header h3 {
		margin: 0;
		font-size: 0.9rem;
		font-weight: 300;
		letter-spacing: 0.1em;
		color: #BD93F9;
	}
	
	.search-input {
		padding: 0.4rem 0.8rem;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(139, 233, 253, 0.3);
		border-radius: 6px;
		color: #FFFFFF;
		font-size: 0.75rem;
		width: 180px;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #8BE9FD;
	}
	
	.network-visualization {
		flex: 1;
		position: relative;
	}
	
	.source-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		grid-template-rows: repeat(3, 1fr);
		gap: 1rem;
		height: 100%;
		position: relative;
		z-index: 2;
	}
	
	.source-node {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(139, 233, 253, 0.2);
		border-radius: 8px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}
	
	.source-node:hover {
		background: rgba(139, 233, 253, 0.05);
		border-color: #8BE9FD;
		transform: scale(1.05);
		z-index: 10;
	}
	
	.source-icon {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.data-stack {
		display: flex;
		flex-direction: column;
		gap: 3px;
		width: 30px;
		background: rgba(255, 255, 255, 0.1);
		padding: 5px;
		border-radius: 4px;
	}
	
	.data-light {
		width: 100%;
		height: 4px;
		border-radius: 1px;
	}
	
	.source-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.9);
		text-align: center;
		font-weight: 600;
	}
	
	.source-hosts {
		font-size: 0.8rem;
		color: #8BE9FD;
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.source-capacity {
		width: 100%;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.capacity-bar {
		flex: 1;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.capacity-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.capacity-text {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		min-width: 30px;
	}
	
	/* Charts Section */
	.charts-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chart-panel {
		flex: 1;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
	}
	
	.chart-panel h3 {
		margin: 0 0 1rem 0;
		font-size: 0.75rem;
		color: #8BE9FD;
		font-weight: 300;
		letter-spacing: 0.1em;
	}
	
	.distribution-chart {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		grid-template-rows: repeat(2, 1fr);
		gap: 0.5rem;
		flex: 1;
	}
	
	.dist-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}
	
	.dist-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		text-align: center;
	}
	
	.dist-gauge {
		width: 60px;
		height: 60px;
	}
	
	.dist-gauge svg {
		width: 100%;
		height: 100%;
	}
	
	.dist-hosts {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.7);
		font-family: 'Courier New', monospace;
	}
	
	.load-bars {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	
	.load-bar-item {
		display: grid;
		grid-template-columns: 60px 1fr 20px;
		gap: 0.5rem;
		align-items: center;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	.load-bar-item:hover {
		transform: translateX(2px);
	}
	
	.load-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.7);
		text-align: right;
	}
	
	.load-track {
		height: 16px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.load-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.4rem;
		transition: width 0.5s ease;
	}
	
	.load-value {
		font-size: 0.6rem;
		color: #FFFFFF;
		font-weight: 600;
	}
	
	.load-icon {
		font-size: 0.8rem;
		text-align: center;
	}
	
	/* List Panel */
	.list-panel {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.source-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.source-list {
		flex: 1;
		overflow-y: auto;
	}
	
	.sources-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.sources-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.9);
		z-index: 10;
	}
	
	.sources-table th {
		padding: 0.5rem;
		text-align: left;
		font-size: 0.6rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.sources-table th.sortable {
		cursor: pointer;
		transition: color 0.2s;
	}
	
	.sources-table th.sortable:hover {
		color: #8BE9FD;
	}
	
	.sort-icon {
		color: #8BE9FD;
		margin-left: 0.25rem;
	}
	
	.sources-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.sources-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.05);
	}
	
	.sources-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank {
		color: #BD93F9;
		font-weight: 600;
		font-size: 0.65rem;
	}
	
	.table-name {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.65rem;
	}
	
	.status-dot {
		font-size: 0.8rem;
	}
	
	.host-count {
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.mini-bar {
		width: 50px;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.mini-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.status-label {
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.03em;
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
		align-items: start;
		margin-bottom: 1rem;
	}
	
	.detail-header h3 {
		margin: 0 0 0.25rem 0;
		font-size: 1.1rem;
		color: #BD93F9;
	}
	
	.source-stats {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		display: flex;
		gap: 0.5rem;
	}
	
	.close-btn {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		color: #FFFFFF;
		width: 28px;
		height: 28px;
		border-radius: 6px;
		font-size: 1rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}
	
	.close-btn:hover {
		background: rgba(189, 147, 249, 0.2);
		border-color: #BD93F9;
	}
	
	.hosts-list {
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
	
	.hosts-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.9);
		z-index: 10;
	}
	
	.hosts-table th {
		padding: 0.5rem;
		text-align: left;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		letter-spacing: 0.05em;
	}
	
	.hosts-table td {
		padding: 0.5rem;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.hostname {
		font-family: 'Courier New', monospace;
		color: #8BE9FD;
		font-size: 0.6rem;
	}
	
	.status-ind {
		font-size: 0.8rem;
	}
	
	.status-ind.active {
		color: #50FA7B;
	}
	
	.status-ind.inactive {
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
	
	.source-loader {
		display: flex;
		gap: 1rem;
		align-items: flex-end;
	}
	
	.data-block {
		width: 30px;
		background: linear-gradient(180deg, #BD93F9, #8BE9FD);
		border-radius: 4px;
		animation: blockPulse 1.5s ease-in-out infinite;
	}
	
	.block-1 {
		height: 60px;
		animation-delay: 0s;
	}
	
	.block-2 {
		height: 80px;
		animation-delay: 0.3s;
	}
	
	.block-3 {
		height: 50px;
		animation-delay: 0.6s;
	}
	
	@keyframes blockPulse {
		0%, 100% { opacity: 0.3; transform: scaleY(0.9); }
		50% { opacity: 1; transform: scaleY(1); }
	}
	
	.loading-state p {
		color: rgba(255, 255, 255, 0.5);
		font-size: 0.8rem;
		letter-spacing: 0.2em;
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 6px;
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