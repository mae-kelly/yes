<!-- BusinessUnitMetrics.svelte - Division Host Distribution -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedDivision = null;
	let divisionDetails = [];
	let searchTerm = '';
	
	// Animation states
	let animationFrame = null;
	let rotationDegree = 0;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/business_unit_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Division metrics error:', err);
			loading = false;
		}
		
		// Start animations
		const animate = () => {
			rotationDegree = (rotationDegree + 0.2) % 360;
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});

	$: divisions = data.business_intelligence ? 
		Object.entries(data.business_intelligence)
			.filter(([division]) => division.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = divisions.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = divisions.length > 0 ? Math.max(...divisions.map(([,c]) => c)) : 1;
	$: avgHostsPerDivision = divisions.length > 0 ? Math.round(totalHosts / divisions.length) : 0;
	
	// Key metrics
	$: divisionCount = divisions.length;
	$: topDivision = divisions[0] || ['N/A', 0];
	$: concentration = topDivision[1] > 0 ? ((topDivision[1] / totalHosts) * 100).toFixed(1) : 0;
	
	// Top performers
	$: topFive = divisions.slice(0, 5);
	$: bottomFive = divisions.slice(-5).reverse();

	async function drillDownDivision(division, count) {
		selectedDivision = { division, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(division)}`);
			let result = await response.json();
			divisionDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Division drill-down error:', err);
			divisionDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedDivision = null;
		divisionDetails = [];
	}
	
	function getDivisionStatus(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#BD93F9' };
		if (percentage >= 50) return { level: 'HIGH', color: '#8BE9FD' };
		if (percentage >= 25) return { level: 'MEDIUM', color: '#50FA7B' };
		return { level: 'LOW', color: '#FFB86C' };
	}
	
	function getDivisionSize(count) {
		if (count > 10000) return 'ENTERPRISE';
		if (count > 5000) return 'LARGE';
		if (count > 1000) return 'MEDIUM';
		if (count > 100) return 'SMALL';
		return 'MINIMAL';
	}
</script>

<div class="division-interface">
	<!-- Top Metrics -->
	<div class="metrics-header">
		<div class="metric-card">
			<div class="metric-icon">📊</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #BD93F9">{divisionCount}</div>
				<div class="metric-label">DIVISIONS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">💻</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #8BE9FD">{totalHosts.toLocaleString()}</div>
				<div class="metric-label">TOTAL HOSTS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">🏢</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #50FA7B; font-size: 1.2rem">
					{topDivision[0].substring(0, 25).toUpperCase()}
				</div>
				<div class="metric-label">TOP DIVISION</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📈</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FFB86C">{concentration}%</div>
				<div class="metric-label">TOP CONCENTRATION</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">⚖️</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FF79C6">{avgHostsPerDivision.toLocaleString()}</div>
				<div class="metric-label">AVG HOSTS/DIV</div>
			</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content-layout">
		<!-- Left: Organizational Chart -->
		<div class="org-panel">
			<div class="panel-header">
				<h2>ORGANIZATIONAL STRUCTURE</h2>
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="Search divisions..."
					   class="search-input"/>
			</div>
			
			{#if loading && !selectedDivision}
				<div class="loading-state">
					<div class="org-loader">
						<div class="org-node node-1"></div>
						<div class="org-node node-2"></div>
						<div class="org-node node-3"></div>
						<div class="org-node node-4"></div>
					</div>
					<p>ANALYZING ORGANIZATIONAL STRUCTURE...</p>
				</div>
			{:else if selectedDivision}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedDivision.division.toUpperCase()}</h3>
							<div class="division-stats">
								<span>{selectedDivision.count.toLocaleString()} HOSTS</span>
								<span>•</span>
								<span>{((selectedDivision.count / totalHosts) * 100).toFixed(2)}% OF TOTAL</span>
								<span>•</span>
								<span>{getDivisionSize(selectedDivision.count)} DIVISION</span>
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
								{#each divisionDetails as host}
									<tr>
										<td class="hostname">{host.host}</td>
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
								<div class="node-icon">🏢</div>
								<div class="node-label">ORGANIZATION</div>
								<div class="node-count">{totalHosts.toLocaleString()} HOSTS</div>
							</div>
						</div>
						<div class="tree-branches">
							{#each topFive as [division, count], i}
								{@const status = getDivisionStatus(count)}
								{@const percentage = ((count / totalHosts) * 100).toFixed(1)}
								<div class="branch-container">
									<div class="branch-line"></div>
									<div class="division-node" 
										 style="border-color: {status.color}"
										 on:click={() => drillDownDivision(division, count)}>
										<div class="node-header" style="background: {status.color}20">
											<span class="node-rank">#{i + 1}</span>
										</div>
										<div class="node-body">
											<div class="node-name">{division.substring(0, 20).toUpperCase()}</div>
											<div class="node-metrics">
												<span class="node-hosts" style="color: {status.color}">
													{count.toLocaleString()}
												</span>
												<span class="node-percent">{percentage}%</span>
											</div>
											<div class="node-bar">
												<div class="bar-fill" style="width: {percentage}%; background: {status.color}"></div>
											</div>
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
					
					<!-- Bubble Chart -->
					<div class="bubble-chart">
						<svg viewBox="0 0 400 300">
							{#each divisions.slice(0, 15) as [division, count], i}
								{@const radius = Math.sqrt(count / maxHosts) * 40}
								{@const x = 50 + (i % 5) * 75}
								{@const y = 50 + Math.floor(i / 5) * 80}
								{@const status = getDivisionStatus(count)}
								
								<g class="bubble-group" on:click={() => drillDownDivision(division, count)}>
									<circle cx="{x}" cy="{y}" r="{radius}" 
											fill="{status.color}" opacity="0.3"/>
									<circle cx="{x}" cy="{y}" r="{radius * 0.7}" 
											fill="{status.color}" opacity="0.6"/>
									<text x="{x}" y="{y}" text-anchor="middle" 
										  fill="#FFFFFF" font-size="9" font-weight="600">
										{count.toLocaleString()}
									</text>
								</g>
							{/each}
						</svg>
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Middle: Analytics -->
		<div class="analytics-panel">
			<!-- Distribution Chart -->
			<div class="chart-box">
				<h3>HOST DISTRIBUTION BY DIVISION</h3>
				<div class="distribution-bars">
					{#each topFive as [division, count], i}
						{@const percentage = (count / maxHosts) * 100}
						{@const status = getDivisionStatus(count)}
						<div class="dist-item" on:click={() => drillDownDivision(division, count)}>
							<div class="dist-rank">#{i + 1}</div>
							<div class="dist-name">{division.substring(0, 12).toUpperCase()}</div>
							<div class="dist-bar">
								<div class="dist-fill" 
									 style="width: {percentage}%; 
											background: linear-gradient(90deg, {status.color}40, {status.color})">
									<span class="dist-value">{count.toLocaleString()}</span>
								</div>
							</div>
							<div class="dist-percent">{((count/totalHosts)*100).toFixed(1)}%</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Size Distribution -->
			<div class="chart-box">
				<h3>DIVISION SIZE DISTRIBUTION</h3>
				<div class="size-chart">
					{@const sizeGroups = divisions.reduce((acc, [div, count]) => {
						const size = getDivisionSize(count);
						acc[size] = (acc[size] || 0) + 1;
						return acc;
					}, {})}
					{#each Object.entries(sizeGroups) as [size, count], i}
						{@const colors = ['#BD93F9', '#8BE9FD', '#50FA7B', '#FFB86C', '#FF79C6']}
						<div class="size-item">
							<div class="size-label">{size}</div>
							<div class="size-count" style="color: {colors[i % 5]}">{count}</div>
							<div class="size-bar">
								<div class="size-fill" 
									 style="height: {(count / divisionCount) * 100}%; 
											background: {colors[i % 5]}">
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
						<span class="coverage-label">Divisions with >1000 hosts</span>
						<span class="coverage-value" style="color: #BD93F9">
							{divisions.filter(([_, c]) => c > 1000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Divisions with >5000 hosts</span>
						<span class="coverage-value" style="color: #8BE9FD">
							{divisions.filter(([_, c]) => c > 5000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Divisions with >10000 hosts</span>
						<span class="coverage-value" style="color: #50FA7B">
							{divisions.filter(([_, c]) => c > 10000).length}
						</span>
					</div>
				</div>
			</div>
		</div>
		
		<!-- Right: Division List -->
		<div class="list-panel">
			<div class="panel-header">
				<h3>ALL DIVISIONS</h3>
				<span class="division-count">{divisions.length} TOTAL</span>
			</div>
			<div class="division-list">
				<table class="divisions-table">
					<thead>
						<tr>
							<th>#</th>
							<th>DIVISION</th>
							<th>HOSTS</th>
							<th>SIZE</th>
							<th>STATUS</th>
						</tr>
					</thead>
					<tbody>
						{#each divisions as [division, count], i}
							{@const status = getDivisionStatus(count)}
							{@const size = getDivisionSize(count)}
							<tr on:click={() => drillDownDivision(division, count)}>
								<td class="rank">{i + 1}</td>
								<td class="division-name">
									<span class="status-indicator" style="background: {status.color}"></span>
									{division.substring(0, 25).toUpperCase()}
								</td>
								<td class="host-count" style="color: {status.color}">
									{count.toLocaleString()}
								</td>
								<td>
									<span class="size-badge" style="color: {status.color}">
										{size}
									</span>
								</td>
								<td>
									<span class="status-badge" style="color: {status.color}; border-color: {status.color}">
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
	.division-interface {
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
	}
	
	.metric-card {
		flex: 1;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		gap: 1rem;
		align-items: center;
	}
	
	.metric-icon {
		font-size: 2rem;
	}
	
	.metric-content {
		flex: 1;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
		margin-bottom: 0.25rem;
	}
	
	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
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
	
	.org-visualization {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	/* Tree Container */
	.tree-container {
		flex: 1;
	}
	
	.tree-root {
		display: flex;
		justify-content: center;
		margin-bottom: 2rem;
	}
	
	.root-node {
		background: rgba(189, 147, 249, 0.1);
		border: 2px solid #BD93F9;
		border-radius: 10px;
		padding: 1rem 2rem;
		text-align: center;
	}
	
	.node-icon {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}
	
	.node-label {
		font-size: 0.8rem;
		color: #BD93F9;
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
		position: relative;
	}
	
	.branch-container {
		position: relative;
		flex: 1;
		max-width: 150px;
	}
	
	.branch-line {
		position: absolute;
		top: -2rem;
		left: 50%;
		width: 1px;
		height: 2rem;
		background: rgba(139, 233, 253, 0.3);
	}
	
	.division-node {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.3s ease;
		overflow: hidden;
	}
	
	.division-node:hover {
		transform: scale(1.05);
		background: rgba(139, 233, 253, 0.05);
	}
	
	.node-header {
		padding: 0.3rem;
		text-align: center;
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.node-rank {
		color: #FFFFFF;
	}
	
	.node-body {
		padding: 0.5rem;
	}
	
	.node-name {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.9);
		margin-bottom: 0.3rem;
		text-align: center;
	}
	
	.node-metrics {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.3rem;
		font-size: 0.7rem;
	}
	
	.node-hosts {
		font-weight: 700;
		font-family: 'Courier New', monospace;
	}
	
	.node-percent {
		color: rgba(255, 255, 255, 0.6);
	}
	
	.node-bar {
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	/* Bubble Chart */
	.bubble-chart {
		height: 180px;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 8px;
		padding: 0.5rem;
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
		transform: scale(1.1);
	}
	
	/* Analytics Panel */
	.analytics-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chart-box {
		flex: 1;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
	}
	
	.chart-box h3 {
		margin: 0 0 1rem 0;
		font-size: 0.75rem;
		color: #8BE9FD;
		font-weight: 300;
		letter-spacing: 0.1em;
	}
	
	.distribution-bars {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.dist-item {
		display: grid;
		grid-template-columns: 25px 100px 1fr 45px;
		gap: 0.5rem;
		align-items: center;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	.dist-item:hover {
		transform: translateX(2px);
	}
	
	.dist-rank {
		font-size: 0.65rem;
		color: #BD93F9;
		font-weight: 600;
	}
	
	.dist-name {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.dist-bar {
		height: 18px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.dist-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.4rem;
		transition: width 0.5s ease;
	}
	
	.dist-value {
		font-size: 0.6rem;
		color: #FFFFFF;
		font-weight: 600;
	}
	
	.dist-percent {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		text-align: right;
	}
	
	/* Size Chart */
	.size-chart {
		display: flex;
		align-items: flex-end;
		justify-content: space-around;
		height: 100px;
	}
	
	.size-item {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.3rem;
	}
	
	.size-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		writing-mode: vertical-lr;
		text-align: center;
	}
	
	.size-count {
		font-size: 0.9rem;
		font-weight: 700;
	}
	
	.size-bar {
		width: 30px;
		height: 60px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px 4px 0 0;
		display: flex;
		align-items: flex-end;
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
		gap: 0.75rem;
	}
	
	.coverage-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 6px;
	}
	
	.coverage-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.coverage-value {
		font-size: 1rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
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
	
	.division-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.division-list {
		flex: 1;
		overflow-y: auto;
	}
	
	.divisions-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.divisions-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.9);
		z-index: 10;
	}
	
	.divisions-table th {
		padding: 0.5rem;
		text-align: left;
		font-size: 0.6rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.divisions-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.divisions-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.05);
	}
	
	.divisions-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank {
		color: #BD93F9;
		font-weight: 600;
		font-size: 0.65rem;
	}
	
	.division-name {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.65rem;
	}
	
	.status-indicator {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.host-count {
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.size-badge {
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}
	
	.status-badge {
		font-size: 0.6rem;
		padding: 0.15rem 0.3rem;
		border: 1px solid;
		border-radius: 4px;
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
	
	.division-stats {
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
	
	.hosts-container {
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
	
	.status-dot {
		font-size: 0.8rem;
	}
	
	.status-dot.active {
		color: #50FA7B;
	}
	
	.status-dot.inactive {
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
	
	.org-loader {
		position: relative;
		width: 100px;
		height: 100px;
	}
	
	.org-node {
		position: absolute;
		width: 20px;
		height: 20px;
		background: linear-gradient(135deg, #BD93F9, #8BE9FD);
		border-radius: 50%;
		animation: nodeFloat 2s ease-in-out infinite;
	}
	
	.node-1 {
		top: 0;
		left: 40px;
	}
	
	.node-2 {
		top: 30px;
		left: 10px;
		animation-delay: 0.5s;
	}
	
	.node-3 {
		top: 30px;
		left: 70px;
		animation-delay: 1s;
	}
	
	.node-4 {
		top: 70px;
		left: 40px;
		animation-delay: 1.5s;
	}
	
	@keyframes nodeFloat {
		0%, 100% { transform: scale(1); opacity: 0.5; }
		50% { transform: scale(1.2); opacity: 1; }
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
</style>