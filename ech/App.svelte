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
		{ id: 'source_tables', name: 'Source Intelligence', icon: '◈', color: '#00ffff' },
		{ id: 'domain_metrics', name: '1DC vs FEAD', icon: '◆', color: '#ff00ff' },
		{ id: 'infrastructure_type', name: 'Infrastructure', icon: '⬢', color: '#0096ff' },
		{ id: 'region_metrics', name: 'Global Regions', icon: '◉', color: '#00ffff' },
		{ id: 'country_metrics', name: 'Country Analysis', icon: '⬟', color: '#ff00ff' },
		{ id: 'data_center', name: 'Data Centers', icon: '⬡', color: '#0096ff' },
		{ id: 'cloud_region', name: 'Cloud Regions', icon: '◯', color: '#00ffff' },
		{ id: 'class_metrics', name: 'Class Analysis', icon: '◐', color: '#ff00ff' },
		{ id: 'system_classification', name: 'System Types', icon: '◑', color: '#0096ff' },
		{ id: 'business_unit', name: 'Business Units', icon: '◒', color: '#00ffff' },
		{ id: 'cio_metrics', name: 'CIO Analysis', icon: '◓', color: '#ff00ff' },
		{ id: 'tanium_coverage', name: 'Tanium Coverage', icon: '⬠', color: '#0096ff' },
		{ id: 'cmdb_presence', name: 'CMDB Status', icon: '⬢', color: '#00ffff' }
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

<main class="dashboard">
	<header class="header">
		<div class="header-left">
			<div class="brand">
				<div class="brand-icon">
					<div class="icon-ring"></div>
					<span class="icon-center">◈</span>
				</div>
				<div class="brand-text">
					<h1 class="title">AO1 Log Visibility Dashboard</h1>
					<span class="subtitle">CSOC Infrastructure Monitoring</span>
				</div>
			</div>
			
			<nav class="navigation">
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
			</nav>
		</div>
		
		<div class="header-right">
			<div class="status-info">
				<div class="status-item">
					<span class="status-label">Status</span>
					<span class="status-value operational">{systemStatus}</span>
				</div>
				<div class="status-item">
					<span class="status-label">Time</span>
					<span class="status-value">{currentTime}</span>
				</div>
			</div>
		</div>
	</header>

	<section class="content">
		<div class="content-wrapper">
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
	</section>
</main>

<style>
	:global(body) {
		font-family: 'JetBrains Mono', monospace;
		background: #0a0a0a;
		color: #ffffff;
		overflow-x: hidden;
		margin: 0;
		padding: 0;
	}

	.dashboard {
		width: 100vw;
		min-height: 100vh;
		background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
		display: flex;
		flex-direction: column;
	}

	.header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9) 0%, rgba(26, 26, 46, 0.8) 100%);
		border-bottom: 1px solid rgba(0, 255, 255, 0.2);
		padding: 1rem 2rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		backdrop-filter: blur(20px);
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 2rem;
		flex: 1;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-shrink: 0;
	}

	.brand-icon {
		position: relative;
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.icon-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid rgba(0, 255, 255, 0.6);
		border-radius: 50%;
		animation: rotate 6s linear infinite;
	}

	.icon-center {
		color: #00ffff;
		font-size: 1.2rem;
		text-shadow: 0 0 10px #00ffff;
		position: relative;
		z-index: 2;
	}

	.brand-text {
		display: flex;
		flex-direction: column;
	}

	.title {
		font-size: 1.2rem;
		font-weight: 700;
		color: #ffffff;
		margin: 0;
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
	}

	.subtitle {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 400;
		margin-top: 0.2rem;
	}

	.navigation {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
		flex: 1;
		margin-left: 1rem;
	}

	.nav-tab {
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 6px;
		padding: 0.5rem 1rem;
		color: #ffffff;
		font-family: inherit;
		font-size: 0.75rem;
		font-weight: 500;
		cursor: pointer;
		position: relative;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		transition: all 0.3s ease;
		white-space: nowrap;
	}

	.nav-tab:hover {
		border-color: var(--module-color);
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.04) 100%);
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
	}

	.nav-tab.active {
		border-color: var(--module-color);
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
	}

	.tab-icon {
		font-size: 0.9rem;
		color: var(--module-color);
	}

	.tab-name {
		color: #ffffff;
		font-weight: 500;
		letter-spacing: 0.02em;
	}

	.header-right {
		display: flex;
		align-items: center;
		flex-shrink: 0;
	}

	.status-info {
		display: flex;
		gap: 1.5rem;
	}

	.status-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.2rem;
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

	.content {
		flex: 1;
		background: rgba(0, 0, 0, 0.3);
		position: relative;
	}

	.content-wrapper {
		width: 100%;
		height: 100%;
		padding: 1.5rem;
		overflow-y: auto;
	}

	:global(::-webkit-scrollbar) {
		width: 8px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.3);
	}

	:global(::-webkit-scrollbar-thumb) {
		background: linear-gradient(135deg, #00ffff, #ff00ff);
		border-radius: 4px;
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, #ff00ff, #00ffff);
	}

	@keyframes rotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@media (max-width: 1200px) {
		.navigation {
			flex-wrap: wrap;
		}
	}

	@media (max-width: 768px) {
		.header {
			flex-direction: column;
			gap: 1rem;
			padding: 1rem;
		}

		.header-left {
			flex-direction: column;
			width: 100%;
		}

		.navigation {
			justify-content: center;
			margin-left: 0;
		}

		.nav-tab {
			padding: 0.4rem 0.8rem;
			font-size: 0.7rem;
		}
	}

	@media (max-width: 480px) {
		.navigation {
			grid-template-columns: repeat(2, 1fr);
			display: grid;
			gap: 0.5rem;
			width: 100%;
		}

		.nav-tab {
			justify-content: center;
		}
	}
</style>