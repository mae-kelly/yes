<!-- SourceTables.svelte - Quantum Frequency Analysis -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let particles = [];
	let glitchEffect = false;
	let hologramActive = false;
	
	// 3D rotation states
	let rotationX = 0;
	let rotationY = 0;
	let perspective = 1000;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			let result = await response.json();
			data = result;
			loading = false;
			
			// Initialize particle system
			for (let i = 0; i < 50; i++) {
				particles.push({
					x: Math.random() * 100,
					y: Math.random() * 100,
					z: Math.random() * 100,
					speed: Math.random() * 2 + 0.5
				});
			}
		} catch (err) {
			console.error('Source tables error:', err);
			loading = false;
		}
		
		// Glitch effect timer
		const glitchInterval = setInterval(() => {
			glitchEffect = true;
			setTimeout(() => glitchEffect = false, 100);
		}, 5000);
		
		// 3D rotation animation
		const rotateInterval = setInterval(() => {
			rotationY = Math.sin(Date.now() * 0.0005) * 10;
			rotationX = Math.cos(Date.now() * 0.0003) * 5;
		}, 50);
		
		return () => {
			clearInterval(glitchInterval);
			clearInterval(rotateInterval);
		};
	});

	$: filteredSources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxFreq = filteredSources.length > 0 ? Math.max(...filteredSources.map(([,f]) => f)) : 1;

	function getThreatLevel(frequency) {
		const percentage = (frequency / maxFreq) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#ff0066', glow: '0 0 40px #ff0066' };
		if (percentage >= 50) return { level: 'HIGH', color: '#ff9900', glow: '0 0 30px #ff9900' };
		if (percentage >= 25) return { level: 'MEDIUM', color: '#ffcc00', glow: '0 0 25px #ffcc00' };
		return { level: 'LOW', color: '#00ffff', glow: '0 0 20px #00ffff' };
	}

	async function drillDownSource(source, frequency) {
		selectedSource = { source, frequency };
		hologramActive = true;
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			hostDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Host search error:', err);
			hostDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		hologramActive = false;
		setTimeout(() => {
			selectedSource = null;
			hostDetails = [];
		}, 300);
	}
</script>

