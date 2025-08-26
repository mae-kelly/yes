<!-- App.svelte -->
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
		{ id: 'source_tables', name: 'SOURCE INTEL', color: '#00ffff', icon: '◈' },
		{ id: 'domain_metrics', name: '1DC vs FEAD', color: '#ff00ff', icon: '◆' },
		{ id: 'infrastructure_type', name: 'INFRASTRUCTURE', color: '#0096ff', icon: '⬢' },
		{ id: 'region_metrics', name: 'GLOBAL REGIONS', color: '#00ffff', icon: '◉' },
		{ id: 'country_metrics', name: 'COUNTRY SCAN', color: '#ff00ff', icon: '⬟' },
		{ id: 'data_center', name: 'DATA CENTERS', color: '#0096ff', icon: '⬡' },
		{ id: 'class_metrics', name: 'CLASS ANALYSIS', color: '#ff00ff', icon: '◐' },
		{ id: 'system_classification', name: 'SYSTEM TYPES', color: '#0096ff', icon: '◑' },
		{ id: 'business_unit', name: 'BUSINESS UNITS', color: '#00ffff', icon: '◒' },
		{ id: 'cio_metrics', name: 'CIO ANALYSIS', color: '#ff00ff', icon: '◓' },
		{ id: 'tanium_coverage', name: 'TANIUM', color: '#0096ff', icon: '⬠' },
		{ id: 'cmdb_presence', name: 'CMDB STATUS', color: '#00ffff', icon: '⬢' }
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
	<!-- Animated background particles -->
	<div class="matrix-rain">
		{#each Array(50) as _, i}
			<div class="rain-drop" style="left: {Math.random() * 100}%; animation-delay: {Math.random() * 5}s; animation-duration: {3 + Math.random() * 4}s;"></div>
		{/each}
	</div>

	<!-- Neural grid pattern -->
	<div class="neural-grid">
		{#each Array(20) as _, i}
			<div class="grid-line horizontal" style="top: {i * 5}%;"></div>
		{/each}
		{#each Array(20) as _, i}
			<div class="grid-line vertical" style="left: {i * 5}%;"></div>
		{/each}
	</div>

	<!-- Header with branding and time -->
	<header class="cyber-header">
		<div class="header-left">
			<div class="neural-logo">
				<div class="logo-rings">
					<div class="ring ring-outer"></div>
					<div class="ring ring-middle"></div>
					<div class="ring ring-inner"></div>
				</div>
				<div class="logo-center">◆</div>
			</div>
			<div class="system-title">
				<h1>AO1 VISIBILITY</h1>
				<p>CYBERSECURITY OPERATIONS CENTER</p>
			</div>
		</div>

		<div class="header-right">
			<div class="time-display">
				<div class="time-label">SYSTEM TIME</div>
				<div class="time-value">{currentTime}</div>
			</div>
		</div>
	</header>

	<!-- Top navigation tabs -->
	<nav class="top-navigation">
		{#each modules as module, i}
			<button 
				class="cyber-tab {currentView === module.id ? 'active' : ''}"
				style="--tab-color: {module.color}; --delay: {i * 0.1}s"
				on:click={() => switchView(module.id)}
			>
				<div class="tab-icon">{module.icon}</div>
				<span class="tab-name">{module.name}</span>
				<div class="tab-glow"></div>
			</button>
		{/each}
	</nav>

	<!-- Main content viewport -->
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
		font-family: 'Orbitron', 'Exo 2', 'Rajdhani', monospace;
		background: #000;
		color: #fff;
		overflow-x: hidden;
		margin: 0;
		padding: 0;
	}

	.cyberpunk-interface {
		width: 100vw;
		height: 100vh;
		position: relative;
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
		opacity: 0.3;
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
		opacity: 0.1;
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
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(26, 13, 46, 0.8));
		border-bottom: 2px solid #00ffff;
		backdrop-filter: blur(20px);
		z-index: 10;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 2rem;
		position: relative;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.neural-logo {
		position: relative;
		width: 60px;
		height: 60px;
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
		border: 2px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: ringRotate 8s linear infinite;
	}

	.ring-outer {
		width: 60px;
		height: 60px;
		border-color: #00ffff;
		opacity: 0.8;
	}

	.ring-middle {
		width: 45px;
		height: 45px;
		border-color: #ff00ff;
		opacity: 0.6;
		animation-direction: reverse;
		animation-duration: 6s;
	}

	.ring-inner {
		width: 30px;
		height: 30px;
		border-color: #0096ff;
		animation-duration: 4s;
	}

	.logo-center {
		font-size: 1.5rem;
		color: #00ffff;
		text-shadow: 0 0 20px #00ffff;
		z-index: 3;
		position: relative;
		animation: corePulse 3s ease-in-out infinite;
	}

	.system-title h1 {
		font-size: 1.5rem;
		font-weight: 700;
		color: #fff;
		margin: 0;
		text-shadow: 0 0 20px #00ffff;
		letter-spacing: 0.2em;
	}

	.system-title p {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		margin: 0;
		letter-spacing: 0.15em;
	}

	.header-right {
		display: flex;
		align-items: center;
	}

	.time-display {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.03));
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 8px;
		padding: 1rem;
		backdrop-filter: blur(10px);
		text-align: center;
	}

	.time-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		margin-bottom: 0.3rem;
	}

	.time-value {
		font-size: 0.9rem;
		font-weight: 600;
		color: #00ffff;
		text-shadow: 0 0 8px #00ffff;
	}

	.top-navigation {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(26, 13, 46, 0.6));
		border-bottom: 1px solid rgba(0, 255, 255, 0.2);
		backdrop-filter: blur(20px);
		z-index: 10;
		display: flex;
		padding: 0.5rem 2rem;
		gap: 0.5rem;
		overflow-x: auto;
		scrollbar-width: none;
		-ms-overflow-style: none;
	}

	.top-navigation::-webkit-scrollbar {
		display: none;
	}

	.cyber-tab {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6) 0%, rgba(255, 255, 255, 0.03) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 6px;
		padding: 0.8rem 1.2rem;
		color: #ffffff;
		font-family: inherit;
		font-size: 0.7rem;
		font-weight: 500;
		cursor: pointer;
		position: relative;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		white-space: nowrap;
		backdrop-filter: blur(10px);
		overflow: hidden;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		animation: tabEntrance 0.5s ease-out;
		animation-delay: var(--delay);
		animation-fill-mode: both;
		opacity: 0;
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
		transform: translateY(-2px);
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
	}

	.cyber-tab.active {
		border-color: var(--tab-color);
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9) 0%, rgba(255, 255, 255, 0.08) 100%);
		box-shadow: 0 0 20px var(--tab-color);
	}

	.tab-icon {
		font-size: 1rem;
		color: var(--tab-color);
		text-shadow: 0 0 10px var(--tab-color);
	}

	.tab-name {
		position: relative;
		z-index: 2;
		letter-spacing: 0.02em;
		text-transform: uppercase;
	}

	.cyber-tab.active .tab-name {
		color: var(--tab-color);
		text-shadow: 0 0 8px var(--tab-color);
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
		border-radius: 6px;
	}

	.cyber-tab:hover .tab-glow,
	.cyber-tab.active .tab-glow {
		opacity: 0.1;
	}

	.data-viewport {
		flex: 1;
		position: relative;
		z-index: 5;
		padding: 1rem;
		overflow: hidden;
	}

	.viewport-frame {
		position: relative;
		width: 100%;
		height: 100%;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.4) 0%, 
			rgba(0, 255, 255, 0.02) 50%,
			rgba(255, 0, 255, 0.02) 100%);
		border: 2px solid #00ffff;
		border-radius: 16px;
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
		width: 30px;
		height: 30px;
		border: 3px solid #00ffff;
	}

	.corner.tl {
		top: 15px;
		left: 15px;
		border-right: none;
		border-bottom: none;
		border-top-left-radius: 8px;
	}

	.corner.tr {
		top: 15px;
		right: 15px;
		border-left: none;
		border-bottom: none;
		border-top-right-radius: 8px;
	}

	.corner.bl {
		bottom: 15px;
		left: 15px;
		border-right: none;
		border-top: none;
		border-bottom-left-radius: 8px;
	}

	.corner.br {
		bottom: 15px;
		right: 15px;
		border-left: none;
		border-top: none;
		border-bottom-right-radius: 8px;
	}

	.content-stream {
		position: relative;
		z-index: 2;
		width: 100%;
		height: 100%;
		padding: 2rem;
		overflow-y: auto;
	}

	:global(::-webkit-scrollbar) {
		width: 8px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 4px;
	}

	:global(::-webkit-scrollbar-thumb) {
		background: linear-gradient(135deg, #00ffff, #ff00ff);
		border-radius: 4px;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, #ff00ff, #00ffff);
	}

	@keyframes ringRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes corePulse {
		0%, 100% { 
			opacity: 0.9; 
			transform: scale(1);
			text-shadow: 0 0 20px #00ffff;
		}
		50% { 
			opacity: 1; 
			transform: scale(1.05);
			text-shadow: 0 0 30px #00ffff;
		}
	}

	@keyframes tabEntrance {
		0% { 
			opacity: 0; 
			transform: translateY(-10px);
		}
		100% { 
			opacity: 1; 
			transform: translateY(0);
		}
	}

	@media (max-width: 1200px) {
		.cyber-header {
			flex-direction: column;
			gap: 1rem;
			padding: 1rem;
		}
	}

	@media (max-width: 768px) {
		.system-title {
			text-align: center;
		}

		.top-navigation {
			padding: 0.5rem 1rem;
		}

		.cyber-tab {
			padding: 0.6rem 1rem;
			font-size: 0.65rem;
		}

		.data-viewport {
			padding: 0.5rem;
		}

		.content-stream {
			padding: 1rem;
		}
	}
</style>