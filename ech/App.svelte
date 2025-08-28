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
		{ id: 'source_tables', name: 'SOURCE TABLES', code: 'SRC-TBL', status: 'ACTIVE', color: '#00ff88' },
		{ id: 'region_metrics', name: 'REGIONS', code: 'REG-MET', status: 'ACTIVE', color: '#00ffff' },
		{ id: 'country_metrics', name: 'COUNTRIES', code: 'CTY-MET', status: 'ACTIVE', color: '#ff00ff' },
		{ id: 'data_center', name: 'DATA CENTERS', code: 'DC-FAC', status: 'MONITORING', color: '#ff9900' },
		{ id: 'business_units', name: 'DIVISIONS', code: 'BU-DIV', status: 'ACTIVE', color: '#00ff88' },
		{ id: 'cio_metrics', name: 'EXECUTIVES', code: 'CIO-EX', status: 'ACTIVE', color: '#ff0066' }
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

	// Random glitch effect
	let glitchActive = false;
	setInterval(() => {
		glitchActive = Math.random() > 0.98;
		if (glitchActive) setTimeout(() => glitchActive = false, 100);
	}, 1000);

	// Threat level simulation
	let threatLevel = 0.3;
	setInterval(() => {
		threatLevel = 0.3 + Math.random() * 0.4;
	}, 5000);
</script>

