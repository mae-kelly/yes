<!-- ech/DomainMetrics.svelte -->
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
		const radius = 80;
		const circumference = 2 * Math.PI * radius;
		const strokeDasharray = circumference;
		const strokeDashoffset = circumference - (percentage / 100) * circumference;
		return { strokeDasharray, strokeDashoffset };
	}
</script>

<div class="domain-matrix-core">
	<div class="matrix-header">
		<div class="header-hologram">
			<div class="holo-rings">
				<div class="holo-ring ring-1"></div>
				<div class="holo-ring ring-2"></div>
			</div>
			<div class="header-center">◆</div>
		</div>
		<div class="header-info">
			<h2 class="matrix-title">DOMAIN CLASSIFICATION MATRIX</h2>
			<p class="matrix-subtitle">1DC vs FEAD Neural Analysis Protocol</p>
		</div>
		<div class="classification-badge">
			<div class="badge-ring"></div>
			<span class="badge-text">CLASSIFIED</span>
		</div>
	</div>

	{#if loading}
		<div class="neural-loading">
			<div class="loading-hologram">
				<div class="loading-rings">
					<div class="loading-ring ring-outer"></div>
					<div class="loading-ring ring-middle"></div>
					<div class="loading-ring ring-inner"></div>
				</div>
				<div class="loading-core">◆</div>
			</div>
			<div class="loading-text">ANALYZING DOMAIN STRUCTURES...</div>
		</div>
	{:else if error}
		<div class="error-state">
			<div class="error-hologram">
				<div class="error-ring"></div>
				<div class="error-center">⚠</div>
			</div>
			<div class="error-text">CRITICAL ERROR: {error}</div>
		</div>
	{:else}
		<div class="matrix-content">
			<div class="domain-overview">
				<div class="central-hologram">
					<svg width="220" height="220" viewBox="0 0 220 220" class="domain-visualization">
						<defs>
							<radialGradient id="centerGradient">
								<stop offset="0%" style="stop-color:rgba(0,255,255,0.3);stop-opacity:1" />
								<stop offset="100%" style="stop-color:rgba(255,0,255,0.1);stop-opacity:0" />
							</radialGradient>
							<filter id="hologramGlow">
								<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
								<feMerge>
									<feMergeNode in="coloredBlur"/>
									<feMergeNode in="SourceGraphic"/>
								</feMerge>
							</filter>
						</defs>
						
						<circle cx="110" cy="110" r="90" fill="url(#centerGradient)" opacity="0.3"/>
						
						{#if data.domain_analysis && totalDomains > 0}
							{@const oneDcProgress = getCircularProgress(oneDcPercentage)}
							{@const feadProgress = getCircularProgress(feadPercentage)}
							{@const otherProgress = getCircularProgress(otherPercentage)}
							
							<g filter="url(#hologramGlow)">
								<circle 
									cx="110" cy="110" r="80" 
									fill="none" 
									stroke="rgba(0, 255, 255, 0.2)" 
									stroke-width="2"
									stroke-dasharray="5,5"
									class="guide-ring"
								/>
								
								<circle 
									cx="110" cy="110" r="80" 
									fill="none" 
									stroke="#00ffff" 
									stroke-width="4"
									stroke-dasharray="{oneDcProgress.strokeDasharray}"
									stroke-dashoffset="{oneDcProgress.strokeDashoffset}"
									transform="rotate(-90 110 110)"
									class="domain-arc onedc-arc"
								/>
								
								<circle 
									cx="110" cy="110" r="65" 
									fill="none" 
									stroke="#ff00ff" 
									stroke-width="4"
									stroke-dasharray="{feadProgress.strokeDasharray}"
									stroke-dashoffset="{feadProgress.strokeDashoffset}"
									transform="rotate(-90 110 110)"
									class="domain-arc fead-arc"
								/>
								
								<circle 
									cx="110" cy="110" r="50" 
									fill="none" 
									stroke="#0096ff" 
									stroke-width="4"
									stroke-dasharray="{otherProgress.strokeDasharray}"
									stroke-dashoffset="{otherProgress.strokeDashoffset}"
									transform="rotate(-90 110 110)"
									class="domain-arc other-arc"
								/>
							</g>
						{/if}
						
						<circle cx="110" cy="110" r="25" fill="rgba(0, 0, 0, 0.8)" stroke="rgba(0, 255, 255, 0.4)" stroke-width="2"/>
						<text x="110" y="115" text-anchor="middle" fill="rgba(0, 255, 255, 0.9)" font-size="12" font-family="JetBrains Mono" font-weight="700">
							DOMAINS
						</text>
					</svg>
					
					<div class="domain-labels">
						<div class="label-node onedc-label" style="--label-color: #00ffff">
							<div class="label-ring"></div>
							<div class="label-info">
								<span class="label-name">1DC</span>
								<span class="label-value">{oneDcPercentage}%</span>
							</div>
						</div>
						
						<div class="label-node fead-label" style="--label-color: #ff00ff">
							<div class="label-ring"></div>
							<div class="label-info">
								<span class="label-name">FEAD</span>
								<span class="label-value">{feadPercentage}%</span>
							</div>
						</div>
						
						<div class="label-node other-label" style="--label-color: #0096ff">
							<div class="label-ring"></div>
							<div class="label-info">
								<span class="label-name">OTHER</span>
								<span class="label-value">{otherPercentage}%</span>
							</div>
						</div>
					</div>
				</div>

				<div class="metrics-cluster">
					<div class="metric-hologram">
						<div class="metric-frame">
							<div class="frame-glow"></div>
							<div class="metric-content">
								<span class="metric-value">{totalDomains.toLocaleString()}</span>
								<span class="metric-label">TOTAL ANALYZED</span>
							</div>
						</div>
					</div>
					
					<div class="metric-hologram">
						<div class="metric-frame">
							<div class="frame-glow"></div>
							<div class="metric-content">
								<span class="metric-value">{dominantDomain ? dominantDomain[0].toUpperCase() : 'N/A'}</span>
								<span class="metric-label">DOMINANT TYPE</span>
							</div>
						</div>
					</div>
				</div>
			</div>

			<div class="classification-breakdown">
				<div class="breakdown-header">
					<div class="header-symbol">◈</div>
					<h3>CLASSIFICATION BREAKDOWN</h3>
				</div>
				
				<div class="classification-grid">
					<div class="class-node" style="--node-color: #00ffff">
						<div class="node-hologram">
							<div class="node-ring"></div>
							<div class="node-core">
								<div class="core-indicator"></div>
							</div>
						</div>
						<div class="node-data">
							<div class="node-header">
								<span class="node-name">1DC DOMAINS</span>
								<span class="node-percentage">{oneDcPercentage}%</span>
							</div>
							<div class="node-count">{data.domain_analysis ? data.domain_analysis['1dc'] || 0 : 0}</div>
							<div class="node-bar">
								<div class="bar-fill" style="width: {oneDcPercentage}%; background: linear-gradient(90deg, #00ffff, #0088cc);"></div>
							</div>
						</div>
					</div>

					<div class="class-node" style="--node-color: #ff00ff">
						<div class="node-hologram">
							<div class="node-ring"></div>
							<div class="node-core">
								<div class="core-indicator"></div>
							</div>
						</div>
						<div class="node-data">
							<div class="node-header">
								<span class="node-name">FEAD DOMAINS</span>
								<span class="node-percentage">{feadPercentage}%</span>
							</div>
							<div class="node-count">{data.domain_analysis ? data.domain_analysis['fead'] || 0 : 0}</div>
							<div class="node-bar">
								<div class="bar-fill" style="width: {feadPercentage}%; background: linear-gradient(90deg, #ff00ff, #cc0088);"></div>
							</div>
						</div>
					</div>

					<div class="class-node" style="--node-color: #0096ff">
						<div class="node-hologram">
							<div class="node-ring"></div>
							<div class="node-core">
								<div class="core-indicator"></div>
							</div>
						</div>
						<div class="node-data">
							<div class="node-header">
								<span class="node-name">OTHER DOMAINS</span>
								<span class="node-percentage">{otherPercentage}%</span>
							</div>
							<div class="node-count">{data.domain_analysis ? data.domain_analysis['other'] || 0 : 0}</div>
							<div class="node-bar">
								<div class="bar-fill" style="width: {otherPercentage}%; background: linear-gradient(90deg, #0096ff, #0066cc);"></div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<div class="intelligence-summary">
				<div class="summary-header">
					<div class="header-symbol">◉</div>
					<h3>NEURAL INTELLIGENCE SUMMARY</h3>
				</div>
				
				<div class="summary-content">
					<div class="summary-grid">
						{#if dominantDomain}
							<div class="summary-item">
								<div class="item-icon">◯</div>
								<div class="item-text">
									Primary classification: <strong style="color: #00ffff">{dominantDomain[0].toUpperCase()}</strong> domains 
									({dominantDomain[1].toLocaleString()} instances)
								</div>
							</div>
							
							<div class="summary-item">
								<div class="item-icon">◯</div>
								<div class="item-text">
									Domain distribution shows <strong style="color: #ff00ff">
									{oneDcPercentage > feadPercentage ? '1DC dominance' : feadPercentage > oneDcPercentage ? 'FEAD prevalence' : 'balanced split'}</strong>
								</div>
							</div>
							
							<div class="summary-item">
								<div class="item-icon">◯</div>
								<div class="item-text">
									Total domain entities processed: <strong style="color: #0096ff">{totalDomains.toLocaleString()}</strong>
								</div>
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	{/if}

	<div class="neural-footer">
		<div class="footer-line"></div>
		<div class="classification-notice">
			◆ DOMAIN INTELLIGENCE // NEURAL CLASSIFICATION PROTOCOL ACTIVE
		</div>
	</div>
</div>

<style>
	.domain-matrix-core {
		width: 100%;
		height: 100%;
		font-family: 'JetBrains Mono', monospace;
		color: #ffffff;
		display: flex;
		flex-direction: column;
	}

	.matrix-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1.5rem;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(255, 0, 255, 0.05) 50%,
			rgba(0, 255, 255, 0.05) 100%);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 12px;
		margin-bottom: 1.5rem;
		backdrop-filter: blur(20px);
	}

	.header-hologram {
		position: relative;
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.holo-rings {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
	}

	.holo-ring {
		position: absolute;
		border-radius: 50%;
		border: 2px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: holoRotate 6s linear infinite;
	}

	.ring-1 {
		width: 60px;
		height: 60px;
		border-color: rgba(255, 0, 255, 0.6);
	}

	.ring-2 {
		width: 45px;
		height: 45px;
		border-color: rgba(0, 255, 255, 0.4);
		animation-direction: reverse;
		animation-duration: 4s;
	}

	.header-center {
		position: relative;
		z-index: 3;
		font-size: 1.5rem;
		color: rgba(255, 0, 255, 0.9);
		text-shadow: 0 0 20px rgba(255, 0, 255, 0.8);
		animation: centerGlow 3s ease-in-out infinite;
	}

	.header-info {
		flex: 1;
		margin-left: 1.5rem;
	}

	.matrix-title {
		font-size: 1.2rem;
		font-weight: 700;
		color: #ffffff;
		margin: 0;
		text-shadow: 0 0 15px rgba(255, 0, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.matrix-subtitle {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		margin: 0.25rem 0 0 0;
		font-weight: 300;
	}

	.classification-badge {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: linear-gradient(135deg, 
			rgba(255, 0, 0, 0.1), 
			rgba(255, 100, 100, 0.05));
		border: 1px solid rgba(255, 0, 0, 0.3);
		border-radius: 6px;
		backdrop-filter: blur(10px);
	}

	.badge-ring {
		width: 8px;
		height: 8px;
		background: #ff0000;
		border-radius: 50%;
		animation: badgePulse 2s ease-in-out infinite;
		box-shadow: 0 0 10px #ff0000;
	}

	.badge-text {
		font-size: 0.7rem;
		color: #ff0000;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.neural-loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		flex: 1;
		gap: 2rem;
	}

	.loading-hologram {
		position: relative;
		width: 120px;
		height: 120px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.loading-rings {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
	}

	.loading-ring {
		position: absolute;
		border-radius: 50%;
		border: 2px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: loadingRotate 3s linear infinite;
	}

	.ring-outer {
		width: 120px;
		height: 120px;
		border-color: rgba(255, 0, 255, 0.6);
	}

	.ring-middle {
		width: 90px;
		height: 90px;
		border-color: rgba(0, 255, 255, 0.4);
		animation-direction: reverse;
		animation-duration: 2s;
	}

	.ring-inner {
		width: 60px;
		height: 60px;
		border-color: rgba(0, 150, 255, 0.8);
		animation-duration: 1s;
	}

	.loading-core {
		position: relative;
		z-index: 3;
		font-size: 2rem;
		color: rgba(255, 0, 255, 0.9);
		text-shadow: 0 0 20px rgba(255, 0, 255, 0.8);
		animation: loadingPulse 2s ease-in-out infinite;
	}

	.loading-text {
		color: rgba(255, 0, 255, 0.8);
		font-size: 1rem;
		font-weight: 500;
		letter-spacing: 0.1em;
	}

	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		flex: 1;
		gap: 1.5rem;
	}

	.error-hologram {
		position: relative;
		width: 80px;
		height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.error-ring {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		border: 3px solid rgba(255, 0, 0, 0.6);
		border-radius: 50%;
		animation: errorPulse 1.5s ease-in-out infinite;
	}

	.error-center {
		font-size: 2rem;
		color: rgba(255, 0, 0, 0.9);
		text-shadow: 0 0 20px rgba(255, 0, 0, 0.8);
	}

	.error-text {
		color: rgba(255, 0, 0, 0.8);
		font-size: 1rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.matrix-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.domain-overview {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 3rem;
		align-items: center;
	}

	.central-hologram {
		position: relative;
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.domain-visualization {
		filter: drop-shadow(0 0 15px rgba(255, 0, 255, 0.3));
	}

	.guide-ring {
		animation: guideRotate 20s linear infinite;
	}

	.domain-arc {
		transition: stroke-dashoffset 2s cubic-bezier(0.4, 0, 0.2, 1);
		filter: drop-shadow(0 0 8px currentColor);
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

	.domain-labels {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	.label-node {
		position: absolute;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.75rem;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid var(--label-color);
		border-radius: 6px;
		backdrop-filter: blur(10px);
	}

	.onedc-label {
		top: 10%;
		right: -20%;
	}

	.fead-label {
		bottom: 10%;
		right: -20%;
	}

	.other-label {
		bottom: 10%;
		left: -20%;
	}

	.label-ring {
		width: 8px;
		height: 8px;
		border: 2px solid var(--label-color);
		border-radius: 50%;
		animation: labelRingPulse 2s ease-in-out infinite;
	}

	.label-info {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
	}

	.label-name {
		font-size: 0.7rem;
		font-weight: 600;
		color: var(--label-color);
		letter-spacing: 0.05em;
	}

	.label-value {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 400;
	}

	.metrics-cluster {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.metric-hologram {
		position: relative;
	}

	.metric-frame {
		position: relative;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(0, 255, 255, 0.03) 100%);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 8px;
		padding: 1.5rem;
		text-align: center;
		backdrop-filter: blur(10px);
	}

	.frame-glow {
		position: absolute;
		top: -1px;
		left: -1px;
		right: -1px;
		bottom: -1px;
		background: linear-gradient(45deg, 
			rgba(0, 255, 255, 0.2), 
			rgba(255, 0, 255, 0.1));
		border-radius: 8px;
		z-index: -1;
		animation: frameGlow 3s ease-in-out infinite;
	}

	.metric-content {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.metric-value {
		font-size: 1.8rem;
		font-weight: 700;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
	}

	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 400;
		letter-spacing: 0.05em;
	}

	.classification-breakdown {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.4) 0%, 
			rgba(0, 255, 255, 0.02) 50%,
			rgba(255, 0, 255, 0.02) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
	}

	.breakdown-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1.5rem;
	}

	.header-symbol {
		font-size: 1.2rem;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
		animation: symbolFloat 3s ease-in-out infinite;
	}

	.breakdown-header h3 {
		font-size: 1rem;
		font-weight: 700;
		color: rgba(0, 255, 255, 0.9);
		margin: 0;
		letter-spacing: 0.05em;
	}

	.classification-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1rem;
	}

	.class-node {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		padding: 1rem;
		display: flex;
		align-items: center;
		gap: 1rem;
		transition: all 0.3s ease;
	}

	.class-node:hover {
		border-color: var(--node-color);
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
		transform: translateY(-2px);
	}

	.node-hologram {
		position: relative;
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.node-ring {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		border: 2px solid var(--node-color);
		border-radius: 50%;
		opacity: 0.4;
		animation: nodeRingRotate 4s linear infinite;
	}

	.node-core {
		position: relative;
		z-index: 2;
		width: 20px;
		height: 20px;
		background: radial-gradient(circle, var(--node-color), transparent);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.core-indicator {
		width: 6px;
		height: 6px;
		background: var(--node-color);
		border-radius: 50%;
		animation: coreIndicatorPulse 2s ease-in-out infinite;
		box-shadow: 0 0 8px var(--node-color);
	}

	.node-data {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.node-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.node-name {
		font-size: 0.8rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.9);
		letter-spacing: 0.02em;
	}

	.node-percentage {
		font-size: 0.8rem;
		font-weight: 700;
		color: var(--node-color);
		text-shadow: 0 0 8px var(--node-color);
	}

	.node-count {
		font-size: 1.2rem;
		font-weight: 700;
		color: #ffffff;
		text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
	}

	.node-bar {
		height: 6px;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 3px;
		overflow: hidden;
		position: relative;
	}

	.bar-fill {
		height: 100%;
		border-radius: 3px;
		transition: width 2s cubic-bezier(0.4, 0, 0.2, 1);
		position: relative;
		box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
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

	.intelligence-summary {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(255, 0, 255, 0.02) 50%,
			rgba(0, 150, 255, 0.02) 100%);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
	}

	.summary-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1.5rem;
	}

	.summary-header .header-symbol {
		color: rgba(255, 0, 255, 0.9);
		text-shadow: 0 0 15px rgba(255, 0, 255, 0.6);
	}

	.summary-header h3 {
		font-size: 1rem;
		font-weight: 700;
		color: rgba(255, 0, 255, 0.9);
		margin: 0;
		letter-spacing: 0.05em;
	}

	.summary-grid {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.summary-item {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		padding: 1rem;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.4) 0%, 
			rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		backdrop-filter: blur(10px);
	}

	.item-icon {
		font-size: 1rem;
		color: rgba(255, 0, 255, 0.8);
		text-shadow: 0 0 10px rgba(255, 0, 255, 0.5);
		margin-top: 0.1rem;
		flex-shrink: 0;
	}

	.item-text {
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.8);
		line-height: 1.4;
		font-weight: 400;
	}

	.item-text strong {
		color: #ffffff;
		font-weight: 600;
		text-shadow: 0 0 8px currentColor;
	}

	.neural-footer {
		margin-top: 2rem;
		padding-top: 1rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		text-align: center;
	}

	.footer-line {
		width: 100%;
		height: 1px;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(255, 0, 255, 0.4), 
			transparent);
		margin-bottom: 1rem;
	}

	.classification-notice {
		font-size: 0.7rem;
		color: rgba(255, 0, 255, 0.7);
		font-weight: 500;
		letter-spacing: 0.05em;
	}

	@keyframes holoRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes centerGlow {
		0%, 100% { 
			text-shadow: 0 0 20px rgba(255, 0, 255, 0.8); 
			transform: scale(1);
		}
		50% { 
			text-shadow: 0 0 30px rgba(255, 0, 255, 1); 
			transform: scale(1.05);
		}
	}

	@keyframes badgePulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.1); }
	}

	@keyframes loadingRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes loadingPulse {
		0%, 100% { opacity: 0.9; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.1); }
	}

	@keyframes errorPulse {
		0%, 100% { 
			border-color: rgba(255, 0, 0, 0.6); 
			box-shadow: 0 0 20px rgba(255, 0, 0, 0.3);
		}
		50% { 
			border-color: rgba(255, 0, 0, 1); 
			box-shadow: 0 0 40px rgba(255, 0, 0, 0.6);
		}
	}

	@keyframes guideRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes arcGlow {
		0%, 100% { filter: drop-shadow(0 0 8px currentColor); }
		50% { filter: drop-shadow(0 0 15px currentColor); }
	}

	@keyframes labelRingPulse {
		0%, 100% { 
			border-color: var(--label-color); 
			box-shadow: 0 0 5px var(--label-color);
		}
		50% { 
			border-color: rgba(255, 255, 255, 0.8); 
			box-shadow: 0 0 15px var(--label-color);
		}
	}

	@keyframes frameGlow {
		0%, 100% { opacity: 0.2; }
		50% { opacity: 0.4; }
	}

	@keyframes symbolFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-3px); }
	}

	@keyframes nodeRingRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes coreIndicatorPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.2); }
	}

	@keyframes barSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@media (max-width: 1200px) {
		.domain-overview {
			grid-template-columns: 1fr;
			gap: 2rem;
			text-align: center;
		}

		.classification-grid {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 768px) {
		.matrix-header {
			flex-direction: column;
			gap: 1rem;
			text-align: center;
		}

		.header-info {
			margin-left: 0;
		}

		.summary-item {
			flex-direction: column;
			gap: 0.5rem;
		}
	}
</style>