<!-- ech/SourceTables.svelte -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let searchTerm = '';
	let selectedSource = null;

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			let result = await response.json();
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
		let percentage = (frequency / data.total_mentions) * 100;
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
		let percentage = (frequency / maxFrequency) * 100;
		let circumference = 2 * Math.PI * 45;
		let strokeDasharray = circumference;
		let strokeDashoffset = circumference - (percentage / 100) * circumference;
		return { strokeDasharray, strokeDashoffset };
	}

	function getThreatCount(level) {
		return filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === level).length;
	}

	function getMaxThreatCount() {
		return Math.max(
			filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'CRITICAL').length,
			filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'HIGH').length,
			filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'MEDIUM').length,
			filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'LOW').length
		);
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
					<div class="scan-ring ring-4"></div>
				</div>
				<div class="scan-center">◈</div>
				<div class="scan-particles">
					{#each Array(8) as _, i}
						<div class="scan-particle" style="animation-delay: {i * 0.2}s; transform: rotate({i * 45}deg) translateX(40px)"></div>
					{/each}
				</div>
			</div>
			<div class="scanner-text">ANALYZING SOURCE INTELLIGENCE MATRIX</div>
			<div class="scanner-progress">
				<div class="progress-wave"></div>
			</div>
		</div>
	{:else}
		<div class="intelligence-header">
			<div class="metrics-cluster">
				<div class="holo-metric primary">
					<div class="metric-ring">
						<svg width="140" height="140" viewBox="0 0 140 140" class="metric-svg">
							<defs>
								<radialGradient id="primaryGlow" cx="50%" cy="50%" r="50%">
									<stop offset="0%" style="stop-color:#00ffff;stop-opacity:0.6" />
									<stop offset="70%" style="stop-color:#0088cc;stop-opacity:0.3" />
									<stop offset="100%" style="stop-color:transparent;stop-opacity:0" />
								</radialGradient>
								<linearGradient id="uniqueGradient" x1="0%" y1="0%" x2="100%" y2="0%">
									<stop offset="0%" style="stop-color:#00ffff;stop-opacity:1" />
									<stop offset="50%" style="stop-color:#0099ff;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#ff00ff;stop-opacity:1" />
								</linearGradient>
								<filter id="ringGlow">
									<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
									<feMerge>
										<feMergeNode in="coloredBlur"/>
										<feMergeNode in="SourceGraphic"/>
									</feMerge>
								</filter>
							</defs>
							<circle cx="70" cy="70" r="55" fill="url(#primaryGlow)" opacity="0.4"/>
							<circle cx="70" cy="70" r="50" fill="none" stroke="rgba(0, 255, 255, 0.1)" stroke-width="2"/>
							<circle 
								cx="70" cy="70" r="50" 
								fill="none" 
								stroke="url(#uniqueGradient)" 
								stroke-width="4"
								stroke-dasharray="314"
								stroke-dashoffset="50"
								transform="rotate(-90 70 70)"
								class="progress-ring primary-ring"
								filter="url(#ringGlow)"
							/>
							<circle cx="70" cy="70" r="35" fill="none" stroke="rgba(0, 255, 255, 0.2)" stroke-width="1" stroke-dasharray="2,2" class="guide-ring"/>
						</svg>
						<div class="metric-center">
							<span class="metric-value">{(data.unique_sources || 0).toLocaleString()}</span>
							<span class="metric-label">UNIQUE SOURCES</span>
							<div class="metric-pulse"></div>
						</div>
					</div>
				</div>
				
				<div class="holo-metric secondary">
					<div class="metric-ring">
						<svg width="140" height="140" viewBox="0 0 140 140" class="metric-svg">
							<defs>
								<radialGradient id="secondaryGlow" cx="50%" cy="50%" r="50%">
									<stop offset="0%" style="stop-color:#ff00ff;stop-opacity:0.6" />
									<stop offset="70%" style="stop-color:#cc0088;stop-opacity:0.3" />
									<stop offset="100%" style="stop-color:transparent;stop-opacity:0" />
								</radialGradient>
								<linearGradient id="mentionsGradient" x1="0%" y1="0%" x2="100%" y2="0%">
									<stop offset="0%" style="stop-color:#ff00ff;stop-opacity:1" />
									<stop offset="50%" style="stop-color:#cc0099;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#0096ff;stop-opacity:1" />
								</linearGradient>
							</defs>
							<circle cx="70" cy="70" r="55" fill="url(#secondaryGlow)" opacity="0.4"/>
							<circle cx="70" cy="70" r="50" fill="none" stroke="rgba(255, 0, 255, 0.1)" stroke-width="2"/>
							<circle 
								cx="70" cy="70" r="50" 
								fill="none" 
								stroke="url(#mentionsGradient)" 
								stroke-width="4"
								stroke-dasharray="314"
								stroke-dashoffset="100"
								transform="rotate(-90 70 70)"
								class="progress-ring secondary-ring"
								filter="url(#ringGlow)"
							/>
							<circle cx="70" cy="70" r="35" fill="none" stroke="rgba(255, 0, 255, 0.2)" stroke-width="1" stroke-dasharray="2,2" class="guide-ring"/>
						</svg>
						<div class="metric-center">
							<span class="metric-value">{(data.total_mentions || 0).toLocaleString()}</span>
							<span class="metric-label">TOTAL MENTIONS</span>
							<div class="metric-pulse"></div>
						</div>
					</div>
				</div>

				<div class="holo-metric tertiary">
					<div class="metric-ring">
						<svg width="140" height="140" viewBox="0 0 140 140" class="metric-svg">
							<defs>
								<radialGradient id="tertiaryGlow" cx="50%" cy="50%" r="50%">
									<stop offset="0%" style="stop-color:#0096ff;stop-opacity:0.6" />
									<stop offset="70%" style="stop-color:#0066cc;stop-opacity:0.3" />
									<stop offset="100%" style="stop-color:transparent;stop-opacity:0" />
								</radialGradient>
								<linearGradient id="threatGradient" x1="0%" y1="0%" x2="100%" y2="0%">
									<stop offset="0%" style="stop-color:#0096ff;stop-opacity:1" />
									<stop offset="33%" style="stop-color:#ffaa00;stop-opacity:1" />
									<stop offset="66%" style="stop-color:#ff0066;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#ff00ff;stop-opacity:1" />
								</linearGradient>
							</defs>
							<circle cx="70" cy="70" r="55" fill="url(#tertiaryGlow)" opacity="0.4"/>
							<circle cx="70" cy="70" r="50" fill="none" stroke="rgba(0, 150, 255, 0.1)" stroke-width="2"/>
							<circle 
								cx="70" cy="70" r="50" 
								fill="none" 
								stroke="url(#threatGradient)" 
								stroke-width="4"
								stroke-dasharray="314"
								stroke-dashoffset="150"
								transform="rotate(-90 70 70)"
								class="progress-ring tertiary-ring"
								filter="url(#ringGlow)"
							/>
							<circle cx="70" cy="70" r="35" fill="none" stroke="rgba(0, 150, 255, 0.2)" stroke-width="1" stroke-dasharray="2,2" class="guide-ring"/>
						</svg>
						<div class="metric-center">
							<span class="metric-value">{filteredSources.length}</span>
							<span class="metric-label">FILTERED RESULTS</span>
							<div class="metric-pulse"></div>
						</div>
					</div>
				</div>
			</div>

			<div class="neural-search">
				<div class="search-frame">
					<div class="search-border">
						<div class="border-glow"></div>
					</div>
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="NEURAL SEARCH PROTOCOL ACTIVE..."
						class="search-input"
					/>
					<div class="search-beam"></div>
					<div class="search-particles">
						<div class="particle"></div>
						<div class="particle"></div>
						<div class="particle"></div>
						<div class="particle"></div>
					</div>
					<div class="search-scanner">
						<div class="scanner-line"></div>
					</div>
				</div>
			</div>
		</div>

		<div class="data-matrix">
			<div class="source-hologram">
				<div class="matrix-title">
					<div class="title-hologram">
						<div class="title-ring"></div>
						<span class="title-symbol">◈</span>
					</div>
					<div class="title-text">
						<span class="title-main">SOURCE THREAT HOLOGRAM</span>
						<span class="title-sub">Neural Classification Matrix</span>
					</div>
				</div>
				
				<div class="holographic-grid">
					{#each filteredSources.slice(0, 24) as [source, frequency], index}
						{@html (() => {
							let threat = getThreatLevel(frequency);
							let progress = getCircularProgress(frequency);
							return '';
						})()}
						<div 
							class="source-node"
							style="--threat-color: {getThreatLevel(frequency).color}; --threat-intensity: {getThreatLevel(frequency).intensity}; --node-delay: {index * 0.05}s"
							on:click={() => selectSource(source, frequency)}
						>
							<div class="node-hologram">
								<svg width="90" height="90" viewBox="0 0 90 90" class="holo-ring">
									<defs>
										<filter id="nodeGlow{index}">
											<feGaussianBlur stdDeviation="2" result="coloredBlur"/>
											<feMerge>
												<feMergeNode in="coloredBlur"/>
												<feMergeNode in="SourceGraphic"/>
											</feMerge>
										</filter>
									</defs>
									<circle cx="45" cy="45" r="35" fill="none" stroke="rgba(255, 255, 255, 0.05)" stroke-width="1"/>
									<circle cx="45" cy="45" r="30" fill="none" stroke="rgba(255, 255, 255, 0.1)" stroke-width="2"/>
									<circle 
										cx="45" cy="45" r="30" 
										fill="none" 
										stroke="{getThreatLevel(frequency).color}" 
										stroke-width="3"
										stroke-dasharray="{getCircularProgress(frequency).strokeDasharray}"
										stroke-dashoffset="{getCircularProgress(frequency).strokeDashoffset}"
										transform="rotate(-90 45 45)"
										class="node-progress"
										filter="url(#nodeGlow{index})"
									/>
									<circle cx="45" cy="45" r="20" fill="none" stroke="rgba(255, 255, 255, 0.05)" stroke-width="1" stroke-dasharray="1,1" class="inner-guide"/>
								</svg>
								<div class="node-core">
									<div class="threat-indicator" style="background: {getThreatLevel(frequency).color}"></div>
									<div class="core-particles">
										{#each Array(3) as _, i}
											<div class="core-particle" style="animation-delay: {i * 0.3}s"></div>
										{/each}
									</div>
								</div>
							</div>
							
							<div class="node-data">
								<div class="node-header">
									<span class="threat-level">{getThreatLevel(frequency).level}</span>
									<span class="frequency-percent">{getPercentage(frequency)}%</span>
								</div>
								<div class="source-name">{source}</div>
								<div class="frequency-display">
									<span class="frequency-count">{frequency.toLocaleString()}</span>
									<span class="frequency-label">INSTANCES</span>
								</div>
								<div class="node-metrics">
									<div class="metric-bar">
										<div class="bar-fill" style="width: {(frequency / maxFrequency) * 100}%; background: linear-gradient(90deg, {getThreatLevel(frequency).color}, transparent);"></div>
									</div>
								</div>
							</div>
							
							<div class="node-connections">
								<div class="connection-line line-1"></div>
								<div class="connection-line line-2"></div>
								<div class="connection-line line-3"></div>
								<div class="connection-hub"></div>
							</div>

							<div class="node-overlay">
								<div class="overlay-glow"></div>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<div class="analysis-hologram">
				<div class="matrix-title">
					<div class="title-hologram">
						<div class="title-ring secondary"></div>
						<span class="title-symbol">◆</span>
					</div>
					<div class="title-text">
						<span class="title-main">NEURAL ANALYSIS CORE</span>
						<span class="title-sub">Deep Intelligence Mining</span>
					</div>
				</div>
				
				{#if selectedSource}
					<div class="selected-analysis">
						<div class="analysis-frame">
							<div class="frame-glow"></div>
							<div class="frame-particles">
								{#each Array(6) as _, i}
									<div class="frame-particle" style="animation-delay: {i * 0.4}s"></div>
								{/each}
							</div>
							
							<div class="analysis-header">
								<div class="selected-name">{selectedSource.source}</div>
								<div class="threat-assessment">
									{@html (() => {
										let threat = getThreatLevel(selectedSource.frequency);
										return '';
									})()}
									<div class="threat-badge" style="--threat-color: {getThreatLevel(selectedSource.frequency).color}">
										<div class="badge-ring"></div>
										<div class="badge-pulse"></div>
										<span class="threat-text">THREAT LEVEL: {getThreatLevel(selectedSource.frequency).level}</span>
									</div>
								</div>
							</div>
							
							<div class="analysis-metrics">
								<div class="analysis-metric">
									<div class="metric-icon">◉</div>
									<span class="metric-label">FREQUENCY</span>
									<span class="metric-value">{selectedSource.frequency.toLocaleString()}</span>
									<div class="metric-sparkle"></div>
								</div>
								<div class="analysis-metric">
									<div class="metric-icon">◯</div>
									<span class="metric-label">PERCENTAGE</span>
									<span class="metric-value">{getPercentage(selectedSource.frequency)}%</span>
									<div class="metric-sparkle"></div>
								</div>
								<div class="analysis-metric">
									<div class="metric-icon">◈</div>
									<span class="metric-label">THREAT LEVEL</span>
									<span class="metric-value" style="color: {getThreatLevel(selectedSource.frequency).color}">
										{getThreatLevel(selectedSource.frequency).level}
									</span>
									<div class="metric-sparkle"></div>
								</div>
							</div>

							<div class="neural-visualization">
								<div class="viz-header">
									<div class="viz-title">NEURAL PATTERN ANALYSIS</div>
									<div class="viz-status">ACTIVE SCAN</div>
								</div>
								<div class="pattern-grid">
									{#each Array(16) as _, i}
										<div 
											class="pattern-node" 
											style="animation-delay: {i * 0.08}s; opacity: {Math.random() * 0.6 + 0.3}; --pattern-color: {i % 4 === 0 ? '#00ffff' : i % 4 === 1 ? '#ff00ff' : i % 4 === 2 ? '#0096ff' : '#ffaa00'}"
										>
											<div class="pattern-core"></div>
										</div>
									{/each}
								</div>
								<div class="pattern-connections">
									{#each Array(8) as _, i}
										<div class="pattern-line" style="animation-delay: {i * 0.2}s"></div>
									{/each}
								</div>
							</div>

							<div class="data-breakdown">
								<div class="breakdown-title">DATA COMPOSITION ANALYSIS</div>
								<div class="composition-bars">
									<div class="comp-bar">
										<span class="comp-label">CRITICAL INSTANCES</span>
										<div class="comp-fill" style="width: {getThreatLevel(selectedSource.frequency).level === 'CRITICAL' ? 100 : 0}%; background: #ff00ff;"></div>
										<span class="comp-value">{getThreatLevel(selectedSource.frequency).level === 'CRITICAL' ? selectedSource.frequency : 0}</span>
									</div>
									<div class="comp-bar">
										<span class="comp-label">HIGH PRIORITY</span>
										<div class="comp-fill" style="width: {getThreatLevel(selectedSource.frequency).level === 'HIGH' ? 100 : 0}%; background: #ff0066;"></div>
										<span class="comp-value">{getThreatLevel(selectedSource.frequency).level === 'HIGH' ? selectedSource.frequency : 0}</span>
									</div>
									<div class="comp-bar">
										<span class="comp-label">MEDIUM RISK</span>
										<div class="comp-fill" style="width: {getThreatLevel(selectedSource.frequency).level === 'MEDIUM' ? 100 : 0}%; background: #ffaa00;"></div>
										<span class="comp-value">{getThreatLevel(selectedSource.frequency).level === 'MEDIUM' ? selectedSource.frequency : 0}</span>
									</div>
									<div class="comp-bar">
										<span class="comp-label">LOW IMPACT</span>
										<div class="comp-fill" style="width: {getThreatLevel(selectedSource.frequency).level === 'LOW' ? 100 : 0}%; background: #00ffff;"></div>
										<span class="comp-value">{getThreatLevel(selectedSource.frequency).level === 'LOW' ? selectedSource.frequency : 0}</span>
									</div>
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
								<div class="prompt-ring ring-3"></div>
							</div>
							<div class="prompt-center">◯</div>
							<div class="prompt-particles">
								{#each Array(6) as _, i}
									<div class="prompt-particle" style="animation-delay: {i * 0.3}s; transform: rotate({i * 60}deg) translateX(30px)"></div>
								{/each}
							</div>
						</div>
						<div class="prompt-text">SELECT SOURCE NODE FOR DEEP ANALYSIS</div>
						<div class="prompt-subtext">NEURAL INTERFACE READY FOR QUANTUM PROCESSING</div>
						<div class="prompt-indicators">
							{#each Array(3) as _, i}
								<div class="indicator" style="animation-delay: {i * 0.2}s"></div>
							{/each}
						</div>
					</div>
				{/if}

				<div class="threat-distribution">
					<div class="distribution-header">
						<div class="distribution-title">THREAT SPECTRUM ANALYSIS</div>
						<div class="spectrum-indicator">REAL-TIME</div>
					</div>
					<div class="spectrum-bars">
						{#each [['CRITICAL', '#ff00ff'], ['HIGH', '#ff0066'], ['MEDIUM', '#ffaa00'], ['LOW', '#00ffff']] as [level, color]}
							{@html (() => {
								let count = getThreatCount(level);
								let maxCount = getMaxThreatCount();
								return '';
							})()}
							<div class="spectrum-bar">
								<div class="bar-header">
									<span class="bar-label">{level}</span>
									<span class="bar-count">{getThreatCount(level)}</span>
								</div>
								<div class="bar-container">
									<div class="bar-track"></div>
									<div 
										class="bar-fill advanced" 
										style="width: {getMaxThreatCount() > 0 ? (getThreatCount(level) / getMaxThreatCount()) * 100 : 0}%; background: linear-gradient(90deg, {color}, transparent); box-shadow: 0 0 15px {color};"
									>
										<div class="bar-shine"></div>
									</div>
								</div>
								<div class="bar-particles">
									{#each Array(2) as _, i}
										<div class="bar-particle" style="background: {color}; animation-delay: {i * 0.5}s"></div>
									{/each}
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
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.95) 0%, 
			rgba(26, 13, 46, 0.3) 50%,
			rgba(0, 0, 0, 0.95) 100%);
	}

	.neural-scanner {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 500px;
		gap: 3rem;
	}

	.scanner-core {
		position: relative;
		width: 160px;
		height: 160px;
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
		animation: scanRotate 4s linear infinite;
	}

	.ring-1 {
		width: 160px;
		height: 160px;
		border-color: rgba(0, 255, 255, 0.6);
		animation-duration: 6s;
	}

	.ring-2 {
		width: 120px;
		height: 120px;
		border-color: rgba(255, 0, 255, 0.4);
		animation-duration: 4s;
		animation-direction: reverse;
	}

	.ring-3 {
		width: 80px;
		height: 80px;
		border-color: rgba(0, 150, 255, 0.8);
		animation-duration: 3s;
	}

	.ring-4 {
		width: 40px;
		height: 40px;
		border-color: rgba(255, 170, 0, 0.6);
		animation-duration: 2s;
		animation-direction: reverse;
	}

	.scan-center {
		position: relative;
		z-index: 5;
		font-size: 2.5rem;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 30px rgba(0, 255, 255, 0.8);
		animation: centerPulse 3s ease-in-out infinite;
	}

	.scan-particles {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	.scan-particle {
		position: absolute;
		width: 4px;
		height: 4px;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.8), transparent);
		border-radius: 50%;
		top: 50%;
		left: 50%;
		transform-origin: 0 0;
		animation: particleOrbit 3s linear infinite;
	}

	.scanner-text {
		color: rgba(0, 255, 255, 0.8);
		font-size: 1.1rem;
		font-weight: 600;
		letter-spacing: 0.15em;
		animation: textGlow 3s ease-in-out infinite;
		text-align: center;
	}

	.scanner-progress {
		width: 300px;
		height: 6px;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 3px;
		overflow: hidden;
		position: relative;
		border: 1px solid rgba(0, 255, 255, 0.2);
	}

	.progress-wave {
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			transparent 0%, 
			rgba(0, 255, 255, 0.3) 25%, 
			rgba(0, 255, 255, 0.6) 50%, 
			rgba(0, 255, 255, 0.3) 75%, 
			transparent 100%);
		animation: progressWave 2s linear infinite;
	}

	.intelligence-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2.5rem;
		gap: 3rem;
		padding: 0 1rem;
	}

	.metrics-cluster {
		display: flex;
		gap: 2.5rem;
	}

	.holo-metric {
		position: relative;
		transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.holo-metric:hover {
		transform: translateY(-5px);
	}

	.metric-ring {
		position: relative;
		width: 140px;
		height: 140px;
		cursor: pointer;
	}

	.metric-svg {
		filter: drop-shadow(0 0 10px rgba(0, 255, 255, 0.3));
	}

	.progress-ring {
		transition: stroke-dashoffset 2s cubic-bezier(0.4, 0, 0.2, 1);
		animation: ringPulse 4s ease-in-out infinite;
	}

	.primary-ring {
		animation-delay: 0s;
	}

	.secondary-ring {
		animation-delay: 1.3s;
	}

	.tertiary-ring {
		animation-delay: 2.6s;
	}

	.guide-ring {
		animation: guideRotate 15s linear infinite;
	}

	.metric-center {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
		z-index: 10;
	}

	.metric-value {
		display: block;
		font-size: 1.6rem;
		font-weight: 700;
		color: #ffffff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.6);
		margin-bottom: 0.2rem;
		animation: valueGlow 3s ease-in-out infinite;
	}

	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 500;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.metric-pulse {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 80px;
		height: 80px;
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 50%;
		animation: metricPulse 4s ease-in-out infinite;
		pointer-events: none;
	}

	.neural-search {
		flex: 1;
		max-width: 450px;
	}

	.search-frame {
		position: relative;
		width: 100%;
	}

	.search-border {
		position: absolute;
		top: -2px;
		left: -2px;
		right: -2px;
		bottom: -2px;
		border-radius: 10px;
		overflow: hidden;
	}

	.border-glow {
		width: 100%;
		height: 100%;
		background: linear-gradient(45deg, 
			rgba(0, 255, 255, 0.3) 0%, 
			rgba(255, 0, 255, 0.2) 25%,
			rgba(0, 150, 255, 0.3) 50%,
			rgba(255, 0, 255, 0.2) 75%,
			rgba(0, 255, 255, 0.3) 100%);
		animation: borderFlow 3s linear infinite;
	}

	.search-input {
		width: 100%;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(0, 255, 255, 0.05) 50%,
			rgba(0, 0, 0, 0.8) 100%);
		border: 1px solid rgba(0, 255, 255, 0.4);
		border-radius: 8px;
		padding: 1rem 1.5rem;
		color: #ffffff;
		font-family: inherit;
		font-size: 0.9rem;
		font-weight: 500;
		backdrop-filter: blur(20px);
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.1);
		position: relative;
		z-index: 10;
	}

	.search-input::placeholder {
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.08em;
		font-weight: 400;
	}

	.search-input:focus {
		outline: none;
		border-color: rgba(0, 255, 255, 0.8);
		box-shadow: 0 0 30px rgba(0, 255, 255, 0.4);
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
	}

	.search-beam {
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(0, 255, 255, 0.3), 
			transparent);
		animation: searchScan 4s linear infinite;
		border-radius: 8px;
		pointer-events: none;
	}

	.search-particles {
		position: absolute;
		top: 50%;
		right: 20px;
		transform: translateY(-50%);
		display: flex;
		gap: 4px;
	}

	.particle {
		width: 4px;
		height: 4px;
		background: rgba(0, 255, 255, 0.7);
		border-radius: 50%;
		animation: particlePulse 1.8s ease-in-out infinite;
	}

	.particle:nth-child(2) { animation-delay: 0.6s; }
	.particle:nth-child(3) { animation-delay: 1.2s; }
	.particle:nth-child(4) { animation-delay: 1.8s; }

	.search-scanner {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		border-radius: 8px;
		overflow: hidden;
	}

	.scanner-line {
		width: 2px;
		height: 100%;
		background: linear-gradient(180deg, 
			transparent, 
			rgba(0, 255, 255, 0.8), 
			transparent);
		animation: scannerSweep 3s linear infinite;
	}

	.data-matrix {
		display: grid;
		grid-template-columns: 1fr 450px;
		gap: 2.5rem;
		height: calc(100vh - 400px);
	}

	.source-hologram {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(0, 255, 255, 0.03) 25%,
			rgba(255, 0, 255, 0.03) 75%,
			rgba(0, 0, 0, 0.6) 100%);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 20px;
		padding: 2rem;
		backdrop-filter: blur(25px);
		overflow: hidden;
		position: relative;
		box-shadow: 
			0 10px 40px rgba(0, 0, 0, 0.4),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
	}

	.analysis-hologram {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(255, 0, 255, 0.03) 25%,
			rgba(0, 150, 255, 0.03) 75%,
			rgba(0, 0, 0, 0.6) 100%);
		border: 1px solid rgba(255, 0, 255, 0.3);
		border-radius: 20px;
		padding: 2rem;
		backdrop-filter: blur(25px);
		display: flex;
		flex-direction: column;
		overflow-y: auto;
		box-shadow: 
			0 10px 40px rgba(0, 0, 0, 0.4),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
	}

	.matrix-title {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 2rem;
	}

	.title-hologram {
		position: relative;
		width: 50px;
		height: 50px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.title-ring {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		border: 2px solid rgba(0, 255, 255, 0.6);
		border-radius: 50%;
		animation: titleRotate 8s linear infinite;
	}

	.title-ring.secondary {
		border-color: rgba(255, 0, 255, 0.6);
		animation-direction: reverse;
		animation-duration: 6s;
	}

	.title-symbol {
		font-size: 1.4rem;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 20px currentColor;
		animation: symbolFloat 4s ease-in-out infinite;
		position: relative;
		z-index: 2;
	}

	.title-text {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.title-main {
		font-size: 1.1rem;
		font-weight: 700;
		color: rgba(0, 255, 255, 0.9);
		letter-spacing: 0.08em;
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
	}

	.title-sub {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 400;
		letter-spacing: 0.05em;
	}

	.holographic-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		gap: 1.2rem;
		height: calc(100% - 80px);
		overflow-y: auto;
		padding-right: 0.8rem;
	}

	.source-node {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.7) 0%, 
			rgba(255, 255, 255, 0.02) 50%,
			rgba(0, 0, 0, 0.7) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 16px;
		padding: 1.2rem;
		cursor: pointer;
		position: relative;
		transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
		overflow: hidden;
		display: flex;
		align-items: center;
		gap: 1.2rem;
		animation: nodeAppear 0.6s ease-out;
		animation-delay: var(--node-delay);
		animation-fill-mode: both;
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
			rgba(255, 255, 255, 0.08), 
			transparent);
		transition: left 0.8s ease;
	}

	.source-node:hover::before {
		left: 100%;
	}

	.source-node:hover {
		border-color: var(--threat-color);
		box-shadow: 
			0 10px 40px rgba(0, 0, 0, 0.5),
			0 0 25px var(--threat-color);
		transform: translateY(-5px) scale(1.02);
	}

	.node-hologram {
		position: relative;
		flex-shrink: 0;
	}

	.holo-ring {
		filter: drop-shadow(0 0 10px var(--threat-color));
		transition: filter 0.3s ease;
	}

	.node-progress {
		transition: stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1);
		animation: progressGlow 3s ease-in-out infinite;
	}

	.inner-guide {
		animation: innerGuideRotate 10s linear infinite;
	}

	.node-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 25px;
		height: 25px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.threat-indicator {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		animation: threatPulse 2.5s ease-in-out infinite;
		box-shadow: 0 0 15px currentColor;
		position: relative;
		z-index: 2;
	}

	.core-particles {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	.core-particle {
		position: absolute;
		width: 2px;
		height: 2px;
		background: var(--threat-color);
		border-radius: 50%;
		top: 50%;
		left: 50%;
		transform-origin: 0 0;
		animation: coreParticleOrbit 4s linear infinite;
	}

	.node-data {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.node-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.threat-level {
		font-size: 0.7rem;
		font-weight: 700;
		color: var(--threat-color);
		letter-spacing: 0.08em;
		text-shadow: 0 0 10px var(--threat-color);
		padding: 0.2rem 0.5rem;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 4px;
		border: 1px solid var(--threat-color);
	}

	.frequency-percent {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
		text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
	}

	.source-name {
		font-size: 0.95rem;
		font-weight: 600;
		color: #ffffff;
		word-break: break-word;
		line-height: 1.3;
		text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
	}

	.frequency-display {
		display: flex;
		align-items: baseline;
		gap: 0.6rem;
	}

	.frequency-count {
		font-size: 1.1rem;
		font-weight: 700;
		color: var(--threat-color);
		text-shadow: 0 0 15px var(--threat-color);
	}

	.frequency-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.4);
		font-weight: 500;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.node-metrics {
		margin-top: 0.5rem;
	}

	.metric-bar {
		height: 4px;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 2px;
		overflow: hidden;
		position: relative;
	}

	.bar-fill {
		height: 100%;
		border-radius: 2px;
		transition: width 2s cubic-bezier(0.4, 0, 0.2, 1);
		position: relative;
		box-shadow: 0 0 8px rgba(255, 255, 255, 0.2);
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
			rgba(255, 255, 255, 0.6), 
			transparent);
		animation: barSweep 3s linear infinite;
	}

	.node-connections {
		position: absolute;
		right: 15px;
		top: 50%;
		transform: translateY(-50%);
		width: 35px;
		height: 70px;
		pointer-events: none;
	}

	.connection-line {
		position: absolute;
		right: 0;
		width: 25px;
		height: 1px;
		background: linear-gradient(90deg, 
			var(--threat-color), 
			transparent);
		opacity: 0.5;
		animation: connectionFlow 4s ease-in-out infinite;
	}

	.line-1 {
		top: 20%;
		animation-delay: 0s;
	}

	.line-2 {
		top: 50%;
		animation-delay: 1.3s;
	}

	.line-3 {
		top: 80%;
		animation-delay: 2.6s;
	}

	.connection-hub {
		position: absolute;
		right: -2px;
		top: 50%;
		transform: translateY(-50%);
		width: 6px;
		height: 6px;
		background: var(--threat-color);
		border-radius: 50%;
		animation: hubPulse 2s ease-in-out infinite;
		box-shadow: 0 0 8px var(--threat-color);
	}

	.node-overlay {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		pointer-events: none;
		border-radius: 16px;
		overflow: hidden;
	}

	.overlay-glow {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 200%;
		height: 200%;
		background: radial-gradient(circle, var(--threat-color), transparent);
		opacity: 0;
		transition: opacity 0.5s ease;
	}

	.source-node:hover .overlay-glow {
		opacity: 0.05;
	}

	.selected-analysis {
		flex: 1;
	}

	.analysis-frame {
		position: relative;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(0, 255, 255, 0.04) 25%,
			rgba(255, 0, 255, 0.04) 75%,
			rgba(0, 0, 0, 0.8) 100%);
		border: 1px solid rgba(0, 255, 255, 0.4);
		border-radius: 16px;
		padding: 2rem;
		overflow: hidden;
	}

	.frame-glow {
		position: absolute;
		top: -3px;
		left: -3px;
		right: -3px;
		bottom: -3px;
		background: linear-gradient(45deg, 
			rgba(0, 255, 255, 0.3), 
			rgba(255, 0, 255, 0.2),
			rgba(0, 150, 255, 0.3),
			rgba(255, 0, 255, 0.2));
		border-radius: 16px;
		z-index: -1;
		animation: frameGlow 4s ease-in-out infinite;
	}

	.frame-particles {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	.frame-particle {
		position: absolute;
		width: 3px;
		height: 3px;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.6), transparent);
		border-radius: 50%;
		animation: frameParticleFloat 5s ease-in-out infinite;
	}

	.frame-particle:nth-child(1) { top: 10%; left: 10%; }
	.frame-particle:nth-child(2) { top: 20%; right: 10%; }
	.frame-particle:nth-child(3) { bottom: 10%; left: 20%; }
	.frame-particle:nth-child(4) { bottom: 20%; right: 20%; }
	.frame-particle:nth-child(5) { top: 50%; left: 5%; }
	.frame-particle:nth-child(6) { top: 70%; right: 5%; }

	.analysis-header {
		margin-bottom: 2rem;
	}

	.selected-name {
		font-size: 1.2rem;
		font-weight: 700;
		color: #ffffff;
		margin-bottom: 1rem;
		word-break: break-word;
		text-shadow: 0 0 20px rgba(255, 255, 255, 0.4);
		line-height: 1.3;
	}

	.threat-assessment {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.threat-badge {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		padding: 0.8rem 1.2rem;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(255, 255, 255, 0.03) 100%);
		border: 1px solid var(--threat-color);
		border-radius: 8px;
		backdrop-filter: blur(15px);
		position: relative;
		overflow: hidden;
	}

	.badge-ring {
		width: 10px;
		height: 10px;
		border: 2px solid var(--threat-color);
		border-radius: 50%;
		animation: badgeRingPulse 3s ease-in-out infinite;
		position: relative;
		z-index: 2;
	}

	.badge-pulse {
		position: absolute;
		top: 50%;
		left: 10px;
		transform: translate(-50%, -50%);
		width: 20px;
		height: 20px;
		border: 1px solid var(--threat-color);
		border-radius: 50%;
		animation: badgePulseRing 3s ease-in-out infinite;
		pointer-events: none;
	}

	.threat-text {
		font-size: 0.8rem;
		font-weight: 700;
		color: var(--threat-color);
		letter-spacing: 0.08em;
		text-shadow: 0 0 10px var(--threat-color);
		text-transform: uppercase;
	}

	.analysis-metrics {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1.2rem;
		margin-bottom: 2rem;
	}

	.analysis-metric {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 1.2rem;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.6) 0%, 
			rgba(255, 255, 255, 0.03) 100%);
		border: 1px solid rgba(255, 255, 255, 0.15);
		border-radius: 12px;
		backdrop-filter: blur(15px);
		position: relative;
		transition: all 0.3s ease;
	}

	.analysis-metric:hover {
		border-color: rgba(0, 255, 255, 0.4);
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
		transform: translateY(-2px);
	}

	.metric-icon {
		font-size: 1.2rem;
		color: rgba(0, 255, 255, 0.8);
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
		margin-bottom: 0.3rem;
	}

	.analysis-metric .metric-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		font-weight: 500;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		text-align: center;
	}

	.analysis-metric .metric-value {
		font-size: 1.1rem;
		font-weight: 700;
		color: rgba(0, 255, 255, 0.9);
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
		text-align: center;
	}

	.metric-sparkle {
		position: absolute;
		top: 10px;
		right: 10px;
		width: 6px;
		height: 6px;
		background: rgba(0, 255, 255, 0.6);
		border-radius: 50%;
		animation: sparkle 2s ease-in-out infinite;
	}

	.neural-visualization {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.9) 0%, 
			rgba(0, 255, 255, 0.03) 50%,
			rgba(0, 0, 0, 0.9) 100%);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 12px;
		padding: 1.5rem;
		margin-bottom: 2rem;
		position: relative;
	}

	.viz-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.viz-title {
		font-size: 0.85rem;
		font-weight: 700;
		color: rgba(0, 255, 255, 0.8);
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.viz-status {
		font-size: 0.7rem;
		color: rgba(0, 255, 255, 0.6);
		font-weight: 500;
		padding: 0.2rem 0.6rem;
		background: rgba(0, 255, 255, 0.1);
		border-radius: 4px;
		border: 1px solid rgba(0, 255, 255, 0.3);
		animation: statusBlink 2s ease-in-out infinite;
	}

	.pattern-grid {
		display: grid;
		grid-template-columns: repeat(8, 1fr);
		gap: 0.8rem;
		position: relative;
		z-index: 2;
	}

	.pattern-node {
		width: 25px;
		height: 25px;
		background: radial-gradient(circle, 
			var(--pattern-color), 
			transparent);
		border-radius: 50%;
		animation: patternPulse 3s ease-in-out infinite;
		position: relative;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.pattern-node:hover {
		transform: scale(1.2);
		filter: brightness(1.5);
	}

	.pattern-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 8px;
		height: 8px;
		background: #ffffff;
		border-radius: 50%;
		animation: coreFlicker 2s ease-in-out infinite;
	}

	.pattern-connections {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 1;
	}

	.pattern-line {
		position: absolute;
		height: 1px;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(0, 255, 255, 0.4), 
			transparent);
		animation: patternLineFlow 4s ease-in-out infinite;
	}

	.pattern-line:nth-child(1) { top: 20%; width: 60%; left: 10%; }
	.pattern-line:nth-child(2) { top: 40%; width: 80%; left: 5%; }
	.pattern-line:nth-child(3) { top: 60%; width: 50%; right: 10%; }
	.pattern-line:nth-child(4) { top: 80%; width: 70%; left: 15%; }

	.data-breakdown {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(255, 0, 255, 0.03) 100%);
		border: 1px solid rgba(255, 0, 255, 0.3);
		border-radius: 12px;
		padding: 1.5rem;
		margin-bottom: 2rem;
	}

	.breakdown-title {
		font-size: 0.85rem;
		font-weight: 700;
		color: rgba(255, 0, 255, 0.8);
		margin-bottom: 1.2rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.composition-bars {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.comp-bar {
		display: grid;
		grid-template-columns: 1fr 2fr 60px;
		gap: 1rem;
		align-items: center;
	}

	.comp-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}

	.comp-fill {
		height: 8px;
		border-radius: 4px;
		transition: width 2s cubic-bezier(0.4, 0, 0.2, 1);
		position: relative;
		box-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
	}

	.comp-fill::after {
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
		animation: compSweep 3s linear infinite;
	}

	.comp-value {
		font-size: 0.8rem;
		font-weight: 700;
		color: rgba(255, 255, 255, 0.8);
		text-align: right;
	}

	.analysis-prompt {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		flex: 1;
		gap: 2rem;
		text-align: center;
		padding: 2rem;
	}

	.prompt-hologram {
		position: relative;
		width: 100px;
		height: 100px;
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
		border: 2px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: promptRotate 8s linear infinite;
	}

	.prompt-ring.ring-1 {
		width: 100px;
		height: 100px;
		border-color: rgba(255, 255, 255, 0.3);
	}

	.prompt-ring.ring-2 {
		width: 75px;
		height: 75px;
		border-color: rgba(0, 255, 255, 0.4);
		animation-direction: reverse;
		animation-duration: 6s;
	}

	.prompt-ring.ring-3 {
		width: 50px;
		height: 50px;
		border-color: rgba(255, 0, 255, 0.5);
		animation-duration: 4s;
	}

	.prompt-center {
		position: relative;
		z-index: 5;
		font-size: 2.5rem;
		color: rgba(255, 255, 255, 0.4);
		animation: promptPulse 4s ease-in-out infinite;
	}

	.prompt-particles {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	.prompt-particle {
		position: absolute;
		width: 4px;
		height: 4px;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.6), transparent);
		border-radius: 50%;
		top: 50%;
		left: 50%;
		transform-origin: 0 0;
		animation: promptParticleOrbit 5s linear infinite;
	}

	.prompt-text {
		font-size: 1.1rem;
		font-weight: 700;
		color: rgba(255, 255, 255, 0.7);
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.prompt-subtext {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.4);
		font-weight: 400;
		letter-spacing: 0.05em;
		line-height: 1.4;
	}

	.prompt-indicators {
		display: flex;
		gap: 0.8rem;
		margin-top: 1rem;
	}

	.indicator {
		width: 8px;
		height: 8px;
		background: rgba(0, 255, 255, 0.6);
		border-radius: 50%;
		animation: indicatorPulse 2s ease-in-out infinite;
	}

	.threat-distribution {
		margin-top: 2.5rem;
		padding-top: 2rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}

	.distribution-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.distribution-title {
		font-size: 0.9rem;
		font-weight: 700;
		color: rgba(255, 0, 255, 0.9);
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.spectrum-indicator {
		font-size: 0.7rem;
		color: rgba(0, 255, 255, 0.6);
		font-weight: 500;
		padding: 0.3rem 0.8rem;
		background: rgba(0, 255, 255, 0.1);
		border-radius: 4px;
		border: 1px solid rgba(0, 255, 255, 0.3);
		animation: spectrumBlink 3s ease-in-out infinite;
	}

	.spectrum-bars {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.spectrum-bar {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		position: relative;
	}

	.bar-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.bar-label {
		font-size: 0.75rem;
		font-weight: 700;
		color: rgba(255, 255, 255, 0.7);
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.bar-count {
		font-size: 0.85rem;
		font-weight: 700;
		color: rgba(255, 255, 255, 0.9);
		text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
	}

	.bar-container {
		position: relative;
		height: 10px;
		border-radius: 5px;
		overflow: hidden;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.bar-track {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.6);
		border-radius: 5px;
	}

	.bar-fill.advanced {
		position: relative;
		height: 100%;
		border-radius: 5px;
		transition: width 2s cubic-bezier(0.4, 0, 0.2, 1);
		animation: barShimmer 4s ease-in-out infinite;
	}

	.bar-shine {
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(255, 255, 255, 0.4), 
			transparent);
		animation: barSweep 4s linear infinite;
	}

	.bar-particles {
		position: absolute;
		right: 10px;
		top: 50%;
		transform: translateY(-50%);
		display: flex;
		gap: 4px;
	}

	.bar-particle {
		width: 3px;
		height: 3px;
		border-radius: 50%;
		animation: barParticlePulse 2s ease-in-out infinite;
	}

	@keyframes scanRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes centerPulse {
		0%, 100% { opacity: 0.9; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.1); }
	}

	@keyframes particleOrbit {
		0% { transform: rotate(0deg) translateX(25px) rotate(0deg); }
		100% { transform: rotate(360deg) translateX(25px) rotate(-360deg); }
	}

	@keyframes textGlow {
		0%, 100% { text-shadow: 0 0 15px rgba(0, 255, 255, 0.5); }
		50% { text-shadow: 0 0 25px rgba(0, 255, 255, 0.8); }
	}

	@keyframes progressWave {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100%); }
	}

	@keyframes ringPulse {
		0%, 100% { filter: drop-shadow(0 0 8px currentColor); }
		50% { filter: drop-shadow(0 0 20px currentColor); }
	}

	@keyframes guideRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes valueGlow {
		0%, 100% { text-shadow: 0 0 20px rgba(0, 255, 255, 0.6); }
		50% { text-shadow: 0 0 30px rgba(0, 255, 255, 0.9); }
	}

	@keyframes metricPulse {
		0%, 100% { opacity: 0.3; transform: translate(-50%, -50%) scale(1); }
		50% { opacity: 0.6; transform: translate(-50%, -50%) scale(1.05); }
	}

	@keyframes borderFlow {
		0% { transform: translateX(-100%) rotate(0deg); }
		100% { transform: translateX(100%) rotate(360deg); }
	}

	@keyframes searchScan {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes particlePulse {
		0%, 100% { opacity: 0.7; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.3); }
	}

	@keyframes scannerSweep {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100vw); }
	}

	@keyframes titleRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes symbolFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-4px); }
	}

	@keyframes nodeAppear {
		0% { opacity: 0; transform: translateY(30px) scale(0.8); }
		100% { opacity: 1; transform: translateY(0) scale(1); }
	}

	@keyframes progressGlow {
		0%, 100% { filter: drop-shadow(0 0 8px currentColor); }
		50% { filter: drop-shadow(0 0 18px currentColor); }
	}

	@keyframes innerGuideRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(-360deg); }
	}

	@keyframes threatPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.3); }
	}

	@keyframes coreParticleOrbit {
		0% { transform: rotate(0deg) translateX(8px) rotate(0deg); }
		100% { transform: rotate(360deg) translateX(8px) rotate(-360deg); }
	}

	@keyframes barSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes connectionFlow {
		0%, 100% { opacity: 0.5; }
		50% { opacity: 1; }
	}

	@keyframes hubPulse {
		0%, 100% { opacity: 1; transform: translateY(-50%) scale(1); }
		50% { opacity: 0.7; transform: translateY(-50%) scale(1.2); }
	}

	@keyframes frameGlow {
		0%, 100% { opacity: 0.3; }
		50% { opacity: 0.5; }
	}

	@keyframes frameParticleFloat {
		0%, 100% { opacity: 0.3; transform: translateY(0px); }
		50% { opacity: 0.8; transform: translateY(-5px); }
	}

	@keyframes badgeRingPulse {
		0%, 100% { 
			border-color: var(--threat-color); 
			box-shadow: 0 0 8px var(--threat-color);
		}
		50% { 
			border-color: rgba(255, 255, 255, 0.9); 
			box-shadow: 0 0 18px var(--threat-color);
		}
	}

	@keyframes badgePulseRing {
		0%, 100% { opacity: 0; transform: translate(-50%, -50%) scale(1); }
		50% { opacity: 0.6; transform: translate(-50%, -50%) scale(1.5); }
	}

	@keyframes sparkle {
		0%, 100% { opacity: 0.3; transform: scale(1) rotate(0deg); }
		50% { opacity: 1; transform: scale(1.2) rotate(180deg); }
	}

	@keyframes statusBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	@keyframes patternPulse {
		0%, 100% { opacity: 0.4; transform: scale(1); }
		50% { opacity: 0.9; transform: scale(1.15); }
	}

	@keyframes coreFlicker {
		0%, 100% { opacity: 0.8; }
		50% { opacity: 1; }
	}

	@keyframes patternLineFlow {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 0.8; }
	}

	@keyframes compSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes promptRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes promptPulse {
		0%, 100% { opacity: 0.4; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.08); }
	}

	@keyframes promptParticleOrbit {
		0% { transform: rotate(0deg) translateX(35px) rotate(0deg); }
		100% { transform: rotate(360deg) translateX(35px) rotate(-360deg); }
	}

	@keyframes indicatorPulse {
		0%, 100% { opacity: 0.6; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.2); }
	}

	@keyframes spectrumBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.6; }
	}

	@keyframes barShimmer {
		0%, 100% { opacity: 0.9; }
		50% { opacity: 1; }
	}

	@keyframes barParticlePulse {
		0%, 100% { opacity: 0.6; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.3); }
	}

	@media (max-width: 1400px) {
		.data-matrix {
			grid-template-columns: 1fr;
			gap: 2rem;
		}

		.analysis-hologram {
			max-height: 600px;
		}
	}

	@media (max-width: 1024px) {
		.intelligence-header {
			flex-direction: column;
			gap: 2rem;
		}

		.metrics-cluster {
			justify-content: center;
			flex-wrap: wrap;
			gap: 2rem;
		}

		.holographic-grid {
			grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		}

		.analysis-metrics {
			grid-template-columns: 1fr;
		}

		.pattern-grid {
			grid-template-columns: repeat(6, 1fr);
		}
	}

	@media (max-width: 768px) {
		.source-intelligence-matrix {
			padding: 1rem;
		}

		.metrics-cluster {
			flex-direction: column;
			align-items: center;
		}

		.holo-metric {
			width: 120px;
		}

		.metric-ring {
			width: 120px;
			height: 120px;
		}

		.metric-svg {
			width: 120px;
			height: 120px;
		}

		.holographic-grid {
			grid-template-columns: 1fr;
		}

		.source-node {
			flex-direction: column;
			text-align: center;
			gap: 1rem;
		}

		.node-data {
			align-items: center;
		}

		.composition-bars {
			gap: 0.5rem;
		}

		.comp-bar {
			grid-template-columns: 1fr;
			gap: 0.5rem;
			text-align: center;
		}
	}

	@media (max-width: 480px) {
		.scanner-core {
			width: 120px;
			height: 120px;
		}

		.scan-ring.ring-1 {
			width: 120px;
			height: 120px;
		}

		.scan-ring.ring-2 {
			width: 90px;
			height: 90px;
		}

		.scan-ring.ring-3 {
			width: 60px;
			height: 60px;
		}

		.scan-ring.ring-4 {
			width: 30px;
			height: 30px;
		}

		.neural-search {
			width: 100%;
		}

		.search-input {
			padding: 0.8rem 1rem;
			font-size: 0.8rem;
		}

		.source-node {
			padding: 1rem;
		}

		.analysis-frame {
			padding: 1.5rem;
		}

		.pattern-grid {
			grid-template-columns: repeat(4, 1fr);
		}

		.pattern-node {
			width: 20px;
			height: 20px;
		}
	}
</style>