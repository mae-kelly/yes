<!-- CmdbPresence.svelte -->
<script>
	import { onMount } from 'svelte';
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/cmdb_presence');
			data = await response.json();
			loading = false;
		} catch (err) {
			loading = false;
		}
	});

	$: registrationColor = data.registration_rate >= 80 ? '#00ff85' : 
	                      data.registration_rate >= 60 ? '#ffaa00' : '#ff0066';
	$: registrationStatus = data.registration_rate >= 80 ? 'COMPLIANT' : 
	                       data.registration_rate >= 60 ? 'PARTIAL' : 'CRITICAL';

	function getCircularProgress(percentage) {
		const circumference = 2 * Math.PI * 70;
		const strokeDashoffset = circumference - (percentage / 100) * circumference;
		return { strokeDashoffset };
	}
</script>

<div class="cmdb-status-matrix">
	<div class="status-header">
		<div class="cmdb-core">
			<div class="database-icon">⬢</div>
		</div>
		<div class="status-info">
			<h2>CMDB STATUS</h2>
			<p>KEYWORD SEARCH: "YES" IN PRESENT_IN_CMDB</p>
		</div>
		<div class="compliance-badge" style="--badge-color: {registrationColor}">
			<div class="badge-ring"></div>
			<span class="badge-text">{registrationStatus}</span>
		</div>
	</div>

	{#if loading}
		<div class="database-scan">
			<div class="db-scanner">
				<div class="scanner-bars">
					{#each Array(8) as _, i}
						<div class="scan-bar" style="animation-delay: {i * 0.1}s"></div>
					{/each}
				</div>
			</div>
			<p>CHECKING CMDB PRESENCE...</p>
		</div>
	{:else}
		<div class="cmdb-interface">
			<div class="registration-display">
				<div class="main-gauge">
					<svg width="180" height="180" viewBox="0 0 180 180">
						<defs>
							<radialGradient id="gaugeBg">
								<stop offset="0%" style="stop-color:rgba(0,255,133,0.3);stop-opacity:1" />
								<stop offset="100%" style="stop-color:rgba(0,255,133,0.1);stop-opacity:0" />
							</radialGradient>
							<filter id="gaugeGlow">
								<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
								<feMerge>
									<feMergeNode in="coloredBlur"/>
									<feMergeNode in="SourceGraphic"/>
								</feMerge>
							</filter>
						</defs>
						
						<circle cx="90" cy="90" r="80" fill="url(#gaugeBg)"/>
						<circle cx="90" cy="90" r="70" fill="none" stroke="rgba(0, 255, 133, 0.2)" stroke-width="2"/>
						
						<circle 
							cx="90" cy="90" r="70" 
							fill="none" 
							stroke={registrationColor} 
							stroke-width="8"
							stroke-dasharray="440"
							stroke-dashoffset={getCircularProgress(data.registration_rate || 0).strokeDashoffset}
							transform="rotate(-90 90 90)"
							filter="url(#gaugeGlow)"
						/>
						
						<circle cx="90" cy="90" r="30" fill="rgba(0, 0, 0, 0.8)" stroke={registrationColor} stroke-width="2"/>
						<text x="90" y="95" text-anchor="middle" fill={registrationColor} font-size="16" font-weight="700">
							{data.registration_rate || 0}%
						</text>
					</svg>
				</div>
				
				<div class="status-metrics">
					<div class="metric-panel registered">
						<div class="panel-header">REGISTERED</div>
						<div class="panel-value" style="color: {registrationColor}">{(data.cmdb_registered || 0).toLocaleString()}</div>
						<div class="panel-graph">
							{#each Array(10) as _, i}
								<div class="graph-segment" style="height: {Math.random() * 100}%; animation-delay: {i * 0.1}s"></div>
							{/each}
						</div>
					</div>
					
					<div class="metric-panel total">
						<div class="panel-header">TOTAL ASSETS</div>
						<div class="panel-value">{(data.total_assets || 0).toLocaleString()}</div>
						<div class="panel-graph">
							{#each Array(10) as _, i}
								<div class="graph-segment" style="height: {Math.random() * 100}%; animation-delay: {i * 0.1}s"></div>
							{/each}
						</div>
					</div>
					
					<div class="metric-panel gap">
						<div class="panel-header">REGISTRATION GAP</div>
						<div class="panel-value" style="color: #ff0066">{((data.total_assets || 0) - (data.cmdb_registered || 0)).toLocaleString()}</div>
						<div class="panel-graph">
							{#each Array(10) as _, i}
								<div class="graph-segment gap-segment" style="height: {Math.random() * 100}%; animation-delay: {i * 0.1}s"></div>
							{/each}
						</div>
					</div>
				</div>
			</div>

			<div class="compliance-analysis">
				<div class="analysis-header">
					<div class="header-symbol">◎</div>
					<h3>COMPLIANCE ANALYSIS</h3>
					<div class="analysis-indicator" style="background: {registrationColor}"></div>
				</div>
				<div class="analysis-content">
					{#if data.registration_rate >= 90}
						<div class="compliance-item optimal">
							<div class="item-icon">✓</div>
							<div class="item-text">OPTIMAL COMPLIANCE - CMDB registration exceeds standards</div>
						</div>
						<div class="compliance-item">
							<div class="item-icon">→</div>
							<div class="item-text">Maintain current registration processes</div>
						</div>
					{:else if data.registration_rate >= 70}
						<div class="compliance-item partial">
							<div class="item-icon">⚠</div>
							<div class="item-text">PARTIAL COMPLIANCE - Registration gaps detected</div>
						</div>
						<div class="compliance-item">
							<div class="item-icon">→</div>
							<div class="item-text">Register {((data.total_assets || 0) - (data.cmdb_registered || 0)).toLocaleString()} remaining assets</div>
						</div>
					{:else}
						<div class="compliance-item critical">
							<div class="item-icon">✕</div>
							<div class="item-text">CRITICAL NON-COMPLIANCE - Immediate action required</div>
						</div>
						<div class="compliance-item">
							<div class="item-icon">→</div>
							<div class="item-text">URGENT: Register {((data.total_assets || 0) - (data.cmdb_registered || 0)).toLocaleString()} unregistered assets</div>
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}

	<div class="interface-footer">
		<div class="footer-line"></div>
		<div class="protocol-notice">
			⬢ CMDB PRESENCE // REGISTRATION COMPLIANCE PROTOCOL ACTIVE
		</div>
	</div>
</div>

<style>
	.cmdb-status-matrix {
		width: 100%;
		height: 100%;
		font-family: 'Orbitron', 'Exo 2', monospace;
		color: #fff;
		display: flex;
		flex-direction: column;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.status-header {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(0, 255, 133, 0.05) 50%,
			rgba(0, 0, 0, 0.8) 100%);
		border: 2px solid #00ff85;
		border-radius: 12px;
		padding: 1.5rem 2rem;
		margin-bottom: 1.5rem;
		backdrop-filter: blur(20px);
		box-shadow: 0 0 40px rgba(0, 255, 133, 0.2);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.cmdb-core {
		width: 100px;
		height: 100px;
		background: radial-gradient(circle, rgba(0, 255, 133, 0.2), transparent);
		border: 3px solid #00ff85;
		clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
		display: flex;
		align-items: center;
		justify-content: center;
		animation: cmdbPulse 3s ease-in-out infinite;
	}

	.database-icon {
		font-size: 2.5rem;
		color: #00ff85;
		text-shadow: 0 0 20px #00ff85;
	}

	.status-info {
		flex: 1;
		margin-left: 2rem;
	}

	.status-info h2 {
		margin: 0;
		font-size: 1.5rem;
		color: #fff;
		text-shadow: 0 0 15px rgba(0, 255, 133, 0.5);
		letter-spacing: 0.1em;
	}

	.status-info p {
		margin: 0.3rem 0 0 0;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.compliance-badge {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem 1.5rem;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6), 
			rgba(255, 255, 255, 0.02));
		border: 2px solid var(--badge-color);
		border-radius: 8px;
		backdrop-filter: blur(10px);
	}

	.badge-ring {
		width: 15px;
		height: 15px;
		background: var(--badge-color);
		border-radius: 50%;
		animation: badgePulse 2s ease-in-out infinite;
		box-shadow: 0 0 15px var(--badge-color);
	}

	.badge-text {
		font-size: 0.8rem;
		color: var(--badge-color);
		font-weight: 700;
		letter-spacing: 0.1em;
		text-shadow: 0 0 10px var(--badge-color);
	}

	.database-scan {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.db-scanner {
		width: 200px;
		height: 100px;
		background: rgba(0, 255, 133, 0.05);
		border: 2px solid #00ff85;
		border-radius: 8px;
		padding: 1rem;
		display: flex;
		align-items: flex-end;
		justify-content: center;
		gap: 0.3rem;
	}

	.scanner-bars {
		display: flex;
		align-items: flex-end;
		gap: 0.3rem;
		height: 60px;
	}

	.scan-bar {
		width: 6px;
		background: #00ff85;
		border-radius: 3px;
		animation: barScan 2s ease-in-out infinite;
		box-shadow: 0 0 8px #00ff85;
	}

	.cmdb-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.registration-display {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 3rem;
		align-items: center;
	}

	.main-gauge {
		position: relative;
		width: 180px;
		height: 180px;
		background: radial-gradient(circle, rgba(0, 0, 0, 0.8), rgba(0, 255, 133, 0.02));
		border: 3px solid #00ff85;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}

	.status-metrics {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.metric-panel {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 133, 0.03));
		border: 2px solid rgba(0, 255, 133, 0.3);
		border-radius: 8px;
		padding: 1.5rem;
		backdrop-filter: blur(10px);
	}

	.panel-header {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		margin-bottom: 0.5rem;
		letter-spacing: 0.1em;
	}

	.panel-value {
		font-size: 2rem;
		font-weight: 700;
		color: #00ff85;
		text-shadow: 0 0 15px currentColor;
		margin-bottom: 1rem;
	}

	.panel-graph {
		display: flex;
		gap: 0.2rem;
		height: 30px;
		align-items: flex-end;
	}

	.graph-segment {
		width: 4px;
		background: linear-gradient(180deg, #00ff85, #007755);
		border-radius: 2px;
		animation: segmentPulse 2s ease-in-out infinite;
		box-shadow: 0 0 6px rgba(0, 255, 133, 0.5);
	}

	.gap-segment {
		background: linear-gradient(180deg, #ff0066, #cc0044);
		box-shadow: 0 0 6px rgba(255, 0, 102, 0.5);
	}

	.compliance-analysis {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 133, 0.02));
		border: 2px solid rgba(0, 255, 133, 0.3);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
	}

	.analysis-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1.5rem;
	}

	.header-symbol {
		font-size: 1.5rem;
		color: #00ff85;
		text-shadow: 0 0 15px #00ff85;
		animation: symbolFloat 3s ease-in-out infinite;
	}

	.analysis-header h3 {
		flex: 1;
		margin: 0 0 0 1rem;
		font-size: 1.1rem;
		font-weight: 700;
		color: #00ff85;
		letter-spacing: 0.05em;
	}

	.analysis-indicator {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		animation: indicatorPulse 2s ease-in-out infinite;
		box-shadow: 0 0 10px currentColor;
	}

	.analysis-content {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.compliance-item {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		padding: 1rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		backdrop-filter: blur(10px);
	}

	.compliance-item.optimal {
		border-left: 4px solid #00ff85;
		background: linear-gradient(135deg, rgba(0, 255, 133, 0.05), rgba(0, 0, 0, 0.4));
	}

	.compliance-item.partial {
		border-left: 4px solid #ffaa00;
		background: linear-gradient(135deg, rgba(255, 170, 0, 0.05), rgba(0, 0, 0, 0.4));
	}

	.compliance-item.critical {
		border-left: 4px solid #ff0066;
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.05), rgba(0, 0, 0, 0.4));
	}

	.item-icon {
		font-size: 1rem;
		color: #00ff85;
		text-shadow: 0 0 10px #00ff85;
		margin-top: 0.1rem;
		flex-shrink: 0;
	}

	.compliance-item.partial .item-icon {
		color: #ffaa00;
		text-shadow: 0 0 10px #ffaa00;
	}

	.compliance-item.critical .item-icon {
		color: #ff0066;
		text-shadow: 0 0 10px #ff0066;
	}

	.item-text {
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.8);
		line-height: 1.4;
		font-weight: 400;
	}

	.interface-footer {
		padding-top: 1rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		text-align: center;
	}

	.footer-line {
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(0, 255, 133, 0.6), 
			transparent);
		margin-bottom: 1rem;
	}

	.protocol-notice {
		font-size: 0.7rem;
		color: #00ff85;
		font-weight: 600;
		letter-spacing: 0.05em;
		text-shadow: 0 0 8px #00ff85;
	}

	@keyframes cmdbPulse {
		0%, 100% { 
			box-shadow: 0 0 20px rgba(0, 255, 133, 0.3);
			transform: scale(1);
		}
		50% { 
			box-shadow: 0 0 40px rgba(0, 255, 133, 0.6);
			transform: scale(1.02);
		}
	}

	@keyframes badgePulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.1); }
	}

	@keyframes barScan {
		0%, 100% { height: 20%; opacity: 0.3; }
		50% { height: 100%; opacity: 1; }
	}

	@keyframes segmentPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}

	@keyframes symbolFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-3px); }
	}

	@keyframes indicatorPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.2); }
	}

	@media (max-width: 1200px) {
		.registration-display {
			grid-template-columns: 1fr;
			gap: 2rem;
			text-align: center;
		}
	}

	@media (max-width: 768px) {
		.status-header {
			flex-direction: column;
			gap: 1.5rem;
			text-align: center;
		}

		.status-info {
			margin-left: 0;
		}

		.compliance-item {
			flex-direction: column;
			gap: 0.5rem;
		}
	}
</style>