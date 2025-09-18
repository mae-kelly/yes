<!-- SourceTables.svelte - Source Table Host Distribution -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	
	// Visualization states
	let tableNodes = [];
	let dataFlows = [];
	let pulseIntensity = 0;
	let networkActivity = 0;
	let tableProfiles = new Map();
	
	// Animation frame
	let animationFrame;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			let result = await response.json();
			data = result;
			loading = false;
			initializeTableNetwork();
			startNetworkAnimation();
		} catch (err) {
			console.error('Source table sync failed:', err);
			loading = false;
		}
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});
	
	function initializeTableNetwork() {
		if (!data.source_intelligence) return;
		
		let tables = Object.entries(data.source_intelligence)
			.sort((a, b) => b[1] - a[1])
			.slice(0, 50);
		
		// Create nodes for each table
		tables.forEach(([table, hostCount], i) => {
			let angle = (i / tables.length) * Math.PI * 2;
			let radius = 150 + (hostCount / Math.max(...tables.map(t => t[1]))) * 100;
			
			tableNodes.push({
				id: table,
				hostCount: hostCount,
				x: Math.cos(angle) * radius,
				y: Math.sin(angle) * radius,
				connections: Math.floor(Math.random() * 5) + 2,
				dataVolume: hostCount * (10 + Math.random() * 90),
				queryFrequency: Math.floor(hostCount * (0.5 + Math.random())),
				lastAccess: Date.now() - Math.random() * 86400000,
				performance: 70 + Math.random() * 30
			});
			
			tableProfiles.set(table, {
				totalHosts: hostCount,
				activeHosts: Math.floor(hostCount * (0.7 + Math.random() * 0.3)),
				dataSize: (hostCount * (Math.random() * 100 + 50)).toFixed(2),
				replicationFactor: Math.floor(Math.random() * 3) + 1,
				partitions: Math.ceil(hostCount / 1000) || 1
			});
		});
		
		// Create data flow connections
		tableNodes.forEach((node, i) => {
			for (let j = 0; j < node.connections; j++) {
				let targetIdx = Math.floor(Math.random() * tableNodes.length);
				if (targetIdx !== i) {
					dataFlows.push({
						source: i,
						target: targetIdx,
						bandwidth: Math.random() * 100,
						latency: Math.random() * 50,
						packets: []
					});
				}
			}
		});
	}
	
	function startNetworkAnimation() {
		let time = 0;
		
		function animate() {
			time += 0.016;
			
			pulseIntensity = 0.5 + Math.sin(time * 2) * 0.5;
			networkActivity = 50 + Math.sin(time * 0.5) * 30 + Math.sin(time * 1.3) * 20;
			
			// Update data flows
			dataFlows.forEach(flow => {
				flow.bandwidth = Math.max(10, Math.min(100, flow.bandwidth + (Math.random() - 0.5) * 10));
			});
			
			animationFrame = requestAnimationFrame(animate);
		}
		animate();
	}
	
	$: filteredTables = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([table]) => table.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxHosts = filteredTables.length > 0 ? Math.max(...filteredTables.map(([,h]) => h)) : 1;
	
	function getTableClass(hostCount) {
		let normalized = hostCount / maxHosts;
		
		if (normalized >= 0.8) {
			return { level: 'PRIMARY', color: '#FF79C6', symbol: '◈' };
		} else if (normalized >= 0.6) {
			return { level: 'REPLICA', color: '#8BE9FD', symbol: '◆' };
		} else if (normalized >= 0.4) {
			return { level: 'SHARD', color: '#50FA7B', symbol: '▲' };
		} else if (normalized >= 0.2) {
			return { level: 'PARTITION', color: '#F1FA8C', symbol: '●' };
		} else {
			return { level: 'FRAGMENT', color: '#FFB86C', symbol: '○' };
		}
	}
	
	async function drillDownTable(table, hostCount) {
		selectedSource = { table, hostCount };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(table)}`);
			let result = await response.json();
			hostDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Table drill-down failed:', err);
			hostDetails = [];
			loading = false;
		}
	}
	
	function closeDetails() {
		selectedSource = null;
		hostDetails = [];
	}
</script>

<div class="source-table-interface">
	<div class="interface-container">
		<div class="search-section">
			<input type="text"
				   bind:value={searchTerm}
				   placeholder="SEARCH TABLES..."
				   class="search-input"/>
			<div class="search-stats">
				<span class="stat">{filteredTables.length} TABLES</span>
				<span class="stat">{(data.total_mentions || 0).toLocaleString()} TOTAL HOSTS</span>
				<span class="stat">ACTIVITY: {networkActivity.toFixed(0)}%</span>
			</div>
		</div>
		
		{#if loading && !selectedSource}
			<div class="loading-state">
				<div class="loading-animation">
					<div class="cube-loader">
						<div class="cube-face"></div>
						<div class="cube-face"></div>
						<div class="cube-face"></div>
					</div>
				</div>
				<p>SYNCHRONIZING TABLE SCHEMA...</p>
			</div>
		{:else if selectedSource}
			<div class="detail-view">
				<div class="detail-header">
					<div class="table-identity">
						<h2>{selectedSource.table.toUpperCase()}</h2>
						<span class="host-count">{selectedSource.hostCount.toLocaleString()} HOSTS</span>
					</div>
					<button class="close-btn" on:click={closeDetails}>✕</button>
				</div>
				
				<div class="host-grid">
					<table class="hosts-table">
						<thead>
							<tr>
								<th>HOST_ID</th>
								<th>REGION</th>
								<th>COUNTRY</th>
								<th>TYPE</th>
								<th>CMDB</th>
								<th>TANIUM</th>
							</tr>
						</thead>
						<tbody>
							{#each hostDetails.slice(0, 20) as host}
								<tr>
									<td class="host-id">{host.host.substring(0, 40)}</td>
									<td>{host.region || 'UNKNOWN'}</td>
									<td>{host.country || 'UNKNOWN'}</td>
									<td>{host.infrastructure_type || 'UNKNOWN'}</td>
									<td><span class="indicator {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : ''}">{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}</span></td>
									<td><span class="indicator {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : ''}">{host.tanium_coverage?.toLowerCase().includes('tanium') ? '◈' : '○'}</span></td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{:else}
			<div class="main-display">
				<div class="network-visualization">
					<svg viewBox="-300 -300 600 600" class="network-svg">
						<defs>
							<radialGradient id="tableGlow">
								<stop offset="0%" style="stop-color:#FF79C6;stop-opacity:0.8" />
								<stop offset="100%" style="stop-color:#FF79C6;stop-opacity:0" />
							</radialGradient>
						</defs>
						
						{#each dataFlows as flow}
							{#if tableNodes[flow.source] && tableNodes[flow.target]}
								<line x1="{tableNodes[flow.source].x}" y1="{tableNodes[flow.source].y}"
									  x2="{tableNodes[flow.target].x}" y2="{tableNodes[flow.target].y}"
									  stroke="rgba(139, 233, 253, 0.2)"
									  stroke-width="{flow.bandwidth / 50}"
									  opacity="{flow.bandwidth / 200}"/>
							{/if}
						{/each}
						
						{#each tableNodes.slice(0, 20) as node}
							{@const tableClass = getTableClass(node.hostCount)}
							<g transform="translate({node.x}, {node.y})"
							   on:click={() => drillDownTable(node.id, node.hostCount)}
							   class="table-node">
								<circle r="{10 + node.hostCount / maxHosts * 20}"
										fill={tableClass.color}
										opacity="0.2"/>
								<circle r="{5 + node.hostCount / maxHosts * 10}"
										fill={tableClass.color}
										opacity="0.8"/>
								<text text-anchor="middle" dy="4" fill="#000" font-size="12" font-weight="bold">
									{tableClass.symbol}
								</text>
								<text y="-20" text-anchor="middle" fill="#fff" font-size="8" opacity="0.8">
									{node.id.substring(0, 15)}
								</text>
							</g>
						{/each}
					</svg>
					
					<div class="activity-monitor">
						<div class="monitor-bar" style="height: {networkActivity}%; background: linear-gradient(180deg, #FF79C6, #8BE9FD)"></div>
					</div>
				</div>
				
				<div class="table-matrix">
					<div class="matrix-header">
						<h3>TABLE HOST DISTRIBUTION</h3>
					</div>
					<div class="matrix-content">
						<table class="data-table">
							<thead>
								<tr>
									<th>RANK</th>
									<th>TABLE_NAME</th>
									<th>HOST_COUNT</th>
									<th>DISTRIBUTION</th>
									<th>STATUS</th>
								</tr>
							</thead>
							<tbody>
								{#each filteredTables.slice(0, 15) as [table, hostCount], index}
									{@const tableClass = getTableClass(hostCount)}
									{@const profile = tableProfiles.get(table)}
									<tr on:click={() => drillDownTable(table, hostCount)}>
										<td style="color: {tableClass.color}">#{index + 1}</td>
										<td>
											<span style="color: {tableClass.color}">{tableClass.symbol}</span>
											{table.substring(0, 30).toUpperCase()}
										</td>
										<td style="color: #8BE9FD">{hostCount.toLocaleString()}</td>
										<td>
											<div class="distribution-bar">
												<div class="bar-fill" style="width: {(hostCount/maxHosts)*100}%; background: {tableClass.color}"></div>
											</div>
										</td>
										<td>
											<span class="status-badge" style="background: {tableClass.color}20; color: {tableClass.color}">
												{tableClass.level}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.source-table-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000;
		overflow: hidden;
	}
	
	.interface-container {
		height: 100%;
		display: flex;
		flex-direction: column;
		padding: 1rem;
	}
	
	.search-section {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding: 0.5rem;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(255, 121, 198, 0.2);
		border-radius: 8px;
	}
	
	.search-input {
		background: transparent;
		border: none;
		color: #FF79C6;
		font-family: monospace;
		font-size: 0.9rem;
		padding: 0.5rem;
		outline: none;
		letter-spacing: 0.1em;
		flex: 1;
	}
	
	.search-stats {
		display: flex;
		gap: 2rem;
	}
	
	.stat {
		color: #8BE9FD;
		font-size: 0.8rem;
		font-family: monospace;
	}
	
	.main-display {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		height: calc(100% - 60px);
	}
	
	.network-visualization {
		position: relative;
		background: radial-gradient(circle at center, rgba(255, 121, 198, 0.02), transparent);
		border: 1px solid rgba(255, 121, 198, 0.1);
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}
	
	.network-svg {
		width: 90%;
		height: 90%;
	}
	
	.table-node {
		cursor: pointer;
		transition: transform 0.3s ease;
	}
	
	.table-node:hover {
		transform: scale(1.2);
	}
	
	.activity-monitor {
		position: absolute;
		right: 20px;
		top: 20px;
		width: 4px;
		height: 100px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
	}
	
	.monitor-bar {
		width: 100%;
		position: absolute;
		bottom: 0;
		transition: height 0.5s ease;
		border-radius: 2px;
	}
	
	.table-matrix {
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 12px;
		overflow: hidden;
	}
	
	.matrix-header {
		padding: 1rem;
		background: linear-gradient(90deg, rgba(255, 121, 198, 0.1), rgba(139, 233, 253, 0.1));
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.matrix-header h3 {
		margin: 0;
		color: #FF79C6;
		font-size: 0.9rem;
		letter-spacing: 0.1em;
	}
	
	.matrix-content {
		flex: 1;
		overflow-y: auto;
	}
	
	.data-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.data-table th {
		background: rgba(0, 0, 0, 0.8);
		color: #8BE9FD;
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		border-bottom: 1px solid rgba(139, 233, 253, 0.2);
	}
	
	.data-table tr {
		cursor: pointer;
		transition: background 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.data-table tr:hover {
		background: rgba(255, 121, 198, 0.05);
	}
	
	.data-table td {
		padding: 0.6rem 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.distribution-bar {
		width: 100px;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.status-badge {
		padding: 0.2rem 0.4rem;
		border-radius: 4px;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}
	
	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}
	
	.cube-loader {
		width: 60px;
		height: 60px;
		position: relative;
		transform-style: preserve-3d;
		animation: rotateCube 2s linear infinite;
	}
	
	.cube-face {
		position: absolute;
		width: 60px;
		height: 60px;
		border: 2px solid #FF79C6;
		background: rgba(255, 121, 198, 0.1);
	}
	
	.cube-face:nth-child(1) { transform: translateZ(30px); }
	.cube-face:nth-child(2) { transform: rotateY(90deg) translateZ(30px); }
	.cube-face:nth-child(3) { transform: rotateX(90deg) translateZ(30px); }
	
	@keyframes rotateCube {
		from { transform: rotateX(0) rotateY(0); }
		to { transform: rotateX(360deg) rotateY(360deg); }
	}
	
	.loading-state p {
		color: #8BE9FD;
		font-size: 0.9rem;
		letter-spacing: 0.1em;
	}
	
	.detail-view {
		flex: 1;
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 121, 198, 0.1);
		border-radius: 12px;
		overflow: hidden;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
		background: linear-gradient(135deg, rgba(255, 121, 198, 0.1), transparent);
		border-bottom: 1px solid rgba(255, 121, 198, 0.2);
	}
	
	.table-identity h2 {
		margin: 0;
		color: #FF79C6;
		font-size: 1.2rem;
		letter-spacing: 0.05em;
	}
	
	.host-count {
		color: #8BE9FD;
		font-size: 0.9rem;
		font-family: monospace;
	}
	
	.close-btn {
		background: rgba(255, 121, 198, 0.1);
		border: 1px solid #FF79C6;
		color: #FF79C6;
		width: 32px;
		height: 32px;
		border-radius: 50%;
		cursor: pointer;
		font-size: 1.2rem;
		transition: all 0.3s ease;
	}
	
	.close-btn:hover {
		background: rgba(255, 121, 198, 0.2);
		transform: rotate(90deg);
	}
	
	.host-grid {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
	}
	
	.hosts-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.hosts-table th {
		background: rgba(0, 0, 0, 0.8);
		color: #8BE9FD;
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
	}
	
	.hosts-table td {
		padding: 0.6rem 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.host-id {
		font-family: monospace;
		color: #FF79C6;
		font-size: 0.7rem;
	}
	
	.indicator {
		font-size: 0.9rem;
		color: #666;
	}
	
	.indicator.active {
		color: #50FA7B;
		text-shadow: 0 0 10px #50FA7B;
	}
	
	::-webkit-scrollbar {
		width: 4px;
		height: 4px;
	}
	
	::-webkit-scrollbar-track {
		background: #000;
	}
	
	::-webkit-scrollbar-thumb {
		background: linear-gradient(180deg, #FF79C6, #8BE9FD);
		border-radius: 2px;
	}
</style>