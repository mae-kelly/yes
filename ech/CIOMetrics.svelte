<!-- CIOMetrics.svelte - Enhanced with Perfect Screen Fit and 10x Cooler -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCIO = null;
	let cioDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 10;
	let viewMode = 'table';
	let hoveredCIO = null;

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/cio_metrics');
			let result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			console.error('CIO metrics error:', err);
			loading = false;
		}
	});

	$: filteredCIOs = data.operative_intelligence ? 
		Object.entries(data.operative_intelligence)
			.filter(([cio]) => cio.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: paginatedCIOs = filteredCIOs.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(filteredCIOs.length / itemsPerPage);

	$: maxCount = filteredCIOs.length > 0 ? Math.max(...filteredCIOs.map(([,c]) => c)) : 1;

	function getThreatLevel(count) {
		if (!maxCount) return { level: 'LOW', color: '#00ffff', intensity: 0.3 };
		let percentage = (count / maxCount) * 100;
		if (percentage >= 75) return { level: 'EXECUTIVE', color: '#ff00ff', intensity: 1.0 };
		if (percentage >= 50) return { level: 'SENIOR', color: '#ff0066', intensity: 0.8 };
		if (percentage >= 25) return { level: 'DIRECTOR', color: '#ffaa00', intensity: 0.6 };
		return { level: 'MANAGER', color: '#00ffff', intensity: 0.4 };
	}

	function getPercentage(count) {
		let total = Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
	}

	async function drillDownCIO(cio, count) {
		selectedCIO = { cio, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(cio)}`);
			let result = await response.json();
			cioDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('CIO drill-down error:', err);
			cioDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedCIO = null;
		cioDetails = [];
	}

	$: threatDistribution = filteredCIOs.reduce((acc, [_, count]) => {
		let level = getThreatLevel(count).level;
		acc[level] = (acc[level] || 0) + 1;
		return acc;
	}, {});

	$: topCIOs = filteredCIOs.slice(0, 5);
</script>

<div class="cio-dashboard">
	<!-- Header Section -->
	<div class="header-section">
		<div class="header-content">
			<div class="title-block">
				<div class="neural-icon">
					<div class="icon-rings">
						<div class="ring ring-1"></div>
						<div class="ring ring-2"></div>
						<div class="ring ring-3"></div>
					</div>
					<div class="icon-core">◓</div>
				</div>
				<div class="title-text">
					<h1>CIO INTELLIGENCE MATRIX</h1>
					<p>Executive Leadership Asset Control</p>
				</div>
			</div>
			<div class="metrics-row">
				<div class="metric-card">
					<div class="metric-value">{filteredCIOs.length}</div>
					<div class="metric-label">EXECUTIVES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL ASSETS</div>
				</div>
				<div class="metric-card primary">
					<div class="metric-value">{filteredCIOs[0] ? filteredCIOs[0][0].toUpperCase() : 'N/A'}</div>
					<div class="metric-label">PRIMARY CIO</div>
				</div>
				<div class="metric-card critical">
					<div class="metric-value">{threatDistribution['EXECUTIVE'] || 0}</div>
					<div class="metric-label">EXECUTIVE LEVEL</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content Area -->
	<div class="main-content">
		<!-- Left Panel: Table -->
		<div class="table-panel">
			<div class="panel-header">
				<h3>EXECUTIVE ANALYSIS</h3>
				<div class="controls">
					<div class="search-bar">
						<input 
							type="text" 
							bind:value={searchTerm}
							placeholder="Search executives..."
							class="search-input"
						/>
						<div class="search-icon">🔍</div>
					</div>
					<div class="view-toggle">
						<button class="toggle-btn {viewMode === 'table' ? 'active' : ''}" on:click={() => viewMode = 'table'}>
							<span class="btn-icon">▦</span> TABLE
						</button>
						<button class="toggle-btn {viewMode === 'grid' ? 'active' : ''}" on:click={() => viewMode = 'grid'}>
							<span class="btn-icon">▣</span> GRID
						</button>
					</div>
				</div>
			</div>
			
			{#if loading && !selectedCIO}
				<div class="loading-state">
					<div class="quantum-loader">
						<div class="loader-core"></div>
						<div class="loader-ring"></div>
					</div>
					<p>SCANNING EXECUTIVE MATRIX...</p>
				</div>
			{:else if selectedCIO}
				<!-- Drill-down View -->
				<div class="drill-view">
					<div class="drill-header">
						<h4>{selectedCIO.cio.toUpperCase()}</h4>
						<div class="drill-stats">
							<span class="stat-badge">{selectedCIO.count.toLocaleString()} ASSETS</span>
							<span class="stat-badge">{getPercentage(selectedCIO.count)}% CONTROL</span>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>HOST</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>INFRASTRUCTURE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
									<th>STATUS</th>
								</tr>
							</thead>
							<tbody>
								{#each cioDetails as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.region || 'Unknown'}</td>
										<td>{host.country || 'Unknown'}</td>
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
											<span class="exec-badge">CONTROLLED</span>
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
								<th>EXECUTIVE</th>
								<th>ASSETS</th>
								<th>COVERAGE</th>
								<th>LEVEL</th>
								<th>ACTION</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedCIOs as [cio, count]}
								<tr on:mouseenter={() => hoveredCIO = cio} on:mouseleave={() => hoveredCIO = null}>
									<td class="cio-cell">
										<div class="cell-content">
											<span class="indicator pulse" style="background: {getThreatLevel(count).color}"></span>
											<div class="cio-info">
												<span class="cio-name">{cio.toUpperCase()}</span>
												<span class="cio-title">Chief Information Officer</span>
											</div>
										</div>
									</td>
									<td class="center">
										<div class="asset-display">
											<span class="asset-count">{count.toLocaleString()}</span>
											<div class="mini-bar">
												<div class="mini-fill" style="width: {(count/maxCount)*100}%; background: {getThreatLevel(count).color}"></div>
											</div>
										</div>
									</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {getPercentage(count)}%; background: {getThreatLevel(count).color}">
													<span class="coverage-glow"></span>
												</div>
											</div>
											<span class="coverage-text">{getPercentage(count)}%</span>
										</div>
									</td>
									<td class="center">
										<span class="threat-badge {getThreatLevel(count).level.toLowerCase()}">{getThreatLevel(count).level}</span>
									</td>
									<td class="center">
										<button class="drill-btn" on:click={() => drillDownCIO(cio, count)}>
											ACCESS →
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
						class="page-btn"
					>
						◀
					</button>
					<div class="page-info">
						<span class="current-page">{currentPage}</span>
						<span class="page-separator">/</span>
						<span class="total-pages">{totalPages}</span>
					</div>
					<button 
						on:click={() => currentPage = Math.min(totalPages, currentPage + 1)}
						disabled={currentPage === totalPages}
						class="page-btn"
					>
						▶
					</button>
				</div>
			{:else}
				<!-- Grid View -->
				<div class="grid-container">
					{#each paginatedCIOs as [cio, count]}
						<div class="grid-card" 
							style="--card-color: {getThreatLevel(count).color}"
							on:click={() => drillDownCIO(cio, count)}
							on:mouseenter={() => hoveredCIO = cio}
							on:mouseleave={() => hoveredCIO = null}>
							<div class="card-header">
								<div class="executive-avatar">
									<div class="avatar-ring"></div>
									<span class="avatar-icon">👤</span>
								</div>
								<span class="level-indicator {getThreatLevel(count).level.toLowerCase()}">{getThreatLevel(count).level}</span>
							</div>
							<div class="card-body">
								<div class="executive-name">{cio.toUpperCase()}</div>
								<div class="executive-title">Chief Information Officer</div>
								<div class="asset-counter">
									<span class="counter-value">{count.toLocaleString()}</span>
									<span class="counter-label">ASSETS</span>
								</div>
								<div class="control-bar">
									<div class="control-fill" style="width: {getPercentage(count)}%; background: {getThreatLevel(count).color}"></div>
								</div>
								<div class="card-percentage">{getPercentage(count)}% CONTROL</div>
							</div>
							<div class="card-footer">
								<button class="access-btn">ACCESS PROFILE →</button>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Right Panel: Visualizations -->
		<div class="viz-panel">
			<!-- Executive Hierarchy Chart -->
			<div class="viz-card">
				<h4>EXECUTIVE HIERARCHY</h4>
				<div class="hierarchy-chart">
					<svg viewBox="0 0 300 200">
						<defs>
							<linearGradient id="hierarchyGradient" x1="0%" y1="0%" x2="0%" y2="100%">
								<stop offset="0%" style="stop-color:#ff00ff;stop-opacity:0.8" />
								<stop offset="100%" style="stop-color:#ff00ff;stop-opacity:0" />
							</linearGradient>
							<filter id="glow">
								<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
								<feMerge>
									<feMergeNode in="coloredBlur"/>
									<feMergeNode in="SourceGraphic"/>
								</feMerge>
							</filter>
						</defs>
						
						<!-- Hierarchy levels -->
						{#each topCIOs as [cio, count], i}
							<circle 
								cx={150} 
								cy={40 + i * 30} 
								r={Math.sqrt(count/maxCount) * 20 + 5}
								fill="url(#hierarchyGradient)"
								opacity="0.6"
								filter="url(#glow)"
							/>
							<text 
								x={150} 
								y={45 + i * 30} 
								text-anchor="middle" 
								fill="#ff00ff" 
								font-size="10"
								font-weight="600"
							>
								{cio.substring(0, 10).toUpperCase()}
							</text>
						{/each}
						
						<!-- Connection lines -->
						{#each topCIOs as [_, count], i}
							{#if i < topCIOs.length - 1}
								<line 
									x1="150" y1={50 + i * 30}
									x2="150" y2={30 + (i + 1) * 30}
									stroke="#ff00ff"
									stroke-width="1"
									opacity="0.3"
								/>
							{/if}
						{/each}
					</svg>
				</div>
			</div>

			<!-- Level Distribution -->
			<div class="viz-card">
				<h4>EXECUTIVE LEVELS</h4>
				<div class="level-chart">
					{#each Object.entries(threatDistribution) as [level, count]}
						<div class="level-row">
							<div class="level-label">{level}</div>
							<div class="level-bar-container">
								<div class="level-bar" 
									style="width: {(count/filteredCIOs.length)*100}%; 
										   background: {level === 'EXECUTIVE' ? '#ff00ff' : 
													   level === 'SENIOR' ? '#ff0066' : 
													   level === 'DIRECTOR' ? '#ffaa00' : '#00ffff'}">
									<span class="bar-glow"></span>
								</div>
							</div>
							<div class="level-count">{count}</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Top 5 Executives Bar Chart -->
			<div class="viz-card">
				<h4>TOP 5 EXECUTIVES</h4>
				<div class="bar-chart">
					{#each topCIOs as [cio, count]}
						<div class="bar-item">
							<div class="bar-label">{cio.toUpperCase()}</div>
							<div class="bar-container">
								<div class="bar-fill" 
									style="width: {(count/maxCount)*100}%; 
										   background: linear-gradient(90deg, {getThreatLevel(count).color}, {getThreatLevel(count).color}80)">
									<div class="bar-shimmer"></div>
								</div>
								<span class="bar-value">{count.toLocaleString()}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Control Matrix -->
			<div class="viz-card">
				<h4>CONTROL MATRIX</h4>
				<div class="matrix-grid">
					{#each paginatedCIOs.slice(0, 9) as [cio, count]}
						<div class="matrix-cell" 
							style="background: linear-gradient(135deg, {getThreatLevel(count).color}40, {getThreatLevel(count).color}10); 
								   border-color: {getThreatLevel(count).color}"
							class:active={hoveredCIO === cio}>
							<div class="cell-value">{getPercentage(count)}%</div>
							<div class="cell-label">{cio.substring(0, 8)}</div>
							<div class="cell-pulse"></div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Network Status -->
			<div class="viz-card">
				<h4>NEURAL NETWORK STATUS</h4>
				<div class="network-status">
					<div class="status-grid">
						<div class="status-item">
							<div class="status-indicator active"></div>
							<span>EXECUTIVE TRACKING</span>
						</div>
						<div class="status-item">
							<div class="status-indicator active"></div>
							<span>ASSET CORRELATION</span>
						</div>
						<div class="status-item">
							<div class="status-indicator warning"></div>
							<span>HIERARCHY MAPPING</span>
						</div>
						<div class="status-item">
							<div class="status-indicator active"></div>
							<span>CONTROL ANALYTICS</span>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.cio-dashboard {
		height: 100vh;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, #0a0a0a 0%, #1a0033 100%);
		color: #fff;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
	}

	.header-section {
		background: rgba(0, 0, 0, 0.8);
		border-bottom: 2px solid rgba(255, 0, 255, 0.3);
		padding: 0.8rem 1rem;
		backdrop-filter: blur(10px);
		flex-shrink: 0;
	}

	.header-content {
		max-width: 100%;
	}

	.title-block {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 0.8rem;
	}

	.neural-icon {
		position: relative;
		width: 50px;
		height: 50px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.icon-rings {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.ring {
		position: absolute;
		border-radius: 50%;
		border: 1px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: ringRotate 10s linear infinite;
	}

	.ring-1 {
		width: 50px;
		height: 50px;
		border-color: rgba(255, 0, 255, 0.6);
		animation-duration: 10s;
	}

	.ring-2 {
		width: 35px;
		height: 35px;
		border-color: rgba(255, 0, 102, 0.4);
		animation-duration: 8s;
		animation-direction: reverse;
	}

	.ring-3 {
		width: 20px;
		height: 20px;
		border-color: rgba(0, 255, 255, 0.3);
		animation-duration: 6s;
	}

	.icon-core {
		position: relative;
		z-index: 3;
		font-size: 1.5rem;
		color: #ff00ff;
		text-shadow: 0 0 20px #ff00ff;
		animation: corePulse 3s ease-in-out infinite;
	}

	.title-text h1 {
		margin: 0;
		font-size: 1.2rem;
		color: #ff00ff;
		text-shadow: 0 0 15px rgba(255, 0, 255, 0.5);
		letter-spacing: 0.1em;
	}

	.title-text p {
		margin: 0.2rem 0 0 0;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.metrics-row {
		display: flex;
		gap: 0.8rem;
	}

	.metric-card {
		flex: 1;
		background: rgba(255, 0, 255, 0.05);
		border: 1px solid rgba(255, 0, 255, 0.3);
		border-radius: 6px;
		padding: 0.6rem;
		text-align: center;
		transition: all 0.3s ease;
		position: relative;
		overflow: hidden;
	}

	.metric-card::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 0, 255, 0.2), transparent);
		animation: sweep 3s linear infinite;
	}

	.metric-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(255, 0, 255, 0.2);
	}

	.metric-card.primary {
		background: rgba(0, 255, 133, 0.05);
		border-color: rgba(0, 255, 133, 0.3);
	}

	.metric-card.critical {
		background: rgba(255, 0, 102, 0.05);
		border-color: rgba(255, 0, 102, 0.3);
	}

	.metric-value {
		font-size: 1.3rem;
		font-weight: 700;
		color: #ff00ff;
		text-shadow: 0 0 10px currentColor;
		position: relative;
		z-index: 1;
	}

	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.2rem;
		letter-spacing: 0.05em;
		position: relative;
		z-index: 1;
	}

	.main-content {
		flex: 1;
		display: flex;
		gap: 0.8rem;
		padding: 0.8rem;
		overflow: hidden;
		min-height: 0;
	}

	.table-panel {
		flex: 2;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 8px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		position: relative;
	}

	.table-panel::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 1px;
		background: linear-gradient(90deg, transparent, #ff00ff, transparent);
		animation: scanline 4s linear infinite;
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		overflow-y: auto;
		min-width: 350px;
	}

	.panel-header {
		padding: 0.8rem;
		border-bottom: 1px solid rgba(255, 0, 255, 0.2);
		background: rgba(0, 0, 0, 0.3);
	}

	.panel-header h3 {
		margin: 0 0 0.5rem 0;
		font-size: 0.9rem;
		color: #ff00ff;
		letter-spacing: 0.05em;
	}

	.controls {
		display: flex;
		gap: 0.8rem;
		align-items: center;
	}

	.search-bar {
		flex: 1;
		max-width: 300px;
		position: relative;
	}

	.search-input {
		width: 100%;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 0, 255, 0.3);
		border-radius: 4px;
		padding: 0.4rem 2rem 0.4rem 0.8rem;
		color: #fff;
		font-size: 0.75rem;
		transition: all 0.3s ease;
	}

	.search-input:focus {
		outline: none;
		border-color: #ff00ff;
		box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
	}

	.search-icon {
		position: absolute;
		right: 0.5rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.9rem;
		color: #ff00ff;
		pointer-events: none;
	}

	.view-toggle {
		display: flex;
		gap: 0.2rem;
		background: rgba(0, 0, 0, 0.6);
		border-radius: 4px;
		padding: 0.1rem;
	}

	.toggle-btn {
		background: transparent;
		border: 1px solid transparent;
		color: rgba(255, 255, 255, 0.6);
		padding: 0.3rem 0.6rem;
		border-radius: 3px;
		cursor: pointer;
		font-size: 0.65rem;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}

	.toggle-btn:hover {
		color: #ff00ff;
		background: rgba(255, 0, 255, 0.05);
	}

	.toggle-btn.active {
		background: rgba(255, 0, 255, 0.1);
		border-color: #ff00ff;
		color: #ff00ff;
		box-shadow: 0 0 8px rgba(255, 0, 255, 0.3);
	}

	.btn-icon {
		font-size: 0.8rem;
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
		padding: 0.8rem;
		text-align: left;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
		z-index: 10;
		border-bottom: 2px solid rgba(255, 0, 255, 0.3);
	}

	.data-table td {
		padding: 0.6rem 0.8rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.8);
		transition: all 0.2s ease;
	}

	.data-table tr:hover td {
		background: rgba(255, 0, 255, 0.05);
		color: #fff;
	}

	.cio-cell .cell-content {
		display: flex;
		align-items: center;
		gap: 0.8rem;
	}

	.indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
		position: relative;
	}

	.indicator.pulse::before {
		content: '';
		position: absolute;
		top: -4px;
		left: -4px;
		width: 16px;
		height: 16px;
		border-radius: 50%;
		border: 1px solid currentColor;
		animation: pulse 2s ease-out infinite;
	}

	.cio-info {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
	}

	.cio-name {
		font-weight: 600;
		font-size: 0.8rem;
	}

	.cio-title {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
	}

	.center {
		text-align: center;
	}

	.asset-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.3rem;
	}

	.asset-count {
		font-size: 0.9rem;
		font-weight: 600;
		color: #ff00ff;
		text-shadow: 0 0 8px currentColor;
	}

	.mini-bar {
		width: 60px;
		height: 3px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 2px;
		overflow: hidden;
	}

	.mini-fill {
		height: 100%;
		transition: width 0.5s ease;
	}

	.coverage-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.coverage-bar {
		flex: 1;
		height: 8px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
		overflow: hidden;
		min-width: 80px;
		position: relative;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.5s ease;
		position: relative;
		box-shadow: 0 0 10px currentColor;
	}

	.coverage-glow {
		position: absolute;
		top: 0;
		right: 0;
		width: 20px;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8));
		animation: glow 2s linear infinite;
	}

	.coverage-text {
		font-size: 0.7rem;
		min-width: 45px;
		text-align: right;
		font-weight: 600;
		color: #ff00ff;
		text-shadow: 0 0 5px currentColor;
	}

	.threat-badge {
		padding: 0.25rem 0.6rem;
		border-radius: 4px;
		font-size: 0.65rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		position: relative;
		overflow: hidden;
	}

	.threat-badge::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
		animation: sweep 3s linear infinite;
	}

	.threat-badge.executive {
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
		box-shadow: 0 0 8px rgba(255, 0, 255, 0.4);
	}

	.threat-badge.senior {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
		box-shadow: 0 0 8px rgba(255, 0, 102, 0.4);
	}

	.threat-badge.director {
		background: rgba(255, 170, 0, 0.2);
		color: #ffaa00;
		border: 1px solid #ffaa00;
		box-shadow: 0 0 8px rgba(255, 170, 0, 0.4);
	}

	.threat-badge.manager {
		background: rgba(0, 255, 255, 0.2);
		color: #00ffff;
		border: 1px solid #00ffff;
		box-shadow: 0 0 8px rgba(0, 255, 255, 0.4);
	}

	.drill-btn {
		background: linear-gradient(135deg, rgba(255, 0, 255, 0.1), rgba(255, 0, 255, 0.2));
		border: 1px solid #ff00ff;
		color: #ff00ff;
		padding: 0.3rem 0.8rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.65rem;
		font-weight: 600;
		transition: all 0.3s ease;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		position: relative;
		overflow: hidden;
	}

	.drill-btn::before {
		content: '';
		position: absolute;
		top: 50%;
		left: -100%;
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, #ff00ff, transparent);
		animation: laser 2s linear infinite;
	}

	.drill-btn:hover {
		background: rgba(255, 0, 255, 0.2);
		transform: translateX(2px);
		box-shadow: 0 0 15px rgba(255, 0, 255, 0.4);
		text-shadow: 0 0 8px currentColor;
	}

	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		padding: 0.8rem;
		border-top: 1px solid rgba(255, 0, 255, 0.2);
		background: rgba(0, 0, 0, 0.3);
	}

	.page-btn {
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid #ff00ff;
		color: #ff00ff;
		width: 36px;
		height: 36px;
		border-radius: 50%;
		cursor: pointer;
		transition: all 0.3s ease;
		font-size: 0.8rem;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.page-btn:hover:not(:disabled) {
		background: rgba(255, 0, 255, 0.2);
		transform: scale(1.1);
		box-shadow: 0 0 15px rgba(255, 0, 255, 0.4);
	}

	.page-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.page-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
		font-weight: 600;
	}

	.current-page {
		color: #ff00ff;
		text-shadow: 0 0 10px currentColor;
	}

	.page-separator {
		color: rgba(255, 255, 255, 0.3);
	}

	.total-pages {
		color: rgba(255, 255, 255, 0.6);
	}

	.grid-container {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		gap: 1rem;
		padding: 1rem;
		overflow-y: auto;
		flex: 1;
	}

	.grid-card {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 0, 255, 0.05));
		border: 1px solid var(--card-color);
		border-radius: 8px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		position: relative;
		overflow: hidden;
	}

	.grid-card::before {
		content: '';
		position: absolute;
		top: -2px;
		left: -2px;
		right: -2px;
		bottom: -2px;
		background: linear-gradient(45deg, var(--card-color), transparent, var(--card-color));
		border-radius: 8px;
		opacity: 0;
		z-index: -1;
		transition: opacity 0.3s ease;
	}

	.grid-card:hover::before {
		opacity: 1;
		animation: borderRotate 3s linear infinite;
	}

	.grid-card:hover {
		transform: translateY(-5px);
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 30px var(--card-color);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.executive-avatar {
		position: relative;
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.avatar-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid var(--card-color);
		border-radius: 50%;
		animation: avatarPulse 3s ease-in-out infinite;
	}

	.avatar-icon {
		font-size: 1.5rem;
		filter: hue-rotate(280deg) saturate(2);
		position: relative;
		z-index: 1;
	}

	.level-indicator {
		font-size: 0.55rem;
		padding: 0.2rem 0.4rem;
		border-radius: 4px;
		font-weight: 600;
		text-transform: uppercase;
	}

	.level-indicator.executive {
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
	}

	.level-indicator.senior {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.level-indicator.director {
		background: rgba(255, 170, 0, 0.2);
		color: #ffaa00;
		border: 1px solid #ffaa00;
	}

	.level-indicator.manager {
		background: rgba(0, 255, 255, 0.2);
		color: #00ffff;
		border: 1px solid #00ffff;
	}

	.card-body {
		text-align: center;
	}

	.executive-name {
		font-size: 0.85rem;
		color: #fff;
		font-weight: 600;
		margin-bottom: 0.2rem;
		text-shadow: 0 0 10px rgba(255, 0, 255, 0.5);
	}

	.executive-title {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		margin-bottom: 0.8rem;
	}

	.asset-counter {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin-bottom: 0.6rem;
	}

	.counter-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--card-color);
		text-shadow: 0 0 15px var(--card-color);
	}

	.counter-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.control-bar {
		width: 100%;
		height: 6px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 3px;
		overflow: hidden;
		margin-bottom: 0.4rem;
	}

	.control-fill {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 10px currentColor;
		position: relative;
		overflow: hidden;
	}

	.control-fill::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
		animation: shimmer 2s linear infinite;
	}

	.card-percentage {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.7);
		margin-bottom: 0.8rem;
	}

	.card-footer {
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		padding-top: 0.8rem;
	}

	.access-btn {
		width: 100%;
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid var(--card-color);
		color: var(--card-color);
		padding: 0.4rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.65rem;
		font-weight: 600;
		transition: all 0.3s ease;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.access-btn:hover {
		background: rgba(255, 0, 255, 0.2);
		box-shadow: 0 0 10px var(--card-color);
		text-shadow: 0 0 8px currentColor;
	}

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1.5rem;
	}

	.quantum-loader {
		position: relative;
		width: 80px;
		height: 80px;
	}

	.loader-core {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 3px solid rgba(255, 0, 255, 0.1);
		border-radius: 50%;
	}

	.loader-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 3px solid transparent;
		border-top-color: #ff00ff;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.loading-state p {
		color: #ff00ff;
		font-size: 0.9rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-shadow: 0 0 10px currentColor;
		animation: blink 1.5s ease-in-out infinite;
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
		padding: 1rem;
		border-bottom: 2px solid rgba(255, 0, 255, 0.3);
		background: linear-gradient(135deg, rgba(255, 0, 255, 0.1), rgba(0, 0, 0, 0.5));
	}

	.drill-header h4 {
		margin: 0;
		color: #ff00ff;
		font-size: 1rem;
		text-shadow: 0 0 10px currentColor;
		letter-spacing: 0.05em;
	}

	.drill-stats {
		display: flex;
		gap: 1rem;
	}

	.stat-badge {
		padding: 0.3rem 0.8rem;
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid #ff00ff;
		border-radius: 4px;
		color: #ff00ff;
		font-size: 0.7rem;
		font-weight: 600;
		text-shadow: 0 0 5px currentColor;
	}

	.close-btn {
		background: transparent;
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 30px;
		height: 30px;
		border-radius: 50%;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.3s ease;
		font-size: 0.9rem;
	}

	.close-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: rotate(90deg);
		box-shadow: 0 0 15px rgba(255, 0, 102, 0.4);
	}

	.host-cell {
		font-family: monospace;
		color: #00ffff;
		font-size: 0.75rem;
		text-shadow: 0 0 5px currentColor;
	}

	.status-badge {
		padding: 0.2rem 0.4rem;
		border-radius: 3px;
		font-size: 0.65rem;
		font-weight: 600;
	}

	.status-badge.active {
		background: rgba(0, 255, 133, 0.2);
		color: #00ff85;
		border: 1px solid #00ff85;
		text-shadow: 0 0 5px currentColor;
	}

	.status-badge.inactive {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
		text-shadow: 0 0 5px currentColor;
	}

	.exec-badge {
		padding: 0.2rem 0.6rem;
		background: linear-gradient(135deg, rgba(255, 0, 255, 0.2), rgba(255, 0, 255, 0.1));
		color: #ff00ff;
		border: 1px solid #ff00ff;
		border-radius: 3px;
		font-size: 0.6rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		text-shadow: 0 0 5px currentColor;
	}

	.viz-card {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 8px;
		padding: 0.8rem;
		animation: vizEntrance 0.6s ease-out;
		position: relative;
		overflow: hidden;
	}

	.viz-card::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 1px;
		background: linear-gradient(90deg, transparent, #ff00ff, transparent);
		animation: scanline 3s linear infinite;
	}

	.viz-card h4 {
		margin: 0 0 0.8rem 0;
		font-size: 0.75rem;
		color: #ff00ff;
		letter-spacing: 0.05em;
		text-align: center;
		text-shadow: 0 0 8px currentColor;
		position: relative;
		z-index: 1;
	}

	.hierarchy-chart {
		width: 100%;
		display: flex;
		justify-content: center;
	}

	.level-chart {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.level-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.level-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
		min-width: 70px;
		text-transform: uppercase;
		font-weight: 600;
	}

	.level-bar-container {
		flex: 1;
		height: 8px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
		overflow: hidden;
	}

	.level-bar {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 10px currentColor;
		position: relative;
	}

	.bar-glow {
		position: absolute;
		top: 0;
		right: 0;
		width: 20px;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8));
		animation: glow 2s linear infinite;
	}

	.level-count {
		font-size: 0.7rem;
		color: #ff00ff;
		min-width: 20px;
		text-align: right;
		font-weight: 600;
		text-shadow: 0 0 5px currentColor;
	}

	.bar-chart {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.bar-item {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.bar-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
		font-weight: 600;
	}

	.bar-container {
		position: relative;
		height: 20px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
		overflow: hidden;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
		position: relative;
		overflow: hidden;
		box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.3);
	}

	.bar-shimmer {
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
		animation: shimmer 2s linear infinite;
	}

	.bar-value {
		position: absolute;
		right: 0.5rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.65rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
	}

	.matrix-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.5rem;
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
		transition: all 0.3s ease;
		position: relative;
		overflow: hidden;
	}

	.matrix-cell.active {
		animation: cellPulse 0.5s ease;
	}

	.cell-pulse {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 100%;
		height: 100%;
		background: radial-gradient(circle, currentColor, transparent);
		transform: translate(-50%, -50%);
		opacity: 0;
		pointer-events: none;
	}

	.matrix-cell:hover .cell-pulse {
		animation: pulse 0.6s ease-out;
	}

	.cell-value {
		font-size: 0.75rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 0 0 5px currentColor;
	}

	.cell-label {
		font-size: 0.5rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.2rem;
		text-transform: uppercase;
	}

	.network-status {
		padding: 0.5rem;
	}

	.status-grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 0.5rem;
	}

	.status-item {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		padding: 0.4rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 4px;
	}

	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		position: relative;
	}

	.status-indicator.active {
		background: #00ff85;
		box-shadow: 0 0 10px #00ff85;
		animation: statusBlink 2s ease-in-out infinite;
	}

	.status-indicator.warning {
		background: #ffaa00;
		box-shadow: 0 0 10px #ffaa00;
		animation: statusBlink 1s ease-in-out infinite;
	}

	.status-item span {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.7);
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	@keyframes ringRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes corePulse {
		0%, 100% { opacity: 0.9; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.1); }
	}

	@keyframes sweep {
		to { left: 100%; }
	}

	@keyframes scanline {
		0% { transform: translateY(0); }
		100% { transform: translateY(100vh); }
	}

	@keyframes pulse {
		0% { transform: scale(1); opacity: 1; }
		100% { transform: scale(2); opacity: 0; }
	}

	@keyframes glow {
		0% { transform: translateX(-20px); }
		100% { transform: translateX(20px); }
	}

	@keyframes laser {
		to { left: 100%; }
	}

	@keyframes borderRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes avatarPulse {
		0%, 100% { transform: scale(1); opacity: 0.8; }
		50% { transform: scale(1.1); opacity: 1; }
	}

	@keyframes shimmer {
		to { left: 100%; }
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@keyframes blink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	@keyframes vizEntrance {
		from { opacity: 0; transform: translateX(20px); }
		to { opacity: 1; transform: translateX(0); }
	}

	@keyframes cellPulse {
		0% { transform: scale(1); }
		50% { transform: scale(1.05); }
		100% { transform: scale(1); }
	}

	@keyframes statusBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.6; }
	}

	@media (max-width: 1200px) {
		.main-content {
			flex-direction: column;
		}
		
		.viz-panel {
			flex-direction: row;
			overflow-x: auto;
			min-width: auto;
		}
		
		.viz-card {
			min-width: 280px;
		}
	}

	@media (max-width: 768px) {
		.metrics-row {
			flex-wrap: wrap;
		}
		
		.metric-card {
			min-width: calc(50% - 0.4rem);
		}
		
		.controls {
			flex-direction: column;
			gap: 0.5rem;
		}
		
		.search-bar {
			max-width: 100%;
		}
		
		.grid-container {
			grid-template-columns: 1fr;
		}
	}
</style>