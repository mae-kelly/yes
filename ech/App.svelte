<!-- Updated App.svelte with inline navigation -->
<script>
	import { onMount } from 'svelte';
	import SourceTables from './SourceTables.svelte';
	import DomainMetrics from './DomainMetrics.svelte';
	import InfrastructureType from './InfrastructureType.svelte';
	import RegionMetrics from './RegionMetrics.svelte';
	import CountryMetrics from './CountryMetrics.svelte';
	import DataCenter from './DataCenter.svelte';
	import ClassMetrics from './ClassMetrics.svelte';
	import BusinessUnitMetrics from './BusinessUnitMetrics.svelte';
	import CIOMetrics from './CIOMetrics.svelte';

	let currentView = 'source_tables';
	let currentTime = '';
	let systemStatus = 'INITIALIZING';
	
	let modules = [
		{ id: 'source_tables', name: 'SOURCE', color: '#00ffff', icon: '◈' },
		{ id: 'domain_metrics', name: '1DC vs FEAD', color: '#ff00ff', icon: '◆' },
		{ id: 'infrastructure_type', name: 'INFRA', color: '#0096ff', icon: '⬢' },
		{ id: 'region_metrics', name: 'REGIONS', color: '#00ff85', icon: '◉' },
		{ id: 'country_metrics', name: 'COUNTRIES', color: '#ffaa00', icon: '⬟' },
		{ id: 'data_center', name: 'CENTERS', color: '#ff0066', icon: '⬡' },
		{ id: 'class_metrics', name: 'CLASSES', color: '#ff00ff', icon: '◐' },
		{ id: 'business_units', name: 'BUSINESS', color: '#00ff85', icon: '◒' },
		{ id: 'cio_metrics', name: 'CIO', color: '#ffaa00', icon: '◓' },
		{ id: 'advanced_analytics', name: 'AI ANALYTICS', color: '#ff00ff', icon: '◎' }
	];

	onMount(() => {
		const updateTime = () => {
			const now = new Date();
			currentTime = now.toISOString().slice(0, 19).replace('T', ' ') + 'Z';
		};
		updateTime();
		const interval = setInterval(updateTime, 1000);
		
		setTimeout(() => {
			systemStatus = 'OPERATIONAL';
		}, 2000);
		
		return () => clearInterval(interval);
	});

	function switchView(moduleId) {
		currentView = moduleId;
	}
</script>

