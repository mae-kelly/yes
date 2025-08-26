<!-- ech/App.svelte -->
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

	const modules = [
		{ id: 'source_tables', name: 'SOURCE INTEL', icon: '◈', color: '#00D4FF' },
		{ id: 'domain_metrics', name: '1DC vs FEAD', icon: '◆', color: '#FF0080' },
		{ id: 'infrastructure_type', name: 'INFRASTRUCTURE', icon: '⬢', color: '#8B5CF6' },
		{ id: 'region_metrics', name: 'GLOBAL REGIONS', icon: '◉', color: '#00FF85' },
		{ id: 'country_metrics', name: 'COUNTRY INTEL', icon: '⬟', color: '#FFE500' },
		{ id: 'data_center', name: 'DATA CENTERS', icon: '⬡', color: '#FF4500' },
		{ id: 'cloud_region', name: 'CLOUD MATRIX', icon: '◯', color: '#00D4FF' },
		{ id: 'class_metrics', name: 'CLASS ANALYSIS', icon: '◐', color: '#FF0080' },
		{ id: 'system_classification', name: 'SYSTEM TYPES', icon: '◑', color: '#8B5CF6' },
		{ id: 'business_unit', name: 'BUSINESS UNITS', icon: '◒', color: '#00FF85' },
		{ id: 'cio_metrics', name: 'CIO INTELLIGENCE', icon: '◓', color: '#FFE500' },
		{ id: 'tanium_coverage', name: 'TANIUM AGENTS', icon: '⬠', color: '#FF4500' },
		{ id: 'cmdb_presence', name: 'CMDB STATUS', icon: '⬢', color: '#00D4FF' }
	];

	let currentTime = '';

	onMount(() => {
		const updateTime = () => {
			currentTime = new Date().toISOString().slice(0, 19) + 'Z';
		};
		updateTime();
		setInterval(updateTime, 1000);
	});

	function switchView(moduleId) {
		currentView = moduleId;
	}
</script>

