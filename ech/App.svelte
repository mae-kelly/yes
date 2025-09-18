<!-- App.svelte - Fixed Command Center -->
<script>
	import { onMount, onDestroy } from 'svelte';
	import SourceTables from './SourceTables.svelte';
	import RegionMetrics from './RegionMetrics.svelte';
	import CountryMetrics from './CountryMetrics.svelte';
	import DataCenter from './DataCenter.svelte';
	import BusinessUnitMetrics from './BusinessUnitMetrics.svelte';
	import CIOMetrics from './CIOMetrics.svelte';

	let currentView = 'source_tables';
	let time = new Date().toLocaleTimeString('en-US', { hour12: false });
	let date = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase();
	
	let modules = [
		{ id: 'source_tables', name: 'SOURCES', code: 'SRC', status: 'ACTIVE', icon: '◈' },
		{ id: 'region_metrics', name: 'REGIONS', code: 'REG', status: 'ACTIVE', icon: '🌍' },
		{ id: 'country_metrics', name: 'COUNTRIES', code: 'CTY', status: 'ACTIVE', icon: '🗺️' },
		{ id: 'data_center', name: 'DATA CENTERS', code: 'DC', status: 'MONITORING', icon: '🏢' },
		{ id: 'business_units', name: 'DIVISIONS', code: 'BU', status: 'ACTIVE', icon: '👥' },
		{ id: 'cio_metrics', name: 'EXECUTIVES', code: 'CIO', status: 'ACTIVE', icon: '👔' }
	];

	function switchView(moduleId) {
		currentView = moduleId;
	}

	// Update time every second
	let timeInterval;
	onMount(() => {
		timeInterval = setInterval(() => {
			time = new Date().toLocaleTimeString('en-US', { hour12: false });
		}, 1000);
	});

	onDestroy(() => {
		if (timeInterval) clearInterval(timeInterval);
	});

	// Subtle animation states
	let scanPosition = 0;
	let animationFrame;
	
	onMount(() => {
		const animate = () => {
			scanPosition = (scanPosition + 0.5) % 100;
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	});

	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});
</script>

