<!-- SourceTables.svelte -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';
	let sortField = 'frequency';
	let sortDirection = 'desc';

	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/source_tables');
			let result = await response.json();
			data = result;
			loading = false;
		} catch (err) {
			console.error('Source tables error:', err);
			loading = false;
		}
	});

	$: filteredSources = data.source_intelligence ? 
		Object.entries(data.source_intelligence)
			.filter(([source]) => source.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => {
				if (sortField === 'frequency') {
					return sortDirection === 'desc' ? b[1] - a[1] : a[1] - b[1];
				} else {
					return sortDirection === 'desc' ? 
						b[0].localeCompare(a[0]) : a[0].localeCompare(b[0]);
				}
			}) : [];

	function getThreatLevel(frequency) {
		if (!data.total_mentions) return { level: 'LOW', color: '#0096ff', intensity: 0.3 };
		let percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRITICAL', color: '#ff00ff', intensity: 1.0 };
		if (percentage >= 10) return { level: 'HIGH', color: '#ff0066', intensity: 0.8 };
		if (percentage >= 5) return { level: 'MEDIUM', color: '#ffaa00', intensity: 0.6 };
		return { level: 'LOW', color: '#00ffff', intensity: 0.4 };
	}

	function getPercentage(frequency) {
		if (!data.total_mentions) return '0.00';
		return ((frequency / data.total_mentions) * 100).toFixed(2);
	}

	async function drillDownSource(source, frequency) {
		selectedSource = { source, frequency };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(source)}`);
			let result = await response.json();
			hostDetails = result.hosts || [];
			loading = false;
		} catch (err) {
			console.error('Host search error:', err);
			hostDetails = [];
			loading = false;
		}
	}

	function sortBy(field) {
		if (sortField === field) {
			sortDirection = sortDirection === 'desc' ? 'asc' : 'desc';
		} else {
			sortField = field;
			sortDirection = 'desc';
		}
	}

	function closeDetails() {
		selectedSource = null;
		hostDetails = [];
	}

	function getCircularProgress(percentage) {
		const circumference = 2 * Math.PI * 30;
		const strokeDashoffset = circumference - (percentage / 100) * circumference;
		return { strokeDashoffset };
	}
</script>

<div class="source-intel-matrix">
	<div class="matrix-header">
		<div class="header-hud">
			<div class="hud-element">
				<div class="hud-icon">◈</div>
				<div class="hud-data">
					<div class="data-label">SOURCE INTELLIGENCE</div>
					<div class="data-value">ANALYSIS PROTOCOL ACTIVE</div>
				</div>
			</div>
			<div class="metrics-display">
				<div class="metric-ring">
					<svg width="80" height="80" viewBox="0 0 80 80">
						<circle cx="40" cy="40" r="30" fill="none" stroke="rgba(0, 255, 255, 0.2)" stroke-width="2"/>
						<circle 
							cx="40" cy="40" r="30" 
							fill="none" 
							stroke="#00ffff" 
							stroke-width="3"
							stroke-dasharray="188"
							stroke-dashoffset={getCircularProgress(85).strokeDashoffset}
							transform="rotate(-90 40 40)"
						/>
					</svg>
					<div class="ring-content">
						<div class="ring-value">{(data.unique_sources || 0).toLocaleString()}</div>
						<div class="ring-label">SOURCES</div>
					</div>
				</div>
				<div class="metric-ring">
					<svg width="80" height="80" viewBox="0 0 80 80">
						<circle cx="40" cy="40" r="30" fill="none" stroke="rgba(255, 0, 255, 0.2)" stroke-width="2"/>
						<circle 
							cx="40" cy="40" r="30" 
							fill="none" 
							stroke="#ff00ff" 
							stroke-width="3"
							stroke-dasharray="188"
							stroke-dashoffset={getCircularProgress(92).strokeDashoffset}
							transform="rotate(-90 40 40)"
						/>
					</svg>
					<div class="ring-content">
						<div class="ring-value">{(data.total_mentions || 0).toLocaleString()}</div>
						<div class="ring-label">MENTIONS</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<div class="control-matrix">
		<div class="search-console">
			<div class="console-frame">
				<input 
					type="text" 
					bind:value={searchTerm}
					placeholder="SEARCH SOURCE INTELLIGENCE..."
					class="console-input"
				/>
				<div class="search-scanner"></div>
			</div>
		</div>
		
		<div class="view-selector">
			<button class="selector-btn {!selectedSource ? 'active' : ''}" on:click={closeDetails}>
				<span class="btn-icon">▣</span>
				TABLE VIEW
			</button>
			{#if selectedSource}
				<button class="selector-btn active">
					<span class="btn-icon">⚡</span>
					DRILL: {selectedSource.source}
				</button>
			{/if}
		</div>
	</div>

	{#if loading && !selectedSource}
		<div class="loading-interface">
			<div class="loading-rings">
				{#each Array(3) as _, i}
					<div class="loading-ring" style="--delay: {i * 0.2}s; --size: {60 + i * 20}px"></div>
				{/each}
			</div>
			<div class="loading-text">SCANNING SOURCE INTELLIGENCE...</div>
		</div>
	{:else if selectedSource}
		<div class="drill-interface">
			<div class="drill-header">
				<div class="target-display">
					<div class="target-badge" style="--threat-color: {getThreatLevel(selectedSource.frequency).color}">
						<div class="badge-ring"></div>
						<span class="threat-level">{getThreatLevel(selectedSource.frequency).level}</span>
					</div>
					<div class="target-info">
						<h3>{selectedSource.source}</h3>
						<div class="target-stats">
							<span class="stat">FREQ: {selectedSource.frequency.toLocaleString()}</span>
							<span class="stat">COV: {getPercentage(selectedSource.frequency)}%</span>
						</div>
					</div>
				</div>
				
				<button class="close-terminal" on:click={closeDetails}>
					<div class="close-icon">✕</div>
				</button>
			</div>

			{#if loading}
				<div class="scanning-hosts">
					<div class="scan-grid">
						{#each Array(9) as _, i}
							<div class="scan-cell" style="animation-delay: {i * 0.1}s"></div>
						{/each}
					</div>
					<p>RETRIEVING HOST DETAILS...</p>
				</div>
			{:else}
				<div class="host-matrix">
					<div class="matrix-grid">
						<div class="grid-header">
							<div class="header-cell">HOST</div>
							<div class="header-cell">REGION</div>
							<div class="header-cell">COUNTRY</div>
							<div class="header-cell">INFRA</div>
							<div class="header-cell">DC</div>
							<div class="header-cell">CMDB</div>
							<div class="header-cell">TANIUM</div>
						</div>
						{#each hostDetails.slice(0, 50) as host, i}
							<div class="grid-row" style="animation-delay: {i * 0.05}s">
								<div class="data-cell host-cell">{host.host}</div>
								<div class="data-cell">{host.region}</div>
								<div class="data-cell">{host.country}</div>
								<div class="data-cell">{host.infrastructure_type}</div>
								<div class="data-cell">{host.data_center}</div>
								<div class="data-cell">
									<span class="status-chip {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
										{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'ACTIVE' : 'INACTIVE'}
									</span>
								</div>
								<div class="data-cell">
									<span class="status-chip {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
										{host.tanium_coverage?.toLowerCase().includes('tanium') ? 'COVERED' : 'NOT COVERED'}
									</span>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	{:else}
		<div class="data-matrix">
			<div class="matrix-grid">
				<div class="grid-header">
					<div class="header-cell sortable" on:click={() => sortBy('source')}>
						SOURCE TABLE
						{#if sortField === 'source'}
							<span class="sort-arrow">{sortDirection === 'desc' ? '▼' : '▲'}</span>
						{/if}
					</div>
					<div class="header-cell sortable" on:click={() => sortBy('frequency')}>
						FREQUENCY
						{#if sortField === 'frequency'}
							<span class="sort-arrow">{sortDirection === 'desc' ? '▼' : '▲'}</span>
						{/if}
					</div>
					<div class="header-cell">COVERAGE</div>
					<div class="header-cell">THREAT LEVEL</div>
					<div class="header-cell">ACTIONS</div>
				</div>
				
				{#each filteredSources.slice(0, 50) as [source, frequency], i}
					<div class="grid-row" style="--threat-color: {getThreatLevel(frequency).color}; animation-delay: {i * 0.02}s">
						<div class="data-cell source-cell">
							<div class="source-indicator" style="background: {getThreatLevel(frequency).color}"></div>
							{source}
						</div>
						<div class="data-cell frequency-cell">
							<span class="frequency-value">{frequency.toLocaleString()}</span>
						</div>
						<div class="data-cell coverage-cell">
							<div class="coverage-bar">
								<div class="coverage-fill" style="width: {getPercentage(frequency)}%; background: {getThreatLevel(frequency).color};"></div>
								<span class="coverage-text">{getPercentage(frequency)}%</span>
							</div>
						</div>
						<div class="data-cell threat-cell">
							<span class="threat-badge {getThreatLevel(frequency).level.toLowerCase()}" 
								  style="color: {getThreatLevel(frequency).color}; border-color: {getThreatLevel(frequency).color};">
								{getThreatLevel(frequency).level}
							</span>
						</div>
						<div class="data-cell action-cell">
							<button class="drill-button" on:click={() => drillDownSource(source, frequency)}>
								<span class="drill-icon">⚡</span>
								DRILL DOWN
							</button>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<div class="interface-footer">
		<div class="footer-stats">
			<span>DISPLAYING {filteredSources.length} OF {data.unique_sources || 0} SOURCES</span>
			<span>AVG MENTIONS/SOURCE: {((data.total_mentions || 0) / (data.unique_sources || 1)).toFixed(0)}</span>
		</div>
		<div class="neural-signature">
			◈ SOURCE INTELLIGENCE PROTOCOL ACTIVE
		</div>
	</div>
</div>

<style>
	.source-intel-matrix {
		width: 100%;
		height: 100%;
		font-family: 'Orbitron', 'Exo 2', monospace;
		color: #fff;
		display: flex;
		flex-direction: column;
		background: transparent;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.matrix-header {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(0, 255, 255, 0.05) 50%,
			rgba(0, 0, 0, 0.8) 100%);
		border: 2px solid #00ffff;
		border-radius: 12px;
		padding: 1.5rem 2rem;
		margin-bottom: 1.5rem;
		backdrop-filter: blur(20px);
		box-shadow: 0 0 30px rgba(0, 255, 255, 0.2);
	}

	.header-hud {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.hud-element {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.hud-icon {
		font-size: 2rem;
		color: #00ffff;
		text-shadow: 0 0 20px #00ffff;
		animation: iconPulse 3s ease-in-out infinite;
	}

	.hud-data {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.data-label {
		font-size: 1.2rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
	}

	.data-value {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 400;
	}

	.metrics-display {
		display: flex;
		gap: 2rem;
	}

	.metric-ring {
		position: relative;
		width: 80px;
		height: 80px;
	}

	.ring-content {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
	}

	.ring-value {
		font-size: 1rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 10px #00ffff;
	}

	.ring-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.2rem;
	}

	.control-matrix {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		gap: 2rem;
	}

	.search-console {
		flex: 1;
		max-width: 500px;
	}

	.console-frame {
		position: relative;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 255, 255, 0.05));
		border: 2px solid #00ffff;
		border-radius: 8px;
		overflow: hidden;
	}

	.console-input {
		width: 100%;
		background: transparent;
		border: none;
		padding: 1rem 1.5rem;
		color: #fff;
		font-family: inherit;
		font-size: 0.9rem;
		font-weight: 600;
		outline: none;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.console-input::placeholder {
		color: rgba(255, 255, 255, 0.4);
		text-shadow: 0 0 8px rgba(0, 255, 255, 0.3);
	}

	.search-scanner {
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.3), transparent);
		animation: scannerSweep 3s linear infinite;
		pointer-events: none;
	}

	.view-selector {
		display: flex;
		gap: 0.5rem;
	}

	.selector-btn {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.02));
		border: 2px solid rgba(255, 255, 255, 0.1);
		border-radius: 6px;
		padding: 0.8rem 1.5rem;
		color: rgba(255, 255, 255, 0.7);
		font-family: inherit;
		font-size: 0.7rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.selector-btn:hover,
	.selector-btn.active {
		border-color: #00ffff;
		color: #00ffff;
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
		text-shadow: 0 0 8px #00ffff;
	}

	.btn-icon {
		font-size: 0.8rem;
		animation: iconFloat 2s ease-in-out infinite;
	}

	.loading-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.loading-rings {
		position: relative;
		width: 120px;
		height: 120px;
	}

	.loading-ring {
		position: absolute;
		width: var(--size);
		height: var(--size);
		border: 3px solid transparent;
		border-top: 3px solid #00ffff;
		border-radius: 50%;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: ringSpin 2s linear infinite;
		animation-delay: var(--delay);
	}

	.loading-text {
		color: #00ffff;
		font-size: 1rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		animation: textGlow 2s ease-in-out infinite;
	}

	.data-matrix {
		flex: 1;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.02));
		border: 2px solid #00ffff;
		border-radius: 12px;
		overflow: hidden;
	}

	.matrix-grid {
		width: 100%;
		display: flex;
		flex-direction: column;
	}

	.grid-header {
		display: grid;
		grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(0, 255, 255, 0.1));
		border-bottom: 2px solid #00ffff;
	}

	.header-cell {
		padding: 1rem 1.5rem;
		font-size: 0.8rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 8px #00ffff;
		border-right: 1px solid rgba(0, 255, 255, 0.2);
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.sortable {
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.sortable:hover {
		background: rgba(0, 255, 255, 0.05);
	}

	.sort-arrow {
		color: #ff00ff;
		text-shadow: 0 0 8px #ff00ff;
	}

	.grid-row {
		display: grid;
		grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.3s ease;
		animation: rowEntrance 0.5s ease-out;
		animation-fill-mode: both;
		opacity: 0;
	}

	.grid-row:hover {
		background: linear-gradient(90deg, 
			rgba(0, 255, 255, 0.05), 
			rgba(255, 0, 255, 0.02), 
			transparent);
		box-shadow: inset 3px 0 0 var(--threat-color);
	}

	.data-cell {
		padding: 1rem 1.5rem;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
		border-right: 1px solid rgba(255, 255, 255, 0.05);
		display: flex;
		align-items: center;
	}

	.source-cell {
		font-weight: 600;
		color: #fff;
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.source-indicator {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		box-shadow: 0 0 10px currentColor;
		animation: indicatorPulse 2s ease-in-out infinite;
	}

	.frequency-cell {
		justify-content: center;
	}

	.frequency-value {
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 8px #00ffff;
	}

	.coverage-cell {
		justify-content: center;
	}

	.coverage-bar {
		position: relative;
		width: 100px;
		height: 20px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 10px;
		border: 1px solid rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}

	.coverage-fill {
		height: 100%;
		border-radius: 10px;
		transition: width 1s ease-out;
		box-shadow: 0 0 15px currentColor;
	}

	.coverage-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 0.7rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
	}

	.threat-cell {
		justify-content: center;
	}

	.threat-badge {
		padding: 0.4rem 0.8rem;
		border: 2px solid;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		background: rgba(0, 0, 0, 0.4);
		text-shadow: 0 0 8px currentColor;
		animation: badgeGlow 3s ease-in-out infinite;
	}

	.action-cell {
		justify-content: center;
	}

	.drill-button {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.05));
		border: 2px solid #00ffff;
		border-radius: 6px;
		padding: 0.6rem 1rem;
		color: #00ffff;
		font-family: inherit;
		font-size: 0.7rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		text-transform: uppercase;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		letter-spacing: 0.05em;
	}

	.drill-button:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 255, 255, 0.1));
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
		transform: translateY(-2px);
		text-shadow: 0 0 8px #00ffff;
	}

	.drill-icon {
		font-size: 0.8rem;
		animation: iconSpark 2s ease-in-out infinite;
	}

	.drill-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 0, 255, 0.02));
		border: 2px solid #ff00ff;
		border-radius: 12px;
		overflow: hidden;
	}

	.drill-header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(255, 0, 255, 0.05));
		border-bottom: 2px solid #ff00ff;
		padding: 1.5rem 2rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.target-display {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.target-badge {
		position: relative;
		padding: 1rem;
		border: 2px solid var(--threat-color);
		border-radius: 8px;
		background: rgba(0, 0, 0, 0.6);
		text-align: center;
	}

	.badge-ring {
		position: absolute;
		top: -2px;
		left: -2px;
		right: -2px;
		bottom: -2px;
		border: 1px solid var(--threat-color);
		border-radius: 8px;
		animation: ringRotate 4s linear infinite;
		opacity: 0.5;
	}

	.threat-level {
		font-size: 0.8rem;
		font-weight: 700;
		color: var(--threat-color);
		text-shadow: 0 0 10px var(--threat-color);
		z-index: 2;
		position: relative;
	}

	.target-info h3 {
		margin: 0;
		font-size: 1.3rem;
		color: #fff;
		text-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
	}

	.target-stats {
		display: flex;
		gap: 1.5rem;
		margin-top: 0.5rem;
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.stat {
		color: #ff00ff;
		font-weight: 600;
		text-shadow: 0 0 8px #ff00ff;
	}

	.close-terminal {
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.2), rgba(255, 0, 102, 0.1));
		border: 2px solid #ff0066;
		border-radius: 50%;
		width: 50px;
		height: 50px;
		color: #ff0066;
		font-size: 1.5rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-terminal:hover {
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.3), rgba(255, 0, 102, 0.2));
		box-shadow: 0 0 25px rgba(255, 0, 102, 0.5);
		transform: rotate(90deg);
	}

	.close-icon {
		text-shadow: 0 0 10px #ff0066;
	}

	.scanning-hosts {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
		color: #ff00ff;
	}

	.scan-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.5rem;
		width: 120px;
		height: 120px;
	}

	.scan-cell {
		background: #ff00ff;
		border-radius: 2px;
		animation: cellFlicker 1.5s ease-in-out infinite;
		opacity: 0.3;
	}

	.host-matrix {
		flex: 1;
		padding: 1rem;
		overflow-y: auto;
	}

	.host-matrix .grid-header {
		grid-template-columns: 2fr 1fr 1fr 1.5fr 1fr 1fr 1.5fr;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(255, 0, 255, 0.1));
		border-bottom: 2px solid #ff00ff;
	}

	.host-matrix .header-cell {
		color: #ff00ff;
		text-shadow: 0 0 8px #ff00ff;
	}

	.host-matrix .grid-row {
		grid-template-columns: 2fr 1fr 1fr 1.5fr 1fr 1fr 1.5fr;
	}

	.host-cell {
		color: #fff;
		font-weight: 600;
	}

	.status-chip {
		padding: 0.3rem 0.8rem;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border: 1px solid;
	}

	.status-chip.active {
		background: rgba(0, 255, 133, 0.1);
		color: #00ff85;
		border-color: #00ff85;
		text-shadow: 0 0 8px #00ff85;
	}

	.status-chip.inactive {
		background: rgba(255, 0, 102, 0.1);
		color: #ff0066;
		border-color: #ff0066;
		text-shadow: 0 0 8px #ff0066;
	}

	.interface-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 0;
		margin-top: 1.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.5);
	}

	.footer-stats {
		display: flex;
		gap: 2rem;
	}

	.neural-signature {
		color: #00ffff;
		font-weight: 600;
		letter-spacing: 0.05em;
		text-shadow: 0 0 8px #00ffff;
	}

	@keyframes iconPulse {
		0%, 100% { transform: scale(1); text-shadow: 0 0 20px #00ffff; }
		50% { transform: scale(1.05); text-shadow: 0 0 30px #00ffff; }
	}

	@keyframes scannerSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-2px); }
	}

	@keyframes ringSpin {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes textGlow {
		0%, 100% { text-shadow: 0 0 10px #00ffff; }
		50% { text-shadow: 0 0 20px #00ffff; }
	}

	@keyframes rowEntrance {
		0% { 
			opacity: 0; 
			transform: translateX(-20px);
		}
		100% { 
			opacity: 1; 
			transform: translateX(0);
		}
	}

	@keyframes indicatorPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.6; transform: scale(1.2); }
	}

	@keyframes badgeGlow {
		0%, 100% { box-shadow: 0 0 8px currentColor; }
		50% { box-shadow: 0 0 16px currentColor; }
	}

	@keyframes iconSpark {
		0%, 100% { text-shadow: 0 0 5px currentColor; }
		50% { text-shadow: 0 0 15px currentColor; }
	}

	@keyframes ringRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes cellFlicker {
		0%, 100% { opacity: 0.3; background: #ff00ff; }
		50% { opacity: 1; background: #fff; }
	}

	@media (max-width: 1200px) {
		.header-hud {
			flex-direction: column;
			gap: 1rem;
		}

		.control-matrix {
			flex-direction: column;
			gap: 1rem;
		}

		.matrix-grid .grid-header,
		.matrix-grid .grid-row {
			grid-template-columns: 1fr;
			gap: 0.5rem;
		}

		.data-cell {
			justify-content: space-between;
		}
	}

	@media (max-width: 768px) {
		.matrix-header {
			padding: 1rem;
		}

		.drill-header {
			flex-direction: column;
			gap: 1rem;
			align-items: flex-start;
		}

		.target-display {
			flex-direction: column;
			align-items: flex-start;
			gap: 1rem;
		}
	}
</style>