<!-- DataCenter.svelte - Facility Intelligence Grid -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCenter = null;
	let centerDetails = [];
	let searchTerm = '';
	let powerLevels = [];
	let gridActivity = [];

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/data_center_metrics');
			let result = await response.json();
			data = result;
			loading = false;
			
			// Initialize power levels for visualization
			for (let i = 0; i < 10; i++) {
				powerLevels.push(Math.random());
				gridActivity.push({
					x: Math.random() * 100,
					y: Math.random() * 100,
					intensity: Math.random()
				});
			}
		} catch (err) {
			console.error('Data center error:', err);
			loading = false;
		}
		
		// Power fluctuation animation
		const powerInterval = setInterval(() => {
			powerLevels = powerLevels.map(() => Math.random());
		}, 2000);
		
		return () => clearInterval(powerInterval);
	});

	$: filteredCenters = data.facility_intelligence ? 
		Object.entries(data.facility_intelligence)
			.filter(([center]) => center.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: maxCount = filteredCenters.length > 0 ? Math.max(...filteredCenters.map(([,c]) => c)) : 1;

	function getPercentage(count) {
		let total = Object.values(data.facility_intelligence || {}).reduce((a, b) => a + b, 0);
		if (!total) return 0;
		return ((count / total) * 100).toFixed(2);
	}

	function getUtilization(count) {
		return Math.min(95, (count / maxCount) * 100).toFixed(1);
	}

	function getFacilityStatus(utilization) {
		if (utilization >= 80) return { status: 'CRITICAL', color: '#ff0066', icon: '▲' };
		if (utilization >= 60) return { status: 'HIGH', color: '#ff9900', icon: '◆' };
		if (utilization >= 40) return { status: 'OPTIMAL', color: '#0a4f3c', icon: '●' };
		return { status: 'LOW', color: '#ffcc00', icon: '▼' };
	}

	async function drillDownCenter(center, count) {
		selectedCenter = { center, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(center)}`);
			let result = await response.json();
			centerDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Center drill-down error:', err);
			centerDetails = [];
			loading = false;
		}
	}

	function closeDetails() {
		selectedCenter = null;
		centerDetails = [];
	}
</script>

<div class="dashboard-container">
	<div class="main-content">
		<!-- Left Panel: Facility Command -->
		<div class="table-panel">
			<div class="panel-header">
				<div class="header-main">
					<div>
						<h3 class="panel-title">DATA CENTERS</h3>
						<div class="subtitle">FACILITY INTELLIGENCE NETWORK</div>
					</div>
					<div class="power-indicator">
						<svg viewBox="0 0 60 30" class="power-svg">
							{#each powerLevels as level, i}
								<rect x="{i * 6}" y="{30 - level * 25}" 
									  width="4" height="{level * 25}"
									  fill="#0a4f3c" opacity="{level}">
									<animate attributeName="height" 
											values="{level * 25};{level * 30};{level * 25}" 
											dur="1s" repeatCount="indefinite"/>
								</rect>
							{/each}
						</svg>
					</div>
				</div>
				<div class="controls">
					<input 
						type="text" 
						bind:value={searchTerm}
						placeholder="SEARCH FACILITIES..."
						class="search-input"
					/>
				</div>
			</div>
			
			{#if loading && !selectedCenter}
				<div class="loading-state">
					<div class="facility-loader">
						<div class="loader-core"></div>
						<div class="loader-ring"></div>
						<div class="loader-satellites">
							<div class="satellite"></div>
							<div class="satellite"></div>
							<div class="satellite"></div>
						</div>
					</div>
					<p class="loading-text">INITIALIZING FACILITY GRID...</p>
				</div>
			{:else if selectedCenter}
				<div class="drill-view">
					<div class="drill-header">
						<div class="drill-info">
							<h4>{selectedCenter.center.toUpperCase()}</h4>
							<div class="drill-metrics">
								<span class="metric-item">ASSETS: {selectedCenter.count.toLocaleString()}</span>
								<span class="metric-item">UTILIZATION: {getUtilization(selectedCenter.count)}%</span>
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
									<th>COUNTRY</th>
									<th>INFRASTRUCTURE</th>
									<th>CMDB</th>
									<th>TANIUM</th>
								</tr>
							</thead>
							<tbody>
								{#each centerDetails as host}
									<tr>
										<td class="host-cell">{host.host.substring(0, 30)}</td>
										<td>{host.region || 'CLASSIFIED'}</td>
										<td>{host.country || 'CLASSIFIED'}</td>
										<td>{host.infrastructure_type || 'CLASSIFIED'}</td>
										<td>
											<span class="status-badge {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
												{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'ONLINE' : 'OFFLINE'}
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
								<th>FACILITY</th>
								<th>ASSETS</th>
								<th>UTILIZATION</th>
								<th>STATUS</th>
								<th>POWER GRID</th>
							</tr>
						</thead>
						<tbody>
							{#each filteredCenters as [center, count]}
								{@const utilization = getUtilization(count)}
								{@const status = getFacilityStatus(utilization)}
								<tr on:click={() => drillDownCenter(center, count)}>
									<td class="center-cell">
										<div class="center-icon" style="color: {status.color}">{status.icon}</div>
										<span class="center-name">{center.substring(0, 30).toUpperCase()}</span>
									</td>
									<td class="center">{count.toLocaleString()}</td>
									<td class="center">
										<div class="utilization-display">
											<span class="util-value">{utilization}%</span>
											<div class="util-bar-bg">
												<div class="util-bar" style="width: {utilization}%; background: {status.color}"></div>
											</div>
										</div>
									</td>
									<td class="center">
										<span class="status-indicator" style="color: {status.color}; border-color: {status.color}">
											{status.status}
										</span>
									</td>
									<td>
										<div class="power-grid">
											<svg viewBox="0 0 50 20" class="grid-svg">
												<defs>
													<linearGradient id="powerGrad{center}" x1="0%" y1="0%" x2="100%" y2="0%">
														<stop offset="0%" style="stop-color:#0a4f3c;stop-opacity:0.2" />
														<stop offset="{utilization}%" style="stop-color:{status.color};stop-opacity:1" />
														<stop offset="100%" style="stop-color:#111;stop-opacity:0.2" />
													</linearGradient>
												</defs>
												<rect x="0" y="8" width="50" height="4" fill="url(#powerGrad{center})"/>
												{#each Array(5) as _, i}
													<circle cx="{i * 12 + 6}" cy="10" r="3" 
															fill={i < Math.ceil(utilization/20) ? status.color : '#111'} 
															opacity={i < Math.ceil(utilization/20) ? '1' : '0.3'}>
														{#if i < Math.ceil(utilization/20)}
															<animate attributeName="r" values="3;4;3" dur="1s" repeatCount="indefinite"/>
														{/if}
													</circle>
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

		<!-- Right Panel: Facility Intelligence -->
		<div class="viz-panel">
			<!-- Facility Metrics -->
			<div class="metrics-command">
				<div class="metric-card">
					<div class="metric-header">
						<div class="metric-icon">◈</div>
						<span class="metric-label">FACILITIES</span>
					</div>
					<div class="metric-value">{filteredCenters.length}</div>
					<div class="metric-graph">
						<svg viewBox="0 0 60 20">
							{#each Array(10) as _, i}
								<line x1="{i * 6}" y1="20" x2="{i * 6}" y2="{20 - Math.random() * 15}" 
									  stroke="#0a4f3c" stroke-width="2" opacity="{Math.random()}"/>
							{/each}
						</svg>
					</div>
				</div>
				<div class="metric-card">
					<div class="metric-header">
						<div class="metric-icon">◉</div>
						<span class="metric-label">AVG/CENTER</span>
					</div>
					<div class="metric-value">{Math.round(Object.values(data.facility_intelligence || {}).reduce((a, b) => a + b, 0) / filteredCenters.length || 0)}</div>
					<div class="metric-graph">
						<svg viewBox="0 0 60 20">
							<polyline points="0,15 10,10 20,12 30,8 40,14 50,9 60,11" 
									  fill="none" stroke="#0a4f3c" stroke-width="1"/>
						</svg>
					</div>
				</div>
			</div>

			<!-- Facility Network Map -->
			<div class="viz-card">
				<div class="card-header">
					<h4>FACILITY NETWORK</h4>
					<div class="card-status active"></div>
				</div>
				<div class="network-map">
					<svg viewBox="0 0 120 120" class="network-svg">
						<defs>
							<radialGradient id="nodeGlow">
								<stop offset="0%" style="stop-color:#0a4f3c;stop-opacity:1" />
								<stop offset="100%" style="stop-color:#0a4f3c;stop-opacity:0" />
							</radialGradient>
							<filter id="blur">
								<feGaussianBlur in="SourceGraphic" stdDeviation="1" />
							</filter>
						</defs>
						
						<!-- Grid background -->
						<pattern id="gridPattern" width="20" height="20" patternUnits="userSpaceOnUse">
							<path d="M 20 0 L 0 0 0 20" fill="none" stroke="#0a4f3c" stroke-width="0.2" opacity="0.3"/>
						</pattern>
						<rect width="120" height="120" fill="url(#gridPattern)" />
						
						<!-- Central node -->
						<circle cx="60" cy="60" r="8" fill="#0a4f3c" filter="url(#blur)"/>
						<circle cx="60" cy="60" r="12" fill="none" stroke="#0a4f3c" stroke-width="1" opacity="0.5">
							<animate attributeName="r" values="12;20;12" dur="3s" repeatCount="indefinite"/>
							<animate attributeName="opacity" values="0.5;0.1;0.5" dur="3s" repeatCount="indefinite"/>
						</circle>
						
						<!-- Facility nodes -->
						{#each filteredCenters.slice(0, 6) as [center, count], i}
							{@const angle = (i * 60) * Math.PI / 180}
							{@const x = 60 + Math.cos(angle) * 35}
							{@const y = 60 + Math.sin(angle) * 35}
							{@const utilization = getUtilization(count)}
							{@const status = getFacilityStatus(utilization)}
							
							<line x1="60" y1="60" x2="{x}" y2="{y}" 
								  stroke="#0a4f3c" stroke-width="0.5" opacity="0.3"/>
							<circle cx="{x}" cy="{y}" r="{4 + (count/maxCount) * 4}" 
									fill="url(#nodeGlow)" opacity="0.5"/>
							<circle cx="{x}" cy="{y}" r="{3 + (count/maxCount) * 3}" 
									fill={status.color} opacity="0.8"/>
							
							<!-- Pulse animation for high utilization -->
							{#if utilization > 60}
								<circle cx="{x}" cy="{y}" r="{3 + (count/maxCount) * 3}" 
										fill="none" stroke={status.color} stroke-width="1">
									<animate attributeName="r" 
											values="{3 + (count/maxCount) * 3};{8 + (count/maxCount) * 3};{3 + (count/maxCount) * 3}" 
											dur="2s" repeatCount="indefinite"/>
									<animate attributeName="opacity" values="0.8;0;0.8" dur="2s" repeatCount="indefinite"/>
								</circle>
							{/if}
						{/each}
					</svg>
				</div>
			</div>

			<!-- Utilization Matrix -->
			<div class="viz-card">
				<div class="card-header">
					<h4>UTILIZATION MATRIX</h4>
					<div class="card-status"></div>
				</div>
				<div class="utilization-matrix">
					{#each filteredCenters.slice(0, 6) as [center, count]}
						{@const utilization = getUtilization(count)}
						{@const status = getFacilityStatus(utilization)}
						<div class="matrix-item">
							<div class="matrix-header">
								<span class="matrix-name">{center.substring(0, 8).toUpperCase()}</span>
								<span class="matrix-percent" style="color: {status.color}">{utilization}%</span>
							</div>
							<div class="matrix-bars">
								{#each Array(10) as _, i}
									<div class="matrix-bar" 
										 style="background: {i < Math.ceil(utilization/10) ? status.color : '#111'}">
									</div>
								{/each}
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Capacity Analysis -->
			<div class="viz-card">
				<div class="card-header">
					<h4>CAPACITY ANALYSIS</h4>
					<div class="card-status active"></div>
				</div>
				<div class="capacity-chart">
					{#each filteredCenters.slice(0, 5) as [center, count]}
						{@const utilization = getUtilization(count)}
						{@const status = getFacilityStatus(utilization)}
						<div class="capacity-item">
							<div class="capacity-label">{center.substring(0, 15).toUpperCase()}</div>
							<div class="capacity-visual">
								<div class="capacity-track"></div>
								<div class="capacity-fill" 
									 style="width: {(count/maxCount)*100}%; 
											background: linear-gradient(90deg, #0a4f3c, {status.color})">
									<div class="capacity-marker"></div>
								</div>
								<span class="capacity-value">{count}</span>
							</div>
							<div class="capacity-status">
								<span class="status-text" style="color: {status.color}">{status.status}</span>
								<span class="status-icon" style="color: {status.color}">{status.icon}</span>
							</div>
						</div>
					{/each}
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

	.table-panel::after {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, #0a4f3c, transparent);
		animation: scanLine 3s linear infinite;
	}

	@keyframes scanLine {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100%); }
	}

	.panel-header {
		padding: 1.5rem;
		border-bottom: 1px solid #0a4f3c;
		background: rgba(10, 79, 60, 0.02);
		flex-shrink: 0;
	}

	.header-main {
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

	.power-indicator {
		width: 60px;
		height: 30px;
	}

	.power-svg {
		width: 100%;
		height: 100%;
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

	.facility-loader {
		width: 100px;
		height: 100px;
		position: relative;
	}

	.loader-core {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 20px;
		height: 20px;
		background: #0a4f3c;
		border-radius: 50%;
		box-shadow: 0 0 20px rgba(10, 79, 60, 0.8);
	}

	.loader-ring {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 60px;
		height: 60px;
		border: 2px solid #0a4f3c;
		border-radius: 50%;
		border-top-color: transparent;
		animation: ringRotate 1.5s linear infinite;
	}

	@keyframes ringRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	.loader-satellites {
		position: absolute;
		width: 100%;
		height: 100%;
		animation: satelliteOrbit 3s linear infinite;
	}

	@keyframes satelliteOrbit {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.satellite {
		position: absolute;
		width: 6px;
		height: 6px;
		background: #0a4f3c;
		border-radius: 50%;
	}

	.satellite:nth-child(1) {
		top: 10px;
		left: 50%;
		transform: translateX(-50%);
	}

	.satellite:nth-child(2) {
		bottom: 10px;
		left: 50%;
		transform: translateX(-50%);
	}

	.satellite:nth-child(3) {
		top: 50%;
		right: 10px;
		transform: translateY(-50%);
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

	.center-cell {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.center-icon {
		font-size: 1rem;
		animation: iconPulse 2s ease-in-out infinite;
	}

	@keyframes iconPulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.2); }
	}

	.center-name {
		font-weight: 500;
		color: #e0e0e0;
	}

	.center {
		text-align: center;
	}

	.utilization-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}

	.util-value {
		font-size: 0.75rem;
		font-weight: 600;
		color: #b8a678;
	}

	.util-bar-bg {
		width: 60px;
		height: 4px;
		background: rgba(10, 79, 60, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}

	.util-bar {
		height: 100%;
		transition: width 0.3s ease;
	}

	.status-indicator {
		padding: 0.3rem 0.6rem;
		border: 1px solid;
		border-radius: 2px;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
	}

	.power-grid {
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.grid-svg {
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
		position: relative;
		overflow: hidden;
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
		margin-bottom: 0.5rem;
	}

	.metric-graph {
		height: 20px;
		opacity: 0.6;
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

	.network-map {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 120px;
	}

	.network-svg {
		width: 100%;
		max-width: 120px;
		height: auto;
	}

	.utilization-matrix {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.75rem;
	}

	.matrix-item {
		background: rgba(0, 0, 0, 0.5);
		border: 1px solid #111;
		border-radius: 4px;
		padding: 0.75rem;
	}

	.matrix-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.matrix-name {
		font-size: 0.65rem;
		color: #b8a678;
		letter-spacing: 0.05em;
	}

	.matrix-percent {
		font-size: 0.7rem;
		font-weight: 600;
	}

	.matrix-bars {
		display: flex;
		gap: 2px;
	}

	.matrix-bar {
		flex: 1;
		height: 4px;
		transition: background 0.3s ease;
	}

	.capacity-chart {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.capacity-item {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.capacity-label {
		font-size: 0.75rem;
		color: #e0e0e0;
		font-weight: 500;
	}

	.capacity-visual {
		position: relative;
		height: 8px;
	}

	.capacity-track {
		position: absolute;
		width: 100%;
		height: 100%;
		background: rgba(10, 79, 60, 0.1);
		border-radius: 4px;
	}

	.capacity-fill {
		position: relative;
		height: 100%;
		border-radius: 4px;
		display: flex;
		align-items: center;
		transition: width 0.3s ease;
	}

	.capacity-marker {
		position: absolute;
		right: 0;
		width: 2px;
		height: 12px;
		background: rgba(255, 255, 255, 0.8);
		animation: markerPulse 1s ease-in-out infinite;
	}

	@keyframes markerPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}

	.capacity-value {
		position: absolute;
		right: -30px;
		font-size: 0.65rem;
		color: #b8a678;
		font-weight: 600;
	}

	.capacity-status {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.status-text {
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.status-icon {
		font-size: 0.8rem;
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

	.drill-info h4 {
		margin: 0;
		color: #0a4f3c;
		font-size: 1.1rem;
		letter-spacing: 0.1em;
	}

	.drill-metrics {
		display: flex;
		gap: 1rem;
		margin-top: 0.5rem;
	}

	.metric-item {
		font-size: 0.7rem;
		color: #b8a678;
		padding: 0.25rem 0.5rem;
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