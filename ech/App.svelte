<!-- App.svelte - Log Lens Command Center -->
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
	let quantumCoherence = 98.7;
	let dataFlowRate = 0;
	
	let modules = [
		{ id: 'source_tables', name: 'TABLES', color: '#00ff88', icon: '⬢', status: 'ACTIVE', load: 87 },
		{ id: 'region_metrics', name: 'REGIONS', color: '#00ffdd', icon: '◈', status: 'ACTIVE', load: 78 },
		{ id: 'country_metrics', name: 'COUNTRIES', color: '#88ff00', icon: '⬡', status: 'ACTIVE', load: 85 },
		{ id: 'data_center', name: 'DATA CENTERS', color: '#00aaff', icon: '◇', status: 'MONITORING', load: 73 },
		{ id: 'business_units', name: 'DIVISIONS', color: '#0088ff', icon: '◉', status: 'ACTIVE', load: 81 },
		{ id: 'cio_metrics', name: 'CIOS', color: '#44ff00', icon: '◎', status: 'ACTIVE', load: 89 }
	];

	// Dynamic title mapping
	$: currentPageTitle = modules.find(m => m.id === currentView)?.name || 'LOG LENS';

	onMount(() => {
		// Time display
		const updateTime = () => {
			const now = new Date();
			currentTime = now.toISOString().slice(0, 19).replace('T', ' ') + 'Z';
		};
		updateTime();
		const timeInterval = setInterval(updateTime, 1000);

		// Update metrics
		const metricsInterval = setInterval(() => {
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
	<!-- Circuit Background -->
	<div class="circuit-layer">
		<svg class="circuit-svg" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
			<!-- Horizontal lines -->
			<line x1="0" y1="150" x2="400" y2="150" class="circuit-line" />
			<line x1="600" y1="150" x2="1200" y2="150" class="circuit-line" />
			<line x1="1400" y1="150" x2="1920" y2="150" class="circuit-line" />
			
			<line x1="0" y1="300" x2="300" y2="300" class="circuit-line" />
			<line x1="500" y1="300" x2="900" y2="300" class="circuit-line" />
			<line x1="1100" y1="300" x2="1920" y2="300" class="circuit-line" />
			
			<line x1="200" y1="600" x2="800" y2="600" class="circuit-line" />
			<line x1="1000" y1="600" x2="1600" y2="600" class="circuit-line" />
			
			<line x1="0" y1="850" x2="600" y2="850" class="circuit-line" />
			<line x1="800" y1="850" x2="1400" y2="850" class="circuit-line" />
			<line x1="1600" y1="850" x2="1920" y2="850" class="circuit-line" />
			
			<!-- Vertical lines -->
			<line x1="300" y1="0" x2="300" y2="400" class="circuit-line" />
			<line x1="300" y1="600" x2="300" y2="1080" class="circuit-line" />
			
			<line x1="700" y1="100" x2="700" y2="500" class="circuit-line" />
			<line x1="700" y1="700" x2="700" y2="1080" class="circuit-line" />
			
			<line x1="1200" y1="0" x2="1200" y2="350" class="circuit-line" />
			<line x1="1200" y1="550" x2="1200" y2="950" class="circuit-line" />
			
			<line x1="1600" y1="200" x2="1600" y2="700" class="circuit-line" />
			<line x1="1600" y1="900" x2="1600" y2="1080" class="circuit-line" />
			
			<!-- Circuit nodes -->
			<circle cx="300" cy="150" r="4" class="circuit-node" />
			<circle cx="700" cy="300" r="4" class="circuit-node" />
			<circle cx="1200" cy="600" r="4" class="circuit-node" />
			<circle cx="1600" cy="850" r="4" class="circuit-node" />
			
			<circle cx="500" cy="300" r="3" class="circuit-node small" />
			<circle cx="900" cy="600" r="3" class="circuit-node small" />
			<circle cx="400" cy="150" r="3" class="circuit-node small" />
			<circle cx="800" cy="850" r="3" class="circuit-node small" />
		</svg>
	</div>

	<!-- Command Header -->
	<header class="command-header">
		<div class="header-grid">
			<!-- Brand Section -->
			<div class="brand-section">
				<div class="logo-container">
					<div class="logo-core">👁</div>
					<div class="logo-ring"></div>
				</div>
				<div class="brand-text">
					<h1>AO1 VISIBILITY</h1>
					<p>{currentPageTitle}</p>
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
		background: #0a0f0a;
		color: #e0ffe0;
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
		background: radial-gradient(ellipse at center, #0f1f0f 0%, #051005 50%, #000800 100%);
		position: relative;
	}

	.circuit-layer {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 0;
		opacity: 0.15;
	}

	.circuit-svg {
		width: 100%;
		height: 100%;
	}

	.circuit-line {
		stroke: #00ff88;
		stroke-width: 1;
		fill: none;
		opacity: 0.3;
		animation: circuitPulse 4s ease-in-out infinite;
	}

	.circuit-node {
		fill: #00ffdd;
		opacity: 0.6;
		animation: nodePulse 2s ease-in-out infinite;
	}

	.circuit-node.small {
		fill: #88ff00;
		opacity: 0.4;
		animation: nodePulse 3s ease-in-out infinite;
	}

	@keyframes circuitPulse {
		0%, 100% { opacity: 0.3; }
		50% { opacity: 0.7; }
	}

	@keyframes nodePulse {
		0%, 100% { opacity: 0.6; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.2); }
	}

	/* Header - Fixed Height */
	.command-header {
		height: 100px;
		background: rgba(5, 20, 5, 0.95);
		border-bottom: 2px solid #00ff88;
		backdrop-filter: blur(15px);
		flex-shrink: 0;
		z-index: 10;
		position: relative;
		box-shadow: 0 2px 20px rgba(0, 255, 136, 0.3);
	}

	.header-grid {
		height: 100%;
		display: grid;
		grid-template-columns: 300px 1fr;
		gap: 2rem;
		padding: 0 2rem;
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
		width: 55px;
		height: 55px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.logo-core {
		font-size: 32px;
		color: #00ffdd;
		text-shadow: 0 0 25px rgba(0, 255, 221, 0.8), 0 0 40px rgba(0, 255, 221, 0.4);
		z-index: 1;
		animation: eyePulse 3s ease-in-out infinite;
	}

	.logo-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 3px solid #00ff88;
		border-radius: 8px;
		animation: ringRotate 12s linear infinite;
		opacity: 0.6;
		box-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
	}

	@keyframes eyePulse {
		0%, 100% { opacity: 0.9; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.15); }
	}

	@keyframes ringRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.brand-text h1 {
		margin: 0;
		font-size: 22px;
		color: #00ffdd;
		font-weight: 700;
		letter-spacing: 3px;
		text-shadow: 0 0 15px rgba(0, 255, 221, 0.6);
	}

	.brand-text p {
		margin: 5px 0 0 0;
		font-size: 14px;
		color: #88ff00;
		text-transform: uppercase;
		letter-spacing: 2px;
		font-weight: 600;
		text-shadow: 0 0 10px rgba(136, 255, 0, 0.5);
	}

	/* Navigation */
	.nav-section {
		display: flex;
		gap: 12px;
		justify-content: center;
		flex-wrap: wrap;
	}

	.nav-module {
		display: flex;
		align-items: center;
		gap: 10px;
		background: rgba(5, 20, 5, 0.8);
		border: 2px solid rgba(0, 255, 136, 0.3);
		border-radius: 8px;
		padding: 10px 16px;
		color: rgba(224, 255, 224, 0.7);
		cursor: pointer;
		transition: all 0.3s ease;
		min-width: 140px;
		position: relative;
		backdrop-filter: blur(5px);
	}

	.nav-module::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: linear-gradient(45deg, transparent, rgba(0, 255, 136, 0.1), transparent);
		opacity: 0;
		transition: opacity 0.3s ease;
		border-radius: 6px;
	}

	.nav-module:hover::before {
		opacity: 1;
	}

	.nav-module:hover {
		background: rgba(10, 30, 10, 0.9);
		border-color: var(--module-color);
		color: var(--module-color);
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4), 0 0 20px var(--module-color);
	}

	.nav-module.active {
		background: linear-gradient(135deg, 
			color-mix(in srgb, var(--module-color) 20%, transparent),
			color-mix(in srgb, var(--module-color) 8%, transparent));
		border-color: var(--module-color);
		color: var(--module-color);
		box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3), 0 0 25px var(--module-color);
		transform: translateY(-1px);
	}

	.module-icon {
		font-size: 20px;
		filter: drop-shadow(0 0 8px var(--module-color));
	}

	.module-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.module-name {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 1px;
	}

	.module-load {
		width: 100%;
		height: 3px;
		background: rgba(0, 0, 0, 0.6);
		border-radius: 2px;
		overflow: hidden;
		border: 1px solid rgba(0, 255, 136, 0.2);
	}

	.load-fill {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 8px currentColor;
		position: relative;
	}

	.load-fill::after {
		content: '';
		position: absolute;
		top: 0;
		right: 0;
		width: 20px;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6));
		animation: loadGlint 2s ease-in-out infinite;
	}

	@keyframes loadGlint {
		0%, 100% { opacity: 0; }
		50% { opacity: 1; }
	}

	/* Viewport */
	.viewport {
		flex: 1;
		position: relative;
		overflow: hidden;
		background: linear-gradient(180deg, rgba(5, 20, 5, 0.3) 0%, rgba(0, 15, 0, 0.6) 100%);
		z-index: 5;
	}

	/* Responsive */
	@media (max-width: 1400px) {
		.header-grid {
			grid-template-columns: 280px 1fr;
			gap: 1.5rem;
		}
		
		.nav-module {
			min-width: 130px;
			padding: 8px 14px;
		}
	}

	@media (max-width: 1200px) {
		.command-header {
			height: auto;
			padding: 15px 0;
		}
		
		.header-grid {
			grid-template-columns: 1fr;
			gap: 15px;
		}
		
		.brand-section {
			justify-content: center;
		}
		
		.nav-section {
			flex-wrap: wrap;
			padding: 10px 0;
		}
		
		.nav-module {
			min-width: calc(33.33% - 8px);
		}
	}

	@media (max-width: 768px) {
		.nav-module {
			min-width: calc(50% - 6px);
		}
	}
</style>