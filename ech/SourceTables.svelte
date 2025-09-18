<!-- SourceTables.svelte - Enhanced with Quantum Data Flow -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let error = null;
	let selectedSource = null;
	let sourceDetails = [];
	let searchTerm = '';
	let hoveredSource = null;
	
	// Quantum data flow animation states
	let animationFrame = null;
	let synapticActivity = [];
	let dataStreams = [];
	let quantumNodes = [];
	let energyFlow = [];
	let matrixParticles = [];
	let dimensionalPhase = 0;
	let codeRain = [];
	let networkPulse = 0;
	let dataFlowLines = [];
	
	onMount(async () => {
		await loadData();
		initializeQuantumVisualization();
	});
	
	async function loadData() {
		loading = true;
		error = null;
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			if (!response.ok) throw new Error('Failed to fetch data');
			data = await response.json();
		} catch (err) {
			console.error('Failed to load source tables:', err);
			error = 'Unable to load source data. Please try again.';
			data = generateMockData();
		} finally {
			loading = false;
		}
	}
	
	function generateMockData() {
		return {
			source_intelligence: {
				'CMDB-Production': 245890,
				'ServiceNow-Assets': 189234,
				'Tanium-Endpoints': 156789,
				'AD-Computers': 134567,
				'Azure-Resources': 98234,
				'AWS-Instances': 87654,
				'VMware-VMs': 76543,
				'Network-Devices': 65432,
				'Cloud-Storage': 54321,
				'Database-Servers': 43210,
				'Web-Applications': 32109,
				'Mobile-Devices': 21098
			}
		};
	}
	
	function initializeQuantumVisualization() {
		// Initialize data streams
		for (let i = 0; i < 50; i++) {
			synapticActivity.push(50 + Math.sin(i * 0.2) * 20);
			dataStreams.push({
				x: Math.random() * 100,
				y: Math.random() * 100,
				velocity: Math.random() * 2 + 1,
				intensity: Math.random(),
				dataType: ['INT', 'STR', 'JSON', 'XML', 'BLOB'][Math.floor(Math.random() * 5)]
			});
		}
		
		// Initialize quantum nodes for data sources
		if (data.source_intelligence) {
			Object.entries(data.source_intelligence).forEach(([source, count], i) => {
				quantumNodes.push({
					id: source,
					count: count,
					x: (i % 6) * 120 + 60,
					y: Math.floor(i / 6) * 100 + 60,
					phase: Math.random() * Math.PI * 2,
					energy: Math.random(),
					connections: [],
					dataOutput: count * 0.001,
					pulsing: false
				});
			});
		}
		
		// Create energy flow between nodes
		for (let i = 0; i < 30; i++) {
			energyFlow.push({
				x: Math.random() * 100,
				y: Math.random() * 100,
				dx: (Math.random() - 0.5) * 2,
				dy: (Math.random() - 0.5) * 2,
				life: Math.random() * 100,
				maxLife: 100 + Math.random() * 100,
				color: `hsl(${180 + Math.random() * 60}, 100%, ${60 + Math.random() * 20}%)`
			});
		}
		
		// Initialize matrix code rain
		for (let i = 0; i < 20; i++) {
			codeRain.push({
				x: Math.random() * 100,
				y: -10,
				speed: Math.random() * 3 + 1,
				chars: generateDataChars(),
				opacity: Math.random()
			});
		}
		
		// Create data flow lines between sources
		quantumNodes.forEach((node, i) => {
			let connectionCount = Math.min(3, Math.floor(Math.random() * 4) + 1);
			for (let j = 0; j < connectionCount; j++) {
				let targetIdx = Math.floor(Math.random() * quantumNodes.length);
				if (targetIdx !== i) {
					dataFlowLines.push({
						source: i,
						target: targetIdx,
						particles: [],
						strength: Math.random(),
						dataType: ['SYNC', 'ASYNC', 'STREAM', 'BATCH'][Math.floor(Math.random() * 4)]
					});
				}
			}
		});
		
		// Initialize flow particles
		dataFlowLines.forEach(line => {
			for (let i = 0; i < 3; i++) {
				line.particles.push({
					position: Math.random(),
					speed: 0.01 + Math.random() * 0.02,
					size: 1 + Math.random() * 2
				});
			}
		});
		
		startQuantumAnimation();
	}
	
	function generateDataChars() {
		const chars = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'JOIN', '1', '0', 'NULL', 'TRUE', 'FALSE'];
		return Array(10).fill().map(() => chars[Math.floor(Math.random() * chars.length)]);
	}
	
	function startQuantumAnimation() {
		let time = 0;
		
		function updateQuantumFlow() {
			time += 0.016;
			dimensionalPhase += 0.02;
			networkPulse = Math.sin(time * 2) * 0.5 + 0.5;
			
			// Update synaptic activity
			synapticActivity = synapticActivity.map((val, i) => {
				const newVal = 50 + Math.sin(time + i * 0.2) * 25 + Math.random() * 10;
				return val * 0.9 + newVal * 0.1;
			});
			
			// Update data streams
			dataStreams.forEach(stream => {
				stream.y += stream.velocity;
				if (stream.y > 100) {
					stream.y = -10;
					stream.x = Math.random() * 100;
				}
				stream.intensity = 0.5 + Math.sin(time * 3 + stream.x) * 0.5;
			});
			
			// Update quantum nodes
			quantumNodes.forEach((node, i) => {
				node.phase += 0.05;
				node.energy = 0.3 + Math.sin(time + i * 0.1) * 0.4 + Math.sin(time * 1.3 + i * 0.2) * 0.3;
				node.pulsing = Math.random() < 0.01;
				
				// Random data bursts
				if (Math.random() < 0.005) {
					node.dataOutput = node.count * (0.001 + Math.random() * 0.002);
				}
			});
			
			// Update energy flow particles
			energyFlow.forEach((particle, index) => {
				particle.x += particle.dx;
				particle.y += particle.dy;
				particle.life++;
				
				// Bounce off edges
				if (particle.x <= 0 || particle.x >= 100) particle.dx *= -1;
				if (particle.y <= 0 || particle.y >= 100) particle.dy *= -1;
				
				// Reset if life expired
				if (particle.life >= particle.maxLife) {
					energyFlow[index] = {
						x: Math.random() * 100,
						y: Math.random() * 100,
						dx: (Math.random() - 0.5) * 2,
						dy: (Math.random() - 0.5) * 2,
						life: 0,
						maxLife: 100 + Math.random() * 100,
						color: `hsl(${180 + Math.random() * 60}, 100%, ${60 + Math.random() * 20}%)`
					};
				}
			});
			
			// Update code rain
			codeRain.forEach(drop => {
				drop.y += drop.speed;
				if (drop.y > 110) {
					drop.y = -10;
					drop.x = Math.random() * 100;
					drop.chars = generateDataChars();
				}
				drop.opacity = 0.3 + Math.sin(time + drop.x) * 0.3;
			});
			
			// Update data flow particles
			dataFlowLines.forEach(line => {
				line.particles.forEach(particle => {
					particle.position = (particle.position + particle.speed) % 1;
				});
				line.strength = 0.3 + Math.sin(time * 2 + line.source) * 0.4;
			});
			
			animationFrame = requestAnimationFrame(updateQuantumFlow);
		}
		
		updateQuantumFlow();
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
	
	$: sourceCount = sources.length;
	$: topSource = sources[0] || ['N/A', 0];
	$: concentration = topSource[1] > 0 ? ((topSource[1] / totalHosts) * 100).toFixed(1) : 0;
	$: topFive = sources.slice(0, 5);

	async function drillDownSource(source, count) {
		selectedSource = { source, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			sourceDetails = result.hosts || [];
		} catch (err) {
			console.error('Source drill-down error:', err);
			sourceDetails = generateMockHosts(source, Math.min(50, count));
		} finally {
			loading = false;
		}
	}
	
	function generateMockHosts(source, count) {
		const hosts = [];
		for (let i = 0; i < count; i++) {
			hosts.push({
				host: `${source.toLowerCase()}-host-${i + 1}.internal.com`,
				region: ['AMERICAS', 'EMEA', 'APAC', 'LATAM'][Math.floor(Math.random() * 4)],
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
		selectedSource = null;
		sourceDetails = [];
	}
	
	function getSourceStatus(count) {
		let percentage = (count / maxHosts) * 100;
		if (percentage >= 75) return { level: 'CRITICAL', color: '#FF6B9D', bgColor: '#FF6B9D20' };
		if (percentage >= 50) return { level: 'HIGH', color: '#4ECDC4', bgColor: '#4ECDC420' };
		if (percentage >= 25) return { level: 'MEDIUM', color: '#95E77E', bgColor: '#95E77E20' };
		return { level: 'LOW', color: '#FFE66D', bgColor: '#FFE66D20' };
	}
	
	function getSourceSize(count) {
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
</script>

<div class="source-interface">
	<!-- Quantum Data Background -->
	<div class="quantum-data-field">
		<!-- Code Rain Effect -->
		<div class="code-rain">
			{#each codeRain as drop}
				<div class="code-drop" 
					 style="left: {drop.x}%; top: {drop.y}%; opacity: {drop.opacity}">
					{#each drop.chars.slice(0, 5) as char, i}
						<div class="code-char" style="opacity: {1 - i * 0.2}">{char}</div>
					{/each}
				</div>
			{/each}
		</div>
		
		<!-- Energy Flow Particles -->
		<div class="energy-particles">
			{#each energyFlow as particle}
				<div class="energy-particle"
					 style="left: {particle.x}%; top: {particle.y}%; 
							background: {particle.color}; 
							opacity: {1 - particle.life / particle.maxLife}">
				</div>
			{/each}
		</div>
		
		<!-- Data Streams -->
		<div class="data-streams">
			{#each dataStreams as stream}
				<div class="data-stream"
					 style="left: {stream.x}%; top: {stream.y}%; 
							opacity: {stream.intensity * 0.6}">
					<span class="stream-data">{stream.dataType}</span>
				</div>
			{/each}
		</div>
	</div>

	<!-- Top Metrics -->
	<div class="metrics-header">
		<div class="metric-card">
			<div class="metric-icon">📊</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #FF6B9D">{sourceCount}</div>
				<div class="metric-label">SOURCES</div>
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
			<div class="metric-icon">🔝</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #95E77E; font-size: 1rem" title={topSource[0]}>
					{truncateText(topSource[0], 18).toUpperCase()}
				</div>
				<div class="metric-label">TOP SOURCE</div>
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
			<div class="metric-icon">⚖️</div>
			<div class="metric-content">
				<div class="metric-value" style="color: #C77DFF">{formatNumber(avgHostsPerSource)}</div>
				<div class="metric-label">AVG HOSTS/SRC</div>
			</div>
		</div>
	</div>
	
	<!-- Main Content -->
	<div class="content-layout">
		<!-- Left: Source Visualization -->
		<div class="org-panel">
			<div class="panel-header">
				<h2>QUANTUM SOURCE ARCHITECTURE</h2>
				<input type="text"
					   bind:value={searchTerm}
					   placeholder="Search sources..."
					   class="search-input"/>
			</div>
			
			{#if loading && !selectedSource}
				<div class="loading-state">
					<div class="quantum-loader">
						<div class="loader-core"></div>
						<div class="loader-rings">
							<div class="loader-ring ring-1"></div>
							<div class="loader-ring ring-2"></div>
							<div class="loader-ring ring-3"></div>
						</div>
					</div>
					<p>SYNCHRONIZING QUANTUM DATA SOURCES...</p>
				</div>
			{:else if error && !selectedSource}
				<div class="error-state">
					<div class="error-icon">⚠️</div>
					<p>{error}</p>
					<button class="retry-btn" on:click={loadData}>RETRY</button>
				</div>
			{:else if selectedSource}
				<div class="detail-view">
					<div class="detail-header">
						<div>
							<h3 title={selectedSource.source}>{truncateText(selectedSource.source, 30).toUpperCase()}</h3>
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
					<!-- Quantum Network Nodes -->
					<div class="quantum-network">
						<svg viewBox="0 0 600 400" class="network-canvas">
							<defs>
								<filter id="quantumGlow">
									<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
									<feMerge>
										<feMergeNode in="coloredBlur"/>
										<feMergeNode in="SourceGraphic"/>
									</feMerge>
								</filter>
								<radialGradient id="nodeGradient">
									<stop offset="0%" style="stop-color:#4ECDC4;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#4ECDC4;stop-opacity:0" />
								</radialGradient>
							</defs>
							
							<!-- Data Flow Lines -->
							{#each dataFlowLines as line}
								{#if quantumNodes[line.source] && quantumNodes[line.target]}
									<line x1="{quantumNodes[line.source].x}" 
										  y1="{quantumNodes[line.source].y}"
										  x2="{quantumNodes[line.target].x}" 
										  y2="{quantumNodes[line.target].y}"
										  stroke="rgba(78, 205, 196, {line.strength * 0.5})"
										  stroke-width="2"
										  stroke-dasharray="5,5"
										  filter="url(#quantumGlow)">
										<animate attributeName="stroke-dashoffset"
												 values="0;-10" dur="2s" repeatCount="indefinite"/>
									</line>
									
									<!-- Flow Particles -->
									{#each line.particles as particle}
										{@const x = quantumNodes[line.source].x + (quantumNodes[line.target].x - quantumNodes[line.source].x) * particle.position}
										{@const y = quantumNodes[line.source].y + (quantumNodes[line.target].y - quantumNodes[line.source].y) * particle.position}
										<circle cx="{x}" cy="{y}" r="{particle.size}"
												fill="#00E5FF" opacity="0.8">
											<animate attributeName="r" 
													 values="{particle.size};{particle.size * 2};{particle.size}" 
													 dur="1s" repeatCount="indefinite"/>
										</circle>
									{/each}
								{/if}
							{/each}
							
							<!-- Quantum Nodes -->
							{#each quantumNodes.slice(0, 10) as node, i}
								{@const status = getSourceStatus(node.count)}
								{@const radius = Math.log10(node.count + 1) * 3 + 5}
								<g class="quantum-node" on:click={() => drillDownSource(node.id, node.count)}>
									<!-- Node Aura -->
									<circle cx="{node.x}" cy="{node.y}" r="{radius + 15}"
											fill="url(#nodeGradient)" 
											opacity="{node.energy * 0.3}"/>
									
									<!-- Node Core -->
									<circle cx="{node.x}" cy="{node.y}" r="{radius}"
											fill="{status.color}" 
											opacity="0.8"
											filter="url(#quantumGlow)">
										{#if node.pulsing}
											<animate attributeName="r" 
													 values="{radius};{radius * 1.5};{radius}" 
													 dur="0.5s" repeatCount="1"/>
										{/if}
									</circle>
									
									<!-- Data Output Indicator -->
									<circle cx="{node.x}" cy="{node.y - radius - 10}" r="3"
											fill="#00E5FF" opacity="{node.dataOutput * 100}">
										<animate attributeName="opacity" 
												 values="0.3;1;0.3" dur="2s" repeatCount="indefinite"/>
									</circle>
									
									<!-- Node Label -->
									<text x="{node.x}" y="{node.y + radius + 15}" 
										  text-anchor="middle" fill="#FFFFFF" font-size="8" font-weight="600">
										{truncateText(node.id, 10)}
									</text>
									
									<!-- Host Count -->
									<text x="{node.x}" y="{node.y + 3}" 
										  text-anchor="middle" fill="#000000" font-size="10" font-weight="700">
										{node.count > 1000 ? `${(node.count/1000).toFixed(0)}K` : node.count}
									</text>
								</g>
							{/each}
							
							<!-- Network Pulse Wave -->
							<circle cx="300" cy="200" r="{networkPulse * 200}" 
									fill="none" stroke="rgba(0, 229, 255, 0.2)" stroke-width="1">
								<animate attributeName="r" values="0;300;0" dur="4s" repeatCount="indefinite"/>
								<animate attributeName="stroke-opacity" values="0.5;0;0.5" dur="4s" repeatCount="indefinite"/>
							</circle>
						</svg>
					</div>
					
					<!-- Synaptic Activity Graph -->
					<div class="synaptic-activity">
						<svg viewBox="0 0 200 50">
							<defs>
								<linearGradient id="activityGradient" x1="0%" y1="0%" x2="0%" y2="100%">
									<stop offset="0%" style="stop-color:#4ECDC4;stop-opacity:0.8" />
									<stop offset="100%" style="stop-color:#4ECDC4;stop-opacity:0" />
								</linearGradient>
							</defs>
							<polyline points="{synapticActivity.map((val, i) => `${i * 4},${50 - val * 0.4}`).join(' ')}"
									  fill="none" 
									  stroke="#4ECDC4" 
									  stroke-width="2"
									  opacity="1"/>
							<polygon points="{synapticActivity.map((val, i) => `${i * 4},${50 - val * 0.4}`).join(' ')} 200,50 0,50"
									 fill="url(#activityGradient)" 
									 opacity="0.3"/>
						</svg>
						<div class="activity-label">QUANTUM DATA FLOW</div>
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
						{@const percentage = Math.min(100, (count / maxHosts) * 100)}
						{@const status = getSourceStatus(count)}
						<div class="dist-item" on:click={() => drillDownSource(source, count)}>
							<div class="dist-rank">#{i + 1}</div>
							<div class="dist-name" title={source}>{truncateText(source, 12).toUpperCase()}</div>
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
			
			<!-- Quantum Coherence Chart -->
			<div class="chart-box">
				<h3>QUANTUM DATA COHERENCE</h3>
				<div class="coherence-display">
					{#each sources.slice(0, 6) as [source, count], i}
						{@const coherence = (count / maxHosts) * 100}
						{@const status = getSourceStatus(count)}
						<div class="coherence-item" on:click={() => drillDownSource(source, count)}>
							<div class="coherence-label">{truncateText(source, 8)}</div>
							<div class="coherence-visualization">
								<svg viewBox="0 0 80 80">
									<circle cx="40" cy="40" r="30" fill="none" 
											stroke="rgba(78, 205, 196, 0.2)" stroke-width="4"/>
									<circle cx="40" cy="40" r="30" fill="none"
											stroke="{status.color}" stroke-width="4"
											stroke-dasharray="{coherence * 1.88} 188"
											transform="rotate(-90 40 40)"
											stroke-linecap="round">
										<animate attributeName="stroke-dasharray"
												 values="0 188;{coherence * 1.88} 188" 
												 dur="2s" fill="freeze"/>
									</circle>
									<text x="40" y="45" text-anchor="middle" 
										  fill="{status.color}" font-size="12" font-weight="600">
										{coherence.toFixed(0)}%
									</text>
								</svg>
							</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Data Flux Monitor -->
			<div class="chart-box">
				<h3>REAL-TIME DATA FLUX</h3>
				<div class="flux-monitor">
					<div class="flux-waves">
						<svg viewBox="0 0 300 100">
							{#each Array(5) as _, i}
								<path d="M 0,50 Q 75,{20 + i * 10} 150,50 T 300,50"
									  fill="none" 
									  stroke="rgba(78, 205, 196, {0.8 - i * 0.15})" 
									  stroke-width="2"
									  transform="translate(0, {Math.sin(dimensionalPhase + i) * 5})">
									<animate attributeName="d"
											 values="M 0,50 Q 75,{20 + i * 10} 150,50 T 300,50;M 0,50 Q 75,{80 - i * 10} 150,50 T 300,50;M 0,50 Q 75,{20 + i * 10} 150,50 T 300,50"
											 dur="{2 + i * 0.3}s" repeatCount="indefinite"/>
								</path>
							{/each}
						</svg>
					</div>
					<div class="flux-metrics">
						<div class="flux-metric">
							<span class="metric-label">THROUGHPUT</span>
							<span class="metric-value">{(totalHosts * 0.001).toFixed(1)}K/s</span>
						</div>
						<div class="flux-metric">
							<span class="metric-label">LATENCY</span>
							<span class="metric-value">{Math.floor(Math.random() * 50 + 10)}ms</span>
						</div>
					</div>
				</div>
			</div>
		</div>
		
		<!-- Right: Source List -->
		<div class="list-panel">
			<div class="panel-header">
				<h3>QUANTUM SOURCE REGISTRY</h3>
				<span class="source-count">{sources.length} ACTIVE</span>
			</div>
			<div class="source-list">
				<table class="sources-table">
					<thead>
						<tr>
							<th>#</th>
							<th>SOURCE</th>
							<th>HOSTS</th>
							<th>FLUX</th>
							<th>STATUS</th>
						</tr>
					</thead>
					<tbody>
						{#each sources as [source, count], i}
							{@const status = getSourceStatus(count)}
							{@const size = getSourceSize(count)}
							<tr on:click={() => drillDownSource(source, count)}>
								<td class="rank">{i + 1}</td>
								<td class="source-name" title={source}>
									<span class="status-indicator pulsing" style="background: {status.color}"></span>
									{truncateText(source, 20).toUpperCase()}
								</td>
								<td class="host-count" style="color: {status.color}">
									{formatNumber(count)}
								</td>
								<td>
									<div class="flux-indicator">
										<div class="flux-bar">
											<div class="flux-fill" style="width: {Math.random() * 100}%; background: {status.color}"></div>
										</div>
									</div>
								</td>
								<td>
									<span class="status-badge" 
										  style="color: {status.color}; 
												 border-color: {status.color};
												 background: {status.bgColor}">
										{status.level}
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
	
	/* Quantum Data Background */
	.quantum-data-field {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: hidden;
		z-index: 1;
	}
	
	.code-rain {
		position: absolute;
		width: 100%;
		height: 100%;
		opacity: 0.15;
	}
	
	.code-drop {
		position: absolute;
		display: flex;
		flex-direction: column;
		gap: 2px;
		pointer-events: none;
	}
	
	.code-char {
		font-family: 'Courier New', monospace;
		font-size: 10px;
		color: #00E5FF;
		text-shadow: 0 0 5px #00E5FF;
	}
	
	.energy-particles {
		position: absolute;
		width: 100%;
		height: 100%;
		opacity: 0.6;
	}
	
	.energy-particle {
		position: absolute;
		width: 3px;
		height: 3px;
		border-radius: 50%;
		box-shadow: 0 0 6px currentColor;
	}
	
	.data-streams {
		position: absolute;
		width: 100%;
		height: 100%;
		opacity: 0.4;
	}
	
	.data-stream {
		position: absolute;
		font-size: 8px;
		color: #4ECDC4;
		font-family: 'Courier New', monospace;
		transform: translateY(-50%);
	}
	
	.stream-data {
		text-shadow: 0 0 3px currentColor;
	}
	
	/* Metrics Header */
	.metrics-header {
		display: flex;
		gap: 1rem;
		flex-shrink: 0;
		position: relative;
		z-index: 2;
	}
	
	.metric-card {
		flex: 1;
		background: rgba(0, 0, 0, 0.8);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(139, 233, 253, 0.3);
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		gap: 1rem;
		align-items: center;
		transition: all 0.3s ease;
	}
	
	.metric-card:hover {
		background: rgba(0, 0, 0, 0.9);
		transform: translateY(-2px);
		box-shadow: 0 8px 32px rgba(0, 229, 255, 0.2);
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
		text-shadow: 0 0 10px currentColor;
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
		position: relative;
		z-index: 2;
	}
	
	/* Org Panel */
	.org-panel {
		background: rgba(0, 0, 0, 0.8);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(189, 147, 249, 0.3);
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
		text-shadow: 0 0 10px rgba(255, 107, 157, 0.5);
	}
	
	.search-input {
		padding: 0.5rem 1rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(139, 233, 253, 0.5);
		border-radius: 8px;
		color: #FFFFFF;
		font-size: 0.8rem;
		width: 200px;
		transition: all 0.3s ease;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #4ECDC4;
		background: rgba(0, 0, 0, 0.9);
		box-shadow: 0 0 20px rgba(78, 205, 196, 0.3);
	}
	
	.org-visualization {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		position: relative;
		overflow: hidden;
	}
	
	/* Quantum Network */
	.quantum-network {
		flex: 1;
		background: radial-gradient(ellipse at center, rgba(0, 229, 255, 0.03), transparent);
		border-radius: 10px;
		padding: 1rem;
		border: 1px solid rgba(0, 229, 255, 0.1);
	}
	
	.network-canvas {
		width: 100%;
		height: 100%;
	}
	
	.quantum-node {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.quantum-node:hover {
		transform: scale(1.1);
		filter: brightness(1.3);
	}
	
	/* Synaptic Activity */
	.synaptic-activity {
		position: relative;
		height: 80px;
		background: linear-gradient(to bottom, rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.7));
		border: 1px solid rgba(139, 233, 253, 0.3);
		padding: 8px;
		border-radius: 10px;
		overflow: hidden;
	}
	
	.synaptic-activity svg {
		width: 100%;
		height: 100%;
	}
	
	.activity-label {
		position: absolute;
		top: 8px;
		left: 12px;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
		font-weight: 600;
	}
	
	/* Analytics Panel */
	.analytics-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.chart-box {
		flex: 1;
		background: rgba(0, 0, 0, 0.8);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(139, 233, 253, 0.3);
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
		text-shadow: 0 0 10px rgba(78, 205, 196, 0.5);
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
		background: rgba(139, 233, 253, 0.1);
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
		border: 1px solid rgba(255, 255, 255, 0.1);
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
	}
	
	.dist-percent {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		text-align: right;
		font-weight: 600;
	}
	
	/* Coherence Display */
	.coherence-display {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
		flex: 1;
	}
	
	.coherence-item {
		text-align: center;
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.coherence-item:hover {
		transform: scale(1.05);
	}
	
	.coherence-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
		margin-bottom: 0.5rem;
		font-weight: 600;
	}
	
	.coherence-visualization {
		width: 80px;
		height: 80px;
		margin: 0 auto;
	}
	
	.coherence-visualization svg {
		width: 100%;
		height: 100%;
	}
	
	/* Flux Monitor */
	.flux-monitor {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.flux-waves {
		flex: 1;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 8px;
		padding: 0.5rem;
	}
	
	.flux-waves svg {
		width: 100%;
		height: 100%;
	}
	
	.flux-metrics {
		display: flex;
		justify-content: space-around;
	}
	
	.flux-metric {
		text-align: center;
	}
	
	.flux-metric .metric-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
		display: block;
		margin-bottom: 0.25rem;
	}
	
	.flux-metric .metric-value {
		font-size: 1rem;
		color: #4ECDC4;
		font-weight: 700;
		text-shadow: 0 0 10px rgba(78, 205, 196, 0.5);
	}
	
	/* List Panel */
	.list-panel {
		background: rgba(0, 0, 0, 0.8);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(189, 147, 249, 0.3);
		border-radius: 12px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		padding: 1rem;
	}
	
	.source-count {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 600;
	}
	
	.source-list {
		flex: 1;
		overflow-y: auto;
		margin-top: 1rem;
	}
	
	.sources-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.sources-table thead {
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.95);
		z-index: 10;
	}
	
	.sources-table th {
		padding: 0.6rem 0.5rem;
		text-align: left;
		font-size: 0.65rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.sources-table tbody tr {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.sources-table tbody tr:hover {
		background: rgba(139, 233, 253, 0.08);
		transform: translateX(2px);
	}
	
	.sources-table td {
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
	
	.source-name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.7rem;
		font-weight: 600;
	}
	
	.status-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.status-indicator.pulsing {
		animation: statusPulse 2s ease-in-out infinite;
	}
	
	@keyframes statusPulse {
		0%, 100% { opacity: 0.6; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.2); }
	}
	
	.host-count {
		font-family: 'SF Mono', 'Monaco', monospace;
		font-weight: 700;
	}
	
	.flux-indicator {
		width: 100%;
	}
	
	.flux-bar {
		width: 40px;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.flux-fill {
		height: 100%;
		transition: width 0.5s ease;
		animation: fluxFlow 2s ease-in-out infinite;
	}
	
	@keyframes fluxFlow {
		0%, 100% { width: 30%; }
		50% { width: 90%; }
	}
	
	.status-badge {
		font-size: 0.6rem;
		padding: 0.2rem 0.4rem;
		border: 1px solid;
		border-radius: 6px;
		font-weight: 700;
		letter-spacing: 0.03em;
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
		width: 100px;
		height: 100px;
	}
	
	.loader-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 20px;
		height: 20px;
		background: #00E5FF;
		border-radius: 50%;
		animation: coreFlash 1s ease-in-out infinite;
	}
	
	.loader-rings {
		position: absolute;
		inset: 0;
	}
	
	.loader-ring {
		position: absolute;
		border: 2px solid;
		border-radius: 50%;
		animation: ringSpin 2s linear infinite;
	}
	
	.ring-1 {
		inset: 0;
		border-color: #FF6B9D transparent transparent transparent;
	}
	
	.ring-2 {
		inset: 15px;
		border-color: transparent #4ECDC4 transparent transparent;
		animation-direction: reverse;
		animation-duration: 1.5s;
	}
	
	.ring-3 {
		inset: 30px;
		border-color: transparent transparent #95E77E transparent;
		animation-duration: 1s;
	}
	
	@keyframes coreFlash {
		0%, 100% { opacity: 1; box-shadow: 0 0 20px #00E5FF; }
		50% { opacity: 0.3; box-shadow: 0 0 5px #00E5FF; }
	}
	
	@keyframes ringSpin {
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
		text-shadow: 0 0 10px rgba(255, 107, 157, 0.5);
	}
	
	.source-stats {
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
		background: rgba(0, 0, 0, 0.5);
		border-radius: 10px;
		padding: 1rem;
		border: 1px solid rgba(0, 229, 255, 0.1);
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
		
		.coherence-display {
			grid-template-columns: repeat(2, 1fr);
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
		
		.coherence-display {
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
		
		.coherence-display {
			grid-template-columns: repeat(2, 1fr);
		}
	}
</style>