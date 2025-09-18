<!-- SourceTables.svelte - Quantum Matrix Intelligence Interface -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	
	// Quantum visualization states
	let matrixNodes = [];
	let dataFlows = [];
	let quantumWaves = [];
	let matrixGrid = [];
	let pulsarNodes = [];
	let signalStrength = 0;
	let dataVelocity = 0;
	let quantumCoherence = 0;
	let sourceProfiles = new Map();
	
	// Animation controllers
	let animationFrames = {
		matrix: null,
		pulsar: null,
		quantum: null
	};
	
	// Neon pastel colors
	const neonColors = {
		primary: '#FF79C6',    // Pink
		secondary: '#8BE9FD',  // Cyan
		tertiary: '#BD93F9',   // Purple
		quaternary: '#50FA7B', // Green
		warning: '#F1FA8C',    // Yellow
		danger: '#FF5555',     // Red
		accent: '#FFB86C'      // Orange
	};
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			let result = await response.json();
			data = result;
			loading = false;
			initializeQuantumMatrix();
			startQuantumAnimation();
		} catch (err) {
			console.error('Matrix sync failed:', err);
			loading = false;
		}
	});
	
	onDestroy(() => {
		Object.values(animationFrames).forEach(frame => {
			if (frame) cancelAnimationFrame(frame);
		});
	});
	
	function initializeQuantumMatrix() {
		if (!data.source_intelligence) return;
		
		let sources = Object.entries(data.source_intelligence)
			.sort((a, b) => b[1] - a[1])
			.slice(0, 50);
		
		// Create matrix nodes in 3D space
		sources.forEach(([source, frequency], i) => {
			let angle = (i / sources.length) * Math.PI * 2;
			let radius = 100 + Math.sin(i * 0.5) * 50;
			
			matrixNodes.push({
				id: source,
				frequency: frequency,
				x: Math.cos(angle) * radius,
				y: Math.sin(angle) * radius,
				z: Math.sin(i * 0.3) * 50,
				energy: Math.random(),
				quantum: Math.random(),
				resonance: Math.random(),
				color: Object.values(neonColors)[i % 7],
				connections: []
			});
			
			sourceProfiles.set(source, {
				signature: generateQuantumSignature(frequency),
				metrics: {
					power: frequency / sources[0][1] * 100,
					stability: 50 + Math.random() * 50,
					entanglement: Math.random() * 100,
					coherence: Math.random()
				}
			});
		});
		
		// Create data flow connections
		matrixNodes.forEach((node, i) => {
			let connections = Math.min(3, Math.floor(Math.random() * 5) + 1);
			for (let j = 0; j < connections; j++) {
				let target = Math.floor(Math.random() * matrixNodes.length);
				if (target !== i) {
					dataFlows.push({
						source: i,
						target: target,
						strength: Math.random(),
						particles: Array(5).fill().map(() => ({
							position: Math.random(),
							speed: 0.5 + Math.random() * 0.5
						}))
					});
				}
			}
		});
		
		// Initialize quantum waves
		for (let i = 0; i < 20; i++) {
			quantumWaves.push({
				amplitude: Math.random() * 50,
				frequency: Math.random() * 0.1,
				phase: Math.random() * Math.PI * 2,
				color: Object.values(neonColors)[Math.floor(Math.random() * 7)]
			});
		}
		
		// Create matrix grid
		for (let x = 0; x < 20; x++) {
			matrixGrid[x] = [];
			for (let y = 0; y < 20; y++) {
				matrixGrid[x][y] = {
					value: Math.random(),
					active: Math.random() > 0.7,
					pulse: Math.random() * Math.PI * 2
				};
			}
		}
		
		// Initialize pulsar nodes for radar visualization
		for (let i = 0; i < 8; i++) {
			pulsarNodes.push({
				angle: (i / 8) * Math.PI * 2,
				radius: 50 + Math.random() * 100,
				intensity: Math.random(),
				frequency: Math.random() * 2
			});
		}
	}
	
	function generateQuantumSignature(seed) {
		let sig = 'QX-';
		for (let i = 0; i < 16; i++) {
			sig += ((seed * (i + 1) * 997) % 16).toString(16).toUpperCase();
			if (i === 3 || i === 7 || i === 11) sig += '-';
		}
		return sig;
	}
	
	function startQuantumAnimation() {
		let time = 0;
		
		function animate() {
			time += 0.016;
			
			// Update signal metrics
			signalStrength = 50 + Math.sin(time * 0.5) * 30 + Math.sin(time * 1.7) * 20;
			dataVelocity = 30 + Math.sin(time * 0.8) * 30;
			quantumCoherence = 0.5 + Math.sin(time * 0.3) * 0.5;
			
			// Update matrix nodes
			matrixNodes.forEach((node, i) => {
				node.energy = 0.5 + Math.sin(time + i * 0.1) * 0.5;
				node.quantum = 0.5 + Math.cos(time * 2 + i * 0.2) * 0.5;
				node.resonance = Math.abs(Math.sin(time * 0.5 + i * 0.15));
			});
			
			// Update data flows
			dataFlows.forEach(flow => {
				flow.particles.forEach(particle => {
					particle.position = (particle.position + particle.speed * 0.01) % 1;
				});
			});
			
			// Update quantum waves
			quantumWaves.forEach(wave => {
				wave.phase += wave.frequency;
			});
			
			// Update matrix grid
			matrixGrid.forEach(row => {
				row.forEach(cell => {
					cell.value = 0.5 + Math.sin(time + cell.pulse) * 0.5;
				});
			});
			
			// Update pulsar nodes
			pulsarNodes.forEach(node => {
				node.intensity = 0.5 + Math.sin(time * node.frequency) * 0.5;
			});
			
			animationFrames.matrix = requestAnimationFrame(animate);
		}
		animate();
	}
	
	$: filteredSources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxFreq = filteredSources.length > 0 ? Math.max(...filteredSources.map(([,f]) => f)) : 1;
	
	function getSourceClass(frequency) {
		let normalized = frequency / maxFreq;
		let percentile = normalized * 100;
		
		if (percentile >= 85) return { level: 'QUANTUM', color: neonColors.primary, symbol: '◈' };
		if (percentile >= 65) return { level: 'MATRIX', color: neonColors.secondary, symbol: '◆' };
		if (percentile >= 45) return { level: 'NEURAL', color: neonColors.tertiary, symbol: '▲' };
		if (percentile >= 25) return { level: 'DATA', color: neonColors.quaternary, symbol: '●' };
		return { level: 'SIGNAL', color: neonColors.warning, symbol: '○' };
	}
	
	async function drillDownSource(source, frequency) {
		selectedSource = { source, frequency };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			hostDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Source scan failed:', err);
			hostDetails = [];
			loading = false;
		}
	}
	
	function closeDetails() {
		selectedSource = null;
		hostDetails = [];
	}
