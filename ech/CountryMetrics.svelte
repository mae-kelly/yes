<!-- CountryMetrics.svelte - National Defense Grid -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';
	let scanlinePos = 0;
	let heatmapData = [];

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/country_metrics');
			let result = await response.json();
			data = result;
			loading = false;
			
			// Generate heatmap data
			if (data.global_intelligence) {
				const sorted = Object.entries(data.global_intelligence).sort((a, b) => b[1] - a[1]);
				for (let i = 0; i < Math.min(20, sorted.length); i++) {
					heatmapData.push({
						intensity: sorted[i][1] / sorted[0][1],
						x: (i % 5) * 20 + 10,
						y: Math.floor(i / 5) * 20 + 10
					});
				}
			}
		} catch (err) {
			console.error('Country metrics error:', err);
			loading = false;
		}
		
		// Scanline animation
		const scanInterval = setInterval(() => {
			scanlinePos = (scanlinePos + 1) % 100;
		}, 50);
		
		return () => clearInterval(scanInterval);
	});

	$: sortedCountries = data.global_intelligence ? 
		Object.entries(data.global_intelligence)
			.filter(([country]) => country.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = sortedCountries.length > 0 ? Math.max(...sortedCountries.map(([,c]) => c)) : 1;

	function getPercentage(count) {
		let total = Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
	}

	function getDefenseLevel(count) {
		const percentage = (count / maxCount) * 100;
		if (percentage >= 60) return { level: 'FORTIFIED', color: '#0a4f3c', priority: 1 };
		if (percentage >= 40) return { level: 'SECURED', color: '#ffcc00', priority: 2 };
		if (percentage >= 20) return { level: 'MONITORED', color: '#ff9900', priority: 3 };
		return { level: 'VULNERABLE', color: '#ff0066', priority: 4 };
	}

	async function drillDownCountry(country, count) {
		selectedCountry = { country, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(country)}`);
			let result = await response.json();
			countryDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Country drill-down error:', err);
			countryDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedCountry = null;
		countryDetails = [];
	}
</script>

<div class="dashboard-container">
	<div class="main-content">
		<!-- Left Panel: National Command -->
		<div class="table-panel">
			<div class="panel-header">
				<div class="header-top">
					<div>
						<h3 class="panel-title">COUNTRIES</h3>
						<div class="subtitle">NATIONAL DEFENSE NETWORK</div>
					</div>
					<div class="defense-status">
						<div class="status-ring"></div>
						<div class="status-ring"></div>
						<div class="status-ring"></div>
					</div>
				</div>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="SEARCH NATIONS..."
						class="search-input"
					/>
					<div class="search-scan" style="left: {scanlinePos}%"></div>
				</div>
			</div>
			
			{#if loading && !selectedCountry}
				<div class="loading-state">
					<div class="defense-loader">
						<div class="loader-shield"></div>
						<div class="loader-pulse"></div>
					</div>
					<p class="loading-text">SCANNING NATIONAL GRIDS...</p>
				</div>
			{:else if selectedCountry}
				<div class="drill-view">
					<div class="drill-header">
						<div class="drill-title">
							<h4>{selectedCountry.country.toUpperCase()}</h4>
							<span class="drill-count">{selectedCountry.count.toLocaleString()} ASSETS</span>
						</div>
						<button class="close-btn" on:click={closeDetails}>
							<svg width="20" height="20" viewBox="0 0 20 20">
								<path d="M2 2L18 18M18 2L2 18" stroke="#ff0066" stroke-width="2"/>
							</svg>
						</button>
					</div>
					<div class="drill-table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>REGION</th>
									<th>INFRASTRUCTURE</th>
									<th>DATA CENTER</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each countryDetails as host}
									<tr>
										<td class="host-cell">{host.host.substring(0, 30)}</td>
										<td>{host.region || 'CLASSIFIED'}</td>
										<td>{host.infrastructure_type || 'CLASSIFIED'}</td>
										<td>{host.data_center || 'CLASSIFIED'}</td>
										<td>
											<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'VERIFIED' : 'UNKNOWN'}
											</span>
										</td>
										<td>
											<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? 'SECURED' : 'EXPOSED'}
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
					<table class="data-table">
						<thead>
							<tr>
								<th>NATION</th>
								<th>ASSETS</th>
								<th>COVERAGE</th>
								<th>DEFENSE LEVEL</th>
								<th>THREAT MATRIX</th>
							</tr>
						</thead>
						<tbody>
							{#each sortedCountries as [country, count]}
								{@const defense = getDefenseLevel(count)}
								<tr on:click={() => drillDownCountry(country, count)}>
									<td class="country-cell">
										<div class="country-indicator" style="background: {defense.color}"></div>
										<span class="country-name">{country.substring(0, 30).toUpperCase()}</span>
									</td>
									<td class="center">
										<span class="asset-value">{count.toLocaleString()}</span>
									</td>
									<td class="center">{getPercentage(count)}%</td>
									<td class="center">
										<div class="defense-badge" style="border-color: {defense.color}">
											<span style="color: {defense.color}">{defense.level}</span>
											<div class="defense-bars">
												{#each Array(4) as _, i}
													<div class="defense-bar" 
														style="background: {i < (5 - defense.priority) ? defense.color : '#111'}">
													</div>
												{/each}
											</div>
										</div>
									</td>
									<td>
										<div class="threat-visualization">
											<svg viewBox="0 0 40 20" class="threat-svg">
												{#each Array(8) as _, i}
													<rect x="{i * 5}" y="5" width="4" height="{10 * (count/maxCount)}" 
														  fill={defense.color} opacity="{0.3 + (i * 0.1)}"/>
												{/each}
												<line x1="0" y1="10" x2="40" y2="10" 
													  stroke={defense.color} stroke-width="0.5" opacity="0.5"/>
											</svg>
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>

		<!-- Right Panel: Strategic Overview -->
		<div class="viz-panel">
			<!-- National Metrics -->
			<div class="metrics-grid">
				<div class="metric-card primary">
					<div class="metric-icon">◈</div>
					<div class="metric-content">
						<div class="metric-value">{(data.total_countries || 0)}</div>
						<div class="metric-label">NATIONS</div>
					</div>
				</div>
				<div class="metric-card secondary">
					<div class="metric-icon">◉</div>
					<div class="metric-content">
						<div class="metric-value">{Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
						<div class="metric-label">GLOBAL ASSETS</div>
					</div>
				</div>
			</div>

			<!-- Strategic Heatmap -->
			<div class="viz-card">
				<div class="card-header">
					<h4>STRATEGIC HEATMAP</h4>
					<div class="card-status active"></div>
				</div>
				<div class="heatmap-container">
					<svg viewBox="0 0 100 80" class="heatmap-svg">
						<defs>
							<radialGradient id="heatGradient">
								<stop offset="0%" style="stop-color:#0a4f3c;stop-opacity:1" />
								<stop offset="100%" style="stop-color:#0a4f3c;stop-opacity:0" />
							</radialGradient>
						</defs>
						
						<!-- Grid background -->
						{#each Array(5) as _, i}
							<line x1="0" y1="{i * 20}" x2="100" y2="{i * 20}" 
								  stroke="#0a4f3c" stroke-width="0.2" opacity="0.2"/>
							<line x1="{i * 20}" y1="0" x2="{i * 20}" y2="80" 
								  stroke="#0a4f3c" stroke-width="0.2" opacity="0.2"/>
						{/each}
						
						<!-- Heatmap points -->
						{#each heatmapData as point}
							<circle cx="{point.x}" cy="{point.y}" r="{8 * point.intensity}" 
									fill="url(#heatGradient)" opacity="{0.3 + point.intensity * 0.5}"/>
							<circle cx="{point.x}" cy="{point.y}" r="2" 
									fill="#0a4f3c" opacity="{point.intensity}"/>
						{/each}
					</svg>
				</div>
			</div>

			<!-- Top Nations -->
			<div class="viz-card">
				<div class="card-header">
					<h4>STRATEGIC PRIORITIES</h4>
					<div class="card-status"></div>
				</div>
				<div class="priority-list">
					{#each sortedCountries.slice(0, 8) as [country, count], i}
						{@const defense = getDefenseLevel(count)}
						<div class="priority-item">
							<div class="priority-rank" style="border-color: {defense.color}">
								<span>{i + 1}</span>
							</div>
							<div class="priority-details">
								<div class="priority-name">{country.substring(0, 20).toUpperCase()}</div>
								<div class="priority-bar-container">
									<div class="priority-bar" 
										 style="width: {(count/maxCount)*100}%; 
												background: linear-gradient(90deg, #0a4f3c, {defense.color})">
									</div>
								</div>
							</div>
							<div class="priority-stats">
								<span class="stat-value">{count.toLocaleString()}</span>
								<span class="stat-label">{defense.level}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Defense Matrix -->
			<div class="viz-card">
				<div class="card-header">
					<h4>DEFENSE MATRIX</h4>
					<div class="card-status active"></div>
				</div>
				<div class="defense-matrix">
					{#each sortedCountries.slice(0, 6) as [country, count]}
						{@const defense = getDefenseLevel(count)}
						{@const percentage = getPercentage(count)}
						<div class="matrix-cell" style="border-color: {defense.color}">
							<div class="matrix-country">{country.substring(0, 10).toUpperCase()}</div>
							<div class="matrix-visual">
								<svg viewBox="0 0 40 40" class="matrix-icon">
									<polygon points="20,5 35,20 20,35 5,20" 
											fill="none" stroke={defense.color} stroke-width="1.5"/>
									<circle cx="20" cy="20" r="8" 
											fill={defense.color} opacity="0.3"/>
									<circle cx="20" cy="20" r="3" 
											fill={defense.color}/>
								</svg>
							</div>
							<div class="matrix-percentage" style="color: {defense.color}">{percentage}%</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.dashboard-container {
		height: calc(100vh - 180px);
		display: flex;
		background: #000000;
		color: #e0e0e0;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
		padding: 1rem;
	}

	.main-content {
		flex: 1;
		display: flex;
		gap: 1rem;
		overflow: hidden;
	}

	.table-panel {
		flex: 1.5;
		background: linear-gradient(135deg, #0a0a0a 0%, #050505 100%);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		position: relative;
	}

	.panel-header {
		padding: 1.5rem;
		border-bottom: 1px solid #0a4f3c;
		background: rgba(10, 79, 60, 0.02);
		flex-shrink: 0;
	}

	.header-top {
		display: flex;
		justify-content: space-between;
		align-items: start;
		margin-bottom: 1rem;
	}

	.panel-title {
		margin: 0;
		color: #0a4f3c;
		font-size: 1.2rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-shadow: 0 0 20px rgba(10, 79, 60, 0.5);
	}

	.subtitle {
		font-size: 0.7rem;
		color: #666;
		letter-spacing: 0.2em;
		margin-top: 0.25rem;
	}

	.defense-status {
		display: flex;
		gap: 0.5rem;
	}

	.status-ring {
		width: 12px;
		height: 12px;
		border: 2px solid #0a4f3c;
		border-radius: 50%;
		animation: ringPulse 2s ease-in-out infinite;
	}

	.status-ring:nth-child(2) {
		animation-delay: 0.3s;
	}

	.status-ring:nth-child(3) {
		animation-delay: 0.6s;
	}

	@keyframes ringPulse {
		0%, 100% { transform: scale(1); opacity: 0.3; }
		50% { transform: scale(1.2); opacity: 1; }
	}

	.controls {
		position: relative;
	}

	.search-input {
		width: 100%;
		background: #000;
		border: 1px solid #0a4f3c;
		border-radius: 2px;
		padding: 0.6rem 1rem;
		color: #e0e0e0;
		font-size: 0.8rem;
		font-family: inherit;
		letter-spacing: 0.05em;
	}

	.search-input:focus {
		outline: none;
		box-shadow: 0 0 20px rgba(10, 79, 60, 0.3);
		background: rgba(10, 79, 60, 0.02);
	}

	.search-scan {
		position: absolute;
		bottom: 0;
		width: 50px;
		height: 1px;
		background: linear-gradient(90deg, transparent, #0a4f3c, transparent);
		transition: left 0.05s linear;
	}

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.defense-loader {
		width: 80px;
		height: 80px;
		position: relative;
	}

	.loader-shield {
		width: 100%;
		height: 100%;
		border: 3px solid #0a4f3c;
		border-radius: 50%;
		clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
		animation: shieldRotate 2s linear infinite;
	}

	.loader-pulse {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 40px;
		height: 40px;
		background: radial-gradient(circle, #0a4f3c, transparent);
		border-radius: 50%;
		animation: pulse 1s ease-in-out infinite;
	}

	@keyframes shieldRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes pulse {
		0%, 100% { opacity: 0.3; transform: translate(-50%, -50%) scale(1); }
		50% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
	}

	.loading-text {
		color: #0a4f3c;
		font-size: 0.8rem;
		letter-spacing: 0.2em;
	}

	.table-scroll-container {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.8rem;
	}

	.data-table th {
		background: rgba(10, 79, 60, 0.05);
		color: #0a4f3c;
		padding: 1rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 2px solid #0a4f3c;
	}

	.data-table td {
		padding: 0.8rem 1rem;
		border-bottom: 1px solid rgba(10, 79, 60, 0.1);
		color: #b8a678;
	}

	.data-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.data-table tbody tr:hover {
		background: rgba(10, 79, 60, 0.05);
	}

	.country-cell {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.country-indicator {
		width: 8px;
		height: 8px;
		transform: rotate(45deg);
		animation: indicatorPulse 2s ease-in-out infinite;
	}

	@keyframes indicatorPulse {
		0%, 100% { transform: rotate(45deg) scale(1); }
		50% { transform: rotate(45deg) scale(1.3); }
	}

	.country-name {
		font-weight: 500;
		color: #e0e0e0;
	}

	.center {
		text-align: center;
	}

	.asset-value {
		font-weight: 600;
		color: #b8a678;
	}

	.defense-badge {
		display: inline-flex;
		flex-direction: column;
		align-items: center;
		gap: 0.3rem;
		padding: 0.3rem 0.6rem;
		border: 1px solid;
		border-radius: 2px;
	}

	.defense-badge span {
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.defense-bars {
		display: flex;
		gap: 2px;
	}

	.defense-bar {
		width: 3px;
		height: 6px;
	}

	.threat-visualization {
		display: flex;
		justify-content: center;
	}

	.threat-svg {
		width: 40px;
		height: 20px;
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.metric-card {
		background: linear-gradient(135deg, #0a0a0a 0%, #050505 100%);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		padding: 1.2rem;
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.metric-icon {
		font-size: 1.5rem;
		color: #0a4f3c;
		animation: iconPulse 3s ease-in-out infinite;
	}

	@keyframes iconPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.metric-content {
		flex: 1;
	}

	.metric-value {
		font-size: 1.8rem;
		font-weight: 700;
		color: #0a4f3c;
		text-shadow: 0 0 20px rgba(10, 79, 60, 0.5);
	}

	.metric-label {
		font-size: 0.7rem;
		color: #b8a678;
		letter-spacing: 0.1em;
		margin-top: 0.25rem;
	}

	.viz-card {
		background: linear-gradient(135deg, #0a0a0a 0%, #050505 100%);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		padding: 1.5rem;
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.viz-card h4 {
		margin: 0;
		font-size: 0.9rem;
		color: #0a4f3c;
		letter-spacing: 0.1em;
		font-weight: 600;
	}

	.card-status {
		width: 6px;
		height: 6px;
		background: #0a4f3c;
		border-radius: 50%;
		animation: statusBlink 2s ease-in-out infinite;
	}

	.card-status.active {
		background: #ff0066;
		animation-duration: 0.5s;
	}

	@keyframes statusBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}

	.heatmap-container {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 100px;
	}

	.heatmap-svg {
		width: 100%;
		height: auto;
	}

	.priority-list {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.priority-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.priority-rank {
		width: 28px;
		height: 28px;
		border: 1px solid;
		border-radius: 2px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.8rem;
		font-weight: 600;
		color: #0a4f3c;
	}

	.priority-details {
		flex: 1;
	}

	.priority-name {
		font-size: 0.75rem;
		color: #e0e0e0;
		font-weight: 500;
		margin-bottom: 0.25rem;
	}

	.priority-bar-container {
		height: 4px;
		background: rgba(10, 79, 60, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}

	.priority-bar {
		height: 100%;
		transition: width 0.3s ease;
	}

	.priority-stats {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 0.2rem;
	}

	.stat-value {
		font-size: 0.7rem;
		color: #b8a678;
		font-weight: 600;
	}

	.stat-label {
		font-size: 0.6rem;
		color: #666;
		letter-spacing: 0.05em;
	}

	.defense-matrix {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.75rem;
	}

	.matrix-cell {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid;
		border-radius: 4px;
		padding: 0.75rem;
		text-align: center;
	}

	.matrix-country {
		font-size: 0.65rem;
		color: #b8a678;
		margin-bottom: 0.5rem;
		letter-spacing: 0.05em;
	}

	.matrix-visual {
		display: flex;
		justify-content: center;
		margin: 0.5rem 0;
	}

	.matrix-icon {
		width: 40px;
		height: 40px;
	}

	.matrix-percentage {
		font-size: 0.75rem;
		font-weight: 600;
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
		border-bottom: 2px solid #0a4f3c;
		background: rgba(10, 79, 60, 0.05);
	}

	.drill-title {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.drill-title h4 {
		margin: 0;
		color: #0a4f3c;
		font-size: 1.1rem;
		letter-spacing: 0.1em;
	}

	.drill-count {
		font-size: 0.8rem;
		color: #b8a678;
		padding: 0.25rem 0.5rem;
		border: 1px solid #0a4f3c;
		border-radius: 2px;
	}

	.close-btn {
		background: rgba(255, 0, 102, 0.1);
		border: 1px solid #ff0066;
		width: 35px;
		height: 35px;
		border-radius: 2px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}

	.close-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: scale(1.1);
	}

	.drill-table-container {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}

	.host-cell {
		font-family: 'Courier New', monospace;
		color: #0a4f3c;
		font-weight: 600;
	}

	.status-badge {
		padding: 0.25rem 0.5rem;
		border-radius: 2px;
		font-size: 0.65rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.status-badge.active {
		background: rgba(10, 79, 60, 0.2);
		color: #0a4f3c;
		border: 1px solid #0a4f3c;
	}

	.status-badge.inactive {
		background: rgba(255, 0, 102, 0.1);
		color: #ff0066;
		border: 1px solid #ff0066;
	}
</style>