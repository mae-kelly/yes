<!-- SourceTables.svelte - Enhanced with Quantum Wave Animation -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let sourceDetails = [];
	let searchTerm = '';
	
	// Animation states for the city visualization
	let animationFrame = null;
	let rotationDegree = 0;
	let synapticActivity = [];
	let quantumWaves = [];
	let dataNodes = [];
	let energyPulse = 0;
	let cityGrid = [];
	let quantumLayers = [];
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Failed to load source tables:', err);
			loading = false;
		}
		
		// Initialize city grid like BusinessUnitMetrics
		for (let x = 0; x < 20; x++) {
			cityGrid[x] = [];
			for (let z = 0; z < 20; z++) {
				cityGrid[x][z] = {
					elevation: Math.sin(x * 0.3) * Math.cos(z * 0.3) * 10,
					energy: Math.random(),
					active: Math.random() > 0.3,
					pulse: Math.random() * Math.PI * 2
				};
			}
		}
		
		// Create quantum layers (vertical slices through the architecture)
		for (let i = 0; i < 10; i++) {
			quantumLayers.push({
				depth: i * 50,
				opacity: 1 - (i * 0.08),
				frequency: 50 + i * 50,
				particles: generateQuantumParticles(30),
				wave: []
			});
		}
		
		// Initialize animations
		for (let i = 0; i < 50; i++) {
			synapticActivity.push(50 + Math.random() * 30);
			quantumWaves.push({
				amplitude: 20 + Math.random() * 30,
				frequency: 0.01 + Math.random() * 0.02,
				phase: Math.random() * Math.PI * 2,
				color: ['#BD93F9', '#8BE9FD', '#50FA7B'][Math.floor(Math.random() * 3)]
			});
		}
		
		// Initialize data nodes for 3D effect
		for (let i = 0; i < 15; i++) {
			dataNodes.push({
				x: Math.random() * 100,
				y: Math.random() * 100,
				z: Math.random() * 50,
				vx: (Math.random() - 0.5) * 0.5,
				vy: (Math.random() - 0.5) * 0.5,
				vz: (Math.random() - 0.5) * 0.3,
				size: 2 + Math.random() * 4,
				color: ['#BD93F9', '#8BE9FD', '#50FA7B', '#FFB86C'][Math.floor(Math.random() * 4)],
				pulse: Math.random() * Math.PI * 2
			});
		}
		
		// Start animations
		const animate = () => {
			const time = Date.now() * 0.001;
			rotationDegree = (rotationDegree + 0.2) % 360;
			energyPulse = (energyPulse + 0.05) % (Math.PI * 2);
			
			// Update city grid cells
			cityGrid.forEach((row, x) => {
				row.forEach((cell, z) => {
					cell.energy = 0.5 + Math.sin(time + cell.pulse) * 0.5;
					cell.elevation = Math.sin(x * 0.3 + time * 0.2) * Math.cos(z * 0.3 + time * 0.1) * 10;
				});
			});
			
			// Update quantum layers
			quantumLayers.forEach((layer, i) => {
				layer.particles.forEach(p => {
					p.x = (p.x + p.vx + 100) % 100;
					p.y = (p.y + p.vy + 100) % 100;
					p.z = (p.z + p.vz + 100) % 100;
					p.energy = 0.5 + Math.sin(time * 2 + i) * 0.5;
				});
				
				// Generate wave pattern
				layer.wave = [];
				for (let j = 0; j < 50; j++) {
					layer.wave.push(Math.sin(time + j * 0.2 + i * 0.5) * 20);
				}
			});
			
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	});
	
	function generateQuantumParticles(count) {
		let particles = [];
		for (let i = 0; i < count; i++) {
			particles.push({
				x: Math.random() * 100,
				y: Math.random() * 100,
				z: Math.random() * 100,
				vx: (Math.random() - 0.5) * 0.5,
				vy: (Math.random() - 0.5) * 0.5,
				vz: (Math.random() - 0.5) * 0.5,
				energy: Math.random(),
				color: `hsl(${280 + Math.random() * 60}, 100%, ${60 + Math.random() * 20}%)`
			});
		}
		return particles;
	}
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});

	$: sources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalHosts = sources.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = sources.length > 0 ? Math.max(...sources.map(([,c]) => c)) : 1;
	$: avgHostsPerSource = sources.length > 0 ? Math.round(totalHosts / sources.length) : 0;
	
	// Key metrics
	$: sourceCount = sources.length;
	$: topSource = sources[0] || ['N/A', 0];
	$: concentration = topSource[1] > 0 ? ((topSource[1] / totalHosts) * 100).toFixed(1) : 0;
	
	// Top performers
	$: topFive = sources.slice(0, 5);

	async function drillDownSource(source, count) {
		selectedSource = { source, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			sourceDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Source drill-down error:', err);
			sourceDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedSource = null;
		sourceDetails = [];
	}
	
	function getSourceStatus(count) {
		let percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#BD93F9' };
		if (percentage >= 50) return { level: 'HIGH', color: '#8BE9FD' };
		if (percentage >= 25) return { level: 'MEDIUM', color: '#50FA7B' };
		return { level: 'LOW', color: '#FFB86C' };
	}
	
	function getSourceSize(count) {
		if (count > 10000) return 'MASSIVE';
		if (count > 5000) return 'LARGE';
		if (count > 1000) return 'MEDIUM';
		if (count > 100) return 'SMALL';
		return 'MINIMAL';
	}
	
	function formatNumber(num) {
		return new Intl.NumberFormat('en-US').format(num);
	}
</script>

<div class="source-interface">
	<!-- Quantum City Background like BusinessUnitMetrics -->
	<div class="quantum-city">
		<!-- City Grid Base -->
		<div class="city-grid-base">
			{#each cityGrid as row, x}
				{#each row as cell, z}
					{#if cell.active}
						<div class="grid-cell"
							 style="left: {x * 5}%; 
									top: {z * 5}%;
									height: {5 + cell.elevation}px;
									background: linear-gradient(180deg, 
										rgba(189, 147, 249, {cell.energy * 0.3}), 
										rgba(139, 233, 253, {cell.energy * 0.1}));
									box-shadow: 0 0 {10 * cell.energy}px rgba(189, 147, 249, {cell.energy * 0.5})">
						</div>
					{/if}
				{/each}
			{/each}
		</div>
		
		<!-- Quantum Layers -->
		{#each quantumLayers as layer}
			<div class="quantum-layer"
				 style="transform: translateZ({layer.depth}px); opacity: {layer.opacity}">
				<svg class="layer-waves" viewBox="0 0 100 100">
					<path d="M 0,50 {layer.wave.map((y, i) => `L ${i * 2},${50 + y}`).join(' ')}"
						  stroke="rgba(189, 147, 249, 0.3)"
						  stroke-width="0.5"
						  fill="none"/>
				</svg>
				{#each layer.particles as particle}
					<div class="quantum-particle"
						 style="left: {particle.x}%; 
								top: {particle.y}%;
								background: {particle.color};
								opacity: {particle.energy};
								box-shadow: 0 0 {5 * particle.energy}px {particle.color}">
					</div>
				{/each}
			</div>
		{/each}
	</div>
	
	<!-- Top Metrics -->
	<div class="metrics-header">
		<div class="metric-card">
			<div class="metric-icon">📊</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #BD93F9">{sourceCount}</div>
				<div class="metric-label">SOURCES</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">💻</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #8BE9FD">{formatNumber(totalHosts)}</div>
				<div class="metric-label">TOTAL HOSTS</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">🔝</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #50FA7B; font-size: 1.2rem">
					{topSource[0].substring(0, 25).toUpperCase()}
				</div>
				<div class="metric-label">TOP SOURCE</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">📈</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FFB86C">{concentration}%</div>
				<div class="metric-label">TOP CONCENTRATION</div>
			</div>
		</div>
		<div class="metric-card">
			<div class="metric-icon">⚖️</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FF79C6">{formatNumber(avgHostsPerSource)}</div>
				<div class="metric-label">AVG HOSTS/SRC</div>
			</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content-layout">
		<!-- Left: Source Visualization -->
		<div class="org-panel">
			<div class="panel-header">
				<h2>SOURCE TABLE STRUCTURE</h2>
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="Search sources..."
					   class="search-input"/>
			</div>
			
			{#if loading && !selectedSource}
				<div class="loading-state">
					<div class="org-loader">
						<div class="org-node node-1"></div>
						<div class="org-node node-2"></div>
						<div class="org-node node-3"></div>
						<div class="org-node node-4"></div>
					</div>
					<p>ANALYZING SOURCE STRUCTURE...</p>
				</div>
			{:else if selectedSource}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3>{selectedSource.source.toUpperCase()}</h3>
							<div class="source-stats">
								<span>{formatNumber(selectedSource.count)} HOSTS</span>
								<span>•</span>
								<span>{((selectedSource.count / totalHosts) * 100).toFixed(2)}% OF TOTAL</span>
								<span>•</span>
								<span>{getSourceSize(selectedSource.count)} TABLE</span>
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
								{#each sourceDetails as host}
									<tr>
										<td class="hostname">{host.host}</td>
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
					<!-- Hierarchical Tree -->
					<div class="tree-container">
						<div class="tree-root">
							<div class="root-node">
								<div class="node-icon">📊</div>
								<div class="node-label">SOURCE TABLES</div>
								<div class="node-count">{formatNumber(totalHosts)} HOSTS</div>
							</div>
						</div>
						<div class="tree-branches">
							{#each topFive as [source, count], i}
								<div class="branch-container">
									<div class="branch-line"></div>
									<div class="source-node" 
										 style="border-color: {getSourceStatus(count).color}"
										 on:click={() => drillDownSource(source, count)}>
										<div class="node-header" style="background: {getSourceStatus(count).color}20">
											<span class="node-rank">#{i + 1}</span>
										</div>
										<div class="node-body">
											<div class="node-name">{source.substring(0, 20).toUpperCase()}</div>
											<div class="node-metrics">
												<span class="node-hosts" style="color: {getSourceStatus(count).color}">
													{formatNumber(count)}
												</span>
												<span class="node-percent">{((count / totalHosts) * 100).toFixed(1)}%</span>
											</div>
											<div class="node-bar">
												<div class="bar-fill" style="width: {((count / totalHosts) * 100).toFixed(1)}%; background: {getSourceStatus(count).color}"></div>
											</div>
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
					
					<!-- Bubble Chart -->
					<div class="bubble-chart">
						<svg viewBox="0 0 400 300">
							{#each sources.slice(0, 15) as [source, count], i}
								<g class="bubble-group" on:click={() => drillDownSource(source, count)}>
									<circle cx="{50 + (i % 5) * 75}" cy="{50 + Math.floor(i / 5) * 80}" 
											r="{Math.sqrt(count / maxHosts) * 40}" 
											fill="{getSourceStatus(count).color}" opacity="0.3"/>
									<circle cx="{50 + (i % 5) * 75}" cy="{50 + Math.floor(i / 5) * 80}" 
											r="{Math.sqrt(count / maxHosts) * 40 * 0.7}" 
											fill="{getSourceStatus(count).color}" opacity="0.6"/>
									<text x="{50 + (i % 5) * 75}" y="{50 + Math.floor(i / 5) * 80}" 
										  text-anchor="middle" 
										  fill="#FFFFFF" font-size="9" font-weight="600">
										{formatNumber(count)}
									</text>
								</g>
							{/each}
						</svg>
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Middle: Analytics -->
		<div class="analytics-panel">
			<!-- Distribution Chart -->
			<div class="chart-box">
				<h3>HOST DISTRIBUTION BY SOURCE</h3>
				<div class="distribution-bars">
					{#each topFive as [source, count], i}
						<div class="dist-item" on:click={() => drillDownSource(source, count)}>
							<div class="dist-rank">#{i + 1}</div>
							<div class="dist-name">{source.substring(0, 12).toUpperCase()}</div>
							<div class="dist-bar">
								<div class="dist-fill" 
									 style="width: {(count / maxHosts) * 100}%; 
											background: linear-gradient(90deg, {getSourceStatus(count).color}40, {getSourceStatus(count).color})">
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
				<h3>SOURCE SIZE DISTRIBUTION</h3>
				<div class="size-chart">
					{#each ['MASSIVE', 'LARGE', 'MEDIUM', 'SMALL', 'MINIMAL'] as size, i}
						<div class="size-item">
							<div class="size-label">{size}</div>
							<div class="size-count" style="color: {['#BD93F9', '#8BE9FD', '#50FA7B', '#FFB86C', '#FF79C6'][i]}">
								{sources.filter(([_, c]) => getSourceSize(c) === size).length}
							</div>
							<div class="size-bar">
								<div class="size-fill" 
									 style="height: {(sources.filter(([_, c]) => getSourceSize(c) === size).length / sourceCount) * 100}%; 
											background: {['#BD93F9', '#8BE9FD', '#50FA7B', '#FFB86C', '#FF79C6'][i]}">
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
						<span class="coverage-label">Sources with >1000 hosts</span>
						<span class="coverage-value" style="color: #BD93F9">
							{sources.filter(([_, c]) => c > 1000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Sources with >5000 hosts</span>
						<span class="coverage-value" style="color: #8BE9FD">
							{sources.filter(([_, c]) => c > 5000).length}
						</span>
					</div>
					<div class="coverage-item">
						<span class="coverage-label">Sources with >10000 hosts</span>
						<span class="coverage-value" style="color: #50FA7B">
							{sources.filter(([_, c]) => c > 10000).length}
						</span>
					</div>
				</div>
			</div>
		</div>
		
		<!-- Right: Source List -->
		<div class="list-panel">
			<div class="panel-header">
				<h3>ALL SOURCES</h3>
				<span class="source-count">{sources.length} TOTAL</span>
			</div>
			<div class="source-list">
				<table class="sources-table">
					<thead>
						<tr>
							<th>#</th>
							<th>SOURCE</th>
							<th>HOSTS</th>
							<th>SIZE</th>
							<th>STATUS</th>
						</tr>
					</thead>
					<tbody>
						{#each sources as [source, count], i}
							<tr on:click={() => drillDownSource(source, count)}>
								<td class="rank">{i + 1}</td>
								<td class="source-name">
									<span class="status-indicator" style="background: {getSourceStatus(count).color}"></span>
									{source.substring(0, 25).toUpperCase()}
								</td>
								<td class="host-count" style="color: {getSourceStatus(count).color}">
									{formatNumber(count)}
								</td>
								<td>
									<span class="size-badge" style="color: {getSourceStatus(count).color}">
										{getSourceSize(count)}
									</span>
								</td>
								<td>
									<span class="status-badge" style="color: {getSourceStatus(count).color}; border-color: {getSourceStatus(count).color}">
										{getSourceStatus(count).level}
									</span>
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
	.source-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		display: flex;
		flex-direction: column;
		padding: 1rem;
		gap: 1rem;
		overflow: hidden;
		position: relative;
	}
	
	/* Quantum City Background */
	.quantum-city {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		transform-style: preserve-3d;
	}
	
	.city-grid-base {
		position: absolute;
		width: 100%;
		height: 100%;
		transform: rotateX(60deg) translateZ(-100px);
		opacity: 0.3;
	}
	
	.grid-cell {
		position: absolute;
		width: 4%;
		border: 1px solid rgba(189, 147, 249, 0.1);
	}
	
	.quantum-layer {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		transform-style: preserve-3d;
	}
	
	.layer-waves {
		position: absolute;
		width: 100%;
		height: 100%;
		opacity: 0.3;
	}
	
	.quantum-particle {
		position: absolute;
		width: 2px;
		height: 2px;
		border-radius: 50%;
	}
	
	/* Metrics Header */
	.metrics-header {
		display: flex;
		gap: 1rem;
		position: relative;
		z-index: 1;
	}
	
	.metric-card {
		flex: 1;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		gap: 1rem;
		align-items: center;
		backdrop-filter: blur(10px);
	}
	
	.metric-icon {
		font-size: 2rem;
	}
	
	.metric-content {
		flex: 1;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
		margin-bottom: 0.25rem;
	}
	
	.metric-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
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
		position: relative;
		z-index: 1;
	}
	
	/* Org Panel */
	.org-panel {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		backdrop-filter: blur(10px);
	}
	
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.panel-header h2, .panel-header h3 {
		margin: 0;
		font-size: 0.9rem;
		font-weight: 300;
		letter-spacing: 0.1em;
		color: #BD93F9;
	}
	
	.search-input {
		padding: 0.4rem 0.8rem;
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid rgba(139, 233, 253, 0.3);
		border-radius: 6px;
		color: #FFFFFF;
		font-size: 0.75rem;
		width: 180px;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #8BE9FD;
	}
	
	.org-visualization {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		position: relative;
	}
	
	/* Tree Container */
	.tree-container {
		flex: 1;
	}
	
	.tree-root {
		display: flex;
		justify-content: center;
		margin-bottom: 2rem;
	}
	
	.root-node {
		background: rgba(189, 147, 249, 0.1);
		border: 2px solid #BD93F9;
		border-radius: 10px;
		padding: 1rem 2rem;
		text-align: center;
	}
	
	.node-icon {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}
	
	.node-label {
		font-size: 0.8rem;
		color: #BD93F9;
		font-weight: 600;
		letter-spacing: 0.1em;
	}
	
	.node-count {
		font-size: 1rem;
		color: #FFFFFF;
		font-weight: 700;
		margin-top: 0.25rem;
	}
	
	.tree-branches {
		display: flex;
		justify-content: space-around;
		position: relative;
	}
	
	.branch-container {
		position: relative;
		flex: 1;
		max-width: 150px;
	}
	
	.branch-line {
		position: absolute;
		top: -2rem;
		left: 50%;
		width: 1px;
		height: 2rem;
		background: rgba(139, 233, 253, 0.3);
	}
	
	.source-node {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.3s ease;
		overflow: hidden;
	}
	
	.source-node:hover {
		transform: scale(1.05);
		background: rgba(139, 233, 253, 0.05);
	}
	
	.node-header {
		padding: 0.3rem;
		text-align: center;
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.node-rank {
		color: #FFFFFF;
	}
	
	.node-body {
		padding: 0.5rem;
	}
	
	.node-name {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.9);
		margin-bottom: 0.3rem;
		text-align: center;
	}
	
	.node-metrics {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.3rem;
		font-size: 0.7rem;
	}
	
	.node-hosts {
		font-weight: 700;
		font-family: 'Courier New', monospace;
	}
	
	.node-percent {
		color: rgba(255, 255, 255, 0.6);
	}
	
	.node-bar {
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	/* Bubble Chart */
	.bubble-chart {
		height: 180px;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 8px;
		padding: 0.5rem;
	}
	
	.bubble-chart svg {
		width: 100%;
		height: 100%;
	}
	
	.bubble-group {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.bubble-group:hover {
		transform: scale(1.1);
	}
	
	/* Analytics Panel */
	.analytics-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chart-box {
		flex: 1;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(139, 233, 253, 0.1);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		backdrop-filter: blur(10px);
	}
	
	.chart-box h3 {
		margin: 0 0 1rem 0;
		font-size: 0.75rem;
		color: #8BE9FD;
		font-weight: 300;
		letter-spacing: 0.1em;
	}
	
	.distribution-bars {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.dist-item {
		display: grid;
		grid-template-columns: 25px 100px 1fr 45px;
		gap: 0.5rem;
		align-items: center;
		cursor: pointer;
		transition: all 0.2s ease;
	}
	
	.dist-item:hover {
		transform: translateX(2px);
	}
	
	.dist-rank {
		font-size: 0.65rem;
		color: #BD93F9;
		font-weight: 600;
	}
	
	.dist-name {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.dist-bar {
		height: 18px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.dist-fill {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: 0 0.4rem;
		transition: width 0.5s ease;
	}
	
	.dist-value {
		font-size: 0.6rem;
		color: #FFFFFF;
		font-weight: 600;
	}
	
	.dist-percent {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		text-align: right;
	}
	
	/* Size Chart */
	.size-chart {
		display: flex;
		align-items: flex-end;
		justify-content: space-around;
		height: 100px;
	}
	
	.size-item {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.3rem;
	}
	
	.size-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		writing-mode: vertical-lr;
		text-align: center;
	}
	
	.size-count {
		font-size: 0.9rem;
		font-weight: 700;
	}
	
	.size-bar {
		width: 30px;
		height: 60px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 4px 4px 0 0;
		display: flex;
		align-items: flex-end;
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
		gap: 0.75rem;
	}
	
	.coverage-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 6px;
	}
	
	.coverage-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.coverage-value {
		font-size: 1rem;
		font-weight: 700;
		font-family: 'Courier New', monospace;
	}
	
	/* List Panel */
	.list-panel {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(189, 147, 249, 0.1);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		backdrop-filter: blur(10px);
	}
	
	.source-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	.source-list {
		flex: 1;
		overflow-y: auto;
	}
	
	.sources-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.sources-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.9);
		z-index: 10;
	}
	
	.sources-table th {
		padding: 0.5rem;
		text-align: left;
		font-size: 0.6rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.sources-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.sources-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.05);
	}
	
	.sources-table td {
		padding: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank {
		color: #BD93F9;
		font-weight: 600;
		font-size: 0.65rem;
	}
	
	.source-name {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.65rem;
	}
	
	.status-indicator {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.host-count {
		font-family: 'Courier New', monospace;
		font-weight: 600;
	}
	
	.size-badge {
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}
	
	.status-badge {
		font-size: 0.6rem;
		padding: 0.15rem 0.3rem;
		border: 1px solid;
		border-radius: 4px;
		font-weight: 600;
		letter-spacing: 0.03em;
	}
	
	/* Detail View */
	.detail-view {
		flex: 1;
		display: flex;
		flex-direction: column;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: start;
		margin-bottom: 1rem;
	}
	
	.detail-header h3 {
		margin: 0 0 0.25rem 0;
		font-size: 1.1rem;
		color: #BD93F9;
	}
	
	.source-stats {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		display: flex;
		gap: 0.5rem;
	}
	
	.close-btn {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		color: #FFFFFF;
		width: 28px;
		height: 28px;
		border-radius: 6px;
		font-size: 1rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}
	
	.close-btn:hover {
		background: rgba(189, 147, 249, 0.2);
		border-color: #BD93F9;
	}
	
	.hosts-container {
		flex: 1;
		overflow-y: auto;
		background: rgba(0, 0, 0, 0.3);
		border-radius: 8px;
		padding: 1rem;
	}
	
	.hosts-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.hosts-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.9);
		z-index: 10;
	}
	
	.hosts-table th {
		padding: 0.5rem;
		text-align: left;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		letter-spacing: 0.05em;
	}
	
	.hosts-table td {
		padding: 0.5rem;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.hostname {
		font-family: 'Courier New', monospace;
		color: #8BE9FD;
		font-size: 0.6rem;
	}
	
	.status-dot {
		font-size: 0.8rem;
	}
	
	.status-dot.active {
		color: #50FA7B;
	}
	
	.status-dot.inactive {
		color: #FF5555;
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
	
	.org-loader {
		position: relative;
		width: 100px;
		height: 100px;
	}
	
	.org-node {
		position: absolute;
		width: 20px;
		height: 20px;
		background: linear-gradient(135deg, #BD93F9, #8BE9FD);
		border-radius: 50%;
		animation: nodeFloat 2s ease-in-out infinite;
	}
	
	.node-1 {
		top: 0;
		left: 40px;
	}
	
	.node-2 {
		top: 30px;
		left: 10px;
		animation-delay: 0.5s;
	}
	
	.node-3 {
		top: 30px;
		left: 70px;
		animation-delay: 1s;
	}
	
	.node-4 {
		top: 70px;
		left: 40px;
		animation-delay: 1.5s;
	}
	
	@keyframes nodeFloat {
		0%, 100% { transform: scale(1); opacity: 0.5; }
		50% { transform: scale(1.2); opacity: 1; }
	}
	
	.loading-state p {
		color: rgba(255, 255, 255, 0.5);
		font-size: 0.8rem;
		letter-spacing: 0.2em;
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 6px;
	}
	
	::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.5);
	}
	
	::-webkit-scrollbar-thumb {
		background: rgba(189, 147, 249, 0.3);
		border-radius: 3px;
	}
	
	/* Responsive */
	@media (max-width: 1400px) {
		.content-layout {
			grid-template-columns: 1fr 300px 280px;
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
	}
</style>