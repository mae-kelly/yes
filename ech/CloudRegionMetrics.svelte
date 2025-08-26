<script>
	import { onMount } from 'svelte';
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/cloud_region_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			loading = false;
		}
	});
</script>

<div class="cloud-panel">
	<header class="panel-header">
		<span class="header-icon">◯</span>
		<h2>CLOUD REGIONS</h2>
		<p>Unique cloud region mapping</p>
	</header>
	
	{#if loading}
		<div class="loading">Scanning cloud regions...</div>
	{:else}
		<div class="cloud-grid">
			{#each data.cloud_matrix || [] as region}
				<div class="cloud-region">
					<span class="region-code">{region}</span>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.cloud-panel {
		background: rgba(0, 26, 0, 0.95);
		border: 1px solid #00ff41;
		border-radius: 8px;
		padding: 20px;
	}
	.cloud-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 10px;
	}
	.cloud-region {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-radius: 4px;
		padding: 10px;
		text-align: center;
	}
	.region-code {
		color: #00ff41;
		font-size: 12px;
		font-family: monospace;
	}
</style>