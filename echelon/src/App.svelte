<script>
	import { onMount } from 'svelte';
	import SourceTables from './components/SourceTables.svelte';
	import DomainMetrics from './components/DomainMetrics.svelte';
	import InfrastructureType from './components/InfrastructureType.svelte';
	import RegionMetrics from './components/RegionMetrics.svelte';
	import CountryMetrics from './components/CountryMetrics.svelte';
	import DataCenterMetrics from './components/DataCenterMetrics.svelte';
	import CloudRegionMetrics from './components/CloudRegionMetrics.svelte';
	import ClassMetrics from './components/ClassMetrics.svelte';
	import SystemClassification from './components/SystemClassification.svelte';
	import BusinessUnitMetrics from './components/BusinessUnitMetrics.svelte';
	import CioMetrics from './components/CioMetrics.svelte';
	import TaniumCoverage from './components/TaniumCoverage.svelte';
	import CmdbPresence from './components/CmdbPresence.svelte';
	import MatrixBackground from './components/MatrixBackground.svelte';

	let currentView = 'source_tables';
	let systemStatus = 'operational';

	const menuItems = [
		{ id: 'source_tables', label: 'SOURCE TABLES', icon: '◈', description: 'Comma-separated analysis' },
		{ id: 'domain_metrics', label: '1DC vs FEAD', icon: '◆', description: 'Domain battle analysis' },
		{ id: 'infrastructure_type', label: 'INFRASTRUCTURE', icon: '⬢', description: 'Pipe-separated types' },
		{ id: 'region_metrics', label: 'REGIONS', icon: '◉', description: 'Global distribution' },
		{ id: 'country_metrics', label: 'COUNTRIES', icon: '⬟', description: 'Normalized countries' },
		{ id: 'data_center', label: 'DATA CENTERS', icon: '⬡', description: 'First word analysis' },
		{ id: 'cloud_region', label: 'CLOUD REGIONS', icon: '◯', description: 'Cloud mapping' },
		{ id: 'class_metrics', label: 'CLASSES', icon: '◐', description: 'Class number extraction' },
		{ id: 'system_classification', label: 'SYSTEMS', icon: '◑', description: 'System taxonomy' },
		{ id: 'business_unit', label: 'BUSINESS UNITS', icon: '◒', description: 'Unit analysis' },
		{ id: 'cio_metrics', label: 'CIO ANALYSIS', icon: '◓', description: 'Words only filter' },
		{ id: 'tanium_coverage', label: 'TANIUM', icon: '⬠', description: 'Keyword: tanium' },
		{ id: 'cmdb_presence', label: 'CMDB', icon: '⬢', description: 'Keyword: yes' }
	];

	onMount(() => {
		document.title = 'AO1 Log Visibility - Neural Threat Intelligence';
	});

	function switchView(viewId) {
		currentView = viewId;
	}
</script>

