// ech/App.svelte
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
	import MatrixBackground from './MatrixBackground.svelte';

	let currentView = 'source_tables';
	let systemStatus = 'SHADOWNET_ONLINE';
	let threatLevel = 'DEFCON_2';
	let neuralSync = 100;

	const menuItems = [
		{ id: 'source_tables', label: 'GHOST_PROTOCOL', icon: '⧫', description: 'Spectral data interception', threat: 'CRITICAL' },
		{ id: 'domain_metrics', label: 'BLACKSITE_ANALYSIS', icon: '▲', description: 'Domain warfare intelligence', threat: 'HIGH' },
		{ id: 'infrastructure_type', label: 'DARKWEB_MATRIX', icon: '◈', description: 'Infrastructure penetration map', threat: 'CRITICAL' },
		{ id: 'region_metrics', label: 'GLOBAL_SHADOW', icon: '●', description: 'Worldwide surveillance grid', threat: 'HIGH' },
		{ id: 'country_metrics', label: 'NATION_STATE', icon: '▼', description: 'Geopolitical threat vectors', threat: 'EXTREME' },
		{ id: 'data_center', label: 'VAULT_NEXUS', icon: '■', description: 'Classified facility mapping', threat: 'TOP_SECRET' },
		{ id: 'cloud_region', label: 'SKYNET_OPS', icon: '◆', description: 'Cloud warfare deployment', threat: 'HIGH' },
		{ id: 'class_metrics', label: 'CIPHER_GRADE', icon: '◉', description: 'Classification neural net', threat: 'MEDIUM' },
		{ id: 'system_classification', label: 'MAINFRAME_ID', icon: '▬', description: 'System identification protocol', threat: 'HIGH' },
		{ id: 'business_unit', label: 'CORPORATE_INTEL', icon: '◐', description: 'Business entity profiling', threat: 'MEDIUM' },
		{ id: 'cio_metrics', label: 'EXECUTIVE_SHADOW', icon: '◑', description: 'Leadership surveillance', threat: 'EXTREME' },
		{ id: 'tanium_coverage', label: 'AGENT_GRID', icon: '⬟', description: 'Field operative status', threat: 'CRITICAL' },
		{ id: 'cmdb_presence', label: 'DATABASE_GHOST', icon: '◈', description: 'Registry phantom check', threat: 'HIGH' }
	];

	let scanningEffect = false;
	let alertPulse = false;

	onMount(() => {
		document.title = '◢◤ SHADOWNET NEURAL COMMAND ◢◤';
		
		setInterval(() => {
			neuralSync = Math.floor(95 + Math.random() * 5);
			if (Math.random() < 0.1) {
				alertPulse = true;
				setTimeout(() => alertPulse = false, 2000);
			}
		}, 3000);
	});

	function switchView(viewId) {
		scanningEffect = true;
		currentView = viewId;
		setTimeout(() => scanningEffect = false, 800);
	}

	function getThreatColor(threat) {
		switch(threat) {
			case 'EXTREME': return '#ff0040';
			case 'TOP_SECRET': return '#ff6600';
			case 'CRITICAL': return '#ff0080';
			case 'HIGH': return '#ffaa00';
			case 'MEDIUM': return '#00ffff';
			default: return '#00ff41';
		}
	}
</script>

