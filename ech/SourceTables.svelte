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
		if (!data.total_mentions) return { level: 'LOW', color: '#00ffff', priority: 1 };
		let percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRITICAL', color: '#ff0066', priority: 4 };
		if (percentage >= 10) return { level: 'HIGH', color: '#ff9900', priority: 3 };
		if (percentage >= 5) return { level: 'MEDIUM', color: '#ffcc00', priority: 2 };
		return { level: 'LOW', color: '#00ffff', priority: 1 };
	}

	function getPercentage(frequency) {
		if (!data.total_mentions) return '0.00';
		return ((frequency / data.total_mentions) * 100).toFixed(2);
	}

	function selectSource(source, frequency) {
		selectedSource = { source, frequency };
	}

	function getProgress(frequency) {
		return Math.round((frequency / maxFrequency) * 100);
	}

	function getCoverageStatus(percentage) {
		if (percentage >= 15) return 'critical-coverage';
		if (percentage >= 10) return 'high-coverage';
		if (percentage >= 5) return 'medium-coverage';
		return 'low-coverage';
	}
</script>

<div class="source-analysis">
	{#if loading}
		<div class="loading-state">
			<div class="loader">
				<div class="loader-ring"></div>
				<div class="loader-dot"></div>
			</div>
			<p class="loading-text">Loading source intelligence data...</p>
		</div>
	{:else}
		<div class="analysis-header">
			<div class="metrics-overview">
				<div class="metric-card">
					<div class="metric-value">{(data.unique_sources || 0).toLocaleString()}</div>
					<div class="metric-label">Unique Sources</div>
					<div class="metric-progress">
						<div class="progress-bar" style="width: 85%"></div>
					</div>
				</div>
				
				<div class="metric-card">
					<div class="metric-value">{(data.total_mentions || 0).toLocaleString()}</div>
					<div class="metric-label">Total Log Mentions</div>
					<div class="metric-progress">
						<div class="progress-bar" style="width: 92%"></div>
					</div>
				</div>

				<div class="metric-card">
					<div class="metric-value">{filteredSources.length}</div>
					<div class="metric-label">Filtered Results</div>
					<div class="metric-progress">
						<div class="progress-bar" style="width: {Math.min(100, (filteredSources.length / (data.unique_sources || 1)) * 100)}%"></div>
					</div>
				</div>
			</div>

			<div class="search-section">
				<div class="search-container">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search source tables..."
						class="search-input"
					/>
					<div class="search-icon">🔍</div>
				</div>
			</div>
		</div>

		<div class="analysis-content">
			<div class="sources-panel">
				<div class="panel-header">
					<h3>Source Table Analysis</h3>
					<div class="panel-info">
						Showing {filteredSources.length} of {data.unique_sources || 0} sources
					</div>
				</div>
				
				<div class="sources-grid">
					{#each filteredSources.slice(0, 20) as [source, frequency]}
						{@html (() => {
							let threat = getThreatLevel(frequency);
							let progress = getProgress(frequency);
							let percentage = getPercentage(frequency);
							return '';
						})()}
						<div 
							class="source-item {getCoverageStatus(parseFloat(getPercentage(frequency)))}"
							on:click={() => selectSource(source, frequency)}
						>
							<div class="source-header">
								<div class="source-name">{source}</div>
								<div class="threat-badge {getThreatLevel(frequency).level.toLowerCase()}">
									{getThreatLevel(frequency).level}
								</div>
							</div>
							
							<div class="source-metrics">
								<div class="metric">
									<span class="metric-label">Frequency:</span>
									<span class="metric-value">{frequency.toLocaleString()}</span>
								</div>
								<div class="metric">
									<span class="metric-label">Coverage:</span>
									<span class="metric-value">{getPercentage(frequency)}%</span>
								</div>
							</div>

							<div class="coverage-bar">
								<div 
									class="coverage-fill" 
									style="width: {getProgress(frequency)}%; background: {getThreatLevel(frequency).color};"
								></div>
							</div>

							<div class="visibility-status">
								<div class="status-indicator {getThreatLevel(frequency).level.toLowerCase()}"></div>
								<span class="status-text">Log Visibility: {getThreatLevel(frequency).level}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<div class="details-panel">
				<div class="panel-header">
					<h3>Source Details</h3>
				</div>
				
				{#if selectedSource}
					<div class="source-details">
						<div class="detail-section">
							<h4>Selected Source</h4>
							<div class="source-title">{selectedSource.source}</div>
						</div>
						
						<div class="detail-section">
							<h4>Coverage Metrics</h4>
							<div class="metrics-grid">
								<div class="detail-metric">
									<span class="label">Log Frequency</span>
									<span class="value">{selectedSource.frequency.toLocaleString()}</span>
								</div>
								<div class="detail-metric">
									<span class="label">Coverage %</span>
									<span class="value">{getPercentage(selectedSource.frequency)}%</span>
								</div>
								<div class="detail-metric">
									<span class="label">Priority Level</span>
									<span class="value {getThreatLevel(selectedSource.frequency).level.toLowerCase()}">
										{getThreatLevel(selectedSource.frequency).level}
									</span>
								</div>
							</div>
						</div>

						<div class="detail-section">
							<h4>Visibility Assessment</h4>
							<div class="assessment-content">
								{#if getThreatLevel(selectedSource.frequency).level === 'CRITICAL'}
									<p class="assessment-text critical">
										This source represents a critical component of log visibility infrastructure. 
										High frequency indicates significant coverage across monitored systems.
									</p>
								{:else if getThreatLevel(selectedSource.frequency).level === 'HIGH'}
									<p class="assessment-text high">
										Important source with substantial log volume. Regular monitoring recommended 
										to maintain visibility standards.
									</p>
								{:else if getThreatLevel(selectedSource.frequency).level === 'MEDIUM'}
									<p class="assessment-text medium">
										Moderate coverage source. Consider expansion opportunities to increase 
										visibility across infrastructure.
									</p>
								{:else}
									<p class="assessment-text low">
										Low coverage source. May represent specialized systems or require 
										configuration review for optimal visibility.
									</p>
								{/if}
							</div>
						</div>
					</div>
				{:else}
					<div class="no-selection">
						<div class="placeholder-icon">📊</div>
						<p>Select a source from the list to view detailed analysis</p>
						<div class="help-text">
							Click on any source table entry to see coverage metrics, 
							visibility assessment, and recommendations.
						</div>
					</div>
				{/if}

				<div class="coverage-summary">
					<h4>Coverage Distribution</h4>
					<div class="distribution-chart">
						{#each [['CRITICAL', '#ff0066'], ['HIGH', '#ff9900'], ['MEDIUM', '#ffcc00'], ['LOW', '#00ffff']] as [level, color]}
							{@html (() => {
								let count = filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === level).length;
								let maxCount = Math.max(
									filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'CRITICAL').length,
									filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'HIGH').length,
									filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'MEDIUM').length,
									filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'LOW').length
								);
								return '';
							})()}
							<div class="distribution-item">
								<div class="distribution-label">{level}</div>
								<div class="distribution-bar">
									<div 
										class="distribution-fill" 
										style="width: {(() => {
											let count = filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === level).length;
											let maxCount = Math.max(
												filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'CRITICAL').length,
												filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'HIGH').length,
												filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'MEDIUM').length,
												filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === 'LOW').length
											);
											return maxCount > 0 ? (count / maxCount) * 100 : 0;
										})()}%; background: {color};"
									></div>
								</div>
								<div class="distribution-count">
									{(() => {
										return filteredSources.filter(([_, freq]) => getThreatLevel(freq).level === level).length;
									})()}
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
	.source-analysis {
		width: 100%;
		height: 100%;
		background: #0a0a0a;
		color: #ffffff;
		font-family: 'JetBrains Mono', monospace;
	}

	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 400px;
		gap: 1rem;
	}

	.loader {
		position: relative;
		width: 60px;
		height: 60px;
	}

	.loader-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 3px solid rgba(0, 255, 255, 0.2);
		border-top: 3px solid #00ffff;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.loader-dot {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 8px;
		height: 8px;
		background: #00ffff;
		border-radius: 50%;
		animation: pulse 1.5s ease-in-out infinite;
	}

	.loading-text {
		color: rgba(255, 255, 255, 0.7);
		font-size: 0.9rem;
	}

	.analysis-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 2rem;
		gap: 2rem;
	}

	.metrics-overview {
		display: flex;
		gap: 1.5rem;
	}

	.metric-card {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6) 0%, rgba(0, 255, 255, 0.05) 100%);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 8px;
		padding: 1.5rem;
		min-width: 160px;
		text-align: center;
	}

	.metric-value {
		font-size: 1.8rem;
		font-weight: 700;
		color: #00ffff;
		margin-bottom: 0.5rem;
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}

	.metric-label {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		margin-bottom: 0.8rem;
	}

	.metric-progress {
		height: 4px;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 2px;
		overflow: hidden;
	}

	.progress-bar {
		height: 100%;
		background: linear-gradient(90deg, #00ffff, #0099cc);
		transition: width 1s ease-out;
	}

	.search-section {
		flex-shrink: 0;
	}

	.search-container {
		position: relative;
		width: 300px;
	}

	.search-input {
		width: 100%;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6) 0%, rgba(0, 255, 255, 0.05) 100%);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 6px;
		padding: 0.8rem 1rem;
		padding-right: 3rem;
		color: #ffffff;
		font-family: inherit;
		font-size: 0.9rem;
		transition: all 0.3s ease;
	}

	.search-input::placeholder {
		color: rgba(255, 255, 255, 0.4);
	}

	.search-input:focus {
		outline: none;
		border-color: #00ffff;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
	}

	.search-icon {
		position: absolute;
		right: 1rem;
		top: 50%;
		transform: translateY(-50%);
		color: rgba(255, 255, 255, 0.5);
	}

	.analysis-content {
		display: grid;
		grid-template-columns: 1fr 400px;
		gap: 2rem;
		height: calc(100vh - 250px);
	}

	.sources-panel, .details-panel {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6) 0%, rgba(26, 26, 46, 0.3) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		overflow: hidden;
	}

	.panel-header {
		background: rgba(0, 0, 0, 0.4);
		padding: 1rem 1.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.panel-header h3 {
		margin: 0;
		color: #00ffff;
		font-size: 1rem;
		font-weight: 600;
	}

	.panel-info {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}

	.sources-grid {
		padding: 1rem;
		overflow-y: auto;
		height: calc(100% - 80px);
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 1rem;
	}

	.source-item {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(255, 255, 255, 0.02) 100%);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.source-item:hover {
		border-color: #00ffff;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
		transform: translateY(-2px);
	}

	.source-item.critical-coverage {
		border-left: 4px solid #ff0066;
	}

	.source-item.high-coverage {
		border-left: 4px solid #ff9900;
	}

	.source-item.medium-coverage {
		border-left: 4px solid #ffcc00;
	}

	.source-item.low-coverage {
		border-left: 4px solid #00ffff;
	}

	.source-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 0.8rem;
	}

	.source-name {
		font-weight: 600;
		color: #ffffff;
		font-size: 0.9rem;
		line-height: 1.2;
		flex: 1;
		margin-right: 0.5rem;
	}

	.threat-badge {
		padding: 0.2rem 0.6rem;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.threat-badge.critical {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.threat-badge.high {
		background: rgba(255, 153, 0, 0.2);
		color: #ff9900;
		border: 1px solid #ff9900;
	}

	.threat-badge.medium {
		background: rgba(255, 204, 0, 0.2);
		color: #ffcc00;
		border: 1px solid #ffcc00;
	}

	.threat-badge.low {
		background: rgba(0, 255, 255, 0.2);
		color: #00ffff;
		border: 1px solid #00ffff;
	}

	.source-metrics {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.5rem;
		margin-bottom: 0.8rem;
	}

	.metric {
		font-size: 0.7rem;
	}

	.metric-label {
		color: rgba(255, 255, 255, 0.5);
		margin-right: 0.3rem;
	}

	.metric-value {
		color: #ffffff;
		font-weight: 600;
	}

	.coverage-bar {
		height: 4px;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 2px;
		overflow: hidden;
		margin-bottom: 0.8rem;
	}

	.coverage-fill {
		height: 100%;
		border-radius: 2px;
		transition: width 1s ease-out;
	}

	.visibility-status {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		animation: blink 2s ease-in-out infinite;
	}

	.status-indicator.critical {
		background: #ff0066;
	}

	.status-indicator.high {
		background: #ff9900;
	}

	.status-indicator.medium {
		background: #ffcc00;
	}

	.status-indicator.low {
		background: #00ffff;
	}

	.status-text {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
	}

	.details-panel {
		padding: 1.5rem;
		overflow-y: auto;
	}

	.source-details {
		padding-top: 1rem;
	}

	.detail-section {
		margin-bottom: 2rem;
	}

	.detail-section h4 {
		color: #00ffff;
		font-size: 0.9rem;
		margin-bottom: 1rem;
		font-weight: 600;
	}

	.source-title {
		font-size: 1.1rem;
		font-weight: 600;
		color: #ffffff;
		line-height: 1.3;
	}

	.metrics-grid {
		display: grid;
		gap: 0.8rem;
	}

	.detail-metric {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 0;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}

	.detail-metric .label {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.detail-metric .value {
		font-weight: 600;
		color: #ffffff;
	}

	.detail-metric .value.critical {
		color: #ff0066;
	}

	.detail-metric .value.high {
		color: #ff9900;
	}

	.detail-metric .value.medium {
		color: #ffcc00;
	}

	.detail-metric .value.low {
		color: #00ffff;
	}

	.assessment-content {
		background: rgba(0, 0, 0, 0.3);
		border-radius: 6px;
		padding: 1rem;
	}

	.assessment-text {
		font-size: 0.8rem;
		line-height: 1.4;
		margin: 0;
	}

	.assessment-text.critical {
		color: #ff9999;
		border-left: 3px solid #ff0066;
		padding-left: 0.8rem;
	}

	.assessment-text.high {
		color: #ffcc99;
		border-left: 3px solid #ff9900;
		padding-left: 0.8rem;
	}

	.assessment-text.medium {
		color: #ffff99;
		border-left: 3px solid #ffcc00;
		padding-left: 0.8rem;
	}

	.assessment-text.low {
		color: #99ffff;
		border-left: 3px solid #00ffff;
		padding-left: 0.8rem;
	}

	.no-selection {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 200px;
		text-align: center;
		color: rgba(255, 255, 255, 0.5);
		gap: 1rem;
	}

	.placeholder-icon {
		font-size: 2rem;
		opacity: 0.5;
	}

	.help-text {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.4);
		line-height: 1.4;
		max-width: 250px;
	}

	.coverage-summary {
		margin-top: 2rem;
		padding-top: 1.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}

	.coverage-summary h4 {
		color: #00ffff;
		font-size: 0.9rem;
		margin-bottom: 1rem;
		font-weight: 600;
	}

	.distribution-chart {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.distribution-item {
		display: grid;
		grid-template-columns: 80px 1fr 30px;
		align-items: center;
		gap: 0.8rem;
	}

	.distribution-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
	}

	.distribution-bar {
		height: 6px;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 3px;
		overflow: hidden;
	}

	.distribution-fill {
		height: 100%;
		border-radius: 3px;
		transition: width 1s ease-out;
	}

	.distribution-count {
		font-size: 0.7rem;
		color: #ffffff;
		font-weight: 600;
		text-align: center;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
		50% { opacity: 0.5; transform: translate(-50%, -50%) scale(0.8); }
	}

	@keyframes blink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	@media (max-width: 1200px) {
		.analysis-content {
			grid-template-columns: 1fr;
			gap: 1.5rem;
		}

		.details-panel {
			order: -1;
		}
	}

	@media (max-width: 768px) {
		.analysis-header {
			flex-direction: column;
			gap: 1rem;
		}

		.metrics-overview {
			flex-wrap: wrap;
			justify-content: center;
		}

		.search-container {
			width: 100%;
		}

		.sources-grid {
			grid-template-columns: 1fr;
		}
	}
</style>