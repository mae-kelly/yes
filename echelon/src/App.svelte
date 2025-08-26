<script>
	import { onMount } from 'svelte';
	import SourceTables from './components/SourceTables.svelte';
	import DomainMetrics from './components/DomainMetrics.svelte';
	import InfrastructureType from './components/InfrastructureType.svelte';
	import RegionMetrics from './components/RegionMetrics.svelte';
	import CountryMetrics from './components/CountryMetrics.svelte';
	import DataCenterMetrics from './components/DataCenterMetrics.svelte';
	import CloudRegionMetrics from './components/CloudRegionMetrics.svelte';
	import ClassMetrics from './components/ClassMetrics.svelte';
	import SystemClassification from './components/SystemClassification.svelte';
	import BusinessUnitMetrics from './components/BusinessUnitMetrics.svelte';
	import CioMetrics from './components/CioMetrics.svelte';
	import TaniumCoverage from './components/TaniumCoverage.svelte';
	import CmdbPresence from './components/CmdbPresence.svelte';
	import MatrixBackground from './components/MatrixBackground.svelte';

	let currentView = 'source_tables';

	const menuItems = [
		{ id: 'source_tables', label: 'SOURCE TABLES ANALYSIS', icon: '◈' },
		{ id: 'domain_metrics', label: '1DC vs FEAD DOMAINS', icon: '◆' },
		{ id: 'infrastructure_type', label: 'INFRASTRUCTURE TYPES', icon: '⬢' },
		{ id: 'region_metrics', label: 'REGIONAL DISTRIBUTION', icon: '◉' },
		{ id: 'country_metrics', label: 'COUNTRY ANALYSIS', icon: '⬟' },
		{ id: 'data_center', label: 'DATA CENTER MAPPING', icon: '⬡' },
		{ id: 'cloud_region', label: 'CLOUD REGIONS', icon: '◯' },
		{ id: 'class_metrics', label: 'CLASS ANALYSIS', icon: '◐' },
		{ id: 'system_classification', label: 'SYSTEM TAXONOMY', icon: '◑' },
		{ id: 'business_unit', label: 'BUSINESS UNITS', icon: '◒' },
		{ id: 'cio_metrics', label: 'CIO ANALYSIS', icon: '◓' },
		{ id: 'tanium_coverage', label: 'TANIUM COVERAGE', icon: '⬠' },
		{ id: 'cmdb_presence', label: 'CMDB PRESENCE', icon: '⬢' }
	];

	onMount(() => {
		const canvas = document.getElementById('matrix-canvas');
		if (canvas) {
			canvas.width = window.innerWidth;
			canvas.height = window.innerHeight;
		}
	});
</script>

<main class="ao1-terminal">
	<MatrixBackground />
	
	<div class="dashboard-container">
		<header class="ao1-header">
			<div class="header-left">
				<div class="ao1-brand">
					<span class="brand-icon">◈</span>
					<div class="brand-text">
						<span class="main-title">AO1 LOG VISIBILITY</span>
						<span class="sub-title">NEURAL THREAT INTELLIGENCE</span>
					</div>
				</div>
			</div>
			<div class="header-right">
				<div class="classification-banner">CLASSIFICATION: TOP SECRET</div>
				<div class="timestamp">NEURAL LINK ACTIVE // {new Date().toISOString().slice(0, 19)}Z</div>
			</div>
		</header>

		<nav class="ao1-nav">
			{#each menuItems as item}
				<button 
					class="nav-item {currentView === item.id ? 'active' : ''}"
					on:click={() => currentView = item.id}
				>
					<span class="nav-icon">{item.icon}</span>
					<span class="nav-label">{item.label}</span>
				</button>
			{/each}
		</nav>

		<main class="ao1-main">
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
		</main>
	</div>
</main>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: 'Courier New', monospace;
		background: #000;
		color: #00ff41;
		overflow: hidden;
	}

	.ao1-terminal {
		width: 100vw;
		height: 100vh;
		position: relative;
		background: radial-gradient(ellipse at center, #001100 0%, #000000 100%);
	}

	.dashboard-container {
		position: relative;
		z-index: 10;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.1);
	}

	.ao1-header {
		background: linear-gradient(135deg, rgba(0, 26, 0, 0.95), rgba(0, 13, 0, 0.85));
		border-bottom: 2px solid #00ff41;
		padding: 15px 25px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		backdrop-filter: blur(20px);
		box-shadow: 0 0 20px rgba(0, 255, 65, 0.3);
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 40px;
	}

	.ao1-brand {
		display: flex;
		align-items: center;
		gap: 15px;
	}

	.brand-icon {
		font-size: 28px;
		animation: brand-pulse 3s infinite;
	}

	@keyframes brand-pulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.1); }
	}

	.brand-text {
		display: flex;
		flex-direction: column;
	}

	.main-title {
		font-size: 20px;
		font-weight: bold;
		letter-spacing: 2px;
	}

	.sub-title {
		font-size: 11px;
		color: #66ff66;
		opacity: 0.8;
	}

	.header-right {
		text-align: right;
		font-size: 11px;
	}

	.classification-banner {
		color: #ff6600;
		font-weight: bold;
		margin-bottom: 3px;
		animation: classify-blink 2s infinite;
	}

	@keyframes classify-blink {
		0%, 50% { opacity: 1; }
		51%, 100% { opacity: 0.7; }
	}

	.timestamp {
		color: #66ff66;
		opacity: 0.8;
	}

	.ao1-nav {
		background: rgba(0, 0, 0, 0.9);
		border-bottom: 1px solid #004400;
		padding: 12px 25px;
		display: flex;
		gap: 8px;
		overflow-x: auto;
		backdrop-filter: blur(10px);
	}

	.nav-item {
		background: transparent;
		border: 1px solid #004400;
		color: #00ff41;
		padding: 12px 16px;
		font-family: inherit;
		font-size: 10px;
		cursor: pointer;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
		white-space: nowrap;
		border-radius: 6px;
		transition: all 0.3s ease;
		min-width: 120px;
		position: relative;
	}

	.nav-item:hover,
	.nav-item.active {
		background: linear-gradient(135deg, rgba(0, 255, 65, 0.2), rgba(0, 255, 65, 0.1));
		border-color: #00ff41;
		box-shadow: 0 0 15px rgba(0, 255, 65, 0.4);
		transform: translateY(-2px);
	}

	.nav-icon {
		font-size: 16px;
	}

	.nav-label {
		font-weight: bold;
		letter-spacing: 1px;
		text-align: center;
	}

	.ao1-main {
		flex: 1;
		padding: 25px;
		overflow-y: auto;
		background: rgba(0, 0, 0, 0.2);
	}

	:global(::-webkit-scrollbar) {
		width: 10px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.5);
	}

	:global(::-webkit-scrollbar-thumb) {
		background: linear-gradient(135deg, #004400, #00ff41);
		border-radius: 5px;
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, #00ff41, #66ff66);
	}
</style>