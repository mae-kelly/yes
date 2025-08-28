<!-- App.svelte - Intelligence Command Center -->
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
		{ id: 'source_tables', name: 'SOURCE INTEL', color: '#00ff9f', icon: '◆', status: 'ACTIVE', load: 87 },
		{ id: 'region_metrics', name: 'REGIONAL OPS', color: '#00ffea', icon: '▣', status: 'ACTIVE', load: 78 },
		{ id: 'country_metrics', name: 'GLOBAL SCAN', color: '#ff9f00', icon: '◈', status: 'ACTIVE', load: 85 },
		{ id: 'data_center', name: 'FACILITY NET', color: '#ff3366', icon: '⬢', status: 'MONITORING', load: 73 },
		{ id: 'business_units', name: 'DIVISION CTL', color: '#9f00ff', icon: '◉', status: 'ACTIVE', load: 81 },
		{ id: 'cio_metrics', name: 'EXEC COMMAND', color: '#00ff00', icon: '◎', status: 'ACTIVE', load: 89 }
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

<main class="command-interface">
	<!-- Command Header -->
	<header class="command-header">
		<div class="header-grid">
			<!-- Brand Section -->
			<div class="brand-section">
				<div class="logo-container">
					<div class="logo-core">◈</div>
					<div class="logo-ring"></div>
				</div>
				<div class="brand-text">
					<h1>NEURAL COMMAND</h1>
					<p>FISERV INTELLIGENCE NETWORK</p>
				</div>
			</div>

			<!-- Navigation -->
			<nav class="nav-section">
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
					</button>
				{/each}
			</nav>

			<!-- Status Metrics -->
			<div class="status-section">
				<div class="metric">
					<span class="metric-label">STATUS</span>
					<span class="metric-value active">{systemStatus}</span>
				</div>
				<div class="metric">
					<span class="metric-label">THREAT</span>
					<span class="metric-value" style="color: hsl({120 - threatLevel * 1.2}, 100%, 50%)">{threatLevel.toFixed(1)}%</span>
				</div>
				<div class="metric">
					<span class="metric-label">ALERTS</span>
					<span class="metric-value {activeAlerts > 0 ? 'alert' : ''}">{activeAlerts}</span>
				</div>
				<div class="metric time">
					<span class="metric-value">{currentTime}</span>
				</div>
			</div>
		</div>
	</header>

	<!-- Main Viewport -->
	<section class="viewport">
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
	</section>
</main>

<style>
	:global(body) {
		font-family: 'JetBrains Mono', 'Courier New', monospace;
		background: #000;
		color: #fff;
		overflow: hidden;
		margin: 0;
		padding: 0;
		font-size: 13px;
		line-height: 1.4;
	}

	.command-interface {
		width: 100vw;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%);
	}

	/* Header - Fixed Height */
	.command-header {
		height: 80px;
		background: rgba(0, 0, 0, 0.95);
		border-bottom: 1px solid rgba(0, 255, 159, 0.2);
		backdrop-filter: blur(10px);
		flex-shrink: 0;
	}

	.header-grid {
		height: 100%;
		display: grid;
		grid-template-columns: 280px 1fr 320px;
		gap: 2rem;
		padding: 0 1.5rem;
		align-items: center;
	}

	/* Brand */
	.brand-section {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.logo-container {
		position: relative;
		width: 45px;
		height: 45px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.logo-core {
		font-size: 24px;
		color: #00ff9f;
		text-shadow: 0 0 20px rgba(0, 255, 159, 0.8);
		z-index: 1;
		animation: corePulse 3s ease-in-out infinite;
	}

	.logo-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid #00ff9f;
		border-radius: 4px;
		animation: ringRotate 8s linear infinite;
		opacity: 0.3;
	}

	@keyframes corePulse {
		0%, 100% { opacity: 0.8; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.1); }
	}

	@keyframes ringRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.brand-text h1 {
		margin: 0;
		font-size: 18px;
		color: #00ff9f;
		font-weight: 700;
		letter-spacing: 2px;
		text-shadow: 0 0 10px rgba(0, 255, 159, 0.5);
	}

	.brand-text p {
		margin: 2px 0 0 0;
		font-size: 10px;
		color: rgba(255, 255, 255, 0.5);
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	/* Navigation */
	.nav-section {
		display: flex;
		gap: 8px;
		justify-content: center;
	}

	.nav-module {
		display: flex;
		align-items: center;
		gap: 8px;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		padding: 8px 12px;
		color: rgba(255, 255, 255, 0.5);
		cursor: pointer;
		transition: all 0.2s ease;
		min-width: 130px;
	}

	.nav-module:hover {
		background: rgba(0, 0, 0, 0.9);
		border-color: var(--module-color);
		color: var(--module-color);
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
	}

	.nav-module.active {
		background: linear-gradient(135deg, 
			color-mix(in srgb, var(--module-color) 15%, transparent),
			color-mix(in srgb, var(--module-color) 5%, transparent));
		border-color: var(--module-color);
		color: var(--module-color);
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
	}

	.module-icon {
		font-size: 16px;
		filter: drop-shadow(0 0 4px var(--module-color));
	}

	.module-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.module-name {
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.5px;
	}

	.module-load {
		width: 100%;
		height: 2px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 1px;
		overflow: hidden;
	}

	.load-fill {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 4px currentColor;
	}

	/* Status */
	.status-section {
		display: flex;
		gap: 20px;
		align-items: center;
		justify-content: flex-end;
	}

	.metric {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.metric-label {
		font-size: 9px;
		color: rgba(255, 255, 255, 0.4);
		text-transform: uppercase;
		letter-spacing: 1px;
		font-weight: 600;
	}

	.metric-value {
		font-size: 14px;
		font-weight: 700;
		color: #00ffea;
		text-shadow: 0 0 8px currentColor;
	}

	.metric-value.active {
		color: #00ff9f;
	}

	.metric-value.alert {
		color: #ff3366;
		animation: alertPulse 1s ease-in-out infinite;
	}

	@keyframes alertPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.metric.time .metric-value {
		font-size: 11px;
		color: #9f00ff;
		font-family: 'Courier New', monospace;
	}

	/* Viewport */
	.viewport {
		flex: 1;
		position: relative;
		overflow: hidden;
		background: linear-gradient(180deg, rgba(0, 0, 0, 0.5) 0%, rgba(0, 0, 0, 0.8) 100%);
	}

	/* Responsive */
	@media (max-width: 1400px) {
		.header-grid {
			grid-template-columns: 260px 1fr 280px;
			gap: 1.5rem;
		}
		
		.nav-module {
			min-width: 120px;
			padding: 6px 10px;
		}
	}

	@media (max-width: 1200px) {
		.command-header {
			height: auto;
			padding: 12px 0;
		}
		
		.header-grid {
			grid-template-columns: 1fr;
			gap: 12px;
		}
		
		.brand-section {
			justify-content: center;
		}
		
		.nav-section {
			flex-wrap: wrap;
			padding: 8px 0;
		}
		
		.nav-module {
			min-width: calc(33.33% - 6px);
		}
		
		.status-section {
			justify-content: center;
			padding: 8px 0;
		}
	}

	@media (max-width: 768px) {
		.nav-module {
			min-width: calc(50% - 4px);
		}
		
		.status-section {
			flex-wrap: wrap;
			gap: 12px;
		}
	}
</style>