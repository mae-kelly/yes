<!-- BusinessUnitMetrics.svelte - Quantum Division Matrix Interface -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedDivision = null;
	let divisionDetails = [];
	let searchTerm = '';
	let visualMode = 'helix'; // 'helix', 'matrix', 'constellation'
	let quantumPhase = 0;
	let dataFlowActive = true;
	let neuralPulse = 0;
	let matrixGrid = [];
	let helixRotation = { x: 0, y: 0, z: 0 };
	let constellationNodes = [];
	
	// Animation intervals
	let phaseInterval;
	let pulseInterval;
	let helixInterval;
	let matrixInterval;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/business_unit_metrics');
			let result = await response.json();
			data = result;
			loading = false;
			initializeQuantumSystem();
			startAnimations();
		} catch (err) {
			console.error('Division matrix sync failed:', err);
			loading = false;
		}
	});
	
	onDestroy(() => {
		if (phaseInterval) clearInterval(phaseInterval);
		if (pulseInterval) clearInterval(pulseInterval);
		if (helixInterval) clearInterval(helixInterval);
		if (matrixInterval) clearInterval(matrixInterval);
	});
	
	function initializeQuantumSystem() {
		// Initialize matrix grid
		for (let i = 0; i < 10; i++) {
			matrixGrid.push([]);
			for (let j = 0; j < 10; j++) {
				matrixGrid[i].push({
					active: Math.random() > 0.7,
					intensity: Math.random(),
					symbol: String.fromCharCode(9632 + Math.floor(Math.random() * 20))
				});
			}
		}
		
		// Initialize constellation nodes
		if (data.business_intelligence) {
			let divisions = Object.entries(data.business_intelligence).slice(0, 30);
			divisions.forEach(([division, count], i) => {
				let phi = Math.acos(-1 + (2 * i) / divisions.length);
				let theta = Math.sqrt(divisions.length * Math.PI) * phi;
				
				constellationNodes.push({
					division: division,
					count: count,
					x: Math.cos(theta) * Math.sin(phi) * 200,
					y: Math.sin(theta) * Math.sin(phi) * 200,
					z: Math.cos(phi) * 200,
					connections: []
				});
			});
			
			// Create connections
			constellationNodes.forEach((node, i) => {
				let connectionCount = Math.min(3, Math.floor(Math.random() * 5));
				for (let j = 0; j < connectionCount; j++) {
					let targetIndex = Math.floor(Math.random() * constellationNodes.length);
					if (targetIndex !== i) {
						node.connections.push(targetIndex);
					}
				}
			});
		}
	}
	
	function startAnimations() {
		phaseInterval = setInterval(() => {
			quantumPhase = (quantumPhase + 1) % 360;
		}, 50);
		
		pulseInterval = setInterval(() => {
			neuralPulse = Math.sin(Date.now() * 0.001) * 0.5 + 0.5;
		}, 50);
		
		helixInterval = setInterval(() => {
			helixRotation = {
				x: (helixRotation.x + 0.5) % 360,
				y: (helixRotation.y + 1) % 360,
				z: (helixRotation.z + 0.25) % 360
			};
		}, 50);
		
		matrixInterval = setInterval(() => {
			matrixGrid = matrixGrid.map(row => 
				row.map(cell => ({
					...cell,
					active: Math.random() > 0.8 ? !cell.active : cell.active,
					intensity: Math.random()
				}))
			);
		}, 500);
	}
	
	$: filteredDivisions = data.business_intelligence ? 
		Object.entries(data.business_intelligence)
			.filter(([division]) => division.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredDivisions.length > 0 ? Math.max(...filteredDivisions.map(([,c]) => c)) : 1;
	$: minCount = filteredDivisions.length > 0 ? Math.min(...filteredDivisions.map(([,c]) => c)) : 0;
	
	function calculateDivisionMetrics(count) {
		let normalized = (count - minCount) / (maxCount - minCount || 1);
		let percentile = normalized * 100;
		
		let classification, powerLevel, threatIndex, color, symbol;
		
		if (percentile >= 85) {
			classification = 'NEXUS';
			powerLevel = 100;
			threatIndex = 95;
			color = '#ff00ff';
			symbol = '⬢';
		} else if (percentile >= 65) {
			classification = 'PRIME';
			powerLevel = 75;
			threatIndex = 70;
			color = '#ff6600';
			symbol = '⬡';
		} else if (percentile >= 45) {
			classification = 'CORE';
			powerLevel = 50;
			threatIndex = 45;
			color = '#00ff00';
			symbol = '◆';
		} else if (percentile >= 25) {
			classification = 'SECTOR';
			powerLevel = 30;
			threatIndex = 25;
			color = '#00ffff';
			symbol = '◇';
		} else {
			classification = 'FRONTIER';
			powerLevel = 15;
			threatIndex = 10;
			color = '#0099ff';
			symbol = '○';
		}
		
		return {
			classification: classification,
			powerLevel: powerLevel,
			threatIndex: threatIndex,
			color: color,
			symbol: symbol,
			percentile: percentile.toFixed(1),
			quantumSignature: generateQuantumCode(count),
			dataFlow: (count * 0.001).toFixed(2),
			neuralDensity: (normalized * 1000).toFixed(0)
		};
	}
	
	function generateQuantumCode(seed) {
		let code = [];
		let chars = '0123456789ABCDEF';
		for (let i = 0; i < 4; i++) {
			let segment = '';
			for (let j = 0; j < 4; j++) {
				segment += chars[(seed * (i + j + 1) * 997) % 16];
			}
			code.push(segment);
		}
		return code.join('-');
	}
	
	function getPercentage(count) {
		let total = Object.values(data.business_intelligence || {}).reduce((a, b) => a + b, 0);
		return total > 0 ? ((count / total) * 100).toFixed(2) : '0.00';
	}
	
	async function drillDownDivision(division, count) {
		selectedDivision = { division: division, count: count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(division)}`);
			let result = await response.json();
			divisionDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Division deep scan failed:', err);
			divisionDetails = [];
			loading = false;
		}
	}
	
	function closeDetails() {
		selectedDivision = null;
		divisionDetails = [];
	}
</script>

<div class="quantum-division-matrix">
	<!-- Quantum Background Effects -->
	<div class="quantum-field">
		<div class="quantum-wave" style="transform: rotate({quantumPhase}deg)"></div>
		<div class="quantum-wave wave-2" style="transform: rotate({-quantumPhase * 1.5}deg)"></div>
		<div class="quantum-wave wave-3" style="transform: rotate({quantumPhase * 0.75}deg)"></div>
	</div>
	
	<!-- Matrix Grid Background -->
	<div class="matrix-grid-bg">
		{#each matrixGrid as row, i}
			{#each row as cell, j}
				{#if cell.active}
					<div class="grid-cell" 
						 style="left: {j * 10}%; 
								top: {i * 10}%; 
								opacity: {cell.intensity};
								color: {cell.intensity > 0.5 ? '#00ffff' : '#ff00ff'}">
						{cell.symbol}
					</div>
				{/if}
			{/each}
		{/each}
	</div>
	
	<div class="division-interface">
		<!-- Quantum Header -->
		<header class="quantum-header">
			<div class="header-left">
				<div class="quantum-logo">
					<div class="logo-helix" style="transform: rotateX({helixRotation.x}deg) rotateY({helixRotation.y}deg) rotateZ({helixRotation.z}deg)">
						<div class="helix-strand strand-1"></div>
						<div class="helix-strand strand-2"></div>
						<div class="helix-core">⬢</div>
					</div>
				</div>
				<div class="header-info">
					<h1 class="matrix-title">DIVISION QUANTUM MATRIX</h1>
					<div class="sync-status">
						<span class="sync-indicator" style="opacity: {neuralPulse}"></span>
						<span class="sync-text">NEURAL SYNC: {(neuralPulse * 100).toFixed(0)}%</span>
					</div>
				</div>
			</div>
			
			<div class="control-center">
				<input 
					type="text" 
					bind:value={searchTerm}
					placeholder="QUANTUM SEARCH..."
					class="quantum-input"
				/>
				<div class="scan-line" style="width: {searchTerm ? '100%' : '0'}"></div>
			</div>
			
			<div class="mode-selector">
				<button class="mode-btn {visualMode === 'helix' ? 'active' : ''}" 
						on:click={() => visualMode = 'helix'}>
					<span class="mode-icon">⬢</span>
					HELIX
				</button>
				<button class="mode-btn {visualMode === 'matrix' ? 'active' : ''}" 
						on:click={() => visualMode = 'matrix'}>
					<span class="mode-icon">◈</span>
					MATRIX
				</button>
				<button class="mode-btn {visualMode === 'constellation' ? 'active' : ''}" 
						on:click={() => visualMode = 'constellation'}>
					<span class="mode-icon">✦</span>
					CONSTELLATION
				</button>
			</div>
		</header>
		
		<!-- Main Content Area -->
		<div class="content-matrix">
			{#if loading && !selectedDivision}
				<div class="quantum-loader">
					<div class="loader-helix">
						<div class="helix-ring ring-1"></div>
						<div class="helix-ring ring-2"></div>
						<div class="helix-ring ring-3"></div>
					</div>
					<p class="loader-text">SYNCHRONIZING DIVISION MATRIX...</p>
				</div>
			{:else if selectedDivision}
				{#key selectedDivision}
				<div class="division-detail-interface">
					<div class="detail-header">
						<div class="division-hologram">
							<div class="hologram-core">
								{calculateDivisionMetrics(selectedDivision.count).symbol}
							</div>
							<div class="division-info">
								<h2>{selectedDivision.division.toUpperCase()}</h2>
								<div class="quantum-code">
									{calculateDivisionMetrics(selectedDivision.count).quantumSignature}
								</div>
							</div>
						</div>
						<button class="matrix-close" on:click={closeDetails}>
							<span>⬡</span>
						</button>
					</div>
					
					<div class="metrics-matrix">
						<div class="metric-node">
							<div class="node-value" style="color: {calculateDivisionMetrics(selectedDivision.count).color}">{selectedDivision.count.toLocaleString()}</div>
							<div class="node-label">NODES</div>
						</div>
						<div class="metric-node">
							<div class="node-value" style="color: {calculateDivisionMetrics(selectedDivision.count).color}">{getPercentage(selectedDivision.count)}%</div>
							<div class="node-label">CONTROL</div>
						</div>
						<div class="metric-node">
							<div class="node-value" style="color: {calculateDivisionMetrics(selectedDivision.count).color}">{calculateDivisionMetrics(selectedDivision.count).classification}</div>
							<div class="node-label">CLASS</div>
						</div>
						<div class="metric-node">
							<div class="node-value" style="color: {calculateDivisionMetrics(selectedDivision.count).color}">{calculateDivisionMetrics(selectedDivision.count).neuralDensity}</div>
							<div class="node-label">DENSITY</div>
						</div>
					</div>
					
					<div class="data-stream">
						<table class="stream-table">
							<thead>
								<tr>
									<th>NODE_ID</th>
									<th>SECTOR</th>
									<th>REGION</th>
									<th>INFRA</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each divisionDetails as host}
									<tr class="stream-row">
										<td class="node-id">{host.host.substring(0, 20)}</td>
										<td>{host.country || 'UNKNOWN'}</td>
										<td>{host.region || 'UNKNOWN'}</td>
										<td>{host.infrastructure_type || 'UNKNOWN'}</td>
										<td>
											<span class="quantum-status {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'synced' : 'desynced'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? '◈' : '○'}
											</span>
										</td>
										<td>
											<span class="quantum-status {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'shielded' : 'exposed'}">
												{host.tanium_coverage?.toLowerCase().includes('tanium') ? '⬢' : '⬡'}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
				{/key}
			{:else if visualMode === 'helix'}
				<div class="helix-visualization">
					<div class="helix-container">
						{#each filteredDivisions.slice(0, 20) as [division, count], i}
							{#key division}
							<div class="helix-node"
								 style="transform: translate3d({Math.cos((i / 20) * Math.PI * 4) * 150}px, {(i / 20) * 400 - 200}px, {Math.sin((i / 20) * Math.PI * 4) * 150}px);
										background: radial-gradient(circle, {calculateDivisionMetrics(count).color}, transparent);
										box-shadow: 0 0 {20 + calculateDivisionMetrics(count).powerLevel * 0.3}px {calculateDivisionMetrics(count).color}"
								 on:click={() => drillDownDivision(division, count)}>
								<div class="helix-node-content">
									<span class="node-symbol" style="color: {calculateDivisionMetrics(count).color}">{calculateDivisionMetrics(count).symbol}</span>
									<span class="node-name">{division.substring(0, 10)}</span>
									<span class="node-power">{calculateDivisionMetrics(count).percentile}%</span>
								</div>
							</div>
							{/key}
						{/each}
						
						<!-- Helix DNA Strands -->
						<svg class="helix-strands" viewBox="0 0 300 400">
							{#each Array(20) as _, i}
								<line x1="{150 + Math.cos((i / 20) * Math.PI * 4) * 100}" 
									  y1="{(i / 20) * 400}" 
									  x2="{150 + Math.cos(((i + 1) / 20) * Math.PI * 4) * 100}" 
									  y2="{((i + 1) / 20) * 400}"
									  stroke="#00ffff" stroke-width="0.5" opacity="0.3"/>
								<line x1="{300 - (150 + Math.cos((i / 20) * Math.PI * 4) * 100)}" 
									  y1="{(i / 20) * 400}" 
									  x2="{300 - (150 + Math.cos(((i + 1) / 20) * Math.PI * 4) * 100)}" 
									  y2="{((i + 1) / 20) * 400}"
									  stroke="#ff00ff" stroke-width="0.5" opacity="0.3"/>
							{/each}
						</svg>
					</div>
				</div>
			{:else if visualMode === 'matrix'}
				<div class="matrix-visualization">
					<div class="matrix-container">
						{#each filteredDivisions.slice(0, 25) as [division, count], i}
							{#key division}
							<div class="matrix-cell-large"
								 style="left: {(i % 5) * 20}%;
										top: {Math.floor(i / 5) * 20}%;
										background: linear-gradient(135deg, {calculateDivisionMetrics(count).color}20, transparent);
										border-color: {calculateDivisionMetrics(count).color}"
								 on:click={() => drillDownDivision(division, count)}>
								<div class="cell-header">
									<span class="cell-symbol" style="color: {calculateDivisionMetrics(count).color}">{calculateDivisionMetrics(count).symbol}</span>
									<span class="cell-class">{calculateDivisionMetrics(count).classification}</span>
								</div>
								<div class="cell-name">{division.substring(0, 15).toUpperCase()}</div>
								<div class="cell-metrics">
									<div class="metric-bar">
										<div class="bar-fill" style="width: {calculateDivisionMetrics(count).percentile}%; background: {calculateDivisionMetrics(count).color}"></div>
									</div>
									<span class="metric-value">{count.toLocaleString()}</span>
								</div>
								<div class="cell-footer">
									<span class="threat-index">T:{calculateDivisionMetrics(count).threatIndex}</span>
									<span class="power-level">P:{calculateDivisionMetrics(count).powerLevel}</span>
								</div>
							</div>
							{/key}
						{/each}
					</div>
				</div>
			{:else if visualMode === 'constellation'}
				<div class="constellation-visualization">
					<div class="constellation-container">
						<svg class="constellation-svg" viewBox="-250 -250 500 500">
							<defs>
								<radialGradient id="nodeGradient">
									<stop offset="0%" style="stop-color:#00ffff;stop-opacity:1" />
									<stop offset="100%" style="stop-color:#00ffff;stop-opacity:0" />
								</radialGradient>
								<filter id="glow">
									<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
									<feMerge>
										<feMergeNode in="coloredBlur"/>
										<feMergeNode in="SourceGraphic"/>
									</feMerge>
								</filter>
							</defs>
							
							<!-- Connections -->
							{#each constellationNodes as node, i}
								{#each node.connections as targetIndex}
									{#if targetIndex < constellationNodes.length}
										<line 
											x1="{node.x}" y1="{node.y}"
											x2="{constellationNodes[targetIndex].x}" 
											y2="{constellationNodes[targetIndex].y}"
											stroke="#00ffff" 
											stroke-width="0.5" 
											opacity="0.2"/>
									{/if}
								{/each}
							{/each}
							
							<!-- Nodes -->
							{#each constellationNodes as node}
								{#key node.division}
								<g class="constellation-node"
								   transform="translate({node.x}, {node.y})"
								   on:click={() => drillDownDivision(node.division, node.count)}>
									<circle r="{5 + calculateDivisionMetrics(node.count).powerLevel * 0.1}" 
											fill={calculateDivisionMetrics(node.count).color}
											filter="url(#glow)"
											opacity="0.8"/>
									<text y="-10" text-anchor="middle" 
										  fill="#ffffff" font-size="6" opacity="0.8">
										{node.division.substring(0, 10)}
									</text>
								</g>
								{/key}
							{/each}
						</svg>
					</div>
				</div>
			{/if}
			
			<!-- Division Data Table -->
			<div class="division-data-matrix">
				<table class="quantum-table">
					<thead>
						<tr>
							<th>RANK</th>
							<th>DIVISION</th>
							<th>CLASS</th>
							<th>NODES</th>
							<th>CONTROL</th>
							<th>POWER</th>
							<th>QUANTUM_ID</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredDivisions as [division, count], index}
							{#key division}
							<tr class="data-row"
								style="border-left: 3px solid {calculateDivisionMetrics(count).color}"
								on:click={() => drillDownDivision(division, count)}>
								<td class="rank-cell">
									<span style="color: {calculateDivisionMetrics(count).color}">#{index + 1}</span>
								</td>
								<td class="division-cell">
									<span class="division-symbol" style="color: {calculateDivisionMetrics(count).color}">{calculateDivisionMetrics(count).symbol}</span>
									<span class="division-name">{division.substring(0, 30).toUpperCase()}</span>
								</td>
								<td>
									<span class="class-badge" style="background: {calculateDivisionMetrics(count).color}15; color: {calculateDivisionMetrics(count).color}; border: 1px solid {calculateDivisionMetrics(count).color}">
										{calculateDivisionMetrics(count).classification}
									</span>
								</td>
								<td class="numeric">{count.toLocaleString()}</td>
								<td>
									<div class="control-meter">
										<div class="meter-fill" style="width: {getPercentage(count)}%; background: linear-gradient(90deg, transparent, {calculateDivisionMetrics(count).color})"></div>
										<span class="meter-text">{getPercentage(count)}%</span>
									</div>
								</td>
								<td>
									<div class="power-indicator">
										<div class="power-bar" style="height: {calculateDivisionMetrics(count).powerLevel}%; background: {calculateDivisionMetrics(count).color}"></div>
										<span class="power-text">{calculateDivisionMetrics(count).powerLevel}</span>
									</div>
								</td>
								<td class="quantum-id">{calculateDivisionMetrics(count).quantumSignature}</td>
							</tr>
							{/key}
						{/each}
					</tbody>
				</table>
			</div>