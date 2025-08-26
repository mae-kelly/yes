<!-- CountryMetrics.svelte -->
<script>
	import { onMount } from 'svelte';
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/country_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			loading = false;
		}
	});

	$: sortedCountries = data.global_intelligence ? 
		Object.entries(data.global_intelligence).sort((a, b) => b[1] - a[1]) : [];

	function getCountryThreat(count, total) {
		const percentage = (count / total) * 100;
		if (percentage >= 25) return { level: 'CRITICAL', color: '#ff00ff' };
		if (percentage >= 15) return { level: 'HIGH', color: '#ff0066' };
		if (percentage >= 5) return { level: 'MEDIUM', color: '#ffaa00' };
		return { level: 'LOW', color: '#00ffff' };
	}

	function getCountryFlag(country) {
		// Simple flag representation using geometric shapes
		const flags = {
			'united states': '🇺🇸',
			'canada': '🇨🇦',
			'mexico': '🇲🇽',
			'united kingdom': '🇬🇧',
			'germany': '🇩🇪',
			'france': '🇫🇷',
			'japan': '🇯🇵',
			'china': '🇨🇳',
			'australia': '🇦🇺'
		};
		return flags[country.toLowerCase()] || '🏴';
	}
</script>

<div class="country-scan-matrix">
	<div class="matrix-header">
		<div class="scan-core">
			<div class="hexagon-scanner">
				<div class="hex-layers">
					<div class="hex-layer layer-1"></div>
					<div class="hex-layer layer-2"></div>
					<div class="hex-layer layer-3"></div>
				</div>
				<div class="scanner-center">⬟</div>
			</div>
			<div class="scan-info">
				<h2 class="scan-title">COUNTRY SCAN</h2>
				<p class="scan-subtitle">NORMALIZED COUNTRY DISTRIBUTION ANALYSIS</p>
			</div>
		</div>
		<div class="scan-stats">
			<div class="stat-display">
				<div class="stat-value">{data.total_countries || 0}</div>
				<div class="stat-label">COUNTRIES</div>
			</div>
			<div class="stat-display">
				<div class="stat-value">{Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0).toLocaleString()}</div>
				<div class="stat-label">TOTAL ASSETS</div>
			</div>
		</div>
	</div>

	{#if loading}
		<div class="scanning-world">
			<div class="world-scanner">
				<div class="scanner-grid">
					{#each Array(25) as _, i}
						<div class="scan-cell" style="animation-delay: {i * 0.05}s"></div>
					{/each}
				</div>
				<div class="scan-overlay">
					<div class="scan-line"></div>
				</div>
			</div>
			<div class="scan-text">ANALYZING GLOBAL COUNTRIES...</div>
		</div>
	{:else}
		<div class="countries-interface">
			<div class="world-grid">
				{#each sortedCountries.slice(0, 20) as [country, count], i}
					{@const total = Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0)}
					{@const threat = getCountryThreat(count, total)}
					{@const percentage = total > 0 ? (count / total * 100) : 0}
					<div class="country-node" style="--threat-color: {threat.color}; animation-delay: {i * 0.1}s">
						<div class="node-frame">
							<div class="frame-border"></div>
							<div class="node-header">
								<div class="country-flag">{getCountryFlag(country)}</div>
								<div class="threat-badge" style="background: {threat.color}20; color: {threat.color}; border-color: {threat.color}">
									{threat.level}
								</div>
							</div>
							
							<div class="country-info">
								<div class="country-name">{country.toUpperCase()}</div>
								<div class="asset-count">{count.toLocaleString()}</div>
								<div class="country-percentage">{percentage.toFixed(2)}%</div>
							</div>

							<div class="threat-meter">
								<div class="meter-track">
									<div class="meter-fill" style="width: {percentage}%; background: {threat.color};"></div>
								</div>
								<div class="meter-indicators">
									{#each Array(10) as _, j}
										<div class="indicator" style="opacity: {j < (percentage / 10) ? 1 : 0.3}"></div>
									{/each}
								</div>
							</div>

							<div class="connection-matrix">
								{#each Array(6) as _, k}
									<div class="connection-dot" style="animation-delay: {k * 0.2}s"></div>
								{/each}
							</div>

							<div class="node-glow"></div>
						</div>
					</div>
				{/each}
			</div>

			<div class="intelligence-panel">
				<div class="panel-header">
					<div class="header-symbol">◎</div>
					<h3>GLOBAL INTELLIGENCE</h3>
					<div class="activity-monitor">
						{#each Array(8) as _, i}
							<div class="activity-bar" style="height: {Math.random() * 100}%; animation-delay: {i * 0.1}s"></div>
						{/each}
					</div>
				</div>
				
				<div class="intelligence-grid">
					<div class="intel-section">
						<div class="section-title">TOP TARGETS</div>
						<div class="target-list">
							{#each sortedCountries.slice(0, 5) as [country, count], i}
								{@const total = Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0)}
								{@const percentage = total > 0 ? (count / total * 100) : 0}
								<div class="target-item" style="animation-delay: {i * 0.1}s">
									<div class="target-rank">#{i + 1}</div>
									<div class="target-flag">{getCountryFlag(country)}</div>
									<div class="target-name">{country.toUpperCase()}</div>
									<div class="target-assets">{count.toLocaleString()}</div>
									<div class="target-percentage">{percentage.toFixed(1)}%</div>
								</div>
							{/each}
						</div>
					</div>

					<div class="intel-section">
						<div class="section-title">THREAT LEVELS</div>
						<div class="threat-distribution">
							{@const total = Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0)}
							{@const threats = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 }}
							{#each sortedCountries as [country, count]}
								{@const threat = getCountryThreat(count, total)}
								{threats[threat.level]++}
							{/each}
							{#each Object.entries(threats) as [level, levelCount]}
								{@const levelColor = level === 'CRITICAL' ? '#ff00ff' : level === 'HIGH' ? '#ff0066' : level === 'MEDIUM' ? '#ffaa00' : '#00ffff'}
								<div class="threat-stat">
									<div class="threat-indicator" style="background: {levelColor}"></div>
									<div class="threat-name">{level}</div>
									<div class="threat-count">{levelCount}</div>
								</div>
							{/each}
						</div>
					</div>

					<div class="intel-section">
						<div class="section-title">COVERAGE ANALYSIS</div>
						<div class="coverage-stats">
							<div class="coverage-item">
								<div class="coverage-label">TOTAL COUNTRIES</div>
								<div class="coverage-value">{sortedCountries.length}</div>
							</div>
							<div class="coverage-item">
								<div class="coverage-label">PRIMARY TARGET</div>
								<div class="coverage-value">{sortedCountries.length > 0 ? sortedCountries[0][0].toUpperCase() : 'N/A'}</div>
							</div>
							<div class="coverage-item">
								<div class="coverage-label">CONCENTRATION</div>
								<div class="coverage-value">
									{sortedCountries.length > 0 ? 
										((sortedCountries[0][1] / Object.values(data.global_intelligence || {}).reduce((a, b) => a + b, 0)) * 100).toFixed(1) : 0}%
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	{/if}

	<div class="interface-footer">
		<div class="footer-line"></div>
		<div class="protocol-notice">
			⬟ COUNTRY SCAN // GLOBAL DISTRIBUTION PROTOCOL ACTIVE
		</div>
	</div>
</div>

<style>
	.country-scan-matrix {
		width: 100%;
		height: 100%;
		font-family: 'Orbitron', 'Exo 2', monospace;
		color: #fff;
		display: flex;
		flex-direction: column;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.matrix-header {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(255, 0, 255, 0.05) 50%,
			rgba(0, 0, 0, 0.8) 100%);
		border: 2px solid #ff00ff;
		border-radius: 12px;
		padding: 1.5rem 2rem;
		margin-bottom: 1.5rem;
		backdrop-filter: blur(20px);
		box-shadow: 0 0 40px rgba(255, 0, 255, 0.2);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.scan-core {
		display: flex;
		align-items: center;
		gap: 2rem;
	}

	.hexagon-scanner {
		position: relative;
		width: 100px;
		height: 100px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.hex-layers {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.hex-layer {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		border: 2px solid;
		clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
		animation: hexRotate 8s linear infinite;
	}

	.layer-1 {
		width: 100px;
		height: 100px;
		border-color: #ff00ff;
		opacity: 0.8;
	}

	.layer-2 {
		width: 75px;
		height: 75px;
		border-color: #cc00cc;
		opacity: 0.6;
		animation-direction: reverse;
		animation-duration: 6s;
	}

	.layer-3 {
		width: 50px;
		height: 50px;
		border-color: #990099;
		animation-duration: 4s;
	}

	.scanner-center {
		position: relative;
		z-index: 3;
		font-size: 2.5rem;
		color: #ff00ff;
		text-shadow: 0 0 25px #ff00ff;
		animation: scannerPulse 3s ease-in-out infinite;
	}

	.scan-info {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.scan-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: #fff;
		margin: 0;
		text-shadow: 0 0 15px rgba(255, 0, 255, 0.5);
		letter-spacing: 0.1em;
	}

	.scan-subtitle {
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.6);
		margin: 0;
		font-weight: 300;
	}

	.scan-stats {
		display: flex;
		gap: 2rem;
	}

	.stat-display {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 0, 255, 0.03));
		border: 2px solid rgba(255, 0, 255, 0.3);
		border-radius: 8px;
		padding: 1rem 1.5rem;
		text-align: center;
		backdrop-filter: blur(10px);
	}

	.stat-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #ff00ff;
		text-shadow: 0 0 10px #ff00ff;
		margin-bottom: 0.3rem;
	}

	.stat-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.1em;
	}

	.scanning-world {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.world-scanner {
		position: relative;
		width: 250px;
		height: 250px;
		background: radial-gradient(circle, rgba(255, 0, 255, 0.1), transparent);
		border: 3px solid #ff00ff;
		border-radius: 8px;
		overflow: hidden;
	}

	.scanner-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 2px;
		width: 100%;
		height: 100%;
		padding: 10px;
	}

	.scan-cell {
		background: #ff00ff;
		border-radius: 2px;
		animation: cellScan 2s ease-in-out infinite;
		opacity: 0.3;
	}

	.scan-overlay {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}

	.scan-line {
		position: absolute;
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, #ff00ff, transparent);
		animation: scanLineSweep 3s linear infinite;
		box-shadow: 0 0 10px #ff00ff;
	}

	.scan-text {
		color: #ff00ff;
		font-size: 1.1rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-shadow: 0 0 15px #ff00ff;
	}

	.countries-interface {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.world-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.country-node {
		position: relative;
		animation: nodeEntrance 0.8s ease-out;
		animation-fill-mode: both;
		opacity: 0;
	}

	.node-frame {
		position: relative;
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(255, 255, 255, 0.02) 100%);
		border: 2px solid var(--threat-color);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
		transition: all 0.3s ease;
		overflow: hidden;
	}

	.country-node:hover .node-frame {
		transform: translateY(-5px) scale(1.02);
		box-shadow: 0 15px 40px rgba(0, 0, 0, 0.6), 0 0 30px var(--threat-color);
	}

	.frame-border {
		position: absolute;
		top: -2px;
		left: -2px;
		right: -2px;
		bottom: -2px;
		background: linear-gradient(45deg, var(--threat-color), transparent, var(--threat-color));
		opacity: 0;
		transition: opacity 0.3s ease;
		border-radius: 12px;
		z-index: -1;
		animation: borderPulse 3s ease-in-out infinite;
	}

	.country-node:hover .frame-border {
		opacity: 0.2;
	}

	.node-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.country-flag {
		font-size: 2rem;
		filter: brightness(1.2) saturate(1.5);
	}

	.threat-badge {
		padding: 0.3rem 0.8rem;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 700;
		letter-spacing: 0.05em;
		border: 1px solid;
		text-shadow: 0 0 8px currentColor;
		animation: badgeGlow 2s ease-in-out infinite;
	}

	.country-info {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-bottom: 1rem;
		text-align: center;
	}

	.country-name {
		font-size: 1rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
	}

	.asset-count {
		font-size: 2rem;
		font-weight: 700;
		color: var(--threat-color);
		text-shadow: 0 0 15px var(--threat-color);
	}

	.country-percentage {
		font-size: 0.9rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.8);
	}

	.threat-meter {
		margin-bottom: 1rem;
	}

	.meter-track {
		height: 8px;
		background: rgba(0, 0, 0, 0.6);
		border-radius: 4px;
		overflow: hidden;
		border: 1px solid rgba(255, 255, 255, 0.1);
		position: relative;
		margin-bottom: 0.5rem;
	}

	.meter-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 2s cubic-bezier(0.4, 0, 0.2, 1);
		box-shadow: 0 0 15px currentColor;
		position: relative;
		overflow: hidden;
	}

	.meter-fill::after {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 100%;
		height: 100%;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(255, 255, 255, 0.4), 
			transparent);
		animation: meterSweep 3s linear infinite;
	}

	.meter-indicators {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.indicator {
		width: 4px;
		height: 8px;
		background: var(--threat-color);
		border-radius: 2px;
		transition: opacity 0.3s ease;
		box-shadow: 0 0 6px var(--threat-color);
	}

	.connection-matrix {
		display: flex;
		justify-content: center;
		gap: 0.5rem;
		align-items: center;
	}

	.connection-dot {
		width: 6px;
		height: 6px;
		background: var(--threat-color);
		border-radius: 50%;
		animation: dotPulse 2s ease-in-out infinite;
		box-shadow: 0 0 6px var(--threat-color);
		opacity: 0.7;
	}

	.node-glow {
		position: absolute;
		top: -4px;
		left: -4px;
		right: -4px;
		bottom: -4px;
		background: radial-gradient(circle, var(--threat-color), transparent);
		opacity: 0;
		transition: opacity 0.3s ease;
		border-radius: 12px;
		z-index: -2;
	}

	.country-node:hover .node-glow {
		opacity: 0.1;
	}

	.intelligence-panel {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 0, 255, 0.02));
		border: 2px solid rgba(255, 0, 255, 0.3);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
	}

	.panel-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1.5rem;
	}

	.header-symbol {
		font-size: 1.5rem;
		color: #ff00ff;
		text-shadow: 0 0 15px #ff00ff;
		animation: symbolFloat 3s ease-in-out infinite;
	}

	.panel-header h3 {
		flex: 1;
		margin: 0 0 0 1rem;
		font-size: 1.1rem;
		font-weight: 700;
		color: #ff00ff;
		letter-spacing: 0.05em;
	}

	.activity-monitor {
		display: flex;
		gap: 0.2rem;
		align-items: flex-end;
	}

	.activity-bar {
		width: 4px;
		background: #ff00ff;
		border-radius: 2px;
		animation: activityPulse 1.5s ease-in-out infinite;
		box-shadow: 0 0 6px #ff00ff;
	}

	.intelligence-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1.5rem;
	}

	.intel-section {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		padding: 1rem;
		backdrop-filter: blur(10px);
	}

	.section-title {
		font-size: 0.8rem;
		font-weight: 700;
		color: #ff00ff;
		margin-bottom: 1rem;
		letter-spacing: 0.05em;
		text-shadow: 0 0 8px #ff00ff;
		border-bottom: 1px solid rgba(255, 0, 255, 0.2);
		padding-bottom: 0.5rem;
	}

	.target-list {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.target-item {
		display: grid;
		grid-template-columns: auto auto 1fr auto auto;
		gap: 0.8rem;
		align-items: center;
		padding: 0.5rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.01));
		border-radius: 4px;
		animation: targetEntrance 0.6s ease-out;
		animation-fill-mode: both;
	}

	.target-rank {
		font-size: 0.8rem;
		font-weight: 700;
		color: #ff00ff;
		text-shadow: 0 0 8px #ff00ff;
	}

	.target-flag {
		font-size: 1.2rem;
	}

	.target-name {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.9);
		font-weight: 600;
	}

	.target-assets {
		font-size: 0.9rem;
		font-weight: 700;
		color: #fff;
		text-align: right;
	}

	.target-percentage {
		font-size: 0.8rem;
		font-weight: 600;
		color: #ff00ff;
		text-shadow: 0 0 8px #ff00ff;
	}

	.threat-distribution {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.threat-stat {
		display: grid;
		grid-template-columns: auto 1fr auto;
		gap: 0.8rem;
		align-items: center;
		padding: 0.5rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.01));
		border-radius: 4px;
	}

	.threat-indicator {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		animation: threatPulse 2s ease-in-out infinite;
		box-shadow: 0 0 8px currentColor;
	}

	.threat-name {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.8);
		font-weight: 600;
	}

	.threat-count {
		font-size: 0.9rem;
		font-weight: 700;
		color: #fff;
		text-align: right;
	}

	.coverage-stats {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.coverage-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 255, 255, 0.01));
		border-radius: 4px;
	}

	.coverage-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
	}

	.coverage-value {
		font-size: 0.9rem;
		font-weight: 700;
		color: #ff00ff;
		text-shadow: 0 0 8px #ff00ff;
	}

	.interface-footer {
		padding-top: 1rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		text-align: center;
	}

	.footer-line {
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(255, 0, 255, 0.6), 
			transparent);
		margin-bottom: 1rem;
	}

	.protocol-notice {
		font-size: 0.7rem;
		color: #ff00ff;
		font-weight: 600;
		letter-spacing: 0.05em;
		text-shadow: 0 0 8px #ff00ff;
	}

	@keyframes hexRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes scannerPulse {
		0%, 100% { 
			text-shadow: 0 0 25px #ff00ff; 
			transform: scale(1);
		}
		50% { 
			text-shadow: 0 0 35px #ff00ff; 
			transform: scale(1.05);
		}
	}

	@keyframes cellScan {
		0%, 100% { opacity: 0.3; background: #ff00ff; }
		50% { opacity: 1; background: #fff; }
	}

	@keyframes scanLineSweep {
		0% { top: 0; }
		100% { top: 100%; }
	}

	@keyframes nodeEntrance {
		0% { 
			opacity: 0; 
			transform: translateY(30px) scale(0.9);
		}
		100% { 
			opacity: 1; 
			transform: translateY(0) scale(1);
		}
	}

	@keyframes borderPulse {
		0%, 100% { opacity: 0.1; }
		50% { opacity: 0.3; }
	}

	@keyframes badgeGlow {
		0%, 100% { box-shadow: 0 0 8px currentColor; }
		50% { box-shadow: 0 0 16px currentColor; }
	}

	@keyframes meterSweep {
		0% { left: -100%; }
		100% { left: 100%; }
	}

	@keyframes dotPulse {
		0%, 100% { opacity: 0.7; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.2); }
	}

	@keyframes symbolFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-3px); }
	}

	@keyframes activityPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	@keyframes targetEntrance {
		0% { 
			opacity: 0; 
			transform: translateX(-20px);
		}
		100% { 
			opacity: 1; 
			transform: translateX(0);
		}
	}

	@keyframes threatPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.2); }
	}

	@media (max-width: 1200px) {
		.matrix-header {
			flex-direction: column;
			gap: 1.5rem;
			text-align: center;
		}

		.world-grid {
			grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		}

		.intelligence-grid {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 768px) {
		.scan-core {
			flex-direction: column;
			gap: 1rem;
		}

		.scan-stats {
			flex-direction: column;
			gap: 1rem;
		}

		.target-item {
			grid-template-columns: 1fr;
			gap: 0.5rem;
			text-align: center;
		}

		.threat-stat, .coverage-item {
			grid-template-columns: 1fr;
			text-align: center;
			gap: 0.5rem;
		}
	}
</style>