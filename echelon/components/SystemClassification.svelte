# src/components/SystemClassification.svelte
<script>
	import { onMount } from 'svelte';
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/system_classification_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			loading = false;
		}
	});

	$: sortedSystems = data.system_matrix ? 
		Object.entries(data.system_matrix).sort((a, b) => b[1] - a[1]) : [];
</script>

<div class="system-panel">
	<header class="panel-header">
		<span class="header-icon">◑</span>
		<h2>SYSTEM TAXONOMY</h2>
		<p>Pipe-separated system classifications</p>
	</header>
	
	{#if loading}
		<div class="loading">Classifying systems...</div>
	{:else}
		<div class="system-list">
			{#each sortedSystems.slice(0, 25) as [system, count]}
				<div class="system-row">
					<span class="system-name">{system}</span>
					<span class="system-count">{count}</span>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.system-panel {
		background: rgba(0, 26, 0, 0.95);
		border: 1px solid #00ff41;
		border-radius: 8px;
		padding: 20px;
	}
	.system-list {
		max-height: 600px;
		overflow-y: auto;
	}
	.system-row {
		display: flex;
		justify-content: space-between;
		padding: 8px 0;
		border-bottom: 1px solid #004400;
	}
	.system-name {
		color: #00ff41;
		flex: 1;
	}
	.system-count {
		color: #66ff66;
		font-weight: bold;
		min-width: 40px;
		text-align: right;
	}
</style>

---

# src/components/BusinessUnitMetrics.svelte
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
			loading = false;
		}
	});

	$: sortedUnits = data.business_intelligence ? 
		Object.entries(data.business_intelligence).sort((a, b) => b[1] - a[1]) : [];
</script>

<div class="bu-panel">
	<header class="panel-header">
		<span class="header-icon">◒</span>
		<h2>BUSINESS UNITS</h2>
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
	.bu-list {
		max-height: 500px;
		overflow-y: auto;
	}
	.bu-row {
		display: flex;
		justify-content: space-between;
		padding: 10px;
		margin-bottom: 5px;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-radius: 4px;
	}
	.bu-name {
		color: #00ff41;
		flex: 1;
	}
	.bu-count {
		color: #66ff66;
		font-weight: bold;
	}
</style>

---