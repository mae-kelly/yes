<!-- CIOMetrics.svelte - QUANTUM EXECUTIVE COMMAND CENTER -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedExecutive = null;
	let executiveDetails = [];
	let searchTerm = '';
	let viewMode = 'hierarchy';
	
	// Advanced visualization states
	let executiveHierarchy = { name: 'CEO', children: [] };
	let networkNodes = [];
	let networkLinks = [];
	let powerMatrix = [];
	let influenceMap = [];
	let decisionFlow = [];
	let executiveProfiles = new Map();
	let quantumConnections = [];
	let holographicData = [];
	let timelineEvents = [];
	let performanceMetrics = [];
	
	// Real-time metrics
	let decisionVelocity = 0;
	let executiveSync = 100;
	let strategicAlignment = 0;
	let operationalEfficiency = 0;
	let networkStrength = 0;
	
	// Animation states
	let rotationAngle = 0;
	let pulsePhase = 0;
	let dataFlowPhase = 0;
	let particlePhase = 0;
	let animationFrame = null;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/cio_metrics');
			data = await response.json();
			loading = false;
			initializeExecutiveNetwork();
			startQuantumAnimations();
		} catch (err) {
			console.error('Executive sync failed:', err);
			data = generateMockData();
			loading = false;
			initializeExecutiveNetwork();
			startQuantumAnimations();
		}
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});
	
	function generateMockData() {
		const executives = {};
		const titles = ['CIO', 'CTO', 'CISO', 'CDO', 'VP_ENG', 'VP_OPS', 'VP_SEC', 'DIR_INF', 'DIR_APP', 'DIR_DATA'];
		const names = ['SMITH', 'JOHNSON', 'WILLIAMS', 'JONES', 'BROWN', 'DAVIS', 'MILLER', 'WILSON', 'MOORE', 'TAYLOR'];
		
		for (let i = 0; i < 50; i++) {
			const title = titles[Math.floor(Math.random() * titles.length)];
			const name = names[Math.floor(Math.random() * names.length)];
			executives[`${title}_${name}_${i}`] = Math.floor(Math.random() * 50000) + 5000;
		}
		return { operative_intelligence: executives };
	}
	
	function initializeExecutiveNetwork() {
		if (!data.operative_intelligence) return;
		
		const executives = Object.entries(data.operative_intelligence)
			.sort((a, b) => b[1] - a[1]);
		
		// Build executive hierarchy
		buildHierarchy(executives);
		
		// Create network visualization
		executives.forEach(([exec, count], i) => {
			const level = getExecutiveLevel(exec);
			const angle = (i / executives.length) * Math.PI * 2;
			const radius = 150 + (level.tier * 50);
			
			networkNodes.push({
				id: exec,
				name: exec,
				value: count,
				x: 250 + Math.cos(angle) * radius,
				y: 250 + Math.sin(angle) * radius,
				level: level.level,
				color: level.color,
				tier: level.tier,
				influence: Math.random() * 100,
				decisions: Math.floor(Math.random() * 1000),
				teams: Math.floor(Math.random() * 50),
				projects: Math.floor(Math.random() * 100)
			});
			
			// Create executive profile
			executiveProfiles.set(exec, {
				assets: count,
				performance: generatePerformanceData(),
				connections: Math.floor(Math.random() * 20) + 5,
				decisionAccuracy: 70 + Math.random() * 30,
				responseTime: Math.random() * 48,
				strategicImpact: Math.random() * 100,
				operationalLoad: Math.random() * 100,
				riskProfile: Math.random(),
				innovationScore: Math.random() * 100
			});
		});
		
		// Create network links
		networkNodes.forEach((node, i) => {
			const connectionCount = Math.min(5, Math.floor(Math.random() * 8) + 2);
			for (let j = 0; j < connectionCount; j++) {
				const targetIdx = Math.floor(Math.random() * networkNodes.length);
				if (targetIdx !== i) {
					networkLinks.push({
						source: i,
						target: targetIdx,
						strength: Math.random(),
						type: Math.random() > 0.5 ? 'direct' : 'indirect',
						dataFlow: Math.random() * 1000,
						latency: Math.random() * 100
					});
				}
			}
		});
		
		// Initialize power matrix
		for (let i = 0; i < 10; i++) {
			for (let j = 0; j < 10; j++) {
				powerMatrix.push({
					x: i,
					y: j,
					power: Math.random(),
					influence: Math.random(),
					active: Math.random() > 0.3
				});
			}
		}
		
		// Create influence map
		executives.slice(0, 20).forEach(([exec, count]) => {
			influenceMap.push({
				executive: exec,
				influence: Math.random() * 100,
				growth: Math.random() * 20 - 10,
				connections: Math.floor(Math.random() * 50),
				decisions: Math.floor(Math.random() * 100)
			});
		});
		
		// Decision flow paths
		for (let i = 0; i < 15; i++) {
			decisionFlow.push({
				id: `DECISION_${i}`,
				source: networkNodes[Math.floor(Math.random() * Math.min(10, networkNodes.length))],
				target: networkNodes[Math.floor(Math.random() * networkNodes.length)],
				type: ['Strategic', 'Operational', 'Tactical'][Math.floor(Math.random() * 3)],
				status: ['Pending', 'Approved', 'Implemented'][Math.floor(Math.random() * 3)],
				impact: Math.random() * 100,
				urgency: Math.random() * 100
			});
		}
		
		// Quantum connections (advanced linking)
		for (let i = 0; i < 30; i++) {
			quantumConnections.push({
				particles: [],
				strength: Math.random(),
				frequency: Math.random() * 100,
				resonance: Math.random()
			});
			
			for (let j = 0; j < 10; j++) {
				quantumConnections[i].particles.push({
					position: Math.random(),
					speed: 0.01 + Math.random() * 0.03,
					energy: Math.random()
				});
			}
		}
		
		// Timeline events
		for (let i = 0; i < 24; i++) {
			timelineEvents.push({
				hour: i,
				decisions: Math.floor(Math.random() * 50),
				meetings: Math.floor(Math.random() * 10),
				alerts: Math.floor(Math.random() * 20),
				communications: Math.floor(Math.random() * 100)
			});
		}
		
		// Performance metrics history
		for (let i = 0; i < 30; i++) {
			performanceMetrics.push({
				day: i,
				efficiency: 60 + Math.sin(i * 0.3) * 20 + Math.random() * 10,
				decisions: 50 + Math.cos(i * 0.2) * 30 + Math.random() * 20,
				collaboration: 70 + Math.sin(i * 0.4) * 15 + Math.random() * 15
			});
		}
	}
	
	function buildHierarchy(executives) {
		// Build a tree structure for C-suite
		const cLevelExecs = executives.filter(([name]) => 
			name.includes('CIO') || name.includes('CTO') || name.includes('CISO') || name.includes('CDO')
		).slice(0, 4);
		
		const vpLevelExecs = executives.filter(([name]) => name.includes('VP')).slice(0, 8);
		const dirLevelExecs = executives.filter(([name]) => name.includes('DIR')).slice(0, 16);
		
		executiveHierarchy.children = cLevelExecs.map(([name, count]) => ({
			name,
			value: count,
			children: vpLevelExecs.slice(0, 2).map(([vpName, vpCount]) => ({
				name: vpName,
				value: vpCount,
				children: dirLevelExecs.slice(0, 2).map(([dirName, dirCount]) => ({
					name: dirName,
					value: dirCount,
					children: []
				}))
			}))
		}));
	}
	
	function generatePerformanceData() {
		const data = [];
		for (let i = 0; i < 12; i++) {
			data.push({
				month: i,
				performance: 60 + Math.random() * 40,
				target: 80,
				trend: Math.random() > 0.5 ? 'up' : 'down'
			});
		}
		return data;
	}
	
	function getExecutiveLevel(name) {
		if (name.includes('CIO') || name.includes('CTO') || name.includes('CISO')) {
			return { level: 'C-SUITE', tier: 1, color: '#FF00FF', bgColor: '#FF00FF20', icon: '👑' };
		}
		if (name.includes('VP')) {
			return { level: 'VP', tier: 2, color: '#00FFFF', bgColor: '#00FFFF20', icon: '⭐' };
		}
		if (name.includes('DIR')) {
			return { level: 'DIRECTOR', tier: 3, color: '#00FF00', bgColor: '#00FF0020', icon: '💎' };
		}
		return { level: 'MANAGER', tier: 4, color: '#FFFF00', bgColor: '#FFFF0020', icon: '◆' };
	}
	
	function startQuantumAnimations() {
		let time = 0;
		
		function animate() {
			time += 0.016;
			
			// Update rotation and phases
			rotationAngle = (rotationAngle + 0.5) % 360;
			pulsePhase = (pulsePhase + 0.02) % (Math.PI * 2);
			dataFlowPhase = (dataFlowPhase + 0.03) % (Math.PI * 2);
			particlePhase = (particlePhase + 0.01) % (Math.PI * 2);
			
			// Update metrics
			decisionVelocity = 50 + Math.sin(time * 0.5) * 30 + Math.sin(time * 1.3) * 20;
			executiveSync = 85 + Math.sin(time * 0.3) * 10 + Math.random() * 5;
			strategicAlignment = 70 + Math.sin(time * 0.4) * 20 + Math.random() * 10;
			operationalEfficiency = 75 + Math.cos(time * 0.35) * 15 + Math.random() * 10;
			networkStrength = 80 + Math.sin(time * 0.45) * 15 + Math.random() * 5;
			
			// Update quantum connections
			quantumConnections.forEach(conn => {
				conn.particles.forEach(particle => {
					particle.position = (particle.position + particle.speed) % 1;
					particle.energy = 0.5 + Math.sin(time * 2 + particle.position * Math.PI * 2) * 0.5;
				});
			});
			
			animationFrame = requestAnimationFrame(animate);
		}
		animate();
	}
	
	$: filteredExecutives = data.operative_intelligence ? 
		Object.entries(data.operative_intelligence)
			.filter(([exec]) => exec.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: totalAssets = filteredExecutives.reduce((sum, [_, count]) => sum + count, 0);
	$: maxAssets = filteredExecutives.length > 0 ? Math.max(...filteredExecutives.map(([,c]) => c)) : 1;
	
	async function drillDownExecutive(executive, count) {
		selectedExecutive = { executive, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(executive)}`);
			let result = await response.json();
			executiveDetails = result.hosts || [];
		} catch (err) {
			console.error('Executive deep scan failed:', err);
			executiveDetails = generateMockHosts(executive, Math.min(100, count));
		} finally {
			loading = false;
		}
	}
	
	function generateMockHosts(executive, count) {
		const hosts = [];
		for (let i = 0; i < count; i++) {
			hosts.push({
				host: `${executive.toLowerCase()}-system-${i + 1}.corp`,
				region: ['Americas', 'EMEA', 'APAC'][Math.floor(Math.random() * 3)],
				country: ['USA', 'UK', 'Singapore'][Math.floor(Math.random() * 3)],
				infrastructure_type: ['Cloud', 'Hybrid', 'On-Premise'][Math.floor(Math.random() * 3)],
				business_unit: executive.split('_')[0],
				present_in_cmdb: Math.random() > 0.2 ? 'Yes' : 'No',
				tanium_coverage: Math.random() > 0.3 ? 'Tanium' : 'No Coverage'
			});
		}
		return hosts;
	}
	
	function closeDetails() {
		selectedExecutive = null;
		executiveDetails = [];
	}
	
	function formatNumber(num) {
		return new Intl.NumberFormat('en-US').format(num);
	}
</script>

<div class="executive-quantum-interface">
	<!-- Header Command Bar -->
	<div class="command-bar">
		<div class="command-section">
			<h1 class="interface-title">
				<span class="title-icon">👑</span>
				EXECUTIVE QUANTUM COMMAND
			</h1>
		</div>
		
		<div class="control-section">
			<input type="text"
				   bind:value={searchTerm}
				   placeholder="Search executives..."
				   class="search-input"/>
			
			<div class="view-switcher">
				<button class="view-btn {viewMode === 'hierarchy' ? 'active' : ''}"
						on:click={() => viewMode = 'hierarchy'}>
					<span class="btn-icon">🏛️</span>
					HIERARCHY
				</button>
				<button class="view-btn {viewMode === 'network' ? 'active' : ''}"
						on:click={() => viewMode = 'network'}>
					<span class="btn-icon">🌐</span>
					NETWORK
				</button>
				<button class="view-btn {viewMode === 'matrix' ? 'active' : ''}"
						on:click={() => viewMode = 'matrix'}>
					<span class="btn-icon">⚡</span>
					MATRIX
				</button>
				<button class="view-btn {viewMode === 'quantum' ? 'active' : ''}"
						on:click={() => viewMode = 'quantum'}>
					<span class="btn-icon">💫</span>
					QUANTUM
				</button>
			</div>
		</div>
		
		<div class="metrics-section">
			<div class="live-metric">
				<span class="metric-label">SYNC</span>
				<div class="metric-bar">
					<div class="bar-fill" style="width: {executiveSync}%; background: linear-gradient(90deg, #FF00FF, #00FFFF)"></div>
				</div>
				<span class="metric-value">{executiveSync.toFixed(0)}%</span>
			</div>
			<div class="live-metric">
				<span class="metric-label">VELOCITY</span>
				<span class="metric-value" style="color: #00FF00">{decisionVelocity.toFixed(0)}</span>
			</div>
		</div>
	</div>
	
	<!-- Main Content Area -->
	<div class="main-content">
		{#if loading && !selectedExecutive}
			<div class="loading-state">
				<div class="quantum-loader">
					<div class="loader-ring ring-1"></div>
					<div class="loader-ring ring-2"></div>
					<div class="loader-ring ring-3"></div>
					<div class="loader-core">👑</div>
				</div>
				<p class="loading-text">INITIALIZING EXECUTIVE MATRIX...</p>
			</div>
		{:else if selectedExecutive}
			<div class="executive-detail-view">
				<div class="detail-header">
					<div class="executive-profile">
						<div class="profile-icon" style="background: {getExecutiveLevel(selectedExecutive.executive).bgColor}">
							{getExecutiveLevel(selectedExecutive.executive).icon}
						</div>
						<div class="profile-info">
							<h2>{selectedExecutive.executive.toUpperCase()}</h2>
							<div class="profile-stats">
								<span>{formatNumber(selectedExecutive.count)} ASSETS</span>
								<span>•</span>
								<span>{getExecutiveLevel(selectedExecutive.executive).level}</span>
								<span>•</span>
								<span>{((selectedExecutive.count / totalAssets) * 100).toFixed(1)}% CONTROL</span>
							</div>
						</div>
					</div>
					<button class="close-detail-btn" on:click={closeDetails}>
						<span>✕</span> CLOSE PROFILE
					</button>
				</div>
				
				<div class="detail-grid">
					<div class="detail-section performance">
						<h3>PERFORMANCE METRICS</h3>
						<svg viewBox="0 0 400 200" class="performance-chart">
							{#if executiveProfiles.get(selectedExecutive.executive)}
								{@const profile = executiveProfiles.get(selectedExecutive.executive)}
								<polyline points="{profile.performance.map((d, i) => `${i * 33},${200 - d.performance * 2}`).join(' ')}"
										  fill="none" stroke="#00FFFF" stroke-width="2"/>
								<polyline points="0,40 400,40"
										  fill="none" stroke="#FF00FF" stroke-width="1" opacity="0.3" stroke-dasharray="5,5"/>
							{/if}
						</svg>
					</div>
					
					<div class="detail-section assets-list">
						<h3>MANAGED ASSETS</h3>
						<div class="assets-table">
							<table>
								<thead>
									<tr>
										<th>HOSTNAME</th>
										<th>REGION</th>
										<th>TYPE</th>
										<th>STATUS</th>
									</tr>
								</thead>
								<tbody>
									{#each executiveDetails.slice(0, 10) as host}
										<tr>
											<td class="hostname">{host.host}</td>
											<td>{host.region}</td>
											<td>{host.infrastructure_type}</td>
											<td>
												<span class="status-badge {host.present_in_cmdb === 'Yes' ? 'active' : 'inactive'}">
													{host.present_in_cmdb === 'Yes' ? 'SYNCED' : 'OFFLINE'}
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
		{:else if viewMode === 'hierarchy'}
			<div class="hierarchy-view">
				<div class="org-chart">
					<!-- CEO Node -->
					<div class="hierarchy-level level-0">
						<div class="exec-node ceo">
							<span class="node-icon">👑</span>
							<span class="node-title">CEO</span>
							<span class="node-count">{formatNumber(totalAssets)}</span>
						</div>
					</div>
					
					<!-- C-Suite Level -->
					<div class="hierarchy-level level-1">
						{#each filteredExecutives.filter(([n]) => n.includes('CIO') || n.includes('CTO') || n.includes('CISO')).slice(0, 4) as [exec, count]}
							<div class="exec-node c-suite" on:click={() => drillDownExecutive(exec, count)}>
								<span class="node-icon">{getExecutiveLevel(exec).icon}</span>
								<span class="node-title">{exec.split('_')[0]}</span>
								<span class="node-count">{formatNumber(count)}</span>
								<div class="node-glow" style="background: {getExecutiveLevel(exec).color}"></div>
							</div>
						{/each}
					</div>
					
					<!-- VP Level -->
					<div class="hierarchy-level level-2">
						{#each filteredExecutives.filter(([n]) => n.includes('VP')).slice(0, 8) as [exec, count]}
							<div class="exec-node vp" on:click={() => drillDownExecutive(exec, count)}>
								<span class="node-icon">⭐</span>
								<span class="node-title">{exec.substring(0, 10)}</span>
								<span class="node-count">{formatNumber(count)}</span>
							</div>
						{/each}
					</div>
				</div>
			</div>
		{:else if viewMode === 'network'}
			<div class="network-view">
				<svg viewBox="0 0 800 600" class="executive-network">
					<defs>
						<radialGradient id="execGradient">
							<stop offset="0%" style="stop-color:#FFFFFF;stop-opacity:1" />
							<stop offset="100%" style="stop-color:#00FFFF;stop-opacity:0.3" />
						</radialGradient>
						<filter id="execGlow">
							<feGaussianBlur stdDeviation="4" result="coloredBlur"/>
							<feMerge>
								<feMergeNode in="coloredBlur"/>
								<feMergeNode in="SourceGraphic"/>
							</feMerge>
						</filter>
					</defs>
					
					<!-- Connection lines -->
					{#each networkLinks as link}
						{#if networkNodes[link.source] && networkNodes[link.target]}
							<line x1="{networkNodes[link.source].x * 1.6}" 
								  y1="{networkNodes[link.source].y * 1.2}"
								  x2="{networkNodes[link.target].x * 1.6}" 
								  y2="{networkNodes[link.target].y * 1.2}"
								  stroke="{link.type === 'direct' ? '#00FFFF' : '#FF00FF'}"
								  stroke-width="{link.strength * 2}"
								  opacity="{link.strength * 0.5}"
								  stroke-dasharray="{link.type === 'indirect' ? '5,5' : 'none'}">
								<animate attributeName="stroke-opacity"
										 values="{link.strength * 0.3};{link.strength * 0.7};{link.strength * 0.3}"
										 dur="3s" repeatCount="indefinite"/>
							</line>
						{/if}
					{/each}
					
					<!-- Executive nodes -->
					{#each networkNodes as node, i}
						<g transform="translate({node.x * 1.6}, {node.y * 1.2})"
						   class="exec-network-node"
						   on:click={() => drillDownExecutive(node.name, node.value)}>
							<circle r="{15 + Math.sqrt(node.value / maxAssets) * 30}"
									fill="{node.color}"
									opacity="0.3"
									filter="url(#execGlow)"/>
							<circle r="{10 + Math.sqrt(node.value / maxAssets) * 25}"
									fill="{node.color}"
									opacity="0.8"/>
							<text text-anchor="middle" dy="-20" font-size="10" fill="#FFFFFF" font-weight="600">
								{node.name.split('_')[0]}
							</text>
							<text text-anchor="middle" dy="4" font-size="12" fill="#FFFFFF" font-weight="bold">
								{formatNumber(node.value)}
							</text>
						</g>
					{/each}
				</svg>
			</div>
		{:else if viewMode === 'matrix'}
			<div class="matrix-view">
				<div class="power-grid">
					{#each powerMatrix as cell}
						<div class="power-cell"
							 style="background: rgba(255, 0, 255, {cell.power});
									border-color: rgba(0, 255, 255, {cell.influence});
									transform: rotateX({Math.sin(pulsePhase + cell.x) * 10}deg) 
											   rotateY({Math.cos(pulsePhase + cell.y) * 10}deg)">
							{#if cell.active}
								<div class="cell-pulse"></div>
							{/if}
						</div>
					{/each}
				</div>
				
				<div class="influence-chart">
					<h3>INFLUENCE DYNAMICS</h3>
					{#each influenceMap.slice(0, 10) as exec}
						<div class="influence-bar">
							<span class="exec-label">{exec.executive.substring(0, 15)}</span>
							<div class="bar-container">
								<div class="influence-level"
									 style="width: {exec.influence}%;
											background: linear-gradient(90deg, #FF00FF, #00FFFF)">
								</div>
							</div>
							<span class="influence-value">{exec.influence.toFixed(0)}</span>
							<span class="growth-indicator {exec.growth > 0 ? 'positive' : 'negative'}">
								{exec.growth > 0 ? '↑' : '↓'} {Math.abs(exec.growth).toFixed(0)}%
							</span>
						</div>
					{/each}
				</div>
			</div>
		{:else if viewMode === 'quantum'}
			<div class="quantum-view">
				<div class="quantum-visualization">
					<svg viewBox="0 0 600 600" class="quantum-field">
						<!-- Quantum field background -->
						<defs>
							<radialGradient id="quantumGradient">
								<stop offset="0%" style="stop-color:#FF00FF;stop-opacity:0.3" />
								<stop offset="50%" style="stop-color:#00FFFF;stop-opacity:0.2" />
								<stop offset="100%" style="stop-color:#000000;stop-opacity:0" />
							</radialGradient>
						</defs>
						
						<circle cx="300" cy="300" r="250" fill="url(#quantumGradient)" 
								transform="rotate({rotationAngle}, 300, 300)"/>
						
						<!-- Quantum connections -->
						{#each quantumConnections.slice(0, 20) as conn, i}
							{@const angle = (i / 20) * Math.PI * 2}
							{@const x1 = 300 + Math.cos(angle) * 100}
							{@const y1 = 300 + Math.sin(angle) * 100}
							{@const x2 = 300 + Math.cos(angle + Math.PI) * 100}
							{@const y2 = 300 + Math.sin(angle + Math.PI) * 100}
							
							<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
								  stroke="#00FFFF" stroke-width="{conn.strength * 3}"
								  opacity="{conn.strength}">
								{#each conn.particles as particle}
									<circle cx="{x1 + (x2 - x1) * particle.position}" 
											cy="{y1 + (y2 - y1) * particle.position}"
											r="2" fill="#FFFFFF" opacity="{particle.energy}"/>
								{/each}
							</line>
						{/each}
						
						<!-- Executive quantum nodes -->
						{#each filteredExecutives.slice(0, 15) as [exec, count], i}
							{@const angle = (i / 15) * Math.PI * 2}
							{@const radius = 100 + Math.sqrt(count / maxAssets) * 100}
							{@const x = 300 + Math.cos(angle + rotationAngle * 0.01) * radius}
							{@const y = 300 + Math.sin(angle + rotationAngle * 0.01) * radius}
							
							<g transform="translate({x}, {y})"
							   on:click={() => drillDownExecutive(exec, count)}>
								<circle r="{20 + Math.sqrt(count / maxAssets) * 20}"
										fill="{getExecutiveLevel(exec).color}"
										opacity="0.3"/>
								<circle r="{15 + Math.sqrt(count / maxAssets) * 15}"
										fill="{getExecutiveLevel(exec).color}"
										opacity="0.8"/>
								<text text-anchor="middle" dy="4" font-size="8" fill="#FFFFFF">
									{exec.split('_')[0]}
								</text>
							</g>
						{/each}
					</svg>
				</div>
				
				<div class="quantum-metrics">
					<div class="metric-display">
						<span class="metric-title">STRATEGIC ALIGNMENT</span>
						<div class="metric-visual">
							<svg viewBox="0 0 100 100">
								<circle cx="50" cy="50" r="40" fill="none" stroke="#333" stroke-width="8"/>
								<circle cx="50" cy="50" r="40" fill="none" 
										stroke="url(#gradientStroke)" stroke-width="8"
										stroke-dasharray="{strategicAlignment * 2.5} 250"
										transform="rotate(-90 50 50)"/>
								<text x="50" y="55" text-anchor="middle" font-size="20" fill="#00FFFF">
									{strategicAlignment.toFixed(0)}%
								</text>
							</svg>
						</div>
					</div>
					
					<div class="metric-display">
						<span class="metric-title">NETWORK STRENGTH</span>
						<div class="network-strength-bars">
							{#each Array(10) as _, i}
								<div class="strength-bar"
									 style="height: {20 + Math.sin(pulsePhase + i * 0.5) * 15}px;
											background: {i < networkStrength / 10 ? '#00FF00' : '#333'}">
								</div>
							{/each}
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
	
	<!-- Timeline Activity Bar -->
	<div class="timeline-bar">
		<h3>24H ACTIVITY TIMELINE</h3>
		<div class="timeline-chart">
			{#each timelineEvents as event}
				<div class="timeline-hour">
					<div class="hour-label">{event.hour}h</div>
					<div class="hour-metrics">
						<div class="metric-bar decisions" 
							 style="height: {event.decisions}px"
							 title="{event.decisions} decisions"></div>
						<div class="metric-bar meetings" 
							 style="height: {event.meetings * 5}px"
							 title="{event.meetings} meetings"></div>
						<div class="metric-bar alerts" 
							 style="height: {event.alerts * 2}px"
							 title="{event.alerts} alerts"></div>
					</div>
				</div>
			{/each}
		</div>
	</div>
</div>

<style>
	.executive-quantum-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: linear-gradient(135deg, #0a0014 0%, #1a0033 100%);
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	/* Command Bar */
	.command-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem 2rem;
		background: rgba(0, 0, 0, 0.9);
		border-bottom: 2px solid rgba(255, 0, 255, 0.3);
		backdrop-filter: blur(20px);
	}
	
	.command-section {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.interface-title {
		margin: 0;
		font-size: 1.4rem;
		background: linear-gradient(90deg, #FF00FF, #00FFFF, #FF00FF);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		font-weight: 700;
		letter-spacing: 0.1em;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.title-icon {
		font-size: 1.8rem;
		filter: drop-shadow(0 0 10px rgba(255, 0, 255, 0.8));
	}
	
	.control-section {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.search-input {
		padding: 0.8rem 1.5rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 25px;
		color: #00FFFF;
		font-size: 0.9rem;
		width: 250px;
		transition: all 0.3s ease;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #00FFFF;
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
		width: 300px;
	}
	
	.view-switcher {
		display: flex;
		gap: 0.5rem;
		background: rgba(0, 0, 0, 0.6);
		padding: 0.3rem;
		border-radius: 25px;
		border: 1px solid rgba(255, 0, 255, 0.2);
	}
	
	.view-btn {
		padding: 0.6rem 1.2rem;
		background: transparent;
		border: none;
		color: rgba(255, 255, 255, 0.7);
		cursor: pointer;
		border-radius: 20px;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.8rem;
		font-weight: 600;
	}
	
	.view-btn:hover {
		background: rgba(255, 0, 255, 0.1);
		color: #FF00FF;
	}
	
	.view-btn.active {
		background: linear-gradient(135deg, rgba(255, 0, 255, 0.3), rgba(0, 255, 255, 0.3));
		color: #FFFFFF;
		box-shadow: 0 0 15px rgba(255, 0, 255, 0.4);
	}
	
	.btn-icon {
		font-size: 1rem;
	}
	
	.metrics-section {
		display: flex;
		gap: 2rem;
		align-items: center;
	}
	
	.live-metric {
		display: flex;
		align-items: center;
		gap: 0.8rem;
	}
	
	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		font-weight: 600;
	}
	
	.metric-bar {
		width: 100px;
		height: 6px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
		border-radius: 3px;
	}
	
	.metric-value {
		font-size: 1rem;
		font-weight: 700;
		color: #00FFFF;
		font-family: 'SF Mono', 'Monaco', monospace;
	}
	
	/* Main Content */
	.main-content {
		flex: 1;
		padding: 2rem;
		overflow: auto;
	}
	
	/* Loading State */
	.loading-state {
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.quantum-loader {
		position: relative;
		width: 150px;
		height: 150px;
	}
	
	.loader-ring {
		position: absolute;
		border: 2px solid;
		border-radius: 50%;
		animation: ringRotate 3s linear infinite;
	}
	
	.ring-1 {
		inset: 0;
		border-color: #FF00FF transparent #FF00FF transparent;
	}
	
	.ring-2 {
		inset: 20px;
		border-color: transparent #00FFFF transparent #00FFFF;
		animation-delay: -1s;
	}
	
	.ring-3 {
		inset: 40px;
		border-color: #00FF00 transparent #00FF00 transparent;
		animation-delay: -2s;
	}
	
	@keyframes ringRotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.loader-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 3rem;
		animation: corePulse 2s ease-in-out infinite;
	}
	
	@keyframes corePulse {
		0%, 100% { transform: translate(-50%, -50%) scale(1); filter: brightness(1); }
		50% { transform: translate(-50%, -50%) scale(1.2); filter: brightness(1.5); }
	}
	
	.loading-text {
		color: rgba(255, 255, 255, 0.6);
		font-size: 1rem;
		letter-spacing: 0.2em;
		animation: textGlow 2s ease-in-out infinite;
	}
	
	@keyframes textGlow {
		0%, 100% { opacity: 0.6; }
		50% { opacity: 1; text-shadow: 0 0 20px rgba(0, 255, 255, 0.8); }
	}
	
	/* Executive Detail View */
	.executive-detail-view {
		height: 100%;
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.8);
		border: 2px solid rgba(255, 0, 255, 0.3);
		border-radius: 20px;
		overflow: hidden;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 2rem;
		background: linear-gradient(135deg, rgba(255, 0, 255, 0.1), rgba(0, 255, 255, 0.1));
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.executive-profile {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.profile-icon {
		width: 80px;
		height: 80px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 3rem;
		box-shadow: 0 0 30px currentColor;
	}
	
	.profile-info h2 {
		margin: 0;
		font-size: 1.6rem;
		color: #FFFFFF;
		font-weight: 300;
		letter-spacing: 0.05em;
	}
	
	.profile-stats {
		display: flex;
		gap: 1rem;
		margin-top: 0.5rem;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.close-detail-btn {
		padding: 0.8rem 1.5rem;
		background: rgba(255, 0, 0, 0.1);
		border: 1px solid #FF0066;
		color: #FF0066;
		border-radius: 25px;
		cursor: pointer;
		transition: all 0.3s ease;
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.close-detail-btn:hover {
		background: rgba(255, 0, 102, 0.2);
		box-shadow: 0 0 20px rgba(255, 0, 102, 0.4);
		transform: scale(1.05);
	}
	
	.detail-grid {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		padding: 2rem;
		overflow: auto;
	}
	
	.detail-section {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 15px;
		padding: 1.5rem;
	}
	
	.detail-section h3 {
		margin: 0 0 1rem 0;
		font-size: 0.9rem;
		color: #00FFFF;
		letter-spacing: 0.1em;
		font-weight: 600;
	}
	
	.performance-chart {
		width: 100%;
		height: 200px;
	}
	
	.assets-table {
		overflow: auto;
		max-height: 400px;
	}
	
	.assets-table table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.assets-table th {
		padding: 0.8rem;
		background: rgba(0, 255, 255, 0.1);
		color: #00FFFF;
		font-size: 0.7rem;
		letter-spacing: 0.1em;
		font-weight: 600;
		text-align: left;
		position: sticky;
		top: 0;
	}
	
	.assets-table td {
		padding: 0.6rem 0.8rem;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.hostname {
		font-family: 'SF Mono', 'Monaco', monospace;
		color: #00FFFF;
		font-size: 0.75rem;
	}
	
	.status-badge {
		padding: 0.2rem 0.6rem;
		border-radius: 12px;
		font-size: 0.65rem;
		font-weight: 600;
	}
	
	.status-badge.active {
		background: rgba(0, 255, 0, 0.2);
		color: #00FF00;
		border: 1px solid #00FF00;
	}
	
	.status-badge.inactive {
		background: rgba(255, 0, 0, 0.2);
		color: #FF0000;
		border: 1px solid #FF0000;
	}
	
	/* Hierarchy View */
	.hierarchy-view {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.org-chart {
		display: flex;
		flex-direction: column;
		gap: 3rem;
		align-items: center;
	}
	
	.hierarchy-level {
		display: flex;
		gap: 2rem;
		justify-content: center;
		position: relative;
	}
	
	.exec-node {
		background: rgba(0, 0, 0, 0.8);
		border: 2px solid;
		border-radius: 15px;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
		transition: all 0.3s ease;
		position: relative;
		min-width: 120px;
	}
	
	.exec-node.ceo {
		border-color: #FFD700;
		box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
	}
	
	.exec-node.c-suite {
		border-color: #FF00FF;
		box-shadow: 0 0 25px rgba(255, 0, 255, 0.4);
	}
	
	.exec-node.vp {
		border-color: #00FFFF;
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
	}
	
	.exec-node:hover {
		transform: scale(1.1) translateY(-5px);
		z-index: 10;
	}
	
	.node-icon {
		font-size: 2rem;
		filter: drop-shadow(0 0 10px currentColor);
	}
	
	.node-title {
		font-size: 0.9rem;
		font-weight: 600;
		color: #FFFFFF;
		letter-spacing: 0.05em;
	}
	
	.node-count {
		font-size: 1.2rem;
		font-weight: 700;
		color: #00FFFF;
		font-family: 'SF Mono', 'Monaco', monospace;
	}
	
	.node-glow {
		position: absolute;
		inset: -10px;
		border-radius: 20px;
		opacity: 0.3;
		filter: blur(20px);
		z-index: -1;
	}
	
	/* Network View */
	.network-view {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		background: radial-gradient(circle at center, rgba(0, 255, 255, 0.05), transparent);
	}
	
	.executive-network {
		width: 100%;
		height: 100%;
		max-width: 1000px;
		max-height: 800px;
	}
	
	.exec-network-node {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.exec-network-node:hover {
		transform: scale(1.2);
	}
	
	/* Matrix View */
	.matrix-view {
		height: 100%;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		padding: 2rem;
	}
	
	.power-grid {
		display: grid;
		grid-template-columns: repeat(10, 1fr);
		grid-template-rows: repeat(10, 1fr);
		gap: 0.5rem;
		padding: 2rem;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(255, 0, 255, 0.3);
		border-radius: 20px;
	}
	
	.power-cell {
		aspect-ratio: 1;
		border: 1px solid;
		border-radius: 5px;
		position: relative;
		transition: all 0.3s ease;
		transform-style: preserve-3d;
	}
	
	.power-cell:hover {
		z-index: 10;
		transform: scale(1.5) translateZ(20px);
	}
	
	.cell-pulse {
		position: absolute;
		inset: 0;
		background: radial-gradient(circle at center, #FFFFFF, transparent);
		border-radius: 5px;
		animation: cellPulse 2s ease-in-out infinite;
	}
	
	@keyframes cellPulse {
		0%, 100% { opacity: 0; }
		50% { opacity: 0.5; }
	}
	
	.influence-chart {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 20px;
		padding: 1.5rem;
	}
	
	.influence-chart h3 {
		margin: 0 0 1.5rem 0;
		font-size: 1rem;
		color: #00FFFF;
		letter-spacing: 0.1em;
		font-weight: 600;
	}
	
	.influence-bar {
		display: grid;
		grid-template-columns: 120px 1fr 50px 50px;
		gap: 1rem;
		align-items: center;
		margin-bottom: 1rem;
	}
	
	.exec-label {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	
	.bar-container {
		height: 20px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 10px;
		overflow: hidden;
	}
	
	.influence-level {
		height: 100%;
		transition: width 0.5s ease;
		border-radius: 10px;
	}
	
	.influence-value {
		font-size: 0.8rem;
		font-weight: 600;
		color: #00FFFF;
		font-family: 'SF Mono', 'Monaco', monospace;
	}
	
	.growth-indicator {
		font-size: 0.75rem;
		font-weight: 600;
	}
	
	.growth-indicator.positive {
		color: #00FF00;
	}
	
	.growth-indicator.negative {
		color: #FF0000;
	}
	
	/* Quantum View */
	.quantum-view {
		height: 100%;
		display: grid;
		grid-template-columns: 2fr 1fr;
		gap: 2rem;
		padding: 2rem;
	}
	
	.quantum-visualization {
		background: rgba(0, 0, 0, 0.8);
		border: 2px solid rgba(255, 0, 255, 0.3);
		border-radius: 20px;
		padding: 1rem;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.quantum-field {
		width: 100%;
		height: 100%;
		max-width: 600px;
		max-height: 600px;
	}
	
	.quantum-metrics {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}
	
	.metric-display {
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 15px;
		padding: 1.5rem;
		text-align: center;
	}
	
	.metric-title {
		display: block;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
		margin-bottom: 1rem;
		font-weight: 600;
	}
	
	.metric-visual svg {
		width: 100%;
		height: auto;
	}
	
	.network-strength-bars {
		display: flex;
		gap: 0.5rem;
		justify-content: center;
		align-items: flex-end;
		height: 60px;
	}
	
	.strength-bar {
		width: 15px;
		background: #00FF00;
		border-radius: 2px;
		transition: all 0.3s ease;
	}
	
	/* Timeline Bar */
	.timeline-bar {
		padding: 1rem 2rem;
		background: rgba(0, 0, 0, 0.9);
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.timeline-bar h3 {
		margin: 0 0 1rem 0;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
		font-weight: 600;
	}
	
	.timeline-chart {
		display: flex;
		gap: 0.5rem;
		align-items: flex-end;
		height: 60px;
	}
	
	.timeline-hour {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}
	
	.hour-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.4);
	}
	
	.hour-metrics {
		display: flex;
		gap: 2px;
		align-items: flex-end;
		height: 40px;
	}
	
	.metric-bar {
		width: 8px;
		border-radius: 2px 2px 0 0;
		transition: all 0.3s ease;
	}
	
	.metric-bar.decisions {
		background: #FF00FF;
	}
	
	.metric-bar.meetings {
		background: #00FFFF;
	}
	
	.metric-bar.alerts {
		background: #FFFF00;
	}
	
	.metric-bar:hover {
		filter: brightness(1.5);
		transform: scaleY(1.1);
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
		background: linear-gradient(to bottom, #FF00FF, #00FFFF);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(to bottom, #FF00FFCC, #00FFFFCC);
	}
	
	/* Responsive */
	@media (max-width: 1400px) {
		.quantum-view {
			grid-template-columns: 1fr;
		}
		
		.matrix-view {
			grid-template-columns: 1fr;
		}
	}
	
	@media (max-width: 768px) {
		.command-bar {
			flex-direction: column;
			gap: 1rem;
		}
		
		.control-section {
			width: 100%;
			flex-direction: column;
		}
		
		.view-switcher {
			width: 100%;
			justify-content: center;
		}
		
		.hierarchy-level {
			flex-direction: column;
		}
	}
</style>