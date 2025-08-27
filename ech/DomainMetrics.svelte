<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedDomain = null;
	let domainHosts = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 12;
	let viewMode = 'table';

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
			.map(([domain, count]) => ({ domain, count, percentage: data.domain_percentages?.[domain] || 0 }))
			.sort((a, b) => b.count - a.count) : [];
	
	$: paginatedDomains = domainList.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(domainList.length / itemsPerPage);

	function getDomainColor(domain) {
		if (domain === '1dc_only') return '#ff00ff';
		if (domain === 'fead_only') return '#00ffff';
		if (domain === 'both_domains') return '#00ff85';
		return '#0096ff';
	}

	function getDomainStatus(domain) {
		if (domain === 'both_domains') return 'SYNCED';
		if (domain === '1dc_only') return '1DC';
		if (domain === 'fead_only') return 'FEAD';
		return 'UNKNOWN';
	}

	async function drillDownDomain(domain, count) {
		selectedDomain = { domain, count };
		loading = true;
		
		try {
			let searchQuery = domain === '1dc_only' ? '1dc' : domain === 'fead_only' ? 'fead' : domain;
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(searchQuery)}`);
			let result = await response.json();
			domainHosts = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Domain drill-down error:', err);
			domainHosts = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedDomain = null;
		domainHosts = [];
	}
</script>

<div class="warfare-dashboard">
	<!-- Quantum Header -->
	<div class="quantum-header">
		<div class="warfare-core">
			<div class="core-rings">
				<div class="ring ring-1"></div>
				<div class="ring ring-2"></div>
				<div class="ring ring-3"></div>
			</div>
			<div class="core-symbol">◆</div>
		</div>
		<div class="warfare-info">
			<h1>DOMAIN WARFARE MATRIX</h1>
			<p>1DC vs FEAD QUANTUM ANALYSIS</p>
		</div>
		<div class="warfare-metrics">
			<div class="metric-cell">
				<div class="metric-value">{(data.total_hosts || 0).toLocaleString()}</div>
				<div class="metric-label">TOTAL</div>
			</div>
			<div class="metric-cell dc">
				<div class="metric-value">{data.domain_percentages?.['1dc_only'] || 0}%</div>
				<div class="metric-label">1DC</div>
			</div>
			<div class="metric-cell fead">
				<div class="metric-value">{data.domain_percentages?.['fead_only'] || 0}%</div>
				<div class="metric-label">FEAD</div>
			</div>
			<div class="metric-cell synced">
				<div class="metric-value">{data.domain_percentages?.['both_domains'] || 0}%</div>
				<div class="metric-label">DUAL</div>
			</div>
			<div class="metric-cell status">
				<div class="status-indicator">{data.warfare_status || 'ANALYZING'}</div>
			</div>
		</div>
	</div>

	<!-- Main Grid -->
	<div class="warfare-grid">
		<!-- Left Panel: Data Table -->
		<div class="table-section">
			<div class="section-header">
				<h3>DOMAIN INTELLIGENCE</h3>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search domains..."
						class="search-input"
					/>
					<div class="view-toggle">
						<button class="toggle-btn {viewMode === 'table' ? 'active' : ''}" on:click={() => viewMode = 'table'}>
							TABLE
						</button>
						<button class="toggle-btn {viewMode === 'grid' ? 'active' : ''}" on:click={() => viewMode = 'grid'}>
							MATRIX
						</button>
					</div>
				</div>
			</div>
			
			{#if loading && !selectedDomain}
				<div class="loading-state">
					<div class="quantum-spinner">
						<div class="spinner-ring"></div>
						<div class="spinner-core"></div>
					</div>
					<p>ANALYZING DOMAIN WARFARE...</p>
				</div>
			{:else if selectedDomain}
				<!-- Drill-down View -->
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedDomain.domain.toUpperCase().replace('_', ' ')}</h4>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>REGION</th>
									<th>INFRA</th>
									<th>CMDB</th>
									<th>TANIUM</th>
									<th>STATUS</th>
								</tr>
							</thead>
							<tbody>
								{#each domainHosts as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.region || 'Unknown'}</td>
										<td>{host.infrastructure_type || 'Unknown'}</td>
										<td>
											<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '✓' : '✗'}
											</span>
										</td>
										<td>
											<span class="status-badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? '✓' : '✗'}
											</span>
										</td>
										<td>
											<span class="domain-badge" style="background: {getDomainColor(selectedDomain.domain)}20; color: {getDomainColor(selectedDomain.domain)}">
												{getDomainStatus(selectedDomain.domain)}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else if viewMode === 'table'}
				<!-- Main Table -->
				<div class="table-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>DOMAIN</th>
								<th>HOSTS</th>
								<th>COVERAGE</th>
								<th>STATUS</th>
								<th>ACTION</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedDomains as item}
								<tr>
									<td class="domain-cell">
										<div class="cell-content">
											<span class="indicator" style="background: {getDomainColor(item.domain)}"></span>
											<span>{item.domain.toUpperCase().replace(/_/g, ' ')}</span>
										</div>
									</td>
									<td class="center">{item.count.toLocaleString()}</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {item.percentage}%; background: {getDomainColor(item.domain)}"></div>
											</div>
											<span class="coverage-text">{item.percentage}%</span>
										</div>
									</td>
									<td class="center">
										<span class="status-label" style="color: {getDomainColor(item.domain)}">
											{getDomainStatus(item.domain)}
										</span>
									</td>
									<td class="center">
										<button class="drill-btn" style="border-color: {getDomainColor(item.domain)}" 
											on:click={() => drillDownDomain(item.domain, item.count)}>
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
				<div class="matrix-container">
					{#each paginatedDomains as item}
						<div class="domain-card" style="--domain-color: {getDomainColor(item.domain)}" 
							on:click={() => drillDownDomain(item.domain, item.count)}>
							<div class="card-header">
								<span class="domain-icon">⬢</span>
								<span class="domain-type">{getDomainStatus(item.domain)}</span>
							</div>
							<div class="card-body">
								<div class="domain-name">{item.domain.replace(/_/g, ' ').toUpperCase()}</div>
								<div class="domain-count">{item.count.toLocaleString()}</div>
								<div class="progress-ring">
									<svg width="60" height="60">
										<circle cx="30" cy="30" r="25" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="3"/>
										<circle cx="30" cy="30" r="25" fill="none" 
											stroke={getDomainColor(item.domain)} 
											stroke-width="3"
											stroke-dasharray={`${item.percentage * 1.57} 157`}
											transform="rotate(-90 30 30)"/>
									</svg>
									<div class="ring-value">{item.percentage}%</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Right Panel: Visualizations -->
		<div class="viz-section">
			<!-- Domain Warfare Chart -->
			<div class="viz-card warfare-chart">
				<h4>WARFARE VISUALIZATION</h4>
				<div class="battle-field">
					<svg viewBox="0 0 300 200">
						<defs>
							<radialGradient id="dcGrad">
								<stop offset="0%" style="stop-color:#ff00ff;stop-opacity:0.8" />
								<stop offset="100%" style="stop-color:#ff00ff;stop-opacity:0" />
							</radialGradient>
							<radialGradient id="feadGrad">
								<stop offset="0%" style="stop-color:#00ffff;stop-opacity:0.8" />
								<stop offset="100%" style="stop-color:#00ffff;stop-opacity:0" />
							</radialGradient>
							<radialGradient id="dualGrad">
								<stop offset="0%" style="stop-color:#00ff85;stop-opacity:0.8" />
								<stop offset="100%" style="stop-color:#00ff85;stop-opacity:0" />
							</radialGradient>
						</defs>
						
						<!-- 1DC Domain -->
						<circle cx="75" cy="100" r={Math.sqrt((data.domain_distribution?.['1dc_only'] || 0) / 100) * 50} 
							fill="url(#dcGrad)" class="pulse-animation"/>
						<text x="75" y="100" text-anchor="middle" fill="#ff00ff" font-size="14" font-weight="bold">
							1DC
						</text>
						<text x="75" y="115" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="10">
							{data.domain_distribution?.['1dc_only'] || 0}
						</text>
						
						<!-- FEAD Domain -->
						<circle cx="225" cy="100" r={Math.sqrt((data.domain_distribution?.['fead_only'] || 0) / 100) * 50} 
							fill="url(#feadGrad)" class="pulse-animation" style="animation-delay: 0.5s"/>
						<text x="225" y="100" text-anchor="middle" fill="#00ffff" font-size="14" font-weight="bold">
							FEAD
						</text>
						<text x="225" y="115" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="10">
							{data.domain_distribution?.['fead_only'] || 0}
						</text>
						
						<!-- Dual Domain -->
						<circle cx="150" cy="100" r={Math.sqrt((data.domain_distribution?.['both_domains'] || 0) / 100) * 30} 
							fill="url(#dualGrad)" class="pulse-animation" style="animation-delay: 1s"/>
						<text x="150" y="100" text-anchor="middle" fill="#00ff85" font-size="12" font-weight="bold">
							DUAL
						</text>
						
						<!-- Status -->
						<text x="150" y="180" text-anchor="middle" fill="#ff00ff" font-size="12" font-weight="bold" class="glow-text">
							{data.warfare_status || 'ANALYZING'}
						</text>
					</svg>
				</div>
			</div>

			<!-- Coverage Matrix -->
			<div class="viz-card">
				<h4>SECURITY COVERAGE</h4>
				<div class="coverage-matrix">
					{#if data.domain_coverage}
						{#each Object.entries(data.domain_coverage) as [domain, coverage]}
							<div class="coverage-item">
								<div class="coverage-label">{domain.replace(/_/g, ' ').toUpperCase()}</div>
								<div class="coverage-bars">
									<div class="bar-row">
										<span class="bar-label">CMDB</span>
										<div class="mini-bar">
											<div class="mini-fill" style="width: {coverage.cmdb_coverage || 0}%; background: #ff00ff"></div>
										</div>
										<span class="bar-value">{coverage.cmdb_coverage || 0}%</span>
									</div>
									<div class="bar-row">
										<span class="bar-label">TANIUM</span>
										<div class="mini-bar">
											<div class="mini-fill" style="width: {coverage.tanium_coverage || 0}%; background: #00ffff"></div>
										</div>
										<span class="bar-value">{coverage.tanium_coverage || 0}%</span>
									</div>
									<div class="bar-row">
										<span class="bar-label">SPLUNK</span>
										<div class="mini-bar">
											<div class="mini-fill" style="width: {coverage.splunk_coverage || 0}%; background: #00ff85"></div>
										</div>
										<span class="bar-value">{coverage.splunk_coverage || 0}%</span>
									</div>
								</div>
							</div>
						{/each}
					{/if}
				</div>
			</div>

			<!-- Domain Distribution -->
			<div class="viz-card">
				<h4>DISTRIBUTION MATRIX</h4>
				<div class="distribution-grid">
					{#each domainList as item}
						<div class="dist-cell" style="--cell-color: {getDomainColor(item.domain)}">
							<div class="dist-value">{item.percentage}%</div>
							<div class="dist-label">{item.domain.substring(0, 4).toUpperCase()}</div>
							<div class="dist-bar" style="height: {item.percentage}%"></div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.warfare-dashboard {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, #0a0a0a 0%, #1a0033 100%);
		color: #fff;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
	}

	.quantum-header {
		background: rgba(0, 0, 0, 0.8);
		border-bottom: 2px solid rgba(255, 0, 255, 0.3);
		padding: 0.8rem 1rem;
		backdrop-filter: blur(20px);
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-shrink: 0;
		height: 80px;
	}

	.warfare-core {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 60px;
		height: 60px;
		position: relative;
	}

	.core-rings {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.ring {
		position: absolute;
		border-radius: 50%;
		border: 2px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: ringRotate 10s linear infinite;
	}

	.ring-1 {
		width: 60px;
		height: 60px;
		border-color: #ff00ff;
		opacity: 0.8;
	}

	.ring-2 {
		width: 45px;
		height: 45px;
		border-color: #00ffff;
		opacity: 0.6;
		animation-direction: reverse;
	}

	.ring-3 {
		width: 30px;
		height: 30px;
		border-color: #00ff85;
		opacity: 0.4;
	}

	.core-symbol {
		position: relative;
		z-index: 3;
		font-size: 1.5rem;
		color: #ff00ff;
		text-shadow: 0 0 20px #ff00ff;
		animation: symbolPulse 3s ease-in-out infinite;
	}

	.warfare-info {
		flex: 1;
		margin-left: 1rem;
	}

	.warfare-info h1 {
		margin: 0;
		font-size: 1.2rem;
		color: #ff00ff;
		text-shadow: 0 0 15px rgba(255, 0, 255, 0.5);
		letter-spacing: 0.1em;
	}

	.warfare-info p {
		margin: 0.2rem 0 0 0;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.warfare-metrics {
		display: flex;
		gap: 0.8rem;
	}

	.metric-cell {
		background: rgba(255, 0, 255, 0.05);
		border: 1px solid rgba(255, 0, 255, 0.3);
		border-radius: 6px;
		padding: 0.5rem 0.8rem;
		text-align: center;
		min-width: 80px;
	}

	.metric-cell.dc {
		background: rgba(255, 0, 255, 0.1);
		border-color: #ff00ff;
	}

	.metric-cell.fead {
		background: rgba(0, 255, 255, 0.1);
		border-color: #00ffff;
	}

	.metric-cell.synced {
		background: rgba(0, 255, 133, 0.1);
		border-color: #00ff85;
	}

	.metric-cell.status {
		background: rgba(255, 170, 0, 0.05);
		border-color: rgba(255, 170, 0, 0.3);
		min-width: 120px;
	}

	.metric-value {
		font-size: 1.1rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 10px currentColor;
	}

	.metric-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.1rem;
		letter-spacing: 0.05em;
	}

	.status-indicator {
		font-size: 0.8rem;
		color: #ffaa00;
		font-weight: 700;
		text-shadow: 0 0 10px #ffaa00;
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
		gap: 0.6rem;
		overflow-y: auto;
		min-width: 320px;
	}

	.section-header {
		padding: 0.6rem 0.8rem;
		border-bottom: 1px solid rgba(255, 0, 255, 0.2);
		background: rgba(255, 0, 255, 0.05);
	}

	.section-header h3 {
		margin: 0 0 0.4rem 0;
		font-size: 0.8rem;
		color: #ff00ff;
		letter-spacing: 0.05em;
		text-shadow: 0 0 10px rgba(255, 0, 255, 0.5);
	}

	.controls {
		display: flex;
		gap: 0.6rem;
		align-items: center;
	}

	.search-input {
		flex: 1;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 0, 255, 0.3);
		border-radius: 4px;
		padding: 0.3rem 0.6rem;
		color: #fff;
		font-size: 0.7rem;
	}

	.search-input:focus {
		outline: none;
		border-color: #ff00ff;
		box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
	}

	.view-toggle {
		display: flex;
		gap: 0.2rem;
	}

	.toggle-btn {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 0, 255, 0.3);
		color: rgba(255, 255, 255, 0.7);
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.65rem;
		transition: all 0.3s ease;
	}

	.toggle-btn.active {
		background: rgba(255, 0, 255, 0.1);
		border-color: #ff00ff;
		color: #ff00ff;
		text-shadow: 0 0 5px #ff00ff;
	}

	.table-container {
		flex: 1;
		overflow: auto;
		padding: 0.5rem;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.75rem;
	}

	.data-table th {
		background: rgba(255, 0, 255, 0.1);
		color: #ff00ff;
		padding: 0.5rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
		z-index: 10;
		text-shadow: 0 0 5px rgba(255, 0, 255, 0.5);
	}

	.data-table td {
		padding: 0.4rem 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.8);
	}

	.data-table tr:hover {
		background: rgba(255, 0, 255, 0.05);
	}

	.domain-cell .cell-content {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
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
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 10px currentColor;
	}

	.coverage-text {
		font-size: 0.65rem;
		min-width: 40px;
		text-align: right;
	}

	.status-label {
		font-weight: 600;
		text-shadow: 0 0 5px currentColor;
		font-size: 0.7rem;
	}

	.drill-btn {
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid;
		color: #ff00ff;
		padding: 0.2rem 0.5rem;
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

	.matrix-container {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
		gap: 0.8rem;
		padding: 0.8rem;
		overflow-y: auto;
		flex: 1;
	}

	.domain-card {
		background: rgba(0, 0, 0, 0.6);
		border: 2px solid var(--domain-color);
		border-radius: 8px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		text-align: center;
	}

	.domain-card:hover {
		transform: translateY(-3px) scale(1.02);
		box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5), 0 0 30px var(--domain-color);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.domain-icon {
		font-size: 1.2rem;
		color: var(--domain-color);
		animation: iconFloat 3s ease-in-out infinite;
	}

	.domain-type {
		font-size: 0.6rem;
		padding: 0.15rem 0.3rem;
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid var(--domain-color);
		border-radius: 3px;
		color: var(--domain-color);
		font-weight: 600;
	}

	.card-body {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.domain-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
		font-weight: 600;
	}

	.domain-count {
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--domain-color);
		text-shadow: 0 0 15px var(--domain-color);
	}

	.progress-ring {
		position: relative;
		width: 60px;
		height: 60px;
		margin: 0 auto;
	}

	.ring-value {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 0.7rem;
		font-weight: 600;
		color: var(--domain-color);
		text-shadow: 0 0 5px var(--domain-color);
	}

	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		padding: 0.5rem;
		border-top: 1px solid rgba(255, 0, 255, 0.2);
		background: rgba(0, 0, 0, 0.3);
	}

	.pagination button {
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid #ff00ff;
		color: #ff00ff;
		padding: 0.3rem 0.6rem;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.3s ease;
		font-size: 0.65rem;
	}

	.pagination button:hover:not(:disabled) {
		background: rgba(255, 0, 255, 0.2);
		transform: scale(1.05);
	}

	.pagination button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.pagination span {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.viz-card {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 6px;
		padding: 0.6rem;
	}

	.viz-card h4 {
		margin: 0 0 0.5rem 0;
		font-size: 0.7rem;
		color: #ff00ff;
		letter-spacing: 0.05em;
		text-align: center;
		text-shadow: 0 0 10px rgba(255, 0, 255, 0.5);
	}

	.battle-field {
		width: 100%;
		display: flex;
		justify-content: center;
	}

	.pulse-animation {
		animation: pulse 3s ease-in-out infinite;
	}

	.glow-text {
		animation: textGlow 2s ease-in-out infinite;
	}

	.coverage-matrix {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.coverage-item {
		background: rgba(255, 0, 255, 0.05);
		border-radius: 4px;
		padding: 0.5rem;
	}

	.coverage-label {
		font-size: 0.65rem;
		color: #ff00ff;
		margin-bottom: 0.3rem;
		font-weight: 600;
		text-shadow: 0 0 5px rgba(255, 0, 255, 0.5);
	}

	.coverage-bars {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.bar-row {
		display: grid;
		grid-template-columns: 50px 1fr 40px;
		align-items: center;
		gap: 0.3rem;
	}

	.bar-label {
		font-size: 0.55rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.mini-bar {
		height: 4px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 2px;
		overflow: hidden;
	}

	.mini-fill {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 5px currentColor;
	}

	.bar-value {
		font-size: 0.55rem;
		color: rgba(255, 255, 255, 0.8);
		text-align: right;
	}

	.distribution-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.5rem;
		height: 100px;
	}

	.dist-cell {
		position: relative;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid var(--cell-color);
		border-radius: 4px;
		padding: 0.3rem;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		align-items: center;
		overflow: hidden;
	}

	.dist-bar {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		background: linear-gradient(180deg, var(--cell-color), transparent);
		opacity: 0.3;
		transition: height 0.5s ease;
	}

	.dist-value {
		font-size: 0.7rem;
		font-weight: 600;
		color: var(--cell-color);
		text-shadow: 0 0 5px var(--cell-color);
		z-index: 1;
	}

	.dist-label {
		font-size: 0.5rem;
		color: rgba(255, 255, 255, 0.6);
		z-index: 1;
	}

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}

	.quantum-spinner {
		width: 60px;
		height: 60px;
		position: relative;
	}

	.spinner-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 3px solid rgba(255, 0, 255, 0.2);
		border-top-color: #ff00ff;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.spinner-core {
		position: absolute;
		width: 30px;
		height: 30px;
		background: radial-gradient(circle, #ff00ff, transparent);
		border-radius: 50%;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: corePulse 2s ease-in-out infinite;
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
		padding: 0.6rem 0.8rem;
		border-bottom: 1px solid rgba(255, 0, 255, 0.3);
		background: rgba(255, 0, 255, 0.05);
	}

	.drill-header h4 {
		margin: 0;
		color: #ff00ff;
		font-size: 0.8rem;
		text-shadow: 0 0 10px rgba(255, 0, 255, 0.5);
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
		font-size: 0.7rem;
	}

	.close-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: rotate(90deg);
	}

	.host-cell {
		font-family: monospace;
		color: #00ffff;
		font-size: 0.7rem;
	}

	.status-badge {
		padding: 0.1rem 0.3rem;
		border-radius: 3px;
		font-size: 0.6rem;
		font-weight: 600;
	}

	.status-badge.active {
		background: rgba(0, 255, 133, 0.2);
		color: #00ff85;
		border: 1px solid #00ff85;
	}

	.status-badge.inactive {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.domain-badge {
		padding: 0.15rem 0.4rem;
		border: 1px solid;
		border-radius: 3px;
		font-size: 0.6rem;
		font-weight: 600;
	}

	@keyframes ringRotate {
		from { transform: translate(-50%, -50%) rotate(0deg); }
		to { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes symbolPulse {
		0%, 100% { transform: scale(1); opacity: 0.9; }
		50% { transform: scale(1.1); opacity: 1; }
	}

	@keyframes pulse {
		0%, 100% { opacity: 0.8; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.05); }
	}

	@keyframes textGlow {
		0%, 100% { text-shadow: 0 0 10px currentColor; }
		50% { text-shadow: 0 0 20px currentColor, 0 0 30px currentColor; }
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@keyframes corePulse {
		0%, 100% { opacity: 0.6; }
		50% { opacity: 1; }
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-3px); }
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
			min-width: 280px;
		}
	}

	@media (max-width: 768px) {
		.warfare-metrics {
			flex-wrap: wrap;
		}
		
		.metric-cell {
			min-width: calc(50% - 0.4rem);
		}
	}
</style>