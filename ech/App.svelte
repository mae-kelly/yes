<!-- App.svelte - Ultra Enhanced Tactical Command Center -->
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

	// Animated scan effects
	let scanPosition = 0;
	let pulseIntensity = 0;
	let dataStream = [];
	
	const scanInterval = setInterval(() => {
		scanPosition = (scanPosition + 0.5) % 100;
		pulseIntensity = Math.sin(Date.now() * 0.001) * 0.5 + 0.5;
	}, 50);
	
	// Generate data stream
	onMount(() => {
		for (let i = 0; i < 20; i++) {
			dataStream.push({
				value: Math.random(),
				speed: Math.random() * 2 + 1
			});
		}
	});

	onDestroy(() => {
		clearInterval(scanInterval);
	});
</script>

<main class="command-interface">
	<!-- Tactical Header -->
	<header class="tactical-header">
		<!-- Top scan line -->
		<div class="scan-line-top" style="left: {scanPosition}%"></div>
		
		<div class="header-grid">
			<!-- Left Section: Advanced Logo -->
			<div class="system-section">
				<div class="quantum-logo">
					<div class="logo-container">
						<!-- Outer hexagon frame -->
						<svg viewBox="0 0 120 120" class="logo-frame">
							<defs>
								<linearGradient id="techGrad" x1="0%" y1="0%" x2="100%" y2="100%">
									<stop offset="0%" style="stop-color:#0a4f3c;stop-opacity:1" />
									<stop offset="50%" style="stop-color:#0d6b4f;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#0a4f3c;stop-opacity:1" />
								</linearGradient>
								<filter id="glow">
									<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
									<feMerge>
										<feMergeNode in="coloredBlur"/>
										<feMergeNode in="SourceGraphic"/>
									</feMerge>
								</filter>
							</defs>
							
							<!-- Background grid -->
							<pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
								<path d="M 10 0 L 0 0 0 10" fill="none" stroke="#0a4f3c" stroke-width="0.1" opacity="0.3"/>
							</pattern>
							<rect width="120" height="120" fill="url(#grid)" />
							
							<!-- Rotating rings -->
							<g class="rotate-slow">
								<polygon points="60,10 100,35 100,85 60,110 20,85 20,35" 
										fill="none" stroke="url(#techGrad)" stroke-width="1" opacity="0.3"/>
							</g>
							<g class="rotate-reverse">
								<polygon points="60,20 90,40 90,80 60,100 30,80 30,40" 
										fill="none" stroke="#0a4f3c" stroke-width="1.5" opacity="0.5"/>
							</g>
							
							<!-- Core structure -->
							<g filter="url(#glow)">
								<polygon points="60,30 80,45 80,75 60,90 40,75 40,45" 
										fill="none" stroke="#0a4f3c" stroke-width="2"/>
								
								<!-- Inner triangular core -->
								<path d="M60,40 L70,60 L50,60 Z" fill="none" stroke="#0a4f3c" stroke-width="1.5" class="pulse"/>
								
								<!-- Center dot matrix -->
								<circle cx="60" cy="55" r="2" fill="#0a4f3c" class="pulse-dot"/>
								<circle cx="55" cy="60" r="1" fill="#0a4f3c" opacity="0.5"/>
								<circle cx="65" cy="60" r="1" fill="#0a4f3c" opacity="0.5"/>
							</g>
							
							<!-- Data flow lines -->
							<path d="M10,60 L40,60" stroke="#0a4f3c" stroke-width="0.5" opacity="{pulseIntensity}" class="data-flow"/>
							<path d="M80,60 L110,60" stroke="#0a4f3c" stroke-width="0.5" opacity="{1-pulseIntensity}" class="data-flow"/>
							<path d="M60,30 L60,10" stroke="#0a4f3c" stroke-width="0.5" opacity="{pulseIntensity}" class="data-flow"/>
							<path d="M60,90 L60,110" stroke="#0a4f3c" stroke-width="0.5" opacity="{1-pulseIntensity}" class="data-flow"/>
						</svg>
						
						<!-- Holographic overlay -->
						<div class="holo-overlay"></div>
					</div>
				</div>
				
				<div class="system-info">
					<div class="system-title">LOG LENS</div>
					<div class="system-subtitle">TACTICAL RECONNAISSANCE SYSTEM</div>
					<div class="system-stats">
						<div class="stat-group">
							<span class="stat-label">MODULE</span>
							<span class="stat-value">{getCurrentModule().name}</span>
						</div>
						<div class="stat-divider"></div>
						<div class="stat-group">
							<span class="stat-label">CODE</span>
							<span class="stat-value">{getCurrentModule().code}</span>
						</div>
					</div>
				</div>
			</div>

			<!-- Center Section: Tactical Navigation -->
			<nav class="nav-matrix">
				<div class="nav-background">
					{#each Array(6) as _, i}
						<div class="nav-line" style="animation-delay: {i * 0.1}s"></div>
					{/each}
				</div>
				<div class="nav-grid">
					{#each modules as module, i}
						<button 
							class="nav-cell {currentView === module.id ? 'active' : ''}"
							on:click={() => switchView(module.id)}>
							<div class="nav-hex">
								<svg viewBox="0 0 60 60" class="hex-icon">
									<polygon points="30,5 50,17.5 50,42.5 30,55 10,42.5 10,17.5" 
											fill="none" 
											stroke="{currentView === module.id ? '#0a4f3c' : '#333'}" 
											stroke-width="1"/>
									{#if currentView === module.id}
										<polygon points="30,10 45,20 45,40 30,50 15,40 15,20" 
												fill="#0a4f3c" 
												opacity="0.1"/>
									{/if}
								</svg>
							</div>
							<div class="nav-content">
								<div class="nav-code">{module.code}</div>
								<div class="nav-name">{module.name}</div>
								{#if currentView === module.id}
									<div class="nav-active-indicator"></div>
								{/if}
							</div>
						</button>
					{/each}
				</div>
			</nav>

			<!-- Right Section: System Status -->
			<div class="status-section">
				<div class="status-matrix">
					<div class="status-row">
						<div class="status-cell">
							<div class="status-indicator online"></div>
							<span class="status-label">SYSTEM</span>
							<span class="status-value">ONLINE</span>
						</div>
						<div class="status-cell">
							<div class="status-indicator nominal"></div>
							<span class="status-label">THREAT</span>
							<span class="status-value">NOMINAL</span>
						</div>
					</div>
					<div class="status-row">
						<div class="status-cell">
							<span class="status-label">TIME</span>
							<span class="status-value time">{time}</span>
						</div>
						<div class="status-cell">
							<span class="status-label">DATE</span>
							<span class="status-value">{date}</span>
						</div>
					</div>
				</div>
				
				<!-- Quantum wave monitor -->
				<div class="quantum-monitor">
					<svg viewBox="0 0 120 40" class="monitor-display">
						<defs>
							<linearGradient id="waveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
								<stop offset="0%" style="stop-color:#0a4f3c;stop-opacity:0" />
								<stop offset="50%" style="stop-color:#0a4f3c;stop-opacity:1" />
								<stop offset="100%" style="stop-color:#0a4f3c;stop-opacity:0" />
							</linearGradient>
						</defs>
						<rect x="0" y="0" width="120" height="40" fill="#000" opacity="0.5"/>
						{#each dataStream as stream, i}
							<rect x="{i * 6}" y="{20 - stream.value * 15}" 
								  width="4" height="{stream.value * 30}"
								  fill="#0a4f3c" opacity="{stream.value}"/>
						{/each}
						<polyline points="0,20 20,15 40,25 60,10 80,30 100,20 120,20" 
								  fill="none" stroke="url(#waveGrad)" stroke-width="1" class="wave-animation"/>
					</svg>
				</div>
			</div>
		</div>
		
		<!-- Bottom Status Bar -->
		<div class="header-status-bar">
			<div class="status-bar-grid">
				<div class="bar-segment">
					<span class="segment-icon">▶</span>
					<span class="segment-label">SECURE CHANNEL</span>
					<span class="segment-value">ESTABLISHED</span>
				</div>
				<div class="bar-segment">
					<span class="segment-icon">◆</span>
					<span class="segment-label">ENCRYPTION</span>
					<span class="segment-value">AES-256</span>
				</div>
				<div class="bar-segment">
					<span class="segment-icon">▲</span>
					<span class="segment-label">BANDWIDTH</span>
					<span class="segment-value">10GB/S</span>
				</div>
				<div class="bar-segment">
					<span class="segment-icon">●</span>
					<span class="segment-label">NODES</span>
					<span class="segment-value">1,337</span>
				</div>
				<div class="bar-segment">
					<span class="segment-icon">■</span>
					<span class="segment-label">LATENCY</span>
					<span class="segment-value">0.3MS</span>
				</div>
			</div>
			<div class="scan-overlay-bar" style="left: {scanPosition}%"></div>
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
	}

	.command-interface {
		width: 100vw;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: #000000;
		position: relative;
	}

	.tactical-header {
		background: linear-gradient(180deg, #0a0a0a 0%, #050505 100%);
		border-bottom: 2px solid #0a4f3c;
		flex-shrink: 0;
		position: relative;
		overflow: hidden;
	}

	.scan-line-top {
		position: absolute;
		top: 0;
		height: 1px;
		width: 100px;
		background: linear-gradient(90deg, transparent, #0a4f3c, transparent);
		transition: left 0.05s linear;
		z-index: 100;
	}

	.header-grid {
		display: grid;
		grid-template-columns: 400px 1fr 350px;
		gap: 2rem;
		padding: 1.5rem 2rem;
		align-items: center;
	}

	.system-section {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.quantum-logo {
		position: relative;
	}

	.logo-container {
		width: 120px;
		height: 120px;
		position: relative;
	}

	.logo-frame {
		width: 100%;
		height: 100%;
		filter: drop-shadow(0 0 30px rgba(10, 79, 60, 0.4));
	}

	.holo-overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: linear-gradient(45deg, transparent 30%, rgba(10, 79, 60, 0.1) 50%, transparent 70%);
		animation: holoScan 3s linear infinite;
		pointer-events: none;
	}

	@keyframes holoScan {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100%); }
	}

	.rotate-slow {
		animation: rotate 20s linear infinite;
		transform-origin: center;
	}

	.rotate-reverse {
		animation: rotate 15s linear infinite reverse;
		transform-origin: center;
	}

	.pulse {
		animation: pulse 2s ease-in-out infinite;
	}

	.pulse-dot {
		animation: pulseDot 1s ease-in-out infinite;
	}

	.data-flow {
		animation: dataFlow 2s linear infinite;
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
		0%, 100% { r: 2; opacity: 1; }
		50% { r: 4; opacity: 0.6; }
	}

	@keyframes dataFlow {
		0%, 100% { stroke-dasharray: 0 100; }
		50% { stroke-dasharray: 100 0; }
	}

	.system-info {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.system-title {
		font-size: 2rem;
		font-weight: 700;
		color: #0a4f3c;
		letter-spacing: 0.2em;
		text-shadow: 0 0 30px rgba(10, 79, 60, 0.6);
	}

	.system-subtitle {
		font-size: 0.7rem;
		color: #666;
		letter-spacing: 0.3em;
		font-weight: 300;
	}

	.system-stats {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-top: 0.5rem;
	}

	.stat-group {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.stat-label {
		font-size: 0.6rem;
		color: #666;
		letter-spacing: 0.1em;
	}

	.stat-value {
		font-size: 0.8rem;
		color: #0a4f3c;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.stat-divider {
		width: 1px;
		height: 30px;
		background: linear-gradient(180deg, transparent, #0a4f3c, transparent);
	}

	.nav-matrix {
		position: relative;
		padding: 1rem;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid #111;
		border-radius: 4px;
	}

	.nav-background {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		overflow: hidden;
		pointer-events: none;
	}

	.nav-line {
		position: absolute;
		width: 100%;
		height: 1px;
		background: linear-gradient(90deg, transparent, #0a4f3c, transparent);
		opacity: 0.1;
		animation: navScan 4s linear infinite;
	}

	@keyframes navScan {
		0% { transform: translateY(0); opacity: 0; }
		50% { opacity: 0.3; }
		100% { transform: translateY(100px); opacity: 0; }
	}

	.nav-grid {
		display: grid;
		grid-template-columns: repeat(6, 1fr);
		gap: 0.75rem;
		position: relative;
		z-index: 1;
	}

	.nav-cell {
		position: relative;
		background: #000;
		border: 1px solid #111;
		padding: 0.5rem;
		cursor: pointer;
		transition: all 0.3s ease;
		overflow: hidden;
	}

	.nav-cell::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(10, 79, 60, 0.2), transparent);
		transition: left 0.5s ease;
	}

	.nav-cell:hover::before {
		left: 100%;
	}

	.nav-cell:hover {
		background: rgba(10, 79, 60, 0.05);
		border-color: #0a4f3c;
		transform: translateY(-2px);
	}

	.nav-cell.active {
		background: rgba(10, 79, 60, 0.1);
		border-color: #0a4f3c;
		box-shadow: 0 0 20px rgba(10, 79, 60, 0.3);
	}

	.nav-hex {
		display: flex;
		justify-content: center;
		margin-bottom: 0.3rem;
	}

	.hex-icon {
		width: 30px;
		height: 30px;
	}

	.nav-content {
		position: relative;
		text-align: center;
	}

	.nav-code {
		font-size: 0.55rem;
		color: #666;
		letter-spacing: 0.1em;
		margin-bottom: 0.2rem;
	}

	.nav-name {
		font-size: 0.65rem;
		color: #b8a678;
		font-weight: 500;
		letter-spacing: 0.05em;
	}

	.nav-cell.active .nav-name {
		color: #0a4f3c;
	}

	.nav-active-indicator {
		position: absolute;
		bottom: -5px;
		left: 20%;
		right: 20%;
		height: 2px;
		background: #0a4f3c;
		box-shadow: 0 0 10px rgba(10, 79, 60, 0.8);
		animation: indicatorPulse 1s ease-in-out infinite;
	}

	@keyframes indicatorPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.status-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.status-matrix {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.status-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.status-cell {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		position: relative;
	}

	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		position: absolute;
		top: 0;
		right: 0;
		animation: statusBlink 2s ease-in-out infinite;
	}

	.status-indicator.online {
		background: #0a4f3c;
		box-shadow: 0 0 10px rgba(10, 79, 60, 0.8);
	}

	.status-indicator.nominal {
		background: #0a4f3c;
		box-shadow: 0 0 10px rgba(10, 79, 60, 0.8);
	}

	@keyframes statusBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}

	.status-value.time {
		font-family: 'Courier New', monospace;
		letter-spacing: 0.1em;
	}

	.quantum-monitor {
		height: 40px;
		border: 1px solid #111;
		border-radius: 2px;
		overflow: hidden;
		background: #000;
		position: relative;
	}

	.monitor-display {
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
		background: linear-gradient(90deg, #000 0%, #0a0a0a 50%, #000 100%);
		border-top: 1px solid #111;
		padding: 0.5rem 2rem;
		overflow: hidden;
	}

	.status-bar-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 2rem;
	}

	.bar-segment {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.65rem;
	}

	.segment-icon {
		color: #0a4f3c;
		font-size: 0.8rem;
	}

	.segment-label {
		color: #666;
		letter-spacing: 0.05em;
	}

	.segment-value {
		color: #b8a678;
		font-weight: 600;
	}

	.scan-overlay-bar {
		position: absolute;
		top: 0;
		width: 200px;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(10, 79, 60, 0.1), transparent);
		transition: left 0.05s linear;
		pointer-events: none;
	}

	.viewport {
		flex: 1;
		position: relative;
		overflow: hidden;
		background: #000000;
	}

	.content-wrapper {
		width: 100%;
		height: 100%;
		position: relative;
	}
</style>