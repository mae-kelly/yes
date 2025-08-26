<!-- ech/App.svelte -->
<script>
	import { onMount } from 'svelte';
	import SourceTables from './SourceTables.svelte';
	import DomainMetrics from './DomainMetrics.svelte';
	import InfrastructureType from './InfrastructureType.svelte';
	import RegionMetrics from './RegionMetrics.svelte';
	import CountryMetrics from './CountryMetrics.svelte';
	import DataCenterMetrics from './DataCenterMetrics.svelte';
	import CloudRegionMetrics from './CloudRegionMetrics.svelte';
	import ClassMetrics from './ClassMetrics.svelte';
	import SystemClassification from './SystemClassification.svelte';
	import BusinessUnitMetrics from './BusinessUnitMetrics.svelte';
	import CioMetrics from './CioMetrics.svelte';
	import TaniumCoverage from './TaniumCoverage.svelte';
	import CmdbPresence from './CmdbPresence.svelte';

	let currentView = 'source_tables';
	let systemStatus = 'OPERATIONAL';

	let modules = [
		{ id: 'source_tables', name: 'Source Intelligence', color: '#00ffff' },
		{ id: 'domain_metrics', name: '1DC vs FEAD', color: '#ff00ff' },
		{ id: 'infrastructure_type', name: 'Infrastructure', color: '#0096ff' },
		{ id: 'region_metrics', name: 'Global Regions', color: '#00ffff' },
		{ id: 'country_metrics', name: 'Country Analysis', color: '#ff00ff' },
		{ id: 'data_center', name: 'Data Centers', color: '#0096ff' },
		{ id: 'cloud_region', name: 'Cloud Regions', color: '#00ffff' },
		{ id: 'class_metrics', name: 'Class Analysis', color: '#ff00ff' },
		{ id: 'system_classification', name: 'System Types', color: '#0096ff' },
		{ id: 'business_unit', name: 'Business Units', color: '#00ffff' },
		{ id: 'cio_metrics', name: 'CIO Analysis', color: '#ff00ff' },
		{ id: 'tanium_coverage', name: 'Tanium Coverage', color: '#0096ff' },
		{ id: 'cmdb_presence', name: 'CMDB Status', color: '#00ffff' }
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
	<div class="matrix-background"></div>
	<div class="floating-particles">
		{#each Array(20) as _, i}
			<div class="particle" style="left: {Math.random() * 100}%; animation-delay: {Math.random() * 5}s;"></div>
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
					<div class="logo-center">◈</div>
				</div>
				<div class="brand-text">
					<h1 class="title">AO1 Log Visibility Dashboard</h1>
					<span class="subtitle">CSOC Infrastructure Monitoring</span>
				</div>
			</div>
			
			<nav class="tab-navigation">
				{#each modules as module}
					<button 
						class="cyber-tab {currentView === module.id ? 'active' : ''}"
						style="--tab-color: {module.color}"
						on:click={() => switchView(module.id)}
					>
						<span class="tab-name">{module.name}</span>
						<div class="tab-glow"></div>
					</button>
				{/each}
			</nav>
			
			<div class="status-panel">
				<div class="status-ring"></div>
				<div class="status-info">
					<div class="status-item">
						<span class="status-label">STATUS</span>
						<span class="status-value operational">{systemStatus}</span>
					</div>
					<div class="status-item">
						<span class="status-label">TIME</span>
						<span class="status-value">{currentTime}</span>
					</div>
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
				{:else if currentView === 'cloud_region'}
					<CloudRegionMetrics />
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
		font-family: 'JetBrains Mono', monospace;
		background: radial-gradient(ellipse at center, #1a0d2e 0%, #0f0520 40%, #000000 100%);
		color: #ffffff;
		overflow: hidden;
		margin: 0;
		padding: 0;
		font-weight: 400;
	}

	.cyberpunk-interface {
		width: 100vw;
		height: 100vh;
		position: relative;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.matrix-background {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: 
			radial-gradient(circle at 20% 30%, rgba(0, 255, 255, 0.1) 0%, transparent 50%),
			radial-gradient(circle at 80% 70%, rgba(255, 0, 255, 0.08) 0%, transparent 50%),
			radial-gradient(circle at 40% 80%, rgba(0, 150, 255, 0.06) 0%, transparent 50%);
		pointer-events: none;
		z-index: 1;
		animation: ambientPulse 8s ease-in-out infinite alternate;
	}

	.floating-particles {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 2;
	}

	.particle {
		position: absolute;
		width: 2px;
		height: 2px;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.8), transparent);
		border-radius: 50%;
		animation: floatUp 6s linear infinite;
	}

	.cyber-header {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.9) 0%, 
			rgba(26, 13, 46, 0.8) 50%,
			rgba(0, 0, 0, 0.9) 100%);
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		backdrop-filter: blur(20px);
		z-index: 10;
		position: relative;
		box-shadow: 0 4px 32px rgba(0, 255, 255, 0.1);
	}

	.header-content {
		display: flex;
		align-items: center;
		padding: 1rem 2rem;
		gap: 2rem;
		min-height: 80px;
	}

	.brand-section {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-shrink: 0;
	}

	.neural-logo {
		position: relative;
		width: 50px;
		height: 50px;
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
		width: 50px;
		height: 50px;
		border-color: rgba(0, 255, 255, 0.6);
	}

	.ring-middle {
		width: 35px;
		height: 35px;
		border-color: rgba(255, 0, 255, 0.4);
		animation-direction: reverse;
		animation-duration: 6s;
	}

	.ring-inner {
		width: 20px;
		height: 20px;
		border-color: rgba(0, 150, 255, 0.8);
		animation-duration: 4s;
	}

	.logo-center {
		font-size: 1.5rem;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
		z-index: 3;
		position: relative;
		animation: corePulse 3s ease-in-out infinite;
	}

	.brand-text {
		display: flex;
		flex-direction: column;
	}

	.title {
		font-size: 1.3rem;
		font-weight: 700;
		color: #ffffff;
		margin: 0;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.02em;
	}

	.subtitle {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 300;
		margin-top: 0.2rem;
	}

	.tab-navigation {
		display: flex;
		flex: 1;
		gap: 0.3rem;
		overflow-x: auto;
		padding: 0.5rem 0;
		scrollbar-width: none;
		-ms-overflow-style: none;
	}

	.tab-navigation::-webkit-scrollbar {
		display: none;
	}

	.cyber-tab {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6) 0%, rgba(255, 255, 255, 0.03) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 6px;
		padding: 0.6rem 1rem;
		color: #ffffff;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.7rem;
		font-weight: 500;
		cursor: pointer;
		position: relative;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		white-space: nowrap;
		backdrop-filter: blur(10px);
		overflow: hidden;
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
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
	}

	.cyber-tab.active {
		border-color: var(--tab-color);
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9) 0%, rgba(255, 255, 255, 0.08) 100%);
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
	}

	.tab-name {
		position: relative;
		z-index: 2;
		letter-spacing: 0.02em;
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
		opacity: 0.05;
	}

	.status-panel {
		position: relative;
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-shrink: 0;
	}

	.status-ring {
		width: 12px;
		height: 12px;
		border: 2px solid rgba(0, 255, 133, 0.8);
		border-radius: 50%;
		animation: statusPulse 2s ease-in-out infinite;
		box-shadow: 0 0 10px rgba(0, 255, 133, 0.5);
	}

	.status-info {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.status-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.status-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 400;
		text-transform: uppercase;
	}

	.status-value {
		font-size: 0.7rem;
		font-weight: 600;
		color: #ffffff;
	}

	.status-value.operational {
		color: #00ff85;
		text-shadow: 0 0 8px rgba(0, 255, 133, 0.5);
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
		border: 1px solid rgba(0, 255, 255, 0.2);
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
		background: linear-gradient(135deg, 
			rgba(0, 255, 255, 0.6), 
			rgba(255, 0, 255, 0.4));
		border-radius: 4px;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, 
			rgba(0, 255, 255, 0.8), 
			rgba(255, 0, 255, 0.6));
	}

	@keyframes ambientPulse {
		0% { opacity: 0.3; }
		100% { opacity: 0.7; }
	}

	@keyframes floatUp {
		0% { 
			transform: translateY(100vh) translateX(0);
			opacity: 0;
		}
		10% { opacity: 1; }
		90% { opacity: 1; }
		100% { 
			transform: translateY(-10vh) translateX(50px);
			opacity: 0;
		}
	}

	@keyframes ringRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes corePulse {
		0%, 100% { 
			opacity: 0.9; 
			transform: scale(1);
			text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
		}
		50% { 
			opacity: 1; 
			transform: scale(1.05);
			text-shadow: 0 0 30px rgba(0, 255, 255, 1);
		}
	}

	@keyframes statusPulse {
		0%, 100% { 
			opacity: 1; 
			box-shadow: 0 0 10px rgba(0, 255, 133, 0.5);
		}
		50% { 
			opacity: 0.7; 
			box-shadow: 0 0 20px rgba(0, 255, 133, 0.8);
		}
	}

	@media (max-width: 1200px) {
		.header-content {
			flex-wrap: wrap;
			padding: 1rem;
		}

		.tab-navigation {
			order: 3;
			width: 100%;
			margin-top: 0.5rem;
		}
	}

	@media (max-width: 768px) {
		.brand-section {
			flex-direction: column;
			text-align: center;
			gap: 0.5rem;
		}

		.cyber-tab {
			padding: 0.5rem 0.8rem;
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