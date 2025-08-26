<!-- App.svelte -->
<script>
	import { onMount } from 'svelte';
	import SourceTables from './SourceTables.svelte';
	import DomainMetrics from './DomainMetrics.svelte';
	import InfrastructureType from './InfrastructureType.svelte';
	import RegionMetrics from './RegionMetrics.svelte';
	import CountryMetrics from './CountryMetrics.svelte';
	import DataCenterMetrics from './DataCenterMetrics.svelte';
	import CloudRegionMetrics from './CloudRegionMetrics.svelte';
	import ClassMetrics from './ClassMetrics.svelte';
	import SystemClassification from './SystemClassification.svelte';
	import BusinessUnitMetrics from './BusinessUnitMetrics.svelte';
	import CioMetrics from './CioMetrics.svelte';
	import TaniumCoverage from './TaniumCoverage.svelte';
	import CmdbPresence from './CmdbPresence.svelte';

	let currentView = 'source_tables';
	let systemStatus = 'OPERATIONAL';
	let cpuUsage = 32.5;
	let gpuUsage = 60.4;
	let ramUsage = 51.8;
	let networkUsage = 80.5;

	let modules = [
		{ id: 'source_tables', name: 'SOURCE INTEL', color: '#00ffff', icon: '◈' },
		{ id: 'domain_metrics', name: '1DC vs FEAD', color: '#ff00ff', icon: '◆' },
		{ id: 'infrastructure_type', name: 'INFRASTRUCTURE', color: '#0096ff', icon: '⬢' },
		{ id: 'region_metrics', name: 'GLOBAL REGIONS', color: '#00ffff', icon: '◉' },
		{ id: 'country_metrics', name: 'COUNTRY SCAN', color: '#ff00ff', icon: '⬟' },
		{ id: 'data_center', name: 'DATA CENTERS', color: '#0096ff', icon: '⬡' },
		{ id: 'cloud_region', name: 'CLOUD MATRIX', color: '#00ffff', icon: '◯' },
		{ id: 'class_metrics', name: 'CLASS ANALYSIS', color: '#ff00ff', icon: '◐' },
		{ id: 'system_classification', name: 'SYSTEM TYPES', color: '#0096ff', icon: '◑' },
		{ id: 'business_unit', name: 'BUSINESS UNITS', color: '#00ffff', icon: '◒' },
		{ id: 'cio_metrics', name: 'CIO ANALYSIS', color: '#ff00ff', icon: '◓' },
		{ id: 'tanium_coverage', name: 'TANIUM', color: '#0096ff', icon: '⬠' },
		{ id: 'cmdb_presence', name: 'CMDB STATUS', color: '#00ffff', icon: '⬢' }
	];

	let currentTime = '';
	let systemLoad = 97.5;

	onMount(() => {
		let updateTime = () => {
			currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ') + 'Z';
		};
		updateTime();
		setInterval(updateTime, 1000);

		// Animate system metrics
		setInterval(() => {
			cpuUsage = 30 + Math.random() * 10;
			gpuUsage = 55 + Math.random() * 15;
			ramUsage = 45 + Math.random() * 20;
			networkUsage = 75 + Math.random() * 15;
			systemLoad = 95 + Math.random() * 5;
		}, 3000);
	});

	function switchView(moduleId) {
		currentView = moduleId;
	}

	function getCircularProgress(percentage) {
		const circumference = 2 * Math.PI * 45;
		const strokeDashoffset = circumference - (percentage / 100) * circumference;
		return { strokeDashoffset };
	}
</script>

