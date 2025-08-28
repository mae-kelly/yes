<!-- CIOMetrics.svelte - Executive Command Interface -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCio = null;
	let cioDetails = [];
	let searchTerm = '';
	let executiveNodes = [];
	let hierarchyPulse = [];

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/cio_metrics');
			data = await response.json();
			loading = false;
			
			// Initialize executive visualization
			if (data.operative_intelligence) {
				const sorted = Object.entries(data.operative_intelligence).sort((a, b) => b[1] - a[1]);
				for (let i = 0; i < Math.min(8, sorted.length); i++) {
					executiveNodes.push({
						angle: (i * 45) * Math.PI / 180,
						radius: 30 + Math.random() * 20,
						intensity: sorted[i][1] / sorted[0][1]
					});
				}
			}
			
			// Hierarchy pulse animation
			for (let i = 0; i < 4; i++) {
				hierarchyPulse.push(Math.random());
			}
		} catch (err) {
			console.error('CIO metrics error:', err);
			loading = false;
		}
	});

	$: sortedCios = data.operative_intelligence ? 
		Object.entries(data.operative_intelligence)
			.filter(([cio]) => cio.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxAssets = sortedCios.length > 0 ? Math.max(...sortedCios.map(([,count]) => count)) : 1;

	function getExecutiveLevel(count) {
		if (!maxAssets) return { level: 'ANALYST', color: '#b8a678', icon: '▪', tier: 1 };
		let percentage = (count / maxAssets) * 100;
		if (percentage >= 70) return { level: 'C-SUITE', color: '#ff0066', icon: '◆', tier: 4 };
		if (percentage >= 40) return { level: 'VP', color: '#ff9900', icon: '▲', tier: 3 };
		if (percentage >= 20) return { level: 'DIRECTOR', color: '#ffcc00', icon: '●', tier: 2 };
		return { level: 'ANALYST', color: '#0a4f3c', icon: '▪', tier: 1 };
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
</script>

<div class="dashboard-container">
	<div class="main-content">
		<!-- Left Panel: Executive Command -->
		<div class="table-panel">
			<div class="panel-header">
				<div class="header-grid">
					<div>
						<h3 class="panel-title">EXECUTIVES</h3>
						<div class="subtitle">LEADERSHIP COMMAND INTERFACE</div>
					</div>
					<div class="executive-beacon">
						<svg viewBox="0 0 60 60" class="beacon-svg">
							<defs>
								<radialGradient id="beaconGrad">
									<stop offset="0%" style="stop-color:#ff0066;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#ff0066;stop-opacity:0" />
								</radialGradient>
							</defs>
							
							<!-- Rotating triangles -->
							{#each Array(3) as _, i}
								<g transform="rotate({i * 120} 30 30)" class="rotate-beacon">
									<path d="M30,10 L40,30 L20,30 Z" 
										  fill="none" stroke="#ff0066" stroke-width="0.5" 
										  opacity="{0.3 + i * 0.2}"/>
								</g>
							{/each}
							
							<!-- Central core -->
							<circle cx="30" cy="30" r="8" fill="url(#beaconGrad)" opacity="0.5"/>
							<circle cx="30" cy="30" r="5" fill="#ff0066" opacity="0.8"/>
							
							<!-- Pulse rings -->
							{#each hierarchyPulse as pulse, i}
								<circle cx="30" cy="30" r="{10 + i * 8}" 
										fill="none" stroke="#ff0066" stroke-width="0.5" 
										opacity="{pulse * 0.5}">
									<animate attributeName="r" 
											values="{10 + i * 8};{20 + i * 8};{10 + i * 8}" 
											dur="{2 + i * 0.5}s" repeatCount="indefinite"/>
									<animate attributeName="opacity" 
											values="{pulse * 0.5};0;{pulse * 0.5}" 
											dur="{2 + i * 0.5}s" repeatCount="indefinite"/>
								</circle>
							{/each}
						</svg>
					</div>
				</div>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="SEARCH EXECUTIVES..."
						class="search-input"
					/>
				</div>
			</div>
			
			{#if loading && !selectedCio}
				<div class="loading-state">
					<div class="executive-loader">
						<div class="loader-pyramid">
							<div class="pyramid-level"></div>
							<div class="pyramid-level"></div>
							<div class="pyramid-level"></div>
							<div class="pyramid-level"></div>
						</div>
					</div>
					<p class="loading-text">SCANNING EXECUTIVE DATA...</p>
				</div>
			{:else if selectedCio}
				<div class="drill-view">
					<div class="drill-header">
						<div class="exec-profile">
							{@const exec = getExecutiveLevel(selectedCio.count)}
							<span class="profile-icon" style="color: {exec.color}; font-size: 1.5rem">
								{exec.icon}
							</span>
							<div>
								<h4>{selectedCio.cio.toUpperCase()}</h4>
								<div class="profile-stats">
									<span>{selectedCio.count.toLocaleString()} ASSETS</span>
									<span>{getPercentage(selectedCio.count)}% COVERAGE</span>
									<span style="color: {exec.color}">{exec.level}</span>
								</div>
							</div>
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
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each cioDetails as host}
									<tr>
										<td class="host-cell">{host.host}</td>
										<td>{host.region || 'CLASSIFIED'}</td>
										<td>{host.infrastructure_type || 'CLASSIFIED'}</td>
										<td>
											<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'ACTIVE' : 'INACTIVE'}
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
								<th>EXECUTIVE</th>
								<th>LEVEL</th>
								<th>ASSETS</th>
								<th>COVERAGE</th>
								<th>COMMAND AUTHORITY</th>
							</tr>
						</thead>
						<tbody>
							{#each sortedCios as [cio, count]}
								{@const exec = getExecutiveLevel(count)}
								<tr on:click={() => drillDownCio(cio, count)}>
									<td class="exec-cell">
										<span class="exec-icon" style="color: {exec.color}">{exec.icon}</span>
										<span class="exec-name">{cio.substring(0, 30).toUpperCase()}</span>
									</td>
									<td class="center">
										<span class="level-badge" style="color: {exec.color}; border-color: {exec.color}">
											{exec.level}
										</span>
									</td>
									<td class="center">{count.toLocaleString()}</td>
									<td class="center">
										<div class="coverage-meter">
											<span class="coverage-text">{getPercentage(count)}%</span>
											<div class="coverage-track">
												<div class="coverage-fill" 
													 style="width: {getPercentage(count)}%; 
															background: linear-gradient(90deg, #0a4f3c, {exec.color})">
												</div>
											</div>
										</div>
									</td>
									<td>
										<div class="authority-display">
											<svg viewBox="0 0 50 20" class="authority-svg">
												{#each Array(exec.tier) as _, i}
													<polygon points="{10 + i*10},15 {15 + i*10},5 {20 + i*10},15" 
															fill={exec.color} opacity="{0.4 + i * 0.15}"/>
												{/each}
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

		<!-- Right Panel: Executive Intelligence -->
		<div class="viz-panel">
			<!-- Executive Metrics -->
			<div class="metrics-command">
				<div class="metric-card">
					<div class="metric-header">
						<span class="metric-icon">◆</span>
						<span class="metric-label">EXECUTIVES</span>
					</div>
					<div class="metric-value">{sortedCios.length}</div>
				</div>
				<div class="metric-card">
					<div class="metric-header">
						<span class="metric-icon">◉</span>
						<span class="metric-label">TOTAL ASSETS</span>
					</div>
					<div class="metric-value">{Object.values(data.operative_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
				</div>
			</div>

			<!-- Hierarchy Visualization -->
			<div class="viz-card">
				<div class="card-header">
					<h4>ORGANIZATIONAL HIERARCHY</h4>
					<div class="card-status active"></div>
				</div>
				<div class="hierarchy-chart">
					<svg viewBox="0 0 120 100" class="hierarchy-svg">
						<defs>
							<linearGradient id="hierGrad" x1="0%" y1="0%" x2="0%" y2="100%">
								<stop offset="0%" style="stop-color:#ff0066;stop-opacity:0.5" />
								<stop offset="100%" style="stop-color:#0a4f3c;stop-opacity:0.5" />
							</linearGradient>
						</defs>
						
						<!-- Pyramid structure -->
						<polygon points="60,10 100,90 20,90" 
								fill="url(#hierGrad)" opacity="0.2"/>
						
						<!-- Hierarchy levels -->
						{#each Object.entries(executiveDistribution) as [level, count], i}
							{@const levelData = level === 'C-SUITE' ? {y: 20, color: '#ff0066'} :
								level === 'VP' ? {y: 40, color: '#ff9900'} :
								level === 'DIRECTOR' ? {y: 60, color: '#ffcc00'} :
								{y: 80, color: '#0a4f3c'}}
							<line x1="30" y1="{levelData.y}" x2="90" y2="{levelData.y}" 
								  stroke={levelData.color} stroke-width="1" opacity="0.5"/>
							<circle cx="60" cy="{levelData.y}" r="{3 + count}" 
									fill={levelData.color} opacity="0.8"/>
							<text x="100" y="{levelData.y + 3}" 
								  fill={levelData.color} font-size="8" font-weight="600">
								{count}
							</text>
						{/each}
						
						<!-- Connection lines -->
						<line x1="60" y1="20" x2="60" y2="80" 
							  stroke="#0a4f3c" stroke-width="0.5" opacity="0.3" stroke-dasharray="2,2"/>
					</svg>
					
					<div class="hierarchy-labels">
						{#each Object.entries(executiveDistribution) as [level, count]}
							{@const levelData = level === 'C-SUITE' ? {color: '#ff0066', icon: '◆'} :
								level === 'VP' ? {color: '#ff9900', icon: '▲'} :
								level === 'DIRECTOR' ? {color: '#ffcc00', icon: '●'} :
								{color: '#0a4f3c', icon: '▪'}}
							<div class="hier-item">
								<span class="hier-icon" style="color: {levelData.color}">{levelData.icon}</span>
								<span class="hier-level">{level}</span>
								<span class="hier-count" style="color: {levelData.color}">{count}</span>
							</div>
						{/each}
					</div>
				</div>
			</div>

			<!-- Top Executives -->
			<div class="viz-card">
				<div class="card-header">
					<h4>TOP EXECUTIVES</h4>
					<div class="card-status"></div>
				</div>
				<div class="exec-list">
					{#each sortedCios.slice(0, 6) as [cio, count], i}
						{@const exec = getExecutiveLevel(count)}
						<div class="exec-item">
							<div class="exec-rank" style="background: linear-gradient(135deg, {exec.color}22, transparent)">
								<span style="color: {exec.color}">{i + 1}</span>
							</div>
							<div class="exec-details">
								<div class="exec-item-name">{cio.substring(0, 20).toUpperCase()}</div>
								<div class="exec-visual">
									<div class="exec-bar-bg"></div>
									<div class="exec-bar" 
										 style="width: {(count/maxAssets)*100}%; 
												background: linear-gradient(90deg, #0a4f3c, {exec.color})">
										<div class="exec-pulse"></div>
									</div>
								</div>
								<div class="exec-stats">
									<span>{count.toLocaleString()} ASSETS</span>
									<span style="color: {exec.color}">{exec.level}</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Command Authority Matrix -->
			<div class="viz-card">
				<div class="card-header">
					<h4>COMMAND AUTHORITY</h4>
					<div class="card-status active"></div>
				</div>
				<div class="authority-matrix">
					<svg viewBox="0 0 200 200" class="matrix-svg">
						<defs>
							<radialGradient id="authGrad">
								<stop offset="0%" style="stop-color:#ff0066;stop-opacity:0.8" />
								<stop offset="100%" style="stop-color:#ff0066;stop-opacity:0" />
							</radialGradient>
						</defs>
						
						<!-- Background grid -->
						<pattern id="matrixGrid" width="20" height="20" patternUnits="userSpaceOnUse">
							<path d="M 20 0 L 0 0 0 20" fill="none" stroke="#0a4f3c" stroke-width="0.1" opacity="0.3"/>
						</pattern>
						<rect width="200" height="200" fill="url(#matrixGrid)" />
						
						<!-- Central authority node -->
						<circle cx="100" cy="100" r="15" fill="url(#authGrad)"/>
						<circle cx="100" cy="100" r="10" fill="#ff0066" opacity="0.8"/>
						
						<!-- Executive nodes -->
						{#each executiveNodes as node, i}
							{@const x = 100 + Math.cos(node.angle) * node.radius}
							{@const y = 100 + Math.sin(node.angle) * node.radius}
							<line x1="100" y1="100" x2="{x}" y2="{y}" 
								  stroke="#0a4f3c" stroke-width="0.5" opacity="{node.intensity * 0.5}"/>
							<circle cx="{x}" cy="{y}" r="{3 + node.intensity * 5}" 
									fill="#0a4f3c" opacity="{node.intensity}"/>
						{/each}
						
						<!-- Authority rings -->
						<circle cx="100" cy="100" r="40" fill="none" stroke="#ff0066" stroke-width="0.5" opacity="0.3" stroke-dasharray="5,5"/>
						<circle cx="100" cy="100" r="60" fill="none" stroke="#ff9900" stroke-width="0.5" opacity="0.3" stroke-dasharray="5,5"/>
						<circle cx="100" cy="100" r="80" fill="none" stroke="#ffcc00" stroke-width="0.5" opacity="0.3" stroke-dasharray="5,5"/>
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

	.header-grid {
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

	.executive-beacon {
		width: 60px;
		height: 60px;
	}

	.beacon-svg {
		width: 100%;
		height: 100%;
		filter: drop-shadow(0 0 10px rgba(255, 0, 102, 0.5));
	}

	.rotate-beacon {
		animation: beaconRotate 4s linear infinite;
		transform-origin: center;
	}

	@keyframes beaconRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
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

	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.executive-loader {
		width: 80px;
		height: 80px;
		position: relative;
	}

	.loader-pyramid {
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 2px;
	}

	.pyramid-level {
		height: 15px;
		background: #0a4f3c;
		margin: 0 auto;
		animation: pyramidPulse 1.5s ease-in-out infinite;
	}

	.pyramid-level:nth-child(1) {
		width: 20px;
		animation-delay: 0s;
		background: #ff0066;
	}

	.pyramid-level:nth-child(2) {
		width: 35px;
		animation-delay: 0.1s;
		background: #ff9900;
	}

	.pyramid-level:nth-child(3) {
		width: 50px;
		animation-delay: 0.2s;
		background: #ffcc00;
	}

	.pyramid-level:nth-child(4) {
		width: 65px;
		animation-delay: 0.3s;
		background: #0a4f3c;
	}

	@keyframes pyramidPulse {
		0%, 100% { opacity: 0.3; transform: scaleX(0.9); }
		50% { opacity: 1; transform: scaleX(1); }
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

	.exec-cell {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.exec-icon {
		font-size: 1rem;
	}

	.exec-name {
		font-weight: 500;
		color: #e0e0e0;
	}

	.center {
		text-align: center;
	}

	.level-badge {
		padding: 0.3rem 0.6rem;
		border: 1px solid;
		border-radius: 2px;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.coverage-meter {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}

	.coverage-text {
		font-size: 0.75rem;
		font-weight: 600;
	}

	.coverage-track {
		width: 60px;
		height: 3px;
		background: rgba(10, 79, 60, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}

	.coverage-fill {
		height: 100%;
		transition: width 0.3s ease;
		position: relative;
	}

	.authority-display {
		display: flex;
		justify-content: center;
	}

	.authority-svg {
		width: 50px;
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

	.metrics-command {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.metric-card {
		background: linear-gradient(135deg, #0a0a0a 0%, #050505 100%);
		border: 1px solid #0a4f3c;
		border-radius: 4px;
		padding: 1.2rem;
	}

	.metric-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.metric-icon {
		font-size: 1rem;
		color: #0a4f3c;
	}

	.metric-label {
		font-size: 0.7rem;
		color: #666;
		letter-spacing: 0.1em;
	}

	.metric-value {
		font-size: 2rem;
		font-weight: 700;
		color: #0a4f3c;
		text-shadow: 0 0 20px rgba(10, 79, 60, 0.5);
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

	.hierarchy-chart {
		display: flex;
		gap: 1rem;
		align-items: center;
	}

	.hierarchy-svg {
		flex: 1;
		max-width: 120px;
	}

	.hierarchy-labels {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.hier-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.hier-icon {
		font-size: 0.8rem;
	}

	.hier-level {
		flex: 1;
		font-size: 0.65rem;
		color: #b8a678;
		letter-spacing: 0.05em;
	}

	.hier-count {
		font-size: 0.7rem;
		font-weight: 600;
	}

	.exec-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.exec-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.exec-rank {
		width: 28px;
		height: 28px;
		border-radius: 2px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.8rem;
		font-weight: 600;
	}

	.exec-details {
		flex: 1;
	}

	.exec-item-name {
		font-size: 0.7rem;
		color: #e0e0e0;
		font-weight: 500;
		margin-bottom: 0.3rem;
	}

	.exec-visual {
		position: relative;
		height: 4px;
		margin-bottom: 0.3rem;
	}

	.exec-bar-bg {
		position: absolute;
		width: 100%;
		height: 100%;
		background: rgba(10, 79, 60, 0.1);
		border-radius: 2px;
	}

	.exec-bar {
		position: relative;
		height: 100%;
		border-radius: 2px;
		overflow: hidden;
		transition: width 0.3s ease;
	}

	.exec-pulse {
		position: absolute;
		right: 0;
		top: 0;
		width: 10px;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5));
		animation: pulseSweep 2s linear infinite;
	}

	@keyframes pulseSweep {
		0% { right: -10px; }
		100% { right: 100%; }
	}

	.exec-stats {
		display: flex;
		justify-content: space-between;
		font-size: 0.65rem;
	}

	.exec-stats span:first-child {
		color: #b8a678;
	}

	.exec-stats span:last-child {
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.authority-matrix {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 200px;
	}

	.matrix-svg {
		width: 100%;
		max-width: 200px;
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
		border-bottom: 2px solid #0a4f3c;
		background: rgba(10, 79, 60, 0.05);
	}

	.exec-profile {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.profile-icon {
		animation: iconFloat 3s ease-in-out infinite;
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-3px); }
	}

	.exec-profile h4 {
		margin: 0;
		color: #0a4f3c;
		font-size: 1.1rem;
		letter-spacing: 0.1em;
	}

	.profile-stats {
		display: flex;
		gap: 1rem;
		margin-top: 0.5rem;
	}

	.profile-stats span {
		font-size: 0.65rem;
		padding: 0.2rem 0.4rem;
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