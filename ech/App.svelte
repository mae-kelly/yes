<!-- Enhanced App.svelte with Ultra-Modern Header -->
<script>
	import { onMount, onDestroy } from 'svelte';
	import SourceTables from './SourceTables.svelte';
	import RegionMetrics from './RegionMetrics.svelte';
	import CountryMetrics from './CountryMetrics.svelte';
	import DataCenter from './DataCenter.svelte';
	import BusinessUnitMetrics from './BusinessUnitMetrics.svelte';
	import CIOMetrics from './CIOMetrics.svelte';

	let currentView = 'source_tables';
	let currentTime = '';
	let systemStatus = 'INITIALIZING';
	let threatLevel = 0;
	let activeAlerts = 0;
	let dataFlowRate = 0;
	let quantumCoherence = 98.7;
	let neuralActivity = [];
	let particleField = [];
	let glitchEffect = false;
	let scanlinePosition = 0;
	
	let modules = [
		{ id: 'source_tables', name: 'SOURCE INTELLIGENCE', color: '#00ffff', icon: '◈', status: 'ACTIVE', load: 87 },
		{ id: 'region_metrics', name: 'REGIONAL MATRIX', color: '#00ff85', icon: '◉', status: 'ACTIVE', load: 78 },
		{ id: 'country_metrics', name: 'GLOBAL SURVEILLANCE', color: '#ffaa00', icon: '⬟', status: 'ACTIVE', load: 85 },
		{ id: 'data_center', name: 'FACILITY INTELLIGENCE', color: '#ff0066', icon: '⬡', status: 'MONITORING', load: 73 },
		{ id: 'business_units', name: 'BUSINESS MATRIX', color: '#00ff85', icon: '◒', status: 'ACTIVE', load: 81 },
		{ id: 'cio_metrics', name: 'EXECUTIVE COMMAND', color: '#ff00ff', icon: '◓', status: 'ACTIVE', load: 89 }
	];

	let hologramLayers = [];
	let connectionPaths = [];
	let dataStreams = [];

	onMount(() => {
		// Time display with milliseconds
		const updateTime = () => {
			const now = new Date();
			currentTime = now.toISOString().slice(0, 23).replace('T', ' ') + 'Z';
		};
		updateTime();
		const timeInterval = setInterval(updateTime, 10);
		
		// System initialization sequence
		setTimeout(() => {
			systemStatus = 'CALIBRATING';
			setTimeout(() => {
				systemStatus = 'OPERATIONAL';
				initializeNeuralNetwork();
			}, 1500);
		}, 1000);

		// Initialize particle field
		for (let i = 0; i < 50; i++) {
			particleField.push({
				x: Math.random() * window.innerWidth,
				y: Math.random() * window.innerHeight,
				vx: (Math.random() - 0.5) * 2,
				vy: (Math.random() - 0.5) * 2,
				size: Math.random() * 3 + 1,
				opacity: Math.random() * 0.5 + 0.3,
				color: Math.random() > 0.5 ? '#00ffff' : '#ff00ff'
			});
		}

		// Neural activity simulation
		const neuralInterval = setInterval(() => {
			neuralActivity = Array.from({length: 20}, () => Math.random() * 100);
			threatLevel = Math.random() * 100;
			activeAlerts = Math.floor(Math.random() * 5);
			dataFlowRate = 50 + Math.random() * 50;
			quantumCoherence = 95 + Math.random() * 5;
			
			// Random glitch effect
			if (Math.random() < 0.02) {
				glitchEffect = true;
				setTimeout(() => glitchEffect = false, 100);
			}
		}, 2000);

		// Scanline animation
		const scanlineInterval = setInterval(() => {
			scanlinePosition = (scanlinePosition + 2) % 100;
		}, 50);

		// Module status updates
		const statusInterval = setInterval(() => {
			modules = modules.map(m => ({
				...m,
				load: Math.max(30, Math.min(100, m.load + (Math.random() - 0.5) * 10)),
				status: Math.random() > 0.95 ? 'ALERT' : Math.random() > 0.9 ? 'MONITORING' : 'ACTIVE'
			}));
		}, 3000);

		// Initialize hologram layers
		initializeHologramLayers();
		
		// Particle animation
		const animateParticles = () => {
			particleField = particleField.map(p => {
				p.x += p.vx;
				p.y += p.vy;
				if (p.x < 0 || p.x > window.innerWidth) p.vx *= -1;
				if (p.y < 0 || p.y > window.innerHeight) p.vy *= -1;
				return p;
			});
			requestAnimationFrame(animateParticles);
		};
		animateParticles();
		
		return () => {
			clearInterval(timeInterval);
			clearInterval(neuralInterval);
			clearInterval(scanlineInterval);
			clearInterval(statusInterval);
		};
	});

	function initializeNeuralNetwork() {
		// Create connection paths between modules
		for (let i = 0; i < modules.length - 1; i++) {
			connectionPaths.push({
				from: i,
				to: (i + 1) % modules.length,
				active: Math.random() > 0.3,
				strength: Math.random()
			});
		}
	}

	function initializeHologramLayers() {
		for (let i = 0; i < 5; i++) {
			hologramLayers.push({
				rotation: Math.random() * 360,
				scale: 0.8 + Math.random() * 0.4,
				opacity: 0.3 + Math.random() * 0.3
			});
		}
	}

	function switchView(moduleId) {
		// Add transition effect
		document.querySelector('.content-stream').style.opacity = '0';
		setTimeout(() => {
			currentView = moduleId;
			document.querySelector('.content-stream').style.opacity = '1';
		}, 300);
	}

	function getModuleStatus(module) {
		if (module.status === 'ALERT') return 'alert';
		if (module.status === 'MONITORING') return 'monitoring';
		if (module.status === 'QUANTUM') return 'quantum';
		return 'active';
	}
