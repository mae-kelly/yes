<script>
	import { onMount } from 'svelte';
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/region_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Region metrics error:', err);
			loading = false;
		}
	});

	$: totalCoverage = data.total_coverage || 0;
	$: sortedRegions = data.global_surveillance ? 
		Object.entries(data.global_surveillance).sort((a, b) => b[1] - a[1]) : [];
</script>

<div class="region-panel">
	<header class="panel-header">
		<span class="header-icon">◉</span>
		<h2>GLOBAL REGION ANALYSIS</h2>
		<p>Normalized regional distribution</p>
	</header>
	
	{#if loading}
		<div class="loading">Analyzing global regions...</div>
	{:else}
		<div class="region-overview">
			<div class="coverage-total">
				<span class="total-value">{totalCoverage.toLocaleString()}</span>
				<span class="total-label">TOTAL COVERAGE</span>
			</div>
		</div>
		
		<div class="region-breakdown">
			{#each sortedRegions as [region, count]}
				{@const percentage = totalCoverage > 0 ? (count / totalCoverage * 100) : 0}
				<div class="region-card">
					<div class="region-name">{region.toUpperCase()}</div>
					<div class="region-stats">
						<div class="region-count">{count.toLocaleString()}</div>
						<div class="region-percentage">{percentage.toFixed(1)}%</div>
					</div>
					<div class="region-bar">
						<div class="bar-fill" style="width: {percentage}%"></div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.region-panel {
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
		animation: region-pulse 3s ease-in-out infinite;
	}
	
	@keyframes region-pulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.1); }
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
	}
	
	.loading {
		text-align: center;
		padding: 40px;
		color: #ffaa00;
	}
	
	.region-overview {
		margin-bottom: 25px;
		text-align: center;
	}
	
	.coverage-total {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-radius: 6px;
		padding: 20px;
		display: inline-block;
	}
	
	.total-value {
		display: block;
		font-size: 28px;
		font-weight: bold;
		color: #00ff41;
		margin-bottom: 5px;
	}
	
	.total-label {
		font-size: 12px;
		color: #66ff66;
		letter-spacing: 1px;
	}
	
	.region-breakdown {
		display: flex;
		flex-direction: column;
		gap: 15px;
	}
	
	.region-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-radius: 6px;
		padding: 15px;
		transition: all 0.3s ease;
	}
	
	.region-card:hover {
		border-color: #00ff41;
		box-shadow: 0 0 15px rgba(0, 255, 65, 0.3);
	}
	
	.region-name {
		color: #00ff41;
		font-weight: bold;
		margin-bottom: 10px;
		font-size: 14px;
	}
	
	.region-stats {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 10px;
	}
	
	.region-count {
		font-size: 18px;
		font-weight: bold;
		color: #ffffff;
	}
	
	.region-percentage {
		font-size: 12px;
		color: #66ff66;
	}
	
	.region-bar {
		height: 6px;
		background: #002200;
		border-radius: 3px;
		overflow: hidden;
	}
	
	.bar-fill {
		height: 100%;
		background: linear-gradient(90deg, #004400, #00ff41);
		border-radius: 3px;
		transition: width 1s ease-out;
	}
</style>