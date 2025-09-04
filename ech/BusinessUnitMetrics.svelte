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
			const divisions = Object.entries(data.business_intelligence).slice(0, 30);
			divisions.forEach(([division, count], i) => {
				const phi = Math.acos(-1 + (2 * i) / divisions.length);
				const theta = Math.sqrt(divisions.length * Math.PI) * phi;
				
				constellationNodes.push({
					division,
					count,
					x: Math.cos(theta) * Math.sin(phi) * 200,
					y: Math.sin(theta) * Math.sin(phi) * 200,
					z: Math.cos(phi) * 200,
					connections: []
				});
			});
			
			// Create connections
			constellationNodes.forEach((node, i) => {
				const connectionCount = Math.min(3, Math.floor(Math.random() * 5));
				for (let j = 0; j < connectionCount; j++) {
					const targetIndex = Math.floor(Math.random() * constellationNodes.length);
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
		const normalized = (count - minCount) / (maxCount - minCount || 1);
		const percentile = normalized * 100;
		
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
			classification,
			powerLevel,
			threatIndex,
			color,
			symbol,
			percentile: percentile.toFixed(1),
			quantumSignature: generateQuantumCode(count),
			dataFlow: (count * 0.001).toFixed(2),
			neuralDensity: (normalized * 1000).toFixed(0)
		};
	}
	
	function generateQuantumCode(seed) {
		const code = [];
		const chars = '0123456789ABCDEF';
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
		const total = Object.values(data.business_intelligence || {}).reduce((a, b) => a + b, 0);
		return total > 0 ? ((count / total) * 100).toFixed(2) : '0.00';
	}
	
	async function drillDownDivision(division, count) {
		selectedDivision = { division, count };
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
						{@const metrics = calculateDivisionMetrics(selectedDivision.count)}
						<div class="metric-node">
							<div class="node-value" style="color: {metrics.color}">{selectedDivision.count.toLocaleString()}</div>
							<div class="node-label">NODES</div>
						</div>
						<div class="metric-node">
							<div class="node-value" style="color: {metrics.color}">{getPercentage(selectedDivision.count)}%</div>
							<div class="node-label">CONTROL</div>
						</div>
						<div class="metric-node">
							<div class="node-value" style="color: {metrics.color}">{metrics.classification}</div>
							<div class="node-label">CLASS</div>
						</div>
						<div class="metric-node">
							<div class="node-value" style="color: {metrics.color}">{metrics.neuralDensity}</div>
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
			{:else if visualMode === 'helix'}
				<div class="helix-visualization">
					<div class="helix-container">
						{#each filteredDivisions.slice(0, 20) as [division, count], i}
							{@const metrics = calculateDivisionMetrics(count)}
							{@const angle = (i / 20) * Math.PI * 4}
							{@const y = (i / 20) * 400 - 200}
							{@const x = Math.cos(angle) * 150}
							{@const z = Math.sin(angle) * 150}
							
							<div class="helix-node"
								 style="transform: translate3d({x}px, {y}px, {z}px);
										background: radial-gradient(circle, {metrics.color}, transparent);
										box-shadow: 0 0 {20 + metrics.powerLevel * 0.3}px {metrics.color}"
								 on:click={() => drillDownDivision(division, count)}>
								<div class="helix-node-content">
									<span class="node-symbol" style="color: {metrics.color}">{metrics.symbol}</span>
									<span class="node-name">{division.substring(0, 10)}</span>
									<span class="node-power">{metrics.percentile}%</span>
								</div>
							</div>
						{/each}
						
						<!-- Helix DNA Strands -->
						<svg class="helix-strands" viewBox="0 0 300 400">
							{#each Array(20) as _, i}
								{@const angle1 = (i / 20) * Math.PI * 4}
								{@const angle2 = ((i + 1) / 20) * Math.PI * 4}
								{@const y1 = (i / 20) * 400}
								{@const y2 = ((i + 1) / 20) * 400}
								{@const x1 = 150 + Math.cos(angle1) * 100}
								{@const x2 = 150 + Math.cos(angle2) * 100}
								
								<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
									  stroke="#00ffff" stroke-width="0.5" opacity="0.3"/>
								<line x1="{300 - x1}" y1="{y1}" x2="{300 - x2}" y2="{y2}"
									  stroke="#ff00ff" stroke-width="0.5" opacity="0.3"/>
							{/each}
						</svg>
					</div>
				</div>
			{:else if visualMode === 'matrix'}
				<div class="matrix-visualization">
					<div class="matrix-container">
						{#each filteredDivisions.slice(0, 25) as [division, count], i}
							{@const metrics = calculateDivisionMetrics(count)}
							{@const row = Math.floor(i / 5)}
							{@const col = i % 5}
							
							<div class="matrix-cell-large"
								 style="left: {col * 20}%;
										top: {row * 20}%;
										background: linear-gradient(135deg, {metrics.color}20, transparent);
										border-color: {metrics.color}"
								 on:click={() => drillDownDivision(division, count)}>
								<div class="cell-header">
									<span class="cell-symbol" style="color: {metrics.color}">{metrics.symbol}</span>
									<span class="cell-class">{metrics.classification}</span>
								</div>
								<div class="cell-name">{division.substring(0, 15).toUpperCase()}</div>
								<div class="cell-metrics">
									<div class="metric-bar">
										<div class="bar-fill" style="width: {metrics.percentile}%; background: {metrics.color}"></div>
									</div>
									<span class="metric-value">{count.toLocaleString()}</span>
								</div>
								<div class="cell-footer">
									<span class="threat-index">T:{metrics.threatIndex}</span>
									<span class="power-level">P:{metrics.powerLevel}</span>
								</div>
							</div>
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
								{@const metrics = calculateDivisionMetrics(node.count)}
								<g class="constellation-node"
								   transform="translate({node.x}, {node.y})"
								   on:click={() => drillDownDivision(node.division, node.count)}>
									<circle r="{5 + metrics.powerLevel * 0.1}" 
											fill={metrics.color}
											filter="url(#glow)"
											opacity="0.8"/>
									<text y="-10" text-anchor="middle" 
										  fill="#ffffff" font-size="6" opacity="0.8">
										{node.division.substring(0, 10)}
									</text>
								</g>
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
							{@const metrics = calculateDivisionMetrics(count)}
							<tr class="data-row"
								style="border-left: 3px solid {metrics.color}"
								on:click={() => drillDownDivision(division, count)}>
								<td class="rank-cell">
									<span style="color: {metrics.color}">#{index + 1}</span>
								</td>
								<td class="division-cell">
									<span class="division-symbol" style="color: {metrics.color}">{metrics.symbol}</span>
									<span class="division-name">{division.substring(0, 30).toUpperCase()}</span>
								</td>
								<td>
									<span class="class-badge" style="background: {metrics.color}15; color: {metrics.color}; border: 1px solid {metrics.color}">
										{metrics.classification}
									</span>
								</td>
								<td class="numeric">{count.toLocaleString()}</td>
								<td>
									<div class="control-meter">
										<div class="meter-fill" style="width: {getPercentage(count)}%; background: linear-gradient(90deg, transparent, {metrics.color})"></div>
										<span class="meter-text">{getPercentage(count)}%</span>
									</div>
								</td>
								<td>
									<div class="power-indicator">
										<div class="power-bar" style="height: {metrics.powerLevel}%; background: {metrics.color}"></div>
										<span class="power-text">{metrics.powerLevel}</span>
									</div>
								</td>
								<td class="quantum-id">{metrics.quantumSignature}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>
</div>

<style>
	.quantum-division-matrix {
		width: 100%;
		height: calc(100vh - 80px);
		background: #000000;
		position: relative;
		overflow: hidden;
	}
	
	/* Quantum Field Background */
	.quantum-field {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
		overflow: hidden;
	}
	
	.quantum-wave {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 200%;
		height: 200%;
		transform: translate(-50%, -50%);
		background: radial-gradient(ellipse at center, 
			transparent 0%, 
			rgba(0, 255, 255, 0.05) 25%, 
			transparent 50%, 
			rgba(255, 0, 255, 0.03) 75%, 
			transparent 100%);
		animation: waveExpand 8s ease-in-out infinite;
	}
	
	.wave-2 {
		animation-duration: 10s;
		animation-delay: 2s;
	}
	
	.wave-3 {
		animation-duration: 12s;
		animation-delay: 4s;
	}
	
	@keyframes waveExpand {
		0%, 100% { transform: translate(-50%, -50%) scale(0.8); opacity: 0; }
		50% { transform: translate(-50%, -50%) scale(1.5); opacity: 1; }
	}
	
	/* Matrix Grid Background */
	.matrix-grid-bg {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	
	.grid-cell {
		position: absolute;
		font-size: 0.8rem;
		font-family: 'Courier New', monospace;
		animation: gridFade 3s ease-in-out infinite;
	}
	
	@keyframes gridFade {
		0%, 100% { opacity: 0.1; }
		50% { opacity: 0.5; }
	}
	
	.division-interface {
		position: relative;
		z-index: 1;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
	
	/* Quantum Header */
	.quantum-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.1), rgba(0, 0, 0, 0.9));
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		backdrop-filter: blur(20px);
	}
	
	.header-left {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.quantum-logo {
		width: 60px;
		height: 60px;
		perspective: 1000px;
	}
	
	.logo-helix {
		width: 100%;
		height: 100%;
		position: relative;
		transform-style: preserve-3d;
	}
	
	.helix-strand {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid;
		border-radius: 50%;
	}
	
	.strand-1 {
		border-color: #00ffff;
		transform: rotateY(0deg);
	}
	
	.strand-2 {
		border-color: #ff00ff;
		transform: rotateY(90deg);
	}
	
	.helix-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 1.5rem;
		color: #00ffff;
		text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
	}
	
	.header-info h1 {
		margin: 0;
		font-size: 1.3rem;
		font-weight: 200;
		letter-spacing: 0.3em;
		background: linear-gradient(90deg, #00ffff, #ff00ff);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}
	
	.sync-status {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-top: 0.5rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
	}
	
	.sync-indicator {
		width: 6px;
		height: 6px;
		background: #00ff00;
		border-radius: 50%;
		box-shadow: 0 0 10px #00ff00;
	}
	
	/* Control Center */
	.control-center {
		position: relative;
		flex: 1;
		max-width: 400px;
		margin: 0 2rem;
	}
	
	.quantum-input {
		width: 100%;
		padding: 0.75rem 1rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid rgba(0, 255, 255, 0.3);
		color: #00ffff;
		font-family: 'Courier New', monospace;
		font-size: 0.9rem;
		letter-spacing: 0.1em;
		transition: all 0.3s ease;
	}
	
	.quantum-input:focus {
		outline: none;
		border-color: #00ffff;
		background: rgba(0, 255, 255, 0.05);
		box-shadow: 0 0 30px rgba(0, 255, 255, 0.3);
	}
	
	.scan-line {
		position: absolute;
		bottom: 0;
		left: 0;
		height: 1px;
		background: linear-gradient(90deg, transparent, #00ffff, transparent);
		transition: width 0.3s ease;
	}
	
	/* Mode Selector */
	.mode-selector {
		display: flex;
		gap: 0.5rem;
		background: rgba(0, 0, 0, 0.8);
		padding: 0.25rem;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}
	
	.mode-btn {
		padding: 0.5rem 1rem;
		background: transparent;
		border: 1px solid transparent;
		color: rgba(255, 255, 255, 0.6);
		font-size: 0.75rem;
		letter-spacing: 0.1em;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.mode-btn:hover {
		background: rgba(0, 255, 255, 0.05);
		border-color: rgba(0, 255, 255, 0.3);
	}
	
	.mode-btn.active {
		background: rgba(0, 255, 255, 0.1);
		border-color: #00ffff;
		color: #00ffff;
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
	}
	
	.mode-icon {
		font-size: 1rem;
	}
	
	/* Content Matrix */
	.content-matrix {
		flex: 1;
		display: flex;
		gap: 2rem;
		padding: 2rem;
		overflow: hidden;
	}
	
	/* Quantum Loader */
	.quantum-loader {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}
	
	.loader-helix {
		position: relative;
		width: 100px;
		height: 100px;
	}
	
	.helix-ring {
		position: absolute;
		border: 1px solid;
		border-radius: 50%;
		animation: helixRotate 3s linear infinite;
	}
	
	.ring-1 {
		inset: 0;
		border-color: #00ffff;
	}
	
	.ring-2 {
		inset: 20px;
		border-color: #ff00ff;
		animation-direction: reverse;
	}
	
	.ring-3 {
		inset: 40px;
		border-color: #00ff00;
		animation-duration: 4s;
	}
	
	@keyframes helixRotate {
		from { transform: rotateX(60deg) rotateZ(0deg); }
		to { transform: rotateX(60deg) rotateZ(360deg); }
	}
	
	.loader-text {
		color: rgba(0, 255, 255, 0.6);
		font-size: 0.8rem;
		letter-spacing: 0.2em;
		animation: pulse 2s ease-in-out infinite;
	}
	
	/* Helix Visualization */
	.helix-visualization {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		perspective: 1000px;
	}
	
	.helix-container {
		position: relative;
		width: 300px;
		height: 400px;
		transform-style: preserve-3d;
		animation: helixRotate 20s linear infinite;
	}
	
	.helix-node {
		position: absolute;
		width: 80px;
		height: 40px;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.helix-node:hover {
		transform: scale(1.2) !important;
		z-index: 100;
	}
	
	.helix-node-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.7rem;
	}
	
	.node-symbol {
		font-size: 1.2rem;
	}
	
	.node-name {
		color: rgba(255, 255, 255, 0.8);
		font-size: 0.6rem;
		letter-spacing: 0.05em;
	}
	
	.node-power {
		color: #00ffff;
		font-weight: 600;
		font-size: 0.65rem;
	}
	
	.helix-strands {
		position: absolute;
		top: 0;
		left: 0;
		pointer-events: none;
	}
	
	/* Matrix Visualization */
	.matrix-visualization {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.matrix-container {
		position: relative;
		width: 100%;
		height: 100%;
		max-width: 800px;
		max-height: 800px;
	}
	
	.matrix-cell-large {
		position: absolute;
		width: 18%;
		height: 18%;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid;
		padding: 0.75rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
	}
	
	.matrix-cell-large:hover {
		transform: scale(1.05);
		z-index: 100;
		box-shadow: 0 0 30px currentColor;
	}
	
	.cell-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.cell-symbol {
		font-size: 1.2rem;
	}
	
	.cell-class {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
	}
	
	.cell-name {
		font-size: 0.7rem;
		font-weight: 300;
		color: #ffffff;
		letter-spacing: 0.05em;
		margin: 0.5rem 0;
	}
	
	.cell-metrics {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.metric-bar {
		flex: 1;
		height: 3px;
		background: rgba(255, 255, 255, 0.1);
	}
	
	.bar-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.metric-value {
		font-size: 0.65rem;
		color: #00ffff;
		font-family: 'Courier New', monospace;
	}
	
	.cell-footer {
		display: flex;
		justify-content: space-between;
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	/* Constellation Visualization */
	.constellation-visualization {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.constellation-container {
		width: 100%;
		height: 100%;
		max-width: 600px;
		max-height: 600px;
		animation: constellationRotate 30s linear infinite;
	}
	
	@keyframes constellationRotate {
		from { transform: rotateZ(0deg); }
		to { transform: rotateZ(360deg); }
	}
	
	.constellation-svg {
		width: 100%;
		height: 100%;
	}
	
	.constellation-node {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.constellation-node:hover {
		transform: scale(1.5);
	}
	
	/* Division Data Matrix */
	.division-data-matrix {
		width: 50%;
		overflow: auto;
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid rgba(0, 255, 255, 0.1);
		backdrop-filter: blur(10px);
	}
	
	.quantum-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.quantum-table th {
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.1), rgba(0, 0, 0, 0.8));
		color: #00ffff;
		padding: 1rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 300;
		letter-spacing: 0.2em;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		position: sticky;
		top: 0;
		z-index: 10;
	}
	
	.data-row {
		cursor: pointer;
		transition: all 0.2s ease;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.data-row:hover {
		background: rgba(0, 255, 255, 0.02);
		transform: translateX(5px);
	}
	
	.quantum-table td {
		padding: 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.rank-cell {
		font-weight: 600;
		font-family: 'Courier New', monospace;
	}
	
	.division-cell {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.division-symbol {
		font-size: 1rem;
	}
	
	.division-name {
		font-weight: 300;
		letter-spacing: 0.05em;
	}
	
	.class-badge {
		padding: 0.25rem 0.5rem;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
	}
	
	.numeric {
		font-family: 'Courier New', monospace;
		color: #00ffff;
	}
	
	.control-meter {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.meter-fill {
		flex: 1;
		height: 3px;
		max-width: 100px;
	}
	
	.meter-text {
		font-size: 0.7rem;
		min-width: 45px;
		text-align: right;
		color: rgba(255, 255, 255, 0.6);
	}
	
	.power-indicator {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.power-bar {
		width: 20px;
		height: 20px;
		background: rgba(255, 255, 255, 0.1);
		position: relative;
	}
	
	.power-text {
		font-size: 0.7rem;
		font-family: 'Courier New', monospace;
	}
	
	.quantum-id {
		font-family: 'Courier New', monospace;
		font-size: 0.65rem;
		color: rgba(0, 255, 255, 0.6);
		letter-spacing: 0.05em;
	}
	
	/* Detail Interface */
	.division-detail-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 0, 0, 0.9));
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
	}
	
	.division-hologram {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}
	
	.hologram-core {
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.3), transparent);
		border: 2px solid #00ffff;
		animation: hologramPulse 3s ease-in-out infinite;
	}
	
	@keyframes hologramPulse {
		0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 255, 0.5); transform: scale(1); }
		50% { box-shadow: 0 0 40px rgba(0, 255, 255, 0.8); transform: scale(1.05); }
	}
	
	.division-info h2 {
		margin: 0;
		font-size: 1.3rem;
		font-weight: 200;
		color: #00ffff;
		letter-spacing: 0.1em;
	}
	
	.quantum-code {
		font-family: 'Courier New', monospace;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.5);
		margin-top: 0.5rem;
		letter-spacing: 0.1em;
	}
	
	.matrix-close {
		background: none;
		border: 1px solid #ff0066;
		color: #ff0066;
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.3s ease;
		font-size: 1.5rem;
	}
	
	.matrix-close:hover {
		background: rgba(255, 0, 102, 0.1);
		box-shadow: 0 0 20px rgba(255, 0, 102, 0.5);
		transform: rotate(180deg);
	}
	
	.metrics-matrix {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
		padding: 1.5rem;
		background: rgba(0, 0, 0, 0.5);
	}
	
	.metric-node {
		text-align: center;
		padding: 1rem;
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.05), transparent);
		border: 1px solid rgba(0, 255, 255, 0.2);
	}
	
	.node-value {
		font-size: 1.5rem;
		font-weight: 100;
		margin-bottom: 0.5rem;
		text-shadow: 0 0 20px currentColor;
	}
	
	.node-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
	}
	
	.data-stream {
		flex: 1;
		overflow: auto;
		padding: 1rem;
	}
	
	.stream-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.stream-table th {
		background: rgba(0, 0, 0, 0.8);
		color: #00ffff;
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 300;
		letter-spacing: 0.1em;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		position: sticky;
		top: 0;
	}
	
	.stream-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.2s ease;
	}
	
	.stream-row:hover {
		background: rgba(0, 255, 255, 0.02);
	}
	
	.stream-table td {
		padding: 0.75rem;
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.node-id {
		font-family: 'Courier New', monospace;
		color: #00ffff;
		font-size: 0.7rem;
	}
	
	.quantum-status {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		font-size: 1rem;
	}
	
	.quantum-status.synced {
		color: #00ff00;
		text-shadow: 0 0 10px #00ff00;
	}
	
	.quantum-status.desynced {
		color: #666666;
	}
	
	.quantum-status.shielded {
		color: #00ffff;
		text-shadow: 0 0 10px #00ffff;
	}
	
	.quantum-status.exposed {
		color: #ff0066;
		text-shadow: 0 0 10px #ff0066;
	}
	
	/* Responsive */
	@media (max-width: 1400px) {
		.content-matrix {
			flex-direction: column;
		}
		
		.division-data-matrix {
			width: 100%;
			max-height: 300px;
		}
	}
	
	@media (max-width: 768px) {
		.quantum-header {
			flex-direction: column;
			gap: 1rem;
		}
		
		.mode-selector {
			width: 100%;
			justify-content: center;
		}
		
		.metrics-matrix {
			grid-template-columns: repeat(2, 1fr);
		}
	}
</style>