<script>
	import { onMount } from 'svelte';
	import GlobalView from './GlobalView.svelte';
	import InfrastructureType from './InfrastructureType.svelte';
	import BUApplicationView from './BUApplicationView.svelte';
	import SystemClassification from './SystemClassification.svelte';
	import SecurityControlCoverage from './SecurityControlCoverage.svelte';
	import LoggingCompliance from './LoggingCompliance.svelte';
	import DomainVisibility from './DomainVisibility.svelte';

	let currentView = 'global_view';
	let currentTime = '';
	let systemStatus = 'INITIALIZING';
	
	let modules = [
		{ id: 'global_view', name: 'GLOBAL VIEW', color: '#00ffff', icon: '🌐', description: 'Regional & Country Visibility' },
		{ id: 'infrastructure_type', name: 'INFRASTRUCTURE', color: '#ff00ff', icon: '⬢', description: 'On-Prem, Cloud, SaaS, API' },
		{ id: 'bu_application', name: 'BU & APPLICATION', color: '#0096ff', icon: '◈', description: 'Business Unit & CIO View' },
		{ id: 'system_classification', name: 'SYSTEM CLASS', color: '#00ff85', icon: '◑', description: 'Windows, Linux, *Nix, Mainframe' },
		{ id: 'security_control', name: 'SECURITY CONTROL', color: '#ff0066', icon: '🛡️', description: 'EDR, Tanium, DLP Coverage' },
		{ id: 'logging_compliance', name: 'LOGGING', color: '#ffaa00', icon: '📊', description: 'GSO & Splunk Compliance' },
		{ id: 'domain_visibility', name: 'DOMAIN', color: '#00ffff', icon: '◆', description: '1DC vs FEAD Analysis' }
	];

	onMount(() => {
		const updateTime = () => {
			const now = new Date();
			currentTime = now.toISOString().slice(0, 19).replace('T', ' ') + 'Z';
		};
		updateTime();
		const interval = setInterval(updateTime, 1000);
		
		setTimeout(() => {
			systemStatus = 'OPERATIONAL';
		}, 2000);
		
		return () => clearInterval(interval);
	});

	function switchView(moduleId) {
		currentView = moduleId;
	}
</script>

