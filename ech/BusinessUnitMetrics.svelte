<!-- BusinessUnitMetrics.svelte - Quantum Division Matrix Interface -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedDivision = null;
	let divisionDetails = [];
	let searchTerm = '';
	
	// Visualization states
	let viewMode = 'constellation'; // 'constellation', 'flow', 'hexgrid', 'pulse'
	let divisionNodes = [];
	let dataFlows = [];
	let hexGrid = [];
	let particleSystem = [];
	let quantumState = 'INITIALIZING';
	let networkMatrix = [];
	let energyLevel = 0;
	let dataStreamVolume = 0;
	let flowField = [];
	
	// Animation references
	let animationFrameId;
	let intervals = [];
	
	// Neon pastel color scheme
	const neonColors = {
		primary: '#00FFAA',     // Mint Green
		secondary: '#FF00AA',    // Hot Magenta
		tertiary: '#AAFF00',     // Lime
		quaternary: '#AA00FF',   // Purple
		accent1: '#00AAFF',      // Sky Blue
		accent2: '#FFAA00',      // Gold
		accent3: '#FF00FF',      // Pure Magenta
		danger: '#FF0055',       // Red Pink
		warning: '#FFAA55',      // Orange
		success: '#00FF55'       // Green
	};
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/business_unit_metrics');
			let result = await response.json();
			data = result;
			loading = false;
			quantumState = 'SYNCHRONIZED';
			initializeVisualization();
			startAnimations();
		} catch (err) {
			console.error('Division matrix sync failed:', err);
			loading = false;
			quantumState = 'DESYNCHRONIZED';
		}
	});
	
	onDestroy(() => {
		if (animationFrameId) cancelAnimationFrame(animationFrameId);
		intervals.forEach(interval => clearInterval(interval));
	});
	
	function initializeVisualization() {
		if (!data.business_intelligence) return;
		
		// Create division nodes
		let divisions = Object.entries(data.business_intelligence);
		let maxCount = Math.max(...divisions.map(([,c]) => c));
		
		// Create constellation nodes
		divisions.forEach(([division, count], i) => {
			let importance = count / maxCount;
			
			// 3D sphere distribution
			let phi = Math.acos(-1 + (2 * i) / divisions.length);
			let theta = Math.sqrt(divisions.length * Math.PI) * phi;
			
			divisionNodes.push({
				id: i,
				name: division,
				count: count,
				importance: importance,
				x: Math.cos(theta) * Math.sin(phi) * 200,
				y: Math.sin(theta) * Math.sin(phi) * 200,
				z: Math.cos(phi) * 200,
				rotationSpeed: 0.5 + Math.random() * 0.5,
				pulsePhase: Math.random() * Math.PI * 2,
				color: interpolateNeonColor(importance),
				connections: [],
				dataFlow: Math.random() * 100,
				energy: importance * 100
			});
		});
		
		// Create data flow connections
		divisionNodes.forEach((node, i) => {
			// Connect to nearby nodes based on importance similarity
			divisionNodes.forEach((target, j) => {
				if (i !== j) {
					let distance = Math.sqrt(
						Math.pow(node.x - target.x, 2) + 
						Math.pow(node.y - target.y, 2) + 
						Math.pow(node.z - target.z, 2)
					);
					if (distance < 150 || Math.random() > 0.8) {
						dataFlows.push({
							source: i,
							target: j,
							strength: 1 / (distance / 100),
							particles: [],
							flowRate: Math.random() * 10 + 5
						});
					}
				}
			});
		});
		
		// Initialize hexagonal grid
		let gridSize = 10;
		for (let q = -gridSize; q <= gridSize; q++) {
			for (let r = -gridSize; r <= gridSize; r++) {
				if (Math.abs(q + r) <= gridSize) {
					hexGrid.push({
						q: q,
						r: r,
						x: q * 1.5 * 30,
						y: (q * 0.5 + r) * Math.sqrt(3) * 30,
						active: Math.random() > 0.3,
						energy: Math.random() * 100,
						divisionIndex: Math.floor(Math.random() * divisions.length),
						pulse: Math.random() * Math.PI * 2
					});
				}
			}
		}
		
		// Initialize particle system
		for (let i = 0; i < 300; i++) {
			particleSystem.push({
				x: Math.random() * window.innerWidth,
				y: Math.random() * window.innerHeight,
				z: Math.random() * 200 - 100,
				vx: (Math.random() - 0.5) * 1,
				vy: (Math.random() - 0.5) * 1,
				vz: (Math.random() - 0.5) * 0.5,
				size: Math.random() * 3 + 0.5,
				color: Object.values(neonColors)[Math.floor(Math.random() * 10)],
				life: Math.random() * 100,
				type: ['data', 'energy', 'quantum'][Math.floor(Math.random() * 3)]
			});
		}
		
		// Initialize flow field
		let fieldSize = 20;
		for (let i = 0; i < fieldSize; i++) {
			flowField.push([]);
			for (let j = 0; j < fieldSize; j++) {
				flowField[i].push({
					angle: Math.random() * Math.PI * 2,
					magnitude: Math.random() * 5,
					vorticity: (Math.random() - 0.5) * 0.1
				});
			}
		}
		
		// Create data flow particles
		dataFlows.forEach(flow => {
			for (let i = 0; i < flow.flowRate; i++) {
				flow.particles.push({
					progress: Math.random(),
					speed: 0.005 + Math.random() * 0.01,
					size: Math.random() * 3 + 1,
					glow: Math.random() * 0.5 + 0.5
				});
			}
		});
	}
	
	function interpolateNeonColor(value) {
		if (value > 0.8) return neonColors.primary;
		if (value > 0.6) return neonColors.secondary;
		if (value > 0.4) return neonColors.tertiary;
		if (value > 0.2) return neonColors.quaternary;
		return neonColors.accent1;
	}
	
	function startAnimations() {
		// Main animation loop
		function animate() {
			updateParticles();
			updateDataFlows();
			updateHexGrid();
			updateFlowField();
			energyLevel = 50 + Math.sin(Date.now() * 0.001) * 50;
			dataStreamVolume = 50 + Math.sin(Date.now() * 0.0007) * 50;
			animationFrameId = requestAnimationFrame(animate);
		}
		animate();
		
		// Quantum state updates
		intervals.push(setInterval(() => {
			quantumState = ['SYNCHRONIZED', 'PROCESSING', 'ANALYZING', 'OPTIMIZING', 'CORRELATING'][
				Math.floor(Math.random() * 5)
			];
		}, 3000));
		
		// Network matrix updates
		intervals.push(setInterval(() => {
			networkMatrix = divisionNodes.map(node => ({
				...node,
				dataFlow: Math.max(0, Math.min(100, node.dataFlow + (Math.random() - 0.5) * 20)),
				energy: Math.max(0, Math.min(100, node.energy + (Math.random() - 0.5) * 10))
			}));
		}, 100));
	}
	
	function updateParticles() {
		particleSystem = particleSystem.map(p => {
			// Apply flow field forces
			let fieldX = Math.floor(p.x / window.innerWidth * 20);
			let fieldY = Math.floor(p.y / window.innerHeight * 20);
			if (flowField[fieldY] && flowField[fieldY][fieldX]) {
				let field = flowField[fieldY][fieldX];
				p.vx += Math.cos(field.angle) * field.magnitude * 0.01;
				p.vy += Math.sin(field.angle) * field.magnitude * 0.01;
			}
			
			// Update position
			p.x = (p.x + p.vx + window.innerWidth) % window.innerWidth;
			p.y = (p.y + p.vy + window.innerHeight) % window.innerHeight;
			p.z = (p.z + p.vz + 200) % 200 - 100;
			p.life = (p.life + 1) % 100;
			
			// Apply damping
			p.vx *= 0.99;
			p.vy *= 0.99;
			p.vz *= 0.99;
			
			return p;
		});
	}
	
	function updateDataFlows() {
		dataFlows.forEach(flow => {
			flow.particles = flow.particles.map(particle => ({
				...particle,
				progress: (particle.progress + particle.speed) % 1
			}));
		});
	}
	
	function updateHexGrid() {
		hexGrid = hexGrid.map(hex => ({
			...hex,
			pulse: hex.pulse + 0.05,
			energy: hex.active ? 50 + Math.sin(hex.pulse) * 50 : 0
		}));
	}
	
	function updateFlowField() {
		flowField = flowField.map(row => 
			row.map(cell => ({
				...cell,
				angle: cell.angle + cell.vorticity,
				magnitude: 2 + Math.sin(Date.now() * 0.001 + cell.angle) * 3
			}))
		);
	}
	
	$: filteredDivisions = data.business_intelligence ? 
		Object.entries(data.business_intelligence)
			.filter(([division]) => division.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredDivisions.length > 0 ? 
		Math.max(...filteredDivisions.map(([,c]) => c)) : 1;
	
	function calculateMetrics(count) {
		let normalized = count / maxCount;
		let percentile = normalized * 100;
		
		return {
			percentile: percentile.toFixed(1),
			powerLevel: (normalized * 100).toFixed(0),
			networkReach: (count * 0.01).toFixed(2),
			dataNodes: count,
			throughput: (normalized * 1000).toFixed(0),
			latency: (10 / (normalized + 0.1)).toFixed(1),
			efficiency: (70 + normalized * 30).toFixed(0),
			quantumSignature: generateQuantumSignature(count),
			color: interpolateNeonColor(normalized)
		};
	}
	
	function generateQuantumSignature(seed) {
		let sig = '';
		let chars = '0123456789ABCDEF';
		for (let i = 0; i < 16; i++) {
			sig += chars[(seed * (i + 1) * 997) % 16];
			if (i % 4 === 3 && i < 15) sig += ':';
		}
		return sig;
	}
	
	function getPercentage(count) {
		let total = Object.values(data.business_intelligence || {}).reduce((a, b) => a + b, 0);
		return total > 0 ? ((count / total) * 100).toFixed(2) : '0.00';
	}
	
	async function drillDownDivision(division, count) {
		selectedDivision = { division, count };
		loading = true;
		quantumState = 'DEEP_SCANNING';
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(division)}`);
			let result = await response.json();
			divisionDetails = result.hosts || [];
			loading = false;
			quantumState = 'SYNCHRONIZED';
		} catch (err) {
			console.error('Division deep scan failed:', err);
			divisionDetails = [];
			loading = false;
			quantumState = 'ERROR';
		}
	}
	
	function closeDetails() {
		selectedDivision = null;
		divisionDetails = [];
		quantumState = 'SYNCHRONIZED';
	}
	
	// 3D rotation for constellation view
	let rotationX = 0;
	let rotationY = 0;
	let isDragging = false;
	let lastMouseX = 0;
	let lastMouseY = 0;
	
	function handleMouseDown(e) {
		if (viewMode === 'constellation') {
			isDragging = true;
			lastMouseX = e.clientX;
			lastMouseY = e.clientY;
		}
	}
	
	function handleMouseMove(e) {
		if (isDragging && viewMode === 'constellation') {
			rotationY += (e.clientX - lastMouseX) * 0.5;
			rotationX += (e.clientY - lastMouseY) * 0.5;
			lastMouseX = e.clientX;
			lastMouseY = e.clientY;
		}
	}
	
	function handleMouseUp() {
		isDragging = false;
	}
</script>

<svelte:window 
	on:mousemove={handleMouseMove}
	on:mouseup={handleMouseUp}
/>

<div class="quantum-division-interface">
	<!-- Particle System Background -->
	<div class="particle-field">
		{#each particleSystem as particle}
			<div class="quantum-particle"
				 style="left: {particle.x}px;
						top: {particle.y}px;
						width: {particle.size}px;
						height: {particle.size}px;
						background: {particle.color};
						opacity: {0.3 + (particle.life / 100) * 0.5};
						transform: translateZ({particle.z}px);
						box-shadow: 0 0 {particle.glow * 10}px {particle.color}">
			</div>
		{/each}
	</div>
	
	<!-- Flow Field Visualization -->
	<svg class="flow-field-layer">
		<defs>
			<linearGradient id="flowGradient" x1="0%" y1="0%" x2="100%" y2="100%">
				<stop offset="0%" style="stop-color:{neonColors.primary};stop-opacity:0" />
				<stop offset="50%" style="stop-color:{neonColors.secondary};stop-opacity:0.5" />
				<stop offset="100%" style="stop-color:{neonColors.tertiary};stop-opacity:0" />
			</linearGradient>
			<filter id="divisionGlow">
				<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
				<feMerge>
					<feMergeNode in="coloredBlur"/>
					<feMergeNode in="SourceGraphic"/>
				</feMerge>
			</filter>
		</defs>
		
		{#each flowField as row, i}
			{#each row as cell, j}
				<line x1="{j * 5}%" y1="{i * 5}%"
					  x2="{j * 5 + Math.cos(cell.angle) * 2}%"
					  y2="{i * 5 + Math.sin(cell.angle) * 2}%"
					  stroke="url(#flowGradient)"
					  stroke-width="0.5"
					  opacity="{0.1 + cell.magnitude / 10}"/>
			{/each}
		{/each}
	</svg>
	
	<div class="division-container">
		<!-- Quantum Header -->
		<header class="quantum-header">
			<div class="header-layout">
				<div class="brand-area">
					<div class="quantum-emblem">
						<div class="emblem-structure">
							<div class="emblem-layer layer-1" style="border-color: {neonColors.primary}; transform: rotate({energyLevel * 2}deg)"></div>
							<div class="emblem-layer layer-2" style="border-color: {neonColors.secondary}; transform: rotate({-energyLevel * 1.5}deg)"></div>
							<div class="emblem-layer layer-3" style="border-color: {neonColors.tertiary}; transform: rotate({energyLevel}deg)"></div>
							<div class="emblem-core">
								<span class="core-glyph">⬢</span>
							</div>
						</div>
					</div>
					<div class="brand-info">
						<h1 class="interface-title" data-text="DIVISION QUANTUM MATRIX">
							DIVISION QUANTUM MATRIX
						</h1>
						<div class="system-status">
							<span class="status-indicator" style="background: {quantumState === 'ERROR' ? neonColors.danger : neonColors.success}"></span>
							<span class="status-label">STATE: {quantumState}</span>
							<span class="separator">•</span>
							<span class="energy-label">ENERGY: {energyLevel.toFixed(0)}%</span>
							<span class="separator">•</span>
							<span class="volume-label">VOLUME: {dataStreamVolume.toFixed(0)}%</span>
						</div>
					</div>
				</div>
				
				<div class="control-area">
					<div class="search-module">
						<input 
							type="text" 
							bind:value={searchTerm}
							placeholder="QUANTUM SEARCH..."
							class="quantum-input"
						/>
						<div class="search-scanner" style="width: {searchTerm ? '100%' : '0'}"></div>
					</div>
					
					<div class="view-selector">
						<button class="view-btn {viewMode === 'constellation' ? 'active' : ''}"
								on:click={() => viewMode = 'constellation'}
								style="--btn-color: {neonColors.primary}">
							<span class="btn-icon">✦</span>
							<span class="btn-label">CONSTELLATION</span>
						</button>
						<button class="view-btn {viewMode === 'flow' ? 'active' : ''}"
								on:click={() => viewMode = 'flow'}
								style="--btn-color: {neonColors.secondary}">
							<span class="btn-icon">◈</span>
							<span class="btn-label">FLOW</span>
						</button>
						<button class="view-btn {viewMode === 'hexgrid' ? 'active' : ''}"
								on:click={() => viewMode = 'hexgrid'}
								style="--btn-color: {neonColors.tertiary}">
							<span class="btn-icon">⬢</span>
							<span class="btn-label">HEXGRID</span>
						</button>
						<button class="view-btn {viewMode === 'pulse' ? 'active' : ''}"
								on:click={() => viewMode = 'pulse'}
								style="--btn-color: {neonColors.quaternary}">
							<span class="btn-icon">◉</span>
							<span class="btn-label">PULSE</span>
						</button>
					</div>
				</div>
				
				<div class="metrics-area">
					<div class="metric-block">
						<div class="metric-number" style="color: {neonColors.primary}">
							{filteredDivisions.length}
						</div>
						<div class="metric-text">DIVISIONS</div>
					</div>
					<div class="metric-block">
						<div class="metric-number" style="color: {neonColors.secondary}">
							{Object.values(data.business_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}
						</div>
						<div class="metric-text">NODES</div>
					</div>
				</div>
			</div>
		</header>
		
		<!-- Main Interface -->
		<div class="interface-viewport">
			{#if loading && !selectedDivision}
				<div class="loading-interface">
					<div class="loading-quantum">
						<div class="quantum-ring" style="border-color: {neonColors.primary}"></div>
						<div class="quantum-ring" style="border-color: {neonColors.secondary}; animation-delay: 0.3s"></div>
						<div class="quantum-ring" style="border-color: {neonColors.tertiary}; animation-delay: 0.6s"></div>
						<div class="quantum-center">⬢</div>
					</div>
					<p class="loading-message">SYNCHRONIZING DIVISION MATRIX...</p>
				</div>
			{:else if selectedDivision}
				<!-- Detail View -->
				<div class="division-detail-view">
					<div class="detail-header">
						<div class="division-profile">
							<div class="profile-avatar" style="border-color: {calculateMetrics(selectedDivision.count).color}">
								<div class="avatar-layers">
									<div class="layer" style="border-color: {neonColors.primary}"></div>
									<div class="layer" style="border-color: {neonColors.secondary}"></div>
								</div>
								<div class="avatar-symbol">⬢</div>
							</div>
							<div class="profile-data">
								<h2 class="division-name">{selectedDivision.division.toUpperCase()}</h2>
								<div class="division-signature">
									{calculateMetrics(selectedDivision.count).quantumSignature}
								</div>
								<div class="division-badges">
									<span class="badge" style="background: {neonColors.primary}20; color: {neonColors.primary}">
										POWER: {calculateMetrics(selectedDivision.count).powerLevel}%
									</span>
									<span class="badge" style="background: {neonColors.secondary}20; color: {neonColors.secondary}">
										EFFICIENCY: {calculateMetrics(selectedDivision.count).efficiency}%
									</span>
									<span class="badge" style="background: {neonColors.tertiary}20; color: {neonColors.tertiary}">
										THROUGHPUT: {calculateMetrics(selectedDivision.count).throughput}MB/s
									</span>
								</div>
							</div>
						</div>
						<button class="close-button" on:click={closeDetails}>
							<span>✕</span>
						</button>
					</div>
					
					<div class="detail-grid">
						{#each [
							{ icon: '⬢', label: 'NODES', value: selectedDivision.count.toLocaleString(), color: neonColors.primary },
							{ icon: '◈', label: 'NETWORK', value: getPercentage(selectedDivision.count) + '%', color: neonColors.secondary },
							{ icon: '✦', label: 'LATENCY', value: calculateMetrics(selectedDivision.count).latency + 'ms', color: neonColors.tertiary },
							{ icon: '◉', label: 'REACH', value: calculateMetrics(selectedDivision.count).networkReach + 'K', color: neonColors.quaternary }
						] as metric}
							<div class="detail-metric">
								<div class="metric-icon" style="color: {metric.color}">{metric.icon}</div>
								<div class="metric-content">
									<div class="metric-value" style="color: {metric.color}">{metric.value}</div>
									<div class="metric-label">{metric.label}</div>
								</div>
								<div class="metric-graph">
									<svg viewBox="0 0 100 30">
										<polyline points="{Array(20).fill(0).map((_, i) => `${i * 5},${30 - Math.random() * 30}`).join(' ')}"
												  fill="none" stroke="{metric.color}" stroke-width="1" opacity="0.6"/>
									</svg>
								</div>
							</div>
						{/each}
					</div>
					
					<div class="detail-data">
						<div class="data-header">
							<h3>DIVISION DATA STREAM</h3>
							<div class="data-status">
								<span class="status-live">LIVE</span>
								<span class="status-dot"></span>
							</div>
						</div>
						<div class="data-table-container">
							<table class="data-table">
								<thead>
									<tr>
										<th>NODE_ID</th>
										<th>SECTOR</th>
										<th>REGION</th>
										<th>INFRASTRUCTURE</th>
										<th>CMDB_SYNC</th>
										<th>TANIUM_SHIELD</th>
									</tr>
								</thead>
								<tbody>
									{#each divisionDetails as host}
										<tr class="table-row">
											<td class="node-id">{host.host.substring(0, 30)}</td>
											<td>{host.country || 'UNKNOWN'}</td>
											<td>{host.region || 'UNKNOWN'}</td>
											<td>{host.infrastructure_type || 'UNKNOWN'}</td>
											<td>
												<span class="status {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}"
													  style="color: {host.present_in_cmdb?.toLowerCase().includes('yes') ? neonColors.success : neonColors.danger}">
													{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}
												</span>
											</td>
											<td>
												<span class="status {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'secured' : 'exposed'}"
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
			{:else if viewMode === 'constellation'}
				<!-- Constellation View -->
				<div class="constellation-view" on:mousedown={handleMouseDown}>
					<div class="constellation-container" 
						 style="transform: rotateX({rotationX}deg) rotateY({rotationY}deg)">
						<svg class="constellation-svg" viewBox="-400 -400 800 800">
							<!-- Data Flows -->
							{#each dataFlows as flow}
								{#if divisionNodes[flow.source] && divisionNodes[flow.target]}
									<line x1="{divisionNodes[flow.source].x}"
										  y1="{divisionNodes[flow.source].y}"
										  x2="{divisionNodes[flow.target].x}"
										  y2="{divisionNodes[flow.target].y}"
										  stroke="{neonColors.primary}"
										  stroke-width="{0.5 + flow.strength * 0.5}"
										  opacity="{0.1 + flow.strength * 0.2}">
										<animate attributeName="stroke-opacity"
												 values="0.1;0.3;0.1"
												 dur="{3 / flow.flowRate}s"
												 repeatCount="indefinite"/>
									</line>
									
									<!-- Flow Particles -->
									{#each flow.particles as particle}
										{@const x = divisionNodes[flow.source].x + (divisionNodes[flow.target].x - divisionNodes[flow.source].x) * particle.progress}
										{@const y = divisionNodes[flow.source].y + (divisionNodes[flow.target].y - divisionNodes[flow.source].y) * particle.progress}
										<circle cx="{x}" cy="{y}" r="{particle.size}"
												fill="{neonColors.accent1}"
												opacity="{particle.glow}"
												filter="url(#divisionGlow)"/>
									{/each}
								{/if}
							{/each}
							
							<!-- Division Nodes -->
							{#each divisionNodes as node}
								<g class="division-node"
								   transform="translate({node.x}, {node.y})"
								   on:click={() => drillDownDivision(node.name, node.count)}>
									<!-- Outer glow -->
									<circle r="{15 + node.importance * 25}"
											fill="{node.color}"
											opacity="0.1"/>
									<!-- Middle ring -->
									<circle r="{10 + node.importance * 15}"
											fill="none"
											stroke="{node.color}"
											stroke-width="1"
											opacity="0.5">
										<animate attributeName="r"
												 values="{10 + node.importance * 15};{12 + node.importance * 15};{10 + node.importance * 15}"
												 dur="{2 + node.importance}s"
												 repeatCount="indefinite"/>
									</circle>
									<!-- Core -->
									<circle r="{5 + node.importance * 10}"
											fill="{node.color}"
											opacity="0.8"/>
									<!-- Label -->
									<text y="-{20 + node.importance * 25}"
										  text-anchor="middle"
										  fill="#ffffff"
										  font-size="10"
										  opacity="0.9">
										{node.name.substring(0, 20)}
									</text>
									<!-- Value -->
									<text y="4"
										  text-anchor="middle"
										  fill="{node.color}"
										  font-size="8"
										  font-weight="bold">
										{node.count}
									</text>
								</g>
							{/each}
							
							<!-- Central Nexus -->
							<g transform="translate(0, 0)">
								<circle r="40" fill="none" stroke="{neonColors.primary}" stroke-width="0.5" opacity="0.3">
									<animate attributeName="r" values="40;45;40" dur="3s" repeatCount="indefinite"/>
								</circle>
								<circle r="30" fill="none" stroke="{neonColors.secondary}" stroke-width="0.5" opacity="0.3">
									<animate attributeName="r" values="30;35;30" dur="4s" repeatCount="indefinite"/>
								</circle>
								<text text-anchor="middle" fill="{neonColors.primary}" font-size="14" font-weight="bold">
									NEXUS
								</text>
							</g>
						</svg>
					</div>
					
					<div class="constellation-controls">
						<div class="control-hint">Click and drag to rotate</div>
					</div>
				</div>
			{:else if viewMode === 'flow'}
				<!-- Flow View -->
				<div class="flow-view">
					<div class="flow-container">
						<!-- Animated flow visualization will go here -->
						<svg class="flow-svg" viewBox="0 0 1000 600">
							{#each filteredDivisions.slice(0, 20) as [division, count], i}
								{@const metrics = calculateMetrics(count)}
								{@const x = 100 + (i % 5) * 180}
								{@const y = 100 + Math.floor(i / 5) * 120}
								
								<g class="flow-node" transform="translate({x}, {y})"
								   on:click={() => drillDownDivision(division, count)}>
									<rect x="-60" y="-30" width="120" height="60"
										  fill="none"
										  stroke="{metrics.color}"
										  stroke-width="1"
										  opacity="0.5"
										  rx="10"/>
									<rect x="-60" y="-30" width="{metrics.percentile * 1.2}" height="60"
										  fill="{metrics.color}"
										  opacity="0.1"
										  rx="10"/>
									<text text-anchor="middle" y="-5" fill="#ffffff" font-size="10">
										{division.substring(0, 15)}
									</text>
									<text text-anchor="middle" y="10" fill="{metrics.color}" font-size="12" font-weight="bold">
										{count}
									</text>
								</g>
							{/each}
						</svg>
					</div>
				</div>
			{:else if viewMode === 'hexgrid'}
				<!-- Hexagonal Grid View -->
				<div class="hexgrid-view">
					<div class="hexgrid-container">
						<svg class="hexgrid-svg" viewBox="-400 -400 800 800">
							{#each hexGrid as hex}
								{#if hex.active && divisionNodes[hex.divisionIndex]}
									{@const division = divisionNodes[hex.divisionIndex]}
									<g transform="translate({hex.x}, {hex.y})"
									   on:click={() => drillDownDivision(division.name, division.count)}>
										<polygon points="-26,0 -13,-22.5 13,-22.5 26,0 13,22.5 -13,22.5"
												 fill="{division.color}"
												 opacity="{0.1 + hex.energy / 200}"
												 stroke="{division.color}"
												 stroke-width="1"/>
										<text text-anchor="middle" y="4" 
											  fill="#ffffff" 
											  font-size="8" 
											  opacity="{0.5 + hex.energy / 200}">
											{division.name.substring(0, 3).toUpperCase()}
										</text>
									</g>
								{/if}
							{/each}
						</svg>
					</div>
				</div>
			{:else if viewMode === 'pulse'}
				<!-- Pulse View -->
				<div class="pulse-view">
					<div class="pulse-container">
						<div class="pulse-center">
							<div class="pulse-core">
								<div class="core-value">{dataStreamVolume.toFixed(0)}%</div>
								<div class="core-label">DATA VOLUME</div>
							</div>
							<div class="pulse-wave wave-1" style="border-color: {neonColors.primary}"></div>
							<div class="pulse-wave wave-2" style="border-color: {neonColors.secondary}"></div>
							<div class="pulse-wave wave-3" style="border-color: {neonColors.tertiary}"></div>
						</div>
						
						<div class="pulse-satellites">
							{#each filteredDivisions.slice(0, 8) as [division, count], i}
								{@const angle = (i / 8) * Math.PI * 2}
								{@const metrics = calculateMetrics(count)}
								<div class="satellite-node"
									 style="left: {50 + Math.cos(angle) * 35}%;
											top: {50 + Math.sin(angle) * 35}%"
									 on:click={() => drillDownDivision(division, count)}>
									<div class="satellite-glow" style="background: {metrics.color}"></div>
									<div class="satellite-info">
										<span class="satellite-name">{division.substring(0, 12)}</span>
										<span class="satellite-value" style="color: {metrics.color}">{metrics.powerLevel}%</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>
			{/if}
			
			<!-- Data Matrix Table -->
			{#if !selectedDivision}
				<div class="data-matrix">
					<div class="matrix-header">
						<h3>DIVISION DATA MATRIX</h3>
					</div>
					<div class="matrix-content">
						<table class="matrix-table">
							<thead>
								<tr>
									<th>RANK</th>
									<th>DIVISION</th>
									<th>NODES</th>
									<th>SHARE</th>
									<th>POWER</th>
									<th>EFFICIENCY</th>
									<th>SIGNATURE</th>
								</tr>
							</thead>
							<tbody>
								{#each filteredDivisions as [division, count], index}
									{@const metrics = calculateMetrics(count)}
									<tr class="matrix-row"
										style="border-left: 3px solid {metrics.color}"
										on:click={() => drillDownDivision(division, count)}>
										<td class="rank-col">
											<span style="color: {metrics.color}">#{index + 1}</span>
										</td>
										<td class="division-col">
											<span class="division-icon" style="color: {metrics.color}">⬢</span>
											<span class="division-text">{division.substring(0, 30).toUpperCase()}</span>
										</td>
										<td class="numeric-col" style="color: {metrics.color}">
											{count.toLocaleString()}
										</td>
										<td class="share-col">
											<div class="share-bar">
												<div class="share-fill" 
													 style="width: {getPercentage(count)}%; 
															background: {metrics.color}"></div>
											</div>
											<span class="share-value">{getPercentage(count)}%</span>
										</td>
										<td class="power-col">
											<div class="power-indicator">
												<div class="power-bar" 
													 style="width: {metrics.powerLevel}%; 
															background: {metrics.color}"></div>
											</div>
											<span class="power-value">{metrics.powerLevel}%</span>
										</td>
										<td class="efficiency-col">
											<span style="color: {metrics.color}">{metrics.efficiency}%</span>
										</td>
										<td class="signature-col">
											<span class="signature-text">{metrics.quantumSignature}</span>
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
	.quantum-division-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		position: relative;
		overflow: hidden;
		font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
	}
	
	/* Particle Field */
	.particle-field {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
		perspective: 1000px;
	}
	
	.quantum-particle {
		position: absolute;
		border-radius: 50%;
		animation: floatParticle 30s linear infinite;
	}
	
	@keyframes floatParticle {
		0% { transform: translate3d(0, 0, 0) scale(1); }
		25% { transform: translate3d(50px, -50px, 100px) scale(1.2); }
		50% { transform: translate3d(-30px, 30px, -50px) scale(0.8); }
		75% { transform: translate3d(40px, 20px, 50px) scale(1.1); }
		100% { transform: translate3d(0, 0, 0) scale(1); }
	}
	
	/* Flow Field Layer */
	.flow-field-layer {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 2;
		opacity: 0.2;
	}
	
	/* Container */
	.division-container {
		position: relative;
		z-index: 10;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
	
	/* Header */
	.quantum-header {
		background: linear-gradient(180deg, rgba(0, 255, 170, 0.03), rgba(0, 0, 0, 0.95));
		backdrop-filter: blur(20px);
		border-bottom: 1px solid rgba(0, 255, 170, 0.2);
		padding: 1.5rem 2rem;
	}
	
	.header-layout {
		display: grid;
		grid-template-columns: 1fr auto auto;
		gap: 3rem;
		align-items: center;
	}
	
	.brand-area {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.quantum-emblem {
		width: 60px;
		height: 60px;
		position: relative;
	}
	
	.emblem-structure {
		width: 100%;
		height: 100%;
		position: relative;
		transform-style: preserve-3d;
	}
	
	.emblem-layer {
		position: absolute;
		inset: 0;
		border: 1px solid;
		transform-style: preserve-3d;
	}
	
	.layer-1 {
		inset: 0;
		clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
	}
	
	.layer-2 {
		inset: 10px;
		clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
	}
	
	.layer-3 {
		inset: 20px;
		clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
	}
	
	.emblem-core {
		position: absolute;
		inset: 25px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.2rem;
		color: #00FFAA;
		text-shadow: 0 0 20px rgba(0, 255, 170, 0.8);
		animation: coreBreathe 3s ease-in-out infinite;
	}
	
	@keyframes coreBreathe {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.1); opacity: 0.8; }
	}
	
	.interface-title {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 200;
		letter-spacing: 0.3em;
		background: linear-gradient(90deg, #00FFAA, #FF00AA, #AAFF00);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		position: relative;
		animation: titleShimmer 5s linear infinite;
	}
	
	@keyframes titleShimmer {
		0% { background-position: 0% 50%; }
		100% { background-position: 200% 50%; }
	}
	
	/* Glitch effect for title */
	.interface-title::before,
	.interface-title::after {
		content: attr(data-text);
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, #00FFAA, #FF00AA, #AAFF00);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		z-index: -1;
	}
	
	.interface-title::before {
		animation: glitch-1 0.5s infinite;
		text-shadow: -2px 0 #FF00AA;
	}
	
	.interface-title::after {
		animation: glitch-2 0.5s infinite;
		text-shadow: 2px 0 #00FFAA;
	}
	
	@keyframes glitch-1 {
		0%, 100% { clip-path: inset(0 0 0 0); }
		25% { clip-path: inset(10% 0 60% 0); transform: translate(-2px, 1px); }
		50% { clip-path: inset(30% 0 40% 0); transform: translate(2px, -1px); }
		75% { clip-path: inset(50% 0 20% 0); transform: translate(-1px, 2px); }
	}
	
	@keyframes glitch-2 {
		0%, 100% { clip-path: inset(0 0 0 0); }
		25% { clip-path: inset(60% 0 10% 0); transform: translate(1px, -2px); }
		50% { clip-path: inset(20% 0 50% 0); transform: translate(-2px, 1px); }
		75% { clip-path: inset(40% 0 30% 0); transform: translate(2px, 2px); }
	}
	
	.system-status {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-top: 0.5rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
	}
	
	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: statusBlink 2s ease-in-out infinite;
	}
	
	@keyframes statusBlink {
		0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 currentColor; }
		50% { transform: scale(1.2); box-shadow: 0 0 0 4px transparent; }
	}
	
	.separator {
		color: rgba(255, 255, 255, 0.2);
	}
	
	/* Control Area */
	.control-area {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.search-module {
		position: relative;
	}
	
	.quantum-input {
		width: 100%;
		padding: 0.75rem 1rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 170, 0.2);
		border-radius: 8px;
		color: #00FFAA;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.9rem;
		letter-spacing: 0.05em;
		transition: all 0.3s ease;
	}
	
	.quantum-input::placeholder {
		color: rgba(0, 255, 170, 0.4);
	}
	
	.quantum-input:focus {
		outline: none;
		border-color: #00FFAA;
		background: rgba(0, 255, 170, 0.05);
		box-shadow: 0 0 30px rgba(0, 255, 170, 0.2);
	}
	
	.search-scanner {
		position: absolute;
		bottom: 0;
		left: 0;
		height: 1px;
		background: linear-gradient(90deg, transparent, #00FFAA, transparent);
		transition: width 0.3s ease;
	}
	
	.view-selector {
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
		--btn-color: #00FFAA;
	}
	
	.view-btn:hover {
		border-color: var(--btn-color);
		background: rgba(0, 255, 170, 0.05);
		color: var(--btn-color);
	}
	
	.view-btn.active {
		border-color: var(--btn-color);
		background: linear-gradient(135deg, rgba(0, 255, 170, 0.1), rgba(0, 0, 0, 0.6));
		color: var(--btn-color);
		box-shadow: 0 0 20px rgba(0, 255, 170, 0.2);
	}
	
	.btn-icon {
		font-size: 1.2rem;
	}
	
	.btn-label {
		font-size: 0.65rem;
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	/* Metrics Area */
	.metrics-area {
		display: flex;
		gap: 2rem;
	}
	
	.metric-block {
		text-align: center;
	}
	
	.metric-number {
		font-size: 1.8rem;
		font-weight: 100;
		font-family: 'JetBrains Mono', monospace;
		text-shadow: 0 0 20px currentColor;
	}
	
	.metric-text {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.2em;
		margin-top: 0.25rem;
		font-weight: 500;
	}
	
	/* Interface Viewport */
	.interface-viewport {
		flex: 1;
		padding: 2rem;
		overflow: hidden;
		display: flex;
		gap: 2rem;
	}
	
	/* Loading Interface */
	.loading-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.loading-quantum {
		position: relative;
		width: 120px;
		height: 120px;
	}
	
	.quantum-ring {
		position: absolute;
		inset: 0;
		border: 2px solid;
		clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
		animation: quantumSpin 3s linear infinite;
	}
	
	.quantum-ring:nth-child(2) {
		inset: 20px;
	}
	
	.quantum-ring:nth-child(3) {
		inset: 40px;
	}
	
	@keyframes quantumSpin {
		from { transform: rotate(0deg) scale(1); }
		50% { transform: rotate(180deg) scale(1.1); }
		to { transform: rotate(360deg) scale(1); }
	}
	
	.quantum-center {
		position: absolute;
		inset: 45px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		color: #00FFAA;
		text-shadow: 0 0 30px rgba(0, 255, 170, 0.8);
		animation: pulse 2s ease-in-out infinite;
	}
	
	@keyframes pulse {
		0%, 100% { opacity: 0.5; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.1); }
	}
	
	.loading-message {
		color: rgba(0, 255, 170, 0.6);
		font-size: 0.9rem;
		letter-spacing: 0.2em;
		animation: pulse 2s ease-in-out infinite;
	}
	
	/* Constellation View */
	.constellation-view {
		flex: 1;
		position: relative;
		background: radial-gradient(ellipse at center, rgba(0, 255, 170, 0.02), transparent);
		border: 1px solid rgba(0, 255, 170, 0.1);
		border-radius: 16px;
		overflow: hidden;
		cursor: move;
	}
	
	.constellation-container {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		transform-style: preserve-3d;
		transition: transform 0.1s ease;
	}
	
	.constellation-svg {
		width: 100%;
		height: 100%;
	}
	
	.division-node {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.division-node:hover {
		transform: scale(1.2);
	}
	
	.constellation-controls {
		position: absolute;
		bottom: 1rem;
		right: 1rem;
		padding: 0.5rem 1rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 170, 0.2);
		border-radius: 8px;
	}
	
	.control-hint {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}
	
	/* Flow View */
	.flow-view {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 170, 0.1);
		border-radius: 16px;
		overflow: hidden;
	}
	
	.flow-container {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.flow-svg {
		width: 100%;
		height: 100%;
	}
	
	.flow-node {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.flow-node:hover {
		transform: scale(1.1);
	}
	
	/* Hexgrid View */
	.hexgrid-view {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 170, 0.1);
		border-radius: 16px;
		overflow: hidden;
	}
	
	.hexgrid-container {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.hexgrid-svg {
		width: 100%;
		height: 100%;
	}
	
	/* Pulse View */
	.pulse-view {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 170, 0.1);
		border-radius: 16px;
		position: relative;
		overflow: hidden;
	}
	
	.pulse-container {
		width: 100%;
		height: 100%;
		position: relative;
	}
	
	.pulse-center {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 200px;
		height: 200px;
	}
	
	.pulse-core {
		position: absolute;
		inset: 60px;
		background: radial-gradient(circle, rgba(0, 255, 170, 0.3), transparent);
		border-radius: 50%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}
	
	.core-value {
		font-size: 1.5rem;
		font-weight: 100;
		color: #00FFAA;
		font-family: 'JetBrains Mono', monospace;
		text-shadow: 0 0 20px rgba(0, 255, 170, 0.8);
	}
	
	.core-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		margin-top: 0.25rem;
	}
	
	.pulse-wave {
		position: absolute;
		inset: 0;
		border: 2px solid;
		border-radius: 50%;
		animation: waveExpand 3s ease-out infinite;
	}
	
	.wave-2 {
		animation-delay: 1s;
	}
	
	.wave-3 {
		animation-delay: 2s;
	}
	
	@keyframes waveExpand {
		0% { transform: scale(0.8); opacity: 1; }
		100% { transform: scale(2); opacity: 0; }
	}
	
	.pulse-satellites {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}
	
	.satellite-node {
		position: absolute;
		transform: translate(-50%, -50%);
		cursor: pointer;
		pointer-events: all;
		transition: all 0.3s ease;
	}
	
	.satellite-node:hover {
		z-index: 10;
		transform: translate(-50%, -50%) scale(1.2);
	}
	
	.satellite-glow {
		width: 60px;
		height: 60px;
		border-radius: 50%;
		animation: satellitePulse 2s ease-in-out infinite;
	}
	
	@keyframes satellitePulse {
		0%, 100% { transform: scale(1); opacity: 0.3; }
		50% { transform: scale(1.3); opacity: 0.6; }
	}
	
	.satellite-info {
		position: absolute;
		top: 100%;
		left: 50%;
		transform: translateX(-50%);
		margin-top: 0.5rem;
		text-align: center;
		white-space: nowrap;
	}
	
	.satellite-name {
		display: block;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.7);
		margin-bottom: 0.25rem;
	}
	
	.satellite-value {
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	/* Data Matrix */
	.data-matrix {
		width: 400px;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 170, 0.1);
		border-radius: 16px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.matrix-header {
		padding: 1rem 1.5rem;
		background: rgba(0, 0, 0, 0.4);
		border-bottom: 1px solid rgba(0, 255, 170, 0.1);
	}
	
	.matrix-header h3 {
		margin: 0;
		font-size: 0.9rem;
		color: #00FFAA;
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	.matrix-content {
		flex: 1;
		overflow: auto;
	}
	
	.matrix-table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0;
	}
	
	.matrix-table th {
		background: rgba(0, 0, 0, 0.6);
		color: rgba(0, 255, 170, 0.7);
		padding: 0.75rem 0.5rem;
		text-align: left;
		font-size: 0.65rem;
		font-weight: 500;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 1px solid rgba(0, 255, 170, 0.2);
	}
	
	.matrix-row {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.03);
	}
	
	.matrix-row:hover {
		background: rgba(0, 255, 170, 0.02);
		transform: translateX(5px);
	}
	
	.matrix-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.rank-col {
		font-weight: 600;
		font-family: 'JetBrains Mono', monospace;
		width: 50px;
	}
	
	.division-col {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.division-icon {
		font-size: 0.9rem;
	}
	
	.division-text {
		font-weight: 300;
		letter-spacing: 0.05em;
	}
	
	.numeric-col {
		font-family: 'JetBrains Mono', monospace;
	}
	
	.share-col {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.share-bar {
		width: 40px;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.share-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.share-value {
		font-size: 0.65rem;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.power-col {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.power-indicator {
		width: 40px;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		overflow: hidden;
		border-radius: 2px;
	}
	
	.power-bar {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.power-value {
		font-size: 0.65rem;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.efficiency-col {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.7rem;
	}
	
	.signature-col {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.05em;
	}
	
	/* Detail View */
	.division-detail-view {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2rem;
		overflow: hidden;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 2rem;
		background: linear-gradient(135deg, rgba(0, 255, 170, 0.05), rgba(0, 0, 0, 0.8));
		border: 1px solid rgba(0, 255, 170, 0.2);
		border-radius: 16px;
	}
	
	.division-profile {
		display: flex;
		align-items: center;
		gap: 2rem;
	}
	
	.profile-avatar {
		width: 100px;
		height: 100px;
		border: 2px solid;
		clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.avatar-layers {
		position: absolute;
		inset: -10px;
		pointer-events: none;
	}
	
	.avatar-layers .layer {
		position: absolute;
		inset: 0;
		border: 1px solid;
		clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
		animation: layerRotate 4s linear infinite;
	}
	
	.avatar-layers .layer:nth-child(2) {
		inset: 10px;
		animation-direction: reverse;
		animation-duration: 6s;
	}
	
	@keyframes layerRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.avatar-symbol {
		font-size: 2.5rem;
		color: #00FFAA;
		text-shadow: 0 0 30px rgba(0, 255, 170, 0.8);
		z-index: 2;
	}
	
	.profile-data {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.division-name {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 200;
		color: #00FFAA;
		letter-spacing: 0.1em;
		text-shadow: 0 0 20px rgba(0, 255, 170, 0.5);
	}
	
	.division-signature {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}
	
	.division-badges {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}
	
	.badge {
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-size: 0.75rem;
		font-weight: 500;
		letter-spacing: 0.05em;
		border: 1px solid currentColor;
	}
	
	.close-button {
		width: 48px;
		height: 48px;
		background: rgba(255, 0, 85, 0.1);
		border: 1px solid #FF0055;
		border-radius: 12px;
		color: #FF0055;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.close-button:hover {
		background: rgba(255, 0, 85, 0.2);
		transform: rotate(90deg);
		box-shadow: 0 0 30px rgba(255, 0, 85, 0.5);
	}
	
	.close-button span {
		font-size: 1.5rem;
	}
	
	.detail-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1.5rem;
	}
	
	.detail-metric {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 16px;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		position: relative;
		overflow: hidden;
	}
	
	.detail-metric::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 1px;
		background: linear-gradient(90deg, transparent, currentColor, transparent);
		animation: scanLine 3s linear infinite;
	}
	
	@keyframes scanLine {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100%); }
	}
	
	.metric-icon {
		font-size: 1.5rem;
		text-shadow: 0 0 20px currentColor;
	}
	
	.metric-content {
		flex: 1;
	}
	
	.metric-value {
		font-size: 1.8rem;
		font-weight: 100;
		font-family: 'JetBrains Mono', monospace;
		text-shadow: 0 0 20px currentColor;
	}
	
	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		margin-top: 0.5rem;
	}
	
	.metric-graph {
		margin-top: auto;
		height: 30px;
	}
	
	.metric-graph svg {
		width: 100%;
		height: 100%;
	}
	
	.detail-data {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 170, 0.1);
		border-radius: 16px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.data-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
		background: rgba(0, 0, 0, 0.4);
		border-bottom: 1px solid rgba(0, 255, 170, 0.1);
	}
	
	.data-header h3 {
		margin: 0;
		font-size: 0.9rem;
		color: #00FFAA;
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	.data-status {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	
	.status-live {
		font-size: 0.7rem;
		color: #00FF55;
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	.status-dot {
		width: 8px;
		height: 8px;
		background: #00FF55;
		border-radius: 50%;
		animation: liveBlink 1s ease-in-out infinite;
	}
	
	@keyframes liveBlink {
		0%, 100% { opacity: 1; box-shadow: 0 0 10px #00FF55; }
		50% { opacity: 0.3; box-shadow: none; }
	}
	
	.data-table-container {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}
	
	.data-table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0;
	}
	
	.data-table th {
		background: rgba(0, 0, 0, 0.6);
		color: rgba(0, 255, 170, 0.7);
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 500;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 1px solid rgba(0, 255, 170, 0.2);
	}
	
	.table-row {
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.03);
	}
	
	.table-row:hover {
		background: rgba(0, 255, 170, 0.02);
	}
	
	.data-table td {
		padding: 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.node-id {
		font-family: 'JetBrains Mono', monospace;
		color: #00FFAA;
		font-size: 0.7rem;
		letter-spacing: 0.05em;
	}
	
	.status {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		font-size: 1rem;
		text-shadow: 0 0 10px currentColor;
	}
	
	/* Responsive */
	@media (max-width: 1600px) {
		.header-layout {
			grid-template-columns: 1fr;
			gap: 1.5rem;
		}
		
		.metrics-area {
			justify-content: flex-start;
		}
		
		.detail-grid {
			grid-template-columns: repeat(2, 1fr);
		}
		
		.interface-viewport {
			flex-direction: column;
		}
		
		.data-matrix {
			width: 100%;
			max-height: 300px;
		}
	}
	
	@media (max-width: 768px) {
		.interface-viewport {
			padding: 1rem;
		}
		
		.detail-grid {
			grid-template-columns: 1fr;
		}
	}
	
	/* Scrollbar Styling */
	::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}
	
	::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.4);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb {
		background: linear-gradient(180deg, #00FFAA, #FF00AA);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(180deg, #00FFAA, #AAFF00);
	}