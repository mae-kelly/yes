<script>
	import { onMount } from 'svelte';
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/data_center_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			loading = false;
		}
	});

	$: sortedCenters = data.facility_intelligence ? 
		Object.entries(data.facility_intelligence).sort((a, b) => b[1] - a[1]) : [];
</script>

<div class="dc-panel">
	<header class="panel-header">
		<span class="header-icon">⬡</span>
		<h2>DATA CENTER MAPPING</h2>
		<p>First word analysis</p>
	</header>
	
	{#if loading}
		<div class="loading">Mapping data centers...</div>
	{:else}
		<div class="dc-grid">
			{#each sortedCenters as [center, count]}
				<div class="dc-card">
					<div class="dc-name">{center}</div>
					<div class="dc-count">{count}</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.dc-panel {
		background: rgba(0, 26, 0, 0.95);
		border: 1px solid #00ff41;
		border-radius: 8px;
		padding: 20px;
	}
	.dc-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 15px;
	}
	.dc-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-radius: 6px;
		padding: 15px;
		text-align: center;
	}
	.dc-name {
		color: #00ff41;
		margin-bottom: 10px;
		font-weight: bold;
	}
	.dc-count {
		font-size: 24px;
		color: #66ff66;
	}
</style>