<main class="command-interface">
	<!-- Advanced Header -->
	<header class="tactical-header {glitchActive ? 'glitch' : ''}">
		<div class="header-grid">
			<!-- Left Section: Advanced Logo System -->
			<div class="system-section">
				<div class="quantum-logo">
					<!-- Holographic Core -->
					<div class="holo-core">
						<svg viewBox="0 0 120 120" class="logo-main">
							<!-- Background Grid -->
							<defs>
								<pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
									<path d="M 10 0 L 0 0 0 10" fill="none" stroke="#0a4f3c" stroke-width="0.2" opacity="0.5"/>
								</pattern>
								<filter id="glow">
									<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
									<feMerge>
										<feMergeNode in="coloredBlur"/>
										<feMergeNode in="SourceGraphic"/>
									</feMerge>
								</filter>
								<linearGradient id="techGrad" x1="0%" y1="0%" x2="100%" y2="100%">
									<stop offset="0%" style="stop-color:#00ffff;stop-opacity:1" />
									<stop offset="50%" style="stop-color:#0a4f3c;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#00ff88;stop-opacity:1" />
								</linearGradient>
							</defs>
							
							<!-- Grid Background -->
							<rect width="120" height="120" fill="url(#grid)" opacity="0.3"/>
							
							<!-- Outer Defense Ring -->
							<g class="defense-ring">
								<circle cx="60" cy="60" r="55" fill="none" stroke="url(#techGrad)" stroke-width="0.5" opacity="0.8"/>
								<circle cx="60" cy="60" r="52" fill="none" stroke="#0a4f3c" stroke-width="0.3" stroke-dasharray="2 3" class="rotate-slow"/>
								<circle cx="60" cy="60" r="48" fill="none" stroke="#00ffff" stroke-width="0.2" stroke-dasharray="5 5" class="rotate-fast"/>
							</g>
							
							<!-- Tactical Hexagon Frame -->
							<g class="tactical-frame">
								<polygon points="60,20 90,35 90,65 60,80 30,65 30,35" 
										 fill="none" stroke="#0a4f3c" stroke-width="1.5" opacity="0.8"/>
								<polygon points="60,25 85,38 85,62 60,75 35,62 35,38" 
										 fill="none" stroke="#00ffff" stroke-width="0.5" class="pulse"/>
							</g>
							
							<!-- Inner Core Triangle -->
							<g class="core-system">
								<path d="M60,35 L75,55 L45,55 Z" fill="none" stroke="#00ff88" stroke-width="1" filter="url(#glow)" class="pulse"/>
								<circle cx="60" cy="48" r="8" fill="#000" stroke="#0a4f3c" stroke-width="1"/>
								<circle cx="60" cy="48" r="4" fill="#00ffff" class="pulse-dot"/>
							</g>
							
							<!-- Tactical Lines -->
							<g class="tactical-lines">
								<line x1="10" y1="60" x2="25" y2="60" stroke="#00ff88" stroke-width="0.5" class="scan-line-h"/>
								<line x1="95" y1="60" x2="110" y2="60" stroke="#00ff88" stroke-width="0.5" class="scan-line-h"/>
								<line x1="60" y1="10" x2="60" y2="25" stroke="#00ffff" stroke-width="0.5" class="scan-line-v"/>
								<line x1="60" y1="95" x2="60" y2="110" stroke="#00ffff" stroke-width="0.5" class="scan-line-v"/>
							</g>
							
							<!-- Corner Brackets -->
							<g class="corner-brackets">
								<path d="M15,25 L15,15 L25,15" fill="none" stroke="#ff0066" stroke-width="0.5"/>
								<path d="M95,15 L105,15 L105,25" fill="none" stroke="#ff0066" stroke-width="0.5"/>
								<path d="M105,95 L105,105 L95,105" fill="none" stroke="#ff0066" stroke-width="0.5"/>
								<path d="M25,105 L15,105 L15,95" fill="none" stroke="#ff0066" stroke-width="0.5"/>
							</g>
						</svg>
						
						<!-- Orbiting Elements -->
						<div class="orbit-container">
							<div class="orbit-element orbit-1"></div>
							<div class="orbit-element orbit-2"></div>
							<div class="orbit-element orbit-3"></div>
						</div>
					</div>
					
					<!-- Scan Effect -->
					<div class="scan-overlay" style="top: {scanPosition}%"></div>
				</div>
				
				<div class="system-info">
					<div class="system-designation">
						<span class="designation-prefix">TACTICAL-OPS</span>
						<span class="designation-separator">//</span>
						<span class="designation-main">LOG LENS</span>
					</div>
					<div class="system-subtitle">RECONNAISSANCE COMMAND SYSTEM v4.1</div>
					<div class="system-stats">
						<span class="stat-item">
							<span class="stat-icon">▣</span>
							<span class="stat-label">MODULE:</span>
							<span class="stat-value" style="color: {getCurrentModule().color}">{getCurrentModule().name}</span>
						</span>
						<span class="stat-divider">|</span>
						<span class="stat-item">
							<span class="stat-icon">◈</span>
							<span class="stat-label">CODE:</span>
							<span class="stat-value">{getCurrentModule().code}</span>
						</span>
						<span class="stat-divider">|</span>
						<span class="stat-item">
							<span class="stat-icon">◉</span>
							<span class="stat-label">STATUS:</span>
							<span class="stat-value status-{getCurrentModule().status.toLowerCase()}">{getCurrentModule().status}</span>
						</span>
					</div>
				</div>
			</div>

			<!-- Center Section: Navigation Matrix -->
			<nav class="nav-matrix">
				<div class="nav-grid">
					{#each modules as module}
						<button 
							class="nav-cell {currentView === module.id ? 'active' : ''}"
							on:click={() => switchView(module.id)}>
							<div class="nav-cell-border"></div>
							<div class="nav-content">
								<div class="nav-icon">
									{#if module.id === 'source_tables'}
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
											<rect x="3" y="3" width="7" height="7" />
											<rect x="14" y="3" width="7" height="7" />
											<rect x="3" y="14" width="7" height="7" />
											<rect x="14" y="14" width="7" height="7" />
										</svg>
									{:else if module.id === 'region_metrics'}
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
											<circle cx="12" cy="12" r="10" />
											<path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
										</svg>
									{:else if module.id === 'country_metrics'}
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
											<path d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"/>
										</svg>
									{:else if module.id === 'data_center'}
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
											<path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
										</svg>
									{:else if module.id === 'business_units'}
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
											<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
										</svg>
									{:else if module.id === 'cio_metrics'}
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
											<path d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
										</svg>
									{/if}
								</div>
								<div class="nav-code">{module.code}</div>
								<div class="nav-name">{module.name}</div>
								{#if currentView === module.id}
									<div class="nav-active-indicator" style="background: {module.color}"></div>
								{/if}
							</div>
						</button>
					{/each}
				</div>
			</nav>

			<!-- Right Section: Advanced Status Panel -->
			<div class="status-section">
				<div class="threat-monitor">
					<div class="threat-label">THREAT ANALYSIS</div>
					<div class="threat-bar">
						<div class="threat-fill" style="width: {threatLevel * 100}%; background: {threatLevel > 0.6 ? '#ff0066' : threatLevel > 0.4 ? '#ff9900' : '#00ff88'}"></div>
					</div>
					<div class="threat-value">{(threatLevel * 100).toFixed(0)}%</div>
				</div>
				
				<div class="status-grid">
					<div class="status-item">
						<span class="status-icon">◆</span>
						<span class="status-label">SYSTEM</span>
						<span class="status-value online">ONLINE</span>
					</div>
					<div class="status-item">
						<span class="status-icon">▲</span>
						<span class="status-label">UPLINK</span>
						<span class="status-value nominal">SECURE</span>
					</div>
					<div class="status-item">
						<span class="status-icon">◈</span>
						<span class="status-label">TIME</span>
						<span class="status-value">{time}</span>
					</div>
					<div class="status-item">
						<span class="status-icon">◉</span>
						<span class="status-label">DATE</span>
						<span class="status-value">{date}</span>
					</div>
				</div>
				
				<div class="quantum-indicator">
					<svg viewBox="0 0 120 40" class="quantum-wave">
						<defs>
							<linearGradient id="waveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
								<stop offset="0%" style="stop-color:#00ffff;stop-opacity:0" />
								<stop offset="50%" style="stop-color:#00ff88;stop-opacity:1" />
								<stop offset="100%" style="stop-color:#00ffff;stop-opacity:0" />
							</linearGradient>
						</defs>
						<polyline points="0,20 10,10 20,25 30,15 40,20 50,5 60,30 70,20 80,20 90,10 100,25 110,15 120,20" 
								  fill="none" 
								  stroke="url(#waveGrad)" 
								  stroke-width="1.5"
								  class="wave-animation"/>
						<polyline points="0,20 10,25 20,10 30,20 40,15 50,30 60,5 70,20 80,20 90,25 100,10 110,20 120,15" 
								  fill="none" 
								  stroke="#0a4f3c" 
								  stroke-width="0.5"
								  opacity="0.5"
								  class="wave-animation-reverse"/>
					</svg>
				</div>
			</div>
		</div>
		
		<!-- Bottom Status Bar with Military-Grade Design -->
		<div class="header-status-bar">
			<div class="status-bar-content">
				<span class="bar-item critical">▶ SECURE CHANNEL: AES-256-GCM</span>
				<span class="bar-item">◆ ENCRYPTION: QUANTUM-SAFE</span>
				<span class="bar-item">▲ BANDWIDTH: 10GB/S</span>
				<span class="bar-item">● NODES: 1,337 ACTIVE</span>
				<span class="bar-item">■ LATENCY: 0.3MS</span>
				<span class="bar-item warning">⬢ PACKETS: 847.2K/S</span>
			</div>
			<div class="scan-line-horizontal" style="left: {scanPosition}%"></div>
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

	.tactical-header.glitch {
		animation: glitch 0.1s ease;
	}

	@keyframes glitch {
		0%, 100% { transform: translateX(0); }
		25% { transform: translateX(-2px); }
		50% { transform: translateX(2px); }
		75% { transform: translateX(-1px); }
	}

	.header-grid {
		display: grid;
		grid-template-columns: 420px 1fr 340px;
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
		width: 120px;
		height: 120px;
		position: relative;
		flex-shrink: 0;
	}

	.holo-core {
		position: relative;
		width: 100%;
		height: 100%;
	}

	.logo-main {
		width: 100%;
		height: 100%;
		filter: drop-shadow(0 0 20px rgba(0, 255, 255, 0.3));
	}

	.defense-ring {
		transform-origin: center;
	}

	.rotate-slow {
		animation: rotate 20s linear infinite;
	}

	.rotate-fast {
		animation: rotate-reverse 10s linear infinite;
	}

	@keyframes rotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	@keyframes rotate-reverse {
		from { transform: rotate(360deg); }
		to { transform: rotate(0deg); }
	}

	.pulse {
		animation: pulse 2s ease-in-out infinite;
	}

	.pulse-dot {
		animation: pulseDot 1s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 0.6; }
		50% { opacity: 1; }
	}

	@keyframes pulseDot {
		0%, 100% { r: 4; opacity: 1; }
		50% { r: 6; opacity: 0.6; }
	}

	.scan-line-h {
		animation: scanH 3s ease-in-out infinite;
	}

	.scan-line-v {
		animation: scanV 3s ease-in-out infinite;
	}

	@keyframes scanH {
		0%, 100% { opacity: 0.2; }
		50% { opacity: 1; }
	}

	@keyframes scanV {
		0%, 100% { opacity: 0.2; }
		50% { opacity: 1; }
	}

	.orbit-container {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	.orbit-element {
		position: absolute;
		width: 4px;
		height: 4px;
		background: #00ffff;
		border-radius: 50%;
		box-shadow: 0 0 10px #00ffff;
	}

	.orbit-1 {
		top: 20%;
		left: 50%;
		animation: orbit1 8s linear infinite;
	}

	.orbit-2 {
		top: 50%;
		left: 20%;
		animation: orbit2 12s linear infinite;
	}

	.orbit-3 {
		top: 80%;
		left: 50%;
		animation: orbit3 15s linear infinite;
	}

	@keyframes orbit1 {
		from { transform: rotate(0deg) translateX(40px) rotate(0deg); }
		to { transform: rotate(360deg) translateX(40px) rotate(-360deg); }
	}

	@keyframes orbit2 {
		from { transform: rotate(0deg) translateX(50px) rotate(0deg); }
		to { transform: rotate(-360deg) translateX(50px) rotate(360deg); }
	}

	@keyframes orbit3 {
		from { transform: rotate(0deg) translateX(45px) rotate(0deg); }
		to { transform: rotate(360deg) translateX(45px) rotate(-360deg); }
	}

	.scan-overlay {
		position: absolute;
		left: 0;
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, #00ff88, transparent);
		opacity: 0.8;
		transition: top 0.05s linear;
	}

	.system-info {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.system-designation {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.designation-prefix {
		font-size: 0.7rem;
		color: #00ffff;
		letter-spacing: 0.2em;
		font-weight: 400;
	}

	.designation-separator {
		color: #0a4f3c;
		font-size: 1rem;
	}

	.designation-main {
		font-size: 2rem;
		font-weight: 700;
		background: linear-gradient(135deg, #00ffff, #00ff88);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		letter-spacing: 0.15em;
		text-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
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
		margin-top: 0.5rem;
	}

	.stat-item {
		display: flex;
		gap: 0.3rem;
		align-items: center;
	}

	.stat-icon {
		color: #0a4f3c;
		font-size: 0.8rem;
	}

	.stat-label {
		font-size: 0.65rem;
		color: #666;
		font-weight: 400;
	}

	.stat-value {
		font-size: 0.75rem;
		color: #00ffff;
		font-weight: 600;
	}

	.status-active {
		color: #00ff88;
	}

	.status-monitoring {
		color: #ff9900;
	}

	.stat-divider {
		color: #333;
		font-size: 0.8rem;
	}

	.nav-matrix {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.nav-grid {
		display: grid;
		grid-template-columns: repeat(6, 1fr);
		gap: 0.75rem;
		padding: 0.75rem;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid #111;
		border-radius: 8px;
		position: relative;
	}

	.nav-grid::before {
		content: '';
		position: absolute;
		top: -1px;
		left: -1px;
		right: -1px;
		bottom: -1px;
		background: linear-gradient(45deg, #00ffff, transparent, #00ff88);
		border-radius: 8px;
		opacity: 0.1;
		z-index: -1;
	}

	.nav-cell {
		position: relative;
		background: #000;
		border: 1px solid #111;
		padding: 0.75rem 0.5rem;
		cursor: pointer;
		transition: all 0.2s ease;
		overflow: hidden;
		border-radius: 4px;
	}

	.nav-cell-border {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		border: 1px solid transparent;
		transition: all 0.3s ease;
		pointer-events: none;
	}

	.nav-cell:hover .nav-cell-border {
		border-color: #00ffff;
		box-shadow: inset 0 0 10px rgba(0, 255, 255, 0.2);
	}

	.nav-cell.active .nav-cell-border {
		border-color: #00ff88;
		box-shadow: inset 0 0 15px rgba(0, 255, 136, 0.3);
	}

	.nav-content {
		position: relative;
		text-align: center;
	}

	.nav-icon {
		width: 24px;
		height: 24px;
		margin: 0 auto 0.3rem;
		color: #0a4f3c;
		transition: all 0.2s ease;
	}

	.nav-cell:hover .nav-icon {
		color: #00ffff;
		filter: drop-shadow(0 0 5px currentColor);
	}

	.nav-cell.active .nav-icon {
		color: #00ff88;
		filter: drop-shadow(0 0 8px currentColor);
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
		color: #00ff88;
	}

	.nav-active-indicator {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		height: 2px;
		box-shadow: 0 0 10px currentColor;
		animation: activeGlow 1s ease-in-out infinite;
	}

	@keyframes activeGlow {
		0%, 100% { opacity: 0.6; }
		50% { opacity: 1; }
	}

	.status-section {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.threat-monitor {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid #111;
		border-radius: 4px;
		padding: 0.5rem;
	}

	.threat-label {
		font-size: 0.6rem;
		color: #666;
		letter-spacing: 0.1em;
		margin-bottom: 0.3rem;
	}

	.threat-bar {
		height: 4px;
		background: #111;
		border-radius: 2px;
		overflow: hidden;
		margin-bottom: 0.2rem;
	}

	.threat-fill {
		height: 100%;
		transition: all 0.3s ease;
		box-shadow: 0 0 10px currentColor;
	}

	.threat-value {
		font-size: 0.7rem;
		color: #00ffff;
		text-align: right;
		font-weight: 600;
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

	.status-icon {
		color: #0a4f3c;
		font-size: 0.8rem;
		margin-bottom: 0.1rem;
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
		color: #00ff88;
	}

	.status-value.nominal {
		color: #00ffff;
	}

	.quantum-indicator {
		height: 40px;
		overflow: hidden;
		border: 1px solid #111;
		border-radius: 4px;
		background: #000;
		padding: 4px;
		position: relative;
	}

	.quantum-wave {
		width: 100%;
		height: 100%;
	}

	.wave-animation {
		animation: waveMove 4s linear infinite;
	}

	.wave-animation-reverse {
		animation: waveMove 6s linear infinite reverse;
	}

	@keyframes waveMove {
		0% { transform: translateX(0); }
		100% { transform: translateX(-60px); }
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
		font-family: inherit;
	}

	.bar-item {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		transition: color 0.2s ease;
	}

	.bar-item.critical {
		color: #00ff88;
	}

	.bar-item.warning {
		color: #ff9900;
	}

	.scan-line-horizontal {
		position: absolute;
		top: 0;
		width: 100px;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.2), transparent);
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
			grid-template-columns: 340px 1fr 280px;
			gap: 1rem;
		}
		
		.quantum-logo {
			width: 100px;
			height: 100px;
		}
		
		.designation-main {
			font-size: 1.5rem;
		}
	}
</style>