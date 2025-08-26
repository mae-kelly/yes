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
		const circumference = 2 * Math.PI * 18;
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
					<svg width="40" height="40" viewBox="0 0 40 40">
						<circle cx="20" cy="20" r="18" fill="none" stroke="rgba(0, 255, 255, 0.2)" stroke-width="1"/>
						<circle 
							cx="20" cy="20" r="18" 
							fill="none" 
							stroke="#00ffff" 
							stroke-width="2"
							stroke-dasharray="113"
							stroke-dashoffset={getCircularProgress(85).strokeDashoffset}
							transform="rotate(-90 20 20)"
						/>
					</svg>
					<div class="ring-content">
						<div class="ring-value">{(data.unique_sources || 0).toLocaleString()}</div>
						<div class="ring-label">SRC</div>
					</div>
				</div>
				<div class="metric-ring">
					<svg width="40" height="40" viewBox="0 0 40 40">
						<circle cx="20" cy="20" r="18" fill="none" stroke="rgba(255, 0, 255, 0.2)" stroke-width="1"/>
						<circle 
							cx="20" cy="20" r="18" 
							fill="none" 
							stroke="#ff00ff" 
							stroke-width="2"
							stroke-dasharray="113"
							stroke-dashoffset={getCircularProgress(92).strokeDashoffset}
							transform="rotate(-90 20 20)"
						/>
					</svg>
					<div class="ring-content">
						<div class="ring-value">{(data.total_mentions || 0).toLocaleString()}</div>
						<div class="ring-label">TOT</div>
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
					placeholder="SEARCH SOURCE..."
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
					<div class="loading-ring" style="--delay: {i * 0.2}s; --size: {25 + i * 8}px"></div>
				{/each}
			</div>
			<div class="loading-text">SCANNING...</div>
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
							<div class="header-cell">TAN</div>
						</div>
						{#each hostDetails.slice(0, 100) as host, i}
							<div class="grid-row" style="animation-delay: {i * 0.01}s">
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
					<div class="header-cell">THR</div>
					<div class="header-cell">ACT</div>
				</div>
				
				{#each filteredSources.slice(0, 25) as [source, frequency], i}
					<div class="grid-row" style="--threat-color: {getThreatLevel(frequency).color}; animation-delay: {i * 0.01}s">
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
							</button>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<div class="interface-footer">
		<div class="footer-stats">
			<span>SHOWING {Math.min(filteredSources.length, 25)} OF {filteredSources.length}</span>
			<span>AVG: {((data.total_mentions || 0) / (data.unique_sources || 1)).toFixed(0)}/SRC</span>
		</div>
		<div class="neural-signature">
			◈ SOURCE INTELLIGENCE ACTIVE
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
		letter-spacing: 0.02em;
		font-size: 0.65rem;
	}

	.matrix-header {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(0, 255, 255, 0.05) 50%,
			rgba(0, 0, 0, 0.8) 100%);
		border: 1px solid #00ffff;
		border-radius: 6px;
		padding: 0.5rem 0.8rem;
		margin-bottom: 0.6rem;
		backdrop-filter: blur(20px);
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
		flex-shrink: 0;
	}

	.header-hud {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.hud-element {
		display: flex;
		align-items: center;
		gap: 0.6rem;
	}

	.hud-icon {
		font-size: 1.2rem;
		color: #00ffff;
		text-shadow: 0 0 10px #00ffff;
		animation: iconPulse 3s ease-in-out infinite;
	}

	.hud-data {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
	}

	.data-label {
		font-size: 0.7rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 8px rgba(0, 255, 255, 0.5);
	}

	.data-value {
		font-size: 0.5rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 400;
	}

	.metrics-display {
		display: flex;
		gap: 1rem;
	}

	.metric-ring {
		position: relative;
		width: 40px;
		height: 40px;
	}

	.ring-content {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		text-align: center;
	}

	.ring-value {
		font-size: 0.55rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 6px #00ffff;
	}

	.ring-label {
		font-size: 0.35rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.05rem;
	}

	.control-matrix {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.6rem;
		gap: 0.8rem;
		flex-shrink: 0;
	}

	.search-console {
		flex: 1;
		max-width: 280px;
	}

	.console-frame {
		position: relative;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 255, 255, 0.05));
		border: 1px solid #00ffff;
		border-radius: 4px;
		overflow: hidden;
	}

	.console-input {
		width: 100%;
		background: transparent;
		border: none;
		padding: 0.4rem 0.7rem;
		color: #fff;
		font-family: inherit;
		font-size: 0.55rem;
		font-weight: 600;
		outline: none;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.console-input::placeholder {
		color: rgba(255, 255, 255, 0.4);
		text-shadow: 0 0 4px rgba(0, 255, 255, 0.3);
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
		gap: 0.2rem;
	}

	.selector-btn {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 3px;
		padding: 0.3rem 0.6rem;
		color: rgba(255, 255, 255, 0.7);
		font-family: inherit;
		font-size: 0.5rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		text-transform: uppercase;
		letter-spacing: 0.02em;
		display: flex;
		align-items: center;
		gap: 0.2rem;
	}

	.selector-btn:hover,
	.selector-btn.active {
		border-color: #00ffff;
		color: #00ffff;
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
		text-shadow: 0 0 4px #00ffff;
	}

	.btn-icon {
		font-size: 0.6rem;
		animation: iconFloat 2s ease-in-out infinite;
	}

	.loading-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}

	.loading-rings {
		position: relative;
		width: 60px;
		height: 60px;
	}

	.loading-ring {
		position: absolute;
		width: var(--size);
		height: var(--size);
		border: 1px solid transparent;
		border-top: 1px solid #00ffff;
		border-radius: 50%;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: ringSpin 2s linear infinite;
		animation-delay: var(--delay);
	}

	.loading-text {
		color: #00ffff;
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.05em;
		animation: textGlow 2s ease-in-out infinite;
	}

	.data-matrix {
		flex: 1;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.02));
		border: 1px solid #00ffff;
		border-radius: 6px;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}

	.matrix-grid {
		width: 100%;
		display: flex;
		flex-direction: column;
		flex: 1;
		overflow-y: auto;
	}

	.grid-header {
		display: grid;
		grid-template-columns: 2fr 0.6fr 0.6fr 0.4fr 0.4fr;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(0, 255, 255, 0.1));
		border-bottom: 1px solid #00ffff;
		gap: 0.5px;
		position: sticky;
		top: 0;
		z-index: 10;
		flex-shrink: 0;
	}

	.header-cell {
		padding: 0.4rem 0.5rem;
		font-size: 0.5rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 4px #00ffff;
		border-right: 1px solid rgba(0, 255, 255, 0.2);
		display: flex;
		align-items: center;
		letter-spacing: 0.02em;
	}

	.grid-row {
		display: grid;
		grid-template-columns: 2fr 0.6fr 0.6fr 0.4fr 0.4fr;
		border-bottom: 1px solid rgba(255, 255, 255, 0.03);
		transition: all 0.3s ease;
		animation: rowEntrance 0.4s ease-out;
		animation-fill-mode: both;
		opacity: 0;
		gap: 0.5px;
		min-height: 28px;
	}

	.grid-row:hover {
		background: linear-gradient(90deg, 
			rgba(0, 255, 255, 0.05), 
			rgba(255, 0, 255, 0.02), 
			transparent);
		box-shadow: inset 2px 0 0 var(--threat-color);
	}

	.data-cell {
		padding: 0.3rem 0.5rem;
		font-size: 0.55rem;
		color: rgba(255, 255, 255, 0.8);
		border-right: 1px solid rgba(255, 255, 255, 0.03);
		display: flex;
		align-items: center;
		line-height: 1.2;
	}

	.source-cell {
		font-weight: 600;
		color: #fff;
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}

	.source-indicator {
		width: 4px;
		height: 4px;
		border-radius: 50%;
		box-shadow: 0 0 6px currentColor;
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
		text-shadow: 0 0 4px #00ffff;
	}

	.coverage-cell {
		justify-content: center;
	}

	.coverage-bar {
		position: relative;
		width: 45px;
		height: 8px;
		background: rgba(0, 0, 0, 0.5);
		border-radius: 4px;
		border: 1px solid rgba(255, 255, 255, 0.1);
		overflow: hidden;
	}

	.coverage-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 1s ease-out;
		box-shadow: 0 0 8px currentColor;
	}

	.coverage-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 0.4rem;
		font-weight: 600;
		color: #fff;
		text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
	}

	.threat-cell {
		justify-content: center;
	}

	.threat-badge {
		padding: 0.15rem 0.35rem;
		border: 1px solid;
		border-radius: 2px;
		font-size: 0.4rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.02em;
		background: rgba(0, 0, 0, 0.4);
		text-shadow: 0 0 4px currentColor;
		animation: badgeGlow 3s ease-in-out infinite;
	}

	.action-cell {
		justify-content: center;
	}

	.drill-button {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 255, 255, 0.05));
		border: 1px solid #00ffff;
		border-radius: 3px;
		padding: 0.2rem 0.4rem;
		color: #00ffff;
		font-family: inherit;
		font-size: 0.45rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		text-transform: uppercase;
		display: flex;
		align-items: center;
		gap: 0.2rem;
		letter-spacing: 0.02em;
	}

	.drill-button:hover {
		background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 255, 255, 0.1));
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.4);
		transform: translateY(-1px);
		text-shadow: 0 0 4px #00ffff;
	}

	.drill-icon {
		font-size: 0.5rem;
		animation: iconSpark 2s ease-in-out infinite;
	}

	.drill-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 0, 255, 0.02));
		border: 1px solid #ff00ff;
		border-radius: 6px;
		overflow: hidden;
	}

	.drill-header {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(255, 0, 255, 0.05));
		border-bottom: 1px solid #ff00ff;
		padding: 0.5rem 0.8rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-shrink: 0;
	}

	.target-display {
		display: flex;
		align-items: center;
		gap: 0.8rem;
	}

	.target-badge {
		position: relative;
		padding: 0.4rem;
		border: 1px solid var(--threat-color);
		border-radius: 4px;
		background: rgba(0, 0, 0, 0.6);
		text-align: center;
	}

	.badge-ring {
		position: absolute;
		top: -1px;
		left: -1px;
		right: -1px;
		bottom: -1px;
		border: 1px solid var(--threat-color);
		border-radius: 4px;
		animation: ringRotate 4s linear infinite;
		opacity: 0.5;
	}

	.threat-level {
		font-size: 0.5rem;
		font-weight: 700;
		color: var(--threat-color);
		text-shadow: 0 0 6px var(--threat-color);
		z-index: 2;
		position: relative;
	}

	.target-info h3 {
		margin: 0;
		font-size: 0.8rem;
		color: #fff;
		text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
	}

	.target-stats {
		display: flex;
		gap: 0.8rem;
		margin-top: 0.2rem;
		font-size: 0.5rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.stat {
		color: #ff00ff;
		font-weight: 600;
		text-shadow: 0 0 4px #ff00ff;
	}

	.close-terminal {
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.2), rgba(255, 0, 102, 0.1));
		border: 1px solid #ff0066;
		border-radius: 50%;
		width: 26px;
		height: 26px;
		color: #ff0066;
		font-size: 0.8rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-terminal:hover {
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.3), rgba(255, 0, 102, 0.2));
		box-shadow: 0 0 15px rgba(255, 0, 102, 0.5);
		transform: rotate(90deg);
	}

	.close-icon {
		text-shadow: 0 0 6px #ff0066;
	}

	.scanning-hosts {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		color: #ff00ff;
	}

	.scan-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.2rem;
		width: 60px;
		height: 60px;
	}

	.scan-cell {
		background: #ff00ff;
		border-radius: 1px;
		animation: cellFlicker 1.5s ease-in-out infinite;
		opacity: 0.3;
	}

	.host-matrix {
		flex: 1;
		padding: 0.5rem;
		overflow-y: auto;
		max-height: calc(100% - 60px);
	}

	.host-matrix .grid-header {
		grid-template-columns: 2fr 0.8fr 0.8fr 0.8fr 0.4fr 0.4fr;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(255, 0, 255, 0.1));
		border-bottom: 1px solid #ff00ff;
		position: sticky;
		top: 0;
		z-index: 2;
	}

	.host-matrix .header-cell {
		color: #ff00ff;
		text-shadow: 0 0 4px #ff00ff;
	}

	.host-matrix .grid-row {
		grid-template-columns: 2fr 0.8fr 0.8fr 0.8fr 0.4fr 0.4fr;
		min-height: 24px;
	}

	.host-cell {
		color: #fff;
		font-weight: 600;
	}

	.status-chip {
		padding: 0.1rem 0.25rem;
		border-radius: 2px;
		font-size: 0.4rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.02em;
		border: 1px solid;
	}

	.status-chip.active {
		background: rgba(0, 255, 133, 0.1);
		color: #00ff85;
		border-color: #00ff85;
		text-shadow: 0 0 4px #00ff85;
	}

	.status-chip.inactive {
		background: rgba(255, 0, 102, 0.1);
		color: #ff0066;
		border-color: #ff0066;
		text-shadow: 0 0 4px #ff0066;
	}

	.interface-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.4rem 0;
		margin-top: 0.6rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		font-size: 0.45rem;
		color: rgba(255, 255, 255, 0.5);
		flex-shrink: 0;
	}

	.footer-stats {
		display: flex;
		gap: 1rem;
	}

	.neural-signature {
		color: #00ffff;
		font-weight: 600;
		letter-spacing: 0.02em;
		text-shadow: 0 0 4px #00ffff;
	}

	@keyframes iconPulse {
		0%, 100% { transform: scale(1); text-shadow: 0 0 10px #00ffff; }
		50% { transform: scale(1.05); text-shadow: 0 0 15px #00ffff; }
	}

	@keyframes scannerSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-1px); }
	}

	@keyframes ringSpin {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes textGlow {
		0%, 100% { text-shadow: 0 0 6px #00ffff; }
		50% { text-shadow: 0 0 10px #00ffff; }
	}

	@keyframes rowEntrance {
		0% { 
			opacity: 0; 
			transform: translateX(-10px);
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
		0%, 100% { box-shadow: 0 0 4px currentColor; }
		50% { box-shadow: 0 0 8px currentColor; }
	}

	@keyframes iconSpark {
		0%, 100% { text-shadow: 0 0 3px currentColor; }
		50% { text-shadow: 0 0 8px currentColor; }
	}

	@keyframes ringRotate {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes cellFlicker {
		0%, 100% { opacity: 0.3; background: #ff00ff; }
		50% { opacity: 1; background: #fff; }
	}
</style>