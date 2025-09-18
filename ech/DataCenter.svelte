<!-- DataCenter.svelte - Data Center Host Distribution -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedFacility = null;
	let facilityDetails = [];
	let searchTerm = '';
	
	// Animation states  
	let animationFrame = null;
	let pulsePhase = 0;
	let connectionFlow = 0;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/data_center_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Data center metrics error:', err);
			loading = false;
		}
		
		// Start animations
		const animate = () => {
			pulsePhase = (pulsePhase + 0.02) % (Math.PI * 2);
			connectionFlow = (connectionFlow + 1) % 100;
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	});
	
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
	
	// Capacity calculations (simulated)
	$: totalCapacity = facilityCount * 5000; // Assume 5000 max per DC
	$: capacityUsed = ((totalHosts / totalCapacity) * 100).toFixed(1);

	async function drillDownFacility(facility, count) {
		selectedFacility = { facility, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(facility)}`);
			let result = await response.json();
			facilityDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Facility drill-down error:', err);
			facilityDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedFacility = null;
		facilityDetails = [];
	}
	
	function getFacilityStatus(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'HIGH LOAD', color: '#BD93F9', icon: '🔴' };
		if (percentage >= 50) return { level: 'OPTIMAL', color: '#8BE9FD', icon: '🟢' };
		if (percentage >= 25) return { level: 'MODERATE', color: '#50FA7B', icon: '🟡' };
		return { level: 'LOW', color: '#FFB86C', icon: '⚪' };
	}
	
	function getCapacityLevel(count) {
		// Simulate capacity based on host count
		const maxCapacity = 5000;
		return Math.min(100, (count / maxCapacity) * 100);
	}
</script>

<div class="datacenter-interface">
	<!-- Top Metrics -->
	<div class="metrics-ribbon">
		<div class="metric-box">
			<div class="metric-label">DATA CENTERS</div>
			<div class="metric-value" style="color: #BD93F9">{facilityCount}</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">TOTAL HOSTS</div>
			<div class="metric-value" style="color: #8BE9FD">{totalHosts.toLocaleString()}</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">TOP FACILITY</div>
			<div class="metric-value" style="color: #50FA7B; font-size: 1.2rem">
				{topFacility[0].substring(0, 20).toUpperCase()}
			</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">AVG HOSTS/DC</div>
			<div class="metric-value" style="color: #FFB86C">{avgHostsPerDC.toLocaleString()}</div>
		</div>
		<div class="metric-box">
			<div class="metric-label">CAPACITY USED</div>
			<div class="metric-value" style="color: #FF79C6">{capacityUsed}%</div>
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
			{:else if selectedFacility}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedFacility.facility.toUpperCase()}</h3>
							<div class="facility-stats">
								<span>{selectedFacility.count.toLocaleString()} HOSTS</span>
								<span>•</span>
								<span>{getCapacityLevel(selectedFacility.count).toFixed(0)}% CAPACITY</span>
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
										<td class="hostname">{host.host}</td>
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
							<div class="dc-node" on:click={() => drillDownFacility(facility, count)}>
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
								<div class="dc-name">{facility.substring(0, 15).toUpperCase()}</div>
								<div class="dc-hosts">{count.toLocaleString()} HOSTS</div>
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
										  stroke="rgba(139, 233, 253, 0.2)" stroke-width="1"
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
						<div class="capacity-item">
							<div class="capacity-label">{facility.substring(0, 10).toUpperCase()}</div>
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
							<div class="capacity-hosts">{count}</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Load Distribution -->
			<div class="chart-panel">
				<h3>LOAD DISTRIBUTION</h3>
				<div class="load-bars">
					{#each facilities.slice(0, 10) as [facility, count], i}
						{@const percentage = (count / maxHosts) * 100}
						{@const status = getFacilityStatus(count)}
						<div class="load-bar-item">
							<div class="load-label">{facility.substring(0, 8).toUpperCase()}</div>
							<div class="load-track">
								<div class="load-fill" 
									 style="width: {percentage}%; 
											background: linear-gradient(90deg, {status.color}40, {status.color})">
									<span class="load-value">{count}</span>
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
								<td class="facility-name">
									<span class="status-dot" style="color: {status.color}">●</span>
									{facility.substring(0, 20).toUpperCase()}
								</td>
								<td class="host-count" style="color: {status.color}">
									{count.toLocaleString()}
								</td>
								<td>
									<div class="mini-bar">
										<div class="mini-fill" style="width: {capacity}%; background: {status.color}"></div>
									</div>
								</td>
								<td>
									<span class="status-label" style="color: {status.color}">
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
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
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
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		font-weight: 600;
		margin-bottom: 0.5rem;
	}
	
	.metric-value {
		font-size: 1.8rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
	}
	
	/* Content Layout */
	.content-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 380px 300px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Network Panel */
	.network-panel {
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
	
	.network-visualization {
		flex: 1;
		position: relative;
	}
	
	.dc-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		grid-template-rows: repeat(3, 1fr);
		gap: 1rem;
		height: 100%;
		position: relative;
		z-index: 2;
	}
	
	.dc-node {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(139, 233, 253, 0.2);
		border-radius: 8px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}
	
	.dc-node:hover {
		background: rgba(139, 233, 253, 0.05);
		border-color: #8BE9FD;
		transform: scale(1.05);
		z-index: 10;
	}
	
	.dc-icon {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.server-stack {
		display: flex;
		flex-direction: column;
		gap: 3px;
		width: 30px;
		background: rgba(255, 255, 255, 0.1);
		padding: 5px;
		border-radius: 4px;
	}
	
	.server-light {
		width: 100%;
		height: 4px;
		border-radius: 1px;
	}
	
	.dc-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.9);
		text-align: center;
		font-weight: 600;
	}
	
	.dc-hosts {
		font-size: 0.8rem;
		color: #8BE9FD;
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.dc-capacity {
		width: 100%;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.capacity-bar {
		flex: 1;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.capacity-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.capacity-text {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		min-width: 30px;
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
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
	}
	
	.chart-panel h3 {
		margin: 0 0 1rem 0;
		font-size: 0.75rem;
		color: #8BE9FD;
		font-weight: 300;
		letter-spacing: 0.1em;
	}
	
	.capacity-chart {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		grid-template-rows: repeat(2, 1fr);
		gap: 0.5rem;
		flex: 1;
	}
	
	.capacity-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}
	
	.capacity-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		text-align: center;
	}
	
	.capacity-gauge {
		width: 60px;
		height: 60px;
	}
	
	.capacity-gauge svg {
		width: 100%;
		height: 100%;
	}
	
	.capacity-hosts {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.7);
		font-family: 'Courier New', monospace;
	}
	
	.load-bars {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	
	.load-bar-item {
		display: grid;
		grid-template-columns: 60px 1fr 20px;
		gap: 0.5rem;
		align-items: center;
	}
	
	.load-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.7);
		text-align: right;
	}
	
	.load-track {
		height: 16px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.load-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.4rem;
		transition: width 0.5s ease;
	}
	
	.load-value {
		font-size: 0.6rem;
		color: #FFFFFF;
		font-weight: 600;
	}
	
	.load-icon {
		font-size: 0.8rem;
		text-align: center;
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
	
	.facility-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.facility-list {
		flex: 1;
		overflow-y: auto;
	}
	
	.facilities-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.facilities-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.9);
		z-index: 10;
	}
	
	.facilities-table th {
		padding: 0.5rem;
		text-align: left;
		font-size: 0.6rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.facilities-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.facilities-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.05);
	}
	
	.facilities-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank {
		color: #BD93F9;
		font-weight: 600;
		font-size: 0.65rem;
	}
	
	.facility-name {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.65rem;
	}
	
	.status-dot {
		font-size: 0.8rem;
	}
	
	.host-count {
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.mini-bar {
		width: 50px;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.mini-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.status-label {
		font-size: 0.6rem;
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
	
	.facility-stats {
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
	
	.hosts-list {
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
	
	.dc-loader {
		display: flex;
		gap: 1rem;
		align-items: flex-end;
	}
	
	.server-rack {
		width: 30px;
		background: linear-gradient(180deg, #BD93F9, #8BE9FD);
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
	
	::-webkit-scrollbar-thumb:hover {
		background: rgba(189, 147, 249, 0.5);
	}
</style>