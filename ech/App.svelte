<!-- App.svelte - Ultra Premium Command Center -->
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

	function getCurrentModule() {
		return modules.find(m => m.id === currentView) || modules[0];
	}

	// Update time every second
	const interval = setInterval(() => {
		time = new Date().toLocaleTimeString('en-US', { hour12: false });
	}, 1000);

	onDestroy(() => {
		clearInterval(interval);
	});

	// Animation states
	let scanPosition = 0;
	let pulseIntensity = 0;
	
	const scanInterval = setInterval(() => {
		scanPosition = (scanPosition + 0.5) % 100;
		pulseIntensity = Math.sin(Date.now() * 0.001) * 0.5 + 0.5;
	}, 50);

	onDestroy(() => {
		clearInterval(scanInterval);
	});
</script>

<main class="command-interface">
	<!-- Premium Header -->
	<header class="premium-header">
		<div class="header-container">
			<!-- Logo Section -->
			<div class="logo-section">
				<div class="logo-wrapper">
					<div class="logo-hex">
						<svg viewBox="0 0 80 80" class="logo-svg">
							<defs>
								<linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
									<stop offset="0%" style="stop-color:#00E5FF;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#7C4DFF;stop-opacity:1" />
								</linearGradient>
								<filter id="glow">
									<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
									<feMerge>
										<feMergeNode in="coloredBlur"/>
										<feMergeNode in="SourceGraphic"/>
									</feMerge>
								</filter>
							</defs>
							<polygon points="40,10 65,22.5 65,57.5 40,70 15,57.5 15,22.5" 
									fill="none" stroke="url(#logoGrad)" stroke-width="2" filter="url(#glow)"/>
							<text x="40" y="45" text-anchor="middle" fill="#00E5FF" font-size="20" font-weight="bold">LL</text>
						</svg>
					</div>
					<div class="logo-text">
						<h1>LOG LENS</h1>
						<span class="tagline">TACTICAL INTELLIGENCE</span>
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
							{#if currentView === module.id}
								<div class="module-indicator"></div>
							{/if}
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

		<!-- Scanning Line -->
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
	:global(body) {
		font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Inter', sans-serif;
		background: #000000;
		color: #ffffff;
		overflow: hidden;
		margin: 0;
		padding: 0;
		height: 100vh;
		width: 100vw;
	}

	.command-interface {
		width: 100vw;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, #000000 0%, #0a0a14 100%);
		position: relative;
		overflow: hidden;
	}

	/* Premium Header */
	.premium-header {
		background: rgba(0, 0, 0, 0.9);
		backdrop-filter: blur(20px);
		border-bottom: 1px solid rgba(0, 229, 255, 0.2);
		position: relative;
		z-index: 100;
		box-shadow: 0 4px 24px rgba(0, 0, 0, 0.8);
	}

	.header-container {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 2rem;
		height: 80px;
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
		width: 50px;
		height: 50px;
		position: relative;
	}

	.logo-svg {
		width: 100%;
		height: 100%;
		filter: drop-shadow(0 0 20px rgba(0, 229, 255, 0.5));
	}

	.logo-text h1 {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 700;
		background: linear-gradient(135deg, #00E5FF, #7C4DFF);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		letter-spacing: 0.1em;
	}

	.tagline {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.2em;
		font-weight: 500;
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
		background: rgba(255, 255, 255, 0.03);
		padding: 0.5rem;
		border-radius: 16px;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.nav-module {
		position: relative;
		padding: 0.75rem 1.5rem;
		background: transparent;
		border: none;
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.85rem;
		font-weight: 500;
		cursor: pointer;
		border-radius: 12px;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		display: flex;
		align-items: center;
		gap: 0.5rem;
		letter-spacing: 0.05em;
	}

	.module-icon {
		font-size: 1.1rem;
		filter: saturate(1.5);
	}

	.module-name {
		font-size: 0.75rem;
	}

	.nav-module:hover {
		background: rgba(0, 229, 255, 0.1);
		color: #00E5FF;
		transform: translateY(-1px);
	}

	.nav-module.active {
		background: rgba(0, 229, 255, 0.15);
		color: #00E5FF;
		box-shadow: 0 0 20px rgba(0, 229, 255, 0.3);
	}

	.module-indicator {
		position: absolute;
		bottom: 4px;
		left: 50%;
		transform: translateX(-50%);
		width: 30px;
		height: 2px;
		background: linear-gradient(90deg, transparent, #00E5FF, transparent);
		animation: indicatorPulse 2s ease-in-out infinite;
	}

	@keyframes indicatorPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	/* Status Section */
	.status-section {
		flex: 0 0 auto;
	}

	.status-grid {
		display: flex;
		gap: 2rem;
		align-items: center;
	}

	.status-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.status-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.1em;
		font-weight: 600;
	}

	.status-value {
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.8);
		font-weight: 500;
		font-family: 'SF Mono', 'Monaco', monospace;
	}

	.status-value.online {
		color: #00E5FF;
		text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
	}

	/* Scan Line */
	.scan-line {
		position: absolute;
		bottom: 0;
		height: 1px;
		width: 100px;
		background: linear-gradient(90deg, transparent, #00E5FF, transparent);
		transition: left 0.05s linear;
		pointer-events: none;
	}

	/* Content Viewport */
	.content-viewport {
		flex: 1;
		position: relative;
		overflow: hidden;
		background: radial-gradient(ellipse at center, rgba(0, 229, 255, 0.01) 0%, transparent 70%);
	}

	.content-container {
		width: 100%;
		height: 100%;
		padding: 1.5rem;
		overflow: hidden;
	}

	/* Responsive Design */
	@media (max-width: 1400px) {
		.nav-module {
			padding: 0.75rem 1rem;
		}
		
		.module-name {
			display: none;
		}
		
		.nav-modules {
			gap: 0.25rem;
		}
	}

	@media (max-width: 768px) {
		.header-container {
			padding: 0.75rem 1rem;
			height: 60px;
		}

		.logo-text h1 {
			font-size: 1.25rem;
		}

		.tagline {
			display: none;
		}

		.status-grid {
			gap: 1rem;
		}

		.content-container {
			padding: 1rem;
		}
	}
</style>