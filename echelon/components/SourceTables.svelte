<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let error = null;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/source_tables');
			data = await response.json();
			loading = false;
		} catch (err) {
			error = 'SOURCE INTELLIGENCE COMPROMISED';
			loading = false;
		}
	});

	function getRiskLevel(percentage) {
		if (percentage >= 15) return { level: 'CRITICAL', color: '#ff0000' };
		if (percentage >= 10) return { level: 'HIGH', color: '#ff6600' };
		if (percentage >= 5) return { level: 'MEDIUM', color: '#ffaa00' };
		return { level: 'LOW', color: '#00ff41' };
	}
</script>

<div class="source-panel">
	<header class="panel-header">
		<span class="header-icon">◈</span>
		<h2>SOURCE TABLES INTELLIGENCE</h2>
		<p>Comma-separated frequency analysis</p>
	</header>
	
	{#if loading}
		<div class="loading">Analyzing source tables...</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else}
		<div class="source-grid">
			{#each Object.entries(data.data || {}).slice(0, 20) as [source, frequency]}
				{@const percentage = data.total_mentions ? (frequency / data.total_mentions * 100) : 0}
				{@const risk = getRiskLevel(percentage)}
				<div class="source-card" style="border-left-color: {risk.color}">
					<div class="source-name">{source}</div>
					<div class="source-stats">
						<div class="frequency">{frequency.toLocaleString()}</div>
						<div class="percentage">{percentage.toFixed(1)}%</div>
						<div class="risk-badge" style="background: {risk.color}">{risk.level}</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.source-panel {
		background: rgba(0, 26, 0, 0.95);
		border: 1px solid #00ff41;
		border-radius: 8px;
		padding: 20px;
		box-shadow: 0 0 20px rgba(0, 255, 65, 0.3);
	}
	.panel-header {
		display: flex;
		align-items: center;
		gap: 15px;
		margin-bottom: 20px;
		border-bottom: 1px solid #004400;
		padding-bottom: 15px;
	}
	.header-icon {
		font-size: 24px;
		color: #00ff41;
		animation: pulse 2s infinite;
	}
	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}
	.panel-header h2 {
		margin: 0;
		color: #00ff41;
		font-size: 16px;
		letter-spacing: 1px;
	}
	.panel-header p {
		margin: 2px 0 0 0;
		color: #66ff66;
		font-size: 11px;
		opacity: 0.8;
	}
	.loading, .error {
		text-align: center;
		padding: 40px;
		color: #ffaa00;
		font-size: 14px;
	}
	.source-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 15px;
	}
	.source-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-left: 4px solid;
		border-radius: 6px;
		padding: 15px;
		transition: all 0.3s ease;
		cursor: pointer;
	}
	.source-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 5px 20px rgba(0, 0, 0, 0.5);
		border-color: #00ff41;
	}
	.source-name {
		color: #00ff41;
		font-weight: bold;
		margin-bottom: 10px;
		font-size: 13px;
		word-break: break-word;
	}
	.source-stats {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 10px;
	}
	.frequency {
		color: #ffffff;
		font-weight: bold;
		font-size: 16px;
	}
	.percentage {
		color: #66ff66;
		font-size: 12px;
	}
	.risk-badge {
		padding: 4px 8px;
		border-radius: 4px;
		font-size: 8px;
		font-weight: bold;
		color: #000;
		letter-spacing: 1px;
	}
</style>

---

// src/components/DomainMetrics.svelte
<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/domain_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			loading = false;
		}
	});
</script>

