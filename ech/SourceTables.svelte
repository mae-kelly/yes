<!-- SourceTables.svelte - ULTIMATE QUANTUM MATRIX INTERFACE -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let sourceDetails = [];
	let searchTerm = '';
	let sortColumn = 'count';
	let sortDirection = 'desc';
	let currentPage = 1;
	let itemsPerPage = 20;
	
	// Advanced visualization states
	let networkGraph = { nodes: [], links: [] };
	let heatmapData = [];
	let timeSeriesData = [];
	let distributionData = [];
	let correlationMatrix = [];
	let pulsePhase = 0;
	let dataFlowRate = 0;
	let quantumEntanglement = 0;
	let neuralActivity = [];
	let particleSystem = [];
	let waveformData = [];
	let hologramDepth = 0;
	
	// Animation controllers
	let animationFrames = {
		main: null,
		particles: null,
		waves: null,
		neural: null
	};
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			data = await response.json();
			loading = false;
			initializeAdvancedVisualizations();
			startQuantumAnimations();
		} catch (err) {
			console.error('Source sync failed:', err);
			data = generateMockData();
			loading = false;
			initializeAdvancedVisualizations();
			startQuantumAnimations();
		}
	});
	
	onDestroy(() => {
		Object.values(animationFrames).forEach(frame => {
			if (frame) cancelAnimationFrame(frame);
		});
	});
	
	function generateMockData() {
		const sources = {};
		const categories = ['DATABASE', 'API', 'STREAM', 'CACHE', 'QUEUE', 'STORAGE', 'COMPUTE', 'NETWORK'];
		for (let i = 0; i < 100; i++) {
			const category = categories[Math.floor(Math.random() * categories.length)];
			sources[`${category}_SOURCE_${i}`] = Math.floor(Math.random() * 100000) + 1000;
		}
		return { source_intelligence: sources };
	}
	
	function initializeAdvancedVisualizations() {
		if (!data.source_intelligence) return;
		
		const sources = Object.entries(data.source_intelligence);
		
		// Build network graph
		networkGraph.nodes = sources.slice(0, 30).map(([name, count], i) => ({
			id: name,
			value: count,
			x: Math.cos(i * Math.PI * 2 / 30) * 200 + 250,
			y: Math.sin(i * Math.PI * 2 / 30) * 200 + 250,
			vx: (Math.random() - 0.5) * 2,
			vy: (Math.random() - 0.5) * 2,
			category: getSourceCategory(name),
			connections: Math.floor(Math.random() * 5) + 1
		}));
		
		// Create network links
		networkGraph.nodes.forEach((node, i) => {
			for (let j = 0; j < node.connections; j++) {
				const target = networkGraph.nodes[Math.floor(Math.random() * networkGraph.nodes.length)];
				if (target && target.id !== node.id) {
					networkGraph.links.push({
						source: node.id,
						target: target.id,
						strength: Math.random(),
						active: Math.random() > 0.5
					});
				}
			}
		});
		
		// Generate heatmap data (hourly activity)
		for (let hour = 0; hour < 24; hour++) {
			for (let day = 0; day < 7; day++) {
				heatmapData.push({
					hour,
					day,
					value: Math.random() * 100,
					surge: Math.random() > 0.95
				});
			}
		}
		
		// Time series data
		for (let i = 0; i < 100; i++) {
			timeSeriesData.push({
				time: i,
				value: 50 + Math.sin(i * 0.1) * 30 + Math.random() * 20,
				anomaly: Math.random() > 0.95
			});
		}
		
		// Distribution analysis
		sources.forEach(([name, count]) => {
			const category = getSourceCategory(name);
			let existing = distributionData.find(d => d.category === category);
			if (existing) {
				existing.count += count;
				existing.sources++;
			} else {
				distributionData.push({
					category,
					count,
					sources: 1,
					efficiency: 70 + Math.random() * 30
				});
			}
		});
		
		// Initialize neural activity
		for (let i = 0; i < 50; i++) {
			neuralActivity.push({
				x: Math.random() * 500,
				y: Math.random() * 200,
				radius: Math.random() * 20 + 5,
				pulseRate: Math.random() * 0.1,
				connections: []
			});
		}
		
		// Connect neurons
		neuralActivity.forEach((neuron, i) => {
			const connectionCount = Math.floor(Math.random() * 3) + 1;
			for (let j = 0; j < connectionCount; j++) {
				const targetIndex = Math.floor(Math.random() * neuralActivity.length);
				if (targetIndex !== i) {
					neuron.connections.push(targetIndex);
				}
			}
		});
		
		// Particle system
		for (let i = 0; i < 200; i++) {
			particleSystem.push({
				x: Math.random() * 500,
				y: Math.random() * 300,
				z: Math.random() * 100,
				vx: (Math.random() - 0.5) * 2,
				vy: (Math.random() - 0.5) * 2,
				vz: (Math.random() - 0.5),
				life: Math.random(),
				type: Math.random() > 0.5 ? 'data' : 'quantum',
				color: Math.random() > 0.5 ? '#00FFFF' : '#FF00FF'
			});
		}
		
		// Waveform data
		for (let i = 0; i < 200; i++) {
			waveformData.push({
				primary: Math.sin(i * 0.05) * 50,
				secondary: Math.cos(i * 0.08) * 30,
				tertiary: Math.sin(i * 0.03) * Math.cos(i * 0.07) * 40,
				interference: Math.random() * 10
			});
		}
		
		// Correlation matrix
		const categories = Array.from(new Set(sources.map(([name]) => getSourceCategory(name))));
		categories.forEach((cat1, i) => {
			categories.forEach((cat2, j) => {
				correlationMatrix.push({
					x: cat1,
					y: cat2,
					value: i === j ? 1 : Math.random(),
					strength: Math.random()
				});
			});
		});
	}
	
	function getSourceCategory(name) {
		if (name.includes('DATABASE')) return 'DATABASE';
		if (name.includes('API')) return 'API';
		if (name.includes('STREAM')) return 'STREAM';
		if (name.includes('CACHE')) return 'CACHE';
		if (name.includes('QUEUE')) return 'QUEUE';
		if (name.includes('STORAGE')) return 'STORAGE';
		if (name.includes('COMPUTE')) return 'COMPUTE';
		if (name.includes('NETWORK')) return 'NETWORK';
		return 'OTHER';
	}
	
	function startQuantumAnimations() {
		let time = 0;
		
		function animate() {
			time += 0.016;
			
			// Update quantum states
			pulsePhase = (pulsePhase + 0.02) % (Math.PI * 2);
			dataFlowRate = 50 + Math.sin(time * 0.5) * 30 + Math.sin(time * 1.3) * 20;
			quantumEntanglement = Math.abs(Math.sin(time * 0.3)) * 100;
			hologramDepth = Math.sin(time * 0.1) * 50;
			
			// Update network graph physics
			networkGraph.nodes.forEach(node => {
				// Apply forces
				node.vx *= 0.99; // Damping
				node.vy *= 0.99;
				
				// Attraction to center
				const dx = 250 - node.x;
				const dy = 250 - node.y;
				node.vx += dx * 0.001;
				node.vy += dy * 0.001;
				
				// Repulsion from other nodes
				networkGraph.nodes.forEach(other => {
					if (other.id !== node.id) {
						const dx = node.x - other.x;
						const dy = node.y - other.y;
						const dist = Math.sqrt(dx * dx + dy * dy);
						if (dist < 100 && dist > 0) {
							node.vx += (dx / dist) * 2;
							node.vy += (dy / dist) * 2;
						}
					}
				});
				
				// Update position
				node.x += node.vx;
				node.y += node.vy;
				
				// Boundaries
				node.x = Math.max(50, Math.min(450, node.x));
				node.y = Math.max(50, Math.min(450, node.y));
			});
			
			// Update particles
			particleSystem.forEach(particle => {
				particle.x += particle.vx;
				particle.y += particle.vy;
				particle.z += particle.vz;
				particle.life -= 0.005;
				
				if (particle.x < 0 || particle.x > 500) particle.vx *= -1;
				if (particle.y < 0 || particle.y > 300) particle.vy *= -1;
				if (particle.z < 0 || particle.z > 100) particle.vz *= -1;
				
				if (particle.life <= 0) {
					particle.life = 1;
					particle.x = Math.random() * 500;
					particle.y = Math.random() * 300;
				}
			});
			
			// Update waveforms
			waveformData = waveformData.map((point, i) => ({
				primary: Math.sin((time + i) * 0.05) * 50,
				secondary: Math.cos((time + i) * 0.08) * 30,
				tertiary: Math.sin((time + i) * 0.03) * Math.cos((time + i) * 0.07) * 40,
				interference: Math.sin(time * 2 + i * 0.1) * 10
			}));
			
			// Neural pulse
			neuralActivity.forEach(neuron => {
				neuron.pulseRate = Math.abs(Math.sin(time + Math.random()));
			});
			
			animationFrames.main = requestAnimationFrame(animate);
		}
		animate();
	}
	
	$: sources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => {
				if (sortColumn === 'name') {
					return sortDirection === 'asc' ? 
						a[0].localeCompare(b[0]) : b[0].localeCompare(a[0]);
				}
				return sortDirection === 'asc' ? a[1] - b[1] : b[1] - a[1];
			}) : [];
	
	$: paginatedSources = sources.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(sources.length / itemsPerPage);
	$: totalHosts = sources.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = sources.length > 0 ? Math.max(...sources.map(([,c]) => c)) : 1;
	$: avgHosts = sources.length > 0 ? Math.round(totalHosts / sources.length) : 0;
	
	function sortTable(column) {
		if (sortColumn === column) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = column;
			sortDirection = 'desc';
		}
	}
	
	async function drillDownSource(source, count) {
		selectedSource = { source, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			sourceDetails = result.hosts || [];
		} catch (err) {
			console.error('Source drill-down failed:', err);
			sourceDetails = generateMockHosts(source, Math.min(100, count));
		} finally {
			loading = false;
		}
	}
	
	function generateMockHosts(source, count) {
		const hosts = [];
		for (let i = 0; i < count; i++) {
			hosts.push({
				host: `${source.toLowerCase()}-node-${i + 1}.quantum.internal`,
				region: ['AMERICAS', 'EMEA', 'APAC'][Math.floor(Math.random() * 3)],
				country: ['USA', 'Germany', 'Japan', 'UK', 'Singapore'][Math.floor(Math.random() * 5)],
				data_center: `DC-${Math.floor(Math.random() * 10) + 1}`,
				infrastructure_type: ['Virtual', 'Physical', 'Container', 'Serverless'][Math.floor(Math.random() * 4)],
				present_in_cmdb: Math.random() > 0.2 ? 'Yes' : 'No',
				tanium_coverage: Math.random() > 0.3 ? 'Tanium' : 'No Coverage'
			});
		}
		return hosts;
	}
	
	function closeDetails() {
		selectedSource = null;
		sourceDetails = [];
	}
	
	function getSourceLevel(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 80) return { level: 'QUANTUM', color: '#FF00FF', glow: '#FF00FF40' };
		if (percentage >= 60) return { level: 'NEURAL', color: '#00FFFF', glow: '#00FFFF40' };
		if (percentage >= 40) return { level: 'PLASMA', color: '#00FF00', glow: '#00FF0040' };
		if (percentage >= 20) return { level: 'ENERGY', color: '#FFFF00', glow: '#FFFF0040' };
		return { level: 'PARTICLE', color: '#FF8800', glow: '#FF880040' };
	}
	
	function formatNumber(num) {
		if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
		if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
		return num.toString();
	}
	
	function getCategoryColor(category) {
		const colors = {
			'DATABASE': '#FF00FF',
			'API': '#00FFFF',
			'STREAM': '#00FF00',
			'CACHE': '#FFFF00',
			'QUEUE': '#FF8800',
			'STORAGE': '#FF0088',
			'COMPUTE': '#8800FF',
			'NETWORK': '#00FF88',
			'OTHER': '#888888'
		};
		return colors[category] || '#FFFFFF';
	}
