<!-- TaniumCoverage.svelte -->
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

	$: coverageColor = data.coverage_percentage >= 80 ? '#00ff85' : 
	                  data.coverage_percentage >= 60 ? '#ffaa00' : '#ff0066';
	$: coverageStatus = data.coverage_percentage >= 80 ? 'OPTIMAL' : 
	                   data.coverage_percentage >= 60 ? 'ACCEPTABLE' : 'CRITICAL';

	function getCircularProgress(percentage) {
		const circumference = 2 * Math.PI * 80;
		const strokeDashoffset = circumference - (percentage / 100) * circumference;
		return { strokeDashoffset };
	}
</script>

<div class="tanium-command-matrix">
	<div class="matrix-header">
		<div class="command-hub">
			<div class="hub-core">
				<div class="core-frame">⬠</div>
			</div>
			<div class="hub-data">
				<h2 class="hub-title">TANIUM COVERAGE</h2>
				<p class="hub-subtitle">AGENT DEPLOYMENT STATUS MATRIX</p>
			</div>
			<div class="status-beacon" style="--beacon-color: {coverageColor}">
				<div class="beacon-ring"></div>
				<span class="beacon-text">{coverageStatus}</span>
			</div>
		</div>
	</div>

	{#if loading}
		<div class="scanning-grid">
			<div class="grid-core">
				{#each Array(16) as _, i}
					<div class="grid-cell" style="animation-delay: {i * 0.1}s"></div>
				{/each}
			</div>
			<p class="scan-status">SCANNING TANIUM INFRASTRUCTURE...</p>
		</div>
	{:else if error}
		<div class="error-matrix">
			<div class="error-core">⚠</div>
			<p class="error-text">CRITICAL ERROR: {error}</p>
		</div>
	{:else}
		<div class="coverage-interface">
			<div class="coverage-display">
				<div class="main-radar">
					<svg width="200" height="200" viewBox="0 0 200 200">
						<defs>
							<radialGradient id="radarBg">
								<stop offset="0%" style="stop-color:rgba(0,255,133,0.3);stop-opacity:1" />
								<stop offset="100%" style="stop-color:rgba(0,255,133,0.1);stop-opacity:0" />
							</radialGradient>
							<filter id="coverageGlow">
								<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
								<feMerge>
									<feMergeNode in="coloredBlur"/>
									<feMergeNode in="SourceGraphic"/>
								</feMerge>
							</filter>
						</defs>
						
						<circle cx="100" cy="100" r="90" fill="url(#radarBg)"/>
						<circle cx="100" cy="100" r="80" fill="none" stroke="rgba(0, 255, 133, 0.2)" stroke-width="2"/>
						<circle cx="100" cy="100" r="60" fill="none" stroke="rgba(0, 255, 133, 0.1)" stroke-width="1"/>
						<circle cx="100" cy="100" r="40" fill="none" stroke="rgba(0, 255, 133, 0.1)" stroke-width="1"/>
						
						<circle 
							cx="100" cy="100" r="80" 
							fill="none" 
							stroke={coverageColor} 
							stroke-width="6"
							stroke-dasharray="502"
							stroke-dashoffset={getCircularProgress(data.coverage_percentage || 0).strokeDashoffset}
							transform="rotate(-90 100 100)"
							filter="url(#coverageGlow)"
						/>
						
						<circle cx="100" cy="100" r="25" fill="rgba(0, 0, 0, 0.8)" stroke={coverageColor} stroke-width="2"/>
						<text x="100" y="105" text-anchor="middle" fill={coverageColor} font-size="14" font-weight="700">
							{data.coverage_percentage || 0}%
						</text>
					</svg>
					<div class="radar-sweep"></div>
				</div>
				
				<div class="coverage-stats">
					<div class="stat-module">
						<div class="module-header">DEPLOYED</div>
						<div class="module-value" style="color: {coverageColor}">{(data.tanium_deployed || 0).toLocaleString()}</div>
						<div class="module-graph">
							{#each Array(8) as _, i}
								<div class="graph-bar" style="height: {Math.random() * 100}%; animation-delay: {i * 0.1}s"></div>
							{/each}
						</div>
					</div>
					
					<div class="stat-module">
						<div class="module-header">TOTAL ASSETS</div>
						<div class="module-value">{(data.total_assets || 0).toLocaleString()}</div>
						<div class="module-graph">
							{#each Array(8) as _, i}
								<div class="graph-bar" style="height: {Math.random() * 100}%; animation-delay: {i * 0.1}s"></div>
							{/each}
						</div>
					</div>
					
					<div class="stat-module">
						<div class="module-header">COVERAGE GAP</div>
						<div class="module-value" style="color: #ff0066">{((data.total_assets || 0) - (data.tanium_deployed || 0)).toLocaleString()}</div>
						<div class="module-graph">
							{#each Array(8) as _, i}
								<div class="graph-bar gap-bar" style="height: {Math.random() * 100}%; animation-delay: {i * 0.1}s"></div>
							{/each}
						</div>
					</div>
				</div>
			</div>

			<div class="threat-assessment">
				<div class="assessment-header">
					<div class="header-icon">◎</div>
					<h3>THREAT ASSESSMENT</h3>
					<div class="threat-indicator" style="background: {coverageColor}"></div>
				</div>
				<div class="assessment-content">
					{#if data.coverage_percentage >= 80}
						<div class="assessment-item optimal">
							<div class="item-marker">◯</div>
							<div class="item-text">OPTIMAL COVERAGE - Tanium deployment meets security standards</div>
						</div>
						<div class="assessment-item">
							<div class="item-marker">▶</div>
							<div class="item-text">Maintain current deployment levels and monitor for new assets</div>
						</div>
					{:else if data.coverage_percentage >= 60}
						<div class="assessment-item warning">
							<div class="item-marker">⚠</div>
							<div class="item-text">ACCEPTABLE COVERAGE - Monitor for potential security gaps</div>
						</div>
						<div class="assessment-item">
							<div class="item-marker">▶</div>
							<div class="item-text">Prioritize deployment to remaining {((data.total_assets || 0) - (data.tanium_deployed || 0)).toLocaleString()} assets</div>
						</div>
					{:else}
						<div class="assessment-item critical">
							<div class="item-marker">⚠</div>
							<div class="item-text">CRITICAL COVERAGE GAP - Immediate deployment required</div>
						</div>
						<div class="assessment-item">
							<div class="item-marker">▶</div>
							<div class="item-text">URGENT: Deploy Tanium to {((data.total_assets || 0) - (data.tanium_deployed || 0)).toLocaleString()} unprotected assets</div>
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}

	<div class="interface-footer">
		<div class="footer-line"></div>
		<div class="protocol-notice">
			⬠ TANIUM DEPLOYMENT // AGENT COVERAGE PROTOCOL ACTIVE
		</div>
	</div>
</div>

<style>
	.tanium-command-matrix {
		width: 100%;
		height: 100%;
		font-family: 'Orbitron', 'Exo 2', monospace;
		color: #fff;
		display: flex;
		flex-direction: column;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.matrix-header {
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
	}

	.command-hub {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.hub-core {
		width: 80px;
		height: 80px;
		background: radial-gradient(circle, rgba(0, 255, 133, 0.2), transparent);
		border: 3px solid #00ff85;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		animation: hubPulse 3s ease-in-out infinite;
	}

	.core-frame {
		font-size: 2rem;
		color: #00ff85;
		text-shadow: 0 0 20px #00ff85;
		animation: frameRotate 8s linear infinite;
	}

	.hub-data {
		flex: 1;
		margin-left: 2rem;
	}

	.hub-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: #fff;
		margin: 0;
		text-shadow: 0 0 15px rgba(0, 255, 133, 0.5);
		letter-spacing: 0.1em;
	}

	.hub-subtitle {
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.6);
		margin: 0.3rem 0 0 0;
		font-weight: 300;
	}

	.status-beacon {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem 1.5rem;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6), 
			rgba(255, 255, 255, 0.02));
		border: 2px solid var(--beacon-color);
		border-radius: 8px;
		backdrop-filter: blur(10px);
	}

	.beacon-ring {
		width: 15px;
		height: 15px;
		background: var(--beacon-color);
		border-radius: 50%;
		animation: beaconPulse 2s ease-in-out infinite;
		box-shadow: 0 0 15px var(--beacon-color);
	}

	.beacon-text {
		font-size: 0.8rem;
		color: var(--beacon-color);
		font-weight: 700;
		letter-spacing: 0.1em;
		text-shadow: 0 0 10px var(--beacon-color);
	}

	.scanning-grid {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.grid-core {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 0.5rem;
		width: 120px;
		height: 120px;
	}

	.grid-cell {
		background: #00ff85;
		border-radius: 2px;
		animation: cellFlicker 1.5s ease-in-out infinite;
		opacity: 0.3;
	}

	.scan-status {
		color: #00ff85;
		font-size: 1.1rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-shadow: 0 0 15px #00ff85;
	}

	.error-matrix {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.error-core {
		font-size: 4rem;
		color: #ff0066;
		text-shadow: 0 0 30px #ff0066;
		animation: errorPulse 1.5s ease-in-out infinite;
	}

	.error-text {
		color: #ff0066;
		font-size: 1.1rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		text-shadow: 0 0 15px #ff0066;
	}

	.coverage-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.coverage-display {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 3rem;
		align-items: center;
	}

	.main-radar {
		position: relative;
		width: 200px;
		height: 200px;
		background: radial-gradient(circle, rgba(0, 0, 0, 0.8), rgba(0, 255, 133, 0.02));
		border: 3px solid #00ff85;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}

	.radar-sweep {
		position: absolute;
		width: 2px;
		height: 100px;
		background: linear-gradient(180deg, #00ff85, transparent);
		top: 50%;
		left: 50%;
		transform-origin: bottom center;
		transform: translate(-50%, -100%);
		animation: radarSweep 4s linear infinite;
		box-shadow: 0 0 10px #00ff85;
	}

	.coverage-stats {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.stat-module {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 133, 0.03));
		border: 2px solid rgba(0, 255, 133, 0.3);
		border-radius: 8px;
		padding: 1.5rem;
		backdrop-filter: blur(10px);
	}

	.module-header {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		margin-bottom: 0.5rem;
		letter-spacing: 0.1em;
	}

	.module-value {
		font-size: 2rem;
		font-weight: 700;
		color: #00ff85;
		text-shadow: 0 0 15px currentColor;
		margin-bottom: 1rem;
	}

	.module-graph {
		display: flex;
		gap: 0.3rem;
		height: 30px;
		align-items: flex-end;
	}

	.graph-bar {
		width: 4px;
		background: linear-gradient(180deg, #00ff85, #007755);
		border-radius: 2px;
		animation: barPulse 2s ease-in-out infinite;
		box-shadow: 0 0 6px rgba(0, 255, 133, 0.5);
	}

	.gap-bar {
		background: linear-gradient(180deg, #ff0066, #cc0044);
		box-shadow: 0 0 6px rgba(255, 0, 102, 0.5);
	}

	.threat-assessment {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 133, 0.02));
		border: 2px solid rgba(0, 255, 133, 0.3);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
	}

	.assessment-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1.5rem;
	}

	.header-icon {
		font-size: 1.5rem;
		color: #00ff85;
		text-shadow: 0 0 15px #00ff85;
		animation: iconFloat 3s ease-in-out infinite;
	}

	.assessment-header h3 {
		flex: 1;
		margin: 0 0 0 1rem;
		font-size: 1.1rem;
		font-weight: 700;
		color: #00ff85;
		letter-spacing: 0.05em;
	}

	.threat-indicator {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		animation: indicatorPulse 2s ease-in-out infinite;
		box-shadow: 0 0 10px currentColor;
	}

	.assessment-content {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.assessment-item {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		padding: 1rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		backdrop-filter: blur(10px);
	}

	.assessment-item.optimal {
		border-left: 4px solid #00ff85;
		background: linear-gradient(135deg, rgba(0, 255, 133, 0.05), rgba(0, 0, 0, 0.4));
	}

	.assessment-item.warning {
		border-left: 4px solid #ffaa00;
		background: linear-gradient(135deg, rgba(255, 170, 0, 0.05), rgba(0, 0, 0, 0.4));
	}

	.assessment-item.critical {
		border-left: 4px solid #ff0066;
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.05), rgba(0, 0, 0, 0.4));
	}

	.item-marker {
		font-size: 1rem;
		color: #00ff85;
		text-shadow: 0 0 10px #00ff85;
		margin-top: 0.1rem;
		flex-shrink: 0;
	}

	.assessment-item.warning .item-marker {
		color: #ffaa00;
		text-shadow: 0 0 10px #ffaa00;
	}

	.assessment-item.critical .item-marker {
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

	@keyframes hubPulse {
		0%, 100% { 
			box-shadow: 0 0 20px rgba(0, 255, 133, 0.3);
			transform: scale(1);
		}
		50% { 
			box-shadow: 0 0 40px rgba(0, 255, 133, 0.6);
			transform: scale(1.02);
		}
	}

	@keyframes frameRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes beaconPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.1); }
	}

	@keyframes cellFlicker {
		0%, 100% { opacity: 0.3; background: #00ff85; }
		50% { opacity: 1; background: #fff; }
	}

	@keyframes errorPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.1); }
	}

	@keyframes radarSweep {
		0% { transform: translate(-50%, -100%) rotate(0deg); }
		100% { transform: translate(-50%, -100%) rotate(360deg); }
	}

	@keyframes barPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-3px); }
	}

	@keyframes indicatorPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.2); }
	}

	@media (max-width: 1200px) {
		.coverage-display {
			grid-template-columns: 1fr;
			gap: 2rem;
			text-align: center;
		}
	}

	@media (max-width: 768px) {
		.command-hub {
			flex-direction: column;
			gap: 1.5rem;
			text-align: center;
		}

		.hub-data {
			margin-left: 0;
		}

		.assessment-item {
			flex-direction: column;
			gap: 0.5rem;
		}
	}
</style>

<!-- Add remaining components here: RegionMetrics, CountryMetrics, etc. -->
<!-- Each would follow the same cyberpunk gaming aesthetic pattern -->
<!-- with unique color schemes and visual elements -->