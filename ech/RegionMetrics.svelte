<!-- Center: Main Data Table -->
		<div class="center-section">
			<div class="table-container">
				<div class="table-header">
					<h2 class="table-title">REGIONAL COMMAND MATRIX</h2>
					<div class="table-controls">
						<input type="text" 
							   bind:value={searchTerm}
							   placeholder="SEARCH REGIONS..."
							   class="search-input"/>
						<select class="items-select" bind:value={itemsPerPage}>
							<option value={10}>10 per page</option>
							<option value={15}>15 per page</option>
							<option value={20}>20 per page</option>
							<option value={50}>50 per page</option>
						</select>
						<div class="pagination">
							<button on:click={() => currentPage = 1} disabled={currentPage === 1}>⏮</button>
							<button on:click={() => currentPage = Math.max(1, currentPage - 1)} disabled={currentPage === 1}>◀</button>
							<span class="page-info">Page {currentPage} of {totalPages}</span>
							<button on:click={() => currentPage = Math.min(totalPages, currentPage + 1)} disabled={currentPage === totalPages}>▶</button>
							<button on:click={() => currentPage = totalPages} disabled={currentPage === totalPages}>⏭</button>
						</div>
					</div>
				</div>
				
				{#if selectedRegion}
					<div class="detail-view">
						<div class="detail-header">
							<div>
								<h3>{selectedRegion.region.toUpperCase()}</h3>
								<div class="detail-stats">
									<span>{formatNumber(selectedRegion.count)} hosts</span>
									<span>•</span>
									<span>{((selectedRegion.count / totalHosts) * 100).toFixed(2)}% of global</span>
								</div>
							</div>
							<button class="close-btn" on:click={closeDetails}>✕ CLOSE</button>
						</div>
						<div class="detail-content">
							<table class="detail-table">
								<thead>
									<tr>
										<th>HOSTNAME</th>
										<th>COUNTRY</th>
										<th>DATA CENTER</th>
										<th>TYPE</th>
										<th>CMDB</th>
										<th>TANIUM</th>
										<th>STATUS</th>
									</tr>
								</thead>
								<tbody>
									{#each regionDetails as host}
										<tr class="detail-row">
											<td class="hostname">{host.host}</td>
											<td>{host.country}</td>
											<td>{host.data_center}</td>
											<td>
												<span class="type-badge {host.infrastructure_type.toLowerCase()}">
													{host.infrastructure_type}
												</span>
											</td>
											<td>
												<span class="status-dot {host.present_in_cmdb === 'Yes' ? 'active' : 'inactive'}">●</span>
											</td>
											<td>
												<span class="status-dot {host.tanium_coverage === 'Tanium' ? 'active' : 'inactive'}">●</span>
											</td>
											<td>
												<span class="status-badge {Math.random() > 0.2 ? 'online' : 'offline'}">
													{Math.random() > 0.2 ? 'ONLINE' : 'OFFLINE'}
												</span>
											</td>
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
									# {sortColumn === 'rank' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th class="sortable" on:click={() => sortTable('name')}>
									REGION {sortColumn === 'name' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th class="sortable" on:click={() => sortTable('count')}>
									HOSTS {sortColumn === 'count' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th>SCALE</th>
								<th>% OF GLOBAL</th>
								<th>BANDWIDTH</th>
								<th>LATENCY</th>
								<th>SECURITY</th>
								<th>STATUS</th>
								<th>ACTIONS</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedRegions as [region, count], i}
								{@const level = getRegionLevel(count)}
								{@const percentage = (count / totalHosts) * 100}
								{@const traffic = trafficFlows.find(t => t.region === region)}
								{@const threat = threatMatrix.find(t => t.region === region)}
								<tr class="data-row" style="--glow-color: {level.glow}">
									<td class="rank">{(currentPage - 1) * itemsPerPage + i + 1}</td>
									<td class="region-name">
										<span class="region-indicator" style="background: {level.color}">●</span>
										{region}
									</td>
									<td class="host-count" style="color: {level.color}">
										{formatNumber(count)}
									</td>
									<td>
										<span class="scale-badge" style="background: {level.glow}; color: {level.color}">
											{level.level}
										</span>
									</td>
									<td class="percentage">
										<div class="percentage-bar">
											<div class="percentage-fill" 
												 style="width: {percentage}%; 
														background: linear-gradient(90deg, transparent, {level.color})">
											</div>
											<span class="percentage-text">{percentage.toFixed(1)}%</span>
										</div>
									</td>
									<td class="bandwidth">
										<span class="bandwidth-value">
											{traffic ? formatNumber(traffic.incoming + traffic.outgoing) : '0'} Mbps
										</span>
									</td>
									<td class="latency">
										<span class="latency-value {networkLatency < 20 ? 'good' : networkLatency < 50 ? 'medium' : 'poor'}">
											{(10 + Math.random() * 50).toFixed(0)}ms
										</span>
									</td>
									<td class="security">
										<div class="security-meter">
											<div class="security-level" 
												 style="width: {threat ? (threat.blocked / threat.threats) * 100 : 100}%;
														background: {threat && threat.severity > 0.7 ? '#FF0000' : threat && threat.severity > 0.4 ? '#FFFF00' : '#00FF00'}">
											</div>
										</div>
									</td>
									<td>
										<span class="status-indicator {percentage > 20 ? 'active' : 'standby'}">
											{percentage > 20 ? '◈ ACTIVE' : '○ STANDBY'}
										</span>
									</td>
									<td>
										<button class="action-btn analyze" on:click={() => drillDownRegion(region, count)}>
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
		
		<!-- Right: Analytics & Monitoring -->
		<div class="right-section">
			<!-- Bandwidth Usage Chart -->
			<div class="chart-container">
				<h3 class="section-title">BANDWIDTH UTILIZATION</h3>
				<svg viewBox="0 0 300 150" class="bandwidth-chart">
					<defs>
						<linearGradient id="bandwidthGradient1" x1="0%" y1="0%" x2="0%" y2="100%">
							<stop offset="0%" style="stop-color:#FF00FF;stop-opacity:0.8" />
							<stop offset="100%" style="stop-color:#FF00FF;stop-opacity:0.1" />
						</linearGradient>
						<linearGradient id="bandwidthGradient2" x1="0%" y1="0%" x2="0%" y2="100%">
							<stop offset="0%" style="stop-color:#00FFFF;stop-opacity:0.8" />
							<stop offset="100%" style="stop-color:#00FFFF;stop-opacity:0.1" />
						</linearGradient>
						<linearGradient id="bandwidthGradient3" x1="0%" y1="0%" x2="0%" y2="100%">
							<stop offset="0%" style="stop-color:#00FF00;stop-opacity:0.8" />
							<stop offset="100%" style="stop-color:#00FF00;stop-opacity:0.1" />
						</linearGradient>
					</defs>
					
					<!-- Grid -->
					<g class="grid" opacity="0.2">
						{#each Array(5) as _, i}
							<line x1="0" y1="{i * 30}" x2="300" y2="{i * 30}" stroke="#333" stroke-width="0.5"/>
						{/each}
					</g>
					
					<!-- North America -->
					<polygon points="{bandwidthUsage.map((d, i) => `${i * 6.25},${150 - d.northAmerica * 1.5}`).join(' ')} 300,150 0,150"
							 fill="url(#bandwidthGradient1)" opacity="0.7"/>
					<polyline points="{bandwidthUsage.map((d, i) => `${i * 6.25},${150 - d.northAmerica * 1.5}`).join(' ')}"
							  fill="none" stroke="#FF00FF" stroke-width="2"/>
					
					<!-- Europe -->
					<polygon points="{bandwidthUsage.map((d, i) => `${i * 6.25},${150 - d.europe * 1.5}`).join(' ')} 300,150 0,150"
							 fill="url(#bandwidthGradient2)" opacity="0.5"/>
					<polyline points="{bandwidthUsage.map((d, i) => `${i * 6.25},${150 - d.europe * 1.5}`).join(' ')}"
							  fill="none" stroke="#00FFFF" stroke-width="2"/>
					
					<!-- Asia Pacific -->
					<polygon points="{bandwidthUsage.map((d, i) => `${i * 6.25},${150 - d.asiaPacific * 1.5}`).join(' ')} 300,150 0,150"
							 fill="url(#bandwidthGradient3)" opacity="0.3"/>
					<polyline points="{bandwidthUsage.map((d, i) => `${i * 6.25},${150 - d.asiaPacific * 1.5}`).join(' ')}"
							  fill="none" stroke="#00FF00" stroke-width="2"/>
				</svg>
				<div class="chart-legend">
					<span class="legend-item"><span style="background:#FF00FF">●</span> North America</span>
					<span class="legend-item"><span style="background:#00FFFF">●</span> Europe</span>
					<span class="legend-item"><span style="background:#00FF00">●</span> Asia Pacific</span>
				</div>
			</div>
			
			<!-- Inter-Region Connections -->
			<div class="connections-container">
				<h3 class="section-title">INTER-REGION TUNNELS</h3>
				<svg viewBox="0 0 300 300" class="connections-graph">
					<!-- Draw connections -->
					{#each interconnections as source, i}
						{#each interconnections.slice(i + 1) as target, j}
							{#if Math.random() > 0.6}
								<line x1="{source.x * 0.6}" y1="{source.y * 0.6}" 
									  x2="{target.x * 0.6}" y2="{target.y * 0.6}"
									  stroke="{source.status === 'online' && target.status === 'online' ? '#00FF00' : '#FF0000'}"
									  stroke-width="1" opacity="0.3"
									  stroke-dasharray="{source.status === 'offline' || target.status === 'offline' ? '5,5' : 'none'}">
									{#if source.status === 'online' && target.status === 'online'}
										<animate attributeName="stroke-opacity"
												 values="0.3;0.8;0.3" dur="3s" repeatCount="indefinite"/>
									{/if}
								</line>
							{/if}
						{/each}
					{/each}
					
					<!-- Draw nodes -->
					{#each interconnections as node}
						<g transform="translate({node.x * 0.6}, {node.y * 0.6})">
							<circle r="8" 
									fill="{node.status === 'online' ? '#00FF00' : '#FF0000'}"
									opacity="0.8"/>
							<text text-anchor="middle" dy="20" font-size="8" fill="#FFFFFF">
								{node.id.substring(0, 3)}
							</text>
						</g>
					{/each}
				</svg>
			</div>
			
			<!-- Quantum Tunnels Status -->
			<div class="tunnels-container">
				<h3 class="section-title">QUANTUM TUNNELS</h3>
				<div class="tunnels-list">
					{#each quantumTunnels.slice(0, 5) as tunnel}
						<div class="tunnel-item">
							<div class="tunnel-header">
								<span class="tunnel-id">{tunnel.id}</span>
								<span class="tunnel-route">{tunnel.sourceRegion.substring(0, 3)} → {tunnel.targetRegion.substring(0, 3)}</span>
							</div>
							<div class="tunnel-visualization">
								<svg viewBox="0 0 200 20" class="tunnel-svg">
									{#each tunnel.particles as particle}
										<circle cx="{particle.position * 200}" cy="10" r="2"
												fill="#00FFFF" opacity="{tunnel.stability}"/>
									{/each}
									<line x1="0" y1="10" x2="200" y2="10" 
										  stroke="#00FFFF" stroke-width="1" opacity="0.2"/>
								</svg>
							</div>
							<div class="tunnel-stats">
								<span>Stability: {(tunnel.stability * 100).toFixed(0)}%</span>
								<span>Entanglement: {(tunnel.entanglement * 100).toFixed(0)}%</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
	
	<!-- Bottom Status Panel -->
	<div class="bottom-panel">
		<div class="activity-monitor">
			<span class="monitor-label">GLOBAL ACTIVITY</span>
			<div class="activity-bar">
				<div class="activity-level" style="width: {globalActivity}%"></div>
			</div>
			<span class="monitor-value">{globalActivity.toFixed(0)}%</span>
		</div>
		<div class="uptime-monitor">
			<span class="monitor-label">SYSTEM UPTIME</span>
			<span class="monitor-value uptime">{uptime.toFixed(2)}%</span>
		</div>
		<div class="transfer-monitor">
			<span class="monitor-label">DATA TRANSFER</span>
			<span class="monitor-value">{formatNumber(dataTransferRate * 1000000)} B/s</span>
		</div>
	</div>
</div>

<style>
	.global-command-interface {
		width: 100%;
		height: calc(100vh - 80px);
		background: linear-gradient(135deg, #000011, #000033);
		display: flex;
		flex-direction: column;
		gap: 1rem;
		padding: 1rem;
		overflow: hidden;
	}
	
	/* Status Bar */
	.status-bar {
		display: flex;
		gap: 1rem;
		height: 90px;
		flex-shrink: 0;
	}
	
	.status-card {
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
	
	.status-card.pulse-blue { animation: pulseBlue 3s infinite; }
	.status-card.pulse-green { animation: pulseGreen 3s infinite; }
	.status-card.pulse-yellow { animation: pulseYellow 3s infinite; }
	.status-card.pulse-purple { animation: pulsePurple 3s infinite; }
	.status-card.pulse-red { animation: pulseRed 3s infinite; }
	
	@keyframes pulseBlue {
		0%, 100% { box-shadow: 0 0 10px rgba(0, 255, 255, 0.3); }
		50% { box-shadow: 0 0 30px rgba(0, 255, 255, 0.6); }
	}
	
	@keyframes pulseGreen {
		0%, 100% { box-shadow: 0 0 10px rgba(0, 255, 0, 0.3); }
		50% { box-shadow: 0 0 30px rgba(0, 255, 0, 0.6); }
	}
	
	@keyframes pulseYellow {
		0%, 100% { box-shadow: 0 0 10px rgba(255, 255, 0, 0.3); }
		50% { box-shadow: 0 0 30px rgba(255, 255, 0, 0.6); }
	}
	
	@keyframes pulsePurple {
		0%, 100% { box-shadow: 0 0 10px rgba(255, 0, 255, 0.3); }
		50% { box-shadow: 0 0 30px rgba(255, 0, 255, 0.6); }
	}
	
	@keyframes pulseRed {
		0%, 100% { box-shadow: 0 0 10px rgba(255, 0, 0, 0.3); }
		50% { box-shadow: 0 0 30px rgba(255, 0, 0, 0.6); }
	}
	
	.status-icon {
		font-size: 2.5rem;
	}
	
	.status-info {
		flex: 1;
	}
	
	.status-value {
		font-size: 1.8rem;
		font-weight: bold;
		color: #FFFFFF;
		font-family: 'Courier New', monospace;
		text-shadow: 0 0 10px currentColor;
	}
	
	.status-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
		text-transform: uppercase;
	}
	
	.status-chart {
		position: absolute;
		right: 10px;
		width: 70px;
		height: 35px;
		opacity: 0.5;
	}
	
	/* Main Grid */
	.main-grid {
		flex: 1;
		display: grid;
		grid-template-columns: 350px 1fr 350px;
		gap: 1rem;
		min-height: 0;
	}
	
	/* Sections */
	.left-section, .right-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
	}
	
	.center-section {
		display: flex;
		flex-direction: column;
		min-height: 0;
	}
	
	/* Section Titles */
	.section-title {
		margin: 0 0 0.5rem 0;
		font-size: 0.9rem;
		color: #00FFFF;
		letter-spacing: 0.1em;
		font-weight: 400;
		text-transform: uppercase;
	}
	
	/* Globe Container */
	.globe-container {
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 10px;
		padding: 1rem;
	}
	
	.globe-view {
		width: 100%;
		height: auto;
	}
	
	.region-marker {
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.region-marker:hover {
		transform: scale(1.2);
	}
	
	.satellite {
		pointer-events: none;
	}
	
	/* Threat Container */
	.threat-container {
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid rgba(255, 0, 0, 0.3);
		border-radius: 10px;
		padding: 1rem;
	}
	
	.threat-grid {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.threat-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.threat-header {
		display: flex;
		justify-content: space-between;
		min-width: 150px;
		font-size: 0.75rem;
	}
	
	.threat-region {
		color: rgba(255, 255, 255, 0.8);
	}
	
	.threat-count {
		font-weight: bold;
		font-family: 'Courier New', monospace;
	}
	
	.threat-count.normal { color: #00FF00; }
	.threat-count.warning { color: #FFFF00; }
	.threat-count.critical { color: #FF0000; }
	
	.threat-bar {
		flex: 1;
		height: 8px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.threat-blocked {
		height: 100%;
		background: linear-gradient(90deg, #00FF00, #00FFFF);
		transition: width 0.5s;
	}
	
	.threat-trend {
		font-size: 0.8rem;
		font-weight: bold;
		width: 30px;
		text-align: center;
	}
	
	.threat-trend.increasing { color: #FF0000; }
	.threat-trend.decreasing { color: #00FF00; }
	
	/* Table Container */
	.table-container {
		flex: 1;
		background: rgba(0, 0, 0, 0.9);
		border: 2px solid rgba(0, 255, 255, 0.4);
		border-radius: 10px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: 0 0 40px rgba(0, 255, 255, 0.3);
	}
	
	.table-header {
		padding: 1rem;
		background: linear-gradient(180deg, rgba(0, 255, 255, 0.1), transparent);
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
	}
	
	.table-title {
		margin: 0 0 1rem 0;
		font-size: 1.3rem;
		color: #00FFFF;
		letter-spacing: 0.2em;
		font-weight: 300;
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
		text-transform: uppercase;
	}
	
	.table-controls {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
	}
	
	.search-input {
		padding: 0.6rem 1rem;
		background: rgba(0, 0, 0, 0.7);
		border: 1px solid rgba(0, 255, 255, 0.3);
		color: #00FFFF;
		font-family: 'Courier New', monospace;
		border-radius: 5px;
		width: 250px;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #00FFFF;
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
	}
	
	.items-select {
		padding: 0.6rem;
		background: rgba(0, 0, 0, 0.7);
		border: 1px solid rgba(0, 255, 255, 0.3);
		color: #00FFFF;
		border-radius: 5px;
		cursor: pointer;
	}
	
	.pagination {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.pagination button {
		padding: 0.6rem 0.8rem;
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid #00FFFF;
		color: #00FFFF;
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
		font-size: 0.9rem;
	}
	
	.pagination button:hover:not(:disabled) {
		background: rgba(0, 255, 255, 0.3);
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
		transform: scale(1.05);
	}
	
	.pagination button:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	
	.page-info {
		color: #00FFFF;
		font-family: 'Courier New', monospace;
		padding: 0 1rem;
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
		padding: 1rem 0.8rem;
		text-align: left;
		font-size: 0.75rem;
		color: #00FFFF;
		letter-spacing: 0.1em;
		font-weight: 600;
		border-bottom: 2px solid rgba(0, 255, 255, 0.3);
		white-space: nowrap;
		text-transform: uppercase;
	}
	
	.data-table th.sortable {
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.data-table th.sortable:hover {
		background: rgba(0, 255, 255, 0.1);
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
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
		background: rgba(0, 255, 255, 0.08);
		box-shadow: inset 0 0 30px var(--glow-color);
		transform: translateX(5px);
	}
	
	.data-table td {
		padding: 0.9rem 0.8rem;
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.9);
	}
	
	.rank {
		color: #FF00FF;
		font-weight: bold;
		font-family: 'Courier New', monospace;
	}
	
	.region-name {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 500;
	}
	
	.region-indicator {
		font-size: 0.8rem;
		width: 10px;
		height: 10px;
		border-radius: 50%;
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
	
	.host-count {
		font-family: 'Courier New', monospace;
		font-weight: bold;
		font-size: 0.95rem;
	}
	
	.scale-badge {
		padding: 0.3rem 0.6rem;
		border-radius: 5px;
		font-size: 0.65rem;
		font-weight: 700;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}
	
	.percentage-bar {
		position: relative;
		width: 100px;
		height: 20px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 10px;
		overflow: hidden;
	}
	
	.percentage-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.percentage-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 0.65rem;
		color: #FFFFFF;
		font-weight: bold;
		text-shadow: 0 0 3px #000000;
	}
	
	.bandwidth-value, .latency-value {
		font-family: 'Courier New', monospace;
		font-size: 0.75rem;
		font-weight: 600;
	}
	
	.latency-value.good { color: #00FF00; }
	.latency-value.medium { color: #FFFF00; }
	.latency-value.poor { color: #FF0000; }
	
	.security-meter {
		width: 60px;
		height: 8px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		overflow: hidden;
	}
	
	.security-level {
		height: 100%;
		transition: all 0.5s;
	}
	
	.status-indicator {
		font-size: 0.8rem;
		font-weight: 600;
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
	}
	
	.status-indicator.active { color: #00FF00; }
	.status-indicator.standby { color: #FFFF00; }
	
	.action-btn {
		padding: 0.5rem 1rem;
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.3));
		border: 1px solid #00FFFF;
		color: #00FFFF;
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
		text-transform: uppercase;
	}
	
	.action-btn:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.3), rgba(0, 255, 255, 0.5));
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.6);
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
		padding-bottom: 1rem;
		border-bottom: 2px solid rgba(0, 255, 255, 0.3);
	}
	
	.detail-header h3 {
		margin: 0;
		color: #00FFFF;
		font-size: 1.3rem;
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}
	
	.detail-stats {
		display: flex;
		gap: 1rem;
		margin-top: 0.5rem;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.close-btn {
		padding: 0.6rem 1.2rem;
		background: rgba(255, 0, 0, 0.1);
		border: 1px solid #FF0000;
		color: #FF0000;
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
		font-weight: 600;
		letter-spacing: 0.1em;
	}
	
	.close-btn:hover {
		background: rgba(255, 0, 0, 0.3);
		box-shadow: 0 0 15px rgba(255, 0, 0, 0.5);
	}
	
	.detail-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.detail-table thead {
		background: rgba(0, 255, 255, 0.05);
	}
	
	.detail-table th {
		padding: 0.8rem;
		background: rgba(0, 255, 255, 0.1);
		color: #00FFFF;
		font-size: 0.75rem;
		letter-spacing: 0.05em;
		border-bottom: 1px solid rgba(0, 255, 255, 0.3);
		text-align: left;
	}
	
	.detail-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.2s;
	}
	
	.detail-row:hover {
		background: rgba(0, 255, 255, 0.05);
	}
	
	.detail-table td {
		padding: 0.6rem 0.8rem;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
	}
	
	.hostname {
		font-family: 'Courier New', monospace;
		color: #00FFFF;
		font-size: 0.75rem;
	}
	
	.type-badge {
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		font-size: 0.65rem;
		font-weight: 600;
		text-transform: uppercase;
	}
	
	.type-badge.virtual { background: rgba(0, 255, 255, 0.2); color: #00FFFF; }
	.type-badge.physical { background: rgba(255, 0, 255, 0.2); color: #FF00FF; }
	.type-badge.container { background: rgba(0, 255, 0, 0.2); color: #00FF00; }
	.type-badge.hybrid { background: rgba(255, 255, 0, 0.2); color: #FFFF00; }
	
	.status-dot {
		font-size: 0.9rem;
		display: inline-block;
	}
	
	.status-dot.active { color: #00FF00; filter: drop-shadow(0 0 5px #00FF00); }
	.status-dot.inactive { color: #FF0000; filter: drop-shadow(0 0 5px #FF0000); }
	
	.status-badge {
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		font-size: 0.65rem;
		font-weight: 600;
	}
	
	.status-badge.online {
		background: rgba(0, 255, 0, 0.2);
		color: #00FF00;
		border: 1px solid #00FF00;
	}
	
	.status-badge.offline {
		background: rgba(255, 0, 0, 0.2);
		color: #FF0000;
		border: 1px solid #FF0000;
	}
	
	/* Charts */
	.chart-container, .connections-container, .tunnels-container {
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 10px;
		padding: 1rem;
	}
	
	.bandwidth-chart, .connections-graph {
		width: 100%;
		height: auto;
	}
	
	.chart-legend {
		display: flex;
		justify-content: center;
		gap: 1rem;
		margin-top: 0.5rem;
		font-size: 0.7rem;
	}
	
	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		color: rgba(255, 255, 255, 0.7);
	}
	
	.legend-item span {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		display: inline-block;
	}
	
	/* Tunnels */
	.tunnels-list {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}
	
	.tunnel-item {
		background: rgba(0, 255, 255, 0.05);
		border: 1px solid rgba(0, 255, 255, 0.2);
		border-radius: 5px;
		padding: 0.5rem;
	}
	
	.tunnel-header {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.3rem;
		font-size: 0.75rem;
	}
	
	.tunnel-id {
		color: #00FFFF;
		font-weight: 600;
	}
	
	.tunnel-route {
		color: rgba(255, 255, 255, 0.6);
	}
	
	.tunnel-visualization {
		height: 20px;
		margin-bottom: 0.3rem;
	}
	
	.tunnel-svg {
		width: 100%;
		height: 100%;
	}
	
	.tunnel-stats {
		display: flex;
		justify-content: space-between;
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.5);
	}
	
	/* Bottom Panel */
	.bottom-panel {
		display: flex;
		gap: 2rem;
		padding: 1rem;
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid rgba(0, 255, 255, 0.3);
		border-radius: 10px;
		align-items: center;
		justify-content: center;
	}
	
	.activity-monitor, .uptime-monitor, .transfer-monitor {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.monitor-label {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
	}
	
	.activity-bar {
		width: 150px;
		height: 10px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 5px;
		overflow: hidden;
	}
	
	.activity-level {
		height: 100%;
		background: linear-gradient(90deg, #00FF00, #FFFF00, #FF0000);
		transition: width 0.5s;
	}
	
	.monitor-value {
		font-size: 1rem;
		color: #00FFFF;
		font-family: 'Courier New', monospace;
		font-weight: bold;
	}
	
	.monitor-value.uptime {
		color: #00FF00;
	}
	
	/* Scrollbar */
	::-webkit-scrollbar {
		width: 8px;
	}
	
	::-webkit-scrollbar-track {
		background: #000033;
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb {
		background: linear-gradient(180deg, #00FFFF, #FF00FF);
		border-radius: 4px;
	}
	
	::-webkit-scrollbar-thumb:hover {
		background: linear-gradient(180deg, #00FFFF, #FF00FF);
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}
	
	/* Responsive */
	@media (max-width: 1600px) {
		.main-grid {
			grid-template-columns: 300px 1fr 300px;
		}
	}
	
	@media (max-width: 1200px) {
		.main-grid {
			grid-template-columns: 1fr;
		}
		
		.left-section, .right-section {
			display: none;
		}
		
		.status-bar {
			flex-wrap: wrap;
			height: auto;
		}
		
		.status-card {
			min-width: calc(50% - 0.5rem);
		}
	}
</style><!-- RegionMetrics.svelte - ULTIMATE GLOBAL COMMAND CENTER -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';
	let sortColumn = 'count';
	let sortDirection = 'desc';
	let currentPage = 1;
	let itemsPerPage = 15;
	
	// Advanced visualization states
	let globeRotation = 0;
	let satelliteData = [];
	let dataStreams = [];
	let heatZones = [];
	let trafficFlows = [];
	let threatMatrix = [];
	let bandwidthUsage = [];
	let latencyMap = [];
	let interconnections = [];
	let pulsarSignals = [];
	let quantumTunnels = [];
	let holoProjection = 0;
	
	// Real-time metrics
	let globalActivity = 0;
	let networkLatency = 0;
	let dataTransferRate = 0;
	let securityScore = 100;
	let uptime = 99.99;
	
	// Animation controllers
	let animationFrames = {
		globe: null,
		satellites: null,
		streams: null,
		pulsar: null
	};
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/region_metrics');
			data = await response.json();
			loading = false;
			initializeGlobalSystems();
			startGlobalAnimations();
		} catch (err) {
			console.error('Region sync failed:', err);
			data = generateMockData();
			loading = false;
			initializeGlobalSystems();
			startGlobalAnimations();
		}
	});
	
	onDestroy(() => {
		Object.values(animationFrames).forEach(frame => {
			if (frame) cancelAnimationFrame(frame);
		});
	});
	
	function generateMockData() {
		return {
			global_surveillance: {
				'North America': 631301,
				'Europe': 258301,
				'Asia Pacific': 173653,
				'Latin America': 84580,
				'Middle East': 58450,
				'Africa': 32890,
				'Oceania': 18650,
				'Antarctica': 2150
			}
		};
	}
	
	function initializeGlobalSystems() {
		if (!data.global_surveillance) return;
		
		const regions = Object.entries(data.global_surveillance);
		
		// Initialize satellites
		for (let i = 0; i < 12; i++) {
			satelliteData.push({
				id: `SAT-${i}`,
				angle: (i / 12) * Math.PI * 2,
				altitude: 200 + Math.random() * 100,
				speed: 0.01 + Math.random() * 0.02,
				active: Math.random() > 0.2,
				dataRate: Math.random() * 1000,
				signal: Math.random(),
				orbit: Math.random() > 0.5 ? 'LEO' : 'GEO'
			});
		}
		
		// Initialize data streams between regions
		regions.forEach(([region1, count1], i) => {
			regions.forEach(([region2, count2], j) => {
				if (i < j) {
					dataStreams.push({
						source: region1,
						target: region2,
						bandwidth: Math.min(count1, count2) / 1000,
						active: Math.random() > 0.3,
						latency: 10 + Math.random() * 200,
						packetLoss: Math.random() * 5,
						encrypted: Math.random() > 0.5
					});
				}
			});
		});
		
		// Heat zones for activity monitoring
		for (let i = 0; i < 50; i++) {
			heatZones.push({
				lat: (Math.random() - 0.5) * 180,
				lon: (Math.random() - 0.5) * 360,
				intensity: Math.random(),
				radius: 20 + Math.random() * 50,
				type: ['normal', 'warning', 'critical'][Math.floor(Math.random() * 3)]
			});
		}
		
		// Traffic flow patterns
		regions.forEach(([region, count]) => {
			trafficFlows.push({
				region,
				incoming: Math.random() * count * 0.3,
				outgoing: Math.random() * count * 0.3,
				internal: Math.random() * count * 0.4,
				peakHour: Math.floor(Math.random() * 24),
				utilization: Math.random() * 100
			});
		});
		
		// Threat matrix
		regions.forEach(([region]) => {
			threatMatrix.push({
				region,
				threats: Math.floor(Math.random() * 100),
				blocked: Math.floor(Math.random() * 90),
				severity: Math.random(),
				trend: Math.random() > 0.5 ? 'increasing' : 'decreasing'
			});
		});
		
		// Bandwidth usage time series
		for (let i = 0; i < 48; i++) {
			bandwidthUsage.push({
				time: i,
				northAmerica: 50 + Math.sin(i * 0.2) * 30 + Math.random() * 20,
				europe: 40 + Math.cos(i * 0.2) * 25 + Math.random() * 15,
				asiaPacific: 45 + Math.sin(i * 0.3) * 20 + Math.random() * 15,
				other: 30 + Math.sin(i * 0.4) * 15 + Math.random() * 10
			});
		}
		
		// Latency map
		regions.forEach(([source]) => {
			regions.forEach(([target]) => {
				if (source !== target) {
					latencyMap.push({
						source,
						target,
						latency: 5 + Math.random() * 200,
						jitter: Math.random() * 20,
						quality: Math.random()
					});
				}
			});
		});
		
		// Interconnections graph
		regions.forEach(([region], i) => {
			interconnections.push({
				id: region,
				x: Math.cos(i * Math.PI * 2 / regions.length) * 200 + 250,
				y: Math.sin(i * Math.PI * 2 / regions.length) * 200 + 250,
				connections: Math.floor(Math.random() * regions.length),
				bandwidth: Math.random() * 10000,
				status: Math.random() > 0.1 ? 'online' : 'offline'
			});
		});
		
		// Pulsar signals (for visual effect)
		for (let i = 0; i < 20; i++) {
			pulsarSignals.push({
				x: Math.random() * 500,
				y: Math.random() * 500,
				radius: 0,
				maxRadius: 50 + Math.random() * 100,
				speed: 0.5 + Math.random(),
				color: ['#00FFFF', '#FF00FF', '#00FF00', '#FFFF00'][Math.floor(Math.random() * 4)]
			});
		}
		
		// Quantum tunnels (advanced network paths)
		for (let i = 0; i < 10; i++) {
			quantumTunnels.push({
				id: `QT-${i}`,
				sourceRegion: regions[Math.floor(Math.random() * regions.length)][0],
				targetRegion: regions[Math.floor(Math.random() * regions.length)][0],
				particles: [],
				stability: Math.random(),
				entanglement: Math.random()
			});
			
			// Add particles to each tunnel
			for (let j = 0; j < 10; j++) {
				quantumTunnels[i].particles.push({
					position: Math.random(),
					speed: 0.01 + Math.random() * 0.03
				});
			}
		}