<main class="ao1-interface">
	<div class="matrix-rain">
		{#each Array(30) as _, i}
			<div class="rain-drop" style="left: {Math.random() * 100}%; animation-delay: {Math.random() * 5}s; animation-duration: {3 + Math.random() * 4}s;"></div>
		{/each}
	</div>

	<header class="system-header">
		<div class="header-content">
			<div class="brand-section">
				<div class="ao1-logo">
					<div class="logo-rings">
						<div class="ring ring-outer"></div>
						<div class="ring ring-middle"></div>
						<div class="ring ring-inner"></div>
					</div>
					<div class="logo-center">AO1</div>
				</div>
				<div class="brand-text">
					<h1 class="title">LOG VISIBILITY MEASUREMENT</h1>
					<span class="subtitle">FISERV CSOC NEURAL THREAT INTELLIGENCE</span>
				</div>
			</div>
			
			<div class="status-panel">
				<div class="status-indicator {systemStatus === 'OPERATIONAL' ? 'active' : 'initializing'}">
					<div class="indicator-light"></div>
					<span class="status-text">{systemStatus}</span>
				</div>
				<div class="time-display">
					<span class="time-label">SYSTEM TIME</span>
					<span class="time-value">{currentTime}</span>
				</div>
			</div>
		</div>
		
		<nav class="module-navigation">
			{#each modules as module}
				<button 
					class="nav-module {currentView === module.id ? 'active' : ''}"
					style="--module-color: {module.color}"
					on:click={() => switchView(module.id)}
				>
					<span class="module-icon">{module.icon}</span>
					<div class="module-info">
						<span class="module-name">{module.name}</span>
						<span class="module-desc">{module.description}</span>
					</div>
					{#if currentView === module.id}
						<div class="active-indicator"></div>
					{/if}
				</button>
			{/each}
		</nav>
	</header>

	<section class="data-viewport">
		<div class="viewport-frame">
			<div class="frame-corners">
				<div class="corner tl"></div>
				<div class="corner tr"></div>
				<div class="corner bl"></div>
				<div class="corner br"></div>
			</div>
			
			<div class="content-stream">
				{#if currentView === 'global_view'}
					<GlobalView />
				{:else if currentView === 'infrastructure_type'}
					<InfrastructureType />
				{:else if currentView === 'bu_application'}
					<BUApplicationView />
				{:else if currentView === 'system_classification'}
					<SystemClassification />
				{:else if currentView === 'security_control'}
					<SecurityControlCoverage />
				{:else if currentView === 'logging_compliance'}
					<LoggingCompliance />
				{:else if currentView === 'domain_visibility'}
					<DomainVisibility />
				{/if}
			</div>
		</div>
	</section>
</main>

<style>
	:global(body) {
		font-family: 'Orbitron', 'JetBrains Mono', monospace;
		background: #000;
		color: #fff;
		overflow: hidden;
		margin: 0;
		padding: 0;
		font-size: 14px;
		line-height: 1.4;
	}

	.ao1-interface {
		width: 100vw;
		height: 100vh;
		position: fixed;
		top: 0;
		left: 0;
		display: flex;
		flex-direction: column;
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
		opacity: 0.15;
	}

	@keyframes rainfall {
		0% { transform: translateY(-100vh); }
		100% { transform: translateY(100vh); }
	}

	.system-header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.95), rgba(26, 13, 46, 0.85));
		border-bottom: 2px solid #00ffff;
		backdrop-filter: blur(25px);
		z-index: 10;
		position: relative;
		box-shadow: 0 4px 30px rgba(0, 255, 255, 0.2);
		flex-shrink: 0;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
	}

	.brand-section {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.ao1-logo {
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
		border-color: rgba(0, 255, 255, 0.6);
	}

	.ring-middle {
		width: 45px;
		height: 45px;
		border-color: rgba(255, 0, 255, 0.4);
		animation-direction: reverse;
		animation-duration: 6s;
	}

	.ring-inner {
		width: 30px;
		height: 30px;
		border-color: rgba(0, 150, 255, 0.8);
		animation-duration: 4s;
	}

	.logo-center {
		font-size: 1rem;
		font-weight: 700;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.8);
		z-index: 3;
		position: relative;
		animation: corePulse 3s ease-in-out infinite;
		letter-spacing: 0.1em;
	}

	.brand-text {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.title {
		font-size: 1.3rem;
		font-weight: 700;
		color: #ffffff;
		margin: 0;
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.subtitle {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.status-panel {
		display: flex;
		align-items: center;
		gap: 2rem;
	}

	.status-indicator {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.05));
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 6px;
		backdrop-filter: blur(10px);
	}

	.indicator-light {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: #ff0066;
		animation: statusPulse 2s ease-in-out infinite;
	}

	.status-indicator.active .indicator-light {
		background: #00ff85;
		box-shadow: 0 0 10px #00ff85;
	}

	.status-text {
		font-size: 0.7rem;
		font-weight: 600;
		color: #00ffff;
		letter-spacing: 0.05em;
	}

	.time-display {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.time-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.time-value {
		font-size: 0.8rem;
		font-weight: 600;
		color: #00ffff;
		text-shadow: 0 0 8px rgba(0, 255, 255, 0.5);
	}

	.module-navigation {
		display: flex;
		gap: 0.5rem;
		padding: 0.5rem 1.5rem;
		background: rgba(0, 0, 0, 0.3);
		overflow-x: auto;
	}

	.nav-module {
		position: relative;
		display: flex;
		align-items: center;
		gap: 0.8rem;
		padding: 0.8rem 1.2rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		color: rgba(255, 255, 255, 0.7);
		cursor: pointer;
		transition: all 0.3s ease;
		white-space: nowrap;
	}

	.nav-module:hover {
		border-color: var(--module-color);
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.7), rgba(255, 255, 255, 0.05));
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
	}

	.nav-module.active {
		border-color: var(--module-color);
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 255, 255, 0.08));
		box-shadow: 0 0 25px rgba(0, 255, 255, 0.2);
	}

	.module-icon {
		font-size: 1.5rem;
		filter: drop-shadow(0 0 8px var(--module-color));
	}

	.module-info {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.module-name {
		font-size: 0.8rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.module-desc {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
	}

	.active-indicator {
		position: absolute;
		bottom: -2px;
		left: 0;
		right: 0;
		height: 3px;
		background: var(--module-color);
		box-shadow: 0 0 10px var(--module-color);
		animation: indicatorGlow 2s ease-in-out infinite;
	}

	.data-viewport {
		flex: 1;
		position: relative;
		z-index: 5;
		padding: 1rem;
		overflow: hidden;
		min-height: 0;
	}

	.viewport-frame {
		position: relative;
		width: 100%;
		height: 100%;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.4) 0%, 
			rgba(0, 255, 255, 0.02) 50%,
			rgba(255, 0, 255, 0.02) 100%);
		border: 2px solid rgba(0, 255, 255, 0.2);
		border-radius: 10px;
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

	.corner.tl {
		top: 10px;
		left: 10px;
		border-right: none;
		border-bottom: none;
		border-top-left-radius: 4px;
	}

	.corner.tr {
		top: 10px;
		right: 10px;
		border-left: none;
		border-bottom: none;
		border-top-right-radius: 4px;
	}

	.corner.bl {
		bottom: 10px;
		left: 10px;
		border-right: none;
		border-top: none;
		border-bottom-left-radius: 4px;
	}

	.corner.br {
		bottom: 10px;
		right: 10px;
		border-left: none;
		border-top: none;
		border-bottom-right-radius: 4px;
	}

	.content-stream {
		position: relative;
		z-index: 2;
		width: 100%;
		height: 100%;
		padding: 1.5rem;
		overflow-y: auto;
		overflow-x: hidden;
	}

	@keyframes ringRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes corePulse {
		0%, 100% { 
			opacity: 0.9; 
			transform: scale(1);
		}
		50% { 
			opacity: 1; 
			transform: scale(1.05);
		}
	}

	@keyframes statusPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	@keyframes indicatorGlow {
		0%, 100% { opacity: 0.8; }
		50% { opacity: 1; }
	}
</style>