<div class="quantum-container {glitchEffect ? 'glitch' : ''}">
	<!-- Particle Background -->
	<div class="particle-system">
		{#each particles as particle}
			<div class="quantum-particle" 
				style="left: {particle.x}%; top: {particle.y}%; 
					   animation-duration: {particle.speed}s;
					   transform: translateZ({particle.z}px)">
			</div>
		{/each}
	</div>

	<div class="main-interface" style="transform: perspective({perspective}px) rotateX({rotationX}deg) rotateY({rotationY}deg)">
		<!-- Neural Grid Panel -->
		<div class="neural-panel">
			<div class="panel-frame">
				<div class="corner-accent top-left"></div>
				<div class="corner-accent top-right"></div>
				<div class="corner-accent bottom-left"></div>
				<div class="corner-accent bottom-right"></div>
				
				<div class="panel-header">
					<div class="header-circuits">
						<svg class="circuit-pattern" viewBox="0 0 200 40">
							<path d="M0,20 L50,20 L60,10 L90,10 L100,20 L200,20" 
								  stroke="#00ffff" stroke-width="1" fill="none" opacity="0.5"/>
							<circle cx="60" cy="10" r="3" fill="#00ffff"/>
							<circle cx="90" cy="10" r="3" fill="#00ffff"/>
						</svg>
					</div>
					
					<h3 class="panel-title">
						<span class="title-glow">QUANTUM FREQUENCY MATRIX</span>
						<span class="title-subtitle">SOURCE TABLE ANALYSIS</span>
					</h3>
					
					<div class="search-module">
						<div class="search-frame">
							<input 
								type="text" 
								bind:value={searchTerm}
								placeholder="INITIATE SEARCH PROTOCOL..."
								class="quantum-search"
							/>
							<div class="search-scanner"></div>
						</div>
					</div>
				</div>
				
				{#if loading && !selectedSource}
					<div class="loading-vortex">
						<div class="vortex-rings">
							<div class="vortex-ring ring-1"></div>
							<div class="vortex-ring ring-2"></div>
							<div class="vortex-ring ring-3"></div>
						</div>
						<p class="loading-text">QUANTUM TUNNELING IN PROGRESS...</p>
					</div>
				{:else if selectedSource}
					<div class="hologram-view {hologramActive ? 'active' : ''}">
						<div class="hologram-header">
							<h4 class="hologram-title">{selectedSource.source.toUpperCase()}</h4>
							<button class="close-hologram" on:click={closeDetails}>
								<svg width="24" height="24" viewBox="0 0 24 24">
									<path d="M6 6L18 18M18 6L6 18" stroke="#ff0066" stroke-width="2"/>
								</svg>
							</button>
						</div>
						
						<div class="hologram-stats">
							<div class="stat-orb">
								<div class="orb-value">{selectedSource.frequency.toLocaleString()}</div>
								<div class="orb-label">FREQUENCY</div>
							</div>
							<div class="stat-orb">
								<div class="orb-value">{hostDetails.length}</div>
								<div class="orb-label">HOSTS</div>
							</div>
						</div>
						
						<div class="hologram-grid">
							{#each hostDetails.slice(0, 10) as host}
								<div class="host-card">
									<div class="host-id">{host.host.substring(0, 20)}</div>
									<div class="host-metrics">
										<span class="metric-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
											CMDB
										</span>
										<span class="metric-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
											TANIUM
										</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{:else}
					<div class="frequency-matrix">
						{#each filteredSources.slice(0, 12) as [source, frequency]}
							{@const threat = getThreatLevel(frequency)}
							<div class="frequency-node" 
								 on:click={() => drillDownSource(source, frequency)}
								 style="--node-color: {threat.color}; --node-glow: {threat.glow}">
								
								<div class="node-hexagon">
									<svg viewBox="0 0 100 100" class="hex-svg">
										<polygon points="50,5 90,25 90,75 50,95 10,75 10,25" 
												fill="none" 
												stroke={threat.color} 
												stroke-width="2"/>
										<polygon points="50,10 85,28 85,72 50,90 15,72 15,28" 
												fill={threat.color} 
												opacity="0.1"/>
									</svg>
									
									<div class="node-core">
										<div class="frequency-value">{frequency}</div>
									</div>
								</div>
								
								<div class="node-label">{source.substring(0, 10).toUpperCase()}</div>
								
								<div class="threat-indicator">
									<span class="threat-level" style="color: {threat.color}">{threat.level}</span>
								</div>
								
								<div class="energy-field"></div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- Visualization Panel -->
		<div class="viz-panel">
			<!-- Quantum Metrics Display -->
			<div class="quantum-metrics">
				<div class="metric-module">
					<div class="metric-hologram">
						<div class="hologram-number">{filteredSources.length}</div>
						<div class="hologram-label">SOURCES</div>
						<div class="metric-pulse"></div>
					</div>
				</div>
				
				<div class="metric-module">
					<div class="metric-hologram">
						<div class="hologram-number">{(data.total_mentions || 0).toLocaleString()}</div>
						<div class="hologram-label">MENTIONS</div>
						<div class="metric-pulse"></div>
					</div>
				</div>
			</div>

			<!-- Waveform Visualizer -->
			<div class="waveform-display">
				<h4 class="display-title">FREQUENCY WAVEFORM</h4>
				<svg viewBox="0 0 400 200" class="waveform-svg">
					<defs>
						<linearGradient id="waveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
							<stop offset="0%" style="stop-color:#00ffff;stop-opacity:0.8" />
							<stop offset="100%" style="stop-color:#00ffff;stop-opacity:0" />
						</linearGradient>
					</defs>
					
					{#each filteredSources.slice(0, 20) as [source, frequency], i}
						{@const height = (frequency / maxFreq) * 80}
						{@const x = i * 20 + 10}
						<g class="wave-bar">
							<rect x="{x}" y="{100 - height}" width="15" height="{height}" 
								  fill="url(#waveGradient)" opacity="0.8"/>
							<rect x="{x}" y="{100}" width="15" height="{height}" 
								  fill="url(#waveGradient)" opacity="0.3" transform="scale(1, -1) translate(0, -200)"/>
						</g>
					{/each}
					
					<line x1="0" y1="100" x2="400" y2="100" stroke="#00ffff" stroke-width="0.5" opacity="0.5"/>
				</svg>
			</div>

			<!-- Threat Matrix 3D -->
			<div class="threat-matrix-3d">
				<h4 class="display-title">THREAT MATRIX</h4>
				<div class="matrix-3d-container">
					<div class="matrix-cube">
						{#each filteredSources.slice(0, 8) as [source, frequency], i}
							{@const threat = getThreatLevel(frequency)}
							{@const angle = (i / 8) * 360}
							{@const radius = 60}
							{@const x = Math.cos(angle * Math.PI / 180) * radius}
							{@const y = Math.sin(angle * Math.PI / 180) * radius}
							
							<div class="threat-node-3d" 
								 style="transform: translate3d({x}px, {y}px, {frequency/maxFreq * 50}px)">
								<div class="node-sphere" style="background: {threat.color}; box-shadow: {threat.glow}">
									<span class="node-freq">{frequency}</span>
								</div>
							</div>
						{/each}
						
						<div class="matrix-core">
							<div class="core-pulse"></div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.quantum-container {
		height: calc(100vh - 180px);
		position: relative;
		background: linear-gradient(135deg, #000000 0%, #0a0f1c 50%, #000000 100%);
		overflow: hidden;
		padding: 1.5rem;
	}

	.quantum-container.glitch {
		animation: glitchEffect 0.1s linear;
	}

	@keyframes glitchEffect {
		0%, 100% { transform: translateX(0); }
		20% { transform: translateX(-2px); }
		40% { transform: translateX(2px); }
		60% { transform: translateX(-1px); }
		80% { transform: translateX(1px); }
	}

	.particle-system {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		transform-style: preserve-3d;
	}

	.quantum-particle {
		position: absolute;
		width: 2px;
		height: 2px;
		background: #00ffff;
		border-radius: 50%;
		animation: particleFloat 10s linear infinite;
		box-shadow: 0 0 10px #00ffff;
	}

	@keyframes particleFloat {
		0% { transform: translateY(100vh) translateZ(0px); opacity: 0; }
		10% { opacity: 1; }
		90% { opacity: 1; }
		100% { transform: translateY(-10vh) translateZ(100px); opacity: 0; }
	}

	.main-interface {
		display: flex;
		gap: 2rem;
		height: 100%;
		transform-style: preserve-3d;
		transition: transform 0.3s ease;
	}

	.neural-panel {
		flex: 1.5;
		position: relative;
	}

	.panel-frame {
		height: 100%;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid #00ffff;
		border-radius: 8px;
		position: relative;
		backdrop-filter: blur(10px);
		overflow: hidden;
	}

	.corner-accent {
		position: absolute;
		width: 20px;
		height: 20px;
		border: 2px solid #00ffff;
	}

	.corner-accent.top-left {
		top: -1px;
		left: -1px;
		border-right: none;
		border-bottom: none;
	}

	.corner-accent.top-right {
		top: -1px;
		right: -1px;
		border-left: none;
		border-bottom: none;
	}

	.corner-accent.bottom-left {
		bottom: -1px;
		left: -1px;
		border-right: none;
		border-top: none;
	}

	.corner-accent.bottom-right {
		bottom: -1px;
		right: -1px;
		border-left: none;
		border-top: none;
	}

	.panel-header {
		padding: 1.5rem;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.05) 0%, transparent 100%);
		position: relative;
	}

	.header-circuits {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		opacity: 0.3;
	}

	.panel-title {
		position: relative;
		z-index: 1;
		margin-bottom: 1rem;
	}

	.title-glow {
		font-size: 1.5rem;
		color: #00ffff;
		text-shadow: 0 0 30px #00ffff, 0 0 60px #00ffff;
		font-weight: 700;
		letter-spacing: 0.1em;
		display: block;
	}

	.title-subtitle {
		font-size: 0.7rem;
		color: rgba(0, 255, 255, 0.6);
		letter-spacing: 0.3em;
		margin-top: 0.5rem;
		display: block;
	}

	.search-module {
		position: relative;
		z-index: 1;
	}

	.search-frame {
		position: relative;
		overflow: hidden;
		border-radius: 4px;
	}

	.quantum-search {
		width: 100%;
		padding: 0.8rem 1rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 255, 0.3);
		color: #00ffff;
		font-family: inherit;
		font-size: 0.9rem;
		letter-spacing: 0.05em;
		transition: all 0.3s ease;
	}

	.quantum-search:focus {
		outline: none;
		border-color: #00ffff;
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
		background: rgba(0, 255, 255, 0.02);
	}

	.search-scanner {
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.2), transparent);
		animation: scanLine 3s linear infinite;
		pointer-events: none;
	}

	@keyframes scanLine {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	.loading-vortex {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 400px;
	}

	.vortex-rings {
		position: relative;
		width: 150px;
		height: 150px;
	}

	.vortex-ring {
		position: absolute;
		border: 2px solid #00ffff;
		border-radius: 50%;
		box-shadow: 0 0 20px #00ffff;
	}

	.ring-1 {
		width: 150px;
		height: 150px;
		animation: vortexSpin 3s linear infinite;
	}

	.ring-2 {
		width: 100px;
		height: 100px;
		top: 25px;
		left: 25px;
		animation: vortexSpin 2s linear infinite reverse;
	}

	.ring-3 {
		width: 50px;
		height: 50px;
		top: 50px;
		left: 50px;
		animation: vortexSpin 1s linear infinite;
	}

	@keyframes vortexSpin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.frequency-matrix {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		gap: 1.5rem;
		padding: 2rem;
		overflow-y: auto;
		height: calc(100% - 120px);
	}

	.frequency-node {
		position: relative;
		cursor: pointer;
		transition: all 0.3s ease;
		transform-style: preserve-3d;
	}

	.frequency-node:hover {
		transform: translateZ(20px) scale(1.05);
	}

	.node-hexagon {
		position: relative;
		width: 120px;
		height: 120px;
		margin: 0 auto;
	}

	.hex-svg {
		width: 100%;
		height: 100%;
		filter: drop-shadow(var(--node-glow));
		animation: hexPulse 3s ease-in-out infinite;
	}

	@keyframes hexPulse {
		0%, 100% { opacity: 0.8; }
		50% { opacity: 1; }
	}

	.node-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
	}

	.frequency-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #ffffff;
		text-shadow: 0 0 20px var(--node-color);
	}

	.node-label {
		text-align: center;
		margin-top: 0.5rem;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
		letter-spacing: 0.1em;
	}

	.threat-indicator {
		text-align: center;
		margin-top: 0.3rem;
	}

	.threat-level {
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
	}

	.energy-field {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 150%;
		height: 150%;
		border-radius: 50%;
		background: radial-gradient(circle, var(--node-color), transparent);
		opacity: 0;
		transition: opacity 0.3s ease;
		pointer-events: none;
	}

	.frequency-node:hover .energy-field {
		opacity: 0.2;
	}

	.hologram-view {
		padding: 2rem;
		opacity: 0;
		transform: scale(0.9);
		transition: all 0.3s ease;
	}

	.hologram-view.active {
		opacity: 1;
		transform: scale(1);
	}

	.hologram-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
	}

	.hologram-title {
		font-size: 1.5rem;
		color: #00ffff;
		text-shadow: 0 0 30px #00ffff;
		margin: 0;
	}

	.close-hologram {
		background: rgba(255, 0, 102, 0.1);
		border: 1px solid #ff0066;
		width: 40px;
		height: 40px;
		border-radius: 4px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.3s ease;
	}

	.close-hologram:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: scale(1.1);
		box-shadow: 0 0 20px rgba(255, 0, 102, 0.5);
	}

	.hologram-stats {
		display: flex;
		gap: 2rem;
		margin-bottom: 2rem;
		justify-content: center;
	}

	.stat-orb {
		text-align: center;
		padding: 1.5rem;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.1), transparent);
		border-radius: 50%;
		border: 1px solid rgba(0, 255, 255, 0.3);
	}

	.orb-value {
		font-size: 2rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 20px #00ffff;
	}

	.orb-label {
		font-size: 0.7rem;
		color: rgba(0, 255, 255, 0.6);
		letter-spacing: 0.2em;
		margin-top: 0.5rem;
	}

	.hologram-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: 1rem;
		max-height: 400px;
		overflow-y: auto;
	}

	.host-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 4px;
		padding: 1rem;
		transition: all 0.3s ease;
	}

	.host-card:hover {
		border-color: #00ffff;
		background: rgba(0, 255, 255, 0.02);
		transform: translateY(-2px);
	}

	.host-id {
		font-family: 'Courier New', monospace;
		color: #00ffff;
		margin-bottom: 0.5rem;
		font-size: 0.9rem;
	}

	.host-metrics {
		display: flex;
		gap: 0.5rem;
	}

	.metric-badge {
		padding: 0.2rem 0.5rem;
		border-radius: 3px;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.metric-badge.active {
		background: rgba(0, 255, 133, 0.2);
		color: #00ff85;
		border: 1px solid #00ff85;
	}

	.metric-badge.inactive {
		background: rgba(255, 0, 102, 0.1);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		overflow-y: auto;
	}

	.quantum-metrics {
		display: flex;
		gap: 1rem;
	}

	.metric-module {
		flex: 1;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 8px;
		padding: 1.5rem;
		position: relative;
		overflow: hidden;
	}

	.metric-hologram {
		text-align: center;
		position: relative;
		z-index: 1;
	}

	.hologram-number {
		font-size: 2.5rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 30px #00ffff;
		animation: hologramFlicker 3s ease-in-out infinite;
	}

	@keyframes hologramFlicker {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.8; }
	}

	.hologram-label {
		font-size: 0.8rem;
		color: rgba(0, 255, 255, 0.6);
		letter-spacing: 0.2em;
		margin-top: 0.5rem;
	}

	.metric-pulse {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 200%;
		height: 200%;
		border-radius: 50%;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.2), transparent);
		animation: metricPulse 2s ease-in-out infinite;
	}

	@keyframes metricPulse {
		0%, 100% { transform: translate(-50%, -50%) scale(0.8); opacity: 0; }
		50% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
	}

	.waveform-display, .threat-matrix-3d {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 8px;
		padding: 1.5rem;
		backdrop-filter: blur(10px);
	}

	.display-title {
		margin: 0 0 1rem 0;
		font-size: 0.9rem;
		color: #00ffff;
		letter-spacing: 0.1em;
		font-weight: 600;
		text-shadow: 0 0 10px #00ffff;
	}

	.waveform-svg {
		width: 100%;
		height: auto;
	}

	.wave-bar {
		transition: all 0.3s ease;
	}

	.wave-bar:hover {
		opacity: 1;
		filter: brightness(1.2);
	}

	.matrix-3d-container {
		height: 200px;
		position: relative;
		perspective: 800px;
	}

	.matrix-cube {
		width: 100%;
		height: 100%;
		position: relative;
		transform-style: preserve-3d;
		animation: cubeRotate 10s linear infinite;
	}

	@keyframes cubeRotate {
		0% { transform: rotateY(0deg) rotateX(10deg); }
		100% { transform: rotateY(360deg) rotateX(10deg); }
	}

	.threat-node-3d {
		position: absolute;
		top: 50%;
		left: 50%;
		transform-style: preserve-3d;
		transition: all 0.3s ease;
	}

	.node-sphere {
		width: 30px;
		height: 30px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #ffffff;
		font-size: 0.7rem;
		font-weight: 600;
	}

	.matrix-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 40px;
		height: 40px;
		border-radius: 50%;
		background: radial-gradient(circle, #00ffff, transparent);
		animation: corePulse 2s ease-in-out infinite;
	}

	.core-pulse {
		width: 100%;
		height: 100%;
		border-radius: 50%;
		border: 2px solid #00ffff;
		animation: corePulseRing 2s ease-in-out infinite;
	}

	@keyframes corePulse {
		0%, 100% { transform: translate(-50%, -50%) scale(1); }
		50% { transform: translate(-50%, -50%) scale(1.2); }
	}

	@keyframes corePulseRing {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.5); opacity: 0.3; }
	}

	/* Scrollbar styling */
	::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}

	::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.3);
		border-radius: 4px;
	}

	::-webkit-scrollbar-thumb {
		background: linear-gradient(135deg, #00ffff, #0088ff);
		border-radius: 4px;
	}

	::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(135deg, #00ffff, #00ff85);
	}
</style>