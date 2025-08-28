<!-- Advanced App.svelte with Cinematic UI -->
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
		{ id: 'source_tables', name: 'SOURCE', color: '#00ffff', icon: '◈', status: 'ACTIVE', load: 87 },
		{ id: 'region_metrics', name: 'REGIONS', color: '#00ff85', icon: '◉', status: 'ACTIVE', load: 78 },
		{ id: 'country_metrics', name: 'COUNTRIES', color: '#ffaa00', icon: '⬟', status: 'ACTIVE', load: 85 },
		{ id: 'data_center', name: 'CENTERS', color: '#ff0066', icon: '⬡', status: 'MONITORING', load: 73 },
		{ id: 'business_units', name: 'BUSINESS', color: '#00ff85', icon: '◒', status: 'ACTIVE', load: 81 },
		{ id: 'cio_metrics', name: 'CIO', color: '#ffaa00', icon: '◓', status: 'ACTIVE', load: 89 },
		{ id: 'advanced_analytics', name: 'AI CORE', color: '#ff00ff', icon: '◎', status: 'QUANTUM', load: 95 }
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

	<!-- Advanced Header -->
	<header class="system-header">
		<div class="header-content">
			<!-- Left: Brand & Status -->
			<div class="brand-section">
				<div class="ao1-logo-advanced">
					<div class="logo-hologram">
						{#each hologramLayers as layer, i}
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
				</div>
				<div class="brand-info">
					<h1 class="title">NEURAL INTELLIGENCE MATRIX</h1>
					<div class="subtitle">FISERV QUANTUM THREAT DETECTION SYSTEM</div>
					<div class="status-row">
						<span class="status-indicator {systemStatus === 'OPERATIONAL' ? 'active' : 'initializing'}">
							● {systemStatus}
						</span>
						<span class="threat-indicator" style="color: hsl({120 - threatLevel * 1.2}, 100%, 50%)">
							THREAT: {threatLevel.toFixed(1)}%
						</span>
						<span class="alert-counter {activeAlerts > 0 ? 'active' : ''}">
							⚠ {activeAlerts} ALERTS
						</span>
					</div>
				</div>
			</div>
			
			<!-- Center: Module Navigation -->
			<nav class="quantum-navigation">
				<div class="nav-container">
					<div class="nav-background"></div>
					{#each modules as module, i}
						<button 
							class="nav-module {currentView === module.id ? 'active' : ''} {getModuleStatus(module)}"
							style="--module-color: {module.color}; --delay: {i * 0.05}s"
							on:click={() => switchView(module.id)}>
							<div class="module-background"></div>
							<div class="module-content">
								<span class="module-icon">{module.icon}</span>
								<span class="module-name">{module.name}</span>
								<div class="module-load">
									<div class="load-bar" style="width: {module.load}%"></div>
								</div>
								<span class="module-status">{module.status}</span>
							</div>
						</button>
					{/each}
				</div>
			</nav>
			
			<!-- Right: Metrics Panel -->
			<div class="metrics-panel">
				<div class="metric-display">
					<div class="metric-label">QUANTUM COHERENCE</div>
					<div class="metric-value">{quantumCoherence.toFixed(1)}%</div>
					<div class="metric-bar">
						<div class="bar-fill" style="width: {quantumCoherence}%; background: linear-gradient(90deg, #00ffff, #ff00ff)"></div>
					</div>
				</div>
				<div class="metric-display">
					<div class="metric-label">DATA FLOW</div>
					<div class="metric-value">{dataFlowRate.toFixed(0)} TB/s</div>
					<div class="flow-indicator">
						{#each Array(5) as _, i}
							<div class="flow-dot" style="animation-delay: {i * 0.1}s"></div>
						{/each}
					</div>
				</div>
				<div class="time-display-advanced">
					<div class="time-label">SYSTEM TIME</div>
					<div class="time-value">{currentTime}</div>
					<div class="time-zone">UTC GLOBAL</div>
				</div>
			</div>
		</div>
	</header>

	<!-- Neural Activity Display -->
	<div class="neural-activity-bar">
		<div class="activity-label">NEURAL PATHWAYS</div>
		<div class="activity-graph">
			{#each neuralActivity as activity, i}
				<div class="activity-bar" 
					 style="height: {activity}%; 
							background: linear-gradient(180deg, 
								rgba(0, 255, 255, 0.8), 
								rgba(255, 0, 255, 0.4));
							animation-delay: {i * 0.05}s">
				</div>
			{/each}
		</div>
	</div>

	<!-- Main Viewport -->
	<section class="data-viewport-advanced">
		<div class="viewport-frame-advanced">
			<!-- Holographic Corners -->
			<div class="holo-corner tl">
				<svg width="60" height="60">
					<path d="M0,20 L0,0 L20,0" stroke="#00ffff" stroke-width="2" fill="none"/>
					<path d="M5,20 L5,5 L20,5" stroke="rgba(0, 255, 255, 0.3)" stroke-width="1" fill="none"/>
				</svg>
			</div>
			<div class="holo-corner tr">
				<svg width="60" height="60">
					<path d="M40,0 L60,0 L60,20" stroke="#00ffff" stroke-width="2" fill="none"/>
					<path d="M40,5 L55,5 L55,20" stroke="rgba(0, 255, 255, 0.3)" stroke-width="1" fill="none"/>
				</svg>
			</div>
			<div class="holo-corner bl">
				<svg width="60" height="60">
					<path d="M0,40 L0,60 L20,60" stroke="#00ffff" stroke-width="2" fill="none"/>
					<path d="M5,40 L5,55 L20,55" stroke="rgba(0, 255, 255, 0.3)" stroke-width="1" fill="none"/>
				</svg>
			</div>
			<div class="holo-corner br">
				<svg width="60" height="60">
					<path d="M40,60 L60,60 L60,40" stroke="#00ffff" stroke-width="2" fill="none"/>
					<path d="M40,55 L55,55 L55,40" stroke="rgba(0, 255, 255, 0.3)" stroke-width="1" fill="none"/>
				</svg>
			</div>
			
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
				{:else}
					<div class="ai-core-view">
						<h2>QUANTUM AI CORE ACTIVE</h2>
						<div class="quantum-visualization">
							<div class="quantum-sphere"></div>
						</div>
					</div>
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
		font-size: clamp(12px, 1.2vw, 16px);
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

	.system-header {
		background: linear-gradient(180deg, 
			rgba(0, 0, 0, 0.95) 0%, 
			rgba(26, 13, 46, 0.85) 50%,
			rgba(0, 0, 0, 0.95) 100%);
		border-bottom: 1px solid rgba(0, 255, 255, 0.5);
		backdrop-filter: blur(20px);
		z-index: 100;
		position: relative;
		box-shadow: 
			0 4px 30px rgba(0, 255, 255, 0.3),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
		flex-shrink: 0;
		padding: clamp(0.5rem, 1.5vh, 1rem) clamp(1rem, 2vw, 2rem);
	}

	.header-content {
		display: grid;
		grid-template-columns: minmax(300px, 1fr) minmax(500px, 2fr) minmax(250px, 1fr);
		align-items: center;
		gap: clamp(1rem, 2vw, 2rem);
		max-width: 100%;
		height: 100%;
	}

	.brand-section {
		display: flex;
		align-items: center;
		gap: clamp(0.8rem, 1.5vw, 1.5rem);
	}

	.ao1-logo-advanced {
		position: relative;
		width: clamp(60px, 5vw, 80px);
		height: clamp(60px, 5vw, 80px);
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

	.logo-text {
		font-size: clamp(0.8rem, 1.2vw, 1.2rem);
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
		font-size: clamp(1rem, 1.5vw, 1.4rem);
		font-weight: 800;
		background: linear-gradient(90deg, #00ffff, #ffffff, #ff00ff);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.subtitle {
		font-size: clamp(0.5rem, 0.8vw, 0.7rem);
		color: rgba(255, 255, 255, 0.7);
		text-transform: uppercase;
		letter-spacing: 0.15em;
		opacity: 0.8;
	}

	.status-row {
		display: flex;
		gap: 1rem;
		align-items: center;
		margin-top: 0.2rem;
	}

	.status-indicator {
		font-size: clamp(0.6rem, 0.8vw, 0.7rem);
		color: rgba(255, 255, 255, 0.6);
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}

	.status-indicator.active {
		color: #00ff85;
		text-shadow: 0 0 10px currentColor;
	}

	.threat-indicator {
		font-size: clamp(0.6rem, 0.8vw, 0.7rem);
		font-weight: 600;
		transition: color 0.3s ease;
	}

	.alert-counter {
		font-size: clamp(0.6rem, 0.8vw, 0.7rem);
		color: rgba(255, 255, 255, 0.4);
		transition: all 0.3s ease;
	}

	.alert-counter.active {
		color: #ff0066;
		animation: alertPulse 1s ease-in-out infinite;
	}

	@keyframes alertPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.quantum-navigation {
		display: flex;
		justify-content: center;
		align-items: center;
		position: relative;
	}

	.nav-container {
		display: flex;
		gap: clamp(0.3rem, 0.8vw, 0.6rem);
		position: relative;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 10px;
		backdrop-filter: blur(10px);
	}

	.nav-background {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			rgba(0, 255, 255, 0.05),
			rgba(255, 0, 255, 0.05),
			rgba(0, 255, 255, 0.05));
		border-radius: 10px;
		opacity: 0.5;
		z-index: -1;
	}

	.nav-module {
		position: relative;
		background: transparent;
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		padding: clamp(0.4rem, 0.8vw, 0.6rem) clamp(0.6rem, 1vw, 0.8rem);
		color: rgba(255, 255, 255, 0.6);
		cursor: pointer;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		overflow: hidden;
		animation: moduleEntry 0.6s ease-out backwards;
		animation-delay: var(--delay);
		min-width: clamp(80px, 10vw, 120px);
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
			rgba(0, 0, 0, 0.6),
			rgba(255, 255, 255, 0.02));
		z-index: -1;
		transition: all 0.3s ease;
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
			0 8px 20px color-mix(in srgb, var(--module-color) 30%, transparent),
			inset 0 1px 0 color-mix(in srgb, var(--module-color) 50%, transparent);
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
		0%, 100% { box-shadow: 0 0 10px rgba(255, 0, 102, 0.5); }
		50% { box-shadow: 0 0 20px rgba(255, 0, 102, 0.8); }
	}

	@keyframes quantumShimmer {
		0%, 100% { filter: hue-rotate(0deg); }
		50% { filter: hue-rotate(60deg); }
	}

	.module-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.2rem;
		position: relative;
		z-index: 1;
	}

	.module-icon {
		font-size: clamp(1rem, 1.5vw, 1.3rem);
		filter: drop-shadow(0 0 8px var(--module-color));
		animation: iconFloat 3s ease-in-out infinite;
		animation-delay: var(--delay);
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-2px); }
	}

	.module-name {
		font-size: clamp(0.55rem, 0.7vw, 0.65rem);
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
		font-size: clamp(0.45rem, 0.6vw, 0.55rem);
		opacity: 0.6;
		letter-spacing: 0.05em;
	}

	.metrics-panel {
		display: flex;
		flex-direction: column;
		gap: clamp(0.5rem, 1vh, 0.8rem);
		align-items: flex-end;
		min-width: 200px;
	}

	.metric-display {
		text-align: right;
	}

	.metric-label {
		font-size: clamp(0.5rem, 0.7vw, 0.6rem);
		color: rgba(255, 255, 255, 0.5);
		text-transform: uppercase;
		letter-spacing: 0.1em;
		margin-bottom: 0.1rem;
	}

	.metric-value {
		font-size: clamp(0.8rem, 1.2vw, 1.1rem);
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 10px currentColor;
	}

	.metric-bar {
		width: 100px;
		height: 3px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 2px;
		overflow: hidden;
		margin-top: 0.2rem;
	}

	.bar-fill {
		height: 100%;
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

	.time-display-advanced {
		margin-top: 0.5rem;
		padding-top: 0.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}

	.time-value {
		font-family: 'JetBrains Mono', monospace;
		font-size: clamp(0.65rem, 0.9vw, 0.8rem);
		color: #00ffff;
		text-shadow: 0 0 8px currentColor;
		letter-spacing: 0.05em;
	}

	.time-zone {
		font-size: clamp(0.45rem, 0.6vw, 0.55rem);
		color: rgba(255, 255, 255, 0.4);
		margin-top: 0.1rem;
	}

	.neural-activity-bar {
		background: rgba(0, 0, 0, 0.6);
		border-bottom: 1px solid rgba(0, 255, 255, 0.2);
		padding: clamp(0.3rem, 0.5vh, 0.5rem) clamp(1rem, 2vw, 2rem);
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.activity-label {
		font-size: clamp(0.6rem, 0.8vw, 0.7rem);
		color: rgba(255, 255, 255, 0.6);
		text-transform: uppercase;
		letter-spacing: 0.1em;
		min-width: 120px;
	}

	.activity-graph {
		flex: 1;
		height: 30px;
		display: flex;
		align-items: flex-end;
		gap: 2px;
		overflow: hidden;
	}

	.activity-bar {
		flex: 1;
		min-width: 3px;
		animation: activityPulse 2s ease-in-out infinite;
	}

	@keyframes activityPulse {
		0%, 100% { transform: scaleY(1); opacity: 0.8; }
		50% { transform: scaleY(1.2); opacity: 1; }
	}

	.data-viewport-advanced {
		flex: 1;
		position: relative;
		z-index: 10;
		padding: clamp(0.8rem, 1.5vh, 1rem);
		overflow: hidden;
		display: flex;
		align-items: stretch;
	}

	.viewport-frame-advanced {
		position: relative;
		width: 100%;
		height: 100%;
		background: 
			linear-gradient(135deg, 
				rgba(0, 0, 0, 0.4) 0%, 
				rgba(0, 255, 255, 0.02) 30%,
				rgba(255, 0, 255, 0.02) 70%,
				rgba(0, 0, 0, 0.4) 100%);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 12px;
		backdrop-filter: blur(15px);
		box-shadow: 
			0 10px 40px rgba(0, 0, 0, 0.5),
			inset 0 2px 0 rgba(255, 255, 255, 0.1),
			inset 0 -2px 0 rgba(0, 0, 0, 0.3);
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.holo-corner {
		position: absolute;
		z-index: 20;
		opacity: 0.8;
		animation: cornerPulse 3s ease-in-out infinite;
	}

	.holo-corner.tl { top: 0; left: 0; }
	.holo-corner.tr { top: 0; right: 0; }
	.holo-corner.bl { bottom: 0; left: 0; }
	.holo-corner.br { bottom: 0; right: 0; }

	@keyframes cornerPulse {
		0%, 100% { opacity: 0.8; }
		50% { opacity: 1; }
	}

	.content-stream {
		position: relative;
		z-index: 15;
		width: 100%;
		height: 100%;
		padding: clamp(1rem, 2vh, 1.5rem);
		overflow-y: auto;
		overflow-x: hidden;
		transition: opacity 0.3s ease;
	}

	.content-stream::-webkit-scrollbar {
		width: 8px;
	}

	.content-stream::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.3);
		border-radius: 4px;
	}

	.content-stream::-webkit-scrollbar-thumb {
		background: linear-gradient(180deg, #00ffff, #ff00ff);
		border-radius: 4px;
	}

	.ai-core-view {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		text-align: center;
	}

	.ai-core-view h2 {
		font-size: clamp(1.5rem, 2.5vw, 2rem);
		background: linear-gradient(90deg, #00ffff, #ff00ff, #00ffff);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		margin-bottom: 2rem;
		animation: aiTextGlow 2s ease-in-out infinite;
	}

	@keyframes aiTextGlow {
		0%, 100% { filter: drop-shadow(0 0 20px rgba(0, 255, 255, 0.8)); }
		50% { filter: drop-shadow(0 0 30px rgba(255, 0, 255, 0.8)); }
	}

	.quantum-visualization {
		position: relative;
		width: 300px;
		height: 300px;
	}

	.quantum-sphere {
		width: 100%;
		height: 100%;
		background: radial-gradient(circle at 30% 30%, 
			rgba(0, 255, 255, 0.8),
			rgba(255, 0, 255, 0.4),
			rgba(0, 0, 0, 0.8));
		border-radius: 50%;
		box-shadow: 
			0 0 60px rgba(0, 255, 255, 0.8),
			inset 0 0 60px rgba(255, 0, 255, 0.5),
			0 0 120px rgba(0, 255, 255, 0.4);
		animation: quantumSphere 4s ease-in-out infinite;
	}

	@keyframes quantumSphere {
		0%, 100% { 
			transform: rotate(0deg) scale(1);
			filter: hue-rotate(0deg);
		}
		25% { 
			transform: rotate(90deg) scale(1.05);
			filter: hue-rotate(45deg);
		}
		50% { 
			transform: rotate(180deg) scale(1.1);
			filter: hue-rotate(90deg);
		}
		75% { 
			transform: rotate(270deg) scale(1.05);
			filter: hue-rotate(45deg);
		}
	}

	/* Responsive Design */
	@media (max-width: 1400px) {
		.header-content {
			grid-template-columns: minmax(250px, 1fr) minmax(400px, 2fr) minmax(200px, 1fr);
		}
		
		.nav-module {
			min-width: clamp(70px, 9vw, 100px);
		}
	}

	@media (max-width: 1024px) {
		.header-content {
			grid-template-columns: 1fr;
			gap: 0.8rem;
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
		
		.neural-activity-bar {
			display: none;
		}
	}

	@media (max-width: 768px) {
		.nav-container {
			flex-wrap: wrap;
			justify-content: center;
			max-width: 100%;
		}
		
		.nav-module {
			min-width: calc(25% - 0.6rem);
			flex: 0 1 auto;
		}
		
		.module-status {
			display: none;
		}
		
		.metrics-panel {
			gap: 1rem;
		}
		
		.metric-display {
			text-align: center;
		}
	}

	@media (max-width: 480px) {
		.nav-module {
			min-width: calc(33.33% - 0.6rem);
		}
		
		.module-name {
			font-size: 0.5rem;
		}
		
		.module-load {
			display: none;
		}
		
		.ao1-logo-advanced {
			width: 50px;
			height: 50px;
		}
		
		.title {
			font-size: 0.9rem;
		}
		
		.subtitle {
			display: none;
		}
	}
</style>