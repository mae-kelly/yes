<!-- SourceTables.svelte - Military Intelligence Tables -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 8;

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
	
	$: paginatedSources = filteredSources.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(filteredSources.length / itemsPerPage);
	$: maxFreq = filteredSources.length > 0 ? Math.max(...filteredSources.map(([,f]) => f)) : 1;

	function getThreatLevel(frequency) {
		if (!data.total_mentions) return { level: 'LOW', color: '#b8a678' };
		let percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRITICAL', color: '#8b4513' };
		if (percentage >= 10) return { level: 'HIGH', color: '#704214' };
		if (percentage >= 5) return { level: 'MEDIUM', color: '#5c4033' };
		return { level: 'LOW', color: '#b8a678' };
	}

	function getPercentage(frequency) {
		if (!data.total_mentions) return 0;
		return ((frequency / data.total_mentions) * 100).toFixed(2);
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

<div class="tables-container">
	<!-- Control Bar -->
	<div class="control-bar">
		<div class="section-header">
			<svg class="section-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
				<rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
				<line x1="3" y1="9" x2="21" y2="9" stroke="currentColor" stroke-width="2"/>
				<line x1="9" y1="9" x2="9" y2="21" stroke="currentColor" stroke-width="2"/>
			</svg>
			<h2>SOURCE INTELLIGENCE MATRIX</h2>
		</div>
		
		<div class="controls">
			<input 
				type="text" 
				bind:value={searchTerm}
				placeholder="Search sources..."
				class="search-input"
			/>
			
			<div class="stats">
				<div class="stat">
					<span class="stat-value">{(data.unique_sources || 0).toLocaleString()}</span>
					<span class="stat-label">SOURCES</span>
				</div>
				<div class="stat">
					<span class="stat-value">{(data.total_mentions || 0).toLocaleString()}</span>
					<span class="stat-label">MENTIONS</span>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content -->
	<div class="content-area">
		{#if loading && !selectedSource}
			<div class="loading-state">
				<div class="loader"></div>
				<p>ANALYZING DATA...</p>
			</div>
		{:else if selectedSource}
			<!-- Drill-down View -->
			<div class="drill-panel">
				<div class="drill-header">
					<h3>{selectedSource.source.toUpperCase()}</h3>
					<span class="drill-badge">{selectedSource.frequency} INSTANCES</span>
					<button class="close-btn" on:click={closeDetails}>
						<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
							<path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
						</svg>
					</button>
				</div>
				
				<div class="drill-table">
					<table>
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
							{#each hostDetails.slice(0, 10) as host}
								<tr>
									<td class="host-cell">{host.host}</td>
									<td>{host.region || 'Unknown'}</td>
									<td>{host.country || 'Unknown'}</td>
									<td>{host.infrastructure_type || 'Unknown'}</td>
									<td>
										<span class="badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
											{host.present_in_cmdb?.toLowerCase().includes('yes') ? '✓' : '✗'}
										</span>
									</td>
									<td>
										<span class="badge {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
											{host.tanium_coverage?.toLowerCase().includes('tanium') ? '✓' : '✗'}
										</span>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{:else}
			<!-- Grid View -->
			<div class="sources-grid">
				{#each paginatedSources as [source, frequency]}
					{@const threat = getThreatLevel(frequency)}
					<div class="source-card" on:click={() => drillDownSource(source, frequency)}>
						<div class="card-header">
							<span class="threat-level" style="background: {threat.color}20; border-color: {threat.color}">
								{threat.level}
							</span>
						</div>
						<div class="card-body">
							<div class="source-name">{source.toUpperCase()}</div>
							<div class="frequency-value">{frequency.toLocaleString()}</div>
							<div class="meter">
								<div class="meter-fill" style="width: {(frequency/maxFreq)*100}%; background: {threat.color}"></div>
							</div>
							<div class="percentage">{getPercentage(frequency)}%</div>
						</div>
					</div>
				{/each}
			</div>
			
			<!-- Pagination -->
			{#if totalPages > 1}
				<div class="pagination">
					<button 
						class="page-btn"
						on:click={() => currentPage = Math.max(1, currentPage - 1)}
						disabled={currentPage === 1}>
						◀
					</button>
					<span class="page-info">{currentPage} / {totalPages}</span>
					<button 
						class="page-btn"
						on:click={() => currentPage = Math.min(totalPages, currentPage + 1)}
						disabled={currentPage === totalPages}>
						▶
					</button>
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.tables-container {
		height: 100%;
		display: flex;
		flex-direction: column;
		background: #000;
		color: #fff;
		padding: 0.8rem;
		font-family: 'JetBrains Mono', monospace;
	}

	/* Control Bar */
	.control-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.6rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		margin-bottom: 0.8rem;
		flex-shrink: 0;
	}

	.section-header {
		display: flex;
		align-items: center;
		gap: 0.6rem;
	}

	.section-icon {
		width: 20px;
		height: 20px;
		color: #0a4f3c;
	}

	.section-header h2 {
		margin: 0;
		font-size: 0.8rem;
		color: #0a4f3c;
		letter-spacing: 0.1em;
		font-weight: 600;
	}

	.controls {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.search-input {
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid #1e3a5f;
		border-radius: 3px;
		padding: 0.3rem 0.6rem;
		color: #fff;
		font-size: 0.7rem;
		width: 200px;
		font-family: inherit;
	}

	.search-input:focus {
		outline: none;
		border-color: #0a4f3c;
		box-shadow: 0 0 6px rgba(10, 79, 60, 0.3);
	}

	.stats {
		display: flex;
		gap: 1.5rem;
	}

	.stat {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.stat-value {
		font-size: 0.9rem;
		font-weight: 700;
		color: #0a4f3c;
		text-shadow: 0 0 6px rgba(10, 79, 60, 0.3);
	}

	.stat-label {
		font-size: 0.5rem;
		color: #b8a678;
		letter-spacing: 0.1em;
		margin-top: 0.1rem;
	}

	/* Content Area */
	.content-area {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		min-height: 0;
	}

	/* Grid */
	.sources-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 0.6rem;
		flex: 1;
		overflow-y: auto;
		padding: 0.2rem;
	}

	.source-card {
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid #1e3a5f;
		border-radius: 4px;
		padding: 0.6rem;
		cursor: pointer;
		transition: all 0.2s ease;
		height: fit-content;
	}

	.source-card:hover {
		border-color: #0a4f3c;
		box-shadow: 0 4px 12px rgba(10, 79, 60, 0.2);
		background: rgba(10, 79, 60, 0.05);
	}

	.card-header {
		margin-bottom: 0.4rem;
	}

	.threat-level {
		display: inline-block;
		font-size: 0.5rem;
		padding: 0.15rem 0.3rem;
		border-radius: 2px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border: 1px solid;
	}

	.card-body {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.source-name {
		font-size: 0.65rem;
		font-weight: 600;
		color: #fff;
		letter-spacing: 0.05em;
		line-height: 1.2;
		word-break: break-word;
	}

	.frequency-value {
		font-size: 1rem;
		font-weight: 700;
		color: #0a4f3c;
		text-shadow: 0 0 6px rgba(10, 79, 60, 0.3);
	}

	.meter {
		width: 100%;
		height: 3px;
		background: rgba(30, 58, 95, 0.2);
		border-radius: 2px;
		overflow: hidden;
	}

	.meter-fill {
		height: 100%;
		transition: width 0.3s ease;
	}

	.percentage {
		font-size: 0.6rem;
		color: #b8a678;
		text-align: right;
	}

	/* Drill Panel */
	.drill-panel {
		flex: 1;
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.drill-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.6rem;
		background: rgba(10, 79, 60, 0.1);
		border-bottom: 1px solid #0a4f3c;
	}

	.drill-header h3 {
		margin: 0;
		color: #0a4f3c;
		font-size: 0.8rem;
		letter-spacing: 0.1em;
		flex: 1;
	}

	.drill-badge {
		padding: 0.2rem 0.4rem;
		background: rgba(30, 58, 95, 0.2);
		border: 1px solid #1e3a5f;
		border-radius: 2px;
		color: #b8a678;
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.close-btn {
		width: 24px;
		height: 24px;
		background: transparent;
		border: 1px solid #8b4513;
		color: #8b4513;
		border-radius: 2px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}

	.close-btn svg {
		width: 14px;
		height: 14px;
	}

	.close-btn:hover {
		background: rgba(139, 69, 19, 0.2);
	}

	.drill-table {
		flex: 1;
		overflow: auto;
		padding: 0.6rem;
	}

	.drill-table table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0 0.2rem;
	}

	.drill-table th {
		background: rgba(10, 79, 60, 0.15);
		color: #0a4f3c;
		padding: 0.4rem;
		text-align: left;
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		border: 1px solid rgba(10, 79, 60, 0.3);
	}

	.drill-table td {
		padding: 0.4rem;
		color: #fff;
		font-size: 0.65rem;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(30, 58, 95, 0.2);
	}

	.host-cell {
		font-family: 'Courier New', monospace;
		color: #b8a678;
	}

	.badge {
		padding: 0.1rem 0.25rem;
		border-radius: 2px;
		font-size: 0.55rem;
		font-weight: 600;
	}

	.badge.active {
		background: rgba(10, 79, 60, 0.2);
		color: #0a4f3c;
		border: 1px solid #0a4f3c;
	}

	.badge.inactive {
		background: rgba(139, 69, 19, 0.2);
		color: #8b4513;
		border: 1px solid #8b4513;
	}

	/* Loading */
	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.8rem;
	}

	.loader {
		width: 32px;
		height: 32px;
		border: 3px solid rgba(10, 79, 60, 0.2);
		border-top-color: #0a4f3c;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.loading-state p {
		color: #0a4f3c;
		font-size: 0.7rem;
		letter-spacing: 0.1em;
	}

	/* Pagination */
	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 0.8rem;
		padding: 0.6rem 0 0.2rem 0;
		margin-top: auto;
	}

	.page-btn {
		width: 28px;
		height: 28px;
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid #1e3a5f;
		color: #b8a678;
		border-radius: 2px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
		font-size: 0.7rem;
		font-family: inherit;
	}

	.page-btn:hover:not(:disabled) {
		background: rgba(10, 79, 60, 0.1);
		border-color: #0a4f3c;
		color: #fff;
	}

	.page-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.page-info {
		padding: 0.2rem 0.6rem;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid #1e3a5f;
		border-radius: 2px;
		color: #b8a678;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	/* Scrollbar */
	::-webkit-scrollbar {
		width: 6px;
		height: 6px;
	}

	::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.3);
		border-radius: 3px;
	}

	::-webkit-scrollbar-thumb {
		background: #0a4f3c;
		border-radius: 3px;
	}

	::-webkit-scrollbar-thumb:hover {
		background: #1e3a5f;
	}

	/* Responsive */
	@media (max-width: 1200px) {
		.sources-grid {
			grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		}
		
		.controls {
			gap: 0.6rem;
		}
		
		.search-input {
			width: 150px;
		}
	}

	@media (max-width: 768px) {
		.control-bar {
			flex-direction: column;
			align-items: flex-start;
			gap: 0.6rem;
		}
		
		.sources-grid {
			grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
			gap: 0.4rem;
		}
		
		.controls {
			width: 100%;
			justify-content: space-between;
		}
	}
</style>