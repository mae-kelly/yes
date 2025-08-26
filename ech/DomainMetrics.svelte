<!-- DomainMetrics.svelte - Optimized for Maximum Data Density -->
<script>
	import { onMount } from 'svelte';

	let data = {};
	let loading = true;
	let error = null;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/domain_metrics');
			const result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			error = 'DOMAIN MATRIX COMPROMISED';
			loading = false;
		}
	});

	$: totalDomains = data.domain_analysis ? 
		Object.values(data.domain_analysis).reduce((a, b) => a + b, 0) : 0;
	$: dominantDomain = data.domain_analysis ? 
		Object.entries(data.domain_analysis).sort((a, b) => b[1] - a[1])[0] : null;
	$: oneDcPercentage = data.domain_analysis ? 
		Math.round((data.domain_analysis['1dc'] || 0) / totalDomains * 100) : 0;
	$: feadPercentage = data.domain_analysis ? 
		Math.round((data.domain_analysis['fead'] || 0) / totalDomains * 100) : 0;
	$: otherPercentage = data.domain_analysis ? 
		Math.round((data.domain_analysis['other'] || 0) / totalDomains * 100) : 0;

	function getCircularProgress(percentage) {
		const radius = 45;
		const circumference = 2 * Math.PI * radius;
		const strokeDashoffset = circumference - (percentage / 100) * circumference;
		return { strokeDashoffset };
	}
</script>

