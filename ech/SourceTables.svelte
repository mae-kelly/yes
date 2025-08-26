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
			data = await response.json();
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
		const percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRITICAL', color: '#FF0080' };
		if (percentage >= 10) return { level: 'HIGH', color: '#FF4500' };
		if (percentage >= 5) return { level: 'MEDIUM', color: '#FFE500' };
		return { level: 'LOW', color: '#00FF85' };
	}

	function selectSource(source, frequency) {
		selectedSource = { source, frequency };
	}

	function getThreatStats() {
		return filteredSources.reduce((acc, [source, freq]) => {
			const threat = getThreatLevel(freq);
			acc[threat.level] = (acc[threat.level] || 0) + 1;
			return acc;
		}, {});
	}
</script>

<div class="intel-matrix">
	{#if loading}
		<div class="neural-loader">
			<div class="loader-core">
				<div class="core-ring"></div>
				<div class="core-inner">◈</div>
			</div>
			<div class="loader-text">ANALYZING SOURCE INTELLIGENCE...</div>
		</div>
	{:else}
		<div class="matrix-header">
			<div class="header-metrics">
				<div class="metric-crystal">
					<div class="crystal-core">
						<span class="crystal-value">{(data.unique_sources || 0).toLocaleString()}</span>
						<span class="crystal-label">UNIQUE SOURCES</span>
					</div>
					<div class="crystal-glow"></div>
				</div>
				
				<div class="metric-crystal">
					<div class="crystal-core">
						<span class="crystal-value">{(data.total_mentions || 0).toLocaleString()}</span>
						<span class="crystal-label">TOTAL MENTIONS</span>
					</div>
					<div class="crystal-glow"></div>
				</div>
			</div>

			<div class="neural-search">
				<div class="search-container">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="SEARCH SOURCE INTELLIGENCE..."
						class="search-input"
					/>
					<div class="search-scanner"></div>
				</div>
			</div>
		</div>

		<div class="intelligence-grid">
			<div class="sources-matrix">
				<div class="matrix-title">
					<span class="title-icon">◈</span>
					SOURCE THREAT MATRIX
				</div>
				
				<div class="source-grid">
					{#each filteredSources.slice(0, 50) as [source, frequency]}
						{@const threat = getThreatLevel(frequency)}
						{@const percentage = ((frequency / data.total_mentions) * 100).toFixed(2)}
						<div 
							class="source-crystal"
							style="--threat-color: {threat.color}; --bar-width: {(frequency / maxFrequency) * 100}%"
							on:click={() => selectSource(source, frequency)}
						>
							<div class="crystal-header">
								<div class="threat-indicator" style="background: {threat.color}"></div>
								<span class="threat-level">{threat.level}</span>
							</div>
							
							<div class="source-name">{source}</div>
							
							<div class="frequency-display">
								<span class="frequency-count">{frequency.toLocaleString()}</span>
								<span class="frequency-percent">{percentage}%</span>
							</div>
							
							<div class="frequency-bar">
								<div class="bar-fill" style="background: {threat.color}"></div>
							</div>
							
							<div class="crystal-overlay"></div>
						</div>
					{/each}
				</div>
			</div>

			<div class="analysis-panel">
				<div class="panel-title">
					<span class="title-icon">◆</span>
					NEURAL ANALYSIS
				</div>
				
				{#if selectedSource}
					{@const threat = getThreatLevel(selectedSource.frequency)}
					<div class="selected-analysis">
						<div class="analysis-header">
							<div class="selected-name">{selectedSource.source}</div>
							<div class="selected-metrics">
								<div class="metric">
									<span class="metric-label">FREQUENCY</span>
									<span class="metric-value">{selectedSource.frequency.toLocaleString()}</span>
								</div>
								<div class="metric">
									<span class="metric-label">PERCENTAGE</span>
									<span class="metric-value">{((selectedSource.frequency / data.total_mentions) * 100).toFixed(2)}%</span>
								</div>
							</div>
						</div>
						
						<div class="threat-assessment">
							<div class="assessment-level" style="--level-color: {threat.color}">
								<div class="level-indicator"></div>
								<span class="level-text">THREAT LEVEL: {threat.level}</span>
							</div>
						</div>
					</div>
				{:else}
					<div class="analysis-prompt">
						<div class="prompt-icon">◯</div>
						<div class="prompt-text">SELECT A SOURCE FOR DETAILED ANALYSIS</div>
					</div>
				{/if}

				<div class="distribution-chart">
					<div class="chart-title">THREAT DISTRIBUTION</div>
					{@const threatStats = getThreatStats()}
					{@const maxCount = Math.max(...Object.values(threatStats))}
					<div class="threat-bars">
						{#each [['CRITICAL', '#FF0080'], ['HIGH', '#FF4500'], ['MEDIUM', '#FFE500'], ['LOW', '#00FF85']] as [level, color]}
							{@const count = threatStats[level] || 0}
							<div class="threat-bar">
								<span class="bar-label">{level}</span>
								<div class="bar-container">
									<div 
										class="bar" 
										style="width: {maxCount > 0 ? (count / maxCount) * 100 : 0}%; background: {color}"
									></div>
								</div>
								<span class="bar-count">{count}</span>
							</div>
						{/each}
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.intel-matrix {
		width: 100%;
		height: 100%;
		font-family: 'JetBrains Mono', monospace;
		color: #fff;
		background: transparent;
	}

	.neural-loader {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 400px;
		gap: 2rem;
	}

	.loader-core {
		position: relative;
		width: 80px;
		height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.core-ring {
		position: absolute;
		width: 80px;
		height: 80px;
		border: 2px solid #00D4FF;
		border-radius: 50%;
		animation: coreRotate 2s linear infinite;
	}

	.core-inner {
		font-size: 2rem;
		color: #00D4FF;
		animation: corePulse 2s ease-in-out infinite;
	}

	.loader-text {
		color: #00D4FF;
		font-size: 0.9rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		animation: textGlow 2s ease-in-out infinite;
	}

	.matrix-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		gap: 2rem;
	}

	.header-metrics {
		display: flex;
		gap: 2rem;
	}

	.metric-crystal {
		position: relative;
		width: 180px;
		height: 100px;
	}

	.crystal-core {
		background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
		border: 1px solid rgba(0, 212, 255, 0.3);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		position: relative;
		backdrop-filter: blur(20px);
		transition: all 0.3s ease;
	}

	.crystal-core:hover {
		border-color: #00D4FF;
		box-shadow: 0 0 30px rgba(0, 212, 255, 0.2);
		transform: translateY(-2px);
	}

	.crystal-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #00D4FF;
		text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
	}

	.crystal-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.25rem;
		letter-spacing: 0.05em;
	}

	.crystal-glow {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 200px;
		height: 120px;
		background: radial-gradient(ellipse, rgba(0, 212, 255, 0.1), transparent);
		border-radius: 50%;
		animation: crystalPulse 3s ease-in-out infinite;
		pointer-events: none;
	}

	.neural-search {
		flex: 1;
		max-width: 400px;
	}

	.search-container {
		position: relative;
	}

	.search-input {
		width: 100%;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6) 0%, rgba(0, 20, 40, 0.6) 100%);
		border: 1px solid rgba(0, 212, 255, 0.3);
		border-radius: 8px;
		padding: 0.75rem 1rem;
		color: #fff;
		font-family: inherit;
		font-size: 0.9rem;
		backdrop-filter: blur(20px);
		transition: all 0.3s ease;
	}

	.search-input::placeholder {
		color: rgba(255, 255, 255, 0.4);
		letter-spacing: 0.05em;
	}

	.search-input:focus {
		outline: none;
		border-color: #00D4FF;
		box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
	}

	.search-scanner {
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.2), transparent);
		animation: scannerSweep 3s linear infinite;
		border-radius: 8px;
		pointer-events: none;
	}

	.intelligence-grid {
		display: grid;
		grid-template-columns: 1fr 400px;
		gap: 2rem;
		height: calc(100vh - 300px);
	}

	.sources-matrix {
		background: linear-gradient(135deg, rgba(0, 20, 40, 0.3) 0%, rgba(0, 10, 20, 0.3) 100%);
		border: 1px solid rgba(0, 212, 255, 0.2);
		border-radius: 16px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
		overflow: hidden;
	}

	.matrix-title {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1.5rem;
		font-size: 1rem;
		font-weight: 700;
		color: #00D4FF;
		letter-spacing: 0.05em;
	}

	.title-icon {
		font-size: 1.2rem;
		animation: iconFloat 3s ease-in-out infinite;
	}

	.source-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1rem;
		height: calc(100% - 60px);
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.source-crystal {
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1rem;
		cursor: pointer;
		position: relative;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		overflow: hidden;
	}

	.source-crystal::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
		transition: left 0.6s ease;
	}

	.source-crystal:hover::before {
		left: 100%;
	}

	.source-crystal:hover {
		border-color: var(--threat-color);
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
		transform: translateY(-3px);
	}

	.crystal-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.75rem;
	}

	.threat-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: indicatorPulse 2s ease-in-out infinite;
	}

	.threat-level {
		font-size: 0.7rem;
		font-weight: 600;
		color: var(--threat-color);
		letter-spacing: 0.05em;
	}

	.source-name {
		font-size: 0.9rem;
		font-weight: 600;
		color: #fff;
		margin-bottom: 0.75rem;
		word-break: break-word;
	}

	.frequency-display {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.75rem;
	}

	.frequency-count {
		font-size: 1.1rem;
		font-weight: 700;
		color: var(--threat-color);
	}

	.frequency-percent {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 500;
	}

	.frequency-bar {
		height: 4px;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 2px;
		overflow: hidden;
		position: relative;
	}

	.bar-fill {
		height: 100%;
		width: var(--bar-width);
		border-radius: 2px;
		transition: width 1s ease-out;
		position: relative;
	}

	.bar-fill::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
		animation: barShine 2s infinite;
	}

	.crystal-overlay {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: radial-gradient(circle at center, var(--threat-color), transparent);
		opacity: 0;
		transition: opacity 0.3s ease;
		border-radius: 12px;
		pointer-events: none;
	}

	.source-crystal:hover .crystal-overlay {
		opacity: 0.03;
	}

	.analysis-panel {
		background: linear-gradient(135deg, rgba(0, 20, 40, 0.4) 0%, rgba(0, 10, 20, 0.4) 100%);
		border: 1px solid rgba(139, 92, 246, 0.2);
		border-radius: 16px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
		display: flex;
		flex-direction: column;
	}

	.panel-title {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1.5rem;
		font-size: 1rem;
		font-weight: 700;
		color: #8B5CF6;
		letter-spacing: 0.05em;
	}

	.selected-analysis {
		flex: 1;
	}

	.analysis-header {
		margin-bottom: 1.5rem;
	}

	.selected-name {
		font-size: 1.1rem;
		font-weight: 700;
		color: #fff;
		margin-bottom: 1rem;
		word-break: break-word;
	}

	.selected-metrics {
		display: flex;
		gap: 1.5rem;
	}

	.metric {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.metric-value {
		font-size: 1rem;
		font-weight: 700;
		color: #8B5CF6;
	}

	.threat-assessment {
		margin-bottom: 2rem;
	}

	.assessment-level {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem;
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid var(--level-color);
		border-radius: 8px;
		backdrop-filter: blur(10px);
	}

	.level-indicator {
		width: 12px;
		height: 12px;
		background: var(--level-color);
		border-radius: 50%;
		animation: levelPulse 2s ease-in-out infinite;
	}

	.level-text {
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--level-color);
		letter-spacing: 0.05em;
	}

	.analysis-prompt {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		flex: 1;
		gap: 1rem;
		color: rgba(255, 255, 255, 0.4);
	}

	.prompt-icon {
		font-size: 3rem;
		animation: promptPulse 3s ease-in-out infinite;
	}

	.prompt-text {
		font-size: 0.9rem;
		font-weight: 500;
		letter-spacing: 0.05em;
		text-align: center;
	}

	.distribution-chart {
		margin-top: 2rem;
	}

	.chart-title {
		font-size: 0.9rem;
		font-weight: 700;
		color: #8B5CF6;
		margin-bottom: 1rem;
		letter-spacing: 0.05em;
	}

	.threat-bars {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.threat-bar {
		display: grid;
		grid-template-columns: 80px 1fr 40px;
		align-items: center;
		gap: 0.75rem;
	}

	.bar-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.bar-container {
		height: 8px;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 4px;
		overflow: hidden;
	}

	.bar {
		height: 100%;
		border-radius: 4px;
		transition: width 1s ease-out;
		position: relative;
	}

	.bar::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
		animation: barShine 3s infinite;
	}

	.bar-count {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.7);
		font-weight: 600;
		text-align: right;
	}

	@keyframes coreRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes corePulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.1); }
	}

	@keyframes textGlow {
		0%, 100% { text-shadow: 0 0 10px rgba(0, 212, 255, 0.5); }
		50% { text-shadow: 0 0 20px rgba(0, 212, 255, 0.8); }
	}

	@keyframes crystalPulse {
		0%, 100% { opacity: 0.1; transform: translate(-50%, -50%) scale(1); }
		50% { opacity: 0.2; transform: translate(-50%, -50%) scale(1.05); }
	}

	@keyframes scannerSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-3px); }
	}

	@keyframes indicatorPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.6; transform: scale(1.2); }
	}

	@keyframes barShine {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes levelPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.1); }
	}

	@keyframes promptPulse {
		0%, 100% { opacity: 0.4; transform: scale(1); }
		50% { opacity: 0.6; transform: scale(1.05); }
	}
</style>