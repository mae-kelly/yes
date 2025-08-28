<!-- App.svelte - Military Intelligence Dashboard -->
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
		{ id: 'source_tables', name: 'TABLES', status: 'ACTIVE' },
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
		return module ? module.name : 'TABLES';
	}
</script>

<main class="military-interface">
	<!-- Military Header -->
	<header class="military-header">
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

			<!-- Navigation Modules -->
			<nav class="military-nav">
				<div class="nav-container">
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
				</div>
			</nav>
		</div>
	</header>

	<!-- Main Content -->
	<section class="military-viewport">
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
		font-family: 'JetBrains Mono', 'Courier New', monospace;
		background: #000;
		color: #fff;
		overflow: hidden;
		margin: 0;
		padding: 0;
		font-size: 13px;
		line-height: 1.4;
	}

	.military-interface {
		width: 100vw;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: #000;
		overflow: hidden;
	}

	/* Military Header */
	.military-header {
		background: rgba(0, 0, 0, 0.95);
		border-bottom: 2px solid #0a4f3c; /* Deep emerald green */
		padding: 0.75rem 1rem;
		flex-shrink: 0;
	}

	.header-container {
		display: flex;
		align-items: center;
		justify-content: space-between;
		max-width: 100%;
	}

	/* Brand Section */
	.brand-section {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.logo-container {
		width: 42px;
		height: 42px;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}

	.eye-logo {
		width: 100%;
		height: 100%;
		color: #0a4f3c;
		filter: drop-shadow(0 0 8px rgba(10, 79, 60, 0.5));
		animation: eyePulse 4s ease-in-out infinite;
	}

	@keyframes eyePulse {
		0%, 100% { 
			opacity: 0.9;
			filter: drop-shadow(0 0 8px rgba(10, 79, 60, 0.5));
		}
		50% { 
			opacity: 1;
			filter: drop-shadow(0 0 12px rgba(10, 79, 60, 0.8));
		}
	}

	.brand-info h1 {
		margin: 0;
		font-size: 1.1rem;
		color: #0a4f3c;
		text-shadow: 0 0 8px rgba(10, 79, 60, 0.4);
		letter-spacing: 0.15em;
		font-weight: 700;
	}

	.system-subtitle {
		margin: 0.1rem 0 0 0;
		font-size: 0.7rem;
		color: #1e3a5f; /* Navy */
		text-transform: uppercase;
		letter-spacing: 0.2em;
		font-weight: 500;
	}

	/* Navigation */
	.military-nav {
		display: flex;
		align-items: center;
	}

	.nav-container {
		display: flex;
		gap: 0.5rem;
		background: rgba(0, 0, 0, 0.5);
		padding: 0.3rem;
		border: 1px solid rgba(10, 79, 60, 0.2);
		border-radius: 4px;
	}

	.nav-module {
		position: relative;
		background: rgba(0, 0, 0, 0.7);
		border: 1px solid rgba(30, 58, 95, 0.3); /* Navy border */
		border-radius: 3px;
		padding: 0.4rem 0.8rem;
		color: #b8a678; /* Beige */
		cursor: pointer;
		transition: all 0.2s ease;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		min-width: 90px;
		text-align: center;
	}

	.nav-module:hover {
		background: rgba(10, 79, 60, 0.1);
		border-color: #0a4f3c;
		color: #fff;
	}

	.nav-module.active {
		background: linear-gradient(135deg, 
			rgba(10, 79, 60, 0.2),
			rgba(30, 58, 95, 0.15));
		border-color: #0a4f3c;
		color: #fff;
		box-shadow: 
			0 2px 8px rgba(10, 79, 60, 0.2),
			inset 0 1px 0 rgba(255, 255, 255, 0.05);
	}

	.module-name {
		position: relative;
		z-index: 1;
	}

	.active-indicator {
		position: absolute;
		bottom: -2px;
		left: 20%;
		right: 20%;
		height: 2px;
		background: #0a4f3c;
		box-shadow: 0 0 6px rgba(10, 79, 60, 0.6);
		border-radius: 1px;
	}

	/* Main Viewport */
	.military-viewport {
		flex: 1;
		position: relative;
		overflow: hidden;
		display: flex;
		background: #000;
	}

	.content-container {
		width: 100%;
		height: 100%;
		position: relative;
		overflow: hidden;
	}

	/* Responsive Design */
	@media (max-width: 1400px) {
		.nav-module {
			min-width: 80px;
			padding: 0.35rem 0.6rem;
			font-size: 0.6rem;
		}
		
		.brand-info h1 {
			font-size: 1rem;
		}
		
		.system-subtitle {
			font-size: 0.65rem;
		}
	}

	@media (max-width: 1200px) {
		.military-header {
			padding: 0.6rem 0.8rem;
		}
		
		.nav-module {
			min-width: 70px;
			padding: 0.3rem 0.5rem;
			font-size: 0.55rem;
		}
		
		.logo-container {
			width: 36px;
			height: 36px;
		}
	}

	@media (max-width: 768px) {
		.nav-container {
			gap: 0.3rem;
		}
		
		.nav-module {
			min-width: 60px;
			padding: 0.25rem 0.4rem;
			font-size: 0.5rem;
			letter-spacing: 0.05em;
		}
		
		.brand-info h1 {
			font-size: 0.9rem;
		}
		
		.system-subtitle {
			font-size: 0.6rem;
		}
	}
</style>