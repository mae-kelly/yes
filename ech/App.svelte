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
		{ id: 'source_tables', name: 'SOURCE INTEL', icon: '◈', color: '#00ffff', desc: 'Data Source Analysis' },
		{ id: 'domain_metrics', name: 'DOMAIN MATRIX', icon: '◆', color: '#ff00ff', desc: '1DC vs FEAD Classification' },
		{ id: 'infrastructure_type', name: 'INFRA NODES', icon: '⬢', color: '#0096ff', desc: 'Infrastructure Mapping' },
		{ id: 'region_metrics', name: 'GEO SECTORS', icon: '◉', color: '#00ffff', desc: 'Global Regions' },
		{ id: 'country_metrics', name: 'NATION STATE', icon: '⬟', color: '#ff00ff', desc: 'Country Intelligence' },
		{ id: 'data_center', name: 'DATA CORES', icon: '⬡', color: '#0096ff', desc: 'Facility Networks' },
		{ id: 'cloud_region', name: 'CLOUD MATRIX', icon: '◯', color: '#00ffff', desc: 'Cloud Infrastructure' },
		{ id: 'class_metrics', name: 'CLASS CIPHER', icon: '◐', color: '#ff00ff', desc: 'Classification Analysis' },
		{ id: 'system_classification', name: 'SYS TAXONOMY', icon: '◑', color: '#0096ff', desc: 'System Types' },
		{ id: 'business_unit', name: 'BIZ UNITS', icon: '◒', color: '#00ffff', desc: 'Business Intelligence' },
		{ id: 'cio_metrics', name: 'CIO INTEL', icon: '◓', color: '#ff00ff', desc: 'Executive Analysis' },
		{ id: 'tanium_coverage', name: 'TANIUM NET', icon: '⬠', color: '#0096ff', desc: 'Agent Coverage' },
		{ id: 'cmdb_presence', name: 'CMDB STATUS', icon: '⬢', color: '#00ffff', desc: 'Database Presence' }
	];

	let currentTime = '';
	let particles = [];

	onMount(() => {
		const updateTime = () => {
			currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ') + 'Z';
		};
		updateTime();
		setInterval(updateTime, 1000);

		for (let i = 0; i < 50; i++) {
			particles.push({
				x: Math.random() * window.innerWidth,
				y: Math.random() * window.innerHeight,
				vx: (Math.random() - 0.5) * 0.5,
				vy: (Math.random() - 0.5) * 0.5,
				life: Math.random() * 100,
				maxLife: 100 + Math.random() * 200
			});
		}

		const animateParticles = () => {
			particles.forEach(particle => {
				particle.x += particle.vx;
				particle.y += particle.vy;
				particle.life++;

				if (particle.x < 0 || particle.x > window.innerWidth) particle.vx *= -1;
				if (particle.y < 0 || particle.y > window.innerHeight) particle.vy *= -1;

				if (particle.life > particle.maxLife) {
					particle.x = Math.random() * window.innerWidth;
					particle.y = Math.random() * window.innerHeight;
					particle.life = 0;
				}
			});
			requestAnimationFrame(animateParticles);
		};
		animateParticles();
	});

	function switchView(moduleId) {
		currentView = moduleId;
	}
</script>

