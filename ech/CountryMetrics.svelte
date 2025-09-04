<!-- CountryMetrics.svelte - Quantum Geopolitical Intelligence Matrix -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';
	
	// Visualization states
	let viewMode = 'globe'; // 'globe', 'heatmap', 'connections', 'intelligence'
	let globeRotation = { x: -23.5, y: 0, z: 0 };
	let countryNodes = [];
	let geoConnections = [];
	let heatmapData = [];
	let intelligenceNetwork = [];
	let quantumState = 'INITIALIZING';
	let threatLevel = 'STABLE';
	let globalActivity = 0;
	let dataFlowRate = 0;
	
	// Interactive globe
	let isDragging = false;
	let lastMouseX = 0;
	let lastMouseY = 0;
	let autoRotate = true;
	
	// Particle system for atmosphere
	let atmosphereParticles = [];
	let satellites = [];
	let dataStreams = [];
	
	// Animation references
	let animationFrameId;
	let intervals = [];
	
	// Neon pastel colors for geopolitical visualization
	const neonColors = {
		primary: '#00FFAA',     // Mint (allied)
		secondary: '#FF00AA',    // Magenta (neutral)
		tertiary: '#FFAA00',     // Gold (economic)
		quaternary: '#00AAFF',   // Sky Blue (diplomatic)
		threat: '#FF0066',       // Red-Pink (threat)
		safe: '#00FF66',         // Green (safe)
		warning: '#FFAA66',      // Orange (warning)
		critical: '#FF0044',     // Red (critical)
		data: '#66FFFF',         // Light Cyan (data)
		quantum: '#FF66FF'       // Light Magenta (quantum)
	};
	
	// Real world approximate coordinates for major countries
	const countryCoordinates = {
		'united states': { lat: 39.8283, lng: -98.5795 },
		'china': { lat: 35.8617, lng: 104.1954 },
		'russia': { lat: 61.5240, lng: 105.3188 },
		'india': { lat: 20.5937, lng: 78.9629 },
		'brazil': { lat: -14.2350, lng: -51.9253 },
		'united kingdom': { lat: 55.3781, lng: -3.4360 },
		'germany': { lat: 51.1657, lng: 10.4515 },
		'japan': { lat: 36.2048, lng: 138.2529 },
		'australia': { lat: -25.2744, lng: 133.7751 },
		'canada': { lat: 56.1304, lng: -106.3468 },
		'france': { lat: 46.2276, lng: 2.2137 },
		'italy': { lat: 41.8719, lng: 12.5674 },
		'mexico': { lat: 23.6345, lng: -102.5528 },
		'south korea': { lat: 35.9078, lng: 127.7669 },
		'spain': { lat: 40.4637, lng: -3.7492 },
		'indonesia': { lat: -0.7893, lng: 113.9213 },
		'netherlands': { lat: 52.1326, lng: 5.2913 },
		'saudi arabia': { lat: 23.8859, lng: 45.0792 },
		'turkey': { lat: 38.9637, lng: 35.2433 },
		'switzerland': { lat: 46.8182, lng: 8.2275 }
	};
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/country_metrics');
			let result = await response.json();
			data = result;
			loading = false;
			quantumState = 'SYNCHRONIZED';
			initializeVisualization();
			startAnimations();
		} catch (err) {
			console.error('Geopolitical matrix sync failed:', err);
			loading = false;
			quantumState = 'DESYNCHRONIZED';
		}
	});
	
	onDestroy(() => {
		if (animationFrameId) cancelAnimationFrame(animationFrameId);
		intervals.forEach(interval => clearInterval(interval));
	});
	
	function initializeVisualization() {
		if (!data.global_intelligence) return;
		
		// Create country nodes with coordinates
		let countries = Object.entries(data.global_intelligence);
		let maxCount = Math.max(...countries.map(([,c]) => c));
		
		countries.forEach(([country, count], i) => {
			let importance = count / maxCount;
			let coords = getCountryCoordinates(country);
			
			// Convert lat/lng to 3D sphere coordinates
			let phi = (90 - coords.lat) * Math.PI / 180;
			let theta = (coords.lng + 180) * Math.PI / 180;
			let radius = 200;
			
			countryNodes.push({
				id: i,
				name: country,
				count: count,
				importance: importance,
				lat: coords.lat,
				lng: coords.lng,
				x: radius * Math.sin(phi) * Math.cos(theta),
				y: radius * Math.cos(phi),
				z: radius * Math.sin(phi) * Math.sin(theta),
				threatLevel: Math.random() * 100,
				economicPower: importance * 100,
				diplomaticInfluence: Math.random() * 100,
				cyberCapability: Math.random() * 100,
				color: interpolateGeopoliticalColor(importance, Math.random() * 100)
			});
		});
		
		// Create geopolitical connections
		countryNodes.forEach((node, i) => {
			// Connect to nearby high-importance countries
			countryNodes.forEach((target, j) => {
				if (i !== j) {
					let distance = calculateDistance(node, target);
					if ((distance < 5000 && Math.random() > 0.5) || 
					    (node.importance > 0.7 && target.importance > 0.7 && Math.random() > 0.7)) {
						geoConnections.push({
							source: i,
							target: j,
							strength: Math.min(node.importance, target.importance),
							type: getConnectionType(node, target),
							active: true,
							dataFlow: []
						});
						
						// Add data flow particles
						for (let k = 0; k < 5; k++) {
							geoConnections[geoConnections.length - 1].dataFlow.push({
								progress: Math.random(),
								speed: 0.005 + Math.random() * 0.01,
								size: Math.random() * 3 + 1
							});
						}
					}
				}
			});
		});
		
		// Initialize atmosphere particles
		for (let i = 0; i < 500; i++) {
			atmosphereParticles.push({
				lat: (Math.random() - 0.5) * 180,
				lng: (Math.random() - 0.5) * 360,
				altitude: 210 + Math.random() * 50,
				speed: 0.1 + Math.random() * 0.5,
				size: Math.random() * 2 + 0.5,
				color: Object.values(neonColors)[Math.floor(Math.random() * 10)],
				type: ['data', 'signal', 'quantum'][Math.floor(Math.random() * 3)]
			});
		}
		
		// Initialize satellites
		for (let i = 0; i < 12; i++) {
			satellites.push({
				id: i,
				lat: (Math.random() - 0.5) * 180,
				lng: (Math.random() - 0.5) * 360,
				altitude: 250 + Math.random() * 100,
				orbit: {
					speed: 0.2 + Math.random() * 0.3,
					inclination: Math.random() * 90
				},
				type: ['surveillance', 'communication', 'weather', 'military'][Math.floor(Math.random() * 4)],
				active: true,
				signalStrength: Math.random() * 100
			});
		}
		
		// Initialize heatmap data
		for (let lat = -80; lat <= 80; lat += 20) {
			for (let lng = -180; lng <= 180; lng += 30) {
				heatmapData.push({
					lat: lat,
					lng: lng,
					intensity: Math.random() * 100,
					type: ['economic', 'military', 'cyber', 'diplomatic'][Math.floor(Math.random() * 4)]
				});
			}
		}
	}
	
	function getCountryCoordinates(countryName) {
		let key = countryName.toLowerCase();
		if (countryCoordinates[key]) {
			return countryCoordinates[key];
		}
		// Default random position if country not found
		return {
			lat: (Math.random() - 0.5) * 160,
			lng: (Math.random() - 0.5) * 360
		};
	}
	
	function calculateDistance(node1, node2) {
		// Simplified distance calculation
		return Math.sqrt(
			Math.pow(node1.lat - node2.lat, 2) + 
			Math.pow(node1.lng - node2.lng, 2)
		) * 111; // Convert to approximate km
	}
	
	function getConnectionType(node1, node2) {
		if (node1.economicPower > 70 && node2.economicPower > 70) return 'economic';
		if (node1.cyberCapability > 70 && node2.cyberCapability > 70) return 'cyber';
		if (node1.diplomaticInfluence > 70 && node2.diplomaticInfluence > 70) return 'diplomatic';
		return 'general';
	}
	
	function interpolateGeopoliticalColor(importance, threat) {
		if (threat > 70) return neonColors.threat;
		if (threat > 50) return neonColors.warning;
		if (importance > 0.7) return neonColors.primary;
		if (importance > 0.5) return neonColors.secondary;
		if (importance > 0.3) return neonColors.tertiary;
		return neonColors.quaternary;
	}
	
	function startAnimations() {
		// Main animation loop
		function animate() {
			updateGlobeRotation();
			updateAtmosphere();
			updateSatellites();
			updateDataFlows();
			updateHeatmap();
			
			globalActivity = 50 + Math.sin(Date.now() * 0.001) * 50;
			dataFlowRate = 30 + Math.sin(Date.now() * 0.0008) * 30;
			
			animationFrameId = requestAnimationFrame(animate);
		}
		animate();
		
		// Update quantum state
		intervals.push(setInterval(() => {
			quantumState = ['SYNCHRONIZED', 'ANALYZING', 'PROCESSING', 'CORRELATING', 'MONITORING'][
				Math.floor(Math.random() * 5)
			];
			
			// Update threat level based on activity
			let avgThreat = countryNodes.reduce((sum, node) => sum + node.threatLevel, 0) / countryNodes.length;
			if (avgThreat < 30) threatLevel = 'STABLE';
			else if (avgThreat < 50) threatLevel = 'ELEVATED';
			else if (avgThreat < 70) threatLevel = 'HIGH';
			else threatLevel = 'CRITICAL';
		}, 3000));
	}
	
	function updateGlobeRotation() {
		if (autoRotate && !isDragging) {
			globeRotation.y = (globeRotation.y + 0.2) % 360;
		}
	}
	
	function updateAtmosphere() {
		atmosphereParticles = atmosphereParticles.map(particle => {
			particle.lng = (particle.lng + particle.speed) % 360;
			return particle;
		});
	}
	
	function updateSatellites() {
		satellites = satellites.map(sat => {
			sat.lng = (sat.lng + sat.orbit.speed) % 360;
			sat.lat = Math.sin(Date.now() * 0.001 * sat.orbit.speed) * sat.orbit.inclination;
			sat.signalStrength = Math.max(0, Math.min(100, sat.signalStrength + (Math.random() - 0.5) * 10));
			return sat;
		});
	}
	
	function updateDataFlows() {
		geoConnections.forEach(conn => {
			conn.dataFlow = conn.dataFlow.map(particle => ({
				...particle,
				progress: (particle.progress + particle.speed) % 1
			}));
		});
	}
	
	function updateHeatmap() {
		heatmapData = heatmapData.map(point => ({
			...point,
			intensity: Math.max(0, Math.min(100, point.intensity + (Math.random() - 0.5) * 5))
		}));
	}
	
	$: filteredCountries = data.global_intelligence ? 
		Object.entries(data.global_intelligence)
			.filter(([country]) => country.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredCountries.length > 0 ? 
		Math.max(...filteredCountries.map(([,c]) => c)) : 1;
	
	function calculateMetrics(count) {
		let normalized = count / maxCount;
		
		return {
			percentile: (normalized * 100).toFixed(1),
			globalInfluence: (normalized * 100).toFixed(0),
			economicPower: (50 + normalized * 50).toFixed(0),
			cyberCapability: (30 + normalized * 70).toFixed(0),
			diplomaticReach: (40 + normalized * 60).toFixed(0),
			threatIndex: (Math.random() * 100).toFixed(0),
			stabilityScore: (100 - Math.random() * 30).toFixed(0),
			dataNodes: count,
			quantumSignature: generateQuantumSignature(count),
			color: interpolateGeopoliticalColor(normalized, Math.random() * 100)
		};
	}
	
	function generateQuantumSignature(seed) {
		let sig = '';
		let chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
		for (let i = 0; i < 12; i++) {
			sig += chars[(seed * (i + 1) * 997) % 36];
			if (i === 2 || i === 5 || i === 8) sig += '-';
		}
		return sig;
	}
	
	function getPercentage(count) {
		let total = Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0);
		return total > 0 ? ((count / total) * 100).toFixed(2) : '0.00';
	}
	
	async function drillDownCountry(country, count) {
		selectedCountry = { country, count };
		loading = true;
		quantumState = 'DEEP_SCANNING';
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(country)}`);
			let result = await response.json();
			countryDetails = result.hosts || [];
			loading = false;
			quantumState = 'SYNCHRONIZED';
		} catch (err) {
			console.error('Country deep scan failed:', err);
			countryDetails = [];
			loading = false;
			quantumState = 'ERROR';
		}
	}
	
	function closeDetails() {
		selectedCountry = null;
		countryDetails = [];
		quantumState = 'SYNCHRONIZED';
	}
	
	// Globe interaction handlers
	function handleMouseDown(e) {
		if (viewMode === 'globe') {
			isDragging = true;
			lastMouseX = e.clientX;
			lastMouseY = e.clientY;
			autoRotate = false;
		}
	}
	
	function handleMouseMove(e) {
		if (isDragging && viewMode === 'globe') {
			globeRotation.y += (e.clientX - lastMouseX) * 0.5;
			globeRotation.x = Math.max(-90, Math.min(90, globeRotation.x + (e.clientY - lastMouseY) * 0.5));
			lastMouseX = e.clientX;
			lastMouseY = e.clientY;
		}
	}
	
	function handleMouseUp() {
		isDragging = false;
	}
	
	function handleWheel(e) {
		if (viewMode === 'globe') {
			e.preventDefault();
			// Zoom functionality can be added here
		}
	}
</script>

<svelte:window 
	on:mousemove={handleMouseMove}
	on:mouseup={handleMouseUp}
/>

<div class="quantum-geo-interface">
	<!-- Atmosphere Particle Field -->
	<div class="atmosphere-field">
		{#each atmosphereParticles as particle}
			{@const phi = (90 - particle.lat) * Math.PI / 180}
			{@const theta = (particle.lng + 180) * Math.PI / 180}
			{@const x = particle.altitude * Math.sin(phi) * Math.cos(theta)}
			{@const y = particle.altitude * Math.cos(phi)}
			{@const z = particle.altitude * Math.sin(phi) * Math.sin(theta)}
			<div class="atmosphere-particle"
				 style="transform: translate3d({x}px, {y}px, {z}px);
						width: {particle.size}px;
						height: {particle.size}px;
						background: {particle.color};
						opacity: {0.3 + Math.sin(Date.now() * 0.001 + particle.lat) * 0.2}">
			</div>
		{/each}
	</div>
	
	<div class="geo-container">
		<!-- Quantum Header -->
		<header class="geo-header">
			<div class="header-layout">
				<div class="brand-area">
					<div class="geo-emblem">
						<div class="emblem-globe">
							<div class="globe-layer layer-1" style="border-color: {neonColors.primary}"></div>
							<div class="globe-layer layer-2" style="border-color: {neonColors.secondary}"></div>
							<div class="globe-layer layer-3" style="border-color: {neonColors.tertiary}"></div>
							<div class="globe-core">🌍</div>
						</div>
					</div>
					<div class="brand-data">
						<h1 class="interface-name" data-text="GLOBAL INTELLIGENCE MATRIX">
							GLOBAL INTELLIGENCE MATRIX
						</h1>
						<div class="status-bar">
							<span class="status-item">
								<span class="status-indicator" style="background: {threatLevel === 'CRITICAL' ? neonColors.critical : 
																					  threatLevel === 'HIGH' ? neonColors.threat : 
																					  threatLevel === 'ELEVATED' ? neonColors.warning : 
																					  neonColors.safe}"></span>
								THREAT: {threatLevel}
							</span>
							<span class="status-divider">|</span>
							<span class="status-item">STATE: {quantumState}</span>
							<span class="status-divider">|</span>
							<span class="status-item">ACTIVITY: {globalActivity.toFixed(0)}%</span>
							<span class="status-divider">|</span>
							<span class="status-item">FLOW: {dataFlowRate.toFixed(0)} Tb/s</span>
						</div>
					</div>
				</div>
				
				<div class="control-zone">
					<div class="search-module">
						<input 
							type="text" 
							bind:value={searchTerm}
							placeholder="COUNTRY SEARCH..."
							class="geo-search"
						/>
						<div class="search-scan" style="width: {searchTerm ? '100%' : '0'}"></div>
					</div>
					
					<div class="view-selector">
						<button class="view-btn {viewMode === 'globe' ? 'active' : ''}"
								on:click={() => { viewMode = 'globe'; autoRotate = true; }}
								style="--color: {neonColors.primary}">
							<span class="btn-icon">🌍</span>
							<span class="btn-label">GLOBE</span>
						</button>
						<button class="view-btn {viewMode === 'heatmap' ? 'active' : ''}"
								on:click={() => viewMode = 'heatmap'}
								style="--color: {neonColors.secondary}">
							<span class="btn-icon">🗺️</span>
							<span class="btn-label">HEATMAP</span>
						</button>
						<button class="view-btn {viewMode === 'connections' ? 'active' : ''}"
								on:click={() => viewMode = 'connections'}
								style="--color: {neonColors.tertiary}">
							<span class="btn-icon">🔗</span>
							<span class="btn-label">NETWORK</span>
						</button>
						<button class="view-btn {viewMode === 'intelligence' ? 'active' : ''}"
								on:click={() => viewMode = 'intelligence'}
								style="--color: {neonColors.quaternary}">
							<span class="btn-icon">🎯</span>
							<span class="btn-label">INTEL</span>
						</button>
					</div>
				</div>
				
				<div class="metrics-zone">
					<div class="metric-display">
						<div class="metric-value" style="color: {neonColors.primary}">
							{filteredCountries.length}
						</div>
						<div class="metric-label">NATIONS</div>
					</div>
					<div class="metric-display">
						<div class="metric-value" style="color: {neonColors.secondary}">
							{Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}
						</div>
						<div class="metric-label">ASSETS</div>
					</div>
				</div>
			</div>
		</header>
		
		<!-- Main Viewport -->
		<div class="geo-viewport">
			{#if loading && !selectedCountry}
				<div class="loading-screen">
					<div class="loading-globe">
						<div class="globe-scanner">
							<div class="scanner-ring ring-1" style="border-color: {neonColors.primary}"></div>
							<div class="scanner-ring ring-2" style="border-color: {neonColors.secondary}"></div>
							<div class="scanner-ring ring-3" style="border-color: {neonColors.tertiary}"></div>
						</div>
						<div class="scanner-core">🌍</div>
					</div>
					<p class="loading-message">ESTABLISHING GLOBAL QUANTUM LINK...</p>
				</div>
			{:else if selectedCountry}
				<!-- Country Detail View -->
				<div class="country-detail-interface">
					<div class="detail-header">
						<div class="country-profile">
							<div class="profile-flag" style="border-color: {calculateMetrics(selectedCountry.count).color}">
								<div class="flag-layers">
									<div class="layer" style="border-color: {neonColors.primary}"></div>
									<div class="layer" style="border-color: {neonColors.secondary}"></div>
								</div>
								<div class="flag-icon">🏳️</div>
							</div>
							<div class="profile-info">
								<h2 class="country-name">{selectedCountry.country.toUpperCase()}</h2>
								<div class="country-signature">
									{calculateMetrics(selectedCountry.count).quantumSignature}
								</div>
								<div class="country-badges">
									<span class="badge" style="background: {neonColors.primary}20; color: {neonColors.primary}">
										INFLUENCE: {calculateMetrics(selectedCountry.count).globalInfluence}%
									</span>
									<span class="badge" style="background: {neonColors.secondary}20; color: {neonColors.secondary}">
										ECONOMIC: {calculateMetrics(selectedCountry.count).economicPower}%
									</span>
									<span class="badge" style="background: {neonColors.tertiary}20; color: {neonColors.tertiary}">
										CYBER: {calculateMetrics(selectedCountry.count).cyberCapability}%
									</span>
								</div>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>
							<span>✕</span>
						</button>
					</div>
					
					<div class="detail-metrics-grid">
						<div class="metric-card">
							<div class="card-icon" style="color: {neonColors.primary}">📊</div>
							<div class="card-data">
								<div class="data-value" style="color: {neonColors.primary}">
									{selectedCountry.count.toLocaleString()}
								</div>
								<div class="data-label">DIGITAL ASSETS</div>
							</div>
							<div class="card-visual">
								<div class="mini-chart">
									{#each Array(20) as _, i}
										<div class="chart-bar" style="height: {Math.random() * 100}%; background: {neonColors.primary}"></div>
									{/each}
								</div>
							</div>
						</div>
						
						<div class="metric-card">
							<div class="card-icon" style="color: {neonColors.secondary}">🌐</div>
							<div class="card-data">
								<div class="data-value" style="color: {neonColors.secondary}">
									{getPercentage(selectedCountry.count)}%
								</div>
								<div class="data-label">GLOBAL SHARE</div>
							</div>
							<div class="card-visual">
								<div class="progress-ring">
									<svg viewBox="0 0 36 36">
										<path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
											  fill="none"
											  stroke="{neonColors.secondary}"
											  stroke-width="2"
											  stroke-dasharray="{getPercentage(selectedCountry.count)}, 100"/>
									</svg>
									<div class="ring-value">{getPercentage(selectedCountry.count)}%</div>
								</div>
							</div>
						</div>
						
						<div class="metric-card">
							<div class="card-icon" style="color: {neonColors.tertiary}">🛡️</div>
							<div class="card-data">
								<div class="data-value" style="color: {neonColors.tertiary}">
									{calculateMetrics(selectedCountry.count).stabilityScore}%
								</div>
								<div class="data-label">STABILITY</div>
							</div>
							<div class="card-visual">
								<div class="stability-meter">
									<div class="meter-fill" style="width: {calculateMetrics(selectedCountry.count).stabilityScore}%; 
																   background: {neonColors.tertiary}"></div>
									<div class="meter-markers">
										{#each Array(10) as _, i}
											<div class="marker"></div>
										{/each}
									</div>
								</div>
							</div>
						</div>
						
						<div class="metric-card">
							<div class="card-icon" style="color: {neonColors.threat}">⚠️</div>
							<div class="card-data">
								<div class="data-value" style="color: {neonColors.threat}">
									{calculateMetrics(selectedCountry.count).threatIndex}
								</div>
								<div class="data-label">THREAT INDEX</div>
							</div>
							<div class="card-visual">
								<div class="threat-radar">
									<div class="radar-sweep" style="transform: rotate({Date.now() * 0.1 % 360}deg)"></div>
									<div class="radar-dot" style="background: {neonColors.threat}"></div>
								</div>
							</div>
						</div>
					</div>
					
					<div class="detail-data-stream">
						<div class="stream-header">
							<h3>INTELLIGENCE DATA STREAM</h3>
							<div class="stream-indicators">
								<span class="indicator-live">LIVE</span>
								<span class="indicator-pulse"></span>
							</div>
						</div>
						<div class="stream-table-wrapper">
							<table class="intel-table">
								<thead>
									<tr>
										<th>ASSET_ID</th>
										<th>REGION</th>
										<th>INFRASTRUCTURE</th>
										<th>DIVISION</th>
										<th>CMDB_SYNC</th>
										<th>TANIUM_SHIELD</th>
									</tr>
								</thead>
								<tbody>
									{#each countryDetails as host}
										<tr class="intel-row">
											<td class="asset-id">{host.host.substring(0, 30)}</td>
											<td>{host.region || 'CLASSIFIED'}</td>
											<td>{host.infrastructure_type || 'UNKNOWN'}</td>
											<td>{host.business_unit || 'UNASSIGNED'}</td>
											<td>
												<span class="sync-status {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'synced' : 'desynced'}"
													  style="color: {host.present_in_cmdb?.toLowerCase().includes('yes') ? neonColors.safe : neonColors.critical}">
													{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}
												</span>
											</td>
											<td>
												<span class="shield-status {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'protected' : 'vulnerable'}"
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
			{:else if viewMode === 'globe'}
				<!-- Globe View -->
				<div class="globe-view" on:mousedown={handleMouseDown} on:wheel={handleWheel}>
					<div class="globe-container" style="transform: rotateX({globeRotation.x}deg) rotateY({globeRotation.y}deg) rotateZ({globeRotation.z}deg)">
						<div class="globe-sphere">
							<!-- Globe mesh -->
							<svg class="globe-svg" viewBox="-300 -300 600 600">
								<defs>
									<radialGradient id="globeGradient">
										<stop offset="0%" style="stop-color:{neonColors.primary};stop-opacity:0.3" />
										<stop offset="100%" style="stop-color:{neonColors.primary};stop-opacity:0" />
									</radialGradient>
									<filter id="glow">
										<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
										<feMerge>
											<feMergeNode in="coloredBlur"/>
											<feMergeNode in="SourceGraphic"/>
										</feMerge>
									</filter>
								</defs>
								
								<!-- Globe outline -->
								<circle cx="0" cy="0" r="200" fill="url(#globeGradient)" stroke="{neonColors.primary}" stroke-width="0.5" opacity="0.3"/>
								
								<!-- Latitude lines -->
								{#each [-60, -30, 0, 30, 60] as lat}
									{@const y = Math.sin(lat * Math.PI / 180) * 200}
									{@const r = Math.cos(lat * Math.PI / 180) * 200}
									<ellipse cx="0" cy="{y}" rx="{r}" ry="{r * 0.3}" fill="none" stroke="{neonColors.primary}" stroke-width="0.3" opacity="0.5"/>
								{/each}
								
								<!-- Longitude lines -->
								{#each [0, 30, 60, 90, 120, 150] as lng}
									<ellipse cx="0" cy="0" rx="200" ry="200" fill="none" stroke="{neonColors.primary}" stroke-width="0.3" opacity="0.5"
											 transform="rotate({lng} 0 0)"/>
								{/each}
								
								<!-- Country nodes -->
								{#each countryNodes as node}
									{@const visible = node.z > 0}
									{#if visible}
										<g transform="translate({node.x}, {-node.y})" on:click={() => drillDownCountry(node.name, node.count)}>
											<circle r="{5 + node.importance * 15}" fill="{node.color}" opacity="0.3"/>
											<circle r="{3 + node.importance * 8}" fill="{node.color}" opacity="0.8" filter="url(#glow)"/>
											<text y="-{10 + node.importance * 15}" text-anchor="middle" fill="#ffffff" font-size="8" opacity="0.9">
												{node.name.substring(0, 15).toUpperCase()}
											</text>
										</g>
									{/if}
								{/each}
								
								<!-- Connections -->
								{#each geoConnections as conn}
									{#if countryNodes[conn.source] && countryNodes[conn.target] && countryNodes[conn.source].z > 0 && countryNodes[conn.target].z > 0}
										<line x1="{countryNodes[conn.source].x}" y1="{-countryNodes[conn.source].y}"
											  x2="{countryNodes[conn.target].x}" y2="{-countryNodes[conn.target].y}"
											  stroke="{conn.type === 'economic' ? neonColors.tertiary : 
													   conn.type === 'cyber' ? neonColors.data : 
													   conn.type === 'diplomatic' ? neonColors.quaternary : 
													   neonColors.primary}"
											  stroke-width="{0.5 + conn.strength}"
											  opacity="{0.2 + conn.strength * 0.3}"/>
									{/if}
								{/each}
								
								<!-- Satellites -->
								{#each satellites as sat}
									{@const satPhi = (90 - sat.lat) * Math.PI / 180}
									{@const satTheta = (sat.lng + 180) * Math.PI / 180}
									{@const satX = sat.altitude * Math.sin(satPhi) * Math.cos(satTheta)}
									{@const satY = sat.altitude * Math.cos(satPhi)}
									<g transform="translate({satX}, {-satY})">
										<rect x="-5" y="-2" width="10" height="4" fill="{sat.active ? neonColors.safe : neonColors.critical}" opacity="0.8"/>
										<line x1="0" y1="0" x2="0" y2="{200 - sat.altitude}" stroke="{neonColors.data}" stroke-width="0.3" opacity="0.5" stroke-dasharray="2,3"/>
									</g>
								{/each}
							</svg>
						</div>
					</div>
					
					<div class="globe-controls">
						<button class="control-btn" on:click={() => autoRotate = !autoRotate} style="color: {neonColors.primary}">
							{autoRotate ? '⏸️' : '▶️'} {autoRotate ? 'PAUSE' : 'ROTATE'}
						</button>
					</div>
				</div>
			{:else if viewMode === 'heatmap'}
				<!-- Heatmap View (continued in next part...) -->
			{/if}
		</div>
	</div>
</div>

<style>
	/* Styles will continue in next part */
</style>