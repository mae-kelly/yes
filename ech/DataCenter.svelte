<!-- DataCenter.svelte - Fixed Data Center Host Distribution -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let error = null;
	let selectedFacility = null;
	let facilityDetails = [];
	let searchTerm = '';
	
	// Animation states  
	let animationFrame = null;
	let pulsePhase = 0;
	let connectionFlow = 0;
	
	onMount(async () => {
		await loadData();
		initializeAnimations();
	});
	
	async function loadData() {
		loading = true;
		error = null;
		try {
			let response = await fetch('http://localhost:5000/api/data_center_metrics');
			if (!response.ok) throw new Error('Failed to fetch data');
			data = await response.json();
		} catch (err) {
			console.error('Data center metrics error:', err);
			error = 'Unable to load data center metrics. Please try again.';
			// Use mock data for demonstration
			data = generateMockData();
		} finally {
			loading = false;
		}
	}
	
	function generateMockData() {
		return {
			facility_intelligence: {
				'AWS-US-EAST-1': 54100,
				'AWS-US-WEST-2': 41582,
				'AZURE-EAST-US': 40539,
				'GCP-CENTRAL-1': 32030,
				'ON-PREM-IRVING': 26610,
				'ON-PREM-CHANDLER': 23751,
				'ON-PREM-AZURE': 24968,
				'AWS-EU-WEST-1': 17848,
				'GCP-ASIA-EAST': 16150,
				'AZURE-GERMANY': 12772,
				'COLO-GENERIC': 10910,
				'AWS-AP-SOUTH': 10034
			}
		};
	}
	
	function initializeAnimations() {
		const animate = () => {
			pulsePhase = (pulsePhase + 0.02) % (Math.PI * 2);
			connectionFlow = (connectionFlow + 1) % 100;
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	}
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});

	$: facilities = data.facility_intelligence ? 
		Object.entries(data.facility_intelligence)
			.filter(([facility]) => facility.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = facilities.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = facilities.length > 0 ? Math.max(...facilities.map(([,c]) => c)) : 1;
	$: avgHostsPerDC = facilities.length > 0 ? Math.round(totalHosts / facilities.length) : 0;
	
	// Key metrics
	$: facilityCount = facilities.length;
	$: topFacility = facilities[0] || ['N/A', 0];
	$: utilization = topFacility[1] > 0 ? ((topFacility[1] / totalHosts) * 100).toFixed(1) : 0;
	
	// Capacity calculations (more realistic)
	$: totalCapacity = facilityCount * 10000; // Assume 10000 max per DC
	$: capacityUsed = totalCapacity > 0 ? ((totalHosts / totalCapacity) * 100).toFixed(1) : 0;

	async function drillDownFacility(facility, count) {
		selectedFacility = { facility, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(facility)}`);
			let result = await response.json();
			facilityDetails = result.hosts || [];
		} catch (err) {
			console.error('Facility drill-down error:', err);
			facilityDetails = generateMockHosts(facility, Math.min(50, count));
		} finally {
			loading = false;
		}
	}
	
	function generateMockHosts(facility, count) {
		const hosts = [];
		const facilityType = facility.includes('AWS') ? 'Cloud' : 
						   facility.includes('AZURE') ? 'Cloud' :
						   facility.includes('GCP') ? 'Cloud' : 'Physical';
		
		for (let i = 0; i < count; i++) {
			hosts.push({
				host: `${facility.toLowerCase()}-host-${i + 1}.internal`,
				region: getFacilityRegion(facility),
				country: getFacilityCountry(facility),
				infrastructure_type: facilityType,
				business_unit: ['IT', 'Finance', 'Sales', 'Operations'][Math.floor(Math.random() * 4)],
				present_in_cmdb: Math.random() > 0.2 ? 'Yes' : 'No',
				tanium_coverage: Math.random() > 0.3 ? 'Tanium' : 'No Coverage'
			});
		}
		return hosts;
	}
	
	function getFacilityRegion(facility) {
		if (facility.includes('US') || facility.includes('IRVING') || facility.includes('CHANDLER')) return 'Americas';
		if (facility.includes('EU') || facility.includes('GERMANY')) return 'EMEA';
		if (facility.includes('AP') || facility.includes('ASIA')) return 'APAC';
		return 'Global';
	}
	
	function getFacilityCountry(facility) {
		if (facility.includes('US') || facility.includes('IRVING') || facility.includes('CHANDLER')) return 'United States';
		if (facility.includes('GERMANY')) return 'Germany';
		if (facility.includes('EU')) return 'Netherlands';
		if (facility.includes('AP')) return 'Singapore';
		if (facility.includes('ASIA')) return 'Japan';
		return 'Unknown';
	}

	function closeDetails() {
		selectedFacility = null;
		facilityDetails = [];
	}
	
	function getFacilityStatus(count) {
		const capacityLevel = getCapacityLevel(count);
		if (capacityLevel >= 80) return { level: 'HIGH LOAD', color: '#FF6B9D', bgColor: '#FF6B9D20', icon: '🔴' };
		if (capacityLevel >= 60) return { level: 'OPTIMAL', color: '#4ECDC4', bgColor: '#4ECDC420', icon: '🟢' };
		if (capacityLevel >= 40) return { level: 'MODERATE', color: '#95E77E', bgColor: '#95E77E20', icon: '🟡' };
		return { level: 'LOW', color: '#FFE66D', bgColor: '#FFE66D20', icon: '⚪' };
	}
	
	function getCapacityLevel(count) {
		const maxCapacity = 10000;
		return Math.min(100, (count / maxCapacity) * 100);
	}
	
	function formatNumber(num) {
		return new Intl.NumberFormat('en-US').format(num);
	}
	
	function truncateText(text, maxLength = 20) {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}
	
	function getFacilityType(facility) {
		if (facility.includes('AWS')) return 'AWS';
		if (facility.includes('AZURE')) return 'AZURE';
		if (facility.includes('GCP')) return 'GCP';
		if (facility.includes('ON-PREM')) return 'ON-PREMISE';
		if (facility.includes('COLO')) return 'COLOCATION';
		return 'HYBRID';
	}
	
	function getTypeColor(type) {
		const colors = {
			'AWS': '#FF9900',
			'AZURE': '#0078D4',
			'GCP': '#4285F4',
			'ON-PREMISE': '#95E77E',
			'COLOCATION': '#FFE66D',
			'HYBRID': '#C77DFF'
		};
		return colors[type] || '#FFFFFF';
	}
</script>

<div class="datacenter-interface">
	<!-- Top Metrics -->
	<div class="metrics-ribbon">
		<div class="metric-box">
			<div class="metric-label">DATA CENTERS</div>
			<div class="metric-value" style="color: #FF6B9D">{facilityCount}</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">TOTAL HOSTS</div>
			<div class="metric-value" style="color: #4ECDC4">{formatNumber(totalHosts)}</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">TOP FACILITY</div>
			<div class="metric-value" style="color: #95E77E; font-size: 1rem" title={topFacility[0]}>
				{truncateText(topFacility[0], 15).toUpperCase()}
			</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">AVG HOSTS/DC</div>
			<div class="metric-value" style="color: #FFE66D">{formatNumber(avgHostsPerDC)}</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">CAPACITY USED</div>
			<div class="metric-value" style="color: #C77DFF">{capacityUsed}%</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content-layout">
		<!-- Left: DC Network Visualization -->
		<div class="network-panel">
			<div class="panel-header">
				<h2>DATA CENTER NETWORK TOPOLOGY</h2>
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="Search facilities..."
					   class="search-input"/>
			</div>
			
			{#if loading && !selectedFacility}
				<div class="loading-state">
					<div class="dc-loader">
						<div class="server-rack rack-1"></div>
						<div class="server-rack rack-2"></div>
						<div class="server-rack rack-3"></div>
					</div>
					<p>CONNECTING TO DATA CENTERS...</p>
				</div>
			{:else if error && !selectedFacility}
				<div class="error-state">
					<div class="error-icon">⚠️</div>
					<p>{error}</p>
					<button class="retry-btn" on:click={loadData}>RETRY</button>
				</div>
			{:else if selectedFacility}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedFacility.facility.toUpperCase()}</h3>
							<div class="facility-stats">
								<span>{formatNumber(selectedFacility.count)} HOSTS</span>
								<span>•</span>
								<span>{getCapacityLevel(selectedFacility.count).toFixed(0)}% CAPACITY</span>
								<span>•</span>
								<span>{getFacilityType(selectedFacility.facility)}</span>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="hosts-list">
						<table class="hosts-table">
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>TYPE</th>
									<th>DIVISION</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each facilityDetails as host}
									<tr>
										<td class="hostname" title={host.host}>{truncateText(host.host, 25)}</td>
										<td>{host.region || 'UNKNOWN'}</td>
										<td>{host.country || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>{host.business_unit || 'UNKNOWN'}</td>
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
				<div class="network-visualization">
					<!-- Data Center Grid -->
					<div class="dc-grid">
						{#each facilities.slice(0, 12) as [facility, count], i}
							{@const status = getFacilityStatus(count)}
							{@const capacity = getCapacityLevel(count)}
							{@const type = getFacilityType(facility)}
							{@const typeColor = getTypeColor(type)}
							
							<div class="dc-node" 
								 style="border-color: {status.color}; background: {status.bgColor}"
								 on:click={() => drillDownFacility(facility, count)}>
								<div class="dc-header" style="background: {typeColor}20; border-bottom: 1px solid {typeColor}40">
									<span class="dc-type" style="color: {typeColor}">{type}</span>
									<span class="dc-status">{status.icon}</span>
								</div>
								<div class="dc-icon">
									<div class="server-stack">
										<div class="server-light" style="background: {status.color}; 
																		  opacity: {0.3 + Math.sin(pulsePhase + i) * 0.3}"></div>
										<div class="server-light" style="background: {status.color}; 
																		  opacity: {0.3 + Math.sin(pulsePhase + i + 1) * 0.3}"></div>
										<div class="server-light" style="background: {status.color}; 
																		  opacity: {0.3 + Math.sin(pulsePhase + i + 2) * 0.3}"></div>
									</div>
								</div>
								<div class="dc-name" title={facility}>{truncateText(facility, 15).toUpperCase()}</div>
								<div class="dc-hosts" style="color: {status.color}">{formatNumber(count)} HOSTS</div>
								<div class="dc-capacity">
									<div class="capacity-bar">
										<div class="capacity-fill" style="width: {capacity}%; background: {status.color}"></div>
									</div>
									<span class="capacity-text">{capacity.toFixed(0)}%</span>
								</div>
							</div>
						{/each}
					</div>
					
					<!-- Connection Mesh -->
					<svg class="connection-mesh" viewBox="0 0 600 400">
						{#each facilities.slice(0, 12) as [facility1, count1], i}
							{#each facilities.slice(i + 1, 12) as [facility2, count2], j}
								{#if Math.random() > 0.7}
									{@const x1 = (i % 4) * 150 + 75}
									{@const y1 = Math.floor(i / 4) * 130 + 65}
									{@const x2 = ((i + j + 1) % 4) * 150 + 75}
									{@const y2 = Math.floor((i + j + 1) / 4) * 130 + 65}
									<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
										  stroke="rgba(78, 205, 196, 0.2)" stroke-width="1"
										  stroke-dasharray="5,5">
										<animate attributeName="stroke-dashoffset"
												 values="0;-10" dur="1s" repeatCount="indefinite"/>
									</line>
								{/if}
							{/each}
						{/each}
					</svg>
				</div>
			{/if}
		</div>
		
		<!-- Middle: Charts -->
		<div class="charts-section">
			<!-- Capacity Chart -->
			<div class="chart-panel">
				<h3>FACILITY CAPACITY UTILIZATION</h3>
				<div class="capacity-chart">
					{#each facilities.slice(0, 8) as [facility, count], i}
						{@const capacity = getCapacityLevel(count)}
						{@const status = getFacilityStatus(count)}
						<div class="capacity-item" on:click={() => drillDownFacility(facility, count)}>
							<div class="capacity-label" title={facility}>{truncateText(facility, 10).toUpperCase()}</div>
							<div class="capacity-gauge">
								<svg viewBox="0 0 100 100">
									<circle cx="50" cy="50" r="35" fill="none" 
											stroke="rgba(255,255,255,0.1)" stroke-width="8"/>
									<circle cx="50" cy="50" r="35" fill="none"
											stroke="{status.color}" stroke-width="8"
											stroke-dasharray="{capacity * 2.2} 220"
											stroke-linecap="round"
											transform="rotate(-90 50 50)"/>
									<text x="50" y="50" text-anchor="middle" dy="5"
										  fill="{status.color}" font-size="16" font-weight="600">
										{capacity.toFixed(0)}%
									</text>
								</svg>
							</div>
							<div class="capacity-hosts" style="color: {status.color}">{formatNumber(count)}</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Load Distribution -->
			<div class="chart-panel">
				<h3>LOAD DISTRIBUTION</h3>
				<div class="load-bars">
					{#each facilities.slice(0, 10) as [facility, count], i}
						{@const percentage = Math.min(100, (count / maxHosts) * 100)}
						{@const status = getFacilityStatus(count)}
						<div class="load-bar-item" on:click={() => drillDownFacility(facility, count)}>
							<div class="load-label" title={facility}>{truncateText(facility, 8).toUpperCase()}</div>
							<div class="load-track">
								<div class="load-fill" 
									 style="width: {percentage}%; 
											background: linear-gradient(90deg, {status.color}40, {status.color})">
									<span class="load-value">{formatNumber(count)}</span>
								</div>
							</div>
							<div class="load-icon">{status.icon}</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
		
		<!-- Right: Facility List -->
		<div class="list-panel">
			<div class="panel-header">
				<h3>ALL FACILITIES</h3>
				<span class="facility-count">{facilities.length} ACTIVE</span>
			</div>
			<div class="facility-list">
				<table class="facilities-table">
					<thead>
						<tr>
							<th>#</th>
							<th>FACILITY</th>
							<th>HOSTS</th>
							<th>LOAD</th>
							<th>STATUS</th>
						</tr>
					</thead>
					<tbody>
						{#each facilities as [facility, count], i}
							{@const status = getFacilityStatus(count)}
							{@const capacity = getCapacityLevel(count)}
							<tr on:click={() => drillDownFacility(facility, count)}>
								<td class="rank">{i + 1}</td>
								<td class="facility-name" title={facility}>
									<span class="status-dot" style="color: {status.color}">●</span>
									{truncateText(facility, 18).toUpperCase()}
								</td>
								<td class="host-count" style="color: {status.color}">
									{formatNumber(count)}
								</td>
								<td>
									<div class="mini-bar">
										<div class="mini-fill" style="width: {capacity}%; background: {status.color}"></div>
									</div>
								</td>
								<td>
									<span class="status-label" 
										  style="color: {status.color}; 
												 background: {status.bgColor};
												 border: 1px solid {status.color}">
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
	.datacenter-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		display: flex;
		flex-direction: column;
		padding: 1rem;
		gap: 1rem;
		overflow: hidden;
	}
	
	/* Metrics Ribbon */
	.metrics-ribbon {
		display: flex;
		gap: 1rem;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(139, 233, 253, 0.2);
		border-radius: 12px;
		padding: 1rem;
		flex-shrink: 0;
	}
	
	.metric-box {
		flex: 1;
		text-align: center;
		padding: 0 1rem;
		border-right: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.metric-box:last-child {
		border-right: none;
	}
	
	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
		font-weight: 600;
		margin-bottom: 0.5rem;
	}
	
	.metric-value {
		font-size: 1.8rem;
		font-weight: 700;
		font-family: 'SF Mono', 'Monaco', monospace;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	/* Content Layout */
	.content-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 380px 320px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Network Panel */
	.network-panel {
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
	
	.network-visualization {
		flex: 1;
		position: relative;
		overflow: auto;
	}
	
	.dc-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
		position: relative;
		z-index: 2;
		padding: 0.5rem;
	}
	
	.dc-node {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid;
		border-radius: 10px;
		padding: 0.8rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		overflow: hidden;
	}
	
	.dc-node:hover {
		transform: scale(1.05) translateY(-2px);
		z-index: 10;
		box-shadow: 0 8px 20px rgba(78, 205, 196, 0.4);
	}
	
	.dc-header {
		width: 100%;
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.3rem 0.5rem;
		margin: -0.8rem -0.8rem 0.5rem;
		font-size: 0.65rem;
		font-weight: 600;
	}
	
	.dc-type {
		letter-spacing: 0.05em;
	}
	
	.dc-status {
		font-size: 0.8rem;
	}
	
	.dc-icon {
		width: 50px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.server-stack {
		display: flex;
		flex-direction: column;
		gap: 3px;
		width: 35px;
		background: rgba(255, 255, 255, 0.1);
		padding: 6px;
		border-radius: 4px;
	}
	
	.server-light {
		width: 100%;
		height: 4px;
		border-radius: 2px;
		transition: opacity 0.3s ease;
	}
	
	.dc-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.9);
		text-align: center;
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		width: 100%;
	}
	
	.dc-hosts {
		font-size: 0.85rem;
		font-family: 'SF Mono', 'Monaco', monospace;
		font-weight: 700;
	}
	
	.dc-capacity {
		width: 100%;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.capacity-bar {
		flex: 1;
		height: 5px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		overflow: hidden;
	}
	
	.capacity-fill {
		height: 100%;
		transition: width 0.5s ease;
		border-radius: 3px;
	}
	
	.capacity-text {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.7);
		min-width: 35px;
		font-weight: 600;
	}
	
	.connection-mesh {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
	}
	
	/* Charts Section */
	.charts-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chart-panel {
		flex: 1;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(139, 233, 253, 0.2);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
	}
	
	.chart-panel h3 {
		margin: 0 0 1rem 0;
		font-size: 0.8rem;
		color: #4ECDC4;
		font-weight: 400;
		letter-spacing: 0.1em;
	}
	
	.capacity-chart {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 0.8rem;
		flex: 1;
	}
	
	.capacity-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.3rem;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	.capacity-item:hover {
		transform: scale(1.05);
	}
	
	.capacity-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.7);
		text-align: center;
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		width: 100%;
	}
	
	.capacity-gauge {
		width: 70px;
		height: 70px;
	}
	
	.capacity-gauge svg {
		width: 100%;
		height: 100%;
	}
	
	.capacity-hosts {
		font-size: 0.65rem;
		font-family: 'SF Mono', 'Monaco', monospace;
		font-weight: 700;
	}
	
	.load-bars {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		overflow-y: auto;
	}
	
	.load-bar-item {
		display: grid;
		grid-template-columns: 70px 1fr 25px;
		gap: 0.5rem;
		align-items: center;
		cursor: pointer;
		padding: 0.2rem;
		border-radius: 4px;
		transition: all 0.2s ease;
	}
	
	.load-bar-item:hover {
		background: rgba(139, 233, 253, 0.05);
	}
	
	.load-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
		text-align: right;
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.load-track {
		height: 18px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.load-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.5rem;
		transition: width 0.5s ease;
		border-radius: 4px;
	}
	
	.load-value {
		font-size: 0.6rem;
		color: #FFFFFF;
		font-weight: 700;
		text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
	}
	
	.load-icon {
		font-size: 0.9rem;
		text-align: center;
	}
	
	/* List Panel */
	.list-panel {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(189, 147, 249, 0.2);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		padding: 1rem;
	}
	
	.facility-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
	}
	
	.facility-list {
		flex: 1;
		overflow-y: auto;
		margin-top: 1rem;
	}
	
	.facilities-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.facilities-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.95);
		z-index: 10;
	}
	
	.facilities-table th {
		padding: 0.6rem 0.5rem;
		text-align: left;
		font-size: 0.65rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.facilities-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.facilities-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.08);
		transform: translateX(2px);
	}
	
	.facilities-table td {
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
	
	.facility-name {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.7rem;
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.status-dot {
		font-size: 0.9rem;
		flex-shrink: 0;
	}
	
	.host-count {
		font-family: 'SF Mono', 'Monaco', monospace;
		font-weight: 700;
	}
	
	.mini-bar {
		width: 60px;
		height: 5px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		overflow: hidden;
	}
	
	.mini-fill {
		height: 100%;
		transition: width 0.5s ease;
		border-radius: 3px;
	}
	
	.status-label {
		font-size: 0.6rem;
		font-weight: 700;
		letter-spacing: 0.03em;
		padding: 0.2rem 0.4rem;
		border-radius: 4px;
		white-space: nowrap;
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
	
	.facility-stats {
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
	
	.hosts-list {
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
	
	.status-ind {
		font-size: 0.9rem;
		display: inline-block;
		text-align: center;
	}
	
	.status-ind.active {
		color: #95E77E;
		text-shadow: 0 0 8px #95E77E;
	}
	
	.status-ind.inactive {
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
	
	.dc-loader {
		display: flex;
		gap: 1rem;
		align-items: flex-end;
	}
	
	.server-rack {
		width: 35px;
		background: linear-gradient(180deg, #FF6B9D, #4ECDC4);
		border-radius: 4px;
		animation: rackPulse 1.5s ease-in-out infinite;
	}
	
	.rack-1 {
		height: 60px;
		animation-delay: 0s;
	}
	
	.rack-2 {
		height: 80px;
		animation-delay: 0.3s;
	}
	
	.rack-3 {
		height: 50px;
		animation-delay: 0.6s;
	}
	
	@keyframes rackPulse {
		0%, 100% { opacity: 0.3; transform: scaleY(0.9); }
		50% { opacity: 1; transform: scaleY(1); }
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
		
		.dc-grid {
			grid-template-columns: repeat(3, 1fr);
		}
		
		.capacity-chart {
			grid-template-columns: repeat(3, 1fr);
		}
	}
	
	@media (max-width: 1200px) {
		.content-layout {
			grid-template-columns: 1fr;
			grid-template-rows: 1fr auto;
		}
		
		.charts-section {
			display: grid;
			grid-template-columns: 1fr 1fr;
			grid-template-rows: 1fr;
		}
		
		.list-panel {
			display: none;
		}
		
		.dc-grid {
			grid-template-columns: repeat(4, 1fr);
		}
	}
	
	@media (max-width: 768px) {
		.metrics-ribbon {
			flex-wrap: wrap;
		}
		
		.metric-box {
			min-width: calc(50% - 0.5rem);
			padding: 0.5rem;
			border-right: none;
			border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		}
		
		.metric-value {
			font-size: 1.3rem;
		}
		
		.dc-grid {
			grid-template-columns: repeat(2, 1fr);
		}
		
		.capacity-chart {
			grid-template-columns: repeat(2, 1fr);
		}
		
		.charts-section {
			grid-template-columns: 1fr;
		}
	}
</style>