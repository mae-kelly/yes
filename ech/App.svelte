<!-- App.svelte - Futuristic Military Command Center -->
<script>
	import { onMount, onDestroy } from 'svelte';
	import SourceTables from './SourceTables.svelte';
	import RegionMetrics from './RegionMetrics.svelte';
	import CountryMetrics from './CountryMetrics.svelte';
	import DataCenter from './DataCenter.svelte';
	import BusinessUnitMetrics from './BusinessUnitMetrics.svelte';
	import CIOMetrics from './CIOMetrics.svelte';

	let currentView = 'source_tables';
	let time = new Date();
	let glitchActive = false;
	
	let modules = [
		{ id: 'source_tables', name: 'SOURCE TABLES', code: 'SRC-TBL', status: 'ACTIVE' },
		{ id: 'region_metrics', name: 'REGIONS', code: 'RGN-MTR', status: 'ACTIVE' },
		{ id: 'country_metrics', name: 'COUNTRIES', code: 'CNT-MTR', status: 'ACTIVE' },
		{ id: 'data_center', name: 'DATA CENTERS', code: 'DC-OPS', status: 'MONITORING' },
		{ id: 'business_units', name: 'DIVISIONS', code: 'DIV-OPS', status: 'ACTIVE' },
		{ id: 'cio_metrics', name: 'EXECUTIVES', code: 'CIO-CMD', status: 'ACTIVE' }
	];

	function switchView(moduleId) {
		glitchActive = true;
		setTimeout(() => {
			currentView = moduleId;
			glitchActive = false;
		}, 200);
	}

	function getCurrentModule() {
		return modules.find(m => m.id === currentView) || modules[0];
	}

	let interval;
	onMount(() => {
		interval = setInterval(() => {
			time = new Date();
		}, 1000);
	});

	onDestroy(() => {
		if (interval) clearInterval(interval);
	});

	$: currentModule = getCurrentModule();
	$: timeString = time.toLocaleTimeString('en-US', { hour12: false });
	$: dateString = time.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }).toUpperCase();
</script>