<main class="shadownet-terminal">
	<MatrixBackground />
	
	<div class="command-interface" class:scanning={scanningEffect}>
		<header class="neural-header" class:alert={alertPulse}>
			<div class="header-left">
				<div class="shadownet-brand">
					<div class="brand-core">
						<span class="core-symbol">◢◤</span>
						<div class="neural-pulse"></div>
					</div>
					<div class="brand-identity">
						<span class="primary-designation">SHADOWNET NEURAL COMMAND</span>
						<span class="sub-designation">QUANTUM THREAT INTELLIGENCE MATRIX</span>
					</div>
				</div>
				<div class="system-vitals">
					<div class="vital-metric">
						<span class="metric-label">STATUS</span>
						<span class="metric-value threat-critical">{systemStatus}</span>
						<div class="vital-pulse"></div>
					</div>
					<div class="vital-metric">
						<span class="metric-label">DEFCON</span>
						<span class="metric-value threat-extreme">{threatLevel}</span>
						<div class="vital-pulse"></div>
					</div>
					<div class="vital-metric">
						<span class="metric-label">SYNC</span>
						<span class="metric-value">{neuralSync}%</span>
						<div class="sync-bar">
							<div class="sync-fill" style="width: {neuralSync}%"></div>
						</div>
					</div>
				</div>
			</div>
			<div class="header-right">
				<div class="security-matrix">
					<div class="classification-stamp">
						<span class="stamp-text">◢ EYES ONLY ◤</span>
						<div class="security-indicator"></div>
					</div>
					<div class="neural-timestamp">
						<span class="time-label">NEURAL SYNC ACTIVE</span>
						<span class="time-value">{new Date().toISOString().slice(0, 19)}Ω</span>
					</div>
				</div>
			</div>
		</header>

		<nav class="tactical-navigation">
			<div class="nav-grid">
				{#each menuItems as item}
					<button 
						class="tactical-module {currentView === item.id ? 'active' : ''}"
						on:click={() => switchView(item.id)}
						style="--threat-color: {getThreatColor(item.threat)}"
					>
						<div class="module-threat-indicator" style="background: {getThreatColor(item.threat)}"></div>
						<div class="module-core">
							<div class="module-symbol">{item.icon}</div>
							<div class="module-data">
								<div class="module-designation">{item.label}</div>
								<div class="module-description">{item.description}</div>
								<div class="threat-classification" style="color: {getThreatColor(item.threat)}">{item.threat}</div>
							</div>
						</div>
						<div class="module-scanner"></div>
					</button>
				{/each}
			</div>
		</nav>

		<main class="operational-workspace">
			<div class="workspace-command-bar">
				<div class="workspace-designation">
					<div class="designation-icon">◢</div>
					<span class="designation-text">{menuItems.find(item => item.id === currentView)?.label || 'UNKNOWN_PROTOCOL'}</span>
					<div class="designation-scanner"></div>
				</div>
				<div class="workspace-controls">
					<button class="command-btn neural-refresh" on:click={() => location.reload()}>
						<span class="btn-symbol">⟲</span>
						<span>NEURAL_RESET</span>
						<div class="btn-energy"></div>
					</button>
					<div class="neural-status">
						<div class="status-core"></div>
						<span>QUANTUM_LINK</span>
						<div class="link-strength"></div>
					</div>
				</div>
			</div>

			<div class="workspace-content" class:scanning={scanningEffect}>
				<div class="scan-overlay">
					<div class="scan-line"></div>
					<div class="scan-grid">
						{#each Array(20) as _, i}
							<div class="grid-node" style="animation-delay: {i * 0.05}s"></div>
						{/each}
					</div>
				</div>
				
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
		</main>
	</div>
</main>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: 'Consolas', 'Monaco', 'Roboto Mono', monospace;
		background: #000;
		color: #00ff41;
		overflow: hidden;
		user-select: none;
	}

	.shadownet-terminal {
		width: 100vw;
		height: 100vh;
		position: relative;
		background: radial-gradient(ellipse at 30% 20%, #001a00 0%, #000606 35%, #000000 100%);
		overflow: hidden;
	}

	.command-interface {
		position: relative;
		z-index: 100;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.05);
		transition: all 0.3s ease;
	}

	.command-interface.scanning {
		filter: hue-rotate(30deg) brightness(1.2);
	}

	.neural-header {
		background: linear-gradient(135deg, rgba(0, 40, 0, 0.98), rgba(0, 20, 0, 0.95), rgba(10, 0, 10, 0.97));
		border-bottom: 3px solid #00ff41;
		padding: 12px 20px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		backdrop-filter: blur(25px);
		box-shadow: 
			0 0 50px rgba(0, 255, 65, 0.4),
			inset 0 -1px 20px rgba(0, 255, 65, 0.1);
		position: relative;
	}

	.neural-header.alert {
		animation: alert-flash 1s ease-in-out;
		border-bottom-color: #ff0040;
	}

	@keyframes alert-flash {
		0%, 100% { background: linear-gradient(135deg, rgba(0, 40, 0, 0.98), rgba(0, 20, 0, 0.95), rgba(10, 0, 10, 0.97)); }
		50% { background: linear-gradient(135deg, rgba(40, 0, 0, 0.98), rgba(20, 0, 0, 0.95), rgba(10, 10, 0, 0.97)); }
	}

	.shadownet-brand {
		display: flex;
		align-items: center;
		gap: 20px;
	}

	.brand-core {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.core-symbol {
		font-size: 38px;
		color: #00ff41;
		animation: core-rotation 6s linear infinite;
		filter: drop-shadow(0 0 15px #00ff41);
	}

	@keyframes core-rotation {
		0% { transform: rotate(0deg) scale(1); color: #00ff41; }
		25% { transform: rotate(90deg) scale(1.1); color: #40ff80; }
		50% { transform: rotate(180deg) scale(1); color: #80ffff; }
		75% { transform: rotate(270deg) scale(1.1); color: #40ff80; }
		100% { transform: rotate(360deg) scale(1); color: #00ff41; }
	}

	.neural-pulse {
		position: absolute;
		width: 60px;
		height: 60px;
		border: 2px solid rgba(0, 255, 65, 0.3);
		border-radius: 50%;
		animation: neural-expand 2s ease-out infinite;
	}

	@keyframes neural-expand {
		0% { transform: scale(0.5); opacity: 1; }
		100% { transform: scale(2); opacity: 0; }
	}

	.brand-identity {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.primary-designation {
		font-size: 28px;
		font-weight: 900;
		letter-spacing: 4px;
		color: #00ff41;
		text-shadow: 0 0 20px #00ff41;
		animation: designation-glow 3s ease-in-out infinite alternate;
	}

	@keyframes designation-glow {
		from { text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41; }
		to { text-shadow: 0 0 20px #00ff41, 0 0 40px #00ff41, 0 0 60px #00ff41; }
	}

	.sub-designation {
		font-size: 11px;
		color: #80ff80;
		letter-spacing: 2px;
		opacity: 0.9;
	}

	.system-vitals {
		display: flex;
		gap: 30px;
		align-items: center;
	}

	.vital-metric {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
		position: relative;
	}

	.metric-label {
		font-size: 8px;
		color: #80ff80;
		letter-spacing: 2px;
		font-weight: bold;
	}

	.metric-value {
		font-size: 14px;
		font-weight: 900;
		letter-spacing: 1px;
	}

	.metric-value.threat-critical {
		color: #ff0040;
		animation: threat-pulse 2s infinite;
	}

	.metric-value.threat-extreme {
		color: #ff6600;
		animation: extreme-flash 1.5s infinite;
	}

	@keyframes threat-pulse {
		0%, 70% { opacity: 1; }
		71%, 100% { opacity: 0.3; }
	}

	@keyframes extreme-flash {
		0%, 50% { color: #ff6600; }
		51%, 100% { color: #ff0000; }
	}

	.vital-pulse {
		width: 8px;
		height: 8px;
		background: #00ff41;
		border-radius: 50%;
		animation: vital-beat 1s infinite;
	}

	@keyframes vital-beat {
		0%, 50% { opacity: 1; transform: scale(1); }
		51%, 100% { opacity: 0.2; transform: scale(0.5); }
	}

	.sync-bar {
		width: 40px;
		height: 4px;
		background: rgba(0, 255, 65, 0.2);
		border-radius: 2px;
		overflow: hidden;
		border: 1px solid #004400;
	}

	.sync-fill {
		height: 100%;
		background: linear-gradient(90deg, #00ff41, #80ff80);
		transition: width 0.5s ease;
		position: relative;
	}

	.sync-fill::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
		animation: sync-shine 2s infinite;
	}

	@keyframes sync-shine {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	.security-matrix {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 8px;
	}

	.classification-stamp {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 6px 12px;
		background: rgba(255, 0, 64, 0.15);
		border: 1px solid #ff0040;
		border-radius: 3px;
	}

	.stamp-text {
		color: #ff0040;
		font-weight: 900;
		font-size: 10px;
		letter-spacing: 2px;
		animation: stamp-flash 4s infinite;
	}

	@keyframes stamp-flash {
		0%, 80% { opacity: 1; }
		81%, 100% { opacity: 0.4; }
	}

	.security-indicator {
		width: 10px;
		height: 10px;
		background: #ff0040;
		border-radius: 50%;
		animation: security-pulse 2s infinite;
	}

	@keyframes security-pulse {
		0%, 50% { opacity: 1; box-shadow: 0 0 10px #ff0040; }
		51%, 100% { opacity: 0.3; box-shadow: none; }
	}

	.neural-timestamp {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 2px;
	}

	.time-label {
		font-size: 8px;
		color: #80ff80;
		opacity: 0.8;
		letter-spacing: 1px;
	}

	.time-value {
		font-size: 11px;
		color: #00ff41;
		font-family: 'Courier New', monospace;
		letter-spacing: 1px;
	}

	.tactical-navigation {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.98), rgba(20, 0, 20, 0.95));
		border-bottom: 1px solid #004400;
		padding: 8px 20px;
		backdrop-filter: blur(20px);
		box-shadow: inset 0 0 30px rgba(0, 255, 65, 0.05);
	}

	.nav-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 6px;
		max-height: 140px;
		overflow-y: auto;
	}

	.tactical-module {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(10, 0, 10, 0.6));
		border: 1px solid var(--threat-color);
		color: #00ff41;
		padding: 8px;
		font-family: inherit;
		font-size: 8px;
		cursor: pointer;
		border-radius: 4px;
		transition: all 0.3s ease;
		position: relative;
		overflow: hidden;
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.tactical-module::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(0, 255, 65, 0.1), transparent);
		transition: left 0.6s ease;
	}

	.tactical-module:hover::before,
	.tactical-module.active::before {
		left: 100%;
	}

	.tactical-module:hover,
	.tactical-module.active {
		background: linear-gradient(135deg, rgba(0, 255, 65, 0.2), rgba(0, 255, 65, 0.05));
		border-color: var(--threat-color);
		box-shadow: 
			0 0 25px rgba(0, 255, 65, 0.5),
			inset 0 0 15px rgba(0, 255, 65, 0.1);
		transform: translateY(-2px);
	}

	.module-threat-indicator {
		width: 4px;
		height: 40px;
		border-radius: 2px;
		animation: threat-indicator-pulse 2s infinite;
	}

	@keyframes threat-indicator-pulse {
		0%, 50% { opacity: 1; }
		51%, 100% { opacity: 0.3; }
	}

	.module-core {
		display: flex;
		align-items: center;
		gap: 8px;
		flex: 1;
	}

	.module-symbol {
		font-size: 16px;
		color: var(--threat-color);
		animation: symbol-hover 3s ease-in-out infinite;
	}

	@keyframes symbol-hover {
		0%, 100% { transform: translateY(0) rotate(0deg); }
		50% { transform: translateY(-1px) rotate(180deg); }
	}

	.module-data {
		display: flex;
		flex-direction: column;
		gap: 1px;
	}

	.module-designation {
		font-weight: 900;
		letter-spacing: 1px;
		color: #00ff41;
		font-size: 9px;
	}

	.module-description {
		font-size: 7px;
		color: #80ff80;
		opacity: 0.8;
		line-height: 1.2;
	}

	.threat-classification {
		font-size: 6px;
		font-weight: 900;
		letter-spacing: 1px;
		opacity: 0.9;
	}

	.module-scanner {
		width: 20px;
		height: 2px;
		background: linear-gradient(90deg, transparent, var(--threat-color), transparent);
		animation: scanner-sweep 3s linear infinite;
		opacity: 0.6;
	}

	@keyframes scanner-sweep {
		0% { transform: translateX(-20px); }
		100% { transform: translateX(20px); }
	}

	.operational-workspace {
		flex: 1;
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.4);
		position: relative;
	}

	.workspace-command-bar {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.95), rgba(0, 20, 0, 0.9));
		border-bottom: 1px solid #004400;
		padding: 12px 20px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		backdrop-filter: blur(15px);
		box-shadow: inset 0 0 20px rgba(0, 255, 65, 0.05);
	}

	.workspace-designation {
		display: flex;
		align-items: center;
		gap: 12px;
		position: relative;
	}

	.designation-icon {
		font-size: 18px;
		color: #00ff41;
		animation: designation-rotate 4s linear infinite;
	}

	@keyframes designation-rotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.designation-text {
		font-size: 18px;
		font-weight: 900;
		color: #00ff41;
		letter-spacing: 3px;
		text-shadow: 0 0 15px #00ff41;
		animation: text-energy 2s ease-in-out infinite alternate;
	}

	@keyframes text-energy {
		from { text-shadow: 0 0 10px #00ff41; }
		to { text-shadow: 0 0 25px #00ff41, 0 0 35px #00ff41; }
	}

	.designation-scanner {
		width: 60px;
		height: 2px;
		background: linear-gradient(90deg, transparent, #00ff41, transparent);
		animation: designation-scan 2s linear infinite;
	}

	@keyframes designation-scan {
		0% { transform: translateX(-30px); opacity: 0; }
		50% { opacity: 1; }
		100% { transform: translateX(30px); opacity: 0; }
	}

	.workspace-controls {
		display: flex;
		align-items: center;
		gap: 25px;
	}

	.command-btn {
		background: linear-gradient(135deg, rgba(0, 255, 65, 0.3), rgba(0, 255, 65, 0.1));
		border: 1px solid #00ff41;
		color: #00ff41;
		padding: 8px 16px;
		font-family: inherit;
		font-size: 10px;
		cursor: pointer;
		border-radius: 3px;
		display: flex;
		align-items: center;
		gap: 8px;
		transition: all 0.3s ease;
		letter-spacing: 1px;
		font-weight: 900;
		position: relative;
		overflow: hidden;
	}

	.command-btn:hover {
		background: linear-gradient(135deg, rgba(0, 255, 65, 0.5), rgba(0, 255, 65, 0.2));
		box-shadow: 0 0 20px rgba(0, 255, 65, 0.6);
		transform: translateY(-2px);
	}

	.btn-symbol {
		font-size: 14px;
	}

	.btn-energy {
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(0, 255, 65, 0.4), transparent);
		animation: btn-energy-flow 3s infinite;
	}

	@keyframes btn-energy-flow {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	.neural-status {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 10px;
		color: #80ff80;
		font-weight: bold;
	}

	.status-core {
		width: 10px;
		height: 10px;
		background: #00ff41;
		border-radius: 50%;
		animation: core-pulse 1.5s infinite;
		position: relative;
	}

	.status-core::after {
		content: '';
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid rgba(0, 255, 65, 0.5);
		border-radius: 50%;
		animation: core-ripple 1.5s infinite;
	}

	@keyframes core-pulse {
		0%, 50% { opacity: 1; transform: scale(1); }
		51%, 100% { opacity: 0.4; transform: scale(0.8); }
	}

	@keyframes core-ripple {
		0% { transform: scale(1); opacity: 1; }
		100% { transform: scale(2); opacity: 0; }
	}

	.link-strength {
		width: 30px;
		height: 4px;
		background: rgba(0, 255, 65, 0.3);
		border-radius: 2px;
		position: relative;
		overflow: hidden;
	}

	.link-strength::after {
		content: '';
		position: absolute;
		left: 0;
		top: 0;
		height: 100%;
		width: 80%;
		background: #00ff41;
		animation: link-activity 2s ease-in-out infinite;
	}

	@keyframes link-activity {
		0%, 100% { width: 80%; }
		50% { width: 100%; }
	}

	.workspace-content {
		flex: 1;
		padding: 20px;
		overflow-y: auto;
		background: rgba(0, 0, 0, 0.1);
		position: relative;
	}

	.scan-overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		opacity: 0;
		transition: opacity 0.3s ease;
	}

	.workspace-content.scanning .scan-overlay {
		opacity: 1;
	}

	.scan-line {
		position: absolute;
		width: 100%;
		height: 3px;
		background: linear-gradient(90deg, transparent, #00ff41, transparent);
		animation: scan-sweep 0.8s ease-in-out;
		box-shadow: 0 0 10px #00ff41;
	}

	@keyframes scan-sweep {
		0% { top: 0%; opacity: 0; }
		50% { opacity: 1; }
		100% { top: 100%; opacity: 0; }
	}

	.scan-grid {
		position: absolute;
		width: 100%;
		height: 100%;
		display: grid;
		grid-template-columns: repeat(10, 1fr);
		grid-template-rows: repeat(2, 1fr);
		gap: 2px;
	}

	.grid-node {
		background: rgba(0, 255, 65, 0.1);
		animation: node-scan 0.8s ease-in-out;
	}

	@keyframes node-scan {
		0%, 100% { opacity: 0; background: rgba(0, 255, 65, 0.1); }
		50% { opacity: 1; background: rgba(0, 255, 65, 0.3); }
	}

	:global(::-webkit-scrollbar) {
		width: 8px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.8);
		border-radius: 4px;
	}

	:global(::-webkit-scrollbar-thumb) {
		background: linear-gradient(135deg, #004400, #00ff41);
		border-radius: 4px;
		border: 1px solid #002200;
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, #00ff41, #80ff80);
	}
</style>