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
		{ id: 'source_tables', name: 'SOURCES', code: 'SRC' },
		{ id: 'region_metrics', name: 'REGIONS', code: 'REG' },
		{ id: 'country_metrics', name: 'COUNTRIES', code: 'CTY' },
		{ id: 'data_center', name: 'DATA CENTERS', code: 'DC' },
		{ id: 'business_units', name: 'DIVISIONS', code: 'BU' },
		{ id: 'cio_metrics', name: 'EXECUTIVES', code: 'CIO' }
	];

	function switchView(moduleId) {
		currentView = moduleId;
	}

	let timeInterval;
	onMount(() => {
		timeInterval = setInterval(() => {
			time = new Date().toLocaleTimeString('en-US', { hour12: false });
		}, 1000);
	});

	onDestroy(() => {
		if (timeInterval) clearInterval(timeInterval);
	});

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
	<header class="header">
		<div class="header-container">
			<div class="logo-section">
				<div class="logo-wrapper">
					<div class="logo-hex">
						<svg viewBox="0 0 80 80" class="logo-svg">
							<polygon points="40,10 65,22.5 65,57.5 40,70 15,57.5 15,22.5" 
									fill="none" stroke="#8DE5FF" stroke-width="2"/>
							<text x="40" y="45" text-anchor="middle" fill="#8DE5FF" font-size="16" font-weight="bold" font-family="JetBrains Mono">LL</text>
						</svg>
					</div>
					<div class="logo-text">
						<h1>LOG LENS</h1>
						<span class="tagline">INFRASTRUCTURE ANALYTICS</span>
					</div>
				</div>
			</div>

			<nav class="nav-section">
				<div class="nav-modules">
					{#each modules as module}
						<button 
							class="nav-module {currentView === module.id ? 'active' : ''}"
							on:click={() => switchView(module.id)}>
							<span class="module-code">{module.code}</span>
							<span class="module-name">{module.name}</span>
						</button>
					{/each}
				</div>
			</nav>

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

		<div class="scan-line" style="left: {scanPosition}%"></div>
	</header>

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
		font-family: 'JetBrains Mono', monospace;
	}

	:global(body) {
		background: #000000;
		color: #FFFFFF;
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
		background: #000000;
	}

	.header {
		background: #000000;
		border-bottom: 1px solid rgba(141, 229, 255, 0.2);
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
		color: #8DE5FF;
		letter-spacing: 0.1em;
		line-height: 1;
		font-family: 'JetBrains Mono', monospace;
	}

	.tagline {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.2em;
		font-weight: 400;
		line-height: 1;
		font-family: 'JetBrains Mono', monospace;
	}

	.nav-section {
		flex: 1;
		display: flex;
		justify-content: center;
		padding: 0 2rem;
	}

	.nav-modules {
		display: flex;
		gap: 0.5rem;
		background: rgba(141, 229, 255, 0.05);
		padding: 0.5rem;
		border-radius: 12px;
		border: 1px solid rgba(141, 229, 255, 0.1);
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
		font-family: 'JetBrains Mono', monospace;
	}

	.module-code {
		color: #FF8DFF;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.module-name {
		font-size: 0.75rem;
		line-height: 1;
	}

	.nav-module:hover {
		background: rgba(141, 229, 255, 0.1);
		color: #8DE5FF;
	}

	.nav-module.active {
		background: rgba(141, 229, 255, 0.2);
		color: #8DE5FF;
		box-shadow: 0 0 10px rgba(141, 229, 255, 0.3);
	}

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
		font-family: 'JetBrains Mono', monospace;
	}

	.status-value {
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.9);
		font-weight: 500;
		font-family: 'JetBrains Mono', monospace;
		line-height: 1;
	}

	.status-value.online {
		color: #8DE5FF;
	}

	.scan-line {
		position: absolute;
		bottom: 0;
		height: 1px;
		width: 60px;
		background: linear-gradient(90deg, transparent, #8DE5FF, transparent);
		transition: left 0.1s linear;
		pointer-events: none;
		opacity: 0.6;
	}

	.content-viewport {
		flex: 1;
		position: relative;
		overflow: hidden;
		background: #000000;
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

	:global(body::-webkit-scrollbar) {
		display: none;
	}
</style>