<div class="domain-panel">
	<header class="panel-header">
		<span class="header-icon">◆</span>
		<h2>1DC vs FEAD DOMAIN ANALYSIS</h2>
		<p>Pipe-separated domain classification (one per row logic)</p>
	</header>
	
	{#if loading}
		<div class="loading">Analyzing domain warfare...</div>
	{:else}
		<div class="domain-battle">
			<div class="combatant onedc">
				<div class="combatant-name">1DC DOMAINS</div>
				<div class="combatant-count">{data.domain_analysis ? data.domain_analysis['1dc'] || 0 : 0}</div>
				<div class="combatant-percentage">
					{data.domain_distribution ? data.domain_distribution['1dc_percentage'].toFixed(1) : 0}%
				</div>
			</div>
			
			<div class="vs-indicator">VS</div>
			
			<div class="combatant fead">
				<div class="combatant-name">FEAD DOMAINS</div>
				<div class="combatant-count">{data.domain_analysis ? data.domain_analysis['fead'] || 0 : 0}</div>
				<div class="combatant-percentage">
					{data.domain_distribution ? data.domain_distribution['fead_percentage'].toFixed(1) : 0}%
				</div>
			</div>
		</div>
		
		<div class="battle-result">
			{@const onedc = data.domain_analysis ? data.domain_analysis['1dc'] || 0 : 0}
			{@const fead = data.domain_analysis ? data.domain_analysis['fead'] || 0 : 0}
			<div class="winner">
				{onedc > fead ? '1DC DOMINANCE' : fead > onedc ? 'FEAD DOMINANCE' : 'BALANCED WARFARE'}
			</div>
		</div>
	{/if}
</div>

<style>
	.domain-panel {
		background: rgba(13, 0, 26, 0.95);
		border: 1px solid #6600cc;
		border-radius: 8px;
		padding: 20px;
		box-shadow: 0 0 20px rgba(102, 0, 204, 0.3);
	}
	.panel-header {
		display: flex;
		align-items: center;
		gap: 15px;
		margin-bottom: 20px;
		border-bottom: 1px solid #440066;
		padding-bottom: 15px;
	}
	.header-icon {
		font-size: 24px;
		color: #6600cc;
		animation: diamond-spin 8s linear infinite;
	}
	@keyframes diamond-spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	.panel-header h2 {
		margin: 0;
		color: #6600cc;
		font-size: 16px;
		letter-spacing: 1px;
	}
	.panel-header p {
		margin: 2px 0 0 0;
		color: #9966ff;
		font-size: 11px;
	}
	.loading {
		text-align: center;
		padding: 40px;
		color: #9966ff;
	}
	.domain-battle {
		display: grid;
		grid-template-columns: 1fr auto 1fr;
		gap: 30px;
		align-items: center;
		margin-bottom: 25px;
	}
	.combatant {
		background: rgba(0, 0, 0, 0.6);
		border: 2px solid;
		border-radius: 8px;
		padding: 25px;
		text-align: center;
	}
	.combatant.onedc {
		border-color: #00ff41;
	}
	.combatant.fead {
		border-color: #0099ff;
	}
	.combatant-name {
		font-size: 14px;
		font-weight: bold;
		margin-bottom: 15px;
		letter-spacing: 1px;
	}
	.onedc .combatant-name {
		color: #00ff41;
	}
	.fead .combatant-name {
		color: #0099ff;
	}
	.combatant-count {
		font-size: 28px;
		font-weight: bold;
		margin-bottom: 10px;
		color: #ffffff;
	}
	.combatant-percentage {
		font-size: 16px;
		color: #66ff66;
	}
	.vs-indicator {
		font-size: 20px;
		font-weight: bold;
		color: #ff6600;
		text-align: center;
		animation: vs-pulse 2s infinite;
	}
	@keyframes vs-pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}
	.battle-result {
		text-align: center;
		background: rgba(0, 0, 0, 0.8);
		border: 1px solid #440066;
		border-radius: 6px;
		padding: 20px;
	}
	.winner {
		font-size: 18px;
		font-weight: bold;
		color: #6600cc;
		letter-spacing: 2px;
		animation: winner-glow 2s ease-in-out infinite alternate;
	}
	@keyframes winner-glow {
		from { text-shadow: 0 0 10px #6600cc; }
		to { text-shadow: 0 0 25px #6600cc; }
	}
</style>