<script>
	import { onMount } from 'svelte';

	let data = {};
	let loading = true;
	let error = null;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/tanium_coverage');
			const result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			error = 'TANIUM NETWORK COMPROMISED';
			loading = false;
		}
	});

	$: coverageColor = data.coverage_percentage >= 80 ? '#00ff41' : 
	                  data.coverage_percentage >= 60 ? '#ffaa00' : '#ff4444';
	$: coverageStatus = data.coverage_percentage >= 80 ? 'OPTIMAL' : 
	                   data.coverage_percentage >= 60 ? 'ACCEPTABLE' : 'CRITICAL';
</script>

<div class="tanium-panel">
	<header class="panel-header">
		<div class="header-content">
			<span class="header-icon">⬠</span>
			<div class="header-text">
				<h2>TANIUM COVERAGE ANALYSIS</h2>
				<p>Agent deployment status (keyword search: "tanium")</p>
			</div>
		</div>
		<div class="status-badge" style="border-color: {coverageColor}; color: {coverageColor}">
			{coverageStatus}
		</div>
	</header>

	{#if loading}
		<div class="loading-state">
			<div class="tanium-loader">
				<div class="loader-ring"></div>
				<div class="loader-core">⬠</div>
			</div>
			<p>Scanning Tanium infrastructure...</p>
		</div>
	{:else if error}
		<div class="error-state">
			<span class="error-icon">⚠</span>
			<p>CRITICAL ERROR: {error}</p>
		</div>
	{:else}
		<div class="panel-content">
			<div class="coverage-overview">
				<div class="coverage-circle">
					<svg width="160" height="160" viewBox="0 0 160 160">
						<circle
							cx="80"
							cy="80"
							r="70"
							fill="none"
							stroke="#004400"
							stroke-width="10"
						/>
						<circle
							cx="80"
							cy="80"
							r="70"
							fill="none"
							stroke={coverageColor}
							stroke-width="10"
							stroke-dasharray="439.8"
							stroke-dashoffset={439.8 * (1 - (data.coverage_percentage || 0) / 100)}
							stroke-linecap="round"
							transform="rotate(-90 80 80)"
							class="progress-circle"
						/>
					</svg>
					<div class="circle-content">
						<div class="percentage" style="color: {coverageColor}">
							{data.coverage_percentage || 0}%
						</div>
						<div class="coverage-label">COVERAGE</div>
					</div>
				</div>

				<div class="coverage-stats">
					<div class="stat-grid">
						<div class="stat-card deployed">
							<div class="stat-value">{(data.tanium_deployed || 0).toLocaleString()}</div>
							<div class="stat-label">TANIUM DEPLOYED</div>
							<div class="stat-icon">⬢</div>
						</div>
						<div class="stat-card total">
							<div class="stat-value">{(data.total_assets || 0).toLocaleString()}</div>
							<div class="stat-label">TOTAL ASSETS</div>
							<div class="stat-icon">◯</div>
						</div>
						<div class="stat-card gap">
							<div class="stat-value">{((data.total_assets || 0) - (data.tanium_deployed || 0)).toLocaleString()}</div>
							<div class="stat-label">COVERAGE GAP</div>
							<div class="stat-icon">⚠</div>
						</div>
					</div>
				</div>
			</div>

			<div class="coverage-heatmap">
				<h3>DEPLOYMENT HEATMAP</h3>
				<div class="heatmap-container">
					<div class="heatmap-row">
						<span class="heatmap-label">Tanium Deployed</span>
						<div class="heatmap-bar deployed">
							<div class="bar-fill" style="width: {data.coverage_percentage || 0}%; background: {coverageColor};"></div>
							<div class="bar-value">{data.coverage_percentage || 0}%</div>
						</div>
					</div>
					<div class="heatmap-row">
						<span class="heatmap-label">Coverage Gap</span>
						<div class="heatmap-bar gap">
							<div class="bar-fill" style="width: {100 - (data.coverage_percentage || 0)}%; background: #ff4444;"></div>
							<div class="bar-value">{100 - (data.coverage_percentage || 0)}%</div>
						</div>
					</div>
				</div>
			</div>

			<div class="threat-assessment">
				<div class="assessment-header">
					<h3>THREAT ASSESSMENT</h3>
					<div class="threat-indicator" style="background: {coverageColor}"></div>
				</div>
				<div class="assessment-content">
					{#if data.coverage_percentage >= 80}
						<p class="assessment-text optimal">
							◯ OPTIMAL COVERAGE - Tanium deployment meets security standards
						</p>
						<p class="assessment-recommendation">
							→ Maintain current deployment levels and monitor for new assets
						</p>
					{:else if data.coverage_percentage >= 60}
						<p class="assessment-text warning">
							⚠ ACCEPTABLE COVERAGE - Monitor for potential security gaps
						</p>
						<p class="assessment-recommendation">
							→ Prioritize deployment to remaining {((data.total_assets || 0) - (data.tanium_deployed || 0)).toLocaleString()} assets
						</p>
					{:else}
						<p class="assessment-text critical">
							⚠ CRITICAL COVERAGE GAP - Immediate deployment required
						</p>
						<p class="assessment-recommendation">
							→ URGENT: Deploy Tanium to {((data.total_assets || 0) - (data.tanium_deployed || 0)).toLocaleString()} unprotected assets
						</p>
					{/if}
				</div>
			</div>

			<div class="neural-footer">
				<div class="classification-notice">
					⬠ TANIUM DEPLOYMENT // AGENT COVERAGE PROTOCOL ACTIVE
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.tanium-panel {
		background: linear-gradient(135deg, rgba(0, 26, 13, 0.95) 0%, rgba(0, 13, 6, 0.95) 100%);
		border: 1px solid #00ff41;
		border-radius: 8px;
		overflow: hidden;
		box-shadow: 
			0 0 20px rgba(0, 255, 65, 0.3),
			inset 0 0 20px rgba(0, 255, 65, 0.05);
		animation: tanium-pulse 3s ease-in-out infinite alternate;
	}

	@keyframes tanium-pulse {
		from { box-shadow: 0 0 20px rgba(0, 255, 65, 0.2), inset 0 0 20px rgba(0, 255, 65, 0.05); }
		to { box-shadow: 0 0 30px rgba(0, 255, 65, 0.4), inset 0 0 30px rgba(0, 255, 65, 0.1); }
	}

	.panel-header {
		background: rgba(0, 0, 0, 0.9);
		border-bottom: 1px solid #004400;
		padding: 15px 20px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.header-content {
		display: flex;
		align-items: center;
		gap: 15px;
	}

	.header-icon {
		font-size: 24px;
		color: #00ff41;
		animation: hex-rotate 6s linear infinite;
	}

	@keyframes hex-rotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.header-text h2 {
		margin: 0;
		font-size: 16px;
		color: #00ff41;
		letter-spacing: 1px;
	}

	.header-text p {
		margin: 2px 0 0 0;
		font-size: 11px;
		color: #66ff66;
		opacity: 0.8;
	}

	.status-badge {
		padding: 5px 12px;
		border: 1px solid;
		border-radius: 4px;
		font-size: 11px;
		font-weight: bold;
		letter-spacing: 1px;
		background: rgba(0, 0, 0, 0.3);
	}

	.loading-state {
		padding: 40px;
		text-align: center;
	}

	.tanium-loader {
		position: relative;
		width: 60px;
		height: 60px;
		margin: 0 auto 20px;
	}

	.loader-ring {
		position: absolute;
		width: 60px;
		height: 60px;
		border: 3px solid #004400;
		border-top: 3px solid #00ff41;
		border-radius: 50%;
		animation: loader-spin 1s linear infinite;
	}

	.loader-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 20px;
		color: #00ff41;
	}

	@keyframes loader-spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.panel-content {
		padding: 20px;
	}

	.coverage-overview {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 30px;
		margin-bottom: 30px;
		align-items: center;
	}

	.coverage-circle {
		position: relative;
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.progress-circle {
		transition: stroke-dashoffset 2s ease-out;
	}

	.circle-content {
		position: absolute;
		text-align: center;
	}

	.percentage {
		font-size: 28px;
		font-weight: bold;
		animation: percentage-glow 2s ease-in-out infinite alternate;
	}

	@keyframes percentage-glow {
		from { filter: drop-shadow(0 0 5px currentColor); }
		to { filter: drop-shadow(0 0 15px currentColor); }
	}

	.coverage-label {
		font-size: 12px;
		color: #66ff66;
		margin-top: 5px;
	}

	.stat-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 15px;
	}

	.stat-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-radius: 6px;
		padding: 15px;
		text-align: center;
		position: relative;
		transition: all 0.3s ease;
	}

	.stat-card:hover {
		border-color: #00ff41;
		box-shadow: 0 0 15px rgba(0, 255, 65, 0.3);
	}

	.stat-card.deployed {
		border-left: 4px solid #00ff41;
	}

	.stat-card.total {
		border-left: 4px solid #0099ff;
	}

	.stat-card.gap {
		border-left: 4px solid #ff4444;
	}

	.stat-value {
		font-size: 20px;
		font-weight: bold;
		color: #00ff41;
		margin-bottom: 5px;
	}

	.stat-label {
		font-size: 9px;
		color: #66ff66;
		letter-spacing: 1px;
	}

	.stat-icon {
		position: absolute;
		top: 10px;
		right: 10px;
		font-size: 14px;
		color: #004400;
	}

	.coverage-heatmap h3 {
		color: #00ff41;
		margin: 0 0 15px 0;
		font-size: 14px;
		letter-spacing: 1px;
		border-bottom: 1px solid #004400;
		padding-bottom: 10px;
	}

	.heatmap-container {
		display: flex;
		flex-direction: column;
		gap: 15px;
		margin-bottom: 25px;
	}

	.heatmap-row {
		display: grid;
		grid-template-columns: 150px 1fr;
		gap: 15px;
		align-items: center;
	}

	.heatmap-label {
		font-size: 12px;
		color: #66ff66;
	}

	.heatmap-bar {
		height: 25px;
		background: #002200;
		border-radius: 4px;
		overflow: hidden;
		border: 1px solid #004400;
		position: relative;
		display: flex;
		align-items: center;
	}

	.bar-fill {
		height: 100%;
		border-radius: 3px;
		transition: width 1.5s ease-out;
		position: relative;
	}

	.bar-fill::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
		animation: bar-shine 2s infinite;
	}

	@keyframes bar-shine {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	.bar-value {
		position: absolute;
		right: 10px;
		font-size: 11px;
		font-weight: bold;
		color: #000;
		mix-blend-mode: difference;
	}

	.threat-assessment {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid #004400;
		border-radius: 6px;
		padding: 20px;
		margin-bottom: 20px;
	}

	.assessment-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 15px;
	}

	.assessment-header h3 {
		margin: 0;
		color: #00ff41;
		font-size: 14px;
		letter-spacing: 1px;
	}

	.threat-indicator {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		animation: indicator-pulse 2s infinite;
	}

	@keyframes indicator-pulse {
		0%, 50% { opacity: 1; }
		51%, 100% { opacity: 0.3; }
	}

	.assessment-text {
		margin: 0 0 10px 0;
		font-size: 12px;
		padding: 10px;
		border-radius: 4px;
		border-left: 4px solid;
	}

	.assessment-text.optimal {
		background: rgba(0, 255, 65, 0.1);
		border-left-color: #00ff41;
		color: #00ff41;
	}

	.assessment-text.warning {
		background: rgba(255, 170, 0, 0.1);
		border-left-color: #ffaa00;
		color: #ffaa00;
	}

	.assessment-text.critical {
		background: rgba(255, 68, 68, 0.1);
		border-left-color: #ff4444;
		color: #ff4444;
	}

	.assessment-recommendation {
		margin: 0;
		font-size: 11px;
		color: #66ff66;
		font-style: italic;
		padding-left: 20px;
	}

	.neural-footer {
		border-top: 1px solid #004400;
		padding-top: 15px;
		font-size: 10px;
		color: #00ff41;
		text-align: center;
	}
</style>