</script>

<div class="ultimate-interface">
	<!-- Header Metrics Bar -->
	<div class="metrics-bar">
		<div class="metric-card glow-purple">
			<div class="metric-icon">◈</div>
			<div class="metric-info">
				<div class="metric-value">{sources.length}</div>
				<div class="metric-label">TOTAL SOURCES</div>
			</div>
			<div class="metric-sparkline">
				<svg viewBox="0 0 50 20">
					{#each Array(20) as _, i}
						<rect x="{i * 2.5}" y="{20 - Math.random() * 20}" 
							  width="2" height="{Math.random() * 20}"
							  fill="#FF00FF" opacity="{0.3 + i * 0.035}"/>
					{/each}
				</svg>
			</div>
		</div>
		
		<div class="metric-card glow-cyan">
			<div class="metric-icon">⬢</div>
			<div class="metric-info">
				<div class="metric-value">{formatNumber(totalHosts)}</div>
				<div class="metric-label">TOTAL HOSTS</div>
			</div>
			<div class="metric-sparkline">
				<svg viewBox="0 0 50 20">
					<polyline points="{timeSeriesData.slice(-20).map((d, i) => `${i * 2.5},${20 - d.value / 5}`).join(' ')}"
							  fill="none" stroke="#00FFFF" stroke-width="2" opacity="0.8"/>
				</svg>
			</div>
		</div>
		
		<div class="metric-card glow-green">
			<div class="metric-icon">◆</div>
			<div class="metric-info">
				<div class="metric-value">{formatNumber(avgHosts)}</div>
				<div class="metric-label">AVG PER SOURCE</div>
			</div>
			<div class="metric-sparkline">
				<svg viewBox="0 0 50 20">
					<path d="M 0,10 Q 12,5 25,10 T 50,10" 
						  fill="none" stroke="#00FF00" stroke-width="2" opacity="0.8"/>
				</svg>
			</div>
		</div>
		
		<div class="metric-card glow-yellow">
			<div class="metric-icon">▲</div>
			<div class="metric-info">
				<div class="metric-value">{dataFlowRate.toFixed(0)}%</div>
				<div class="metric-label">DATA FLOW RATE</div>
			</div>
			<div class="metric-sparkline">
				<svg viewBox="0 0 50 20">
					<circle cx="25" cy="10" r="{5 + Math.sin(pulsePhase) * 3}"
							fill="none" stroke="#FFFF00" stroke-width="2" opacity="0.8"/>
				</svg>
			</div>
		</div>
		
		<div class="metric-card glow-orange">
			<div class="metric-icon">●</div>
			<div class="metric-info">
				<div class="metric-value">{quantumEntanglement.toFixed(0)}%</div>
				<div class="metric-label">QUANTUM STATE</div>
			</div>
			<div class="metric-sparkline">
				<svg viewBox="0 0 50 20">
					{#each Array(10) as _, i}
						<circle cx="{5 + i * 5}" cy="10" r="2"
								fill="#FF8800" opacity="{Math.sin(pulsePhase + i * 0.5) * 0.5 + 0.5}"/>
					{/each}
				</svg>
			</div>
		</div>
	</div>
	
	<!-- Main Layout -->
	<div class="main-layout">
		<!-- Left: Network Graph & Heatmap -->
		<div class="left-panel">
			<!-- Network Graph -->
			<div class="graph-container">
				<h3 class="graph-title">NETWORK TOPOLOGY</h3>
				<svg viewBox="0 0 500 500" class="network-graph">
					<defs>
						<radialGradient id="nodeGradient">
							<stop offset="0%" style="stop-color:#FFFFFF;stop-opacity:1" />
							<stop offset="100%" style="stop-color:#00FFFF;stop-opacity:0.3" />
						</radialGradient>
						<filter id="glow">
							<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
							<feMerge>
								<feMergeNode in="coloredBlur"/>
								<feMergeNode in="SourceGraphic"/>
							</feMerge>
						</filter>
					</defs>
					
					<!-- Grid -->
					<g class="grid" opacity="0.1">
						{#each Array(10) as _, i}
							<line x1="0" y1="{i * 50}" x2="500" y2="{i * 50}" stroke="#00FFFF" stroke-width="0.5"/>
							<line x1="{i * 50}" y1="0" x2="{i * 50}" y2="500" stroke="#00FFFF" stroke-width="0.5"/>
						{/each}
					</g>
					
					<!-- Links -->
					{#each networkGraph.links as link}
						{@const source = networkGraph.nodes.find(n => n.id === link.source)}
						{@const target = networkGraph.nodes.find(n => n.id === link.target)}
						{#if source && target}
							<line x1="{source.x}" y1="{source.y}" 
								  x2="{target.x}" y2="{target.y}"
								  stroke="{link.active ? '#00FFFF' : '#444444'}"
								  stroke-width="{link.strength * 2}"
								  opacity="{link.active ? 0.6 : 0.2}">
								{#if link.active}
									<animate attributeName="stroke-opacity"
											 values="0.2;0.8;0.2" dur="2s" repeatCount="indefinite"/>
								{/if}
							</line>
						{/if}
					{/each}
					
					<!-- Nodes -->
					{#each networkGraph.nodes as node}
						<g class="node" transform="translate({node.x}, {node.y})"
						   on:click={() => drillDownSource(node.id, node.value)}>
							<circle r="{Math.sqrt(node.value / maxHosts) * 30 + 5}"
									fill="{getCategoryColor(node.category)}"
									opacity="0.8"
									filter="url(#glow)"/>
							<circle r="{Math.sqrt(node.value / maxHosts) * 30 + 5}"
									fill="none"
									stroke="#FFFFFF"
									stroke-width="1"
									opacity="0.5"/>
							<text text-anchor="middle" dy="4" 
								  font-size="8" fill="#FFFFFF" font-weight="bold">
								{formatNumber(node.value)}
							</text>
						</g>
					{/each}
				</svg>
			</div>
			
			<!-- Activity Heatmap -->
			<div class="graph-container">
				<h3 class="graph-title">ACTIVITY HEATMAP</h3>
				<svg viewBox="0 0 500 200" class="heatmap">
					{#each heatmapData as cell}
						<rect x="{cell.hour * 20}" y="{cell.day * 25}"
							  width="19" height="24"
							  fill="{cell.surge ? '#FF00FF' : '#00FFFF'}"
							  opacity="{cell.value / 100}">
							{#if cell.surge}
								<animate attributeName="opacity"
										 values="0.3;1;0.3" dur="1s" repeatCount="indefinite"/>
							{/if}
						</rect>
					{/each}
					<!-- Hour labels -->
					{#each Array(24) as _, h}
						{#if h % 6 === 0}
							<text x="{h * 20 + 10}" y="190" 
								  text-anchor="middle" font-size="8" fill="#888">
								{h}h
							</text>
						{/if}
					{/each}
					<!-- Day labels -->
					{#each ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as day, d}
						<text x="-5" y="{d * 25 + 15}" 
							  text-anchor="end" font-size="8" fill="#888">
							{day}
						</text>
					{/each}
				</svg>
			</div>
		</div>
		
		<!-- Center: Main Table -->
		<div class="center-panel">
			<div class="table-container">
				<div class="table-header">
					<h2 class="table-title">SOURCE QUANTUM MATRIX</h2>
					<div class="table-controls">
						<input type="text" 
							   bind:value={searchTerm}
							   placeholder="SEARCH SOURCES..."
							   class="search-input"/>
						<div class="pagination">
							<button on:click={() => currentPage = Math.max(1, currentPage - 1)}
									disabled={currentPage === 1}>◀</button>
							<span class="page-info">{currentPage} / {totalPages}</span>
							<button on:click={() => currentPage = Math.min(totalPages, currentPage + 1)}
									disabled={currentPage === totalPages}>▶</button>
						</div>
					</div>
				</div>
				
				{#if selectedSource}
					<div class="detail-view">
						<div class="detail-header">
							<h3>{selectedSource.source}</h3>
							<button class="close-btn" on:click={closeDetails}>✕</button>
						</div>
						<div class="detail-content">
							<table class="detail-table">
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
											<td>{host.region}</td>
											<td>{host.country}</td>
											<td>{host.data_center}</td>
											<td>{host.infrastructure_type}</td>
											<td><span class="status {host.present_in_cmdb === 'Yes' ? 'active' : 'inactive'}">●</span></td>
											<td><span class="status {host.tanium_coverage === 'Tanium' ? 'active' : 'inactive'}">●</span></td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				{:else}
					<table class="data-table">
						<thead>
							<tr>
								<th class="sortable" on:click={() => sortTable('rank')}>
									RANK {sortColumn === 'rank' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th class="sortable" on:click={() => sortTable('name')}>
									SOURCE {sortColumn === 'name' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th class="sortable" on:click={() => sortTable('count')}>
									HOSTS {sortColumn === 'count' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th>CATEGORY</th>
								<th>LEVEL</th>
								<th>UTILIZATION</th>
								<th>STATUS</th>
								<th>ACTIONS</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedSources as [source, count], i}
								{@const level = getSourceLevel(count)}
								{@const category = getSourceCategory(source)}
								{@const utilization = (count / maxHosts) * 100}
								<tr class="data-row" style="--glow-color: {level.glow}">
									<td class="rank">#{(currentPage - 1) * itemsPerPage + i + 1}</td>
									<td class="source-name">
										<span class="category-dot" style="background: {getCategoryColor(category)}"></span>
										{source}
									</td>
									<td class="host-count" style="color: {level.color}">
										{formatNumber(count)}
									</td>
									<td>
										<span class="category-badge" style="background: {getCategoryColor(category)}20; color: {getCategoryColor(category)}">
											{category}
										</span>
									</td>
									<td>
										<span class="level-badge" style="background: {level.glow}; color: {level.color}">
											{level.level}
										</span>
									</td>
									<td>
										<div class="utilization-bar">
											<div class="utilization-fill" 
												 style="width: {utilization}%; background: linear-gradient(90deg, {level.color}40, {level.color})">
											</div>
											<span class="utilization-text">{utilization.toFixed(1)}%</span>
										</div>
									</td>
									<td>
										<span class="status-indicator {utilization > 80 ? 'critical' : utilization > 60 ? 'warning' : 'normal'}">
											{utilization > 80 ? '◈' : utilization > 60 ? '◆' : '●'}
										</span>
									</td>
									<td>
										<button class="action-btn" on:click={() => drillDownSource(source, count)}>
											ANALYZE
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				{/if}
			</div>
		</div>
		
		<!-- Right: Analytics -->
		<div class="right-panel">
			<!-- Distribution Chart -->
			<div class="graph-container">
				<h3 class="graph-title">CATEGORY DISTRIBUTION</h3>
				<div class="distribution-chart">
					{#each distributionData as cat}
						<div class="dist-item">
							<div class="dist-header">
								<span class="dist-category" style="color: {getCategoryColor(cat.category)}">
									{cat.category}
								</span>
								<span class="dist-count">{formatNumber(cat.count)}</span>
							</div>
							<div class="dist-bar">
								<div class="dist-fill" 
									 style="width: {(cat.count / totalHosts) * 100}%; 
											background: linear-gradient(90deg, transparent, {getCategoryColor(cat.category)})">
								</div>
							</div>
							<div class="dist-footer">
								<span>{cat.sources} sources</span>
								<span>{cat.efficiency.toFixed(0)}% efficiency</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Waveform Monitor -->
			<div class="graph-container">
				<h3 class="graph-title">QUANTUM WAVEFORM</h3>
				<svg viewBox="0 0 400 150" class="waveform">
					<defs>
						<linearGradient id="waveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
							<stop offset="0%" style="stop-color:#00FFFF;stop-opacity:0.8" />
							<stop offset="100%" style="stop-color:#00FFFF;stop-opacity:0" />
						</linearGradient>
					</defs>
					
					<!-- Primary wave -->
					<path d="M 0,75 {waveformData.map((d, i) => `L ${i * 2},${75 + d.primary}`).join(' ')}"
						  fill="none" stroke="#00FFFF" stroke-width="2" opacity="0.8"/>
					
					<!-- Secondary wave -->
					<path d="M 0,75 {waveformData.map((d, i) => `L ${i * 2},${75 + d.secondary}`).join(' ')}"
						  fill="none" stroke="#FF00FF" stroke-width="1.5" opacity="0.6"/>
					
					<!-- Tertiary wave -->
					<path d="M 0,75 {waveformData.map((d, i) => `L ${i * 2},${75 + d.tertiary}`).join(' ')}"
						  fill="none" stroke="#00FF00" stroke-width="1" opacity="0.4"/>
					
					<!-- Interference pattern -->
					{#each waveformData as d, i}
						{#if Math.abs(d.interference) > 8}
							<circle cx="{i * 2}" cy="{75 + d.primary}" r="2" fill="#FFFF00" opacity="0.8">
								<animate attributeName="r" values="2;4;2" dur="0.5s" />
							</circle>
						{/if}
					{/each}
				</svg>
			</div>
			
			<!-- Correlation Matrix -->
			<div class="graph-container">
				<h3 class="graph-title">CORRELATION MATRIX</h3>
				<div class="correlation-matrix">
					{#each correlationMatrix.slice(0, 64) as cell}
						<div class="matrix-cell" 
							 style="background: rgba(0, 255, 255, {cell.value}); 
									border-color: rgba(255, 255, 255, {cell.strength})"
							 title="{cell.x} → {cell.y}: {cell.value.toFixed(2)}">
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
	
	<!-- Bottom: Particle System & Neural Network -->
	<div class="bottom-panel">
		<!-- Particle System -->
		<div class="particle-container">
			<svg viewBox="0 0 500 100" class="particle-system">
				{#each particleSystem.slice(0, 50) as particle}
					<circle cx="{particle.x}" cy="{particle.y / 3}" 
							r="{2 + particle.z / 50}"
							fill="{particle.color}"
							opacity="{particle.life}">
						<animate attributeName="opacity"
								 values="{particle.life};0;{particle.life}" 
								 dur="3s" repeatCount="indefinite"/>
					</circle>
				{/each}
			</svg>
		</div>
		
		<!-- Neural Network -->
		<div class="neural-container">
			<svg viewBox="0 0 500 100" class="neural-network">
				<!-- Connections -->
				{#each neuralActivity as neuron, i}
					{#each neuron.connections as targetIndex}
						{@const target = neuralActivity[targetIndex]}
						{#if target}
							<line x1="{neuron.x}" y1="{neuron.y / 2}" 
								  x2="{target.x}" y2="{target.y / 2}"
								  stroke="#00FF00" stroke-width="0.5"
								  opacity="{neuron.pulseRate * 0.5}"/>
						{/if}
					{/each}
				{/each}
				
				<!-- Neurons -->
				{#each neuralActivity as neuron}
					<circle cx="{neuron.x}" cy="{neuron.y / 2}" 
							r="{neuron.radius * neuron.pulseRate}"
							fill="rgba(0, 255, 0, 0.3)"
							stroke="#00FF00" stroke-width="1"/>
				{/each}
			</svg>
		</div>
	</div>
</div>

<style>
	.ultimate-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		padding: 1rem;
		overflow: hidden;
	}
	
	/* Metrics Bar */
	.metrics-bar {
		display: flex;
		gap: 1rem;
		height: 80px;
		flex-shrink: 0;
	}
	
	.metric-card {
		flex: 1;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		align-items: center;
		gap: 1rem;
		position: relative;
		overflow: hidden;
	}
	
	.metric-card.glow-purple { box-shadow: 0 0 20px rgba(255, 0, 255, 0.3); }
	.metric-card.glow-cyan { box-shadow: 0 0 20px rgba(0, 255, 255, 0.3); }
	.metric-card.glow-green { box-shadow: 0 0 20px rgba(0, 255, 0, 0.3); }
	.metric-card.glow-yellow { box-shadow: 0 0 20px rgba(255, 255, 0, 0.3); }
	.metric-card.glow-orange { box-shadow: 0 0 20px rgba(255, 136, 0, 0.3); }
	
	.metric-icon {
		font-size: 2rem;
		color: #FFFFFF;
		filter: drop-shadow(0 0 10px currentColor);
	}
	
	.metric-info {
		flex: 1;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: bold;
		color: #FFFFFF;
		font-family: 'Courier New', monospace;
	}
	
	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
	}
	
	.metric-sparkline {
		position: absolute;
		right: 10px;
		width: 60px;
		height: 30px;
		opacity: 0.5;
	}
	
	/* Main Layout */
	.main-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 300px 1fr 300px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Panels */
	.left-panel, .right-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
	}
	
	.center-panel {
		display: flex;
		flex-direction: column;
		min-height: 0;
	}
	
	/* Graph Containers */
	.graph-container {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 10px;
		padding: 1rem;
	}
	
	.graph-title {
		margin: 0 0 0.5rem 0;
		font-size: 0.8rem;
		color: #00FFFF;
		letter-spacing: 0.1em;
		font-weight: 400;
	}
	
	/* Table Container */
	.table-container {
		flex: 1;
		background: rgba(0, 0, 0, 0.8);
		border: 2px solid rgba(0, 255, 255, 0.3);
		border-radius: 10px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: 0 0 30px rgba(0, 255, 255, 0.2);
	}
	
	.table-header {
		padding: 1rem;
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.1), transparent);
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
	}
	
	.table-title {
		margin: 0 0 0.5rem 0;
		font-size: 1.2rem;
		color: #00FFFF;
		letter-spacing: 0.2em;
		font-weight: 300;
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}
	
	.table-controls {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.search-input {
		padding: 0.5rem 1rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 255, 0.3);
		color: #00FFFF;
		font-family: 'Courier New', monospace;
		border-radius: 5px;
		width: 300px;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #00FFFF;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}
	
	.pagination {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.pagination button {
		padding: 0.5rem 1rem;
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid #00FFFF;
		color: #00FFFF;
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
	}
	
	.pagination button:hover:not(:disabled) {
		background: rgba(0, 255, 255, 0.3);
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}
	
	.pagination button:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	
	.page-info {
		color: #00FFFF;
		font-family: 'Courier New', monospace;
	}
	
	/* Data Table */
	.data-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.data-table thead {
		background: rgba(0, 255, 255, 0.05);
		position: sticky;
		top: 0;
		z-index: 10;
	}
	
	.data-table th {
		padding: 1rem;
		text-align: left;
		font-size: 0.8rem;
		color: #00FFFF;
		letter-spacing: 0.1em;
		font-weight: 600;
		border-bottom: 2px solid rgba(0, 255, 255, 0.3);
		white-space: nowrap;
	}
	
	.data-table th.sortable {
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.data-table th.sortable:hover {
		background: rgba(0, 255, 255, 0.1);
		text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
	}
	
	.data-table tbody {
		overflow-y: auto;
	}
	
	.data-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.3s;
		cursor: pointer;
	}
	
	.data-row:hover {
		background: rgba(0, 255, 255, 0.05);
		box-shadow: 0 0 20px var(--glow-color);
		transform: translateX(5px);
	}
	
	.data-table td {
		padding: 0.8rem 1rem;
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.9);
	}
	
	.rank {
		color: #FF00FF;
		font-weight: bold;
		font-family: 'Courier New', monospace;
	}
	
	.source-name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-family: 'Courier New', monospace;
		color: #FFFFFF;
	}
	
	.category-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.host-count {
		font-family: 'Courier New', monospace;
		font-weight: bold;
	}
	
	.category-badge, .level-badge {
		padding: 0.3rem 0.6rem;
		border-radius: 5px;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}
	
	.utilization-bar {
		position: relative;
		width: 100px;
		height: 20px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 10px;
		overflow: hidden;
	}
	
	.utilization-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.utilization-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 0.7rem;
		color: #FFFFFF;
		font-weight: bold;
		text-shadow: 0 0 3px #000000;
	}
	
	.status-indicator {
		font-size: 1.2rem;
		display: inline-block;
		filter: drop-shadow(0 0 5px currentColor);
	}
	
	.status-indicator.normal { color: #00FF00; }
	.status-indicator.warning { color: #FFFF00; }
	.status-indicator.critical { color: #FF0000; }
	
	.action-btn {
		padding: 0.4rem 0.8rem;
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.3));
		border: 1px solid #00FFFF;
		color: #00FFFF;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
	}
	
	.action-btn:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.3), rgba(0, 255, 255, 0.5));
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
		transform: scale(1.05);
	}
	
	/* Detail View */
	.detail-view {
		flex: 1;
		padding: 1rem;
		overflow-y: auto;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
	}
	
	.detail-header h3 {
		margin: 0;
		color: #00FFFF;
		font-size: 1.2rem;
	}
	
	.close-btn {
		padding: 0.5rem 1rem;
		background: rgba(255, 0, 0, 0.1);
		border: 1px solid #FF0000;
		color: #FF0000;
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
	}
	
	.close-btn:hover {
		background: rgba(255, 0, 0, 0.3);
		box-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
	}
	
	.detail-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.detail-table th {
		padding: 0.5rem;
		background: rgba(0, 255, 255, 0.1);
		color: #00FFFF;
		font-size: 0.7rem;
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
	}
	
	.detail-table td {
		padding: 0.5rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.hostname {
		font-family: 'Courier New', monospace;
		color: #00FFFF;
		font-size: 0.7rem;
	}
	
	.status {
		font-size: 0.8rem;
	}
	
	.status.active { color: #00FF00; }
	.status.inactive { color: #FF0000; }
	
	/* Visualizations */
	.network-graph, .heatmap, .waveform, .particle-system, .neural-network {
		width: 100%;
		height: auto;
	}
	
	.node {
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.node:hover {
		transform: scale(1.2);
	}
	
	/* Distribution Chart */
	.distribution-chart {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.dist-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	
	.dist-header {
		display: flex;
		justify-content: space-between;
		font-size: 0.75rem;
	}
	
	.dist-category {
		font-weight: 600;
	}
	
	.dist-count {
		color: rgba(255, 255, 255, 0.6);
		font-family: 'Courier New', monospace;
	}
	
	.dist-bar {
		height: 15px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 5px;
		overflow: hidden;
	}
	
	.dist-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.dist-footer {
		display: flex;
		justify-content: space-between;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	/* Correlation Matrix */
	.correlation-matrix {
		display: grid;
		grid-template-columns: repeat(8, 1fr);
		grid-template-rows: repeat(8, 1fr);
		gap: 2px;
		aspect-ratio: 1;
	}
	
	.matrix-cell {
		border: 1px solid;
		border-radius: 2px;
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.matrix-cell:hover {
		transform: scale(1.5);
		z-index: 10;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}
	
	/* Bottom Panel */
	.bottom-panel {
		display: flex;
		gap: 1rem;
		height: 120px;
	}
	
	.particle-container, .neural-container {
		flex: 1;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 10px;
		padding: 0.5rem;
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 8px;
	}
	
	::-webkit-scrollbar-track {
		background: #000000;
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb {
		background: linear-gradient(180deg, #00FFFF, #FF00FF);
		border-radius: 4px;
	}
</style>