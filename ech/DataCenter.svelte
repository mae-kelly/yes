<!-- DataCenter.svelte - Quantum Reactor Core Interface -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedFacility = null;
	let facilityDetails = [];
	let searchTerm = '';
	
	// Reactor core states
	let reactorCores = [];
	let plasmaField = [];
	let magneticField = [];
	let coolingSystem = [];
	let powerGrid = [];
	let coreTemperature = 0;
	let plasmaContainment = 100;
	let magneticFlux = 0;
	let energyOutput = 0;
	let criticalityLevel = 0;
	let facilityProfiles = new Map();
	
	// Quantum reactor visualization
	let reactorRings = [];
	let energyBeams = [];
	let coolingNodes = [];
	let dataFlowStreams = [];
	let containmentField = [];
	
	// Animation controllers
	let animationFrames = {
		reactor: null,
		plasma: null,
		magnetic: null
	};
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/data_center_metrics');
			data = await response.json();
			loading = false;
			initializeReactorSystem();
			startReactorSimulation();
		} catch (err) {
			console.error('Reactor core sync failed:', err);
			loading = false;
		}
	});
	
	onDestroy(() => {
		Object.values(animationFrames).forEach(frame => {
			if (frame) cancelAnimationFrame(frame);
		});
	});
	
	function initializeReactorSystem() {
		if (!data.facility_intelligence) return;
		
		let facilities = Object.entries(data.facility_intelligence)
			.sort((a, b) => b[1] - a[1])
			.slice(0, 100);
		
		// Create reactor cores for each facility
		facilities.forEach(([facility, count], i) => {
			let angleStep = (Math.PI * 2) / Math.min(facilities.length, 20);
			let radius = 150 + (i % 3) * 50;
			let angle = i * angleStep;
			
			let core = {
				id: facility,
				count: count,
				x: Math.cos(angle) * radius,
				y: Math.sin(angle) * radius,
				z: Math.sin(i * 0.5) * 50,
				// Reactor properties
				temperature: 2000 + Math.random() * 3000, // Kelvin
				pressure: 100 + Math.random() * 900, // Bar
				plasma: Math.random(),
				magnetic: Math.random(),
				cooling: Math.random(),
				output: Math.log10(count + 1) * 100, // MW
				efficiency: 70 + Math.random() * 30,
				containment: 90 + Math.random() * 10,
				status: 'OPERATIONAL',
				fuelType: ['DEUTERIUM', 'TRITIUM', 'HELIUM-3', 'QUANTUM'][Math.floor(Math.random() * 4)],
				coolingType: ['LIQUID_HELIUM', 'PLASMA_EXHAUST', 'QUANTUM_DISSIPATION'][Math.floor(Math.random() * 3)],
				connections: []
			};
			
			reactorCores.push(core);
			facilityProfiles.set(facility, generateFacilityProfile(facility, count));
		});
		
		// Initialize reactor rings (tokamak visualization)
		for (let i = 0; i < 8; i++) {
			reactorRings.push({
				radius: 50 + i * 20,
				rotation: i * 45,
				speed: 1 + Math.random() * 2,
				energy: Math.random(),
				particles: generateRingParticles(20)
			});
		}
		
		// Initialize plasma field
		for (let i = 0; i < 500; i++) {
			plasmaField.push({
				x: (Math.random() - 0.5) * 400,
				y: (Math.random() - 0.5) * 400,
				z: (Math.random() - 0.5) * 200,
				vx: (Math.random() - 0.5) * 2,
				vy: (Math.random() - 0.5) * 2,
				vz: (Math.random() - 0.5) * 2,
				temperature: 1000 + Math.random() * 4000,
				charge: Math.random() > 0.5 ? 1 : -1,
				mass: Math.random(),
				life: Math.random()
			});
		}
		
		// Initialize magnetic field lines
		for (let i = 0; i < 20; i++) {
			magneticField.push({
				startAngle: Math.random() * Math.PI * 2,
				endAngle: Math.random() * Math.PI * 2,
				radius: 100 + Math.random() * 100,
				strength: Math.random(),
				polarity: Math.random() > 0.5 ? 1 : -1
			});
		}
		
		// Initialize cooling system
		for (let i = 0; i < 30; i++) {
			coolingSystem.push({
				x: (Math.random() - 0.5) * 300,
				y: (Math.random() - 0.5) * 300,
				temperature: -273 + Math.random() * 100, // Near absolute zero
				flow: Math.random(),
				pressure: Math.random() * 100,
				active: Math.random() > 0.2
			});
		}
		
		// Create energy beams between cores
		createEnergyNetwork();
		
		// Initialize containment field
		for (let r = 0; r < 5; r++) {
			containmentField.push({
				radius: 200 + r * 30,
				strength: 1 - r * 0.15,
				fluctuation: Math.random() * 0.2
			});
		}
	}
	
	function generateFacilityProfile(facility, count) {
		return {
			reactorSignature: generateReactorSignature(count),
			powerMetrics: {
				capacity: Math.log10(count + 1) * 1000, // MW
				efficiency: 70 + Math.random() * 30,
				uptime: 95 + Math.random() * 5,
				peakOutput: Math.log10(count + 1) * 1200,
				baseline: Math.log10(count + 1) * 800
			},
			thermalProfile: {
				coreTemp: 2000 + Math.random() * 3000,
				coolantTemp: -200 + Math.random() * 50,
				heatDissipation: Math.random() * 1000,
				thermalEfficiency: 30 + Math.random() * 40
			},
			quantumMetrics: {
				entanglement: Math.random(),
				coherence: Math.random(),
				superposition: Math.random() > 0.7,
				quantumEfficiency: Math.random() * 100
			},
			safetyMetrics: {
				containment: 90 + Math.random() * 10,
				radiation: Math.random() * 100,
				pressure: 100 + Math.random() * 900,
				structural: 80 + Math.random() * 20
			}
		};
	}
	
	function generateReactorSignature(seed) {
		let sig = 'RX-';
		let pattern = seed * 31337;
		for (let i = 0; i < 3; i++) {
			pattern = (pattern * 1103515245 + 12345) & 0x7fffffff;
			sig += (pattern % 1000).toString().padStart(3, '0');
			if (i < 2) sig += '-';
		}
		sig += '-' + ['ALPHA', 'BETA', 'GAMMA', 'DELTA', 'OMEGA'][seed % 5];
		return sig;
	}
	
	function generateRingParticles(count) {
		let particles = [];
		for (let i = 0; i < count; i++) {
			particles.push({
				angle: (i / count) * Math.PI * 2,
				speed: 0.5 + Math.random() * 1.5,
				size: 1 + Math.random() * 2,
				energy: Math.random(),
				trail: []
			});
		}
		return particles;
	}
	
	function createEnergyNetwork() {
		reactorCores.forEach((core, i) => {
			let connectionCount = Math.min(3, 1 + Math.floor(Math.random() * 3));
			for (let j = 0; j < connectionCount; j++) {
				let targetIdx = Math.floor(Math.random() * reactorCores.length);
				if (targetIdx !== i) {
					energyBeams.push({
						source: i,
						target: targetIdx,
						energy: Math.random(),
						wavelength: 380 + Math.random() * 400, // nm
						intensity: Math.random(),
						active: Math.random() > 0.3,
						particles: []
					});
				}
			}
		});
		
		// Initialize beam particles
		energyBeams.forEach(beam => {
			for (let i = 0; i < 10; i++) {
				beam.particles.push({
					position: Math.random(),
					speed: 0.5 + Math.random() * 0.5
				});
			}
		});
	}
	
	function startReactorSimulation() {
		let time = 0;
		
		function updateReactorCore() {
			time += 0.016;
			
			// Update core temperature (oscillating)
			coreTemperature = 3000 + Math.sin(time * 0.5) * 1000 + Math.sin(time * 1.7) * 500;
			
			// Update plasma containment
			plasmaContainment = 85 + Math.sin(time * 0.3) * 10 + Math.random() * 5;
			
			// Update magnetic flux
			magneticFlux = Math.sin(time * 0.7) * 100;
			
			// Update energy output
			energyOutput = 500 + Math.sin(time * 0.4) * 200 + Math.sin(time * 1.2) * 100;
			
			// Update criticality (danger level)
			criticalityLevel = coreTemperature > 3800 ? 
				(coreTemperature - 3800) / 200 : 0;
			
			// Update reactor cores
			reactorCores.forEach((core, i) => {
				core.temperature = 2000 + Math.sin(time + i * 0.1) * 3000;
				core.plasma = 0.5 + Math.sin(time * 2 + i * 0.2) * 0.5;
				core.magnetic = 0.5 + Math.cos(time * 1.5 + i * 0.15) * 0.5;
				core.cooling = Math.max(0.2, Math.min(1, core.cooling + (Math.random() - 0.5) * 0.1));
				
				// Update status based on metrics
				if (core.temperature > 4500 && core.cooling < 0.3) {
					core.status = 'CRITICAL';
				} else if (core.temperature > 3500 || core.cooling < 0.5) {
					core.status = 'WARNING';
				} else {
					core.status = 'OPERATIONAL';
				}
			});
			
			// Update reactor rings
			reactorRings.forEach(ring => {
				ring.rotation += ring.speed;
				ring.energy = 0.5 + Math.sin(time * 3 + ring.radius * 0.01) * 0.5;
				ring.particles.forEach(particle => {
					particle.angle += particle.speed * 0.01;
					particle.energy = 0.5 + Math.sin(time * 2 + particle.angle) * 0.5;
					
					// Update particle trail
					particle.trail.push({
						x: Math.cos(particle.angle) * ring.radius,
						y: Math.sin(particle.angle) * ring.radius
					});
					if (particle.trail.length > 10) {
						particle.trail.shift();
					}
				});
			});
			
			// Update plasma field
			plasmaField.forEach(particle => {
				// Magnetic confinement effect
				let r = Math.sqrt(particle.x * particle.x + particle.y * particle.y);
				if (r > 180) {
					let angle = Math.atan2(particle.y, particle.x);
					particle.vx -= Math.cos(angle) * 0.5;
					particle.vy -= Math.sin(angle) * 0.5;
				}
				
				particle.x += particle.vx;
				particle.y += particle.vy;
				particle.z += particle.vz;
				
				// Wrap around
				if (Math.abs(particle.z) > 100) particle.vz *= -1;
				
				particle.temperature = 1000 + Math.sin(time * 4 + particle.life) * 4000;
				particle.life = (particle.life + 0.01) % 1;
			});
			
			// Update magnetic field
			magneticField.forEach(field => {
				field.strength = 0.5 + Math.sin(time * 2 + field.startAngle) * 0.5;
			});
			
			// Update cooling system
			coolingSystem.forEach(node => {
				node.flow = 0.5 + Math.sin(time * 3 + node.x * 0.01) * 0.5;
				node.temperature = -273 + Math.sin(time * 2) * 50 + Math.random() * 50;
				node.active = Math.random() > 0.1;
			});
			
			// Update energy beams
			energyBeams.forEach(beam => {
				beam.intensity = 0.5 + Math.sin(time * 4) * 0.5;
				beam.particles.forEach(particle => {
					particle.position = (particle.position + particle.speed * 0.01) % 1;
				});
			});
			
			// Update containment field
			containmentField.forEach((field, i) => {
				field.fluctuation = Math.sin(time * 2 + i * 0.5) * 0.2;
			});
			
			animationFrames.reactor = requestAnimationFrame(updateReactorCore);
		}
		
		updateReactorCore();
	}
	
	$: filteredFacilities = data.facility_intelligence ? 
		Object.entries(data.facility_intelligence)
			.filter(([facility]) => facility.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredFacilities.length > 0 ? Math.max(...filteredFacilities.map(([,c]) => c)) : 1;
	$: minCount = filteredFacilities.length > 0 ? Math.min(...filteredFacilities.map(([,c]) => c)) : 0;
	
	function getFacilityClass(count) {
		let normalized = (count - minCount) / (maxCount - minCount || 1);
		let percentile = normalized * 100;
		
		if (percentile >= 85) {
			return {
				level: 'FUSION_NEXUS',
				color: '#FF6BCB', // Neon magenta
				glow: '#FF6BCB40',
				symbol: '⬢',
				description: 'Quantum Fusion Core'
			};
		} else if (percentile >= 65) {
			return {
				level: 'PLASMA_CORE',
				color: '#79E7FF', // Neon sky blue
				glow: '#79E7FF40',
				symbol: '◈',
				description: 'Plasma Reactor'
			};
		} else if (percentile >= 45) {
			return {
				level: 'ENERGY_NODE',
				color: '#A78BFA', // Neon violet
				glow: '#A78BFA40',
				symbol: '◆',
				description: 'Energy Station'
			};
		} else if (percentile >= 25) {
			return {
				level: 'COOLING_UNIT',
				color: '#34D399', // Neon emerald
				glow: '#34D39940',
				symbol: '▲',
				description: 'Cooling Array'
			};
		} else {
			return {
				level: 'BACKUP_GEN',
				color: '#FBBF24', // Neon amber
				glow: '#FBBF2440',
				symbol: '●',
				description: 'Backup Generator'
			};
		}
	}
	
	async function drillDownFacility(facility, count) {
		selectedFacility = { facility, count };
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
	
	function getTemperatureColor(temp) {
		// Temperature gradient from cold to hot
		if (temp < 1000) return '#79E7FF'; // Cold - cyan
		if (temp < 2000) return '#34D399'; // Cool - emerald
		if (temp < 3000) return '#FBBF24'; // Warm - amber
		if (temp < 4000) return '#FF6BCB'; // Hot - magenta
		return '#FF1744'; // Critical - red
	}
</script>

<div class="quantum-reactor-interface">
	<!-- Plasma Field Background -->
	<div class="plasma-field-container">
		<!-- Plasma particles -->
		<div class="plasma-field">
			{#each plasmaField.slice(0, 100) as particle}
				<div class="plasma-particle"
					 style="left: {50 + particle.x / 4}%;
							top: {50 + particle.y / 4}%;
							background: {particle.charge > 0 ? '#FF6BCB' : '#79E7FF'};
							opacity: {particle.life};
							box-shadow: 0 0 {particle.temperature / 500}px {particle.charge > 0 ? '#FF6BCB' : '#79E7FF'}">
				</div>
			{/each}
		</div>
		
		<!-- Magnetic field lines -->
		<svg class="magnetic-field-svg" viewBox="-250 -250 500 500">
			<defs>
				<radialGradient id="fieldGradient">
					<stop offset="0%" style="stop-color:#A78BFA;stop-opacity:0.8" />
					<stop offset="100%" style="stop-color:#A78BFA;stop-opacity:0" />
				</radialGradient>
			</defs>
			{#each magneticField as field}
				<path d="M {Math.cos(field.startAngle) * field.radius},{Math.sin(field.startAngle) * field.radius}
						 Q 0,{field.polarity * 50}
						   {Math.cos(field.endAngle) * field.radius},{Math.sin(field.endAngle) * field.radius}"
					  stroke="rgba(167, 139, 250, {field.strength * 0.3})"
					  stroke-width="1"
					  fill="none"
					  stroke-dasharray="5,5">
					<animate attributeName="stroke-dashoffset" 
							 values="0;10" 
							 dur="{2 / field.strength}s" 
							 repeatCount="indefinite"/>
				</path>
			{/each}
		</svg>
		
		<!-- Containment field rings -->
		{#each containmentField as field}
			<div class="containment-ring"
				 style="width: {field.radius * 2}px;
						height: {field.radius * 2}px;
						border: 2px solid rgba(121, 231, 255, {field.strength * 0.3});
						box-shadow: 0 0 {20 * field.strength}px rgba(121, 231, 255, {field.strength * 0.2});
						transform: scale({1 + field.fluctuation})">
			</div>
		{/each}
	</div>
	
	<div class="reactor-control-interface">
		<!-- Reactor Header -->
		<header class="reactor-header">
			<div class="header-reactor">
				<div class="reactor-core-visual">
					<!-- Tokamak visualization -->
					<div class="tokamak-container">
						{#each reactorRings as ring}
							<div class="reactor-ring"
								 style="width: {ring.radius * 2}px;
										height: {ring.radius * 2}px;
										transform: rotate({ring.rotation}deg);
										border-color: rgba(255, 107, 203, {ring.energy})">
								{#each ring.particles as particle}
									<div class="ring-particle"
										 style="transform: rotate({particle.angle * 57.3}deg) translateX({ring.radius}px);
												background: rgba(121, 231, 255, {particle.energy});
												width: {particle.size}px;
												height: {particle.size}px">
									</div>
								{/each}
							</div>
						{/each}
						<div class="reactor-core-center">
							<div class="core-pulse" style="background: {getTemperatureColor(coreTemperature)}"></div>
							<span class="core-symbol">⬢</span>
						</div>
					</div>
				</div>
				<div class="reactor-info">
					<h1 class="reactor-title">QUANTUM REACTOR CONTROL</h1>
					<div class="reactor-metrics">
						<div class="metric">
							<span class="metric-label">CORE TEMP</span>
							<span class="metric-value" style="color: {getTemperatureColor(coreTemperature)}">
								{coreTemperature.toFixed(0)}K
							</span>
						</div>
						<div class="metric">
							<span class="metric-label">CONTAINMENT</span>
							<div class="containment-bar">
								<div class="bar-fill" 
									 style="width: {plasmaContainment}%;
											background: {plasmaContainment > 90 ? '#34D399' : plasmaContainment > 70 ? '#FBBF24' : '#FF1744'}">
								</div>
							</div>
							<span class="metric-value">{plasmaContainment.toFixed(1)}%</span>
						</div>
						<div class="metric">
							<span class="metric-label">OUTPUT</span>
							<span class="metric-value" style="color: #FBBF24">{energyOutput.toFixed(0)} MW</span>
						</div>
					</div>
				</div>
			</div>
			
			<div class="reactor-search">
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="SEARCH REACTORS..."
					   class="search-input"/>
				<div class="search-energy"></div>
			</div>
			
			<div class="reactor-status">
				<div class="status-display">
					<div class="status-value">{filteredFacilities.length}</div>
					<div class="status-label">REACTORS</div>
				</div>
				<div class="status-display">
					<div class="status-value">{energyBeams.length}</div>
					<div class="status-label">CONNECTIONS</div>
				</div>
				<div class="status-display {criticalityLevel > 0 ? 'critical' : ''}">
					<div class="status-value">{(criticalityLevel * 100).toFixed(0)}%</div>
					<div class="status-label">CRITICALITY</div>
				</div>
			</div>
		</header>
		
		<!-- Main Reactor Display -->
		<div class="reactor-display">
			{#if loading && !selectedFacility}
				<div class="reactor-loading">
					<div class="loading-reactor">
						<div class="reactor-startup">
							<div class="startup-ring ring-1"></div>
							<div class="startup-ring ring-2"></div>
							<div class="startup-ring ring-3"></div>
							<div class="startup-core">⬢</div>
						</div>
					</div>
					<p class="loading-text">INITIALIZING FUSION REACTOR...</p>
				</div>
			{:else if selectedFacility}
				<div class="facility-deep-dive">
					<div class="dive-header">
						<div class="facility-reactor">
							<div class="reactor-hologram">
								<div class="hologram-core" style="background: {getFacilityClass(selectedFacility.count).color}">
									{getFacilityClass(selectedFacility.count).symbol}
								</div>
								<div class="hologram-rings">
									{#each Array(4) as _, i}
										<div class="holo-ring" 
											 style="animation-delay: {i * 0.25}s;
													width: {40 + i * 15}px;
													height: {40 + i * 15}px;
													border-color: {getFacilityClass(selectedFacility.count).color}">
										</div>
									{/each}
								</div>
								<!-- Energy flow visualization -->
								<div class="energy-flow-visual">
									{#each Array(8) as _, i}
										<div class="energy-stream"
											 style="transform: rotate({i * 45}deg);
													background: linear-gradient(90deg, transparent, {getFacilityClass(selectedFacility.count).color}, transparent)">
										</div>
									{/each}
								</div>
							</div>
							<div class="facility-data">
								<h2>{selectedFacility.facility.toUpperCase()}</h2>
								<div class="reactor-signature">
									{facilityProfiles.get(selectedFacility.facility)?.reactorSignature || 'RX-UNKNOWN'}
								</div>
							</div>
						</div>
						<button class="close-reactor" on:click={closeDetails}>
							<span>✕</span>
						</button>
					</div>
					
					{#if facilityProfiles.get(selectedFacility.facility)}
						{@const profile = facilityProfiles.get(selectedFacility.facility)}
						<div class="reactor-analysis">
							<div class="analysis-grid">
								<!-- Power Metrics -->
								<div class="analysis-panel">
									<h3>POWER METRICS</h3>
									<div class="power-display">
										<div class="power-gauge">
											<svg viewBox="0 0 100 100">
												<circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255, 107, 203, 0.2)" stroke-width="8"/>
												<circle cx="50" cy="50" r="40" fill="none" 
														stroke="#FF6BCB" 
														stroke-width="8"
														stroke-dasharray="{profile.powerMetrics.efficiency * 2.51} 251"
														stroke-linecap="round"
														transform="rotate(-90 50 50)"/>
											</svg>
											<div class="gauge-center">
												<div class="gauge-value">{profile.powerMetrics.capacity.toFixed(0)}</div>
												<div class="gauge-label">MW</div>
											</div>
										</div>
										<div class="power-stats">
											<div class="stat">
												<span>Efficiency</span>
												<span>{profile.powerMetrics.efficiency.toFixed(1)}%</span>
											</div>
											<div class="stat">
												<span>Peak Output</span>
												<span>{profile.powerMetrics.peakOutput.toFixed(0)} MW</span>
											</div>
											<div class="stat">
												<span>Uptime</span>
												<span>{profile.powerMetrics.uptime.toFixed(2)}%</span>
											</div>
										</div>
									</div>
								</div>
								
								<!-- Thermal Profile -->
								<div class="analysis-panel">
									<h3>THERMAL PROFILE</h3>
									<div class="thermal-display">
										<div class="temp-bars">
											<div class="temp-bar">
												<div class="bar-label">CORE</div>
												<div class="bar-container">
													<div class="bar-fill" 
														 style="height: {profile.thermalProfile.coreTemp / 50}%;
																background: {getTemperatureColor(profile.thermalProfile.coreTemp)}">
													</div>
												</div>
												<div class="bar-value">{profile.thermalProfile.coreTemp.toFixed(0)}K</div>
											</div>
											<div class="temp-bar">
												<div class="bar-label">COOLANT</div>
												<div class="bar-container">
													<div class="bar-fill" 
														 style="height: {Math.abs(profile.thermalProfile.coolantTemp) / 3}%;
																background: #79E7FF">
													</div>
												</div>
												<div class="bar-value">{profile.thermalProfile.coolantTemp.toFixed(0)}°C</div>
											</div>
											<div class="temp-bar">
												<div class="bar-label">DISSIPATION</div>
												<div class="bar-container">
													<div class="bar-fill" 
														 style="height: {profile.thermalProfile.heatDissipation / 10}%;
																background: #34D399">
													</div>
												</div>
												<div class="bar-value">{profile.thermalProfile.heatDissipation.toFixed(0)}W</div>
											</div>
										</div>
									</div>
								</div>
								
								<!-- Quantum Metrics -->
								<div class="analysis-panel">
									<h3>QUANTUM STATE</h3>
									<div class="quantum-display">
										<div class="quantum-orb">
											<div class="orb-layer layer-1" style="border-color: #A78BFA"></div>
											<div class="orb-layer layer-2" style="border-color: #FF6BCB"></div>
											<div class="orb-layer layer-3" style="border-color: #79E7FF"></div>
											<div class="orb-center">
												<div class="quantum-value">{(profile.quantumMetrics.coherence * 100).toFixed(0)}%</div>
												<div class="quantum-label">COHERENCE</div>
											</div>
										</div>
										<div class="quantum-stats">
											<div class="q-stat">
												<span>Entanglement</span>
												<span>{(profile.quantumMetrics.entanglement * 100).toFixed(1)}%</span>
											</div>
											<div class="q-stat">
												<span>Superposition</span>
												<span>{profile.quantumMetrics.superposition ? 'ACTIVE' : 'COLLAPSED'}</span>
											</div>
										</div>
									</div>
								</div>
								
								<!-- Safety Metrics -->
								<div class="analysis-panel">
									<h3>SAFETY SYSTEMS</h3>
									<div class="safety-display">
										<div class="safety-indicators">
											<div class="indicator">
												<div class="indicator-bar">
													<div class="indicator-fill"
														 style="width: {profile.safetyMetrics.containment}%;
																background: {profile.safetyMetrics.containment > 95 ? '#34D399' : 
																			profile.safetyMetrics.containment > 85 ? '#FBBF24' : '#FF1744'}">
													</div>
												</div>
												<span>Containment {profile.safetyMetrics.containment.toFixed(0)}%</span>
											</div>
											<div class="indicator">
												<div class="indicator-bar">
													<div class="indicator-fill"
														 style="width: {100 - profile.safetyMetrics.radiation}%;
																background: {profile.safetyMetrics.radiation < 20 ? '#34D399' : 
																			profile.safetyMetrics.radiation < 50 ? '#FBBF24' : '#FF1744'}">
													</div>
												</div>
												<span>Radiation {profile.safetyMetrics.radiation.toFixed(0)} mSv</span>
											</div>
											<div class="indicator">
												<div class="indicator-bar">
													<div class="indicator-fill"
														 style="width: {profile.safetyMetrics.structural}%;
																background: {profile.safetyMetrics.structural > 90 ? '#34D399' : 
																			profile.safetyMetrics.structural > 70 ? '#FBBF24' : '#FF1744'}">
													</div>
												</div>
												<span>Structural {profile.safetyMetrics.structural.toFixed(0)}%</span>
											</div>
										</div>
									</div>
								</div>
							</div>
						</div>
					{/if}
					
					<div class="facility-node-stream">
						<table class="nodes-table">
							<thead>
								<tr>
									<th>NODE_ID</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>INFRASTRUCTURE</th>
									<th>SYNC_STATUS</th>
									<th>COOLING</th>
								</tr>
							</thead>
							<tbody>
								{#each facilityDetails as host}
									<tr class="node-row">
										<td class="node-id">{host.host.substring(0, 35)}</td>
										<td>{host.region || 'UNASSIGNED'}</td>
										<td>{host.country || 'UNASSIGNED'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>
											<span class="status-indicator {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'online' : 'offline'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}
											</span>
										</td>
										<td>
											<span class="cooling-indicator {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'optimal' : 'warning'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? '❄' : '🔥'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<!-- Reactor Network Visualization -->
				<div class="reactor-network">
					<div class="network-3d-space">
						<!-- Central reactor core -->
						<div class="central-reactor">
							<div class="central-core">
								<div class="core-rings">
									{#each Array(5) as _, i}
										<div class="core-ring"
											 style="animation-delay: {i * 0.2}s;
													width: {60 + i * 20}px;
													height: {60 + i * 20}px;
													border-color: rgba(255, 107, 203, {1 - i * 0.15})">
										</div>
									{/each}
								</div>
								<div class="core-center">⬢</div>
							</div>
						</div>
						
						<!-- Reactor nodes -->
						<svg class="reactor-connections" viewBox="-400 -400 800 800">
							<!-- Energy beams -->
							{#each energyBeams as beam}
								{#if reactorCores[beam.source] && reactorCores[beam.target]}
									<line x1="{reactorCores[beam.source].x}"
										  y1="{reactorCores[beam.source].y}"
										  x2="{reactorCores[beam.target].x}"
										  y2="{reactorCores[beam.target].y}"
										  stroke="rgba(121, 231, 255, {beam.intensity * 0.3})"
										  stroke-width="{beam.active ? 2 : 1}"
										  stroke-dasharray="{beam.active ? 'none' : '5,5'}">
										{#if beam.active}
											<animate attributeName="stroke-opacity"
													 values="0.3;0.8;0.3"
													 dur="2s"
													 repeatCount="indefinite"/>
										{/if}
									</line>
								{/if}
							{/each}
							
							<!-- Reactor nodes -->
							{#each reactorCores.slice(0, 30) as core}
								{@const facilityClass = getFacilityClass(core.count)}
								<g transform="translate({core.x}, {core.y})"
								   on:click={() => drillDownFacility(core.id, core.count)}>
									<!-- Node glow -->
									<circle r="{15 + core.plasma * 15}"
											fill={facilityClass.color}
											opacity="{core.plasma * 0.2}"
											filter="url(#fieldGradient)"/>
									<!-- Node core -->
									<circle r="10"
											fill={facilityClass.color}
											opacity="0.8"
											stroke={core.status === 'CRITICAL' ? '#FF1744' : 
													core.status === 'WARNING' ? '#FBBF24' : facilityClass.color}
											stroke-width="{core.status === 'OPERATIONAL' ? 1 : 2}"/>
									<!-- Node symbol -->
									<text text-anchor="middle"
										  dy="4"
										  fill="#000000"
										  font-size="12"
										  font-weight="bold">
										{facilityClass.symbol}
									</text>
									<!-- Node label -->
									<text y="20"
										  text-anchor="middle"
										  fill="#FFFFFF"
										  font-size="8"
										  opacity="0.8">
										{core.id.substring(0, 10)}
									</text>
								</g>
							{/each}
						</svg>
						
						<!-- Cooling nodes visualization -->
						<div class="cooling-network">
							{#each coolingSystem.slice(0, 20) as node}
								{#if node.active}
									<div class="cooling-node"
										 style="left: {50 + node.x / 6}%;
												top: {50 + node.y / 6}%;
												background: radial-gradient(circle, 
													rgba(121, 231, 255, {node.flow}), 
													transparent);
												box-shadow: 0 0 {10 * node.flow}px rgba(121, 231, 255, 0.5)">
									</div>
								{/if}
							{/each}
						</div>
					</div>
					
					<!-- Facility Matrix Table -->
					<div class="facility-matrix">
						<table class="matrix-table">
							<thead>
								<tr>
									<th>RANK</th>
									<th>REACTOR_ID</th>
									<th>CLASSIFICATION</th>
									<th>NODES</th>
									<th>TEMPERATURE</th>
									<th>OUTPUT</th>
									<th>STATUS</th>
								</tr>
							</thead>
							<tbody>
								{#each filteredFacilities as [facility, count], index}
									{@const facilityClass = getFacilityClass(count)}
									{@const profile = facilityProfiles.get(facility)}
									{@const core = reactorCores.find(c => c.id === facility)}
									<tr class="matrix-row"
										style="border-left: 3px solid {facilityClass.color}"
										on:click={() => drillDownFacility(facility, count)}>
										<td class="rank-cell">
											<span style="color: {facilityClass.color}">#{index + 1}</span>
										</td>
										<td class="facility-cell">
											<span class="facility-symbol" style="color: {facilityClass.color}">
												{facilityClass.symbol}
											</span>
											<span class="facility-name">{facility.substring(0, 30).toUpperCase()}</span>
										</td>
										<td>
											<span class="class-badge"
												  style="background: {facilityClass.glow};
														 color: {facilityClass.color};
														 border: 1px solid {facilityClass.color}">
												{facilityClass.level}
											</span>
										</td>
										<td class="numeric">{count.toLocaleString()}</td>
										<td>
											<span style="color: {getTemperatureColor(core?.temperature || 0)}">
												{core?.temperature.toFixed(0) || '0'}K
											</span>
										</td>
										<td>
											<div class="output-display">
												<div class="output-bar">
													<div class="output-fill"
														 style="width: {profile ? (profile.powerMetrics.capacity / 10) : 0}%;
																background: linear-gradient(90deg, transparent, {facilityClass.color})">
													</div>
												</div>
												<span>{profile?.powerMetrics.capacity.toFixed(0) || '0'} MW</span>
											</div>
										</td>
										<td>
											<span class="status-badge {core?.status.toLowerCase() || 'unknown'}">
												{core?.status || 'UNKNOWN'}
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
	.quantum-reactor-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		position: relative;
		overflow: hidden;
	}
	
	/* Plasma Field Container */
	.plasma-field-container {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.plasma-field {
		position: absolute;
		width: 100%;
		height: 100%;
	}
	
	.plasma-particle {
		position: absolute;
		width: 2px;
		height: 2px;
		border-radius: 50%;
	}
	
	.magnetic-field-svg {
		position: absolute;
		width: 100%;
		height: 100%;
		opacity: 0.5;
	}
	
	.containment-ring {
		position: absolute;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		border-radius: 50%;
		transition: transform 0.5s ease;
	}
	
	.reactor-control-interface {
		position: relative;
		z-index: 1;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
	
	/* Reactor Header */
	.reactor-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 2rem;
		background: linear-gradient(180deg, rgba(255, 107, 203, 0.05), transparent);
		border-bottom: 1px solid rgba(255, 107, 203, 0.2);
		backdrop-filter: blur(20px);
		z-index: 10;
	}
	
	.header-reactor {
		display: flex;
		align-items: center;
		gap: 2rem;
	}
	
	.reactor-core-visual {
		width: 120px;
		height: 120px;
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.tokamak-container {
		width: 100%;
		height: 100%;
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.reactor-ring {
		position: absolute;
		border: 1px solid;
		border-radius: 50%;
		transition: transform 0.1s linear;
	}
	
	.ring-particle {
		position: absolute;
		border-radius: 50%;
		transform-origin: center;
		left: 50%;
		top: 50%;
		margin-left: -1px;
		margin-top: -1px;
	}
	
	.reactor-core-center {
		position: relative;
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 10;
	}
	
	.core-pulse {
		position: absolute;
		width: 100%;
		height: 100%;
		border-radius: 50%;
		animation: corePulse 2s ease-in-out infinite;
		opacity: 0.5;
	}
	
	@keyframes corePulse {
		0%, 100% { transform: scale(0.8); opacity: 0.5; }
		50% { transform: scale(1.2); opacity: 1; }
	}
	
	.core-symbol {
		font-size: 1.5rem;
		color: #FF6BCB;
		text-shadow: 0 0 30px rgba(255, 107, 203, 0.8);
		z-index: 1;
	}
	
	.reactor-info {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.reactor-title {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 200;
		letter-spacing: 0.3em;
		background: linear-gradient(90deg, #FF6BCB, #79E7FF, #A78BFA);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}
	
	.reactor-metrics {
		display: flex;
		gap: 2rem;
	}
	
	.metric {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}
	
	.containment-bar {
		width: 100px;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.metric-value {
		font-size: 0.8rem;
		font-family: 'Courier New', monospace;
		min-width: 60px;
		text-align: right;
	}
	
	/* Reactor Search */
	.reactor-search {
		position: relative;
		flex: 1;
		max-width: 400px;
		margin: 0 2rem;
	}
	
	.search-input {
		width: 100%;
		padding: 0.75rem 1rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(255, 107, 203, 0.3);
		color: #FF6BCB;
		font-family: 'Courier New', monospace;
		font-size: 0.9rem;
		letter-spacing: 0.1em;
		transition: all 0.3s ease;
	}
	
	.search-input::placeholder {
		color: rgba(255, 107, 203, 0.4);
	}
	
	.search-input:focus {
		outline: none;
		border-color: #FF6BCB;
		background: rgba(255, 107, 203, 0.05);
		box-shadow: 0 0 30px rgba(255, 107, 203, 0.3);
	}
	
	.search-energy {
		position: absolute;
		bottom: -1px;
		left: 0;
		right: 0;
		height: 2px;
		background: linear-gradient(90deg, transparent, #FF6BCB, transparent);
		animation: energyFlow 2s linear infinite;
	}
	
	@keyframes energyFlow {
		from { transform: translateX(-100%); }
		to { transform: translateX(100%); }
	}
	
	/* Reactor Status */
	.reactor-status {
		display: flex;
		gap: 2rem;
	}
	
	.status-display {
		text-align: center;
	}
	
	.status-value {
		font-size: 1.8rem;
		font-weight: 100;
		color: #79E7FF;
		text-shadow: 0 0 20px rgba(121, 231, 255, 0.5);
		font-family: 'Courier New', monospace;
	}
	
	.status-display.critical .status-value {
		color: #FF1744;
		text-shadow: 0 0 20px rgba(255, 23, 68, 0.8);
		animation: criticalBlink 1s ease-in-out infinite;
	}
	
	@keyframes criticalBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}
	
	.status-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.2em;
		margin-top: 0.25rem;
	}
	
	/* Reactor Display */
	.reactor-display {
		flex: 1;
		overflow: hidden;
		padding: 2rem;
	}
	
	/* Loading State */
	.reactor-loading {
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.loading-reactor {
		position: relative;
		width: 150px;
		height: 150px;
	}
	
	.reactor-startup {
		width: 100%;
		height: 100%;
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.startup-ring {
		position: absolute;
		border: 2px solid #FF6BCB;
		border-radius: 50%;
		animation: startupRotate 3s linear infinite;
	}
	
	.startup-ring.ring-1 {
		inset: 0;
		animation-direction: normal;
	}
	
	.startup-ring.ring-2 {
		inset: 20px;
		animation-direction: reverse;
		border-color: #79E7FF;
	}
	
	.startup-ring.ring-3 {
		inset: 40px;
		animation-direction: normal;
		animation-duration: 2s;
		border-color: #A78BFA;
	}
	
	@keyframes startupRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.startup-core {
		font-size: 2rem;
		color: #FF6BCB;
		text-shadow: 0 0 30px rgba(255, 107, 203, 0.8);
		z-index: 1;
		animation: startupPulse 2s ease-in-out infinite;
	}
	
	@keyframes startupPulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.2); }
	}
	
	.loading-text {
		color: rgba(255, 107, 203, 0.6);
		font-size: 0.9rem;
		letter-spacing: 0.2em;
		animation: loadingFade 2s ease-in-out infinite;
	}
	
	@keyframes loadingFade {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 1; }
	}
	
	/* Reactor Network */
	.reactor-network {
		height: 100%;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
	}
	
	.network-3d-space {
		position: relative;
		background: radial-gradient(circle at center, rgba(255, 107, 203, 0.02), transparent);
		border: 1px solid rgba(255, 107, 203, 0.1);
		border-radius: 20px;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}
	
	.central-reactor {
		position: absolute;
		z-index: 10;
	}
	
	.central-core {
		position: relative;
		width: 120px;
		height: 120px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.core-rings {
		position: absolute;
		width: 100%;
		height: 100%;
	}
	
	.core-ring {
		position: absolute;
		border: 2px solid;
		border-radius: 50%;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		animation: coreRingRotate 5s linear infinite;
	}
	
	@keyframes coreRingRotate {
		from { transform: translate(-50%, -50%) rotate(0deg); }
		to { transform: translate(-50%, -50%) rotate(360deg); }
	}
	
	.core-center {
		font-size: 2rem;
		color: #FF6BCB;
		text-shadow: 0 0 40px rgba(255, 107, 203, 0.8);
		z-index: 1;
	}
	
	.reactor-connections {
		width: 100%;
		height: 100%;
		max-width: 600px;
		max-height: 600px;
	}
	
	.reactor-connections g {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.reactor-connections g:hover {
		transform: scale(1.2);
	}
	
	.cooling-network {
		position: absolute;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	
	.cooling-node {
		position: absolute;
		width: 20px;
		height: 20px;
		border-radius: 50%;
	}
	
	/* Facility Matrix */
	.facility-matrix {
		overflow: auto;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 107, 203, 0.1);
		border-radius: 20px;
		backdrop-filter: blur(10px);
	}
	
	.matrix-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.matrix-table th {
		background: linear-gradient(180deg, rgba(255, 107, 203, 0.1), rgba(0, 0, 0, 0.8));
		color: #FF6BCB;
		padding: 1rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 300;
		letter-spacing: 0.2em;
		border-bottom: 1px solid rgba(255, 107, 203, 0.3);
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
		background: rgba(255, 107, 203, 0.03);
		transform: translateX(5px);
	}
	
	.matrix-table td {
		padding: 0.75rem 1rem;
		font-size: 0.8rem;
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
	
	.facility-symbol {
		font-size: 1.2rem;
	}
	
	.facility-name {
		font-weight: 300;
		letter-spacing: 0.05em;
	}
	
	.class-badge {
		display: inline-block;
		padding: 0.3rem 0.6rem;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		border-radius: 4px;
	}
	
	.numeric {
		font-family: 'Courier New', monospace;
		color: #79E7FF;
	}
	
	.output-display {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
	}
	
	.output-bar {
		width: 60px;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}
	
	.output-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.status-badge {
		display: inline-block;
		padding: 0.2rem 0.4rem;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		border-radius: 4px;
		text-transform: uppercase;
	}
	
	.status-badge.operational {
		background: rgba(52, 211, 153, 0.2);
		color: #34D399;
		border: 1px solid #34D399;
	}
	
	.status-badge.warning {
		background: rgba(251, 191, 36, 0.2);
		color: #FBBF24;
		border: 1px solid #FBBF24;
	}
	
	.status-badge.critical {
		background: rgba(255, 23, 68, 0.2);
		color: #FF1744;
		border: 1px solid #FF1744;
		animation: statusBlink 1s ease-in-out infinite;
	}
	
	@keyframes statusBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}
	
	.status-badge.unknown {
		background: rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.5);
		border: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	/* Facility Deep Dive */
	.facility-deep-dive {
		height: 100%;
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 107, 203, 0.1);
		border-radius: 20px;
		backdrop-filter: blur(20px);
		overflow: hidden;
	}
	
	.dive-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 2rem;
		background: linear-gradient(135deg, rgba(255, 107, 203, 0.1), transparent);
		border-bottom: 1px solid rgba(255, 107, 203, 0.2);
	}
	
	.facility-reactor {
		display: flex;
		align-items: center;
		gap: 2rem;
	}
	
	.reactor-hologram {
		position: relative;
		width: 120px;
		height: 120px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.hologram-core {
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		border-radius: 50%;
		z-index: 2;
		box-shadow: 0 0 40px currentColor;
	}
	
	.hologram-rings {
		position: absolute;
		inset: 0;
		z-index: 1;
	}
	
	.holo-ring {
		position: absolute;
		border: 1px solid;
		border-radius: 50%;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		animation: holoRotate 3s ease-in-out infinite;
	}
	
	@keyframes holoRotate {
		0%, 100% { transform: translate(-50%, -50%) rotate(0deg) scale(1); }
		50% { transform: translate(-50%, -50%) rotate(180deg) scale(1.1); }
	}
	
	.energy-flow-visual {
		position: absolute;
		inset: -30px;
		z-index: 0;
	}
	
	.energy-stream {
		position: absolute;
		width: 100%;
		height: 2px;
		top: 50%;
		left: 0;
		transform-origin: center;
		animation: streamFlow 3s linear infinite;
	}
	
	@keyframes streamFlow {
		0% { opacity: 0; }
		50% { opacity: 1; }
		100% { opacity: 0; }
	}
	
	.facility-data {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.facility-data h2 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 200;
		color: #FF6BCB;
		letter-spacing: 0.1em;
		text-shadow: 0 0 20px rgba(255, 107, 203, 0.5);
	}
	
	.reactor-signature {
		font-family: 'Courier New', monospace;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}
	
	.close-reactor {
		background: rgba(255, 23, 68, 0.1);
		border: 1px solid #FF1744;
		color: #FF1744;
		width: 40px;
		height: 40px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.3s ease;
		font-size: 1.5rem;
	}
	
	.close-reactor:hover {
		background: rgba(255, 23, 68, 0.2);
		transform: rotate(90deg);
		box-shadow: 0 0 20px rgba(255, 23, 68, 0.5);
	}
	
	/* Reactor Analysis */
	.reactor-analysis {
		padding: 2rem;
		border-bottom: 1px solid rgba(255, 107, 203, 0.1);
	}
	
	.analysis-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1.5rem;
	}
	
	.analysis-panel {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 107, 203, 0.2);
		border-radius: 10px;
		padding: 1rem;
	}
	
	.analysis-panel h3 {
		margin: 0 0 1rem 0;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		font-weight: 300;
	}
	
	/* Power Display */
	.power-display {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.power-gauge {
		position: relative;
		width: 100px;
		height: 100px;
		margin: 0 auto;
	}
	
	.power-gauge svg {
		width: 100%;
		height: 100%;
	}
	
	.gauge-center {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
	}
	
	.gauge-value {
		font-size: 1.2rem;
		font-weight: 600;
		color: #FF6BCB;
	}
	
	.gauge-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.power-stats {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		font-size: 0.7rem;
	}
	
	.stat {
		display: flex;
		justify-content: space-between;
		color: rgba(255, 255, 255, 0.6);
	}
	
	.stat span:last-child {
		color: #79E7FF;
		font-family: 'Courier New', monospace;
	}
	
	/* Thermal Display */
	.thermal-display {
		display: flex;
		justify-content: space-around;
		align-items: flex-end;
		height: 120px;
	}
	
	.temp-bar {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}
	
	.bar-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.bar-container {
		width: 20px;
		height: 60px;
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		position: relative;
		display: flex;
		align-items: flex-end;
	}
	
	.bar-fill {
		width: 100%;
		transition: height 0.5s ease;
		border-radius: 1px;
	}
	
	.bar-value {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.8);
		font-family: 'Courier New', monospace;
		white-space: nowrap;
	}
	
	/* Quantum Display */
	.quantum-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
	}
	
	.quantum-orb {
		position: relative;
		width: 100px;
		height: 100px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.orb-layer {
		position: absolute;
		border: 1px solid;
		border-radius: 50%;
		animation: orbFloat 4s ease-in-out infinite;
	}
	
	.layer-1 {
		inset: 0;
		animation-delay: 0s;
	}
	
	.layer-2 {
		inset: 10px;
		animation-delay: 0.5s;
	}
	
	.layer-3 {
		inset: 20px;
		animation-delay: 1s;
	}
	
	@keyframes orbFloat {
		0%, 100% { transform: scale(1) rotate(0deg); }
		25% { transform: scale(1.1) rotate(90deg); }
		50% { transform: scale(1) rotate(180deg); }
		75% { transform: scale(0.9) rotate(270deg); }
	}
	
	.orb-center {
		text-align: center;
		z-index: 1;
	}
	
	.quantum-value {
		font-size: 1.2rem;
		font-weight: 600;
		color: #A78BFA;
	}
	
	.quantum-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.quantum-stats {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		font-size: 0.65rem;
		width: 100%;
	}
	
	.q-stat {
		display: flex;
		justify-content: space-between;
		color: rgba(255, 255, 255, 0.6);
	}
	
	.q-stat span:last-child {
		color: #A78BFA;
		font-family: 'Courier New', monospace;
	}
	
	/* Safety Display */
	.safety-display {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.safety-indicators {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.indicator {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	
	.indicator-bar {
		width: 100%;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.indicator-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.indicator span {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
	}
	
	/* Facility Node Stream */
	.facility-node-stream {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}
	
	.nodes-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.nodes-table th {
		background: rgba(0, 0, 0, 0.8);
		color: #FF6BCB;
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 300;
		letter-spacing: 0.1em;
		border-bottom: 1px solid rgba(255, 107, 203, 0.3);
		position: sticky;
		top: 0;
	}
	
	.node-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.2s ease;
	}
	
	.node-row:hover {
		background: rgba(255, 107, 203, 0.02);
	}
	
	.nodes-table td {
		padding: 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.node-id {
		font-family: 'Courier New', monospace;
		color: #79E7FF;
		font-size: 0.7rem;
	}
	
	.status-indicator, .cooling-indicator {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		font-size: 1rem;
	}
	
	.status-indicator.online {
		color: #34D399;
		text-shadow: 0 0 10px #34D399;
	}
	
	.status-indicator.offline {
		color: #666666;
	}
	
	.cooling-indicator.optimal {
		color: #79E7FF;
		text-shadow: 0 0 10px #79E7FF;
	}
	
	.cooling-indicator.warning {
		color: #FF1744;
		text-shadow: 0 0 10px #FF1744;
	}
	
	/* Responsive */
	@media (max-width: 1400px) {
		.reactor-network {
			grid-template-columns: 1fr;
		}
		
		.analysis-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}
	
	@media (max-width: 768px) {
		.reactor-header {
			flex-direction: column;
			gap: 1rem;
		}
		
		.analysis-grid {
			grid-template-columns: 1fr;
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
		background: linear-gradient(180deg, #FF6BCB, #79E7FF);
		border-radius: 3px;
	}
	
	::-webkit-scrollbar-corner {
		background: #000000;
	}