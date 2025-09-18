<!-- SourceTables.svelte - Production Ready -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let animationFrame = null;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Failed to load source tables:', err);
			loading = false;
		}
		startAnimation();
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});
	
	function startAnimation() {
		let time = 0;
		function animate() {
			time += 0.016;
			animationFrame = requestAnimationFrame(animate);
		}
		animate();
	}

	$: sources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = sources.reduce((sum, [_, count]) => sum + count, 0);
	$: maxCount = sources.length > 0 ? Math.max(...sources.map(([,c]) => c)) : 1;

	async function selectSource(source, count) {
		selectedSource = { source, count };
		loading = true;
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			hostDetails = result.hosts || [];
		} catch (err) {
			console.error('Failed to load host details:', err);
			hostDetails = [];
		}
		loading = false;
	}

	function closeDetails() {
		selectedSource = null;
		hostDetails = [];
	}
	
	function getSourceLevel(count) {
		let percentage = (count / maxCount) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#BD93F9' };
		if (percentage >= 50) return { level: 'HIGH', color: '#8BE9FD' };
		if (percentage >= 25) return { level: 'MEDIUM', color: '#50FA7B' };
		return { level: 'LOW', color: '#FFB86C' };
	}
</script>

<div class="container">
	<!-- Header Metrics -->
	<div class="metrics-row">
		<div class="metric">
			<div class="metric-value" style="color:#BD93F9">{sources.length}</div>
			<div class="metric-label">SOURCE TABLES</div>
		</div>
		<div class="metric">
			<div class="metric-value" style="color:#8BE9FD">{totalHosts.toLocaleString()}</div>
			<div class="metric-label">TOTAL HOSTS</div>
		</div>
		<div class="metric">
			<div class="metric-value" style="color:#50FA7B">{sources[0]?.[0]?.toUpperCase() || 'N/A'}</div>
			<div class="metric-label">TOP SOURCE</div>
		</div>
		<div class="metric">
			<div class="metric-value" style="color:#FFB86C">{maxCount.toLocaleString()}</div>
			<div class="metric-label">MAX TABLE SIZE</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content">
		<!-- Visualization Panel -->
		<div class="main-panel">
			<div class="panel-header">
				<h2>SOURCE TABLE DISTRIBUTION</h2>
				<input type="text" bind:value={searchTerm} placeholder="Search..." class="search"/>
			</div>
			
			{#if loading && !selectedSource}
				<div class="loading">
					<div class="spinner"></div>
					<p>LOADING SOURCE TABLES...</p>
				</div>
			{:else if selectedSource}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedSource.source.toUpperCase()}</h3>
							<span class="subtitle">{selectedSource.count.toLocaleString()} HOSTS</span>
						</div>
						<button class="close" on:click={closeDetails}>×</button>
					</div>
					<div class="detail-content">
						<table>
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>TYPE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each hostDetails as host}
									<tr>
										<td class="mono">{host.host}</td>
										<td>{host.region || '-'}</td>
										<td>{host.country || '-'}</td>
										<td>{host.infrastructure_type || '-'}</td>
										<td><span class="dot {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : ''}">●</span></td>
										<td><span class="dot {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : ''}">●</span></td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<!-- Bar Chart -->
				<div class="chart">
					<div class="bars">
						{#each sources.slice(0, 10) as [source, count]}
							{#key source}
								<div class="bar-group" on:click={() => selectSource(source, count)}>
									<div class="bar" style="height:{(count/maxCount)*100}%; background:{getSourceLevel(count).color}">
										<span class="bar-value">{count.toLocaleString()}</span>
									</div>
									<div class="bar-label">{source.substring(0, 10)}</div>
								</div>
							{/key}
						{/each}
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Table List -->
		<div class="side-panel">
			<div class="panel-header">
				<h3>ALL SOURCES</h3>
				<span class="count">{sources.length}</span>
			</div>
			<div class="table-container">
				<table>
					<thead>
						<tr>
							<th>#</th>
							<th>SOURCE</th>
							<th>HOSTS</th>
							<th>%</th>
						</tr>
					</thead>
					<tbody>
						{#each sources as [source, count], i}
							<tr on:click={() => selectSource(source, count)}>
								<td class="rank">{i + 1}</td>
								<td class="name">
									<span class="indicator" style="background:{getSourceLevel(count).color}"></span>
									{source.toUpperCase()}
								</td>
								<td class="value" style="color:{getSourceLevel(count).color}">{count.toLocaleString()}</td>
								<td class="percent">{((count/totalHosts)*100).toFixed(1)}%</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>
</div>

<style>
	.container {
		height: calc(100vh - 80px);
		background: #000;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.metrics-row {
		display: flex;
		gap: 1rem;
		background: rgba(255,255,255,0.02);
		border: 1px solid rgba(139,233,253,0.1);
		border-radius: 8px;
		padding: 1rem;
	}
	
	.metric {
		flex: 1;
		text-align: center;
	}
	
	.metric-value {
		font: 700 1.8rem/1 'SF Mono', monospace;
		margin-bottom: 0.5rem;
	}
	
	.metric-label {
		font: 600 0.7rem/1 system-ui;
		color: rgba(255,255,255,0.5);
		letter-spacing: 0.1em;
	}
	
	.content {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 400px;
		gap: 1rem;
		min-height: 0;
	}
	
	.main-panel, .side-panel {
		background: rgba(255,255,255,0.02);
		border: 1px solid rgba(189,147,249,0.1);
		border-radius: 8px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		border-bottom: 1px solid rgba(255,255,255,0.1);
	}
	
	.panel-header h2, .panel-header h3 {
		margin: 0;
		font: 300 0.9rem/1 system-ui;
		color: #BD93F9;
		letter-spacing: 0.1em;
	}
	
	.search {
		padding: 0.5rem 1rem;
		background: rgba(0,0,0,0.5);
		border: 1px solid rgba(139,233,253,0.3);
		border-radius: 4px;
		color: #fff;
		font-size: 0.8rem;
		width: 200px;
	}
	
	.search:focus {
		outline: none;
		border-color: #8BE9FD;
		box-shadow: 0 0 0 1px #8BE9FD;
	}
	
	.count {
		font: 600 0.8rem/1 'SF Mono', monospace;
		color: rgba(255,255,255,0.5);
	}
	
	.chart {
		flex: 1;
		padding: 2rem;
		display: flex;
		align-items: flex-end;
		justify-content: center;
	}
	
	.bars {
		display: flex;
		gap: 1rem;
		align-items: flex-end;
		height: 100%;
		width: 100%;
		max-width: 800px;
	}
	
	.bar-group {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
		height: 100%;
	}
	
	.bar {
		width: 100%;
		max-width: 60px;
		border-radius: 4px 4px 0 0;
		display: flex;
		align-items: flex-start;
		justify-content: center;
		padding-top: 0.5rem;
		transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
		position: relative;
	}
	
	.bar:hover {
		filter: brightness(1.2);
		transform: translateY(-4px);
	}
	
	.bar-value {
		font: 600 0.7rem/1 'SF Mono', monospace;
		color: #fff;
	}
	
	.bar-label {
		font: 400 0.65rem/1 system-ui;
		color: rgba(255,255,255,0.6);
		text-align: center;
	}
	
	.table-container {
		flex: 1;
		overflow-y: auto;
	}
	
	table {
		width: 100%;
		border-collapse: collapse;
	}
	
	thead {
		position: sticky;
		top: 0;
		background: rgba(0,0,0,0.9);
		z-index: 10;
	}
	
	th {
		padding: 0.75rem;
		text-align: left;
		font: 600 0.65rem/1 system-ui;
		color: rgba(255,255,255,0.5);
		letter-spacing: 0.1em;
		border-bottom: 1px solid rgba(255,255,255,0.1);
	}
	
	tbody tr {
		cursor: pointer;
		transition: background 0.2s;
		border-bottom: 1px solid rgba(255,255,255,0.05);
	}
	
	tbody tr:hover {
		background: rgba(139,233,253,0.05);
	}
	
	td {
		padding: 0.75rem;
		font: 400 0.75rem/1 system-ui;
		color: rgba(255,255,255,0.8);
	}
	
	.rank {
		color: #BD93F9;
		font-weight: 600;
	}
	
	.name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.indicator {
		width: 6px;
		height: 6px;
		border-radius: 50%;
	}
	
	.value {
		font-family: 'SF Mono', monospace;
		font-weight: 600;
	}
	
	.percent {
		color: rgba(255,255,255,0.5);
	}
	
	.detail-view {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: 1rem;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: start;
		margin-bottom: 1rem;
	}
	
	.detail-header h3 {
		margin: 0;
		font: 600 1.2rem/1 system-ui;
		color: #BD93F9;
		margin-bottom: 0.25rem;
	}
	
	.subtitle {
		font: 400 0.8rem/1 system-ui;
		color: rgba(255,255,255,0.6);
	}
	
	.close {
		background: rgba(255,255,255,0.1);
		border: 1px solid rgba(255,255,255,0.2);
		color: #fff;
		width: 32px;
		height: 32px;
		border-radius: 4px;
		font-size: 1.5rem;
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.close:hover {
		background: rgba(189,147,249,0.2);
		border-color: #BD93F9;
		transform: scale(1.1);
	}
	
	.detail-content {
		flex: 1;
		overflow-y: auto;
		background: rgba(0,0,0,0.3);
		border-radius: 4px;
		padding: 1rem;
	}
	
	.mono {
		font-family: 'SF Mono', monospace;
		color: #8BE9FD;
		font-size: 0.7rem;
	}
	
	.dot {
		font-size: 1rem;
		color: #FF5555;
	}
	
	.dot.active {
		color: #50FA7B;
	}
	
	.loading {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.spinner {
		width: 48px;
		height: 48px;
		border: 3px solid rgba(189,147,249,0.2);
		border-top-color: #BD93F9;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}
	
	@keyframes spin {
		to { transform: rotate(360deg); }
	}
	
	.loading p {
		color: rgba(255,255,255,0.5);
		font: 400 0.8rem/1 system-ui;
		letter-spacing: 0.2em;
	}
	
	::-webkit-scrollbar {
		width: 6px;
	}
	
	::-webkit-scrollbar-track {
		background: rgba(0,0,0,0.5);
	}
	
	::-webkit-scrollbar-thumb {
		background: rgba(189,147,249,0.3);
		border-radius: 3px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: rgba(189,147,249,0.5);
	}
</style>