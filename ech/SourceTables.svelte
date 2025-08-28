<!-- SourceTables.svelte - Premium Frequency Analysis -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let hoveredIndex = -1;

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
	
	$: maxFreq = filteredSources.length > 0 ? Math.max(...filteredSources.map(([,f]) => f)) : 1;

	function getPercentage(frequency) {
		if (!data.total_mentions) return 0;
		return ((frequency / data.total_mentions) * 100).toFixed(2);
	}

	function getThreatLevel(frequency) {
		const percentage = (frequency / maxFreq) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#FF1744', glow: 'rgba(255, 23, 68, 0.4)' };
		if (percentage >= 50) return { level: 'HIGH', color: '#FFA726', glow: 'rgba(255, 167, 38, 0.4)' };
		if (percentage >= 25) return { level: 'MEDIUM', color: '#FFD600', glow: 'rgba(255, 214, 0, 0.4)' };
		return { level: 'LOW', color: '#00E5FF', glow: 'rgba(0, 229, 255, 0.4)' };
	}

	async function drillDownSource(source, frequency) {
		selectedSource = { source, frequency };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			hostDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Host search error:', err);
			hostDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedSource = null;
		hostDetails = [];
	}
</script>

<div class="dashboard-container">
	<!-- Premium Background Effects -->
	<div class="background-effects">
		<div class="gradient-orb orb-1"></div>
		<div class="gradient-orb orb-2"></div>
		<div class="gradient-orb orb-3"></div>
		<div class="grid-overlay"></div>
	</div>

	<div class="main-content">
		<!-- Left Panel: Premium Table -->
		<div class="table-panel glass-panel">
			<div class="panel-header">
				<div class="header-content">
					<div class="title-group">
						<h3 class="panel-title">
							<span class="title-icon">◈</span>
							SOURCE TABLES
						</h3>
						<div class="subtitle">FREQUENCY ANALYSIS MATRIX</div>
					</div>
					<div class="header-stats">
						<div class="stat-pill">
							<span class="stat-label">SOURCES</span>
							<span class="stat-value">{filteredSources.length}</span>
						</div>
						<div class="stat-pill">
							<span class="stat-label">MENTIONS</span>
							<span class="stat-value">{(data.total_mentions || 0).toLocaleString()}</span>
						</div>
					</div>
				</div>
				<div class="search-wrapper">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search sources..."
						class="search-input premium-input"
					/>
					<div class="search-icon">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<circle cx="11" cy="11" r="8"></circle>
							<path d="m21 21-4.35-4.35"></path>
						</svg>
					</div>
				</div>
			</div>
			
			{#if loading && !selectedSource}
				<div class="loading-state">
					<div class="premium-loader">
						<div class="loader-ring"></div>
						<div class="loader-ring"></div>
						<div class="loader-ring"></div>
						<div class="loader-core">
							<span>◈</span>
						</div>
					</div>
					<p class="loading-text">ANALYZING SOURCE MATRICES</p>
				</div>
			{:else if selectedSource}
				<div class="drill-view">
					<div class="drill-header glass-header">
						<div class="drill-title">
							<span class="drill-icon">▸</span>
							<h4>{selectedSource.source.toUpperCase()}</h4>
							<span class="drill-badge">{selectedSource.frequency.toLocaleString()} mentions</span>
						</div>
						<button class="close-btn premium-btn" on:click={closeDetails}>
							<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<line x1="18" y1="6" x2="6" y2="18"></line>
								<line x1="6" y1="6" x2="18" y2="18"></line>
							</svg>
						</button>
					</div>
					<div class="drill-table-container">
						<table class="data-table premium-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>INFRASTRUCTURE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each hostDetails as host, index}
									<tr class="table-row {hoveredIndex === index ? 'hovered' : ''}"
										on:mouseenter={() => hoveredIndex = index}
										on:mouseleave={() => hoveredIndex = -1}>
										<td class="host-cell">{host.host}</td>
										<td>{host.region || 'UNKNOWN'}</td>
										<td>{host.country || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>
											<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'badge-success' : 'badge-danger'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'ACTIVE' : 'INACTIVE'}
											</span>
										</td>
										<td>
											<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'badge-success' : 'badge-warning'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? 'DEPLOYED' : 'MISSING'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="table-scroll-container">
					<table class="data-table premium-table">
						<thead>
							<tr>
								<th>SOURCE TABLE</th>
								<th>FREQUENCY</th>
								<th>COVERAGE</th>
								<th>THREAT LEVEL</th>
								<th>VISIBILITY MATRIX</th>
							</tr>
						</thead>
						<tbody>
							{#each filteredSources as [source, frequency], index}
								{@const threat = getThreatLevel(frequency)}
								<tr class="table-row {hoveredIndex === index ? 'hovered' : ''}"
									on:click={() => drillDownSource(source, frequency)}
									on:mouseenter={() => hoveredIndex = index}
									on:mouseleave={() => hoveredIndex = -1}>
									<td class="source-cell">
										<div class="source-indicator" style="background: {threat.color}; box-shadow: 0 0 12px {threat.glow}"></div>
										<span class="source-name">{source.toUpperCase()}</span>
									</td>
									<td class="frequency-cell">
										<div class="frequency-content">
											<span class="frequency-value">{frequency.toLocaleString()}</span>
											<div class="frequency-bar-bg">
												<div class="frequency-bar" style="width: {(frequency/maxFreq)*100}%; background: linear-gradient(90deg, {threat.color}, {threat.glow})"></div>
											</div>
										</div>
									</td>
									<td class="coverage-cell">
										<div class="coverage-content">
											<span class="coverage-value">{getPercentage(frequency)}%</span>
											<div class="coverage-ring">
												<svg width="24" height="24" viewBox="0 0 36 36">
													<circle cx="18" cy="18" r="15" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="2"/>
													<circle cx="18" cy="18" r="15" fill="none" stroke={threat.color} stroke-width="2"
														stroke-dasharray="{getPercentage(frequency)} 100"
														transform="rotate(-90 18 18)"/>
												</svg>
											</div>
										</div>
									</td>
									<td class="threat-cell">
										<span class="threat-badge" style="background: linear-gradient(135deg, {threat.color}22, {threat.color}44); border-color: {threat.color}">
											<span class="threat-icon">⚡</span>
											{threat.level}
										</span>
									</td>
									<td class="matrix-cell">
										<div class="matrix-visualization">
											{#each Array(10) as _, i}
												<div class="matrix-bar" 
													style="height: {(frequency/maxFreq) * (10 - i) * 10}%; 
														  background: {threat.color};
														  opacity: {0.3 + (i * 0.07)};
														  animation-delay: {i * 0.05}s">
												</div>
											{/each}
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>

		<!-- Right Panel: Premium Visualizations -->
		<div class="viz-panel">
			<!-- Top Metrics Cards -->
			<div class="metrics-row">
				<div class="metric-card glass-card">
					<div class="metric-icon-wrapper">
						<div class="metric-icon">◈</div>
					</div>
					<div class="metric-content">
						<div class="metric-value">{filteredSources.length}</div>
						<div class="metric-label">UNIQUE SOURCES</div>
					</div>
					<div class="metric-sparkline">
						<svg viewBox="0 0 100 30">
							{#each Array(20) as _, i}
								<rect x="{i * 5}" y="{30 - Math.random() * 25}" 
									  width="3" height="{Math.random() * 25}"
									  fill="url(#sparkGradient)" opacity="{0.4 + Math.random() * 0.6}"/>
							{/each}
							<defs>
								<linearGradient id="sparkGradient" x1="0%" y1="0%" x2="0%" y2="100%">
									<stop offset="0%" style="stop-color:#00E5FF;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#00E5FF;stop-opacity:0.3" />
								</linearGradient>
							</defs>
						</svg>
					</div>
				</div>
				
				<div class="metric-card glass-card">
					<div class="metric-icon-wrapper">
						<div class="metric-icon">◉</div>
					</div>
					<div class="metric-content">
						<div class="metric-value">{(data.total_mentions || 0).toLocaleString()}</div>
						<div class="metric-label">TOTAL MENTIONS</div>
					</div>
					<div class="metric-sparkline">
						<svg viewBox="0 0 100 30">
							<polyline points="0,25 10,20 20,22 30,15 40,18 50,10 60,15 70,12 80,20 90,18 100,25" 
									  fill="none" stroke="url(#lineGradient)" stroke-width="2"/>
							<defs>
								<linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
									<stop offset="0%" style="stop-color:#00E5FF;stop-opacity:0.3" />
									<stop offset="50%" style="stop-color:#00E5FF;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#00E5FF;stop-opacity:0.3" />
								</linearGradient>
							</defs>
						</svg>
					</div>
				</div>
			</div>

			<!-- Frequency Spectrum -->
			<div class="viz-card glass-card">
				<div class="card-header">
					<h4>FREQUENCY SPECTRUM</h4>
					<div class="card-status-indicator"></div>
				</div>
				<div class="spectrum-chart">
					{#each filteredSources.slice(0, 8) as [source, frequency]}
						{@const threat = getThreatLevel(frequency)}
						{@const percentage = (frequency/maxFreq)*100}
						<div class="spectrum-item">
							<div class="spectrum-label">{source.substring(0, 12).toUpperCase()}</div>
							<div class="spectrum-visual">
								<div class="spectrum-track"></div>
								<div class="spectrum-fill" 
									 style="width: {percentage}%; 
											background: linear-gradient(90deg, {threat.color}, {threat.glow})">
									<div class="spectrum-glow"></div>
								</div>
								<span class="spectrum-value">{frequency.toLocaleString()}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Threat Matrix Grid -->
			<div class="viz-card glass-card">
				<div class="card-header">
					<h4>THREAT MATRIX</h4>
					<div class="card-status-indicator active"></div>
				</div>
				<div class="threat-matrix">
					<svg viewBox="0 0 200 150" class="matrix-svg">
						<defs>
							<radialGradient id="nodeGradient">
								<stop offset="0%" style="stop-color:#00E5FF;stop-opacity:0.8" />
								<stop offset="100%" style="stop-color:#00E5FF;stop-opacity:0" />
							</radialGradient>
							<filter id="glowFilter">
								<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
								<feMerge>
									<feMergeNode in="coloredBlur"/>
									<feMergeNode in="SourceGraphic"/>
								</feMerge>
							</filter>
						</defs>
						
						<!-- Background grid -->
						{#each Array(10) as _, i}
							<line x1="{i * 20}" y1="0" x2="{i * 20}" y2="150" 
								  stroke="rgba(0,229,255,0.05)" stroke-width="0.5"/>
							<line x1="0" y1="{i * 15}" x2="200" y2="{i * 15}" 
								  stroke="rgba(0,229,255,0.05)" stroke-width="0.5"/>
						{/each}
						
						<!-- Data nodes -->
						{#each filteredSources.slice(0, 8) as [source, frequency], i}
							{@const x = (i % 4) * 50 + 25}
							{@const y = Math.floor(i / 4) * 50 + 25}
							{@const size = (frequency / maxFreq) * 20 + 5}
							{@const threat = getThreatLevel(frequency)}
							
							<circle cx="{x}" cy="{y}" r="{size}" 
									fill="url(#nodeGradient)" opacity="0.3" filter="url(#glowFilter)"/>
							<circle cx="{x}" cy="{y}" r="{size/2}" 
									fill={threat.color} opacity="0.8"/>
							<circle cx="{x}" cy="{y}" r="2" 
									fill="#ffffff"/>
							
							<!-- Pulse animation -->
							<circle cx="{x}" cy="{y}" r="{size/2}" 
									fill="none" stroke={threat.color} stroke-width="1" opacity="0">
								<animate attributeName="r" values="{size/2};{size};{size/2}" dur="3s" repeatCount="indefinite"/>
								<animate attributeName="opacity" values="0.8;0;0.8" dur="3s" repeatCount="indefinite"/>
							</circle>
						{/each}
						
						<!-- Connection lines -->
						{#each filteredSources.slice(0, 7) as [source, frequency], i}
							{#if i < filteredSources.slice(0, 7).length - 1}
								{@const x1 = (i % 4) * 50 + 25}
								{@const y1 = Math.floor(i / 4) * 50 + 25}
								{@const x2 = ((i + 1) % 4) * 50 + 25}
								{@const y2 = Math.floor((i + 1) / 4) * 50 + 25}
								<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
									  stroke="rgba(0,229,255,0.2)" stroke-width="0.5" stroke-dasharray="2,3"/>
							{/if}
						{/each}
					</svg>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.dashboard-container {
		height: calc(100vh - 180px);
		display: flex;
		position: relative;
		background: #000000;
		color: #ffffff;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
		overflow: hidden;
		padding: 1.5rem;
	}

	.background-effects {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		z-index: 0;
	}

	.gradient-orb {
		position: absolute;
		border-radius: 50%;
		filter: blur(80px);
		opacity: 0.3;
		animation: orbFloat 20s infinite ease-in-out;
	}

	.orb-1 {
		width: 600px;
		height: 600px;
		background: radial-gradient(circle, #00E5FF 0%, transparent 70%);
		top: -200px;
		left: -200px;
		animation-duration: 25s;
	}

	.orb-2 {
		width: 400px;
		height: 400px;
		background: radial-gradient(circle, #7C4DFF 0%, transparent 70%);
		bottom: -100px;
		right: -100px;
		animation-duration: 20s;
		animation-delay: -5s;
	}

	.orb-3 {
		width: 300px;
		height: 300px;
		background: radial-gradient(circle, #FF1744 0%, transparent 70%);
		top: 50%;
		left: 50%;
		animation-duration: 30s;
		animation-delay: -10s;
	}

	@keyframes orbFloat {
		0%, 100% { transform: translate(0, 0) scale(1); }
		33% { transform: translate(50px, -50px) scale(1.1); }
		66% { transform: translate(-50px, 50px) scale(0.9); }
	}

	.grid-overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background-image: 
			linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px),
			linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px);
		background-size: 50px 50px;
		animation: gridMove 10s linear infinite;
	}

	@keyframes gridMove {
		0% { transform: translate(0, 0); }
		100% { transform: translate(50px, 50px); }
	}

	.main-content {
		flex: 1;
		display: flex;
		gap: 1.5rem;
		overflow: hidden;
		position: relative;
		z-index: 1;
	}

	.glass-panel, .glass-card, .glass-header {
		background: rgba(255, 255, 255, 0.03);
		backdrop-filter: blur(20px);
		-webkit-backdrop-filter: blur(20px);
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.table-panel {
		flex: 1.5;
		border-radius: 24px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: 
			0 20px 60px rgba(0, 0, 0, 0.5),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
	}

	.panel-header {
		padding: 2rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.08);
		background: rgba(0, 0, 0, 0.3);
		flex-shrink: 0;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1.5rem;
	}

	.title-group {
		flex: 1;
	}

	.panel-title {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 600;
		background: linear-gradient(135deg, #ffffff 0%, #00E5FF 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.title-icon {
		font-size: 1.8rem;
		color: #00E5FF;
		text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
		animation: iconPulse 2s ease-in-out infinite;
	}

	@keyframes iconPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.8; transform: scale(1.05); }
	}

	.subtitle {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.2em;
		margin-top: 0.5rem;
		font-weight: 500;
	}

	.header-stats {
		display: flex;
		gap: 1rem;
	}

	.stat-pill {
		background: rgba(0, 229, 255, 0.1);
		border: 1px solid rgba(0, 229, 255, 0.3);
		border-radius: 100px;
		padding: 0.5rem 1rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		min-width: 80px;
	}

	.stat-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		font-weight: 600;
	}

	.stat-value {
		font-size: 1rem;
		font-weight: 700;
		color: #00E5FF;
	}

	.search-wrapper {
		position: relative;
		width: 100%;
	}

	.premium-input {
		width: 100%;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 0.875rem 1rem 0.875rem 2.75rem;
		color: #ffffff;
		font-size: 0.9rem;
		font-family: inherit;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.premium-input:focus {
		outline: none;
		border-color: #00E5FF;
		background: rgba(0, 229, 255, 0.05);
		box-shadow: 0 0 0 3px rgba(0, 229, 255, 0.1);
	}

	.premium-input::placeholder {
		color: rgba(255, 255, 255, 0.3);
	}

	.search-icon {
		position: absolute;
		left: 1rem;
		top: 50%;
		transform: translateY(-50%);
		color: rgba(255, 255, 255, 0.5);
		pointer-events: none;
	}

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.premium-loader {
		width: 100px;
		height: 100px;
		position: relative;
	}

	.loader-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid transparent;
		border-top-color: #00E5FF;
		border-radius: 50%;
		animation: loaderSpin 1.5s linear infinite;
	}

	.loader-ring:nth-child(2) {
		width: 80%;
		height: 80%;
		top: 10%;
		left: 10%;
		animation-delay: 0.2s;
		border-top-color: #7C4DFF;
	}

	.loader-ring:nth-child(3) {
		width: 60%;
		height: 60%;
		top: 20%;
		left: 20%;
		animation-delay: 0.4s;
		border-top-color: #FF1744;
	}

	.loader-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 2rem;
		color: #00E5FF;
		text-shadow: 0 0 20px rgba(0, 229, 255, 0.8);
	}

	@keyframes loaderSpin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.loading-text {
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.85rem;
		letter-spacing: 0.2em;
		font-weight: 500;
	}

	.table-scroll-container {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
		padding: 0 1rem;
	}

	.table-scroll-container::-webkit-scrollbar {
		width: 6px;
	}

	.table-scroll-container::-webkit-scrollbar-track {
		background: rgba(255, 255, 255, 0.02);
	}

	.table-scroll-container::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
	}

	.table-scroll-container::-webkit-scrollbar-thumb:hover {
		background: rgba(255, 255, 255, 0.2);
	}

	.premium-table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0;
		font-size: 0.875rem;
	}

	.premium-table th {
		background: rgba(0, 0, 0, 0.4);
		color: rgba(255, 255, 255, 0.6);
		padding: 1rem;
		text-align: left;
		font-weight: 600;
		font-size: 0.75rem;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.premium-table td {
		padding: 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.8);
		transition: all 0.2s ease;
	}

	.table-row {
		cursor: pointer;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		position: relative;
	}

	.table-row:hover {
		background: rgba(0, 229, 255, 0.05);
	}

	.table-row.hovered td {
		color: #ffffff;
	}

	.source-cell {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.source-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
		animation: indicatorPulse 2s ease-in-out infinite;
	}

	@keyframes indicatorPulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.2); }
	}

	.source-name {
		font-weight: 500;
	}

	.frequency-cell, .coverage-cell {
		min-width: 120px;
	}

	.frequency-content {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.frequency-value {
		font-weight: 600;
		font-size: 0.9rem;
		color: #ffffff;
	}

	.frequency-bar-bg {
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		overflow: hidden;
		width: 80px;
	}

	.frequency-bar {
		height: 100%;
		transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.coverage-content {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.coverage-value {
		font-weight: 600;
	}

	.coverage-ring {
		flex-shrink: 0;
	}

	.threat-cell {
		min-width: 120px;
	}

	.threat-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.375rem 0.75rem;
		border: 1px solid;
		border-radius: 8px;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.threat-icon {
		font-size: 1rem;
	}

	.matrix-cell {
		min-width: 100px;
	}

	.matrix-visualization {
		display: flex;
		align-items: flex-end;
		gap: 2px;
		height: 30px;
	}

	.matrix-bar {
		width: 3px;
		background: #00E5FF;
		animation: matrixPulse 2s ease-in-out infinite;
	}

	@keyframes matrixPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.6; }
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.viz-panel::-webkit-scrollbar {
		width: 6px;
	}

	.viz-panel::-webkit-scrollbar-track {
		background: rgba(255, 255, 255, 0.02);
	}

	.viz-panel::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
	}

	.metrics-row {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1.5rem;
	}

	.metric-card {
		border-radius: 16px;
		padding: 1.5rem;
		position: relative;
		overflow: hidden;
		box-shadow: 
			0 10px 40px rgba(0, 0, 0, 0.3),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
	}

	.metric-icon-wrapper {
		position: absolute;
		top: 1.5rem;
		right: 1.5rem;
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 229, 255, 0.1);
		border-radius: 12px;
	}

	.metric-icon {
		font-size: 1.5rem;
		color: #00E5FF;
		text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
	}

	.metric-content {
		position: relative;
		z-index: 1;
	}

	.metric-value {
		font-size: 2rem;
		font-weight: 700;
		background: linear-gradient(135deg, #ffffff 0%, #00E5FF 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		margin-bottom: 0.25rem;
	}

	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.15em;
		font-weight: 600;
	}

	.metric-sparkline {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		height: 30px;
		opacity: 0.5;
	}

	.metric-sparkline svg {
		width: 100%;
		height: 100%;
	}

	.viz-card {
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 
			0 10px 40px rgba(0, 0, 0, 0.3),
			inset 0 1px 0 rgba(255, 255, 255, 0.1);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.viz-card h4 {
		margin: 0;
		font-size: 0.875rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.7);
		letter-spacing: 0.1em;
	}

	.card-status-indicator {
		width: 6px;
		height: 6px;
		background: rgba(0, 229, 255, 0.5);
		border-radius: 50%;
		animation: statusBlink 2s ease-in-out infinite;
	}

	.card-status-indicator.active {
		background: #00E5FF;
		animation: statusBlink 0.5s ease-in-out infinite;
		box-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
	}

	@keyframes statusBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}

	.spectrum-chart {
		display: flex;
		flex-direction: column;
		gap: 0.875rem;
	}

	.spectrum-item {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.spectrum-label {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 500;
	}

	.spectrum-visual {
		position: relative;
		height: 24px;
		display: flex;
		align-items: center;
	}

	.spectrum-track {
		position: absolute;
		width: 100%;
		height: 6px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 6px;
	}

	.spectrum-fill {
		position: relative;
		height: 6px;
		border-radius: 6px;
		transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
		overflow: hidden;
	}

	.spectrum-glow {
		position: absolute;
		right: 0;
		top: 50%;
		transform: translateY(-50%);
		width: 20px;
		height: 200%;
		background: rgba(255, 255, 255, 0.5);
		filter: blur(10px);
		animation: spectrumGlow 2s ease-in-out infinite;
	}

	@keyframes spectrumGlow {
		0%, 100% { opacity: 0; transform: translateY(-50%) translateX(-10px); }
		50% { opacity: 1; transform: translateY(-50%) translateX(0); }
	}

	.spectrum-value {
		position: absolute;
		right: 0;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
		font-weight: 600;
	}

	.threat-matrix {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 150px;
		padding: 1rem;
	}

	.matrix-svg {
		width: 100%;
		height: auto;
	}

	.drill-view {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.drill-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		background: rgba(0, 229, 255, 0.03);
	}

	.drill-title {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.drill-icon {
		font-size: 1.5rem;
		color: #00E5FF;
		animation: drillPulse 1s ease-in-out infinite;
	}

	@keyframes drillPulse {
		0%, 100% { transform: translateX(0); }
		50% { transform: translateX(5px); }
	}

	.drill-header h4 {
		margin: 0;
		font-size: 1.125rem;
		font-weight: 600;
		color: #ffffff;
	}

	.drill-badge {
		background: rgba(0, 229, 255, 0.1);
		border: 1px solid rgba(0, 229, 255, 0.3);
		border-radius: 100px;
		padding: 0.25rem 0.75rem;
		font-size: 0.75rem;
		color: #00E5FF;
		font-weight: 600;
	}

	.premium-btn {
		background: rgba(255, 23, 68, 0.1);
		border: 1px solid rgba(255, 23, 68, 0.3);
		width: 36px;
		height: 36px;
		border-radius: 12px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #FF1744;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.premium-btn:hover {
		background: rgba(255, 23, 68, 0.2);
		transform: scale(1.05);
		box-shadow: 0 0 20px rgba(255, 23, 68, 0.3);
	}

	.drill-table-container {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}

	.host-cell {
		font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
		color: #00E5FF;
		font-weight: 500;
		font-size: 0.875rem;
	}

	.status-badge {
		padding: 0.25rem 0.625rem;
		border-radius: 6px;
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		display: inline-block;
	}

	.badge-success {
		background: rgba(0, 229, 255, 0.15);
		color: #00E5FF;
		border: 1px solid rgba(0, 229, 255, 0.3);
	}

	.badge-warning {
		background: rgba(255, 214, 0, 0.15);
		color: #FFD600;
		border: 1px solid rgba(255, 214, 0, 0.3);
	}

	.badge-danger {
		background: rgba(255, 23, 68, 0.15);
		color: #FF1744;
		border: 1px solid rgba(255, 23, 68, 0.3);
	}
</style>