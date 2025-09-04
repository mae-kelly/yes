<!-- CountryMetrics.svelte - Premium Country Intelligence Dashboard -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';
	let viewMode = 'grid'; // 'grid' or 'list'

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

	$: filteredCountries = data.global_intelligence ? 
		Object.entries(data.global_intelligence)
			.filter(([country]) => country.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredCountries.length > 0 ? Math.max(...filteredCountries.map(([,c]) => c)) : 1;

	function getPercentage(count) {
		let total = Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
	}

	function getThreatLevel(count) {
		const percentage = (count / maxCount) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#FF1744' };
		if (percentage >= 50) return { level: 'HIGH', color: '#FFA726' };
		if (percentage >= 25) return { level: 'MEDIUM', color: '#FFD600' };
		return { level: 'LOW', color: '#00E5FF' };
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
	<!-- Header Controls -->
	<div class="header-section">
		<div class="header-content">
			<div class="title-section">
				<h2 class="main-title">
					<span class="title-icon">🗺️</span>
					COUNTRY INTELLIGENCE MATRIX
				</h2>
				<div class="subtitle">Global Asset Distribution Analysis</div>
			</div>
			
			<div class="controls-section">
				<div class="search-wrapper">
					<svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<circle cx="11" cy="11" r="8"></circle>
						<path d="m21 21-4.35-4.35"></path>
					</svg>
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search countries..."
						class="search-input"
					/>
				</div>
				
				<div class="view-toggle">
					<button 
						class="toggle-btn {viewMode === 'grid' ? 'active' : ''}"
						on:click={() => viewMode = 'grid'}>
						<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
							<rect x="3" y="3" width="7" height="7"/>
							<rect x="14" y="3" width="7" height="7"/>
							<rect x="3" y="14" width="7" height="7"/>
							<rect x="14" y="14" width="7" height="7"/>
						</svg>
					</button>
					<button 
						class="toggle-btn {viewMode === 'list' ? 'active' : ''}"
						on:click={() => viewMode = 'list'}>
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="8" y1="6" x2="21" y2="6"/>
							<line x1="8" y1="12" x2="21" y2="12"/>
							<line x1="8" y1="18" x2="21" y2="18"/>
							<line x1="3" y1="6" x2="3.01" y2="6"/>
							<line x1="3" y1="12" x2="3.01" y2="12"/>
							<line x1="3" y1="18" x2="3.01" y2="18"/>
						</svg>
					</button>
				</div>
			</div>
			
			<div class="stats-section">
				<div class="stat-card">
					<div class="stat-value">{(data.total_countries || 0)}</div>
					<div class="stat-label">COUNTRIES</div>
				</div>
				<div class="stat-card">
					<div class="stat-value">
						{Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}
					</div>
					<div class="stat-label">TOTAL ASSETS</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content -->
	<div class="content-section">
		{#if loading && !selectedCountry}
			<div class="loading-state">
				<div class="globe-loader">
					<div class="globe"></div>
					<div class="orbit"></div>
				</div>
				<p>Analyzing global networks...</p>
			</div>
		{:else if selectedCountry}
			<div class="detail-view">
				<div class="detail-header">
					<div class="detail-title">
						<h3>{selectedCountry.country.toUpperCase()}</h3>
						<span class="detail-badge">{selectedCountry.count.toLocaleString()} assets</span>
					</div>
					<button class="close-btn" on:click={closeDetails}>
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
							<line x1="18" y1="6" x2="6" y2="18"/>
							<line x1="6" y1="6" x2="18" y2="18"/>
						</svg>
					</button>
				</div>
				<div class="detail-content">
					<table class="detail-table">
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
									<td class="host-cell">{host.host}</td>
									<td>{host.region || 'Unknown'}</td>
									<td>{host.infrastructure_type || 'Unknown'}</td>
									<td>{host.data_center || 'Unknown'}</td>
									<td>
										<span class="status-dot {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}"></span>
									</td>
									<td>
										<span class="status-dot {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'warning'}"></span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{:else if viewMode === 'grid'}
			<div class="countries-grid">
				{#each filteredCountries as [country, count]}
					{@const threat = getThreatLevel(count)}
					{@const percentage = getPercentage(count)}
					<div class="country-card" 
						on:click={() => drillDownCountry(country, count)}
						style="--threat-color: {threat.color}">
						<div class="card-glow"></div>
						<div class="card-content">
							<div class="country-flag">🏴</div>
							<h3 class="country-name">{country.toUpperCase()}</h3>
							<div class="country-stats">
								<div class="stat">
									<span class="stat-number" style="color: {threat.color}">
										{count.toLocaleString()}
									</span>
									<span class="stat-text">ASSETS</span>
								</div>
								<div class="stat">
									<span class="stat-number" style="color: {threat.color}">
										{percentage}%
									</span>
									<span class="stat-text">COVERAGE</span>
								</div>
							</div>
							<div class="threat-level" style="background: {threat.color}20; color: {threat.color}">
								{threat.level}
							</div>
							<div class="progress-ring">
								<svg width="60" height="60" viewBox="0 0 36 36">
									<circle cx="18" cy="18" r="15" 
											fill="none" 
											stroke="rgba(255,255,255,0.1)" 
											stroke-width="2"/>
									<circle cx="18" cy="18" r="15" 
											fill="none" 
											stroke={threat.color} 
											stroke-width="2"
											stroke-dasharray="{percentage} 100"
											transform="rotate(-90 18 18)"
											stroke-linecap="round"/>
								</svg>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<div class="countries-list">
				<table class="list-table">
					<thead>
						<tr>
							<th>#</th>
							<th>COUNTRY</th>
							<th>ASSETS</th>
							<th>COVERAGE</th>
							<th>THREAT LEVEL</th>
							<th>VISUALIZATION</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredCountries as [country, count], index}
							{@const threat = getThreatLevel(count)}
							{@const percentage = getPercentage(count)}
							<tr class="list-row" on:click={() => drillDownCountry(country, count)}>
								<td class="rank">{index + 1}</td>
								<td class="country-name-cell">
									<span class="flag-icon">🏴</span>
									{country.toUpperCase()}
								</td>
								<td class="numeric" style="color: {threat.color}">{count.toLocaleString()}</td>
								<td class="numeric">{percentage}%</td>
								<td>
									<span class="threat-badge" style="background: {threat.color}20; color: {threat.color}">
										{threat.level}
									</span>
								</td>
								<td>
									<div class="mini-bar">
										<div class="mini-bar-fill" style="width: {(count/maxCount)*100}%; background: {threat.color}"></div>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>

<style>
	.dashboard-container {
		height: calc(100vh - 80px);
		width: 100%;
		display: flex;
		flex-direction: column;
		background: #000000;
		overflow: hidden;
	}

	/* Header Section */
	.header-section {
		background: linear-gradient(135deg, rgba(0, 229, 255, 0.05), transparent);
		border-bottom: 1px solid rgba(0, 229, 255, 0.1);
		padding: 1.5rem;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 2rem;
	}

	.title-section {
		flex: 0 0 auto;
	}

	.main-title {
		margin: 0;
		font-size: 1.25rem;
		font-weight: 600;
		color: #00E5FF;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
	}

	.title-icon {
		font-size: 1.5rem;
		filter: saturate(1.5);
	}

	.subtitle {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.5);
		margin-top: 0.25rem;
		letter-spacing: 0.1em;
	}

	.controls-section {
		flex: 1;
		display: flex;
		align-items: center;
		gap: 1rem;
		justify-content: center;
	}

	.search-wrapper {
		position: relative;
		width: 100%;
		max-width: 400px;
	}

	.search-icon {
		position: absolute;
		left: 1rem;
		top: 50%;
		transform: translateY(-50%);
		color: rgba(255, 255, 255, 0.4);
		stroke-width: 2;
	}

	.search-input {
		width: 100%;
		padding: 0.75rem 1rem 0.75rem 3rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		color: #ffffff;
		font-size: 0.9rem;
		transition: all 0.3s ease;
	}

	.search-input:focus {
		outline: none;
		border-color: #00E5FF;
		background: rgba(0, 229, 255, 0.05);
		box-shadow: 0 0 20px rgba(0, 229, 255, 0.2);
	}

	.view-toggle {
		display: flex;
		gap: 0.25rem;
		background: rgba(0, 0, 0, 0.6);
		padding: 0.25rem;
		border-radius: 8px;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.toggle-btn {
		padding: 0.5rem;
		background: transparent;
		border: none;
		color: rgba(255, 255, 255, 0.4);
		cursor: pointer;
		border-radius: 6px;
		transition: all 0.2s ease;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.toggle-btn:hover {
		background: rgba(255, 255, 255, 0.05);
	}

	.toggle-btn.active {
		background: rgba(0, 229, 255, 0.2);
		color: #00E5FF;
	}

	.stats-section {
		display: flex;
		gap: 1rem;
	}

	.stat-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 229, 255, 0.2);
		border-radius: 12px;
		padding: 0.75rem 1.25rem;
		text-align: center;
	}

	.stat-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #00E5FF;
		text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
	}

	.stat-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		margin-top: 0.25rem;
	}

	/* Content Section */
	.content-section {
		flex: 1;
		padding: 1.5rem;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	/* Grid View */
	.countries-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 1rem;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.country-card {
		position: relative;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.7));
		border: 1px solid var(--threat-color, rgba(255, 255, 255, 0.1));
		border-radius: 16px;
		padding: 1.5rem;
		cursor: pointer;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		overflow: hidden;
	}

	.card-glow {
		position: absolute;
		top: -50%;
		left: -50%;
		width: 200%;
		height: 200%;
		background: radial-gradient(circle, var(--threat-color, #00E5FF) 0%, transparent 70%);
		opacity: 0;
		transition: opacity 0.3s ease;
		pointer-events: none;
	}

	.country-card:hover {
		transform: translateY(-8px) scale(1.02);
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8);
	}

	.country-card:hover .card-glow {
		opacity: 0.1;
	}

	.card-content {
		position: relative;
		z-index: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.75rem;
	}

	.country-flag {
		font-size: 2rem;
		filter: grayscale(0.5);
	}

	.country-name {
		margin: 0;
		font-size: 0.85rem;
		font-weight: 600;
		color: #ffffff;
		text-align: center;
		letter-spacing: 0.05em;
	}

	.country-stats {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		width: 100%;
		margin: 0.5rem 0;
	}

	.stat {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}

	.stat-number {
		font-size: 1.1rem;
		font-weight: 700;
	}

	.stat-text {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.threat-level {
		padding: 0.25rem 0.5rem;
		border-radius: 6px;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		width: 100%;
		text-align: center;
	}

	.progress-ring {
		margin-top: 0.5rem;
	}

	/* List View */
	.countries-list {
		flex: 1;
		overflow: auto;
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 16px;
	}

	.list-table {
		width: 100%;
		border-collapse: collapse;
	}

	.list-table th {
		background: rgba(0, 0, 0, 0.8);
		color: rgba(255, 255, 255, 0.6);
		padding: 1rem;
		text-align: left;
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 1px solid rgba(0, 229, 255, 0.2);
	}

	.list-table td {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.8);
		font-size: 0.85rem;
	}

	.list-row {
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.list-row:hover {
		background: rgba(0, 229, 255, 0.05);
	}

	.rank {
		font-weight: 600;
		color: #00E5FF;
		width: 50px;
	}

	.country-name-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 500;
	}

	.flag-icon {
		font-size: 1rem;
	}

	.numeric {
		font-family: 'SF Mono', monospace;
		text-align: right;
	}

	.threat-badge {
		padding: 0.25rem 0.5rem;
		border-radius: 6px;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		display: inline-block;
	}

	.mini-bar {
		width: 100px;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}

	.mini-bar-fill {
		height: 100%;
		transition: width 0.3s ease;
	}

	/* Loading State */
	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.globe-loader {
		position: relative;
		width: 80px;
		height: 80px;
	}

	.globe {
		width: 100%;
		height: 100%;
		border: 2px solid #00E5FF;
		border-radius: 50%;
		position: relative;
		animation: rotate 2s linear infinite;
	}

	.globe::before {
		content: '';
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid rgba(0, 229, 255, 0.3);
		border-radius: 50%;
		transform: rotateX(60deg);
	}

	.globe::after {
		content: '';
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid rgba(0, 229, 255, 0.3);
		border-radius: 50%;
		transform: rotateY(60deg);
	}

	.orbit {
		position: absolute;
		width: 120%;
		height: 120%;
		border: 1px solid rgba(0, 229, 255, 0.2);
		border-radius: 50%;
		top: -10%;
		left: -10%;
		animation: rotate 3s linear infinite reverse;
	}

	@keyframes rotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	/* Detail View */
	.detail-view {
		flex: 1;
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 16px;
		overflow: hidden;
	}

	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		background: linear-gradient(135deg, rgba(0, 229, 255, 0.1), transparent);
		border-bottom: 1px solid rgba(0, 229, 255, 0.2);
	}

	.detail-title {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.detail-title h3 {
		margin: 0;
		font-size: 1.1rem;
		color: #00E5FF;
		font-weight: 600;
	}

	.detail-badge {
		background: rgba(0, 229, 255, 0.2);
		border: 1px solid #00E5FF;
		padding: 0.25rem 0.75rem;
		border-radius: 100px;
		font-size: 0.75rem;
		color: #00E5FF;
		font-weight: 500;
	}

	.close-btn {
		background: rgba(255, 23, 68, 0.1);
		border: 1px solid #FF1744;
		color: #FF1744;
		width: 36px;
		height: 36px;
		border-radius: 8px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}

	.close-btn:hover {
		background: rgba(255, 23, 68, 0.2);
		transform: scale(1.1);
	}

	.detail-content {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}

	.detail-table {
		width: 100%;
		border-collapse: collapse;
	}

	.detail-table th {
		background: rgba(0, 0, 0, 0.4);
		color: rgba(255, 255, 255, 0.6);
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
	}

	.detail-table td {
		padding: 0.75rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.host-cell {
		font-family: 'SF Mono', monospace;
		color: #00E5FF;
		font-weight: 500;
	}

	.status-dot {
		display: inline-block;
		width: 8px;
		height: 8px;
		border-radius: 50%;
		margin: 0 auto;
	}

	.status-dot.active {
		background: #00E5FF;
		box-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
	}

	.status-dot.inactive {
		background: #FF1744;
		box-shadow: 0 0 10px rgba(255, 23, 68, 0.5);
	}

	.status-dot.warning {
		background: #FFD600;
		box-shadow: 0 0 10px rgba(255, 214, 0, 0.5);
	}

	/* Scrollbar */
	::-webkit-scrollbar {
		width: 6px;
		height: 6px;
	}

	::-webkit-scrollbar-track {
		background: rgba(255, 255, 255, 0.02);
	}

	::-webkit-scrollbar-thumb {
		background: rgba(0, 229, 255, 0.2);
		border-radius: 3px;
	}

	::-webkit-scrollbar-thumb:hover {
		background: rgba(0, 229, 255, 0.3);
	}

	/* Responsive */
	@media (max-width: 1200px) {
		.countries-grid {
			grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		}
		
		.header-content {
			flex-direction: column;
			align-items: stretch;
			gap: 1rem;
		}
		
		.controls-section {
			justify-content: space-between;
		}
	}

	@media (max-width: 768px) {
		.countries-grid {
			grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		}
		
		.stats-section {
			width: 100%;
		}
		
		.stat-card {
			flex: 1;
		}
	}
</style>