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
	let time = new Date().toLocaleTimeString('en-US', { hour12: false });
	let date = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase();
	
	let modules = [
		{ id: 'source_tables', name: 'SOURCE TABLES', code: 'SRC-TBL', status: 'ACTIVE' },
		{ id: 'region_metrics', name: 'REGIONS', code: 'REG-MET', status: 'ACTIVE' },
		{ id: 'country_metrics', name: 'COUNTRIES', code: 'CTY-MET', status: 'ACTIVE' },
		{ id: 'data_center', name: 'DATA CENTERS', code: 'DC-FAC', status: 'MONITORING' },
		{ id: 'business_units', name: 'DIVISIONS', code: 'BU-DIV', status: 'ACTIVE' },
		{ id: 'cio_metrics', name: 'EXECUTIVES', code: 'CIO-EX', status: 'ACTIVE' }
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

	// Animated scan line effect
	let scanPosition = 0;
	const scanInterval = setInterval(() => {
		scanPosition = (scanPosition + 1) % 100;
	}, 50);

	onDestroy(() => {
		clearInterval(scanInterval);
	});
</script>

<main class="command-interface">
	<!-- Advanced Header -->
	<header class="tactical-header">
		<div class="header-grid">
			<!-- Left Section: Logo and System Info -->
			<div class="system-section">
				<div class="quantum-logo">
					<svg viewBox="0 0 80 80" class="logo-main">
						<!-- Outer Ring -->
						<circle cx="40" cy="40" r="38" fill="none" stroke="url(#techGradient)" stroke-width="1" opacity="0.5"/>
						<circle cx="40" cy="40" r="35" fill="none" stroke="url(#techGradient)" stroke-width="0.5" stroke-dasharray="5 3" class="rotate-slow"/>
						
						<!-- Middle Hexagon -->
						<polygon points="40,15 60,27.5 60,52.5 40,65 20,52.5 20,27.5" fill="none" stroke="#0a4f3c" stroke-width="1.5"/>
						
						<!-- Inner Triangle -->
						<path d="M40,25 L50,45 L30,45 Z" fill="none" stroke="#0a4f3c" stroke-width="1" class="pulse"/>
						
						<!-- Center Core -->
						<circle cx="40" cy="40" r="8" fill="#0a0a0a" stroke="#0a4f3c" stroke-width="1"/>
						<circle cx="40" cy="40" r="3" fill="#0a4f3c" class="pulse-dot"/>
						
						<!-- Tech Lines -->
						<line x1="10" y1="40" x2="20" y2="40" stroke="#0a4f3c" stroke-width="0.5" opacity="0.6"/>
						<line x1="60" y1="40" x2="70" y2="40" stroke="#0a4f3c" stroke-width="0.5" opacity="0.6"/>
						<line x1="40" y1="10" x2="40" y2="20" stroke="#0a4f3c" stroke-width="0.5" opacity="0.6"/>
						<line x1="40" y1="60" x2="40" y2="70" stroke="#0a4f3c" stroke-width="0.5" opacity="0.6"/>
						
						<defs>
							<linearGradient id="techGradient" x1="0%" y1="0%" x2="100%" y2="100%">
								<stop offset="0%" style="stop-color:#0a4f3c;stop-opacity:1" />
								<stop offset="50%" style="stop-color:#0d6b4f;stop-opacity:1" />
								<stop offset="100%" style="stop-color:#0a4f3c;stop-opacity:1" />
							</linearGradient>
						</defs>
					</svg>
					<div class="scan-line" style="top: {scanPosition}%"></div>
				</div>
				
				<div class="system-info">
					<div class="system-title">LOG LENS</div>
					<div class="system-subtitle">TACTICAL RECONNAISSANCE SYSTEM</div>
					<div class="system-stats">
						<span class="stat-item">
							<span class="stat-label">MODULE:</span>
							<span class="stat-value">{getCurrentModule().name}</span>
						</span>
						<span class="stat-divider">|</span>
						<span class="stat-item">
							<span class="stat-label">CODE:</span>
							<span class="stat-value">{getCurrentModule().code}</span>
						</span>
					</div>
				</div>
			</div>

			<!-- Center Section: Navigation -->
			<nav class="nav-grid">
				{#each modules as module}
					<button 
						class="nav-cell {currentView === module.id ? 'active' : ''}"
						on:click={() => switchView(module.id)}>
						<div class="nav-content">
							<div class="nav-code">{module.code}</div>
							<div class="nav-name">{module.name}</div>
							{#if currentView === module.id}
								<div class="nav-active-bar"></div>
							{/if}
						</div>
					</button>
				{/each}
			</nav>

			<!-- Right Section: Status Panel -->
			<div class="status-section">
				<div class="status-grid">
					<div class="status-item">
						<span class="status-label">SYSTEM</span>
						<span class="status-value online">ONLINE</span>
					</div>
					<div class="status-item">
						<span class="status-label">THREAT</span>
						<span class="status-value nominal">NOMINAL</span>
					</div>
					<div class="status-item">
						<span class="status-label">TIME</span>
						<span class="status-value">{time}</span>
					</div>
					<div class="status-item">
						<span class="status-label">DATE</span>
						<span class="status-value">{date}</span>
					</div>
				</div>
				<div class="quantum-indicator">
					<svg viewBox="0 0 60 20" class="quantum-wave">
						<polyline points="0,10 5,5 10,15 15,8 20,12 25,3 30,17 35,10 40,10 45,5 50,15 55,10 60,10" 
								  fill="none" 
								  stroke="#0a4f3c" 
								  stroke-width="1"
								  class="wave-animation"/>
					</svg>
				</div>
			</div>
		</div>
		
		<!-- Bottom Status Bar -->
		<div class="header-status-bar">
			<div class="status-bar-content">
				<span class="bar-item">▶ SECURE CHANNEL ESTABLISHED</span>
				<span class="bar-item">◆ ENCRYPTION: AES-256</span>
				<span class="bar-item">▲ BANDWIDTH: 10GB/S</span>
				<span class="bar-item">● NODES: 1,337</span>
				<span class="bar-item">■ LATENCY: 0.3MS</span>
			</div>
			<div class="scan-overlay" style="left: {scanPosition}%"></div>
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
		background: #000000;
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

	.command-interface {
		width: 100vw;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: #000000;
		overflow: hidden;
	}

	.tactical-header {
		background: linear-gradient(180deg, #0a0a0a 0%, #000000 100%);
		border-bottom: 1px solid #0a4f3c;
		flex-shrink: 0;
		position: relative;
	}

	.header-grid {
		display: grid;
		grid-template-columns: 380px 1fr 320px;
		gap: 2rem;
		padding: 1rem 1.5rem;
		align-items: center;
	}

	.system-section {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.quantum-logo {
		width: 80px;
		height: 80px;
		position: relative;
		flex-shrink: 0;
	}

	.logo-main {
		width: 100%;
		height: 100%;
		filter: drop-shadow(0 0 20px rgba(10, 79, 60, 0.5));
	}

	.rotate-slow {
		animation: rotate 20s linear infinite;
		transform-origin: center;
	}

	.pulse {
		animation: pulse 2s ease-in-out infinite;
	}

	.pulse-dot {
		animation: pulseDot 1s ease-in-out infinite;
	}

	@keyframes rotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	@keyframes pulse {
		0%, 100% { opacity: 0.6; }
		50% { opacity: 1; }
	}

	@keyframes pulseDot {
		0%, 100% { r: 3; opacity: 1; }
		50% { r: 5; opacity: 0.6; }
	}

	.scan-line {
		position: absolute;
		left: 0;
		width: 100%;
		height: 1px;
		background: linear-gradient(90deg, transparent, #0a4f3c, transparent);
		opacity: 0.5;
		transition: top 0.05s linear;
	}

	.system-info {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.system-title {
		font-size: 1.8rem;
		font-weight: 700;
		color: #0a4f3c;
		letter-spacing: 0.15em;
		text-shadow: 0 0 20px rgba(10, 79, 60, 0.5);
	}

	.system-subtitle {
		font-size: 0.65rem;
		color: #666;
		letter-spacing: 0.3em;
		font-weight: 300;
	}

	.system-stats {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-top: 0.25rem;
	}

	.stat-item {
		display: flex;
		gap: 0.3rem;
		align-items: center;
	}

	.stat-label {
		font-size: 0.65rem;
		color: #666;
		font-weight: 400;
	}

	.stat-value {
		font-size: 0.75rem;
		color: #0a4f3c;
		font-weight: 600;
	}

	.stat-divider {
		color: #333;
		font-size: 0.8rem;
	}

	.nav-grid {
		display: grid;
		grid-template-columns: repeat(6, 1fr);
		gap: 0.5rem;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid #111;
		border-radius: 4px;
	}

	.nav-cell {
		position: relative;
		background: #000;
		border: 1px solid #111;
		padding: 0.75rem 0.5rem;
		cursor: pointer;
		transition: all 0.2s ease;
		overflow: hidden;
	}

	.nav-cell::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 1px;
		background: linear-gradient(90deg, transparent, #0a4f3c, transparent);
		opacity: 0;
		transition: opacity 0.3s ease;
	}

	.nav-cell:hover::before {
		opacity: 0.5;
	}

	.nav-cell:hover {
		background: rgba(10, 79, 60, 0.05);
		border-color: #0a4f3c;
	}

	.nav-cell.active {
		background: rgba(10, 79, 60, 0.1);
		border-color: #0a4f3c;
	}

	.nav-content {
		position: relative;
		text-align: center;
	}

	.nav-code {
		font-size: 0.6rem;
		color: #666;
		letter-spacing: 0.1em;
		margin-bottom: 0.2rem;
	}

	.nav-name {
		font-size: 0.7rem;
		color: #b8a678;
		font-weight: 500;
		letter-spacing: 0.05em;
	}

	.nav-cell.active .nav-name {
		color: #0a4f3c;
	}

	.nav-active-bar {
		position: absolute;
		bottom: 0;
		left: 10%;
		right: 10%;
		height: 2px;
		background: #0a4f3c;
		box-shadow: 0 0 10px rgba(10, 79, 60, 0.5);
	}

	.status-section {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.status-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.5rem;
	}

	.status-item {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.status-label {
		font-size: 0.6rem;
		color: #666;
		letter-spacing: 0.1em;
	}

	.status-value {
		font-size: 0.75rem;
		font-weight: 600;
		color: #b8a678;
	}

	.status-value.online {
		color: #0a4f3c;
	}

	.status-value.nominal {
		color: #0a4f3c;
	}

	.quantum-indicator {
		height: 20px;
		overflow: hidden;
		border: 1px solid #111;
		border-radius: 2px;
		background: #000;
		padding: 2px;
	}

	.quantum-wave {
		width: 100%;
		height: 100%;
	}

	.wave-animation {
		animation: waveMove 3s linear infinite;
	}

	@keyframes waveMove {
		0% { transform: translateX(0); }
		100% { transform: translateX(-50%); }
	}

	.header-status-bar {
		position: relative;
		background: #000;
		border-top: 1px solid #111;
		padding: 0.3rem 1.5rem;
		overflow: hidden;
	}

	.status-bar-content {
		display: flex;
		gap: 2rem;
		font-size: 0.65rem;
		color: #666;
		letter-spacing: 0.05em;
	}

	.bar-item {
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}

	.scan-overlay {
		position: absolute;
		top: 0;
		width: 100px;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(10, 79, 60, 0.1), transparent);
		transition: left 0.05s linear;
		pointer-events: none;
	}

	.viewport {
		flex: 1;
		position: relative;
		overflow: hidden;
		display: flex;
		background: #000000;
	}

	.content-wrapper {
		width: 100%;
		height: 100%;
		position: relative;
		overflow: hidden;
	}

	@media (max-width: 1400px) {
		.header-grid {
			grid-template-columns: 300px 1fr 280px;
			gap: 1rem;
		}
		
		.nav-grid {
			grid-template-columns: repeat(6, 1fr);
		}
	}

	@media (max-width: 1200px) {
		.system-title {
			font-size: 1.5rem;
		}
		
		.nav-cell {
			padding: 0.6rem 0.4rem;
		}
	}
</style>