<!-- Enhanced App.svelte with Professional Matrix-Style Header -->
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
	let systemStatus = 'OPERATIONAL';
	let threatLevel = 0;
	let activeAlerts = 0;
	let dataFlowRate = 0;
	let quantumCoherence = 98.7;
	
	let modules = [
		{ id: 'source_tables', name: 'SOURCE INTELLIGENCE', color: '#00ffff', icon: '◈', status: 'ACTIVE', load: 87 },
		{ id: 'region_metrics', name: 'REGIONAL MATRIX', color: '#00ff85', icon: '◉', status: 'ACTIVE', load: 78 },
		{ id: 'country_metrics', name: 'GLOBAL SURVEILLANCE', color: '#ffaa00', icon: '⬟', status: 'ACTIVE', load: 85 },
		{ id: 'data_center', name: 'FACILITY INTELLIGENCE', color: '#ff0066', icon: '⬡', status: 'MONITORING', load: 73 },
		{ id: 'business_units', name: 'BUSINESS MATRIX', color: '#00ff85', icon: '◒', status: 'ACTIVE', load: 81 },
		{ id: 'cio_metrics', name: 'EXECUTIVE COMMAND', color: '#ff00ff', icon: '◓', status: 'ACTIVE', load: 89 }
	];

	onMount(() => {
		// Time display
		const updateTime = () => {
			const now = new Date();
			currentTime = now.toISOString().slice(0, 23).replace('T', ' ') + 'Z';
		};
		updateTime();
		const timeInterval = setInterval(updateTime, 1000);

		// Update metrics
		const metricsInterval = setInterval(() => {
			threatLevel = Math.random() * 100;
			activeAlerts = Math.floor(Math.random() * 5);
			dataFlowRate = 50 + Math.random() * 50;
			quantumCoherence = 95 + Math.random() * 5;
			
			modules = modules.map(m => ({
				...m,
				load: Math.max(30, Math.min(100, m.load + (Math.random() - 0.5) * 10))
			}));
		}, 3000);
		
		return () => {
			clearInterval(timeInterval);
			clearInterval(metricsInterval);
		};
	});

	function switchView(moduleId) {
		currentView = moduleId;
	}
</script>

