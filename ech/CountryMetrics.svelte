<!-- CountryMetrics.svelte - Enhanced Country Analysis with Geographic Visualization -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/country_metrics');
			let result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			console.error('Country metrics error:', err);
			loading = false;
		}
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

	function getCountryFlag(country) {
		// Simplified flag representation
		const flags = {
			'united states': '🇺🇸',
			'usa': '🇺🇸',
			'canada': '🇨🇦',
			'united kingdom': '🇬🇧',
			'uk': '🇬🇧',
			'germany': '🇩🇪',
			'france': '🇫🇷',
			'japan': '🇯🇵',
			'china': '🇨🇳',
			'india': '🇮🇳',
			'brazil': '🇧🇷'
		};
		return flags[country.toLowerCase()] || '🌍';
	}

	function getSecurityLevel(count) {
		const percentage = (count / maxCount) * 100;
		if (percentage >= 60) return { level: 'SECURE', color: '#0f8', icon: '🛡️' };
		if (percentage >= 30) return { level: 'MONITORED', color: '#ff0', icon: '⚠️' };
		return { level: 'VULNERABLE', color: '#f00', icon: '⚡' };
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
		<!-- Left Panel: Country Table -->
		<div class="table-panel">
			<div class="panel-header">
				<div class="geo-scanner"></div>
				<h3 class="panel-title">
					<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"/>
					</svg>
					GEOGRAPHIC ASSET DISTRIBUTION
				</h3>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search countries..."
						class="search-input"
					/>
					<div class="control-buttons">
						<button class="control-btn">MAP</button>
						<button class="control-btn">LIST</button>
						<button class="control-btn active">HYBRID</button>
					</div>
				</div>
			</div>
			
			{#if loading && !selectedCountry}
				<div class="loading-state">
					<div class="geo-loader">
						<div class="loader-globe">🌐</div>
						<div class="loader-ring"></div>
					</div>
					<p>MAPPING GLOBAL INFRASTRUCTURE...</p>
				</div>
			{:else if selectedCountry}
				<div class="drill-view">
					<div class="drill-header">
						<h4>
							<span class="country-flag">{getCountryFlag(selectedCountry.country)}</span>
							{selectedCountry.country.toUpperCase()}
						</h4>
						<div class="drill-stats">
							<span>ASSETS: {selectedCountry.count.toLocaleString()}</span>
							<span>COVERAGE: {getPercentage(selectedCountry.count)}%</span>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
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
										<td>{host.region || '-'}</td>
										<td>{host.infrastructure_type || '-'}</td>
										<td>{host.data_center || '-'}</td>
										<td>
											<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '●' : '○'}
											</span>
										</td>
										<td>
											<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? '●' : '○'}
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
								<th>COUNTRY</th>
								<th>ASSETS</th>
								<th>PERCENTAGE</th>
								<th>SECURITY</th>
								<th>DISTRIBUTION</th>
							</tr>
						</thead>
						<tbody>
							{#each sortedCountries as [country, count]}
								{@const security = getSecurityLevel(count)}
								<tr on:click={() => drillDownCountry(country, count)} class="data-row">
									<td class="country-cell">
										<span class="country-flag">{getCountryFlag(country)}</span>
										<span class="country-name">{country.substring(0, 30).toUpperCase()}</span>
									</td>
									<td class="center">
										<span class="asset-count">{count.toLocaleString()}</span>
									</td>
									<td class="center">
										<span class="percentage">{getPercentage(count)}%</span>
									</td>
									<td class="center">
										<span class="security-level" style="color: {security.color}">
											<span class="security-icon">{security.icon}</span>
											{security.level}
										</span>
									</td>
									<td>
										<div class="distribution-meter">
											<div class="meter-fill" style="width: {(count/maxCount)*100}%; background: {security.color}">
												<div class="meter-pulse"></div>
											</div>
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>

		<!-- Right Panel: Visualizations -->
		<div class="viz-panel">
			<!-- Metrics -->
			<div class="metrics-row">
				<div class="metric-card">
					<div class="metric-icon">🌍</div>
					<div class="metric-value">{data.total_countries || 0}</div>
					<div class="metric-label">COUNTRIES</div>
				</div>
				<div class="metric-card">
					<div class="metric-icon">◈</div>
					<div class="metric-value">{Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL ASSETS</div>
				</div>
			</div>

			<!-- Geographic Map -->
			<div class="viz-card">
				<h4>
					<span class="viz-icon">◎</span>
					GEOGRAPHIC CONCENTRATION MAP
				</h4>
				<div class="geo-map">
					<svg viewBox="0 0 400 200" class="world-visualization">
						<!-- Simplified world map points -->
						{#each sortedCountries.slice(0, 10) as [country, count], i}
							{@const security = getSecurityLevel(count)}
							{@const x = 50 + (i % 5) * 70}
							{@const y = 50 + Math.floor(i / 5) * 60}
							{@const size = (count / maxCount) * 30 + 10}
							
							<g class="country-node">
								<!-- Ripple effect -->
								<circle cx={x} cy={y} r={size * 1.5} fill={security.color} opacity="0.1" class="ripple"/>
								<circle cx={x} cy={y} r={size * 1.2} fill={security.color} opacity="0.2" class="ripple-delayed"/>
								
								<!-- Main node -->
								<circle cx={x} cy={y} r={size} fill={security.color} opacity="0.4"/>
								<circle cx={x} cy={y} r={size * 0.7} fill={security.color} opacity="0.6"/>
								<circle cx={x} cy={y} r={size * 0.4} fill={security.color} opacity="0.8" class="node-core"/>
								
								<!-- Country code -->
								<text x={x} y={y + 3} text-anchor="middle" font-size="8" fill="#fff" font-weight="600">
									{country.substring(0, 3).toUpperCase()}
								</text>
							</g>
						{/each}
						
						<!-- Connection lines -->
						{#each sortedCountries.slice(0, 5) as [_, _1], i}
							{#if i < 4}
								{@const x1 = 50 + (i % 5) * 70}
								{@const y1 = 50 + Math.floor(i / 5) * 60}
								{@const x2 = 50 + ((i + 1) % 5) * 70}
								{@const y2 = 50 + Math.floor((i + 1) / 5) * 60}
								<line x1={x1} y1={y1} x2={x2} y2={y2} 
									  stroke="#0ff" stroke-width="0.5" opacity="0.3" 
									  stroke-dasharray="2,4" class="connection-line"/>
							{/if}
						{/each}
					</svg>
				</div>
			</div>

			<!-- Top Countries Bar Chart -->
			<div class="viz-card">
				<h4>
					<span class="viz-icon">▣</span>
					TOP COUNTRIES BY ASSETS
				</h4>
				<div class="bar-chart">
					{#each sortedCountries.slice(0, 8) as [country, count]}
						{@const security = getSecurityLevel(count)}
						<div class="bar-item">
							<div class="bar-label">
								<span class="bar-flag">{getCountryFlag(country)}</span>
								{country.substring(0, 20).toUpperCase()}
							</div>
							<div class="bar-container">
								<div class="bar-fill" style="width: {(count/maxCount)*100}%; background: linear-gradient(90deg, {security.color}, transparent)">
									<div class="bar-shine"></div>
								</div>
								<span class="bar-value">{count.toLocaleString()}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Security Assessment Grid -->
			<div class="viz-card">
				<h4>
					<span class="viz-icon">🛡️</span>
					SECURITY ASSESSMENT MATRIX
				</h4>
				<div class="security-grid">
					{#each sortedCountries.slice(0, 6) as [country, count]}
						{@const security = getSecurityLevel(count)}
						<div class="security-card" style="border-color: {security.color}">
							<div class="security-header">
								<span class="security-flag">{getCountryFlag(country)}</span>
								<span class="security-status" style="color: {security.color}">{security.icon}</span>
							</div>
							<div class="security-country">{country.substring(0, 10).toUpperCase()}</div>
							<div class="security-value" style="color: {security.color}">{getPercentage(count)}%</div>
							<div class="security-label">{security.level}</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.dashboard-container {
		height: calc(100vh - 200px);
		display: flex;
		background: #000;
		color: #fff;
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
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid #0ff;
		border-radius: 4px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		position: relative;
	}

	.panel-header {
		padding: 1rem 1.5rem;
		border-bottom: 1px solid rgba(0, 255, 255, 0.2);
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.05) 0%, transparent 100%);
		position: relative;
	}

	.geo-scanner {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 2px;
		background: linear-gradient(90deg, transparent, #0ff, transparent);
		animation: scan 3s linear infinite;
	}

	@keyframes scan {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100%); }
	}

	.panel-title {
		margin: 0 0 1rem 0;
		color: #0ff;
		font-size: 1rem;
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
	}

	.icon {
		width: 20px;
		height: 20px;
		color: #0ff;
	}

	.controls {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.search-input {
		flex: 1;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 2px;
		padding: 0.5rem 0.75rem;
		color: #fff;
		font-family: inherit;
	}

	.search-input:focus {
		outline: none;
		border-color: #0ff;
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
	}

	.control-buttons {
		display: flex;
		gap: 0.25rem;
	}

	.control-btn {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 2px;
		padding: 0.5rem 0.75rem;
		color: #666;
		font-size: 0.7rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.control-btn.active,
	.control-btn:hover {
		background: rgba(0, 255, 255, 0.1);
		border-color: #0ff;
		color: #0ff;
	}

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}

	.geo-loader {
		width: 80px;
		height: 80px;
		position: relative;
	}

	.loader-globe {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 3rem;
		animation: globeSpin 2s linear infinite;
	}

	.loader-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid #0ff;
		border-radius: 50%;
		border-top-color: transparent;
		animation: ringSpin 1s linear infinite;
	}

	@keyframes globeSpin {
		to { transform: translate(-50%, -50%) rotateY(360deg); }
	}

	@keyframes ringSpin {
		to { transform: rotate(360deg); }
	}

	.table-scroll-container {
		flex: 1;
		overflow-y: auto;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
	}

	.data-table th {
		background: rgba(0, 255, 255, 0.05);
		color: #0ff;
		padding: 0.75rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 2px solid #0ff;
	}

	.data-table td {
		padding: 0.75rem;
		border-bottom: 1px solid rgba(0, 255, 255, 0.1);
		color: #aaa;
	}

	.data-row {
		cursor: pointer;
		transition: all 0.2s;
	}

	.data-row:hover {
		background: rgba(0, 255, 255, 0.05);
	}

	.country-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.country-flag {
		font-size: 1.2rem;
	}

	.country-name {
		font-weight: 500;
		color: #fff;
	}

	.center {
		text-align: center;
	}

	.asset-count {
		color: #0ff;
		font-weight: 600;
	}

	.percentage {
		color: #ff0;
		font-weight: 500;
	}

	.security-level {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.security-icon {
		font-size: 0.9rem;
	}

	.distribution-meter {
		height: 8px;
		background: rgba(0, 255, 255, 0.1);
		border-radius: 4px;
		overflow: hidden;
		position: relative;
	}

	.meter-fill {
		height: 100%;
		transition: width 0.5s ease;
		position: relative;
	}

	.meter-pulse {
		position: absolute;
		top: 0;
		right: 0;
		width: 30px;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
		animation: meterPulse 1.5s linear infinite;
	}

	@keyframes meterPulse {
		0% { transform: translateX(-30px); }
		100% { transform: translateX(30px); }
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
	}

	.metrics-row {
		display: flex;
		gap: 1rem;
	}

	.metric-card {
		flex: 1;
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid #0ff;
		border-radius: 4px;
		padding: 1.5rem;
		text-align: center;
	}

	.metric-icon {
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}

	.metric-value {
		font-size: 2rem;
		font-weight: 700;
		color: #0ff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
		margin-bottom: 0.5rem;
	}

	.metric-label {
		font-size: 0.7rem;
		color: #666;
		letter-spacing: 0.1em;
	}

	.viz-card {
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 4px;
		padding: 1.5rem;
	}

	.viz-card h4 {
		margin: 0 0 1rem 0;
		font-size: 0.85rem;
		color: #0ff;
		letter-spacing: 0.05em;
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.viz-icon {
		font-size: 1rem;
	}

	.geo-map {
		width: 100%;
		height: 200px;
	}

	.world-visualization {
		width: 100%;
		height: 100%;
	}

	.ripple {
		animation: rippleEffect 3s ease-out infinite;
	}

	.ripple-delayed {
		animation: rippleEffect 3s ease-out infinite;
		animation-delay: 1.5s;
	}

	@keyframes rippleEffect {
		0% { transform: scale(0.8); opacity: 0.4; }
		100% { transform: scale(1.5); opacity: 0; }
	}

	.node-core {
		animation: corePulse 2s ease-in-out infinite;
	}

	@keyframes corePulse {
		0%, 100% { opacity: 0.8; }
		50% { opacity: 1; }
	}

	.connection-line {
		animation: connectionFlow 3s linear infinite;
	}

	@keyframes connectionFlow {
		0% { stroke-dashoffset: 0; }
		100% { stroke-dashoffset: -12; }
	}

	.bar-chart {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.bar-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.bar-label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
		color: #aaa;
		font-weight: 500;
	}

	.bar-flag {
		font-size: 1rem;
	}

	.bar-container {
		position: relative;
		height: 20px;
		background: rgba(0, 255, 255, 0.05);
		border-radius: 2px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
		position: relative;
	}

	.bar-shine {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 50%;
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.2), transparent);
	}

	.bar-value {
		position: absolute;
		right: 0.5rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.7rem;
		font-weight: 600;
		color: #fff;
	}

	.security-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.75rem;
	}

	.security-card {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid;
		border-radius: 4px;
		padding: 0.75rem;
		text-align: center;
		transition: all 0.2s;
	}

	.security-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 20px rgba(0, 255, 255, 0.2);
	}

	.security-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.security-flag {
		font-size: 1.2rem;
	}

	.security-status {
		font-size: 1rem;
	}

	.security-country {
		font-size: 0.7rem;
		color: #aaa;
		margin-bottom: 0.25rem;
	}

	.security-value {
		font-size: 1.2rem;
		font-weight: 700;
		margin-bottom: 0.25rem;
	}

	.security-label {
		font-size: 0.6rem;
		color: #666;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	/* Drill-down styles */
	.drill-view {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.drill-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
		border-bottom: 2px solid #0ff;
		background: rgba(0, 255, 255, 0.05);
	}

	.drill-header h4 {
		margin: 0;
		color: #0ff;
		font-size: 1.2rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.drill-stats {
		display: flex;
		gap: 1rem;
		font-size: 0.8rem;
		color: #aaa;
	}

	.close-btn {
		background: rgba(255, 0, 100, 0.1);
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 30px;
		height: 30px;
		border-radius: 2px;
		cursor: pointer;
		font-size: 1.2rem;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}

	.close-btn:hover {
		background: rgba(255, 0, 100, 0.2);
		transform: scale(1.1);
	}

	.drill-table-container {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}

	.host-cell {
		font-family: 'Courier New', monospace;
		color: #0ff;
		font-weight: 500;
	}

	.status-badge {
		font-size: 1rem;
		display: inline-block;
		width: 20px;
		text-align: center;
	}

	.status-badge.active {
		color: #0f8;
	}

	.status-badge.inactive {
		color: #f00;
	}
</style>