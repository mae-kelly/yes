<script>
	import { onMount } from 'svelte';
	import SourceTables from './SourceTables.svelte';
	import DomainMetrics from './DomainMetrics.svelte';
	import InfrastructureType from './InfrastructureType.svelte';
	import RegionMetrics from './RegionMetrics.svelte';
	import CountryMetrics from './CountryMetrics.svelte';
	import DataCenterMetrics from './DataCenterMetrics.svelte';
	import ClassMetrics from './ClassMetrics.svelte';
	import SystemClassification from './SystemClassification.svelte';
	import BusinessUnitMetrics from './BusinessUnitMetrics.svelte';
	import CioMetrics from './CioMetrics.svelte';
	import TaniumCoverage from './TaniumCoverage.svelte';
	import CmdbPresence from './CmdbPresence.svelte';

	let currentView = 'source_tables';

	let modules = [
		{ id: 'source_tables', name: 'SRC', color: '#00ffff', icon: '◈' },
		{ id: 'domain_metrics', name: 'DOM', color: '#ff00ff', icon: '◆' },
		{ id: 'infrastructure_type', name: 'INF', color: '#0096ff', icon: '⬢' },
		{ id: 'region_metrics', name: 'REG', color: '#00ffff', icon: '◉' },
		{ id: 'country_metrics', name: 'CTY', color: '#ff00ff', icon: '⬟' },
		{ id: 'data_center', name: 'DC', color: '#0096ff', icon: '⬡' },
		{ id: 'class_metrics', name: 'CLS', color: '#ff00ff', icon: '◐' },
		{ id: 'system_classification', name: 'SYS', color: '#0096ff', icon: '◑' },
		{ id: 'business_unit', name: 'BIZ', color: '#00ffff', icon: '◒' },
		{ id: 'cio_metrics', name: 'CIO', color: '#ff00ff', icon: '◓' },
		{ id: 'tanium_coverage', name: 'TAN', color: '#0096ff', icon: '⬠' },
		{ id: 'cmdb_presence', name: 'CMB', color: '#00ffff', icon: '⬢' }
	];

	let currentTime = '';

	onMount(() => {
		let updateTime = () => {
			currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ') + 'Z';
		};
		updateTime();
		setInterval(updateTime, 1000);
	});

	function switchView(moduleId) {
		currentView = moduleId;
	}
</script>