<main class="cyber-terminal">
	<div class="hex-background"></div>
	<div class="neural-particles"></div>
	
	<header class="cyber-header">
		<div class="header-left">
			<div class="neural-brand">
				<div class="brand-core">
					<span class="core-icon">◈</span>
					<div class="core-rings">
						<div class="ring ring-1"></div>
						<div class="ring ring-2"></div>
						<div class="ring ring-3"></div>
					</div>
				</div>
				<div class="brand-text">
					<h1 class="main-title">AO1 NEURAL INTELLIGENCE</h1>
					<span class="sub-title">CSOC VISIBILITY MATRIX</span>
				</div>
			</div>
			
			<nav class="inline-nav">
				<div class="nav-modules">
					{#each modules as module}
						<button 
							class="nav-tab {currentView === module.id ? 'active' : ''}"
							style="--module-color: {module.color}"
							on:click={() => switchView(module.id)}
						>
							<span class="tab-icon">{module.icon}</span>
							<span class="tab-name">{module.name}</span>
							<div class="tab-glow"></div>
						</button>
					{/each}
				</div>
			</nav>
		</div>
		
		<div class="header-right">
			<div class="system-metrics">
				<div class="metric-pod">
					<span class="metric-label">STATUS</span>
					<span class="metric-value status-operational">{systemStatus}</span>
				</div>
				<div class="metric-pod">
					<span class="metric-label">CLEARANCE</span>
					<span class="metric-value">TOP SECRET</span>
				</div>
				<div class="metric-pod">
					<span class="metric-label">NEURAL LINK</span>
					<span class="metric-value neural-time">{currentTime}</span>
				</div>
			</div>
			
			<div class="classification-banner">
				<div class="class-indicator"></div>
				<span class="class-text">CLASSIFIED</span>
			</div>
		</div>
	</header>

	<section class="cyber-workspace">
		<div class="workspace-header">
			<div class="current-module">
				<span class="module-breadcrumb">NEURAL MATRIX /</span>
				<span class="module-current">{modules.find(m => m.id === currentView)?.name || 'UNKNOWN'}</span>
			</div>
			
			<div class="workspace-controls">
				<button class="cyber-button refresh-btn" on:click={() => location.reload()}>
					<span class="btn-icon">⟲</span>
					<span class="btn-text">REFRESH</span>
				</button>
				
				<div class="connection-status">
					<div class="status-pulse"></div>
					<span class="status-text">QUANTUM LINK ACTIVE</span>
				</div>
			</div>
		</div>

		<div class="workspace-content">
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
	</section>
</main>

<style>
	:global(body) {
		font-family: 'JetBrains Mono', monospace;
		background: #000;
		color: #fff;
		overflow: hidden;
		margin: 0;
		padding: 0;
	}

	.cyber-terminal {
		width: 100vw;
		height: 100vh;
		background: radial-gradient(ellipse at center, #001122 0%, #000000 100%);
		position: relative;
		display: flex;
		flex-direction: column;
	}

	.hex-background {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background-image: 
			radial-gradient(circle at 20px 20px, rgba(0, 212, 255, 0.03) 1px, transparent 1px),
			radial-gradient(circle at 60px 60px, rgba(255, 0, 128, 0.03) 1px, transparent 1px);
		background-size: 40px 40px;
		animation: hexShift 30s linear infinite;
		pointer-events: none;
		z-index: 1;
	}

	.neural-particles {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 2;
		background: 
			radial-gradient(2px 2px at 100px 150px, #00D4FF, transparent),
			radial-gradient(2px 2px at 400px 50px, #FF0080, transparent),
			radial-gradient(1px 1px at 300px 300px, #8B5CF6, transparent),
			radial-gradient(1px 1px at 800px 200px, #00FF85, transparent);
		animation: particleFloat 25s ease-in-out infinite;
	}

	.cyber-header {
		background: linear-gradient(135deg, rgba(0, 20, 40, 0.95) 0%, rgba(0, 10, 20, 0.95) 100%);
		border-bottom: 1px solid rgba(0, 212, 255, 0.3);
		padding: 0.5rem 1.5rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		backdrop-filter: blur(20px);
		position: relative;
		z-index: 10;
		box-shadow: 0 4px 32px rgba(0, 212, 255, 0.1);
		height: 70px;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 2rem;
		flex: 1;
	}

	.neural-brand {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-shrink: 0;
	}

	.brand-core {
		position: relative;
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.core-icon {
		color: #00D4FF;
		font-size: 1.5rem;
		z-index: 3;
		position: relative;
		animation: coreRotate 8s linear infinite;
	}

	.core-rings {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
	}

	.ring {
		position: absolute;
		border-radius: 50%;
		border: 1px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
	}

	.ring-1 {
		width: 30px;
		height: 30px;
		border-color: rgba(0, 212, 255, 0.4);
		animation: ringRotate1 6s linear infinite;
	}

	.ring-2 {
		width: 38px;
		height: 38px;
		border-color: rgba(255, 0, 128, 0.3);
		animation: ringRotate2 8s linear infinite reverse;
	}

	.ring-3 {
		width: 46px;
		height: 46px;
		border-color: rgba(139, 92, 246, 0.2);
		animation: ringRotate3 10s linear infinite;
	}

	.brand-text {
		display: flex;
		flex-direction: column;
	}

	.main-title {
		font-size: 1.1rem;
		font-weight: 700;
		color: #fff;
		margin: 0;
		text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.sub-title {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 400;
		letter-spacing: 0.1em;
		margin-top: 0.25rem;
	}

	.inline-nav {
		flex: 1;
		margin-left: 2rem;
	}

	.nav-modules {
		display: flex;
		gap: 0.5rem;
		overflow-x: auto;
		padding: 0.25rem 0;
	}

	.nav-tab {
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 6px;
		padding: 0.4rem 0.8rem;
		color: #fff;
		font-family: inherit;
		font-size: 0.7rem;
		font-weight: 500;
		cursor: pointer;
		position: relative;
		display: flex;
		align-items: center;
		gap: 0.4rem;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		white-space: nowrap;
		overflow: hidden;
	}

	.nav-tab:hover {
		border-color: var(--module-color);
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.04) 100%);
		transform: translateY(-1px);
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
	}

	.nav-tab.active {
		border-color: var(--module-color);
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
		box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
	}

	.tab-icon {
		font-size: 1rem;
		color: var(--module-color);
		z-index: 2;
		position: relative;
	}

	.tab-name {
		color: #fff;
		font-weight: 600;
		letter-spacing: 0.02em;
		z-index: 2;
		position: relative;
	}

	.tab-glow {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 100%;
		height: 100%;
		background: radial-gradient(circle, var(--module-color), transparent);
		opacity: 0;
		transition: opacity 0.3s ease;
		border-radius: 6px;
	}

	.nav-tab:hover .tab-glow,
	.nav-tab.active .tab-glow {
		opacity: 0.08;
	}

	.header-right {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		flex-shrink: 0;
	}

	.system-metrics {
		display: flex;
		gap: 1rem;
	}

	.metric-pod {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.2rem;
	}

	.metric-label {
		font-size: 0.55rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 400;
		letter-spacing: 0.1em;
	}

	.metric-value {
		font-size: 0.7rem;
		font-weight: 600;
		color: #fff;
	}

	.status-operational {
		color: #00FF85;
		text-shadow: 0 0 10px rgba(0, 255, 133, 0.5);
		animation: statusPulse 2s ease-in-out infinite;
	}

	.neural-time {
		color: #00D4FF;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.6rem;
	}

	.classification-banner {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.4rem 0.8rem;
		background: linear-gradient(45deg, rgba(255, 0, 128, 0.1), rgba(255, 69, 0, 0.1));
		border: 1px solid rgba(255, 0, 128, 0.3);
		border-radius: 4px;
		backdrop-filter: blur(10px);
	}

	.class-indicator {
		width: 6px;
		height: 6px;
		background: #FF0080;
		border-radius: 50%;
		animation: classificationPulse 1.5s ease-in-out infinite;
	}

	.class-text {
		font-size: 0.6rem;
		color: #FF0080;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.cyber-nav {
		display: none;
	}

	.cyber-workspace {
		flex: 1;
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.3);
		position: relative;
		z-index: 8;
	}

	.workspace-header {
		background: linear-gradient(135deg, rgba(0, 10, 20, 0.9) 0%, rgba(0, 5, 10, 0.9) 100%);
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		padding: 1rem 1.5rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		backdrop-filter: blur(10px);
	}

	.current-module {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.module-breadcrumb {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 400;
	}

	.module-current {
		font-size: 1rem;
		color: #00D4FF;
		font-weight: 700;
		text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.workspace-controls {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.cyber-button {
		background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%);
		border: 1px solid rgba(0, 212, 255, 0.3);
		border-radius: 6px;
		color: #00D4FF;
		font-family: inherit;
		font-size: 0.8rem;
		font-weight: 600;
		padding: 0.5rem 1rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		transition: all 0.3s ease;
		letter-spacing: 0.05em;
	}

	.cyber-button:hover {
		background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(0, 212, 255, 0.1) 100%);
		box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
		transform: translateY(-1px);
	}

	.btn-icon {
		font-size: 1rem;
	}

	.connection-status {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.status-pulse {
		width: 8px;
		height: 8px;
		background: #00FF85;
		border-radius: 50%;
		animation: connectionPulse 1.5s ease-in-out infinite;
	}

	.status-text {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
		font-weight: 500;
		letter-spacing: 0.05em;
	}

	.workspace-content {
		flex: 1;
		padding: 1.5rem;
		overflow-y: auto;
		position: relative;
	}

	:global(::-webkit-scrollbar) {
		width: 8px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.3);
	}

	:global(::-webkit-scrollbar-thumb) {
		background: linear-gradient(135deg, #00D4FF, #8B5CF6);
		border-radius: 4px;
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, #FF0080, #00D4FF);
	}

	@keyframes hexShift {
		0% { transform: translate(0, 0); }
		100% { transform: translate(40px, 40px); }
	}

	@keyframes particleFloat {
		0%, 100% { opacity: 0.3; transform: translateY(0px); }
		50% { opacity: 0.6; transform: translateY(-20px); }
	}

	@keyframes coreRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes ringRotate1 {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes ringRotate2 {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(-360deg); }
	}

	@keyframes ringRotate3 {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes statusPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}

	@keyframes classificationPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.6; transform: scale(1.1); }
	}

	@keyframes moduleFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-3px); }
	}

	@keyframes statusDotPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.5; transform: scale(0.8); }
	}

	@keyframes connectionPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.6; transform: scale(1.2); }
	}
</style>