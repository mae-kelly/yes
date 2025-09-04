<!-- DataCenter.svelte - Premium Facility Intelligence Dashboard -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCenter = null;
	let centerDetails = [];
	let searchTerm = '';
	let powerLevels = [];

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/data_center_metrics');
			let result = await response.json();
			data = result;
			loading = false;
			
			// Initialize power levels
			for (let i = 0; i < 20; i++) {
				powerLevels.push(Math.random());
			}
		} catch (err) {
			console.error('Data center error:', err);
			loading = false;
		}
		
		// Power animation
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

	function getUtilization(count) {
		return Math.min(95, (count / maxCount) * 100).toFixed(1);
	}

	function getFacilityStatus(utilization) {
		if (utilization >= 80) return { status: 'CRITICAL', color: '#FF1744', icon: '⚠️' };
		if (utilization >= 60) return { status: 'HIGH', color: '#FFA726', icon: '⚡' };
		if (utilization >= 40) return { status: 'OPTIMAL', color: '#00E5FF', icon: '✓' };
		return { status: 'LOW', color: '#FFD600', icon: '◉' };
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
	<!-- 3D Visualization Panel -->
	<div class="visualization-panel">
		<div class="viz-header">
			<h2 class="panel-title">
				<span class="title-icon">🏢</span>
				GLOBAL DATA CENTER NETWORK
			</h2>
			<div class="power-indicator">
				<span class="power-label">SYSTEM POWER</span>
				<div class="power-bars">
					{#each powerLevels.slice(0, 10) as level}
						<div class="power-bar" style="height: {level * 20}px; background: {level > 0.7 ? '#FF1744' : level > 0.4 ? '#FFA726' : '#00E5FF'}"></div>
					{/each}
				</div>
			</div>
		</div>
		
		<div class="facility-map">
			<div class="map-container">
				{#each filteredCenters.slice(0, 8) as [center, count], i}
					{@const utilization = getUtilization(count)}
					{@const status = getFacilityStatus(utilization)}
					{@const angle = (i * 45) * Math.PI / 180}
					{@const radius = 120}
					{@const x = 200 + Math.cos(angle) * radius}
					{@const y = 150 + Math.sin(angle) * radius}
					
					<div class="facility-node" 
						style="left: {x}px; top: {y}px"
						on:click={() => drillDownCenter(center, count)}>
						<div class="node-core" style="background: {status.color}; box-shadow: 0 0 30px {status.color}">
							<span class="node-icon">{status.icon}</span>
						</div>
						<div class="node-label">{center.substring(0, 10).toUpperCase()}</div>
						<div class="node-value">{utilization}%</div>
						<div class="node-pulse" style="border-color: {status.color}"></div>
					</div>
					
					<!-- Connection lines to center -->
					<svg class="connection-line" style="left: 0; top: 0; width: 400px; height: 300px; position: absolute; pointer-events: none;">
						<line x1="200" y1="150" x2="{x}" y2="{y}" 
							  stroke={status.color} 
							  stroke-width="1" 
							  opacity="0.3"
							  stroke-dasharray="2,3"/>
					</svg>
				{/each}
				
				<!-- Central hub -->
				<div class="central-hub">
					<div class="hub-core">
						<span class="hub-text">HUB</span>
					</div>
					<div class="hub-ring"></div>
					<div class="hub-ring ring-2"></div>
				</div>
			</div>
		</div>
	</div>

	<!-- Data Management Panel -->
	<div class="management-panel">
		<div class="panel-header">
			<div class="search-bar">
				<input 
					type="text" 
					bind:value={searchTerm}
					placeholder="Search facilities..."
					class="search-input"
				/>
			</div>
			<div class="panel-stats">
				<div class="stat">
					<span class="stat-value">{filteredCenters.length}</span>
					<span class="stat-label">FACILITIES</span>
				</div>
				<div class="stat">
					<span class="stat-value">
						{Object.values(data.facility_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}
					</span>
					<span class="stat-label">TOTAL ASSETS</span>
				</div>
			</div>
		</div>
		
		{#if loading && !selectedCenter}
			<div class="loading-state">
				<div class="server-loader">
					<div class="server-rack"></div>
					<div class="server-rack"></div>
					<div class="server-rack"></div>
				</div>
				<p>Connecting to facilities...</p>
			</div>
		{:else if selectedCenter}
			<div class="detail-view">
				<div class="detail-header">
					<h3>{selectedCenter.center.toUpperCase()}</h3>
					<button class="close-btn" on:click={closeDetails}>×</button>
				</div>
				<div class="detail-metrics">
					<div class="metric-item">
						<span class="metric-label">Assets</span>
						<span class="metric-value">{selectedCenter.count.toLocaleString()}</span>
					</div>
					<div class="metric-item">
						<span class="metric-label">Utilization</span>
						<span class="metric-value">{getUtilization(selectedCenter.count)}%</span>
					</div>
				</div>
				<div class="detail-content">
					<table class="detail-table">
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
									<td>{host.region || 'Unknown'}</td>
									<td>{host.country || 'Unknown'}</td>
									<td>{host.infrastructure_type || 'Unknown'}</td>
									<td>
										<span class="status-indicator {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'online' : 'offline'}">
											{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'ONLINE' : 'OFFLINE'}
										</span>
									</td>
									<td>
										<span class="status-indicator {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'secured' : 'exposed'}">
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
			<div class="facilities-grid">
				{#each filteredCenters as [center, count]}
					{@const utilization = getUtilization(count)}
					{@const status = getFacilityStatus(utilization)}
					<div class="facility-card" 
						on:click={() => drillDownCenter(center, count)}
						style="--status-color: {status.color}">
						<div class="card-header">
							<div class="facility-name">
								<span class="status-icon" style="color: {status.color}">{status.icon}</span>
								{center.substring(0, 20).toUpperCase()}
							</div>
							<span class="facility-status" style="color: {status.color}">{status.status}</span>
						</div>
						
						<div class="card-body">
							<div class="utilization-gauge">
								<svg viewBox="0 0 100 100" class="gauge-svg">
									<circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="5"/>
									<circle cx="50" cy="50" r="45" 
											fill="none" 
											stroke={status.color} 
											stroke-width="5"
											stroke-dasharray="{utilization * 2.83} 283"
											transform="rotate(-90 50 50)"
											stroke-linecap="round"/>
								</svg>
								<div class="gauge-value">
									<span class="gauge-number">{utilization}</span>
									<span class="gauge-unit">%</span>
								</div>
							</div>
							
							<div class="facility-stats">
								<div class="stat-item">
									<span class="stat-label">ASSETS</span>
									<span class="stat-value">{count.toLocaleString()}</span>
								</div>
								<div class="stat-item">
									<span class="stat-label">LOAD</span>
									<span class="stat-value" style="color: {status.color}">{status.status}</span>
								</div>
							</div>
						</div>
						
						<div class="card-footer">
							<div class="activity-monitor">
								{#each Array(15) as _, i}
									<div class="activity-bar" 
										 style="height: {Math.random() * 100}%; 
												background: {status.color}; 
												opacity: {0.3 + Math.random() * 0.7}">
									</div>
								{/each}
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>

<style>
	.dashboard-container {
		height: calc(100vh - 80px);
		width: 100%;
		display: grid;
		grid-template-columns: 450px 1fr;
		gap: 1.5rem;
		background: #000000;
		overflow: hidden;
	}

	/* Visualization Panel */
	.visualization-panel {
		background: linear-gradient(135deg, rgba(0, 229, 255, 0.03), transparent);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(0, 229, 255, 0.1);
		border-radius: 20px;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
	}

	.viz-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.panel-title {
		margin: 0;
		font-size: 1.1rem;
		font-weight: 600;
		color: #00E5FF;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.title-icon {
		font-size: 1.5rem;
		filter: saturate(1.5);
	}

	.power-indicator {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.power-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.power-bars {
		display: flex;
		gap: 2px;
		align-items: flex-end;
		height: 25px;
	}

	.power-bar {
		width: 3px;
		transition: all 0.5s ease;
		border-radius: 1px;
	}

	.facility-map {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}

	.map-container {
		position: relative;
		width: 400px;
		height: 300px;
	}

	.facility-node {
		position: absolute;
		cursor: pointer;
		transition: all 0.3s ease;
		z-index: 10;
	}

	.facility-node:hover {
		transform: scale(1.2);
		z-index: 20;
	}

	.node-core {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.2rem;
		position: relative;
		animation: float 3s ease-in-out infinite;
	}

	@keyframes float {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-5px); }
	}

	.node-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.8);
		text-align: center;
		margin-top: 0.25rem;
		font-weight: 500;
	}

	.node-value {
		font-size: 0.7rem;
		color: #00E5FF;
		text-align: center;
		font-weight: 600;
	}

	.node-pulse {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 50px;
		height: 50px;
		border: 2px solid;
		border-radius: 50%;
		animation: pulse 2s ease-in-out infinite;
		pointer-events: none;
	}

	@keyframes pulse {
		0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
		50% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
	}

	.central-hub {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
	}

	.hub-core {
		width: 60px;
		height: 60px;
		background: linear-gradient(135deg, #00E5FF, #7C4DFF);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
		z-index: 5;
		box-shadow: 0 0 40px rgba(0, 229, 255, 0.5);
	}

	.hub-text {
		font-weight: 700;
		font-size: 0.8rem;
		color: #ffffff;
		letter-spacing: 0.05em;
	}

	.hub-ring {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 80px;
		height: 80px;
		border: 1px solid rgba(0, 229, 255, 0.3);
		border-radius: 50%;
		animation: rotate 10s linear infinite;
	}

	.ring-2 {
		width: 100px;
		height: 100px;
		animation-direction: reverse;
		animation-duration: 15s;
	}

	@keyframes rotate {
		from { transform: translate(-50%, -50%) rotate(0deg); }
		to { transform: translate(-50%, -50%) rotate(360deg); }
	}

	/* Management Panel */
	.management-panel {
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(20px);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 20px;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.panel-header {
		margin-bottom: 1.5rem;
	}

	.search-bar {
		margin-bottom: 1rem;
	}

	.search-input {
		width: 100%;
		padding: 0.75rem 1rem;
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		color: #ffffff;
		font-size: 0.9rem;
		transition: all 0.3s ease;
	}

	.search-input:focus {
		outline: none;
		border-color: #00E5FF;
		background: rgba(0, 229, 255, 0.05);
	}

	.panel-stats {
		display: flex;
		gap: 2rem;
	}

	.stat {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.stat-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #00E5FF;
		text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
	}

	.stat-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.1em;
		margin-top: 0.25rem;
	}

	/* Facilities Grid */
	.facilities-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: 1rem;
		overflow-y: auto;
		padding-right: 0.5rem;
	}

	.facility-card {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.7));
		border: 1px solid var(--status-color, rgba(255, 255, 255, 0.1));
		border-radius: 16px;
		padding: 1.25rem;
		cursor: pointer;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.facility-card:hover {
		transform: translateY(-4px);
		box-shadow: 0 12px 32px rgba(0, 0, 0, 0.8);
		border-width: 2px;
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.facility-name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.85rem;
		font-weight: 600;
		color: #ffffff;
	}

	.status-icon {
		font-size: 1rem;
	}

	.facility-status {
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.card-body {
		display: flex;
		gap: 1.5rem;
		align-items: center;
	}

	.utilization-gauge {
		position: relative;
		width: 80px;
		height: 80px;
	}

	.gauge-svg {
		width: 100%;
		height: 100%;
		transform: rotate(-90deg);
	}

	.gauge-value {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		display: flex;
		align-items: baseline;
		gap: 2px;
	}

	.gauge-number {
		font-size: 1.2rem;
		font-weight: 700;
		color: #ffffff;
	}

	.gauge-unit {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}

	.facility-stats {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr;
		gap: 0.5rem;
	}

	.stat-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.stat-item .stat-label {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
		letter-spacing: 0.05em;
	}

	.stat-item .stat-value {
		font-size: 0.85rem;
		font-weight: 600;
		color: #ffffff;
	}

	.card-footer {
		padding-top: 0.75rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}

	.activity-monitor {
		display: flex;
		gap: 1px;
		height: 20px;
		align-items: flex-end;
	}

	.activity-bar {
		flex: 1;
		border-radius: 1px;
		transition: height 0.3s ease;
	}

	/* Loading State */
	.loading-state {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1.5rem;
	}

	.server-loader {
		display: flex;
		gap: 0.5rem;
	}

	.server-rack {
		width: 15px;
		height: 60px;
		background: linear-gradient(180deg, #00E5FF, #7C4DFF);
		border-radius: 2px;
		animation: serverPulse 1s ease-in-out infinite;
	}

	.server-rack:nth-child(2) {
		animation-delay: 0.2s;
	}

	.server-rack:nth-child(3) {
		animation-delay: 0.4s;
	}

	@keyframes serverPulse {
		0%, 100% { transform: scaleY(1); opacity: 0.5; }
		50% { transform: scaleY(1.2); opacity: 1; }
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
		align-items: center;
		padding: 1rem;
		background: rgba(0, 229, 255, 0.05);
		border-radius: 12px;
		margin-bottom: 1rem;
	}

	.detail-header h3 {
		margin: 0;
		font-size: 1rem;
		color: #00E5FF;
		font-weight: 600;
	}

	.close-btn {
		background: rgba(255, 23, 68, 0.1);
		border: none;
		color: #FF1744;
		width: 32px;
		height: 32px;
		border-radius: 8px;
		font-size: 1.5rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s ease;
	}

	.close-btn:hover {
		background: rgba(255, 23, 68, 0.2);
		transform: scale(1.1);
	}

	.detail-metrics {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.metric-item {
		background: rgba(0, 0, 0, 0.4);
		padding: 0.75rem;
		border-radius: 8px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.metric-label {
		font-size: 0.75rem;
		color: rgba(255, 255, 255, 0.5);
	}

	.metric-value {
		font-size: 1rem;
		font-weight: 600;
		color: #00E5FF;
	}

	.detail-content {
		flex: 1;
		overflow: auto;
	}

	.detail-table {
		width: 100%;
		border-collapse: collapse;
	}

	.detail-table th {
		background: rgba(0, 0, 0, 0.4);
		color: rgba(255, 255, 255, 0.6);
		padding: 0.75rem;
		text-align: left;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		position: sticky;
		top: 0;
	}

	.detail-table td {
		padding: 0.75rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.host-cell {
		font-family: 'SF Mono', monospace;
		color: #00E5FF;
		font-weight: 500;
	}

	.status-indicator {
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.05em;
	}

	.status-indicator.online {
		background: rgba(0, 229, 255, 0.2);
		color: #00E5FF;
		border: 1px solid #00E5FF;
	}

	.status-indicator.offline {
		background: rgba(255, 23, 68, 0.2);
		color: #FF1744;
		border: 1px solid #FF1744;
	}

	.status-indicator.secured {
		background: rgba(0, 229, 255, 0.2);
		color: #00E5FF;
		border: 1px solid #00E5FF;
	}

	.status-indicator.exposed {
		background: rgba(255, 214, 0, 0.2);
		color: #FFD600;
		border: 1px solid #FFD600;
	}

	/* Responsive */
	@media (max-width: 1200px) {
		.dashboard-container {
			grid-template-columns: 1fr;
			grid-template-rows: 350px 1fr;
		}
		
		.facilities-grid {
			grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		}
	}

	@media (max-width: 768px) {
		.dashboard-container {
			grid-template-rows: 250px 1fr;
		}
		
		.facilities-grid {
			grid-template-columns: 1fr;
		}
	}

	/* Scrollbar */
	::-webkit-scrollbar {
		width: 6px;
	}

	::-webkit-scrollbar-track {
		background: rgba(255, 255, 255, 0.02);
	}

	::-webkit-scrollbar-thumb {
		background: rgba(0, 229, 255, 0.2);
		border-radius: 3px;
	}

	::-webkit-scrollbar-thumb:hover {
		background: rgba(0, 229, 255, 0.3);
	}
</style>