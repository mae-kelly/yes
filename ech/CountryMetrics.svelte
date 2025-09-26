<!-- ech/CountryMetrics.svelte -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedCountry = null;
	let countryDetails = [];
	let searchTerm = '';
	let currentPage = 1;
	let itemsPerPage = 15;
	let viewMode = 'table';
	
	let particleField = [];
	let connectionLines = [];
	let rotationAngle = 0;
	let animationFrame;
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/country_metrics');
			data = await response.json();
			loading = false;
			initializeVisuals();
			startAnimations();
		} catch (err) {
			console.error('Country sync failed:', err);
			loading = false;
		}
	});
	
	onDestroy(() => {
		if (animationFrame) cancelAnimationFrame(animationFrame);
	});
	
	function initializeVisuals() {
		for (let i = 0; i < 100; i++) {
			particleField.push({
				x: Math.random() * 800,
				y: Math.random() * 600,
				z: Math.random() * 100,
				vx: (Math.random() - 0.5) * 0.5,
				vy: (Math.random() - 0.5) * 0.5,
				size: Math.random() * 3 + 1
			});
		}
		
		for (let i = 0; i < 20; i++) {
			connectionLines.push({
				x1: Math.random() * 800,
				y1: Math.random() * 600,
				x2: Math.random() * 800,
				y2: Math.random() * 600,
				progress: Math.random()
			});
		}
	}
	
	function startAnimations() {
		const animate = () => {
			rotationAngle = (rotationAngle + 0.2) % 360;
			
			particleField.forEach(p => {
				p.x += p.vx;
				p.y += p.vy;
				if (p.x < 0 || p.x > 800) p.vx *= -1;
				if (p.y < 0 || p.y > 600) p.vy *= -1;
			});
			
			connectionLines.forEach(line => {
				line.progress += 0.01;
				if (line.progress > 1) {
					line.progress = 0;
					line.x1 = Math.random() * 800;
					line.y1 = Math.random() * 600;
					line.x2 = Math.random() * 800;
					line.y2 = Math.random() * 600;
				}
			});
			
			animationFrame = requestAnimationFrame(animate);
		};
		animate();
	}
	
	$: countries = data.global_intelligence ? 
		Object.entries(data.global_intelligence)
			.filter(([country]) => country.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => b[1] - a[1]) : [];
	
	$: paginatedCountries = countries.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(countries.length / itemsPerPage);
	$: totalHosts = countries.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = countries.length > 0 ? Math.max(...countries.map(([,c]) => c)) : 1;
	
	async function drillDownCountry(country, count) {
		selectedCountry = { country, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(country)}`);
			let result = await response.json();
			countryDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Country drill-down failed:', err);
			countryDetails = [];
			loading = false;
		}
	}
	
	function closeDetails() {
		selectedCountry = null;
		countryDetails = [];
	}
	
	function getCountryLevel(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 80) return { level: 'SUPERPOWER', color: '#ff00ff' };
		if (percentage >= 60) return { level: 'MAJOR', color: '#00ffff' };
		if (percentage >= 40) return { level: 'SIGNIFICANT', color: '#ff69b4' };
		if (percentage >= 20) return { level: 'MODERATE', color: '#ff00ff' };
		return { level: 'EMERGING', color: '#00ffff' };
	}
	
	function formatNumber(num) {
		if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
		if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
		return num.toString();
	}
</script>

<div class="country-interface">
	<div class="intel-bar">
		<div class="intel-card">
			<div class="intel-value">{countries.length}</div>
			<div class="intel-label">COUNTRIES TRACKED</div>
		</div>
		<div class="intel-card">
			<div class="intel-value">{formatNumber(totalHosts)}</div>
			<div class="intel-label">GLOBAL ASSETS</div>
		</div>
		<div class="intel-card">
			<div class="intel-value">{Math.round(totalHosts / countries.length) || 0}</div>
			<div class="intel-label">AVG PER COUNTRY</div>
		</div>
	</div>
	
	<div class="main-content">
		<div class="visualization-panel">
			<div class="view-controls">
				<button class="view-btn {viewMode === 'table' ? 'active' : ''}" on:click={() => viewMode = 'table'}>TABLE</button>
				<button class="view-btn {viewMode === 'graph' ? 'active' : ''}" on:click={() => viewMode = 'graph'}>GRAPH</button>
				<button class="view-btn {viewMode === 'cards' ? 'active' : ''}" on:click={() => viewMode = 'cards'}>CARDS</button>
			</div>
			
			{#if viewMode === 'graph'}
				<div class="graph-view" style="transform: rotateY({rotationAngle}deg)">
					<svg viewBox="0 0 800 600" class="network-graph">
						<defs>
							<filter id="countryGlow">
								<feGaussianBlur stdDeviation="3" result="coloredBlur"/>
								<feMerge>
									<feMergeNode in="coloredBlur"/>
									<feMergeNode in="SourceGraphic"/>
								</feMerge>
							</filter>
						</defs>
						
						{#each connectionLines as line}
							<line x1="{line.x1}" y1="{line.y1}"
								  x2="{line.x1 + (line.x2 - line.x1) * line.progress}"
								  y2="{line.y1 + (line.y2 - line.y1) * line.progress}"
								  stroke="#00ffff" stroke-width="1" opacity="0.3"/>
						{/each}
						
						{#each particleField as particle}
							<circle cx="{particle.x}" cy="{particle.y}" r="{particle.size}"
									fill="#ff00ff" opacity="{0.3 + particle.z / 100 * 0.5}"
									filter="url(#countryGlow)"/>
						{/each}
						
						{#each countries.slice(0, 20) as [country, count], i}
							{@const angle = (i / 20) * Math.PI * 2}
							{@const x = 400 + Math.cos(angle) * 200}
							{@const y = 300 + Math.sin(angle) * 200}
							{@const level = getCountryLevel(count)}
							<g transform="translate({x}, {y})"
							   on:click={() => drillDownCountry(country, count)}
							   class="country-node">
								<circle r="30" fill="#000000" stroke="{level.color}"
										stroke-width="2" opacity="0.9"
										filter="url(#countryGlow)"/>
								<text text-anchor="middle" dy="-40" font-size="10"
									  fill="#ffffff" font-weight="600">
									{country.substring(0, 10).toUpperCase()}
								</text>
								<text text-anchor="middle" dy="5" font-size="14"
									  fill="{level.color}" font-weight="700"
									  style="text-shadow: 0 0 15px {level.color}">
									{formatNumber(count)}
								</text>
							</g>
						{/each}
					</svg>
				</div>
			{:else if viewMode === 'cards'}
				<div class="cards-view">
					{#each paginatedCountries as [country, count]}
						{@const level = getCountryLevel(count)}
						<div class="country-card" style="border-color: {level.color}"
							 on:click={() => drillDownCountry(country, count)}>
							<div class="card-header" style="background: linear-gradient(135deg, {level.color}20, transparent)">
								<span class="card-name">{country.toUpperCase()}</span>
							</div>
							<div class="card-body">
								<div class="card-stat">
									<span class="stat-label">HOSTS</span>
									<span class="stat-value" style="color: {level.color}">{formatNumber(count)}</span>
								</div>
								<div class="card-stat">
									<span class="stat-label">LEVEL</span>
									<span class="stat-value">{level.level}</span>
								</div>
							</div>
							<div class="card-footer">
								<div class="card-bar">
									<div class="card-fill" style="width: {(count / maxHosts) * 100}%; background: {level.color}"></div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
		
		<div class="data-panel">
			<div class="table-container">
				<div class="table-header">
					<h2>COUNTRY INTELLIGENCE MATRIX</h2>
					<div class="controls">
						<input type="text" 
							   bind:value={searchTerm}
							   placeholder="SEARCH COUNTRIES..."
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
				
				{#if selectedCountry}
					<div class="detail-view">
						<div class="detail-header">
							<h3>{selectedCountry.country.toUpperCase()}</h3>
							<button class="close-btn" on:click={closeDetails}>✕ CLOSE</button>
						</div>
						<table class="detail-table">
							<thead>
								<tr>
									<th>HOSTNAME</th>
									<th>REGION</th>
									<th>TYPE</th>
									<th>STATUS</th>
								</tr>
							</thead>
							<tbody>
								{#each countryDetails as host}
									<tr>
										<td class="hostname">{host.host}</td>
										<td>{host.region}</td>
										<td>{host.infrastructure_type}</td>
										<td>
											<span class="status-dot {host.present_in_cmdb === 'Yes' ? 'active' : 'inactive'}"></span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else if viewMode === 'table'}
					<table class="data-table">
						<thead>
							<tr>
								<th>RANK</th>
								<th>COUNTRY</th>
								<th>HOSTS</th>
								<th>LEVEL</th>
								<th>% GLOBAL</th>
								<th>STATUS</th>
								<th>ACTIONS</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedCountries as [country, count], i}
								{@const level = getCountryLevel(count)}
								{@const percentage = (count / totalHosts) * 100}
								<tr class="data-row">
									<td class="rank">#{(currentPage - 1) * itemsPerPage + i + 1}</td>
									<td class="country-name">{country}</td>
									<td class="host-count" style="color: {level.color}; text-shadow: 0 0 15px {level.color}">
										{formatNumber(count)}
									</td>
									<td>
										<span class="level-badge" style="background: {level.color}20; color: {level.color}; border: 1px solid {level.color}; box-shadow: 0 0 10px {level.color}">
											{level.level}
										</span>
									</td>
									<td>
										<div class="percentage-bar">
											<div class="percentage-fill" 
												 style="width: {percentage}%; background: linear-gradient(90deg, #00ffff, {level.color}); box-shadow: 0 0 10px {level.color}">
											</div>
											<span class="percentage-text">{percentage.toFixed(1)}%</span>
										</div>
									</td>
									<td>
										<span class="status-indicator {percentage > 10 ? 'online' : 'standby'}">
											{percentage > 10 ? 'ACTIVE' : 'STANDBY'}
										</span>
									</td>
									<td>
										<button class="action-btn" on:click={() => drillDownCountry(country, count)}>
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
	.country-interface {
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		background: #000000;
		font-family: 'JetBrains Mono', monospace;
	}
	
	.intel-bar {
		display: flex;
		gap: 1rem;
		height: 80px;
		flex-shrink: 0;
	}
	
	.intel-card {
		flex: 1;
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid #00ffff;
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		position: relative;
		overflow: hidden;
		box-shadow: 0 0 30px rgba(0, 255, 255, 0.3);
	}
	
	.intel-card::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(255, 0, 255, 0.3), transparent);
		animation: sweep 3s infinite;
	}
	
	@keyframes sweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}
	
	.intel-value {
		font-size: 1.8rem;
		font-weight: 700;
		color: #ffffff;
		text-shadow: 0 0 20px #00ffff;
		z-index: 1;
	}
	
	.intel-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
		letter-spacing: 0.2em;
		margin-top: 0.25rem;
		z-index: 1;
	}
	
	.main-content {
		flex: 1;
		display: grid;
		grid-template-columns: 800px 1fr;
		gap: 1rem;
		min-height: 0;
	}
	
	.visualization-panel {
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid #ff00ff;
		border-radius: 10px;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		box-shadow: 0 0 30px rgba(255, 0, 255, 0.3);
	}
	
	.view-controls {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
		justify-content: center;
	}
	
	.view-btn {
		padding: 0.5rem 1rem;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid #00ffff;
		color: rgba(255, 255, 255, 0.7);
		cursor: pointer;
		border-radius: 5px;
		transition: all 0.3s;
		font-family: 'JetBrains Mono', monospace;
		font-weight: 600;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
	}
	
	.view-btn:hover {
		background: rgba(0, 255, 255, 0.1);
		color: #00ffff;
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
	}
	
	.view-btn.active {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.3), rgba(255, 0, 255, 0.3));
		color: #ffffff;
		border-color: #ff00ff;
		box-shadow: 0 0 25px rgba(255, 0, 255, 0.5);
	}
	
	.graph-view {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: transform 0.1s linear;
	}
	
	.network-graph {
		width: 100%;
		height: auto;
	}
	
	.country-node {
		cursor: pointer;
		transition: all 0.3s ease;
	}
	
	.country-node:hover {
		transform: scale(1.2);
		filter: brightness(1.5);
	}
	
	.cards-view {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
		overflow-y: auto;
		padding: 0.5rem;
	}
	
	.country-card {
		background: rgba(0, 0, 0, 0.8);
		border: 2px solid;
		border-radius: 10px;
		overflow: hidden;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 0 15px currentColor;
	}
	
	.country-card:hover {
		transform: translateY(-5px) scale(1.02);
		box-shadow: 0 10px 30px currentColor;
	}
	
	.card-header {
		padding: 0.8rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.card-name {
		font-size: 0.8rem;
		font-weight: 700;
		color: #ffffff;
		text-shadow: 0 0 10px currentColor;
	}
	
	.card-body {
		padding: 1rem;
	}
	
	.card-stat {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.5rem;
		font-size: 0.75rem;
	}
	
	.stat-label {
		color: rgba(255, 255, 255, 0.6);
		font-weight: 500;
	}
	
	.stat-value {
		font-weight: 700;
		text-shadow: 0 0 10px currentColor;
	}
	
	.card-footer {
		padding: 0.5rem;
	}
	
	.card-bar {
		height: 6px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		overflow: hidden;
	}
	
	.card-fill {
		height: 100%;
		transition: width 0.5s;
		box-shadow: 0 0 10px currentColor;
	}
	
	.data-panel {
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
		box-shadow: 0 0 30px rgba(255, 105, 180, 0.3);
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
	
	.country-name {
		color: #ffffff;
		font-weight: 500;
	}
	
	.host-count {
		font-weight: 700;
	}
	
	.level-badge {
		padding: 0.3rem 0.8rem;
		border-radius: 5px;
		font-size: 0.65rem;
		font-weight: 700;
		letter-spacing: 0.1em;
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
	
	.status-indicator.online {
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