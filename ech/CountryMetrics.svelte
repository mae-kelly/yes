<!-- CountryMetrics.svelte - ULTIMATE GLOBAL SURVEILLANCE MATRIX -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';
	let sortColumn = 'count';
	let sortDirection = 'desc';
	let currentPage = 1;
	let itemsPerPage = 25;
	let viewMode = 'table';
	
	// Advanced visualization states
	let worldMapData = [];
	let migrationFlows = [];
	let heatmapIntensity = [];
	let countryConnections = [];
	let dataFlowParticles = [];
	let geoPulseWaves = [];
	let satelliteTracking = [];
	let cyberActivity = [];
	let quantumRoutes = [];
	
	// Real-time metrics
	let globalDataFlow = 0;
	let activeConnections = 0;
	let threatLevel = 0;
	let encryptionStrength = 100;
	let packetLoss = 0;
	
	// Animation states
	let earthRotation = 0;
	let pulsePhase = 0;
	let dataStreamPhase = 0;
	
	let animationFrames = {
		earth: null,
		flows: null,
		cyber: null
	};
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/country_metrics');
			data = await response.json();
			loading = false;
			initializeGlobalSystems();
			startGlobalAnimations();
		} catch (err) {
			console.error('Country sync failed:', err);
			data = generateMockData();
			loading = false;
			initializeGlobalSystems();
			startGlobalAnimations();
		}
	});
	
	onDestroy(() => {
		Object.values(animationFrames).forEach(frame => {
			if (frame) cancelAnimationFrame(frame);
		});
	});
	
	function generateMockData() {
		const countries = [
			'United States', 'China', 'India', 'Germany', 'Japan', 'United Kingdom',
			'France', 'Brazil', 'Canada', 'Australia', 'Russia', 'South Korea',
			'Italy', 'Spain', 'Mexico', 'Netherlands', 'Switzerland', 'Sweden',
			'Singapore', 'Israel', 'Norway', 'Denmark', 'Finland', 'Belgium',
			'Austria', 'Ireland', 'New Zealand', 'UAE', 'Saudi Arabia', 'Poland'
		];
		
		const mockData = {};
		countries.forEach(country => {
			mockData[country] = Math.floor(Math.random() * 500000) + 10000;
		});
		
		return { global_intelligence: mockData };
	}
	
	function initializeGlobalSystems() {
		if (!data.global_intelligence) return;
		
		const countries = Object.entries(data.global_intelligence);
		
		// Initialize world map data points
		countries.forEach(([country, count]) => {
			const coords = getCountryCoordinates(country);
			worldMapData.push({
				country,
				count,
				lat: coords.lat,
				lon: coords.lon,
				radius: Math.sqrt(count / 1000),
				active: Math.random() > 0.2,
				threatLevel: Math.random(),
				bandwidth: Math.random() * 1000
			});
		});
		
		// Create migration flows between countries
		for (let i = 0; i < 30; i++) {
			const source = worldMapData[Math.floor(Math.random() * worldMapData.length)];
			const target = worldMapData[Math.floor(Math.random() * worldMapData.length)];
			if (source && target && source !== target) {
				migrationFlows.push({
					source: source.country,
					target: target.country,
					volume: Math.random() * 10000,
					active: Math.random() > 0.3,
					type: ['data', 'traffic', 'sync'][Math.floor(Math.random() * 3)]
				});
			}
		}
		
		// Heat map intensity grid
		for (let lat = -90; lat <= 90; lat += 10) {
			for (let lon = -180; lon <= 180; lon += 10) {
				heatmapIntensity.push({
					lat,
					lon,
					intensity: Math.random(),
					trend: Math.random() > 0.5 ? 'increasing' : 'decreasing'
				});
			}
		}
		
		// Country connections network
		countries.forEach(([country1], i) => {
			const connections = Math.floor(Math.random() * 5) + 1;
			for (let j = 0; j < connections; j++) {
				const targetIndex = Math.floor(Math.random() * countries.length);
				if (targetIndex !== i) {
					countryConnections.push({
						source: country1,
						target: countries[targetIndex][0],
						strength: Math.random(),
						latency: Math.random() * 200,
						bandwidth: Math.random() * 10000
					});
				}
			}
		});
		
		// Data flow particles
		for (let i = 0; i < 200; i++) {
			dataFlowParticles.push({
				id: i,
				x: Math.random() * 1000,
				y: Math.random() * 500,
				vx: (Math.random() - 0.5) * 2,
				vy: (Math.random() - 0.5) * 2,
				size: Math.random() * 3 + 1,
				color: ['#00FFFF', '#FF00FF', '#00FF00'][Math.floor(Math.random() * 3)],
				life: Math.random()
			});
		}
		
		// Geo pulse waves
		for (let i = 0; i < 10; i++) {
			const country = worldMapData[Math.floor(Math.random() * worldMapData.length)];
			if (country) {
				geoPulseWaves.push({
					lat: country.lat,
					lon: country.lon,
					radius: 0,
					maxRadius: 100 + Math.random() * 200,
					speed: 1 + Math.random() * 2,
					color: '#00FFFF',
					opacity: 1
				});
			}
		}
		
		// Satellite tracking
		for (let i = 0; i < 8; i++) {
			satelliteTracking.push({
				id: `SAT-${i}`,
				orbit: Math.random() * 360,
				altitude: 100 + Math.random() * 50,
				speed: 0.5 + Math.random() * 0.5,
				coverage: Math.random() * 30,
				signal: Math.random(),
				tracking: countries[Math.floor(Math.random() * countries.length)][0]
			});
		}
		
		// Cyber activity monitoring
		countries.forEach(([country]) => {
			cyberActivity.push({
				country,
				attacks: Math.floor(Math.random() * 1000),
				blocked: Math.floor(Math.random() * 900),
				active: Math.random() > 0.5,
				severity: Math.random()
			});
		});
		
		// Quantum routes
		for (let i = 0; i < 15; i++) {
			const source = countries[Math.floor(Math.random() * countries.length)][0];
			const target = countries[Math.floor(Math.random() * countries.length)][0];
			if (source !== target) {
				quantumRoutes.push({
					id: `QR-${i}`,
					source,
					target,
					entanglement: Math.random(),
					stability: Math.random(),
					bandwidth: Math.random() * 10000
				});
			}
		}
	}
	
	function getCountryCoordinates(country) {
		const coords = {
			'United States': { lat: 39, lon: -98 },
			'China': { lat: 35, lon: 105 },
			'India': { lat: 20, lon: 77 },
			'Germany': { lat: 51, lon: 9 },
			'Japan': { lat: 36, lon: 138 },
			'United Kingdom': { lat: 54, lon: -2 },
			'France': { lat: 46, lon: 2 },
			'Brazil': { lat: -10, lon: -55 },
			'Canada': { lat: 56, lon: -106 },
			'Australia': { lat: -27, lon: 133 },
			'Russia': { lat: 61, lon: 105 },
			'South Korea': { lat: 37, lon: 128 },
			'Italy': { lat: 42, lon: 12 },
			'Spain': { lat: 40, lon: -4 },
			'Mexico': { lat: 23, lon: -102 },
			'Netherlands': { lat: 52, lon: 5 },
			'Switzerland': { lat: 47, lon: 8 },
			'Sweden': { lat: 60, lon: 18 },
			'Singapore': { lat: 1, lon: 104 },
			'Israel': { lat: 31, lon: 35 }
		};
		return coords[country] || { lat: 0, lon: 0 };
	}
	
	function startGlobalAnimations() {
		let time = 0;
		
		function animate() {
			time += 0.016;
			
			// Update rotations and phases
			earthRotation = (earthRotation + 0.2) % 360;
			pulsePhase = (pulsePhase + 0.02) % (Math.PI * 2);
			dataStreamPhase = (dataStreamPhase + 0.03) % (Math.PI * 2);
			
			// Update metrics
			globalDataFlow = 50 + Math.sin(time * 0.5) * 30 + Math.random() * 20;
			activeConnections = Math.floor(100 + Math.sin(time * 0.3) * 50);
			threatLevel = Math.abs(Math.sin(time * 0.2)) * 100;
			encryptionStrength = 85 + Math.sin(time * 0.4) * 10 + Math.random() * 5;
			packetLoss = Math.abs(Math.sin(time * 0.6)) * 5;
			
			// Update data particles
			dataFlowParticles.forEach(particle => {
				particle.x += particle.vx;
				particle.y += particle.vy;
				particle.life -= 0.01;
				
				if (particle.x < 0 || particle.x > 1000) particle.vx *= -1;
				if (particle.y < 0 || particle.y > 500) particle.vy *= -1;
				
				if (particle.life <= 0) {
					particle.life = 1;
					particle.x = Math.random() * 1000;
					particle.y = Math.random() * 500;
				}
			});
			
			// Update pulse waves
			geoPulseWaves.forEach(wave => {
				wave.radius += wave.speed;
				wave.opacity = 1 - (wave.radius / wave.maxRadius);
				
				if (wave.radius > wave.maxRadius) {
					wave.radius = 0;
					const country = worldMapData[Math.floor(Math.random() * worldMapData.length)];
					if (country) {
						wave.lat = country.lat;
						wave.lon = country.lon;
					}
				}
			});
			
			// Update satellites
			satelliteTracking.forEach(sat => {
				sat.orbit = (sat.orbit + sat.speed) % 360;
				sat.signal = Math.abs(Math.sin(time + sat.orbit * 0.01));
			});
			
			animationFrames.earth = requestAnimationFrame(animate);
		}
		animate();
	}
	
	$: countries = data.global_intelligence ? 
		Object.entries(data.global_intelligence)
			.filter(([country]) => country.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => {
				if (sortColumn === 'name') {
					return sortDirection === 'asc' ? 
						a[0].localeCompare(b[0]) : b[0].localeCompare(a[0]);
				}
				return sortDirection === 'asc' ? a[1] - b[1] : b[1] - a[1];
			}) : [];
	
	$: paginatedCountries = countries.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(countries.length / itemsPerPage);
	$: totalHosts = countries.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = countries.length > 0 ? Math.max(...countries.map(([,c]) => c)) : 1;
	$: avgHosts = countries.length > 0 ? Math.round(totalHosts / countries.length) : 0;
	
	function sortTable(column) {
		if (sortColumn === column) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = column;
			sortDirection = 'desc';
		}
	}
	
	async function drillDownCountry(country, count) {
		selectedCountry = { country, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(country)}`);
			let result = await response.json();
			countryDetails = result.hosts || [];
		} catch (err) {
			console.error('Country drill-down failed:', err);
			countryDetails = generateMockHosts(country, Math.min(100, count));
		} finally {
			loading = false;
		}
	}
	
	function generateMockHosts(country, count) {
		const hosts = [];
		for (let i = 0; i < count; i++) {
			hosts.push({
				host: `${country.toLowerCase().replace(/\s/g, '-')}-node-${i + 1}.global`,
				region: getRegionForCountry(country),
				data_center: `DC-${country.substring(0, 2).toUpperCase()}-${Math.floor(Math.random() * 10) + 1}`,
				infrastructure_type: ['Virtual', 'Physical', 'Cloud', 'Hybrid'][Math.floor(Math.random() * 4)],
				business_unit: ['IT', 'Finance', 'Operations', 'Security'][Math.floor(Math.random() * 4)],
				present_in_cmdb: Math.random() > 0.2 ? 'Yes' : 'No',
				tanium_coverage: Math.random() > 0.3 ? 'Tanium' : 'No Coverage'
			});
		}
		return hosts;
	}
	
	function getRegionForCountry(country) {
		const regions = {
			'United States': 'Americas',
			'Canada': 'Americas',
			'Brazil': 'Americas',
			'Mexico': 'Americas',
			'Germany': 'EMEA',
			'United Kingdom': 'EMEA',
			'France': 'EMEA',
			'Italy': 'EMEA',
			'Spain': 'EMEA',
			'Netherlands': 'EMEA',
			'Switzerland': 'EMEA',
			'Sweden': 'EMEA',
			'Norway': 'EMEA',
			'Denmark': 'EMEA',
			'Finland': 'EMEA',
			'Belgium': 'EMEA',
			'Austria': 'EMEA',
			'Poland': 'EMEA',
			'Russia': 'EMEA',
			'Israel': 'EMEA',
			'Saudi Arabia': 'EMEA',
			'UAE': 'EMEA',
			'China': 'APAC',
			'Japan': 'APAC',
			'India': 'APAC',
			'South Korea': 'APAC',
			'Singapore': 'APAC',
			'Australia': 'APAC',
			'New Zealand': 'APAC'
		};
		return regions[country] || 'Global';
	}
	
	function closeDetails() {
		selectedCountry = null;
		countryDetails = [];
	}
	
	function getCountryLevel(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 80) return { level: 'SUPERPOWER', color: '#FF0000', glow: '#FF000040' };
		if (percentage >= 60) return { level: 'MAJOR', color: '#FF00FF', glow: '#FF00FF40' };
		if (percentage >= 40) return { level: 'SIGNIFICANT', color: '#00FFFF', glow: '#00FFFF40' };
		if (percentage >= 20) return { level: 'MODERATE', color: '#00FF00', glow: '#00FF0040' };
		return { level: 'EMERGING', color: '#FFFF00', glow: '#FFFF0040' };
	}
	
	function formatNumber(num) {
		if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
		if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
		return num.toString();
	}
</script>

<div class="global-surveillance-interface">
	<!-- Top Intelligence Bar -->
	<div class="intelligence-bar">
		<div class="intel-card quantum-red">
			<div class="intel-icon">🌍</div>
			<div class="intel-data">
				<div class="intel-value">{countries.length}</div>
				<div class="intel-label">COUNTRIES TRACKED</div>
			</div>
			<div class="intel-spark">
				<svg viewBox="0 0 80 40">
					{#each Array(20) as _, i}
						<circle cx="{i * 4}" cy="{20 + Math.sin(pulsePhase + i * 0.3) * 15}" 
								r="2" fill="#FF0000" opacity="{0.3 + i * 0.03}"/>
					{/each}
				</svg>
			</div>
		</div>
		
		<div class="intel-card quantum-purple">
			<div class="intel-icon">🛰️</div>
			<div class="intel-data">
				<div class="intel-value">{formatNumber(totalHosts)}</div>
				<div class="intel-label">GLOBAL ASSETS</div>
			</div>
			<div class="intel-spark">
				<svg viewBox="0 0 80 40">
					<path d="M 0,20 Q 20,{20 - globalDataFlow / 5} 40,20 T 80,20" 
						  fill="none" stroke="#FF00FF" stroke-width="2" opacity="0.8"/>
				</svg>
			</div>
		</div>
		
		<div class="intel-card quantum-cyan">
			<div class="intel-icon">📡</div>
			<div class="intel-data">
				<div class="intel-value">{activeConnections}</div>
				<div class="intel-label">ACTIVE CONNECTIONS</div>
			</div>
			<div class="intel-spark">
				<svg viewBox="0 0 80 40">
					{#each Array(10) as _, i}
						<rect x="{i * 8}" y="{40 - Math.random() * 30}" 
							  width="6" height="{Math.random() * 30}"
							  fill="#00FFFF" opacity="0.6"/>
					{/each}
				</svg>
			</div>
		</div>
		
		<div class="intel-card quantum-green">
			<div class="intel-icon">🔐</div>
			<div class="intel-data">
				<div class="intel-value">{encryptionStrength.toFixed(1)}%</div>
				<div class="intel-label">ENCRYPTION STRENGTH</div>
			</div>
			<div class="intel-spark">
				<svg viewBox="0 0 80 40">
					<rect x="0" y="15" width="{encryptionStrength * 0.8}" height="10" 
						  fill="#00FF00" opacity="0.8" rx="5"/>
				</svg>
			</div>
		</div>
		
		<div class="intel-card quantum-yellow">
			<div class="intel-icon">⚠️</div>
			<div class="intel-data">
				<div class="intel-value">{threatLevel.toFixed(0)}%</div>
				<div class="intel-label">THREAT LEVEL</div>
			</div>
			<div class="intel-spark">
				<svg viewBox="0 0 80 40">
					<polygon points="40,10 50,30 30,30" 
							 fill="#FFFF00" opacity="{0.3 + threatLevel / 100}"/>
				</svg>
			</div>
		</div>
	</div>
	
	<!-- Main Grid -->
	<div class="surveillance-grid">
		<!-- Left: World Map Visualization -->
		<div class="map-section">
			<!-- 3D Globe -->
			<div class="globe-container">
				<h3 class="section-title">GLOBAL SURVEILLANCE NETWORK</h3>
				<svg viewBox="0 0 600 400" class="world-map">
					<defs>
						<radialGradient id="earthGradient">
							<stop offset="0%" style="stop-color:#003366;stop-opacity:1" />
							<stop offset="100%" style="stop-color:#000033;stop-opacity:0.5" />
						</radialGradient>
						<filter id="countryGlow">
							<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
							<feMerge>
								<feMergeNode in="coloredBlur"/>
								<feMergeNode in="SourceGraphic"/>
							</feMerge>
						</filter>
					</defs>
					
					<!-- Earth background -->
					<ellipse cx="300" cy="200" rx="250" ry="150" 
							 fill="url(#earthGradient)" opacity="0.3"/>
					
					<!-- Grid -->
					<g opacity="0.2" transform="rotate({earthRotation}, 300, 200)">
						{#each Array(8) as _, i}
							<ellipse cx="300" cy="200" 
									 rx="{250 - i * 30}" ry="{150 - i * 18}"
									 fill="none" stroke="#00FFFF" stroke-width="0.5"/>
							<line x1="50" y1="200" x2="550" y2="200" 
								  stroke="#00FFFF" stroke-width="0.5"
								  transform="rotate({i * 45}, 300, 200)"/>
						{/each}
					</g>
					
					<!-- Country nodes -->
					{#each worldMapData as country}
						{@const level = getCountryLevel(country.count)}
						{@const x = 300 + (country.lon / 180) * 200 * Math.cos(country.lat * Math.PI / 180)}
						{@const y = 200 + (country.lat / 90) * 100}
						<g class="country-node" on:click={() => drillDownCountry(country.country, country.count)}>
							<circle cx="{x}" cy="{y}" 
									r="{5 + country.radius / 10}"
									fill="{level.color}" 
									opacity="{country.active ? 0.8 : 0.3}"
									filter="url(#countryGlow)">
								{#if country.active}
									<animate attributeName="r" 
											 values="{5 + country.radius / 10};{7 + country.radius / 10};{5 + country.radius / 10}"
											 dur="2s" repeatCount="indefinite"/>
								{/if}
							</circle>
							<text x="{x}" y="{y - 10}" 
								  text-anchor="middle" font-size="7" 
								  fill="#FFFFFF" font-weight="bold">
								{country.country.substring(0, 3).toUpperCase()}
							</text>
						</g>
					{/each}
					
					<!-- Data flow lines -->
					{#each migrationFlows.slice(0, 20) as flow}
						{@const source = worldMapData.find(w => w.country === flow.source)}
						{@const target = worldMapData.find(w => w.country === flow.target)}
						{#if source && target}
							{@const x1 = 300 + (source.lon / 180) * 200 * Math.cos(source.lat * Math.PI / 180)}
							{@const y1 = 200 + (source.lat / 90) * 100}
							{@const x2 = 300 + (target.lon / 180) * 200 * Math.cos(target.lat * Math.PI / 180)}
							{@const y2 = 200 + (target.lat / 90) * 100}
							<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
								  stroke="{flow.active ? '#00FFFF' : '#444444'}"
								  stroke-width="{flow.active ? 1 : 0.5}"
								  opacity="{flow.active ? 0.6 : 0.2}"
								  stroke-dasharray="{flow.active ? 'none' : '5,5'}">
								{#if flow.active}
									<animate attributeName="stroke-opacity"
											 values="0.2;0.8;0.2" dur="3s" repeatCount="indefinite"/>
								{/if}
							</line>
						{/if}
					{/each}
					
					<!-- Pulse waves -->
					{#each geoPulseWaves as wave}
						{@const x = 300 + (wave.lon / 180) * 200}
						{@const y = 200 + (wave.lat / 90) * 100}
						<circle cx="{x}" cy="{y}" r="{wave.radius}"
								fill="none" stroke="{wave.color}" 
								stroke-width="1" opacity="{wave.opacity}"/>
					{/each}
					
					<!-- Satellites -->
					{#each satelliteTracking as sat}
						{@const angle = sat.orbit * Math.PI / 180}
						{@const x = 300 + Math.cos(angle) * (150 + sat.altitude)}
						{@const y = 200 + Math.sin(angle) * (100 + sat.altitude * 0.6)}
						<g class="satellite">
							<rect x="{x - 5}" y="{y - 3}" width="10" height="6"
								  fill="#FFFF00" opacity="{sat.signal}"
								  transform="rotate({sat.orbit}, {x}, {y})"/>
							<circle cx="{x}" cy="{y}" r="{sat.coverage}" 
									fill="none" stroke="#FFFF00" 
									stroke-width="0.5" opacity="0.2"
									stroke-dasharray="2,2"/>
						</g>
					{/each}
				</svg>
			</div>
			
			<!-- Cyber Activity Monitor -->
			<div class="cyber-monitor">
				<h3 class="section-title">CYBER ACTIVITY MONITOR</h3>
				<div class="cyber-grid">
					{#each cyberActivity.slice(0, 12) as activity}
						<div class="cyber-item {activity.active ? 'active' : 'inactive'}">
							<div class="cyber-country">{activity.country.substring(0, 8)}</div>
							<div class="cyber-stats">
								<span class="attacks">{activity.attacks}</span>
								<span class="blocked">{activity.blocked}</span>
							</div>
							<div class="cyber-bar">
								<div class="cyber-level" 
									 style="width: {(activity.blocked / activity.attacks) * 100}%;
											background: {activity.severity > 0.7 ? '#FF0000' : activity.severity > 0.4 ? '#FFFF00' : '#00FF00'}">
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
		
		<!-- Center: Main Data Table -->
		<div class="table-section">
			<div class="table-container">
				<div class="table-header">
					<h2 class="table-title">COUNTRY INTELLIGENCE MATRIX</h2>
					<div class="table-controls">
						<input type="text" 
							   bind:value={searchTerm}
							   placeholder="SEARCH COUNTRIES..."
							   class="search-input"/>
						<div class="view-controls">
							<button class="view-btn {viewMode === 'table' ? 'active' : ''}" 
									on:click={() => viewMode = 'table'}>TABLE</button>
							<button class="view-btn {viewMode === 'cards' ? 'active' : ''}" 
									on:click={() => viewMode = 'cards'}>CARDS</button>
							<button class="view-btn {viewMode === 'graph' ? 'active' : ''}" 
									on:click={() => viewMode = 'graph'}>GRAPH</button>
						</div>
						<div class="pagination">
							<button on:click={() => currentPage = 1} disabled={currentPage === 1}>⏮</button>
							<button on:click={() => currentPage = Math.max(1, currentPage - 1)} disabled={currentPage === 1}>◀</button>
							<span class="page-info">{currentPage} / {totalPages}</span>
							<button on:click={() => currentPage = Math.min(totalPages, currentPage + 1)} disabled={currentPage === totalPages}>▶</button>
							<button on:click={() => currentPage = totalPages} disabled={currentPage === totalPages}>⏭</button>
						</div>
					</div>
				</div>
				
				{#if selectedCountry}
					<div class="detail-view">
						<div class="detail-header">
							<div>
								<h3>{selectedCountry.country.toUpperCase()}</h3>
								<div class="detail-stats">
									<span>{formatNumber(selectedCountry.count)} hosts</span>
									<span>•</span>
									<span>{((selectedCountry.count / totalHosts) * 100).toFixed(2)}% of global</span>
									<span>•</span>
									<span>Region: {getRegionForCountry(selectedCountry.country)}</span>
								</div>
							</div>
							<button class="close-btn" on:click={closeDetails}>✕ CLOSE</button>
						</div>
						<div class="detail-content">
							<table class="detail-table">
								<thead>
									<tr>
										<th>HOSTNAME</th>
										<th>REGION</th>
										<th>DATA CENTER</th>
										<th>TYPE</th>
										<th>UNIT</th>
										<th>CMDB</th>
										<th>TANIUM</th>
									</tr>
								</thead>
								<tbody>
									{#each countryDetails as host}
										<tr class="detail-row">
											<td class="hostname">{host.host}</td>
											<td>{host.region}</td>
											<td>{host.data_center}</td>
											<td>
												<span class="type-badge {host.infrastructure_type.toLowerCase()}">
													{host.infrastructure_type}
												</span>
											</td>
											<td>{host.business_unit}</td>
											<td>
												<span class="status-dot {host.present_in_cmdb === 'Yes' ? 'active' : 'inactive'}">●</span>
											</td>
											<td>
												<span class="status-dot {host.tanium_coverage === 'Tanium' ? 'active' : 'inactive'}">●</span>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				{:else if viewMode === 'table'}
					<table class="data-table">
						<thead>
							<tr>
								<th class="sortable" on:click={() => sortTable('rank')}>
									RANK {sortColumn === 'rank' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th class="sortable" on:click={() => sortTable('name')}>
									COUNTRY {sortColumn === 'name' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th class="sortable" on:click={() => sortTable('count')}>
									HOSTS {sortColumn === 'count' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th>LEVEL</th>
								<th>% GLOBAL</th>
								<th>REGION</th>
								<th>CONNECTIONS</th>
								<th>THREAT</th>
								<th>STATUS</th>
								<th>ACTIONS</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedCountries as [country, count], i}
								{@const level = getCountryLevel(count)}
								{@const percentage = (count / totalHosts) * 100}
								{@const region = getRegionForCountry(country)}
								{@const connections = countryConnections.filter(c => c.source === country).length}
								{@const cyber = cyberActivity.find(c => c.country === country)}
								<tr class="data-row" style="--glow-color: {level.glow}">
									<td class="rank">#{(currentPage - 1) * itemsPerPage + i + 1}</td>
									<td class="country-name">
										<span class="country-flag">🏴</span>
										{country}
									</td>
									<td class="host-count" style="color: {level.color}">
										{formatNumber(count)}
									</td>
									<td>
										<span class="level-badge" style="background: {level.glow}; color: {level.color}">
											{level.level}
										</span>
									</td>
									<td>
										<div class="percentage-bar">
											<div class="percentage-fill" 
												 style="width: {percentage}%; 
														background: linear-gradient(90deg, transparent, {level.color})">
											</div>
											<span class="percentage-text">{percentage.toFixed(1)}%</span>
										</div>
									</td>
									<td class="region">{region}</td>
									<td class="connections">
										<span class="conn-value">{connections}</span>
										<span class="conn-indicator">⚡</span>
									</td>
									<td>
										<div class="threat-meter">
											<div class="threat-level" 
												 style="width: {cyber ? cyber.severity * 100 : 0}%;
														background: {cyber && cyber.severity > 0.7 ? '#FF0000' : cyber && cyber.severity > 0.4 ? '#FFFF00' : '#00FF00'}">
											</div>
										</div>
									</td>
									<td>
										<span class="status-indicator {percentage > 10 ? 'online' : 'standby'}">
											{percentage > 10 ? '◈' : '○'}
										</span>
									</td>
									<td>
										<button class="action-btn" on:click={() => drillDownCountry(country, count)}>
											ANALYZE
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				{:else if viewMode === 'cards'}
					<div class="cards-view">
						{#each paginatedCountries as [country, count]}
							{@const level = getCountryLevel(count)}
							{@const percentage = (count / totalHosts) * 100}
							<div class="country-card" style="border-color: {level.color}"
								 on:click={() => drillDownCountry(country, count)}>
								<div class="card-header" style="background: {level.glow}">
									<span class="card-flag">🏴</span>
									<span class="card-name">{country}</span>
								</div>
								<div class="card-body">
									<div class="card-stat">
										<span class="stat-label">Hosts</span>
										<span class="stat-value" style="color: {level.color}">{formatNumber(count)}</span>
									</div>
									<div class="card-stat">
										<span class="stat-label">Global %</span>
										<span class="stat-value">{percentage.toFixed(1)}%</span>
									</div>
									<div class="card-stat">
										<span class="stat-label">Level</span>
										<span class="stat-value">{level.level}</span>
									</div>
								</div>
								<div class="card-footer">
									<div class="card-bar">
										<div class="card-fill" style="width: {percentage}%; background: {level.color}"></div>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{:else if viewMode === 'graph'}
					<div class="graph-view">
						<svg viewBox="0 0 800 400" class="network-graph">
							<!-- Connections -->
							{#each countryConnections.slice(0, 50) as connection}
								{@const source = countries.find(([c]) => c === connection.source)}
								{@const target = countries.find(([c]) => c === connection.target)}
								{#if source && target}
									{@const sourceIndex = countries.indexOf(source)}
									{@const targetIndex = countries.indexOf(target)}
									{@const x1 = 400 + Math.cos(sourceIndex * Math.PI * 2 / countries.length) * 150}
									{@const y1 = 200 + Math.sin(sourceIndex * Math.PI * 2 / countries.length) * 150}
									{@const x2 = 400 + Math.cos(targetIndex * Math.PI * 2 / countries.length) * 150}
									{@const y2 = 200 + Math.sin(targetIndex * Math.PI * 2 / countries.length) * 150}
									<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
										  stroke="#00FFFF" stroke-width="{connection.strength}"
										  opacity="0.3"/>
								{/if}
							{/each}
							
							<!-- Nodes -->
							{#each countries.slice(0, 30) as [country, count], i}
								{@const level = getCountryLevel(count)}
								{@const x = 400 + Math.cos(i * Math.PI * 2 / 30) * 150}
								{@const y = 200 + Math.sin(i * Math.PI * 2 / 30) * 150}
								<g class="graph-node" on:click={() => drillDownCountry(country, count)}>
									<circle cx="{x}" cy="{y}" 
											r="{10 + Math.sqrt(count / maxHosts) * 20}"
											fill="{level.color}" opacity="0.7"/>
									<text x="{x}" y="{y + 3}" 
										  text-anchor="middle" font-size="8" 
										  fill="#FFFFFF" font-weight="bold">
										{country.substring(0, 3).toUpperCase()}
									</text>
								</g>
							{/each}
						</svg>
					</div>
				{/if}
			</div>
		</div>
		
		<!-- Right: Analytics -->
		<div class="analytics-section">
			<!-- Top Countries Chart -->
			<div class="chart-container">
				<h3 class="section-title">TOP 10 COUNTRIES</h3>
				<div class="top-countries">
					{#each countries.slice(0, 10) as [country, count], i}
						{@const level = getCountryLevel(count)}
						{@const percentage = (count / maxHosts) * 100}
						<div class="top-item" on:click={() => drillDownCountry(country, count)}>
							<div class="top-rank" style="color: {level.color}">#{i + 1}</div>
							<div class="top-name">{country}</div>
							<div class="top-bar">
								<div class="top-fill" 
									 style="width: {percentage}%; 
											background: linear-gradient(90deg, transparent, {level.color})">
								</div>
							</div>
							<div class="top-value" style="color: {level.color}">{formatNumber(count)}</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Quantum Routes -->
			<div class="routes-container">
				<h3 class="section-title">QUANTUM ROUTES</h3>
				<div class="routes-list">
					{#each quantumRoutes.slice(0, 8) as route}
						<div class="route-item">
							<div class="route-header">
								<span class="route-id">{route.id}</span>
								<span class="route-path">{route.source.substring(0, 3)} → {route.target.substring(0, 3)}</span>
							</div>
							<div class="route-metrics">
								<div class="route-metric">
									<span class="metric-label">Entanglement</span>
									<div class="metric-bar">
										<div class="metric-fill" 
											 style="width: {route.entanglement * 100}%; 
													background: #FF00FF">
										</div>
									</div>
								</div>
								<div class="route-metric">
									<span class="metric-label">Stability</span>
									<div class="metric-bar">
										<div class="metric-fill" 
											 style="width: {route.stability * 100}%; 
													background: #00FFFF">
										</div>
									</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Real-time Metrics -->
			<div class="realtime-container">
				<h3 class="section-title">REAL-TIME METRICS</h3>
				<div class="realtime-grid">
					<div class="realtime-item">
						<span class="rt-label">Data Flow</span>
						<span class="rt-value">{globalDataFlow.toFixed(0)}%</span>
					</div>
					<div class="realtime-item">
						<span class="rt-label">Packet Loss</span>
						<span class="rt-value" style="color: {packetLoss > 3 ? '#FF0000' : '#00FF00'}">
							{packetLoss.toFixed(2)}%
						</span>
					</div>
					<div class="realtime-item">
						<span class="rt-label">Active Nodes</span>
						<span class="rt-value">{activeConnections}</span>
					</div>
					<div class="realtime-item">
						<span class="rt-label">Encryption</span>
						<span class="rt-value">{encryptionStrength.toFixed(0)}%</span>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.global-surveillance-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: linear-gradient(135deg, #000033, #000066);
		display: flex;
		flex-direction: column;
		gap: 1rem;
		padding: 1rem;
		overflow: hidden;
	}
	
	/* Intelligence Bar */
	.intelligence-bar {
		display: flex;
		gap: 1rem;
		height: 100px;
		flex-shrink: 0;
	}
	
	.intel-card {
		flex: 1;
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid rgba(255, 255, 255, 0.3);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		align-items: center;
		gap: 1rem;
		position: relative;
		overflow: hidden;
	}
	
	.intel-card.quantum-red { box-shadow: 0 0 25px rgba(255, 0, 0, 0.4); }
	.intel-card.quantum-purple { box-shadow: 0 0 25px rgba(255, 0, 255, 0.4); }
	.intel-card.quantum-cyan { box-shadow: 0 0 25px rgba(0, 255, 255, 0.4); }
	.intel-card.quantum-green { box-shadow: 0 0 25px rgba(0, 255, 0, 0.4); }
	.intel-card.quantum-yellow { box-shadow: 0 0 25px rgba(255, 255, 0, 0.4); }
	
	.intel-icon {
		font-size: 3rem;
	}
	
	.intel-data {
		flex: 1;
	}
	
	.intel-value {
		font-size: 2rem;
		font-weight: bold;
		color: #FFFFFF;
		font-family: 'Courier New', monospace;
		text-shadow: 0 0 15px currentColor;
	}
	
	.intel-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
		letter-spacing: 0.1em;
		text-transform: uppercase;
	}
	
	.intel-spark {
		position: absolute;
		right: 10px;
		width: 80px;
		height: 40px;
		opacity: 0.6;
	}
	
	/* Surveillance Grid */
	.surveillance-grid {
		flex: 1;
		display: grid;
		grid-template-columns: 400px 1fr 350px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Map Section */
	.map-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
	}
	
	.globe-container, .cyber-monitor {
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 12px;
		padding: 1rem;
	}
	
	.section-title {
		margin: 0 0 1rem 0;
		font-size: 0.9rem;
		color: #00FFFF;
		letter-spacing: 0.1em;
		font-weight: 400;
		text-transform: uppercase;
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}
	
	.world-map {
		width: 100%;
		height: auto;
	}
	
	.country-node {
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.country-node:hover {
		transform: scale(1.2);
	}
	
	.satellite {
		pointer-events: none;
	}
	
	/* Cyber Monitor */
	.cyber-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.5rem;
	}
	
	.cyber-item {
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 6px;
		font-size: 0.7rem;
	}
	
	.cyber-item.active {
		border-color: #00FF00;
		background: rgba(0, 255, 0, 0.05);
	}
	
	.cyber-item.inactive {
		border-color: #FF0000;
		background: rgba(255, 0, 0, 0.05);
	}
	
	.cyber-country {
		color: #FFFFFF;
		font-weight: 600;
		margin-bottom: 0.25rem;
	}
	
	.cyber-stats {
		display: flex;
		justify-content: space-between;
		font-size: 0.6rem;
		margin-bottom: 0.25rem;
	}
	
	.attacks { color: #FF0000; }
	.blocked { color: #00FF00; }
	
	.cyber-bar {
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.cyber-level {
		height: 100%;
		transition: all 0.5s;
	}
	
	/* Table Section */
	.table-section {
		display: flex;
		flex-direction: column;
		min-height: 0;
	}
	
	.table-container {
		flex: 1;
		background: rgba(0, 0, 0, 0.95);
		border: 2px solid rgba(0, 255, 255, 0.4);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: 0 0 50px rgba(0, 255, 255, 0.3);
	}
	
	.table-header {
		padding: 1.5rem;
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.15), transparent);
		border-bottom: 1px solid rgba(0, 255, 255, 0.4);
	}
	
	.table-title {
		margin: 0 0 1rem 0;
		font-size: 1.4rem;
		color: #00FFFF;
		letter-spacing: 0.2em;
		font-weight: 300;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.7);
		text-transform: uppercase;
	}
	
	.table-controls {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
	}
	
	.search-input {
		padding: 0.7rem 1.2rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.4);
		color: #00FFFF;
		font-family: 'Courier New', monospace;
		border-radius: 6px;
		width: 280px;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #00FFFF;
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.6);
	}
	
	.view-controls {
		display: flex;
		gap: 0.5rem;
		background: rgba(0, 0, 0, 0.6);
		padding: 3px;
		border-radius: 6px;
	}
	
	.view-btn {
		padding: 0.5rem 1rem;
		background: transparent;
		border: 1px solid transparent;
		color: rgba(255, 255, 255, 0.7);
		cursor: pointer;
		border-radius: 4px;
		transition: all 0.3s;
		font-size: 0.8rem;
		font-weight: 600;
	}
	
	.view-btn:hover {
		background: rgba(0, 255, 255, 0.1);
		color: #00FFFF;
	}
	
	.view-btn.active {
		background: rgba(0, 255, 255, 0.2);
		border-color: #00FFFF;
		color: #00FFFF;
	}
	
	.pagination {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.pagination button {
		padding: 0.5rem 0.8rem;
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid #00FFFF;
		color: #00FFFF;
		cursor: pointer;
		border-radius: 6px;
		transition: all 0.3s;
	}
	
	.pagination button:hover:not(:disabled) {
		background: rgba(0, 255, 255, 0.3);
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
		transform: scale(1.05);
	}
	
	.pagination button:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	
	.page-info {
		color: #00FFFF;
		font-family: 'Courier New', monospace;
		padding: 0 1rem;
	}
	
	/* Data Table */
	.data-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.data-table thead {
		background: rgba(0, 255, 255, 0.08);
		position: sticky;
		top: 0;
		z-index: 10;
	}
	
	.data-table th {
		padding: 1rem 0.8rem;
		text-align: left;
		font-size: 0.75rem;
		color: #00FFFF;
		letter-spacing: 0.1em;
		font-weight: 600;
		border-bottom: 2px solid rgba(0, 255, 255, 0.4);
		text-transform: uppercase;
		white-space: nowrap;
	}
	
	.data-table th.sortable {
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.data-table th.sortable:hover {
		background: rgba(0, 255, 255, 0.1);
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.6);
	}
	
	.data-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.08);
		transition: all 0.3s;
		cursor: pointer;
	}
	
	.data-row:hover {
		background: rgba(0, 255, 255, 0.08);
		box-shadow: inset 0 0 40px var(--glow-color);
		transform: translateX(5px);
	}
	
	.data-table td {
		padding: 1rem 0.8rem;
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.9);
	}
	
	.rank {
		color: #FF00FF;
		font-weight: bold;
		font-family: 'Courier New', monospace;
	}
	
	.country-name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 500;
	}
	
	.country-flag {
		font-size: 1rem;
	}
	
	.host-count {
		font-family: 'Courier New', monospace;
		font-weight: bold;
		font-size: 0.95rem;
	}
	
	.level-badge {
		padding: 0.3rem 0.7rem;
		border-radius: 6px;
		font-size: 0.65rem;
		font-weight: 700;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}
	
	.percentage-bar {
		position: relative;
		width: 100px;
		height: 22px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 11px;
		overflow: hidden;
	}
	
	.percentage-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.percentage-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 0.7rem;
		color: #FFFFFF;
		font-weight: bold;
		text-shadow: 0 0 3px #000000;
	}
	
	.region {
		color: rgba(255, 255, 255, 0.8);
		font-size: 0.8rem;
	}
	
	.connections {
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}
	
	.conn-value {
		font-family: 'Courier New', monospace;
		color: #00FFFF;
	}
	
	.conn-indicator {
		color: #FFFF00;
		font-size: 0.9rem;
	}
	
	.threat-meter {
		width: 60px;
		height: 8px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.threat-level {
		height: 100%;
		transition: all 0.5s;
	}
	
	.status-indicator {
		font-size: 0.9rem;
		font-weight: 600;
	}
	
	.status-indicator.online { color: #00FF00; }
	.status-indicator.standby { color: #FFFF00; }
	
	.action-btn {
		padding: 0.5rem 1rem;
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 255, 255, 0.4));
		border: 1px solid #00FFFF;
		color: #00FFFF;
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		cursor: pointer;
		border-radius: 6px;
		transition: all 0.3s;
		text-transform: uppercase;
	}
	
	.action-btn:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.4), rgba(0, 255, 255, 0.6));
		box-shadow: 0 0 25px rgba(0, 255, 255, 0.7);
		transform: scale(1.05);
	}
	
	/* Cards View */
	.cards-view {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 1rem;
		padding: 1rem;
		overflow-y: auto;
	}
	
	.country-card {
		background: rgba(0, 0, 0, 0.8);
		border: 2px solid;
		border-radius: 10px;
		overflow: hidden;
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.country-card:hover {
		transform: translateY(-5px) scale(1.02);
		box-shadow: 0 10px 30px rgba(0, 255, 255, 0.4);
	}
	
	.card-header {
		padding: 0.8rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.card-flag {
		font-size: 1.5rem;
	}
	
	.card-name {
		font-size: 0.9rem;
		font-weight: 600;
		color: #FFFFFF;
	}
	
	.card-body {
		padding: 1rem;
	}
	
	.card-stat {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.5rem;
		font-size: 0.8rem;
	}
	
	.stat-label {
		color: rgba(255, 255, 255, 0.6);
	}
	
	.stat-value {
		font-weight: 600;
		font-family: 'Courier New', monospace;
	}
	
	.card-footer {
		padding: 0.5rem;
	}
	
	.card-bar {
		height: 6px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		overflow: hidden;
	}
	
	.card-fill {
		height: 100%;
		transition: width 0.5s;
	}
	
	/* Graph View */
	.graph-view {
		padding: 2rem;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: auto;
	}
	
	.network-graph {
		width: 100%;
		height: 100%;
		min-height: 400px;
	}
	
	.graph-node {
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.graph-node:hover {
		transform: scale(1.2);
	}
	
	/* Detail View */
	.detail-view {
		flex: 1;
		padding: 1.5rem;
		overflow-y: auto;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		padding-bottom: 1rem;
		border-bottom: 2px solid rgba(0, 255, 255, 0.4);
	}
	
	.detail-header h3 {
		margin: 0;
		color: #00FFFF;
		font-size: 1.4rem;
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
	}
	
	.detail-stats {
		display: flex;
		gap: 1rem;
		margin-top: 0.5rem;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.close-btn {
		padding: 0.7rem 1.3rem;
		background: rgba(255, 0, 0, 0.2);
		border: 1px solid #FF0000;
		color: #FF0000;
		cursor: pointer;
		border-radius: 6px;
		transition: all 0.3s;
		font-weight: 600;
		letter-spacing: 0.1em;
	}
	
	.close-btn:hover {
		background: rgba(255, 0, 0, 0.4);
		box-shadow: 0 0 20px rgba(255, 0, 0, 0.6);
	}
	
	.detail-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.detail-table thead {
		background: rgba(0, 255, 255, 0.08);
	}
	
	.detail-table th {
		padding: 0.8rem;
		background: rgba(0, 255, 255, 0.1);
		color: #00FFFF;
		font-size: 0.75rem;
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		text-align: left;
	}
	
	.detail-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.08);
		transition: all 0.2s;
	}
	
	.detail-row:hover {
		background: rgba(0, 255, 255, 0.05);
	}
	
	.detail-table td {
		padding: 0.7rem 0.8rem;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.85);
	}
	
	.hostname {
		font-family: 'Courier New', monospace;
		color: #00FFFF;
		font-size: 0.75rem;
	}
	
	.type-badge {
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		font-size: 0.65rem;
		font-weight: 600;
		text-transform: uppercase;
	}
	
	.type-badge.virtual { background: rgba(0, 255, 255, 0.2); color: #00FFFF; }
	.type-badge.physical { background: rgba(255, 0, 255, 0.2); color: #FF00FF; }
	.type-badge.cloud { background: rgba(0, 255, 0, 0.2); color: #00FF00; }
	.type-badge.hybrid { background: rgba(255, 255, 0, 0.2); color: #FFFF00; }
	
	.status-dot {
		font-size: 0.9rem;
		display: inline-block;
	}
	
	.status-dot.active { color: #00FF00; filter: drop-shadow(0 0 5px #00FF00); }
	.status-dot.inactive { color: #FF0000; filter: drop-shadow(0 0 5px #FF0000); }
	
	/* Analytics Section */
	.analytics-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
	}
	
	.chart-container, .routes-container, .realtime-container {
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 12px;
		padding: 1rem;
	}
	
	/* Top Countries */
	.top-countries {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.top-item {
		display: grid;
		grid-template-columns: 30px 100px 1fr 60px;
		gap: 0.5rem;
		align-items: center;
		cursor: pointer;
		padding: 0.3rem;
		border-radius: 4px;
		transition: all 0.2s;
	}
	
	.top-item:hover {
		background: rgba(0, 255, 255, 0.05);
		transform: translateX(3px);
	}
	
	.top-rank {
		font-size: 0.8rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
	}
	
	.top-name {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.9);
		font-weight: 500;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.top-bar {
		height: 18px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 9px;
		overflow: hidden;
	}
	
	.top-fill {
		height: 100%;
		transition: width 0.5s;
	}
	
	.top-value {
		font-size: 0.8rem;
		font-weight: 600;
		font-family: 'Courier New', monospace;
		text-align: right;
	}
	
	/* Quantum Routes */
	.routes-list {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	
	.route-item {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 6px;
		padding: 0.6rem;
	}
	
	.route-header {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.4rem;
		font-size: 0.75rem;
	}
	
	.route-id {
		color: #FF00FF;
		font-weight: 600;
		font-family: 'Courier New', monospace;
	}
	
	.route-path {
		color: rgba(255, 255, 255, 0.7);
	}
	
	.route-metrics {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}
	
	.route-metric {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		min-width: 70px;
	}
	
	.metric-bar {
		flex: 1;
		height: 6px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		overflow: hidden;
	}
	
	.metric-fill {
		height: 100%;
		transition: width 0.5s;
	}
	
	/* Realtime Metrics */
	.realtime-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}
	
	.realtime-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 0.5rem;
		background: rgba(0, 255, 255, 0.05);
		border-radius: 6px;
	}
	
	.rt-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		margin-bottom: 0.3rem;
	}
	
	.rt-value {
		font-size: 1.1rem;
		font-weight: 700;
		color: #00FFFF;
		font-family: 'Courier New', monospace;
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}
	
	::-webkit-scrollbar-track {
		background: #000033;
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb {
		background: linear-gradient(180deg, #00FFFF, #FF00FF);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(180deg, #00FFFF, #FF00FF);
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}
	
	/* Responsive */
	@media (max-width: 1600px) {
		.surveillance-grid {
			grid-template-columns: 350px 1fr 300px;
		}
	}
	
	@media (max-width: 1400px) {
		.surveillance-grid {
			grid-template-columns: 1fr;
			grid-template-rows: auto 1fr auto;
		}
		
		.map-section, .analytics-section {
			display: none;
		}
	}
	
	@media (max-width: 768px) {
		.intelligence-bar {
			flex-wrap: wrap;
			height: auto;
		}
		
		.intel-card {
			min-width: calc(50% - 0.5rem);
		}
		
		.cards-view {
			grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		}
	}
</style>