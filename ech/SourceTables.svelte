<!-- ech/SourceTables.svelte -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let searchTerm = '';
	let selectedSource = null;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/source_tables');
			const result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			console.error('Source tables error:', err);
			loading = false;
		}
	});

	$: filteredSources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];

	$: maxFrequency = filteredSources.length > 0 ? Math.max(...filteredSources.map(([, freq]) => freq)) : 1;

	function getThreatLevel(frequency) {
		if (!data.total_mentions) return { level: 'LOW', color: '#0096ff', intensity: 0.3 };
		const percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRITICAL', color: '#ff00ff', intensity: 1.0 };
		if (percentage >= 10) return { level: 'HIGH', color: '#ff0066', intensity: 0.8 };
		if (percentage >= 5) return { level: 'MEDIUM', color: '#ffaa00', intensity: 0.6 };
		return { level: 'LOW', color: '#00ffff', intensity: 0.4 };
	}

	function getPercentage(frequency) {
		if (!data.total_mentions) return '0.00';
		return ((frequency / data.total_mentions) * 100).toFixed(2);
	}

	function selectSource(source, frequency) {
		selectedSource = { source, frequency };
	}

	function getCircularProgress(frequency) {
		const percentage = (frequency / maxFrequency) * 100;
		const circumference = 2 * Math.PI * 45;
		const strokeDasharray = circumference;
		const strokeDashoffset = circumference - (percentage / 100) * circumference;
		return { strokeDasharray, strokeDashoffset };
	}
</script>

