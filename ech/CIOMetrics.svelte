<!-- CIOMetrics.svelte - Enhanced Executive Intelligence Dashboard -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCio = null;
	let cioDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 10;
	let viewMode = 'dashboard';
	let hoveredCio = null;

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/cio_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('CIO metrics error:', err);
			loading = false;
		}
	});

	$: sortedCios = data.operative_intelligence ? 
		Object.entries(data.operative_intelligence)
			.filter(([cio]) => cio.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: paginatedCios = sortedCios.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(sortedCios.length / itemsPerPage);

	$: maxAssets = sortedCios.length > 0 ? Math.max(...sortedCios.map(([,count]) => count)) : 1;

	function getExecutiveLevel(count) {
		if (!maxAssets) return { level: 'ANALYST', color: '#0096ff', icon: '📊' };
		let percentage = (count / maxAssets) * 100;
		if (percentage >= 70) return { level: 'C-SUITE', color: '#ff00ff', icon: '👔' };
		if (percentage >= 40) return { level: 'VP', color: '#ff0066', icon: '💼' };
		if (percentage >= 20) return { level: 'DIRECTOR', color: '#ffaa00', icon: '📋' };
		return { level: 'ANALYST', color: '#00ffff', icon: '📊' };
	}

	function getPercentage(count) {
		let total = Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
	}

	async function drillDownCio(cio, count) {
		selectedCio = { cio, count };
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
		selectedCio = null;
		cioDetails = [];
	}

	$: executiveDistribution = sortedCios.reduce((acc, [_, count]) => {
		let level = getExecutiveLevel(count).level;
		acc[level] = (acc[level] || 0) + 1;
		return acc;
	}, {});

	$: topExecutives = sortedCios.slice(0, 5);
</script>

<div class="cio-dashboard">
	<!-- Executive Header -->
	<div class="executive-header">
		<div class="header-content">
			<div class="title-block">
				<div class="executive-icon">👤</div>
				<div class="title-text">
					<h1>EXECUTIVE INTELLIGENCE</h1>
					<p>CIO Asset Ownership Analysis</p>
				</div>
			</div>
			<div class="metrics-row">
				<div class="metric-card">
					<div class="metric-value">{sortedCios.length}</div>
					<div class="metric-label">EXECUTIVES</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
					<div class="metric-label">TOTAL ASSETS</div>
				</div>
				<div class="metric-card primary">
					<div class="metric-value">{sortedCios[0] ? sortedCios[0][0].toUpperCase() : 'N/A'}</div>
					<div class="metric-label">TOP EXEC</div>
				</div>
				<div class="metric-card critical">
					<div class="metric-value">{executiveDistribution['C-SUITE'] || 0}</div>
					<div class="metric-label">C-LEVEL</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content Grid -->
	<div class="main-content">
		<!-- Left Panel: Executive Table/Dashboard -->
		<div class="executive-panel">
			<div class="panel-header">
				<h3>EXECUTIVE COMMAND</h3>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="Search executives..."
						class="search-input"
					/>
					<div class="view-toggle">
						<button class="toggle-btn {viewMode === 'dashboard' ? 'active' : ''}" on:click={() => viewMode = 'dashboard'}>
							DASHBOARD
						</button>
						<button class="toggle-btn {viewMode === 'table' ? 'active' : ''}" on:click={() => viewMode = 'table'}>
							TABLE
						</button>
						<button class="toggle-btn {viewMode === 'org' ? 'active' : ''}" on:click={() => viewMode = 'org'}>
							ORG CHART
						</button>
					</div>
				</div>
			</div>
			
			{#if loading && !selectedCio}
				<div class="loading-state">
					<div class="executive-scanner">
						<div class="scan-rings">
							<div class="ring ring-1"></div>
							<div class="ring ring-2"></div>
							<div class="ring ring-3"></div>
						</div>
					</div>
					<p>Scanning executive hierarchy...</p>
				</div>
			{:else if selectedCio}
				<!-- Drill-down View -->
				<div class="drill-view">
					<div class="drill-header">
						<div class="exec-profile">
							<span class="profile-icon">👤</span>
							<h4>{selectedCio.cio.toUpperCase()}</h4>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="drill-stats">
						<div class="stat-item">
							<span class="stat-label">Total Assets</span>
							<span class="stat-value">{selectedCio.count.toLocaleString()}</span>
						</div>
						<div class="stat-item">
							<span class="stat-label">Coverage</span>
							<span class="stat-value">{getPercentage(selectedCio.count)}%</span>
						</div>
						<div class="stat-item">
							<span class="stat-label">Level</span>
							<span class="stat-value">{getExecutiveLevel(selectedCio.count).level}</span>
						</div>
					</div>
					<div class="table-container">
						<table class="data-table">
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
								{#each cioDetails as host}
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
											<span class="exec-badge">MANAGED</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else if viewMode === 'dashboard'}
				<!-- Dashboard View with Cards -->
				<div class="executive-dashboard">
					<div class="dashboard-grid">
						{#each paginatedCios as [cio, count]}
							{@const exec = getExecutiveLevel(count)}
							<div class="exec-card" 
								style="--card-color: {exec.color}"
								on:click={() => drillDownCio(cio, count)}
								on:mouseenter={() => hoveredCio = cio}
								on:mouseleave={() => hoveredCio = null}>
								<div class="card-header">
									<span class="exec-emoji">{exec.icon}</span>
									<span class="exec-level {exec.level.toLowerCase()}">{exec.level}</span>
								</div>
								<div class="card-body">
									<div class="exec-name">{cio.toUpperCase()}</div>
									<div class="asset-count">{count.toLocaleString()}</div>
									<div class="asset-label">ASSETS</div>
									<div class="progress-ring">
										<svg width="60" height="60">
											<circle cx="30" cy="30" r="25" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="3"/>
											<circle 
												cx="30" cy="30" r="25" 
												fill="none" 
												stroke={exec.color} 
												stroke-width="3"
												stroke-dasharray={`${(count/maxAssets) * 157} 157`}
												transform="rotate(-90 30 30)"
											/>
										</svg>
										<div class="ring-value">{getPercentage(count)}%</div>
									</div>
								</div>
								{#if hoveredCio === cio}
									<div class="card-hover-info">
										<div class="info-row">
											<span>Portfolio Size:</span>
											<span>{count}</span>
										</div>
										<div class="info-row">
											<span>Coverage:</span>
											<span>{getPercentage(count)}%</span>
										</div>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			{:else if viewMode === 'table'}
				<!-- Table View -->
				<div class="table-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>EXECUTIVE</th>
								<th>LEVEL</th>
								<th>ASSETS</th>
								<th>COVERAGE</th>
								<th>RISK</th>
								<th>ACTION</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedCios as [cio, count]}
								{@const exec = getExecutiveLevel(count)}
								<tr>
									<td class="exec-cell">
										<div class="cell-content">
											<span class="exec-icon">{exec.icon}</span>
											<span>{cio.toUpperCase()}</span>
										</div>
									</td>
									<td class="center">
										<span class="level-badge {exec.level.toLowerCase()}">{exec.level}</span>
									</td>
									<td class="center">{count.toLocaleString()}</td>
									<td>
										<div class="coverage-cell">
											<div class="coverage-bar">
												<div class="coverage-fill" style="width: {getPercentage(count)}%; background: {exec.color}"></div>
											</div>
											<span class="coverage-text">{getPercentage(count)}%</span>
										</div>
									</td>
									<td class="center">
										<span class="risk-badge {exec.level === 'C-SUITE' ? 'low' : exec.level === 'VP' ? 'medium' : 'high'}">
											{exec.level === 'C-SUITE' ? 'LOW' : exec.level === 'VP' ? 'MEDIUM' : 'HIGH'}
										</span>
									</td>
									<td class="center">
										<button class="drill-btn" on:click={() => drillDownCio(cio, count)}>
											ANALYZE →
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<!-- Org Chart View -->
				<div class="org-chart">
					<div class="org-tree">
						{#each topExecutives as [cio, count], i}
							{@const exec = getExecutiveLevel(count)}
							<div class="org-node level-{exec.level.toLowerCase()}" style="--delay: {i * 0.1}s">
								<div class="node-icon">{exec.icon}</div>
								<div class="node-name">{cio.toUpperCase()}</div>
								<div class="node-assets">{count.toLocaleString()} assets</div>
								<div class="node-connections">
									{#if i < topExecutives.length - 1}
										<div class="connection-line"></div>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
			
			<!-- Pagination -->
			{#if !selectedCio && viewMode !== 'org'}
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
			{/if}
		</div>

		<!-- Right Panel: Visualizations -->
		<div class="viz-panel">
			<!-- Executive Level Distribution -->
			<div class="viz-card">
				<h4>EXECUTIVE HIERARCHY</h4>
				<div class="hierarchy-chart">
					{#each Object.entries(executiveDistribution) as [level, count]}
						{@const levelData = level === 'C-SUITE' ? {color: '#ff00ff', icon: '👔'} :
							level === 'VP' ? {color: '#ff0066', icon: '💼'} :
							level === 'DIRECTOR' ? {color: '#ffaa00', icon: '📋'} :
							{color: '#00ffff', icon: '📊'}}
						<div class="hierarchy-level">
							<div class="level-header">
								<span class="level-icon">{levelData.icon}</span>
								<span class="level-name">{level}</span>
							</div>
							<div class="level-bar-container">
								<div class="level-bar" style="width: {(count/sortedCios.length)*100}%; background: {levelData.color}"></div>
							</div>
							<div class="level-count">{count}</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Top 5 Executives Chart -->
			<div class="viz-card">
				<h4>TOP EXECUTIVES</h4>
				<div class="bar-chart">
					{#each topExecutives as [cio, count]}
						{@const exec = getExecutiveLevel(count)}
						<div class="bar-item">
							<div class="bar-label">
								<span class="bar-icon">{exec.icon}</span>
								<span>{cio.substring(0, 15)}{cio.length > 15 ? '...' : ''}</span>
							</div>
							<div class="bar-container">
								<div class="bar-fill" 
									style="width: {(count/maxAssets)*100}%; background: linear-gradient(90deg, {exec.color}, {exec.color}80)">
								</div>
								<span class="bar-value">{count.toLocaleString()}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Portfolio Distribution -->
			<div class="viz-card">
				<h4>PORTFOLIO DISTRIBUTION</h4>
				<div class="donut-chart">
					<svg viewBox="0 0 200 200">
						{#if sortedCios.length > 0}
							{@const total = Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0)}
							{@const radius = 60}
							{@const circumference = 2 * Math.PI * radius}
							{#each sortedCios.slice(0, 5) as [cio, count], i}
								{@const percentage = (count / total) * 100}
								{@const strokeDasharray = (percentage / 100) * circumference}
								{@const rotation = sortedCios.slice(0, i)
									.reduce((acc, [_, c]) => acc + (c / total) * 360, -90)}
								{@const exec = getExecutiveLevel(count)}
								<circle
									cx="100"
									cy="100"
									r={radius}
									fill="none"
									stroke={exec.color}
									stroke-width="30"
									stroke-dasharray="{strokeDasharray} {circumference}"
									transform="rotate({rotation} 100 100)"
									opacity="0.8"
								/>
							{/each}
						{/if}
						<text x="100" y="95" text-anchor="middle" fill="white" font-size="24" font-weight="bold">
							{sortedCios.length}
						</text>
						<text x="100" y="110" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="10">
							EXECUTIVES
						</text>
					</svg>
				</div>
			</div>

			<!-- Executive Matrix -->
			<div class="viz-card">
				<h4>EXECUTIVE MATRIX</h4>
				<div class="matrix-grid">
					{#each sortedCios.slice(0, 9) as [cio, count]}
						{@const exec = getExecutiveLevel(count)}
						<div class="matrix-cell" 
							style="background: {exec.color}20; border-color: {exec.color}"
							on:click={() => drillDownCio(cio, count)}>
							<div class="cell-icon">{exec.icon}</div>
							<div class="cell-value">{getPercentage(count)}%</div>
							<div class="cell-label">{cio.substring(0, 8)}</div>
						</div>
					{/each}
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
		background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
		color: #fff;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
	}

	.executive-header {
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
		gap: 0.8rem;
		margin-bottom: 0.6rem;
	}

	.executive-icon {
		font-size: 1.8rem;
		filter: hue-rotate(280deg) saturate(2);
		animation: iconFloat 3s ease-in-out infinite;
	}

	.title-text h1 {
		margin: 0;
		font-size: 1.2rem;
		color: #ff00ff;
		text-shadow: 0 0 10px rgba(255, 0, 255, 0.5);
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
		padding: 0.5rem;
		text-align: center;
		transition: all 0.3s ease;
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
		font-size: 1.1rem;
		font-weight: 700;
		color: #ff00ff;
		text-shadow: 0 0 10px currentColor;
	}

	.metric-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.2rem;
		letter-spacing: 0.05em;
	}

	.main-content {
		flex: 1;
		display: flex;
		gap: 0.8rem;
		padding: 0.8rem;
		overflow: hidden;
		min-height: 0;
	}

	.executive-panel {
		flex: 2;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 0, 255, 0.2);
		border-radius: 8px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.viz-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		overflow-y: auto;
		min-width: 300px;
	}

	.panel-header {
		padding: 0.8rem;
		border-bottom: 1px solid rgba(255, 0, 255, 0.2);
		background: rgba(0, 0, 0, 0.3);
	}

	.panel-header h3 {
		margin: 0 0 0.5rem 0;
		font-size: 0.8rem;
		color: #ff00ff;
		letter-spacing: 0.05em;
	}

	.controls {
		display: flex;
		gap: 0.8rem;
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
		font-size: 0.6rem;
		transition: all 0.3s ease;
	}

	.toggle-btn.active {
		background: rgba(255, 0, 255, 0.1);
		border-color: #ff00ff;
		color: #ff00ff;
	}

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}

	.executive-scanner {
		position: relative;
		width: 100px;
		height: 100px;
	}

	.scan-rings {
		position: relative;
		width: 100%;
		height: 100%;
	}

	.ring {
		position: absolute;
		border-radius: 50%;
		border: 2px solid #ff00ff;
		opacity: 0.6;
		animation: ringExpand 2s ease-in-out infinite;
	}

	.ring-1 {
		width: 100px;
		height: 100px;
		animation-delay: 0s;
	}

	.ring-2 {
		width: 70px;
		height: 70px;
		top: 15px;
		left: 15px;
		animation-delay: 0.5s;
	}

	.ring-3 {
		width: 40px;
		height: 40px;
		top: 30px;
		left: 30px;
		animation-delay: 1s;
	}

	.executive-dashboard {
		flex: 1;
		overflow-y: auto;
		padding: 0.8rem;
	}

	.dashboard-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 0.8rem;
	}

	.exec-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid var(--card-color);
		border-radius: 8px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		position: relative;
		overflow: hidden;
	}

	.exec-card:hover {
		transform: translateY(-3px);
		box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 20px var(--card-color);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.6rem;
	}

	.exec-emoji {
		font-size: 1.5rem;
	}

	.exec-level {
		font-size: 0.5rem;
		padding: 0.15rem 0.3rem;
		border-radius: 3px;
		font-weight: 600;
	}

	.exec-level.c-suite {
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
	}

	.exec-level.vp {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.exec-level.director {
		background: rgba(255, 170, 0, 0.2);
		color: #ffaa00;
		border: 1px solid #ffaa00;
	}

	.exec-level.analyst {
		background: rgba(0, 255, 255, 0.2);
		color: #00ffff;
		border: 1px solid #00ffff;
	}

	.card-body {
		text-align: center;
	}

	.exec-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.9);
		margin-bottom: 0.3rem;
		font-weight: 600;
	}

	.asset-count {
		font-size: 1.3rem;
		font-weight: 700;
		color: var(--card-color);
		text-shadow: 0 0 10px var(--card-color);
	}

	.asset-label {
		font-size: 0.55rem;
		color: rgba(255, 255, 255, 0.6);
		margin-bottom: 0.5rem;
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
		font-size: 0.6rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.8);
	}

	.card-hover-info {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		background: rgba(0, 0, 0, 0.9);
		padding: 0.5rem;
		border-top: 1px solid var(--card-color);
		animation: slideUp 0.3s ease;
	}

	.info-row {
		display: flex;
		justify-content: space-between;
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.8);
		margin-bottom: 0.2rem;
	}

	.table-container {
		flex: 1;
		overflow: auto;
		padding: 0.5rem;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.7rem;
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
	}

	.data-table td {
		padding: 0.4rem 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(255, 255, 255, 0.8);
	}

	.data-table tr:hover {
		background: rgba(255, 0, 255, 0.05);
	}

	.exec-cell .cell-content {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.exec-icon {
		font-size: 1rem;
	}

	.center {
		text-align: center;
	}

	.level-badge {
		padding: 0.15rem 0.4rem;
		border-radius: 3px;
		font-size: 0.6rem;
		font-weight: 600;
	}

	.coverage-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.coverage-bar {
		flex: 1;
		height: 5px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 3px;
		overflow: hidden;
		min-width: 60px;
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

	.risk-badge {
		padding: 0.15rem 0.4rem;
		border-radius: 3px;
		font-size: 0.6rem;
		font-weight: 600;
	}

	.risk-badge.low {
		background: rgba(0, 255, 133, 0.2);
		color: #00ff85;
		border: 1px solid #00ff85;
	}

	.risk-badge.medium {
		background: rgba(255, 170, 0, 0.2);
		color: #ffaa00;
		border: 1px solid #ffaa00;
	}

	.risk-badge.high {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
	}

	.drill-btn {
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid #ff00ff;
		color: #ff00ff;
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.6rem;
		transition: all 0.3s ease;
	}

	.drill-btn:hover {
		background: rgba(255, 0, 255, 0.2);
		transform: translateX(2px);
		box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
	}

	.org-chart {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.org-tree {
		display: flex;
		gap: 2rem;
		align-items: center;
		justify-content: center;
	}

	.org-node {
		background: rgba(0, 0, 0, 0.6);
		border: 2px solid;
		border-radius: 8px;
		padding: 1rem;
		text-align: center;
		position: relative;
		animation: nodeAppear 0.6s ease-out;
		animation-delay: var(--delay);
		animation-fill-mode: both;
	}

	.org-node.level-c-suite {
		border-color: #ff00ff;
		box-shadow: 0 0 20px rgba(255, 0, 255, 0.3);
	}

	.org-node.level-vp {
		border-color: #ff0066;
		box-shadow: 0 0 20px rgba(255, 0, 102, 0.3);
	}

	.org-node.level-director {
		border-color: #ffaa00;
		box-shadow: 0 0 20px rgba(255, 170, 0, 0.3);
	}

	.org-node.level-analyst {
		border-color: #00ffff;
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
	}

	.node-icon {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}

	.node-name {
		font-size: 0.8rem;
		font-weight: 600;
		color: #fff;
		margin-bottom: 0.3rem;
	}

	.node-assets {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.connection-line {
		position: absolute;
		right: -2rem;
		top: 50%;
		width: 2rem;
		height: 2px;
		background: linear-gradient(90deg, #ff00ff, transparent);
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
		border-bottom: 1px solid rgba(255, 0, 255, 0.3);
		background: rgba(255, 0, 255, 0.05);
	}

	.exec-profile {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.profile-icon {
		font-size: 1.5rem;
	}

	.drill-header h4 {
		margin: 0;
		color: #ff00ff;
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
		font-size: 0.7rem;
	}

	.close-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		transform: rotate(90deg);
	}

	.drill-stats {
		display: flex;
		gap: 1rem;
		padding: 0.8rem;
		background: rgba(0, 0, 0, 0.3);
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.stat-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.stat-value {
		font-size: 0.9rem;
		font-weight: 600;
		color: #ff00ff;
		text-shadow: 0 0 8px #ff00ff;
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

	.exec-badge {
		padding: 0.1rem 0.3rem;
		background: rgba(255, 0, 255, 0.2);
		color: #ff00ff;
		border: 1px solid #ff00ff;
		border-radius: 3px;
		font-size: 0.6rem;
		font-weight: 600;
	}

	.pagination {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		padding: 0.6rem;
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
		font-size: 0.65rem;
		color: #ff00ff;
		letter-spacing: 0.05em;
		text-align: center;
	}

	.hierarchy-chart {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.hierarchy-level {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.level-header {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		min-width: 80px;
	}

	.level-icon {
		font-size: 0.8rem;
	}

	.level-name {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.level-bar-container {
		flex: 1;
		height: 6px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 3px;
		overflow: hidden;
	}

	.level-bar {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 8px currentColor;
	}

	.level-count {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		min-width: 20px;
		text-align: right;
	}

	.bar-chart {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.bar-item {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.bar-label {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.bar-icon {
		font-size: 0.8rem;
	}

	.bar-container {
		position: relative;
		height: 16px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 3px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
		position: relative;
		overflow: hidden;
	}

	.bar-fill::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
		animation: shimmer 2s infinite;
	}

	.bar-value {
		position: absolute;
		right: 0.3rem;
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.55rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
	}

	.donut-chart {
		width: 100%;
		max-width: 180px;
		margin: 0 auto;
	}

	.matrix-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.3rem;
	}

	.matrix-cell {
		aspect-ratio: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		border: 1px solid;
		border-radius: 3px;
		padding: 0.3rem;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.matrix-cell:hover {
		transform: scale(1.05);
		box-shadow: 0 0 10px currentColor;
	}

	.cell-icon {
		font-size: 0.8rem;
	}

	.cell-value {
		font-size: 0.6rem;
		font-weight: 600;
		color: #fff;
	}

	.cell-label {
		font-size: 0.45rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.1rem;
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-3px); }
	}

	@keyframes ringExpand {
		0% { transform: scale(0.5); opacity: 1; }
		100% { transform: scale(1.5); opacity: 0; }
	}

	@keyframes nodeAppear {
		0% { opacity: 0; transform: scale(0.8); }
		100% { opacity: 1; transform: scale(1); }
	}

	@keyframes slideUp {
		0% { transform: translateY(100%); }
		100% { transform: translateY(0); }
	}

	@keyframes shimmer {
		to { left: 100%; }
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
			min-width: 250px;
		}
		
		.dashboard-grid {
			grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
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
		}
		
		.dashboard-grid {
			grid-template-columns: 1fr;
		}
		
		.org-tree {
			flex-direction: column;
			gap: 1rem;
		}
		
		.connection-line {
			display: none;
		}
	}
</style>