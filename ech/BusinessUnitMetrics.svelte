<!-- BusinessUnitMetrics.svelte - Clean Division Analytics -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedDivision = null;
	let divisionDetails = [];
	let searchTerm = '';
	
	// Simple animation states
	let animationFrame = null;
	let activityData = [];
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/business_unit_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Division sync failed:', err);
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
	
	$: filteredDivisions = data.business_intelligence ? 
		Object.entries(data.business_intelligence)
			.filter(([division]) => division.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = filteredDivisions.reduce((sum, [_, count]) => sum + count, 0);
	$: maxCount = filteredDivisions.length > 0 ? Math.max(...filteredDivisions.map(([,c]) => c)) : 1;
	$: minCount = filteredDivisions.length > 0 ? Math.min(...filteredDivisions.map(([,c]) => c)) : 0;
	$: avgCount = filteredDivisions.length > 0 ? Math.round(totalHosts / filteredDivisions.length) : 0;
	
	function getDivisionClass(count) {
		let normalized = (count - minCount) / (maxCount - minCount || 1);
		let percentile = normalized * 100;
		
		if (percentile >= 85) {
			return {
				level: 'ENTERPRISE',
				color: '#00E5FF',
				bgColor: 'rgba(0, 229, 255, 0.1)',
				description: 'Large Division'
			};
		} else if (percentile >= 65) {
			return {
				level: 'CORPORATE',
				color: '#50FA7B',
				bgColor: 'rgba(80, 250, 123, 0.1)',
				description: 'Major Division'
			};
		} else if (percentile >= 45) {
			return {
				level: 'BUSINESS',
				color: '#FFB86C',
				bgColor: 'rgba(255, 184, 108, 0.1)',
				description: 'Standard Division'
			};
		} else if (percentile >= 25) {
			return {
				level: 'TEAM',
				color: '#FF79C6',
				bgColor: 'rgba(255, 121, 198, 0.1)',
				description: 'Small Division'
			};
		} else {
			return {
				level: 'UNIT',
				color: '#BD93F9',
				bgColor: 'rgba(189, 147, 249, 0.1)',
				description: 'Minimal Division'
			};
		}
	}
	
	async function drillDownDivision(division, count) {
		selectedDivision = { division, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(division)}`);
			let result = await response.json();
			divisionDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Division deep scan failed:', err);
			divisionDetails = [];
			loading = false;
		}
	}
	
	function closeDetails() {
		selectedDivision = null;
		divisionDetails = [];
	}

	function formatNumber(num) {
		return new Intl.NumberFormat('en-US').format(num);
	}

	function truncateText(text, maxLength = 25) {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}
</script>

<div class="division-interface">
	<!-- Header with Key Metrics -->
	<div class="metrics-header">
		<div class="metric-card">
			<div class="metric-icon">🏢</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #00E5FF">{filteredDivisions.length}</div>
				<div class="metric-label">DIVISIONS</div>
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
			<div class="metric-icon">📊</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FFB86C">{formatNumber(maxCount)}</div>
				<div class="metric-label">LARGEST DIVISION</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">⚖️</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FF79C6">{formatNumber(avgCount)}</div>
				<div class="metric-label">AVERAGE SIZE</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📈</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #BD93F9">{filteredDivisions.filter(([_,c]) => c > avgCount).length}</div>
				<div class="metric-label">ABOVE AVERAGE</div>
			</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content-layout">
		<!-- Left: Division Visualization -->
		<div class="division-panel">
			<div class="panel-header">
				<h2>Division Structure</h2>
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="Search divisions..."
					   class="search-input"/>
			</div>
			
			{#if loading && !selectedDivision}
				<div class="loading-state">
					<div class="loader-animation">
						<div class="org-box"></div>
						<div class="org-box"></div>
						<div class="org-box"></div>
						<div class="org-box"></div>
					</div>
					<p>Loading division data...</p>
				</div>
			{:else if selectedDivision}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedDivision.division.toUpperCase()}</h3>
							<div class="division-stats">
								<span>{formatNumber(selectedDivision.count)} hosts</span>
								<span>•</span>
								<span>{((selectedDivision.count / totalHosts) * 100).toFixed(2)}% of total</span>
								<span>•</span>
								<span>{getDivisionClass(selectedDivision.count).level} division</span>
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
									<th>Infrastructure</th>
									<th>CMDB Status</th>
									<th>Security</th>
								</tr>
							</thead>
							<tbody>
								{#each divisionDetails as host}
									<tr>
										<td class="hostname" title={host.host}>{truncateText(host.host, 35)}</td>
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
				<div class="division-visualization">
					<!-- Org Chart Style Layout -->
					<div class="org-chart">
						{#each filteredDivisions.slice(0, 12) as [division, count], i}
							{@const divClass = getDivisionClass(count)}
							<div class="division-box" 
								 style="border-color: {divClass.color}; background: {divClass.bgColor}"
								 on:click={() => drillDownDivision(division, count)}>
								<div class="division-header" style="background: {divClass.color}20">
									<div class="division-rank">#{i + 1}</div>
									<div class="division-level" style="color: {divClass.color}">{divClass.level}</div>
								</div>
								<div class="division-body">
									<div class="division-name" title={division}>{truncateText(division, 20)}</div>
									<div class="division-count" style="color: {divClass.color}">{formatNumber(count)}</div>
									<div class="division-percentage">{((count / totalHosts) * 100).toFixed(1)}%</div>
								</div>
								<div class="division-bar">
									<div class="bar-fill" 
										 style="width: {((count / maxCount) * 100)}%; background: {divClass.color}">
									</div>
								</div>
							</div>
						{/each}
					</div>
					
					<!-- Activity Chart -->
					<div class="activity-chart">
						<h4>Division Activity</h4>
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
		
		<!-- Right: Division Rankings -->
		<div class="rankings-panel">
			<div class="panel-header">
				<h3>Division Rankings</h3>
				<span class="division-count">{filteredDivisions.length} total</span>
			</div>
			
			<div class="rankings-list">
				<table class="rankings-table">
					<thead>
						<tr>
							<th>Rank</th>
							<th>Division</th>
							<th>Hosts</th>
							<th>Share</th>
							<th>Type</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredDivisions as [division, count], index}
							{@const divClass = getDivisionClass(count)}
							<tr on:click={() => drillDownDivision(division, count)}>
								<td class="rank">#{index + 1}</td>
								<td class="division-name" title={division}>
									<span class="status-dot" style="background: {divClass.color}"></span>
									{truncateText(division, 25)}
								</td>
								<td class="host-count" style="color: {divClass.color}">
									{formatNumber(count)}
								</td>
								<td class="percentage">
									{((count / totalHosts) * 100).toFixed(1)}%
								</td>
								<td>
									<span class="type-badge" style="color: {divClass.color}; border-color: {divClass.color}">
										{divClass.level}
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
	.division-interface {
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
	
	/* Division Panel */
	.division-panel {
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
	
	/* Division Visualization */
	.division-visualization {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		overflow: hidden;
	}
	
	.org-chart {
		flex: 1;
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1rem;
		overflow-y: auto;
		padding: 0.5rem;
	}
	
	.division-box {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid;
		border-radius: 10px;
		cursor: pointer;
		transition: all 0.3s ease;
		overflow: hidden;
		height: fit-content;
	}
	
	.division-box:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
	}
	
	.division-header {
		padding: 0.8rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.division-rank {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
	}
	
	.division-level {
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.division-body {
		padding: 1rem;
		text-align: center;
	}
	
	.division-name {
		font-size: 0.9rem;
		color: #ffffff;
		margin-bottom: 0.5rem;
		font-weight: 500;
	}
	
	.division-count {
		font-size: 1.3rem;
		font-weight: 600;
		font-family: 'SF Mono', 'Monaco', monospace;
		margin-bottom: 0.3rem;
	}
	
	.division-percentage {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.7);
		margin-bottom: 0.8rem;
	}
	
	.division-bar {
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
		margin: 0 1rem 1rem;
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
	
	.division-count {
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
	
	.division-name {
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
	
	.type-badge {
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
	
	.division-stats {
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
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.5rem;
	}
	
	.org-box {
		width: 40px;
		height: 40px;
		background: #00E5FF;
		border-radius: 6px;
		animation: orgPulse 1.5s ease-in-out infinite;
	}
	
	.org-box:nth-child(1) { animation-delay: 0s; }
	.org-box:nth-child(2) { animation-delay: 0.3s; }
	.org-box:nth-child(3) { animation-delay: 0.6s; }
	.org-box:nth-child(4) { animation-delay: 0.9s; }
	
	@keyframes orgPulse {
		0%, 100% { opacity: 0.3; transform: scale(0.8); }
		50% { opacity: 1; transform: scale(1); }
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
		
		.org-chart {
			grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
		
		.org-chart {
			grid-template-columns: 1fr;
		}
	}
</style>