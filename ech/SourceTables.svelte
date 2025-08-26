<!-- SourceTables.svelte -->
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedSource = null;
	let hostDetails = [];
	let searchTerm = '';

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
			.sort((a, b) => b[1] - a[1]) : [];

	function getThreatLevel(frequency) {
		if (!data.total_mentions) return { level: 'LOW', color: '#0096ff', intensity: 0.3 };
		let percentage = (frequency / data.total_mentions) * 100;
		if (percentage >= 15) return { level: 'CRIT', color: '#ff00ff', intensity: 1.0 };
		if (percentage >= 10) return { level: 'HIGH', color: '#ff0066', intensity: 0.8 };
		if (percentage >= 5) return { level: 'MED', color: '#ffaa00', intensity: 0.6 };
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

	function closeDetails() {
		selectedSource = null;
		hostDetails = [];
	}

	function getCircularProgress(percentage) {
		const circumference = 2 * Math.PI * 25;
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
					<svg width="60" height="60" viewBox="0 0 60 60">
						<circle cx="30" cy="30" r="25" fill="none" stroke="rgba(0, 255, 255, 0.2)" stroke-width="1.5"/>
						<circle 
							cx="30" cy="30" r="25" 
							fill="none" 
							stroke="#00ffff" 
							stroke-width="2"
							stroke-dasharray="157"
							stroke-dashoffset={getCircularProgress(85).strokeDashoffset}
							transform="rotate(-90 30 30)"
						/>
					</svg>
					<div class="ring-content">
						<div class="ring-value">{(data.unique_sources || 0).toLocaleString()}</div>
						<div class="ring-label">SOURCES</div>
					</div>
				</div>
				<div class="metric-ring">
					<svg width="60" height="60" viewBox="0 0 60 60">
						<circle cx="30" cy="30" r="25" fill="none" stroke="rgba(255, 0, 255, 0.2)" stroke-width="1.5"/>
						<circle 
							cx="30" cy="30" r="25" 
							fill="none" 
							stroke="#ff00ff" 
							stroke-width="2"
							stroke-dasharray="157"
							stroke-dashoffset={getCircularProgress(92).strokeDashoffset}
							transform="rotate(-90 30 30)"
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
				TABLE
			</button>
			{#if selectedSource}
				<button class="selector-btn active">
					<span class="btn-icon">⚡</span>
					DRILL
				</button>
			{/if}
		</div>
	</div>

	{#if loading && !selectedSource}
		<div class="loading-interface">
			<div class="loading-rings">
				{#each Array(3) as _, i}
					<div class="loading-ring" style="--delay: {i * 0.2}s; --size: {40 + i * 15}px"></div>
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
							<span class="stat">F: {selectedSource.frequency.toLocaleString()}</span>
							<span class="stat">%: {getPercentage(selectedSource.frequency)}%</span>
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
							<div class="header-cell">CMDB</div>
							<div class="header-cell">TANIUM</div>
						</div>
						{#each hostDetails.slice(0, 50) as host, i}
							<div class="grid-row" style="animation-delay: {i * 0.03}s">
								<div class="data-cell host-cell">{host.host}</div>
								<div class="data-cell">{host.region}</div>
								<div class="data-cell">{host.country}</div>
								<div class="data-cell">{host.infrastructure_type}</div>
								<div class="data-cell">
									<span class="status-chip {host.present_in_cmdb?.toLowerCase().includes('yes') ? 'active' : 'inactive'}">
										{host.present_in_cmdb?.toLowerCase().includes('yes') ? 'Y' : 'N'}
									</span>
								</div>
								<div class="data-cell">
									<span class="status-chip {host.tanium_coverage?.toLowerCase().includes('tanium') ? 'active' : 'inactive'}">
										{host.tanium_coverage?.toLowerCase().includes('tanium') ? 'Y' : 'N'}
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
					<div class="header-cell">SOURCE TABLE</div>
					<div class="header-cell">FREQ</div>
					<div class="header-cell">COV%</div>
					<div class="header-cell">THREAT</div>
					<div class="header-cell">ACTION</div>
				</div>
				
				{#each filteredSources.slice(0, 12) as [source, frequency], i}
					<div class="grid-row" style="--threat-color: {getThreatLevel(frequency).color}; animation-delay: {i * 0.02}s">
						<div class="data-cell source-cell">
							<div class="source-indicator" style="background: {getThreatLevel(frequency).color}"></div>
							<span class="source-name">{source}</span>
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
							<span class="threat-badge" 
								  style="color: {getThreatLevel(frequency).color}; border-color: {getThreatLevel(frequency).color};">
								{getThreatLevel(frequency).level}
							</span>
						</div>
						<div class="data-cell action-cell">
							<button class="drill-button" on:click={() => drillDownSource(source, frequency)}>
								<span class="drill-icon">⚡</span>
								DRILL
							</button>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<div class="interface-footer">
		<div class="footer-stats">
			<span>SHOWING {Math.min(filteredSources.length, 12)} OF {filteredSources.length}</span>
			<span>AVG: {((data.total_mentions || 0) / (data.unique_sources || 1)).toFixed(0)}/SRC</span>
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
		font-family: 'JetBrains Mono', monospace;
		color: #fff;
		display: flex;
		flex-direction: column;
		background: transparent;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		font-size: 0.75rem;
	}

	.matrix-header {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(0, 255, 255, 0.05) 50%,
			rgba(0, 0, 0, 0.8) 100%);
		border: 2px solid #00ffff;
		border-radius: 8px;
		padding: 0.8rem 1.2rem;
		margin-bottom: 1rem;
		backdrop-filter: blur(20px);
		box-shadow: 0 0 25px rgba(0, 255, 255, 0.2);
	}

	.header-hud {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.hud-element {
		display: flex;
		align-items: center;
		gap: 0.8rem;
	}

	.hud-icon {
		font-size: 1.5rem;
		color: #00ffff;
		text-shadow: 0 0 15px #00ffff;
		animation: iconPulse 3s ease-in-out infinite;
	}

	.hud-data {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.data-label {
		font-size: 0.9rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
	}

	.data-value {
		font-size: 0.65rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 400;
	}

	.metrics-display {
		display: flex;
		gap: 1.5rem;
	}

	.metric-ring {
		position: relative;
		width: 60px;
		height: 60px;
	}

	.ring-content {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
	}

	.ring-value {
		font-size: 0.7rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 8px #00ffff;
	}

	.ring-label {
		font-size: 0.45rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.1rem;
	}

	.control-matrix {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		gap: 1rem;
	}

	.search-console {
		flex: 1;
		max-width: 350px;
	}

	.console-frame {
		position: relative;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 255, 255, 0.05));
		border: 2px solid #00ffff;
		border-radius: 6px;
		overflow: hidden;
	}

	.console-input {
		width: 100%;
		background: transparent;
		border: none;
		padding: 0.6rem 1rem;
		color: #fff;
		font-family: inherit;
		font-size: 0.65rem;
		font-weight: 600;
		outline: none;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.console-input::placeholder {
		color: rgba(255, 255, 255, 0.4);
		text-shadow: 0 0 6px rgba(0, 255, 255, 0.3);
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
		gap: 0.3rem;
	}

	.selector-btn {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.02));
		border: 2px solid rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		padding: 0.5rem 0.8rem;
		color: rgba(255, 255, 255, 0.7);
		font-family: inherit;
		font-size: 0.6rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		display: flex;
		align-items: center;
		gap: 0.3rem;
	}

	.selector-btn:hover,
	.selector-btn.active {
		border-color: #00ffff;
		color: #00ffff;
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
		text-shadow: 0 0 6px #00ffff;
	}

	.btn-icon {
		font-size: 0.7rem;
		animation: iconFloat 2s ease-in-out infinite;
	}

	.loading-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1.5rem;
	}

	.loading-rings {
		position: relative;
		width: 80px;
		height: 80px;
	}

	.loading-ring {
		position: absolute;
		width: var(--size);
		height: var(--size);
		border: 2px solid transparent;
		border-top: 2px solid #00ffff;
		border-radius: 50%;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: ringSpin 2s linear infinite;
		animation-delay: var(--delay);
	}

	.loading-text {
		color: #00ffff;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		animation: textGlow 2s ease-in-out infinite;
	}

	.data-matrix {
		flex: 1;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.02));
		border: 2px solid #00ffff;
		border-radius: 8px;
		overflow: hidden;
	}

	.matrix-grid {
		width: 100%;
		display: flex;
		flex-direction: column;
	}

	.grid-header {
		display: grid;
		grid-template-columns: 2fr 0.8fr 0.8fr 0.6fr 0.8fr;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(0, 255, 255, 0.1));
		border-bottom: 2px solid #00ffff;
		gap: 1px;
	}

	.header-cell {
		padding: 0.6rem 0.8rem;
		font-size: 0.6rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 6px #00ffff;
		border-right: 1px solid rgba(0, 255, 255, 0.2);
		display: flex;
		align-items: center;
		letter-spacing: 0.03em;
	}

	.grid-row {
		display: grid;
		grid-template-columns: 2fr 0.8fr 0.8fr 0.6fr 0.8fr;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: all 0.3s ease;
		animation: rowEntrance 0.5s ease-out;
		animation-fill-mode: both;
		opacity: 0;
		gap: 1px;
	}

	.grid-row:hover {
		background: linear-gradient(90deg, 
			rgba(0, 255, 255, 0.05), 
			rgba(255, 0, 255, 0.02), 
			transparent);
		box-shadow: inset 3px 0 0 var(--threat-color);
	}

	.data-cell {
		padding: 0.6rem 0.8rem;
		font-size: 0.65rem;
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
		gap: 0.6rem;
	}

	.source-indicator {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		box-shadow: 0 0 8px currentColor;
		animation: indicatorPulse 2s ease-in-out infinite;
		flex-shrink: 0;
	}

	.source-name {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.frequency-cell {
		justify-content: center;
	}

	.frequency-value {
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 6px #00ffff;
	}

	.coverage-cell {
		justify-content: center;
	}

	.coverage-bar {
		position: relative;
		width: 60px;
		height: 12px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 6px;
		border: 1px solid rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}

	.coverage-fill {
		height: 100%;
		border-radius: 6px;
		transition: width 1s ease-out;
		box-shadow: 0 0 10px currentColor;
	}

	.coverage-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 0.5rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
	}

	.threat-cell {
		justify-content: center;
	}

	.threat-badge {
		padding: 0.2rem 0.5rem;
		border: 1px solid;
		border-radius: 3px;
		font-size: 0.5rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		background: rgba(0, 0, 0, 0.4);
		text-shadow: 0 0 6px currentColor;
		animation: badgeGlow 3s ease-in-out infinite;
	}

	.action-cell {
		justify-content: center;
	}

	.drill-button {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.05));
		border: 2px solid #00ffff;
		border-radius: 4px;
		padding: 0.3rem 0.6rem;
		color: #00ffff;
		font-family: inherit;
		font-size: 0.55rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		text-transform: uppercase;
		display: flex;
		align-items: center;
		gap: 0.3rem;
		letter-spacing: 0.03em;
	}

	.drill-button:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 255, 255, 0.1));
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.4);
		transform: translateY(-1px);
		text-shadow: 0 0 6px #00ffff;
	}

	.drill-icon {
		font-size: 0.6rem;
		animation: iconSpark 2s ease-in-out infinite;
	}

	.drill-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 0, 255, 0.02));
		border: 2px solid #ff00ff;
		border-radius: 8px;
		overflow: hidden;
	}

	.drill-header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(255, 0, 255, 0.05));
		border-bottom: 2px solid #ff00ff;
		padding: 0.8rem 1.2rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.target-display {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.target-badge {
		position: relative;
		padding: 0.6rem;
		border: 2px solid var(--threat-color);
		border-radius: 6px;
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
		border-radius: 6px;
		animation: ringRotate 4s linear infinite;
		opacity: 0.5;
	}

	.threat-level {
		font-size: 0.6rem;
		font-weight: 700;
		color: var(--threat-color);
		text-shadow: 0 0 8px var(--threat-color);
		z-index: 2;
		position: relative;
	}

	.target-info h3 {
		margin: 0;
		font-size: 1rem;
		color: #fff;
		text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
	}

	.target-stats {
		display: flex;
		gap: 1rem;
		margin-top: 0.3rem;
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.stat {
		color: #ff00ff;
		font-weight: 600;
		text-shadow: 0 0 6px #ff00ff;
	}

	.close-terminal {
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.2), rgba(255, 0, 102, 0.1));
		border: 2px solid #ff0066;
		border-radius: 50%;
		width: 35px;
		height: 35px;
		color: #ff0066;
		font-size: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-terminal:hover {
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.3), rgba(255, 0, 102, 0.2));
		box-shadow: 0 0 20px rgba(255, 0, 102, 0.5);
		transform: rotate(90deg);
	}

	.close-icon {
		text-shadow: 0 0 8px #ff0066;
	}

	.scanning-hosts {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1.5rem;
		color: #ff00ff;
	}

	.scan-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.3rem;
		width: 80px;
		height: 80px;
	}

	.scan-cell {
		background: #ff00ff;
		border-radius: 2px;
		animation: cellFlicker 1.5s ease-in-out infinite;
		opacity: 0.3;
	}

	.host-matrix {
		flex: 1;
		padding: 0.8rem;
		overflow-y: auto;
	}

	.host-matrix .grid-header {
		grid-template-columns: 2fr 1fr 1fr 1fr 0.6fr 0.6fr;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(255, 0, 255, 0.1));
		border-bottom: 2px solid #ff00ff;
	}

	.host-matrix .header-cell {
		color: #ff00ff;
		text-shadow: 0 0 6px #ff00ff;
	}

	.host-matrix .grid-row {
		grid-template-columns: 2fr 1fr 1fr 1fr 0.6fr 0.6fr;
	}

	.host-cell {
		color: #fff;
		font-weight: 600;
	}

	.status-chip {
		padding: 0.2rem 0.4rem;
		border-radius: 3px;
		font-size: 0.5rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		border: 1px solid;
	}

	.status-chip.active {
		background: rgba(0, 255, 133, 0.1);
		color: #00ff85;
		border-color: #00ff85;
		text-shadow: 0 0 6px #00ff85;
	}

	.status-chip.inactive {
		background: rgba(255, 0, 102, 0.1);
		color: #ff0066;
		border-color: #ff0066;
		text-shadow: 0 0 6px #ff0066;
	}

	.interface-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.6rem 0;
		margin-top: 1rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		font-size: 0.55rem;
		color: rgba(255, 255, 255, 0.5);
	}

	.footer-stats {
		display: flex;
		gap: 1.5rem;
	}

	.neural-signature {
		color: #00ffff;
		font-weight: 600;
		letter-spacing: 0.03em;
		text-shadow: 0 0 6px #00ffff;
	}

	@keyframes iconPulse {
		0%, 100% { transform: scale(1); text-shadow: 0 0 15px #00ffff; }
		50% { transform: scale(1.05); text-shadow: 0 0 20px #00ffff; }
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
		0%, 100% { text-shadow: 0 0 8px #00ffff; }
		50% { text-shadow: 0 0 15px #00ffff; }
	}

	@keyframes rowEntrance {
		0% { 
			opacity: 0; 
			transform: translateX(-15px);
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
		0%, 100% { box-shadow: 0 0 6px currentColor; }
		50% { box-shadow: 0 0 12px currentColor; }
	}

	@keyframes iconSpark {
		0%, 100% { text-shadow: 0 0 4px currentColor; }
		50% { text-shadow: 0 0 12px currentColor; }
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
			gap: 0.8rem;
		}

		.control-matrix {
			flex-direction: column;
			gap: 0.8rem;
		}

		.matrix-grid .grid-header,
		.matrix-grid .grid-row {
			grid-template-columns: 1fr;
			gap: 0.3rem;
		}

		.data-cell {
			justify-content: space-between;
		}
	}

	@media (max-width: 768px) {
		.matrix-header {
			padding: 0.6rem;
		}

		.drill-header {
			flex-direction: column;
			gap: 0.8rem;
			align-items: flex-start;
		}

		.target-display {
			flex-direction: column;
			align-items: flex-start;
			gap: 0.8rem;
		}
	}
</style>