<main class="command-interface">
	<!-- Clean Header -->
	<header class="header">
		<div class="header-container">
			<!-- Logo Section -->
			<div class="logo-section">
				<div class="logo-wrapper">
					<div class="logo-hex">
						<svg viewBox="0 0 80 80" class="logo-svg">
							<polygon points="40,10 65,22.5 65,57.5 40,70 15,57.5 15,22.5" 
									fill="none" stroke="#00E5FF" stroke-width="2"/>
							<text x="40" y="45" text-anchor="middle" fill="#00E5FF" font-size="16" font-weight="bold">LL</text>
						</svg>
					</div>
					<div class="logo-text">
						<h1>LOG LENS</h1>
						<span class="tagline">INFRASTRUCTURE ANALYTICS</span>
					</div>
				</div>
			</div>

			<!-- Navigation -->
			<nav class="nav-section">
				<div class="nav-modules">
					{#each modules as module}
						<button 
							class="nav-module {currentView === module.id ? 'active' : ''}"
							on:click={() => switchView(module.id)}>
							<span class="module-icon">{module.icon}</span>
							<span class="module-name">{module.name}</span>
						</button>
					{/each}
				</div>
			</nav>

			<!-- Status Section -->
			<div class="status-section">
				<div class="status-grid">
					<div class="status-item">
						<span class="status-label">TIME</span>
						<span class="status-value">{time}</span>
					</div>
					<div class="status-item">
						<span class="status-label">DATE</span>
						<span class="status-value">{date}</span>
					</div>
					<div class="status-item">
						<span class="status-label">STATUS</span>
						<span class="status-value online">ONLINE</span>
					</div>
				</div>
			</div>
		</div>

		<!-- Subtle Scanning Line -->
		<div class="scan-line" style="left: {scanPosition}%"></div>
	</header>

	<!-- Main Content Area -->
	<section class="content-viewport">
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
	:global(*) {
		margin: 0;
		padding: 0;
		box-sizing: border-box;
	}

	:global(body) {
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
		background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
		color: #ffffff;
		overflow: hidden;
		margin: 0;
		padding: 0;
		height: 100vh;
		width: 100vw;
		position: fixed;
	}

	:global(html) {
		overflow: hidden;
		height: 100%;
	}

	.command-interface {
		width: 100vw;
		height: 100vh;
		display: flex;
		flex-direction: column;
		position: fixed;
		top: 0;
		left: 0;
		overflow: hidden;
	}

	/* Clean Header */
	.header {
		background: rgba(0, 0, 0, 0.95);
		backdrop-filter: blur(10px);
		border-bottom: 1px solid rgba(0, 229, 255, 0.2);
		position: relative;
		z-index: 100;
		flex-shrink: 0;
		height: 80px;
	}

	.header-container {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 2rem;
		height: 100%;
		max-width: 1800px;
		margin: 0 auto;
	}

	/* Logo Section */
	.logo-section {
		flex: 0 0 auto;
	}

	.logo-wrapper {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.logo-hex {
		width: 40px;
		height: 40px;
	}

	.logo-svg {
		width: 100%;
		height: 100%;
	}

	.logo-text h1 {
		margin: 0;
		font-size: 1.3rem;
		font-weight: 600;
		color: #00E5FF;
		letter-spacing: 0.1em;
		line-height: 1;
	}

	.tagline {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.2em;
		font-weight: 400;
		line-height: 1;
	}

	/* Navigation Section */
	.nav-section {
		flex: 1;
		display: flex;
		justify-content: center;
		padding: 0 2rem;
	}

	.nav-modules {
		display: flex;
		gap: 0.5rem;
		background: rgba(255, 255, 255, 0.05);
		padding: 0.5rem;
		border-radius: 12px;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.nav-module {
		position: relative;
		padding: 0.7rem 1.2rem;
		background: transparent;
		border: none;
		color: rgba(255, 255, 255, 0.7);
		font-size: 0.8rem;
		font-weight: 500;
		cursor: pointer;
		border-radius: 8px;
		transition: all 0.2s ease;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		white-space: nowrap;
	}

	.module-icon {
		font-size: 1rem;
		line-height: 1;
	}

	.module-name {
		font-size: 0.75rem;
		line-height: 1;
	}

	.nav-module:hover {
		background: rgba(0, 229, 255, 0.1);
		color: #00E5FF;
	}

	.nav-module.active {
		background: rgba(0, 229, 255, 0.2);
		color: #00E5FF;
		box-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
	}

	/* Status Section */
	.status-section {
		flex: 0 0 auto;
	}

	.status-grid {
		display: flex;
		gap: 1.5rem;
		align-items: center;
	}

	.status-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		text-align: center;
	}

	.status-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		font-weight: 500;
		line-height: 1;
	}

	.status-value {
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.9);
		font-weight: 500;
		font-family: 'SF Mono', 'Monaco', monospace;
		line-height: 1;
	}

	.status-value.online {
		color: #00E5FF;
	}

	/* Subtle Scan Line */
	.scan-line {
		position: absolute;
		bottom: 0;
		height: 1px;
		width: 60px;
		background: linear-gradient(90deg, transparent, #00E5FF, transparent);
		transition: left 0.1s linear;
		pointer-events: none;
		opacity: 0.6;
	}

	/* Content Viewport */
	.content-viewport {
		flex: 1;
		position: relative;
		overflow: hidden;
		background: linear-gradient(135deg, rgba(0, 229, 255, 0.02) 0%, transparent 70%);
		min-height: 0;
	}

	.content-container {
		width: 100%;
		height: 100%;
		padding: 1.5rem;
		overflow: hidden;
		position: absolute;
		top: 0;
		left: 0;
		max-width: 1800px;
		margin: 0 auto;
		left: 50%;
		transform: translateX(-50%);
	}

	/* Responsive Design */
	@media (max-width: 1400px) {
		.nav-module {
			padding: 0.7rem 1rem;
		}
		
		.module-name {
			display: none;
		}
		
		.nav-modules {
			gap: 0.25rem;
		}
	}

	@media (max-width: 768px) {
		.header {
			height: 70px;
		}

		.header-container {
			padding: 0 1rem;
		}

		.logo-text h1 {
			font-size: 1.1rem;
		}

		.tagline {
			display: none;
		}

		.status-grid {
			gap: 1rem;
		}

		.nav-section {
			padding: 0 0.5rem;
		}

		.nav-modules {
			padding: 0.4rem;
		}

		.nav-module {
			padding: 0.6rem 0.8rem;
		}

		.content-container {
			padding: 1rem;
		}
	}

	/* Ensure no scrollbars */
	:global(body::-webkit-scrollbar) {
		display: none;
	}
</style>