<main class="holographic-interface">
	<div class="quantum-background"></div>
	<div class="neural-particles">
		{#each particles as particle}
			<div 
				class="particle-dot" 
				style="left: {particle.x}px; top: {particle.y}px; opacity: {1 - (particle.life / particle.maxLife)}"
			></div>
		{/each}
	</div>
	
	<header class="holo-header">
		<div class="header-core">
			<div class="neural-logo">
				<div class="logo-rings">
					<div class="ring ring-1"></div>
					<div class="ring ring-2"></div>
					<div class="ring ring-3"></div>
				</div>
				<div class="logo-center">
					<span class="core-symbol">◈</span>
				</div>
			</div>
			
			<div class="system-identity">
				<h1 class="main-title">AO1 HOLOGRAPHIC INTELLIGENCE</h1>
				<span class="sub-title">NEURAL THREAT ANALYSIS MATRIX</span>
			</div>
		</div>
		
		<div class="status-cluster">
			<div class="status-node">
				<div class="node-ring"></div>
				<div class="node-data">
					<span class="node-label">SYSTEM</span>
					<span class="node-value">{systemStatus}</span>
				</div>
			</div>
			<div class="status-node">
				<div class="node-ring"></div>
				<div class="node-data">
					<span class="node-label">CLEARANCE</span>
					<span class="node-value">COSMIC</span>
				</div>
			</div>
			<div class="status-node">
				<div class="node-ring"></div>
				<div class="node-data">
					<span class="node-label">NEURAL SYNC</span>
					<span class="node-value time-display">{currentTime}</span>
				</div>
			</div>
		</div>
	</header>

	<nav class="module-grid">
		{#each modules as module}
			<button 
				class="module-node {currentView === module.id ? 'active' : ''}"
				style="--module-color: {module.color}"
				on:click={() => switchView(module.id)}
			>
				<div class="node-hologram">
					<div class="holo-ring"></div>
					<div class="holo-core">
						<span class="module-icon">{module.icon}</span>
					</div>
				</div>
				<div class="node-info">
					<span class="module-name">{module.name}</span>
					<span class="module-desc">{module.desc}</span>
				</div>
				<div class="connection-lines">
					<div class="line line-1"></div>
					<div class="line line-2"></div>
				</div>
			</button>
		{/each}
	</nav>

	<section class="data-viewport">
		<div class="viewport-frame">
			<div class="frame-corners">
				<div class="corner corner-tl"></div>
				<div class="corner corner-tr"></div>
				<div class="corner corner-bl"></div>
				<div class="corner corner-br"></div>
			</div>
			
			<div class="data-stream">
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
</main>

<style>
	:global(body) {
		font-family: 'JetBrains Mono', monospace;
		background: radial-gradient(ellipse at center, #1a0d2e 0%, #0f0520 40%, #000000 100%);
		color: #ffffff;
		overflow-x: hidden;
		margin: 0;
		padding: 0;
	}

	.holographic-interface {
		width: 100vw;
		min-height: 100vh;
		position: relative;
		display: flex;
		flex-direction: column;
		background: transparent;
	}

	.quantum-background {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: 
			radial-gradient(circle at 15% 25%, rgba(0, 255, 255, 0.05) 0%, transparent 50%),
			radial-gradient(circle at 85% 75%, rgba(255, 0, 255, 0.03) 0%, transparent 50%),
			radial-gradient(circle at 50% 50%, rgba(0, 150, 255, 0.02) 0%, transparent 50%);
		animation: quantumShift 12s ease-in-out infinite alternate;
		pointer-events: none;
		z-index: 1;
	}

	@keyframes quantumShift {
		0% { 
			background: 
				radial-gradient(circle at 15% 25%, rgba(0, 255, 255, 0.05) 0%, transparent 50%),
				radial-gradient(circle at 85% 75%, rgba(255, 0, 255, 0.03) 0%, transparent 50%),
				radial-gradient(circle at 50% 50%, rgba(0, 150, 255, 0.02) 0%, transparent 50%);
		}
		100% { 
			background: 
				radial-gradient(circle at 85% 15%, rgba(0, 255, 255, 0.08) 0%, transparent 50%),
				radial-gradient(circle at 15% 85%, rgba(255, 0, 255, 0.06) 0%, transparent 50%),
				radial-gradient(circle at 70% 30%, rgba(0, 150, 255, 0.04) 0%, transparent 50%);
		}
	}

	.neural-particles {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 2;
	}

	.particle-dot {
		position: absolute;
		width: 1px;
		height: 1px;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.6), transparent);
		border-radius: 50%;
	}

	.holo-header {
		background: linear-gradient(135deg, 
			rgba(0, 255, 255, 0.08) 0%, 
			rgba(0, 150, 255, 0.06) 50%,
			rgba(255, 0, 255, 0.08) 100%);
		border-bottom: 1px solid rgba(0, 255, 255, 0.2);
		backdrop-filter: blur(20px);
		padding: 1rem 2rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		position: relative;
		z-index: 10;
		box-shadow: 
			0 4px 32px rgba(0, 255, 255, 0.1),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
	}

	.header-core {
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
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
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
		width: 60px;
		height: 60px;
		border-color: rgba(0, 255, 255, 0.6);
		animation: logoRotate1 8s linear infinite;
	}

	.ring-2 {
		width: 45px;
		height: 45px;
		border-color: rgba(255, 0, 255, 0.4);
		animation: logoRotate2 6s linear infinite reverse;
	}

	.ring-3 {
		width: 30px;
		height: 30px;
		border-color: rgba(0, 150, 255, 0.8);
		animation: logoRotate3 4s linear infinite;
	}

	.logo-center {
		position: relative;
		z-index: 3;
		width: 20px;
		height: 20px;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.3), transparent);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.core-symbol {
		font-size: 1.2rem;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
		animation: symbolPulse 3s ease-in-out infinite;
	}

	.system-identity {
		display: flex;
		flex-direction: column;
	}

	.main-title {
		font-size: 1.4rem;
		font-weight: 700;
		color: #ffffff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.05em;
		margin: 0;
	}

	.sub-title {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 300;
		letter-spacing: 0.1em;
		margin-top: 0.25rem;
	}

	.status-cluster {
		display: flex;
		gap: 2rem;
	}

	.status-node {
		position: relative;
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.75rem 1.25rem;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.3) 0%, 
			rgba(0, 255, 255, 0.05) 100%);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 8px;
		backdrop-filter: blur(10px);
	}

	.node-ring {
		width: 12px;
		height: 12px;
		border: 2px solid rgba(0, 255, 255, 0.8);
		border-radius: 50%;
		animation: nodeRingPulse 2s ease-in-out infinite;
	}

	.node-data {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
	}

	.node-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 400;
		letter-spacing: 0.05em;
		margin-bottom: 0.1rem;
	}

	.node-value {
		font-size: 0.8rem;
		font-weight: 600;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}

	.time-display {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.module-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1rem;
		padding: 1.5rem 2rem;
		z-index: 5;
		max-height: 25vh;
		overflow-y: auto;
	}

	.module-node {
		position: relative;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.4) 0%, 
			rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
		backdrop-filter: blur(20px);
		display: flex;
		align-items: center;
		gap: 1rem;
		overflow: hidden;
	}

	.module-node::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(255, 255, 255, 0.05), 
			transparent);
		transition: left 0.6s ease;
	}

	.module-node:hover::before {
		left: 100%;
	}

	.module-node:hover {
		border-color: var(--module-color);
		box-shadow: 
			0 8px 32px rgba(0, 0, 0, 0.3),
			0 0 20px rgba(0, 255, 255, 0.2);
		transform: translateY(-2px);
	}

	.module-node.active {
		border-color: var(--module-color);
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(255, 255, 255, 0.05) 100%);
		box-shadow: 
			0 0 30px rgba(0, 255, 255, 0.3),
			inset 0 0 20px rgba(0, 255, 255, 0.05);
	}

	.node-hologram {
		position: relative;
		width: 50px;
		height: 50px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.holo-ring {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		border: 2px solid var(--module-color);
		border-radius: 50%;
		opacity: 0.3;
		animation: holoRingRotate 4s linear infinite;
	}

	.holo-core {
		position: relative;
		z-index: 2;
		width: 30px;
		height: 30px;
		background: radial-gradient(circle, var(--module-color), transparent);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		opacity: 0.8;
	}

	.module-icon {
		font-size: 1.2rem;
		color: var(--module-color);
		text-shadow: 0 0 15px var(--module-color);
	}

	.node-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.module-name {
		font-size: 0.9rem;
		font-weight: 700;
		color: #ffffff;
		letter-spacing: 0.02em;
	}

	.module-desc {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 300;
	}

	.connection-lines {
		position: absolute;
		right: 0;
		top: 0;
		width: 30px;
		height: 100%;
		pointer-events: none;
	}

	.line {
		position: absolute;
		right: 10px;
		width: 20px;
		height: 1px;
		background: linear-gradient(90deg, 
			var(--module-color), 
			transparent);
		opacity: 0.3;
		animation: connectionPulse 3s ease-in-out infinite;
	}

	.line-1 {
		top: 30%;
		animation-delay: 0s;
	}

	.line-2 {
		top: 70%;
		animation-delay: 1.5s;
	}

	.data-viewport {
		flex: 1;
		padding: 1.5rem 2rem 2rem;
		position: relative;
		z-index: 5;
	}

	.viewport-frame {
		position: relative;
		width: 100%;
		height: 100%;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.4) 0%, 
			rgba(0, 255, 255, 0.02) 50%,
			rgba(255, 0, 255, 0.02) 100%);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 16px;
		backdrop-filter: blur(20px);
		box-shadow: 
			0 8px 32px rgba(0, 0, 0, 0.3),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
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
		width: 20px;
		height: 20px;
		border: 2px solid rgba(0, 255, 255, 0.6);
	}

	.corner-tl {
		top: 10px;
		left: 10px;
		border-right: none;
		border-bottom: none;
		border-top-left-radius: 4px;
	}

	.corner-tr {
		top: 10px;
		right: 10px;
		border-left: none;
		border-bottom: none;
		border-top-right-radius: 4px;
	}

	.corner-bl {
		bottom: 10px;
		left: 10px;
		border-right: none;
		border-top: none;
		border-bottom-left-radius: 4px;
	}

	.corner-br {
		bottom: 10px;
		right: 10px;
		border-left: none;
		border-top: none;
		border-bottom-right-radius: 4px;
	}

	.data-stream {
		position: relative;
		z-index: 2;
		width: 100%;
		height: 100%;
		padding: 2rem;
		overflow-y: auto;
	}

	:global(::-webkit-scrollbar) {
		width: 8px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 4px;
	}

	:global(::-webkit-scrollbar-thumb) {
		background: linear-gradient(135deg, 
			rgba(0, 255, 255, 0.6), 
			rgba(255, 0, 255, 0.4));
		border-radius: 4px;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, 
			rgba(0, 255, 255, 0.8), 
			rgba(255, 0, 255, 0.6));
	}

	@keyframes logoRotate1 {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes logoRotate2 {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(-360deg); }
	}

	@keyframes logoRotate3 {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes symbolPulse {
		0%, 100% { opacity: 0.9; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.1); }
	}

	@keyframes nodeRingPulse {
		0%, 100% { 
			border-color: rgba(0, 255, 255, 0.8); 
			box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
		}
		50% { 
			border-color: rgba(0, 255, 255, 1); 
			box-shadow: 0 0 20px rgba(0, 255, 255, 0.6);
		}
	}

	@keyframes holoRingRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes connectionPulse {
		0%, 100% { opacity: 0.3; }
		50% { opacity: 0.8; }
	}

	@media (max-width: 768px) {
		.holo-header {
			flex-direction: column;
			gap: 1rem;
			padding: 1rem;
		}

		.status-cluster {
			gap: 1rem;
		}

		.module-grid {
			grid-template-columns: 1fr;
			padding: 1rem;
		}

		.data-viewport {
			padding: 1rem;
		}
	}
</style>