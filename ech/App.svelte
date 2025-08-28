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
		<div class="header-glow"></div>
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
		font-size: clamp(12px, 1.2vw, 14px);
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
			radial-gradient(ellipse at center, #1a0d2e 0%, #0f0520 40%, #000000 100%);
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
		padding: 1rem 1.5rem;
		flex-shrink: 0;
		overflow: visible;
	}

	.header-glow {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 100%;
		background: linear-gradient(90deg,
			transparent 0%,
			rgba(0, 255, 255, 0.1) 20%,
			rgba(255, 0, 255, 0.1) 50%,
			rgba(0, 255, 255, 0.1) 80%,
			transparent 100%);
		opacity: 0.5;
		animation: glowSlide 8s linear infinite;
	}

	@keyframes glowSlide {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100%); }
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
	}

	@keyframes borderFlow {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100%); }
	}

	.header-content {
		display: grid;
		grid-template-columns: minmax(320px, auto) minmax(600px, 1fr) minmax(280px, auto);
		align-items: center;
		gap: 2rem;
		max-width: 100%;
		position: relative;
		z-index: 1;
	}

	/* Enhanced Brand Section */
	.brand-section {
		display: flex;
		align-items: center;
		gap: 1.2rem;
	}

	.ao1-logo-ultra {
		position: relative;
		width: 80px;
		height: 80px;
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
		box-shadow: 0 0 20px currentColor;
	}

	@keyframes hologramRotate {
		0% { transform: rotate(0deg) scale(1); }
		50% { transform: rotate(180deg) scale(1.1); }
		100% { transform: rotate(360deg) scale(1); }
	}

	.logo-core {
		position: relative;
		width: 60%;
		height: 60%;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.8), rgba(255, 0, 255, 0.4));
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 
			0 0 30px rgba(0, 255, 255, 0.8),
			inset 0 0 20px rgba(255, 0, 255, 0.5);
		animation: corePulse 2s ease-in-out infinite;
	}

	.logo-energy {
		position: absolute;
		width: 120%;
		height: 120%;
		top: -10%;
		left: -10%;
		border-radius: 50%;
		background: radial-gradient(circle, transparent 30%, rgba(0, 255, 255, 0.2) 70%, transparent);
		animation: energyPulse 3s ease-in-out infinite;
	}

	@keyframes energyPulse {
		0%, 100% { transform: scale(1); opacity: 0; }
		50% { transform: scale(1.3); opacity: 1; }
	}

	.logo-text {
		font-size: 1.3rem;
		font-weight: 900;
		color: #ffffff;
		text-shadow: 
			0 0 10px rgba(0, 255, 255, 1),
			0 0 20px rgba(0, 255, 255, 0.8),
			0 0 30px rgba(255, 0, 255, 0.6);
		letter-spacing: 0.1em;
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
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.05); }
	}

	@keyframes quantumPulse {
		0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0; }
		50% { transform: translate(-50%, -50%) scale(1.5); opacity: 1; }
	}

	.brand-info {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.title {
		margin: 0;
		font-size: 1.4rem;
		font-weight: 800;
		background: linear-gradient(90deg, #00ffff, #ffffff, #ff00ff);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.subtitle {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
		text-transform: uppercase;
		letter-spacing: 0.15em;
		opacity: 0.8;
	}

	.status-row {
		display: flex;
		gap: 1rem;
		align-items: center;
		margin-top: 0.3rem;
	}

	.status-indicator {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		display: flex;
		align-items: center;
		gap: 0.4rem;
		padding: 0.2rem 0.5rem;
		background: rgba(0, 255, 255, 0.05);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 4px;
	}

	.status-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: #00ff85;
		animation: statusPulse 2s ease-in-out infinite;
	}

	@keyframes statusPulse {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 1; box-shadow: 0 0 10px currentColor; }
	}

	.status-indicator.active {
		color: #00ff85;
		text-shadow: 0 0 10px currentColor;
		border-color: rgba(0, 255, 133, 0.3);
	}

	.threat-indicator {
		font-size: 0.65rem;
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0.2rem 0.5rem;
		background: rgba(255, 0, 255, 0.05);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 4px;
		color: var(--threat-color);
	}

	.threat-icon {
		font-size: 0.8rem;
		animation: threatPulse 1s ease-in-out infinite;
	}

	@keyframes threatPulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.2); }
	}

	.alert-counter {
		font-size: 0.65rem;
		display: flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0.2rem 0.5rem;
		background: rgba(255, 102, 0, 0.05);
		border: 1px solid rgba(255, 102, 0, 0.2);
		border-radius: 4px;
		color: rgba(255, 255, 255, 0.4);
		transition: all 0.3s ease;
	}

	.alert-icon {
		font-size: 0.8rem;
	}

	.alert-counter.active {
		color: #ff0066;
		animation: alertPulse 1s ease-in-out infinite;
		border-color: rgba(255, 0, 102, 0.3);
		background: rgba(255, 0, 102, 0.1);
	}

	@keyframes alertPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
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
		gap: 0.8rem;
		position: relative;
		padding: 0.6rem;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 12px;
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.05);
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
		border-radius: 12px;
		opacity: 0.5;
		z-index: -1;
	}

	.nav-energy-field {
		position: absolute;
		top: -5px;
		left: -5px;
		right: -5px;
		bottom: -5px;
		border-radius: 14px;
		background: linear-gradient(45deg,
			transparent 30%,
			rgba(0, 255, 255, 0.1) 50%,
			transparent 70%);
		animation: energyField 4s linear infinite;
		z-index: -2;
	}

	@keyframes energyField {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.nav-module {
		position: relative;
		background: transparent;
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 10px;
		padding: 0.6rem 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		cursor: pointer;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		overflow: hidden;
		animation: moduleEntry 0.6s ease-out backwards;
		animation-delay: var(--delay);
		min-width: 110px;
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
			rgba(0, 0, 0, 0.8),
			rgba(255, 255, 255, 0.02));
		z-index: -1;
		transition: all 0.3s ease;
	}

	.module-glow {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 80%;
		height: 80%;
		transform: translate(-50%, -50%);
		background: radial-gradient(circle, var(--module-color), transparent);
		opacity: 0;
		transition: all 0.3s ease;
		filter: blur(20px);
	}

	.nav-module:hover .module-glow,
	.nav-module.active .module-glow {
		opacity: 0.3;
	}

	.nav-module:hover .module-background,
	.nav-module.active .module-background {
		background: linear-gradient(135deg, 
			color-mix(in srgb, var(--module-color) 20%, transparent),
			color-mix(in srgb, var(--module-color) 10%, transparent));
	}

	.nav-module:hover,
	.nav-module.active {
		border-color: var(--module-color);
		color: var(--module-color);
		transform: translateY(-2px) scale(1.02);
		box-shadow: 
			0 10px 25px color-mix(in srgb, var(--module-color) 30%, transparent),
			inset 0 1px 0 color-mix(in srgb, var(--module-color) 50%, transparent),
			0 0 30px color-mix(in srgb, var(--module-color) 20%, transparent);
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
		0%, 100% { box-shadow: 0 0 15px rgba(255, 0, 102, 0.5); }
		50% { box-shadow: 0 0 30px rgba(255, 0, 102, 0.8); }
	}

	@keyframes quantumShimmer {
		0%, 100% { filter: hue-rotate(0deg); }
		50% { filter: hue-rotate(60deg); }
	}

	.module-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.3rem;
		position: relative;
		z-index: 1;
	}

	.module-icon {
		font-size: 1.4rem;
		filter: drop-shadow(0 0 10px var(--module-color));
		animation: iconFloat 3s ease-in-out infinite;
		animation-delay: var(--delay);
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-2px); }
	}

	.module-name {
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.module-load {
		width: 100%;
		height: 2px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 1px;
		overflow: hidden;
		margin: 0.2rem 0;
	}

	.load-bar {
		height: 100%;
		background: linear-gradient(90deg, var(--module-color), transparent);
		transition: width 0.5s ease;
		box-shadow: 0 0 5px var(--module-color);
	}

	.module-status {
		font-size: 0.5rem;
		opacity: 0.6;
		letter-spacing: 0.05em;
	}

	.module-active-indicator {
		position: absolute;
		bottom: -8px;
		left: 50%;
		transform: translateX(-50%);
		width: 30px;
		height: 3px;
		background: var(--module-color);
		border-radius: 2px;
		box-shadow: 0 0 10px var(--module-color);
		animation: activeGlow 1s ease-in-out infinite;
	}

	@keyframes activeGlow {
		0%, 100% { opacity: 0.8; }
		50% { opacity: 1; box-shadow: 0 0 20px var(--module-color); }
	}

	/* Enhanced Metrics Panel */
	.metrics-panel {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		align-items: flex-end;
	}

	.metric-display {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		padding: 0.4rem 0.6rem;
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(0, 255, 255, 0.1);
		border-radius: 6px;
		min-width: 200px;
	}

	.metric-icon {
		font-size: 1.2rem;
		color: #00ffff;
		filter: drop-shadow(0 0 5px currentColor);
	}

	.metric-info {
		flex: 1;
	}

	.metric-label {
		font-size: 0.55rem;
		color: rgba(255, 255, 255, 0.5);
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.metric-value {
		font-size: 0.9rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 10px currentColor;
	}

	.metric-bar {
		width: 100%;
		height: 3px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 2px;
		overflow: hidden;
		margin-top: 0.3rem;
	}

	.bar-fill {
		height: 100%;
		background: linear-gradient(90deg, #00ffff, #ff00ff);
		transition: width 0.3s ease;
		box-shadow: 0 0 10px currentColor;
	}

	.flow-indicator {
		display: flex;
		gap: 0.2rem;
		justify-content: flex-end;
		margin-top: 0.2rem;
	}

	.flow-dot {
		width: 4px;
		height: 4px;
		background: #00ffff;
		border-radius: 50%;
		animation: flowAnimation 1s ease-in-out infinite;
	}

	@keyframes flowAnimation {
		0%, 100% { opacity: 0.3; transform: scale(0.8); }
		50% { opacity: 1; transform: scale(1.2); }
	}

	.time-display-ultra {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		padding: 0.4rem 0.6rem;
		background: rgba(255, 0, 255, 0.05);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 6px;
	}

	.time-icon {
		font-size: 1.2rem;
		color: #ff00ff;
		filter: drop-shadow(0 0 5px currentColor);
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
		font-size: 0.7rem;
		color: #ff00ff;
		text-shadow: 0 0 8px currentColor;
		letter-spacing: 0.05em;
	}

	.time-label {
		font-size: 0.55rem;
		color: rgba(255, 255, 255, 0.5);
		text-transform: uppercase;
		letter-spacing: 0.1em;
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
	@media (max-width: 1400px) {
		.header-content {
			grid-template-columns: minmax(280px, auto) minmax(500px, 1fr) minmax(240px, auto);
			gap: 1.5rem;
		}
		
		.nav-module {
			min-width: 95px;
			padding: 0.5rem 0.6rem;
		}
		
		.module-name {
			font-size: 0.55rem;
		}
	}

	@media (max-width: 1200px) {
		.header-content {
			grid-template-columns: 1fr;
			gap: 1rem;
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
			gap: 0.5rem;
		}
		
		.metric-display {
			min-width: auto;
			flex: 1;
		}
	}
</style>