<main class="ao1-terminal">
	<MatrixBackground />
	
	<div class="dashboard-container">
		<header class="ao1-header">
			<div class="header-left">
				<div class="ao1-brand">
					<span class="brand-icon">◈</span>
					<div class="brand-text">
						<span class="main-title">AO1 LOG VISIBILITY</span>
						<span class="sub-title">NEURAL THREAT INTELLIGENCE SYSTEM</span>
					</div>
				</div>
				<div class="system-metrics">
					<div class="metric">
						<span class="metric-label">STATUS</span>
						<span class="metric-value operational">OPERATIONAL</span>
					</div>
					<div class="metric">
						<span class="metric-label">CLEARANCE</span>
						<span class="metric-value">TOP SECRET</span>
					</div>
				</div>
			</div>
			<div class="header-right">
				<div class="classification-banner">
					<span class="classification-text">CLASSIFICATION: TOP SECRET</span>
					<div class="classification-indicator"></div>
				</div>
				<div class="system-timestamp">
					<span class="timestamp-label">NEURAL LINK ACTIVE</span>
					<span class="timestamp-value">{new Date().toISOString().slice(0, 19)}Z</span>
				</div>
			</div>
		</header>

		<nav class="ao1-navigation">
			<div class="nav-container">
				{#each menuItems as item}
					<button 
						class="nav-module {currentView === item.id ? 'active' : ''}"
						on:click={() => switchView(item.id)}
						title={item.description}
					>
						<div class="module-icon">{item.icon}</div>
						<div class="module-info">
							<div class="module-label">{item.label}</div>
							<div class="module-description">{item.description}</div>
						</div>
						<div class="module-status"></div>
					</button>
				{/each}
			</div>
		</nav>

		<main class="ao1-workspace">
			<div class="workspace-header">
				<div class="workspace-title">
					{menuItems.find(item => item.id === currentView)?.label || 'UNKNOWN MODULE'}
				</div>
				<div class="workspace-controls">
					<button class="control-btn refresh" on:click={() => location.reload()}>
						<span class="btn-icon">⟲</span>
						REFRESH
					</button>
					<div class="connection-status">
						<div class="status-dot"></div>
						<span>NEURAL LINK</span>
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
		</main>
	</div>
</main>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: 'Courier New', monospace;
		background: #000;
		color: #00ff41;
		overflow: hidden;
	}

	:global(*) {
		box-sizing: border-box;
	}

	.ao1-terminal {
		width: 100vw;
		height: 100vh;
		position: relative;
		background: radial-gradient(ellipse at center, #001100 0%, #000000 100%);
	}

	.dashboard-container {
		position: relative;
		z-index: 10;
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.1);
	}

	.ao1-header {
		background: linear-gradient(135deg, rgba(0, 26, 0, 0.95), rgba(0, 13, 0, 0.85));
		border-bottom: 2px solid #00ff41;
		padding: 15px 25px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		backdrop-filter: blur(20px);
		box-shadow: 0 0 30px rgba(0, 255, 65, 0.3);
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 40px;
	}

	.ao1-brand {
		display: flex;
		align-items: center;
		gap: 15px;
	}

	.brand-icon {
		font-size: 32px;
		color: #00ff41;
		animation: brand-pulse 4s infinite;
	}

	@keyframes brand-pulse {
		0%, 100% { opacity: 1; transform: scale(1) rotate(0deg); }
		50% { opacity: 0.8; transform: scale(1.1) rotate(180deg); }
	}

	.brand-text {
		display: flex;
		flex-direction: column;
	}

	.main-title {
		font-size: 22px;
		font-weight: bold;
		letter-spacing: 3px;
		color: #00ff41;
	}

	.sub-title {
		font-size: 12px;
		color: #66ff66;
		opacity: 0.9;
		letter-spacing: 1px;
	}

	.system-metrics {
		display: flex;
		gap: 25px;
	}

	.metric {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 3px;
	}

	.metric-label {
		font-size: 9px;
		color: #66ff66;
		letter-spacing: 1px;
	}

	.metric-value {
		font-size: 12px;
		font-weight: bold;
		letter-spacing: 1px;
	}

	.metric-value.operational {
		color: #00ff41;
		animation: operational-glow 2s infinite alternate;
	}

	@keyframes operational-glow {
		from { text-shadow: 0 0 5px #00ff41; }
		to { text-shadow: 0 0 15px #00ff41; }
	}

	.header-right {
		text-align: right;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.classification-banner {
		display: flex;
		align-items: center;
		gap: 10px;
		justify-content: flex-end;
	}

	.classification-text {
		color: #ff6600;
		font-weight: bold;
		font-size: 11px;
		letter-spacing: 1px;
		animation: classify-blink 3s infinite;
	}

	@keyframes classify-blink {
		0%, 50% { opacity: 1; }
		51%, 100% { opacity: 0.6; }
	}

	.classification-indicator {
		width: 8px;
		height: 8px;
		background: #ff6600;
		border-radius: 50%;
		animation: indicator-pulse 2s infinite;
	}

	@keyframes indicator-pulse {
		0%, 50% { opacity: 1; }
		51%, 100% { opacity: 0.3; }
	}

	.system-timestamp {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.timestamp-label {
		font-size: 9px;
		color: #66ff66;
		opacity: 0.8;
	}

	.timestamp-value {
		font-size: 10px;
		color: #00ff41;
		font-family: monospace;
	}

	.ao1-navigation {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.95), rgba(13, 0, 13, 0.95));
		border-bottom: 1px solid #004400;
		padding: 10px 25px;
		backdrop-filter: blur(15px);
	}

	.nav-container {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 8px;
		max-height: 120px;
		overflow-y: auto;
	}

	.nav-module {
		background: transparent;
		border: 1px solid #004400;
		color: #00ff41;
		padding: 12px;
		font-family: inherit;
		font-size: 9px;
		cursor: pointer;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
		border-radius: 6px;
		transition: all 0.3s ease;
		position: relative;
		overflow: hidden;
	}

	.nav-module::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(0, 255, 65, 0.1), transparent);
		transition: left 0.5s ease;
	}

	.nav-module:hover::before,
	.nav-module.active::before {
		left: 100%;
	}

	.nav-module:hover,
	.nav-module.active {
		background: linear-gradient(135deg, rgba(0, 255, 65, 0.15), rgba(0, 255, 65, 0.05));
		border-color: #00ff41;
		box-shadow: 0 0 20px rgba(0, 255, 65, 0.4);
		transform: translateY(-3px);
	}

	.module-icon {
		font-size: 18px;
		color: #00ff41;
		animation: icon-float 4s ease-in-out infinite;
	}

	@keyframes icon-float {
		0%, 100% { transform: translateY(0) rotate(0deg); }
		25% { transform: translateY(-2px) rotate(90deg); }
		50% { transform: translateY(0) rotate(180deg); }
		75% { transform: translateY(-2px) rotate(270deg); }
	}

	.module-info {
		text-align: center;
		flex: 1;
	}

	.module-label {
		font-weight: bold;
		letter-spacing: 1px;
		margin-bottom: 3px;
		color: #00ff41;
	}

	.module-description {
		font-size: 8px;
		color: #66ff66;
		opacity: 0.8;
		line-height: 1.2;
	}

	.module-status {
		width: 6px;
		height: 6px;
		background: #00ff41;
		border-radius: 50%;
		animation: status-blink 2s infinite;
	}

	@keyframes status-blink {
		0%, 50% { opacity: 1; }
		51%, 100% { opacity: 0.3; }
	}

	.ao1-workspace {
		flex: 1;
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.3);
	}

	.workspace-header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(0, 13, 0, 0.9));
		border-bottom: 1px solid #004400;
		padding: 15px 25px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		backdrop-filter: blur(10px);
	}

	.workspace-title {
		font-size: 16px;
		font-weight: bold;
		color: #00ff41;
		letter-spacing: 2px;
		animation: title-glow 3s ease-in-out infinite alternate;
	}

	@keyframes title-glow {
		from { text-shadow: 0 0 10px #00ff41; }
		to { text-shadow: 0 0 20px #00ff41, 0 0 30px #00ff41; }
	}

	.workspace-controls {
		display: flex;
		align-items: center;
		gap: 20px;
	}

	.control-btn {
		background: linear-gradient(135deg, rgba(0, 255, 65, 0.2), rgba(0, 255, 65, 0.1));
		border: 1px solid #00ff41;
		color: #00ff41;
		padding: 8px 16px;
		font-family: inherit;
		font-size: 10px;
		cursor: pointer;
		border-radius: 4px;
		display: flex;
		align-items: center;
		gap: 6px;
		transition: all 0.3s ease;
		letter-spacing: 1px;
		font-weight: bold;
	}

	.control-btn:hover {
		background: linear-gradient(135deg, rgba(0, 255, 65, 0.4), rgba(0, 255, 65, 0.2));
		box-shadow: 0 0 15px rgba(0, 255, 65, 0.5);
		transform: translateY(-2px);
	}

	.btn-icon {
		font-size: 12px;
	}

	.connection-status {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 10px;
		color: #66ff66;
	}

	.status-dot {
		width: 8px;
		height: 8px;
		background: #00ff41;
		border-radius: 50%;
		animation: connection-pulse 2s infinite;
	}

	@keyframes connection-pulse {
		0%, 50% { opacity: 1; }
		51%, 100% { opacity: 0.3; }
	}

	.workspace-content {
		flex: 1;
		padding: 25px;
		overflow-y: auto;
		background: rgba(0, 0, 0, 0.1);
	}

	:global(::-webkit-scrollbar) {
		width: 12px;
	}

	:global(::-webkit-scrollbar-track) {
		background: rgba(0, 0, 0, 0.5);
		border-radius: 6px;
	}

	:global(::-webkit-scrollbar-thumb) {
		background: linear-gradient(135deg, #004400, #00ff41);
		border-radius: 6px;
		border: 1px solid #002200;
	}

	:global(::-webkit-scrollbar-thumb:hover) {
		background: linear-gradient(135deg, #00ff41, #66ff66);
	}

	:global(::-webkit-scrollbar-corner) {
		background: rgba(0, 0, 0, 0.5);
	}
</style>