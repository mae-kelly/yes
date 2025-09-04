<!-- DataCenter.svelte - Quantum Facility Neural Grid Interface -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedFacility = null;
	let facilityDetails = [];
	let searchTerm = '';
	
	// Visualization states
	let viewMode = 'thermal'; // 'thermal', 'network', 'power', 'quantum'
	let facilityNodes = [];
	let thermalGrid = [];
	let powerGrid = [];
	let networkTopology = [];
	let quantumField = [];
	let energyFlow = 0;
	let coolingEfficiency = 0;
	let networkLatency = 0;
	let powerUsage = 0;
	let quantumState = 'INITIALIZING';
	
	// 3D visualization
	let rotationX = 0;
	let rotationY = 0;
	let rotationZ = 0;
	
	// Animation references
	let animationFrameId;
	let intervals = [];
	
	// Neon pastel colors optimized for data centers
	const neonColors = {
		primary: '#00FFFF',     // Cyan (cooling)
		secondary: '#FF00FF',    // Magenta (power)
		tertiary: '#00FF00',     // Green (network)
		quaternary: '#FFFF00',   // Yellow (warning)
		cold: '#0088FF',         // Blue (cold zones)
		hot: '#FF0088',          // Red-pink (hot zones)
		optimal: '#00FFAA',      // Mint (optimal)
		critical: '#FF0044',     // Red (critical)
		warning: '#FFAA00',      // Orange (warning)
		safe: '#00FF88'          // Green-cyan (safe)
	};
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/data_center_metrics');
			let result = await response.json();
			data = result;
			loading = false;
			quantumState = 'SYNCHRONIZED';
			initializeVisualization();
			startAnimations();
		} catch (err) {
			console.error('Facility neural grid sync failed:', err);
			loading = false;
			quantumState = 'DESYNCHRONIZED';
		}
	});
	
	onDestroy(() => {
		if (animationFrameId) cancelAnimationFrame(animationFrameId);
		intervals.forEach(interval => clearInterval(interval));
	});
	
	function initializeVisualization() {
		if (!data.facility_intelligence) return;
		
		// Create facility nodes with 3D positions
		let facilities = Object.entries(data.facility_intelligence);
		let maxCount = Math.max(...facilities.map(([,c]) => c));
		
		facilities.forEach(([facility, count], i) => {
			let importance = count / maxCount;
			
			// Create 3D datacenter layout
			let row = Math.floor(i / 5);
			let col = i % 5;
			let layer = Math.floor(i / 25);
			
			facilityNodes.push({
				id: i,
				name: facility,
				count: count,
				importance: importance,
				x: (col - 2) * 100,
				y: (row - 2) * 100,
				z: layer * 100,
				temperature: 15 + Math.random() * 25,
				powerDraw: importance * 1000 + Math.random() * 500,
				networkLoad: Math.random() * 100,
				coolingStatus: Math.random() > 0.1 ? 'OPTIMAL' : 'WARNING',
				uptime: 99 + Math.random(),
				pue: 1.1 + Math.random() * 0.5,
				color: interpolateThermalColor(15 + Math.random() * 25)
			});
		});
		
		// Initialize thermal grid (20x20)
		for (let i = 0; i < 20; i++) {
			thermalGrid.push([]);
			for (let j = 0; j < 20; j++) {
				thermalGrid[i].push({
					temp: 15 + Math.random() * 25,
					airflow: Math.random(),
					hotspot: Math.random() > 0.95,
					coolingZone: Math.random() > 0.8
				});
			}
		}
		
		// Initialize power grid
		for (let i = 0; i < 10; i++) {
			powerGrid.push({
				id: i,
				name: `PDU-${i + 1}`,
				load: Math.random() * 100,
				voltage: 380 + Math.random() * 40,
				current: Math.random() * 1000,
				efficiency: 85 + Math.random() * 15,
				redundancy: Math.random() > 0.5 ? 'N+1' : '2N',
				status: Math.random() > 0.1 ? 'ONLINE' : 'MAINTENANCE'
			});
		}
		
		// Initialize network topology
		facilityNodes.forEach((node, i) => {
			networkTopology.push({
				source: node,
				connections: [],
				bandwidth: 10 + Math.random() * 90, // Gbps
				packets: Math.random() * 1000000,
				latency: 0.5 + Math.random() * 9.5,
				packetLoss: Math.random() * 0.1
			});
			
			// Create mesh connections
			facilityNodes.forEach((target, j) => {
				if (i !== j && Math.random() > 0.7) {
					networkTopology[i].connections.push({
						target: j,
						bandwidth: Math.random() * 100,
						latency: Math.random() * 10,
						active: true
					});
				}
			});
		});
		
		// Initialize quantum field
		for (let i = 0; i < 100; i++) {
			quantumField.push({
				x: Math.random() * window.innerWidth,
				y: Math.random() * window.innerHeight,
				z: Math.random() * 200 - 100,
				vx: (Math.random() - 0.5) * 2,
				vy: (Math.random() - 0.5) * 2,
				vz: (Math.random() - 0.5) * 1,
				energy: Math.random() * 100,
				type: ['thermal', 'power', 'network', 'quantum'][Math.floor(Math.random() * 4)],
				color: Object.values(neonColors)[Math.floor(Math.random() * 10)]
			});
		}
	}
	
	function interpolateThermalColor(temp) {
		if (temp < 18) return neonColors.cold;
		if (temp < 22) return neonColors.optimal;
		if (temp < 28) return neonColors.primary;
		if (temp < 35) return neonColors.warning;
		return neonColors.hot;
	}
	
	function startAnimations() {
		// Main animation loop
		function animate() {
			updateThermalGrid();
			updatePowerMetrics();
			updateNetworkTopology();
			updateQuantumField();
			
			energyFlow = 50 + Math.sin(Date.now() * 0.001) * 50;
			coolingEfficiency = 70 + Math.sin(Date.now() * 0.0008) * 30;
			networkLatency = 5 + Math.sin(Date.now() * 0.0012) * 5;
			powerUsage = 60 + Math.sin(Date.now() * 0.0006) * 40;
			
			rotationY = (rotationY + 0.2) % 360;
			
			animationFrameId = requestAnimationFrame(animate);
		}
		animate();
		
		// Quantum state updates
		intervals.push(setInterval(() => {
			quantumState = ['SYNCHRONIZED', 'PROCESSING', 'OPTIMIZING', 'ANALYZING', 'COOLING'][
				Math.floor(Math.random() * 5)
			];
		}, 3000));
	}
	
	function updateThermalGrid() {
		thermalGrid = thermalGrid.map(row => 
			row.map(cell => {
				// Simulate heat diffusion
				let newTemp = cell.temp + (Math.random() - 0.5) * 2;
				newTemp = Math.max(15, Math.min(40, newTemp));
				
				return {
					...cell,
					temp: newTemp,
					airflow: Math.max(0, Math.min(1, cell.airflow + (Math.random() - 0.5) * 0.1)),
					hotspot: newTemp > 35
				};
			})
		);
	}
	
	function updatePowerMetrics() {
		powerGrid = powerGrid.map(pdu => ({
			...pdu,
			load: Math.max(0, Math.min(100, pdu.load + (Math.random() - 0.5) * 10)),
			voltage: 380 + Math.random() * 40,
			current: Math.max(0, pdu.current + (Math.random() - 0.5) * 100)
		}));
	}
	
	function updateNetworkTopology() {
		networkTopology = networkTopology.map(node => ({
			...node,
			bandwidth: Math.max(0, Math.min(100, node.bandwidth + (Math.random() - 0.5) * 5)),
			packets: Math.max(0, node.packets + (Math.random() - 0.5) * 100000),
			latency: Math.max(0.5, Math.min(10, node.latency + (Math.random() - 0.5)))
		}));
	}
	
	function updateQuantumField() {
		quantumField = quantumField.map(particle => {
			// Apply forces
			particle.vx += (Math.random() - 0.5) * 0.1;
			particle.vy += (Math.random() - 0.5) * 0.1;
			particle.vz += (Math.random() - 0.5) * 0.05;
			
			// Update position
			particle.x = (particle.x + particle.vx + window.innerWidth) % window.innerWidth;
			particle.y = (particle.y + particle.vy + window.innerHeight) % window.innerHeight;
			particle.z = (particle.z + particle.vz + 200) % 200 - 100;
			
			// Damping
			particle.vx *= 0.99;
			particle.vy *= 0.99;
			particle.vz *= 0.99;
			
			return particle;
		});
	}
	
	$: filteredFacilities = data.facility_intelligence ? 
		Object.entries(data.facility_intelligence)
			.filter(([facility]) => facility.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredFacilities.length > 0 ? 
		Math.max(...filteredFacilities.map(([,c]) => c)) : 1;
	
	function calculateMetrics(count) {
		let normalized = count / maxCount;
		
		return {
			percentile: (normalized * 100).toFixed(1),
			powerUsage: (500 + normalized * 2000).toFixed(0), // kW
			coolingRequirement: (200 + normalized * 800).toFixed(0), // tons
			networkBandwidth: (10 + normalized * 90).toFixed(0), // Gbps
			rackSpace: (10 + normalized * 90).toFixed(0), // racks
			pue: (1.1 + Math.random() * 0.4).toFixed(2),
			uptime: (99 + Math.random()).toFixed(3),
			temperature: (18 + Math.random() * 10).toFixed(1),
			quantumSignature: generateQuantumSignature(count),
			color: interpolateThermalColor(18 + Math.random() * 10)
		};
	}
	
	function generateQuantumSignature(seed) {
		let sig = '';
		let chars = '0123456789ABCDEF';
		for (let i = 0; i < 12; i++) {
			sig += chars[(seed * (i + 1) * 997) % 16];
			if (i === 3 || i === 7) sig += '-';
		}
		return sig;
	}
	
	function getPercentage(count) {
		let total = Object.values(data.facility_intelligence || {}).reduce((a, b) => a + b, 0);
		return total > 0 ? ((count / total) * 100).toFixed(2) : '0.00';
	}
	
	async function drillDownFacility(facility, count) {
		selectedFacility = { facility, count };
		loading = true;
		quantumState = 'DEEP_SCANNING';
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(facility)}`);
			let result = await response.json();
			facilityDetails = result.hosts || [];
			loading = false;
			quantumState = 'SYNCHRONIZED';
		} catch (err) {
			console.error('Facility deep scan failed:', err);
			facilityDetails = [];
			loading = false;
			quantumState = 'ERROR';
		}
	}
	
	function closeDetails() {
		selectedFacility = null;
		facilityDetails = [];
		quantumState = 'SYNCHRONIZED';
	}
</script>

<div class="quantum-facility-interface">
	<!-- Quantum Field Background -->
	<div class="quantum-field">
		{#each quantumField as particle}
			<div class="field-particle"
				 style="left: {particle.x}px;
						top: {particle.y}px;
						width: {2 + particle.energy / 50}px;
						height: {2 + particle.energy / 50}px;
						background: {particle.color};
						opacity: {0.2 + particle.energy / 200};
						transform: translateZ({particle.z}px);
						box-shadow: 0 0 {particle.energy / 10}px {particle.color}">
			</div>
		{/each}
	</div>
	
	<!-- Thermal Overlay -->
	{#if viewMode === 'thermal'}
		<div class="thermal-overlay">
			{#each thermalGrid as row, i}
				{#each row as cell, j}
					<div class="thermal-cell"
						 style="left: {j * 5}%;
								top: {i * 5}%;
								background: {interpolateThermalColor(cell.temp)};
								opacity: {0.3 + cell.airflow * 0.3};
								box-shadow: {cell.hotspot ? `0 0 20px ${neonColors.hot}` : 'none'}">
					</div>
				{/each}
			{/each}
		</div>
	{/if}
	
	<div class="facility-container">
		<!-- Quantum Header -->
		<header class="facility-header">
			<div class="header-grid">
				<div class="brand-section">
					<div class="facility-logo">
						<div class="logo-structure" style="transform: rotateY({rotationY}deg)">
							<div class="logo-cube">
								<div class="cube-face front" style="background: {neonColors.primary}20; border: 1px solid {neonColors.primary}">DC</div>
								<div class="cube-face back" style="background: {neonColors.secondary}20; border: 1px solid {neonColors.secondary}">DC</div>
								<div class="cube-face left" style="background: {neonColors.tertiary}20; border: 1px solid {neonColors.tertiary}">DC</div>
								<div class="cube-face right" style="background: {neonColors.quaternary}20; border: 1px solid {neonColors.quaternary}">DC</div>
								<div class="cube-face top" style="background: {neonColors.optimal}20; border: 1px solid {neonColors.optimal}">DC</div>
								<div class="cube-face bottom" style="background: {neonColors.safe}20; border: 1px solid {neonColors.safe}">DC</div>
							</div>
						</div>
					</div>
					<div class="brand-info">
						<h1 class="interface-title" data-text="GLOBAL FACILITY NEURAL GRID">
							GLOBAL FACILITY NEURAL GRID
						</h1>
						<div class="system-metrics">
							<span class="metric-item">
								<span class="metric-icon" style="color: {neonColors.primary}">❄</span>
								COOLING: {coolingEfficiency.toFixed(0)}%
							</span>
							<span class="metric-separator">|</span>
							<span class="metric-item">
								<span class="metric-icon" style="color: {neonColors.secondary}">⚡</span>
								POWER: {powerUsage.toFixed(0)}%
							</span>
							<span class="metric-separator">|</span>
							<span class="metric-item">
								<span class="metric-icon" style="color: {neonColors.tertiary}">◈</span>
								NETWORK: {(100 - networkLatency * 10).toFixed(0)}%
							</span>
						</div>
					</div>
				</div>
				
				<div class="control-section">
					<div class="search-control">
						<input 
							type="text" 
							bind:value={searchTerm}
							placeholder="FACILITY SEARCH..."
							class="facility-search"
						/>
						<div class="search-beam" style="width: {searchTerm ? '100%' : '0'}"></div>
					</div>
					
					<div class="view-controls">
						<button class="view-btn {viewMode === 'thermal' ? 'active' : ''}"
								on:click={() => viewMode = 'thermal'}
								style="--accent: {neonColors.primary}">
							<span class="btn-icon">🌡️</span>
							<span class="btn-text">THERMAL</span>
						</button>
						<button class="view-btn {viewMode === 'network' ? 'active' : ''}"
								on:click={() => viewMode = 'network'}
								style="--accent: {neonColors.tertiary}">
							<span class="btn-icon">🌐</span>
							<span class="btn-text">NETWORK</span>
						</button>
						<button class="view-btn {viewMode === 'power' ? 'active' : ''}"
								on:click={() => viewMode = 'power'}
								style="--accent: {neonColors.secondary}">
							<span class="btn-icon">⚡</span>
							<span class="btn-text">POWER</span>
						</button>
						<button class="view-btn {viewMode === 'quantum' ? 'active' : ''}"
								on:click={() => viewMode = 'quantum'}
								style="--accent: {neonColors.quaternary}">
							<span class="btn-icon">◈</span>
							<span class="btn-text">QUANTUM</span>
						</button>
					</div>
				</div>
				
				<div class="status-section">
					<div class="status-display">
						<div class="status-value" style="color: {neonColors.primary}">
							{filteredFacilities.length}
						</div>
						<div class="status-label">FACILITIES</div>
					</div>
					<div class="status-display">
						<div class="status-value" style="color: {neonColors.secondary}">
							{Object.values(data.facility_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}
						</div>
						<div class="status-label">NODES</div>
					</div>
					<div class="status-indicator">
						<span class="indicator-dot" style="background: {quantumState === 'ERROR' ? neonColors.critical : neonColors.safe}"></span>
						<span class="indicator-text">{quantumState}</span>
					</div>
				</div>
			</div>
		</header>
		
		<!-- Main Viewport -->
		<div class="facility-viewport">
			{#if loading && !selectedFacility}
				<div class="loading-state">
					<div class="loading-reactor">
						<div class="reactor-core">
							<div class="core-ring ring-1" style="border-color: {neonColors.primary}"></div>
							<div class="core-ring ring-2" style="border-color: {neonColors.secondary}"></div>
							<div class="core-ring ring-3" style="border-color: {neonColors.tertiary}"></div>
							<div class="core-center">⚡</div>
						</div>
					</div>
					<p class="loading-text">INITIALIZING FACILITY NEURAL GRID...</p>
				</div>
			{:else if selectedFacility}
				<!-- Detail View -->
				<div class="facility-detail-view">
					<div class="detail-header">
						<div class="facility-identity">
							<div class="identity-badge" style="border-color: {calculateMetrics(selectedFacility.count).color}">
								<div class="badge-rings">
									<div class="ring" style="border-color: {neonColors.primary}"></div>
									<div class="ring" style="border-color: {neonColors.secondary}"></div>
								</div>
								<div class="badge-icon">🏢</div>
							</div>
							<div class="identity-info">
								<h2 class="facility-name">{selectedFacility.facility.toUpperCase()}</h2>
								<div class="facility-signature">
									{calculateMetrics(selectedFacility.count).quantumSignature}
								</div>
								<div class="facility-stats">
									<span class="stat-badge" style="background: {neonColors.primary}20; color: {neonColors.primary}">
										PUE: {calculateMetrics(selectedFacility.count).pue}
									</span>
									<span class="stat-badge" style="background: {neonColors.secondary}20; color: {neonColors.secondary}">
										POWER: {calculateMetrics(selectedFacility.count).powerUsage}kW
									</span>
									<span class="stat-badge" style="background: {neonColors.tertiary}20; color: {neonColors.tertiary}">
										UPTIME: {calculateMetrics(selectedFacility.count).uptime}%
									</span>
								</div>
							</div>
						</div>
						<button class="close-detail" on:click={closeDetails}>
							<span>✕</span>
						</button>
					</div>
					
					<div class="detail-metrics">
						<div class="metric-card">
							<div class="card-header">
								<span class="card-icon" style="color: {neonColors.primary}">❄</span>
								<span class="card-title">COOLING</span>
							</div>
							<div class="card-value" style="color: {neonColors.primary}">
								{calculateMetrics(selectedFacility.count).coolingRequirement} TONS
							</div>
							<div class="card-graph">
								<div class="graph-bars">
									{#each Array(10) as _, i}
										<div class="bar" style="height: {Math.random() * 100}%; background: {neonColors.primary}"></div>
									{/each}
								</div>
							</div>
						</div>
						
						<div class="metric-card">
							<div class="card-header">
								<span class="card-icon" style="color: {neonColors.secondary}">⚡</span>
								<span class="card-title">POWER</span>
							</div>
							<div class="card-value" style="color: {neonColors.secondary}">
								{calculateMetrics(selectedFacility.count).powerUsage} kW
							</div>
							<div class="card-meter">
								<div class="meter-track">
									<div class="meter-fill" style="width: {calculateMetrics(selectedFacility.count).percentile}%; background: {neonColors.secondary}"></div>
								</div>
							</div>
						</div>
						
						<div class="metric-card">
							<div class="card-header">
								<span class="card-icon" style="color: {neonColors.tertiary}">🌐</span>
								<span class="card-title">NETWORK</span>
							</div>
							<div class="card-value" style="color: {neonColors.tertiary}">
								{calculateMetrics(selectedFacility.count).networkBandwidth} Gbps
							</div>
							<div class="card-pulse">
								<div class="pulse-dot" style="background: {neonColors.tertiary}"></div>
								<div class="pulse-wave" style="border-color: {neonColors.tertiary}"></div>
							</div>
						</div>
						
						<div class="metric-card">
							<div class="card-header">
								<span class="card-icon" style="color: {neonColors.optimal}">🌡️</span>
								<span class="card-title">TEMPERATURE</span>
							</div>
							<div class="card-value" style="color: {neonColors.optimal}">
								{calculateMetrics(selectedFacility.count).temperature}°C
							</div>
							<div class="card-thermal">
								<div class="thermal-gradient" style="background: linear-gradient(90deg, {neonColors.cold}, {neonColors.optimal}, {neonColors.hot})"></div>
								<div class="thermal-marker" style="left: {(parseFloat(calculateMetrics(selectedFacility.count).temperature) - 15) * 4}%"></div>
							</div>
						</div>
					</div>
					
					<div class="detail-stream">
						<div class="stream-header">
							<h3>FACILITY DATA STREAM</h3>
							<div class="stream-status">
								<span class="status-text">LIVE</span>
								<span class="status-pulse"></span>
							</div>
						</div>
						<div class="stream-table-container">
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
											<td class="node-id">{host.host.substring(0, 30)}</td>
											<td>{host.region || 'UNKNOWN'}</td>
											<td>{host.country || 'UNKNOWN'}</td>
											<td>{host.infrastructure_type || 'UNKNOWN'}</td>
											<td>
												<span class="status-icon {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'online' : 'offline'}"
													  style="color: {host.present_in_cmdb?.toLowerCase().includes('yes') ? neonColors.safe : neonColors.critical}">
													{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}
												</span>
											</td>
											<td>
												<span class="status-icon {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'secured' : 'vulnerable'}"
													  style="color: {host.tanium_coverage?.toLowerCase().includes('tanium') ? neonColors.primary : neonColors.warning}">
													{host.tanium_coverage?.toLowerCase().includes('tanium') ? '⬢' : '⬡'}
												</span>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				</div>
			{:else if viewMode === 'thermal'}
				<!-- Thermal View -->
				<div class="thermal-view">
					<div class="thermal-container">
						<div class="thermal-map">
							<svg viewBox="0 0 800 600">
								<defs>
									<radialGradient id="hotspot">
										<stop offset="0%" style="stop-color:{neonColors.hot};stop-opacity:0.8" />
										<stop offset="100%" style="stop-color:{neonColors.hot};stop-opacity:0" />
									</radialGradient>
									<radialGradient id="coldspot">
										<stop offset="0%" style="stop-color:{neonColors.cold};stop-opacity:0.8" />
										<stop offset="100%" style="stop-color:{neonColors.cold};stop-opacity:0" />
									</radialGradient>
								</defs>
								
								<!-- Facility layout -->
								{#each facilityNodes as node, i}
									<g transform="translate({100 + (i % 6) * 120}, {100 + Math.floor(i / 6) * 100})"
									   on:click={() => drillDownFacility(node.name, node.count)}>
										<rect x="-40" y="-30" width="80" height="60"
											  fill={node.color}
											  opacity="0.3"
											  stroke={node.color}
											  stroke-width="2"
											  rx="5"/>
										<circle cx="0" cy="0" r="{20 + node.temperature}"
												fill="url(#{node.temperature > 28 ? 'hotspot' : 'coldspot'})"
												opacity="0.5"/>
										<text text-anchor="middle" y="-35" fill="#ffffff" font-size="10">
											{node.name.substring(0, 15)}
										</text>
										<text text-anchor="middle" y="0" fill="{node.color}" font-size="12" font-weight="bold">
											{node.temperature.toFixed(1)}°C
										</text>
										<text text-anchor="middle" y="15" fill="#ffffff" font-size="9">
											{node.coolingStatus}
										</text>
									</g>
								{/each}
								
								<!-- Airflow visualization -->
								{#each Array(20) as _, i}
									<line x1="0" y1="{i * 30}"
										  x2="800" y2="{i * 30}"
										  stroke="{neonColors.primary}"
										  stroke-width="0.5"
										  opacity="0.1">
										<animate attributeName="x1"
												 values="0;100;0"
												 dur="{5 + i * 0.5}s"
												 repeatCount="indefinite"/>
									</line>
								{/each}
							</svg>
						</div>
						
						<div class="thermal-legend">
							<h4>THERMAL ZONES</h4>
							<div class="legend-items">
								<div class="legend-item">
									<div class="legend-color" style="background: {neonColors.cold}"></div>
									<span>COLD (&lt;18°C)</span>
								</div>
								<div class="legend-item">
									<div class="legend-color" style="background: {neonColors.optimal}"></div>
									<span>OPTIMAL (18-22°C)</span>
								</div>
								<div class="legend-item">
									<div class="legend-color" style="background: {neonColors.primary}"></div>
									<span>NORMAL (22-28°C)</span>
								</div>
								<div class="legend-item">
									<div class="legend-color" style="background: {neonColors.warning}"></div>
									<span>WARNING (28-35°C)</span>
								</div>
								<div class="legend-item">
									<div class="legend-color" style="background: {neonColors.hot}"></div>
									<span>CRITICAL (&gt;35°C)</span>
								</div>
							</div>
						</div>
					</div>
				</div>
			{:else if viewMode === 'network'}
				<!-- Network View -->
				<div class="network-view">
					<div class="network-container">
						<svg class="network-svg" viewBox="-400 -400 800 800">
							<defs>
								<filter id="networkGlow">
									<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
									<feMerge>
										<feMergeNode in="coloredBlur"/>
										<feMergeNode in="SourceGraphic"/>
									</feMerge>
								</filter>
							</defs>
							
							<!-- Network connections -->
							{#each networkTopology as topology}
								{#each topology.connections as conn}
									{#if facilityNodes[conn.target]}
										<line x1="{topology.source.x}"
											  y1="{topology.source.y}"
											  x2="{facilityNodes[conn.target].x}"
											  y2="{facilityNodes[conn.target].y}"
											  stroke="{neonColors.tertiary}"
											  stroke-width="{0.5 + conn.bandwidth / 50}"
											  opacity="{0.2 + conn.bandwidth / 200}">
											<animate attributeName="stroke-dasharray"
													 values="0 5;5 0"
													 dur="{2 / (conn.bandwidth / 10)}s"
													 repeatCount="indefinite"/>
										</line>
										
										<!-- Data packets -->
										<circle r="2" fill="{neonColors.tertiary}" filter="url(#networkGlow)">
											<animateMotion dur="{5 / (conn.bandwidth / 10)}s" repeatCount="indefinite">
												<mpath href="#path{topology.source.id}-{conn.target}"/>
											</animateMotion>
										</circle>
										
										<path id="path{topology.source.id}-{conn.target}"
											  d="M {topology.source.x} {topology.source.y} L {facilityNodes[conn.target].x} {facilityNodes[conn.target].y}"
											  fill="none"/>
									{/if}
								{/each}
							{/each}
							
							<!-- Facility nodes -->
							{#each facilityNodes as node}
								<g transform="translate({node.x}, {node.y})"
								   on:click={() => drillDownFacility(node.name, node.count)}>
									<circle r="{15 + node.networkLoad / 5}"
											fill="{neonColors.tertiary}"
											opacity="0.2"/>
									<circle r="{10 + node.networkLoad / 10}"
											fill="{neonColors.tertiary}"
											opacity="0.6"/>
									<text text-anchor="middle" y="-20" fill="#ffffff" font-size="10">
										{node.name.substring(0, 12)}
									</text>
									<text text-anchor="middle" y="5" fill="{neonColors.tertiary}" font-size="12" font-weight="bold">
										{node.networkLoad.toFixed(0)}%
									</text>
								</g>
							{/each}
							
							<!-- Central core -->
							<circle cx="0" cy="0" r="40" fill="none" stroke="{neonColors.tertiary}" stroke-width="2" opacity="0.5">
								<animate attributeName="r" values="40;45;40" dur="3s" repeatCount="indefinite"/>
							</circle>
							<text text-anchor="middle" fill="{neonColors.tertiary}" font-size="14" font-weight="bold">
								NETWORK CORE
							</text>
						</svg>
					</div>
				</div>
			{:else if viewMode === 'power'}
				<!-- Power View -->
				<div class="power-view">
					<div class="power-container">
						<div class="power-distribution">
							<h3>POWER DISTRIBUTION UNITS</h3>
							<div class="pdu-grid">
								{#each powerGrid as pdu}
									<div class="pdu-unit" style="border-color: {pdu.load > 80 ? neonColors.warning : neonColors.secondary}">
										<div class="pdu-header">
											<span class="pdu-name">{pdu.name}</span>
											<span class="pdu-status" style="color: {pdu.status === 'ONLINE' ? neonColors.safe : neonColors.warning}">
												{pdu.status}
											</span>
										</div>
										<div class="pdu-metrics">
											<div class="pdu-metric">
												<span class="metric-label">LOAD</span>
												<div class="load-bar">
													<div class="load-fill" style="width: {pdu.load}%; background: {pdu.load > 80 ? neonColors.warning : neonColors.secondary}"></div>
												</div>
												<span class="metric-value">{pdu.load.toFixed(0)}%</span>
											</div>
											<div class="pdu-metric">
												<span class="metric-label">VOLTAGE</span>
												<span class="metric-value" style="color: {neonColors.secondary}">{pdu.voltage.toFixed(0)}V</span>
											</div>
											<div class="pdu-metric">
												<span class="metric-label">CURRENT</span>
												<span class="metric-value" style="color: {neonColors.secondary}">{pdu.current.toFixed(0)}A</span>
											</div>
											<div class="pdu-metric">
												<span class="metric-label">EFFICIENCY</span>
												<span class="metric-value" style="color: {pdu.efficiency > 90 ? neonColors.safe : neonColors.warning}">{pdu.efficiency.toFixed(0)}%</span>
											</div>
										</div>
										<div class="pdu-redundancy">
											<span class="redundancy-label">REDUNDANCY:</span>
											<span class="redundancy-value" style="color: {neonColors.optimal}">{pdu.redundancy}</span>
										</div>
									</div>
								{/each}
							</div>
						</div>
						
						<div class="power-flow">
							<svg viewBox="0 0 400 300">
								<!-- Power flow visualization -->
								{#each Array(5) as _, i}
									<rect x="{i * 80}" y="50" width="60" height="40"
										  fill="none" stroke="{neonColors.secondary}" stroke-width="2" rx="5"/>
									<text x="{i * 80 + 30}" y="75" text-anchor="middle" fill="#ffffff" font-size="10">
										UPS-{i + 1}
									</text>
									<line x1="{i * 80 + 30}" y1="90" x2="{i * 80 + 30}" y2="150"
										  stroke="{neonColors.secondary}" stroke-width="2" opacity="0.5"/>
									
									<!-- Animated power flow -->
									<circle cx="{i * 80 + 30}" cy="120" r="3" fill="{neonColors.secondary}">
										<animate attributeName="cy" values="90;150;90" dur="2s" repeatCount="indefinite"/>
										<animate attributeName="opacity" values="1;0;1" dur="2s" repeatCount="indefinite"/>
									</circle>
								{/each}
								
								<rect x="100" y="150" width="200" height="60"
									  fill="{neonColors.secondary}10" stroke="{neonColors.secondary}" stroke-width="2" rx="5"/>
								<text x="200" y="185" text-anchor="middle" fill="{neonColors.secondary}" font-size="14" font-weight="bold">
									MAIN DISTRIBUTION
								</text>
							</svg>
						</div>
					</div>
				</div>
			{:else if viewMode === 'quantum'}
				<!-- Quantum View -->
				<div class="quantum-view">
					<div class="quantum-visualization">
						<div class="quantum-core" style="transform: rotateX({rotationX}deg) rotateY({rotationY}deg) rotateZ({rotationZ}deg)">
							{#each facilityNodes as node, i}
								{@const angle = (i / facilityNodes.length) * Math.PI * 2}
								{@const radius = 150 + node.importance * 100}
								<div class="quantum-node"
									 style="transform: translate3d({Math.cos(angle) * radius}px, {Math.sin(angle) * radius}px, {node.z}px)"
									 on:click={() => drillDownFacility(node.name, node.count)}>
									<div class="node-sphere" style="background: radial-gradient(circle, {node.color}, transparent)">
										<div class="node-data">
											<div class="data-name">{node.name.substring(0, 10)}</div>
											<div class="data-value">{node.count}</div>
										</div>
									</div>
									<div class="node-orbit" style="border-color: {node.color}"></div>
								</div>
							{/each}
							
							<div class="quantum-nexus">
								<div class="nexus-core"></div>
								<div class="nexus-ring ring-1" style="border-color: {neonColors.primary}"></div>
								<div class="nexus-ring ring-2" style="border-color: {neonColors.secondary}"></div>
								<div class="nexus-ring ring-3" style="border-color: {neonColors.tertiary}"></div>
							</div>
						</div>
					</div>
				</div>
			{/if}
			
			<!-- Facility Matrix Table -->
			{#if !selectedFacility}
				<div class="facility-matrix">
					<div class="matrix-header">
						<h3>FACILITY DATA MATRIX</h3>
					</div>
					<div class="matrix-body">
						<table class="matrix-table">
							<thead>
								<tr>
									<th>RANK</th>
									<th>FACILITY</th>
									<th>NODES</th>
									<th>POWER</th>
									<th>PUE</th>
									<th>UPTIME</th>
									<th>STATUS</th>
								</tr>
							</thead>
							<tbody>
								{#each filteredFacilities as [facility, count], index}
									{@const metrics = calculateMetrics(count)}
									<tr class="matrix-row"
										style="border-left: 3px solid {metrics.color}"
										on:click={() => drillDownFacility(facility, count)}>
										<td class="rank-cell">
											<span style="color: {metrics.color}">#{index + 1}</span>
										</td>
										<td class="facility-cell">
											<span class="facility-icon" style="color: {metrics.color}">🏢</span>
											<span class="facility-name">{facility.substring(0, 25).toUpperCase()}</span>
										</td>
										<td class="nodes-cell" style="color: {metrics.color}">
											{count.toLocaleString()}
										</td>
										<td class="power-cell">
											<div class="power-bar">
												<div class="power-fill" style="width: {metrics.percentile}%; background: {neonColors.secondary}"></div>
											</div>
											<span>{metrics.powerUsage}kW</span>
										</td>
										<td class="pue-cell" style="color: {parseFloat(metrics.pue) < 1.5 ? neonColors.safe : neonColors.warning}">
											{metrics.pue}
										</td>
										<td class="uptime-cell" style="color: {parseFloat(metrics.uptime) > 99.9 ? neonColors.safe : neonColors.warning}">
											{metrics.uptime}%
										</td>
										<td class="status-cell">
											<span class="status-badge" style="background: {neonColors.safe}20; color: {neonColors.safe}">
												ONLINE
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.quantum-facility-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		position: relative;
		overflow: hidden;
		font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
	}
	
	/* Quantum Field */
	.quantum-field {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
		perspective: 1000px;
	}
	
	.field-particle {
		position: absolute;
		border-radius: 50%;
		animation: floatField 20s linear infinite;
	}
	
	@keyframes floatField {
		0% { transform: translate3d(0, 0, 0) rotate(0deg); }
		25% { transform: translate3d(30px, -30px, 50px) rotate(90deg); }
		50% { transform: translate3d(-20px, 20px, -50px) rotate(180deg); }
		75% { transform: translate3d(25px, 15px, 25px) rotate(270deg); }
		100% { transform: translate3d(0, 0, 0) rotate(360deg); }
	}
	
	/* Thermal Overlay */
	.thermal-overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 2;
	}
	
	.thermal-cell {
		position: absolute;
		width: 5%;
		height: 5%;
		transition: all 0.5s ease;
	}
	
	/* Container */
	.facility-container {
		position: relative;
		z-index: 10;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
	
	/* Header */
	.facility-header {
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.03), rgba(0, 0, 0, 0.95));
		backdrop-filter: blur(20px);
		border-bottom: 1px solid rgba(0, 255, 255, 0.2);
		padding: 1.5rem 2rem;
	}
	
	.header-grid {
		display: grid;
		grid-template-columns: 1fr auto auto;
		gap: 3rem;
		align-items: center;
	}
	
	.brand-section {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.facility-logo {
		width: 60px;
		height: 60px;
		perspective: 800px;
	}
	
	.logo-structure {
		width: 100%;
		height: 100%;
		transform-style: preserve-3d;
		transition: transform 0.6s;
	}
	
	.logo-cube {
		width: 100%;
		height: 100%;
		position: relative;
		transform-style: preserve-3d;
	}
	
	.cube-face {
		position: absolute;
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.2rem;
		font-weight: bold;
		color: #ffffff;
	}
	
	.cube-face.front { transform: translateZ(30px); }
	.cube-face.back { transform: rotateY(180deg) translateZ(30px); }
	.cube-face.left { transform: rotateY(-90deg) translateZ(30px); }
	.cube-face.right { transform: rotateY(90deg) translateZ(30px); }
	.cube-face.top { transform: rotateX(90deg) translateZ(30px); }
	.cube-face.bottom { transform: rotateX(-90deg) translateZ(30px); }
	
	.interface-title {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 200;
		letter-spacing: 0.3em;
		background: linear-gradient(90deg, #00FFFF, #FF00FF, #00FF00);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		animation: titlePulse 5s linear infinite;
	}
	
	@keyframes titlePulse {
		0% { background-position: 0% 50%; }
		100% { background-position: 200% 50%; }
	}
	
	.system-metrics {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-top: 0.5rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
		letter-spacing: 0.05em;
	}
	
	.metric-icon {
		font-size: 1rem;
		margin-right: 0.25rem;
	}
	
	.metric-separator {
		color: rgba(255, 255, 255, 0.2);
	}
	
	/* Control Section */
	.control-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.search-control {
		position: relative;
	}
	
	.facility-search {
		width: 100%;
		padding: 0.75rem 1rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 8px;
		color: #00FFFF;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.9rem;
		letter-spacing: 0.05em;
		transition: all 0.3s ease;
	}
	
	.facility-search::placeholder {
		color: rgba(0, 255, 255, 0.4);
	}
	
	.facility-search:focus {
		outline: none;
		border-color: #00FFFF;
		background: rgba(0, 255, 255, 0.05);
		box-shadow: 0 0 30px rgba(0, 255, 255, 0.2);
	}
	
	.search-beam {
		position: absolute;
		bottom: 0;
		left: 0;
		height: 1px;
		background: linear-gradient(90deg, transparent, #00FFFF, transparent);
		transition: width 0.3s ease;
	}
	
	.view-controls {
		display: flex;
		gap: 0.5rem;
	}
	
	.view-btn {
		flex: 1;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.7rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		--accent: #00FFFF;
	}
	
	.view-btn:hover {
		border-color: var(--accent);
		background: rgba(0, 255, 255, 0.05);
		color: var(--accent);
	}
	
	.view-btn.active {
		border-color: var(--accent);
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 0, 0, 0.6));
		color: var(--accent);
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
	}
	
	.btn-icon {
		font-size: 1.2rem;
	}
	
	.btn-text {
		font-size: 0.65rem;
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	/* Status Section */
	.status-section {
		display: flex;
		align-items: center;
		gap: 2rem;
	}
	
	.status-display {
		text-align: center;
	}
	
	.status-value {
		font-size: 1.8rem;
		font-weight: 100;
		font-family: 'JetBrains Mono', monospace;
		text-shadow: 0 0 20px currentColor;
	}
	
	.status-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.2em;
		margin-top: 0.25rem;
		font-weight: 500;
	}
	
	.status-indicator {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.indicator-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: indicatorPulse 2s ease-in-out infinite;
	}
	
	@keyframes indicatorPulse {
		0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 currentColor; }
		50% { transform: scale(1.2); box-shadow: 0 0 0 4px transparent; }
	}
	
	.indicator-text {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	/* Viewport */
	.facility-viewport {
		flex: 1;
		padding: 2rem;
		overflow: hidden;
		display: flex;
		gap: 2rem;
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
	
	.loading-reactor {
		position: relative;
		width: 120px;
		height: 120px;
	}
	
	.reactor-core {
		width: 100%;
		height: 100%;
		position: relative;
	}
	
	.core-ring {
		position: absolute;
		inset: 0;
		border: 2px solid;
		border-radius: 50%;
		animation: reactorSpin 3s linear infinite;
	}
	
	.core-ring.ring-2 {
		inset: 20px;
		animation-direction: reverse;
		animation-duration: 4s;
	}
	
	.core-ring.ring-3 {
		inset: 40px;
		animation-duration: 5s;
	}
	
	@keyframes reactorSpin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.core-center {
		position: absolute;
		inset: 45px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		color: #00FFFF;
		text-shadow: 0 0 30px rgba(0, 255, 255, 0.8);
		animation: pulse 2s ease-in-out infinite;
	}
	
	@keyframes pulse {
		0%, 100% { opacity: 0.5; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.1); }
	}
	
	.loading-text {
		color: rgba(0, 255, 255, 0.6);
		font-size: 0.9rem;
		letter-spacing: 0.2em;
		animation: pulse 2s ease-in-out infinite;
	}
	
	/* View-specific styles - Thermal, Network, Power, Quantum views continue... */
	
	/* Facility Matrix */
	.facility-matrix {
		width: 450px;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 255, 0.1);
		border-radius: 16px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.matrix-header {
		padding: 1rem 1.5rem;
		background: rgba(0, 0, 0, 0.4);
		border-bottom: 1px solid rgba(0, 255, 255, 0.1);
	}
	
	.matrix-header h3 {
		margin: 0;
		font-size: 0.9rem;
		color: #00FFFF;
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	.matrix-body {
		flex: 1;
		overflow: auto;
	}
	
	/* Continue with remaining styles... */
</style>