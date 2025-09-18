<!-- BusinessUnitMetrics.svelte - Fixed Division Host Distribution -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let error = null;
	let selectedDivision = null;
	let divisionDetails = [];
	let searchTerm = '';
	
	// Animation states
	let animationFrame = null;
	let rotationDegree = 0;
	let quantumFlow = [];
	
	onMount(async () => {
		await loadData();
		initializeAnimations();
	});
	
	async function loadData() {
		loading = true;
		error = null;
		try {
			let response = await fetch('http://localhost:5000/api/business_unit_metrics');
			if (!response.ok) throw new Error('Failed to fetch data');
			data = await response.json();
		} catch (err) {
			console.error('Division metrics error:', err);
			error = 'Unable to load division data. Please try again.';
			// Use mock data for demonstration
			data = generateMockData();
		} finally {
			loading = false;
		}
	}
	
	function generateMockData() {
		return {
			business_intelligence: {
				'Technology Services': 136143,
				'Merchant APAC': 106602,
				'FinTech APAC': 105693,
				'Issuer APAC': 105624,
				'Technology Services APAC': 102471,
				'Payments APAC': 100412,
				'CAPS Community': 20276,
				'DPS Digital Banking': 17111,
				'Information Technology': 15890,
				'Operations': 12456,
				'Finance': 8765,
				'Human Resources': 5432
			}
		};
	}
	
	function initializeAnimations() {
		// Initialize quantum flow animation
		for (let i = 0; i < 4; i++) {
			quantumFlow.push({
				x: Math.random() * 100,
				y: 0,
				speed: 0.5 + Math.random() * 1.5,
				width: 1 + Math.random() * 3
			});
		}
		
		const animate = () => {
			rotationDegree = (rotationDegree + 0.2) % 360;
			
			// Update quantum flow
			quantumFlow = quantumFlow.map(line => ({
				...line,
				y: (line.y + line.speed) % 100
			}));
			
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	}
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});

	$: divisions = data.business_intelligence ? 
		Object.entries(data.business_intelligence)
			.filter(([division]) => division.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = divisions.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = divisions.length > 0 ? Math.max(...divisions.map(([,c]) => c)) : 1;
	$: avgHostsPerDivision = divisions.length > 0 ? Math.round(totalHosts / divisions.length) : 0;
	
	// Key metrics
	$: divisionCount = divisions.length;
	$: topDivision = divisions[0] || ['N/A', 0];
	$: concentration = topDivision[1] > 0 ? ((topDivision[1] / totalHosts) * 100).toFixed(1) : 0;
	
	// Top performers
	$: topEight = divisions.slice(0, 8);
	$: bottomFive = divisions.slice(-5).reverse();

	async function drillDownDivision(division, count) {
		selectedDivision = { division, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(division)}`);
			let result = await response.json();
			divisionDetails = result.hosts || [];
		} catch (err) {
			console.error('Division drill-down error:', err);
			divisionDetails = generateMockHosts(division, Math.min(50, count));
		} finally {
			loading = false;
		}
	}
	
	function generateMockHosts(division, count) {
		const hosts = [];
		for (let i = 0; i < count; i++) {
			hosts.push({
				host: `${division.toLowerCase().replace(/\s/g, '-')}-host-${i + 1}.internal`,
				region: ['Americas', 'EMEA', 'APAC', 'LATAM'][Math.floor(Math.random() * 4)],
				country: ['United States', 'Germany', 'Japan', 'Brazil'][Math.floor(Math.random() * 4)],
				data_center: `DC-${Math.floor(Math.random() * 10) + 1}`,
				infrastructure_type: ['Virtual', 'Physical', 'Cloud', 'Container'][Math.floor(Math.random() * 4)],
				present_in_cmdb: Math.random() > 0.3 ? 'Yes' : 'No',
				tanium_coverage: Math.random() > 0.4 ? 'Tanium' : 'No Coverage'
			});
		}
		return hosts;
	}

	function closeDetails() {
		selectedDivision = null;
		divisionDetails = [];
	}
	
	function getDivisionStatus(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { 
			level: 'MEGA_STRUCTURE', 
			color: '#FF6B9D', 
			bgColor: '#FF6B9D20',
			resonance: '95.8 Hz'
		};
		if (percentage >= 50) return { 
			level: 'CORE_COMPLEX', 
			color: '#4ECDC4', 
			bgColor: '#4ECDC420',
			resonance: '72.3 Hz'
		};
		if (percentage >= 25) return { 
			level: 'CORE_MODULE', 
			color: '#95E77E', 
			bgColor: '#95E77E20',
			resonance: '45.7 Hz'
		};
		return { 
			level: 'QUANTUM_NODE', 
			color: '#FFE66D', 
			bgColor: '#FFE66D20',
			resonance: '21.2 Hz'
		};
	}
	
	function getDivisionSize(count) {
		if (count > 100000) return 'ENTERPRISE';
		if (count > 50000) return 'LARGE';
		if (count > 10000) return 'MEDIUM';
		if (count > 1000) return 'SMALL';
		return 'MINIMAL';
	}
	
	function formatNumber(num) {
		return new Intl.NumberFormat('en-US').format(num);
	}
	
	function truncateText(text, maxLength = 20) {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}
	
	function getStructuralIntegrity() {
		// Calculate a mock structural integrity value
		const avgLoad = divisions.reduce((sum, [_, count]) => sum + count, 0) / (divisions.length || 1);
		return Math.min(100, (avgLoad / 1000)).toFixed(0);
	}
	
	function getQuantumResonance() {
		// Calculate mock quantum resonance
		const topLoad = topDivision[1];
		return (30 + (topLoad / maxHosts) * 60).toFixed(1);
	}
</script>

<div class="division-interface">
	<!-- Top Metrics -->
	<div class="metrics-header">
		<div class="metric-card">
			<div class="metric-icon">🏢</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FF6B9D">{divisionCount}</div>
				<div class="metric-label">DIVISIONS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">💻</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #4ECDC4">{formatNumber(totalHosts)}</div>
				<div class="metric-label">TOTAL HOSTS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">🏆</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #95E77E; font-size: 1rem" title={topDivision[0]}>
					{truncateText(topDivision[0], 18).toUpperCase()}
				</div>
				<div class="metric-label">TOP DIVISION</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📈</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FFE66D">{concentration}%</div>
				<div class="metric-label">TOP CONCENTRATION</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">⚛️</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #C77DFF">{formatNumber(avgHostsPerDivision)}</div>
				<div class="metric-label">AVG HOSTS/DIV</div>
			</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content-layout">
		<!-- Left: Organizational Chart -->
		<div class="org-panel">
			<div class="panel-header">
				<h2>DIVISION QUANTUM ARCHITECTURE</h2>
				<div class="header-controls">
					<div class="integrity-meter">
						<span class="meter-label">STRUCTURAL INTEGRITY</span>
						<div class="meter-bar">
							<div class="meter-fill" style="width: {getStructuralIntegrity()}%; background: linear-gradient(90deg, #FF6B9D, #4ECDC4)"></div>
						</div>
						<span class="meter-value">{getStructuralIntegrity()}%</span>
					</div>
					<input type="text"
						   bind:value={searchTerm}
						   placeholder="Search divisions..."
						   class="search-input"/>
				</div>
			</div>
			
			{#if loading && !selectedDivision}
				<div class="loading-state">
					<div class="quantum-loader">
						<div class="quantum-core"></div>
						<div class="quantum-ring ring-1"></div>
						<div class="quantum-ring ring-2"></div>
						<div class="quantum-ring ring-3"></div>
					</div>
					<p>ANALYZING ORGANIZATIONAL STRUCTURE...</p>
				</div>
			{:else if error && !selectedDivision}
				<div class="error-state">
					<div class="error-icon">⚠️</div>
					<p>{error}</p>
					<button class="retry-btn" on:click={loadData}>RETRY</button>
				</div>
			{:else if selectedDivision}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedDivision.division.toUpperCase()}</h3>
							<div class="division-stats">
								<span>{formatNumber(selectedDivision.count)} HOSTS</span>
								<span>•</span>
								<span>{((selectedDivision.count / totalHosts) * 100).toFixed(2)}% OF TOTAL</span>
								<span>•</span>
								<span>{getDivisionSize(selectedDivision.count)} DIVISION</span>
							</div>
						</div>
						<button class="close-btn" on:click={closeDetails}>✕</button>
					</div>
					<div class="hosts-container">
						<table class="hosts-table">
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>REGION</th>
									<th>COUNTRY</th>
									<th>DATA CENTER</th>
									<th>TYPE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each divisionDetails as host}
									<tr>
										<td class="hostname" title={host.host}>{truncateText(host.host, 25)}</td>
										<td>{host.region || 'UNKNOWN'}</td>
										<td>{host.country || 'UNKNOWN'}</td>
										<td>{host.data_center || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>
											<span class="status-dot {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												●
											</span>
										</td>
										<td>
											<span class="status-dot {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
												●
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="org-visualization">
					<!-- Quantum Architecture Visualization -->
					<div class="quantum-architecture">
						<div class="quantum-header">
							<span class="quantum-label">QUANTUM RESONANCE</span>
							<span class="quantum-value">{getQuantumResonance()} Hz</span>
						</div>
						
						<!-- Quantum Flow Lines -->
						<svg class="quantum-flow-svg" viewBox="0 0 100 300">
							{#each quantumFlow as line}
								<rect x="{line.x}" y="{line.y * 3}" 
									  width="{line.width}" height="50" 
									  fill="url(#quantumGradient)" 
									  opacity="0.6"/>
							{/each}
							<defs>
								<linearGradient id="quantumGradient" x1="0%" y1="0%" x2="0%" y2="100%">
									<stop offset="0%" style="stop-color:#4ECDC4;stop-opacity:0" />
									<stop offset="50%" style="stop-color:#4ECDC4;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#4ECDC4;stop-opacity:0" />
								</linearGradient>
							</defs>
						</svg>
						
						<!-- Division Rankings -->
						<div class="division-rankings">
							{#each topEight as [division, count], i}
								{@const status = getDivisionStatus(count)}
								<div class="rank-item" on:click={() => drillDownDivision(division, count)}>
									<div class="rank-number">#{i + 1}</div>
									<div class="rank-division">
										<div class="division-icon">▲</div>
										<div class="division-name" title={division}>
											{truncateText(division, 20).toUpperCase()}
										</div>
									</div>
									<div class="rank-architecture">
										<span class="architecture-type" 
											  style="color: {status.color}; background: {status.bgColor}">
											{status.level}
										</span>
									</div>
									<div class="rank-metrics">
										<div class="metric-hosts" style="color: {status.color}">
											{formatNumber(count)}
										</div>
										<div class="metric-bar">
											<div class="bar-fill" 
												 style="width: {(count/maxHosts)*100}%; 
														background: {status.color}"></div>
										</div>
									</div>
									<div class="rank-resonance" style="color: {status.color}">
										{status.resonance}
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Middle: Analytics -->
		<div class="analytics-panel">
			<!-- Distribution Chart -->
			<div class="chart-box">
				<h3>HOST DISTRIBUTION BY DIVISION</h3>
				<div class="distribution-bars">
					{#each topEight.slice(0, 5) as [division, count], i}
						{@const percentage = Math.min(100, (count / maxHosts) * 100)}
						{@const status = getDivisionStatus(count)}
						<div class="dist-item" on:click={() => drillDownDivision(division, count)}>
							<div class="dist-rank">#{i + 1}</div>
							<div class="dist-name" title={division}>{truncateText(division, 12).toUpperCase()}</div>
							<div class="dist-bar">
								<div class="dist-fill" 
									 style="width: {percentage}%; 
											background: linear-gradient(90deg, {status.color}40, {status.color})">
									<span class="dist-value">{formatNumber(count)}</span>
								</div>
							</div>
							<div class="dist-percent">{((count/totalHosts)*100).toFixed(1)}%</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Size Distribution -->
			<div class="chart-box">
				<h3>DIVISION SIZE DISTRIBUTION</h3>
				<div class="size-chart">
					{#each ['ENTERPRISE', 'LARGE', 'MEDIUM', 'SMALL', 'MINIMAL'] as size, i}
						{@const count = divisions.filter(([_, c]) => getDivisionSize(c) === size).length}
						{@const colors = ['#FF6B9D', '#4ECDC4', '#95E77E', '#FFE66D', '#C77DFF']}
						<div class="size-item">
							<div class="size-label">{size}</div>
							<div class="size-count" style="color: {colors[i]}">{count}</div>
							<div class="size-bar">
								<div class="size-fill" 
									 style="height: {divisionCount > 0 ? (count / divisionCount) * 100 : 0}%; 
											background: {colors[i]}">
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Coverage Stats -->
			<div class="chart-box">
				<h3>COVERAGE STATISTICS</h3>
				<div class="coverage-stats">
					<div class="coverage-item">
						<span class="coverage-label">Divisions >10K hosts</span>
						<span class="coverage-value" style="color: #FF6B9D">
							{divisions.filter(([_, c]) => c > 10000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Divisions >50K hosts</span>
						<span class="coverage-value" style="color: #4ECDC4">
							{divisions.filter(([_, c]) => c > 50000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Divisions >100K hosts</span>
						<span class="coverage-value" style="color: #95E77E">
							{divisions.filter(([_, c]) => c > 100000).length}
						</span>
					</div>
				</div>
			</div>
		</div>
		
		<!-- Right: Division List -->
		<div class="list-panel">
			<div class="panel-header">
				<h3>ALL DIVISIONS</h3>
				<span class="division-count">{divisions.length} ACTIVE</span>
			</div>
			<div class="division-list">
				<table class="divisions-table">
					<thead>
						<tr>
							<th>#</th>
							<th>DIVISION</th>
							<th>HOSTS</th>
							<th>ENERGY</th>
							<th>RESONANCE</th>
						</tr>
					</thead>
					<tbody>
						{#each divisions as [division, count], i}
							{@const status = getDivisionStatus(count)}
							<tr on:click={() => drillDownDivision(division, count)}>
								<td class="rank">{i + 1}</td>
								<td class="division-name" title={division}>
									<span class="status-indicator" style="background: {status.color}"></span>
									{truncateText(division, 18).toUpperCase()}
								</td>
								<td class="host-count" style="color: {status.color}">
									{formatNumber(count)}
								</td>
								<td>
									<div class="energy-bar">
										<div class="energy-fill" 
											 style="width: {(count/maxHosts)*100}%; 
													background: {status.color}"></div>
									</div>
								</td>
								<td class="resonance" style="color: {status.color}">
									{status.resonance}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>
</div>

<style>
	.division-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		display: flex;
		flex-direction: column;
		padding: 1rem;
		gap: 1rem;
		overflow: hidden;
	}
	
	/* Metrics Header */
	.metrics-header {
		display: flex;
		gap: 1rem;
		flex-shrink: 0;
	}
	
	.metric-card {
		flex: 1;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(139, 233, 253, 0.2);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		gap: 1rem;
		align-items: center;
		transition: all 0.3s ease;
	}
	
	.metric-card:hover {
		background: rgba(255, 255, 255, 0.05);
		transform: translateY(-2px);
	}
	
	.metric-icon {
		font-size: 2rem;
		filter: saturate(1.5);
	}
	
	.metric-content {
		flex: 1;
		min-width: 0;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: 700;
		font-family: 'SF Mono', 'Monaco', monospace;
		margin-bottom: 0.25rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
		font-weight: 600;
	}
	
	/* Content Layout */
	.content-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 380px 320px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Org Panel */
	.org-panel {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(189, 147, 249, 0.2);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		flex-shrink: 0;
	}
	
	.panel-header h2, .panel-header h3 {
		margin: 0;
		font-size: 0.9rem;
		font-weight: 400;
		letter-spacing: 0.1em;
		color: #FF6B9D;
	}
	
	.header-controls {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.integrity-meter {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.meter-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
		white-space: nowrap;
	}
	
	.meter-bar {
		width: 80px;
		height: 6px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		overflow: hidden;
	}
	
	.meter-fill {
		height: 100%;
		transition: width 0.5s ease;
		border-radius: 3px;
	}
	
	.meter-value {
		font-size: 0.7rem;
		color: #4ECDC4;
		font-weight: 700;
		min-width: 35px;
	}
	
	.search-input {
		padding: 0.5rem 1rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(139, 233, 253, 0.3);
		border-radius: 8px;
		color: #FFFFFF;
		font-size: 0.8rem;
		width: 180px;
		transition: all 0.3s ease;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #4ECDC4;
		background: rgba(0, 0, 0, 0.8);
	}
	
	.org-visualization {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
	}
	
	/* Quantum Architecture */
	.quantum-architecture {
		flex: 1;
		position: relative;
		background: linear-gradient(180deg, rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.2));
		border-radius: 10px;
		border: 1px solid rgba(78, 205, 196, 0.2);
		overflow: hidden;
	}
	
	.quantum-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		background: rgba(0, 0, 0, 0.6);
		border-bottom: 1px solid rgba(78, 205, 196, 0.2);
	}
	
	.quantum-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
	}
	
	.quantum-value {
		font-size: 1rem;
		color: #4ECDC4;
		font-weight: 700;
		font-family: 'SF Mono', 'Monaco', monospace;
	}
	
	.quantum-flow-svg {
		position: absolute;
		top: 60px;
		left: 0;
		width: 100%;
		height: calc(100% - 60px);
		opacity: 0.3;
		pointer-events: none;
	}
	
	.division-rankings {
		position: relative;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		z-index: 1;
	}
	
	.rank-item {
		display: grid;
		grid-template-columns: 35px 1fr auto 150px 60px;
		gap: 1rem;
		align-items: center;
		padding: 0.8rem;
		background: rgba(0, 0, 0, 0.6);
		border-radius: 8px;
		border: 1px solid rgba(255, 255, 255, 0.1);
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.rank-item:hover {
		background: rgba(78, 205, 196, 0.1);
		transform: translateX(4px);
		border-color: rgba(78, 205, 196, 0.3);
	}
	
	.rank-number {
		font-size: 0.9rem;
		font-weight: 700;
		color: #FF6B9D;
	}
	
	.rank-division {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.division-icon {
		color: #4ECDC4;
		font-size: 1rem;
	}
	
	.division-name {
		font-size: 0.75rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.9);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.rank-architecture {
		display: flex;
	}
	
	.architecture-type {
		font-size: 0.65rem;
		padding: 0.3rem 0.6rem;
		border-radius: 6px;
		font-weight: 700;
		letter-spacing: 0.05em;
		white-space: nowrap;
	}
	
	.rank-metrics {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}
	
	.metric-hosts {
		font-size: 0.85rem;
		font-weight: 700;
		font-family: 'SF Mono', 'Monaco', monospace;
		text-align: right;
	}
	
	.metric-bar {
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
		border-radius: 2px;
	}
	
	.rank-resonance {
		font-size: 0.7rem;
		font-weight: 600;
		text-align: right;
		white-space: nowrap;
	}
	
	/* Analytics Panel */
	.analytics-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chart-box {
		flex: 1;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(139, 233, 253, 0.2);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
	}
	
	.chart-box h3 {
		margin: 0 0 1rem 0;
		font-size: 0.8rem;
		color: #4ECDC4;
		font-weight: 400;
		letter-spacing: 0.1em;
	}
	
	.distribution-bars {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	
	.dist-item {
		display: grid;
		grid-template-columns: 30px 100px 1fr 50px;
		gap: 0.5rem;
		align-items: center;
		cursor: pointer;
		transition: all 0.2s ease;
		padding: 0.2rem;
		border-radius: 4px;
	}
	
	.dist-item:hover {
		background: rgba(139, 233, 253, 0.05);
		transform: translateX(2px);
	}
	
	.dist-rank {
		font-size: 0.7rem;
		color: #FF6B9D;
		font-weight: 700;
	}
	
	.dist-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.9);
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.dist-bar {
		height: 20px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.dist-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.5rem;
		transition: width 0.5s ease;
		border-radius: 4px;
	}
	
	.dist-value {
		font-size: 0.65rem;
		color: #FFFFFF;
		font-weight: 700;
		text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
		white-space: nowrap;
	}
	
	.dist-percent {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		text-align: right;
		font-weight: 600;
	}
	
	/* Size Chart */
	.size-chart {
		display: flex;
		align-items: flex-end;
		justify-content: space-around;
		height: 120px;
		padding: 0.5rem 0;
	}
	
	.size-item {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.4rem;
	}
	
	.size-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.7);
		writing-mode: vertical-lr;
		text-align: center;
		font-weight: 600;
	}
	
	.size-count {
		font-size: 1rem;
		font-weight: 700;
	}
	
	.size-bar {
		width: 35px;
		height: 70px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px 4px 0 0;
		display: flex;
		align-items: flex-end;
		overflow: hidden;
	}
	
	.size-fill {
		width: 100%;
		border-radius: 4px 4px 0 0;
		transition: height 0.5s ease;
	}
	
	/* Coverage Stats */
	.coverage-stats {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}
	
	.coverage-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.6rem;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 8px;
		transition: all 0.2s ease;
	}
	
	.coverage-item:hover {
		background: rgba(0, 0, 0, 0.6);
		transform: translateX(2px);
	}
	
	.coverage-label {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
		font-weight: 500;
	}
	
	.coverage-value {
		font-size: 1.1rem;
		font-weight: 700;
		font-family: 'SF Mono', 'Monaco', monospace;
	}
	
	/* List Panel */
	.list-panel {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(189, 147, 249, 0.2);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		padding: 1rem;
	}
	
	.division-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
	}
	
	.division-list {
		flex: 1;
		overflow-y: auto;
		margin-top: 1rem;
	}
	
	.divisions-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.divisions-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.95);
		z-index: 10;
	}
	
	.divisions-table th {
		padding: 0.6rem 0.5rem;
		text-align: left;
		font-size: 0.65rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.divisions-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.divisions-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.08);
		transform: translateX(2px);
	}
	
	.divisions-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.85);
	}
	
	.rank {
		color: #FF6B9D;
		font-weight: 700;
		font-size: 0.7rem;
		width: 30px;
	}
	
	.division-list .division-name {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.host-count {
		font-family: 'SF Mono', 'Monaco', monospace;
		font-weight: 700;
	}
	
	.energy-bar {
		width: 50px;
		height: 5px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		overflow: hidden;
	}
	
	.energy-fill {
		height: 100%;
		transition: width 0.5s ease;
		border-radius: 3px;
	}
	
	.resonance {
		font-size: 0.65rem;
		font-weight: 600;
		white-space: nowrap;
	}
	
	/* Detail View */
	.detail-view {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: start;
		margin-bottom: 1rem;
		flex-shrink: 0;
	}
	
	.detail-header h3 {
		margin: 0 0 0.25rem 0;
		font-size: 1.1rem;
		color: #FF6B9D;
		font-weight: 600;
	}
	
	.division-stats {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
		display: flex;
		gap: 0.5rem;
		font-weight: 500;
	}
	
	.close-btn {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.3);
		color: #FFFFFF;
		width: 32px;
		height: 32px;
		border-radius: 8px;
		font-size: 1.1rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}
	
	.close-btn:hover {
		background: rgba(255, 121, 198, 0.2);
		border-color: #FF6B9D;
		transform: rotate(90deg);
	}
	
	.hosts-container {
		flex: 1;
		overflow-y: auto;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 10px;
		padding: 1rem;
	}
	
	.hosts-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.hosts-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.95);
		z-index: 10;
	}
	
	.hosts-table th {
		padding: 0.6rem 0.5rem;
		text-align: left;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
		letter-spacing: 0.05em;
		font-weight: 600;
	}
	
	.hosts-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.85);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.hostname {
		font-family: 'SF Mono', 'Monaco', monospace;
		color: #4ECDC4;
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.status-dot {
		font-size: 0.9rem;
		display: inline-block;
		text-align: center;
	}
	
	.status-dot.active {
		color: #95E77E;
		text-shadow: 0 0 8px #95E77E;
	}
	
	.status-dot.inactive {
		color: #FF5555;
		opacity: 0.6;
	}
	
	/* Loading State */
	.loading-state, .error-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.quantum-loader {
		position: relative;
		width: 120px;
		height: 120px;
	}
	
	.quantum-core {
		position: absolute;
		width: 30px;
		height: 30px;
		top: 45px;
		left: 45px;
		background: linear-gradient(135deg, #FF6B9D, #4ECDC4);
		border-radius: 50%;
		animation: corePulse 2s ease-in-out infinite;
	}
	
	.quantum-ring {
		position: absolute;
		border: 2px solid;
		border-radius: 50%;
		animation: ringRotate 3s linear infinite;
	}
	
	.ring-1 {
		width: 120px;
		height: 120px;
		border-color: #FF6B9D;
		opacity: 0.6;
	}
	
	.ring-2 {
		width: 80px;
		height: 80px;
		top: 20px;
		left: 20px;
		border-color: #4ECDC4;
		animation-direction: reverse;
		opacity: 0.6;
	}
	
	.ring-3 {
		width: 50px;
		height: 50px;
		top: 35px;
		left: 35px;
		border-color: #95E77E;
		animation-duration: 2s;
		opacity: 0.6;
	}
	
	@keyframes corePulse {
		0%, 100% { transform: scale(1); opacity: 0.8; }
		50% { transform: scale(1.2); opacity: 1; }
	}
	
	@keyframes ringRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.loading-state p, .error-state p {
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.9rem;
		letter-spacing: 0.2em;
		font-weight: 600;
	}
	
	.error-icon {
		font-size: 3rem;
	}
	
	.retry-btn {
		padding: 0.6rem 1.5rem;
		background: linear-gradient(135deg, #FF6B9D, #FF6B9D80);
		border: 1px solid #FF6B9D;
		color: #FFFFFF;
		border-radius: 8px;
		font-size: 0.8rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.retry-btn:hover {
		background: linear-gradient(135deg, #FF6B9D, #FF6B9DCC);
		transform: translateY(-2px);
		box-shadow: 0 4px 15px rgba(255, 107, 157, 0.4);
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 8px;
		height: 8px;
	}
	
	::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb {
		background: linear-gradient(to bottom, #FF6B9D, #4ECDC4);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(to bottom, #FF6B9DCC, #4ECDC4CC);
	}
	
	/* Responsive Design */
	@media (max-width: 1400px) {
		.content-layout {
			grid-template-columns: 1fr 300px 280px;
		}
		
		.metric-value {
			font-size: 1.2rem;
		}
	}
	
	@media (max-width: 1200px) {
		.content-layout {
			grid-template-columns: 1fr;
			grid-template-rows: auto 1fr auto;
		}
		
		.analytics-panel {
			display: grid;
			grid-template-columns: repeat(3, 1fr);
		}
		
		.list-panel {
			display: none;
		}
	}
	
	@media (max-width: 768px) {
		.metrics-header {
			flex-wrap: wrap;
		}
		
		.metric-card {
			min-width: calc(50% - 0.5rem);
		}
		
		.analytics-panel {
			grid-template-columns: 1fr;
		}
		
		.header-controls {
			flex-direction: column;
			align-items: stretch;
		}
		
		.integrity-meter {
			width: 100%;
		}
		
		.meter-bar {
			flex: 1;
		}
	}
</style>