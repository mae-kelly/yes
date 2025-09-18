<!-- CIOMetrics.svelte - Clean Executive Dashboard -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedExecutive = null;
	let executiveDetails = [];
	let searchTerm = '';
	
	// Simple animation states
	let animationFrame = null;
	let networkActivity = [];
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/cio_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Executive sync failed:', err);
			loading = false;
		}
		
		// Initialize network activity
		for (let i = 0; i < 50; i++) {
			networkActivity.push(50 + Math.random() * 30);
		}
		
		// Start simple animation
		const animate = () => {
			networkActivity = networkActivity.map((val, i) => 
				50 + Math.sin(Date.now() * 0.001 + i * 0.2) * 20 + Math.random() * 10
			);
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});
	
	$: filteredExecutives = data.operative_intelligence ? 
		Object.entries(data.operative_intelligence)
			.filter(([exec]) => exec.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalAssets = filteredExecutives.reduce((sum, [_, count]) => sum + count, 0);
	$: maxAssets = filteredExecutives.length > 0 ? Math.max(...filteredExecutives.map(([,c]) => c)) : 1;
	$: minAssets = filteredExecutives.length > 0 ? Math.min(...filteredExecutives.map(([,c]) => c)) : 0;
	$: avgAssets = filteredExecutives.length > 0 ? Math.round(totalAssets / filteredExecutives.length) : 0;
	
	function getExecutiveClass(count) {
		let normalized = (count - minAssets) / (maxAssets - minAssets || 1);
		let percentile = normalized * 100;
		
		if (percentile >= 90) {
			return {
				level: 'C-SUITE',
				color: '#00E5FF',
				bgColor: 'rgba(0, 229, 255, 0.1)',
				description: 'Executive Level'
			};
		} else if (percentile >= 70) {
			return {
				level: 'SENIOR VP',
				color: '#50FA7B',
				bgColor: 'rgba(80, 250, 123, 0.1)',
				description: 'Senior Management'
			};
		} else if (percentile >= 50) {
			return {
				level: 'VP',
				color: '#FFB86C',
				bgColor: 'rgba(255, 184, 108, 0.1)',
				description: 'Vice President'
			};
		} else if (percentile >= 30) {
			return {
				level: 'DIRECTOR',
				color: '#FF79C6',
				bgColor: 'rgba(255, 121, 198, 0.1)',
				description: 'Director Level'
			};
		} else {
			return {
				level: 'MANAGER',
				color: '#BD93F9',
				bgColor: 'rgba(189, 147, 249, 0.1)',
				description: 'Management Level'
			};
		}
	}
	
	async function drillDownExecutive(executive, count) {
		selectedExecutive = { executive, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(executive)}`);
			let result = await response.json();
			executiveDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Executive deep scan failed:', err);
			executiveDetails = [];
			loading = false;
		}
	}
	
	function closeDetails() {
		selectedExecutive = null;
		executiveDetails = [];
	}

	function formatNumber(num) {
		return new Intl.NumberFormat('en-US').format(num);
	}

	function truncateText(text, maxLength = 25) {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}
</script>

<div class="executive-interface">
	<!-- Header with Key Metrics -->
	<div class="metrics-header">
		<div class="metric-card">
			<div class="metric-icon">👔</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #00E5FF">{filteredExecutives.length}</div>
				<div class="metric-label">EXECUTIVES</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">💼</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #50FA7B">{formatNumber(totalAssets)}</div>
				<div class="metric-label">TOTAL ASSETS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">⭐</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FFB86C">{formatNumber(maxAssets)}</div>
				<div class="metric-label">HIGHEST COUNT</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📊</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FF79C6">{formatNumber(avgAssets)}</div>
				<div class="metric-label">AVERAGE</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">🏆</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #BD93F9">{filteredExecutives.filter(([_,c]) => c > avgAssets).length}</div>
				<div class="metric-label">ABOVE AVERAGE</div>
			</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content-layout">
		<!-- Left: Executive Network -->
		<div class="executive-panel">
			<div class="panel-header">
				<h2>Executive Network</h2>
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="Search executives..."
					   class="search-input"/>
			</div>
			
			{#if loading && !selectedExecutive}
				<div class="loading-state">
					<div class="loader-animation">
						<div class="exec-node"></div>
						<div class="exec-node"></div>
						<div class="exec-node"></div>
						<div class="connection-line"></div>
					</div>
					<p>Loading executive data...</p>
				</div>
			{:else if selectedExecutive}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedExecutive.executive.toUpperCase()}</h3>
							<div class="executive-stats">
								<span>{formatNumber(selectedExecutive.count)} assets</span>
								<span>•</span>
								<span>{((selectedExecutive.count / totalAssets) * 100).toFixed(2)}% of total</span>
								<span>•</span>
								<span>{getExecutiveClass(selectedExecutive.count).level}</span>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					
					<div class="hosts-container">
						<table class="hosts-table">
							<thead>
								<tr>
									<th>Asset ID</th>
									<th>Region</th>
									<th>Country</th>
									<th>Infrastructure</th>
									<th>CMDB Status</th>
									<th>Security</th>
								</tr>
							</thead>
							<tbody>
								{#each executiveDetails as host}
									<tr>
										<td class="hostname" title={host.host}>{truncateText(host.host, 30)}</td>
										<td>{host.region || 'Unknown'}</td>
										<td>{host.country || 'Unknown'}</td>
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
				<div class="executive-visualization">
					<!-- Network Diagram -->
					<div class="network-diagram">
						<svg viewBox="0 0 600 400" class="network-svg">
							<!-- Draw connections between top executives -->
							{#each filteredExecutives.slice(0, 8) as [exec1, count1], i}
								{#each filteredExecutives.slice(i + 1, 8) as [exec2, count2], j}
									{#if Math.random() > 0.6}
										{@const x1 = 100 + (i % 4) * 125}
										{@const y1 = 80 + Math.floor(i / 4) * 120}
										{@const x2 = 100 + ((i + j + 1) % 4) * 125}
										{@const y2 = 80 + Math.floor((i + j + 1) / 4) * 120}
										<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
											  stroke="rgba(0, 229, 255, 0.2)" stroke-width="1"
											  stroke-dasharray="3,3" opacity="0.6"/>
									{/if}
								{/each}
							{/each}
							
							<!-- Draw executive nodes -->
							{#each filteredExecutives.slice(0, 8) as [executive, count], i}
								{@const execClass = getExecutiveClass(count)}
								{@const x = 100 + (i % 4) * 125}
								{@const y = 80 + Math.floor(i / 4) * 120}
								{@const radius = 15 + (count / maxAssets) * 20}
								
								<g class="executive-node" on:click={() => drillDownExecutive(executive, count)}>
									<!-- Outer ring -->
									<circle cx="{x}" cy="{y}" r="{radius + 5}"
											fill="{execClass.color}" opacity="0.2"/>
									<!-- Inner core -->
									<circle cx="{x}" cy="{y}" r="{radius}"
											fill="{execClass.color}" opacity="0.6"/>
									<!-- Label -->
									<text x="{x}" y="{y - radius - 10}" 
										  text-anchor="middle" 
										  fill="#ffffff" font-size="10" font-weight="500">
										{truncateText(executive, 12)}
									</text>
									<!-- Count -->
									<text x="{x}" y="{y + 3}" 
										  text-anchor="middle" 
										  fill="#ffffff" font-size="12" font-weight="600">
										{count >= 1000 ? `${(count/1000).toFixed(0)}K` : count}
									</text>
								</g>
							{/each}
						</svg>
					</div>
					
					<!-- Network Activity Chart -->
					<div class="activity-chart">
						<h4>Network Activity</h4>
						<svg viewBox="0 0 200 60">
							<polyline points="{networkActivity.map((val, i) => `${i * 4},${60 - val * 0.6}`).join(' ')}"
									  fill="none" 
									  stroke="#00E5FF" 
									  stroke-width="2"
									  opacity="0.8"/>
						</svg>
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Right: Executive Rankings -->
		<div class="rankings-panel">
			<div class="panel-header">
				<h3>Executive Rankings</h3>
				<span class="executive-count">{filteredExecutives.length} total</span>
			</div>
			
			<div class="rankings-list">
				<table class="rankings-table">
					<thead>
						<tr>
							<th>Rank</th>
							<th>Executive</th>
							<th>Assets</th>
							<th>Share</th>
							<th>Level</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredExecutives as [executive, count], index}
							{@const execClass = getExecutiveClass(count)}
							<tr on:click={() => drillDownExecutive(executive, count)}>
								<td class="rank">#{index + 1}</td>
								<td class="executive-name" title={executive}>
									<span class="status-dot" style="background: {execClass.color}"></span>
									{truncateText(executive, 25)}
								</td>
								<td class="asset-count" style="color: {execClass.color}">
									{formatNumber(count)}
								</td>
								<td class="percentage">
									{((count / totalAssets) * 100).toFixed(1)}%
								</td>
								<td>
									<span class="level-badge" style="color: {execClass.color}; border-color: {execClass.color}">
										{execClass.level}
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
	.executive-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: transparent;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
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
	
	/* Executive Panel */
	.executive-panel {
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
	
	/* Executive Visualization */
	.executive-visualization {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		overflow: hidden;
	}
	
	.network-diagram {
		flex: 1;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 10px;
		padding: 1rem;
		overflow: hidden;
	}
	
	.network-svg {
		width: 100%;
		height: 100%;
	}
	
	.executive-node {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.executive-node:hover {
		transform: scale(1.1);
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
	
	/* Rankings Panel */
	.rankings-panel {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		backdrop-filter: blur(10px);
		overflow: hidden;
		padding: 1.5rem;
	}
	
	.executive-count {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 500;
	}
	
	.rankings-list {
		flex: 1;
		overflow-y: auto;
		margin-top: 1rem;
	}
	
	.rankings-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.rankings-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.95);
		z-index: 10;
	}
	
	.rankings-table th {
		padding: 0.8rem 0.5rem;
		text-align: left;
		font-size: 0.8rem;
		font-weight: 500;
		color: rgba(255, 255, 255, 0.7);
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.rankings-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.rankings-table tbody tr:hover {
		background: rgba(0, 229, 255, 0.05);
	}
	
	.rankings-table td {
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
	
	.executive-name {
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
	
	.asset-count {
		font-family: 'SF Mono', 'Monaco', monospace;
		font-weight: 600;
	}
	
	.percentage {
		font-family: 'SF Mono', 'Monaco', monospace;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.level-badge {
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
	
	.executive-stats {
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
		position: relative;
		width: 120px;
		height: 80px;
	}
	
	.exec-node {
		position: absolute;
		width: 20px;
		height: 20px;
		background: #00E5FF;
		border-radius: 50%;
		animation: nodePulse 2s ease-in-out infinite;
	}
	
	.exec-node:nth-child(1) {
		top: 10px;
		left: 50px;
		animation-delay: 0s;
	}
	
	.exec-node:nth-child(2) {
		top: 40px;
		left: 20px;
		animation-delay: 0.5s;
	}
	
	.exec-node:nth-child(3) {
		top: 40px;
		left: 80px;
		animation-delay: 1s;
	}
	
	.connection-line {
		position: absolute;
		top: 50%;
		left: 0;
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, #00E5FF, transparent);
		animation: connectionFlow 3s linear infinite;
	}
	
	@keyframes nodePulse {
		0%, 100% { opacity: 0.3; transform: scale(0.8); }
		50% { opacity: 1; transform: scale(1.2); }
	}
	
	@keyframes connectionFlow {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100%); }
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
		
		.rankings-panel {
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