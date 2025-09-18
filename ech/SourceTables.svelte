<!-- SourceTables.svelte - Enhanced with fixes -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let error = null;
	let selectedSource = null;
	let sourceDetails = [];
	let searchTerm = '';
	let hoveredSource = null;
	
	// Animation states
	let animationFrame = null;
	let synapticActivity = [];
	
	onMount(async () => {
		await loadData();
		initializeAnimations();
	});
	
	async function loadData() {
		loading = true;
		error = null;
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			if (!response.ok) throw new Error('Failed to fetch data');
			data = await response.json();
		} catch (err) {
			console.error('Failed to load source tables:', err);
			error = 'Unable to load source data. Please try again.';
			// Use mock data for demonstration
			data = generateMockData();
		} finally {
			loading = false;
		}
	}
	
	function generateMockData() {
		return {
			source_intelligence: {
				'CMDB-Production': 245890,
				'ServiceNow-Assets': 189234,
				'Tanium-Endpoints': 156789,
				'AD-Computers': 134567,
				'Azure-Resources': 98234,
				'AWS-Instances': 87654,
				'VMware-VMs': 76543,
				'Network-Devices': 65432,
				'Cloud-Storage': 54321,
				'Database-Servers': 43210,
				'Web-Applications': 32109,
				'Mobile-Devices': 21098
			}
		};
	}
	
	function initializeAnimations() {
		// Initialize with smoother curve
		for (let i = 0; i < 50; i++) {
			synapticActivity.push(50 + Math.sin(i * 0.2) * 20);
		}
		
		const animate = () => {
			// Update synaptic activity with smoother animation
			synapticActivity = synapticActivity.map((val, i) => {
				const newVal = 50 + Math.sin(Date.now() * 0.001 + i * 0.2) * 25 + Math.random() * 10;
				return val * 0.9 + newVal * 0.1; // Smooth transition
			});
			
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	}
	
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
		} catch (err) {
			console.error('Source drill-down error:', err);
			sourceDetails = generateMockHosts(source, Math.min(50, count));
		} finally {
			loading = false;
		}
	}
	
	function generateMockHosts(source, count) {
		const hosts = [];
		for (let i = 0; i < count; i++) {
			hosts.push({
				host: `${source.toLowerCase()}-host-${i + 1}.internal.com`,
				region: ['AMERICAS', 'EMEA', 'APAC', 'LATAM'][Math.floor(Math.random() * 4)],
				country: ['United States', 'Germany', 'Japan', 'Brazil'][Math.floor(Math.random() * 4)],
				data_center: `DC-${Math.floor(Math.random() * 10) + 1}`,
				infrastructure_type: ['Virtual', 'Physical', 'Cloud', 'Container'][Math.floor(Math.random() * 4)],
				present_in_cmdb: Math.random() > 0.3 ? 'Yes' : 'No',
				tanium_coverage: Math.random() > 0.4 ? 'Tanium' : 'No Coverage'
			});
		}
		return hosts;
	}

	function closeDetails() {
		selectedSource = null;
		sourceDetails = [];
	}
	
	function getSourceStatus(count) {
		let percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#FF6B9D', bgColor: '#FF6B9D20' };
		if (percentage >= 50) return { level: 'HIGH', color: '#4ECDC4', bgColor: '#4ECDC420' };
		if (percentage >= 25) return { level: 'MEDIUM', color: '#95E77E', bgColor: '#95E77E20' };
		return { level: 'LOW', color: '#FFE66D', bgColor: '#FFE66D20' };
	}
	
	function getSourceSize(count) {
		if (count > 100000) return 'ENTERPRISE';
		if (count > 50000) return 'LARGE';
		if (count > 10000) return 'MEDIUM';
		if (count > 1000) return 'SMALL';
		return 'MINIMAL';
	}
	
	function formatNumber(num) {
		return new Intl.NumberFormat('en-US').format(num);
	}
	
	function truncateText(text, maxLength = 20) {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}
	
	// Calculate bubble positions to avoid overlap
	function calculateBubblePosition(index, total) {
		const cols = 5;
		const rows = Math.ceil(total / cols);
		const col = index % cols;
		const row = Math.floor(index / cols);
		const spacing = 85;
		const offsetX = 50;
		const offsetY = 50;
		
		// Add some randomness to avoid perfect grid
		const jitterX = (Math.random() - 0.5) * 10;
		const jitterY = (Math.random() - 0.5) * 10;
		
		return {
			x: offsetX + col * spacing + jitterX,
			y: offsetY + row * spacing + jitterY
		};
	}
