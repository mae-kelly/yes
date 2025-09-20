<!-- SourceTables.svelte - Quantum Architecture Interface -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let sourceDetails = [];
	let searchTerm = '';
	
	// Quantum architecture states
	let sourceStructures = [];
	let quantumLayers = [];
	let dataFlows = [];
	let dimensionalShift = 0;
	let dataIntegrity = 100;
	let quantumResonance = 0;
	let networkDepth = 0;
	let sourceDNA = [];
	let sourceProfiles = new Map();
	
	// Holographic visualization
	let dataTowers = [];
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
			let response = await fetch('http://localhost:5000/api/source_tables');
			data = await response.json();
			loading = false;
			initializeQuantumArchitecture();
			startArchitecturalSimulation();
		} catch (err) {
			console.error('Source quantum sync failed:', err);
			loading = false;
		}
	});
	
	onDestroy(() => {
		Object.values(animationFrames).forEach(frame => {
			if (frame) cancelAnimationFrame(frame);
		});
	});
	
	function initializeQuantumArchitecture() {
		if (!data.source_intelligence) return;
		
		let sources = Object.entries(data.source_intelligence)
			.sort((a, b) => b[1] - a[1])
			.slice(0, 100);
		
		// Create architectural structures for each source
		sources.forEach(([source, count], i) => {
			// Create data tower structure
			let tower = {
				id: source,
				count: count,
				height: Math.log10(count + 1) * 50 + 20,
				x: (i % 10) * 100,
				z: Math.floor(i / 10) * 100,
				levels: Math.ceil(Math.log10(count + 1) * 10),
				dataFlow: Math.random(),
				packets: [],
				quantumState: 'STABLE',
				frequency: 100 + Math.random() * 900,
				pattern: generateDataPattern(count),
				nodes: generateDataNodes(count),
				connections: []
			};
			
			dataTowers.push(tower);
			sourceStructures.push(tower);
			
			// Create source profile
			sourceProfiles.set(source, generateSourceProfile(source, count));
		});
		
		// Create quantum layers
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
		
		// Initialize source DNA strands
		for (let i = 0; i < 3; i++) {
			sourceDNA.push({
				strand: i,
				sequence: generateDNASequence(sources.length),
				rotation: i * 120,
				twist: 0
			});
		}
	}
	
	function generateDataPattern(seed) {
		let pattern = [];
		for (let i = 0; i < 8; i++) {
			pattern.push({
				level: i,
				segments: Math.floor(3 + Math.random() * 5),
				rotation: Math.random() * 360,
				scale: 1 - (i * 0.1),
				type: ['DATA_CRYSTAL', 'NEURAL_GRID', 'QUANTUM_MESH', 'PLASMA_CORE'][Math.floor(Math.random() * 4)]
			});
		}
		return pattern;
	}
	
	function generateDataNodes(count) {
		let nodes = [];
		let nodeCount = Math.min(10, Math.floor(Math.log10(count + 1) * 3));
		for (let i = 0; i < nodeCount; i++) {
			nodes.push({
				id: `NODE_${i}`,
				size: Math.random() * count * 0.1,
				active: Math.random() > 0.2,
				resonance: Math.random()
			});
		}
		return nodes;
	}
	
	function generateSourceProfile(source, count) {
		return {
			quantumSignature: generateQuantumSignature(count),
			architecture: {
				complexity: Math.log10(count + 1) * 20,
				stability: 50 + Math.random() * 50,
				scalability: 50 + Math.random() * 50,
				throughput: 50 + Math.random() * 50,
				latency: 50 + Math.random() * 50
			},
			dataMatrix: {
				input: count * 0.1,
				output: count * 0.08,
				efficiency: 80 + Math.random() * 20,
				bandwidth: Math.random()
			},
			networkDimension: 1 + Math.random() * 2,
			quantumCoherence: Math.random(),
			sourceDNA: generateDNASequence(32)
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
		// Create mesh connections between towers
		dataTowers.forEach((tower, i) => {
			let connectionCount = Math.min(5, 2 + Math.floor(Math.random() * 4));
			for (let j = 0; j < connectionCount; j++) {
				let targetIdx = Math.floor(Math.random() * dataTowers.length);
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
			
			// Update network depth
			networkDepth = 3 + Math.sin(time * 0.2) * 2;
			
			// Update data integrity
			dataIntegrity = 70 + Math.sin(time * 0.4) * 20 + Math.random() * 10;
			
			// Update data towers
			dataTowers.forEach((tower, i) => {
				tower.dataFlow = 0.5 + Math.sin(time + i * 0.1) * 0.5;
				tower.frequency = 100 + Math.sin(time * 0.7 + i * 0.2) * 900;
				
				// Pulse effect for active towers
				if (Math.random() < 0.01) {
					tower.quantumState = ['STABLE', 'TRANSMITTING', 'PROCESSING', 'SYNCING'][Math.floor(Math.random() * 4)];
				}
				
				// Update nodes
				tower.nodes.forEach(node => {
					node.active = Math.random() > 0.3;
					node.resonance = Math.abs(Math.sin(time * 2 + Math.random()));
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
			sourceDNA.forEach(dna => {
				dna.twist += 1;
				dna.sequence.forEach(base => {
					base.energy = 0.5 + Math.sin(time * 4 + Math.random()) * 0.5;
				});
			});
			
			animationFrames.quantum = requestAnimationFrame(updateQuantumArchitecture);
		}
		
		updateQuantumArchitecture();
	}

	$: sources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = sources.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = sources.length > 0 ? Math.max(...sources.map(([,c]) => c)) : 1;
	$: minHosts = sources.length > 0 ? Math.min(...sources.map(([,c]) => c)) : 0;

	async function drillDownSource(source, count) {
		selectedSource = { source, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			sourceDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Source deep scan failed:', err);
			sourceDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedSource = null;
		sourceDetails = [];
	}
	
	function getSourceClass(count) {
		let normalized = (count - minHosts) / (maxHosts - minHosts || 1);
		let percentile = normalized * 100;
		
		if (percentile >= 85) {
			return {
				level: 'DATA_NEXUS',
				color: '#BD93F9',
				glow: '#BD93F940',
				symbol: '◈',
				description: 'Quantum Datacenter'
			};
		} else if (percentile >= 65) {
			return {
				level: 'STREAM_HUB',
				color: '#50FA7B',
				glow: '#50FA7B40',
				symbol: '◆',
				description: 'Neural Pipeline'
			};
		} else if (percentile >= 45) {
			return {
				level: 'CACHE_MATRIX',
				color: '#8BE9FD',
				glow: '#8BE9FD40',
				symbol: '▲',
				description: 'Data Repository'
			};
		} else if (percentile >= 25) {
			return {
				level: 'RELAY_NODE',
				color: '#F1FA8C',
				glow: '#F1FA8C40',
				symbol: '●',
				description: 'Transit Point'
			};
		} else {
			return {
				level: 'QUANTUM_SEED',
				color: '#FFB86C',
				glow: '#FFB86C40',
				symbol: '○',
				description: 'Emerging Source'
			};
		}
	}
	
	function formatNumber(num) {
		return new Intl.NumberFormat('en-US').format(num);
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
	
	<div class="source-architecture-interface">
		<!-- Architectural Header -->
		<header class="architectural-header">
			<div class="header-structure">
				<div class="structure-core">
					<!-- DNA Helix Visualization -->
					<div class="dna-helix" style="transform: rotateY({dimensionalShift}deg)">
						{#each sourceDNA as dna}
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
					<h1 class="architecture-title">SOURCE QUANTUM ARCHITECTURE</h1>
					<div class="structure-metrics">
						<div class="metric">
							<span class="metric-label">DATA INTEGRITY</span>
							<div class="integrity-bar">
								<div class="bar-fill" style="width: {dataIntegrity}%; 
															  background: linear-gradient(90deg, #BD93F9, #50FA7B)"></div>
							</div>
							<span class="metric-value">{dataIntegrity.toFixed(0)}%</span>
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
					   placeholder="SEARCH SOURCES..."
					   class="search-input"/>
				<div class="search-scan"></div>
			</div>
			
			<div class="header-analytics">
				<div class="analytic">
					<div class="analytic-value">{sources.length}</div>
					<div class="analytic-label">SOURCES</div>
				</div>
				<div class="analytic">
					<div class="analytic-value">{formatNumber(totalHosts)}</div>
					<div class="analytic-label">TOTAL HOSTS</div>
				</div>
				<div class="analytic">
					<div class="analytic-value">{networkDepth.toFixed(1)}</div>
					<div class="analytic-label">NETWORK DEPTH</div>
				</div>
			</div>
		</header>
		
		<!-- Main Content Layout -->
		<div class="content-layout">
			<!-- Left Panel: 3D Visualization -->
			<div class="visualization-panel">
				{#if loading && !selectedSource}
					<div class="architectural-loading">
						<div class="loading-structure">
							<div class="structure-beam beam-1"></div>
							<div class="structure-beam beam-2"></div>
							<div class="structure-beam beam-3"></div>
							<div class="structure-core-loading">◈</div>
						</div>
						<p class="loading-text">CONSTRUCTING SOURCE ARCHITECTURE...</p>
					</div>
				{:else if selectedSource}
					<div class="source-deep-analysis">
						<div class="analysis-header">
							<div class="source-hologram">
								<div class="hologram-tower">
									<div class="tower-core" style="background: {getSourceClass(selectedSource.count).color}">
										{getSourceClass(selectedSource.count).symbol}
									</div>
									<div class="tower-layers">
										{#each Array(5) as _, i}
											<div class="tower-layer" 
												 style="animation-delay: {i * 0.2}s; 
														border-color: {getSourceClass(selectedSource.count).color}"></div>
										{/each}
									</div>
								</div>
								<div class="source-identity">
									<h2>{selectedSource.source.toUpperCase()}</h2>
									<div class="quantum-signature">
										{sourceProfiles.get(selectedSource.source)?.quantumSignature || 'UNKNOWN'}
									</div>
								</div>
							</div>
							<button class="close-analysis" on:click={closeDetails}>
								<span>✕</span>
							</button>
						</div>
						
						{#if sourceProfiles.get(selectedSource.source)}
							{@const profile = sourceProfiles.get(selectedSource.source)}
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
																border-color: {getSourceClass(selectedSource.count).color}"></div>
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
																	  40,{25 + profile.architecture.scalability * 0.2} 
																	  60,{25 - profile.architecture.throughput * 0.2} 
																	  80,{25 + profile.architecture.latency * 0.2} 
																	  100,25"
															  stroke={getSourceClass(selectedSource.count).color}
															  stroke-width="2"
															  fill="none"/>
												</svg>
											</div>
											<div class="card-value">{profile.architecture.stability.toFixed(0)}%</div>
										</div>
									</div>
									<div class="analysis-card">
										<div class="card-label">DATA MATRIX</div>
										<div class="card-visual">
											<div class="data-flow">
												<div class="flow-in">IN: {profile.dataMatrix.input.toFixed(1)}</div>
												<div class="flow-converter">
													<div class="converter-efficiency">{profile.dataMatrix.efficiency.toFixed(0)}%</div>
												</div>
												<div class="flow-out">OUT: {profile.dataMatrix.output.toFixed(1)}</div>
											</div>
										</div>
									</div>
									<div class="analysis-card">
										<div class="card-label">NETWORK DIMENSION</div>
										<div class="card-visual">
											<div class="network-display">
												{profile.networkDimension.toFixed(2)}D
											</div>
										</div>
									</div>
								</div>
							</div>
						{/if}
						
						<div class="source-node-stream">
							<table class="nodes-table">
								<thead>
									<tr>
										<th>NODE_IDENTIFIER</th>
										<th>REGION</th>
										<th>COUNTRY</th>
										<th>DATACENTER</th>
										<th>INFRASTRUCTURE</th>
										<th>SYNC_STATUS</th>
										<th>SHIELD_STATUS</th>
									</tr>
								</thead>
								<tbody>
									{#each sourceDetails as host}
										<tr class="node-row">
											<td class="node-id">{host.host.substring(0, 35)}</td>
											<td>{host.region || 'UNASSIGNED'}</td>
											<td>{host.country || 'UNASSIGNED'}</td>
											<td>{host.data_center || 'UNKNOWN'}</td>
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
					<!-- 3D City Visualization -->
					<div class="city-visualization">
						<div class="towers-container" style="transform: rotateX(-30deg) rotateY({dimensionalShift}deg)">
							{#each dataTowers.slice(0, 50) as tower, i}
								{@const sourceClass = getSourceClass(tower.count)}
								<div class="tower-structure"
									 style="left: {tower.x}px;
											bottom: 0;
											transform: translateZ({tower.z}px);
											height: {tower.height}px"
									 on:click={() => drillDownSource(tower.id, tower.count)}>
									<div class="tower-body"
										 style="background: linear-gradient(180deg, {sourceClass.color}40, {sourceClass.color}10);
												border: 1px solid {sourceClass.color};
												box-shadow: 0 0 {tower.dataFlow * 30}px {sourceClass.glow}">
										{#each Array(Math.min(10, tower.levels)) as _, level}
											<div class="tower-level"
												 style="bottom: {level * 10}%;
														background: {tower.nodes[level]?.active ? sourceClass.color : 'transparent'};
														opacity: {tower.nodes[level]?.resonance || 0.2}">
											</div>
										{/each}
										<div class="tower-label">{tower.id.substring(0, 10)}</div>
										<div class="tower-beacon"
											 style="background: {sourceClass.color};
													box-shadow: 0 0 {20 + tower.dataFlow * 20}px {sourceClass.color}">
										</div>
									</div>
								</div>
							{/each}
							
							<!-- Energy Connections -->
							<svg class="connection-mesh" viewBox="0 0 1000 1000">
								{#each connectionMesh as connection}
									{#if dataTowers[connection.source] && dataTowers[connection.target]}
										<line x1="{dataTowers[connection.source].x}"
											  y1="{1000 - dataTowers[connection.source].z}"
											  x2="{dataTowers[connection.target].x}"
											  y2="{1000 - dataTowers[connection.target].z}"
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
						
						<!-- Hierarchical Tree Overlay -->
						<div class="tree-overlay">
							<div class="tree-root">
								<div class="root-node">
									<div class="node-icon">◈</div>
									<div class="node-label">SOURCE TABLES</div>
									<div class="node-count">{formatNumber(totalHosts)} HOSTS</div>
								</div>
							</div>
						</div>
					</div>
				{/if}
			</div>
			
			<!-- Middle: Analytics Dashboard -->
			<div class="analytics-panel">
				<!-- Distribution Chart -->
				<div class="chart-box">
					<h3>HOST DISTRIBUTION</h3>
					<div class="distribution-chart">
						{#each sources.slice(0, 5) as [source, count], i}
							{@const sourceClass = getSourceClass(count)}
							<div class="dist-item" on:click={() => drillDownSource(source, count)}>
								<div class="dist-header">
									<span class="dist-rank" style="color: {sourceClass.color}">#{i + 1}</span>
									<span class="dist-name">{source.substring(0, 15).toUpperCase()}</span>
								</div>
								<div class="dist-bar">
									<div class="dist-fill" 
										 style="width: {(count / maxHosts) * 100}%; 
												background: linear-gradient(90deg, transparent, {sourceClass.color})">
									</div>
								</div>
								<div class="dist-footer">
									<span class="dist-value" style="color: {sourceClass.color}">{formatNumber(count)}</span>
									<span class="dist-percent">{((count/totalHosts)*100).toFixed(1)}%</span>
								</div>
							</div>
						{/each}
					</div>
				</div>
				
				<!-- Quantum Metrics -->
				<div class="chart-box">
					<h3>SOURCE METRICS</h3>
					<div class="metrics-grid">
						<div class="metric-item">
							<div class="metric-icon-small">⬢</div>
							<div class="metric-detail">
								<div class="metric-value-small" style="color: #BD93F9">
									{sources.filter(([_, c]) => c > 10000).length}
								</div>
								<div class="metric-label-small">MASSIVE SOURCES</div>
							</div>
						</div>
						<div class="metric-item">
							<div class="metric-icon-small">◆</div>
							<div class="metric-detail">
								<div class="metric-value-small" style="color: #50FA7B">
									{sources.filter(([_, c]) => c > 5000).length}
								</div>
								<div class="metric-label-small">LARGE SOURCES</div>
							</div>
						</div>
						<div class="metric-item">
							<div class="metric-icon-small">▲</div>
							<div class="metric-detail">
								<div class="metric-value-small" style="color: #8BE9FD">
									{sources.filter(([_, c]) => c > 1000).length}
								</div>
								<div class="metric-label-small">MEDIUM SOURCES</div>
							</div>
						</div>
						<div class="metric-item">
							<div class="metric-icon-small">●</div>
							<div class="metric-detail">
								<div class="metric-value-small" style="color: #FFB86C">
									{Math.round(totalHosts / sources.length) || 0}
								</div>
								<div class="metric-label-small">AVG HOSTS/SOURCE</div>
							</div>
						</div>
					</div>
				</div>
			</div>
			
			<!-- Right: Source Matrix -->
			<div class="source-matrix">
				<table class="matrix-table">
					<thead>
						<tr>
							<th>RANK</th>
							<th>SOURCE_ID</th>
							<th>ARCHITECTURE</th>
							<th>HOSTS</th>
							<th>BANDWIDTH</th>
							<th>COHERENCE</th>
						</tr>
					</thead>
					<tbody>
						{#each sources as [source, count], index}
							{@const sourceClass = getSourceClass(count)}
							{@const profile = sourceProfiles.get(source)}
							<tr class="matrix-row"
								style="border-left: 3px solid {sourceClass.color}"
								on:click={() => drillDownSource(source, count)}>
								<td class="rank-cell">
									<span style="color: {sourceClass.color}">#{index + 1}</span>
								</td>
								<td class="source-cell">
									<span class="source-symbol" style="color: {sourceClass.color}">
										{sourceClass.symbol}
									</span>
									<span class="source-name">{source.substring(0, 20).toUpperCase()}</span>
								</td>
								<td>
									<span class="architecture-badge"
										  style="background: {sourceClass.glow};
												 color: {sourceClass.color};
												 border: 1px solid {sourceClass.color}">
										{sourceClass.level}
									</span>
								</td>
								<td class="numeric">{formatNumber(count)}</td>
								<td>
									<div class="bandwidth-meter">
										<div class="bandwidth-level"
											 style="width: {profile ? profile.dataMatrix.efficiency : 0}%;
													background: linear-gradient(90deg, transparent, {sourceClass.color})">
										</div>
									</div>
								</td>
								<td>
									<div class="coherence-display">
										{profile ? profile.quantumCoherence.toFixed(2) : '0.00'}
									</div>
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
	
	.source-architecture-interface {
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
	
	/* Content Layout */
	.content-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 380px 400px;
		gap: 2rem;
		padding: 2rem;
		min-height: 0;
	}
	
	/* Visualization Panel */
	.visualization-panel {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 20px;
		backdrop-filter: blur(10px);
		overflow: hidden;
		position: relative;
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
	
	/* City Visualization */
	.city-visualization {
		position: relative;
		width: 100%;
		height: 100%;
		background: radial-gradient(circle at center, rgba(189, 147, 249, 0.02), transparent);
		perspective: 1000px;
	}
	
	.towers-container {
		position: absolute;
		width: 90%;
		height: 90%;
		top: 5%;
		left: 5%;
		transform-style: preserve-3d;
		transition: transform 0.5s ease;
	}
	
	.tower-structure {
		position: absolute;
		width: 60px;
		cursor: pointer;
		transform-style: preserve-3d;
		transition: all 0.3s ease;
	}
	
	.tower-structure:hover {
		transform: translateZ(20px) scale(1.1);
		z-index: 10;
	}
	
	.tower-body {
		width: 100%;
		height: 100%;
		position: relative;
		transform-style: preserve-3d;
	}
	
	.tower-level {
		position: absolute;
		width: 100%;
		height: 2px;
		left: 0;
	}
	
	.tower-label {
		position: absolute;
		bottom: -20px;
		left: 50%;
		transform: translateX(-50%);
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		white-space: nowrap;
	}
	
	.tower-beacon {
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
	
	/* Tree Overlay */
	.tree-overlay {
		position: absolute;
		bottom: 20px;
		left: 50%;
		transform: translateX(-50%);
		pointer-events: none;
	}
	
	.tree-root {
		display: flex;
		justify-content: center;
	}
	
	.root-node {
		background: rgba(189, 147, 249, 0.1);
		border: 2px solid #BD93F9;
		border-radius: 10px;
		padding: 1rem 2rem;
		text-align: center;
		backdrop-filter: blur(10px);
	}
	
	.node-icon {
		font-size: 2rem;
		color: #BD93F9;
		margin-bottom: 0.5rem;
	}
	
	.node-label {
		font-size: 0.8rem;
		color: #BD93F9;
		font-weight: 600;
		letter-spacing: 0.1em;
	}
	
	.node-count {
		font-size: 1rem;
		color: #FFFFFF;
		font-weight: 700;
		margin-top: 0.25rem;
	}
	
	/* Analytics Panel */
	.analytics-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chart-box {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 15px;
		padding: 1.5rem;
		backdrop-filter: blur(10px);
	}
	
	.chart-box h3 {
		margin: 0 0 1rem 0;
		font-size: 0.8rem;
		color: #8BE9FD;
		font-weight: 300;
		letter-spacing: 0.2em;
	}
	
	.distribution-chart {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.dist-item {
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	.dist-item:hover {
		transform: translateX(5px);
	}
	
	.dist-header {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.25rem;
		align-items: center;
	}
	
	.dist-rank {
		font-size: 0.7rem;
		font-weight: 600;
		font-family: 'Courier New', monospace;
	}
	
	.dist-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
		letter-spacing: 0.05em;
	}
	
	.dist-bar {
		height: 20px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 5px;
		overflow: hidden;
		margin-bottom: 0.25rem;
	}
	
	.dist-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.dist-footer {
		display: flex;
		justify-content: space-between;
		font-size: 0.65rem;
	}
	
	.dist-value {
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.dist-percent {
		color: rgba(255, 255, 255, 0.5);
	}
	
	/* Metrics Grid */
	.metrics-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}
	
	.metric-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem;
		background: rgba(189, 147, 249, 0.05);
		border-radius: 8px;
		border: 1px solid rgba(189, 147, 249, 0.2);
	}
	
	.metric-icon-small {
		font-size: 1.5rem;
	}
	
	.metric-detail {
		flex: 1;
	}
	
	.metric-value-small {
		font-size: 1.2rem;
		font-weight: 600;
		font-family: 'Courier New', monospace;
	}
	
	.metric-label-small {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
		margin-top: 0.1rem;
	}
	
	/* Source Matrix */
	.source-matrix {
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
		font-size: 0.65rem;
		font-weight: 300;
		letter-spacing: 0.15em;
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
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank-cell {
		font-weight: 600;
		font-family: 'Courier New', monospace;
	}
	
	.source-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.source-symbol {
		font-size: 1rem;
	}
	
	.source-name {
		font-weight: 300;
		letter-spacing: 0.02em;
		font-size: 0.7rem;
	}
	
	.architecture-badge {
		display: inline-block;
		padding: 0.25rem 0.5rem;
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		border-radius: 4px;
	}
	
	.numeric {
		font-family: 'Courier New', monospace;
		color: #50FA7B;
		font-weight: 600;
	}
	
	.bandwidth-meter {
		width: 60px;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		overflow: hidden;
		border-radius: 2px;
	}
	
	.bandwidth-level {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.coherence-display {
		font-family: 'Courier New', monospace;
		font-size: 0.7rem;
		color: #8BE9FD;
	}
	
	/* Source Deep Analysis */
	.source-deep-analysis {
		height: 100%;
		display: flex;
		flex-direction: column;
		padding: 2rem;
	}
	
	.analysis-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-bottom: 1.5rem;
		border-bottom: 1px solid rgba(189, 147, 249, 0.2);
		margin-bottom: 1.5rem;
	}
	
	.source-hologram {
		display: flex;
		align-items: center;
		gap: 2rem;
	}
	
	.hologram-tower {
		position: relative;
		width: 100px;
		height: 100px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.tower-core {
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
	
	.tower-layers {
		position: absolute;
		inset: -20px;
	}
	
	.tower-layer {
		position: absolute;
		border: 1px solid;
		border-radius: 10px;
		animation: layerFloat 3s ease-in-out infinite;
	}
	
	.tower-layer:nth-child(1) { inset: 0; }
	.tower-layer:nth-child(2) { inset: 5px; }
	.tower-layer:nth-child(3) { inset: 10px; }
	.tower-layer:nth-child(4) { inset: 15px; }
	.tower-layer:nth-child(5) { inset: 20px; }
	
	@keyframes layerFloat {
		0%, 100% { transform: scale(1) rotateZ(0deg); opacity: 0.3; }
		50% { transform: scale(1.05) rotateZ(5deg); opacity: 0.6; }
	}
	
	.source-identity {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.source-identity h2 {
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
		margin-bottom: 1.5rem;
	}
	
	.analysis-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
	}
	
	.analysis-card {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(189, 147, 249, 0.2);
		border-radius: 10px;
		padding: 1rem;
		text-align: center;
	}
	
	.card-label {
		font-size: 0.65rem;
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
	
	.data-flow {
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
	
	.network-display {
		font-size: 1.5rem;
		font-weight: 600;
		color: #8BE9FD;
		text-shadow: 0 0 20px rgba(139, 233, 253, 0.5);
		font-family: 'Courier New', monospace;
	}
	
	/* Source Node Stream */
	.source-node-stream {
		flex: 1;
		overflow: auto;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 10px;
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
		font-size: 0.65rem;
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
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.node-id {
		font-family: 'Courier New', monospace;
		color: #BD93F9;
		font-size: 0.65rem;
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
		.content-layout {
			grid-template-columns: 1fr 300px;
			grid-template-rows: auto 1fr;
		}
		
		.source-matrix {
			grid-column: 1 / -1;
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
		
		.content-layout {
			grid-template-columns: 1fr;
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