<main class="command-interface">
	<!-- Futuristic Header -->
	<header class="command-header">
		<div class="header-grid">
			<!-- Left Section: Logo and Title -->
			<div class="header-left">
				<div class="logo-section">
					<div class="logo-container">
						<svg class="logo-primary" viewBox="0 0 100 100">
							<!-- Outer hexagon -->
							<polygon points="50,5 90,27.5 90,72.5 50,95 10,72.5 10,27.5" 
								fill="none" 
								stroke="url(#techGradient)" 
								stroke-width="2"/>
							<!-- Inner hexagon -->
							<polygon points="50,20 75,35 75,65 50,80 25,65 25,35" 
								fill="none" 
								stroke="url(#techGradient)" 
								stroke-width="1.5"
								opacity="0.8"/>
							<!-- Center eye -->
							<circle cx="50" cy="50" r="15" fill="none" stroke="url(#techGradient)" stroke-width="2"/>
							<circle cx="50" cy="50" r="8" fill="none" stroke="url(#techGradient)" stroke-width="1.5"/>
							<circle cx="50" cy="50" r="3" fill="url(#techGradient)"/>
							<!-- Scanning lines -->
							<line x1="50" y1="5" x2="50" y2="20" stroke="url(#techGradient)" stroke-width="1" opacity="0.6"/>
							<line x1="50" y1="80" x2="50" y2="95" stroke="url(#techGradient)" stroke-width="1" opacity="0.6"/>
							<line x1="10" y1="50" x2="25" y2="50" stroke="url(#techGradient)" stroke-width="1" opacity="0.6"/>
							<line x1="75" y1="50" x2="90" y2="50" stroke="url(#techGradient)" stroke-width="1" opacity="0.6"/>
							
							<defs>
								<linearGradient id="techGradient" x1="0%" y1="0%" x2="100%" y2="100%">
									<stop offset="0%" style="stop-color:#00ffcc;stop-opacity:1">
										<animate attributeName="stop-color" values="#00ffcc;#0099ff;#00ffcc" dur="3s" repeatCount="indefinite"/>
									</stop>
									<stop offset="100%" style="stop-color:#0099ff;stop-opacity:1">
										<animate attributeName="stop-color" values="#0099ff;#00ffcc;#0099ff" dur="3s" repeatCount="indefinite"/>
									</stop>
								</linearGradient>
							</defs>
						</svg>
						<div class="logo-glitch"></div>
						<div class="logo-scan"></div>
					</div>
					<div class="title-block">
						<div class="system-designation">TACTICAL OPERATIONS</div>
						<h1 class="system-title {glitchActive ? 'glitch' : ''}">
							<span class="title-text">LOG LENS</span>
							<span class="version-badge">v5.0</span>
						</h1>
						<div class="current-module">
							<span class="module-code">[{currentModule.code}]</span>
							<span class="module-title">{currentModule.name}</span>
							<span class="status-indicator {currentModule.status.toLowerCase()}"></span>
						</div>
					</div>
				</div>
			</div>

			<!-- Center Section: Status Display -->
			<div class="header-center">
				<div class="status-panel">
					<div class="status-row">
						<span class="status-label">SYSTEM</span>
						<span class="status-value online">ONLINE</span>
					</div>
					<div class="status-row">
						<span class="status-label">SECURITY</span>
						<span class="status-value secured">MAXIMUM</span>
					</div>
					<div class="status-row">
						<span class="status-label">THREAT LVL</span>
						<span class="status-value nominal">NOMINAL</span>
					</div>
				</div>
				<div class="datetime-display">
					<div class="time">{timeString}</div>
					<div class="date">{dateString}</div>
				</div>
			</div>

			<!-- Right Section: Navigation -->
			<div class="header-right">
				<nav class="nav-grid">
					{#each modules as module}
						<button 
							class="nav-cell {currentView === module.id ? 'active' : ''}"
							on:click={() => switchView(module.id)}>
							<span class="nav-code">{module.code}</span>
							<span class="nav-name">{module.name}</span>
							{#if currentView === module.id}
								<div class="active-frame">
									<svg viewBox="0 0 60 60">
										<polyline points="10,5 5,5 5,10" />
										<polyline points="50,5 55,5 55,10" />
										<polyline points="10,55 5,55 5,50" />
										<polyline points="50,55 55,55 55,50" />
									</svg>
								</div>
							{/if}
						</button>
					{/each}
				</nav>
			</div>
		</div>
		
		<!-- Scanning line effect -->
		<div class="scan-line"></div>
	</header>

	<!-- Main Content -->
	<section class="viewport">
		<div class="content-wrapper {glitchActive ? 'glitching' : ''}">
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
		<!-- HUD Overlay -->
		<div class="hud-overlay">
			<div class="corner-marker top-left"></div>
			<div class="corner-marker top-right"></div>
			<div class="corner-marker bottom-left"></div>
			<div class="corner-marker bottom-right"></div>
		</div>
	</section>
</main>

<style>
	:global(body) {
		font-family: 'JetBrains Mono', 'Courier New', monospace;
		background: #000;
		color: #e0e0e0;
		overflow: hidden;
		margin: 0;
		padding: 0;
		font-size: 14px;
		line-height: 1.5;
	}

	.command-interface {
		width: 100vw;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: 
			radial-gradient(circle at 20% 50%, rgba(0, 255, 204, 0.03) 0%, transparent 50%),
			radial-gradient(circle at 80% 50%, rgba(0, 153, 255, 0.03) 0%, transparent 50%),
			linear-gradient(180deg, #000 0%, #0a0a0a 100%);
		overflow: hidden;
	}

	.command-header {
		position: relative;
		background: linear-gradient(180deg, rgba(0,15,30,0.95) 0%, rgba(0,10,20,0.95) 100%);
		border-bottom: 2px solid #00ffcc;
		padding: 1rem 1.5rem;
		flex-shrink: 0;
		box-shadow: 
			0 4px 20px rgba(0, 255, 204, 0.2),
			inset 0 -1px 0 rgba(0, 255, 204, 0.3);
		overflow: hidden;
	}

	.header-grid {
		display: grid;
		grid-template-columns: 1fr auto 1fr;
		gap: 2rem;
		align-items: center;
		max-width: 100%;
		position: relative;
		z-index: 2;
	}

	.header-left {
		display: flex;
		align-items: center;
	}

	.logo-section {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.logo-container {
		position: relative;
		width: 80px;
		height: 80px;
	}

	.logo-primary {
		width: 100%;
		height: 100%;
		filter: drop-shadow(0 0 20px rgba(0, 255, 204, 0.5));
		animation: logoRotate 20s linear infinite;
	}

	@keyframes logoRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.logo-glitch {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: radial-gradient(circle, rgba(0, 255, 204, 0.2), transparent);
		animation: glitchPulse 2s ease-in-out infinite;
	}

	.logo-scan {
		position: absolute;
		top: -10%;
		left: 0;
		width: 100%;
		height: 20%;
		background: linear-gradient(180deg, transparent, rgba(0, 255, 204, 0.3), transparent);
		animation: logoScan 3s linear infinite;
	}

	@keyframes logoScan {
		0% { top: -20%; }
		100% { top: 100%; }
	}

	@keyframes glitchPulse {
		0%, 100% { opacity: 0; }
		50% { opacity: 1; }
	}

	.title-block {
		display: flex;
		flex-direction: column;
	}

	.system-designation {
		font-size: 0.65rem;
		color: #0099ff;
		letter-spacing: 0.3em;
		margin-bottom: 0.2rem;
		text-transform: uppercase;
		opacity: 0.8;
	}

	.system-title {
		margin: 0;
		font-size: 2rem;
		font-weight: 800;
		letter-spacing: 0.05em;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		position: relative;
	}

	.title-text {
		background: linear-gradient(135deg, #00ffcc 0%, #0099ff 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		text-shadow: 0 0 40px rgba(0, 255, 204, 0.5);
	}

	.version-badge {
		font-size: 0.5rem;
		padding: 0.2rem 0.4rem;
		background: rgba(0, 255, 204, 0.1);
		border: 1px solid #00ffcc;
		border-radius: 3px;
		color: #00ffcc;
		letter-spacing: 0.1em;
	}

	.system-title.glitch {
		animation: textGlitch 0.3s ease-in-out;
	}

	@keyframes textGlitch {
		0%, 100% { transform: translateX(0); }
		20% { transform: translateX(-2px); }
		40% { transform: translateX(2px); }
		60% { transform: translateX(-1px); }
		80% { transform: translateX(1px); }
	}

	.current-module {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-top: 0.5rem;
		font-size: 0.9rem;
		color: #00ffcc;
	}

	.module-code {
		font-size: 0.7rem;
		padding: 0.2rem 0.4rem;
		background: rgba(0, 153, 255, 0.2);
		border: 1px solid #0099ff;
		border-radius: 3px;
		color: #0099ff;
		font-weight: 600;
	}

	.module-title {
		font-weight: 500;
		letter-spacing: 0.1em;
		text-transform: uppercase;
	}

	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: #00ff00;
		animation: statusPulse 2s ease-in-out infinite;
	}

	.status-indicator.monitoring {
		background: #ffaa00;
	}

	@keyframes statusPulse {
		0%, 100% { opacity: 1; box-shadow: 0 0 5px currentColor; }
		50% { opacity: 0.5; box-shadow: 0 0 15px currentColor; }
	}

	.header-center {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.status-panel {
		display: flex;
		gap: 2rem;
		padding: 0.5rem 1rem;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(0, 255, 204, 0.2);
		border-radius: 4px;
	}

	.status-row {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.status-label {
		font-size: 0.6rem;
		color: #0099ff;
		letter-spacing: 0.1em;
		opacity: 0.7;
	}

	.status-value {
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.status-value.online {
		color: #00ff00;
	}

	.status-value.secured {
		color: #00ffcc;
	}

	.status-value.nominal {
		color: #0099ff;
	}

	.datetime-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		font-family: 'Courier New', monospace;
	}

	.time {
		font-size: 1.2rem;
		font-weight: 600;
		color: #00ffcc;
		letter-spacing: 0.1em;
		text-shadow: 0 0 10px rgba(0, 255, 204, 0.5);
	}

	.date {
		font-size: 0.7rem;
		color: #0099ff;
		letter-spacing: 0.15em;
	}

	.header-right {
		display: flex;
		justify-content: flex-end;
	}

	.nav-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.5rem;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(0, 255, 204, 0.1);
		border-radius: 4px;
	}

	.nav-cell {
		position: relative;
		background: rgba(0, 10, 20, 0.6);
		border: 1px solid rgba(0, 153, 255, 0.3);
		padding: 0.6rem;
		cursor: pointer;
		transition: all 0.2s ease;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.2rem;
		min-width: 100px;
	}

	.nav-cell:hover {
		background: rgba(0, 255, 204, 0.1);
		border-color: #00ffcc;
		transform: translateY(-1px);
		box-shadow: 0 4px 10px rgba(0, 255, 204, 0.3);
	}

	.nav-cell.active {
		background: linear-gradient(135deg, rgba(0, 255, 204, 0.2), rgba(0, 153, 255, 0.2));
		border-color: #00ffcc;
		box-shadow: 
			0 0 20px rgba(0, 255, 204, 0.3),
			inset 0 0 10px rgba(0, 255, 204, 0.1);
	}

	.nav-code {
		font-size: 0.65rem;
		color: #0099ff;
		font-weight: 600;
		letter-spacing: 0.1em;
	}

	.nav-name {
		font-size: 0.7rem;
		color: #00ffcc;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.active-frame {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	.active-frame svg {
		width: 100%;
		height: 100%;
		stroke: #00ffcc;
		stroke-width: 2;
		fill: none;
	}

	.scan-line {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, #00ffcc, transparent);
		animation: scanLine 3s linear infinite;
	}

	@keyframes scanLine {
		0% { transform: translateY(0); }
		100% { transform: translateY(100px); }
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
		transition: all 0.3s ease;
	}

	.content-wrapper.glitching {
		animation: contentGlitch 0.2s ease-in-out;
	}

	@keyframes contentGlitch {
		0%, 100% { transform: translateX(0); filter: none; }
		20% { transform: translateX(-2px); filter: hue-rotate(90deg); }
		40% { transform: translateX(2px); filter: hue-rotate(-90deg); }
		60% { transform: translateX(-1px); filter: hue-rotate(45deg); }
		80% { transform: translateX(1px); filter: hue-rotate(-45deg); }
	}

	.hud-overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 10;
	}

	.corner-marker {
		position: absolute;
		width: 30px;
		height: 30px;
		border: 2px solid rgba(0, 255, 204, 0.2);
		opacity: 0.5;
	}

	.corner-marker.top-left {
		top: 10px;
		left: 10px;
		border-right: none;
		border-bottom: none;
	}

	.corner-marker.top-right {
		top: 10px;
		right: 10px;
		border-left: none;
		border-bottom: none;
	}

	.corner-marker.bottom-left {
		bottom: 10px;
		left: 10px;
		border-right: none;
		border-top: none;
	}

	.corner-marker.bottom-right {
		bottom: 10px;
		right: 10px;
		border-left: none;
		border-top: none;
	}

	@media (max-width: 1400px) {
		.header-grid {
			gap: 1rem;
		}
		
		.nav-grid {
			grid-template-columns: repeat(2, 1fr);
		}
		
		.system-title {
			font-size: 1.5rem;
		}
	}

	@media (max-width: 1200px) {
		.logo-container {
			width: 60px;
			height: 60px;
		}
		
		.nav-cell {
			min-width: 90px;
			padding: 0.5rem;
		}
	}
</style>