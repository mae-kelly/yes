<!-- DomainMetrics.svelte - Enhanced with perfect screen fit -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedDomain = null;
	let domainDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 15;
	let activeView = 'table';

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/domain_visibility/breakdown');
			let result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			console.error('Domain metrics error:', err);
			loading = false;
		}
	});

	$: domainList = data.domain_distribution ? 
		Object.entries(data.domain_distribution)
			.filter(([domain]) => domain.toLowerCase().includes(searchTerm.toLowerCase()))
			.map(([domain, count]) => ({ domain, count }))
			.sort((a, b) => b.count - a.count) : [];
	
	$: paginatedDomains = domainList.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(domainList.length / itemsPerPage);

	function getThreatLevel(domain) {
		if (domain === '1dc_only') return { level: 'HIGH', color: '#ff00ff', intensity: 0.9 };
		if (domain === 'fead_only') return { level: 'MED', color: '#00ffff', intensity: 0.7 };
		if (domain === 'both_domains') return { level: 'OPT', color: '#00ff85', intensity: 0.5 };
		return { level: 'LOW', color: '#0096ff', intensity: 0.3 };
	}

	function getPercentage(count) {
		let total = data.total_hosts || 1;
		return ((count / total) * 100).toFixed(2);
	}

	async function drillDownDomain(domain, count) {
		selectedDomain = { domain, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(domain)}`);
			let result = await response.json();
			domainDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Domain drill-down error:', err);
			domainDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedDomain = null;
		domainDetails = [];
	}

	$: domainPercentages = data.domain_percentages || {};
	$: warfareStatus = data.warfare_status || 'ANALYZING';
</script>

<div class="domain-warfare-container">
	<!-- Header Section with Metrics -->
	<div class="warfare-header">
		<div class="header-content">
			<div class="title-section">
				<h1>DOMAIN WARFARE MATRIX</h1>
				<p>1DC vs FEAD Classification Analysis</p>
			</div>
			<div class="warfare-metrics">
				<div class="metric-card critical">
					<div class="metric-value">{(data.total_hosts || 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL HOSTS</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{domainPercentages['1dc_only'] || 0}%</div>
					<div class="metric-label">1DC DOMAIN</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{domainPercentages['fead_only'] || 0}%</div>
					<div class="metric-label">FEAD DOMAIN</div>
				</div>
				<div class="metric-card success">
					<div class="metric-value">{domainPercentages['both_domains'] || 0}%</div>
					<div class="metric-label">DUAL DOMAIN</div>
				</div>
				<div class="metric-card warning">
					<div class="metric-value">{warfareStatus}</div>
					<div class="metric-label">STATUS</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content Grid -->
	<div class="warfare-grid">
		<!-- Left Panel: Table/Details -->
		<div class="table-section">
			<div class="section-header">
				<h3>DOMAIN DISTRIBUTION MATRIX</h3>
				<div class="control-bar">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search domains..."
						class="search-input"
					/>
					<div class="view-toggle">
						<button class="toggle-btn {activeView === 'table' ? 'active' : ''}" on:click={() => activeView = 'table'}>
							TABLE
						</button>
						<button class="toggle-btn {activeView === 'grid' ? 'active' : ''}" on:click={() => activeView = 'grid'}>
							GRID
						</button>
					</div>
				</div>
			</div>
			
			{#if loading && !selectedDomain}
				<div class="loading-matrix">
					<div class="matrix-spinner"></div>
					<p>ANALYZING DOMAIN WARFARE...</p>
				</div>
			{:else if selectedDomain}
				<!-- Drill-down View -->
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedDomain.domain.toUpperCase()} ANALYSIS</h4>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="detail-table-container">
						<table class="detail-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>REGION</th>
									<th>INFRASTRUCTURE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
									<th>STATUS</th>
								</tr>
							</thead>
							<tbody>
								{#each domainDetails as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.region}</td>
										<td>{host.infrastructure_type}</td>
										<td>
											<span class="status-indicator {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '✓' : '✗'}
											</span>
										</td>
										<td>
											<span class="status-indicator {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? '✓' : '✗'}
											</span>
										</td>
										<td>
											<span class="domain-badge">MAPPED</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else if activeView === 'table'}
				<!-- Main Table View -->
				<div class="table-container">
					<table class="warfare-table">
						<thead>
							<tr>
								<th>DOMAIN TYPE</th>
								<th>HOST COUNT</th>
								<th>COVERAGE</th>
								<th>THREAT</th>
								<th>ACTION</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedDomains as item}
								{@const threat = getThreatLevel(item.domain)}
								<tr>
									<td class="domain-cell">
										<div class="cell-content">
											<span class="domain-indicator" style="background: {threat.color}"></span>
											<span>{item.domain.toUpperCase()}</span>
										</div>
									</td>
									<td class="center">{item.count.toLocaleString()}</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {getPercentage(item.count)}%; background: {threat.color}"></div>
											</div>
											<span class="coverage-text">{getPercentage(item.count)}%</span>
										</div>
									</td>
									<td class="center">
										<span class="threat-badge {threat.level.toLowerCase()}">{threat.level}</span>
									</td>
									<td class="center">
										<button class="drill-btn" on:click={() => drillDownDomain(item.domain, item.count)}>
											ANALYZE →
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
				
				<!-- Pagination -->
				<div class="pagination">
					<button 
						on:click={() => currentPage = Math.max(1, currentPage - 1)}
						disabled={currentPage === 1}
					>
						←
					</button>
					<span>Page {currentPage} of {totalPages}</span>
					<button 
						on:click={() => currentPage = Math.min(totalPages, currentPage + 1)}
						disabled={currentPage === totalPages}
					>
						→
					</button>
				</div>
			{:else}
				<!-- Grid View -->
				<div class="domain-grid">
					{#each paginatedDomains as item}
						{@const threat = getThreatLevel(item.domain)}
						<div class="domain-card" style="--card-color: {threat.color}">
							<div class="card-header">
								<span class="domain-type">{item.domain.toUpperCase()}</span>
								<span class="threat-level {threat.level.toLowerCase()}">{threat.level}</span>
							</div>
							<div class="card-metrics">
								<div class="metric-value">{item.count.toLocaleString()}</div>
								<div class="metric-label">HOSTS</div>
								<div class="metric-bar">
									<div class="bar-fill" style="width: {getPercentage(item.count)}%; background: {threat.color}"></div>
								</div>
							</div>
							<button class="card-action" on:click={() => drillDownDomain(item.domain, item.count)}>
								ANALYZE
							</button>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Right Panel: Visualizations -->
		<div class="viz-section">
			<!-- Domain Warfare Chart -->
			<div class="viz-card">
				<h4>DOMAIN WARFARE STATUS</h4>
				<div class="warfare-chart">
					<svg viewBox="0 0 300 200">
						<!-- Background grid -->
						<defs>
							<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
								<path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(0,255,255,0.1)" stroke-width="0.5"/>
							</pattern>
						</defs>
						<rect width="300" height="200" fill="url(#grid)"/>
						
						<!-- 1DC vs FEAD Battle visualization -->
						<circle cx="75" cy="100" r="50" fill="none" stroke="#ff00ff" stroke-width="2" opacity="0.6"/>
						<circle cx="225" cy="100" r="50" fill="none" stroke="#00ffff" stroke-width="2" opacity="0.6"/>
						
						{#if domainPercentages['1dc_only']}
							<circle cx="75" cy="100" r={domainPercentages['1dc_only'] / 2} fill="#ff00ff" opacity="0.4"/>
						{/if}
						{#if domainPercentages['fead_only']}
							<circle cx="225" cy="100" r={domainPercentages['fead_only'] / 2} fill="#00ffff" opacity="0.4"/>
						{/if}
						
						<!-- Overlap for dual domain -->
						{#if domainPercentages['both_domains']}
							<circle cx="150" cy="100" r={domainPercentages['both_domains'] / 2} fill="#00ff85" opacity="0.6"/>
						{/if}
						
						<text x="75" y="100" text-anchor="middle" fill="#ff00ff" font-size="14" font-weight="bold">
							1DC
						</text>
						<text x="225" y="100" text-anchor="middle" fill="#00ffff" font-size="14" font-weight="bold">
							FEAD
						</text>
						<text x="150" y="180" text-anchor="middle" fill="white" font-size="10">
							{warfareStatus}
						</text>
					</svg>
				</div>
			</div>

			<!-- Coverage Analysis -->
			<div class="viz-card">
				<h4>COVERAGE ANALYSIS</h4>
				<div class="coverage-analysis">
					{#if data.domain_coverage}
						{#each Object.entries(data.domain_coverage) as [domain, coverage]}
							<div class="coverage-item">
								<div class="coverage-label">{domain.toUpperCase()}</div>
								<div class="coverage-stats">
									<div class="stat-item">
										<span class="stat-label">CMDB:</span>
										<span class="stat-value">{coverage.cmdb_coverage}%</span>
									</div>
									<div class="stat-item">
										<span class="stat-label">TANIUM:</span>
										<span class="stat-value">{coverage.tanium_coverage}%</span>
									</div>
									<div class="stat-item">
										<span class="stat-label">SPLUNK:</span>
										<span class="stat-value">{coverage.splunk_coverage}%</span>
									</div>
								</div>
								<div class="coverage-bar-mini">
									<div class="bar-fill" style="width: {(coverage.cmdb_coverage + coverage.tanium_coverage + coverage.splunk_coverage) / 3}%; background: linear-gradient(90deg, #ff00ff, #00ffff)"></div>
								</div>
							</div>
						{/each}
					{/if}
				</div>
			</div>

			<!-- Distribution Matrix -->
			<div class="viz-card">
				<h4>DISTRIBUTION MATRIX</h4>
				<div class="matrix-grid">
					{#each domainList.slice(0, 9) as item}
						{@const threat = getThreatLevel(item.domain)}
						<div class="matrix-cell" style="background: {threat.color}20; border-color: {threat.color}">
							<div class="cell-value">{getPercentage(item.count)}%</div>
							<div class="cell-label">{item.domain.substring(0, 8)}</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.domain-warfare-container {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
		color: #fff;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
	}

	.warfare-header {
		background: rgba(0, 0, 0, 0.8);
		border-bottom: 2px solid rgba(255, 0, 255, 0.3);
		padding: 0.8rem 1.2rem;
		backdrop-filter: blur(10px);
	}

	.header-content {
		max-width: 100%;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.title-section h1 {
		margin: 0;
		font-size: 1.3rem;
		color: #ff00ff;
		text-shadow: 0 0 15px rgba(255, 0, 255, 0.5);
		letter-spacing: 0.1em;
	}

	.title-section p {
		margin: 0.2rem 0 0 0;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.warfare-metrics {
		display: flex;
		gap: 0.8rem;
	}

	.metric-card {
		background: rgba(0, 255, 255, 0.05);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 6px;
		padding: 0.5rem 0.8rem;
		text-align: center;
		min-width: 100px;
	}

	.metric-card.critical {
		background: rgba(255, 0, 255, 0.05);
		border-color: rgba(255, 0, 255, 0.3);
	}

	.metric-card.success {
		background: rgba(0, 255, 133, 0.05);
		border-color: rgba(0, 255, 133, 0.3);
	}

	.metric-card.warning {
		background: rgba(255, 170, 0, 0.05);
		border-color: rgba(255, 170, 0, 0.3);
	}

	.metric-value {
		font-size: 1.2rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 10px currentColor;
	}

	.metric-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.2rem;
		letter-spacing: 0.05em;
	}

	.warfare-grid {
		flex: 1;
		display: flex;
		gap: 0.8rem;
		padding: 0.8rem;
		overflow: hidden;
		min-height: 0;
	}

	.table-section {
		flex: 2;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 8px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.viz-section {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		overflow-y: auto;
		min-width: 350px;
	}

	.section-header {
		padding: 0.8rem;
		border-bottom: 1px solid rgba(255, 0, 255, 0.2);
		background: rgba(255, 0, 255, 0.05);
	}

	.section-header h3 {
		margin: 0 0 0.5rem 0;
		font-size: 0.8rem;
		color: #ff00ff;
		letter-spacing: 0.05em;
	}

	.control-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
	}

	.search-input {
		flex: 1;
		max-width: 300px;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 0, 255, 0.3);
		border-radius: 4px;
		padding: 0.4rem;
		color: #fff;
		font-size: 0.75rem;
	}

	.search-input:focus {
		outline: none;
		border-color: #ff00ff;
		box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
	}

	.view-toggle {
		display: flex;
		gap: 0.3rem;
	}

	.toggle-btn {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 0, 255, 0.3);
		color: #ff00ff;
		padding: 0.3rem 0.6rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.65rem;
		transition: all 0.3s ease;
	}

	.toggle-btn.active,
	.toggle-btn:hover {
		background: rgba(255, 0, 255, 0.1);
		box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
	}

	.table-container {
		flex: 1;
		overflow: auto;
		padding: 0.5rem;
	}

	.warfare-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.75rem;
	}

	.warfare-table th {
		background: rgba(255, 0, 255, 0.1);
		color: #ff00ff;
		padding: 0.6rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.warfare-table td {
		padding: 0.5rem 0.6rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.8);
	}

	.warfare-table tr:hover {
		background: rgba(255, 0, 255, 0.05);
	}

	.domain-cell .cell-content {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.domain-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
		animation: pulse 2s infinite;
	}

	.center {
		text-align: center;
	}

	.coverage-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.coverage-bar {
		flex: 1;
		height: 6px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 3px;
		overflow: hidden;
		min-width: 100px;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.3s ease;
		box-shadow: 0 0 10px currentColor;
	}

	.coverage-text {
		font-size: 0.65rem;
		min-width: 45px;
		text-align: right;
	}

	.threat-badge {
		padding: 0.2rem 0.4rem;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 600;
	}

	.threat-badge.high {
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
	}

	.threat-badge.med {
		background: rgba(0, 255, 255, 0.2);
		color: #00ffff;
		border: 1px solid #00ffff;
	}

	.threat-badge.opt {
		background: rgba(0, 255, 133, 0.2);
		color: #00ff85;
		border: 1px solid #00ff85;
	}

	.threat-badge.low {
		background: rgba(0, 150, 255, 0.2);
		color: #0096ff;
		border: 1px solid #0096ff;
	}

	.drill-btn {
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid #ff00ff;
		color: #ff00ff;
		padding: 0.25rem 0.6rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.65rem;
		transition: all 0.3s ease;
	}

	.drill-btn:hover {
		background: rgba(255, 0, 255, 0.2);
		transform: translateX(2px);
		box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
	}

	.domain-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 0.8rem;
		padding: 0.8rem;
		overflow-y: auto;
	}

	.domain-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid var(--card-color);
		border-radius: 8px;
		padding: 1rem;
		transition: all 0.3s ease;
	}

	.domain-card:hover {
		transform: translateY(-3px);
		box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 15px var(--card-color);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.8rem;
	}

	.domain-type {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--card-color);
	}

	.card-metrics {
		text-align: center;
		margin-bottom: 0.8rem;
	}

	.metric-bar {
		height: 4px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 2px;
		overflow: hidden;
		margin-top: 0.5rem;
	}

	.bar-fill {
		height: 100%;
		transition: width 0.3s ease;
	}

	.card-action {
		width: 100%;
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid var(--card-color);
		color: var(--card-color);
		padding: 0.4rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.7rem;
		transition: all 0.3s ease;
	}

	.card-action:hover {
		background: rgba(255, 0, 255, 0.2);
	}

	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		padding: 0.8rem;
		border-top: 1px solid rgba(255, 0, 255, 0.2);
	}

	.pagination button {
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid #ff00ff;
		color: #ff00ff;
		padding: 0.4rem 0.8rem;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.3s ease;
		font-size: 0.7rem;
	}

	.pagination button:hover:not(:disabled) {
		background: rgba(255, 0, 255, 0.2);
	}

	.pagination button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.viz-card {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 8px;
		padding: 0.8rem;
	}

	.viz-card h4 {
		margin: 0 0 0.8rem 0;
		font-size: 0.75rem;
		color: #ff00ff;
		letter-spacing: 0.05em;
	}

	.warfare-chart {
		width: 100%;
		display: flex;
		justify-content: center;
	}

	.coverage-analysis {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.coverage-item {
		padding: 0.5rem;
		background: rgba(255, 0, 255, 0.05);
		border-radius: 4px;
	}

	.coverage-label {
		font-size: 0.7rem;
		color: #ff00ff;
		margin-bottom: 0.3rem;
		font-weight: 600;
	}

	.coverage-stats {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.3rem;
	}

	.stat-item {
		display: flex;
		gap: 0.3rem;
		font-size: 0.6rem;
	}

	.stat-label {
		color: rgba(255, 255, 255, 0.6);
	}

	.stat-value {
		color: #00ffff;
		font-weight: 600;
	}

	.coverage-bar-mini {
		height: 3px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 2px;
		overflow: hidden;
	}

	.matrix-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.4rem;
	}

	.matrix-cell {
		aspect-ratio: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		border: 1px solid;
		border-radius: 4px;
		padding: 0.4rem;
		font-size: 0.6rem;
	}

	.cell-value {
		font-size: 0.7rem;
		font-weight: 600;
		color: #fff;
	}

	.cell-label {
		font-size: 0.5rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.2rem;
	}

	.loading-matrix {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}

	.matrix-spinner {
		width: 40px;
		height: 40px;
		border: 3px solid rgba(255, 0, 255, 0.2);
		border-top-color: #ff00ff;
		border-radius: 50%;
		animation: spin 1s linear infinite;
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
		padding: 0.8rem;
		border-bottom: 1px solid rgba(255, 0, 102, 0.3);
		background: rgba(255, 0, 102, 0.05);
	}

	.drill-header h4 {
		margin: 0;
		color: #ff0066;
		font-size: 0.9rem;
	}

	.close-btn {
		background: transparent;
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.3s ease;
		font-size: 0.8rem;
	}

	.close-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: rotate(90deg);
	}

	.detail-table-container {
		flex: 1;
		overflow: auto;
		padding: 0.5rem;
	}

	.detail-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.7rem;
	}

	.detail-table th {
		background: rgba(255, 0, 102, 0.1);
		color: #ff0066;
		padding: 0.5rem;
		text-align: left;
		font-weight: 600;
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.detail-table td {
		padding: 0.4rem 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}

	.host-cell {
		font-family: monospace;
		color: #00ffff;
		font-size: 0.75rem;
	}

	.status-indicator {
		padding: 0.15rem 0.3rem;
		border-radius: 3px;
		font-size: 0.6rem;
		font-weight: 600;
	}

	.status-indicator.active {
		background: rgba(0, 255, 133, 0.2);
		color: #00ff85;
		border: 1px solid #00ff85;
	}

	.status-indicator.inactive {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.domain-badge {
		padding: 0.15rem 0.3rem;
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
		border-radius: 3px;
		font-size: 0.6rem;
		font-weight: 600;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	@media (max-width: 1200px) {
		.warfare-grid {
			flex-direction: column;
		}
		
		.viz-section {
			flex-direction: row;
			overflow-x: auto;
			min-width: auto;
		}
		
		.viz-card {
			min-width: 300px;
		}
	}

	@media (max-width: 768px) {
		.warfare-metrics {
			flex-wrap: wrap;
		}
		
		.metric-card {
			min-width: calc(50% - 0.4rem);
		}
	}
</style>