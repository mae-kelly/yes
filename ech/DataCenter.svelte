<!-- DataCenter.svelte - Quantum Facility Neural Grid Interface -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedFacility = null;
	let facilityDetails = [];
	let searchTerm = '';
	let viewMode = 'neural'; // 'neural', 'thermal', 'quantum'
	let energyField = [];
	let thermalMap = [];
	let quantumNodes = [];
	let pulsePhase = 0;
	let energyFlow = 0;
	let coolingStatus = 'OPTIMAL';
	let networkLatency = [];
	let facilityGrid = [];
	
	// Animation intervals
	let pulseInterval;
	let energyInterval;
	let thermalInterval;
	let networkInterval;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/data_center_metrics');
			let result = await response.json();
			data = result;
			loading = false;
			initializeFacilitySystem();
			startFacilityAnimations();
		} catch (err) {
			console.error('Facility neural grid sync failed:', err);
			loading = false;
		}
	});
	
	onDestroy(() => {
		if (pulseInterval) clearInterval(pulseInterval);
		if (energyInterval) clearInterval(energyInterval);
		if (thermalInterval) clearInterval(thermalInterval);
		if (networkInterval) clearInterval(networkInterval);
	});
	
	function initializeFacilitySystem() {
		// Initialize energy field
		for (let i = 0; i < 100; i++) {
			energyField.push({
				x: Math.random() * 100,
				y: Math.random() * 100,
				z: Math.random() * 100,
				intensity: Math.random(),
				wavelength: 380 + Math.random() * 400, // visible spectrum
				frequency: Math.random() * 1000
			});
		}
		
		// Initialize thermal map
		for (let i = 0; i < 20; i++) {
			thermalMap.push([]);
			for (let j = 0; j < 20; j++) {
				thermalMap[i].push({
					temp: 15 + Math.random() * 25, // 15-40°C
					flow: Math.random(),
					critical: Math.random() > 0.95
				});
			}
		}
		
		// Initialize quantum nodes for facilities
		if (data.facility_intelligence) {
			let facilities = Object.entries(data.facility_intelligence).slice(0, 30);
			facilities.forEach(([facility, count], i) => {
				quantumNodes.push({
					id: facility,
					count: count,
					x: 50 + Math.cos(i * 0.5) * (20 + Math.random() * 30),
					y: 50 + Math.sin(i * 0.5) * (20 + Math.random() * 30),
					energy: Math.random() * 100,
					status: Math.random() > 0.3 ? 'ONLINE' : Math.random() > 0.5 ? 'MAINTENANCE' : 'CRITICAL',
					connections: []
				});
			});
			
			// Create mesh network
			quantumNodes.forEach((node, i) => {
				let connectionCount = 2 + Math.floor(Math.random() * 3);
				for (let j = 0; j < connectionCount; j++) {
					let target = Math.floor(Math.random() * quantumNodes.length);
					if (target !== i) {
						node.connections.push(target);
					}
				}
			});
		}
		
		// Initialize facility grid
		for (let i = 0; i < 10; i++) {
			facilityGrid.push([]);
			for (let j = 0; j < 10; j++) {
				facilityGrid[i].push({
					active: Math.random() > 0.3,
					load: Math.random() * 100,
					type: ['COMPUTE', 'STORAGE', 'NETWORK', 'COOLING'][Math.floor(Math.random() * 4)]
				});
			}
		}
		
		// Initialize network latency
		for (let i = 0; i < 50; i++) {
			networkLatency.push(5 + Math.random() * 45); // 5-50ms
		}
	}
	
	function startFacilityAnimations() {
		pulseInterval = setInterval(() => {
			pulsePhase = (pulsePhase + 2) % 360;
			energyFlow = Math.sin(Date.now() * 0.001) * 50 + 50;
		}, 50);
		
		energyInterval = setInterval(() => {
			energyField = energyField.map(particle => ({
				...particle,
				x: (particle.x + Math.sin(particle.frequency * 0.01) * 0.5 + 100) % 100,
				y: (particle.y + Math.cos(particle.frequency * 0.01) * 0.5 + 100) % 100,
				intensity: (Math.sin(Date.now() * 0.001 + particle.frequency) + 1) * 0.5
			}));
		}, 50);
		
		thermalInterval = setInterval(() => {
			thermalMap = thermalMap.map(row => 
				row.map(cell => ({
					...cell,
					temp: Math.max(15, Math.min(40, cell.temp + (Math.random() - 0.5) * 2)),
					flow: Math.random(),
					critical: cell.temp > 35
				}))
			);
			
			let avgTemp = thermalMap.flat().reduce((sum, cell) => sum + cell.temp, 0) / 400;
			coolingStatus = avgTemp < 25 ? 'OPTIMAL' : avgTemp < 30 ? 'NORMAL' : avgTemp < 35 ? 'WARNING' : 'CRITICAL';
		}, 2000);
		
		networkInterval = setInterval(() => {
			networkLatency = networkLatency.map(() => 5 + Math.random() * 45);
		}, 1000);
	}
	
	$: filteredFacilities = data.facility_intelligence ? 
		Object.entries(data.facility_intelligence)
			.filter(([facility]) => facility.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredFacilities.length > 0 ? Math.max(...filteredFacilities.map(([,c]) => c)) : 1;
	$: minCount = filteredFacilities.length > 0 ? Math.min(...filteredFacilities.map(([,c]) => c)) : 0;
	
	function calculateFacilityMetrics(count) {
		let normalized = (count - minCount) / (maxCount - minCount || 1);
		let percentile = normalized * 100;
		
		let classification = 'UNKNOWN';
		let powerUsage = 0;
		let coolingRequirement = 0;
		let riskLevel = 0;
		let color = '#00ffff';
		let icon = '⚡';
		
		if (percentile >= 80) {
			classification = 'HYPERSCALE';
			powerUsage = 100;
			coolingRequirement = 95;
			riskLevel = 90;
			color = '#ff00ff';
			icon = '◈';
		} else if (percentile >= 60) {
			classification = 'ENTERPRISE';
			powerUsage = 75;
			coolingRequirement = 70;
			riskLevel = 60;
			color = '#ff6600';
			icon = '◆';
		} else if (percentile >= 40) {
			classification = 'REGIONAL';
			powerUsage = 50;
			coolingRequirement = 45;
			riskLevel = 40;
			color = '#00ff00';
			icon = '▲';
		} else if (percentile >= 20) {
			classification = 'EDGE';
			powerUsage = 30;
			coolingRequirement = 25;
			riskLevel = 20;
			color = '#00ffff';
			icon = '●';
		} else {
			classification = 'MICRO';
			powerUsage = 15;
			coolingRequirement = 10;
			riskLevel = 10;
			color = '#0099ff';
			icon = '○';
		}
		
		return {
			classification: classification,
			powerUsage: powerUsage,
			coolingRequirement: coolingRequirement,
			riskLevel: riskLevel,
			color: color,
			icon: icon,
			percentile: percentile.toFixed(1),
			uptime: (99 + Math.random()).toFixed(3),
			latency: (5 + Math.random() * 20).toFixed(1),
			pue: (1.1 + Math.random() * 0.5).toFixed(2), // Power Usage Effectiveness
			capacity: (normalized * 1000).toFixed(0) + ' MW'
		};
	}
	
	function getPercentage(count) {
		let total = Object.values(data.facility_intelligence || {}).reduce((a, b) => a + b, 0);
		return total > 0 ? ((count / total) * 100).toFixed(2) : '0.00';
	}
	
	function getThermalColor(temp) {
		if (temp < 20) return '#0099ff';
		if (temp < 25) return '#00ffff';
		if (temp < 30) return '#00ff00';
		if (temp < 35) return '#ff6600';
		return '#ff0000';
	}
	
	async function drillDownFacility(facility, count) {
		selectedFacility = { facility: facility, count: count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(facility)}`);
			let result = await response.json();
			facilityDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Facility deep scan failed:', err);
			facilityDetails = [];
			loading = false;
		}
	}
	
	function closeDetails() {
		selectedFacility = null;
		facilityDetails = [];
	}
</script>

<div class="quantum-facility-grid">
	<!-- Energy Field Background -->
	<div class="energy-field">
		{#each energyField as particle}
			<div class="energy-particle"
				 style="left: {particle.x}%;
						top: {particle.y}%;
						opacity: {particle.intensity * 0.5};
						background: hsl({particle.wavelength}, 100%, 50%);
						box-shadow: 0 0 {10 * particle.intensity}px hsl({particle.wavelength}, 100%, 50%)">
			</div>
		{/each}
	</div>
	
	<!-- Neural Grid Lines -->
	<svg class="neural-grid-overlay" viewBox="0 0 100 100">
		<defs>
			<linearGradient id="gridGradient" x1="0%" y1="0%" x2="100%" y2="100%">
				<stop offset="0%" style="stop-color:#00ffff;stop-opacity:0.2">
					<animate attributeName="stop-opacity" values="0.2;0.5;0.2" dur="3s" repeatCount="indefinite"/>
				</stop>
				<stop offset="100%" style="stop-color:#ff00ff;stop-opacity:0.2">
					<animate attributeName="stop-opacity" values="0.2;0.5;0.2" dur="3s" begin="1.5s" repeatCount="indefinite"/>
				</stop>
			</linearGradient>
			<filter id="facilityGlow">
				<feGaussianBlur stdDeviation="2" result="coloredBlur"/>
				<feMerge>
					<feMergeNode in="coloredBlur"/>
					<feMergeNode in="SourceGraphic"/>
				</feMerge>
			</filter>
		</defs>
		
		<!-- Animated grid lines -->
		{#each Array(20) as _, i}
			<line x1="0" y1="{i * 5}" x2="100" y2="{i * 5}" 
				  stroke="url(#gridGradient)" stroke-width="0.1" opacity="{0.2 + Math.sin(pulsePhase * Math.PI / 180 + i * 0.1) * 0.1}"/>
			<line x1="{i * 5}" y1="0" x2="{i * 5}" y2="100" 
				  stroke="url(#gridGradient)" stroke-width="0.1" opacity="{0.2 + Math.cos(pulsePhase * Math.PI / 180 + i * 0.1) * 0.1}"/>
		{/each}
	</svg>
	
	<div class="facility-interface">
		<!-- Quantum Header -->
		<header class="facility-header">
			<div class="header-left">
				<div class="facility-logo">
					<div class="logo-core" style="transform: rotate({pulsePhase}deg)">
						<div class="core-ring ring-1"></div>
						<div class="core-ring ring-2"></div>
						<div class="core-center">⚡</div>
					</div>
				</div>
				<div class="header-info">
					<h1 class="facility-title">GLOBAL FACILITY NEURAL GRID</h1>
					<div class="system-status">
						<span class="status-dot {coolingStatus.toLowerCase()}"></span>
						<span class="status-text">COOLING: {coolingStatus}</span>
						<span class="divider">|</span>
						<span class="energy-text">ENERGY FLOW: {energyFlow.toFixed(0)}%</span>
					</div>
				</div>
			</div>
			
			<div class="control-panel">
				<input 
					type="text" 
					bind:value={searchTerm}
					placeholder="FACILITY SEARCH..."
					class="facility-search"
				/>
				<div class="search-beam" style="width: {searchTerm ? '100%' : '0'}"></div>
			</div>
			
			<div class="view-selector">
				<button class="view-btn {viewMode === 'neural' ? 'active' : ''}"
						on:click={() => viewMode = 'neural'}>
					<span class="view-icon">◈</span>
					NEURAL
				</button>
				<button class="view-btn {viewMode === 'thermal' ? 'active' : ''}"
						on:click={() => viewMode = 'thermal'}>
					<span class="view-icon">🔥</span>
					THERMAL
				</button>
				<button class="view-btn {viewMode === 'quantum' ? 'active' : ''}"
						on:click={() => viewMode = 'quantum'}>
					<span class="view-icon">⚡</span>
					QUANTUM
				</button>
			</div>
			
			<div class="metrics-panel">
				<div class="metric">
					<div class="metric-value">{filteredFacilities.length}</div>
					<div class="metric-label">FACILITIES</div>
				</div>
				<div class="metric">
					<div class="metric-value">{Object.values(data.facility_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="metric-label">NODES</div>
				</div>
			</div>
		</header>
		
		<!-- Main Content -->
		<div class="facility-content">
			{#if loading && !selectedFacility}
				<div class="facility-loader">
					<div class="loader-reactor">
						<div class="reactor-core"></div>
						<div class="reactor-wave wave-1"></div>
						<div class="reactor-wave wave-2"></div>
						<div class="reactor-wave wave-3"></div>
					</div>
					<p class="loader-text">INITIALIZING FACILITY NEURAL GRID...</p>
				</div>
			{:else if selectedFacility}
				{#key selectedFacility}
				<div class="facility-detail-view">
					<div class="detail-header">
						<div class="facility-hologram">
							<div class="hologram-icon" style="color: {calculateFacilityMetrics(selectedFacility.count).color}">
								{calculateFacilityMetrics(selectedFacility.count).icon}
							</div>
							<div class="facility-info">
								<h2>{selectedFacility.facility.toUpperCase()}</h2>
								<div class="facility-stats">
									<span class="stat">PUE: {calculateFacilityMetrics(selectedFacility.count).pue}</span>
									<span class="stat">UPTIME: {calculateFacilityMetrics(selectedFacility.count).uptime}%</span>
									<span class="stat">CAPACITY: {calculateFacilityMetrics(selectedFacility.count).capacity}</span>
								</div>
							</div>
						</div>
						<button class="facility-close" on:click={closeDetails}>
							<span>✕</span>
						</button>
					</div>
					
					<div class="facility-metrics">
						<div class="metric-card">
							<div class="card-value" style="color: {calculateFacilityMetrics(selectedFacility.count).color}">
								{selectedFacility.count.toLocaleString()}
							</div>
							<div class="card-label">ACTIVE NODES</div>
						</div>
						<div class="metric-card">
							<div class="card-value" style="color: {calculateFacilityMetrics(selectedFacility.count).color}">
								{getPercentage(selectedFacility.count)}%
							</div>
							<div class="card-label">NETWORK SHARE</div>
						</div>
						<div class="metric-card">
							<div class="card-value" style="color: {calculateFacilityMetrics(selectedFacility.count).color}">
								{calculateFacilityMetrics(selectedFacility.count).classification}
							</div>
							<div class="card-label">TIER CLASS</div>
						</div>
						<div class="metric-card">
							<div class="card-value" style="color: {calculateFacilityMetrics(selectedFacility.count).color}">
								{calculateFacilityMetrics(selectedFacility.count).latency}ms
							</div>
							<div class="card-label">AVG LATENCY</div>
						</div>
					</div>
					
					<div class="facility-stream">
						<table class="stream-table">
							<thead>
								<tr>
									<th>NODE_ID</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>INFRASTRUCTURE</th>
									<th>CMDB_STATUS</th>
									<th>TANIUM_SHIELD</th>
								</tr>
							</thead>
							<tbody>
								{#each facilityDetails as host}
									<tr class="stream-row">
										<td class="node-id">{host.host.substring(0, 25)}</td>
										<td>{host.region || 'UNKNOWN'}</td>
										<td>{host.country || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>
											<span class="status-indicator {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'online' : 'offline'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}
											</span>
										</td>
										<td>
											<span class="status-indicator {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'secured' : 'vulnerable'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? '⬢' : '⬡'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
				{/key}
			{:else if viewMode === 'neural'}
				<div class="neural-view">
					<div class="neural-map">
						<svg class="neural-svg" viewBox="0 0 100 100">
							<!-- Connections -->
							{#each quantumNodes as node, i}
								{#each node.connections as targetIdx}
									{#if targetIdx < quantumNodes.length}
										<line x1="{node.x}" y1="{node.y}"
											  x2="{quantumNodes[targetIdx].x}" y2="{quantumNodes[targetIdx].y}"
											  stroke="{node.status === 'ONLINE' ? '#00ffff' : node.status === 'MAINTENANCE' ? '#ff6600' : '#ff0000'}"
											  stroke-width="0.2"
											  opacity="{0.3 + node.energy / 200}">
											<animate attributeName="stroke-dasharray" 
													 values="0,5;5,0" 
													 dur="2s" 
													 repeatCount="indefinite"/>
										</line>
									{/if}
								{/each}
							{/each}
							
							<!-- Facility Nodes -->
							{#each filteredFacilities.slice(0, 20) as [facility, count], i}
								{#key facility}
								<g class="facility-node"
								   transform="translate({50 + Math.cos(i * Math.PI / 10) * 35}, {50 + Math.sin(i * Math.PI / 10) * 35})"
								   on:click={() => drillDownFacility(facility, count)}>
									<circle r="{3 + calculateFacilityMetrics(count).powerUsage * 0.05}"
											fill="{calculateFacilityMetrics(count).color}"
											opacity="0.8"
											filter="url(#facilityGlow)">
										<animate attributeName="r" 
												 values="{3 + calculateFacilityMetrics(count).powerUsage * 0.05};{4 + calculateFacilityMetrics(count).powerUsage * 0.05};{3 + calculateFacilityMetrics(count).powerUsage * 0.05}"
												 dur="3s" 
												 repeatCount="indefinite"/>
									</circle>
									<text y="-5" text-anchor="middle" fill="#ffffff" font-size="2" opacity="0.8">
										{facility.substring(0, 10)}
									</text>
								</g>
								{/key}
							{/each}
							
							<!-- Central Core -->
							<circle cx="50" cy="50" r="5" fill="#00ffff" opacity="0.5">
								<animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite"/>
							</circle>
							<text x="50" y="51" text-anchor="middle" fill="#ffffff" font-size="3">CORE</text>
						</svg>
					</div>
				</div>
			{:else if viewMode === 'thermal'}
				<div class="thermal-view">
					<div class="thermal-container">
						<div class="thermal-grid">
							{#each thermalMap as row, i}
								{#each row as cell, j}
									<div class="thermal-cell"
										 style="left: {j * 5}%;
												top: {i * 5}%;
												background: {getThermalColor(cell.temp)};
												opacity: {0.5 + cell.flow * 0.5};
												box-shadow: {cell.critical ? `0 0 10px ${getThermalColor(cell.temp)}` : 'none'}">
										{#if cell.critical}
											<span class="critical-marker">!</span>
										{/if}
									</div>
								{/each}
							{/each}
						</div>
						<div class="thermal-legend">
							<div class="legend-item">
								<div class="legend-color" style="background: #0099ff"></div>
								<span>&lt;20°C</span>
							</div>
							<div class="legend-item">
								<div class="legend-color" style="background: #00ffff"></div>
								<span>20-25°C</span>
							</div>
							<div class="legend-item">
								<div class="legend-color" style="background: #00ff00"></div>
								<span>25-30°C</span>
							</div>
							<div class="legend-item">
								<div class="legend-color" style="background: #ff6600"></div>
								<span>30-35°C</span>
							</div>
							<div class="legend-item">
								<div class="legend-color" style="background: #ff0000"></div>
								<span>&gt;35°C</span>
							</div>
						</div>
					</div>
				</div>
			{:else if viewMode === 'quantum'}
				<div class="quantum-view">
					<div class="quantum-container">
						{#each facilityGrid as row, i}
							{#each row as cell, j}
								{#if cell.active}
									<div class="quantum-cell"
										 style="left: {j * 10}%;
												top: {i * 10}%;
												background: {cell.type === 'COMPUTE' ? '#00ffff' : 
															  cell.type === 'STORAGE' ? '#ff00ff' :
															  cell.type === 'NETWORK' ? '#00ff00' : '#ff6600'};
												opacity: {0.3 + cell.load / 200}">
										<div class="cell-load">{cell.load.toFixed(0)}%</div>
										<div class="cell-type">{cell.type}</div>
									</div>
								{/if}
							{/each}
						{/each}
						
						<!-- Network Latency Graph -->
						<div class="latency-graph">
							<svg viewBox="0 0 200 50">
								<polyline points="{networkLatency.map((lat, i) => `${i * 4},${50 - lat}`).join(' ')}"
										  fill="none" 
										  stroke="#00ffff" 
										  stroke-width="1"
										  opacity="0.8"/>
							</svg>
							<div class="latency-label">NETWORK LATENCY</div>
						</div>
					</div>
				</div>
			{/if}
			
			<!-- Facility Data Matrix -->
			<div class="facility-data-matrix">
				<table class="matrix-table">
					<thead>
						<tr>
							<th>RANK</th>
							<th>FACILITY</th>
							<th>TIER</th>
							<th>NODES</th>
							<th>SHARE</th>
							<th>POWER</th>
							<th>COOLING</th>
							<th>RISK</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredFacilities as [facility, count], index}
							{#key facility}
							<tr class="matrix-row"
								style="border-left: 3px solid {calculateFacilityMetrics(count).color}"
								on:click={() => drillDownFacility(facility, count)}>
								<td class="rank-cell">
									<span style="color: {calculateFacilityMetrics(count).color}">#{index + 1}</span>
								</td>
								<td class="facility-cell">
									<span class="facility-icon" style="color: {calculateFacilityMetrics(count).color}">
										{calculateFacilityMetrics(count).icon}
									</span>
									<span class="facility-name">{facility.substring(0, 25).toUpperCase()}</span>
								</td>
								<td>
									<span class="tier-badge" style="background: {calculateFacilityMetrics(count).color}15; 
												   color: {calculateFacilityMetrics(count).color}; 
												   border: 1px solid {calculateFacilityMetrics(count).color}">
										{calculateFacilityMetrics(count).classification}
									</span>
								</td>
								<td class="numeric">{count.toLocaleString()}</td>
								<td class="share-cell">
									<div class="share-bar">
										<div class="share-fill" style="width: {getPercentage(count)}%; 
																	   background: linear-gradient(90deg, transparent, {calculateFacilityMetrics(count).color})"></div>
									</div>
									<span class="share-text">{getPercentage(count)}%</span>
								</td>
								<td>
									<div class="power-meter">
										<div class="power-level" style="width: {calculateFacilityMetrics(count).powerUsage}%; 
																		 background: {calculateFacilityMetrics(count).color}"></div>
									</div>
									<span class="power-text">{calculateFacilityMetrics(count).powerUsage}%</span>
								</td>
								<td>
									<div class="cooling-meter">
										<div class="cooling-level" style="height: {calculateFacilityMetrics(count).coolingRequirement}%; 
																		  background: {calculateFacilityMetrics(count).color}"></div>
									</div>
									<span class="cooling-text">{calculateFacilityMetrics(count).coolingRequirement}%</span>
								</td>
								<td>
									<span class="risk-indicator" style="color: {calculateFacilityMetrics(count).riskLevel > 60 ? '#ff0000' : 
																				 calculateFacilityMetrics(count).riskLevel > 40 ? '#ff6600' : 
																				 '#00ff00'}">
										{calculateFacilityMetrics(count).riskLevel}%
									</span>
								</td>
							</tr>
							{/key}
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>
</div>

<style>
	.quantum-facility-grid {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		position: relative;
		overflow: hidden;
	}
	
	/* Energy Field */
	.energy-field {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	
	.energy-particle {
		position: absolute;
		width: 2px;
		height: 2px;
		border-radius: 50%;
		animation: energyFloat 10s linear infinite;
	}
	
	@keyframes energyFloat {
		0% { transform: translate(0, 0) scale(1); }
		25% { transform: translate(20px, -20px) scale(1.2); }
		50% { transform: translate(-20px, 20px) scale(0.8); }
		75% { transform: translate(15px, 15px) scale(1.1); }
		100% { transform: translate(0, 0) scale(1); }
	}
	
	/* Neural Grid Overlay */
	.neural-grid-overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	
	.facility-interface {
		position: relative;
		z-index: 1;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
	
	/* Facility Header */
	.facility-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.1), rgba(0, 0, 0, 0.9));
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		backdrop-filter: blur(20px);
		flex-wrap: wrap;
		gap: 1rem;
	}
	
	.header-left {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.facility-logo {
		width: 60px;
		height: 60px;
		position: relative;
	}
	
	.logo-core {
		width: 100%;
		height: 100%;
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.core-ring {
		position: absolute;
		border: 1px solid;
		border-radius: 50%;
		animation: ringPulse 3s ease-in-out infinite;
	}
	
	.ring-1 {
		inset: 0;
		border-color: #00ffff;
	}
	
	.ring-2 {
		inset: 10px;
		border-color: #ff00ff;
		animation-delay: 0.5s;
	}
	
	.core-center {
		font-size: 1.5rem;
		color: #00ffff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
		z-index: 1;
	}
	
	@keyframes ringPulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.2); opacity: 0.5; }
	}
	
	.header-info h1 {
		margin: 0;
		font-size: 1.3rem;
		font-weight: 200;
		letter-spacing: 0.2em;
		background: linear-gradient(90deg, #00ffff, #ff00ff, #00ffff);
		background-size: 200% 100%;
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		animation: gradientShift 5s linear infinite;
	}
	
	@keyframes gradientShift {
		0% { background-position: 0% 50%; }
		100% { background-position: 200% 50%; }
	}
	
	.system-status {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-top: 0.5rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
		letter-spacing: 0.1em;
	}
	
	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: statusBlink 2s ease-in-out infinite;
	}
	
	.status-dot.optimal { background: #00ff00; box-shadow: 0 0 10px #00ff00; }
	.status-dot.normal { background: #00ffff; box-shadow: 0 0 10px #00ffff; }
	.status-dot.warning { background: #ff6600; box-shadow: 0 0 10px #ff6600; }
	.status-dot.critical { background: #ff0000; box-shadow: 0 0 10px #ff0000; animation-duration: 0.5s; }
	
	@keyframes statusBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}
	
	.divider {
		color: rgba(255, 255, 255, 0.3);
	}
	
	/* Control Panel */
	.control-panel {
		position: relative;
		flex: 1;
		max-width: 400px;
	}
	
	.facility-search {
		width: 100%;
		padding: 0.75rem 1rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.3);
		color: #00ffff;
		font-family: 'Courier New', monospace;
		font-size: 0.9rem;
		letter-spacing: 0.1em;
		transition: all 0.3s ease;
	}
	
	.facility-search:focus {
		outline: none;
		border-color: #00ffff;
		background: rgba(0, 255, 255, 0.05);
		box-shadow: 0 0 30px rgba(0, 255, 255, 0.3);
	}
	
	.search-beam {
		position: absolute;
		bottom: 0;
		left: 0;
		height: 2px;
		background: linear-gradient(90deg, transparent, #00ffff, transparent);
		transition: width 0.3s ease;
		animation: beamPulse 2s linear infinite;
	}
	
	@keyframes beamPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}
	
	/* View Selector */
	.view-selector {
		display: flex;
		gap: 0.25rem;
		background: rgba(0, 0, 0, 0.8);
		padding: 0.25rem;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.view-btn {
		padding: 0.5rem 0.75rem;
		background: transparent;
		border: 1px solid transparent;
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.75rem;
		letter-spacing: 0.1em;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.view-btn:hover {
		background: rgba(0, 255, 255, 0.05);
		border-color: rgba(0, 255, 255, 0.3);
	}
	
	.view-btn.active {
		background: rgba(0, 255, 255, 0.1);
		border-color: #00ffff;
		color: #00ffff;
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
	}
	
	.view-icon {
		font-size: 1rem;
	}
	
	/* Metrics Panel */
	.metrics-panel {
		display: flex;
		gap: 2rem;
	}
	
	.metric {
		text-align: center;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: 100;
		color: #00ffff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
		font-family: 'Courier New', monospace;
	}
	
	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.2em;
		margin-top: 0.25rem;
	}
	
	/* Facility Content */
	.facility-content {
		flex: 1;
		display: flex;
		gap: 2rem;
		padding: 2rem;
		overflow: hidden;
	}
	
	/* Loader */
	.facility-loader {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.loader-reactor {
		position: relative;
		width: 120px;
		height: 120px;
	}
	
	.reactor-core {
		position: absolute;
		inset: 40px;
		background: radial-gradient(circle, #00ffff, transparent);
		border-radius: 50%;
		animation: corePulse 2s ease-in-out infinite;
	}
	
	.reactor-wave {
		position: absolute;
		inset: 0;
		border: 2px solid #00ffff;
		border-radius: 50%;
		opacity: 0;
		animation: waveExpand 3s ease-out infinite;
	}
	
	.wave-2 { animation-delay: 1s; }
	.wave-3 { animation-delay: 2s; }
	
	@keyframes corePulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.2); }
	}
	
	@keyframes waveExpand {
		0% { transform: scale(0.5); opacity: 1; }
		100% { transform: scale(2); opacity: 0; }
	}
	
	.loader-text {
		color: rgba(0, 255, 255, 0.6);
		font-size: 0.9rem;
		letter-spacing: 0.2em;
		animation: pulse 2s ease-in-out infinite;
	}
	
	/* Neural View */
	.neural-view {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.neural-map {
		width: 100%;
		height: 100%;
		max-width: 600px;
		max-height: 600px;
	}
	
	.neural-svg {
		width: 100%;
		height: 100%;
	}
	
	.facility-node {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.facility-node:hover {
		transform: scale(1.2);
	}
	
	/* Thermal View */
	.thermal-view {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.thermal-container {
		width: 100%;
		height: 100%;
		max-width: 600px;
		max-height: 600px;
		position: relative;
	}
	
	.thermal-grid {
		width: 100%;
		height: 100%;
		position: relative;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(0, 255, 255, 0.2);
	}
	
	.thermal-cell {
		position: absolute;
		width: 5%;
		height: 5%;
		border: 1px solid rgba(0, 0, 0, 0.2);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.5s ease;
	}
	
	.critical-marker {
		color: #ffffff;
		font-weight: bold;
		font-size: 0.8rem;
		text-shadow: 0 0 5px rgba(255, 255, 255, 0.8);
	}
	
	.thermal-legend {
		position: absolute;
		bottom: -40px;
		left: 0;
		right: 0;
		display: flex;
		justify-content: center;
		gap: 1rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.legend-color {
		width: 20px;
		height: 10px;
		border: 1px solid rgba(255, 255, 255, 0.3);
	}
	
	/* Quantum View */
	.quantum-view {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.quantum-container {
		width: 100%;
		height: 100%;
		max-width: 600px;
		max-height: 600px;
		position: relative;
	}
	
	.quantum-cell {
		position: absolute;
		width: 9%;
		height: 9%;
		border: 1px solid rgba(255, 255, 255, 0.2);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		font-size: 0.6rem;
		color: #ffffff;
		transition: all 0.3s ease;
		cursor: pointer;
	}
	
	.quantum-cell:hover {
		transform: scale(1.1);
		z-index: 10;
		box-shadow: 0 0 20px currentColor;
	}
	
	.cell-load {
		font-weight: bold;
		font-size: 0.8rem;
	}
	
	.cell-type {
		font-size: 0.5rem;
		opacity: 0.7;
	}
	
	.latency-graph {
		position: absolute;
		bottom: 10px;
		left: 10px;
		right: 10px;
		height: 60px;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.3);
		padding: 5px;
	}
	
	.latency-graph svg {
		width: 100%;
		height: 100%;
	}
	
	.latency-label {
		position: absolute;
		top: 5px;
		left: 10px;
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}
	
	/* Facility Data Matrix */
	.facility-data-matrix {
		width: 50%;
		overflow: auto;
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid rgba(0, 255, 255, 0.1);
		backdrop-filter: blur(10px);
	}
	
	.matrix-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.matrix-table th {
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.1), rgba(0, 0, 0, 0.8));
		color: #00ffff;
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 300;
		letter-spacing: 0.15em;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		position: sticky;
		top: 0;
		z-index: 10;
	}
	
	.matrix-row {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.matrix-row:hover {
		background: rgba(0, 255, 255, 0.02);
		transform: translateX(5px);
	}
	
	.matrix-table td {
		padding: 0.5rem 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank-cell {
		font-weight: 600;
		font-family: 'Courier New', monospace;
	}
	
	.facility-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.facility-icon {
		font-size: 1rem;
	}
	
	.facility-name {
		font-weight: 300;
		letter-spacing: 0.05em;
	}
	
	.tier-badge {
		padding: 0.2rem 0.4rem;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
	}
	
	.numeric {
		font-family: 'Courier New', monospace;
		color: #00ffff;
	}
	
	.share-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.share-bar {
		width: 60px;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}
	
	.share-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.share-text {
		font-size: 0.7rem;
		min-width: 40px;
		text-align: right;
		color: rgba(255, 255, 255, 0.6);
	}
	
	.power-meter, .cooling-meter {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
	}
	
	.power-meter {
		width: 40px;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}
	
	.power-level {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.cooling-meter {
		width: 15px;
		height: 15px;
		background: rgba(255, 255, 255, 0.1);
		position: relative;
		border: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.cooling-level {
		position: absolute;
		bottom: 0;
		left: 0;
		width: 100%;
		transition: height 0.5s ease;
	}
	
	.power-text, .cooling-text {
		font-size: 0.65rem;
		font-family: 'Courier New', monospace;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.risk-indicator {
		font-weight: 600;
		font-size: 0.75rem;
	}
	
	/* Detail View */
	.facility-detail-view {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 0, 0, 0.9));
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
	}
	
	.facility-hologram {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.hologram-icon {
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2.5rem;
		background: radial-gradient(circle, currentColor 0%, transparent 70%);
		animation: hologramRotate 4s linear infinite;
	}
	
	@keyframes hologramRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.facility-info h2 {
		margin: 0;
		font-size: 1.3rem;
		font-weight: 200;
		color: #00ffff;
		letter-spacing: 0.1em;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
	}
	
	.facility-stats {
		display: flex;
		gap: 1rem;
		margin-top: 0.5rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.stat {
		padding: 0.25rem 0.5rem;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(0, 255, 255, 0.2);
	}
	
	.facility-close {
		background: none;
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.3s ease;
		font-size: 1.5rem;
	}
	
	.facility-close:hover {
		background: rgba(255, 0, 102, 0.1);
		box-shadow: 0 0 20px rgba(255, 0, 102, 0.5);
		transform: rotate(90deg);
	}
	
	.facility-metrics {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
		padding: 1.5rem;
		background: rgba(0, 0, 0, 0.5);
	}
	
	.metric-card {
		text-align: center;
		padding: 1rem;
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.05), transparent);
		border: 1px solid rgba(0, 255, 255, 0.2);
	}
	
	.card-value {
		font-size: 1.5rem;
		font-weight: 100;
		margin-bottom: 0.5rem;
		text-shadow: 0 0 20px currentColor;
	}
	
	.card-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}
	
	.facility-stream {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}
	
	.stream-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.stream-table th {
		background: rgba(0, 0, 0, 0.8);
		color: #00ffff;
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 300;
		letter-spacing: 0.1em;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		position: sticky;
		top: 0;
	}
	
	.stream-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.2s ease;
	}
	
	.stream-row:hover {
		background: rgba(0, 255, 255, 0.02);
	}
	
	.stream-table td {
		padding: 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.node-id {
		font-family: 'Courier New', monospace;
		color: #00ffff;
		font-size: 0.7rem;
	}
	
	.status-indicator {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		font-size: 1rem;
	}
	
	.status-indicator.online {
		color: #00ff00;
		text-shadow: 0 0 10px #00ff00;
	}
	
	.status-indicator.offline {
		color: #666666;
	}
	
	.status-indicator.secured {
		color: #00ffff;
		text-shadow: 0 0 10px #00ffff;
	}
	
	.status-indicator.vulnerable {
		color: #ff0066;
		text-shadow: 0 0 10px #ff0066;
	}
	
	/* Responsive */
	@media (max-width: 1400px) {
		.facility-content {
			flex-direction: column;
		}
		
		.facility-data-matrix {
			width: 100%;
			max-height: 300px;
		}
	}
	
	@media (max-width: 768px) {
		.facility-header {
			flex-direction: column;
			align-items: stretch;
		}
		
		.facility-metrics {
			grid-template-columns: repeat(2, 1fr);
		}
		
		.control-panel {
			max-width: 100%;
		}
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 6px;
		height: 6px;
	}
	
	::-webkit-scrollbar-track {
		background: #000000;
	}
	
	::-webkit-scrollbar-thumb {
		background: linear-gradient(180deg, #00ffff, #ff00ff);
		border-radius: 0;
	}
	
	::-webkit-scrollbar-corner {
		background: #000000;
	}
</style>