<div class="domain-warfare-matrix">
	<div class="matrix-header">
		<div class="command-center">
			<div class="hologram-core">
				<div class="holo-rings">
					<div class="holo-ring ring-1"></div>
					<div class="holo-ring ring-2"></div>
					<div class="holo-ring ring-3"></div>
				</div>
				<div class="core-symbol">◆</div>
			</div>
			<div class="command-info">
				<h2 class="matrix-title">1DC vs FEAD</h2>
				<p class="matrix-subtitle">DOMAIN CLASSIFICATION WARFARE</p>
			</div>
			<div class="threat-assessment">
				<div class="assessment-ring"></div>
				<span class="assessment-text">CLASSIFIED</span>
			</div>
		</div>
	</div>

	{#if loading}
		<div class="neural-loading">
			<div class="loading-core">
				<div class="core-rings">
					{#each Array(4) as _, i}
						<div class="loading-ring" style="--delay: {i * 0.3}s; --size: {45 + i * 15}px"></div>
					{/each}
				</div>
				<div class="core-nexus">◆</div>
			</div>
			<div class="loading-sequence">ANALYZING DOMAIN STRUCTURES...</div>
		</div>
	{:else if error}
		<div class="error-state">
			<div class="error-core">
				<div class="error-ring"></div>
				<div class="error-symbol">⚠</div>
			</div>
			<div class="error-message">CRITICAL ERROR: {error}</div>
		</div>
	{:else}
		<div class="warfare-interface">
			<div class="battlefield-overview">
				<div class="tactical-display">
					<div class="radar-scope">
						<svg width="200" height="200" viewBox="0 0 200 200" class="domain-radar">
							<defs>
								<radialGradient id="radarGradient">
									<stop offset="0%" style="stop-color:rgba(255,0,255,0.3);stop-opacity:1" />
									<stop offset="100%" style="stop-color:rgba(0,255,255,0.1);stop-opacity:0" />
								</radialGradient>
								<filter id="radarGlow">
									<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
									<feMerge>
										<feMergeNode in="coloredBlur"/>
										<feMergeNode in="SourceGraphic"/>
									</feMerge>
								</filter>
							</defs>
							
							<!-- Radar background -->
							<circle cx="100" cy="100" r="95" fill="url(#radarGradient)" opacity="0.3"/>
							
							<!-- Radar grid -->
							<g stroke="rgba(0, 255, 255, 0.2)" stroke-width="1" fill="none">
								<circle cx="100" cy="100" r="35"/>
								<circle cx="100" cy="100" r="65"/>
								<circle cx="100" cy="100" r="95"/>
								<line x1="5" y1="100" x2="195" y2="100"/>
								<line x1="100" y1="5" x2="100" y2="195"/>
							</g>

							{#if data.domain_analysis && totalDomains > 0}
								<!-- 1DC Arc -->
								<circle 
									cx="100" cy="100" r="80" 
									fill="none" 
									stroke="#ff00ff" 
									stroke-width="6"
									stroke-dasharray="502"
									stroke-dashoffset={502 - (oneDcPercentage / 100) * 502}
									transform="rotate(-90 100 100)"
									filter="url(#radarGlow)"
									class="domain-arc onedc-arc"
								/>
								
								<!-- FEAD Arc -->
								<circle 
									cx="100" cy="100" r="65" 
									fill="none" 
									stroke="#00ffff" 
									stroke-width="6"
									stroke-dasharray="408"
									stroke-dashoffset={408 - (feadPercentage / 100) * 408}
									transform="rotate(-90 100 100)"
									filter="url(#radarGlow)"
									class="domain-arc fead-arc"
								/>
								
								<!-- Other Arc -->
								<circle 
									cx="100" cy="100" r="50" 
									fill="none" 
									stroke="#0096ff" 
									stroke-width="6"
									stroke-dasharray="314"
									stroke-dashoffset={314 - (otherPercentage / 100) * 314}
									transform="rotate(-90 100 100)"
									filter="url(#radarGlow)"
									class="domain-arc other-arc"
								/>
							{/if}
							
							<!-- Central hub -->
							<circle cx="100" cy="100" r="20" fill="rgba(0, 0, 0, 0.8)" stroke="#ff00ff" stroke-width="1"/>
							<text x="100" y="105" text-anchor="middle" fill="#ff00ff" font-size="10" font-family="Orbitron" font-weight="700">
								DOM
							</text>
						</svg>
						
						<!-- Radar sweep -->
						<div class="radar-sweep"></div>
					</div>

					<div class="tactical-readouts">
						<div class="readout-cluster">
							<div class="readout-node onedc-node">
								<div class="node-frame">
									<div class="node-indicator"></div>
								</div>
								<div class="node-data">
									<div class="node-label">1DC</div>
									<div class="node-value">{oneDcPercentage}%</div>
									<div class="node-count">{data.domain_analysis ? data.domain_analysis['1dc'] || 0 : 0}</div>
								</div>
							</div>
							
							<div class="readout-node fead-node">
								<div class="node-frame">
									<div class="node-indicator"></div>
								</div>
								<div class="node-data">
									<div class="node-label">FEAD</div>
									<div class="node-value">{feadPercentage}%</div>
									<div class="node-count">{data.domain_analysis ? data.domain_analysis['fead'] || 0 : 0}</div>
								</div>
							</div>
							
							<div class="readout-node other-node">
								<div class="node-frame">
									<div class="node-indicator"></div>
								</div>
								<div class="node-data">
									<div class="node-label">OTHER</div>
									<div class="node-value">{otherPercentage}%</div>
									<div class="node-count">{data.domain_analysis ? data.domain_analysis['other'] || 0 : 0}</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div class="command-stats">
					<div class="stat-terminal">
						<div class="terminal-frame">
							<div class="terminal-header">TOTAL</div>
							<div class="terminal-value">{totalDomains.toLocaleString()}</div>
							<div class="terminal-bars">
								{#each Array(6) as _, i}
									<div class="bar" style="height: {Math.random() * 100}%; animation-delay: {i * 0.1}s"></div>
								{/each}
							</div>
						</div>
					</div>
					
					<div class="stat-terminal">
						<div class="terminal-frame">
							<div class="terminal-header">DOMINANT</div>
							<div class="terminal-value">{dominantDomain ? dominantDomain[0].toUpperCase() : 'N/A'}</div>
							<div class="terminal-graph">
								<div class="graph-line"></div>
								<div class="graph-points">
									{#each Array(8) as _, i}
										<div class="point" style="left: {i * 12.5}%; bottom: {Math.random() * 80}%"></div>
									{/each}
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<div class="warfare-analysis">
				<div class="analysis-header">
					<div class="header-symbol">◈</div>
					<h3>WARFARE ANALYSIS</h3>
					<div class="signal-bars">
						{#each Array(4) as _, i}
							<div class="signal-bar" style="animation-delay: {i * 0.1}s"></div>
						{/each}
					</div>
				</div>
				
				<div class="battle-grid">
					<div class="domain-sector onedc-sector">
						<div class="sector-header">
							<div class="sector-icon">◆</div>
							<div class="sector-title">1DC</div>
						</div>
						<div class="sector-metrics">
							<div class="metric-display">
								<div class="metric-bar">
									<div class="bar-fill onedc-fill" style="width: {oneDcPercentage}%"></div>
								</div>
								<div class="metric-stats">
									<span class="stat-primary">{oneDcPercentage}%</span>
									<span class="stat-secondary">{data.domain_analysis ? data.domain_analysis['1dc'] || 0 : 0}</span>
								</div>
							</div>
						</div>
						<div class="sector-status {oneDcPercentage > feadPercentage ? 'dominant' : 'contested'}">
							{oneDcPercentage > feadPercentage ? 'DOM' : 'CON'}
						</div>
					</div>

					<div class="domain-sector fead-sector">
						<div class="sector-header">
							<div class="sector-icon">◇</div>
							<div class="sector-title">FEAD</div>
						</div>
						<div class="sector-metrics">
							<div class="metric-display">
								<div class="metric-bar">
									<div class="bar-fill fead-fill" style="width: {feadPercentage}%"></div>
								</div>
								<div class="metric-stats">
									<span class="stat-primary">{feadPercentage}%</span>
									<span class="stat-secondary">{data.domain_analysis ? data.domain_analysis['fead'] || 0 : 0}</span>
								</div>
							</div>
						</div>
						<div class="sector-status {feadPercentage > oneDcPercentage ? 'dominant' : 'contested'}">
							{feadPercentage > oneDcPercentage ? 'DOM' : 'CON'}
						</div>
					</div>

					<div class="domain-sector other-sector">
						<div class="sector-header">
							<div class="sector-icon">◎</div>
							<div class="sector-title">OTHER</div>
						</div>
						<div class="sector-metrics">
							<div class="metric-display">
								<div class="metric-bar">
									<div class="bar-fill other-fill" style="width: {otherPercentage}%"></div>
								</div>
								<div class="metric-stats">
									<span class="stat-primary">{otherPercentage}%</span>
									<span class="stat-secondary">{data.domain_analysis ? data.domain_analysis['other'] || 0 : 0}</span>
								</div>
							</div>
						</div>
						<div class="sector-status neutral">
							NEU
						</div>
					</div>
				</div>
			</div>

			<div class="intel-summary">
				<div class="summary-header">
					<div class="header-symbol">◉</div>
					<h3>TACTICAL INTELLIGENCE</h3>
				</div>
				
				<div class="intel-grid">
					{#if dominantDomain}
						<div class="intel-item">
							<div class="item-marker">▶</div>
							<div class="item-text">
								Primary: <strong style="color: #ff00ff">{dominantDomain[0].toUpperCase()}</strong> ({dominantDomain[1].toLocaleString()})
							</div>
						</div>
						
						<div class="intel-item">
							<div class="item-marker">▶</div>
							<div class="item-text">
								Status: <strong style="color: #00ffff">
								{oneDcPercentage > feadPercentage ? '1DC DOM' : feadPercentage > oneDcPercentage ? 'FEAD SUP' : 'BALANCED'}</strong>
							</div>
						</div>
						
						<div class="intel-item">
							<div class="item-marker">▶</div>
							<div class="item-text">
								Total: <strong style="color: #0096ff">{totalDomains.toLocaleString()}</strong> domains
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}

	<div class="interface-footer">
		<div class="footer-line"></div>
		<div class="classification-notice">
			◆ DOMAIN WARFARE INTELLIGENCE ACTIVE
		</div>
	</div>
</div>

<style>
	.domain-warfare-matrix {
		width: 100%;
		height: 100%;
		font-family: 'Orbitron', 'Exo 2', monospace;
		color: #fff;
		display: flex;
		flex-direction: column;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		font-size: 0.65rem;
	}

	.matrix-header {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(255, 0, 255, 0.05) 50%,
			rgba(0, 255, 255, 0.05) 100%);
		border: 1px solid #ff00ff;
		border-radius: 8px;
		padding: 0.8rem 1.2rem;
		margin-bottom: 0.8rem;
		backdrop-filter: blur(20px);
		box-shadow: 0 0 25px rgba(255, 0, 255, 0.2);
	}

	.command-center {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.hologram-core {
		position: relative;
		width: 50px;
		height: 50px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.holo-rings {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.holo-ring {
		position: absolute;
		border-radius: 50%;
		border: 1px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: holoRotate 8s linear infinite;
	}

	.ring-1 {
		width: 50px;
		height: 50px;
		border-color: #ff00ff;
		opacity: 0.8;
	}

	.ring-2 {
		width: 38px;
		height: 38px;
		border-color: #00ffff;
		opacity: 0.6;
		animation-direction: reverse;
		animation-duration: 6s;
	}

	.ring-3 {
		width: 26px;
		height: 26px;
		border-color: #0096ff;
		animation-duration: 4s;
	}

	.core-symbol {
		position: relative;
		z-index: 3;
		font-size: 1.3rem;
		color: #ff00ff;
		text-shadow: 0 0 12px #ff00ff;
		animation: coreGlow 3s ease-in-out infinite;
	}

	.command-info {
		flex: 1;
		margin-left: 1.2rem;
	}

	.matrix-title {
		font-size: 1rem;
		font-weight: 700;
		color: #fff;
		margin: 0;
		text-shadow: 0 0 10px rgba(255, 0, 255, 0.5);
		letter-spacing: 0.08em;
	}

	.matrix-subtitle {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		margin: 0.2rem 0 0 0;
		font-weight: 300;
	}

	.threat-assessment {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		padding: 0.6rem 1rem;
		background: linear-gradient(135deg, 
			rgba(255, 0, 0, 0.1), 
			rgba(255, 100, 100, 0.05));
		border: 1px solid #ff0066;
		border-radius: 6px;
		backdrop-filter: blur(10px);
	}

	.assessment-ring {
		width: 10px;
		height: 10px;
		background: #ff0066;
		border-radius: 50%;
		animation: assessmentPulse 2s ease-in-out infinite;
		box-shadow: 0 0 10px #ff0066;
	}

	.assessment-text {
		font-size: 0.6rem;
		color: #ff0066;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-shadow: 0 0 8px #ff0066;
	}

	.neural-loading {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1.2rem;
	}

	.loading-core {
		position: relative;
		width: 120px;
		height: 120px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.core-rings {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.loading-ring {
		position: absolute;
		width: var(--size);
		height: var(--size);
		border: 2px solid transparent;
		border-top: 2px solid #ff00ff;
		border-right: 2px solid #00ffff;
		border-radius: 50%;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: loadingSpin 3s linear infinite;
		animation-delay: var(--delay);
	}

	.core-nexus {
		position: relative;
		z-index: 3;
		font-size: 1.8rem;
		color: #ff00ff;
		text-shadow: 0 0 20px #ff00ff;
		animation: nexusGlow 2s ease-in-out infinite;
	}

	.loading-sequence {
		color: #ff00ff;
		font-size: 0.8rem;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-shadow: 0 0 10px #ff00ff;
	}

	.error-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1.2rem;
	}

	.error-core {
		position: relative;
		width: 70px;
		height: 70px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.error-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 3px solid #ff0066;
		border-radius: 50%;
		animation: errorPulse 1.5s ease-in-out infinite;
	}

	.error-symbol {
		font-size: 1.8rem;
		color: #ff0066;
		text-shadow: 0 0 15px #ff0066;
		z-index: 2;
	}

	.error-message {
		color: #ff0066;
		font-size: 0.8rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-shadow: 0 0 10px #ff0066;
	}

	.warfare-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1.2rem;
	}

	.battlefield-overview {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 2rem;
		align-items: center;
	}

	.tactical-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
	}

	.radar-scope {
		position: relative;
		width: 200px;
		height: 200px;
		background: radial-gradient(circle, rgba(0, 0, 0, 0.8), rgba(255, 0, 255, 0.02));
		border: 2px solid #ff00ff;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}

	.domain-radar {
		width: 100%;
		height: 100%;
		filter: drop-shadow(0 0 15px rgba(255, 0, 255, 0.3));
	}

	.radar-sweep {
		position: absolute;
		width: 2px;
		height: 100px;
		background: linear-gradient(180deg, #ff00ff, transparent);
		top: 50%;
		left: 50%;
		transform-origin: bottom center;
		transform: translate(-50%, -100%);
		animation: radarSweep 4s linear infinite;
		box-shadow: 0 0 8px #ff00ff;
	}

	.domain-arc {
		stroke-linecap: round;
		transition: stroke-dashoffset 2s cubic-bezier(0.4, 0, 0.2, 1);
		animation: arcGlow 3s ease-in-out infinite;
	}

	.onedc-arc {
		animation-delay: 0s;
	}

	.fead-arc {
		animation-delay: 1s;
	}

	.other-arc {
		animation-delay: 2s;
	}

	.tactical-readouts {
		width: 100%;
	}

	.readout-cluster {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.readout-node {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		padding: 0.6rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 255, 255, 0.02));
		border: 1px solid;
		border-radius: 6px;
		backdrop-filter: blur(10px);
		transition: all 0.3s ease;
		min-height: 40px;
	}

	.onedc-node {
		border-color: #ff00ff;
	}

	.fead-node {
		border-color: #00ffff;
	}

	.other-node {
		border-color: #0096ff;
	}

	.readout-node:hover {
		transform: translateX(5px);
		box-shadow: 0 0 20px rgba(255, 0, 255, 0.3);
	}

	.node-frame {
		position: relative;
		width: 30px;
		height: 30px;
		border: 1px solid;
		border-radius: 6px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.onedc-node .node-frame {
		border-color: #ff00ff;
	}

	.fead-node .node-frame {
		border-color: #00ffff;
	}

	.other-node .node-frame {
		border-color: #0096ff;
	}

	.node-indicator {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		animation: nodeIndicatorPulse 2s ease-in-out infinite;
	}

	.onedc-node .node-indicator {
		background: #ff00ff;
		box-shadow: 0 0 10px #ff00ff;
	}

	.fead-node .node-indicator {
		background: #00ffff;
		box-shadow: 0 0 10px #00ffff;
	}

	.other-node .node-indicator {
		background: #0096ff;
		box-shadow: 0 0 10px #0096ff;
	}

	.node-data {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.node-label {
		font-size: 0.6rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.9);
		letter-spacing: 0.03em;
	}

	.node-value {
		font-size: 1rem;
		font-weight: 700;
		text-shadow: 0 0 8px currentColor;
	}

	.onedc-node .node-value {
		color: #ff00ff;
	}

	.fead-node .node-value {
		color: #00ffff;
	}

	.other-node .node-value {
		color: #0096ff;
	}

	.node-count {
		font-size: 0.5rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.command-stats {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.stat-terminal {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 255, 255, 0.03));
		border: 1px solid #00ffff;
		border-radius: 6px;
		padding: 0.8rem;
		backdrop-filter: blur(10px);
	}

	.terminal-frame {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		align-items: center;
	}

	.terminal-header {
		font-size: 0.5rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.08em;
	}

	.terminal-value {
		font-size: 1.2rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 10px #00ffff;
	}

	.terminal-bars {
		display: flex;
		gap: 0.2rem;
		height: 25px;
		align-items: flex-end;
	}

	.bar {
		width: 4px;
		background: linear-gradient(180deg, #00ffff, #0096ff);
		border-radius: 2px;
		animation: barPulse 2s ease-in-out infinite;
		box-shadow: 0 0 6px rgba(0, 255, 255, 0.5);
	}

	.terminal-graph {
		position: relative;
		width: 80px;
		height: 25px;
		border: 1px solid rgba(0, 255, 255, 0.2);
		background: rgba(0, 0, 0, 0.4);
		border-radius: 3px;
	}

	.graph-line {
		position: absolute;
		top: 50%;
		left: 0;
		width: 100%;
		height: 1px;
		background: linear-gradient(90deg, transparent, #00ffff, transparent);
		animation: graphPulse 3s ease-in-out infinite;
	}

	.graph-points {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.point {
		position: absolute;
		width: 2px;
		height: 2px;
		background: #00ffff;
		border-radius: 50%;
		box-shadow: 0 0 4px #00ffff;
		animation: pointFlicker 2s ease-in-out infinite;
	}

	.warfare-analysis {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.02));
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 8px;
		padding: 0.8rem;
		backdrop-filter: blur(20px);
	}

	.analysis-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.8rem;
	}

	.header-symbol {
		font-size: 1rem;
		color: #00ffff;
		text-shadow: 0 0 10px #00ffff;
		animation: symbolFloat 3s ease-in-out infinite;
	}

	.analysis-header h3 {
		flex: 1;
		margin: 0 0 0 0.6rem;
		font-size: 0.8rem;
		font-weight: 700;
		color: #00ffff;
		letter-spacing: 0.03em;
	}

	.signal-bars {
		display: flex;
		gap: 0.15rem;
		align-items: flex-end;
	}

	.signal-bar {
		width: 3px;
		background: #00ffff;
		border-radius: 1px;
		animation: signalPulse 1.5s ease-in-out infinite;
		box-shadow: 0 0 4px #00ffff;
	}

	.signal-bar:nth-child(1) { height: 8px; }
	.signal-bar:nth-child(2) { height: 12px; }
	.signal-bar:nth-child(3) { height: 16px; }
	.signal-bar:nth-child(4) { height: 20px; }

	.battle-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 0.8rem;
	}

	.domain-sector {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.02));
		border: 1px solid;
		border-radius: 6px;
		padding: 0.8rem;
		transition: all 0.3s ease;
		min-height: 120px;
	}

	.onedc-sector {
		border-color: #ff00ff;
	}

	.fead-sector {
		border-color: #00ffff;
	}

	.other-sector {
		border-color: #0096ff;
	}

	.domain-sector:hover {
		transform: translateY(-3px);
		box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
	}

	.sector-header {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		margin-bottom: 0.6rem;
	}

	.sector-icon {
		font-size: 1rem;
		text-shadow: 0 0 8px currentColor;
	}

	.onedc-sector .sector-icon {
		color: #ff00ff;
	}

	.fead-sector .sector-icon {
		color: #00ffff;
	}

	.other-sector .sector-icon {
		color: #0096ff;
	}

	.sector-title {
		font-size: 0.7rem;
		font-weight: 700;
		color: #fff;
		letter-spacing: 0.03em;
	}

	.sector-metrics {
		margin-bottom: 0.6rem;
	}

	.metric-display {
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
	}

	.bar-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 2s cubic-bezier(0.4, 0, 0.2, 1);
		position: relative;
		overflow: hidden;
	}

	.onedc-fill {
		background: linear-gradient(90deg, #ff00ff, #cc0088);
		box-shadow: 0 0 12px rgba(255, 0, 255, 0.5);
	}

	.fead-fill {
		background: linear-gradient(90deg, #00ffff, #0088cc);
		box-shadow: 0 0 12px rgba(0, 255, 255, 0.5);
	}

	.other-fill {
		background: linear-gradient(90deg, #0096ff, #0066cc);
		box-shadow: 0 0 12px rgba(0, 150, 255, 0.5);
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

	.metric-stats {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.stat-primary {
		font-size: 1rem;
		font-weight: 700;
		text-shadow: 0 0 8px currentColor;
	}

	.onedc-sector .stat-primary {
		color: #ff00ff;
	}

	.fead-sector .stat-primary {
		color: #00ffff;
	}

	.other-sector .stat-primary {
		color: #0096ff;
	}

	.stat-secondary {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 400;
	}

	.sector-status {
		padding: 0.3rem 0.6rem;
		border-radius: 3px;
		font-size: 0.5rem;
		font-weight: 700;
		text-align: center;
		letter-spacing: 0.08em;
		text-shadow: 0 0 6px currentColor;
	}

	.sector-status.dominant {
		background: rgba(0, 255, 133, 0.1);
		color: #00ff85;
		border: 1px solid #00ff85;
	}

	.sector-status.contested {
		background: rgba(255, 170, 0, 0.1);
		color: #ffaa00;
		border: 1px solid #ffaa00;
	}

	.sector-status.neutral {
		background: rgba(0, 150, 255, 0.1);
		color: #0096ff;
		border: 1px solid #0096ff;
	}

	.intel-summary {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 0, 255, 0.02));
		border: 1px solid rgba(255, 0, 255, 0.3);
		border-radius: 8px;
		padding: 0.8rem;
		backdrop-filter: blur(20px);
	}

	.summary-header {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		margin-bottom: 0.8rem;
	}

	.summary-header .header-symbol {
		color: #ff00ff;
		text-shadow: 0 0 10px #ff00ff;
	}

	.summary-header h3 {
		font-size: 0.8rem;
		font-weight: 700;
		color: #ff00ff;
		margin: 0;
		letter-spacing: 0.03em;
	}

	.intel-grid {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.intel-item {
		display: flex;
		align-items: flex-start;
		gap: 0.6rem;
		padding: 0.5rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		backdrop-filter: blur(10px);
	}

	.item-marker {
		font-size: 0.7rem;
		color: #ff00ff;
		text-shadow: 0 0 8px #ff00ff;
		margin-top: 0.05rem;
		flex-shrink: 0;
	}

	.item-text {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
		line-height: 1.3;
		font-weight: 400;
	}

	.item-text strong {
		color: #fff;
		font-weight: 600;
		text-shadow: 0 0 6px currentColor;
	}

	.interface-footer {
		margin-top: 1rem;
		padding-top: 0.6rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		text-align: center;
	}

	.footer-line {
		width: 100%;
		height: 1px;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(255, 0, 255, 0.6), 
			transparent);
		margin-bottom: 0.6rem;
	}

	.classification-notice {
		font-size: 0.5rem;
		color: #ff00ff;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-shadow: 0 0 6px #ff00ff;
	}

	@keyframes holoRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes coreGlow {
		0%, 100% { 
			text-shadow: 0 0 12px #ff00ff; 
			transform: scale(1);
		}
		50% { 
			text-shadow: 0 0 18px #ff00ff; 
			transform: scale(1.05);
		}
	}

	@keyframes assessmentPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.1); }
	}

	@keyframes loadingSpin {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes nexusGlow {
		0%, 100% { opacity: 0.9; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.1); }
	}

	@keyframes errorPulse {
		0%, 100% { 
			border-color: #ff0066; 
			box-shadow: 0 0 15px rgba(255, 0, 102, 0.3);
		}
		50% { 
			border-color: #ff3388; 
			box-shadow: 0 0 30px rgba(255, 0, 102, 0.6);
		}
	}

	@keyframes radarSweep {
		0% { transform: translate(-50%, -100%) rotate(0deg); }
		100% { transform: translate(-50%, -100%) rotate(360deg); }
	}

	@keyframes arcGlow {
		0%, 100% { filter: url(#radarGlow); }
		50% { filter: url(#radarGlow) brightness(1.2); }
	}

	@keyframes nodeIndicatorPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.2); }
	}

	@keyframes barPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}

	@keyframes graphPulse {
		0%, 100% { opacity: 0.5; }
		50% { opacity: 1; }
	}

	@keyframes pointFlicker {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}

	@keyframes symbolFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-2px); }
	}

	@keyframes signalPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	@keyframes barSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@media (max-width: 1200px) {
		.battlefield-overview {
			grid-template-columns: 1fr;
			gap: 1.2rem;
			text-align: center;
		}

		.battle-grid {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 768px) {
		.command-center {
			flex-direction: column;
			gap: 0.6rem;
			text-align: center;
		}

		.command-info {
			margin-left: 0;
		}

		.intel-item {
			flex-direction: column;
			gap: 0.3rem;
		}

		.font-size: 0.6rem;
	}