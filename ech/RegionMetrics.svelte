<!-- RegionMetrics.svelte -->
<script>
	import { onMount } from 'svelte';
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/region_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Region metrics error:', err);
			loading = false;
		}
	});

	$: totalCoverage = data.total_coverage || 0;
	$: sortedRegions = data.global_surveillance ? 
		Object.entries(data.global_surveillance).sort((a, b) => b[1] - a[1]) : [];

	function getRegionColor(region) {
		const colors = {
			'north america': '#00ffff',
			'emea': '#ff00ff', 
			'latam': '#00ff85',
			'apac': '#0096ff'
		};
		return colors[region.toLowerCase()] || '#ffaa00';
	}

	function getCircularProgress(percentage) {
		const circumference = 2 * Math.PI * 40;
		const strokeDashoffset = circumference - (percentage / 100) * circumference;
		return { strokeDashoffset };
	}
</script>

<div class="global-command-matrix">
	<div class="matrix-header">
		<div class="command-core">
			<div class="global-hub">
				<div class="hub-rings">
					<div class="hub-ring outer-ring"></div>
					<div class="hub-ring middle-ring"></div>
					<div class="hub-ring inner-ring"></div>
				</div>
				<div class="hub-center">◉</div>
			</div>
			<div class="command-info">
				<h2 class="command-title">GLOBAL REGIONS</h2>
				<p class="command-subtitle">NORMALIZED SURVEILLANCE DISTRIBUTION</p>
			</div>
		</div>
		<div class="coverage-display">
			<div class="total-coverage">
				<div class="coverage-ring">
					<svg width="120" height="120" viewBox="0 0 120 120">
						<circle cx="60" cy="60" r="50" fill="none" stroke="rgba(0, 255, 255, 0.2)" stroke-width="2"/>
						<circle 
							cx="60" cy="60" r="50" 
							fill="none" 
							stroke="#00ffff" 
							stroke-width="4"
							stroke-dasharray="314"
							stroke-dashoffset={getCircularProgress(85).strokeDashoffset}
							transform="rotate(-90 60 60)"
						/>
					</svg>
					<div class="coverage-center">
						<div class="coverage-value">{totalCoverage.toLocaleString()}</div>
						<div class="coverage-label">TOTAL</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	{#if loading}
		<div class="scanning-globe">
			<div class="globe-core">
				<div class="scan-layers">
					{#each Array(6) as _, i}
						<div class="scan-layer" style="--delay: {i * 0.3}s; --size: {60 + i * 20}px"></div>
					{/each}
				</div>
				<div class="globe-symbol">🌐</div>
			</div>
			<div class="scan-text">ANALYZING GLOBAL REGIONS...</div>
		</div>
	{:else}
		<div class="regions-interface">
			<div class="world-map">
				<div class="map-grid">
					{#each sortedRegions as [region, count], i}
						{@const percentage = totalCoverage > 0 ? (count / totalCoverage * 100) : 0}
						<div class="region-sector" style="--region-color: {getRegionColor(region)}; animation-delay: {i * 0.2}s">
							<div class="sector-frame">
								<div class="frame-glow"></div>
								<div class="sector-header">
									<div class="region-icon">◈</div>
									<div class="region-name">{region.toUpperCase().replace('_', ' ')}</div>
									<div class="region-status">ACTIVE</div>
								</div>
								
								<div class="sector-metrics">
									<div class="metric-display">
										<div class="metric-value">{count.toLocaleString()}</div>
										<div class="metric-percentage">{percentage.toFixed(1)}%</div>
									</div>
									
									<div class="coverage-bar">
										<div class="bar-track">
											<div class="bar-fill" style="width: {percentage}%; background: {getRegionColor(region)};"></div>
										</div>
									</div>
								</div>

								<div class="sector-grid">
									{#each Array(12) as _, j}
										<div class="grid-dot" style="animation-delay: {j * 0.1}s; opacity: {Math.random()}"></div>
									{/each}
								</div>

								<div class="connection-nodes">
									{#each Array(4) as _, k}
										<div class="connection-node" style="--node-delay: {k * 0.2}s"></div>
									{/each}
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<div class="surveillance-summary">
				<div class="summary-header">
					<div class="header-symbol">◎</div>
					<h3>SURVEILLANCE SUMMARY</h3>
					<div class="signal-strength">
						{#each Array(5) as _, i}
							<div class="signal-bar" style="height: {(i + 1) * 20}%; animation-delay: {i * 0.1}s"></div>
						{/each}
					</div>
				</div>
				
				<div class="summary-grid">
					<div class="summary-stat">
						<div class="stat-icon">🌍</div>
						<div class="stat-data">
							<div class="stat-value">{sortedRegions.length}</div>
							<div class="stat-label">ACTIVE REGIONS</div>
						</div>
					</div>
					
					<div class="summary-stat">
						<div class="stat-icon">📡</div>
						<div class="stat-data">
							<div class="stat-value">{sortedRegions.length > 0 ? sortedRegions[0][0].toUpperCase() : 'N/A'}</div>
							<div class="stat-label">PRIMARY REGION</div>
						</div>
					</div>
					
					<div class="summary-stat">
						<div class="stat-icon">⚡</div>
						<div class="stat-data">
							<div class="stat-value">{sortedRegions.length > 0 ? ((sortedRegions[0][1] / totalCoverage) * 100).toFixed(1) : 0}%</div>
							<div class="stat-label">DOMINANCE</div>
						</div>
					</div>

					<div class="summary-stat">
						<div class="stat-icon">🔗</div>
						<div class="stat-data">
							<div class="stat-value">{(totalCoverage / sortedRegions.length || 0).toFixed(0)}</div>
							<div class="stat-label">AVG/REGION</div>
						</div>
					</div>
				</div>

				<div class="threat-matrix">
					<div class="matrix-title">REGIONAL THREAT MATRIX</div>
					<div class="threat-grid">
						{#each sortedRegions as [region, count]}
							{@const percentage = totalCoverage > 0 ? (count / totalCoverage * 100) : 0}
							{@const threatLevel = percentage > 40 ? 'HIGH' : percentage > 20 ? 'MEDIUM' : 'LOW'}
							{@const threatColor = percentage > 40 ? '#ff0066' : percentage > 20 ? '#ffaa00' : '#00ff85'}
							<div class="threat-item">
								<div class="threat-indicator" style="background: {threatColor}"></div>
								<div class="threat-region">{region.toUpperCase()}</div>
								<div class="threat-level" style="color: {threatColor}">{threatLevel}</div>
								<div class="threat-value">{percentage.toFixed(1)}%</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		</div>
	{/if}

	<div class="interface-footer">
		<div class="footer-line"></div>
		<div class="protocol-notice">
			◉ GLOBAL SURVEILLANCE // REGIONAL ANALYSIS PROTOCOL ACTIVE
		</div>
	</div>
</div>

<style>
	.global-command-matrix {
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
			rgba(0, 255, 255, 0.05) 50%,
			rgba(0, 0, 0, 0.8) 100%);
		border: 2px solid #00ffff;
		border-radius: 12px;
		padding: 1.5rem 2rem;
		margin-bottom: 1.5rem;
		backdrop-filter: blur(20px);
		box-shadow: 0 0 40px rgba(0, 255, 255, 0.2);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.command-core {
		display: flex;
		align-items: center;
		gap: 2rem;
	}

	.global-hub {
		position: relative;
		width: 100px;
		height: 100px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.hub-rings {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.hub-ring {
		position: absolute;
		border-radius: 50%;
		border: 2px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: ringRotate 10s linear infinite;
	}

	.outer-ring {
		width: 100px;
		height: 100px;
		border-color: #00ffff;
		opacity: 0.8;
	}

	.middle-ring {
		width: 75px;
		height: 75px;
		border-color: #0088cc;
		opacity: 0.6;
		animation-direction: reverse;
		animation-duration: 8s;
	}

	.inner-ring {
		width: 50px;
		height: 50px;
		border-color: #0066aa;
		animation-duration: 6s;
	}

	.hub-center {
		position: relative;
		z-index: 3;
		font-size: 2.5rem;
		color: #00ffff;
		text-shadow: 0 0 25px #00ffff;
		animation: hubPulse 3s ease-in-out infinite;
	}

	.command-info {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.command-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: #fff;
		margin: 0;
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}

	.command-subtitle {
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.6);
		margin: 0;
		font-weight: 300;
	}

	.coverage-display {
		display: flex;
		align-items: center;
	}

	.total-coverage {
		position: relative;
	}

	.coverage-ring {
		position: relative;
		width: 120px;
		height: 120px;
	}

	.coverage-center {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
	}

	.coverage-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 15px #00ffff;
	}

	.coverage-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.2rem;
		letter-spacing: 0.1em;
	}

	.scanning-globe {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.globe-core {
		position: relative;
		width: 200px;
		height: 200px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.scan-layers {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.scan-layer {
		position: absolute;
		width: var(--size);
		height: var(--size);
		border: 2px solid #00ffff;
		border-radius: 50%;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: layerPulse 3s ease-in-out infinite;
		animation-delay: var(--delay);
		opacity: 0.6;
	}

	.globe-symbol {
		position: relative;
		z-index: 3;
		font-size: 4rem;
		filter: hue-rotate(180deg) saturate(2);
		animation: globeGlow 2s ease-in-out infinite;
	}

	.scan-text {
		color: #00ffff;
		font-size: 1.1rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-shadow: 0 0 15px #00ffff;
	}

	.regions-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.world-map {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.02));
		border: 2px solid rgba(0, 255, 255, 0.3);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
	}

	.map-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
		gap: 1.5rem;
	}

	.region-sector {
		position: relative;
		animation: sectorEntrance 0.8s ease-out;
		animation-fill-mode: both;
		opacity: 0;
	}

	.sector-frame {
		position: relative;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(255, 255, 255, 0.02) 100%);
		border: 2px solid var(--region-color);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
		transition: all 0.3s ease;
		overflow: hidden;
	}

	.region-sector:hover .sector-frame {
		transform: translateY(-5px);
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 30px var(--region-color);
	}

	.frame-glow {
		position: absolute;
		top: -2px;
		left: -2px;
		right: -2px;
		bottom: -2px;
		background: radial-gradient(circle, var(--region-color), transparent);
		opacity: 0;
		transition: opacity 0.3s ease;
		border-radius: 12px;
		z-index: -1;
	}

	.region-sector:hover .frame-glow {
		opacity: 0.1;
	}

	.sector-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.region-icon {
		font-size: 1.5rem;
		color: var(--region-color);
		text-shadow: 0 0 10px var(--region-color);
		animation: iconFloat 3s ease-in-out infinite;
	}

	.region-name {
		font-size: 1rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
	}

	.region-status {
		padding: 0.3rem 0.8rem;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 700;
		background: rgba(0, 255, 133, 0.1);
		color: #00ff85;
		border: 1px solid #00ff85;
		text-shadow: 0 0 8px #00ff85;
	}

	.sector-metrics {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.metric-display {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.metric-value {
		font-size: 2rem;
		font-weight: 700;
		color: var(--region-color);
		text-shadow: 0 0 15px var(--region-color);
	}

	.metric-percentage {
		font-size: 1.2rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.8);
	}

	.coverage-bar {
		width: 100%;
	}

	.bar-track {
		height: 8px;
		background: rgba(0, 0, 0, 0.6);
		border-radius: 4px;
		overflow: hidden;
		border: 1px solid rgba(255, 255, 255, 0.1);
		position: relative;
	}

	.bar-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 2s cubic-bezier(0.4, 0, 0.2, 1);
		box-shadow: 0 0 15px currentColor;
		position: relative;
		overflow: hidden;
	}

	.bar-fill::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(255, 255, 255, 0.4), 
			transparent);
		animation: barSweep 3s linear infinite;
	}

	.sector-grid {
		display: grid;
		grid-template-columns: repeat(6, 1fr);
		gap: 0.3rem;
		margin-bottom: 1rem;
	}

	.grid-dot {
		width: 8px;
		height: 8px;
		background: var(--region-color);
		border-radius: 50%;
		animation: dotPulse 2s ease-in-out infinite;
		box-shadow: 0 0 6px var(--region-color);
	}

	.connection-nodes {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.connection-node {
		width: 12px;
		height: 12px;
		background: var(--region-color);
		clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
		animation: nodePulse 2s ease-in-out infinite;
		animation-delay: var(--node-delay);
		box-shadow: 0 0 8px var(--region-color);
		opacity: 0.7;
	}

	.surveillance-summary {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.02));
		border: 2px solid rgba(0, 255, 255, 0.3);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
	}

	.summary-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1.5rem;
	}

	.header-symbol {
		font-size: 1.5rem;
		color: #00ffff;
		text-shadow: 0 0 15px #00ffff;
		animation: symbolFloat 3s ease-in-out infinite;
	}

	.summary-header h3 {
		flex: 1;
		margin: 0 0 0 1rem;
		font-size: 1.1rem;
		font-weight: 700;
		color: #00ffff;
		letter-spacing: 0.05em;
	}

	.signal-strength {
		display: flex;
		gap: 0.2rem;
		align-items: flex-end;
	}

	.signal-bar {
		width: 4px;
		background: #00ffff;
		border-radius: 2px;
		animation: signalPulse 1.5s ease-in-out infinite;
		box-shadow: 0 0 6px #00ffff;
	}

	.summary-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.summary-stat {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		backdrop-filter: blur(10px);
	}

	.stat-icon {
		font-size: 1.5rem;
		filter: hue-rotate(180deg) saturate(2) brightness(1.5);
	}

	.stat-data {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.stat-value {
		font-size: 1.3rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 10px #00ffff;
	}

	.stat-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
	}

	.threat-matrix {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(255, 0, 102, 0.02));
		border: 1px solid rgba(255, 0, 102, 0.2);
		border-radius: 8px;
		padding: 1rem;
	}

	.matrix-title {
		font-size: 0.9rem;
		font-weight: 700;
		color: #ff0066;
		margin-bottom: 1rem;
		letter-spacing: 0.05em;
		text-shadow: 0 0 8px #ff0066;
	}

	.threat-grid {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.threat-item {
		display: grid;
		grid-template-columns: auto 1fr auto auto;
		gap: 1rem;
		align-items: center;
		padding: 0.5rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.01));
		border-radius: 4px;
	}

	.threat-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: threatPulse 2s ease-in-out infinite;
		box-shadow: 0 0 8px currentColor;
	}

	.threat-region {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.threat-level {
		font-size: 0.7rem;
		font-weight: 600;
		text-shadow: 0 0 8px currentColor;
	}

	.threat-value {
		font-size: 0.8rem;
		font-weight: 600;
		color: #fff;
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
			rgba(0, 255, 255, 0.6), 
			transparent);
		margin-bottom: 1rem;
	}

	.protocol-notice {
		font-size: 0.7rem;
		color: #00ffff;
		font-weight: 600;
		letter-spacing: 0.05em;
		text-shadow: 0 0 8px #00ffff;
	}

	@keyframes ringRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes hubPulse {
		0%, 100% { 
			text-shadow: 0 0 25px #00ffff; 
			transform: scale(1);
		}
		50% { 
			text-shadow: 0 0 35px #00ffff; 
			transform: scale(1.05);
		}
	}

	@keyframes layerPulse {
		0%, 100% { 
			opacity: 0.3; 
			transform: translate(-50%, -50%) scale(1);
		}
		50% { 
			opacity: 0.8; 
			transform: translate(-50%, -50%) scale(1.05);
		}
	}

	@keyframes globeGlow {
		0%, 100% { filter: hue-rotate(180deg) saturate(2) brightness(1.5); }
		50% { filter: hue-rotate(180deg) saturate(3) brightness(2); }
	}

	@keyframes sectorEntrance {
		0% { 
			opacity: 0; 
			transform: translateY(30px) scale(0.9);
		}
		100% { 
			opacity: 1; 
			transform: translateY(0) scale(1);
		}
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-3px); }
	}

	@keyframes barSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes dotPulse {
		0%, 100% { opacity: 0.6; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.2); }
	}

	@keyframes nodePulse {
		0%, 100% { opacity: 0.7; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.1); }
	}

	@keyframes symbolFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-3px); }
	}

	@keyframes signalPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	@keyframes threatPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.2); }
	}

	@media (max-width: 1200px) {
		.matrix-header {
			flex-direction: column;
			gap: 1.5rem;
			text-align: center;
		}

		.map-grid {
			grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		}
	}

	@media (max-width: 768px) {
		.command-core {
			flex-direction: column;
			gap: 1rem;
		}

		.summary-grid {
			grid-template-columns: 1fr;
		}

		.threat-item {
			grid-template-columns: 1fr;
			gap: 0.5rem;
			text-align: center;
		}
	}
</style>