</script>

<div class="quantum-matrix-interface">
	<!-- Background Matrix Effect -->
	<div class="matrix-background">
		<svg class="matrix-svg" viewBox="0 0 100 100">
			{#each quantumWaves as wave}
				<path d="M 0,{50 + Math.sin(wave.phase) * wave.amplitude} 
						 Q 25,{50 + Math.sin(wave.phase + 1) * wave.amplitude} 
						   50,{50 + Math.sin(wave.phase + 2) * wave.amplitude}
						 T 100,{50 + Math.sin(wave.phase + 3) * wave.amplitude}"
					  stroke={wave.color}
					  stroke-width="0.2"
					  fill="none"
					  opacity="0.3"/>
			{/each}
		</svg>
		
		<!-- Matrix Grid -->
		<div class="matrix-grid-container">
			{#each matrixGrid as row, x}
				{#each row as cell, y}
					{#if cell.active}
						<div class="grid-cell"
							 style="left: {x * 5}%; top: {y * 5}%;
									opacity: {cell.value * 0.5};
									background: {Object.values(neonColors)[Math.floor(cell.value * 7)]}">
						</div>
					{/if}
				{/each}
			{/each}
		</div>
	</div>
	
	<div class="interface-container">
		<!-- Header -->
		<header class="quantum-header">
			<div class="header-structure">
				<div class="quantum-emblem">
					<div class="emblem-rings">
						<div class="ring ring-1" style="border-color: {neonColors.primary}"></div>
						<div class="ring ring-2" style="border-color: {neonColors.secondary}"></div>
						<div class="ring ring-3" style="border-color: {neonColors.tertiary}"></div>
					</div>
					<div class="emblem-core">◈</div>
				</div>
				<div class="header-info">
					<h1 class="interface-title">SOURCE QUANTUM MATRIX</h1>
					<div class="quantum-metrics">
						<span class="metric">SIGNAL: {signalStrength.toFixed(0)}%</span>
						<span class="metric">VELOCITY: {dataVelocity.toFixed(0)} Tb/s</span>
						<span class="metric">COHERENCE: {(quantumCoherence * 100).toFixed(0)}%</span>
					</div>
				</div>
			</div>
			
			<div class="search-module">
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="QUANTUM SEARCH..."
					   class="quantum-search"/>
				<div class="search-wave"></div>
			</div>
			
			<div class="header-stats">
				<div class="stat">
					<div class="stat-value" style="color: {neonColors.primary}">{filteredSources.length}</div>
					<div class="stat-label">SOURCES</div>
				</div>
				<div class="stat">
					<div class="stat-value" style="color: {neonColors.secondary}">
						{(data.total_mentions || 0).toLocaleString()}
					</div>
					<div class="stat-label">MENTIONS</div>
				</div>
			</div>
		</header>
		
		<!-- Main Display -->
		<div class="quantum-display">
			{#if loading && !selectedSource}
				<div class="loading-state">
					<div class="quantum-loader">
						<div class="loader-core">◈</div>
						<div class="loader-ring"></div>
					</div>
					<p>INITIALIZING QUANTUM MATRIX...</p>
				</div>
			{:else if selectedSource}
				<!-- Detail View -->
				<div class="source-detail-view">
					<div class="detail-header">
						<div class="source-identity">
							<div class="identity-visual">
								<div class="visual-core" style="background: {getSourceClass(selectedSource.frequency).color}">
									{getSourceClass(selectedSource.frequency).symbol}
								</div>
								<div class="visual-rings">
									{#each Array(3) as _, i}
										<div class="v-ring" style="animation-delay: {i * 0.3}s"></div>
									{/each}
								</div>
							</div>
							<div class="identity-info">
								<h2>{selectedSource.source.toUpperCase()}</h2>
								<div class="quantum-signature">
									{sourceProfiles.get(selectedSource.source)?.signature}
								</div>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					
					<div class="detail-stream">
						<table class="stream-table">
							<thead>
								<tr>
									<th>NODE_ID</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>TYPE</th>
									<th>SYNC</th>
								</tr>
							</thead>
							<tbody>
								{#each hostDetails.slice(0, 10) as host}
									<tr>
										<td class="node-id">{host.host.substring(0, 30)}</td>
										<td>{host.region || 'UNKNOWN'}</td>
										<td>{host.country || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'QUANTUM'}</td>
										<td>
											<span class="sync-indicator {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="visualization-container">
					<!-- Left: 3D Node Network -->
					<div class="network-visualization">
						<div class="network-3d">
							<svg viewBox="-200 -200 400 400">
								<!-- Data flow connections -->
								{#each dataFlows as flow}
									{#if matrixNodes[flow.source] && matrixNodes[flow.target]}
										<line x1="{matrixNodes[flow.source].x}"
											  y1="{matrixNodes[flow.source].y}"
											  x2="{matrixNodes[flow.target].x}"
											  y2="{matrixNodes[flow.target].y}"
											  stroke={neonColors.secondary}
											  stroke-width="{flow.strength}"
											  opacity="0.3">
											<animate attributeName="stroke-opacity"
													 values="0.2;0.5;0.2"
													 dur="3s"
													 repeatCount="indefinite"/>
										</line>
									{/if}
								{/each}
								
								<!-- Matrix nodes -->
								{#each matrixNodes.slice(0, 20) as node}
									{@const sourceClass = getSourceClass(node.frequency)}
									<g transform="translate({node.x}, {node.y})"
									   on:click={() => drillDownSource(node.id, node.frequency)}>
										<circle r="{8 + node.energy * 12}"
												fill={sourceClass.color}
												opacity="{node.energy * 0.3}"/>
										<circle r="6"
												fill={sourceClass.color}
												opacity="0.8"/>
										<text text-anchor="middle"
											  dy="3"
											  fill="#000000"
											  font-size="8"
											  font-weight="bold">
											{sourceClass.symbol}
										</text>
									</g>
								{/each}
							</svg>
						</div>
						
						<!-- Pulsar Radar -->
						<div class="pulsar-radar">
							<svg viewBox="-150 -150 300 300">
								<defs>
									<radialGradient id="radarGrad">
										<stop offset="0%" style="stop-color:{neonColors.primary};stop-opacity:0.5"/>
										<stop offset="100%" style="stop-color:{neonColors.primary};stop-opacity:0"/>
									</radialGradient>
								</defs>
								
								<!-- Radar rings -->
								{#each [30, 60, 90, 120] as radius}
									<circle cx="0" cy="0" r={radius}
											fill="none"
											stroke={neonColors.primary}
											stroke-width="0.5"
											opacity="0.2"/>
								{/each}
								
								<!-- Radar sweep -->
								<line x1="0" y1="0"
									  x2="0" y2="-120"
									  stroke={neonColors.quaternary}
									  stroke-width="2"
									  opacity="0.8"
									  transform="rotate({Date.now() * 0.1 % 360})"/>
								
								<!-- Pulsar nodes -->
								{#each pulsarNodes as node}
									<circle cx="{Math.cos(node.angle) * node.radius}"
											cy="{Math.sin(node.angle) * node.radius}"
											r="{3 + node.intensity * 5}"
											fill={neonColors.secondary}
											opacity={node.intensity}>
										<animate attributeName="r"
												 values="{3 + node.intensity * 5};{5 + node.intensity * 8};{3 + node.intensity * 5}"
												 dur="{2 / node.frequency}s"
												 repeatCount="indefinite"/>
									</circle>
								{/each}
							</svg>
						</div>
					</div>
					
					<!-- Right: Data Table -->
					<div class="matrix-table-container">
						<table class="quantum-table">
							<thead>
								<tr>
									<th>RANK</th>
									<th>SOURCE_ID</th>
									<th>CLASS</th>
									<th>FREQUENCY</th>
									<th>POWER</th>
									<th>SIGNATURE</th>
								</tr>
							</thead>
							<tbody>
								{#each filteredSources.slice(0, 15) as [source, frequency], index}
									{@const sourceClass = getSourceClass(frequency)}
									{@const profile = sourceProfiles.get(source)}
									<tr style="border-left: 2px solid {sourceClass.color}"
										on:click={() => drillDownSource(source, frequency)}>
										<td style="color: {sourceClass.color}">#{index + 1}</td>
										<td>
											<span style="color: {sourceClass.color}">{sourceClass.symbol}</span>
											<span>{source.substring(0, 20).toUpperCase()}</span>
										</td>
										<td>
											<span class="class-badge" style="background: {sourceClass.color}20; color: {sourceClass.color}">
												{sourceClass.level}
											</span>
										</td>
										<td style="color: {neonColors.secondary}">{frequency.toLocaleString()}</td>
										<td>
											<div class="power-bar">
												<div class="power-fill" style="width: {profile?.metrics.power || 0}%; background: {sourceClass.color}"></div>
											</div>
										</td>
										<td class="signature">{profile?.signature.substring(0, 8)}...</td>
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
	.quantum-matrix-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		position: relative;
		overflow: hidden;
	}
	
	/* Background Effects */
	.matrix-background {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}
	
	.matrix-svg {
		position: absolute;
		width: 100%;
		height: 100%;
		opacity: 0.5;
	}
	
	.matrix-grid-container {
		position: absolute;
		width: 100%;
		height: 100%;
	}
	
	.grid-cell {
		position: absolute;
		width: 2px;
		height: 2px;
		border-radius: 50%;
	}
	
	.interface-container {
		position: relative;
		z-index: 1;
		height: 100%;
		display: flex;
		flex-direction: column;
		padding: 1.5rem;
		gap: 1.5rem;
	}
	
	/* Header */
	.quantum-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(255, 121, 198, 0.2);
		border-radius: 15px;
		backdrop-filter: blur(20px);
	}
	
	.header-structure {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.quantum-emblem {
		position: relative;
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.emblem-rings {
		position: absolute;
		inset: 0;
	}
	
	.ring {
		position: absolute;
		border: 1px solid;
		border-radius: 50%;
		animation: ringRotate 4s linear infinite;
	}
	
	.ring-1 { inset: 0; }
	.ring-2 { inset: 8px; animation-direction: reverse; }
	.ring-3 { inset: 16px; animation-duration: 6s; }
	
	@keyframes ringRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.emblem-core {
		font-size: 1.5rem;
		color: #FF79C6;
		text-shadow: 0 0 20px #FF79C6;
		z-index: 1;
	}
	
	.interface-title {
		margin: 0;
		font-size: 1.2rem;
		font-weight: 200;
		letter-spacing: 0.2em;
		background: linear-gradient(90deg, #FF79C6, #8BE9FD, #BD93F9);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}
	
	.quantum-metrics {
		display: flex;
		gap: 1.5rem;
		margin-top: 0.5rem;
	}
	
	.metric {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
	}
	
	.search-module {
		position: relative;
		flex: 1;
		max-width: 300px;
	}
	
	.quantum-search {
		width: 100%;
		padding: 0.6rem 1rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(139, 233, 253, 0.3);
		border-radius: 8px;
		color: #8BE9FD;
		font-family: monospace;
		font-size: 0.85rem;
		letter-spacing: 0.05em;
	}
	
	.quantum-search:focus {
		outline: none;
		border-color: #8BE9FD;
		box-shadow: 0 0 20px rgba(139, 233, 253, 0.3);
	}
	
	.search-wave {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		height: 1px;
		background: linear-gradient(90deg, transparent, #8BE9FD, transparent);
		animation: waveFlow 2s linear infinite;
	}
	
	@keyframes waveFlow {
		from { transform: translateX(-100%); }
		to { transform: translateX(100%); }
	}
	
	.header-stats {
		display: flex;
		gap: 2rem;
	}
	
	.stat {
		text-align: center;
	}
	
	.stat-value {
		font-size: 1.5rem;
		font-weight: 100;
		font-family: monospace;
	}
	
	.stat-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.1em;
	}
	
	/* Main Display */
	.quantum-display {
		flex: 1;
		overflow: hidden;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 15px;
		backdrop-filter: blur(10px);
		padding: 1.5rem;
	}
	
	.visualization-container {
		height: 100%;
		display: grid;
		grid-template-columns: 1fr 1.2fr;
		gap: 1.5rem;
	}
	
	.network-visualization {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.network-3d {
		flex: 1;
		background: radial-gradient(circle, rgba(255, 121, 198, 0.02), transparent);
		border: 1px solid rgba(255, 121, 198, 0.1);
		border-radius: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}
	
	.network-3d svg {
		width: 100%;
		height: 100%;
		max-height: 300px;
	}
	
	.network-3d g {
		cursor: pointer;
		transition: transform 0.3s ease;
	}
	
	.network-3d g:hover {
		transform: scale(1.2);
	}
	
	.pulsar-radar {
		height: 200px;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.pulsar-radar svg {
		width: 100%;
		height: 100%;
		max-width: 200px;
	}
	
	/* Table */
	.matrix-table-container {
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}
	
	.quantum-table {
		width: 100%;
		border-collapse: collapse;
		flex: 1;
	}
	
	.quantum-table th {
		background: rgba(0, 0, 0, 0.8);
		color: #BD93F9;
		padding: 0.8rem;
		text-align: left;
		font-size: 0.65rem;
		font-weight: 300;
		letter-spacing: 0.1em;
		border-bottom: 1px solid rgba(189, 147, 249, 0.3);
		position: sticky;
		top: 0;
	}
	
	.quantum-table tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.03);
	}
	
	.quantum-table tr:hover {
		background: rgba(255, 121, 198, 0.03);
		transform: translateX(3px);
	}
	
	.quantum-table td {
		padding: 0.6rem 0.8rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.class-badge {
		padding: 0.2rem 0.4rem;
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		border-radius: 4px;
	}
	
	.power-bar {
		width: 60px;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}
	
	.power-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.signature {
		font-family: monospace;
		font-size: 0.65rem;
		color: rgba(139, 233, 253, 0.6);
	}
	
	/* Loading State */
	.loading-state {
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}
	
	.quantum-loader {
		position: relative;
		width: 80px;
		height: 80px;
	}
	
	.loader-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 2rem;
		color: #FF79C6;
		text-shadow: 0 0 30px #FF79C6;
		animation: pulsate 2s ease-in-out infinite;
	}
	
	.loader-ring {
		position: absolute;
		inset: 0;
		border: 2px solid #8BE9FD;
		border-radius: 50%;
		border-left-color: transparent;
		animation: spin 1s linear infinite;
	}
	
	@keyframes pulsate {
		0%, 100% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
		50% { opacity: 0.5; transform: translate(-50%, -50%) scale(0.9); }
	}
	
	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	/* Detail View */
	.source-detail-view {
		height: 100%;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		background: linear-gradient(135deg, rgba(255, 121, 198, 0.1), transparent);
		border-radius: 10px;
	}
	
	.source-identity {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.identity-visual {
		position: relative;
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.visual-core {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		font-size: 1.2rem;
		z-index: 1;
	}
	
	.visual-rings {
		position: absolute;
		inset: -10px;
	}
	
	.v-ring {
		position: absolute;
		border: 1px solid #8BE9FD;
		border-radius: 50%;
		opacity: 0.3;
		animation: expandRing 3s ease-in-out infinite;
	}
	
	.v-ring:nth-child(1) { inset: 0; }
	.v-ring:nth-child(2) { inset: 5px; }
	.v-ring:nth-child(3) { inset: 10px; }
	
	@keyframes expandRing {
		0%, 100% { transform: scale(1); opacity: 0.3; }
		50% { transform: scale(1.1); opacity: 0.6; }
	}
	
	.identity-info h2 {
		margin: 0;
		font-size: 1.1rem;
		color: #FF79C6;
		font-weight: 200;
		letter-spacing: 0.1em;
	}
	
	.quantum-signature {
		font-family: monospace;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.close-btn {
		background: rgba(255, 85, 85, 0.1);
		border: 1px solid #FF5555;
		color: #FF5555;
		width: 32px;
		height: 32px;
		border-radius: 50%;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.2rem;
		transition: all 0.3s ease;
	}
	
	.close-btn:hover {
		background: rgba(255, 85, 85, 0.2);
		transform: rotate(90deg);
	}
	
	.detail-stream {
		flex: 1;
		overflow: auto;
	}
	
	.stream-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.stream-table th {
		background: rgba(0, 0, 0, 0.6);
		color: #8BE9FD;
		padding: 0.6rem;
		text-align: left;
		font-size: 0.65rem;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
	}
	
	.stream-table td {
		padding: 0.5rem 0.6rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.node-id {
		font-family: monospace;
		color: #BD93F9;
		font-size: 0.65rem;
	}
	
	.sync-indicator {
		display: inline-block;
		font-size: 0.9rem;
	}
	
	.sync-indicator.active {
		color: #50FA7B;
		text-shadow: 0 0 10px #50FA7B;
	}
	
	.sync-indicator.inactive {
		color: #666;
	}
	
	/* Hide scrollbars but keep functionality */
	*::-webkit-scrollbar {
		width: 0px;
		height: 0px;
	}
</style>