<div class="source-intelligence-matrix">
	{#if loading}
		<div class="neural-scanner">
			<div class="scanner-core">
				<div class="scan-rings">
					<div class="scan-ring ring-1"></div>
					<div class="scan-ring ring-2"></div>
					<div class="scan-ring ring-3"></div>
				</div>
				<div class="scan-center">◈</div>
			</div>
			<div class="scanner-text">ANALYZING SOURCE INTELLIGENCE MATRIX</div>
		</div>
	{:else}
		<div class="intelligence-header">
			<div class="metrics-cluster">
				<div class="holo-metric">
					<div class="metric-ring">
						<svg width="120" height="120" viewBox="0 0 120 120">
							<circle cx="60" cy="60" r="45" fill="none" stroke="rgba(0, 255, 255, 0.1)" stroke-width="3"/>
							<circle 
								cx="60" cy="60" r="45" 
								fill="none" 
								stroke="url(#uniqueGradient)" 
								stroke-width="3"
								stroke-dasharray="283"
								stroke-dashoffset="0"
								transform="rotate(-90 60 60)"
								class="progress-ring"
							/>
							<defs>
								<linearGradient id="uniqueGradient" x1="0%" y1="0%" x2="100%" y2="0%">
									<stop offset="0%" style="stop-color:#00ffff;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#ff00ff;stop-opacity:1" />
								</linearGradient>
							</defs>
						</svg>
						<div class="metric-center">
							<span class="metric-value">{(data.unique_sources || 0).toLocaleString()}</span>
							<span class="metric-label">SOURCES</span>
						</div>
					</div>
				</div>
				
				<div class="holo-metric">
					<div class="metric-ring">
						<svg width="120" height="120" viewBox="0 0 120 120">
							<circle cx="60" cy="60" r="45" fill="none" stroke="rgba(255, 0, 255, 0.1)" stroke-width="3"/>
							<circle 
								cx="60" cy="60" r="45" 
								fill="none" 
								stroke="url(#mentionsGradient)" 
								stroke-width="3"
								stroke-dasharray="283"
								stroke-dashoffset="70"
								transform="rotate(-90 60 60)"
								class="progress-ring"
							/>
							<defs>
								<linearGradient id="mentionsGradient" x1="0%" y1="0%" x2="100%" y2="0%">
									<stop offset="0%" style="stop-color:#ff00ff;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#0096ff;stop-opacity:1" />
								</linearGradient>
							</defs>
						</svg>
						<div class="metric-center">
							<span class="metric-value">{(data.total_mentions || 0).toLocaleString()}</span>
							<span class="metric-label">MENTIONS</span>
						</div>
					</div>
				</div>
			</div>

			<div class="neural-search">
				<div class="search-frame">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="NEURAL SEARCH PROTOCOL..."
						class="search-input"
					/>
					<div class="search-beam"></div>
					<div class="search-particles">
						<div class="particle"></div>
						<div class="particle"></div>
						<div class="particle"></div>
					</div>
				</div>
			</div>
		</div>

		<div class="data-matrix">
			<div class="source-hologram">
				<div class="matrix-title">
					<span class="title-symbol">◈</span>
					SOURCE THREAT HOLOGRAM
				</div>
				
				<div class="holographic-grid">
					{#each filteredSources.slice(0, 20) as [source, frequency]}
						{@const threat = getThreatLevel(frequency)}
						{@const progress = getCircularProgress(frequency)}
						<div 
							class="source-node"
							style="--threat-color: {threat.color}; --threat-intensity: {threat.intensity}"
							on:click={() => selectSource(source, frequency)}
						>
							<div class="node-hologram">
								<svg width="80" height="80" viewBox="0 0 80 80" class="holo-ring">
									<circle cx="40" cy="40" r="30" fill="none" stroke="rgba(255, 255, 255, 0.1)" stroke-width="2"/>
									<circle 
										cx="40" cy="40" r="30" 
										fill="none" 
										stroke="{threat.color}" 
										stroke-width="2"
										stroke-dasharray="{progress.strokeDasharray}"
										stroke-dashoffset="{progress.strokeDashoffset}"
										transform="rotate(-90 40 40)"
										class="node-progress"
									/>
								</svg>
								<div class="node-core">
									<div class="threat-indicator" style="background: {threat.color}"></div>
								</div>
							</div>
							
							<div class="node-data">
								<div class="node-header">
									<span class="threat-level">{threat.level}</span>
									<span class="frequency-percent">{getPercentage(frequency)}%</span>
								</div>
								<div class="source-name">{source}</div>
								<div class="frequency-display">
									<span class="frequency-count">{frequency.toLocaleString()}</span>
									<span class="frequency-label">INSTANCES</span>
								</div>
							</div>
							
							<div class="node-connections">
								<div class="connection-line line-1"></div>
								<div class="connection-line line-2"></div>
								<div class="connection-line line-3"></div>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<div class="analysis-hologram">
				<div class="matrix-title">
					<span class="title-symbol">◆</span>
					NEURAL ANALYSIS CORE
				</div>
				
				{#if selectedSource}
					<div class="selected-analysis">
						<div class="analysis-frame">
							<div class="frame-glow"></div>
							<div class="analysis-header">
								<div class="selected-name">{selectedSource.source}</div>
								<div class="threat-assessment">
									{@const threat = getThreatLevel(selectedSource.frequency)}
									<div class="threat-badge" style="--threat-color: {threat.color}">
										<div class="badge-ring"></div>
										<span class="threat-text">THREAT: {threat.level}</span>
									</div>
								</div>
							</div>
							
							<div class="analysis-metrics">
								<div class="analysis-metric">
									<span class="metric-label">FREQUENCY</span>
									<span class="metric-value">{selectedSource.frequency.toLocaleString()}</span>
								</div>
								<div class="analysis-metric">
									<span class="metric-label">PERCENTAGE</span>
									<span class="metric-value">{getPercentage(selectedSource.frequency)}%</span>
								</div>
								<div class="analysis-metric">
									<span class="metric-label">THREAT LEVEL</span>
									<span class="metric-value" style="color: {getThreatLevel(selectedSource.frequency).color}">
										{getThreatLevel(selectedSource.frequency).level}
									</span>
								</div>
							</div>

							<div class="neural-visualization">
								<div class="viz-title">NEURAL PATTERN ANALYSIS</div>
								<div class="pattern-grid">
									{#each Array(12) as _, i}
										<div 
											class="pattern-node" 
											style="animation-delay: {i * 0.1}s; opacity: {Math.random() * 0.6 + 0.3}"
										></div>
									{/each}
								</div>
							</div>
						</div>
					</div>
				{:else}
					<div class="analysis-prompt">
						<div class="prompt-hologram">
							<div class="prompt-rings">
								<div class="prompt-ring ring-1"></div>
								<div class="prompt-ring ring-2"></div>
							</div>
							<div class="prompt-center">◯</div>
						</div>
						<div class="prompt-text">SELECT SOURCE NODE FOR DEEP ANALYSIS</div>
						<div class="prompt-subtext">NEURAL INTERFACE READY</div>
					</div>
				{/if}

				<div class="threat-distribution">
					<div class="distribution-title">THREAT SPECTRUM ANALYSIS</div>
					<div class="spectrum-bars">
						{#each [['CRITICAL', '#ff00ff'], ['HIGH', '#ff0066'], ['MEDIUM', '#ffaa00'], ['LOW', '#00ffff']] as [level, color]}
							{@const count = filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === level).length}
							{@const maxCount = Math.max(
								filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'CRITICAL').length,
								filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'HIGH').length,
								filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'MEDIUM').length,
								filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'LOW').length
							)}
							<div class="spectrum-bar">
								<div class="bar-header">
									<span class="bar-label">{level}</span>
									<span class="bar-count">{count}</span>
								</div>
								<div class="bar-container">
									<div class="bar-track"></div>
									<div 
										class="bar-fill" 
										style="width: {maxCount > 0 ? (count / maxCount) * 100 : 0}%; background: {color}; box-shadow: 0 0 15px {color};"
									></div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.source-intelligence-matrix {
		width: 100%;
		height: 100%;
		font-family: 'JetBrains Mono', monospace;
		color: #ffffff;
		position: relative;
	}

	.neural-scanner {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 400px;
		gap: 2rem;
	}

	.scanner-core {
		position: relative;
		width: 120px;
		height: 120px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.scan-rings {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
	}

	.scan-ring {
		position: absolute;
		border-radius: 50%;
		border: 2px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: scanRotate 3s linear infinite;
	}

	.ring-1 {
		width: 120px;
		height: 120px;
		border-color: rgba(0, 255, 255, 0.6);
		animation-duration: 4s;
	}

	.ring-2 {
		width: 90px;
		height: 90px;
		border-color: rgba(255, 0, 255, 0.4);
		animation-duration: 3s;
		animation-direction: reverse;
	}

	.ring-3 {
		width: 60px;
		height: 60px;
		border-color: rgba(0, 150, 255, 0.8);
		animation-duration: 2s;
	}

	.scan-center {
		position: relative;
		z-index: 3;
		font-size: 2rem;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
		animation: centerPulse 2s ease-in-out infinite;
	}

	.scanner-text {
		color: rgba(0, 255, 255, 0.8);
		font-size: 1rem;
		font-weight: 500;
		letter-spacing: 0.1em;
		animation: textGlow 2s ease-in-out infinite;
	}

	.intelligence-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		gap: 2rem;
	}

	.metrics-cluster {
		display: flex;
		gap: 2rem;
	}

	.holo-metric {
		position: relative;
	}

	.metric-ring {
		position: relative;
		width: 120px;
		height: 120px;
	}

	.progress-ring {
		filter: drop-shadow(0 0 5px currentColor);
		animation: ringGlow 3s ease-in-out infinite;
	}

	.metric-center {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
	}

	.metric-value {
		display: block;
		font-size: 1.5rem;
		font-weight: 700;
		color: #ffffff;
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
	}

	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 400;
		letter-spacing: 0.05em;
		margin-top: 0.25rem;
	}

	.neural-search {
		flex: 1;
		max-width: 400px;
	}

	.search-frame {
		position: relative;
		width: 100%;
	}

	.search-input {
		width: 100%;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(0, 255, 255, 0.05) 100%);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 8px;
		padding: 0.75rem 1rem;
		color: #ffffff;
		font-family: inherit;
		font-size: 0.9rem;
		backdrop-filter: blur(20px);
		transition: all 0.3s ease;
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.1);
	}

	.search-input::placeholder {
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.05em;
	}

	.search-input:focus {
		outline: none;
		border-color: rgba(0, 255, 255, 0.8);
		box-shadow: 0 0 25px rgba(0, 255, 255, 0.3);
	}

	.search-beam {
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(0, 255, 255, 0.2), 
			transparent);
		animation: searchScan 3s linear infinite;
		border-radius: 8px;
		pointer-events: none;
	}

	.search-particles {
		position: absolute;
		top: 50%;
		right: 15px;
		transform: translateY(-50%);
		display: flex;
		gap: 3px;
	}

	.particle {
		width: 3px;
		height: 3px;
		background: rgba(0, 255, 255, 0.6);
		border-radius: 50%;
		animation: particlePulse 1.5s ease-in-out infinite;
	}

	.particle:nth-child(2) { animation-delay: 0.5s; }
	.particle:nth-child(3) { animation-delay: 1s; }

	.data-matrix {
		display: grid;
		grid-template-columns: 1fr 400px;
		gap: 2rem;
		height: calc(100vh - 350px);
	}

	.source-hologram {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.4) 0%, 
			rgba(0, 255, 255, 0.02) 50%,
			rgba(255, 0, 255, 0.02) 100%);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 16px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
		overflow: hidden;
		position: relative;
	}

	.analysis-hologram {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.4) 0%, 
			rgba(255, 0, 255, 0.02) 50%,
			rgba(0, 150, 255, 0.02) 100%);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 16px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
		display: flex;
		flex-direction: column;
		overflow-y: auto;
	}

	.matrix-title {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1.5rem;
		font-size: 1rem;
		font-weight: 700;
		color: rgba(0, 255, 255, 0.9);
		letter-spacing: 0.05em;
	}

	.title-symbol {
		font-size: 1.2rem;
		animation: symbolFloat 3s ease-in-out infinite;
		text-shadow: 0 0 15px currentColor;
	}

	.holographic-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 1rem;
		height: calc(100% - 60px);
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.source-node {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1rem;
		cursor: pointer;
		position: relative;
		transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
		overflow: hidden;
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.source-node::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(255, 255, 255, 0.05), 
			transparent);
		transition: left 0.6s ease;
	}

	.source-node:hover::before {
		left: 100%;
	}

	.source-node:hover {
		border-color: var(--threat-color);
		box-shadow: 
			0 8px 32px rgba(0, 0, 0, 0.4),
			0 0 20px var(--threat-color);
		transform: translateY(-3px);
	}

	.node-hologram {
		position: relative;
		flex-shrink: 0;
	}

	.holo-ring {
		filter: drop-shadow(0 0 8px var(--threat-color));
	}

	.node-progress {
		transition: stroke-dashoffset 1s ease-out;
		animation: progressGlow 2s ease-in-out infinite;
	}

	.node-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 20px;
		height: 20px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.threat-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: threatPulse 2s ease-in-out infinite;
		box-shadow: 0 0 10px currentColor;
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

	.threat-level {
		font-size: 0.7rem;
		font-weight: 600;
		color: var(--threat-color);
		letter-spacing: 0.05em;
		text-shadow: 0 0 8px var(--threat-color);
	}

	.frequency-percent {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 500;
	}

	.source-name {
		font-size: 0.9rem;
		font-weight: 600;
		color: #ffffff;
		word-break: break-word;
		line-height: 1.2;
	}

	.frequency-display {
		display: flex;
		align-items: baseline;
		gap: 0.5rem;
	}

	.frequency-count {
		font-size: 1rem;
		font-weight: 700;
		color: var(--threat-color);
		text-shadow: 0 0 10px var(--threat-color);
	}

	.frequency-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.4);
		font-weight: 400;
		letter-spacing: 0.05em;
	}

	.node-connections {
		position: absolute;
		right: 10px;
		top: 50%;
		transform: translateY(-50%);
		width: 30px;
		height: 60px;
		pointer-events: none;
	}

	.connection-line {
		position: absolute;
		right: 0;
		width: 20px;
		height: 1px;
		background: linear-gradient(90deg, 
			var(--threat-color), 
			transparent);
		opacity: 0.4;
		animation: connectionFlow 3s ease-in-out infinite;
	}

	.line-1 {
		top: 20%;
		animation-delay: 0s;
	}

	.line-2 {
		top: 50%;
		animation-delay: 1s;
	}

	.line-3 {
		top: 80%;
		animation-delay: 2s;
	}

	.selected-analysis {
		flex: 1;
	}

	.analysis-frame {
		position: relative;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(0, 255, 255, 0.03) 50%,
			rgba(255, 0, 255, 0.03) 100%);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 12px;
		padding: 1.5rem;
		overflow: hidden;
	}

	.frame-glow {
		position: absolute;
		top: -2px;
		left: -2px;
		right: -2px;
		bottom: -2px;
		background: linear-gradient(45deg, 
			rgba(0, 255, 255, 0.2), 
			rgba(255, 0, 255, 0.2),
			rgba(0, 150, 255, 0.2));
		border-radius: 12px;
		z-index: -1;
		animation: frameGlow 3s ease-in-out infinite;
	}

	.analysis-header {
		margin-bottom: 1.5rem;
	}

	.selected-name {
		font-size: 1.1rem;
		font-weight: 700;
		color: #ffffff;
		margin-bottom: 0.75rem;
		word-break: break-word;
		text-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
	}

	.threat-assessment {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.threat-badge {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.75rem;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.4) 0%, 
			rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid var(--threat-color);
		border-radius: 6px;
		backdrop-filter: blur(10px);
	}

	.badge-ring {
		width: 8px;
		height: 8px;
		border: 2px solid var(--threat-color);
		border-radius: 50%;
		animation: badgeRingPulse 2s ease-in-out infinite;
	}

	.threat-text {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--threat-color);
		letter-spacing: 0.05em;
		text-shadow: 0 0 8px var(--threat-color);
	}

	.analysis-metrics {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.analysis-metric {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		padding: 0.75rem;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.4) 0%, 
			rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		backdrop-filter: blur(10px);
	}

	.analysis-metric .metric-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 400;
		letter-spacing: 0.05em;
	}

	.analysis-metric .metric-value {
		font-size: 1rem;
		font-weight: 700;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}

	.neural-visualization {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(0, 255, 255, 0.02) 100%);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 8px;
		padding: 1rem;
	}

	.viz-title {
		font-size: 0.8rem;
		font-weight: 600;
		color: rgba(0, 255, 255, 0.8);
		margin-bottom: 1rem;
		letter-spacing: 0.05em;
	}

	.pattern-grid {
		display: grid;
		grid-template-columns: repeat(6, 1fr);
		gap: 0.5rem;
	}

	.pattern-node {
		width: 20px;
		height: 20px;
		background: radial-gradient(circle, 
			rgba(0, 255, 255, 0.6), 
			transparent);
		border-radius: 50%;
		animation: patternPulse 2s ease-in-out infinite;
	}

	.analysis-prompt {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		flex: 1;
		gap: 1.5rem;
		text-align: center;
	}

	.prompt-hologram {
		position: relative;
		width: 80px;
		height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.prompt-rings {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
	}

	.prompt-ring {
		position: absolute;
		border-radius: 50%;
		border: 2px solid rgba(255, 255, 255, 0.2);
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: promptRotate 6s linear infinite;
	}

	.prompt-ring.ring-1 {
		width: 80px;
		height: 80px;
	}

	.prompt-ring.ring-2 {
		width: 60px;
		height: 60px;
		animation-direction: reverse;
		animation-duration: 4s;
	}

	.prompt-center {
		position: relative;
		z-index: 3;
		font-size: 2rem;
		color: rgba(255, 255, 255, 0.4);
		animation: promptPulse 3s ease-in-out infinite;
	}

	.prompt-text {
		font-size: 1rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
	}

	.prompt-subtext {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.4);
		font-weight: 300;
	}

	.threat-distribution {
		margin-top: 2rem;
		padding-top: 1.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}

	.distribution-title {
		font-size: 0.9rem;
		font-weight: 700;
		color: rgba(255, 0, 255, 0.9);
		margin-bottom: 1rem;
		letter-spacing: 0.05em;
	}

	.spectrum-bars {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.spectrum-bar {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.bar-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.bar-label {
		font-size: 0.7rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
	}

	.bar-count {
		font-size: 0.8rem;
		font-weight: 700;
		color: rgba(255, 255, 255, 0.8);
	}

	.bar-container {
		position: relative;
		height: 8px;
		border-radius: 4px;
		overflow: hidden;
	}

	.bar-track {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 4px;
	}

	.bar-fill {
		position: relative;
		height: 100%;
		border-radius: 4px;
		transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1);
		animation: barShimmer 3s ease-in-out infinite;
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
			rgba(255, 255, 255, 0.3), 
			transparent);
		animation: barSweep 3s linear infinite;
	}

	@keyframes scanRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes centerPulse {
		0%, 100% { opacity: 0.9; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.1); }
	}

	@keyframes textGlow {
		0%, 100% { text-shadow: 0 0 10px rgba(0, 255, 255, 0.5); }
		50% { text-shadow: 0 0 20px rgba(0, 255, 255, 0.8); }
	}

	@keyframes ringGlow {
		0%, 100% { filter: drop-shadow(0 0 5px currentColor); }
		50% { filter: drop-shadow(0 0 15px currentColor); }
	}

	@keyframes searchScan {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes particlePulse {
		0%, 100% { opacity: 0.6; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.2); }
	}

	@keyframes symbolFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-3px); }
	}

	@keyframes progressGlow {
		0%, 100% { filter: drop-shadow(0 0 5px currentColor); }
		50% { filter: drop-shadow(0 0 15px currentColor); }
	}

	@keyframes threatPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.2); }
	}

	@keyframes connectionFlow {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 0.8; }
	}

	@keyframes frameGlow {
		0%, 100% { opacity: 0.2; }
		50% { opacity: 0.4; }
	}

	@keyframes badgeRingPulse {
		0%, 100% { 
			border-color: var(--threat-color); 
			box-shadow: 0 0 5px var(--threat-color);
		}
		50% { 
			border-color: rgba(255, 255, 255, 0.8); 
			box-shadow: 0 0 15px var(--threat-color);
		}
	}

	@keyframes patternPulse {
		0%, 100% { opacity: 0.3; transform: scale(1); }
		50% { opacity: 0.8; transform: scale(1.1); }
	}

	@keyframes promptRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes promptPulse {
		0%, 100% { opacity: 0.4; transform: scale(1); }
		50% { opacity: 0.6; transform: scale(1.05); }
	}

	@keyframes barShimmer {
		0%, 100% { opacity: 0.8; }
		50% { opacity: 1; }
	}

	@keyframes barSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@media (max-width: 1200px) {
		.data-matrix {
			grid-template-columns: 1fr;
			gap: 1.5rem;
		}
	}

	@media (max-width: 768px) {
		.intelligence-header {
			flex-direction: column;
			gap: 1rem;
		}

		.metrics-cluster {
			justify-content: center;
		}

		.holographic-grid {
			grid-template-columns: 1fr;
		}

		.analysis-metrics {
			grid-template-columns: 1fr;
		}
	}
</style>