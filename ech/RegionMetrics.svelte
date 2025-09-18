<!-- RegionMetrics.svelte - Production Ready -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/region_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Failed to load region metrics:', err);
			loading = false;
		}
	});

	$: regions = data.global_surveillance ? 
		Object.entries(data.global_surveillance)
			.filter(([region]) => region.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = regions.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = regions.length > 0 ? Math.max(...regions.map(([,c]) => c)) : 1;

	async function selectRegion(region, count) {
		selectedRegion = { region, count };
		loading = true;
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(region)}`);
			let result = await response.json();
			regionDetails = result.hosts || [];
		} catch (err) {
			console.error('Failed to load region details:', err);
			regionDetails = [];
		}
		loading = false;
	}

	function closeDetails() {
		selectedRegion = null;
		regionDetails = [];
	}
	
	function getRegionLevel(count) {
		let percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'HIGH', color: '#BD93F9' };
		if (percentage >= 50) return { level: 'MEDIUM', color: '#8BE9FD' };
		if (percentage >= 25) return { level: 'LOW', color: '#50FA7B' };
		return { level: 'MINIMAL', color: '#FFB86C' };
	}
</script>

<div class="container">
	<!-- Metrics Bar -->
	<div class="metrics">
		<div class="metric">
			<div class="value" style="color:#BD93F9">{regions.length}</div>
			<div class="label">REGIONS</div>
		</div>
		<div class="metric">
			<div class="value" style="color:#8BE9FD">{totalHosts.toLocaleString()}</div>
			<div class="label">TOTAL HOSTS</div>
		</div>
		<div class="metric">
			<div class="value" style="color:#50FA7B">{regions[0]?.[0]?.toUpperCase() || 'N/A'}</div>
			<div class="label">TOP REGION</div>
		</div>
		<div class="metric">
			<div class="value" style="color:#FFB86C">
				{regions.length > 0 ? Math.round(totalHosts / regions.length).toLocaleString() : 0}
			</div>
			<div class="label">AVG HOSTS/REGION</div>
		</div>
	</div>
	
	<!-- Main Grid -->
	<div class="grid">
		<!-- Map Panel -->
		<div class="map-panel">
			<div class="header">
				<h2>GLOBAL DISTRIBUTION</h2>
				<input type="text" bind:value={searchTerm} placeholder="Search regions..." class="search"/>
			</div>
			
			{#if loading && !selectedRegion}
				<div class="loading">
					<div class="spinner"></div>
					<p>LOADING REGIONAL DATA...</p>
				</div>
			{:else if selectedRegion}
				<div class="detail">
					<div class="detail-header">
						<div>
							<h3>{selectedRegion.region.toUpperCase()}</h3>
							<span class="sub">{selectedRegion.count.toLocaleString()} HOSTS</span>
						</div>
						<button class="close" on:click={closeDetails}>×</button>
					</div>
					<div class="table-wrap">
						<table>
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>COUNTRY</th>
									<th>TYPE</th>
									<th>DIVISION</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each regionDetails as host}
									<tr>
										<td class="mono">{host.host}</td>
										<td>{host.country || '-'}</td>
										<td>{host.infrastructure_type || '-'}</td>
										<td>{host.business_unit || '-'}</td>
										<td><span class="status {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'ok' : ''}">●</span></td>
										<td><span class="status {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'ok' : ''}">●</span></td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="map">
					<svg viewBox="0 0 800 400">
						{#each regions.slice(0, 10) as [region, count], i}
							<g class="node" on:click={() => selectRegion(region, count)}>
								<circle 
									cx="{100 + (i % 4) * 180}" 
									cy="{100 + Math.floor(i / 4) * 150}" 
									r="{Math.sqrt(count / maxHosts) * 50}"
									fill="{getRegionLevel(count).color}"
									opacity="0.6"/>
								<text 
									x="{100 + (i % 4) * 180}" 
									y="{100 + Math.floor(i / 4) * 150 - Math.sqrt(count / maxHosts) * 50 - 10}"
									text-anchor="middle" 
									fill="#fff" 
									font-size="11">
									{region.toUpperCase()}
								</text>
								<text 
									x="{100 + (i % 4) * 180}" 
									y="{100 + Math.floor(i / 4) * 150 + 5}"
									text-anchor="middle" 
									fill="#fff" 
									font-size="14" 
									font-weight="600">
									{count.toLocaleString()}
								</text>
							</g>
						{/each}
					</svg>
				</div>
			{/if}
		</div>
		
		<!-- Charts -->
		<div class="charts">
			<div class="chart-card">
				<h3>DISTRIBUTION</h3>
				<div class="bars">
					{#each regions.slice(0, 5) as [region, count]}
						<div class="bar-item">
							<span class="bar-label">{region.substring(0, 10)}</span>
							<div class="bar-track">
								<div class="bar-fill" 
									 style="width:{(count/maxHosts)*100}%; background:{getRegionLevel(count).color}">
									<span class="bar-value">{count.toLocaleString()}</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
		
		<!-- List -->
		<div class="list-panel">
			<div class="header">
				<h3>ALL REGIONS</h3>
				<span class="count">{regions.length}</span>
			</div>
			<div class="list">
				<table>
					<thead>
						<tr>
							<th>#</th>
							<th>REGION</th>
							<th>HOSTS</th>
							<th>%</th>
						</tr>
					</thead>
					<tbody>
						{#each regions as [region, count], i}
							<tr on:click={() => selectRegion(region, count)}>
								<td class="rank">#{i + 1}</td>
								<td class="name">
									<span class="dot" style="background:{getRegionLevel(count).color}"></span>
									{region.toUpperCase()}
								</td>
								<td class="count" style="color:{getRegionLevel(count).color}">
									{count.toLocaleString()}
								</td>
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
	
	.metrics {
		display: flex;
		gap: 1rem;
		background: rgba(255,255,255,0.02);
		border: 1px solid rgba(139,233,253,0.1);
		border-radius: 8px;
		padding: 1rem 2rem;
	}
	
	.metric {
		flex: 1;
		text-align: center;
		border-right: 1px solid rgba(255,255,255,0.1);
	}
	
	.metric:last-child {
		border: none;
	}
	
	.value {
		font: 700 1.8rem/1 'SF Mono', monospace;
		margin-bottom: 0.5rem;
	}
	
	.label {
		font: 600 0.7rem/1 system-ui;
		color: rgba(255,255,255,0.5);
		letter-spacing: 0.1em;
	}
	
	.grid {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 350px 300px;
		gap: 1rem;
		min-height: 0;
	}
	
	.map-panel, .charts, .list-panel {
		background: rgba(255,255,255,0.02);
		border: 1px solid rgba(189,147,249,0.1);
		border-radius: 8px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		border-bottom: 1px solid rgba(255,255,255,0.1);
	}
	
	.header h2, .header h3 {
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
		width: 180px;
	}
	
	.search:focus {
		outline: none;
		border-color: #8BE9FD;
	}
	
	.map {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
	}
	
	.map svg {
		width: 100%;
		height: 100%;
	}
	
	.node {
		cursor: pointer;
		transition: transform 0.3s;
	}
	
	.node:hover {
		transform: scale(1.1);
	}
	
	.chart-card {
		padding: 1rem;
	}
	
	.chart-card h3 {
		margin: 0 0 1rem 0;
		font: 300 0.8rem/1 system-ui;
		color: #8BE9FD;
		letter-spacing: 0.1em;
	}
	
	.bars {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.bar-item {
		display: grid;
		grid-template-columns: 80px 1fr;
		gap: 0.5rem;
		align-items: center;
	}
	
	.bar-label {
		font: 400 0.7rem/1 system-ui;
		color: rgba(255,255,255,0.7);
		text-align: right;
	}
	
	.bar-track {
		height: 20px;
		background: rgba(255,255,255,0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.5rem;
		transition: width 0.5s cubic-bezier(0.4,0,0.2,1);
	}
	
	.bar-value {
		font: 600 0.65rem/1 'SF Mono', monospace;
		color: #fff;
	}
	
	.count {
		font: 600 0.8rem/1 'SF Mono', monospace;
		color: rgba(255,255,255,0.5);
	}
	
	.list {
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
		padding: 0.6rem 0.75rem;
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
	
	.dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
	}
	
	.count {
		font-family: 'SF Mono', monospace;
		font-weight: 600;
	}
	
	.percent {
		color: rgba(255,255,255,0.5);
		font-size: 0.7rem;
	}
	
	.detail {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: 1rem;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		margin-bottom: 1rem;
	}
	
	.detail-header h3 {
		margin: 0 0 0.25rem 0;
		font: 600 1.1rem/1 system-ui;
		color: #BD93F9;
	}
	
	.sub {
		font: 400 0.75rem/1 system-ui;
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
	}
	
	.close:hover {
		background: rgba(189,147,249,0.2);
		border-color: #BD93F9;
		transform: scale(1.1);
	}
	
	.table-wrap {
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
	
	.status {
		color: #FF5555;
	}
	
	.status.ok {
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
</style>