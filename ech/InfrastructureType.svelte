<!-- InfrastructureType.svelte -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/infrastructure_type');
			data = await response.json();
			loading = false;
		} catch (err) {
			loading = false;
		}
	});

	$: sortedInfra = data.infrastructure_matrix ? 
		Object.entries(data.infrastructure_matrix).sort((a, b) => b[1] - a[1]).slice(0, 16) : [];
	$: maxCount = sortedInfra.length > 0 ? Math.max(...sortedInfra.map(([,count]) => count)) : 1;

	function getThreatLevel(count) {
		const percentage = (count / maxCount) * 100;
		if (percentage >= 80) return { level: 'CRITICAL', color: '#ff00ff' };
		if (percentage >= 60) return { level: 'HIGH', color: '#ff0066' };
		if (percentage >= 40) return { level: 'MEDIUM', color: '#ffaa00' };
		return { level: 'LOW', color: '#00ffff' };
	}
</script>

<div class="infra-command-center">
	<div class="command-header">
		<div class="header-core">
			<div class="core-hexagon">
				<div class="hex-ring"></div>
				<div class="hex-center">⬢</div>
			</div>
			<div class="command-data">
				<h2 class="command-title">INFRASTRUCTURE</h2>
				<p class="command-subtitle">PIPE-SEPARATED CLASSIFICATION MATRIX</p>
			</div>
		</div>
		<div class="status-display">
			<div class="status-grid">
				<div class="status-cell">
					<div class="cell-value">{Object.keys(data.infrastructure_matrix || {}).length}</div>
					<div class="cell-label">TYPES</div>
				</div>
				<div class="status-cell">
					<div class="cell-value">{Object.values(data.infrastructure_matrix || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="cell-label">TOTAL</div>
				</div>
			</div>
		</div>
	</div>

	{#if loading}
		<div class="scanning-interface">
			<div class="scanner-core">
				<div class="scan-rings">
					{#each Array(5) as _, i}
						<div class="scan-ring" style="--delay: {i * 0.2}s; --size: {60 + i * 15}px"></div>
					{/each}
				</div>
				<div class="scan-symbol">⬢</div>
			</div>
			<div class="scan-text">ANALYZING INFRASTRUCTURE TYPES...</div>
		</div>
	{:else}
		<div class="infra-matrix">
			<div class="matrix-grid">
				{#each sortedInfra as [type, count], i}
					{@const threat = getThreatLevel(count)}
					<div class="infra-node" style="--node-color: {threat.color}; animation-delay: {i * 0.1}s">
						<div class="node-frame">
							<div class="frame-corners">
								<div class="corner tl"></div>
								<div class="corner tr"></div>
								<div class="corner bl"></div>
								<div class="corner br"></div>
							</div>
							
							<div class="node-header">
								<div class="node-icon">◈</div>
								<div class="threat-indicator {threat.level.toLowerCase()}">{threat.level}</div>
							</div>

							<div class="node-content">
								<div class="infra-type">{type.toUpperCase()}</div>
								<div class="infra-count">{count.toLocaleString()}</div>
								
								<div class="metric-bars">
									<div class="metric-bar">
										<div class="bar-fill" style="width: {(count / maxCount) * 100}%; background: {threat.color};"></div>
									</div>
									<div class="metric-percentage">{((count / maxCount) * 100).toFixed(1)}%</div>
								</div>
							</div>

							<div class="node-footer">
								<div class="connection-ports">
									{#each Array(6) as _, j}
										<div class="port" style="animation-delay: {j * 0.2}s"></div>
									{/each}
								</div>
							</div>

							<div class="node-glow"></div>
						</div>
					</div>
				{/each}
			</div>
		</div>

		<div class="analysis-panel">
			<div class="panel-header">
				<div class="header-symbol">◎</div>
				<h3>INFRASTRUCTURE ANALYSIS</h3>
			</div>
			<div class="analysis-grid">
				<div class="analysis-stat">
					<div class="stat-icon">▣</div>
					<div class="stat-data">
						<div class="stat-value">{sortedInfra.length}</div>
						<div class="stat-label">ACTIVE TYPES</div>
					</div>
				</div>
				<div class="analysis-stat">
					<div class="stat-icon">◆</div>
					<div class="stat-data">
						<div class="stat-value">{sortedInfra.length > 0 ? sortedInfra[0][0].toUpperCase() : 'N/A'}</div>
						<div class="stat-label">DOMINANT TYPE</div>
					</div>
				</div>
				<div class="analysis-stat">
					<div class="stat-icon">◈</div>
					<div class="stat-data">
						<div class="stat-value">{sortedInfra.length > 0 ? ((sortedInfra[0][1] / Object.values(data.infrastructure_matrix || {}).reduce((a, b) => a + b, 0)) * 100).toFixed(1) : 0}%</div>
						<div class="stat-label">DOMINANCE</div>
					</div>
				</div>
			</div>
		</div>
	{/if}

	<div class="interface-footer">
		<div class="footer-line"></div>
		<div class="protocol-notice">
			⬢ INFRASTRUCTURE CLASSIFICATION // ANALYSIS PROTOCOL ACTIVE
		</div>
	</div>
</div>

<style>
	.infra-command-center {
		width: 100%;
		height: 100%;
		font-family: 'Orbitron', 'Exo 2', monospace;
		color: #fff;
		display: flex;
		flex-direction: column;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.command-header {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(0, 150, 255, 0.05) 50%,
			rgba(0, 0, 0, 0.8) 100%);
		border: 2px solid #0096ff;
		border-radius: 12px;
		padding: 1.5rem 2rem;
		margin-bottom: 1.5rem;
		backdrop-filter: blur(20px);
		box-shadow: 0 0 40px rgba(0, 150, 255, 0.2);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.header-core {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.core-hexagon {
		position: relative;
		width: 80px;
		height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.hex-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 3px solid #0096ff;
		clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
		animation: hexRotate 8s linear infinite;
		opacity: 0.7;
	}

	.hex-center {
		font-size: 2rem;
		color: #0096ff;
		text-shadow: 0 0 20px #0096ff;
		animation: hexPulse 3s ease-in-out infinite;
		z-index: 2;
	}

	.command-data {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.command-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: #fff;
		margin: 0;
		text-shadow: 0 0 15px rgba(0, 150, 255, 0.5);
		letter-spacing: 0.1em;
	}

	.command-subtitle {
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.6);
		margin: 0;
		font-weight: 300;
	}

	.status-display {
		display: flex;
		align-items: center;
	}

	.status-grid {
		display: flex;
		gap: 2rem;
	}

	.status-cell {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 150, 255, 0.03));
		border: 2px solid rgba(0, 150, 255, 0.3);
		border-radius: 8px;
		padding: 1rem 1.5rem;
		text-align: center;
		backdrop-filter: blur(10px);
	}

	.cell-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #0096ff;
		text-shadow: 0 0 10px #0096ff;
		margin-bottom: 0.3rem;
	}

	.cell-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
	}

	.scanning-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.scanner-core {
		position: relative;
		width: 150px;
		height: 150px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.scan-rings {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.scan-ring {
		position: absolute;
		width: var(--size);
		height: var(--size);
		border: 2px solid #0096ff;
		clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: scanPulse 2s ease-in-out infinite;
		animation-delay: var(--delay);
		opacity: 0.6;
	}

	.scan-symbol {
		position: relative;
		z-index: 3;
		font-size: 2.5rem;
		color: #0096ff;
		text-shadow: 0 0 25px #0096ff;
		animation: scannerGlow 2s ease-in-out infinite;
	}

	.scan-text {
		color: #0096ff;
		font-size: 1.1rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-shadow: 0 0 15px #0096ff;
	}

	.infra-matrix {
		flex: 1;
		margin-bottom: 1.5rem;
	}

	.matrix-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1.5rem;
	}

	.infra-node {
		position: relative;
		animation: nodeEntrance 0.6s ease-out;
		animation-fill-mode: both;
		opacity: 0;
	}

	.node-frame {
		position: relative;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(255, 255, 255, 0.02) 100%);
		border: 2px solid var(--node-color);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
		transition: all 0.3s ease;
		overflow: hidden;
	}

	.infra-node:hover .node-frame {
		transform: translateY(-5px);
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 30px var(--node-color);
	}

	.frame-corners {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	.corner {
		position: absolute;
		width: 15px;
		height: 15px;
		border: 2px solid var(--node-color);
		opacity: 0.6;
	}

	.corner.tl {
		top: 8px;
		left: 8px;
		border-right: none;
		border-bottom: none;
		border-top-left-radius: 4px;
	}

	.corner.tr {
		top: 8px;
		right: 8px;
		border-left: none;
		border-bottom: none;
		border-top-right-radius: 4px;
	}

	.corner.bl {
		bottom: 8px;
		left: 8px;
		border-right: none;
		border-top: none;
		border-bottom-left-radius: 4px;
	}

	.corner.br {
		bottom: 8px;
		right: 8px;
		border-left: none;
		border-top: none;
		border-bottom-right-radius: 4px;
	}

	.node-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.node-icon {
		font-size: 1.5rem;
		color: var(--node-color);
		text-shadow: 0 0 10px var(--node-color);
		animation: iconFloat 3s ease-in-out infinite;
	}

	.threat-indicator {
		padding: 0.3rem 0.8rem;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 700;
		letter-spacing: 0.05em;
		border: 1px solid;
		text-shadow: 0 0 8px currentColor;
	}

	.threat-indicator.critical {
		background: rgba(255, 0, 255, 0.1);
		color: #ff00ff;
		border-color: #ff00ff;
	}

	.threat-indicator.high {
		background: rgba(255, 0, 102, 0.1);
		color: #ff0066;
		border-color: #ff0066;
	}

	.threat-indicator.medium {
		background: rgba(255, 170, 0, 0.1);
		color: #ffaa00;
		border-color: #ffaa00;
	}

	.threat-indicator.low {
		background: rgba(0, 255, 255, 0.1);
		color: #00ffff;
		border-color: #00ffff;
	}

	.node-content {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.infra-type {
		font-size: 1.1rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
		text-align: center;
	}

	.infra-count {
		font-size: 2rem;
		font-weight: 700;
		color: var(--node-color);
		text-shadow: 0 0 15px var(--node-color);
		text-align: center;
	}

	.metric-bars {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.metric-bar {
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

	.metric-percentage {
		font-size: 0.8rem;
		color: var(--node-color);
		text-align: right;
		font-weight: 600;
	}

	.node-footer {
		position: relative;
	}

	.connection-ports {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.port {
		width: 8px;
		height: 8px;
		background: var(--node-color);
		border-radius: 50%;
		animation: portPulse 2s ease-in-out infinite;
		box-shadow: 0 0 8px var(--node-color);
		opacity: 0.6;
	}

	.node-glow {
		position: absolute;
		top: -2px;
		left: -2px;
		right: -2px;
		bottom: -2px;
		background: radial-gradient(circle, var(--node-color), transparent);
		opacity: 0;
		transition: opacity 0.3s ease;
		border-radius: 12px;
		z-index: -1;
	}

	.infra-node:hover .node-glow {
		opacity: 0.1;
	}

	.analysis-panel {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 150, 255, 0.02));
		border: 2px solid rgba(0, 150, 255, 0.3);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
		margin-bottom: 1.5rem;
	}

	.panel-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.header-symbol {
		font-size: 1.5rem;
		color: #0096ff;
		text-shadow: 0 0 15px #0096ff;
		animation: symbolFloat 3s ease-in-out infinite;
	}

	.panel-header h3 {
		font-size: 1.1rem;
		font-weight: 700;
		color: #0096ff;
		margin: 0;
		letter-spacing: 0.05em;
	}

	.analysis-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
	}

	.analysis-stat {
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
		color: #0096ff;
		text-shadow: 0 0 10px #0096ff;
	}

	.stat-data {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.stat-value {
		font-size: 1.3rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
	}

	.stat-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
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
			rgba(0, 150, 255, 0.6), 
			transparent);
		margin-bottom: 1rem;
	}

	.protocol-notice {
		font-size: 0.7rem;
		color: #0096ff;
		font-weight: 600;
		letter-spacing: 0.05em;
		text-shadow: 0 0 8px #0096ff;
	}

	@keyframes hexRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes hexPulse {
		0%, 100% { 
			text-shadow: 0 0 20px #0096ff; 
			transform: scale(1);
		}
		50% { 
			text-shadow: 0 0 30px #0096ff; 
			transform: scale(1.05);
		}
	}

	@keyframes scanPulse {
		0%, 100% { 
			opacity: 0.3; 
			transform: translate(-50%, -50%) scale(1);
		}
		50% { 
			opacity: 0.8; 
			transform: translate(-50%, -50%) scale(1.05);
		}
	}

	@keyframes scannerGlow {
		0%, 100% { 
			text-shadow: 0 0 25px #0096ff; 
			transform: scale(1);
		}
		50% { 
			text-shadow: 0 0 35px #0096ff; 
			transform: scale(1.1);
		}
	}

	@keyframes nodeEntrance {
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

	@keyframes portPulse {
		0%, 100% { opacity: 0.6; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.2); }
	}

	@keyframes symbolFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-3px); }
	}

	@media (max-width: 1200px) {
		.command-header {
			flex-direction: column;
			gap: 1.5rem;
			text-align: center;
		}

		.matrix-grid {
			grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		}
	}

	@media (max-width: 768px) {
		.header-core {
			flex-direction: column;
			gap: 1rem;
		}

		.status-grid {
			flex-direction: column;
			gap: 1rem;
		}

		.analysis-grid {
			grid-template-columns: 1fr;
		}
	}
</style>