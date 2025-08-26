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
			error = 'DOMAIN INTELLIGENCE COMPROMISED';
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
</script>

<div class="domain-panel">
	<header class="panel-header">
		<div class="header-content">
			<span class="header-icon">◆</span>
			<div class="header-text">
				<h2>DOMAIN INTELLIGENCE MATRIX</h2>
				<p>1DC vs FEAD domain classification (one per row logic)</p>
			</div>
		</div>
		<div class="clearance-badge">
			CLASSIFIED
		</div>
	</header>

	{#if loading}
		<div class="loading-state">
			<div class="domain-scanner">
				<div class="scanner-line"></div>
				<div class="scanner-grid">
					{#each Array(16) as _, i}
						<div class="grid-cell" style="animation-delay: {i * 0.1}s"></div>
					{/each}
				</div>
			</div>
			<p>Analyzing domain structures...</p>
		</div>
	{:else if error}
		<div class="error-state">
			<span class="error-icon">⚠</span>
			<p>CRITICAL ERROR: {error}</p>
		</div>
	{:else}
		<div class="panel-content">
			<div class="domain-overview">
				<div class="domain-split-chart">
					<svg width="200" height="200" viewBox="0 0 200 200">
						<defs>
							<filter id="glow">
								<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
								<feMerge>
									<feMergeNode in="coloredBlur"/>
									<feMergeNode in="SourceGraphic"/>
								</feMerge>
							</filter>
						</defs>
						{#if data.domain_analysis && totalDomains > 0}
							{@const oneDcAngle = (data.domain_analysis['1dc'] || 0) / totalDomains * 360}
							{@const feadAngle = (data.domain_analysis['fead'] || 0) / totalDomains * 360}
							{@const otherAngle = (data.domain_analysis['other'] || 0) / totalDomains * 360}
							
							<!-- 1DC Segment -->
							<path
								d="M 100 100 L 100 50 A 50 50 0 {oneDcAngle > 180 ? 1 : 0} 1 {100 + 50 * Math.sin(oneDcAngle * Math.PI / 180)} {100 - 50 * Math.cos(oneDcAngle * Math.PI / 180)} Z"
								fill="#00ff41"
								filter="url(#glow)"
								class="domain-segment"
							/>
							
							<!-- FEAD Segment -->
							<path
								d="M 100 100 L {100 + 50 * Math.sin(oneDcAngle * Math.PI / 180)} {100 - 50 * Math.cos(oneDcAngle * Math.PI / 180)} A 50 50 0 {feadAngle > 180 ? 1 : 0} 1 {100 + 50 * Math.sin((oneDcAngle + feadAngle) * Math.PI / 180)} {100 - 50 * Math.cos((oneDcAngle + feadAngle) * Math.PI / 180)} Z"
								fill="#0099ff"
								filter="url(#glow)"
								class="domain-segment"
							/>
							
							<!-- Other Segment -->
							<path
								d="M 100 100 L {100 + 50 * Math.sin((oneDcAngle + feadAngle) * Math.PI / 180)} {100 - 50 * Math.cos((oneDcAngle + feadAngle) * Math.PI / 180)} A 50 50 0 {otherAngle > 180 ? 1 : 0} 1 100 50 Z"
								fill="#ff6600"
								filter="url(#glow)"
								class="domain-segment"
							/>
						{/if}
						
						<circle
							cx="100"
							cy="100"
							r="25"
							fill="rgba(0, 0, 0, 0.8)"
							stroke="#333"
							stroke-width="2"
						/>
						<text x="100" y="105" text-anchor="middle" fill="#fff" font-size="12" font-family="monospace">
							DOMAINS
						</text>
					</svg>
				</div>

				<div class="domain-metrics">
					<div class="total-domains">
						<span class="metric-value">{totalDomains}</span>
						<span class="metric-label">TOTAL ANALYZED</span>
					</div>
					<div class="dominant-domain">
						<span class="metric-value">{dominantDomain ? dominantDomain[0].toUpperCase() : 'N/A'}</span>
						<span class="metric-label">DOMINANT TYPE</span>
					</div>
				</div>
			</div>

			<div class="domain-breakdown">
				<h3>CLASSIFICATION BREAKDOWN</h3>
				<div class="classification-grid">
					<div class="class-item">
						<div class="class-indicator" style="background: #00ff41"></div>
						<div class="class-content">
							<div class="class-name">1DC DOMAINS</div>
							<div class="class-count">{data.domain_analysis ? data.domain_analysis['1dc'] || 0 : 0}</div>
							<div class="class-percent">{oneDcPercentage}%</div>
						</div>
						<div class="class-bar">
							<div class="bar-fill" style="width: {oneDcPercentage}%; background: #00ff41;"></div>
						</div>
					</div>

					<div class="class-item">
						<div class="class-indicator" style="background: #0099ff"></div>
						<div class="class-content">
							<div class="class-name">FEAD DOMAINS</div>
							<div class="class-count">{data.domain_analysis ? data.domain_analysis['fead'] || 0 : 0}</div>
							<div class="class-percent">{feadPercentage}%</div>
						</div>
						<div class="class-bar">
							<div class="bar-fill" style="width: {feadPercentage}%; background: #0099ff;"></div>
						</div>
					</div>

					<div class="class-item">
						<div class="class-indicator" style="background: #ff6600"></div>
						<div class="class-content">
							<div class="class-name">OTHER DOMAINS</div>
							<div class="class-count">{data.domain_analysis ? data.domain_analysis['other'] || 0 : 0}</div>
							<div class="class-percent">{otherPercentage}%</div>
						</div>
						<div class="class-bar">
							<div class="bar-fill" style="width: {otherPercentage}%; background: #ff6600;"></div>
						</div>
					</div>
				</div>
			</div>

			<div class="intelligence-summary">
				<div class="summary-header">
					<h3>NEURAL ANALYSIS SUMMARY</h3>
				</div>
				<div class="summary-content">
					{#if dominantDomain}
						<p class="analysis-text">
							◯ Primary classification: <strong>{dominantDomain[0].toUpperCase()}</strong> domains ({dominantDomain[1]} instances)
						</p>
						<p class="analysis-text">
							◯ Domain distribution shows {oneDcPercentage > feadPercentage ? '1DC dominance' : feadPercentage > oneDcPercentage ? 'FEAD prevalence' : 'balanced split'}
						</p>
						<p class="analysis-text">
							◯ Total domain entities processed: <strong>{totalDomains.toLocaleString()}</strong>
						</p>
					{/if}
				</div>
			</div>

			<div class="neural-footer">
				<div class="classification-notice">
					◆ DOMAIN INTELLIGENCE // NEURAL CLASSIFICATION PROTOCOL
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.domain-panel {
		background: linear-gradient(135deg, rgba(13, 0, 26, 0.95) 0%, rgba(6, 0, 13, 0.95) 100%);
		border: 1px solid #6600cc;
		border-radius: 8px;
		overflow: hidden;
		box-shadow: 
			0 0 20px rgba(102, 0, 204, 0.3),
			inset 0 0 20px rgba(102, 0, 204, 0.05);
		animation: domain-pulse 3.5s ease-in-out infinite alternate;
	}

	@keyframes domain-pulse {
		from { box-shadow: 0 0 20px rgba(102, 0, 204, 0.2), inset 0 0 20px rgba(102, 0, 204, 0.05); }
		to { box-shadow: 0 0 30px rgba(102, 0, 204, 0.4), inset 0 0 30px rgba(102, 0, 204, 0.1); }
	}

	.panel-header {
		background: rgba(0, 0, 0, 0.9);
		border-bottom: 1px solid #440066;
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
		color: #6600cc;
		animation: diamond-spin 8s linear infinite;
	}

	@keyframes diamond-spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.header-text h2 {
		margin: 0;
		font-size: 16px;
		color: #6600cc;
		letter-spacing: 1px;
	}

	.header-text p {
		margin: 2px 0 0 0;
		font-size: 11px;
		color: #9966ff;
		opacity: 0.8;
	}

	.clearance-badge {
		background: rgba(255, 0, 0, 0.2);
		color: #ff0000;
		padding: 5px 12px;
		border: 1px solid #ff0000;
		border-radius: 4px;
		font-size: 11px;
		font-weight: bold;
		letter-spacing: 1px;
	}

	.loading-state {
		padding: 40px;
		text-align: center;
	}

	.domain-scanner {
		position: relative;
		width: 80px;
		height: 80px;
		margin: 0 auto 20px;
	}

	.scanner-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		grid-template-rows: repeat(4, 1fr);
		gap: 2px;
		width: 80px;
		height: 80px;
	}

	.grid-cell {
		background: #440066;
		animation: cell-scan 2s infinite ease-in-out;
	}

	@keyframes cell-scan {
		0%, 100% { opacity: 0.3; background: #440066; }
		50% { opacity: 1; background: #6600cc; }
	}

	.scanner-line {
		position: absolute;
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, #6600cc, transparent);
		animation: scan-sweep 2s linear infinite;
		z-index: 1;
	}

	@keyframes scan-sweep {
		0% { top: 0%; }
		100% { top: 100%; }
	}

	.panel-content {
		padding: 20px;
	}

	.domain-overview {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 30px;
		margin-bottom: 30px;
		align-items: center;
	}

	.domain-split-chart {
		display: flex;
		justify-content: center;
	}

	.domain-segment {
		transition: opacity 0.3s ease;
		cursor: pointer;
	}

	.domain-segment:hover {
		opacity: 0.8;
	}

	.domain-metrics {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}

	.total-domains,
	.dominant-domain {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #440066;
		border-radius: 6px;
		padding: 15px;
		text-align: center;
	}

	.metric-value {
		display: block;
		font-size: 24px;
		font-weight: bold;
		color: #6600cc;
		margin-bottom: 5px;
		animation: value-glow 2s ease-in-out infinite alternate;
	}

	@keyframes value-glow {
		from { text-shadow: 0 0 10px #6600cc; }
		to { text-shadow: 0 0 20px #6600cc, 0 0 30px #6600cc; }
	}

	.metric-label {
		font-size: 10px;
		color: #9966ff;
		letter-spacing: 1px;
	}

	.domain-breakdown h3 {
		color: #6600cc;
		margin: 0 0 20px 0;
		font-size: 14px;
		letter-spacing: 1px;
		border-bottom: 1px solid #440066;
		padding-bottom: 10px;
	}

	.classification-grid {
		display: flex;
		flex-direction: column;
		gap: 15px;
		margin-bottom: 25px;
	}

	.class-item {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #440066;
		border-radius: 6px;
		padding: 15px;
		display: grid;
		grid-template-columns: auto 1fr auto;
		gap: 15px;
		align-items: center;
		transition: all 0.3s ease;
	}

	.class-item:hover {
		border-color: #6600cc;
		box-shadow: 0 0 15px rgba(102, 0, 204, 0.3);
	}

	.class-indicator {
		width: 16px;
		height: 16px;
		border-radius: 3px;
		animation: indicator-pulse 2s infinite;
	}

	@keyframes indicator-pulse {
		0%, 50% { opacity: 1; }
		51%, 100% { opacity: 0.6; }
	}

	.class-content {
		display: flex;
		align-items: center;
		gap: 15px;
	}

	.class-name {
		font-size: 12px;
		color: #9966ff;
		min-width: 120px;
	}

	.class-count {
		font-size: 16px;
		font-weight: bold;
		color: #ffffff;
		min-width: 40px;
	}

	.class-percent {
		font-size: 12px;
		color: #6600cc;
		font-weight: bold;
		min-width: 40px;
		text-align: right;
	}

	.class-bar {
		width: 100px;
		height: 6px;
		background: #220011;
		border-radius: 3px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		border-radius: 3px;
		transition: width 1s ease-out;
		animation: bar-shimmer 2s infinite;
	}

	@keyframes bar-shimmer {
		0%, 100% { opacity: 0.8; }
		50% { opacity: 1; }
	}

	.intelligence-summary {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid #440066;
		border-radius: 6px;
		padding: 20px;
		margin-bottom: 20px;
	}

	.summary-header h3 {
		margin: 0 0 15px 0;
		color: #6600cc;
		font-size: 14px;
		letter-spacing: 1px;
	}

	.analysis-text {
		margin: 8px 0;
		font-size: 12px;
		color: #9966ff;
		line-height: 1.4;
	}

	.analysis-text strong {
		color: #ffffff;
	}

	.neural-footer {
		border-top: 1px solid #440066;
		padding-top: 15px;
		font-size: 10px;
		color: #6600cc;
		text-align: center;
	}
</style>