<!-- CIOMetrics.svelte - Executive Neural Command Interface -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedExecutive = null;
	let executiveDetails = [];
	let searchTerm = '';
	
	// Neural visualization states
	let neuralNodes = [];
	let synapses = [];
	let brainwaves = [];
	let consciousness = 0;
	let synapticActivity = [];
	let memoryFragments = [];
	let thoughtPatterns = [];
	let executiveProfiles = new Map();
	
	// Animation controllers
	let animationFrames = {
		neural: null,
		waves: null,
		memory: null
	};
	
	// Holographic display
	let hologramLayers = [];
	let dataStreams = [];
	let quantumEntanglement = [];
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/cio_metrics');
			data = await response.json();
			loading = false;
			initializeNeuralNetwork();
			startConsciousnessSimulation();
		} catch (err) {
			console.error('Executive neural sync failed:', err);
			loading = false;
		}
	});
	
	onDestroy(() => {
		Object.values(animationFrames).forEach(frame => {
			if (frame) cancelAnimationFrame(frame);
		});
	});
	
	function initializeNeuralNetwork() {
		if (!data.operative_intelligence) return;
		
		let executives = Object.entries(data.operative_intelligence)
			.sort((a, b) => b[1] - a[1])
			.slice(0, 50);
		
		// Create neural nodes with 3D positioning
		executives.forEach(([exec, count], i) => {
			let phi = Math.acos(-1 + (2 * i) / executives.length);
			let theta = Math.sqrt(executives.length * Math.PI) * phi;
			
			let node = {
				id: exec,
				count: count,
				x: Math.cos(theta) * Math.sin(phi) * 300,
				y: Math.sin(theta) * Math.sin(phi) * 300,
				z: Math.cos(phi) * 300,
				// Neural properties
				activation: Math.random(),
				frequency: 5 + Math.random() * 45, // Hz
				coherence: Math.random(),
				resonance: [],
				memories: generateMemoryFragments(count),
				thoughtStream: [],
				influence: calculateInfluence(count, executives),
				connections: []
			};
			
			neuralNodes.push(node);
			executiveProfiles.set(exec, generateProfile(exec, count));
		});
		
		// Create synaptic connections based on data patterns
		createSynapticNetwork();
		
		// Initialize brainwave patterns
		for (let i = 0; i < 100; i++) {
			brainwaves.push({
				frequency: Math.random() * 40 + 10,
				amplitude: Math.random(),
				phase: Math.random() * Math.PI * 2,
				type: ['alpha', 'beta', 'gamma', 'theta', 'delta'][Math.floor(Math.random() * 5)]
			});
		}
		
		// Create holographic layers
		for (let i = 0; i < 5; i++) {
			hologramLayers.push({
				depth: i * 50,
				opacity: 1 - (i * 0.15),
				rotation: Math.random() * 360,
				particles: generateHologramParticles(20)
			});
		}
	}
	
	function generateMemoryFragments(seed) {
		let fragments = [];
		for (let i = 0; i < 5; i++) {
			fragments.push({
				timestamp: Date.now() - Math.random() * 86400000 * 30,
				intensity: Math.random(),
				encrypted: Math.random() > 0.7,
				data: `MEMORY_${(seed * (i + 1) * 997).toString(16).toUpperCase()}`
			});
		}
		return fragments;
	}
	
	function generateProfile(exec, count) {
		return {
			neuralSignature: generateNeuralSignature(count),
			psychometrics: {
				leadership: 50 + Math.random() * 50,
				innovation: 50 + Math.random() * 50,
				riskTolerance: 50 + Math.random() * 50,
				systemThinking: 50 + Math.random() * 50
			},
			cognitiveBandwidth: Math.log10(count + 1) * 30,
			decisionVelocity: 100 - (1 / (count + 1)) * 1000,
			networkCentrality: 0,
			quantumCoherence: Math.random()
		};
	}
	
	function generateNeuralSignature(seed) {
		let signature = '';
		let pattern = seed * 9973;
		for (let i = 0; i < 32; i++) {
			pattern = (pattern * 1103515245 + 12345) & 0x7fffffff;
			signature += (pattern % 16).toString(16);
			if (i % 8 === 7 && i < 31) signature += '-';
		}
		return signature.toUpperCase();
	}
	
	function calculateInfluence(count, allExecutives) {
		let maxCount = Math.max(...allExecutives.map(([, c]) => c));
		let minCount = Math.min(...allExecutives.map(([, c]) => c));
		let normalized = (count - minCount) / (maxCount - minCount || 1);
		
		return {
			local: normalized * 100,
			global: normalized * 80 + Math.random() * 20,
			quantum: Math.sin(normalized * Math.PI) * 100,
			temporal: 50 + Math.cos(normalized * Math.PI * 2) * 50
		};
	}
	
	function createSynapticNetwork() {
		neuralNodes.forEach((node, i) => {
			// Connect to nearby nodes based on data similarity
			let connectionCount = Math.min(5, Math.floor(Math.random() * 8) + 2);
			let connected = new Set();
			
			for (let j = 0; j < connectionCount; j++) {
				let targetIdx = Math.floor(Math.random() * neuralNodes.length);
				if (targetIdx !== i && !connected.has(targetIdx)) {
					connected.add(targetIdx);
					node.connections.push(targetIdx);
					
					synapses.push({
						source: i,
						target: targetIdx,
						strength: Math.random(),
						neurotransmitter: ['dopamine', 'serotonin', 'gaba', 'glutamate'][Math.floor(Math.random() * 4)],
						firing: false,
						delay: Math.random() * 100
					});
				}
			}
		});
		
		// Calculate network centrality
		neuralNodes.forEach(node => {
			let profile = executiveProfiles.get(node.id);
			if (profile) {
				profile.networkCentrality = (node.connections.length / neuralNodes.length) * 100;
			}
		});
	}
	
	function generateHologramParticles(count) {
		let particles = [];
		for (let i = 0; i < count; i++) {
			particles.push({
				x: Math.random() * 100,
				y: Math.random() * 100,
				z: Math.random() * 100,
				vx: (Math.random() - 0.5) * 0.5,
				vy: (Math.random() - 0.5) * 0.5,
				vz: (Math.random() - 0.5) * 0.5,
				life: Math.random(),
				color: `hsl(${180 + Math.random() * 60}, 100%, ${60 + Math.random() * 20}%)`
			});
		}
		return particles;
	}
	
	function startConsciousnessSimulation() {
		let time = 0;
		
		function updateNeuralActivity() {
			time += 0.016; // ~60fps
			
			// Update consciousness level
			consciousness = 50 + Math.sin(time * 0.5) * 30 + Math.sin(time * 1.3) * 20;
			
			// Update neural nodes
			neuralNodes.forEach((node, i) => {
				node.activation = 0.5 + Math.sin(time + i * 0.1) * 0.5;
				node.frequency = 5 + Math.sin(time * 0.7 + i * 0.2) * 40;
				node.coherence = Math.abs(Math.sin(time * 0.3 + i * 0.15));
				
				// Simulate thought patterns
				if (Math.random() < 0.01) {
					node.thoughtStream.push({
						timestamp: Date.now(),
						pattern: generateThoughtPattern(),
						intensity: Math.random()
					});
					if (node.thoughtStream.length > 10) {
						node.thoughtStream.shift();
					}
				}
			});
			
			// Update synapses
			synapses.forEach(synapse => {
				if (Math.random() < 0.05) {
					synapse.firing = true;
					setTimeout(() => { synapse.firing = false; }, synapse.delay);
				}
				synapse.strength = Math.max(0.1, Math.min(1, synapse.strength + (Math.random() - 0.5) * 0.01));
			});
			
			// Update brainwaves
			brainwaves.forEach(wave => {
				wave.phase += wave.frequency * 0.01;
				wave.amplitude = 0.5 + Math.sin(time * 0.5 + wave.phase) * 0.5;
			});
			
			// Update hologram layers
			hologramLayers.forEach((layer, i) => {
				layer.rotation += 0.1 * (i + 1);
				layer.particles.forEach(p => {
					p.x = (p.x + p.vx + 100) % 100;
					p.y = (p.y + p.vy + 100) % 100;
					p.z = (p.z + p.vz + 100) % 100;
					p.life = (p.life + 0.01) % 1;
				});
			});
			
			// Generate synaptic activity patterns
			synapticActivity = Array(50).fill(0).map((_, i) => 
				50 + Math.sin(time * 2 + i * 0.2) * 30 + Math.random() * 20
			);
			
			animationFrames.neural = requestAnimationFrame(updateNeuralActivity);
		}
		
		updateNeuralActivity();
	}
	
	function generateThoughtPattern() {
		const patterns = [
			'STRATEGIC_ANALYSIS',
			'RISK_ASSESSMENT',
			'INNOVATION_SYNTHESIS',
			'RESOURCE_OPTIMIZATION',
			'NETWORK_EXPANSION',
			'QUANTUM_DECISION',
			'PREDICTIVE_MODELING',
			'CHAOS_NAVIGATION'
		];
		return patterns[Math.floor(Math.random() * patterns.length)];
	}
	
	$: filteredExecutives = data.operative_intelligence ? 
		Object.entries(data.operative_intelligence)
			.filter(([exec]) => exec.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxAssets = filteredExecutives.length > 0 ? Math.max(...filteredExecutives.map(([,c]) => c)) : 1;
	$: minAssets = filteredExecutives.length > 0 ? Math.min(...filteredExecutives.map(([,c]) => c)) : 0;
	
	function getExecutiveClass(count) {
		let normalized = (count - minAssets) / (maxAssets - minAssets || 1);
		let percentile = normalized * 100;
		
		// Dynamic classification without hardcoding titles
		if (percentile >= 90) {
			return {
				level: 'APEX_NEURAL',
				color: '#FF79C6', // Neon pink
				glow: '#FF79C640',
				symbol: '◈',
				description: 'Maximum Consciousness'
			};
		} else if (percentile >= 70) {
			return {
				level: 'QUANTUM_SYNC',
				color: '#8BE9FD', // Neon cyan
				glow: '#8BE9FD40',
				symbol: '◆',
				description: 'High Coherence'
			};
		} else if (percentile >= 50) {
			return {
				level: 'NEURAL_PRIME',
				color: '#BD93F9', // Neon purple
				glow: '#BD93F940',
				symbol: '▲',
				description: 'Active Network'
			};
		} else if (percentile >= 30) {
			return {
				level: 'SYNAPTIC_NODE',
				color: '#50FA7B', // Neon green
				glow: '#50FA7B40',
				symbol: '●',
				description: 'Emerging Pattern'
			};
		} else {
			return {
				level: 'QUANTUM_SEED',
				color: '#F1FA8C', // Neon yellow
				glow: '#F1FA8C40',
				symbol: '○',
				description: 'Initializing'
			};
		}
	}
	
	async function drillDownExecutive(executive, count) {
		selectedExecutive = { executive, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(executive)}`);
			let result = await response.json();
			executiveDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Executive deep scan failed:', err);
			executiveDetails = [];
			loading = false;
		}
	}
	
	function closeDetails() {
		selectedExecutive = null;
		executiveDetails = [];
	}
</script>

<div class="neural-command-interface">
	<!-- Consciousness Background -->
	<div class="consciousness-field">
		<!-- Brainwave visualization -->
		<svg class="brainwave-canvas" viewBox="0 0 100 100">
			<defs>
				<filter id="neuralGlow">
					<feGaussianBlur stdDeviation="2" result="coloredBlur"/>
					<feMerge>
						<feMergeNode in="coloredBlur"/>
						<feMergeNode in="SourceGraphic"/>
					</feMerge>
				</filter>
				<linearGradient id="waveGradient" x1="0%" y1="0%" x2="100%" y2="0%">
					<stop offset="0%" style="stop-color:#FF79C6;stop-opacity:0" />
					<stop offset="50%" style="stop-color:#8BE9FD;stop-opacity:1" />
					<stop offset="100%" style="stop-color:#FF79C6;stop-opacity:0" />
				</linearGradient>
			</defs>
			
			<!-- Brainwave patterns -->
			{#each brainwaves as wave, i}
				<path d="M 0,{50 + Math.sin(wave.phase) * wave.amplitude * 30} 
						 Q 25,{50 + Math.sin(wave.phase + 1) * wave.amplitude * 30} 
						   50,{50 + Math.sin(wave.phase + 2) * wave.amplitude * 30}
						 T 100,{50 + Math.sin(wave.phase + 3) * wave.amplitude * 30}"
					  stroke="url(#waveGradient)"
					  stroke-width="0.5"
					  fill="none"
					  opacity="{wave.amplitude * 0.3}"
					  filter="url(#neuralGlow)"/>
			{/each}
		</svg>
		
		<!-- Holographic layers -->
		{#each hologramLayers as layer}
			<div class="hologram-layer" 
				 style="transform: translateZ({layer.depth}px) rotateY({layer.rotation}deg); 
						opacity: {layer.opacity}">
				{#each layer.particles as particle}
					<div class="hologram-particle"
						 style="left: {particle.x}%; 
								top: {particle.y}%; 
								background: {particle.color};
								opacity: {particle.life}">
					</div>
				{/each}
			</div>
		{/each}
	</div>
	
	<div class="executive-neural-interface">
		<!-- Neural Header -->
		<header class="neural-header">
			<div class="header-consciousness">
				<div class="consciousness-core">
					<div class="core-rings">
						<div class="ring ring-outer" style="animation-duration: 8s"></div>
						<div class="ring ring-middle" style="animation-duration: 6s; animation-direction: reverse"></div>
						<div class="ring ring-inner" style="animation-duration: 4s"></div>
					</div>
					<div class="core-symbol">◈</div>
				</div>
				<div class="consciousness-info">
					<h1 class="neural-title">EXECUTIVE NEURAL MATRIX</h1>
					<div class="consciousness-metrics">
						<div class="metric-item">
							<span class="metric-label">CONSCIOUSNESS</span>
							<div class="metric-bar">
								<div class="bar-fill" style="width: {consciousness}%; background: linear-gradient(90deg, #FF79C6, #8BE9FD)"></div>
							</div>
							<span class="metric-value">{consciousness.toFixed(0)}%</span>
						</div>
					</div>
				</div>
			</div>
			
			<div class="neural-search">
				<div class="search-container">
					<input type="text" 
						   bind:value={searchTerm}
						   placeholder="NEURAL SEARCH..."
						   class="search-input"/>
					<div class="search-pulse"></div>
				</div>
				<div class="search-feedback">
					{#if searchTerm}
						<span class="feedback-text">SCANNING {filteredExecutives.length} NEURAL PATTERNS</span>
					{/if}
				</div>
			</div>
			
			<div class="header-stats">
				<div class="stat-display">
					<div class="stat-value">{filteredExecutives.length}</div>
					<div class="stat-label">NEURAL NODES</div>
				</div>
				<div class="stat-display">
					<div class="stat-value">{synapses.length}</div>
					<div class="stat-label">SYNAPSES</div>
				</div>
				<div class="stat-display">
					<div class="stat-value">{(data.operative_intelligence ? Object.values(data.operative_intelligence).reduce((a, b) => a + b, 0) : 0).toLocaleString()}</div>
					<div class="stat-label">CONNECTIONS</div>
				</div>
			</div>
		</header>
		
		<!-- Main Neural Display -->
		<div class="neural-display">
			{#if loading && !selectedExecutive}
				<div class="neural-loading">
					<div class="loading-brain">
						<div class="brain-hemisphere left"></div>
						<div class="brain-hemisphere right"></div>
						<div class="brain-stem"></div>
						<div class="neural-pulse"></div>
					</div>
					<p class="loading-text">INITIALIZING CONSCIOUSNESS...</p>
				</div>
			{:else if selectedExecutive}
				<div class="executive-deep-dive">
					<div class="deep-header">
						<div class="executive-identity">
							<div class="identity-visualization">
								<div class="identity-core" style="background: {getExecutiveClass(selectedExecutive.count).color}">
									{getExecutiveClass(selectedExecutive.count).symbol}
								</div>
								<div class="identity-rings">
									<div class="identity-ring ring-1"></div>
									<div class="identity-ring ring-2"></div>
									<div class="identity-ring ring-3"></div>
								</div>
							</div>
							<div class="identity-data">
								<h2 class="executive-name">{selectedExecutive.executive.toUpperCase()}</h2>
								<div class="neural-signature">
									{executiveProfiles.get(selectedExecutive.executive)?.neuralSignature || 'UNKNOWN'}
								</div>
							</div>
						</div>
						<button class="close-neural" on:click={closeDetails}>
							<span>✕</span>
						</button>
					</div>
					
					{#if executiveProfiles.get(selectedExecutive.executive)}
						{@const profile = executiveProfiles.get(selectedExecutive.executive)}
						<div class="psychometric-display">
							<div class="psychometric-grid">
								<div class="psychometric-card">
									<div class="psych-label">LEADERSHIP</div>
									<div class="psych-visualization">
										<svg viewBox="0 0 100 100">
											<circle cx="50" cy="50" r="40" fill="none" stroke="#FF79C620" stroke-width="8"/>
											<circle cx="50" cy="50" r="40" fill="none" stroke="#FF79C6" stroke-width="8"
													stroke-dasharray="{profile.psychometrics.leadership * 2.51} 251"
													transform="rotate(-90 50 50)"/>
										</svg>
										<div class="psych-value">{profile.psychometrics.leadership.toFixed(0)}%</div>
									</div>
								</div>
								<div class="psychometric-card">
									<div class="psych-label">INNOVATION</div>
									<div class="psych-visualization">
										<svg viewBox="0 0 100 100">
											<circle cx="50" cy="50" r="40" fill="none" stroke="#8BE9FD20" stroke-width="8"/>
											<circle cx="50" cy="50" r="40" fill="none" stroke="#8BE9FD" stroke-width="8"
													stroke-dasharray="{profile.psychometrics.innovation * 2.51} 251"
													transform="rotate(-90 50 50)"/>
										</svg>
										<div class="psych-value">{profile.psychometrics.innovation.toFixed(0)}%</div>
									</div>
								</div>
								<div class="psychometric-card">
									<div class="psych-label">RISK TOLERANCE</div>
									<div class="psych-visualization">
										<svg viewBox="0 0 100 100">
											<circle cx="50" cy="50" r="40" fill="none" stroke="#BD93F920" stroke-width="8"/>
											<circle cx="50" cy="50" r="40" fill="none" stroke="#BD93F9" stroke-width="8"
													stroke-dasharray="{profile.psychometrics.riskTolerance * 2.51} 251"
													transform="rotate(-90 50 50)"/>
										</svg>
										<div class="psych-value">{profile.psychometrics.riskTolerance.toFixed(0)}%</div>
									</div>
								</div>
								<div class="psychometric-card">
									<div class="psych-label">SYSTEM THINKING</div>
									<div class="psych-visualization">
										<svg viewBox="0 0 100 100">
											<circle cx="50" cy="50" r="40" fill="none" stroke="#50FA7B20" stroke-width="8"/>
											<circle cx="50" cy="50" r="40" fill="none" stroke="#50FA7B" stroke-width="8"
													stroke-dasharray="{profile.psychometrics.systemThinking * 2.51} 251"
													transform="rotate(-90 50 50)"/>
										</svg>
										<div class="psych-value">{profile.psychometrics.systemThinking.toFixed(0)}%</div>
									</div>
								</div>
							</div>
						</div>
					{/if}
					
					<div class="neural-connections-stream">
						<table class="connections-table">
							<thead>
								<tr>
									<th>NODE_ID</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>INFRASTRUCTURE</th>
									<th>SYNC_STATUS</th>
									<th>SECURITY</th>
								</tr>
							</thead>
							<tbody>
								{#each executiveDetails as host}
									<tr class="connection-row">
										<td class="node-id">{host.host.substring(0, 30)}</td>
										<td>{host.region || 'UNKNOWN'}</td>
										<td>{host.country || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>
											<span class="sync-indicator {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'synced' : 'desynced'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}
											</span>
										</td>
										<td>
											<span class="security-indicator {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'secured' : 'vulnerable'}">
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
				<!-- Neural Network Visualization -->
				<div class="neural-visualization">
					<div class="neural-3d-space">
						<!-- Synaptic connections -->
						<svg class="synaptic-network" viewBox="-400 -400 800 800">
							<defs>
								<radialGradient id="nodeGradient">
									<stop offset="0%" style="stop-color:#8BE9FD;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#8BE9FD;stop-opacity:0" />
								</radialGradient>
							</defs>
							
							<!-- Draw synapses -->
							{#each synapses as synapse}
								{#if neuralNodes[synapse.source] && neuralNodes[synapse.target]}
									<line x1="{neuralNodes[synapse.source].x}" 
										  y1="{neuralNodes[synapse.source].y}"
										  x2="{neuralNodes[synapse.target].x}" 
										  y2="{neuralNodes[synapse.target].y}"
										  stroke="{synapse.firing ? '#FF79C6' : '#8BE9FD'}"
										  stroke-width="{synapse.strength * 2}"
										  opacity="{synapse.strength * 0.3 + (synapse.firing ? 0.5 : 0)}"
										  stroke-dasharray="{synapse.firing ? 'none' : '2,3'}">
										{#if synapse.firing}
											<animate attributeName="stroke-opacity" 
													 values="0.3;1;0.3" 
													 dur="0.5s" 
													 repeatCount="1"/>
										{/if}
									</line>
								{/if}
							{/each}
							
							<!-- Draw neural nodes -->
							{#each neuralNodes.slice(0, 30) as node, i}
								{@const executiveClass = getExecutiveClass(node.count)}
								<g class="neural-node-group"
								   transform="translate({node.x}, {node.y})"
								   on:click={() => drillDownExecutive(node.id, node.count)}>
									<!-- Node glow effect -->
									<circle r="{20 + node.activation * 20}" 
											fill="{executiveClass.color}" 
											opacity="{node.activation * 0.2}"
											filter="url(#neuralGlow)"/>
									<!-- Node core -->
									<circle r="{10 + node.coherence * 10}" 
											fill="{executiveClass.color}" 
											opacity="0.8"/>
									<!-- Node symbol -->
									<text text-anchor="middle" 
										  dy="4" 
										  fill="#000000" 
										  font-size="12" 
										  font-weight="bold">
										{executiveClass.symbol}
									</text>
									<!-- Node label -->
									<text y="{-20 - node.activation * 10}" 
										  text-anchor="middle" 
										  fill="#FFFFFF" 
										  font-size="10" 
										  opacity="0.9">
										{node.id.substring(0, 15)}
									</text>
								</g>
							{/each}
						</svg>
						
						<!-- Synaptic activity graph -->
						<div class="synaptic-activity">
							<svg viewBox="0 0 200 50">
								<polyline points="{synapticActivity.map((val, i) => `${i * 4},${50 - val * 0.5}`).join(' ')}"
										  fill="none" 
										  stroke="#8BE9FD" 
										  stroke-width="1"
										  opacity="0.8"/>
							</svg>
							<div class="activity-label">SYNAPTIC ACTIVITY</div>
						</div>
					</div>
					
					<!-- Executive Matrix Table -->
					<div class="executive-matrix">
						<table class="matrix-table">
							<thead>
								<tr>
									<th>RANK</th>
									<th>NEURAL_ID</th>
									<th>CLASSIFICATION</th>
									<th>NODES</th>
									<th>INFLUENCE</th>
									<th>COHERENCE</th>
									<th>SIGNATURE</th>
								</tr>
							</thead>
							<tbody>
								{#each filteredExecutives as [executive, count], index}
									{@const executiveClass = getExecutiveClass(count)}
									{@const profile = executiveProfiles.get(executive)}
									<tr class="matrix-row" 
										style="border-left: 3px solid {executiveClass.color}"
										on:click={() => drillDownExecutive(executive, count)}>
										<td class="rank-cell">
											<span style="color: {executiveClass.color}">#{index + 1}</span>
										</td>
										<td class="executive-cell">
											<span class="executive-symbol" style="color: {executiveClass.color}">
												{executiveClass.symbol}
											</span>
											<span class="executive-id">{executive.substring(0, 30).toUpperCase()}</span>
										</td>
										<td>
											<span class="classification-badge" 
												  style="background: {executiveClass.glow}; 
														 color: {executiveClass.color}; 
														 border: 1px solid {executiveClass.color}">
												{executiveClass.level}
											</span>
										</td>
										<td class="numeric-cell">{count.toLocaleString()}</td>
										<td>
											<div class="influence-display">
												<div class="influence-bar">
													<div class="influence-fill" 
														 style="width: {profile?.networkCentrality || 0}%; 
																background: linear-gradient(90deg, transparent, {executiveClass.color})"></div>
												</div>
												<span class="influence-value">{(profile?.networkCentrality || 0).toFixed(0)}%</span>
											</div>
										</td>
										<td>
											<div class="coherence-meter">
												<div class="coherence-level" 
													 style="height: {profile?.quantumCoherence ? profile.quantumCoherence * 100 : 0}%; 
															background: {executiveClass.color}"></div>
											</div>
										</td>
										<td class="signature-cell">
											<span class="mini-signature">
												{profile?.neuralSignature ? profile.neuralSignature.substring(0, 8) : 'UNKNOWN'}
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
	.neural-command-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		position: relative;
		overflow: hidden;
	}
	
	/* Consciousness Field Background */
	.consciousness-field {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		perspective: 1000px;
		transform-style: preserve-3d;
	}
	
	.brainwave-canvas {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		opacity: 0.3;
	}
	
	.hologram-layer {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		transform-style: preserve-3d;
	}
	
	.hologram-particle {
		position: absolute;
		width: 2px;
		height: 2px;
		border-radius: 50%;
		box-shadow: 0 0 4px currentColor;
	}
	
	.executive-neural-interface {
		position: relative;
		z-index: 1;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
	
	/* Neural Header */
	.neural-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 2rem;
		background: linear-gradient(180deg, rgba(139, 233, 253, 0.05), transparent);
		border-bottom: 1px solid rgba(139, 233, 253, 0.2);
		backdrop-filter: blur(20px);
	}
	
	.header-consciousness {
		display: flex;
		align-items: center;
		gap: 2rem;
	}
	
	.consciousness-core {
		width: 80px;
		height: 80px;
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.core-rings {
		position: absolute;
		width: 100%;
		height: 100%;
	}
	
	.ring {
		position: absolute;
		border: 1px solid;
		border-radius: 50%;
		animation: ringRotate linear infinite;
	}
	
	.ring-outer {
		inset: 0;
		border-color: #FF79C6;
		box-shadow: 0 0 20px #FF79C640;
	}
	
	.ring-middle {
		inset: 15px;
		border-color: #8BE9FD;
		box-shadow: 0 0 15px #8BE9FD40;
	}
	
	.ring-inner {
		inset: 30px;
		border-color: #BD93F9;
		box-shadow: 0 0 10px #BD93F940;
	}
	
	@keyframes ringRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.core-symbol {
		font-size: 2rem;
		color: #8BE9FD;
		text-shadow: 0 0 30px #8BE9FD80;
		z-index: 1;
	}
	
	.consciousness-info {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.neural-title {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 200;
		letter-spacing: 0.3em;
		background: linear-gradient(90deg, #FF79C6, #8BE9FD, #BD93F9);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}
	
	.consciousness-metrics {
		display: flex;
		gap: 1rem;
	}
	
	.metric-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}
	
	.metric-bar {
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
		color: #8BE9FD;
		font-family: 'Courier New', monospace;
		min-width: 35px;
	}
	
	/* Neural Search */
	.neural-search {
		flex: 1;
		max-width: 400px;
		margin: 0 2rem;
	}
	
	.search-container {
		position: relative;
	}
	
	.search-input {
		width: 100%;
		padding: 0.75rem 1rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(139, 233, 253, 0.3);
		border-radius: 0;
		color: #8BE9FD;
		font-family: 'Courier New', monospace;
		font-size: 0.9rem;
		letter-spacing: 0.1em;
		transition: all 0.3s ease;
	}
	
	.search-input::placeholder {
		color: rgba(139, 233, 253, 0.4);
	}
	
	.search-input:focus {
		outline: none;
		border-color: #8BE9FD;
		background: rgba(139, 233, 253, 0.05);
		box-shadow: 0 0 30px rgba(139, 233, 253, 0.3);
	}
	
	.search-pulse {
		position: absolute;
		bottom: -1px;
		left: 0;
		right: 0;
		height: 1px;
		background: linear-gradient(90deg, transparent, #8BE9FD, transparent);
		animation: searchPulse 2s linear infinite;
	}
	
	@keyframes searchPulse {
		from { transform: translateX(-100%); }
		to { transform: translateX(100%); }
	}
	
	.search-feedback {
		margin-top: 0.5rem;
		height: 1rem;
	}
	
	.feedback-text {
		font-size: 0.7rem;
		color: rgba(139, 233, 253, 0.6);
		letter-spacing: 0.1em;
	}
	
	/* Header Stats */
	.header-stats {
		display: flex;
		gap: 2rem;
	}
	
	.stat-display {
		text-align: center;
	}
	
	.stat-display .stat-value {
		font-size: 1.8rem;
		font-weight: 100;
		color: #FF79C6;
		text-shadow: 0 0 20px #FF79C640;
		font-family: 'Courier New', monospace;
	}
	
	.stat-display .stat-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.2em;
		margin-top: 0.25rem;
	}
	
	/* Neural Display */
	.neural-display {
		flex: 1;
		overflow: hidden;
		padding: 2rem;
	}
	
	/* Loading State */
	.neural-loading {
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.loading-brain {
		position: relative;
		width: 150px;
		height: 150px;
	}
	
	.brain-hemisphere {
		position: absolute;
		width: 60px;
		height: 100px;
		background: linear-gradient(135deg, #FF79C6, #8BE9FD);
		border-radius: 50%;
		opacity: 0.3;
		animation: hemisphereFloat 3s ease-in-out infinite;
	}
	
	.brain-hemisphere.left {
		left: 20px;
		animation-delay: 0s;
	}
	
	.brain-hemisphere.right {
		right: 20px;
		animation-delay: 0.5s;
	}
	
	@keyframes hemisphereFloat {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-10px); }
	}
	
	.brain-stem {
		position: absolute;
		bottom: 10px;
		left: 50%;
		transform: translateX(-50%);
		width: 30px;
		height: 40px;
		background: linear-gradient(180deg, #BD93F9, transparent);
		opacity: 0.5;
	}
	
	.neural-pulse {
		position: absolute;
		inset: -20px;
		border: 2px solid #8BE9FD;
		border-radius: 50%;
		animation: neuralPulse 2s ease-out infinite;
	}
	
	@keyframes neuralPulse {
		0% { transform: scale(0.8); opacity: 1; }
		100% { transform: scale(1.5); opacity: 0; }
	}
	
	.loading-text {
		color: rgba(139, 233, 253, 0.6);
		font-size: 0.9rem;
		letter-spacing: 0.2em;
		animation: textPulse 2s ease-in-out infinite;
	}
	
	@keyframes textPulse {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 1; }
	}
	
	/* Neural Visualization */
	.neural-visualization {
		height: 100%;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
	}
	
	.neural-3d-space {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		background: radial-gradient(circle at center, rgba(139, 233, 253, 0.02), transparent);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 20px;
	}
	
	.synaptic-network {
		width: 100%;
		height: 100%;
		max-width: 600px;
		max-height: 600px;
	}
	
	.neural-node-group {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.neural-node-group:hover {
		transform: scale(1.2);
	}
	
	.synaptic-activity {
		position: absolute;
		bottom: 20px;
		left: 20px;
		right: 20px;
		height: 60px;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(139, 233, 253, 0.3);
		padding: 5px;
		border-radius: 10px;
	}
	
	.synaptic-activity svg {
		width: 100%;
		height: 100%;
	}
	
	.activity-label {
		position: absolute;
		top: 5px;
		left: 10px;
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}
	
	/* Executive Matrix */
	.executive-matrix {
		overflow: auto;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 20px;
		backdrop-filter: blur(10px);
	}
	
	.matrix-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.matrix-table th {
		background: linear-gradient(180deg, rgba(139, 233, 253, 0.1), rgba(0, 0, 0, 0.8));
		color: #8BE9FD;
		padding: 1rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 300;
		letter-spacing: 0.2em;
		border-bottom: 1px solid rgba(139, 233, 253, 0.3);
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
		background: rgba(139, 233, 253, 0.03);
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
	
	.executive-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.executive-symbol {
		font-size: 1.2rem;
	}
	
	.executive-id {
		font-weight: 300;
		letter-spacing: 0.05em;
	}
	
	.classification-badge {
		display: inline-block;
		padding: 0.3rem 0.6rem;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		border-radius: 4px;
	}
	
	.numeric-cell {
		font-family: 'Courier New', monospace;
		color: #8BE9FD;
	}
	
	.influence-display {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.influence-bar {
		width: 60px;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}
	
	.influence-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.influence-value {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		min-width: 35px;
	}
	
	.coherence-meter {
		width: 20px;
		height: 20px;
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		position: relative;
		border-radius: 2px;
	}
	
	.coherence-level {
		position: absolute;
		bottom: 0;
		left: 0;
		width: 100%;
		transition: height 0.5s ease;
	}
	
	.signature-cell {
		font-family: 'Courier New', monospace;
		font-size: 0.7rem;
		color: rgba(139, 233, 253, 0.6);
	}
	
	.mini-signature {
		letter-spacing: 0.05em;
	}
	
	/* Executive Deep Dive */
	.executive-deep-dive {
		height: 100%;
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 20px;
		backdrop-filter: blur(20px);
		overflow: hidden;
	}
	
	.deep-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 2rem;
		background: linear-gradient(135deg, rgba(139, 233, 253, 0.1), transparent);
		border-bottom: 1px solid rgba(139, 233, 253, 0.2);
	}
	
	.executive-identity {
		display: flex;
		align-items: center;
		gap: 2rem;
	}
	
	.identity-visualization {
		position: relative;
		width: 100px;
		height: 100px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.identity-core {
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		border-radius: 50%;
		z-index: 1;
		box-shadow: 0 0 40px currentColor;
	}
	
	.identity-rings {
		position: absolute;
		inset: -20px;
	}
	
	.identity-ring {
		position: absolute;
		border: 1px solid #8BE9FD;
		border-radius: 50%;
		opacity: 0.3;
		animation: identityPulse 3s ease-in-out infinite;
	}
	
	.ring-1 {
		inset: 0;
		animation-delay: 0s;
	}
	
	.ring-2 {
		inset: 10px;
		animation-delay: 0.5s;
	}
	
	.ring-3 {
		inset: 20px;
		animation-delay: 1s;
	}
	
	@keyframes identityPulse {
		0%, 100% { transform: scale(1); opacity: 0.3; }
		50% { transform: scale(1.1); opacity: 0.6; }
	}
	
	.identity-data {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.executive-name {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 200;
		color: #8BE9FD;
		letter-spacing: 0.1em;
		text-shadow: 0 0 20px rgba(139, 233, 253, 0.5);
	}
	
	.neural-signature {
		font-family: 'Courier New', monospace;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}
	
	.close-neural {
		background: rgba(255, 121, 198, 0.1);
		border: 1px solid #FF79C6;
		color: #FF79C6;
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
	
	.close-neural:hover {
		background: rgba(255, 121, 198, 0.2);
		transform: rotate(90deg);
		box-shadow: 0 0 20px rgba(255, 121, 198, 0.5);
	}
	
	/* Psychometric Display */
	.psychometric-display {
		padding: 2rem;
		border-bottom: 1px solid rgba(139, 233, 253, 0.1);
	}
	
	.psychometric-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1.5rem;
	}
	
	.psychometric-card {
		text-align: center;
	}
	
	.psych-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		margin-bottom: 0.5rem;
	}
	
	.psych-visualization {
		position: relative;
		width: 100px;
		height: 100px;
		margin: 0 auto;
	}
	
	.psych-visualization svg {
		width: 100%;
		height: 100%;
	}
	
	.psych-value {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 1.2rem;
		font-weight: 600;
		color: #FFFFFF;
	}
	
	/* Neural Connections Stream */
	.neural-connections-stream {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}
	
	.connections-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.connections-table th {
		background: rgba(0, 0, 0, 0.8);
		color: #8BE9FD;
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 300;
		letter-spacing: 0.1em;
		border-bottom: 1px solid rgba(139, 233, 253, 0.3);
		position: sticky;
		top: 0;
	}
	
	.connection-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.2s ease;
	}
	
	.connection-row:hover {
		background: rgba(139, 233, 253, 0.02);
	}
	
	.connections-table td {
		padding: 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.node-id {
		font-family: 'Courier New', monospace;
		color: #8BE9FD;
		font-size: 0.7rem;
	}
	
	.sync-indicator, .security-indicator {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		font-size: 1rem;
	}
	
	.sync-indicator.synced {
		color: #50FA7B;
		text-shadow: 0 0 10px #50FA7B;
	}
	
	.sync-indicator.desynced {
		color: #666666;
	}
	
	.security-indicator.secured {
		color: #8BE9FD;
		text-shadow: 0 0 10px #8BE9FD;
	}
	
	.security-indicator.vulnerable {
		color: #FF79C6;
		text-shadow: 0 0 10px #FF79C6;
	}
	
	/* Responsive */
	@media (max-width: 1400px) {
		.neural-visualization {
			grid-template-columns: 1fr;
		}
		
		.psychometric-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}
	
	@media (max-width: 768px) {
		.neural-header {
			flex-direction: column;
			gap: 1rem;
		}
		
		.psychometric-grid {
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
		background: linear-gradient(180deg, #FF79C6, #8BE9FD);
		border-radius: 3px;
	}
	
	::-webkit-scrollbar-corner {
		background: #000000;
	}
</style>