<main class="ao1-interface">
	<div class="matrix-rain">
		{#each Array(30) as _, i}
			<div class="rain-drop" style="left: {Math.random() * 100}%; animation-delay: {Math.random() * 5}s; animation-duration: {3 + Math.random() * 4}s;"></div>
		{/each}
	</div>

	<header class="system-header">
		<div class="header-content">
			<!-- Left side - Brand and title -->
			<div class="brand-section">
				<div class="ao1-logo">
					<div class="logo-rings">
						<div class="ring ring-outer"></div>
						<div class="ring ring-middle"></div>
						<div class="ring ring-inner"></div>
					</div>
					<div class="logo-center">AO1</div>
				</div>
				<div class="brand-text">
					<h1 class="title">LOG VISIBILITY MEASUREMENT</h1>
					<span class="subtitle">FISERV CSOC NEURAL THREAT INTELLIGENCE</span>
				</div>
			</div>
			
			<!-- Center - Navigation tabs -->
			<nav class="header-navigation">
				<div class="nav-scroll">
					{#each modules as module}
						<button 
							class="nav-tab {currentView === module.id ? 'active' : ''}"
							style="--module-color: {module.color}"
							on:click={() => switchView(module.id)}
						>
							<span class="tab-icon">{module.icon}</span>
							<span class="tab-name">{module.name}</span>
						</button>
					{/each}
				</div>
			</nav>
			
			<!-- Right side - Status panel -->
			<div class="status-panel">
				<div class="status-indicator {systemStatus === 'OPERATIONAL' ? 'active' : 'initializing'}">
					<div class="indicator-light"></div>
					<span class="status-text">{systemStatus}</span>
				</div>
				<div class="time-display">
					<span class="time-label">SYSTEM TIME</span>
					<span class="time-value">{currentTime}</span>
				</div>
			</div>
		</div>
	</header>

	<section class="data-viewport">
		<div class="viewport-frame">
			<div class="frame-corners">
				<div class="corner tl"></div>
				<div class="corner tr"></div>
				<div class="corner bl"></div>
				<div class="corner br"></div>
			</div>
			
			<div class="content-stream">
				{#if currentView === 'source_tables'}
					<SourceTables />
				{:else if currentView === 'domain_metrics'}
					<DomainMetrics />
				{:else if currentView === 'infrastructure_type'}
					<InfrastructureType />
				{:else if currentView === 'region_metrics'}
					<RegionMetrics />
				{:else if currentView === 'country_metrics'}
					<CountryMetrics />
				{:else if currentView === 'data_center'}
					<DataCenter />
				{:else if currentView === 'class_metrics'}
					<ClassMetrics />
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
		font-family: 'Orbitron', 'JetBrains Mono', monospace;
		background: #000;
		color: #fff;
		overflow: hidden;
		margin: 0;
		padding: 0;
		font-size: 14px;
		line-height: 1.4;
	}

	.ao1-interface {
		width: 100vw;
		height: 100vh;
		position: fixed;
		top: 0;
		left: 0;
		display: flex;
		flex-direction: column;
		background: radial-gradient(ellipse at center, #1a0d2e 0%, #0f0520 40%, #000000 100%);
		overflow: hidden;
	}

	.matrix-rain {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
	}

	.rain-drop {
		position: absolute;
		width: 2px;
		height: 20px;
		background: linear-gradient(180deg, transparent, #00ffff, transparent);
		animation: rainfall linear infinite;
		opacity: 0.15;
	}

	@keyframes rainfall {
		0% { transform: translateY(-100vh); }
		100% { transform: translateY(100vh); }
	}

	.system-header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.95), rgba(26, 13, 46, 0.85));
		border-bottom: 2px solid #00ffff;
		backdrop-filter: blur(25px);
		z-index: 10;
		position: relative;
		box-shadow: 0 4px 30px rgba(0, 255, 255, 0.2);
		flex-shrink: 0;
		padding: 1rem 1.5rem;
	}

	.header-content {
		display: grid;
		grid-template-columns: auto 1fr auto;
		align-items: center;
		gap: 2rem;
		max-width: 100%;
	}

	.brand-section {
		display: flex;
		align-items: center;
		gap: 1rem;
		min-width: 0;
	}

	.ao1-logo {
		position: relative;
		width: 50px;
		height: 50px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.logo-rings {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.ring {
		position: absolute;
		border-radius: 50%;
		border: 2px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: ringRotate 8s linear infinite;
	}

	.ring-outer {
		width: 50px;
		height: 50px;
		border-color: rgba(0, 255, 255, 0.6);
	}

	.ring-middle {
		width: 38px;
		height: 38px;
		border-color: rgba(255, 0, 255, 0.4);
		animation-direction: reverse;
		animation-duration: 6s;
	}

	.ring-inner {
		width: 26px;
		height: 26px;
		border-color: rgba(0, 150, 255, 0.8);
		animation-duration: 4s;
	}

	.logo-center {
		font-size: 0.9rem;
		font-weight: 700;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.8);
		z-index: 3;
		position: relative;
		animation: corePulse 3s ease-in-out infinite;
		letter-spacing: 0.1em;
	}

	.brand-text {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		min-width: 0;
	}

	.title {
		font-size: 1.1rem;
		font-weight: 700;
		color: #ffffff;
		margin: 0;
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.05em;
		white-space: nowrap;
	}

	.subtitle {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		text-transform: uppercase;
		letter-spacing: 0.1em;
		white-space: nowrap;
	}

	.header-navigation {
		flex: 1;
		display: flex;
		justify-content: center;
		min-width: 0;
		overflow: hidden;
	}

	.nav-scroll {
		display: flex;
		gap: 0.3rem;
		overflow-x: auto;
		padding: 0.2rem;
		scrollbar-width: none;
		-ms-overflow-style: none;
		max-width: 100%;
	}

	.nav-scroll::-webkit-scrollbar {
		display: none;
	}

	.nav-tab {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		padding: 0.4rem 0.7rem;
		color: rgba(255, 255, 255, 0.7);
		cursor: pointer;
		transition: all 0.3s ease;
		white-space: nowrap;
		display: flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.65rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.02em;
		flex-shrink: 0;
	}

	.nav-tab:hover,
	.nav-tab.active {
		border-color: var(--module-color);
		color: var(--module-color);
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
		transform: translateY(-1px);
		text-shadow: 0 0 6px var(--module-color);
	}

	.nav-tab.active {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 255, 255, 0.05));
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
	}

	.tab-icon {
		font-size: 0.8rem;
		animation: iconFloat 3s ease-in-out infinite;
		filter: drop-shadow(0 0 6px var(--module-color));
	}

	.tab-name {
		font-size: 0.6rem;
		letter-spacing: 0.05em;
	}

	.status-panel {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		align-items: flex-end;
		flex-shrink: 0;
	}

	.status-indicator {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.4rem 0.8rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.05));
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 4px;
		backdrop-filter: blur(10px);
	}

	.indicator-light {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: #ff0066;
		animation: statusPulse 2s ease-in-out infinite;
	}

	.status-indicator.active .indicator-light {
		background: #00ff85;
		box-shadow: 0 0 8px #00ff85;
	}

	.status-text {
		font-size: 0.6rem;
		font-weight: 600;
		color: #00ffff;
		letter-spacing: 0.05em;
	}

	.time-display {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		text-align: right;
	}

	.time-label {
		font-size: 0.5rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.time-value {
		font-size: 0.6rem;
		font-weight: 600;
		color: #00ffff;
		text-shadow: 0 0 6px rgba(0, 255, 255, 0.5);
		font-family: 'JetBrains Mono', monospace;
	}

	.data-viewport {
		flex: 1;
		position: relative;
		z-index: 5;
		padding: 1rem;
		overflow: hidden;
		min-height: 0;
	}

	.viewport-frame {
		position: relative;
		width: 100%;
		height: 100%;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.4) 0%, 
			rgba(0, 255, 255, 0.02) 50%,
			rgba(255, 0, 255, 0.02) 100%);
		border: 2px solid rgba(0, 255, 255, 0.2);
		border-radius: 10px;
		backdrop-filter: blur(20px);
		box-shadow: 
			0 8px 32px rgba(0, 0, 0, 0.3),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}

	.frame-corners {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
	}

	.corner {
		position: absolute;
		width: 20px;
		height: 20px;
		border: 2px solid rgba(0, 255, 255, 0.6);
	}

	.corner.tl {
		top: 10px;
		left: 10px;
		border-right: none;
		border-bottom: none;
		border-top-left-radius: 4px;
	}

	.corner.tr {
		top: 10px;
		right: 10px;
		border-left: none;
		border-bottom: none;
		border-top-right-radius: 4px;
	}

	.corner.bl {
		bottom: 10px;
		left: 10px;
		border-right: none;
		border-top: none;
		border-bottom-left-radius: 4px;
	}

	.corner.br {
		bottom: 10px;
		right: 10px;
		border-left: none;
		border-top: none;
		border-bottom-right-radius: 4px;
	}

	.content-stream {
		position: relative;
		z-index: 2;
		width: 100%;
		height: 100%;
		padding: 1.5rem;
		overflow-y: auto;
		overflow-x: hidden;
	}

	@keyframes ringRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes corePulse {
		0%, 100% { 
			opacity: 0.9; 
			transform: scale(1);
		}
		50% { 
			opacity: 1; 
			transform: scale(1.05);
		}
	}

	@keyframes statusPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-1px); }
	}

	/* Responsive design */
	@media (max-width: 1400px) {
		.header-content {
			grid-template-columns: 1fr auto;
		}
		
		.brand-section {
			justify-self: start;
		}
		
		.header-navigation {
			order: 3;
			grid-column: 1 / -1;
			margin-top: 1rem;
			padding-top: 1rem;
			border-top: 1px solid rgba(255, 255, 255, 0.1);
		}
		
		.status-panel {
			order: 2;
		}
	}

	@media (max-width: 768px) {
		.system-header {
			padding: 0.8rem 1rem;
		}
		
		.header-content {
			grid-template-columns: 1fr;
			gap: 1rem;
		}
		
		.brand-section {
			justify-self: center;
			text-align: center;
		}
		
		.title {
			font-size: 1rem;
		}
		
		.subtitle {
			font-size: 0.55rem;
		}
		
		.nav-tab {
			padding: 0.3rem 0.5rem;
		}
		
		.tab-name {
			font-size: 0.55rem;
		}
		
		.status-panel {
			flex-direction: row;
			justify-content: space-between;
			align-items: center;
		}
		
		.time-display {
			text-align: left;
		}
	}
</style>