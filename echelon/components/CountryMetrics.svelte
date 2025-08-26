# src/components/CountryMetrics.svelte
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
</script>

<div class="country-panel">
	<header class="panel-header">
		<span class="header-icon">⬟</span>
		<h2>COUNTRY ANALYSIS</h2>
		<p>Normalized country distribution</p>
	</header>
	
	{#if loading}
		<div class="loading">Analyzing global countries...</div>
	{:else}
		<div class="country-list">
			{#each sortedCountries.slice(0, 20) as [country, count]}
				<div class="country-row">
					<span class="country-name">{country.toUpperCase()}</span>
					<span class="country-count">{count}</span>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.country-panel {
		background: rgba(0, 26, 0, 0.95);
		border: 1px solid #00ff41;
		border-radius: 8px;
		padding: 20px;
	}
	.panel-header {
		margin-bottom: 20px;
	}
	.panel-header h2 {
		color: #00ff41;
		margin: 5px 0;
	}
	.country-list {
		max-height: 500px;
		overflow-y: auto;
	}
	.country-row {
		display: flex;
		justify-content: space-between;
		padding: 8px 0;
		border-bottom: 1px solid #004400;
	}
	.country-name {
		color: #00ff41;
	}
	.country-count {
		color: #66ff66;
		font-weight: bold;
	}
</style>
