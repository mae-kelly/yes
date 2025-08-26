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