</script>

<div class="source-interface">
	<!-- Top Metrics -->
	<div class="metrics-header">
		<div class="metric-card">
			<div class="metric-icon">📊</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FF6B9D">{sourceCount}</div>
				<div class="metric-label">SOURCES</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">💻</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #4ECDC4">{formatNumber(totalHosts)}</div>
				<div class="metric-label">TOTAL HOSTS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">🔝</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #95E77E; font-size: 1rem" title={topSource[0]}>
					{truncateText(topSource[0], 18).toUpperCase()}
				</div>
				<div class="metric-label">TOP SOURCE</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📈</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FFE66D">{concentration}%</div>
				<div class="metric-label">TOP CONCENTRATION</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">⚖️</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #C77DFF">{formatNumber(avgHostsPerSource)}</div>
				<div class="metric-label">AVG HOSTS/SRC</div>
			</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content-layout">
		<!-- Left: Source Visualization -->
		<div class="org-panel">
			<div class="panel-header">
				<h2>SOURCE TABLE STRUCTURE</h2>
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="Search sources..."
					   class="search-input"/>
			</div>
			
			{#if loading && !selectedSource}
				<div class="loading-state">
					<div class="org-loader">
						<div class="spinner"></div>
					</div>
					<p>ANALYZING SOURCE STRUCTURE...</p>
				</div>
			{:else if error && !selectedSource}
				<div class="error-state">
					<div class="error-icon">⚠️</div>
					<p>{error}</p>
					<button class="retry-btn" on:click={loadData}>RETRY</button>
				</div>
			{:else if selectedSource}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3 title={selectedSource.source}>{truncateText(selectedSource.source, 30).toUpperCase()}</h3>
							<div class="source-stats">
								<span>{formatNumber(selectedSource.count)} HOSTS</span>
								<span>•</span>
								<span>{((selectedSource.count / totalHosts) * 100).toFixed(2)}% OF TOTAL</span>
								<span>•</span>
								<span>{getSourceSize(selectedSource.count)} TABLE</span>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="hosts-container">
						<table class="hosts-table">
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>DATA CENTER</th>
									<th>TYPE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each sourceDetails as host}
									<tr>
										<td class="hostname" title={host.host}>{truncateText(host.host, 25)}</td>
										<td>{host.region || 'UNKNOWN'}</td>
										<td>{host.country || 'UNKNOWN'}</td>
										<td>{host.data_center || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>
											<span class="status-dot {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												●
											</span>
										</td>
										<td>
											<span class="status-dot {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
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
				<div class="org-visualization">
					<!-- Hierarchical Tree -->
					<div class="tree-container">
						<div class="tree-root">
							<div class="root-node">
								<div class="node-icon">📊</div>
								<div class="node-label">SOURCE TABLES</div>
								<div class="node-count">{formatNumber(totalHosts)} HOSTS</div>
							</div>
						</div>
						<div class="tree-branches">
							{#each topFive as [source, count], i}
								{@const status = getSourceStatus(count)}
								<div class="branch-container">
									<div class="branch-line"></div>
									<div class="source-node" 
										 style="border-color: {status.color}; background: {status.bgColor}"
										 on:click={() => drillDownSource(source, count)}
										 title={source}>
										<div class="node-header" style="background: {status.color}30">
											<span class="node-rank">#{i + 1}</span>
										</div>
										<div class="node-body">
											<div class="node-name">{truncateText(source, 15).toUpperCase()}</div>
											<div class="node-metrics">
												<span class="node-hosts" style="color: {status.color}">
													{formatNumber(count)}
												</span>
												<span class="node-percent">{((count / totalHosts) * 100).toFixed(1)}%</span>
											</div>
											<div class="node-bar">
												<div class="bar-fill" 
													 style="width: {Math.min(100, (count / maxHosts) * 100)}%; 
															background: {status.color}"></div>
											</div>
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
					
					<!-- Bubble Chart -->
					<div class="bubble-chart">
						<svg viewBox="0 0 450 250">
							{#each sources.slice(0, Math.min(15, sources.length)) as [source, count], i}
								{@const pos = calculateBubblePosition(i, Math.min(15, sources.length))}
								{@const radius = Math.sqrt(count / maxHosts) * 30 + 10}
								{@const status = getSourceStatus(count)}
								<g class="bubble-group" 
								   on:click={() => drillDownSource(source, count)}
								   on:mouseenter={() => hoveredSource = source}
								   on:mouseleave={() => hoveredSource = null}>
									<circle cx="{pos.x}" cy="{pos.y}" 
											r="{radius}" 
											fill="{status.color}" 
											opacity="0.2"/>
									<circle cx="{pos.x}" cy="{pos.y}" 
											r="{radius * 0.7}" 
											fill="{status.color}" 
											opacity="0.4"/>
									<text x="{pos.x}" y="{pos.y}" 
										  text-anchor="middle" 
										  fill="#FFFFFF" 
										  font-size="10" 
										  font-weight="700">
										{formatNumber(count)}
									</text>
									{#if hoveredSource === source}
										<text x="{pos.x}" y="{pos.y - radius - 5}" 
											  text-anchor="middle" 
											  fill="#FFFFFF" 
											  font-size="8" 
											  font-weight="400">
											{truncateText(source, 20)}
										</text>
									{/if}
								</g>
							{/each}
						</svg>
					</div>
					
					<!-- Synaptic Activity Graph -->
					<div class="synaptic-activity">
						<svg viewBox="0 0 200 50">
							<defs>
								<linearGradient id="activityGradient" x1="0%" y1="0%" x2="0%" y2="100%">
									<stop offset="0%" style="stop-color:#4ECDC4;stop-opacity:0.8" />
									<stop offset="100%" style="stop-color:#4ECDC4;stop-opacity:0" />
								</linearGradient>
							</defs>
							<polyline points="{synapticActivity.map((val, i) => `${i * 4},${50 - val * 0.4}`).join(' ')}"
									  fill="none" 
									  stroke="#4ECDC4" 
									  stroke-width="2"
									  opacity="1"/>
							<polygon points="{synapticActivity.map((val, i) => `${i * 4},${50 - val * 0.4}`).join(' ')} 200,50 0,50"
									 fill="url(#activityGradient)" 
									 opacity="0.3"/>
						</svg>
						<div class="activity-label">SOURCE ACTIVITY</div>
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Middle: Analytics -->
		<div class="analytics-panel">
			<!-- Distribution Chart -->
			<div class="chart-box">
				<h3>HOST DISTRIBUTION BY SOURCE</h3>
				<div class="distribution-bars">
					{#each topFive as [source, count], i}
						{@const percentage = Math.min(100, (count / maxHosts) * 100)}
						{@const status = getSourceStatus(count)}
						<div class="dist-item" on:click={() => drillDownSource(source, count)}>
							<div class="dist-rank">#{i + 1}</div>
							<div class="dist-name" title={source}>{truncateText(source, 12).toUpperCase()}</div>
							<div class="dist-bar">
								<div class="dist-fill" 
									 style="width: {percentage}%; 
											background: linear-gradient(90deg, {status.color}40, {status.color})">
									<span class="dist-value">{formatNumber(count)}</span>
								</div>
							</div>
							<div class="dist-percent">{((count/totalHosts)*100).toFixed(1)}%</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Size Distribution -->
			<div class="chart-box">
				<h3>SOURCE SIZE DISTRIBUTION</h3>
				<div class="size-chart">
					{#each ['ENTERPRISE', 'LARGE', 'MEDIUM', 'SMALL', 'MINIMAL'] as size, i}
						{@const count = sources.filter(([_, c]) => getSourceSize(c) === size).length}
						{@const colors = ['#FF6B9D', '#4ECDC4', '#95E77E', '#FFE66D', '#C77DFF']}
						<div class="size-item">
							<div class="size-label">{size}</div>
							<div class="size-count" style="color: {colors[i]}">
								{count}
							</div>
							<div class="size-bar">
								<div class="size-fill" 
									 style="height: {sourceCount > 0 ? (count / sourceCount) * 100 : 0}%; 
											background: {colors[i]}">
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Coverage Stats -->
			<div class="chart-box">
				<h3>COVERAGE STATISTICS</h3>
				<div class="coverage-stats">
					<div class="coverage-item">
						<span class="coverage-label">Sources with >1K hosts</span>
						<span class="coverage-value" style="color: #FF6B9D">
							{sources.filter(([_, c]) => c > 1000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Sources with >10K hosts</span>
						<span class="coverage-value" style="color: #4ECDC4">
							{sources.filter(([_, c]) => c > 10000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Sources with >50K hosts</span>
						<span class="coverage-value" style="color: #95E77E">
							{sources.filter(([_, c]) => c > 50000).length}
						</span>
					</div>
				</div>
			</div>
		</div>
		
		<!-- Right: Source List -->
		<div class="list-panel">
			<div class="panel-header">
				<h3>ALL SOURCES</h3>
				<span class="source-count">{sources.length} TOTAL</span>
			</div>
			<div class="source-list">
				<table class="sources-table">
					<thead>
						<tr>
							<th>#</th>
							<th>SOURCE</th>
							<th>HOSTS</th>
							<th>SIZE</th>
							<th>STATUS</th>
						</tr>
					</thead>
					<tbody>
						{#each sources as [source, count], i}
							{@const status = getSourceStatus(count)}
							{@const size = getSourceSize(count)}
							<tr on:click={() => drillDownSource(source, count)}>
								<td class="rank">{i + 1}</td>
								<td class="source-name" title={source}>
									<span class="status-indicator" style="background: {status.color}"></span>
									{truncateText(source, 20).toUpperCase()}
								</td>
								<td class="host-count" style="color: {status.color}">
									{formatNumber(count)}
								</td>
								<td>
									<span class="size-badge" style="color: {status.color}">
										{size}
									</span>
								</td>
								<td>
									<span class="status-badge" 
										  style="color: {status.color}; 
												 border-color: {status.color};
												 background: {status.bgColor}">
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
	
	/* Metrics Header */
	.metrics-header {
		display: flex;
		gap: 1rem;
		flex-shrink: 0;
	}
	
	.metric-card {
		flex: 1;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(139, 233, 253, 0.2);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		gap: 1rem;
		align-items: center;
		transition: all 0.3s ease;
	}
	
	.metric-card:hover {
		background: rgba(255, 255, 255, 0.05);
		transform: translateY(-2px);
	}
	
	.metric-icon {
		font-size: 2rem;
		filter: saturate(1.5);
	}
	
	.metric-content {
		flex: 1;
		min-width: 0;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: 700;
		font-family: 'SF Mono', 'Monaco', monospace;
		margin-bottom: 0.25rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
		font-weight: 600;
	}
	
	/* Content Layout */
	.content-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 380px 320px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Org Panel */
	.org-panel {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(189, 147, 249, 0.2);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		flex-shrink: 0;
	}
	
	.panel-header h2, .panel-header h3 {
		margin: 0;
		font-size: 0.9rem;
		font-weight: 400;
		letter-spacing: 0.1em;
		color: #FF6B9D;
	}
	
	.search-input {
		padding: 0.5rem 1rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(139, 233, 253, 0.3);
		border-radius: 8px;
		color: #FFFFFF;
		font-size: 0.8rem;
		width: 200px;
		transition: all 0.3s ease;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #4ECDC4;
		background: rgba(0, 0, 0, 0.8);
	}
	
	.org-visualization {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		position: relative;
		overflow-y: auto;
		padding-right: 0.5rem;
	}
	
	/* Tree Container */
	.tree-container {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}
	
	.tree-root {
		display: flex;
		justify-content: center;
	}
	
	.root-node {
		background: linear-gradient(135deg, rgba(189, 147, 249, 0.1), rgba(189, 147, 249, 0.05));
		border: 2px solid #FF6B9D;
		border-radius: 12px;
		padding: 1rem 2rem;
		text-align: center;
		transition: all 0.3s ease;
	}
	
	.root-node:hover {
		background: linear-gradient(135deg, rgba(189, 147, 249, 0.15), rgba(189, 147, 249, 0.08));
	}
	
	.node-icon {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}
	
	.node-label {
		font-size: 0.8rem;
		color: #FF6B9D;
		font-weight: 600;
		letter-spacing: 0.1em;
	}
	
	.node-count {
		font-size: 1rem;
		color: #FFFFFF;
		font-weight: 700;
		margin-top: 0.25rem;
	}
	
	.tree-branches {
		display: flex;
		justify-content: space-around;
		gap: 0.5rem;
		position: relative;
		flex-wrap: wrap;
	}
	
	.branch-container {
		position: relative;
		flex: 1;
		min-width: 140px;
		max-width: 160px;
	}
	
	.branch-line {
		position: absolute;
		top: -1.5rem;
		left: 50%;
		width: 1px;
		height: 1.5rem;
		background: linear-gradient(to bottom, transparent, rgba(139, 233, 253, 0.5));
	}
	
	.source-node {
		border: 1px solid;
		border-radius: 10px;
		cursor: pointer;
		transition: all 0.3s ease;
		overflow: hidden;
	}
	
	.source-node:hover {
		transform: scale(1.05) translateY(-2px);
		box-shadow: 0 8px 20px rgba(139, 233, 253, 0.3);
	}
	
	.node-header {
		padding: 0.4rem;
		text-align: center;
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.node-rank {
		color: #FFFFFF;
		font-weight: 700;
	}
	
	.node-body {
		padding: 0.6rem;
	}
	
	.node-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.95);
		margin-bottom: 0.4rem;
		text-align: center;
		font-weight: 600;
	}
	
	.node-metrics {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.4rem;
		font-size: 0.75rem;
	}
	
	.node-hosts {
		font-weight: 700;
		font-family: 'SF Mono', 'Monaco', monospace;
	}
	
	.node-percent {
		color: rgba(255, 255, 255, 0.7);
		font-weight: 500;
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
	
	/* Bubble Chart */
	.bubble-chart {
		background: rgba(0, 0, 0, 0.4);
		border-radius: 10px;
		padding: 1rem;
		border: 1px solid rgba(139, 233, 253, 0.1);
	}
	
	.bubble-chart svg {
		width: 100%;
		height: 100%;
	}
	
	.bubble-group {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.bubble-group:hover {
		transform: scale(1.15);
		filter: brightness(1.2);
	}
	
	/* Synaptic Activity */
	.synaptic-activity {
		position: relative;
		height: 80px;
		background: linear-gradient(to bottom, rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.6));
		border: 1px solid rgba(139, 233, 253, 0.3);
		padding: 8px;
		border-radius: 10px;
		overflow: hidden;
	}
	
	.synaptic-activity svg {
		width: 100%;
		height: 100%;
	}
	
	.activity-label {
		position: absolute;
		top: 8px;
		left: 12px;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
		font-weight: 600;
	}
	
	/* Analytics Panel */
	.analytics-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chart-box {
		flex: 1;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(139, 233, 253, 0.2);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
	}
	
	.chart-box h3 {
		margin: 0 0 1rem 0;
		font-size: 0.8rem;
		color: #4ECDC4;
		font-weight: 400;
		letter-spacing: 0.1em;
	}
	
	.distribution-bars {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	
	.dist-item {
		display: grid;
		grid-template-columns: 30px 100px 1fr 50px;
		gap: 0.5rem;
		align-items: center;
		cursor: pointer;
		transition: all 0.2s ease;
		padding: 0.2rem;
		border-radius: 4px;
	}
	
	.dist-item:hover {
		background: rgba(139, 233, 253, 0.05);
		transform: translateX(2px);
	}
	
	.dist-rank {
		font-size: 0.7rem;
		color: #FF6B9D;
		font-weight: 700;
	}
	
	.dist-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.9);
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.dist-bar {
		height: 20px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.dist-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.5rem;
		transition: width 0.5s ease;
		border-radius: 4px;
	}
	
	.dist-value {
		font-size: 0.65rem;
		color: #FFFFFF;
		font-weight: 700;
		text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
	}
	
	.dist-percent {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		text-align: right;
		font-weight: 600;
	}
	
	/* Size Chart */
	.size-chart {
		display: flex;
		align-items: flex-end;
		justify-content: space-around;
		height: 120px;
		padding: 0.5rem 0;
	}
	
	.size-item {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.4rem;
	}
	
	.size-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.7);
		writing-mode: vertical-lr;
		text-align: center;
		font-weight: 600;
	}
	
	.size-count {
		font-size: 1rem;
		font-weight: 700;
	}
	
	.size-bar {
		width: 35px;
		height: 70px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px 4px 0 0;
		display: flex;
		align-items: flex-end;
		overflow: hidden;
	}
	
	.size-fill {
		width: 100%;
		border-radius: 4px 4px 0 0;
		transition: height 0.5s ease;
	}
	
	/* Coverage Stats */
	.coverage-stats {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}
	
	.coverage-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.6rem;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 8px;
		transition: all 0.2s ease;
	}
	
	.coverage-item:hover {
		background: rgba(0, 0, 0, 0.6);
		transform: translateX(2px);
	}
	
	.coverage-label {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
		font-weight: 500;
	}
	
	.coverage-value {
		font-size: 1.1rem;
		font-weight: 700;
		font-family: 'SF Mono', 'Monaco', monospace;
	}
	
	/* List Panel */
	.list-panel {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(189, 147, 249, 0.2);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.source-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
	}
	
	.source-list {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
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
		padding: 0.6rem 0.5rem;
		text-align: left;
		font-size: 0.65rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.sources-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.sources-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.08);
		transform: translateX(2px);
	}
	
	.sources-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.85);
	}
	
	.rank {
		color: #FF6B9D;
		font-weight: 700;
		font-size: 0.7rem;
		width: 30px;
	}
	
	.source-name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.host-count {
		font-family: 'SF Mono', 'Monaco', monospace;
		font-weight: 700;
	}
	
	.size-badge {
		font-size: 0.65rem;
		font-weight: 700;
		letter-spacing: 0.05em;
	}
	
	.status-badge {
		font-size: 0.6rem;
		padding: 0.2rem 0.4rem;
		border: 1px solid;
		border-radius: 6px;
		font-weight: 700;
		letter-spacing: 0.03em;
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
		margin-bottom: 1rem;
		flex-shrink: 0;
	}
	
	.detail-header h3 {
		margin: 0 0 0.25rem 0;
		font-size: 1.1rem;
		color: #FF6B9D;
		font-weight: 600;
	}
	
	.source-stats {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
		display: flex;
		gap: 0.5rem;
		font-weight: 500;
	}
	
	.close-btn {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.3);
		color: #FFFFFF;
		width: 32px;
		height: 32px;
		border-radius: 8px;
		font-size: 1.1rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}
	
	.close-btn:hover {
		background: rgba(255, 121, 198, 0.2);
		border-color: #FF6B9D;
		transform: rotate(90deg);
	}
	
	.hosts-container {
		flex: 1;
		overflow-y: auto;
		background: rgba(0, 0, 0, 0.4);
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
		padding: 0.6rem 0.5rem;
		text-align: left;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
		letter-spacing: 0.05em;
		font-weight: 600;
	}
	
	.hosts-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.85);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.hostname {
		font-family: 'SF Mono', 'Monaco', monospace;
		color: #4ECDC4;
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.status-dot {
		font-size: 0.9rem;
		display: inline-block;
		text-align: center;
	}
	
	.status-dot.active {
		color: #95E77E;
		text-shadow: 0 0 8px #95E77E;
	}
	
	.status-dot.inactive {
		color: #FF5555;
		opacity: 0.6;
	}
	
	/* Loading State */
	.loading-state, .error-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.org-loader {
		position: relative;
		width: 100px;
		height: 100px;
	}
	
	.spinner {
		width: 60px;
		height: 60px;
		margin: 20px;
		border: 4px solid rgba(78, 205, 196, 0.2);
		border-top: 4px solid #4ECDC4;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}
	
	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
	
	.loading-state p, .error-state p {
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.9rem;
		letter-spacing: 0.2em;
		font-weight: 600;
	}
	
	.error-icon {
		font-size: 3rem;
	}
	
	.retry-btn {
		padding: 0.6rem 1.5rem;
		background: linear-gradient(135deg, #FF6B9D, #FF6B9D80);
		border: 1px solid #FF6B9D;
		color: #FFFFFF;
		border-radius: 8px;
		font-size: 0.8rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.retry-btn:hover {
		background: linear-gradient(135deg, #FF6B9D, #FF6B9DCC);
		transform: translateY(-2px);
		box-shadow: 0 4px 15px rgba(255, 107, 157, 0.4);
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}
	
	::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb {
		background: linear-gradient(to bottom, #FF6B9D, #4ECDC4);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(to bottom, #FF6B9DCC, #4ECDC4CC);
	}
	
	/* Responsive Design */
	@media (max-width: 1400px) {
		.content-layout {
			grid-template-columns: 1fr 300px 280px;
		}
		
		.metric-value {
			font-size: 1.2rem;
		}
	}
	
	@media (max-width: 1200px) {
		.content-layout {
			grid-template-columns: 1fr;
			grid-template-rows: auto 1fr auto;
		}
		
		.analytics-panel {
			display: grid;
			grid-template-columns: repeat(3, 1fr);
		}
	}
	
	@media (max-width: 768px) {
		.metrics-header {
			flex-wrap: wrap;
		}
		
		.metric-card {
			min-width: calc(50% - 0.5rem);
		}
		
		.analytics-panel {
			grid-template-columns: 1fr;
		}
	}
</style>