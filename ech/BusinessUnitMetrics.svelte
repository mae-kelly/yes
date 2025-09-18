<!-- BusinessUnitMetrics.svelte - Division Quantum Architecture Interface -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedDivision = null;
	let divisionDetails = [];
	let searchTerm = '';
	
	// Quantum architecture states
	let divisionStructures = [];
	let quantumLayers = [];
	let dataFlows = [];
	let architecturalMatrix = [];
	let dimensionalShift = 0;
	let structuralIntegrity = 100;
	let quantumResonance = 0;
	let fractalDepth = 0;
	let organizationalDNA = [];
	let divisionProfiles = new Map();
	
	// Holographic building visualization
	let buildings = [];
	let cityGrid = [];
	let energyGrid = [];
	let connectionMesh = [];
	
	// Animation controllers
	let animationFrames = {
		quantum: null,
		structural: null,
		energy: null
	};
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/business_unit_metrics');
			data = await response.json();
			loading = false;
			initializeQuantumArchitecture();
			startArchitecturalSimulation();
		} catch (err) {
			console.error('Division quantum sync failed:', err);
			loading = false;
		}
	});
	
	onDestroy(() => {
		Object.values(animationFrames).forEach(frame => {
			if (frame) cancelAnimationFrame(frame);
		});
	});
	
	function initializeQuantumArchitecture() {
		if (!data.business_intelligence) return;
		
		let divisions = Object.entries(data.business_intelligence)
			.sort((a, b) => b[1] - a[1])
			.slice(0, 100);
		
		// Create architectural structures for each division
		divisions.forEach(([division, count], i) => {
			// Create building structure
			let building = {
				id: division,
				count: count,
				height: Math.log10(count + 1) * 50 + 20,
				x: (i % 10) * 100,
				z: Math.floor(i / 10) * 100,
				floors: Math.ceil(Math.log10(count + 1) * 10),
				energyLevel: Math.random(),
				dataFlow: [],
				quantumState: 'STABLE',
				resonanceFrequency: 100 + Math.random() * 900,
				structuralPattern: generateStructuralPattern(count),
				divisions: generateSubDivisions(count),
				connections: []
			};
			
			buildings.push(building);
			divisionStructures.push(building);
			
			// Create division profile
			divisionProfiles.set(division, generateDivisionProfile(division, count));
		});
		
		// Create quantum layers (vertical slices through the architecture)
		for (let i = 0; i < 10; i++) {
			quantumLayers.push({
				depth: i * 50,
				opacity: 1 - (i * 0.08),
				frequency: 50 + i * 50,
				particles: generateQuantumParticles(30),
				wave: []
			});
		}
		
		// Initialize city grid
		for (let x = 0; x < 20; x++) {
			cityGrid[x] = [];
			for (let z = 0; z < 20; z++) {
				cityGrid[x][z] = {
					elevation: Math.sin(x * 0.3) * Math.cos(z * 0.3) * 10,
					energy: Math.random(),
					active: Math.random() > 0.3,
					pulse: Math.random() * Math.PI * 2
				};
			}
		}
		
		// Create energy grid connections
		createEnergyGrid();
		
		// Initialize organizational DNA strands
		for (let i = 0; i < 3; i++) {
			organizationalDNA.push({
				strand: i,
				sequence: generateDNASequence(divisions.length),
				rotation: i * 120,
				twist: 0
			});
		}
	}
	
	function generateStructuralPattern(seed) {
		let pattern = [];
		for (let i = 0; i < 8; i++) {
			pattern.push({
				level: i,
				segments: Math.floor(3 + Math.random() * 5),
				rotation: Math.random() * 360,
				scale: 1 - (i * 0.1),
				material: ['QUANTUM_GLASS', 'NEURAL_MESH', 'PHOTONIC_CRYSTAL', 'PLASMA_FIELD'][Math.floor(Math.random() * 4)]
			});
		}
		return pattern;
	}
	
	function generateSubDivisions(count) {
		let subDivs = [];
		let subCount = Math.min(10, Math.floor(Math.log10(count + 1) * 3));
		for (let i = 0; i < subCount; i++) {
			subDivs.push({
				id: `SUB_${i}`,
				size: Math.random() * count * 0.1,
				active: Math.random() > 0.2,
				resonance: Math.random()
			});
		}
		return subDivs;
	}
	
	function generateDivisionProfile(division, count) {
		return {
			quantumSignature: generateQuantumSignature(count),
			architecture: {
				complexity: Math.log10(count + 1) * 20,
				stability: 50 + Math.random() * 50,
				adaptability: 50 + Math.random() * 50,
				scalability: 50 + Math.random() * 50,
				efficiency: 50 + Math.random() * 50
			},
			energyMatrix: {
				input: count * 0.1,
				output: count * 0.08,
				efficiency: 80 + Math.random() * 20,
				resonance: Math.random()
			},
			fractalDimension: 1 + Math.random() * 2,
			quantumCoherence: Math.random(),
			structuralDNA: generateDNASequence(32)
		};
	}
	
	function generateQuantumSignature(seed) {
		let sig = [];
		let pattern = seed * 13337;
		for (let i = 0; i < 4; i++) {
			let segment = '';
			for (let j = 0; j < 8; j++) {
				pattern = (pattern * 1664525 + 1013904223) & 0xffffffff;
				segment += (pattern % 36).toString(36).toUpperCase();
			}
			sig.push(segment);
		}
		return sig.join('-');
	}
	
	function generateDNASequence(length) {
		let sequence = [];
		const bases = ['A', 'T', 'G', 'C'];
		for (let i = 0; i < length; i++) {
			sequence.push({
				base: bases[Math.floor(Math.random() * 4)],
				pair: bases[(Math.floor(Math.random() * 4) + 2) % 4],
				energy: Math.random(),
				mutation: Math.random() > 0.95
			});
		}
		return sequence;
	}
	
	function generateQuantumParticles(count) {
		let particles = [];
		for (let i = 0; i < count; i++) {
			particles.push({
				x: Math.random() * 100,
				y: Math.random() * 100,
				z: Math.random() * 100,
				vx: (Math.random() - 0.5) * 0.5,
				vy: (Math.random() - 0.5) * 0.5,
				vz: (Math.random() - 0.5) * 0.5,
				energy: Math.random(),
				color: `hsl(${280 + Math.random() * 60}, 100%, ${60 + Math.random() * 20}%)`
			});
		}
		return particles;
	}
	
	function createEnergyGrid() {
		// Create mesh connections between buildings
		buildings.forEach((building, i) => {
			let connectionCount = Math.min(5, 2 + Math.floor(Math.random() * 4));
			for (let j = 0; j < connectionCount; j++) {
				let targetIdx = Math.floor(Math.random() * buildings.length);
				if (targetIdx !== i) {
					connectionMesh.push({
						source: i,
						target: targetIdx,
						strength: Math.random(),
						energy: Math.random(),
						flowing: true,
						particles: []
					});
				}
			}
		});
		
		// Initialize energy flow particles
		connectionMesh.forEach(connection => {
			for (let i = 0; i < 5; i++) {
				connection.particles.push({
					position: Math.random(),
					speed: 0.5 + Math.random() * 0.5,
					size: 1 + Math.random() * 2
				});
			}
		});
	}
	
	function startArchitecturalSimulation() {
		let time = 0;
		
		function updateQuantumArchitecture() {
			time += 0.016;
			
			// Update dimensional shift
			dimensionalShift = Math.sin(time * 0.3) * 180;
			
			// Update quantum resonance
			quantumResonance = 50 + Math.sin(time * 0.5) * 30 + Math.sin(time * 1.7) * 20;
			
			// Update fractal depth
			fractalDepth = 3 + Math.sin(time * 0.2) * 2;
			
			// Update structural integrity based on activity
			structuralIntegrity = 70 + Math.sin(time * 0.4) * 20 + Math.random() * 10;
			
			// Update buildings
			buildings.forEach((building, i) => {
				building.energyLevel = 0.5 + Math.sin(time + i * 0.1) * 0.5;
				building.resonanceFrequency = 100 + Math.sin(time * 0.7 + i * 0.2) * 900;
				
				// Pulse effect for active buildings
				if (Math.random() < 0.01) {
					building.quantumState = ['STABLE', 'RESONATING', 'FLUCTUATING', 'EVOLVING'][Math.floor(Math.random() * 4)];
				}
				
				// Update sub-divisions
				building.divisions.forEach(sub => {
					sub.active = Math.random() > 0.3;
					sub.resonance = Math.abs(Math.sin(time * 2 + Math.random()));
				});
			});
			
			// Update quantum layers
			quantumLayers.forEach((layer, i) => {
				layer.particles.forEach(p => {
					p.x = (p.x + p.vx + 100) % 100;
					p.y = (p.y + p.vy + 100) % 100;
					p.z = (p.z + p.vz + 100) % 100;
					p.energy = 0.5 + Math.sin(time * 2 + i) * 0.5;
				});
				
				// Generate wave pattern
				layer.wave = [];
				for (let j = 0; j < 50; j++) {
					layer.wave.push(Math.sin(time + j * 0.2 + i * 0.5) * 20);
				}
			});
			
			// Update city grid
			cityGrid.forEach((row, x) => {
				row.forEach((cell, z) => {
					cell.energy = 0.5 + Math.sin(time + cell.pulse) * 0.5;
					cell.elevation = Math.sin(x * 0.3 + time * 0.2) * Math.cos(z * 0.3 + time * 0.1) * 10;
				});
			});
			
			// Update energy grid connections
			connectionMesh.forEach(connection => {
				connection.energy = 0.5 + Math.sin(time * 3) * 0.5;
				connection.particles.forEach(particle => {
					particle.position = (particle.position + particle.speed * 0.01) % 1;
				});
			});
			
			// Update DNA strands
			organizationalDNA.forEach(dna => {
				dna.twist += 1;
				dna.sequence.forEach(base => {
					base.energy = 0.5 + Math.sin(time * 4 + Math.random()) * 0.5;
				});
			});
			
			animationFrames.quantum = requestAnimationFrame(updateQuantumArchitecture);
		}
		
		updateQuantumArchitecture();
	}
	
	$: filteredDivisions = data.business_intelligence ? 
		Object.entries(data.business_intelligence)
			.filter(([division]) => division.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredDivisions.length > 0 ? Math.max(...filteredDivisions.map(([,c]) => c)) : 1;
	$: minCount = filteredDivisions.length > 0 ? Math.min(...filteredDivisions.map(([,c]) => c)) : 0;
	
	function getDivisionClass(count) {
		let normalized = (count - minCount) / (maxCount - minCount || 1);
		let percentile = normalized * 100;
		
		if (percentile >= 85) {
			return {
				level: 'MEGA_STRUCTURE',
				color: '#BD93F9', // Neon purple
				glow: '#BD93F940',
				symbol: '◈',
				description: 'Quantum Metropolis'
			};
		} else if (percentile >= 65) {
			return {
				level: 'NEXUS_TOWER',
				color: '#50FA7B', // Neon green
				glow: '#50FA7B40',
				symbol: '◆',
				description: 'Neural Hub'
			};
		} else if (percentile >= 45) {
			return {
				level: 'CORE_COMPLEX',
				color: '#8BE9FD', // Neon cyan
				glow: '#8BE9FD40',
				symbol: '▲',
				description: 'Data Fortress'
			};
		} else if (percentile >= 25) {
			return {
				level: 'SECTOR_NODE',
				color: '#F1FA8C', // Neon yellow
				glow: '#F1FA8C40',
				symbol: '●',
				description: 'Grid Point'
			};
		} else {
			return {
				level: 'QUANTUM_SEED',
				color: '#FFB86C', // Neon orange
				glow: '#FFB86C40',
				symbol: '○',
				description: 'Emerging Structure'
			};
		}
	}
	
	async function drillDownDivision(division, count) {
		selectedDivision = { division, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(division)}`);
			let result = await response.json();
			divisionDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Division deep scan failed:', err);
			divisionDetails = [];
			loading = false;
		}
	}
	
	function closeDetails() {
		selectedDivision = null;
		divisionDetails = [];
	}
</script>

<div class="quantum-architecture-interface">
	<!-- Quantum City Background -->
	<div class="quantum-city">
		<!-- City Grid Base -->
		<div class="city-grid-base">
			{#each cityGrid as row, x}
				{#each row as cell, z}
					{#if cell.active}
						<div class="grid-cell"
							 style="left: {x * 5}%; 
									top: {z * 5}%;
									height: {5 + cell.elevation}px;
									background: linear-gradient(180deg, 
										rgba(189, 147, 249, {cell.energy * 0.3}), 
										rgba(139, 233, 253, {cell.energy * 0.1}));
									box-shadow: 0 0 {10 * cell.energy}px rgba(189, 147, 249, {cell.energy * 0.5})">
						</div>
					{/if}
				{/each}
			{/each}
		</div>
		
		<!-- Quantum Layers -->
		{#each quantumLayers as layer}
			<div class="quantum-layer"
				 style="transform: translateZ({layer.depth}px); opacity: {layer.opacity}">
				<svg class="layer-waves" viewBox="0 0 100 100">
					<path d="M 0,50 {layer.wave.map((y, i) => `L ${i * 2},${50 + y}`).join(' ')}"
						  stroke="rgba(189, 147, 249, 0.3)"
						  stroke-width="0.5"
						  fill="none"/>
				</svg>
				{#each layer.particles as particle}
					<div class="quantum-particle"
						 style="left: {particle.x}%; 
								top: {particle.y}%;
								background: {particle.color};
								opacity: {particle.energy};
								box-shadow: 0 0 {5 * particle.energy}px {particle.color}">
					</div>
				{/each}
			</div>
		{/each}
	</div>
	
	<div class="division-architecture-interface">
		<!-- Architectural Header -->
		<header class="architectural-header">
			<div class="header-structure">
				<div class="structure-core">
					<!-- DNA Helix Visualization -->
					<div class="dna-helix" style="transform: rotateY({dimensionalShift}deg)">
						{#each organizationalDNA as dna}
							<div class="dna-strand" style="transform: rotateZ({dna.rotation}deg) rotateY({dna.twist}deg)">
								{#each dna.sequence.slice(0, 10) as base, i}
									<div class="dna-base" 
										 style="top: {i * 10}%; 
												background: {base.mutation ? '#FF79C6' : '#8BE9FD'};
												opacity: {base.energy}">
										{base.base}
									</div>
								{/each}
							</div>
						{/each}
					</div>
				</div>
				<div class="structure-info">
					<h1 class="architecture-title">DIVISION QUANTUM ARCHITECTURE</h1>
					<div class="structure-metrics">
						<div class="metric">
							<span class="metric-label">STRUCTURAL INTEGRITY</span>
							<div class="integrity-bar">
								<div class="bar-fill" style="width: {structuralIntegrity}%; 
															  background: linear-gradient(90deg, #BD93F9, #50FA7B)"></div>
							</div>
							<span class="metric-value">{structuralIntegrity.toFixed(0)}%</span>
						</div>
						<div class="metric">
							<span class="metric-label">QUANTUM RESONANCE</span>
							<span class="metric-value">{quantumResonance.toFixed(1)} Hz</span>
						</div>
					</div>
				</div>
			</div>
			
			<div class="architectural-search">
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="SEARCH DIVISIONS..."
					   class="search-input"/>
				<div class="search-scan"></div>
			</div>
			
			<div class="header-analytics">
				<div class="analytic">
					<div class="analytic-value">{filteredDivisions.length}</div>
					<div class="analytic-label">STRUCTURES</div>
				</div>
				<div class="analytic">
					<div class="analytic-value">{buildings.length}</div>
					<div class="analytic-label">BUILDINGS</div>
				</div>
				<div class="analytic">
					<div class="analytic-value">{fractalDepth.toFixed(1)}</div>
					<div class="analytic-label">FRACTAL DEPTH</div>
				</div>
			</div>
		</header>
		
		<!-- Main Architectural Display -->
		<div class="architectural-display">
			{#if loading && !selectedDivision}
				<div class="architectural-loading">
					<div class="loading-structure">
						<div class="structure-beam beam-1"></div>
						<div class="structure-beam beam-2"></div>
						<div class="structure-beam beam-3"></div>
						<div class="structure-core-loading">◈</div>
					</div>
					<p class="loading-text">CONSTRUCTING QUANTUM ARCHITECTURE...</p>
				</div>
			{:else if selectedDivision}
				<div class="division-deep-analysis">
					<div class="analysis-header">
						<div class="division-hologram">
							<div class="hologram-building">
								<div class="building-core" style="background: {getDivisionClass(selectedDivision.count).color}">
									{getDivisionClass(selectedDivision.count).symbol}
								</div>
								<div class="building-layers">
									{#each Array(5) as _, i}
										<div class="building-layer" 
											 style="animation-delay: {i * 0.2}s; 
													border-color: {getDivisionClass(selectedDivision.count).color}"></div>
									{/each}
								</div>
							</div>
							<div class="division-identity">
								<h2>{selectedDivision.division.toUpperCase()}</h2>
								<div class="quantum-signature">
									{divisionProfiles.get(selectedDivision.division)?.quantumSignature || 'UNKNOWN'}
								</div>
							</div>
						</div>
						<button class="close-analysis" on:click={closeDetails}>
							<span>✕</span>
						</button>
					</div>
					
					{#if divisionProfiles.get(selectedDivision.division)}
						{@const profile = divisionProfiles.get(selectedDivision.division)}
						<div class="architectural-analysis">
							<div class="analysis-grid">
								<div class="analysis-card">
									<div class="card-label">COMPLEXITY</div>
									<div class="card-visual">
										<div class="complexity-rings">
											{#each Array(3) as _, i}
												<div class="ring" 
													 style="animation-delay: {i * 0.3}s;
															width: {30 + i * 20}px;
															height: {30 + i * 20}px;
															border-color: {getDivisionClass(selectedDivision.count).color}"></div>
											{/each}
										</div>
										<div class="card-value">{profile.architecture.complexity.toFixed(0)}</div>
									</div>
								</div>
								<div class="analysis-card">
									<div class="card-label">STABILITY</div>
									<div class="card-visual">
										<div class="stability-graph">
											<svg viewBox="0 0 100 50">
												<polyline points="0,25 20,{25 - profile.architecture.stability * 0.2} 
																  40,{25 + profile.architecture.adaptability * 0.2} 
																  60,{25 - profile.architecture.scalability * 0.2} 
																  80,{25 + profile.architecture.efficiency * 0.2} 
																  100,25"
														  stroke={getDivisionClass(selectedDivision.count).color}
														  stroke-width="2"
														  fill="none"/>
											</svg>
										</div>
										<div class="card-value">{profile.architecture.stability.toFixed(0)}%</div>
									</div>
								</div>
								<div class="analysis-card">
									<div class="card-label">ENERGY MATRIX</div>
									<div class="card-visual">
										<div class="energy-flow">
											<div class="flow-in">IN: {profile.energyMatrix.input.toFixed(1)}</div>
											<div class="flow-converter">
												<div class="converter-efficiency">{profile.energyMatrix.efficiency.toFixed(0)}%</div>
											</div>
											<div class="flow-out">OUT: {profile.energyMatrix.output.toFixed(1)}</div>
										</div>
									</div>
								</div>
								<div class="analysis-card">
									<div class="card-label">FRACTAL DIMENSION</div>
									<div class="card-visual">
										<div class="fractal-display">
											{profile.fractalDimension.toFixed(2)}D
										</div>
									</div>
								</div>
							</div>
						</div>
					{/if}
					
					<div class="division-node-stream">
						<table class="nodes-table">
							<thead>
								<tr>
									<th>NODE_IDENTIFIER</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>INFRASTRUCTURE</th>
									<th>SYNC_STATUS</th>
									<th>SHIELD_STATUS</th>
								</tr>
							</thead>
							<tbody>
								{#each divisionDetails as host}
									<tr class="node-row">
										<td class="node-id">{host.host.substring(0, 35)}</td>
										<td>{host.region || 'UNASSIGNED'}</td>
										<td>{host.country || 'UNASSIGNED'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>
											<span class="status-indicator {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'synced' : 'desynced'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}
											</span>
										</td>
										<td>
											<span class="shield-indicator {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? '⬢' : '⬡'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<!-- Architectural City View -->
				<div class="architectural-view">
					<div class="city-visualization">
						<!-- 3D Building Grid -->
						<div class="buildings-container" style="transform: rotateX(-30deg) rotateY({dimensionalShift}deg)">
							{#each buildings.slice(0, 50) as building, i}
								{@const divClass = getDivisionClass(building.count)}
								<div class="building-structure"
									 style="left: {building.x}px;
											bottom: 0;
											transform: translateZ({building.z}px);
											height: {building.height}px"
									 on:click={() => drillDownDivision(building.id, building.count)}>
									<div class="building-body"
										 style="background: linear-gradient(180deg, {divClass.color}40, {divClass.color}10);
												border: 1px solid {divClass.color};
												box-shadow: 0 0 {building.energyLevel * 30}px {divClass.glow}">
										<!-- Floors -->
										{#each Array(Math.min(10, building.floors)) as _, floor}
											<div class="building-floor"
												 style="bottom: {floor * 10}%;
														background: {building.divisions[floor]?.active ? divClass.color : 'transparent'};
														opacity: {building.divisions[floor]?.resonance || 0.2}">
											</div>
										{/each}
										<div class="building-label">{building.id.substring(0, 10)}</div>
										<div class="building-beacon"
											 style="background: {divClass.color};
													box-shadow: 0 0 {20 + building.energyLevel * 20}px {divClass.color}">
										</div>
									</div>
								</div>
							{/each}
							
							<!-- Energy Connections -->
							<svg class="connection-mesh" viewBox="0 0 1000 1000">
								{#each connectionMesh as connection}
									{#if buildings[connection.source] && buildings[connection.target]}
										<line x1="{buildings[connection.source].x}"
											  y1="{1000 - buildings[connection.source].z}"
											  x2="{buildings[connection.target].x}"
											  y2="{1000 - buildings[connection.target].z}"
											  stroke="rgba(139, 233, 253, 0.2)"
											  stroke-width="{connection.strength * 2}"
											  stroke-dasharray="{connection.flowing ? 'none' : '5,5'}">
											<animate attributeName="stroke-opacity"
													 values="0.2;0.5;0.2"
													 dur="3s"
													 repeatCount="indefinite"/>
										</line>
									{/if}
								{/each}
							</svg>
						</div>
					</div>
					
					<!-- Division Matrix Table -->
					<div class="division-matrix">
						<table class="matrix-table">
							<thead>
								<tr>
									<th>RANK</th>
									<th>DIVISION_ID</th>
									<th>ARCHITECTURE</th>
									<th>NODES</th>
									<th>ENERGY</th>
									<th>RESONANCE</th>
									<th>QUANTUM_SIG</th>
								</tr>
							</thead>
							<tbody>
								{#each filteredDivisions as [division, count], index}
									{@const divClass = getDivisionClass(count)}
									{@const profile = divisionProfiles.get(division)}
									<tr class="matrix-row"
										style="border-left: 3px solid {divClass.color}"
										on:click={() => drillDownDivision(division, count)}>
										<td class="rank-cell">
											<span style="color: {divClass.color}">#{index + 1}</span>
										</td>
										<td class="division-cell">
											<span class="division-symbol" style="color: {divClass.color}">
												{divClass.symbol}
											</span>
											<span class="division-name">{division.substring(0, 30).toUpperCase()}</span>
										</td>
										<td>
											<span class="architecture-badge"
												  style="background: {divClass.glow};
														 color: {divClass.color};
														 border: 1px solid {divClass.color}">
												{divClass.level}
											</span>
										</td>
										<td class="numeric">{count.toLocaleString()}</td>
										<td>
											<div class="energy-meter">
												<div class="energy-level"
													 style="width: {profile ? profile.energyMatrix.efficiency : 0}%;
															background: linear-gradient(90deg, transparent, {divClass.color})">
												</div>
											</div>
										</td>
										<td>
											<div class="resonance-display">
												{profile ? profile.quantumCoherence.toFixed(2) : '0.00'}
											</div>
										</td>
										<td class="signature-cell">
											{profile ? profile.quantumSignature.substring(0, 8) : 'UNKNOWN'}...
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
	.quantum-architecture-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		position: relative;
		overflow: hidden;
		perspective: 1500px;
	}
	
	/* Quantum City Background */
	.quantum-city {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		transform-style: preserve-3d;
	}
	
	.city-grid-base {
		position: absolute;
		width: 100%;
		height: 100%;
		transform: rotateX(60deg) translateZ(-100px);
		opacity: 0.3;
	}
	
	.grid-cell {
		position: absolute;
		width: 4%;
		border: 1px solid rgba(189, 147, 249, 0.1);
	}
	
	.quantum-layer {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		transform-style: preserve-3d;
	}
	
	.layer-waves {
		position: absolute;
		width: 100%;
		height: 100%;
		opacity: 0.3;
	}
	
	.quantum-particle {
		position: absolute;
		width: 2px;
		height: 2px;
		border-radius: 50%;
	}
	
	.division-architecture-interface {
		position: relative;
		z-index: 1;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
	
	/* Architectural Header */
	.architectural-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 2rem;
		background: linear-gradient(180deg, rgba(189, 147, 249, 0.05), transparent);
		border-bottom: 1px solid rgba(189, 147, 249, 0.2);
		backdrop-filter: blur(20px);
		z-index: 10;
	}
	
	.header-structure {
		display: flex;
		align-items: center;
		gap: 2rem;
	}
	
	.structure-core {
		width: 100px;
		height: 100px;
		position: relative;
		perspective: 500px;
	}
	
	.dna-helix {
		width: 100%;
		height: 100%;
		position: relative;
		transform-style: preserve-3d;
		transition: transform 0.5s ease;
	}
	
	.dna-strand {
		position: absolute;
		width: 100%;
		height: 100%;
		transform-style: preserve-3d;
	}
	
	.dna-base {
		position: absolute;
		width: 20px;
		height: 5px;
		left: 50%;
		transform: translateX(-50%);
		font-size: 0.6rem;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #000000;
		font-weight: bold;
		border-radius: 2px;
	}
	
	.structure-info {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.architecture-title {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 200;
		letter-spacing: 0.3em;
		background: linear-gradient(90deg, #BD93F9, #50FA7B, #8BE9FD);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}
	
	.structure-metrics {
		display: flex;
		gap: 2rem;
		align-items: center;
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
	
	.integrity-bar {
		width: 120px;
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
		color: #BD93F9;
		font-family: 'Courier New', monospace;
	}
	
	/* Architectural Search */
	.architectural-search {
		position: relative;
		flex: 1;
		max-width: 400px;
		margin: 0 2rem;
	}
	
	.search-input {
		width: 100%;
		padding: 0.75rem 1rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(189, 147, 249, 0.3);
		color: #BD93F9;
		font-family: 'Courier New', monospace;
		font-size: 0.9rem;
		letter-spacing: 0.1em;
		transition: all 0.3s ease;
	}
	
	.search-input::placeholder {
		color: rgba(189, 147, 249, 0.4);
	}
	
	.search-input:focus {
		outline: none;
		border-color: #BD93F9;
		background: rgba(189, 147, 249, 0.05);
		box-shadow: 0 0 30px rgba(189, 147, 249, 0.3);
	}
	
	.search-scan {
		position: absolute;
		bottom: -1px;
		left: 0;
		right: 0;
		height: 1px;
		background: linear-gradient(90deg, transparent, #BD93F9, transparent);
		animation: scanLine 2s linear infinite;
	}
	
	@keyframes scanLine {
		from { transform: translateX(-100%); }
		to { transform: translateX(100%); }
	}
	
	/* Header Analytics */
	.header-analytics {
		display: flex;
		gap: 2rem;
	}
	
	.analytic {
		text-align: center;
	}
	
	.analytic-value {
		font-size: 1.8rem;
		font-weight: 100;
		color: #50FA7B;
		text-shadow: 0 0 20px rgba(80, 250, 123, 0.5);
		font-family: 'Courier New', monospace;
	}
	
	.analytic-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.2em;
		margin-top: 0.25rem;
	}
	
	/* Architectural Display */
	.architectural-display {
		flex: 1;
		overflow: hidden;
		padding: 2rem;
	}
	
	/* Loading State */
	.architectural-loading {
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.loading-structure {
		position: relative;
		width: 150px;
		height: 150px;
	}
	
	.structure-beam {
		position: absolute;
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, #BD93F9, transparent);
		left: 0;
		top: 50%;
		transform-origin: center;
		animation: beamRotate 3s linear infinite;
	}
	
	.beam-1 { animation-delay: 0s; }
	.beam-2 { animation-delay: 1s; transform: rotate(60deg); }
	.beam-3 { animation-delay: 2s; transform: rotate(120deg); }
	
	@keyframes beamRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.structure-core-loading {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 2rem;
		color: #BD93F9;
		text-shadow: 0 0 30px rgba(189, 147, 249, 0.8);
		animation: corePulse 2s ease-in-out infinite;
	}
	
	@keyframes corePulse {
		0%, 100% { transform: translate(-50%, -50%) scale(1); }
		50% { transform: translate(-50%, -50%) scale(1.2); }
	}
	
	.loading-text {
		color: rgba(189, 147, 249, 0.6);
		font-size: 0.9rem;
		letter-spacing: 0.2em;
		animation: textFade 2s ease-in-out infinite;
	}
	
	@keyframes textFade {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 1; }
	}
	
	/* Architectural View */
	.architectural-view {
		height: 100%;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
	}
	
	.city-visualization {
		position: relative;
		background: radial-gradient(circle at center, rgba(189, 147, 249, 0.02), transparent);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 20px;
		overflow: hidden;
		perspective: 1000px;
	}
	
	.buildings-container {
		position: absolute;
		width: 90%;
		height: 90%;
		top: 5%;
		left: 5%;
		transform-style: preserve-3d;
		transition: transform 0.5s ease;
	}
	
	.building-structure {
		position: absolute;
		width: 60px;
		cursor: pointer;
		transform-style: preserve-3d;
		transition: all 0.3s ease;
	}
	
	.building-structure:hover {
		transform: translateZ(20px) scale(1.1);
		z-index: 10;
	}
	
	.building-body {
		width: 100%;
		height: 100%;
		position: relative;
		transform-style: preserve-3d;
	}
	
	.building-floor {
		position: absolute;
		width: 100%;
		height: 2px;
		left: 0;
	}
	
	.building-label {
		position: absolute;
		bottom: -20px;
		left: 50%;
		transform: translateX(-50%);
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		white-space: nowrap;
	}
	
	.building-beacon {
		position: absolute;
		top: -5px;
		left: 50%;
		transform: translateX(-50%);
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: beaconPulse 2s ease-in-out infinite;
	}
	
	@keyframes beaconPulse {
		0%, 100% { transform: translateX(-50%) scale(1); }
		50% { transform: translateX(-50%) scale(1.5); }
	}
	
	.connection-mesh {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	
	/* Division Matrix */
	.division-matrix {
		overflow: auto;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 20px;
		backdrop-filter: blur(10px);
	}
	
	.matrix-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.matrix-table th {
		background: linear-gradient(180deg, rgba(189, 147, 249, 0.1), rgba(0, 0, 0, 0.8));
		color: #BD93F9;
		padding: 1rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 300;
		letter-spacing: 0.2em;
		border-bottom: 1px solid rgba(189, 147, 249, 0.3);
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
		background: rgba(189, 147, 249, 0.03);
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
	
	.division-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.division-symbol {
		font-size: 1.2rem;
	}
	
	.division-name {
		font-weight: 300;
		letter-spacing: 0.05em;
	}
	
	.architecture-badge {
		display: inline-block;
		padding: 0.3rem 0.6rem;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		border-radius: 4px;
	}
	
	.numeric {
		font-family: 'Courier New', monospace;
		color: #50FA7B;
	}
	
	.energy-meter {
		width: 80px;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}
	
	.energy-level {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.resonance-display {
		font-family: 'Courier New', monospace;
		font-size: 0.75rem;
		color: #8BE9FD;
	}
	
	.signature-cell {
		font-family: 'Courier New', monospace;
		font-size: 0.7rem;
		color: rgba(189, 147, 249, 0.6);
	}
	
	/* Division Deep Analysis */
	.division-deep-analysis {
		height: 100%;
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 20px;
		backdrop-filter: blur(20px);
		overflow: hidden;
	}
	
	.analysis-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 2rem;
		background: linear-gradient(135deg, rgba(189, 147, 249, 0.1), transparent);
		border-bottom: 1px solid rgba(189, 147, 249, 0.2);
	}
	
	.division-hologram {
		display: flex;
		align-items: center;
		gap: 2rem;
	}
	
	.hologram-building {
		position: relative;
		width: 100px;
		height: 100px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.building-core {
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		border-radius: 10px;
		z-index: 1;
		box-shadow: 0 0 40px currentColor;
	}
	
	.building-layers {
		position: absolute;
		inset: -20px;
	}
	
	.building-layer {
		position: absolute;
		border: 1px solid;
		border-radius: 10px;
		animation: layerFloat 3s ease-in-out infinite;
	}
	
	.building-layer:nth-child(1) { inset: 0; }
	.building-layer:nth-child(2) { inset: 5px; }
	.building-layer:nth-child(3) { inset: 10px; }
	.building-layer:nth-child(4) { inset: 15px; }
	.building-layer:nth-child(5) { inset: 20px; }
	
	@keyframes layerFloat {
		0%, 100% { transform: scale(1) rotateZ(0deg); opacity: 0.3; }
		50% { transform: scale(1.05) rotateZ(5deg); opacity: 0.6; }
	}
	
	.division-identity {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.division-identity h2 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 200;
		color: #BD93F9;
		letter-spacing: 0.1em;
		text-shadow: 0 0 20px rgba(189, 147, 249, 0.5);
	}
	
	.quantum-signature {
		font-family: 'Courier New', monospace;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}
	
	.close-analysis {
		background: rgba(255, 184, 108, 0.1);
		border: 1px solid #FFB86C;
		color: #FFB86C;
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
	
	.close-analysis:hover {
		background: rgba(255, 184, 108, 0.2);
		transform: rotate(90deg);
		box-shadow: 0 0 20px rgba(255, 184, 108, 0.5);
	}
	
	/* Architectural Analysis */
	.architectural-analysis {
		padding: 2rem;
		border-bottom: 1px solid rgba(189, 147, 249, 0.1);
	}
	
	.analysis-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1.5rem;
	}
	
	.analysis-card {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(189, 147, 249, 0.2);
		border-radius: 10px;
		padding: 1rem;
		text-align: center;
	}
	
	.card-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		margin-bottom: 0.5rem;
	}
	
	.card-visual {
		position: relative;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.complexity-rings {
		position: relative;
		width: 60px;
		height: 60px;
	}
	
	.complexity-rings .ring {
		position: absolute;
		border: 1px solid;
		border-radius: 50%;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: ringPulse 3s ease-in-out infinite;
	}
	
	@keyframes ringPulse {
		0%, 100% { opacity: 0.3; }
		50% { opacity: 0.8; }
	}
	
	.card-value {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 1.2rem;
		font-weight: 600;
		color: #FFFFFF;
	}
	
	.stability-graph {
		width: 100%;
		height: 100%;
	}
	
	.stability-graph svg {
		width: 100%;
		height: 100%;
	}
	
	.energy-flow {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		font-size: 0.6rem;
	}
	
	.flow-in, .flow-out {
		color: #50FA7B;
		font-family: 'Courier New', monospace;
	}
	
	.flow-converter {
		width: 30px;
		height: 30px;
		background: radial-gradient(circle, #BD93F9, transparent);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.5rem;
		color: #FFFFFF;
	}
	
	.fractal-display {
		font-size: 1.5rem;
		font-weight: 600;
		color: #8BE9FD;
		text-shadow: 0 0 20px rgba(139, 233, 253, 0.5);
		font-family: 'Courier New', monospace;
	}
	
	/* Division Node Stream */
	.division-node-stream {
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
		color: #BD93F9;
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 300;
		letter-spacing: 0.1em;
		border-bottom: 1px solid rgba(189, 147, 249, 0.3);
		position: sticky;
		top: 0;
	}
	
	.node-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.2s ease;
	}
	
	.node-row:hover {
		background: rgba(189, 147, 249, 0.02);
	}
	
	.nodes-table td {
		padding: 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.node-id {
		font-family: 'Courier New', monospace;
		color: #BD93F9;
		font-size: 0.7rem;
	}
	
	.status-indicator, .shield-indicator {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		font-size: 1rem;
	}
	
	.status-indicator.synced {
		color: #50FA7B;
		text-shadow: 0 0 10px #50FA7B;
	}
	
	.status-indicator.desynced {
		color: #666666;
	}
	
	.shield-indicator.active {
		color: #8BE9FD;
		text-shadow: 0 0 10px #8BE9FD;
	}
	
	.shield-indicator.inactive {
		color: #FFB86C;
		text-shadow: 0 0 10px #FFB86C;
	}
	
	/* Responsive */
	@media (max-width: 1400px) {
		.architectural-view {
			grid-template-columns: 1fr;
		}
		
		.analysis-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}
	
	@media (max-width: 768px) {
		.architectural-header {
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
		background: linear-gradient(180deg, #BD93F9, #50FA7B);
		border-radius: 3px;
	}
	
	::-webkit-scrollbar-corner {
		background: #000000;
	}
</style>