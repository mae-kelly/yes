<!-- ech/RegionMetrics.svelte -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedRegion = null;
	let regionDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 12;
	
	let globeRotation = 0;
	let pulseRadius = [];
	let dataFlows = [];
	let animationFrame;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/region_metrics');
			data = await response.json();
			loading = false;
			initializeVisualization();
			startAnimations();
		} catch (err) {
			console.error('Region sync failed:', err);
			loading = false;
		}
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});
	
	function initializeVisualization() {
		if (!data.global_surveillance) return;
		
		const regions = Object.entries(data.global_surveillance);
		regions.forEach((region, i) => {
			pulseRadius.push({
				id: i,
				radius: 0,
				maxRadius: 100 + Math.random() * 50,
				speed: 1 + Math.random()
			});
		});
		
		for (let i = 0; i < 20; i++) {
			dataFlows.push({
				startX: Math.random() * 600,
				startY: Math.random() * 400,
				endX: Math.random() * 600,
				endY: Math.random() * 400,
				progress: Math.random(),
				speed: 0.01 + Math.random() * 0.02
			});
		}
	}
	
	function startAnimations() {
		const animate = () => {
			globeRotation = (globeRotation + 0.5) % 360;
			
			pulseRadius.forEach(pulse => {
				pulse.radius += pulse.speed;
				if (pulse.radius > pulse.maxRadius) {
					pulse.radius = 0;
				}
			});
			
			dataFlows.forEach(flow => {
				flow.progress += flow.speed;
				if (flow.progress > 1) {
					flow.progress = 0;
					flow.startX = Math.random() * 600;
					flow.startY = Math.random() * 400;
					flow.endX = Math.random() * 600;
					flow.endY = Math.random() * 400;
				}
			});
			
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	}
	
	$: regions = data.global_surveillance ? 
		Object.entries(data.global_surveillance)
			.filter(([region]) => region.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: paginatedRegions = regions.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(regions.length / itemsPerPage);
	$: totalHosts = regions.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = regions.length > 0 ? Math.max(...regions.map(([,c]) => c)) : 1;
	
	async function drillDownRegion(region, count) {
		selectedRegion = { region, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(region)}`);
			let result = await response.json();
			regionDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Region drill-down failed:', err);
			regionDetails = [];
			loading = false;
		}
	}
	
	function closeDetails() {
		selectedRegion = null;
		regionDetails = [];
	}
	
	function getRegionLevel(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 80) return { level: 'NEXUS', color: '#ff00ff' };
		if (percentage >= 60) return { level: 'PRIME', color: '#00ffff' };
		if (percentage >= 40) return { level: 'MAJOR', color: '#ff69b4' };
		if (percentage >= 20) return { level: 'SECTOR', color: '#ff00ff' };
		return { level: 'NODE', color: '#00ffff' };
	}
	
	function formatNumber(num) {
		if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
		if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
		return num.toString();
	}
	
	function getRegionCoords(region) {
		const coords = {
			'North America': { x: 150, y: 150 },
			'Europe': { x: 350, y: 120 },
			'Asia Pacific': { x: 500, y: 180 },
			'APAC': { x: 500, y: 180 },
			'Latin America': { x: 180, y: 280 },
			'LATAM': { x: 180, y: 280 },
			'Middle East': { x: 380, y: 200 },
			'Africa': { x: 350, y: 250 },
			'EMEA': { x: 350, y: 160 },
			'Oceania': { x: 520, y: 300 }
		};
		return coords[region] || { x: 300, y: 200 };
	}
</script>

<div class="region-interface">
	<div class="status-bar">
		<div class="status-card">
			<div class="status-value">{regions.length}</div>
			<div class="status-label">ACTIVE REGIONS</div>
		</div>
		<div class="status-card">
			<div class="status-value">{formatNumber(totalHosts)}</div>
			<div class="status-label">GLOBAL ASSETS</div>
		</div>
		<div class="status-card">
			<div class="status-value">{((totalHosts / regions.length) || 0).toFixed(0)}</div>
			<div class="status-label">AVG PER REGION</div>
		</div>
	</div>
	
	<div class="main-grid">
		<div class="globe-section">
			<div class="globe-container" style="transform: rotateY({globeRotation}deg)">
				<svg viewBox="0 0 600 400" class="world-map">
					<defs>
						<radialGradient id="globeGradient">
							<stop offset="0%" style="stop-color:#00ffff;stop-opacity:0.3" />
							<stop offset="100%" style="stop-color:#ff00ff;stop-opacity:0.1" />
						</radialGradient>
						<filter id="regionGlow">
							<feGaussianBlur stdDeviation="4" result="coloredBlur"/>
							<feMerge>
								<feMergeNode in="coloredBlur"/>
								<feMergeNode in="SourceGraphic"/>
							</feMerge>
						</filter>
					</defs>
					
					<ellipse cx="300" cy="200" rx="280" ry="180" 
							 fill="none" stroke="#00ffff" stroke-width="0.5" opacity="0.3"/>
					<ellipse cx="300" cy="200" rx="200" ry="130" 
							 fill="none" stroke="#ff00ff" stroke-width="0.5" opacity="0.3"/>
					
					{#each dataFlows as flow}
						<line x1="{flow.startX}" y1="{flow.startY}"
							  x2="{flow.startX + (flow.endX - flow.startX) * flow.progress}"
							  y2="{flow.startY + (flow.endY - flow.startY) * flow.progress}"
							  stroke="#00ffff" stroke-width="2" opacity="0.6"
							  filter="url(#regionGlow)"/>
						<circle cx="{flow.startX + (flow.endX - flow.startX) * flow.progress}"
								cy="{flow.startY + (flow.endY - flow.startY) * flow.progress}"
								r="3" fill="#ff00ff" opacity="0.8"
								filter="url(#regionGlow)"/>
					{/each}
					
					{#each regions as [region, count], i}
						{@const coords = getRegionCoords(region)}
						{@const level = getRegionLevel(count)}
						<g transform="translate({coords.x}, {coords.y})"
						   on:click={() => drillDownRegion(region, count)}
						   class="region-node">
							{#if pulseRadius[i]}
								<circle r="{pulseRadius[i].radius}"
										fill="none" stroke="{level.color}"
										opacity="{0.6 - pulseRadius[i].radius / pulseRadius[i].maxRadius * 0.6}"
										stroke-width="2"/>
							{/if}
							<circle r="20" fill="#000000" stroke="{level.color}"
									stroke-width="2" opacity="0.9"
									filter="url(#regionGlow)"/>
							<text text-anchor="middle" dy="-30" font-size="10"
								  fill="#ffffff" font-weight="600"
								  style="text-shadow: 0 0 10px {level.color}">
								{region.toUpperCase()}
							</text>
							<text text-anchor="middle" dy="5" font-size="12"
								  fill="{level.color}" font-weight="700"
								  style="text-shadow: 0 0 15px {level.color}">
								{formatNumber(count)}
							</text>
						</g>
					{/each}
				</svg>
			</div>
		</div>
		
		<div class="table-section">
			<div class="table-container">
				<div class="table-header">
					<h2>REGIONAL COMMAND MATRIX</h2>
					<div class="controls">
						<input type="text" 
							   bind:value={searchTerm}
							   placeholder="SEARCH REGIONS..."
							   class="search-input"/>
						<div class="pagination">
							<button on:click={() => currentPage = 1} disabled={currentPage === 1}>⏮</button>
							<button on:click={() => currentPage = Math.max(1, currentPage - 1)} disabled={currentPage === 1}>◀</button>
							<span class="page-info">{currentPage} / {totalPages}</span>
							<button on:click={() => currentPage = Math.min(totalPages, currentPage + 1)} disabled={currentPage === totalPages}>▶</button>
							<button on:click={() => currentPage = totalPages} disabled={currentPage === totalPages}>⏭</button>
						</div>
					</div>
				</div>
				
				{#if selectedRegion}
					<div class="detail-view">
						<div class="detail-header">
							<h3>{selectedRegion.region.toUpperCase()}</h3>
							<button class="close-btn" on:click={closeDetails}>✕ CLOSE</button>
						</div>
						<table class="detail-table">
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>COUNTRY</th>
									<th>TYPE</th>
									<th>STATUS</th>
								</tr>
							</thead>
							<tbody>
								{#each regionDetails as host}
									<tr>
										<td class="hostname">{host.host}</td>
										<td>{host.country}</td>
										<td>{host.infrastructure_type}</td>
										<td>
											<span class="status-dot {host.present_in_cmdb === 'Yes' ? 'active' : 'inactive'}"></span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<table class="data-table">
						<thead>
							<tr>
								<th>RANK</th>
								<th>REGION</th>
								<th>HOSTS</th>
								<th>LEVEL</th>
								<th>% GLOBAL</th>
								<th>STATUS</th>
								<th>ACTIONS</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedRegions as [region, count], i}
								{@const level = getRegionLevel(count)}
								{@const percentage = (count / totalHosts) * 100}
								<tr class="data-row">
									<td class="rank">#{(currentPage - 1) * itemsPerPage + i + 1}</td>
									<td class="region-name">{region}</td>
									<td class="host-count" style="color: {level.color}; text-shadow: 0 0 15px {level.color}">
										{formatNumber(count)}
									</td>
									<td>
										<span class="level-badge" style="background: {level.color}20; color: {level.color}; border: 1px solid {level.color}">
											{level.level}
										</span>
									</td>
									<td>
										<div class="percentage-bar">
											<div class="percentage-fill" 
												 style="width: {percentage}%; background: linear-gradient(90deg, #00ffff, {level.color})">
											</div>
											<span class="percentage-text">{percentage.toFixed(1)}%</span>
										</div>
									</td>
									<td>
										<span class="status-indicator {percentage > 20 ? 'active' : 'standby'}">
											{percentage > 20 ? 'ACTIVE' : 'STANDBY'}
										</span>
									</td>
									<td>
										<button class="action-btn" on:click={() => drillDownRegion(region, count)}>
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
	</div>
</div>

<style>
	.region-interface {
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		background: #000000;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.status-bar {
		display: flex;
		gap: 1rem;
		height: 80px;
		flex-shrink: 0;
	}
	
	.status-card {
		flex: 1;
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid #ff00ff;
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		box-shadow: 0 0 30px rgba(255, 0, 255, 0.3);
		position: relative;
		overflow: hidden;
	}
	
	.status-card::before {
		content: '';
		position: absolute;
		top: -50%;
		left: -50%;
		width: 200%;
		height: 200%;
		background: radial-gradient(circle, rgba(255, 0, 255, 0.1) 0%, transparent 70%);
		animation: rotate 15s linear infinite;
	}
	
	@keyframes rotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
	
	.status-value {
		font-size: 2rem;
		font-weight: 700;
		color: #ffffff;
		text-shadow: 0 0 25px #ff00ff;
		z-index: 1;
	}
	
	.status-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
		letter-spacing: 0.2em;
		margin-top: 0.25rem;
		z-index: 1;
	}
	
	.main-grid {
		flex: 1;
		display: grid;
		grid-template-columns: 650px 1fr;
		gap: 1rem;
		min-height: 0;
	}
	
	.globe-section {
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid #00ffff;
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		box-shadow: 0 0 40px rgba(0, 255, 255, 0.3);
	}
	
	.globe-container {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: transform 0.1s linear;
	}
	
	.world-map {
		width: 100%;
		height: auto;
		max-height: 100%;
	}
	
	.region-node {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.region-node:hover {
		transform: scale(1.2);
		filter: brightness(1.5);
	}
	
	.table-section {
		display: flex;
		flex-direction: column;
		min-height: 0;
	}
	
	.table-container {
		flex: 1;
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid #ff69b4;
		border-radius: 10px;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: 0 0 40px rgba(255, 105, 180, 0.3);
	}
	
	.table-header {
		padding: 1rem;
		background: linear-gradient(180deg, rgba(255, 105, 180, 0.1), transparent);
		border-bottom: 1px solid #ff69b4;
	}
	
	.table-header h2 {
		margin: 0 0 1rem 0;
		font-size: 1.2rem;
		color: #ffffff;
		letter-spacing: 0.2em;
		font-weight: 600;
		text-shadow: 0 0 20px #ff69b4;
	}
	
	.controls {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
	}
	
	.search-input {
		padding: 0.6rem 1rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid #00ffff;
		color: #ffffff;
		font-family: 'JetBrains Mono', monospace;
		border-radius: 5px;
		width: 300px;
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
	}
	
	.search-input:focus {
		outline: none;
		border-color: #ff00ff;
		box-shadow: 0 0 25px rgba(255, 0, 255, 0.5);
		background: rgba(255, 0, 255, 0.05);
	}
	
	.pagination {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.pagination button {
		padding: 0.5rem 0.8rem;
		background: linear-gradient(135deg, rgba(255, 0, 255, 0.2), rgba(255, 105, 180, 0.2));
		border: 1px solid #ff69b4;
		color: #ffffff;
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
		font-family: 'JetBrains Mono', monospace;
		font-weight: 600;
		box-shadow: 0 0 10px rgba(255, 105, 180, 0.3);
	}
	
	.pagination button:hover:not(:disabled) {
		background: linear-gradient(135deg, rgba(255, 0, 255, 0.4), rgba(255, 105, 180, 0.4));
		box-shadow: 0 0 20px rgba(255, 105, 180, 0.5);
		transform: scale(1.1);
	}
	
	.pagination button:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	
	.page-info {
		color: #ffffff;
		font-family: 'JetBrains Mono', monospace;
		padding: 0 1rem;
		font-weight: 600;
		text-shadow: 0 0 10px #ff00ff;
	}
	
	.data-table {
		width: 100%;
		border-collapse: collapse;
	}
	
	.data-table thead {
		background: rgba(255, 105, 180, 0.05);
		position: sticky;
		top: 0;
		z-index: 10;
	}
	
	.data-table th {
		padding: 1rem;
		text-align: left;
		font-size: 0.75rem;
		color: #00ffff;
		letter-spacing: 0.15em;
		font-weight: 600;
		border-bottom: 2px solid #ff69b4;
		text-shadow: 0 0 10px currentColor;
	}
	
	.data-row {
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.3s;
		cursor: pointer;
	}
	
	.data-row:hover {
		background: rgba(255, 0, 255, 0.05);
		transform: translateX(5px);
		box-shadow: inset 0 0 30px rgba(255, 0, 255, 0.1);
	}
	
	.data-table td {
		padding: 0.9rem;
		font-size: 0.85rem;
		color: rgba(255, 255, 255, 0.9);
		font-family: 'JetBrains Mono', monospace;
	}
	
	.rank {
		color: #ff00ff;
		font-weight: 700;
		text-shadow: 0 0 10px currentColor;
	}
	
	.region-name {
		color: #ffffff;
		font-weight: 500;
	}
	
	.host-count {
		font-weight: 700;
	}
	
	.level-badge {
		padding: 0.3rem 0.8rem;
		border-radius: 5px;
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		box-shadow: 0 0 10px currentColor;
	}
	
	.percentage-bar {
		position: relative;
		width: 100px;
		height: 20px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 10px;
		overflow: hidden;
		border: 1px solid rgba(0, 255, 255, 0.3);
	}
	
	.percentage-fill {
		height: 100%;
		transition: width 0.5s ease;
		box-shadow: 0 0 10px currentColor;
	}
	
	.percentage-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 0.65rem;
		color: #ffffff;
		font-weight: 700;
		text-shadow: 0 0 5px #000000;
	}
	
	.status-indicator {
		font-size: 0.75rem;
		font-weight: 600;
		padding: 0.2rem 0.6rem;
		border-radius: 3px;
	}
	
	.status-indicator.active {
		color: #00ffff;
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid #00ffff;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.4);
	}
	
	.status-indicator.standby {
		color: #ff69b4;
		background: rgba(255, 105, 180, 0.1);
		border: 1px solid #ff69b4;
		box-shadow: 0 0 10px rgba(255, 105, 180, 0.4);
	}
	
	.action-btn {
		padding: 0.4rem 1rem;
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(255, 105, 180, 0.2));
		border: 1px solid #00ffff;
		color: #ffffff;
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
		font-family: 'JetBrains Mono', monospace;
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
	}
	
	.action-btn:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.4), rgba(255, 105, 180, 0.4));
		box-shadow: 0 0 25px rgba(0, 255, 255, 0.5);
		transform: scale(1.05);
		border-color: #ff00ff;
	}
	
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
		border-bottom: 2px solid #ff00ff;
	}
	
	.detail-header h3 {
		margin: 0;
		color: #00ffff;
		font-size: 1.3rem;
		text-shadow: 0 0 20px currentColor;
	}
	
	.close-btn {
		padding: 0.6rem 1.2rem;
		background: rgba(255, 0, 0, 0.1);
		border: 1px solid #ff69b4;
		color: #ffffff;
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
		font-weight: 600;
		box-shadow: 0 0 15px rgba(255, 105, 180, 0.3);
	}
	
	.close-btn:hover {
		background: rgba(255, 0, 0, 0.3);
		box-shadow: 0 0 25px rgba(255, 105, 180, 0.5);
		transform: scale(1.05);
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
		color: #00ffff;
		font-size: 0.75rem;
		letter-spacing: 0.1em;
		border-bottom: 1px solid #00ffff;
		text-align: left;
		text-shadow: 0 0 10px currentColor;
	}
	
	.detail-table td {
		padding: 0.6rem 0.8rem;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}
	
	.hostname {
		font-family: 'JetBrains Mono', monospace;
		color: #ff00ff;
		font-size: 0.75rem;
		text-shadow: 0 0 5px currentColor;
	}
	
	.status-dot {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 50%;
	}
	
	.status-dot.active {
		background: #00ffff;
		box-shadow: 0 0 10px #00ffff;
	}
	
	.status-dot.inactive {
		background: #ff69b4;
		box-shadow: 0 0 10px #ff69b4;
	}
	
	::-webkit-scrollbar {
		width: 8px;
	}
	
	::-webkit-scrollbar-track {
		background: #000000;
	}
	
	::-webkit-scrollbar-thumb {
		background: linear-gradient(180deg, #00ffff, #ff00ff, #ff69b4);
		border-radius: 4px;
		box-shadow: 0 0 10px #00ffff;
	}
</style>