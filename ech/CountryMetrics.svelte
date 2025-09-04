<!-- CountryMetrics.svelte - Quantum Geopolitical Intelligence Matrix -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';
	let viewMode = 'globe'; // 'globe', 'matrix', 'threat'
	let globeRotation = { x: 0, y: 0, z: 0 };
	let satellitePositions = [];
	let dataStreams = [];
	let threatLevel = 'NOMINAL';
	let geoNodes = [];
	let quantumFlux = 0;
	let orbitalData = [];
	
	// Animation intervals
	let globeInterval;
	let satelliteInterval;
	let dataInterval;
	let fluxInterval;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/country_metrics');
			let result = await response.json();
			data = result;
			loading = false;
			initializeGeoSystem();
			startGlobalAnimations();
		} catch (err) {
			console.error('Geopolitical matrix sync failed:', err);
			loading = false;
		}
	});
	
	onDestroy(() => {
		if (globeInterval) clearInterval(globeInterval);
		if (satelliteInterval) clearInterval(satelliteInterval);
		if (dataInterval) clearInterval(dataInterval);
		if (fluxInterval) clearInterval(fluxInterval);
	});
	
	function initializeGeoSystem() {
		// Initialize satellite constellation
		for (let i = 0; i < 8; i++) {
			let angle = (i / 8) * Math.PI * 2;
			satellitePositions.push({
				id: i,
				angle: angle,
				radius: 180 + Math.random() * 40,
				speed: 0.5 + Math.random() * 0.5,
				active: Math.random() > 0.2,
				signal: Math.random() * 100
			});
		}
		
		// Initialize data streams
		for (let i = 0; i < 50; i++) {
			dataStreams.push({
				x: Math.random() * 100,
				y: Math.random() * 100,
				speed: 0.5 + Math.random() * 2,
				width: Math.random() * 3 + 1,
				color: Math.random() > 0.5 ? '#00ffff' : '#ff00ff'
			});
		}
		
		// Initialize geo nodes for countries
		if (data.global_intelligence) {
			let countries = Object.entries(data.global_intelligence).slice(0, 50);
			countries.forEach(([country, count], i) => {
				// Simulate geographic distribution
				let lat = (Math.random() - 0.5) * 180;
				let lng = (Math.random() - 0.5) * 360;
				
				geoNodes.push({
					country: country,
					count: count,
					lat: lat,
					lng: lng,
					x: 50 + Math.cos(lng * Math.PI / 180) * 40 * Math.cos(lat * Math.PI / 180),
					y: 50 + Math.sin(lat * Math.PI / 180) * 40,
					z: Math.sin(lng * Math.PI / 180) * 40 * Math.cos(lat * Math.PI / 180),
					threat: Math.random() * 100,
					stability: 50 + Math.random() * 50,
					connections: []
				});
			});
			
			// Create geopolitical connections
			geoNodes.forEach((node, i) => {
				let connectionCount = Math.floor(Math.random() * 3) + 1;
				for (let j = 0; j < connectionCount; j++) {
					let target = Math.floor(Math.random() * geoNodes.length);
					if (target !== i) {
						node.connections.push(target);
					}
				}
			});
		}
		
		// Initialize orbital data paths
		for (let i = 0; i < 20; i++) {
			orbitalData.push({
				startAngle: Math.random() * Math.PI * 2,
				endAngle: Math.random() * Math.PI * 2,
				radius: 100 + Math.random() * 100,
				active: Math.random() > 0.5
			});
		}
	}
	
	function startGlobalAnimations() {
		globeInterval = setInterval(() => {
			globeRotation = {
				x: (globeRotation.x + 0.2) % 360,
				y: (globeRotation.y + 0.5) % 360,
				z: (globeRotation.z + 0.1) % 360
			};
		}, 50);
		
		satelliteInterval = setInterval(() => {
			satellitePositions = satellitePositions.map(sat => ({
				...sat,
				angle: (sat.angle + sat.speed * 0.01) % (Math.PI * 2),
				signal: Math.max(0, Math.min(100, sat.signal + (Math.random() - 0.5) * 10))
			}));
		}, 100);
		
		dataInterval = setInterval(() => {
			dataStreams = dataStreams.map(stream => ({
				...stream,
				y: (stream.y - stream.speed + 100) % 100
			}));
		}, 50);
		
		fluxInterval = setInterval(() => {
			quantumFlux = Math.sin(Date.now() * 0.001) * 50 + 50;
			
			// Update threat level based on activity
			let avgThreat = geoNodes.reduce((sum, node) => sum + node.threat, 0) / geoNodes.length;
			threatLevel = avgThreat < 30 ? 'NOMINAL' : 
						  avgThreat < 50 ? 'ELEVATED' : 
						  avgThreat < 70 ? 'HIGH' : 'CRITICAL';
		}, 2000);
	}
	
	$: filteredCountries = data.global_intelligence ? 
		Object.entries(data.global_intelligence)
			.filter(([country]) => country.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredCountries.length > 0 ? Math.max(...filteredCountries.map(([,c]) => c)) : 1;
	$: minCount = filteredCountries.length > 0 ? Math.min(...filteredCountries.map(([,c]) => c)) : 0;
	
	function calculateCountryMetrics(count) {
		let normalized = (count - minCount) / (maxCount - minCount || 1);
		let percentile = normalized * 100;
		
		let classification = 'UNKNOWN';
		let geoInfluence = 0;
		let digitalFootprint = 0;
		let riskIndex = 0;
		let color = '#00ffff';
		let icon = '🌍';
		
		if (percentile >= 85) {
			classification = 'SUPERPOWER';
			geoInfluence = 100;
			digitalFootprint = 95;
			riskIndex = 85;
			color = '#ff00ff';
			icon = '⬢';
		} else if (percentile >= 65) {
			classification = 'MAJOR';
			geoInfluence = 75;
			digitalFootprint = 70;
			riskIndex = 60;
			color = '#ff6600';
			icon = '◆';
		} else if (percentile >= 45) {
			classification = 'REGIONAL';
			geoInfluence = 50;
			digitalFootprint = 45;
			riskIndex = 40;
			color = '#00ff00';
			icon = '▲';
		} else if (percentile >= 25) {
			classification = 'EMERGING';
			geoInfluence = 30;
			digitalFootprint = 25;
			riskIndex = 25;
			color = '#00ffff';
			icon = '●';
		} else {
			classification = 'DEVELOPING';
			geoInfluence = 15;
			digitalFootprint = 10;
			riskIndex = 10;
			color = '#0099ff';
			icon = '○';
		}
		
		return {
			classification: classification,
			geoInfluence: geoInfluence,
			digitalFootprint: digitalFootprint,
			riskIndex: riskIndex,
			color: color,
			icon: icon,
			percentile: percentile.toFixed(1),
			gdpImpact: (normalized * 100).toFixed(1),
			cyberScore: (50 + Math.random() * 50).toFixed(0),
			stabilityIndex: (100 - riskIndex + Math.random() * 10).toFixed(0)
		};
	}
	
	function getPercentage(count) {
		let total = Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0);
		return total > 0 ? ((count / total) * 100).toFixed(2) : '0.00';
	}
	
	async function drillDownCountry(country, count) {
		selectedCountry = { country: country, count: count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(country)}`);
			let result = await response.json();
			countryDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Country deep scan failed:', err);
			countryDetails = [];
			loading = false;
		}
	}
	
	function closeDetails() {
		selectedCountry = null;
		countryDetails = [];
	}
</script>

<div class="quantum-geo-matrix">
	<!-- Data Streams Background -->
	<div class="data-stream-layer">
		{#each dataStreams as stream}
			<div class="data-stream"
				 style="left: {stream.x}%;
						top: {stream.y}%;
						width: {stream.width}px;
						height: 20px;
						background: linear-gradient(180deg, transparent, {stream.color}, transparent);
						opacity: 0.5">
			</div>
		{/each}
	</div>
	
	<!-- Orbital Grid -->
	<svg class="orbital-grid" viewBox="0 0 100 100">
		<defs>
			<radialGradient id="geoGradient">
				<stop offset="0%" style="stop-color:#00ffff;stop-opacity:0.5"/>
				<stop offset="100%" style="stop-color:#00ffff;stop-opacity:0"/>
			</radialGradient>
			<filter id="geoGlow">
				<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
				<feMerge>
					<feMergeNode in="coloredBlur"/>
					<feMergeNode in="SourceGraphic"/>
				</feMerge>
			</filter>
		</defs>
		
		<!-- Orbital rings -->
		{#each [30, 40, 50] as radius}
			<circle cx="50" cy="50" r="{radius}" 
					fill="none" 
					stroke="#00ffff" 
					stroke-width="0.1" 
					opacity="0.3"
					stroke-dasharray="2,4">
				<animateTransform attributeName="transform" 
								  attributeType="XML" 
								  type="rotate" 
								  from="0 50 50" 
								  to="360 50 50" 
								  dur="{20 + radius / 5}s" 
								  repeatCount="indefinite"/>
			</circle>
		{/each}
	</svg>
	
	<div class="geo-interface">
		<!-- Quantum Header -->
		<header class="geo-header">
			<div class="header-section">
				<div class="geo-logo">
					<div class="globe-container" style="transform: rotateX({globeRotation.x}deg) rotateY({globeRotation.y}deg) rotateZ({globeRotation.z}deg)">
						<div class="globe-meridian meridian-1"></div>
						<div class="globe-meridian meridian-2"></div>
						<div class="globe-meridian meridian-3"></div>
						<div class="globe-core">🌍</div>
					</div>
				</div>
				<div class="header-info">
					<h1 class="geo-title">GLOBAL INTELLIGENCE MATRIX</h1>
					<div class="threat-status">
						<span class="threat-indicator {threatLevel.toLowerCase()}"></span>
						<span class="threat-text">THREAT LEVEL: {threatLevel}</span>
						<span class="flux-text">| QUANTUM FLUX: {quantumFlux.toFixed(0)}%</span>
					</div>
				</div>
			</div>
			
			<div class="search-control">
				<input 
					type="text" 
					bind:value={searchTerm}
					placeholder="COUNTRY SEARCH..."
					class="geo-search"
				/>
				<div class="scan-wave" style="width: {searchTerm ? '100%' : '0'}"></div>
			</div>
			
			<div class="view-controls">
				<button class="view-btn {viewMode === 'globe' ? 'active' : ''}"
						on:click={() => viewMode = 'globe'}>
					<span>🌍</span>
					GLOBE
				</button>
				<button class="view-btn {viewMode === 'matrix' ? 'active' : ''}"
						on:click={() => viewMode = 'matrix'}>
					<span>◈</span>
					MATRIX
				</button>
				<button class="view-btn {viewMode === 'threat' ? 'active' : ''}"
						on:click={() => viewMode = 'threat'}>
					<span>⚠</span>
					THREAT
				</button>
			</div>
			
			<div class="global-metrics">
				<div class="metric">
					<div class="metric-value">{filteredCountries.length}</div>
					<div class="metric-label">NATIONS</div>
				</div>
				<div class="metric">
					<div class="metric-value">{Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="metric-label">NODES</div>
				</div>
			</div>
		</header>
		
		<!-- Main Content -->
		<div class="geo-content">
			{#if loading && !selectedCountry}
				<div class="geo-loader">
					<div class="loader-globe">
						<div class="globe-ring ring-1"></div>
						<div class="globe-ring ring-2"></div>
						<div class="globe-ring ring-3"></div>
						<div class="globe-center">🌍</div>
					</div>
					<p class="loader-text">ESTABLISHING GLOBAL QUANTUM LINK...</p>
				</div>
			{:else if selectedCountry}
				{#key selectedCountry}
				<div class="country-detail-view">
					<div class="detail-header">
						<div class="country-hologram">
							<div class="hologram-flag" style="color: {calculateCountryMetrics(selectedCountry.count).color}">
								{calculateCountryMetrics(selectedCountry.count).icon}
							</div>
							<div class="country-info">
								<h2>{selectedCountry.country.toUpperCase()}</h2>
								<div class="country-stats">
									<span class="stat">INFLUENCE: {calculateCountryMetrics(selectedCountry.count).geoInfluence}%</span>
									<span class="stat">CYBER: {calculateCountryMetrics(selectedCountry.count).cyberScore}</span>
									<span class="stat">STABILITY: {calculateCountryMetrics(selectedCountry.count).stabilityIndex}</span>
								</div>
							</div>
						</div>
						<button class="geo-close" on:click={closeDetails}>
							<span>✕</span>
						</button>
					</div>
					
					<div class="country-metrics">
						<div class="metric-card">
							<div class="card-value" style="color: {calculateCountryMetrics(selectedCountry.count).color}">
								{selectedCountry.count.toLocaleString()}
							</div>
							<div class="card-label">DIGITAL ASSETS</div>
						</div>
						<div class="metric-card">
							<div class="card-value" style="color: {calculateCountryMetrics(selectedCountry.count).color}">
								{getPercentage(selectedCountry.count)}%
							</div>
							<div class="card-label">GLOBAL SHARE</div>
						</div>
						<div class="metric-card">
							<div class="card-value" style="color: {calculateCountryMetrics(selectedCountry.count).color}">
								{calculateCountryMetrics(selectedCountry.count).classification}
							</div>
							<div class="card-label">GEO-STATUS</div>
						</div>
						<div class="metric-card">
							<div class="card-value" style="color: {calculateCountryMetrics(selectedCountry.count).color}">
								{calculateCountryMetrics(selectedCountry.count).riskIndex}%
							</div>
							<div class="card-label">RISK INDEX</div>
						</div>
					</div>
					
					<div class="country-stream">
						<table class="intel-table">
							<thead>
								<tr>
									<th>ASSET_ID</th>
									<th>REGION</th>
									<th>INFRASTRUCTURE</th>
									<th>DIVISION</th>
									<th>CMDB_SYNC</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each countryDetails as host}
									<tr class="intel-row">
										<td class="asset-id">{host.host.substring(0, 25)}</td>
										<td>{host.region || 'CLASSIFIED'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>{host.business_unit || 'UNASSIGNED'}</td>
										<td>
											<span class="sync-status {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'synced' : 'unsynced'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}
											</span>
										</td>
										<td>
											<span class="shield-status {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'protected' : 'exposed'}">
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
			{:else if viewMode === 'globe'}
				<div class="globe-view">
					<div class="globe-visualization">
						<svg class="globe-svg" viewBox="0 0 400 400">
							<!-- Globe outline -->
							<circle cx="200" cy="200" r="150" 
									fill="none" 
									stroke="#00ffff" 
									stroke-width="1" 
									opacity="0.5"/>
							
							<!-- Latitude lines -->
							{#each [-60, -30, 0, 30, 60] as lat}
								<ellipse cx="200" cy="200" 
										 rx="{150 * Math.cos(lat * Math.PI / 180)}" 
										 ry="10"
										 fill="none" 
										 stroke="#00ffff" 
										 stroke-width="0.5" 
										 opacity="0.3"
										 transform="translate(0, {lat * 1.5})"/>
							{/each}
							
							<!-- Country nodes on globe -->
							{#each geoNodes.slice(0, 30) as node}
								{#key node.country}
								<g transform="translate({200 + node.x * 3}, {200 + node.y * 3})"
								   on:click={() => drillDownCountry(node.country, node.count)}>
									<circle r="{2 + calculateCountryMetrics(node.count).geoInfluence * 0.05}"
											fill="{calculateCountryMetrics(node.count).color}"
											opacity="0.8"
											filter="url(#geoGlow)">
										<animate attributeName="r" 
												 values="{2 + calculateCountryMetrics(node.count).geoInfluence * 0.05};{3 + calculateCountryMetrics(node.count).geoInfluence * 0.05};{2 + calculateCountryMetrics(node.count).geoInfluence * 0.05}"
												 dur="3s" 
												 repeatCount="indefinite"/>
									</circle>
								</g>
								{/key}
							{/each}
							
							<!-- Satellite constellation -->
							{#each satellitePositions as sat}
								<g transform="translate({200 + Math.cos(sat.angle) * sat.radius}, {200 + Math.sin(sat.angle) * sat.radius})">
									<rect x="-5" y="-2" width="10" height="4" 
										  fill="{sat.active ? '#00ff00' : '#ff0000'}" 
										  opacity="{0.5 + sat.signal / 200}"/>
									<line x1="0" y1="0" x2="0" y2="{-sat.signal / 5}" 
										  stroke="{sat.active ? '#00ff00' : '#ff0000'}" 
										  stroke-width="0.5" 
										  opacity="0.5"/>
								</g>
							{/each}
						</svg>
					</div>
				</div>
			{:else if viewMode === 'matrix'}
				<div class="matrix-view">
					<div class="country-grid">
						{#each filteredCountries.slice(0, 36) as [country, count], i}
							{#key country}
							<div class="country-cell"
								 style="background: linear-gradient(135deg, {calculateCountryMetrics(count).color}20, transparent);
										border-color: {calculateCountryMetrics(count).color}"
								 on:click={() => drillDownCountry(country, count)}>
								<div class="cell-header">
									<span class="cell-icon" style="color: {calculateCountryMetrics(count).color}">
										{calculateCountryMetrics(count).icon}
									</span>
									<span class="cell-class">{calculateCountryMetrics(count).classification}</span>
								</div>
								<div class="cell-country">{country.substring(0, 15).toUpperCase()}</div>
								<div class="cell-stats">
									<div class="stat-bar">
										<div class="stat-fill" style="width: {calculateCountryMetrics(count).percentile}%; 
																	   background: {calculateCountryMetrics(count).color}"></div>
									</div>
									<span class="stat-value">{count.toLocaleString()}</span>
								</div>
								<div class="cell-footer">
									<span>INF: {calculateCountryMetrics(count).geoInfluence}%</span>
									<span>RSK: {calculateCountryMetrics(count).riskIndex}%</span>
								</div>
							</div>
							{/key}
						{/each}
					</div>
				</div>
			{:else if viewMode === 'threat'}
				<div class="threat-view">
					<div class="threat-map">
						{#each filteredCountries.slice(0, 20) as [country, count], i}
							{#key country}
							<div class="threat-node"
								 style="left: {20 + (i % 5) * 15}%;
										top: {20 + Math.floor(i / 5) * 15}%;
										background: radial-gradient(circle, {calculateCountryMetrics(count).riskIndex > 50 ? '#ff0000' : 
																			  calculateCountryMetrics(count).riskIndex > 30 ? '#ff6600' : 
																			  '#00ff00'}40, transparent)"
								 on:click={() => drillDownCountry(country, count)}>
								<div class="threat-level-circle" 
									 style="border-color: {calculateCountryMetrics(count).riskIndex > 50 ? '#ff0000' : 
														   calculateCountryMetrics(count).riskIndex > 30 ? '#ff6600' : 
														   '#00ff00'}">
									<div class="threat-pulse"></div>
								</div>
								<div class="threat-info">
									<div class="threat-country">{country.substring(0, 10)}</div>
									<div class="threat-risk">{calculateCountryMetrics(count).riskIndex}%</div>
								</div>
							</div>
							{/key}
						{/each}
						
						<!-- Threat connections -->
						<svg class="threat-connections" viewBox="0 0 100 100">
							{#each geoNodes.slice(0, 10) as node, i}
								{#each node.connections as targetIdx}
									{#if targetIdx < 10}
										<line x1="{20 + (i % 5) * 15}" 
											  y1="{20 + Math.floor(i / 5) * 15}"
											  x2="{20 + (targetIdx % 5) * 15}" 
											  y2="{20 + Math.floor(targetIdx / 5) * 15}"
											  stroke="{node.threat > 50 ? '#ff0000' : '#ff6600'}"
											  stroke-width="0.2"
											  opacity="0.3"
											  stroke-dasharray="2,3">
											<animate attributeName="stroke-dashoffset" 
													 values="0;10" 
													 dur="5s" 
													 repeatCount="indefinite"/>
										</line>
									{/if}
								{/each}
							{/each}
						</svg>
					</div>
				</div>
			{/if}
			
			<!-- Country Data Table -->
			<div class="country-data-matrix">
				<table class="geo-table">
					<thead>
						<tr>
							<th>RANK</th>
							<th>NATION</th>
							<th>STATUS</th>
							<th>ASSETS</th>
							<th>SHARE</th>
							<th>INFLUENCE</th>
							<th>DIGITAL</th>
							<th>RISK</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredCountries as [country, count], index}
							{#key country}
							<tr class="geo-row"
								style="border-left: 3px solid {calculateCountryMetrics(count).color}"
								on:click={() => drillDownCountry(country, count)}>
								<td class="rank-cell">
									<span style="color: {calculateCountryMetrics(count).color}">#{index + 1}</span>
								</td>
								<td class="country-cell">
									<span class="country-icon" style="color: {calculateCountryMetrics(count).color}">
										{calculateCountryMetrics(count).icon}
									</span>
									<span class="country-name">{country.substring(0, 20).toUpperCase()}</span>
								</td>
								<td>
									<span class="status-badge" 
										  style="background: {calculateCountryMetrics(count).color}15; 
												 color: {calculateCountryMetrics(count).color}; 
												 border: 1px solid {calculateCountryMetrics(count).color}">
										{calculateCountryMetrics(count).classification}
									</span>
								</td>
								<td class="numeric">{count.toLocaleString()}</td>
								<td class="share-cell">
									<div class="share-bar">
										<div class="share-fill" 
											 style="width: {getPercentage(count)}%; 
													background: {calculateCountryMetrics(count).color}"></div>
									</div>
									<span>{getPercentage(count)}%</span>
								</td>
								<td>
									<div class="influence-meter">
										<div class="influence-level" 
											 style="width: {calculateCountryMetrics(count).geoInfluence}%; 
													background: {calculateCountryMetrics(count).color}"></div>
									</div>
								</td>
								<td class="digital-cell">
									<span style="color: {calculateCountryMetrics(count).color}">
										{calculateCountryMetrics(count).digitalFootprint}%
									</span>
								</td>
								<td class="risk-cell">
									<span style="color: {calculateCountryMetrics(count).riskIndex > 60 ? '#ff0000' : 
														 calculateCountryMetrics(count).riskIndex > 40 ? '#ff6600' : 
														 '#00ff00'}">
										{calculateCountryMetrics(count).riskIndex}%
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
	.quantum-geo-matrix {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		position: relative;
		overflow: hidden;
	}
	
	/* Data Stream Layer */
	.data-stream-layer {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: hidden;
	}
	
	.data-stream {
		position: absolute;
		animation: dataFlow 5s linear infinite;
	}
	
	@keyframes dataFlow {
		from { transform: translateY(0); }
		to { transform: translateY(-100vh); }
	}
	
	/* Orbital Grid */
	.orbital-grid {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	
	.geo-interface {
		position: relative;
		z-index: 1;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
	
	/* Geo Header */
	.geo-header {
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
	
	.header-section {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.geo-logo {
		width: 60px;
		height: 60px;
		perspective: 1000px;
	}
	
	.globe-container {
		width: 100%;
		height: 100%;
		position: relative;
		transform-style: preserve-3d;
	}
	
	.globe-meridian {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 1px solid #00ffff;
		border-radius: 50%;
		opacity: 0.3;
	}
	
	.meridian-1 { transform: rotateY(0deg); }
	.meridian-2 { transform: rotateY(60deg); }
	.meridian-3 { transform: rotateY(120deg); }
	
	.globe-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 2rem;
		animation: globePulse 3s ease-in-out infinite;
	}
	
	@keyframes globePulse {
		0%, 100% { transform: translate(-50%, -50%) scale(1); }
		50% { transform: translate(-50%, -50%) scale(1.1); }
	}
	
	.header-info h1 {
		margin: 0;
		font-size: 1.3rem;
		font-weight: 200;
		letter-spacing: 0.2em;
		background: linear-gradient(90deg, #00ffff, #ff00ff, #00ff00);
		background-size: 200% 100%;
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		animation: geoGradient 4s linear infinite;
	}
	
	@keyframes geoGradient {
		0% { background-position: 0% 50%; }
		100% { background-position: 200% 50%; }
	}
	
	.threat-status {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-top: 0.5rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
		letter-spacing: 0.1em;
	}
	
	.threat-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: threatPulse 2s ease-in-out infinite;
	}
	
	.threat-indicator.nominal { background: #00ff00; box-shadow: 0 0 10px #00ff00; }
	.threat-indicator.elevated { background: #ffff00; box-shadow: 0 0 10px #ffff00; }
	.threat-indicator.high { background: #ff6600; box-shadow: 0 0 10px #ff6600; animation-duration: 1s; }
	.threat-indicator.critical { background: #ff0000; box-shadow: 0 0 10px #ff0000; animation-duration: 0.5s; }
	
	@keyframes threatPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.5; transform: scale(1.5); }
	}
	
	/* Search Control */
	.search-control {
		position: relative;
		flex: 1;
		max-width: 400px;
	}
	
	.geo-search {
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
	
	.geo-search:focus {
		outline: none;
		border-color: #00ffff;
		background: rgba(0, 255, 255, 0.05);
		box-shadow: 0 0 30px rgba(0, 255, 255, 0.3);
	}
	
	.scan-wave {
		position: absolute;
		bottom: 0;
		left: 0;
		height: 2px;
		background: linear-gradient(90deg, transparent, #00ffff, transparent);
		transition: width 0.3s ease;
	}
	
	/* View Controls */
	.view-controls {
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
	
	/* Global Metrics */
	.global-metrics {
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
	
	/* Geo Content */
	.geo-content {
		flex: 1;
		display: flex;
		gap: 2rem;
		padding: 2rem;
		overflow: hidden;
	}
	
	/* Loader */
	.geo-loader {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.loader-globe {
		position: relative;
		width: 120px;
		height: 120px;
	}
	
	.globe-ring {
		position: absolute;
		border: 1px solid #00ffff;
		border-radius: 50%;
		animation: globeRotate 4s linear infinite;
	}
	
	.ring-1 {
		inset: 0;
		animation-direction: normal;
	}
	
	.ring-2 {
		inset: 20px;
		animation-direction: reverse;
		border-color: #ff00ff;
	}
	
	.ring-3 {
		inset: 40px;
		animation-duration: 6s;
		border-color: #00ff00;
	}
	
	.globe-center {
		position: absolute;
		inset: 45px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
	}
	
	@keyframes globeRotate {
		from { transform: rotateX(60deg) rotateZ(0deg); }
		to { transform: rotateX(60deg) rotateZ(360deg); }
	}
	
	.loader-text {
		color: rgba(0, 255, 255, 0.6);
		font-size: 0.9rem;
		letter-spacing: 0.2em;
		animation: pulse 2s ease-in-out infinite;
	}
	
	/* Globe View */
	.globe-view {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.globe-visualization {
		width: 100%;
		height: 100%;
		max-width: 600px;
		max-height: 600px;
		animation: globeSpin 60s linear infinite;
	}
	
	@keyframes globeSpin {
		from { transform: rotateY(0deg); }
		to { transform: rotateY(360deg); }
	}
	
	.globe-svg {
		width: 100%;
		height: 100%;
	}
	
	/* Matrix View */
	.matrix-view {
		flex: 1;
		overflow: auto;
	}
	
	.country-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		gap: 1rem;
		padding: 1rem;
	}
	
	.country-cell {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.country-cell:hover {
		transform: scale(1.05);
		z-index: 10;
		box-shadow: 0 0 30px currentColor;
	}
	
	.cell-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.cell-icon {
		font-size: 1.2rem;
	}
	
	.cell-class {
		font-size: 0.6rem;
		opacity: 0.7;
	}
	
	.cell-country {
		font-size: 0.8rem;
		font-weight: 300;
		letter-spacing: 0.05em;
		color: #ffffff;
	}
	
	.cell-stats {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.7rem;
	}
	
	.stat-bar {
		flex: 1;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
	}
	
	.stat-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.stat-value {
		color: rgba(255, 255, 255, 0.7);
		font-family: 'Courier New', monospace;
	}
	
	.cell-footer {
		display: flex;
		justify-content: space-between;
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	/* Threat View */
	.threat-view {
		flex: 1;
		position: relative;
	}
	
	.threat-map {
		width: 100%;
		height: 100%;
		position: relative;
	}
	
	.threat-node {
		position: absolute;
		width: 100px;
		height: 100px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.threat-node:hover {
		transform: scale(1.1);
		z-index: 10;
	}
	
	.threat-level-circle {
		width: 50px;
		height: 50px;
		border: 2px solid;
		border-radius: 50%;
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.threat-pulse {
		position: absolute;
		inset: -10px;
		border: 1px solid currentColor;
		border-radius: 50%;
		animation: threatRing 2s ease-out infinite;
	}
	
	@keyframes threatRing {
		0% { transform: scale(0.5); opacity: 1; }
		100% { transform: scale(1.5); opacity: 0; }
	}
	
	.threat-info {
		margin-top: 0.5rem;
		text-align: center;
	}
	
	.threat-country {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
		letter-spacing: 0.05em;
	}
	
	.threat-risk {
		font-size: 0.8rem;
		font-weight: 600;
		color: #ffffff;
	}
	
	.threat-connections {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	
	/* Country Data Matrix */
	.country-data-matrix {
		width: 50%;
		overflow: auto;
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid rgba(0, 255, 255, 0.1);
		backdrop-filter: blur(10px);
	}
	
	.geo-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.geo-table th {
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.1), rgba(0, 0, 0, 0.8));
		color: #00ffff;
		padding: 0.75rem 0.5rem;
		text-align: left;
		font-size: 0.65rem;
		font-weight: 300;
		letter-spacing: 0.15em;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		position: sticky;
		top: 0;
		z-index: 10;
	}
	
	.geo-row {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.geo-row:hover {
		background: rgba(0, 255, 255, 0.02);
		transform: translateX(5px);
	}
	
	.geo-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank-cell {
		font-weight: 600;
		font-family: 'Courier New', monospace;
	}
	
	.country-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.country-icon {
		font-size: 0.9rem;
	}
	
	.country-name {
		font-weight: 300;
		letter-spacing: 0.05em;
	}
	
	.status-badge {
		padding: 0.15rem 0.3rem;
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}
	
	.numeric {
		font-family: 'Courier New', monospace;
		color: #00ffff;
	}
	
	.share-cell {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.65rem;
	}
	
	.share-bar {
		width: 40px;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}
	
	.share-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.influence-meter {
		width: 40px;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}
	
	.influence-level {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.digital-cell {
		font-family: 'Courier New', monospace;
		font-size: 0.7rem;
	}
	
	.risk-cell {
		font-weight: 600;
		font-size: 0.7rem;
	}
	
	/* Detail View */
	.country-detail-view {
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
	
	.country-hologram {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.hologram-flag {
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2.5rem;
		background: radial-gradient(circle, currentColor 0%, transparent 70%);
		animation: flagWave 3s ease-in-out infinite;
	}
	
	@keyframes flagWave {
		0%, 100% { transform: rotate(-5deg); }
		50% { transform: rotate(5deg); }
	}
	
	.country-info h2 {
		margin: 0;
		font-size: 1.3rem;
		font-weight: 200;
		color: #00ffff;
		letter-spacing: 0.1em;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
	}
	
	.country-stats {
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
	
	.geo-close {
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
	
	.geo-close:hover {
		background: rgba(255, 0, 102, 0.1);
		box-shadow: 0 0 20px rgba(255, 0, 102, 0.5);
		transform: rotate(90deg);
	}
	
	.country-metrics {
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
	
	.country-stream {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}
	
	.intel-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.intel-table th {
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
	
	.intel-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.2s ease;
	}
	
	.intel-row:hover {
		background: rgba(0, 255, 255, 0.02);
	}
	
	.intel-table td {
		padding: 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.asset-id {
		font-family: 'Courier New', monospace;
		color: #00ffff;
		font-size: 0.7rem;
	}
	
	.sync-status, .shield-status {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		font-size: 1rem;
	}
	
	.sync-status.synced {
		color: #00ff00;
		text-shadow: 0 0 10px #00ff00;
	}
	
	.sync-status.unsynced {
		color: #666666;
	}
	
	.shield-status.protected {
		color: #00ffff;
		text-shadow: 0 0 10px #00ffff;
	}
	
	.shield-status.exposed {
		color: #ff0066;
		text-shadow: 0 0 10px #ff0066;
	}
	
	/* Responsive */
	@media (max-width: 1400px) {
		.geo-content {
			flex-direction: column;
		}
		
		.country-data-matrix {
			width: 100%;
			max-height: 300px;
		}
	}
	
	@media (max-width: 768px) {
		.geo-header {
			flex-direction: column;
			align-items: stretch;
		}
		
		.country-metrics {
			grid-template-columns: repeat(2, 1fr);
		}
		
		.country-grid {
			grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
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
	
	/* Pulse Animation */
	@keyframes pulse {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 1; }
	}
</style>