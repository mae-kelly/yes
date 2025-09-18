<!-- CountryMetrics.svelte - Production Ready -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';
	let viewMode = 'map';
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/country_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Failed to load country metrics:', err);
			loading = false;
		}
	});

	$: countries = data.global_intelligence ? 
		Object.entries(data.global_intelligence)
			.filter(([country]) => country.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = countries.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = countries.length > 0 ? Math.max(...countries.map(([,c]) => c)) : 1;

	async function selectCountry(country, count) {
		selectedCountry = { country, count };
		loading = true;
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(country)}`);
			let result = await response.json();
			countryDetails = result.hosts || [];
		} catch (err) {
			console.error('Failed to load country details:', err);
			countryDetails = [];
		}
		loading = false;
	}

	function closeDetails() {
		selectedCountry = null;
		countryDetails = [];
	}
	
	function getCountryLevel(count) {
		let percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#BD93F9' };
		if (percentage >= 50) return { level: 'HIGH', color: '#8BE9FD' };
		if (percentage >= 25) return { level: 'MODERATE', color: '#50FA7B' };
		return { level: 'LOW', color: '#FFB86C' };
	}
</script>

<div class="container">
	<!-- KPIs -->
	<div class="kpis">
		<div class="kpi">
			<div class="kpi-value" style="color:#BD93F9">{countries.length}</div>
			<div class="kpi-label">COUNTRIES</div>
		</div>
		<div class="kpi">
			<div class="kpi-value" style="color:#8BE9FD">{totalHosts.toLocaleString()}</div>
			<div class="kpi-label">TOTAL HOSTS</div>
		</div>
		<div class="kpi">
			<div class="kpi-value" style="color:#50FA7B">{countries[0]?.[0]?.toUpperCase() || 'N/A'}</div>
			<div class="kpi-label">TOP COUNTRY</div>
		</div>
		<div class="kpi">
			<div class="kpi-value" style="color:#FFB86C">{((countries.length/195)*100).toFixed(1)}%</div>
			<div class="kpi-label">GLOBAL COVERAGE</div>
		</div>
		<div class="kpi">
			<div class="kpi-value" style="color:#FF79C6">
				{countries[0] ? ((countries[0][1]/totalHosts)*100).toFixed(1) : 0}%
			</div>
			<div class="kpi-label">TOP CONCENTRATION</div>
		</div>
	</div>
	
	<!-- Main Layout -->
	<div class="layout">
		<!-- Map View -->
		<div class="main-view">
			<div class="view-header">
				<h2>GLOBAL INFRASTRUCTURE</h2>
				<div class="controls">
					<input type="text" bind:value={searchTerm} placeholder="Search..." class="search"/>
					<div class="tabs">
						<button class="tab {viewMode === 'map' ? 'active' : ''}" on:click={() => viewMode = 'map'}>MAP</button>
						<button class="tab {viewMode === 'grid' ? 'active' : ''}" on:click={() => viewMode = 'grid'}>GRID</button>
						<button class="tab {viewMode === 'list' ? 'active' : ''}" on:click={() => viewMode = 'list'}>LIST</button>
					</div>
				</div>
			</div>
			
			{#if loading && !selectedCountry}
				<div class="loading">
					<div class="spinner"></div>
					<p>SCANNING GLOBAL INFRASTRUCTURE...</p>
				</div>
			{:else if selectedCountry}
				<div class="detail">
					<div class="detail-header">
						<div>
							<h3>{selectedCountry.country.toUpperCase()}</h3>
							<div class="stats">
								<span>{selectedCountry.count.toLocaleString()} HOSTS</span>
								<span>•</span>
								<span>{((selectedCountry.count/totalHosts)*100).toFixed(2)}% OF GLOBAL</span>
							</div>
						</div>
						<button class="close" on:click={closeDetails}>×</button>
					</div>
					<div class="detail-table">
						<table>
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>REGION</th>
									<th>DATA CENTER</th>
									<th>DIVISION</th>
									<th>TYPE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each countryDetails as host}
									<tr>
										<td class="mono">{host.host}</td>
										<td>{host.region || '-'}</td>
										<td>{host.data_center || '-'}</td>
										<td>{host.business_unit || '-'}</td>
										<td>{host.infrastructure_type || '-'}</td>
										<td><span class="dot {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'ok' : ''}">●</span></td>
										<td><span class="dot {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'ok' : ''}">●</span></td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else if viewMode === 'map'}
				<div class="map-view">
					<svg viewBox="0 0 1000 500">
						{#each countries.slice(0, 20) as [country, count], i}
							<g class="country-node" on:click={() => selectCountry(country, count)}>
								<circle 
									cx="{100 + (i % 5) * 180}" 
									cy="{100 + Math.floor(i / 5) * 100}"
									r="{Math.sqrt(count/maxHosts) * 40}"
									fill="{getCountryLevel(count).color}"
									opacity="0.6"/>
								<text 
									x="{100 + (i % 5) * 180}" 
									y="{85 + Math.floor(i / 5) * 100}"
									text-anchor="middle" 
									fill="#fff" 
									font-size="10">
									{country.substring(0, 15).toUpperCase()}
								</text>
								<text 
									x="{100 + (i % 5) * 180}" 
									y="{105 + Math.floor(i / 5) * 100}"
									text-anchor="middle" 
									fill="#fff" 
									font-size="14" 
									font-weight="700">
									{count.toLocaleString()}
								</text>
							</g>
						{/each}
					</svg>
				</div>
			{:else if viewMode === 'grid'}
				<div class="grid-view">
					{#each countries.slice(0, 20) as [country, count], i}
						<div class="grid-card" on:click={() => selectCountry(country, count)}>
							<div class="card-header" style="background:{getCountryLevel(count).color}20">
								<span class="card-rank">#{i + 1}</span>
							</div>
							<div class="card-body">
								<div class="card-name">{country.substring(0, 20).toUpperCase()}</div>
								<div class="card-value" style="color:{getCountryLevel(count).color}">
									{count.toLocaleString()}
								</div>
								<div class="card-bar">
									<div class="bar-fill" style="width:{(count/maxHosts)*100}%; background:{getCountryLevel(count).color}"></div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{:else if viewMode === 'list'}
				<div class="list-view">
					<table>
						<thead>
							<tr>
								<th>RANK</th>
								<th>COUNTRY</th>
								<th>HOSTS</th>
								<th>% OF TOTAL</th>
								<th>STATUS</th>
							</tr>
						</thead>
						<tbody>
							{#each countries as [country, count], i}
								<tr on:click={() => selectCountry(country, count)}>
									<td class="rank">#{i + 1}</td>
									<td>{country.toUpperCase()}</td>
									<td class="value" style="color:{getCountryLevel(count).color}">
										{count.toLocaleString()}
									</td>
									<td>{((count/totalHosts)*100).toFixed(2)}%</td>
									<td>
										<span class="badge" style="color:{getCountryLevel(count).color}; border-color:{getCountryLevel(count).color}">
											{getCountryLevel(count).level}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
		
		<!-- Analytics -->
		<div class="analytics">
			<!-- Top 10 -->
			<div class="card">
				<h3>TOP 10 COUNTRIES</h3>
				<div class="top-list">
					{#each countries.slice(0, 10) as [country, count], i}
						<div class="top-item" on:click={() => selectCountry(country, count)}>
							<span class="top-rank" style="color:{getCountryLevel(count).color}">#{i + 1}</span>
							<span class="top-name">{country.substring(0, 15).toUpperCase()}</span>
							<span class="top-count" style="color:{getCountryLevel(count).color}">{count.toLocaleString()}</span>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Stats -->
			<div class="card">
				<h3>STATISTICS</h3>
				<div class="stat-list">
					<div class="stat">
						<span>Countries >1000 hosts</span>
						<span style="color:#BD93F9">{countries.filter(([_,c]) => c > 1000).length}</span>
					</div>
					<div class="stat">
						<span>Countries >5000 hosts</span>
						<span style="color:#8BE9FD">{countries.filter(([_,c]) => c > 5000).length}</span>
					</div>
					<div class="stat">
						<span>Countries >10000 hosts</span>
						<span style="color:#50FA7B">{countries.filter(([_,c]) => c > 10000).length}</span>
					</div>
				</div>
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
	
	.kpis {
		display: flex;
		gap: 1rem;
		background: rgba(255,255,255,0.02);
		border: 1px solid rgba(139,233,253,0.1);
		border-radius: 8px;
		padding: 1rem;
	}
	
	.kpi {
		flex: 1;
		text-align: center;
		border-right: 1px solid rgba(255,255,255,0.1);
	}
	
	.kpi:last-child {
		border: none;
	}
	
	.kpi-value {
		font: 700 1.6rem/1 'SF Mono', monospace;
		margin-bottom: 0.5rem;
	}
	
	.kpi-label {
		font: 600 0.65rem/1 system-ui;
		color: rgba(255,255,255,0.5);
		letter-spacing: 0.1em;
	}
	
	.layout {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 380px;
		gap: 1rem;
		min-height: 0;
	}
	
	.main-view, .analytics {
		background: rgba(255,255,255,0.02);
		border: 1px solid rgba(189,147,249,0.1);
		border-radius: 8px;
		overflow: hidden;
	}
	
	.main-view {
		display: flex;
		flex-direction: column;
	}
	
	.view-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		border-bottom: 1px solid rgba(255,255,255,0.1);
	}
	
	.view-header h2 {
		margin: 0;
		font: 300 0.9rem/1 system-ui;
		color: #BD93F9;
		letter-spacing: 0.1em;
	}
	
	.controls {
		display: flex;
		gap: 1rem;
		align-items: center;
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
	
	.tabs {
		display: flex;
		gap: 2px;
		background: rgba(0,0,0,0.5);
		padding: 2px;
		border-radius: 4px;
	}
	
	.tab {
		padding: 0.4rem 0.8rem;
		background: transparent;
		border: none;
		color: rgba(255,255,255,0.6);
		font: 600 0.7rem/1 system-ui;
		cursor: pointer;
		border-radius: 3px;
		transition: all 0.2s;
	}
	
	.tab:hover {
		background: rgba(139,233,253,0.1);
	}
	
	.tab.active {
		background: rgba(139,233,253,0.2);
		color: #8BE9FD;
	}
	
	.map-view {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
	}
	
	.map-view svg {
		width: 100%;
		height: 100%;
	}
	
	.country-node {
		cursor: pointer;
		transition: transform 0.3s;
	}
	
	.country-node:hover {
		transform: scale(1.1);
	}
	
	.grid-view {
		flex: 1;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		gap: 1rem;
		padding: 1rem;
		overflow-y: auto;
	}
	
	.grid-card {
		background: rgba(0,0,0,0.5);
		border: 1px solid rgba(139,233,253,0.2);
		border-radius: 6px;
		cursor: pointer;
		overflow: hidden;
		transition: all 0.3s;
	}
	
	.grid-card:hover {
		transform: scale(1.05);
		border-color: #8BE9FD;
	}
	
	.card-header {
		padding: 0.5rem;
		text-align: right;
		font: 600 0.7rem/1 system-ui;
		color: #fff;
	}
	
	.card-body {
		padding: 0.75rem;
	}
	
	.card-name {
		font: 400 0.7rem/1.2 system-ui;
		color: rgba(255,255,255,0.8);
		margin-bottom: 0.5rem;
	}
	
	.card-value {
		font: 700 1.2rem/1 'SF Mono', monospace;
		margin-bottom: 0.5rem;
	}
	
	.card-bar {
		height: 3px;
		background: rgba(255,255,255,0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s;
	}
	
	.list-view {
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
		font: 600 0.7rem/1 system-ui;
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
	
	.value {
		font-family: 'SF Mono', monospace;
		font-weight: 600;
	}
	
	.badge {
		font-size: 0.65rem;
		padding: 0.2rem 0.4rem;
		border: 1px solid;
		border-radius: 3px;
		font-weight: 600;
	}
	
	.analytics {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		padding: 1rem;
	}
	
	.card {
		background: rgba(0,0,0,0.3);
		border-radius: 6px;
		padding: 1rem;
	}
	
	.card h3 {
		margin: 0 0 1rem 0;
		font: 300 0.8rem/1 system-ui;
		color: #8BE9FD;
		letter-spacing: 0.1em;
	}
	
	.top-list {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	
	.top-item {
		display: grid;
		grid-template-columns: 30px 1fr auto;
		gap: 0.5rem;
		align-items: center;
		padding: 0.4rem;
		background: rgba(255,255,255,0.02);
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.top-item:hover {
		background: rgba(139,233,253,0.05);
		transform: translateX(2px);
	}
	
	.top-rank {
		font: 600 0.7rem/1 system-ui;
	}
	
	.top-name {
		font: 400 0.7rem/1 system-ui;
		color: rgba(255,255,255,0.8);
	}
	
	.top-count {
		font: 600 0.8rem/1 'SF Mono', monospace;
	}
	
	.stat-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.stat {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem;
		background: rgba(255,255,255,0.02);
		border-radius: 4px;
		font: 400 0.7rem/1 system-ui;
		color: rgba(255,255,255,0.7);
	}
	
	.stat span:last-child {
		font-family: 'SF Mono', monospace;
		font-weight: 700;
		font-size: 1rem;
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
	
	.stats {
		font: 400 0.7rem/1 system-ui;
		color: rgba(255,255,255,0.6);
		display: flex;
		gap: 0.5rem;
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
	}
	
	.detail-table {
		flex: 1;
		overflow-y: auto;
		background: rgba(0,0,0,0.3);
		border-radius: 4px;
		padding: 1rem;
	}
	
	.mono {
		font-family: 'SF Mono', monospace;
		color: #8BE9FD;
		font-size: 0.65rem;
	}
	
	.dot {
		color: #FF5555;
		font-size: 0.9rem;
	}
	
	.dot.ok {
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