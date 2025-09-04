<!-- CIOMetrics.svelte - Quantum Executive Neural Interface -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedExecutive = null;
	let executiveDetails = [];
	let searchTerm = '';
	let particleSystem = [];
	let neuralConnections = [];
	let quantumState = 'INITIALIZING';
	let hologramRotation = 0;
	let dataStreamActive = false;
	let threatMatrix = [];
	let executiveNodes = new Map();
	let connectionStrength = new Map();
	
	// Animation intervals
	let rotationInterval;
	let particleInterval;
	let quantumInterval;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/cio_metrics');
			data = await response.json();
			loading = false;
			quantumState = 'SYNCHRONIZED';
			initializeNeuralNetwork();
			startQuantumAnimation();
		} catch (err) {
			console.error('Executive neural sync failed:', err);
			loading = false;
			quantumState = 'DESYNCHRONIZED';
		}
	});
	
	onDestroy(() => {
		if (rotationInterval) clearInterval(rotationInterval);
		if (particleInterval) clearInterval(particleInterval);
		if (quantumInterval) clearInterval(quantumInterval);
	});
	
	function initializeNeuralNetwork() {
		// Generate particle system
		for (let i = 0; i < 50; i++) {
			particleSystem.push({
				x: Math.random() * 100,
				y: Math.random() * 100,
				z: Math.random() * 100,
				vx: (Math.random() - 0.5) * 0.5,
				vy: (Math.random() - 0.5) * 0.5,
				vz: (Math.random() - 0.5) * 0.5,
				size: Math.random() * 3 + 1,
				opacity: Math.random() * 0.5 + 0.3,
				color: `hsl(${180 + Math.random() * 60}, 100%, 50%)`
			});
		}
		
		// Generate neural connections between executives
		if (data.operative_intelligence) {
			const executives = Object.entries(data.operative_intelligence).slice(0, 20);
			executives.forEach(([exec, count], i) => {
				executives.forEach(([exec2, count2], j) => {
					if (i < j && Math.random() > 0.7) {
						neuralConnections.push({
							from: exec,
							to: exec2,
							strength: Math.min(count, count2) / Math.max(count, count2),
							pulsePhase: Math.random() * Math.PI * 2
						});
					}
				});
			});
		}
	}
	
	function startQuantumAnimation() {
		rotationInterval = setInterval(() => {
			hologramRotation = (hologramRotation + 0.5) % 360;
		}, 50);
		
		particleInterval = setInterval(() => {
			particleSystem = particleSystem.map(p => ({
				...p,
				x: (p.x + p.vx + 100) % 100,
				y: (p.y + p.vy + 100) % 100,
				z: (p.z + p.vz + 100) % 100,
				opacity: 0.3 + Math.sin(Date.now() * 0.001 + p.x) * 0.3
			}));
		}, 50);
		
		quantumInterval = setInterval(() => {
			dataStreamActive = !dataStreamActive;
			quantumState = ['SYNCHRONIZED', 'PROCESSING', 'ANALYZING', 'CORRELATING'][Math.floor(Math.random() * 4)];
		}, 3000);
	}
	
	$: sortedExecutives = data.operative_intelligence ? 
		Object.entries(data.operative_intelligence)
			.filter(([exec]) => exec.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxAssets = sortedExecutives.length > 0 ? Math.max(...sortedExecutives.map(([,count]) => count)) : 1;
	$: minAssets = sortedExecutives.length > 0 ? Math.min(...sortedExecutives.map(([,count]) => count)) : 0;
	
	function calculateExecutiveMetrics(count) {
		const normalized = (count - minAssets) / (maxAssets - minAssets);
		const percentile = normalized * 100;
		
		// Dynamic classification based on distribution
		let classification = 'UNKNOWN';
		let threatLevel = 0;
		let color = '#00ffff';
		let icon = '◯';
		
		if (percentile >= 90) {
			classification = 'APEX';
			threatLevel = 95;
			color = '#ff00ff';
			icon = '◈';
		} else if (percentile >= 75) {
			classification = 'PRIME';
			threatLevel = 75;
			color = '#ff6600';
			icon = '◆';
		} else if (percentile >= 50) {
			classification = 'CORE';
			threatLevel = 50;
			color = '#00ff00';
			icon = '▲';
		} else if (percentile >= 25) {
			classification = 'STANDARD';
			threatLevel = 25;
			color = '#00ffff';
			icon = '●';
		} else {
			classification = 'EMERGING';
			threatLevel = 10;
			color = '#0099ff';
			icon = '○';
		}
		
		return {
			classification,
			threatLevel,
			color,
			icon,
			percentile: percentile.toFixed(1),
			quantumSignature: generateQuantumSignature(count),
			neuralActivity: normalized * 100,
			dataFlow: count * 0.001 // TB/s
		};
	}
	
	function generateQuantumSignature(seed) {
		const sig = [];
		for (let i = 0; i < 8; i++) {
			sig.push(((seed * (i + 1) * 9973) % 256).toString(16).padStart(2, '0'));
		}
		return sig.join(':').toUpperCase();
	}
	
	function getPercentage(count) {
		let total = Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
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

<div class="quantum-container">
	<!-- Particle System Background -->
	<div class="particle-field">
		{#each particleSystem as particle}
			<div class="quantum-particle" 
				 style="left: {particle.x}%; 
						top: {particle.y}%; 
						opacity: {particle.opacity};
						width: {particle.size}px;
						height: {particle.size}px;
						background: {particle.color};
						box-shadow: 0 0 {particle.size * 3}px {particle.color};">
			</div>
		{/each}
	</div>
	
	<!-- Neural Grid Overlay -->
	<svg class="neural-grid" viewBox="0 0 100 100">
		<defs>
			<linearGradient id="neuralGradient" x1="0%" y1="0%" x2="100%" y2="100%">
				<stop offset="0%" style="stop-color:#00ffff;stop-opacity:0.3" />
				<stop offset="100%" style="stop-color:#ff00ff;stop-opacity:0.3" />
			</linearGradient>
			<filter id="glow">
				<feGaussianBlur stdDeviation="2" result="coloredBlur"/>
				<feMerge>
					<feMergeNode in="coloredBlur"/>
					<feMergeNode in="SourceGraphic"/>
				</feMerge>
			</filter>
		</defs>
		{#each Array(10) as _, i}
			<line x1="0" y1="{i * 10 + 5}" x2="100" y2="{i * 10 + 5}" 
				  stroke="url(#neuralGradient)" stroke-width="0.1" opacity="0.3"/>
			<line x1="{i * 10 + 5}" y1="0" x2="{i * 10 + 5}" y2="100" 
				  stroke="url(#neuralGradient)" stroke-width="0.1" opacity="0.3"/>
		{/each}
	</svg>
	
	<div class="executive-interface">
		<!-- Quantum Header -->
		<div class="quantum-header">
			<div class="header-matrix">
				<div class="quantum-logo">
					<div class="hologram-container" style="transform: rotateY({hologramRotation}deg)">
						<div class="hologram-face front">◈</div>
						<div class="hologram-face back">◈</div>
						<div class="hologram-face left">◈</div>
						<div class="hologram-face right">◈</div>
					</div>
				</div>
				<div class="header-text">
					<h1 class="glitch-text" data-text="EXECUTIVE NEURAL MATRIX">
						EXECUTIVE NEURAL MATRIX
					</h1>
					<div class="quantum-status">
						<span class="status-indicator {quantumState.toLowerCase()}"></span>
						<span class="status-text">QUANTUM STATE: {quantumState}</span>
					</div>
				</div>
			</div>
			
			<div class="search-matrix">
				<input 
					type="text" 
					bind:value={searchTerm}
					placeholder="NEURAL SEARCH..."
					class="quantum-search"
				/>
				<div class="search-scanner {searchTerm ? 'active' : ''}"></div>
			</div>
			
			<div class="metrics-display">
				<div class="metric-cell">
					<div class="metric-value">{sortedExecutives.length}</div>
					<div class="metric-label">ENTITIES</div>
				</div>
				<div class="metric-cell">
					<div class="metric-value">{(data.operative_intelligence ? Object.values(data.operative_intelligence).reduce((a, b) => a + b, 0) : 0).toLocaleString()}</div>
					<div class="metric-label">NODES</div>
				</div>
			</div>
		</div>
		
		<!-- Main Interface -->
		{#if loading && !selectedExecutive}
			<div class="quantum-loading">
				<div class="loading-core">
					<div class="core-ring ring-1"></div>
					<div class="core-ring ring-2"></div>
					<div class="core-ring ring-3"></div>
					<div class="core-center">◈</div>
				</div>
				<p class="loading-text">INITIALIZING QUANTUM NEURAL INTERFACE...</p>
			</div>
		{:else if selectedExecutive}
			<div class="executive-detail-view">
				<div class="detail-header">
					<div class="executive-hologram">
						<div class="hologram-avatar">
							{calculateExecutiveMetrics(selectedExecutive.count).icon}
						</div>
						<div class="executive-data">
							<h2>{selectedExecutive.executive.toUpperCase()}</h2>
							<div class="executive-signature">
								{calculateExecutiveMetrics(selectedExecutive.count).quantumSignature}
							</div>
						</div>
					</div>
					<button class="quantum-close" on:click={closeDetails}>
						<span class="close-icon">✕</span>
					</button>
				</div>
				
				<div class="executive-metrics-grid">
					<div class="metric-card">
						<div class="card-value">{selectedExecutive.count.toLocaleString()}</div>
						<div class="card-label">NEURAL NODES</div>
					</div>
					<div class="metric-card">
						<div class="card-value">{getPercentage(selectedExecutive.count)}%</div>
						<div class="card-label">NETWORK CONTROL</div>
					</div>
					<div class="metric-card">
						<div class="card-value">{calculateExecutiveMetrics(selectedExecutive.count).classification}</div>
						<div class="card-label">CLASSIFICATION</div>
					</div>
					<div class="metric-card">
						<div class="card-value">{calculateExecutiveMetrics(selectedExecutive.count).threatLevel}%</div>
						<div class="card-label">THREAT LEVEL</div>
					</div>
				</div>
				
				<div class="neural-data-stream">
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
									<td class="node-id">{host.host.substring(0, 20)}</td>
									<td class="data-cell">{host.country || 'UNKNOWN'}</td>
									<td class="data-cell">{host.region || 'UNKNOWN'}</td>
									<td class="data-cell">{host.infrastructure_type || 'UNKNOWN'}</td>
									<td>
										<span class="status-quantum {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
											{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}
										</span>
									</td>
									<td>
										<span class="status-quantum {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'secured' : 'vulnerable'}">
											{host.tanium_coverage?.toLowerCase().includes('tanium') ? '◆' : '◇'}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{:else}
			<!-- Executive Neural Network Visualization -->
			<div class="neural-network-container">
				<div class="network-visualization">
					{#each sortedExecutives.slice(0, 15) as [executive, count], i}
						{@const metrics = calculateExecutiveMetrics(count)}
						{@const angle = (i / 15) * Math.PI * 2}
						{@const radius = 150 + (metrics.percentile * 0.5)}
						{@const x = 250 + Math.cos(angle) * radius}
						{@const y = 250 + Math.sin(angle) * radius}
						
						<div class="executive-node" 
							 style="left: {x}px; 
									top: {y}px; 
									background: radial-gradient(circle, {metrics.color}, transparent);
									box-shadow: 0 0 {20 + metrics.threatLevel * 0.5}px {metrics.color}"
							 on:click={() => drillDownExecutive(executive, count)}>
							<div class="node-core" style="color: {metrics.color}">
								{metrics.icon}
							</div>
							<div class="node-label">{executive.substring(0, 15).toUpperCase()}</div>
							<div class="node-power">{metrics.percentile}%</div>
						</div>
						
						<!-- Neural Connections -->
						<svg class="connection-lines" style="position: absolute; top: 0; left: 0; width: 500px; height: 500px; pointer-events: none;">
							{#each sortedExecutives.slice(i + 1, Math.min(i + 3, 15)) as [exec2, count2], j}
								{@const metrics2 = calculateExecutiveMetrics(count2)}
								{@const angle2 = ((i + j + 1) / 15) * Math.PI * 2}
								{@const radius2 = 150 + (metrics2.percentile * 0.5)}
								{@const x2 = 250 + Math.cos(angle2) * radius2}
								{@const y2 = 250 + Math.sin(angle2) * radius2}
								<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}"
									  stroke="{metrics.color}" 
									  stroke-width="0.5"
									  stroke-dasharray="2,3"
									  opacity="{0.2 + (Math.min(metrics.percentile, metrics2.percentile) / 200)}">
									<animate attributeName="stroke-dashoffset" 
											 values="0;10" 
											 dur="{2 + i * 0.1}s" 
											 repeatCount="indefinite"/>
								</line>
							{/each}
						</svg>
					{/each}
					
					<!-- Central Core -->
					<div class="network-core">
						<div class="core-pulse"></div>
						<div class="core-icon">◈</div>
						<div class="core-label">NEURAL CORE</div>
					</div>
				</div>
				
				<!-- Executive Data Table -->
				<div class="executive-data-matrix">
					<table class="matrix-table">
						<thead>
							<tr>
								<th>RANK</th>
								<th>ENTITY</th>
								<th>CLASSIFICATION</th>
								<th>NODES</th>
								<th>CONTROL</th>
								<th>THREAT</th>
								<th>QUANTUM_SIG</th>
							</tr>
						</thead>
						<tbody>
							{#each sortedExecutives as [executive, count], index}
								{@const metrics = calculateExecutiveMetrics(count)}
								<tr class="matrix-row" 
									style="border-left: 3px solid {metrics.color}"
									on:click={() => drillDownExecutive(executive, count)}>
									<td class="rank-cell">
										<span style="color: {metrics.color}">{index + 1}</span>
									</td>
									<td class="entity-cell">
										<span class="entity-icon" style="color: {metrics.color}">{metrics.icon}</span>
										<span class="entity-name">{executive.substring(0, 25).toUpperCase()}</span>
									</td>
									<td class="classification-cell">
										<span class="classification-badge" style="background: {metrics.color}20; color: {metrics.color}">
											{metrics.classification}
										</span>
									</td>
									<td class="numeric-cell">{count.toLocaleString()}</td>
									<td class="control-cell">
										<div class="control-bar">
											<div class="control-fill" style="width: {getPercentage(count)}%; background: {metrics.color}"></div>
										</div>
										<span class="control-text">{getPercentage(count)}%</span>
									</td>
									<td class="threat-cell">
										<div class="threat-meter">
											<div class="threat-level" style="height: {metrics.threatLevel}%; background: {metrics.color}"></div>
										</div>
										<span class="threat-value">{metrics.threatLevel}</span>
									</td>
									<td class="signature-cell">{metrics.quantumSignature}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.quantum-container {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		position: relative;
		overflow: hidden;
	}
	
	/* Particle Field */
	.particle-field {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	
	.quantum-particle {
		position: absolute;
		border-radius: 50%;
		animation: quantumFloat 20s linear infinite;
	}
	
	@keyframes quantumFloat {
		0% { transform: translate3d(0, 0, 0) scale(1); }
		25% { transform: translate3d(50px, -50px, 100px) scale(1.2); }
		50% { transform: translate3d(-50px, 50px, -100px) scale(0.8); }
		75% { transform: translate3d(30px, 30px, 50px) scale(1.1); }
		100% { transform: translate3d(0, 0, 0) scale(1); }
	}
	
	/* Neural Grid */
	.neural-grid {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	
	.executive-interface {
		position: relative;
		z-index: 1;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
	
	/* Quantum Header */
	.quantum-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.1), transparent);
		border-bottom: 1px solid rgba(0, 255, 255, 0.2);
		backdrop-filter: blur(10px);
	}
	
	.header-matrix {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.quantum-logo {
		width: 60px;
		height: 60px;
		perspective: 1000px;
	}
	
	.hologram-container {
		width: 100%;
		height: 100%;
		position: relative;
		transform-style: preserve-3d;
		transition: transform 0.6s;
	}
	
	.hologram-face {
		position: absolute;
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		color: #00ffff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
	}
	
	.hologram-face.front { transform: translateZ(30px); }
	.hologram-face.back { transform: rotateY(180deg) translateZ(30px); }
	.hologram-face.left { transform: rotateY(-90deg) translateZ(30px); }
	.hologram-face.right { transform: rotateY(90deg) translateZ(30px); }
	
	.header-text h1 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 300;
		letter-spacing: 0.3em;
		color: #00ffff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
	}
	
	/* Glitch Effect */
	.glitch-text {
		position: relative;
		animation: glitch 5s infinite;
	}
	
	.glitch-text::before,
	.glitch-text::after {
		content: attr(data-text);
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
	}
	
	.glitch-text::before {
		animation: glitch-1 0.5s infinite;
		color: #ff00ff;
		z-index: -1;
	}
	
	.glitch-text::after {
		animation: glitch-2 0.5s infinite;
		color: #00ff00;
		z-index: -2;
	}
	
	@keyframes glitch {
		0%, 100% { transform: translate(0); }
		20% { transform: translate(-1px, 1px); }
		40% { transform: translate(1px, -1px); }
		60% { transform: translate(-1px, -1px); }
		80% { transform: translate(1px, 1px); }
	}
	
	@keyframes glitch-1 {
		0%, 100% { clip-path: inset(0 0 0 0); transform: translate(0); }
		25% { clip-path: inset(0 0 20% 0); transform: translate(-2px, 2px); }
		50% { clip-path: inset(20% 0 30% 0); transform: translate(2px, -2px); }
		75% { clip-path: inset(40% 0 0 0); transform: translate(-2px, -2px); }
	}
	
	@keyframes glitch-2 {
		0%, 100% { clip-path: inset(0 0 0 0); transform: translate(0); }
		25% { clip-path: inset(30% 0 0 0); transform: translate(2px, -2px); }
		50% { clip-path: inset(0 0 40% 0); transform: translate(-2px, 2px); }
		75% { clip-path: inset(20% 0 20% 0); transform: translate(2px, 2px); }
	}
	
	.quantum-status {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-top: 0.5rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
	}
	
	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: statusPulse 2s ease-in-out infinite;
	}
	
	.status-indicator.synchronized { background: #00ff00; box-shadow: 0 0 10px #00ff00; }
	.status-indicator.processing { background: #ffff00; box-shadow: 0 0 10px #ffff00; }
	.status-indicator.analyzing { background: #00ffff; box-shadow: 0 0 10px #00ffff; }
	.status-indicator.correlating { background: #ff00ff; box-shadow: 0 0 10px #ff00ff; }
	.status-indicator.desynchronized { background: #ff0000; box-shadow: 0 0 10px #ff0000; }
	.status-indicator.deep_scanning { background: #ff6600; box-shadow: 0 0 10px #ff6600; animation: statusPulse 0.5s ease-in-out infinite; }
	
	@keyframes statusPulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.5); opacity: 0.5; }
	}
	
	/* Search Matrix */
	.search-matrix {
		position: relative;
		flex: 1;
		max-width: 400px;
		margin: 0 2rem;
	}
	
	.quantum-search {
		width: 100%;
		padding: 0.75rem 1rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 0;
		color: #00ffff;
		font-family: inherit;
		font-size: 0.9rem;
		letter-spacing: 0.1em;
		transition: all 0.3s ease;
	}
	
	.quantum-search:focus {
		outline: none;
		border-color: #00ffff;
		background: rgba(0, 255, 255, 0.05);
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
	}
	
	.search-scanner {
		position: absolute;
		bottom: 0;
		left: 0;
		width: 0;
		height: 1px;
		background: linear-gradient(90deg, transparent, #00ffff, transparent);
		transition: width 0.3s ease;
	}
	
	.search-scanner.active {
		width: 100%;
		animation: scan 2s linear infinite;
	}
	
	@keyframes scan {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100%); }
	}
	
	/* Metrics Display */
	.metrics-display {
		display: flex;
		gap: 2rem;
	}
	
	.metric-cell {
		text-align: center;
	}
	
	.metric-value {
		font-size: 1.8rem;
		font-weight: 100;
		color: #00ffff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
		font-family: 'Courier New', monospace;
	}
	
	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.2em;
		margin-top: 0.25rem;
	}
	
	/* Loading State */
	.quantum-loading {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.loading-core {
		position: relative;
		width: 120px;
		height: 120px;
	}
	
	.core-ring {
		position: absolute;
		border: 1px solid;
		border-radius: 50%;
		animation: coreRotate 3s linear infinite;
	}
	
	.ring-1 {
		inset: 0;
		border-color: #00ffff;
		animation-direction: normal;
	}
	
	.ring-2 {
		inset: 15px;
		border-color: #ff00ff;
		animation-direction: reverse;
		animation-duration: 4s;
	}
	
	.ring-3 {
		inset: 30px;
		border-color: #00ff00;
		animation-duration: 5s;
	}
	
	.core-center {
		position: absolute;
		inset: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		color: #00ffff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
	}
	
	@keyframes coreRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.loading-text {
		color: rgba(0, 255, 255, 0.6);
		font-size: 0.9rem;
		letter-spacing: 0.2em;
		animation: pulse 2s ease-in-out infinite;
	}
	
	@keyframes pulse {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 1; }
	}
	
	/* Neural Network Container */
	.neural-network-container {
		flex: 1;
		display: grid;
		grid-template-columns: 500px 1fr;
		gap: 2rem;
		padding: 2rem;
		overflow: hidden;
	}
	
	.network-visualization {
		position: relative;
		width: 500px;
		height: 500px;
		background: radial-gradient(circle at center, rgba(0, 255, 255, 0.05), transparent);
		border: 1px solid rgba(0, 255, 255, 0.1);
	}
	
	.executive-node {
		position: absolute;
		width: 80px;
		height: 80px;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		transform: translate(-50%, -50%);
	}
	
	.executive-node:hover {
		z-index: 100;
		transform: translate(-50%, -50%) scale(1.2);
	}
	
	.node-core {
		font-size: 1.5rem;
		margin-bottom: 0.25rem;
	}
	
	.node-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.8);
		text-align: center;
		letter-spacing: 0.05em;
	}
	
	.node-power {
		font-size: 0.7rem;
		color: #00ffff;
		font-weight: 600;
	}
	
	.network-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 100px;
		height: 100px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}
	
	.core-pulse {
		position: absolute;
		inset: -20px;
		border: 2px solid #00ffff;
		border-radius: 50%;
		animation: corePulse 3s ease-in-out infinite;
	}
	
	@keyframes corePulse {
		0%, 100% { transform: scale(1); opacity: 0; }
		50% { transform: scale(1.5); opacity: 0.5; }
	}
	
	.core-icon {
		font-size: 2rem;
		color: #00ffff;
		text-shadow: 0 0 30px rgba(0, 255, 255, 0.8);
		margin-bottom: 0.5rem;
	}
	
	.core-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
	}
	
	/* Executive Data Matrix */
	.executive-data-matrix {
		overflow: auto;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.1);
		backdrop-filter: blur(10px);
	}
	
	.matrix-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.matrix-table th {
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.1), rgba(0, 0, 0, 0.5));
		color: #00ffff;
		padding: 1rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 300;
		letter-spacing: 0.2em;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
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
		background: rgba(0, 255, 255, 0.05);
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
	
	.entity-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.entity-icon {
		font-size: 1.2rem;
	}
	
	.entity-name {
		font-weight: 300;
		letter-spacing: 0.05em;
	}
	
	.classification-badge {
		padding: 0.25rem 0.5rem;
		border-radius: 0;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		border: 1px solid currentColor;
	}
	
	.numeric-cell {
		font-family: 'Courier New', monospace;
		color: #00ffff;
	}
	
	.control-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.control-bar {
		flex: 1;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		position: relative;
		overflow: hidden;
	}
	
	.control-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.control-text {
		font-size: 0.7rem;
		min-width: 45px;
		text-align: right;
		color: rgba(255, 255, 255, 0.6);
	}
	
	.threat-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.threat-meter {
		width: 30px;
		height: 20px;
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.2);
		position: relative;
		overflow: hidden;
	}
	
	.threat-level {
		position: absolute;
		bottom: 0;
		left: 0;
		width: 100%;
		transition: height 0.5s ease;
	}
	
	.threat-value {
		font-size: 0.7rem;
		font-family: 'Courier New', monospace;
	}
	
	.signature-cell {
		font-family: 'Courier New', monospace;
		font-size: 0.65rem;
		color: rgba(0, 255, 255, 0.6);
		letter-spacing: 0.05em;
	}
	
	/* Detail View */
	.executive-detail-view {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: 2rem;
		overflow: hidden;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
	}
	
	.executive-hologram {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.hologram-avatar {
		width: 80px;
		height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 3rem;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.2), transparent);
		border: 2px solid #00ffff;
		animation: avatarPulse 3s ease-in-out infinite;
	}
	
	@keyframes avatarPulse {
		0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 255, 0.5); }
		50% { box-shadow: 0 0 40px rgba(0, 255, 255, 0.8); }
	}
	
	.executive-data h2 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 300;
		color: #00ffff;
		letter-spacing: 0.1em;
	}
	
	.executive-signature {
		font-family: 'Courier New', monospace;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.5);
		margin-top: 0.5rem;
		letter-spacing: 0.05em;
	}
	
	.quantum-close {
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
	}
	
	.quantum-close:hover {
		background: rgba(255, 0, 102, 0.1);
		box-shadow: 0 0 20px rgba(255, 0, 102, 0.5);
		transform: rotate(90deg);
	}
	
	.close-icon {
		font-size: 1.5rem;
	}
	
	.executive-metrics-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
		margin-bottom: 2rem;
	}
	
	.metric-card {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.05), rgba(0, 0, 0, 0.8));
		border: 1px solid rgba(0, 255, 255, 0.2);
		padding: 1.5rem;
		text-align: center;
	}
	
	.card-value {
		font-size: 1.5rem;
		font-weight: 100;
		color: #00ffff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
		margin-bottom: 0.5rem;
	}
	
	.card-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}
	
	.neural-data-stream {
		flex: 1;
		overflow: auto;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.1);
	}
	
	.quantum-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.quantum-table th {
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.1), rgba(0, 0, 0, 0.5));
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
	
	.data-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.2s ease;
	}
	
	.data-row:hover {
		background: rgba(0, 255, 255, 0.02);
	}
	
	.quantum-table td {
		padding: 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.node-id {
		font-family: 'Courier New', monospace;
		color: #00ffff;
		font-size: 0.7rem;
	}
	
	.data-cell {
		font-weight: 300;
		letter-spacing: 0.05em;
	}
	
	.status-quantum {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		font-size: 1rem;
	}
	
	.status-quantum.active {
		color: #00ff00;
		text-shadow: 0 0 10px #00ff00;
	}
	
	.status-quantum.inactive {
		color: #666666;
	}
	
	.status-quantum.secured {
		color: #00ffff;
		text-shadow: 0 0 10px #00ffff;
	}
	
	.status-quantum.vulnerable {
		color: #ff0066;
		text-shadow: 0 0 10px #ff0066;
	}
	
	/* Responsive */
	@media (max-width: 1400px) {
		.neural-network-container {
			grid-template-columns: 1fr;
		}
		
		.network-visualization {
			margin: 0 auto;
		}
	}
	
	@media (max-width: 768px) {
		.quantum-header {
			flex-direction: column;
			gap: 1rem;
		}
		
		.executive-metrics-grid {
			grid-template-columns: repeat(2, 1fr);
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
</style>