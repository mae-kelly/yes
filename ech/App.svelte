<!-- App.svelte - Enhanced Dashboard -->
<script>
	import { onMount, onDestroy } from 'svelte';
	import SourceTables from './SourceTables.svelte';
	import RegionMetrics from './RegionMetrics.svelte';
	import CountryMetrics from './CountryMetrics.svelte';
	import DataCenter from './DataCenter.svelte';
	import BusinessUnitMetrics from './BusinessUnitMetrics.svelte';
	import CIOMetrics from './CIOMetrics.svelte';

	let currentView = 'source_tables';
	
	let modules = [
		{ id: 'source_tables', name: 'SOURCE TABLES', status: 'ACTIVE' },
		{ id: 'region_metrics', name: 'REGIONS', status: 'ACTIVE' },
		{ id: 'country_metrics', name: 'COUNTRIES', status: 'ACTIVE' },
		{ id: 'data_center', name: 'DATA CENTERS', status: 'MONITORING' },
		{ id: 'business_units', name: 'DIVISIONS', status: 'ACTIVE' },
		{ id: 'cio_metrics', name: 'CIOS', status: 'ACTIVE' }
	];

	function switchView(moduleId) {
		currentView = moduleId;
	}

	function getCurrentTitle() {
		const module = modules.find(m => m.id === currentView);
		return module ? module.name : 'SOURCE TABLES';
	}
</script>

<main class="dashboard-interface">
	<!-- Header -->
	<header class="dashboard-header">
		<div class="header-container">
			<!-- Logo and Title Section -->
			<div class="brand-section">
				<div class="logo-container">
					<svg class="eye-logo" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M24 8C13 8 3.73 15.55 1 26c2.73 10.45 12 18 23 18s20.27-7.55 23-18c-2.73-10.45-12-18-23-18z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
						<circle cx="24" cy="26" r="8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
						<circle cx="24" cy="26" r="3" fill="currentColor"/>
					</svg>
				</div>
				<div class="brand-info">
					<h1 class="system-title">LOG LENS</h1>
					<p class="system-subtitle">{getCurrentTitle()}</p>
				</div>
			</div>

			<!-- Navigation -->
			<nav class="nav-container">
				{#each modules as module}
					<button 
						class="nav-module {currentView === module.id ? 'active' : ''}"
						on:click={() => switchView(module.id)}>
						<span class="module-name">{module.name}</span>
						{#if currentView === module.id}
							<div class="active-indicator"></div>
						{/if}
					</button>
				{/each}
			</nav>
		</div>
	</header>

	<!-- Main Content -->
	<section class="viewport">
		<div class="content-wrapper">
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
		font-family: 'JetBrains Mono', 'Courier New', monospace;
		background: #0a0a0a;
		color: #e0e0e0;
		overflow: hidden;
		margin: 0;
		padding: 0;
		font-size: 14px;
		line-height: 1.5;
	}

	:global(*) {
		box-sizing: border-box;
	}

	:global(::-webkit-scrollbar) {
		width: 8px;
		height: 8px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.3);
	}

	:global(::-webkit-scrollbar-thumb) {
		background: #0a4f3c;
		border-radius: 4px;
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: #0d6b4f;
	}

	.dashboard-interface {
		width: 100vw;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: #0a0a0a;
		overflow: hidden;
	}

	.dashboard-header {
		background: linear-gradient(180deg, #0f0f0f 0%, #0a0a0a 100%);
		border-bottom: 1px solid #0a4f3c;
		padding: 1rem 1.5rem;
		flex-shrink: 0;
	}

	.header-container {
		display: flex;
		align-items: center;
		justify-content: space-between;
		max-width: 100%;
	}

	.brand-section {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.logo-container {
		width: 48px;
		height: 48px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.eye-logo {
		width: 100%;
		height: 100%;
		color: #0a4f3c;
		filter: drop-shadow(0 0 10px rgba(10, 79, 60, 0.4));
	}

	.brand-info h1 {
		margin: 0;
		font-size: 1.4rem;
		color: #0a4f3c;
		letter-spacing: 0.1em;
		font-weight: 600;
	}

	.system-subtitle {
		margin: 0.2rem 0 0 0;
		font-size: 0.8rem;
		color: #b8a678;
		text-transform: uppercase;
		letter-spacing: 0.15em;
		font-weight: 400;
	}

	.nav-container {
		display: flex;
		gap: 0.5rem;
		background: rgba(0, 0, 0, 0.4);
		padding: 0.4rem;
		border: 1px solid rgba(10, 79, 60, 0.2);
		border-radius: 6px;
	}

	.nav-module {
		position: relative;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid transparent;
		border-radius: 4px;
		padding: 0.6rem 1.2rem;
		color: #b8a678;
		cursor: pointer;
		transition: all 0.2s ease;
		font-size: 0.75rem;
		font-weight: 500;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		min-width: 110px;
		text-align: center;
	}

	.nav-module:hover {
		background: rgba(10, 79, 60, 0.1);
		border-color: #0a4f3c;
		color: #e0e0e0;
	}

	.nav-module.active {
		background: rgba(10, 79, 60, 0.15);
		border-color: #0a4f3c;
		color: #ffffff;
	}

	.module-name {
		position: relative;
		z-index: 1;
	}

	.active-indicator {
		position: absolute;
		bottom: 0;
		left: 20%;
		right: 20%;
		height: 2px;
		background: #0a4f3c;
		border-radius: 1px;
	}

	.viewport {
		flex: 1;
		position: relative;
		overflow: hidden;
		display: flex;
		background: #0a0a0a;
	}

	.content-wrapper {
		width: 100%;
		height: 100%;
		position: relative;
		overflow: hidden;
	}

	@media (max-width: 1400px) {
		.nav-module {
			min-width: 100px;
			padding: 0.5rem 1rem;
			font-size: 0.7rem;
		}
	}

	@media (max-width: 1200px) {
		.dashboard-header {
			padding: 0.8rem 1rem;
		}
		
		.nav-module {
			min-width: 90px;
			padding: 0.45rem 0.8rem;
			font-size: 0.65rem;
		}
	}
</style>