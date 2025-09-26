<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let sourceDetails = [];
	let searchTerm = '';
	let sortColumn = 'count';
	let sortDirection = 'desc';
	let currentPage = 1;
	let itemsPerPage = 20;
	
	let networkGraph = { nodes: [], links: [] };
	let pulsePhase = 0;
	let dataFlowRate = 0;
	let quantumEntanglement = 0;
	
	let animationFrames = {
		main: null
	};
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			data = await response.json();
			loading = false;
			initializeVisualizations();
			startAnimations();
		} catch (err) {
			console.error('Source sync failed:', err);
			loading = false;
		}
	});
	
	onDestroy(() => {
		Object.values(animationFrames).forEach(frame => {
			if (frame) cancelAnimationFrame(frame);
		});
	});
	
	function initializeVisualizations() {
		if (!data.source_intelligence) return;
		
		const sources = Object.entries(data.source_intelligence);
		
		networkGraph.nodes = sources.slice(0, 30).map(([name, count], i) => ({
			id: name,
			value: count,
			x: Math.cos(i * Math.PI * 2 / 30) * 200 + 250,
			y: Math.sin(i * Math.PI * 2 / 30) * 200 + 250,
			vx: (Math.random() - 0.5) * 2,
			vy: (Math.random() - 0.5) * 2
		}));
		
		networkGraph.nodes.forEach((node, i) => {
			for (let j = 0; j < 3; j++) {
				const target = networkGraph.nodes[Math.floor(Math.random() * networkGraph.nodes.length)];
				if (target && target.id !== node.id) {
					networkGraph.links.push({
						source: node.id,
						target: target.id,
						strength: Math.random(),
						active: Math.random() > 0.5
					});
				}
			}
		});
	}
	
	function startAnimations() {
		let time = 0;
		
		function animate() {
			time += 0.016;
			
			pulsePhase = (pulsePhase + 0.02) % (Math.PI * 2);
			dataFlowRate = 50 + Math.sin(time * 0.5) * 30;
			quantumEntanglement = Math.abs(Math.sin(time * 0.3)) * 100;
			
			networkGraph.nodes.forEach(node => {
				node.vx *= 0.99;
				node.vy *= 0.99;
				
				const dx = 250 - node.x;
				const dy = 250 - node.y;
				node.vx += dx * 0.001;
				node.vy += dy * 0.001;
				
				networkGraph.nodes.forEach(other => {
					if (other.id !== node.id) {
						const dx = node.x - other.x;
						const dy = node.y - other.y;
						const dist = Math.sqrt(dx * dx + dy * dy);
						if (dist < 100 && dist > 0) {
							node.vx += (dx / dist) * 2;
							node.vy += (dy / dist) * 2;
						}
					}
				});
				
				node.x += node.vx;
				node.y += node.vy;
				
				node.x = Math.max(50, Math.min(450, node.x));
				node.y = Math.max(50, Math.min(450, node.y));
			});
			
			animationFrames.main = requestAnimationFrame(animate);
		}
		animate();
	}
	
	$: sources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => {
				if (sortColumn === 'name') {
					return sortDirection === 'asc' ? 
						a[0].localeCompare(b[0]) : b[0].localeCompare(a[0]);
				}
				return sortDirection === 'asc' ? a[1] - b[1] : b[1] - a[1];
			}) : [];
	
	$: paginatedSources = sources.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(sources.length / itemsPerPage);
	$: totalHosts = sources.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = sources.length > 0 ? Math.max(...sources.map(([,c]) => c)) : 1;
	$: avgHosts = sources.length > 0 ? Math.round(totalHosts / sources.length) : 0;
	
	function sortTable(column) {
		if (sortColumn === column) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = column;
			sortDirection = 'desc';
		}
	}
	
	async function drillDownSource(source, count) {
		selectedSource = { source, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			sourceDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Source drill-down failed:', err);
			sourceDetails = [];
			loading = false;
		}
	}
	
	function closeDetails() {
		selectedSource = null;
		sourceDetails = [];
	}
	
	function getSourceLevel(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 80) return { level: 'QUANTUM', color: '#FF00FF' };
		if (percentage >= 60) return { level: 'NEURAL', color: '#00FFFF' };
		if (percentage >= 40) return { level: 'PLASMA', color: '#BD93F9' };
		if (percentage >= 20) return { level: 'ENERGY', color: '#FF00FF' };
		return { level: 'PARTICLE', color: '#00FFFF' };
	}
	
	function formatNumber(num) {
		if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
		if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
		return num.toString();
	}