</script>

<main class="ao1-interface {glitchEffect ? 'glitch' : ''}">
	<!-- Particle Field Background -->
	<div class="particle-field">
		{#each particleField as particle}
			<div class="particle" 
				style="left: {particle.x}px; 
					   top: {particle.y}px; 
					   width: {particle.size}px; 
					   height: {particle.size}px;
					   background: {particle.color};
					   opacity: {particle.opacity};">
			</div>
		{/each}
	</div>

	<!-- Holographic Grid -->
	<div class="holographic-grid">
		<svg class="grid-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
			{#each Array(10) as _, i}
				<line x1="0" y1="{i * 10}" x2="100" y2="{i * 10}" 
					  stroke="rgba(0, 255, 255, 0.1)" stroke-width="0.1"/>
				<line x1="{i * 10}" y1="0" x2="{i * 10}" y2="100" 
					  stroke="rgba(0, 255, 255, 0.1)" stroke-width="0.1"/>
			{/each}
		</svg>
	</div>

	<!-- Scanline Effect -->
	<div class="scanline" style="top: {scanlinePosition}%"></div>

	<!-- Ultra-Modern Header -->
	<header class="system-header">
		<div class="header-quantum-field"></div>
		<div class="header-energy-wave"></div>
		<div class="header-content">
			<!-- Enhanced Logo Section -->
			<div class="brand-section">
				<div class="ao1-logo-ultra">
					<div class="logo-hologram">
						{#each hologramLayers as layer}
							<div class="hologram-layer" 
								 style="transform: rotate({layer.rotation}deg) scale({layer.scale}); 
										opacity: {layer.opacity};">
								<div class="hologram-ring"></div>
							</div>
						{/each}
					</div>
					<div class="logo-core">
						<span class="logo-text">AO1</span>
						<div class="quantum-indicator" style="opacity: {quantumCoherence / 100}"></div>
					</div>
					<div class="logo-energy"></div>
				</div>
				<div class="brand-info">
					<h1 class="title">NEURAL INTELLIGENCE MATRIX</h1>
					<div class="subtitle">FISERV QUANTUM THREAT DETECTION SYSTEM</div>
					<div class="status-row">
						<span class="status-indicator {systemStatus === 'OPERATIONAL' ? 'active' : 'initializing'}">
							<span class="status-dot"></span>
							{systemStatus}
						</span>
						<span class="threat-indicator" style="--threat-color: hsl({120 - threatLevel * 1.2}, 100%, 50%)">
							<span class="threat-icon">⚡</span>
							THREAT: {threatLevel.toFixed(1)}%
						</span>
						<span class="alert-counter {activeAlerts > 0 ? 'active' : ''}">
							<span class="alert-icon">⚠</span>
							{activeAlerts} ALERTS
						</span>
					</div>
				</div>
			</div>
			
			<!-- Ultra Navigation Modules -->
			<nav class="quantum-navigation">
				<div class="nav-container">
					<div class="nav-background"></div>
					<div class="nav-energy-field"></div>
					{#each modules as module, i}
						<button 
							class="nav-module {currentView === module.id ? 'active' : ''} {getModuleStatus(module)}"
							style="--module-color: {module.color}; --delay: {i * 0.05}s"
							on:click={() => switchView(module.id)}>
							<div class="module-background"></div>
							<div class="module-glow"></div>
							<div class="module-content">
								<span class="module-icon">{module.icon}</span>
								<span class="module-name">{module.name}</span>
								<div class="module-load">
									<div class="load-bar" style="width: {module.load}%"></div>
								</div>
								<span class="module-status">{module.status}</span>
							</div>
							{#if currentView === module.id}
								<div class="module-active-indicator"></div>
							{/if}
						</button>
					{/each}
				</div>
			</nav>
			
			<!-- Enhanced Metrics Panel -->
			<div class="metrics-panel">
				<div class="metric-display">
					<div class="metric-icon">◈</div>
					<div class="metric-info">
						<div class="metric-label">QUANTUM COHERENCE</div>
						<div class="metric-value">{quantumCoherence.toFixed(1)}%</div>
					</div>
					<div class="metric-bar">
						<div class="bar-fill" style="width: {quantumCoherence}%"></div>
					</div>
				</div>
				<div class="metric-display">
					<div class="metric-icon">◉</div>
					<div class="metric-info">
						<div class="metric-label">DATA FLOW</div>
						<div class="metric-value">{dataFlowRate.toFixed(0)} TB/s</div>
					</div>
					<div class="flow-indicator">
						{#each Array(5) as _, i}
							<div class="flow-dot" style="animation-delay: {i * 0.1}s"></div>
						{/each}
					</div>
				</div>
				<div class="time-display-ultra">
					<div class="time-icon">⬡</div>
					<div class="time-content">
						<div class="time-label">SYSTEM TIME</div>
						<div class="time-value">{currentTime}</div>
					</div>
				</div>
			</div>
		</div>
		<div class="header-border"></div>
	</header>

	<!-- Main Viewport -->
	<section class="data-viewport-advanced">
		<div class="viewport-frame-advanced">
			<!-- Content Stream -->
			<div class="content-stream">
				{#if currentView === 'source_tables'}
					<SourceTables />
				{:else if currentView === 'region_metrics'}
					<RegionMetrics />
				{:else if currentView === 'country_metrics'}
					<CountryMetrics />
				{:else if currentView === 'data_center'}
					<DataCenter />
				{:else if currentView === 'business_units'}
					<BusinessUnitMetrics />
				{:else if currentView === 'cio_metrics'}
					<CIOMetrics />
				{/if}
			</div>
		</div>
	</section>
</main>

<style>
	:global(body) {
		font-family: 'JetBrains Mono', 'Consolas', monospace;
		background: #000;
		color: #fff;
		overflow: hidden;
		margin: 0;
		padding: 0;
		font-size: 14px;
		line-height: 1.4;
		cursor: crosshair;
	}

	:global(*) {
		cursor: crosshair;
	}

	:global(button), :global(a), :global(input), :global(.clickable) {
		cursor: pointer !important;
	}

	.ao1-interface {
		width: 100vw;
		height: 100vh;
		position: fixed;
		top: 0;
		left: 0;
		display: flex;
		flex-direction: column;
		background: 
			radial-gradient(ellipse at 20% 30%, rgba(0, 255, 255, 0.15) 0%, transparent 40%),
			radial-gradient(ellipse at 80% 70%, rgba(255, 0, 255, 0.1) 0%, transparent 40%),
			radial-gradient(ellipse at center, rgba(26, 13, 46, 0.95) 0%, rgba(15, 5, 32, 0.95) 40%, rgba(0, 0, 0, 0.98) 100%);
		overflow: hidden;
	}

	.ao1-interface.glitch {
		animation: glitch 0.1s ease;
	}

	@keyframes glitch {
		0%, 100% { transform: translate(0); filter: hue-rotate(0deg); }
		20% { transform: translate(-2px, 2px); filter: hue-rotate(90deg); }
		40% { transform: translate(-2px, -2px); filter: hue-rotate(180deg); }
		60% { transform: translate(2px, 2px); filter: hue-rotate(270deg); }
		80% { transform: translate(2px, -2px); filter: hue-rotate(360deg); }
	}

	.particle-field {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
	}

	.particle {
		position: absolute;
		border-radius: 50%;
		filter: blur(1px);
		box-shadow: 0 0 10px currentColor;
		animation: particlePulse 4s ease-in-out infinite;
	}

	@keyframes particlePulse {
		0%, 100% { opacity: 0.3; }
		50% { opacity: 0.8; }
	}

	.holographic-grid {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 2;
		opacity: 0.3;
	}

	.grid-svg {
		width: 100%;
		height: 100%;
	}

	.scanline {
		position: fixed;
		left: 0;
		width: 100%;
		height: 3px;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(0, 255, 255, 0.4), 
			rgba(0, 255, 255, 0.8),
			rgba(0, 255, 255, 0.4),
			transparent);
		z-index: 3;
		pointer-events: none;
		filter: blur(1px);
	}

	/* Ultra-Modern Header Styles */
	.system-header {
		background: linear-gradient(180deg, 
			rgba(0, 0, 0, 0.98) 0%, 
			rgba(26, 13, 46, 0.95) 50%,
			rgba(0, 0, 0, 0.98) 100%);
		border-bottom: 2px solid transparent;
		backdrop-filter: blur(20px);
		z-index: 100;
		position: relative;
		padding: 1.5rem 2rem;
		flex-shrink: 0;
		overflow: visible;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8);
	}

	.header-quantum-field {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 100%;
		background: 
			radial-gradient(ellipse at 25% 0%, rgba(0, 255, 255, 0.15) 0%, transparent 35%),
			radial-gradient(ellipse at 75% 0%, rgba(255, 0, 255, 0.1) 0%, transparent 35%),
			radial-gradient(ellipse at 50% 0%, rgba(0, 150, 255, 0.08) 0%, transparent 40%);
		animation: quantumShift 15s ease-in-out infinite;
		pointer-events: none;
	}

	@keyframes quantumShift {
		0%, 100% { transform: translateY(0) scale(1); opacity: 0.8; }
		50% { transform: translateY(-10px) scale(1.05); opacity: 1; }
	}

	.header-energy-wave {
		position: absolute;
		bottom: 0;
		left: -100%;
		width: 300%;
		height: 2px;
		background: linear-gradient(90deg,
			transparent 0%,
			rgba(0, 255, 255, 0.8) 15%,
			rgba(255, 0, 255, 0.6) 30%,
			rgba(0, 255, 255, 0.8) 45%,
			transparent 60%);
		animation: energyWave 8s linear infinite;
		pointer-events: none;
	}

	@keyframes energyWave {
		0% { transform: translateX(0); }
		100% { transform: translateX(33.33%); }
	}

	.header-border {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		height: 2px;
		background: linear-gradient(90deg,
			transparent 0%,
			#00ffff 10%,
			#ff00ff 30%,
			#00ff85 50%,
			#ff00ff 70%,
			#00ffff 90%,
			transparent 100%);
		animation: borderFlow 4s linear infinite;
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.6);
	}

	@keyframes borderFlow {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100%); }
	}

	.header-content {
		display: grid;
		grid-template-columns: minmax(350px, auto) minmax(650px, 1fr) minmax(320px, auto);
		align-items: center;
		gap: 2.5rem;
		max-width: 100%;
		position: relative;
		z-index: 1;
	}

	/* Enhanced Brand Section */
	.brand-section {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.ao1-logo-ultra {
		position: relative;
		width: 100px;
		height: 100px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.logo-hologram {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.hologram-layer {
		position: absolute;
		width: 100%;
		height: 100%;
		animation: hologramRotate 10s linear infinite;
	}

	.hologram-ring {
		width: 100%;
		height: 100%;
		border: 2px solid;
		border-image: linear-gradient(45deg, #00ffff, #ff00ff, #00ffff) 1;
		border-radius: 50%;
		box-shadow: 
			0 0 30px currentColor,
			inset 0 0 20px currentColor;
	}

	@keyframes hologramRotate {
		0% { transform: rotate(0deg) scale(1); }
		50% { transform: rotate(180deg) scale(1.1); }
		100% { transform: rotate(360deg) scale(1); }
	}

	.logo-core {
		position: relative;
		width: 70%;
		height: 70%;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.9), rgba(255, 0, 255, 0.5));
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 
			0 0 40px rgba(0, 255, 255, 0.8),
			inset 0 0 30px rgba(255, 0, 255, 0.5);
		animation: corePulse 2s ease-in-out infinite;
	}

	.logo-energy {
		position: absolute;
		width: 130%;
		height: 130%;
		top: -15%;
		left: -15%;
		border-radius: 50%;
		background: radial-gradient(circle, transparent 30%, rgba(0, 255, 255, 0.2) 70%, transparent);
		animation: energyPulse 3s ease-in-out infinite;
	}

	@keyframes energyPulse {
		0%, 100% { transform: scale(1); opacity: 0; }
		50% { transform: scale(1.3); opacity: 1; }
	}

	.logo-text {
		font-size: 1.6rem;
		font-weight: 900;
		color: #ffffff;
		text-shadow: 
			0 0 20px rgba(0, 255, 255, 1),
			0 0 40px rgba(0, 255, 255, 0.8),
			0 0 60px rgba(255, 0, 255, 0.6);
		letter-spacing: 0.15em;
		animation: textGlow 3s ease-in-out infinite;
	}

	@keyframes textGlow {
		0%, 100% { text-shadow: 0 0 20px rgba(0, 255, 255, 1), 0 0 40px rgba(0, 255, 255, 0.8), 0 0 60px rgba(255, 0, 255, 0.6); }
		50% { text-shadow: 0 0 30px rgba(0, 255, 255, 1), 0 0 60px rgba(0, 255, 255, 0.9), 0 0 80px rgba(255, 0, 255, 0.7); }
	}

	.quantum-indicator {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 120%;
		height: 120%;
		transform: translate(-50%, -50%);
		border-radius: 50%;
		background: radial-gradient(circle, transparent 40%, rgba(255, 0, 255, 0.2));
		animation: quantumPulse 3s ease-in-out infinite;
	}

	@keyframes corePulse {
		0%, 100% { transform: scale(1); box-shadow: 0 0 40px rgba(0, 255, 255, 0.8), inset 0 0 30px rgba(255, 0, 255, 0.5); }
		50% { transform: scale(1.05); box-shadow: 0 0 60px rgba(0, 255, 255, 1), inset 0 0 40px rgba(255, 0, 255, 0.7); }
	}

	@keyframes quantumPulse {
		0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0; }
		50% { transform: translate(-50%, -50%) scale(1.5); opacity: 1; }
	}

	.brand-info {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.title {
		margin: 0;
		font-size: 1.6rem;
		font-weight: 800;
		background: linear-gradient(90deg, #00ffff, #ffffff, #ff00ff);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		text-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.08em;
		animation: titleShimmer 4s ease-in-out infinite;
	}

	@keyframes titleShimmer {
		0%, 100% { filter: brightness(1); }
		50% { filter: brightness(1.2); }
	}

	.subtitle {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
		text-transform: uppercase;
		letter-spacing: 0.2em;
		opacity: 0.9;
	}

	.status-row {
		display: flex;
		gap: 1.2rem;
		align-items: center;
		margin-top: 0.4rem;
	}

	.status-indicator {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.3rem 0.6rem;
		background: rgba(0, 255, 255, 0.05);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 6px;
		transition: all 0.3s ease;
	}

	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: #00ff85;
		animation: statusPulse 2s ease-in-out infinite;
		box-shadow: 0 0 10px currentColor;
	}

	@keyframes statusPulse {
		0%, 100% { opacity: 0.4; box-shadow: 0 0 10px currentColor; }
		50% { opacity: 1; box-shadow: 0 0 20px currentColor; }
	}

	.status-indicator.active {
		color: #00ff85;
		text-shadow: 0 0 15px currentColor;
		border-color: rgba(0, 255, 133, 0.4);
		background: rgba(0, 255, 133, 0.08);
	}

	.threat-indicator {
		font-size: 0.7rem;
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 0.4rem;
		padding: 0.3rem 0.6rem;
		background: rgba(255, 0, 255, 0.05);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 6px;
		color: var(--threat-color);
		transition: all 0.3s ease;
	}

	.threat-icon {
		font-size: 0.9rem;
		animation: threatPulse 1s ease-in-out infinite;
	}

	@keyframes threatPulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.2); }
	}

	.alert-counter {
		font-size: 0.7rem;
		display: flex;
		align-items: center;
		gap: 0.4rem;
		padding: 0.3rem 0.6rem;
		background: rgba(255, 102, 0, 0.05);
		border: 1px solid rgba(255, 102, 0, 0.2);
		border-radius: 6px;
		color: rgba(255, 255, 255, 0.4);
		transition: all 0.3s ease;
	}

	.alert-icon {
		font-size: 0.9rem;
	}

	.alert-counter.active {
		color: #ff0066;
		animation: alertPulse 1s ease-in-out infinite;
		border-color: rgba(255, 0, 102, 0.4);
		background: rgba(255, 0, 102, 0.12);
		box-shadow: 0 0 15px rgba(255, 0, 102, 0.3);
	}

	@keyframes alertPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.05); }
	}

	/* Ultra Navigation */
	.quantum-navigation {
		display: flex;
		justify-content: center;
		align-items: center;
		position: relative;
		flex: 1;
	}

	.nav-container {
		display: flex;
		gap: 1rem;
		position: relative;
		padding: 0.8rem;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 16px;
		backdrop-filter: blur(15px);
		border: 1px solid rgba(255, 255, 255, 0.08);
		box-shadow: 
			0 8px 32px rgba(0, 0, 0, 0.4),
			inset 0 1px 0 rgba(255, 255, 255, 0.05);
	}

	.nav-background {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			rgba(0, 255, 255, 0.03),
			rgba(255, 0, 255, 0.03),
			rgba(0, 255, 255, 0.03));
		border-radius: 16px;
		opacity: 0.5;
		z-index: -1;
	}

	.nav-energy-field {
		position: absolute;
		top: -8px;
		left: -8px;
		right: -8px;
		bottom: -8px;
		border-radius: 20px;
		background: linear-gradient(45deg,
			transparent 30%,
			rgba(0, 255, 255, 0.1) 50%,
			transparent 70%);
		animation: energyField 4s linear infinite;
		z-index: -2;
		pointer-events: none;
	}

	@keyframes energyField {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.nav-module {
		position: relative;
		background: transparent;
		border: 1px solid rgba(255, 255, 255, 0.15);
		border-radius: 12px;
		padding: 0.8rem 1.2rem;
		color: rgba(255, 255, 255, 0.7);
		cursor: pointer;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		overflow: hidden;
		animation: moduleEntry 0.6s ease-out backwards;
		animation-delay: var(--delay);
		min-width: 140px;
	}

	@keyframes moduleEntry {
		from {
			opacity: 0;
			transform: translateY(-20px) scale(0.9);
		}
		to {
			opacity: 1;
			transform: translateY(0) scale(1);
		}
	}

	.module-background {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.9),
			rgba(255, 255, 255, 0.02));
		z-index: -1;
		transition: all 0.3s ease;
		border-radius: 12px;
	}

	.module-glow {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 100%;
		height: 100%;
		transform: translate(-50%, -50%);
		background: radial-gradient(circle, var(--module-color), transparent);
		opacity: 0;
		transition: all 0.3s ease;
		filter: blur(25px);
		pointer-events: none;
	}

	.nav-module:hover .module-glow,
	.nav-module.active .module-glow {
		opacity: 0.4;
	}

	.nav-module:hover .module-background,
	.nav-module.active .module-background {
		background: linear-gradient(135deg, 
			color-mix(in srgb, var(--module-color) 25%, transparent),
			color-mix(in srgb, var(--module-color) 15%, transparent));
	}

	.nav-module:hover,
	.nav-module.active {
		border-color: var(--module-color);
		color: var(--module-color);
		transform: translateY(-3px) scale(1.03);
		box-shadow: 
			0 15px 35px color-mix(in srgb, var(--module-color) 35%, transparent),
			inset 0 1px 0 color-mix(in srgb, var(--module-color) 60%, transparent),
			0 0 40px color-mix(in srgb, var(--module-color) 25%, transparent);
	}

	.nav-module.alert {
		animation: moduleAlert 1s ease-in-out infinite;
		border-color: #ff0066;
	}

	.nav-module.monitoring {
		border-color: #ffaa00;
	}

	.nav-module.quantum {
		animation: quantumShimmer 2s ease-in-out infinite;
	}

	@keyframes moduleAlert {
		0%, 100% { box-shadow: 0 0 20px rgba(255, 0, 102, 0.5); }
		50% { box-shadow: 0 0 40px rgba(255, 0, 102, 0.8); }
	}

	@keyframes quantumShimmer {
		0%, 100% { filter: hue-rotate(0deg) brightness(1); }
		50% { filter: hue-rotate(60deg) brightness(1.2); }
	}

	.module-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.4rem;
		position: relative;
		z-index: 1;
	}

	.module-icon {
		font-size: 1.8rem;
		filter: drop-shadow(0 0 15px var(--module-color));
		animation: iconFloat 3s ease-in-out infinite;
		animation-delay: var(--delay);
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-3px); }
	}

	.module-name {
		font-size: 0.65rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-transform: uppercase;
	}

	.module-load {
		width: 100%;
		height: 3px;
		background: rgba(0, 0, 0, 0.6);
		border-radius: 2px;
		overflow: hidden;
		margin: 0.3rem 0;
	}

	.load-bar {
		height: 100%;
		background: linear-gradient(90deg, var(--module-color), transparent);
		transition: width 0.5s ease;
		box-shadow: 0 0 8px var(--module-color);
		position: relative;
		overflow: hidden;
	}

	.load-bar::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
		animation: loadShimmer 2s infinite;
	}

	@keyframes loadShimmer {
		to { left: 100%; }
	}

	.module-status {
		font-size: 0.55rem;
		opacity: 0.7;
		letter-spacing: 0.08em;
		font-weight: 600;
	}

	.module-active-indicator {
		position: absolute;
		bottom: -10px;
		left: 50%;
		transform: translateX(-50%);
		width: 40px;
		height: 4px;
		background: var(--module-color);
		border-radius: 2px;
		box-shadow: 0 0 15px var(--module-color);
		animation: activeGlow 1s ease-in-out infinite;
	}

	@keyframes activeGlow {
		0%, 100% { opacity: 0.8; width: 40px; }
		50% { opacity: 1; width: 50px; box-shadow: 0 0 25px var(--module-color); }
	}

	/* Enhanced Metrics Panel */
	.metrics-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		align-items: flex-end;
	}

	.metric-display {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		padding: 0.5rem 0.8rem;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(0, 255, 255, 0.15);
		border-radius: 8px;
		min-width: 240px;
		backdrop-filter: blur(10px);
		transition: all 0.3s ease;
	}

	.metric-display:hover {
		transform: translateX(-5px);
		border-color: rgba(0, 255, 255, 0.3);
		box-shadow: 0 5px 20px rgba(0, 255, 255, 0.2);
	}

	.metric-icon {
		font-size: 1.4rem;
		color: #00ffff;
		filter: drop-shadow(0 0 8px currentColor);
		animation: metricPulse 3s ease-in-out infinite;
	}

	@keyframes metricPulse {
		0%, 100% { transform: scale(1); opacity: 0.8; }
		50% { transform: scale(1.1); opacity: 1; }
	}

	.metric-info {
		flex: 1;
	}

	.metric-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		text-transform: uppercase;
		letter-spacing: 0.12em;
		font-weight: 600;
	}

	.metric-value {
		font-size: 1rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 15px currentColor;
	}

	.metric-bar {
		width: 100%;
		height: 4px;
		background: rgba(0, 0, 0, 0.6);
		border-radius: 2px;
		overflow: hidden;
		margin-top: 0.4rem;
	}

	.bar-fill {
		height: 100%;
		background: linear-gradient(90deg, #00ffff, #ff00ff);
		transition: width 0.3s ease;
		box-shadow: 0 0 12px currentColor;
		position: relative;
	}

	.bar-fill::after {
		content: '';
		position: absolute;
		top: 0;
		right: 0;
		width: 10px;
		height: 100%;
		background: rgba(255, 255, 255, 0.8);
		filter: blur(4px);
		animation: barGlint 2s ease-in-out infinite;
	}

	@keyframes barGlint {
		0%, 100% { opacity: 0; }
		50% { opacity: 1; }
	}

	.flow-indicator {
		display: flex;
		gap: 0.3rem;
		justify-content: flex-end;
		margin-top: 0.3rem;
	}

	.flow-dot {
		width: 5px;
		height: 5px;
		background: #00ffff;
		border-radius: 50%;
		animation: flowAnimation 1s ease-in-out infinite;
		box-shadow: 0 0 5px currentColor;
	}

	@keyframes flowAnimation {
		0%, 100% { opacity: 0.3; transform: scale(0.8); }
		50% { opacity: 1; transform: scale(1.3); }
	}

	.time-display-ultra {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		padding: 0.5rem 0.8rem;
		background: rgba(255, 0, 255, 0.05);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 8px;
		backdrop-filter: blur(10px);
		transition: all 0.3s ease;
	}

	.time-display-ultra:hover {
		transform: translateX(-5px);
		border-color: rgba(255, 0, 255, 0.3);
		box-shadow: 0 5px 20px rgba(255, 0, 255, 0.2);
	}

	.time-icon {
		font-size: 1.4rem;
		color: #ff00ff;
		filter: drop-shadow(0 0 8px currentColor);
		animation: timeRotate 10s linear infinite;
	}

	@keyframes timeRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.time-content {
		display: flex;
		flex-direction: column;
	}

	.time-value {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.75rem;
		color: #ff00ff;
		text-shadow: 0 0 10px currentColor;
		letter-spacing: 0.05em;
		font-weight: 600;
	}

	.time-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		text-transform: uppercase;
		letter-spacing: 0.12em;
		font-weight: 600;
	}

	/* Main Viewport */
	.data-viewport-advanced {
		flex: 1;
		position: relative;
		z-index: 10;
		overflow: hidden;
		display: flex;
		align-items: stretch;
	}

	.viewport-frame-advanced {
		position: relative;
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
	}

	.content-stream {
		position: relative;
		z-index: 15;
		width: 100%;
		height: 100%;
		overflow: hidden;
		transition: opacity 0.3s ease;
	}

	/* Responsive Design */
	@media (max-width: 1600px) {
		.header-content {
			grid-template-columns: minmax(320px, auto) minmax(600px, 1fr) minmax(280px, auto);
			gap: 2rem;
		}
		
		.nav-module {
			min-width: 120px;
			padding: 0.7rem 1rem;
		}
		
		.module-icon {
			font-size: 1.6rem;
		}
		
		.module-name {
			font-size: 0.6rem;
		}
	}

	@media (max-width: 1400px) {
		.header-content {
			grid-template-columns: minmax(300px, auto) minmax(550px, 1fr) minmax(260px, auto);
			gap: 1.5rem;
		}
		
		.nav-module {
			min-width: 110px;
			padding: 0.6rem 0.8rem;
		}
		
		.title {
			font-size: 1.4rem;
		}
	}

	@media (max-width: 1200px) {
		.header-content {
			grid-template-columns: 1fr;
			gap: 1.2rem;
		}
		
		.quantum-navigation {
			order: 3;
		}
		
		.metrics-panel {
			order: 2;
			flex-direction: row;
			justify-content: space-between;
			width: 100%;
		}
		
		.brand-section {
			order: 1;
		}
	}

	@media (max-width: 768px) {
		.nav-container {
			flex-wrap: wrap;
			justify-content: center;
			max-width: 100%;
		}
		
		.nav-module {
			min-width: calc(33.33% - 0.8rem);
			flex: 0 1 auto;
		}
		
		.module-status {
			display: none;
		}
		
		.metrics-panel {
			gap: 0.6rem;
		}
		
		.metric-display {
			min-width: auto;
			flex: 1;
		}
	}
</style>