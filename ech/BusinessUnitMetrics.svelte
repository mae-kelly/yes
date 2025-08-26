<script>
	import { onMount } from 'svelte';
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/business_unit_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			console.error('Business unit metrics error:', err);
			loading = false;
		}
	});

	$: sortedUnits = data.business_intelligence ? 
		Object.entries(data.business_intelligence).sort((a, b) => b[1] - a[1]) : [];
</script>

<div class="bu-panel">
	<header class="panel-header">
		<span class="header-icon">◒</span>
		<h2>BUSINESS UNIT ANALYSIS</h2>
		<p>Comma and pipe-separated analysis</p>
	</header>
	
	{#if loading}
		<div class="loading">Analyzing business units...</div>
	{:else}
		<div class="bu-list">
			{#each sortedUnits.slice(0, 20) as [unit, count]}
				<div class="bu-row">
					<span class="bu-name">{unit}</span>
					<span class="bu-count">{count}</span>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.bu-panel {
		background: rgba(0, 26, 0, 0.95);
		border: 1px solid #00ff41;
		border-radius: 8px;
		padding: 20px;
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
		animation: bu-rotate 8s linear infinite;
	}
	
	@keyframes bu-rotate {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
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
	
	.bu-list {
		max-height: 500px;
		overflow-y: auto;
	}
	
	.bu-row {
		display: flex;
		justify-content: space-between;
		padding: 12px;
		margin-bottom: 8px;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-radius: 4px;
		transition: all 0.3s ease;
	}
	
	.bu-row:hover {
		border-color: #00ff41;
		background: rgba(0, 255, 65, 0.1);
	}
	
	.bu-name {
		color: #00ff41;
		flex: 1;
		font-weight: bold;
	}
	
	.bu-count {
		color: #66ff66;
		font-weight: bold;
		font-size: 16px;
	}
</style>