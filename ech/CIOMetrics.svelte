<!-- CIOMetrics.svelte - Executive Quantum Neural Network Interface -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedExecutive = null;
	let executiveDetails = [];
	let searchTerm = '';
	
	// Visualization states
	let viewMode = 'neural'; // 'neural', 'hierarchy', 'pulse', 'matrix'
	let neuralNodes = [];
	let connections = [];
	let particleField = [];
	let quantumState = 'INITIALIZING';
	let dataStream = [];
	let holographicLayers = [];
	let energyFlow = 0;
	let networkPulse = 0;
	let timelineData = [];
	let hierarchyLevels = [];
	
	// Animation references
	let animationFrameId;
	let intervals = [];
	
	// Neon pastel color scheme
	const neonColors = {
		primary: '#00FFCC',    // Cyan
		secondary: '#FF00FF',   // Magenta
		tertiary: '#FFFF00',    // Yellow
		quaternary: '#00FF88',  // Mint
		accent1: '#FF88FF',     // Pink
		accent2: '#88FFFF',     // Light Cyan
		accent3: '#FFFF88',     // Light Yellow
		danger: '#FF0088',      // Hot Pink
		warning: '#FFAA00',     // Orange
		success: '#00FF00'      // Lime
	};
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/cio_metrics');
			data = await response.json();
			loading = false;
			quantumState = 'SYNCHRONIZED';
			initializeVisualization();
			startAnimations();
		} catch (err) {
			console.error('Executive neural sync failed:', err);
			loading = false;
			quantumState = 'DESYNCHRONIZED';
		}
	});
	
	onDestroy(() => {
		if (animationFrameId) cancelAnimationFrame(animationFrameId);
		intervals.forEach(interval => clearInterval(interval));
	});
	
	function initializeVisualization() {
		if (!data.operative_intelligence) return;
		
		// Create neural nodes from executive data
		let executives = Object.entries(data.operative_intelligence);
		let maxCount = Math.max(...executives.map(([,c]) => c));
		
		executives.forEach(([executive, count], i) => {
			let importance = count / maxCount;
			let angle = (i / executives.length) * Math.PI * 2;
			let radius = 100 + importance * 150;
			
			neuralNodes.push({
				id: i,
				name: executive,
				count: count,
				importance: importance,
				x: Math.cos(angle) * radius,
				y: Math.sin(angle) * radius,
				z: Math.sin(importance * Math.PI) * 50,
				vx: 0,
				vy: 0,
				vz: 0,
				energy: importance * 100,
				connections: [],
				pulsePhase: Math.random() * Math.PI * 2,
				color: interpolateNeonColor(importance)
			});
		});
		
		// Create neural connections based on similarity
		neuralNodes.forEach((node, i) => {
			neuralNodes.forEach((target, j) => {
				if (i < j) {
					let similarity = Math.abs(node.importance - target.importance);
					if (similarity < 0.3 || Math.random() > 0.7) {
						connections.push({
							source: i,
							target: j,
							strength: 1 - similarity,
							pulseOffset: Math.random() * Math.PI * 2,
							dataFlow: Math.random() * 100
						});
					}
				}
			});
		});
		
		// Initialize particle field for background
		for (let i = 0; i < 200; i++) {
			particleField.push({
				x: Math.random() * window.innerWidth,
				y: Math.random() * window.innerHeight,
				z: Math.random() * 100,
				vx: (Math.random() - 0.5) * 0.5,
				vy: (Math.random() - 0.5) * 0.5,
				size: Math.random() * 2 + 0.5,
				color: Object.values(neonColors)[Math.floor(Math.random() * 6)],
				pulse: Math.random() * Math.PI * 2
			});
		}
		
		// Initialize data stream
		for (let i = 0; i < 50; i++) {
			dataStream.push({
				value: Math.random() * 100,
				timestamp: Date.now() - i * 1000,
				type: ['neural', 'quantum', 'executive'][Math.floor(Math.random() * 3)]
			});
		}
		
		// Create hierarchy levels dynamically
		let sorted = [...executives].sort((a, b) => b[1] - a[1]);
		let levelSize = Math.ceil(sorted.length / 4);
		for (let level = 0; level < 4; level++) {
			hierarchyLevels.push({
				level: level,
				members: sorted.slice(level * levelSize, (level + 1) * levelSize),
				color: Object.values(neonColors)[level]
			});
		}
	}
	
	function interpolateNeonColor(value) {
		if (value > 0.75) return neonColors.primary;
		if (value > 0.5) return neonColors.secondary;
		if (value > 0.25) return neonColors.tertiary;
		return neonColors.quaternary;
	}
	
	function startAnimations() {
		// Main animation loop
		function animate() {
			updateParticles();
			updateNeuralNetwork();
			updateDataStream();
			energyFlow = Math.sin(Date.now() * 0.001) * 50 + 50;
			networkPulse = (Date.now() * 0.1) % 360;
			animationFrameId = requestAnimationFrame(animate);
		}
		animate();
		
		// Quantum state updates
		intervals.push(setInterval(() => {
			quantumState = ['SYNCHRONIZED', 'PROCESSING', 'ANALYZING', 'CORRELATING', 'OPTIMIZING'][
				Math.floor(Math.random() * 5)
			];
		}, 3000));
		
		// Data stream updates
		intervals.push(setInterval(() => {
			dataStream.push({
				value: Math.random() * 100,
				timestamp: Date.now(),
				type: ['neural', 'quantum', 'executive'][Math.floor(Math.random() * 3)]
			});
			dataStream = dataStream.slice(-50);
		}, 100));
	}
	
	function updateParticles() {
		particleField = particleField.map(p => ({
			...p,
			x: (p.x + p.vx + window.innerWidth) % window.innerWidth,
			y: (p.y + p.vy + window.innerHeight) % window.innerHeight,
			pulse: p.pulse + 0.05
		}));
	}
	
	function updateNeuralNetwork() {
		neuralNodes = neuralNodes.map(node => ({
			...node,
			pulsePhase: node.pulsePhase + 0.05,
			energy: 50 + Math.sin(node.pulsePhase) * 50
		}));
	}
	
	function updateDataStream() {
		// Simulate real-time data flow
		connections = connections.map(conn => ({
			...conn,
			dataFlow: Math.max(0, Math.min(100, conn.dataFlow + (Math.random() - 0.5) * 10))
		}));
	}
	
	$: filteredExecutives = data.operative_intelligence ? 
		Object.entries(data.operative_intelligence)
			.filter(([exec]) => exec.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxAssets = filteredExecutives.length > 0 ? 
		Math.max(...filteredExecutives.map(([,c]) => c)) : 1;
	
	function calculateMetrics(count) {
		let normalized = count / maxAssets;
		let percentile = normalized * 100;
		
		return {
			percentile: percentile.toFixed(1),
			powerLevel: (normalized * 100).toFixed(0),
			influence: (Math.pow(normalized, 0.5) * 100).toFixed(0),
			networkReach: (count * 0.01).toFixed(2),
			quantumSignature: generateQuantumSignature(count),
			threatIndex: (normalized * Math.random() * 100).toFixed(0),
			dataNodes: count,
			color: interpolateNeonColor(normalized)
		};
	}
	
	function generateQuantumSignature(seed) {
		let signature = '';
		let chars = '0123456789ABCDEF';
		for (let i = 0; i < 16; i++) {
			signature += chars[(seed * (i + 1) * 9973) % 16];
			if (i % 4 === 3 && i < 15) signature += '-';
		}
		return signature;
	}
	
	function getPercentage(count) {
		let total = Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0);
		return total > 0 ? ((count / total) * 100).toFixed(2) : '0.00';
	}
	
	async function drillDownExecutive(executive, count) {
		selectedExecutive = { executive, count };
		loading = true;
		quantumState = 'DEEP_SCANNING';
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(executive)}`);
			let result = await response.json();
			executiveDetails = result.hosts || [];
			loading = false;
			quantumState = 'SYNCHRONIZED';
		} catch (err) {
			console.error('Executive deep scan failed:', err);
			executiveDetails = [];
			loading = false;
			quantumState = 'ERROR';
		}
	}
	
	function closeDetails() {
		selectedExecutive = null;
		executiveDetails = [];
		quantumState = 'SYNCHRONIZED';
	}
</script>

<div class="quantum-executive-interface">
	<!-- Particle Field Background -->
	<div class="particle-universe">
		{#each particleField as particle}
			<div class="quantum-particle" 
				 style="left: {particle.x}px; 
						top: {particle.y}px;
						width: {particle.size}px;
						height: {particle.size}px;
						background: {particle.color};
						opacity: {0.3 + Math.sin(particle.pulse) * 0.3};
						box-shadow: 0 0 {10 + Math.sin(particle.pulse) * 5}px {particle.color}">
			</div>
		{/each}
	</div>
	
	<!-- Data Stream Visualization -->
	<svg class="data-stream-layer">
		<defs>
			<linearGradient id="dataGradient" x1="0%" y1="0%" x2="100%" y2="0%">
				<stop offset="0%" style="stop-color:{neonColors.primary};stop-opacity:0" />
				<stop offset="50%" style="stop-color:{neonColors.secondary};stop-opacity:1" />
				<stop offset="100%" style="stop-color:{neonColors.tertiary};stop-opacity:0" />
			</linearGradient>
			<filter id="neonGlow">
				<feGaussianBlur stdDeviation="4" result="coloredBlur"/>
				<feMerge>
					<feMergeNode in="coloredBlur"/>
					<feMergeNode in="SourceGraphic"/>
				</feMerge>
			</filter>
		</defs>
		
		{#each Array(10) as _, i}
			<line x1="0" y1="{i * 10}%" x2="100%" y2="{i * 10}%"
				  stroke="url(#dataGradient)" 
				  stroke-width="0.5" 
				  opacity="{0.1 + Math.sin(networkPulse * 0.01 + i) * 0.1}">
				<animate attributeName="x1" 
						 values="-100%;0%;100%" 
						 dur="{5 + i}s" 
						 repeatCount="indefinite"/>
			</line>
		{/each}
	</svg>
	
	<div class="executive-container">
		<!-- Quantum Header -->
		<header class="quantum-header">
			<div class="header-grid">
				<div class="brand-section">
					<div class="quantum-logo">
						<div class="logo-hologram" style="transform: rotate({networkPulse}deg)">
							<div class="hologram-ring ring-1" style="border-color: {neonColors.primary}"></div>
							<div class="hologram-ring ring-2" style="border-color: {neonColors.secondary}"></div>
							<div class="hologram-ring ring-3" style="border-color: {neonColors.tertiary}"></div>
							<div class="hologram-core">
								<span class="core-symbol">∞</span>
							</div>
						</div>
					</div>
					<div class="brand-text">
						<h1 class="glitch-title" data-text="EXECUTIVE QUANTUM NETWORK">
							EXECUTIVE QUANTUM NETWORK
						</h1>
						<div class="quantum-status">
							<span class="status-dot" style="background: {quantumState === 'ERROR' ? neonColors.danger : neonColors.success}"></span>
							<span class="status-text">QUANTUM STATE: {quantumState}</span>
							<span class="divider">|</span>
							<span class="energy-text">ENERGY: {energyFlow.toFixed(0)}%</span>
						</div>
					</div>
				</div>
				
				<div class="control-section">
					<div class="search-container">
						<input 
							type="text" 
							bind:value={searchTerm}
							placeholder="NEURAL SEARCH..."
							class="quantum-search"
						/>
						<div class="search-pulse" style="width: {searchTerm ? '100%' : '0'}"></div>
					</div>
					
					<div class="view-modes">
						<button class="mode-btn {viewMode === 'neural' ? 'active' : ''}"
								on:click={() => viewMode = 'neural'}
								style="--accent-color: {neonColors.primary}">
							<span class="mode-icon">◈</span>
							<span class="mode-label">NEURAL</span>
						</button>
						<button class="mode-btn {viewMode === 'hierarchy' ? 'active' : ''}"
								on:click={() => viewMode = 'hierarchy'}
								style="--accent-color: {neonColors.secondary}">
							<span class="mode-icon">⬢</span>
							<span class="mode-label">HIERARCHY</span>
						</button>
						<button class="mode-btn {viewMode === 'pulse' ? 'active' : ''}"
								on:click={() => viewMode = 'pulse'}
								style="--accent-color: {neonColors.tertiary}">
							<span class="mode-icon">◉</span>
							<span class="mode-label">PULSE</span>
						</button>
						<button class="mode-btn {viewMode === 'matrix' ? 'active' : ''}"
								on:click={() => viewMode = 'matrix'}
								style="--accent-color: {neonColors.quaternary}">
							<span class="mode-icon">▣</span>
							<span class="mode-label">MATRIX</span>
						</button>
					</div>
				</div>
				
				<div class="metrics-section">
					<div class="metric-display">
						<div class="metric-value" style="color: {neonColors.primary}">
							{filteredExecutives.length}
						</div>
						<div class="metric-label">ENTITIES</div>
					</div>
					<div class="metric-display">
						<div class="metric-value" style="color: {neonColors.secondary}">
							{Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}
						</div>
						<div class="metric-label">NODES</div>
					</div>
				</div>
			</div>
		</header>
		
		<!-- Main Interface -->
		<div class="interface-body">
			{#if loading && !selectedExecutive}
				<div class="quantum-loading">
					<div class="loading-vortex">
						<div class="vortex-ring" style="border-color: {neonColors.primary}"></div>
						<div class="vortex-ring" style="border-color: {neonColors.secondary}; animation-delay: 0.2s"></div>
						<div class="vortex-ring" style="border-color: {neonColors.tertiary}; animation-delay: 0.4s"></div>
						<div class="vortex-center">◈</div>
					</div>
					<p class="loading-text">INITIALIZING QUANTUM NEURAL INTERFACE...</p>
				</div>
			{:else if selectedExecutive}
				<!-- Detail View -->
				<div class="executive-detail-interface">
					<div class="detail-header">
						<div class="executive-identity">
							<div class="identity-avatar" style="border-color: {calculateMetrics(selectedExecutive.count).color}">
								<div class="avatar-core">
									<span class="avatar-symbol">◈</span>
								</div>
								<div class="avatar-rings">
									<div class="ring" style="border-color: {neonColors.primary}"></div>
									<div class="ring" style="border-color: {neonColors.secondary}"></div>
								</div>
							</div>
							<div class="identity-data">
								<h2 class="executive-name">{selectedExecutive.executive.toUpperCase()}</h2>
								<div class="quantum-signature">
									{calculateMetrics(selectedExecutive.count).quantumSignature}
								</div>
								<div class="executive-tags">
									<span class="tag" style="background: {neonColors.primary}20; color: {neonColors.primary}">
										POWER: {calculateMetrics(selectedExecutive.count).powerLevel}%
									</span>
									<span class="tag" style="background: {neonColors.secondary}20; color: {neonColors.secondary}">
										INFLUENCE: {calculateMetrics(selectedExecutive.count).influence}%
									</span>
									<span class="tag" style="background: {neonColors.tertiary}20; color: {neonColors.tertiary}">
										REACH: {calculateMetrics(selectedExecutive.count).networkReach}K
									</span>
								</div>
							</div>
						</div>
						<button class="close-detail" on:click={closeDetails}>
							<span class="close-icon">✕</span>
						</button>
					</div>
					
					<div class="detail-metrics">
						<div class="metric-card">
							<div class="card-icon" style="color: {neonColors.primary}">◈</div>
							<div class="card-content">
								<div class="card-value">{selectedExecutive.count.toLocaleString()}</div>
								<div class="card-label">NEURAL NODES</div>
							</div>
							<div class="card-graph">
								<svg viewBox="0 0 100 40">
									<polyline points="{dataStream.slice(-20).map((d, i) => `${i * 5},${40 - d.value * 0.4}`).join(' ')}"
											  fill="none" stroke="{neonColors.primary}" stroke-width="1" opacity="0.8"/>
								</svg>
							</div>
						</div>
						<div class="metric-card">
							<div class="card-icon" style="color: {neonColors.secondary}">⬢</div>
							<div class="card-content">
								<div class="card-value">{getPercentage(selectedExecutive.count)}%</div>
								<div class="card-label">NETWORK CONTROL</div>
							</div>
							<div class="card-progress">
								<div class="progress-track">
									<div class="progress-fill" style="width: {getPercentage(selectedExecutive.count)}%; background: {neonColors.secondary}"></div>
								</div>
							</div>
						</div>
						<div class="metric-card">
							<div class="card-icon" style="color: {neonColors.tertiary}">◉</div>
							<div class="card-content">
								<div class="card-value">{calculateMetrics(selectedExecutive.count).percentile}%</div>
								<div class="card-label">PERCENTILE</div>
							</div>
							<div class="card-indicator">
								<div class="indicator-ring" style="border-color: {neonColors.tertiary}">
									<div class="indicator-value">{calculateMetrics(selectedExecutive.count).percentile}</div>
								</div>
							</div>
						</div>
						<div class="metric-card">
							<div class="card-icon" style="color: {neonColors.quaternary}">▣</div>
							<div class="card-content">
								<div class="card-value">{calculateMetrics(selectedExecutive.count).threatIndex}%</div>
								<div class="card-label">THREAT INDEX</div>
							</div>
							<div class="card-threat">
								<div class="threat-bars">
									{#each Array(10) as _, i}
										<div class="threat-bar" 
											 style="background: {i < calculateMetrics(selectedExecutive.count).threatIndex / 10 ? neonColors.danger : '#111'}"></div>
									{/each}
								</div>
							</div>
						</div>
					</div>
					
					<div class="detail-stream">
						<div class="stream-header">
							<h3>NEURAL DATA STREAM</h3>
							<div class="stream-controls">
								<span class="stream-status">LIVE</span>
								<span class="stream-indicator"></span>
							</div>
						</div>
						<div class="stream-content">
							<table class="quantum-table">
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
									{#each executiveDetails as host}
										<tr class="data-row">
											<td class="node-id">{host.host.substring(0, 30)}</td>
											<td>{host.country || 'UNKNOWN'}</td>
											<td>{host.region || 'UNKNOWN'}</td>
											<td>{host.infrastructure_type || 'UNKNOWN'}</td>
											<td>
												<span class="sync-indicator {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'synced' : 'desynced'}"
													  style="color: {host.present_in_cmdb?.toLowerCase().includes('yes') ? neonColors.success : neonColors.danger}">
													{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}
												</span>
											</td>
											<td>
												<span class="shield-indicator {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'protected' : 'vulnerable'}"
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
			{:else if viewMode === 'neural'}
				<!-- Neural Network View -->
				<div class="neural-view">
					<div class="neural-container">
						<svg class="neural-network" viewBox="-400 -400 800 800">
							<defs>
								<radialGradient id="nodeGradient">
									<stop offset="0%" style="stop-color:{neonColors.primary};stop-opacity:1" />
									<stop offset="100%" style="stop-color:{neonColors.primary};stop-opacity:0" />
								</radialGradient>
							</defs>
							
							<!-- Connections -->
							{#each connections as conn}
								{#if neuralNodes[conn.source] && neuralNodes[conn.target]}
									<line x1="{neuralNodes[conn.source].x}" 
										  y1="{neuralNodes[conn.source].y}"
										  x2="{neuralNodes[conn.target].x}" 
										  y2="{neuralNodes[conn.target].y}"
										  stroke="{neonColors.primary}"
										  stroke-width="{0.5 + conn.strength}"
										  opacity="{0.2 + conn.dataFlow / 200}">
										<animate attributeName="opacity" 
												 values="{0.2 + conn.dataFlow / 200};{0.4 + conn.dataFlow / 200};{0.2 + conn.dataFlow / 200}"
												 dur="2s" 
												 repeatCount="indefinite"/>
									</line>
								{/if}
							{/each}
							
							<!-- Nodes -->
							{#each neuralNodes as node}
								<g class="neural-node" 
								   transform="translate({node.x}, {node.y})"
								   on:click={() => drillDownExecutive(node.name, node.count)}>
									<circle r="{10 + node.importance * 20}"
											fill="{node.color}"
											opacity="0.2"/>
									<circle r="{5 + node.importance * 10}"
											fill="{node.color}"
											opacity="0.6">
										<animate attributeName="r" 
												 values="{5 + node.importance * 10};{7 + node.importance * 10};{5 + node.importance * 10}"
												 dur="{2 + node.importance * 2}s" 
												 repeatCount="indefinite"/>
									</circle>
									<text y="-{15 + node.importance * 20}" 
										  text-anchor="middle" 
										  fill="#ffffff" 
										  font-size="10" 
										  opacity="0.9">
										{node.name.substring(0, 20)}
									</text>
									<text y="4" 
										  text-anchor="middle" 
										  fill="{node.color}" 
										  font-size="8" 
										  font-weight="bold">
										{node.count}
									</text>
								</g>
							{/each}
							
							<!-- Central Core -->
							<circle r="30" fill="none" stroke="{neonColors.primary}" stroke-width="0.5" opacity="0.5">
								<animate attributeName="r" values="30;35;30" dur="3s" repeatCount="indefinite"/>
							</circle>
							<text text-anchor="middle" fill="{neonColors.primary}" font-size="14" font-weight="bold">
								NEXUS
							</text>
						</svg>
					</div>
					
					<!-- Side Panel -->
					<div class="neural-panel">
						<h3>NEURAL METRICS</h3>
						<div class="metrics-list">
							{#each filteredExecutives.slice(0, 10) as [executive, count]}
								{@const metrics = calculateMetrics(count)}
								<div class="metric-item" on:click={() => drillDownExecutive(executive, count)}>
									<div class="item-header">
										<span class="item-name">{executive.substring(0, 20).toUpperCase()}</span>
										<span class="item-value" style="color: {metrics.color}">{count}</span>
									</div>
									<div class="item-bar">
										<div class="bar-fill" style="width: {metrics.percentile}%; background: {metrics.color}"></div>
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>
			{:else if viewMode === 'hierarchy'}
				<!-- Hierarchy View -->
				<div class="hierarchy-view">
					<div class="hierarchy-container">
						{#each hierarchyLevels as level, levelIndex}
							<div class="hierarchy-level" style="--level-color: {level.color}">
								<div class="level-header">
									<span class="level-name">TIER {levelIndex + 1}</span>
									<span class="level-count">{level.members.length} ENTITIES</span>
								</div>
								<div class="level-members">
									{#each level.members as [executive, count]}
										<div class="member-card" 
											 on:click={() => drillDownExecutive(executive, count)}
											 style="border-color: {level.color}20; background: linear-gradient(135deg, {level.color}10, transparent)">
											<div class="member-avatar" style="border-color: {level.color}">
												<span style="color: {level.color}">◈</span>
											</div>
											<div class="member-info">
												<div class="member-name">{executive.substring(0, 25).toUpperCase()}</div>
												<div class="member-stats">
													<span class="stat">{count} nodes</span>
													<span class="stat">{getPercentage(count)}%</span>
												</div>
											</div>
											<div class="member-power">
												<div class="power-ring" style="border-color: {level.color}">
													<span>{calculateMetrics(count).powerLevel}</span>
												</div>
											</div>
										</div>
									{/each}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{:else if viewMode === 'pulse'}
				<!-- Pulse View -->
				<div class="pulse-view">
					<div class="pulse-container">
						<div class="pulse-core">
							<div class="pulse-ring ring-1" style="border-color: {neonColors.primary}"></div>
							<div class="pulse-ring ring-2" style="border-color: {neonColors.secondary}"></div>
							<div class="pulse-ring ring-3" style="border-color: {neonColors.tertiary}"></div>
							<div class="pulse-center">
								<span class="pulse-value">{energyFlow.toFixed(0)}%</span>
								<span class="pulse-label">NETWORK PULSE</span>
							</div>
						</div>
						
						<div class="pulse-nodes">
							{#each filteredExecutives.slice(0, 12) as [executive, count], i}
								{@const angle = (i / 12) * Math.PI * 2}
								{@const metrics = calculateMetrics(count)}
								<div class="pulse-node"
									 style="left: {50 + Math.cos(angle) * 35}%;
											top: {50 + Math.sin(angle) * 35}%"
									 on:click={() => drillDownExecutive(executive, count)}>
									<div class="node-pulse" style="background: {metrics.color}"></div>
									<div class="node-info">
										<span class="node-name">{executive.substring(0, 15)}</span>
										<span class="node-power" style="color: {metrics.color}">{metrics.powerLevel}%</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
					
					<!-- Live Data Stream -->
					<div class="pulse-stream">
						<h3>LIVE DATA STREAM</h3>
						<div class="stream-graph">
							<svg viewBox="0 0 400 100">
								<polyline points="{dataStream.map((d, i) => `${i * 8},${100 - d.value}`).join(' ')}"
										  fill="none" 
										  stroke="{neonColors.primary}" 
										  stroke-width="1" 
										  opacity="0.8" 
										  filter="url(#neonGlow)"/>
								{#each dataStream.slice(-10) as data, i}
									<circle cx="{320 + i * 8}" 
											cy="{100 - data.value}" 
											r="2" 
											fill="{data.type === 'neural' ? neonColors.primary : 
												   data.type === 'quantum' ? neonColors.secondary : 
												   neonColors.tertiary}"
											opacity="0.8"/>
								{/each}
							</svg>
						</div>
					</div>
				</div>
			{:else if viewMode === 'matrix'}
				<!-- Matrix View -->
				<div class="matrix-view">
					<div class="matrix-grid">
						{#each filteredExecutives as [executive, count], i}
							{@const metrics = calculateMetrics(count)}
							<div class="matrix-cell"
								 on:click={() => drillDownExecutive(executive, count)}
								 style="--cell-color: {metrics.color}">
								<div class="cell-background">
									<div class="cell-pattern"></div>
								</div>
								<div class="cell-content">
									<div class="cell-header">
										<span class="cell-icon" style="color: {metrics.color}">◈</span>
										<span class="cell-rank">#{i + 1}</span>
									</div>
									<div class="cell-name">{executive.substring(0, 20).toUpperCase()}</div>
									<div class="cell-metrics">
										<div class="metric-row">
											<span class="metric-label">NODES</span>
											<span class="metric-value" style="color: {metrics.color}">{count}</span>
										</div>
										<div class="metric-row">
											<span class="metric-label">POWER</span>
											<span class="metric-value" style="color: {metrics.color}">{metrics.powerLevel}%</span>
										</div>
									</div>
									<div class="cell-signature">{metrics.quantumSignature}</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.quantum-executive-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		position: relative;
		overflow: hidden;
		font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
	}
	
	/* Particle Universe Background */
	.particle-universe {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
	}
	
	.quantum-particle {
		position: absolute;
		border-radius: 50%;
		transition: all 0.3s ease;
		animation: particleFloat 20s linear infinite;
	}
	
	@keyframes particleFloat {
		0% { transform: translate(0, 0) scale(1) rotate(0deg); }
		25% { transform: translate(30px, -30px) scale(1.2) rotate(90deg); }
		50% { transform: translate(-20px, 20px) scale(0.8) rotate(180deg); }
		75% { transform: translate(40px, 10px) scale(1.1) rotate(270deg); }
		100% { transform: translate(0, 0) scale(1) rotate(360deg); }
	}
	
	/* Data Stream Layer */
	.data-stream-layer {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 2;
		opacity: 0.3;
	}
	
	/* Main Container */
	.executive-container {
		position: relative;
		z-index: 10;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
	
	/* Quantum Header */
	.quantum-header {
		background: linear-gradient(180deg, rgba(0, 255, 204, 0.05), rgba(0, 0, 0, 0.9));
		backdrop-filter: blur(20px);
		border-bottom: 1px solid rgba(0, 255, 204, 0.2);
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
	
	.quantum-logo {
		width: 60px;
		height: 60px;
		position: relative;
	}
	
	.logo-hologram {
		width: 100%;
		height: 100%;
		position: relative;
		transform-style: preserve-3d;
	}
	
	.hologram-ring {
		position: absolute;
		inset: 0;
		border: 1px solid;
		border-radius: 50%;
		animation: hologramRotate 3s linear infinite;
	}
	
	.ring-1 { inset: 0; }
	.ring-2 { inset: 10px; animation-direction: reverse; }
	.ring-3 { inset: 20px; animation-duration: 4s; }
	
	@keyframes hologramRotate {
		from { transform: rotateX(60deg) rotateZ(0deg); }
		to { transform: rotateX(60deg) rotateZ(360deg); }
	}
	
	.hologram-core {
		position: absolute;
		inset: 25px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		color: #00FFCC;
		text-shadow: 0 0 20px rgba(0, 255, 204, 0.8);
		animation: corePulse 2s ease-in-out infinite;
	}
	
	@keyframes corePulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.1); opacity: 0.8; }
	}
	
	.brand-text h1 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 200;
		letter-spacing: 0.3em;
		background: linear-gradient(90deg, #00FFCC, #FF00FF, #FFFF00);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		animation: gradientShift 5s linear infinite;
	}
	
	@keyframes gradientShift {
		0% { background-position: 0% 50%; }
		100% { background-position: 200% 50%; }
	}
	
	/* Glitch Effect */
	.glitch-title {
		position: relative;
	}
	
	.glitch-title::before,
	.glitch-title::after {
		content: attr(data-text);
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, #00FFCC, #FF00FF, #FFFF00);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}
	
	.glitch-title::before {
		animation: glitch-1 0.3s infinite;
		z-index: -1;
		text-shadow: -2px 0 #FF00FF;
	}
	
	.glitch-title::after {
		animation: glitch-2 0.3s infinite;
		z-index: -2;
		text-shadow: -2px 0 #00FFCC;
	}
	
	@keyframes glitch-1 {
		0%, 100% { clip-path: inset(0 0 0 0); }
		20% { clip-path: inset(20% 0 30% 0); transform: translate(-2px, 2px); }
		40% { clip-path: inset(50% 0 20% 0); transform: translate(2px, -2px); }
		60% { clip-path: inset(10% 0 60% 0); transform: translate(-1px, 1px); }
		80% { clip-path: inset(80% 0 5% 0); transform: translate(1px, -1px); }
	}
	
	@keyframes glitch-2 {
		0%, 100% { clip-path: inset(0 0 0 0); }
		20% { clip-path: inset(60% 0 10% 0); transform: translate(2px, 1px); }
		40% { clip-path: inset(20% 0 40% 0); transform: translate(-2px, -1px); }
		60% { clip-path: inset(30% 0 50% 0); transform: translate(1px, 2px); }
		80% { clip-path: inset(70% 0 15% 0); transform: translate(-1px, -2px); }
	}
	
	.quantum-status {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-top: 0.5rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
	}
	
	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: statusPulse 2s ease-in-out infinite;
	}
	
	@keyframes statusPulse {
		0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 currentColor; }
		50% { transform: scale(1.2); box-shadow: 0 0 0 4px transparent; }
	}
	
	.divider {
		color: rgba(255, 255, 255, 0.2);
	}
	
	/* Control Section */
	.control-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.search-container {
		position: relative;
	}
	
	.quantum-search {
		width: 100%;
		padding: 0.75rem 1rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 204, 0.2);
		border-radius: 8px;
		color: #00FFCC;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.9rem;
		letter-spacing: 0.05em;
		transition: all 0.3s ease;
	}
	
	.quantum-search::placeholder {
		color: rgba(0, 255, 204, 0.4);
	}
	
	.quantum-search:focus {
		outline: none;
		border-color: #00FFCC;
		background: rgba(0, 255, 204, 0.05);
		box-shadow: 0 0 30px rgba(0, 255, 204, 0.2);
	}
	
	.search-pulse {
		position: absolute;
		bottom: 0;
		left: 0;
		height: 1px;
		background: linear-gradient(90deg, transparent, #00FFCC, transparent);
		transition: width 0.3s ease;
		animation: pulseLine 2s linear infinite;
	}
	
	@keyframes pulseLine {
		0% { opacity: 0; }
		50% { opacity: 1; }
		100% { opacity: 0; }
	}
	
	.view-modes {
		display: flex;
		gap: 0.5rem;
	}
	
	.mode-btn {
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
	}
	
	.mode-btn:hover {
		border-color: var(--accent-color);
		background: rgba(0, 255, 204, 0.05);
		color: var(--accent-color);
	}
	
	.mode-btn.active {
		border-color: var(--accent-color);
		background: linear-gradient(135deg, rgba(0, 255, 204, 0.1), rgba(0, 0, 0, 0.6));
		color: var(--accent-color);
		box-shadow: 0 0 20px rgba(0, 255, 204, 0.2);
	}
	
	.mode-icon {
		font-size: 1.2rem;
	}
	
	.mode-label {
		font-size: 0.65rem;
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	/* Metrics Section */
	.metrics-section {
		display: flex;
		gap: 2rem;
	}
	
	.metric-display {
		text-align: center;
	}
	
	.metric-value {
		font-size: 1.8rem;
		font-weight: 100;
		font-family: 'JetBrains Mono', monospace;
		text-shadow: 0 0 20px currentColor;
	}
	
	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.2em;
		margin-top: 0.25rem;
		font-weight: 500;
	}
	
	/* Interface Body */
	.interface-body {
		flex: 1;
		overflow: hidden;
		padding: 2rem;
	}
	
	/* Loading State */
	.quantum-loading {
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.loading-vortex {
		position: relative;
		width: 120px;
		height: 120px;
	}
	
	.vortex-ring {
		position: absolute;
		inset: 0;
		border: 2px solid;
		border-radius: 50%;
		animation: vortexSpin 3s linear infinite;
	}
	
	.vortex-ring:nth-child(2) {
		inset: 20px;
	}
	
	.vortex-ring:nth-child(3) {
		inset: 40px;
	}
	
	@keyframes vortexSpin {
		from { transform: rotate(0deg) scale(1); }
		50% { transform: rotate(180deg) scale(1.1); }
		to { transform: rotate(360deg) scale(1); }
	}
	
	.vortex-center {
		position: absolute;
		inset: 45px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		color: #00FFCC;
		text-shadow: 0 0 30px rgba(0, 255, 204, 0.8);
		animation: pulse 2s ease-in-out infinite;
	}
	
	@keyframes pulse {
		0%, 100% { opacity: 0.5; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.1); }
	}
	
	.loading-text {
		color: rgba(0, 255, 204, 0.6);
		font-size: 0.9rem;
		letter-spacing: 0.2em;
		animation: pulse 2s ease-in-out infinite;
	}
	
	/* Neural View */
	.neural-view {
		height: 100%;
		display: grid;
		grid-template-columns: 1fr 400px;
		gap: 2rem;
	}
	
	.neural-container {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 204, 0.1);
		border-radius: 16px;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}
	
	.neural-network {
		width: 100%;
		height: 100%;
		cursor: move;
	}
	
	.neural-node {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.neural-node:hover {
		transform: scale(1.2);
	}
	
	.neural-panel {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 204, 0.1);
		border-radius: 16px;
		padding: 1.5rem;
		overflow-y: auto;
	}
	
	.neural-panel h3 {
		margin: 0 0 1rem 0;
		font-size: 0.9rem;
		color: #00FFCC;
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	.metrics-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.metric-item {
		background: rgba(0, 255, 204, 0.02);
		border: 1px solid rgba(0, 255, 204, 0.1);
		border-radius: 8px;
		padding: 0.75rem;
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.metric-item:hover {
		background: rgba(0, 255, 204, 0.05);
		border-color: rgba(0, 255, 204, 0.3);
		transform: translateX(5px);
	}
	
	.item-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}
	
	.item-name {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
		letter-spacing: 0.05em;
	}
	
	.item-value {
		font-size: 0.85rem;
		font-weight: 600;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.item-bar {
		height: 3px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	/* Hierarchy View */
	.hierarchy-view {
		height: 100%;
		overflow-y: auto;
	}
	
	.hierarchy-container {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}
	
	.hierarchy-level {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 16px;
		padding: 1.5rem;
		border-left: 3px solid var(--level-color);
	}
	
	.level-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 0.75rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.level-name {
		font-size: 0.9rem;
		color: var(--level-color);
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	.level-count {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.level-members {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1rem;
	}
	
	.member-card {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.member-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
	}
	
	.member-avatar {
		width: 40px;
		height: 40px;
		border: 2px solid;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.2rem;
	}
	
	.member-info {
		flex: 1;
	}
	
	.member-name {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.9);
		margin-bottom: 0.25rem;
		letter-spacing: 0.05em;
	}
	
	.member-stats {
		display: flex;
		gap: 0.75rem;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.member-power {
		display: flex;
		align-items: center;
	}
	
	.power-ring {
		width: 36px;
		height: 36px;
		border: 2px solid;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.75rem;
		font-weight: 600;
	}
	
	/* Pulse View */
	.pulse-view {
		height: 100%;
		display: grid;
		grid-template-columns: 1fr 400px;
		gap: 2rem;
	}
	
	.pulse-container {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 204, 0.1);
		border-radius: 16px;
		position: relative;
		overflow: hidden;
	}
	
	.pulse-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 200px;
		height: 200px;
	}
	
	.pulse-ring {
		position: absolute;
		inset: 0;
		border: 2px solid;
		border-radius: 50%;
		animation: pulseExpand 3s ease-out infinite;
	}
	
	.ring-2 {
		inset: 30px;
		animation-delay: 1s;
	}
	
	.ring-3 {
		inset: 60px;
		animation-delay: 2s;
	}
	
	@keyframes pulseExpand {
		0% { transform: scale(1); opacity: 1; }
		100% { transform: scale(2); opacity: 0; }
	}
	
	.pulse-center {
		position: absolute;
		inset: 70px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		background: radial-gradient(circle, rgba(0, 255, 204, 0.2), transparent);
		border-radius: 50%;
	}
	
	.pulse-value {
		font-size: 1.5rem;
		font-weight: 100;
		color: #00FFCC;
		font-family: 'JetBrains Mono', monospace;
		text-shadow: 0 0 20px rgba(0, 255, 204, 0.8);
	}
	
	.pulse-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		margin-top: 0.25rem;
	}
	
	.pulse-nodes {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}
	
	.pulse-node {
		position: absolute;
		transform: translate(-50%, -50%);
		cursor: pointer;
		pointer-events: all;
		transition: all 0.3s ease;
	}
	
	.pulse-node:hover {
		z-index: 10;
		transform: translate(-50%, -50%) scale(1.2);
	}
	
	.node-pulse {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		animation: nodePulse 2s ease-in-out infinite;
	}
	
	@keyframes nodePulse {
		0%, 100% { transform: scale(1); opacity: 0.3; }
		50% { transform: scale(1.3); opacity: 0.6; }
	}
	
	.node-info {
		position: absolute;
		top: 100%;
		left: 50%;
		transform: translateX(-50%);
		margin-top: 0.5rem;
		text-align: center;
		white-space: nowrap;
	}
	
	.node-name {
		display: block;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.7);
		margin-bottom: 0.25rem;
	}
	
	.node-power {
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.pulse-stream {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 204, 0.1);
		border-radius: 16px;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
	}
	
	.pulse-stream h3 {
		margin: 0 0 1rem 0;
		font-size: 0.9rem;
		color: #00FFCC;
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	.stream-graph {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.stream-graph svg {
		width: 100%;
		height: 100%;
	}
	
	/* Matrix View */
	.matrix-view {
		height: 100%;
		overflow: auto;
	}
	
	.matrix-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 1rem;
		padding: 1rem;
	}
	
	.matrix-cell {
		position: relative;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		overflow: hidden;
		cursor: pointer;
		transition: all 0.3s ease;
		--cell-color: #00FFCC;
	}
	
	.matrix-cell:hover {
		transform: translateY(-4px);
		border-color: var(--cell-color);
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.8), 0 0 40px rgba(0, 255, 204, 0.2);
	}
	
	.cell-background {
		position: absolute;
		inset: 0;
		opacity: 0.05;
	}
	
	.cell-pattern {
		width: 100%;
		height: 100%;
		background-image: 
			repeating-linear-gradient(45deg, var(--cell-color) 0, var(--cell-color) 1px, transparent 1px, transparent 15px),
			repeating-linear-gradient(-45deg, var(--cell-color) 0, var(--cell-color) 1px, transparent 1px, transparent 15px);
		opacity: 0.1;
	}
	
	.cell-content {
		position: relative;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.cell-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.cell-icon {
		font-size: 1.2rem;
	}
	
	.cell-rank {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.4);
		font-weight: 600;
	}
	
	.cell-name {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.9);
		letter-spacing: 0.05em;
		font-weight: 500;
	}
	
	.cell-metrics {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.metric-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.65rem;
	}
	
	.metric-label {
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.05em;
	}
	
	.metric-value {
		font-weight: 600;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.cell-signature {
		font-size: 0.5rem;
		color: rgba(255, 255, 255, 0.3);
		font-family: 'JetBrains Mono', monospace;
		letter-spacing: 0.05em;
		text-align: center;
		padding-top: 0.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	/* Detail Interface */
	.executive-detail-interface {
		height: 100%;
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
		background: linear-gradient(135deg, rgba(0, 255, 204, 0.05), rgba(0, 0, 0, 0.8));
		border: 1px solid rgba(0, 255, 204, 0.2);
		border-radius: 16px;
	}
	
	.executive-identity {
		display: flex;
		align-items: center;
		gap: 2rem;
	}
	
	.identity-avatar {
		width: 100px;
		height: 100px;
		border: 2px solid;
		border-radius: 50%;
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.avatar-core {
		font-size: 2.5rem;
		color: #00FFCC;
		text-shadow: 0 0 30px rgba(0, 255, 204, 0.8);
		z-index: 2;
	}
	
	.avatar-rings {
		position: absolute;
		inset: -10px;
		pointer-events: none;
	}
	
	.avatar-rings .ring {
		position: absolute;
		inset: 0;
		border: 1px solid;
		border-radius: 50%;
		animation: avatarRingRotate 4s linear infinite;
	}
	
	.avatar-rings .ring:nth-child(2) {
		inset: 10px;
		animation-direction: reverse;
		animation-duration: 6s;
	}
	
	@keyframes avatarRingRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.identity-data {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.executive-name {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 200;
		color: #00FFCC;
		letter-spacing: 0.1em;
		text-shadow: 0 0 20px rgba(0, 255, 204, 0.5);
	}
	
	.quantum-signature {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}
	
	.executive-tags {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}
	
	.tag {
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-size: 0.75rem;
		font-weight: 500;
		letter-spacing: 0.05em;
		border: 1px solid currentColor;
	}
	
	.close-detail {
		width: 48px;
		height: 48px;
		background: rgba(255, 0, 136, 0.1);
		border: 1px solid #FF0088;
		border-radius: 12px;
		color: #FF0088;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.close-detail:hover {
		background: rgba(255, 0, 136, 0.2);
		transform: rotate(90deg);
		box-shadow: 0 0 30px rgba(255, 0, 136, 0.5);
	}
	
	.close-icon {
		font-size: 1.5rem;
	}
	
	.detail-metrics {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1.5rem;
	}
	
	.metric-card {
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
	
	.metric-card::before {
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
	
	.card-icon {
		font-size: 1.5rem;
		text-shadow: 0 0 20px currentColor;
	}
	
	.card-content {
		flex: 1;
	}
	
	.card-value {
		font-size: 1.8rem;
		font-weight: 100;
		color: #00FFCC;
		font-family: 'JetBrains Mono', monospace;
		text-shadow: 0 0 20px rgba(0, 255, 204, 0.5);
	}
	
	.card-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		margin-top: 0.5rem;
	}
	
	.card-graph,
	.card-progress,
	.card-indicator,
	.card-threat {
		margin-top: auto;
		height: 40px;
	}
	
	.card-graph svg {
		width: 100%;
		height: 100%;
	}
	
	.progress-track {
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.progress-fill {
		height: 100%;
		transition: width 0.5s ease;
		animation: progressPulse 2s ease-in-out infinite;
	}
	
	@keyframes progressPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}
	
	.indicator-ring {
		width: 40px;
		height: 40px;
		border: 2px solid;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		animation: indicatorRotate 4s linear infinite;
	}
	
	@keyframes indicatorRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.indicator-value {
		font-size: 0.75rem;
		font-weight: 600;
	}
	
	.threat-bars {
		display: flex;
		gap: 2px;
		height: 100%;
		align-items: flex-end;
	}
	
	.threat-bar {
		flex: 1;
		height: 100%;
		border-radius: 1px;
		transition: all 0.3s ease;
	}
	
	.detail-stream {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 204, 0.1);
		border-radius: 16px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.stream-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
		background: rgba(0, 0, 0, 0.4);
		border-bottom: 1px solid rgba(0, 255, 204, 0.1);
	}
	
	.stream-header h3 {
		margin: 0;
		font-size: 0.9rem;
		color: #00FFCC;
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	.stream-controls {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	
	.stream-status {
		font-size: 0.7rem;
		color: #00FF88;
		letter-spacing: 0.1em;
		font-weight: 500;
	}
	
	.stream-indicator {
		width: 8px;
		height: 8px;
		background: #00FF88;
		border-radius: 50%;
		animation: streamBlink 1s ease-in-out infinite;
	}
	
	@keyframes streamBlink {
		0%, 100% { opacity: 1; box-shadow: 0 0 10px #00FF88; }
		50% { opacity: 0.3; box-shadow: none; }
	}
	
	.stream-content {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}
	
	.quantum-table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0;
	}
	
	.quantum-table th {
		background: rgba(0, 0, 0, 0.6);
		color: rgba(0, 255, 204, 0.7);
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 500;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 1px solid rgba(0, 255, 204, 0.2);
	}
	
	.data-row {
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.03);
	}
	
	.data-row:hover {
		background: rgba(0, 255, 204, 0.02);
	}
	
	.quantum-table td {
		padding: 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.node-id {
		font-family: 'JetBrains Mono', monospace;
		color: #00FFCC;
		font-size: 0.7rem;
		letter-spacing: 0.05em;
	}
	
	.sync-indicator,
	.shield-indicator {
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
		.header-grid {
			grid-template-columns: 1fr;
			gap: 1.5rem;
		}
		
		.metrics-section {
			justify-content: flex-start;
		}
		
		.detail-metrics {
			grid-template-columns: repeat(2, 1fr);
		}
	}
	
	@media (max-width: 1200px) {
		.neural-view {
			grid-template-columns: 1fr;
		}
		
		.neural-panel {
			display: none;
		}
		
		.pulse-view {
			grid-template-columns: 1fr;
		}
		
		.pulse-stream {
			display: none;
		}
	}
	
	@media (max-width: 768px) {
		.interface-body {
			padding: 1rem;
		}
		
		.matrix-grid {
			grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		}
		
		.level-members {
			grid-template-columns: 1fr;
		}
		
		.detail-metrics {
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
		background: linear-gradient(180deg, #00FFCC, #FF00FF);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(180deg, #00FFCC, #FFFF00);
	}