# src/components/CioMetrics.svelte
<script>
	import { onMount } from 'svelte';
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/cio_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			loading = false;
		}
	});

	$: sortedCios = data.operative_intelligence ? 
		Object.entries(data.operative_intelligence).sort((a, b) => b[1] - a[1]) : [];
</script>

<div class="cio-panel">
	<header class="panel-header">
		<span class="header-icon">◓</span>
		<h2>CIO ANALYSIS</h2>
		<p>Pipe-separated words only (no numbers)</p>
	</header>
	
	{#if loading}
		<div class="loading">Analyzing CIO data...</div>
	{:else}
		<div class="cio-list">
			{#each sortedCios as [cio, count]}
				<div class="cio-row">
					<span class="cio-name">{cio}</span>
					<span class="cio-count">{count}</span>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.cio-panel {
		background: rgba(0, 26, 0, 0.95);
		border: 1px solid #00ff41;
		border-radius: 8px;
		padding: 20px;
	}
	.cio-list {
		max-height: 400px;
		overflow-y: auto;
	}
	.cio-row {
		display: flex;
		justify-content: space-between;
		padding: 8px 0;
		border-bottom: 1px solid #004400;
	}
	.cio-name {
		color: #00ff41;
	}
	.cio-count {
		color: #66ff66;
		font-weight: bold;
	}
</style>

---