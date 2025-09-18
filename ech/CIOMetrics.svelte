<!-- SourceTables.svelte - Production-Ready Source Table Analytics -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	// State management
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let sortBy = 'count';
	let sortOrder = 'desc';
	
	// Animation frame for performance
	let animationFrame = null;
	
	// Lifecycle
	onMount(async () => {
		await fetchData();
		startAnimations();
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});
	
	// Data fetching
	async function fetchData() {
		try {
			loading = true;
			const response = await fetch('http://localhost:5000/api/source_tables');
			data = await response.json();
		} catch (err) {
			console.error('Failed to fetch source tables:', err);
			data = { source_intelligence: {}, total_mentions: 0 };
		} finally {
			loading = false;
		}
	}
	
	async function fetchHostDetails(source) {
		try {
			const response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			const result = await response.json();
			return result.hosts || [];
		} catch (err) {
			console.error('Failed to fetch host details:', err);
			return [];
		}
	}
	
	// Animations
	function startAnimations() {
		let time = 0;
		const animate = () => {
			time += 0.016;
			// Update any time-based animations here
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	}
	
	// Computed values
	$: sources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => {
				if (sortBy === 'name') {
					return sortOrder === 'asc' ? a[0].localeCompare(b[0]) : b[0].localeCompare(a[0]);
				}
				return sortOrder === 'asc' ? a[1] - b[1] : b[1] - a[1];
			}) : [];
	
	$: totalHosts = sources.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = Math.max(...sources.map(([_, c]) => c), 1);
	$: avgHosts = sources.length > 0 ? Math.round(totalHosts / sources.length) : 0;
	$: topSources = sources.slice(0, 10);
	
	// Event handlers
	async function selectSource(source, count) {
		selectedSource = { source, count };
		loading = true;
		hostDetails = await fetchHostDetails(source);
		loading = false;
	}
	
	function closeDetails() {
		selectedSource = null;
		hostDetails = [];
	}
	
	function toggleSort(field) {
		if (sortBy === field) {
			sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
		} else {
			sortBy = field;
			sortOrder = 'desc';
		}
	}
	
	// Utility functions
	function getHealthStatus(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'Critical', color: '#BD93F9', bg: 'rgba(189, 147, 249, 0.1)' };
		if (percentage >= 50) return { level: 'High', color: '#8BE9FD', bg: 'rgba(139, 233, 253, 0.1)' };
		if (percentage >= 25) return { level: 'Medium', color: '#50FA7B', bg: 'rgba(80, 250, 123, 0.1)' };
		return { level: 'Low', color: '#FFB86C', bg: 'rgba(255, 184, 108, 0.1)' };
	}
	
	function formatNumber(num) {
		return num.toLocaleString();
	}
	
	function getPercentage(value, total) {
		return ((value / total) * 100).toFixed(1);
	}
</script>