<main class="matrix-interface">
	<!-- Professional Matrix Header -->
	<header class="matrix-header">
		<div class="header-background"></div>
		<div class="header-container">
			<!-- Logo and Title Section -->
			<div class="brand-section">
				<div class="matrix-logo">
					<div class="logo-icon">◈</div>
					<div class="logo-pulse"></div>
				</div>
				<div class="brand-info">
					<h1 class="system-title">NEURAL INTELLIGENCE MATRIX</h1>
					<p class="system-subtitle">FISERV QUANTUM THREAT DETECTION SYSTEM</p>
				</div>
			</div>

			<!-- Status Metrics -->
			<div class="status-metrics">
				<div class="metric-item">
					<span class="metric-label">STATUS</span>
					<span class="metric-value active">{systemStatus}</span>
				</div>
				<div class="metric-item">
					<span class="metric-label">THREAT</span>
					<span class="metric-value" style="color: hsl({120 - threatLevel * 1.2}, 100%, 50%)">{threatLevel.toFixed(1)}%</span>
				</div>
				<div class="metric-item">
					<span class="metric-label">COHERENCE</span>
					<span class="metric-value">{quantumCoherence.toFixed(1)}%</span>
				</div>
				<div class="metric-item">
					<span class="metric-label">ALERTS</span>
					<span class="metric-value {activeAlerts > 0 ? 'alert' : ''}">{activeAlerts}</span>
				</div>
				<div class="metric-item">
					<span class="metric-label">FLOW</span>
					<span class="metric-value">{dataFlowRate.toFixed(0)} TB/s</span>
				</div>
				<div class="metric-item time">
					<span class="metric-label">SYSTEM TIME</span>
					<span class="metric-value">{currentTime}</span>
				</div>
			</div>
		</div>
	</header>

	<!-- Navigation Bar -->
	<nav class="matrix-nav">
		<div class="nav-container">
			{#each modules as module}
				<button 
					class="nav-module {currentView === module.id ? 'active' : ''}"
					style="--module-color: {module.color}"
					on:click={() => switchView(module.id)}>
					<span class="module-icon">{module.icon}</span>
					<div class="module-info">
						<span class="module-name">{module.name}</span>
						<div class="module-load">
							<div class="load-fill" style="width: {module.load}%; background: {module.color}"></div>
						</div>
					</div>
					{#if currentView === module.id}
						<div class="active-indicator"></div>
					{/if}
				</button>
			{/each}
		</div>
	</nav>

	<!-- Main Content -->
	<section class="matrix-viewport">
		<div class="content-container">
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
	}

	.matrix-interface {
		width: 100vw;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, rgba(0,0,0,0.95) 0%, rgba(26,13,46,0.95) 100%);
		overflow: hidden;
	}

	/* Professional Matrix Header */
	.matrix-header {
		background: rgba(0, 0, 0, 0.8);
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		padding: 1rem 1.5rem;
		backdrop-filter: blur(10px);
		position: relative;
		flex-shrink: 0;
	}

	.header-background {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			rgba(0, 255, 255, 0.03) 0%,
			rgba(255, 0, 255, 0.02) 50%,
			rgba(0, 255, 255, 0.03) 100%);
		opacity: 0.5;
		pointer-events: none;
	}

	.header-container {
		display: flex;
		justify-content: space-between;
		align-items: center;
		position: relative;
		z-index: 1;
	}

	/* Brand Section */
	.brand-section {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.matrix-logo {
		position: relative;
		width: 50px;
		height: 50px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.logo-icon {
		font-size: 2rem;
		color: #00ffff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
		animation: iconPulse 3s ease-in-out infinite;
		z-index: 1;
		position: relative;
	}

	.logo-pulse {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid #00ffff;
		border-radius: 50%;
		animation: pulse 2s ease-out infinite;
		opacity: 0;
	}

	@keyframes iconPulse {
		0%, 100% { transform: scale(1); opacity: 0.9; }
		50% { transform: scale(1.1); opacity: 1; }
	}

	@keyframes pulse {
		0% {
			transform: scale(1);
			opacity: 0.8;
		}
		100% {
			transform: scale(1.5);
			opacity: 0;
		}
	}

	.brand-info h1 {
		margin: 0;
		font-size: 1.3rem;
		color: #00ffff;
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.05em;
		font-weight: 600;
	}

	.system-subtitle {
		margin: 0.2rem 0 0 0;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	/* Status Metrics */
	.status-metrics {
		display: flex;
		gap: 2rem;
		align-items: center;
	}

	.metric-item {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.metric-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		text-transform: uppercase;
		letter-spacing: 0.1em;
		font-weight: 600;
	}

	.metric-value {
		font-size: 0.9rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 10px currentColor;
	}

	.metric-value.active {
		color: #00ff85;
	}

	.metric-value.alert {
		color: #ff0066;
		animation: alertBlink 1s ease-in-out infinite;
	}

	@keyframes alertBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.6; }
	}

	.metric-item.time .metric-value {
		font-size: 0.8rem;
		color: #ff00ff;
		font-family: 'JetBrains Mono', monospace;
	}

	/* Navigation Bar */
	.matrix-nav {
		background: rgba(0, 0, 0, 0.6);
		border-bottom: 1px solid rgba(0, 255, 255, 0.2);
		padding: 0.8rem 1.5rem;
		flex-shrink: 0;
	}

	.nav-container {
		display: flex;
		gap: 1rem;
		justify-content: center;
	}

	.nav-module {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		padding: 0.8rem 1.2rem;
		color: rgba(255, 255, 255, 0.6);
		cursor: pointer;
		transition: all 0.3s ease;
		position: relative;
		min-width: 180px;
	}

	.nav-module:hover {
		background: rgba(0, 0, 0, 0.8);
		border-color: var(--module-color);
		color: var(--module-color);
		transform: translateY(-2px);
		box-shadow: 0 5px 20px rgba(0, 0, 0, 0.4);
	}

	.nav-module.active {
		background: rgba(0, 0, 0, 0.9);
		border-color: var(--module-color);
		color: var(--module-color);
		box-shadow: 
			0 5px 20px rgba(0, 0, 0, 0.4),
			inset 0 1px 0 rgba(255, 255, 255, 0.05);
	}

	.module-icon {
		font-size: 1.5rem;
		filter: drop-shadow(0 0 10px var(--module-color));
	}

	.module-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.module-name {
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}

	.module-load {
		width: 100%;
		height: 3px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 2px;
		overflow: hidden;
	}

	.load-fill {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 5px currentColor;
		position: relative;
	}

	.load-fill::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
		animation: shimmer 2s infinite;
	}

	@keyframes shimmer {
		to { left: 100%; }
	}

	.active-indicator {
		position: absolute;
		bottom: -8px;
		left: 50%;
		transform: translateX(-50%);
		width: 30px;
		height: 2px;
		background: var(--module-color);
		box-shadow: 0 0 10px var(--module-color);
	}

	/* Main Viewport */
	.matrix-viewport {
		flex: 1;
		position: relative;
		overflow: hidden;
		display: flex;
	}

	.content-container {
		width: 100%;
		height: 100%;
		position: relative;
		overflow: hidden;
	}

	/* Responsive Design */
	@media (max-width: 1400px) {
		.status-metrics {
			gap: 1.5rem;
		}
		
		.nav-module {
			min-width: 160px;
			padding: 0.7rem 1rem;
		}
		
		.module-icon {
			font-size: 1.3rem;
		}
		
		.module-name {
			font-size: 0.65rem;
		}
	}

	@media (max-width: 1200px) {
		.header-container {
			flex-direction: column;
			gap: 1rem;
			align-items: flex-start;
		}
		
		.status-metrics {
			width: 100%;
			justify-content: space-between;
		}
		
		.nav-container {
			flex-wrap: wrap;
		}
		
		.nav-module {
			min-width: calc(33.33% - 0.7rem);
		}
	}

	@media (max-width: 768px) {
		.matrix-header {
			padding: 0.8rem 1rem;
		}
		
		.system-title {
			font-size: 1.1rem;
		}
		
		.status-metrics {
			gap: 1rem;
		}
		
		.metric-item {
			min-width: auto;
		}
		
		.nav-module {
			min-width: calc(50% - 0.5rem);
			padding: 0.6rem 0.8rem;
		}
	}
</style>