<main class="cyberpunk-interface">
	<div class="matrix-rain">
		{#each Array(30) as _, i}
			<div class="rain-drop" style="left: {Math.random() * 100}%; animation-delay: {Math.random() * 5}s; animation-duration: {3 + Math.random() * 4}s;"></div>
		{/each}
	</div>

	<div class="neural-grid">
		{#each Array(20) as _, i}
			<div class="grid-line horizontal" style="top: {i * 5}%;"></div>
		{/each}
		{#each Array(20) as _, i}
			<div class="grid-line vertical" style="left: {i * 5}%;"></div>
		{/each}
	</div>

	<header class="cyber-header">
		<div class="header-content">
			<div class="brand-section">
				<div class="neural-logo">
					<div class="logo-rings">
						<div class="ring ring-outer"></div>
						<div class="ring ring-middle"></div>
						<div class="ring ring-inner"></div>
					</div>
					<div class="logo-center">◆</div>
				</div>
				<div class="brand-text">
					<h1 class="title">AO1 VISIBILITY</h1>
				</div>
			</div>
			
			<nav class="tab-navigation">
				{#each modules as module}
					<button 
						class="cyber-tab {currentView === module.id ? 'active' : ''}"
						style="--tab-color: {module.color}"
						on:click={() => switchView(module.id)}
					>
						<span class="tab-icon">{module.icon}</span>
						<span class="tab-name">{module.name}</span>
						<div class="tab-glow"></div>
					</button>
				{/each}
			</nav>
			
			<div class="time-panel">
				<div class="time-display">
					<span class="time-label">TIME</span>
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
					<DataCenterMetrics />
				{:else if currentView === 'class_metrics'}
					<ClassMetrics />
				{:else if currentView === 'system_classification'}
					<SystemClassification />
				{:else if currentView === 'business_unit'}
					<BusinessUnitMetrics />
				{:else if currentView === 'cio_metrics'}
					<CioMetrics />
				{:else if currentView === 'tanium_coverage'}
					<TaniumCoverage />
				{:else if currentView === 'cmdb_presence'}
					<CmdbPresence />
				{/if}
			</div>
		</div>
	</section>
</main>

<style>
	:global(body) {
		font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
		background: #000;
		color: #fff;
		overflow: hidden;
		margin: 0;
		padding: 0;
		font-size: 11px;
		line-height: 1.3;
	}

	.cyberpunk-interface {
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
		width: 1px;
		height: 12px;
		background: linear-gradient(180deg, transparent, #00ffff, transparent);
		animation: rainfall linear infinite;
		opacity: 0.15;
	}

	@keyframes rainfall {
		0% { transform: translateY(-100vh); }
		100% { transform: translateY(100vh); }
	}

	.neural-grid {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
		opacity: 0.05;
	}

	.grid-line {
		position: absolute;
		background: linear-gradient(90deg, transparent, #00ffff, transparent);
	}

	.grid-line.horizontal {
		width: 100%;
		height: 1px;
	}

	.grid-line.vertical {
		height: 100%;
		width: 1px;
		background: linear-gradient(180deg, transparent, #00ffff, transparent);
	}

	.cyber-header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.95), rgba(26, 13, 46, 0.85));
		border-bottom: 1px solid #00ffff;
		backdrop-filter: blur(25px);
		z-index: 10;
		position: relative;
		box-shadow: 0 2px 20px rgba(0, 255, 255, 0.15);
		padding: 0.3rem 0;
		flex-shrink: 0;
		height: 55px;
	}

	.header-content {
		display: flex;
		align-items: center;
		padding: 0.3rem 0.6rem;
		gap: 0.6rem;
		height: 100%;
	}

	.brand-section {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-shrink: 0;
	}

	.neural-logo {
		position: relative;
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.logo-rings {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.ring {
		position: absolute;
		border-radius: 50%;
		border: 1px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: ringRotate 8s linear infinite;
	}

	.ring-outer {
		width: 28px;
		height: 28px;
		border-color: rgba(0, 255, 255, 0.6);
	}

	.ring-middle {
		width: 20px;
		height: 20px;
		border-color: rgba(255, 0, 255, 0.4);
		animation-direction: reverse;
		animation-duration: 6s;
	}

	.ring-inner {
		width: 12px;
		height: 12px;
		border-color: rgba(0, 150, 255, 0.8);
		animation-duration: 4s;
	}

	.logo-center {
		font-size: 0.9rem;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.8);
		z-index: 3;
		position: relative;
		animation: corePulse 3s ease-in-out infinite;
	}

	.brand-text {
		display: flex;
		flex-direction: column;
	}

	.title {
		font-size: 0.8rem;
		font-weight: 700;
		color: #ffffff;
		margin: 0;
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.02em;
	}

	.tab-navigation {
		display: flex;
		flex: 1;
		gap: 0.15rem;
		overflow-x: auto;
		padding: 0.2rem 0;
		scrollbar-width: none;
		-ms-overflow-style: none;
		align-items: center;
		justify-content: center;
	}

	.tab-navigation::-webkit-scrollbar {
		display: none;
	}

	.cyber-tab {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.7) 0%, rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		padding: 0.25rem 0.4rem;
		color: #ffffff;
		font-family: inherit;
		font-size: 0.45rem;
		font-weight: 500;
		cursor: pointer;
		position: relative;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		white-space: nowrap;
		backdrop-filter: blur(10px);
		overflow: hidden;
		display: flex;
		align-items: center;
		gap: 0.2rem;
		text-transform: uppercase;
		letter-spacing: 0.02em;
		min-width: fit-content;
		height: 28px;
	}

	.cyber-tab::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
		transition: left 0.6s ease;
	}

	.cyber-tab:hover::before {
		left: 100%;
	}

	.cyber-tab:hover {
		border-color: var(--tab-color);
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(255, 255, 255, 0.05) 100%);
		transform: translateY(-1px);
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.4);
	}

	.cyber-tab.active {
		border-color: var(--tab-color);
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9) 0%, rgba(255, 255, 255, 0.08) 100%);
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
	}

	.tab-icon {
		font-size: 0.6rem;
		color: var(--tab-color);
		text-shadow: 0 0 6px var(--tab-color);
	}

	.tab-name {
		position: relative;
		z-index: 2;
		letter-spacing: 0.02em;
		font-size: 0.45rem;
	}

	.tab-glow {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: radial-gradient(circle, var(--tab-color), transparent);
		opacity: 0;
		transition: opacity 0.3s ease;
		border-radius: 3px;
	}

	.cyber-tab:hover .tab-glow,
	.cyber-tab.active .tab-glow {
		opacity: 0.05;
	}

	.time-panel {
		display: flex;
		align-items: center;
		flex-shrink: 0;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.7), rgba(0, 255, 255, 0.03));
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 4px;
		padding: 0.4rem 0.5rem;
		backdrop-filter: blur(10px);
	}

	.time-display {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		text-align: center;
	}

	.time-label {
		font-size: 0.4rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 400;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.time-value {
		font-size: 0.45rem;
		font-weight: 600;
		color: #ffffff;
	}

	.data-viewport {
		flex: 1;
		position: relative;
		z-index: 5;
		padding: 0.4rem;
		overflow: hidden;
		min-height: 0;
		height: calc(100vh - 55px);
	}

	.viewport-frame {
		position: relative;
		width: 100%;
		height: 100%;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.4) 0%, 
			rgba(0, 255, 255, 0.02) 50%,
			rgba(255, 0, 255, 0.02) 100%);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 8px;
		backdrop-filter: blur(20px);
		box-shadow: 
			0 6px 25px rgba(0, 0, 0, 0.3),
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
		width: 10px;
		height: 10px;
		border: 1px solid rgba(0, 255, 255, 0.6);
	}

	.corner.tl {
		top: 6px;
		left: 6px;
		border-right: none;
		border-bottom: none;
		border-top-left-radius: 2px;
	}

	.corner.tr {
		top: 6px;
		right: 6px;
		border-left: none;
		border-bottom: none;
		border-top-right-radius: 2px;
	}

	.corner.bl {
		bottom: 6px;
		left: 6px;
		border-right: none;
		border-top: none;
		border-bottom-left-radius: 2px;
	}

	.corner.br {
		bottom: 6px;
		right: 6px;
		border-left: none;
		border-top: none;
		border-bottom-right-radius: 2px;
	}

	.content-stream {
		position: relative;
		z-index: 2;
		width: 100%;
		height: 100%;
		padding: 0.6rem;
		overflow-y: auto;
		overflow-x: hidden;
	}

	:global(::-webkit-scrollbar) {
		width: 4px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 2px;
	}

	:global(::-webkit-scrollbar-thumb) {
		background: linear-gradient(135deg, 
			rgba(0, 255, 255, 0.6), 
			rgba(255, 0, 255, 0.4));
		border-radius: 2px;
		box-shadow: 0 0 6px rgba(0, 255, 255, 0.3);
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, 
			rgba(0, 255, 255, 0.8), 
			rgba(255, 0, 255, 0.6));
	}

	@keyframes ringRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes corePulse {
		0%, 100% { 
			opacity: 0.9; 
			transform: scale(1);
			text-shadow: 0 0 10px rgba(0, 255, 255, 0.8);
		}
		50% { 
			opacity: 1; 
			transform: scale(1.05);
			text-shadow: 0 0 15px rgba(0, 255, 255, 1);
		}
	}

	@media (max-width: 1400px) {
		.header-content {
			flex-wrap: wrap;
			padding: 0.5rem;
			gap: 0.4rem;
		}

		.tab-navigation {
			order: 3;
			width: 100%;
			margin-top: 0.3rem;
		}

		.cyber-header {
			height: auto;
		}

		.data-viewport {
			height: calc(100vh - 80px);
		}
	}

	@media (max-width: 768px) {
		.brand-section {
			flex-direction: column;
			text-align: center;
			gap: 0.2rem;
		}

		.cyber-tab {
			padding: 0.3rem 0.4rem;
			font-size: 0.4rem;
		}

		.data-viewport {
			padding: 0.3rem;
		}

		.content-stream {
			padding: 0.5rem;
		}
	}
</style>