<div class="dashboard">
	<!-- Header Metrics -->
	<div class="metrics-grid">
		<div class="metric-card">
			<div class="metric-header">
				<span class="metric-label">Total Tables</span>
				<span class="metric-icon">📊</span>
			</div>
			<div class="metric-value">{sources.length}</div>
			<div class="metric-change">
				<span class="change-value">Active Sources</span>
			</div>
		</div>
		
		<div class="metric-card">
			<div class="metric-header">
				<span class="metric-label">Total Hosts</span>
				<span class="metric-icon">💻</span>
			</div>
			<div class="metric-value">{formatNumber(totalHosts)}</div>
			<div class="metric-change">
				<span class="change-value">Managed Assets</span>
			</div>
		</div>
		
		<div class="metric-card">
			<div class="metric-header">
				<span class="metric-label">Average Hosts</span>
				<span class="metric-icon">📈</span>
			</div>
			<div class="metric-value">{formatNumber(avgHosts)}</div>
			<div class="metric-change">
				<span class="change-value">Per Table</span>
			</div>
		</div>
		
		<div class="metric-card">
			<div class="metric-header">
				<span class="metric-label">Max Table Size</span>
				<span class="metric-icon">⚡</span>
			</div>
			<div class="metric-value">{formatNumber(maxHosts)}</div>
			<div class="metric-change">
				<span class="change-value">Largest Source</span>
			</div>
		</div>
	</div>
	
	<!-- Main Content Area -->
	<div class="content-area">
		<!-- Left Panel: Visualization -->
		<div class="visualization-panel">
			<div class="panel-header">
				<h2>Table Distribution Analysis</h2>
				<div class="view-controls">
					<input 
						type="text"
						bind:value={searchTerm}
						placeholder="Search tables..."
						class="search-input"
					/>
				</div>
			</div>
			
			<div class="panel-content">
				{#if loading && !selectedSource}
					<div class="loading-container">
						<div class="spinner"></div>
						<p>Loading source tables...</p>
					</div>
				{:else if selectedSource}
					<!-- Detail View -->
					<div class="detail-view">
						<div class="detail-header">
							<div class="detail-title">
								<h3>{selectedSource.source}</h3>
								<div class="detail-stats">
									<span class="stat-badge">{formatNumber(selectedSource.count)} hosts</span>
									<span class="stat-badge">{getPercentage(selectedSource.count, totalHosts)}% of total</span>
								</div>
							</div>
							<button class="btn-close" on:click={closeDetails}>
								<svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
									<line x1="5" y1="5" x2="15" y2="15"/>
									<line x1="15" y1="5" x2="5" y2="15"/>
								</svg>
							</button>
						</div>
						
						<div class="hosts-table-container">
							<table class="hosts-table">
								<thead>
									<tr>
										<th>Hostname</th>
										<th>Region</th>
										<th>Country</th>
										<th>Infrastructure</th>
										<th>Division</th>
										<th>CMDB</th>
										<th>Tanium</th>
									</tr>
								</thead>
								<tbody>
									{#each hostDetails as host}
										<tr>
											<td class="font-mono">{host.host}</td>
											<td>{host.region || '-'}</td>
											<td>{host.country || '-'}</td>
											<td>{host.infrastructure_type || '-'}</td>
											<td>{host.business_unit || '-'}</td>
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
					<!-- Chart View -->
					<div class="charts-container">
						<div class="chart-section">
							<h3 class="chart-title">Top 10 Source Tables</h3>
							<div class="bar-chart">
								{#each topSources as [source, count], i}
									{@const status = getHealthStatus(count)}
									{@const percentage = (count / maxHosts) * 100}
									<div class="bar-item" on:click={() => selectSource(source, count)}>
										<div class="bar-label">
											<span class="bar-rank">#{i + 1}</span>
											<span class="bar-name">{source}</span>
										</div>
										<div class="bar-container">
											<div class="bar-fill" 
												 style="width: {percentage}%; background: linear-gradient(90deg, {status.color}40, {status.color})">
												<span class="bar-value">{formatNumber(count)}</span>
											</div>
										</div>
										<span class="bar-percent">{percentage.toFixed(0)}%</span>
									</div>
								{/each}
							</div>
						</div>
						
						<div class="chart-section">
							<h3 class="chart-title">Distribution Heatmap</h3>
							<div class="heatmap">
								{#each sources.slice(0, 50) as [source, count]}
									{@const intensity = count / maxHosts}
									{@const status = getHealthStatus(count)}
									<div class="heat-cell"
										 style="background: {status.color}; opacity: {0.2 + intensity * 0.6}"
										 title="{source}: {formatNumber(count)} hosts"
										 on:click={() => selectSource(source, count)}>
									</div>
								{/each}
							</div>
						</div>
					</div>
				{/if}
			</div>
		</div>
		
		<!-- Right Panel: Table List -->
		<div class="table-panel">
			<div class="panel-header">
				<h3>All Source Tables</h3>
				<span class="table-count">{sources.length} tables</span>
			</div>
			
			<div class="data-table-container">
				<table class="data-table">
					<thead>
						<tr>
							<th class="sortable" on:click={() => toggleSort('name')}>
								Table Name
								{#if sortBy === 'name'}
									<span class="sort-icon">{sortOrder === 'asc' ? '↑' : '↓'}</span>
								{/if}
							</th>
							<th class="sortable" on:click={() => toggleSort('count')}>
								Host Count
								{#if sortBy === 'count'}
									<span class="sort-icon">{sortOrder === 'asc' ? '↑' : '↓'}</span>
								{/if}
							</th>
							<th>Coverage</th>
							<th>Status</th>
						</tr>
					</thead>
					<tbody>
						{#each sources as [source, count]}
							{@const status = getHealthStatus(count)}
							{@const percentage = getPercentage(count, totalHosts)}
							<tr on:click={() => selectSource(source, count)}>
								<td>
									<div class="table-name">
										<span class="status-dot" style="background: {status.color}"></span>
										{source}
									</div>
								</td>
								<td class="font-mono">{formatNumber(count)}</td>
								<td>
									<div class="coverage-bar">
										<div class="coverage-fill" 
											 style="width: {percentage}%; background: {status.color}"></div>
									</div>
									<span class="coverage-text">{percentage}%</span>
								</td>
								<td>
									<span class="status-badge" style="background: {status.bg}; color: {status.color}">
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
	.dashboard {
		width: 100%;
		height: calc(100vh - 80px);
		background: #0A0A0A;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}
	
	/* Metrics Grid */
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1.5rem;
	}
	
	.metric-card {
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%);
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 16px;
		padding: 1.5rem;
		position: relative;
		overflow: hidden;
		transition: all 0.3s ease;
	}
	
	.metric-card:hover {
		transform: translateY(-2px);
		border-color: rgba(139, 233, 253, 0.3);
		box-shadow: 0 8px 32px rgba(139, 233, 253, 0.1);
	}
	
	.metric-card::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 2px;
		background: linear-gradient(90deg, #BD93F9, #8BE9FD);
		opacity: 0;
		transition: opacity 0.3s ease;
	}
	
	.metric-card:hover::before {
		opacity: 1;
	}
	
	.metric-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}
	
	.metric-label {
		font-size: 0.875rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 500;
	}
	
	.metric-icon {
		font-size: 1.5rem;
		opacity: 0.8;
	}
	
	.metric-value {
		font-size: 2rem;
		font-weight: 700;
		color: #FFFFFF;
		margin-bottom: 0.5rem;
		font-variant-numeric: tabular-nums;
	}
	
	.metric-change {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.change-value {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.4);
	}
	
	/* Content Area */
	.content-area {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 480px;
		gap: 1.5rem;
		min-height: 0;
	}
	
	/* Panels */
	.visualization-panel,
	.table-panel {
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.02) 0%, rgba(255, 255, 255, 0.01) 100%);
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 16px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.panel-header {
		padding: 1.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.08);
		display: flex;
		justify-content: space-between;
		align-items: center;
		background: rgba(0, 0, 0, 0.3);
	}
	
	.panel-header h2,
	.panel-header h3 {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
		color: #FFFFFF;
	}
	
	.table-count {
		font-size: 0.875rem;
		color: rgba(255, 255, 255, 0.4);
	}
	
	.panel-content {
		flex: 1;
		padding: 1.5rem;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}
	
	/* Search Input */
	.search-input {
		padding: 0.625rem 1rem;
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		color: #FFFFFF;
		font-size: 0.875rem;
		width: 240px;
		transition: all 0.3s ease;
	}
	
	.search-input::placeholder {
		color: rgba(255, 255, 255, 0.3);
	}
	
	.search-input:focus {
		outline: none;
		background: rgba(255, 255, 255, 0.08);
		border-color: #8BE9FD;
		box-shadow: 0 0 0 3px rgba(139, 233, 253, 0.1);
	}
	
	/* Loading State */
	.loading-container {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}
	
	.spinner {
		width: 48px;
		height: 48px;
		border: 3px solid rgba(139, 233, 253, 0.1);
		border-top-color: #8BE9FD;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}
	
	@keyframes spin {
		to { transform: rotate(360deg); }
	}
	
	.loading-container p {
		color: rgba(255, 255, 255, 0.4);
		font-size: 0.875rem;
	}
	
	/* Charts */
	.charts-container {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}
	
	.chart-section {
		flex: 1;
		display: flex;
		flex-direction: column;
	}
	
	.chart-title {
		font-size: 0.875rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.8);
		margin: 0 0 1rem 0;
	}
	
	/* Bar Chart */
	.bar-chart {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.bar-item {
		display: grid;
		grid-template-columns: 200px 1fr 60px;
		gap: 1rem;
		align-items: center;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 8px;
		transition: all 0.3s ease;
	}
	
	.bar-item:hover {
		background: rgba(139, 233, 253, 0.05);
	}
	
	.bar-label {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		font-size: 0.813rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.bar-rank {
		color: #BD93F9;
		font-weight: 600;
	}
	
	.bar-name {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.bar-container {
		height: 24px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 12px;
		overflow: hidden;
		position: relative;
	}
	
	.bar-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.75rem;
		border-radius: 12px;
		transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
	}
	
	.bar-value {
		font-size: 0.75rem;
		font-weight: 600;
		color: #FFFFFF;
	}
	
	.bar-percent {
		font-size: 0.813rem;
		color: rgba(255, 255, 255, 0.5);
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
	
	/* Heatmap */
	.heatmap {
		display: grid;
		grid-template-columns: repeat(10, 1fr);
		grid-template-rows: repeat(5, 1fr);
		gap: 4px;
		height: 200px;
		padding: 1rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 12px;
	}
	
	.heat-cell {
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.heat-cell:hover {
		transform: scale(1.2);
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
		z-index: 10;
	}
	
	/* Data Table */
	.data-table-container {
		flex: 1;
		overflow-y: auto;
		padding: 0 1.5rem 1.5rem;
	}
	
	.data-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.data-table thead {
		position: sticky;
		top: 0;
		background: #0A0A0A;
		z-index: 10;
	}
	
	.data-table th {
		padding: 0.75rem;
		text-align: left;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: rgba(255, 255, 255, 0.5);
		border-bottom: 2px solid rgba(255, 255, 255, 0.08);
	}
	
	.data-table th.sortable {
		cursor: pointer;
		user-select: none;
		transition: color 0.3s ease;
	}
	
	.data-table th.sortable:hover {
		color: rgba(255, 255, 255, 0.8);
	}
	
	.sort-icon {
		margin-left: 0.25rem;
		color: #8BE9FD;
	}
	
	.data-table tbody tr {
		cursor: pointer;
		border-bottom: 1px solid rgba(255, 255, 255, 0.04);
		transition: all 0.3s ease;
	}
	
	.data-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.03);
	}
	
	.data-table td {
		padding: 1rem 0.75rem;
		font-size: 0.875rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.table-name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.status-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.coverage-bar {
		display: inline-block;
		width: 60px;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
		margin-right: 0.5rem;
		vertical-align: middle;
	}
	
	.coverage-fill {
		height: 100%;
		transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
	}
	
	.coverage-text {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.5);
		font-variant-numeric: tabular-nums;
	}
	
	.status-badge {
		display: inline-block;
		padding: 0.25rem 0.625rem;
		border-radius: 6px;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.025em;
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
		padding-bottom: 1.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.08);
	}
	
	.detail-title h3 {
		margin: 0 0 0.5rem 0;
		font-size: 1.5rem;
		font-weight: 600;
		color: #FFFFFF;
	}
	
	.detail-stats {
		display: flex;
		gap: 0.75rem;
	}
	
	.stat-badge {
		padding: 0.375rem 0.75rem;
		background: rgba(139, 233, 253, 0.1);
		border: 1px solid rgba(139, 233, 253, 0.2);
		border-radius: 6px;
		font-size: 0.813rem;
		color: #8BE9FD;
		font-weight: 500;
	}
	
	.btn-close {
		width: 36px;
		height: 36px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		color: rgba(255, 255, 255, 0.6);
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.btn-close:hover {
		background: rgba(255, 255, 255, 0.1);
		color: #FFFFFF;
		transform: rotate(90deg);
	}
	
	/* Hosts Table */
	.hosts-table-container {
		flex: 1;
		overflow-y: auto;
		margin-top: 1.5rem;
	}
	
	.hosts-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.hosts-table thead {
		position: sticky;
		top: 0;
		background: linear-gradient(to bottom, #0A0A0A 0%, #0A0A0A 95%, transparent 100%);
		z-index: 10;
	}
	
	.hosts-table th {
		padding: 0.75rem;
		text-align: left;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: rgba(255, 255, 255, 0.5);
		border-bottom: 2px solid rgba(255, 255, 255, 0.08);
	}
	
	.hosts-table tbody tr {
		border-bottom: 1px solid rgba(255, 255, 255, 0.04);
	}
	
	.hosts-table td {
		padding: 0.875rem 0.75rem;
		font-size: 0.813rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.font-mono {
		font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
		font-size: 0.813rem;
		color: #8BE9FD;
	}
	
	.status-indicator {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 600;
	}
	
	.status-indicator.active {
		background: rgba(80, 250, 123, 0.1);
		color: #50FA7B;
	}
	
	.status-indicator.inactive {
		background: rgba(255, 85, 85, 0.1);
		color: #FF5555;
	}
	
	/* Responsive */
	@media (max-width: 1400px) {
		.metrics-grid {
			grid-template-columns: repeat(2, 1fr);
		}
		
		.content-area {
			grid-template-columns: 1fr;
		}
		
		.table-panel {
			display: none;
		}
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}
	
	::-webkit-scrollbar-track {
		background: rgba(255, 255, 255, 0.02);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.1);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: rgba(255, 255, 255, 0.15);
	}
</style>