</script>

<div class="interface">
	<div class="metrics-bar">
		<div class="metric-card">
			<div class="metric-info">
				<div class="metric-value">{sources.length}</div>
				<div class="metric-label">TOTAL SOURCES</div>
			</div>
		</div>
		
		<div class="metric-card">
			<div class="metric-info">
				<div class="metric-value">{formatNumber(totalHosts)}</div>
				<div class="metric-label">TOTAL HOSTS</div>
			</div>
		</div>
		
		<div class="metric-card">
			<div class="metric-info">
				<div class="metric-value">{formatNumber(avgHosts)}</div>
				<div class="metric-label">AVG PER SOURCE</div>
			</div>
		</div>
		
		<div class="metric-card">
			<div class="metric-info">
				<div class="metric-value">{dataFlowRate.toFixed(0)}%</div>
				<div class="metric-label">DATA FLOW RATE</div>
			</div>
		</div>
		
		<div class="metric-card">
			<div class="metric-info">
				<div class="metric-value">{quantumEntanglement.toFixed(0)}%</div>
				<div class="metric-label">QUANTUM STATE</div>
			</div>
		</div>
	</div>
	
	<div class="main-layout">
		<div class="left-panel">
			<div class="graph-container">
				<h3 class="graph-title">NETWORK TOPOLOGY</h3>
				<svg viewBox="0 0 500 500" class="network-graph">
					{#each networkGraph.links as link}
						{@const source = networkGraph.nodes.find(n => n.id === link.source)}
						{@const target = networkGraph.nodes.find(n => n.id === link.target)}
						{#if source && target}
							<line x1="{source.x}" y1="{source.y}" 
								  x2="{target.x}" y2="{target.y}"
								  stroke="{link.active ? '#00FFFF' : '#444444'}"
								  stroke-width="{link.strength * 2}"
								  opacity="{link.active ? 0.6 : 0.2}">
								{#if link.active}
									<animate attributeName="stroke-opacity"
											 values="0.2;0.8;0.2" dur="2s" repeatCount="indefinite"/>
								{/if}
							</line>
						{/if}
					{/each}
					
					{#each networkGraph.nodes as node}
						<g class="node" transform="translate({node.x}, {node.y})"
						   on:click={() => drillDownSource(node.id, node.value)}>
							<circle r="{Math.sqrt(node.value / maxHosts) * 30 + 5}"
									fill="#BD93F9"
									opacity="0.8"/>
							<circle r="{Math.sqrt(node.value / maxHosts) * 30 + 5}"
									fill="none"
									stroke="#FFFFFF"
									stroke-width="1"
									opacity="0.5"/>
							<text text-anchor="middle" dy="4" 
								  font-size="8" fill="#FFFFFF">
								{formatNumber(node.value)}
							</text>
						</g>
					{/each}
				</svg>
			</div>
		</div>
		
		<div class="center-panel">
			<div class="table-container">
				<div class="table-header">
					<h2 class="table-title">SOURCE QUANTUM MATRIX</h2>
					<div class="table-controls">
						<input type="text" 
							   bind:value={searchTerm}
							   placeholder="SEARCH SOURCES..."
							   class="search-input"/>
						<div class="pagination">
							<button on:click={() => currentPage = Math.max(1, currentPage - 1)}
									disabled={currentPage === 1}>PREV</button>
							<span class="page-info">{currentPage} / {totalPages}</span>
							<button on:click={() => currentPage = Math.min(totalPages, currentPage + 1)}
									disabled={currentPage === totalPages}>NEXT</button>
						</div>
					</div>
				</div>
				
				{#if selectedSource}
					<div class="detail-view">
						<div class="detail-header">
							<h3>{selectedSource.source}</h3>
							<button class="close-btn" on:click={closeDetails}>CLOSE</button>
						</div>
						<div class="detail-content">
							<table class="detail-table">
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
											<td class="hostname">{host.host}</td>
											<td>{host.region}</td>
											<td>{host.country}</td>
											<td>{host.data_center}</td>
											<td>{host.infrastructure_type}</td>
											<td><span class="status {host.present_in_cmdb === 'Yes' ? 'active' : 'inactive'}">O</span></td>
											<td><span class="status {host.tanium_coverage === 'Tanium' ? 'active' : 'inactive'}">O</span></td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				{:else}
					<table class="data-table">
						<thead>
							<tr>
								<th class="sortable" on:click={() => sortTable('rank')}>
									RANK {sortColumn === 'rank' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
								</th>
								<th class="sortable" on:click={() => sortTable('name')}>
									SOURCE {sortColumn === 'name' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
								</th>
								<th class="sortable" on:click={() => sortTable('count')}>
									HOSTS {sortColumn === 'count' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
								</th>
								<th>LEVEL</th>
								<th>UTILIZATION</th>
								<th>STATUS</th>
								<th>ACTIONS</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedSources as [source, count], i}
								{@const level = getSourceLevel(count)}
								{@const utilization = (count / maxHosts) * 100}
								<tr class="data-row">
									<td class="rank">#{(currentPage - 1) * itemsPerPage + i + 1}</td>
									<td class="source-name">{source}</td>
									<td class="host-count" style="color: {level.color}">
										{formatNumber(count)}
									</td>
									<td>
										<span class="level-badge" style="background: {level.color}20; color: {level.color}">
											{level.level}
										</span>
									</td>
									<td>
										<div class="utilization-bar">
											<div class="utilization-fill" 
												 style="width: {utilization}%; background: linear-gradient(90deg, {level.color}40, {level.color})">
											</div>
											<span class="utilization-text">{utilization.toFixed(1)}%</span>
										</div>
									</td>
									<td>
										<span class="status-indicator {utilization > 80 ? 'critical' : utilization > 60 ? 'warning' : 'normal'}">
											{utilization > 80 ? '◆' : utilization > 60 ? '◇' : '○'}
										</span>
									</td>
									<td>
										<button class="action-btn" on:click={() => drillDownSource(source, count)}>
											ANALYZE
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		padding: 1rem;
		overflow: hidden;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.metrics-bar {
		display: flex;
		gap: 1rem;
		height: 80px;
		flex-shrink: 0;
	}
	
	.metric-card {
		flex: 1;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		align-items: center;
		gap: 1rem;
		position: relative;
		overflow: hidden;
	}
	
	.metric-info {
		flex: 1;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: 400;
		color: #00FFFF;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.main-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 400px 1fr;
		gap: 1rem;
		min-height: 0;
	}
	
	.left-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
	}
	
	.center-panel {
		display: flex;
		flex-direction: column;
		min-height: 0;
	}
	
	.graph-container {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 10px;
		padding: 1rem;
	}
	
	.graph-title {
		margin: 0 0 0.5rem 0;
		font-size: 0.8rem;
		color: #00FFFF;
		letter-spacing: 0.1em;
		font-weight: 400;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.table-container {
		flex: 1;
		background: rgba(0, 0, 0, 0.8);
		border: 2px solid rgba(0, 255, 255, 0.3);
		border-radius: 10px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: 0 0 30px rgba(0, 255, 255, 0.2);
	}
	
	.table-header {
		padding: 1rem;
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.1), transparent);
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
	}
	
	.table-title {
		margin: 0 0 0.5rem 0;
		font-size: 1.2rem;
		color: #00FFFF;
		letter-spacing: 0.2em;
		font-weight: 300;
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
		font-family: 'JetBrains Mono', monospace;
	}
	
	.table-controls {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.search-input {
		padding: 0.5rem 1rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 255, 0.3);
		color: #00FFFF;
		font-family: 'JetBrains Mono', monospace;
		border-radius: 5px;
		width: 300px;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #00FFFF;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}
	
	.pagination {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.pagination button {
		padding: 0.5rem 1rem;
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid #00FFFF;
		color: #00FFFF;
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.pagination button:hover:not(:disabled) {
		background: rgba(0, 255, 255, 0.3);
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}
	
	.pagination button:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	
	.page-info {
		color: #00FFFF;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.data-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.data-table thead {
		background: rgba(0, 255, 255, 0.05);
		position: sticky;
		top: 0;
		z-index: 10;
	}
	
	.data-table th {
		padding: 1rem;
		text-align: left;
		font-size: 0.8rem;
		color: #00FFFF;
		letter-spacing: 0.1em;
		font-weight: 400;
		border-bottom: 2px solid rgba(0, 255, 255, 0.3);
		white-space: nowrap;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.data-table th.sortable {
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.data-table th.sortable:hover {
		background: rgba(0, 255, 255, 0.1);
		text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
	}
	
	.data-table tbody {
		overflow-y: auto;
	}
	
	.data-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.3s;
		cursor: pointer;
	}
	
	.data-row:hover {
		background: rgba(0, 255, 255, 0.05);
		transform: translateX(5px);
	}
	
	.data-table td {
		padding: 0.8rem 1rem;
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.9);
		font-family: 'JetBrains Mono', monospace;
	}
	
	.rank {
		color: #FF00FF;
		font-weight: 400;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.source-name {
		font-family: 'JetBrains Mono', monospace;
		color: #FFFFFF;
	}
	
	.host-count {
		font-family: 'JetBrains Mono', monospace;
		font-weight: 400;
	}
	
	.level-badge {
		padding: 0.3rem 0.6rem;
		border-radius: 5px;
		font-size: 0.7rem;
		font-weight: 400;
		letter-spacing: 0.05em;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.utilization-bar {
		position: relative;
		width: 100px;
		height: 20px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 10px;
		overflow: hidden;
	}
	
	.utilization-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.utilization-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 0.7rem;
		color: #FFFFFF;
		font-weight: 400;
		text-shadow: 0 0 3px #000000;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.status-indicator {
		font-size: 1.2rem;
		display: inline-block;
		filter: drop-shadow(0 0 5px currentColor);
	}
	
	.status-indicator.normal { color: #00FFFF; }
	.status-indicator.warning { color: #BD93F9; }
	.status-indicator.critical { color: #FF00FF; }
	
	.action-btn {
		padding: 0.4rem 0.8rem;
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.3));
		border: 1px solid #00FFFF;
		color: #00FFFF;
		font-size: 0.7rem;
		font-weight: 400;
		letter-spacing: 0.1em;
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.action-btn:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.3), rgba(0, 255, 255, 0.5));
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
		transform: scale(1.05);
	}
	
	.detail-view {
		flex: 1;
		padding: 1rem;
		overflow-y: auto;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
	}
	
	.detail-header h3 {
		margin: 0;
		color: #00FFFF;
		font-size: 1.2rem;
		font-family: 'JetBrains Mono', monospace;
		font-weight: 400;
	}
	
	.close-btn {
		padding: 0.5rem 1rem;
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid #FF00FF;
		color: #FF00FF;
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.close-btn:hover {
		background: rgba(255, 0, 255, 0.3);
		box-shadow: 0 0 10px rgba(255, 0, 255, 0.5);
	}
	
	.detail-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.detail-table th {
		padding: 0.5rem;
		background: rgba(0, 255, 255, 0.1);
		color: #00FFFF;
		font-size: 0.7rem;
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		font-family: 'JetBrains Mono', monospace;
		font-weight: 400;
	}
	
	.detail-table td {
		padding: 0.5rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		font-family: 'JetBrains Mono', monospace;
	}
	
	.hostname {
		font-family: 'JetBrains Mono', monospace;
		color: #00FFFF;
		font-size: 0.7rem;
	}
	
	.status {
		font-size: 0.8rem;
	}
	
	.status.active { color: #00FFFF; }
	.status.inactive { color: #FF00FF; }
	
	.network-graph, .heatmap {
		width: 100%;
		height: auto;
	}
	
	.node {
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.node:hover {
		transform: scale(1.2);
	}
	
	::-webkit-scrollbar {
		width: 8px;
	}
	
	::-webkit-scrollbar-track {
		background: #000000;
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb {
		background: linear-gradient(180deg, #00FFFF, #FF00FF);
		border-radius: 4px;
	}
</style>