<main class="cyberpunk-interface">
	<!-- Animated background particles -->
	<div class="matrix-rain">
		{#each Array(50) as _, i}
			<div class="rain-drop" style="left: {Math.random() * 100}%; animation-delay: {Math.random() * 5}s; animation-duration: {3 + Math.random() * 4}s;"></div>
		{/each}
	</div>

	<!-- Neural grid pattern -->
	<div class="neural-grid">
		{#each Array(20) as _, i}
			<div class="grid-line horizontal" style="top: {i * 5}%;"></div>
		{/each}
		{#each Array(20) as _, i}
			<div class="grid-line vertical" style="left: {i * 5}%;"></div>
		{/each}
	</div>

	<!-- Header with system metrics -->
	<header class="cyber-header">
		<div class="header-left">
			<div class="neural-logo">
				<div class="logo-rings">
					<div class="ring ring-outer"></div>
					<div class="ring ring-middle"></div>
					<div class="ring ring-inner"></div>
				</div>
				<div class="logo-center">◆</div>
			</div>
			<div class="system-title">
				<h1>DREAMGON</h1>
				<p>INTERACTIVE ARTS</p>
			</div>
		</div>

		<!-- System metrics display -->
		<div class="system-metrics">
			<div class="metric-group">
				<div class="metric-circle">
					<svg width="100" height="100" viewBox="0 0 100 100">
						<circle cx="50" cy="50" r="45" fill="none" stroke="rgba(0, 255, 255, 0.2)" stroke-width="2"/>
						<circle 
							cx="50" cy="50" r="45" 
							fill="none" 
							stroke="#00ffff" 
							stroke-width="3"
							stroke-dasharray="283"
							stroke-dashoffset={getCircularProgress(cpuUsage).strokeDashoffset}
							transform="rotate(-90 50 50)"
						/>
					</svg>
					<div class="metric-content">
						<div class="metric-value">{cpuUsage.toFixed(1)}%</div>
						<div class="metric-label">CPU</div>
						<div class="metric-sublabel">AMD Ryzen9 5950X</div>
					</div>
				</div>
				<div class="metric-details">
					<div class="detail-item">
						<span class="detail-label">CLOCK SPEED</span>
						<span class="detail-value">3.7 GHz</span>
					</div>
				</div>
			</div>

			<div class="metric-group">
				<div class="metric-circle">
					<svg width="100" height="100" viewBox="0 0 100 100">
						<circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255, 0, 255, 0.2)" stroke-width="2"/>
						<circle 
							cx="50" cy="50" r="45" 
							fill="none" 
							stroke="#ff00ff" 
							stroke-width="3"
							stroke-dasharray="283"
							stroke-dashoffset={getCircularProgress(gpuUsage).strokeDashoffset}
							transform="rotate(-90 50 50)"
						/>
					</svg>
					<div class="metric-content">
						<div class="metric-value">{gpuUsage.toFixed(1)}%</div>
						<div class="metric-label">GPU</div>
						<div class="metric-sublabel">GeForce RTX 3080 Ti</div>
					</div>
				</div>
				<div class="metric-details">
					<div class="detail-item">
						<span class="detail-label">MEMORY</span>
						<span class="detail-value">8.91 GB</span>
					</div>
				</div>
			</div>

			<div class="metric-group">
				<div class="metric-circle">
					<svg width="100" height="100" viewBox="0 0 100 100">
						<circle cx="50" cy="50" r="45" fill="none" stroke="rgba(0, 150, 255, 0.2)" stroke-width="2"/>
						<circle 
							cx="50" cy="50" r="45" 
							fill="none" 
							stroke="#0096ff" 
							stroke-width="3"
							stroke-dasharray="283"
							stroke-dashoffset={getCircularProgress(ramUsage).strokeDashoffset}
							transform="rotate(-90 50 50)"
						/>
					</svg>
					<div class="metric-content">
						<div class="metric-value">{ramUsage.toFixed(1)}%</div>
						<div class="metric-label">RAM</div>
						<div class="metric-sublabel">64GB DDR4 RAM</div>
					</div>
				</div>
				<div class="metric-details">
					<div class="detail-item">
						<span class="detail-label">CLOCK SPEED</span>
						<span class="detail-value">3.0GHz</span>
					</div>
				</div>
			</div>

			<div class="metric-group">
				<div class="metric-circle">
					<svg width="100" height="100" viewBox="0 0 100 100">
						<circle cx="50" cy="50" r="45" fill="none" stroke="rgba(0, 255, 255, 0.2)" stroke-width="2"/>
						<circle 
							cx="50" cy="50" r="45" 
							fill="none" 
							stroke="#00ffff" 
							stroke-width="3"
							stroke-dasharray="283"
							stroke-dashoffset={getCircularProgress(networkUsage).strokeDashoffset}
							transform="rotate(-90 50 50)"
						/>
					</svg>
					<div class="metric-content">
						<div class="metric-value">{networkUsage.toFixed(1)}</div>
						<div class="metric-label">ETHERNET</div>
						<div class="metric-sublabel">195.2 Mbits</div>
					</div>
				</div>
				<div class="metric-details">
					<div class="detail-item">
						<span class="detail-label">DATA</span>
					</div>
				</div>
			</div>
		</div>

		<div class="header-right">
			<div class="status-panel">
				<div class="status-ring operational"></div>
				<div class="status-info">
					<div class="status-item">
						<span class="status-label">STATUS</span>
						<span class="status-value operational">{systemStatus}</span>
					</div>
					<div class="status-item">
						<span class="status-label">TIME</span>
						<span class="status-value">{currentTime}</span>
					</div>
				</div>
			</div>
		</div>
	</header>

	<!-- Task manager and system controls -->
	<div class="task-manager">
		<div class="task-section">
			<div class="section-header">
				<span class="header-icon">◈</span>
				<span>TASK MANAGER</span>
			</div>
			<div class="progress-bar">
				<div class="progress-label">SYSTEM</div>
				<div class="progress-track">
					<div class="progress-fill" style="width: {systemLoad}%"></div>
				</div>
				<div class="progress-value">{systemLoad}% loading...</div>
			</div>
			<div class="progress-bar">
				<div class="progress-label">UPDATE</div>
				<div class="progress-track">
					<div class="progress-fill" style="width: 33.9%"></div>
				</div>
				<div class="progress-value">33.9% loading...</div>
			</div>
		</div>

		<div class="source-section">
			<div class="section-header">
				<span class="header-icon">◯</span>
				<span>SOURCE</span>
			</div>
			<div class="source-info">
				FILE: /users.mjs
			</div>
		</div>

		<div class="settings-grid">
			<div class="settings-header">SETTINGS</div>
			<div class="setting-nodes">
				{#each Array(10) as _, i}
					<div class="setting-node" style="--delay: {i * 0.1}s">
						<div class="node-ring"></div>
						<div class="node-value">{(Math.random() * 10).toFixed(1)}</div>
					</div>
				{/each}
			</div>
		</div>
	</div>

	<!-- Navigation modules -->
	<nav class="module-nav">
		{#each modules as module, i}
			<button 
				class="nav-module {currentView === module.id ? 'active' : ''}"
				style="--module-color: {module.color}; --delay: {i * 0.1}s"
				on:click={() => switchView(module.id)}
			>
				<div class="module-icon">{module.icon}</div>
				<div class="module-name">{module.name}</div>
				<div class="module-glow"></div>
			</button>
		{/each}
	</nav>

	<!-- Main content viewport -->
	<section class="data-viewport">
		<div class="viewport-frame">
			<div class="frame-corners">
				<div class="corner tl"></div>
				<div class="corner tr"></div>
				<div class="corner bl"></div>
				<div class="corner br"></div>
			</div>
			
			<div class="content-stream">
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
			</div>
		</div>
	</section>

	<!-- Volume controls -->
	<div class="volume-controls">
		<div class="volume-header">VOLUME</div>
		<div class="volume-sliders">
			{#each ['MASTER', 'AUX 1', 'AUX 2', 'LINEAR', 'STEREO', 'INTRO'] as channel}
				<div class="volume-slider">
					<div class="slider-track">
						<div class="slider-fill" style="height: {Math.random() * 100}%"></div>
					</div>
					<div class="slider-label">{channel}</div>
				</div>
			{/each}
		</div>
	</div>
</main>

<style>
	:global(body) {
		font-family: 'Orbitron', 'Exo 2', 'Rajdhani', monospace;
		background: #000;
		color: #fff;
		overflow: hidden;
		margin: 0;
		padding: 0;
	}

	.cyberpunk-interface {
		width: 100vw;
		height: 100vh;
		position: relative;
		display: grid;
		grid-template-areas: 
			"header header header"
			"task nav content"
			"volume nav content";
		grid-template-columns: 300px 200px 1fr;
		grid-template-rows: auto 1fr auto;
		background: radial-gradient(ellipse at center, #1a0d2e 0%, #0f0520 40%, #000000 100%);
		overflow: hidden;
	}

	.matrix-rain {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
	}

	.rain-drop {
		position: absolute;
		width: 2px;
		height: 20px;
		background: linear-gradient(180deg, transparent, #00ffff, transparent);
		animation: rainfall linear infinite;
		opacity: 0.3;
	}

	@keyframes rainfall {
		0% { transform: translateY(-100vh); }
		100% { transform: translateY(100vh); }
	}

	.neural-grid {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
		opacity: 0.1;
	}

	.grid-line {
		position: absolute;
		background: linear-gradient(90deg, transparent, #00ffff, transparent);
	}

	.grid-line.horizontal {
		width: 100%;
		height: 1px;
	}

	.grid-line.vertical {
		height: 100%;
		width: 1px;
		background: linear-gradient(180deg, transparent, #00ffff, transparent);
	}

	.cyber-header {
		grid-area: header;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(26, 13, 46, 0.8));
		border-bottom: 2px solid #00ffff;
		backdrop-filter: blur(20px);
		z-index: 10;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 2rem;
		position: relative;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.neural-logo {
		position: relative;
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.logo-rings {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.ring {
		position: absolute;
		border-radius: 50%;
		border: 2px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: ringRotate 8s linear infinite;
	}

	.ring-outer {
		width: 60px;
		height: 60px;
		border-color: #00ffff;
		opacity: 0.8;
	}

	.ring-middle {
		width: 45px;
		height: 45px;
		border-color: #ff00ff;
		opacity: 0.6;
		animation-direction: reverse;
		animation-duration: 6s;
	}

	.ring-inner {
		width: 30px;
		height: 30px;
		border-color: #0096ff;
		animation-duration: 4s;
	}

	.logo-center {
		font-size: 1.5rem;
		color: #00ffff;
		text-shadow: 0 0 20px #00ffff;
		z-index: 3;
		position: relative;
		animation: corePulse 3s ease-in-out infinite;
	}

	.system-title h1 {
		font-size: 1.5rem;
		font-weight: 700;
		color: #fff;
		margin: 0;
		text-shadow: 0 0 20px #00ffff;
		letter-spacing: 0.2em;
	}

	.system-title p {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		margin: 0;
		letter-spacing: 0.15em;
	}

	.system-metrics {
		display: flex;
		gap: 2rem;
		align-items: center;
	}

	.metric-group {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.metric-circle {
		position: relative;
		width: 100px;
		height: 100px;
	}

	.metric-circle svg {
		width: 100%;
		height: 100%;
	}

	.metric-content {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
	}

	.metric-value {
		font-size: 1.2rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 10px currentColor;
	}

	.metric-label {
		font-size: 0.8rem;
		font-weight: 700;
		color: #00ffff;
		letter-spacing: 0.1em;
	}

	.metric-sublabel {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.7);
		margin-top: 0.2rem;
	}

	.metric-details {
		text-align: center;
	}

	.detail-item {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.detail-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}

	.detail-value {
		font-size: 0.7rem;
		color: #00ffff;
		font-weight: 600;
	}

	.status-panel {
		display: flex;
		align-items: center;
		gap: 1rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.03));
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 8px;
		padding: 1rem;
		backdrop-filter: blur(10px);
	}

	.status-ring {
		width: 12px;
		height: 12px;
		border: 2px solid;
		border-radius: 50%;
		animation: statusPulse 2s ease-in-out infinite;
	}

	.status-ring.operational {
		border-color: #00ff85;
		box-shadow: 0 0 10px #00ff85;
	}

	.status-info {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.status-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.status-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.status-value {
		font-size: 0.7rem;
		font-weight: 600;
		color: #fff;
	}

	.status-value.operational {
		color: #00ff85;
		text-shadow: 0 0 8px #00ff85;
	}

	.task-manager {
		grid-area: task;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 255, 255, 0.02));
		border: 1px solid rgba(0, 255, 255, 0.2);
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		z-index: 5;
	}

	.section-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.8rem;
		font-weight: 700;
		color: #00ffff;
		letter-spacing: 0.1em;
		margin-bottom: 1rem;
	}

	.header-icon {
		font-size: 1rem;
		animation: iconFloat 2s ease-in-out infinite;
	}

	.progress-bar {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		margin-bottom: 1rem;
	}

	.progress-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.7);
		letter-spacing: 0.1em;
	}

	.progress-track {
		height: 8px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
		overflow: hidden;
		border: 1px solid rgba(0, 255, 255, 0.2);
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #00ffff, #0096ff);
		border-radius: 4px;
		transition: width 0.5s ease;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}

	.progress-value {
		font-size: 0.6rem;
		color: #00ffff;
		text-align: right;
	}

	.source-info {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
		background: rgba(0, 0, 0, 0.5);
		padding: 0.5rem;
		border-radius: 4px;
		border: 1px solid rgba(0, 255, 255, 0.2);
	}

	.settings-grid {
		flex: 1;
	}

	.settings-header {
		font-size: 0.8rem;
		font-weight: 700;
		color: #00ffff;
		letter-spacing: 0.1em;
		margin-bottom: 1rem;
	}

	.setting-nodes {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 0.8rem;
	}

	.setting-node {
		position: relative;
		width: 40px;
		height: 40px;
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.6);
		animation: nodeGlow 2s ease-in-out infinite;
		animation-delay: var(--delay);
	}

	.node-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 1px solid #00ffff;
		border-radius: 50%;
		animation: ringRotate 4s linear infinite;
		opacity: 0.3;
	}

	.node-value {
		font-size: 0.7rem;
		color: #00ffff;
		font-weight: 600;
		z-index: 2;
	}

	.module-nav {
		grid-area: nav;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		padding: 1rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(255, 0, 255, 0.02));
		border: 1px solid rgba(255, 0, 255, 0.2);
		z-index: 5;
		overflow-y: auto;
	}

	.nav-module {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.03));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 6px;
		padding: 0.8rem;
		color: #fff;
		font-family: inherit;
		font-size: 0.7rem;
		font-weight: 600;
		cursor: pointer;
		position: relative;
		transition: all 0.3s ease;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		animation: moduleEntrance 0.5s ease-out;
		animation-delay: var(--delay);
		animation-fill-mode: both;
		opacity: 0;
	}

	.nav-module:hover,
	.nav-module.active {
		border-color: var(--module-color);
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 255, 255, 0.05));
		transform: translateX(5px);
		box-shadow: 0 0 20px var(--module-color);
	}

	.module-icon {
		font-size: 1.2rem;
		color: var(--module-color);
		text-shadow: 0 0 10px var(--module-color);
	}

	.module-name {
		color: rgba(255, 255, 255, 0.9);
		text-align: center;
		line-height: 1.2;
	}

	.nav-module.active .module-name {
		color: var(--module-color);
		text-shadow: 0 0 8px var(--module-color);
	}

	.module-glow {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: radial-gradient(circle, var(--module-color), transparent);
		opacity: 0;
		transition: opacity 0.3s ease;
		border-radius: 6px;
	}

	.nav-module:hover .module-glow,
	.nav-module.active .module-glow {
		opacity: 0.1;
	}

	.data-viewport {
		grid-area: content;
		position: relative;
		z-index: 5;
		padding: 1rem;
		overflow: hidden;
	}

	.viewport-frame {
		position: relative;
		width: 100%;
		height: 100%;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(0, 255, 255, 0.02) 50%,
			rgba(255, 0, 255, 0.02) 100%);
		border: 2px solid #00ffff;
		border-radius: 16px;
		backdrop-filter: blur(20px);
		box-shadow: 
			0 0 40px rgba(0, 255, 255, 0.2),
			inset 0 0 20px rgba(0, 255, 255, 0.05);
		overflow: hidden;
	}

	.frame-corners {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
	}

	.corner {
		position: absolute;
		width: 30px;
		height: 30px;
		border: 3px solid #00ffff;
	}

	.corner.tl {
		top: 15px;
		left: 15px;
		border-right: none;
		border-bottom: none;
		border-top-left-radius: 8px;
	}

	.corner.tr {
		top: 15px;
		right: 15px;
		border-left: none;
		border-bottom: none;
		border-top-right-radius: 8px;
	}

	.corner.bl {
		bottom: 15px;
		left: 15px;
		border-right: none;
		border-top: none;
		border-bottom-left-radius: 8px;
	}

	.corner.br {
		bottom: 15px;
		right: 15px;
		border-left: none;
		border-top: none;
		border-bottom-right-radius: 8px;
	}

	.content-stream {
		position: relative;
		z-index: 2;
		width: 100%;
		height: 100%;
		padding: 2rem;
		overflow-y: auto;
	}

	.volume-controls {
		grid-area: volume;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 150, 255, 0.02));
		border: 1px solid rgba(0, 150, 255, 0.2);
		padding: 1rem;
		z-index: 5;
	}

	.volume-header {
		font-size: 0.8rem;
		font-weight: 700;
		color: #0096ff;
		letter-spacing: 0.1em;
		margin-bottom: 1rem;
	}

	.volume-sliders {
		display: flex;
		gap: 1rem;
		justify-content: space-between;
	}

	.volume-slider {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.slider-track {
		width: 6px;
		height: 80px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 3px;
		position: relative;
		border: 1px solid rgba(0, 150, 255, 0.2);
	}

	.slider-fill {
		position: absolute;
		bottom: 0;
		width: 100%;
		background: linear-gradient(180deg, #0096ff, #00ffff);
		border-radius: 3px;
		transition: height 0.5s ease;
		box-shadow: 0 0 10px rgba(0, 150, 255, 0.5);
	}

	.slider-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.7);
		transform: rotate(-45deg);
		white-space: nowrap;
	}

	:global(::-webkit-scrollbar) {
		width: 8px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 4px;
	}

	:global(::-webkit-scrollbar-thumb) {
		background: linear-gradient(135deg, #00ffff, #ff00ff);
		border-radius: 4px;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, #ff00ff, #00ffff);
	}

	@keyframes ringRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes corePulse {
		0%, 100% { 
			opacity: 0.9; 
			transform: scale(1);
			text-shadow: 0 0 20px #00ffff;
		}
		50% { 
			opacity: 1; 
			transform: scale(1.05);
			text-shadow: 0 0 30px #00ffff;
		}
	}

	@keyframes statusPulse {
		0%, 100% { 
			opacity: 1; 
			box-shadow: 0 0 10px currentColor;
		}
		50% { 
			opacity: 0.7; 
			box-shadow: 0 0 20px currentColor;
		}
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-3px); }
	}

	@keyframes nodeGlow {
		0%, 100% { 
			border-color: rgba(0, 255, 255, 0.3);
			box-shadow: 0 0 5px rgba(0, 255, 255, 0.2);
		}
		50% { 
			border-color: rgba(0, 255, 255, 0.8);
			box-shadow: 0 0 15px rgba(0, 255, 255, 0.4);
		}
	}

	@keyframes moduleEntrance {
		0% { 
			opacity: 0; 
			transform: translateX(-20px);
		}
		100% { 
			opacity: 1; 
			transform: translateX(0);
		}
	}

	@media (max-width: 1200px) {
		.cyberpunk-interface {
			grid-template-areas: 
				"header header"
				"content content"
				"nav task";
			grid-template-columns: 1fr 1fr;
			grid-template-rows: auto 1fr auto;
		}

		.system-metrics {
			gap: 1rem;
		}

		.metric-circle {
			width: 80px;
			height: 80px;
		}

		.volume-controls {
			display: none;
		}
	}

	@media (max-width: 768px) {
		.cyber-header {
			flex-direction: column;
			gap: 1rem;
			padding: 1rem;
		}

		.system-metrics {
			flex-wrap: wrap;
			justify-content: center;
		}

		.cyberpunk-interface {
			grid-template-areas: 
				"header"
				"content"
				"nav";
			grid-template-columns: 1fr;
		}

		.task-manager {
			display: none;
		}
	}
</style>