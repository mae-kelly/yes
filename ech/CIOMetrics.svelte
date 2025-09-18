<!-- CIOMetrics.svelte - Executive Host Distribution -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedExecutive = null;
	let executiveDetails = [];
	let searchTerm = '';
	
	// Animation states
	let animationFrame = null;
	let pulseValue = 0;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/cio_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Executive metrics error:', err);
			loading = false;
		}
		
		// Start animations
		const animate = () => {
			pulseValue = (Math.sin(Date.now() * 0.001) + 1) / 2;
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});

	$: executives = data.operative_intelligence ? 
		Object.entries(data.operative_intelligence)
			.filter(([exec]) => exec.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = executives.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = executives.length > 0 ? Math.max(...executives.map(([,c]) => c)) : 1;
	$: avgHostsPerExec = executives.length > 0 ? Math.round(totalHosts / executives.length) : 0;
	
	// Key metrics
	$: executiveCount = executives.length;
	$: topExecutive = executives[0] || ['N/A', 0];
	$: concentration = topExecutive[1] > 0 ? ((topExecutive[1] / totalHosts) * 100).toFixed(1) : 0;
	
	// Top performers
	$: topTen = executives.slice(0, 10);

	async function drillDownExecutive(executive, count) {
		selectedExecutive = { executive, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(executive)}`);
			let result = await response.json();
			executiveDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Executive drill-down error:', err);
			executiveDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedExecutive = null;
		executiveDetails = [];
	}
	
	function getExecutiveLevel(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'STRATEGIC', color: '#BD93F9' };
		if (percentage >= 50) return { level: 'SENIOR', color: '#8BE9FD' };
		if (percentage >= 25) return { level: 'MID-LEVEL', color: '#50FA7B' };
		return { level: 'JUNIOR', color: '#FFB86C' };
	}
	
	function getSpanOfControl(count) {
		if (count > 10000) return 'ENTERPRISE-WIDE';
		if (count > 5000) return 'MULTI-DIVISION';
		if (count > 1000) return 'DIVISIONAL';
		if (count > 100) return 'DEPARTMENTAL';
		return 'TEAM';
	}
</script>

<div class="executive-interface">
	<!-- Top Metrics -->
	<div class="metrics-bar">
		<div class="metric-tile">
			<div class="metric-icon">👔</div>
			<div class="metric-data">
				<div class="metric-value" style="color: #BD93F9">{executiveCount}</div>
				<div class="metric-label">EXECUTIVES</div>
			</div>
		</div>
		<div class="metric-tile">
			<div class="metric-icon">💻</div>
			<div class="metric-data">
				<div class="metric-value" style="color: #8BE9FD">{totalHosts.toLocaleString()}</div>
				<div class="metric-label">MANAGED HOSTS</div>
			</div>
		</div>
		<div class="metric-tile">
			<div class="metric-icon">👑</div>
			<div class="metric-data">
				<div class="metric-value" style="color: #50FA7B; font-size: 1.2rem">
					{topExecutive[0].substring(0, 25).toUpperCase()}
				</div>
				<div class="metric-label">TOP EXECUTIVE</div>
			</div>
		</div>
		<div class="metric-tile">
			<div class="metric-icon">📊</div>
			<div class="metric-data">
				<div class="metric-value" style="color: #FFB86C">{concentration}%</div>
				<div class="metric-label">TOP CONCENTRATION</div>
			</div>
		</div>
		<div class="metric-tile">
			<div class="metric-icon">⚖️</div>
			<div class="metric-data">
				<div class="metric-value" style="color: #FF79C6">{avgHostsPerExec.toLocaleString()}</div>
				<div class="metric-label">AVG HOSTS/EXEC</div>
			</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="main-layout">
		<!-- Left: Leadership Hierarchy -->
		<div class="hierarchy-panel">
			<div class="panel-header">
				<h2>EXECUTIVE HIERARCHY</h2>
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="Search executives..."
					   class="search-input"/>
			</div>
			
			{#if loading && !selectedExecutive}
				<div class="loading-state">
					<div class="hierarchy-loader">
						<div class="level level-1"></div>
						<div class="level level-2"></div>
						<div class="level level-3"></div>
					</div>
					<p>ANALYZING LEADERSHIP STRUCTURE...</p>
				</div>
			{:else if selectedExecutive}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedExecutive.executive.toUpperCase()}</h3>
							<div class="executive-stats">
								<span>{selectedExecutive.count.toLocaleString()} HOSTS</span>
								<span>•</span>
								<span>{((selectedExecutive.count / totalHosts) * 100).toFixed(2)}% OF TOTAL</span>
								<span>•</span>
								<span>{getSpanOfControl(selectedExecutive.count)}</span>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="hosts-grid">
						<table class="hosts-table">
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>DIVISION</th>
									<th>TYPE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each executiveDetails as host}
									<tr>
										<td class="hostname">{host.host}</td>
										<td>{host.region || 'UNKNOWN'}</td>
										<td>{host.country || 'UNKNOWN'}</td>
										<td>{host.business_unit || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
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
				<div class="hierarchy-visualization">
					<!-- Leadership Pyramid -->
					<div class="pyramid-container">
						{#each topTen.slice(0, 5) as [executive, count], i}
							{@const level = getExecutiveLevel(count)}
							{@const percentage = ((count / totalHosts) * 100).toFixed(1)}
							<div class="pyramid-level" style="width: {100 - i * 15}%">
								<div class="exec-card" 
									 style="background: {level.color}15; border-color: {level.color}"
									 on:click={() => drillDownExecutive(executive, count)}>
									<div class="exec-rank">#{i + 1}</div>
									<div class="exec-info">
										<div class="exec-name">{executive.substring(0, 25).toUpperCase()}</div>
										<div class="exec-metrics">
											<span class="exec-hosts" style="color: {level.color}">
												{count.toLocaleString()} HOSTS
											</span>
											<span class="exec-percent">{percentage}%</span>
										</div>
									</div>
									<div class="exec-level" style="background: {level.color}20; color: {level.color}">
										{level.level}
									</div>
								</div>
							</div>
						{/each}
					</div>
					
					<!-- Network Graph -->
					<div class="network-graph">
						<svg viewBox="0 0 400 200">
							<!-- Central node -->
							<circle cx="200" cy="100" r="20" fill="#BD93F9" opacity="0.6"/>
							<text x="200" y="105" text-anchor="middle" fill="#FFFFFF" font-size="10" font-weight="600">
								LEADERSHIP
							</text>
							
							<!-- Executive nodes -->
							{#each topTen.slice(0, 8) as [executive, count], i}
								{@const angle = (i / 8) * Math.PI * 2}
								{@const radius = 60 + (count / maxHosts) * 40}
								{@const x = 200 + Math.cos(angle) * radius}
								{@const y = 100 + Math.sin(angle) * radius}
								{@const level = getExecutiveLevel(count)}
								
								<g class="exec-node" on:click={() => drillDownExecutive(executive, count)}>
									<line x1="200" y1="100" x2="{x}" y2="{y}" 
										  stroke="{level.color}" stroke-width="1" opacity="0.3"/>
									<circle cx="{x}" cy="{y}" r="{10 + (count/maxHosts) * 10}" 
											fill="{level.color}" opacity="0.6"/>
									<text x="{x}" y="{y + 3}" text-anchor="middle" 
										  fill="#FFFFFF" font-size="7" font-weight="600">
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
		<div class="analytics-section">
			<!-- Span of Control -->
			<div class="analytics-card">
				<h3>SPAN OF CONTROL</h3>
				<div class="control-chart">
					{#each topTen.slice(0, 6) as [executive, count], i}
						{@const percentage = (count / maxHosts) * 100}
						{@const level = getExecutiveLevel(count)}
						{@const span = getSpanOfControl(count)}
						<div class="control-item" on:click={() => drillDownExecutive(executive, count)}>
							<div class="control-name">{executive.substring(0, 15).toUpperCase()}</div>
							<div class="control-bar">
								<div class="control-fill" 
									 style="width: {percentage}%; background: {level.color}">
									<span class="control-value">{count.toLocaleString()}</span>
								</div>
							</div>
							<div class="control-span" style="color: {level.color}">{span}</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Level Distribution -->
			<div class="analytics-card">
				<h3>EXECUTIVE LEVELS</h3>
				<div class="level-distribution">
					{@const levelGroups = executives.reduce((acc, [exec, count]) => {
						const level = getExecutiveLevel(count).level;
						acc[level] = (acc[level] || 0) + 1;
						return acc;
					}, {})}
					<div class="level-chart">
						{#each Object.entries(levelGroups) as [level, count], i}
							{@const colors = ['#BD93F9', '#8BE9FD', '#50FA7B', '#FFB86C']}
							{@const percentage = (count / executiveCount) * 100}
							<div class="level-item">
								<div class="level-name">{level}</div>
								<div class="level-bar">
									<div class="level-fill" 
										 style="width: {percentage}%; background: {colors[i % 4]}">
									</div>
								</div>
								<div class="level-count" style="color: {colors[i % 4]}">{count}</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
			
			<!-- Coverage Metrics -->
			<div class="analytics-card">
				<h3>COVERAGE ANALYSIS</h3>
				<div class="coverage-grid">
					<div class="coverage-stat">
						<div class="coverage-number" style="color: #BD93F9">
							{executives.filter(([_, c]) => c > 5000).length}
						</div>
						<div class="coverage-label">EXECUTIVES WITH >5K HOSTS</div>
					</div>
					<div class="coverage-stat">
						<div class="coverage-number" style="color: #8BE9FD">
							{executives.filter(([_, c]) => c > 10000).length}
						</div>
						<div class="coverage-label">EXECUTIVES WITH >10K HOSTS</div>
					</div>
					<div class="coverage-stat">
						<div class="coverage-number" style="color: #50FA7B">
							{((topTen.reduce((sum, [_, c]) => sum + c, 0) / totalHosts) * 100).toFixed(0)}%
						</div>
						<div class="coverage-label">TOP 10 COVERAGE</div>
					</div>
				</div>
			</div>
		</div>
		
		<!-- Right: Executive List -->
		<div class="list-panel">
			<div class="panel-header">
				<h3>ALL EXECUTIVES</h3>
				<span class="exec-count">{executives.length} TOTAL</span>
			</div>
			<div class="exec-list">
				<table class="executives-table">
					<thead>
						<tr>
							<th>#</th>
							<th>EXECUTIVE</th>
							<th>HOSTS</th>
							<th>SPAN</th>
							<th>LEVEL</th>
						</tr>
					</thead>
					<tbody>
						{#each executives as [executive, count], i}
							{@const level = getExecutiveLevel(count)}
							{@const span = getSpanOfControl(count)}
							<tr on:click={() => drillDownExecutive(executive, count)}>
								<td class="rank">{i + 1}</td>
								<td class="exec-name">
									<span class="level-dot" style="background: {level.color}"></span>
									{executive.substring(0, 25).toUpperCase()}
								</td>
								<td class="host-count" style="color: {level.color}">
									{count.toLocaleString()}
								</td>
								<td class="span-cell">
									<span class="span-badge" style="color: {level.color}">
										{span.substring(0, 10)}
									</span>
								</td>
								<td>
									<span class="level-badge" 
										  style="background: {level.color}20; 
												 color: {level.color};
												 border: 1px solid {level.color}">
										{level.level}
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
		background: #000000;
		display: flex;
		flex-direction: column;
		padding: 1rem;
		gap: 1rem;
		overflow: hidden;
	}
	
	/* Metrics Bar */
	.metrics-bar {
		display: flex;
		gap: 1rem;
	}
	
	.metric-tile {
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
	
	.metric-data {
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
	
	/* Main Layout */
	.main-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 380px 320px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Hierarchy Panel */
	.hierarchy-panel {
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
	
	.hierarchy-visualization {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	/* Pyramid Container */
	.pyramid-container {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
	}
	
	.pyramid-level {
		display: flex;
		justify-content: center;
	}
	
	.exec-card {
		width: 100%;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid;
		border-radius: 8px;
		padding: 0.75rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.exec-card:hover {
		transform: scale(1.02);
		background: rgba(139, 233, 253, 0.05);
	}
	
	.exec-rank {
		font-size: 1rem;
		font-weight: 700;
		color: #FFFFFF;
		min-width: 30px;
	}
	
	.exec-info {
		flex: 1;
	}
	
	.exec-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.9);
		margin-bottom: 0.25rem;
	}
	
	.exec-metrics {
		display: flex;
		gap: 1rem;
		font-size: 0.65rem;
	}
	
	.exec-hosts {
		font-weight: 700;
		font-family: 'Courier New', monospace;
	}
	
	.exec-percent {
		color: rgba(255, 255, 255, 0.6);
	}
	
	.exec-level {
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}
	
	/* Network Graph */
	.network-graph {
		height: 200px;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 8px;
		padding: 1rem;
	}
	
	.network-graph svg {
		width: 100%;
		height: 100%;
	}
	
	.exec-node {
		cursor: pointer;
	}
	
	.exec-node:hover {
		transform: scale(1.1);
	}
	
	/* Analytics Section */
	.analytics-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.analytics-card {
		flex: 1;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
	}
	
	.analytics-card h3 {
		margin: 0 0 1rem 0;
		font-size: 0.75rem;
		color: #8BE9FD;
		font-weight: 300;
		letter-spacing: 0.1em;
	}
	
	/* Control Chart */
	.control-chart {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	
	.control-item {
		display: grid;
		grid-template-columns: 100px 1fr 80px;
		gap: 0.5rem;
		align-items: center;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	.control-item:hover {
		transform: translateX(2px);
	}
	
	.control-name {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.control-bar {
		height: 16px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.control-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.4rem;
		transition: width 0.5s ease;
	}
	
	.control-value {
		font-size: 0.6rem;
		color: #FFFFFF;
		font-weight: 600;
	}
	
	.control-span {
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.03em;
	}
	
	/* Level Distribution */
	.level-distribution {
		flex: 1;
	}
	
	.level-chart {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.level-item {
		display: grid;
		grid-template-columns: 80px 1fr 30px;
		gap: 0.5rem;
		align-items: center;
	}
	
	.level-name {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.level-bar {
		height: 12px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 3px;
		overflow: hidden;
	}
	
	.level-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.level-count {
		font-size: 0.7rem;
		font-weight: 600;
		text-align: right;
	}
	
	/* Coverage Grid */
	.coverage-grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 0.75rem;
	}
	
	.coverage-stat {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 6px;
	}
	
	.coverage-number {
		font-size: 1.2rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
	}
	
	.coverage-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		text-align: right;
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
	
	.exec-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.exec-list {
		flex: 1;
		overflow-y: auto;
	}
	
	.executives-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.executives-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.9);
		z-index: 10;
	}
	
	.executives-table th {
		padding: 0.5rem;
		text-align: left;
		font-size: 0.6rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.executives-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.executives-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.05);
	}
	
	.executives-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank {
		color: #BD93F9;
		font-weight: 600;
		font-size: 0.65rem;
	}
	
	.exec-name {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.65rem;
	}
	
	.level-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.host-count {
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.span-cell {
		font-size: 0.6rem;
	}
	
	.span-badge {
		font-weight: 600;
		letter-spacing: 0.03em;
	}
	
	.level-badge {
		font-size: 0.55rem;
		padding: 0.15rem 0.3rem;
		border-radius: 3px;
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
	
	.executive-stats {
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
	
	.hosts-grid {
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
	
	.hierarchy-loader {
		position: relative;
		width: 100px;
		height: 100px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
	}
	
	.level {
		height: 20px;
		background: linear-gradient(90deg, #BD93F9, #8BE9FD);
		border-radius: 4px;
		animation: levelPulse 1.5s ease-in-out infinite;
	}
	
	.level-1 {
		width: 40px;
		animation-delay: 0s;
	}
	
	.level-2 {
		width: 60px;
		animation-delay: 0.3s;
	}
	
	.level-3 {
		width: 80px;
		animation-delay: 0.6s;
	}
	
	@keyframes levelPulse {
		0%, 100% { opacity: 0.3; transform: scaleX(0.9); }
		50% { opacity: 1; transform: scaleX(1); }
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