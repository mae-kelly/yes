<script>
	import { onMount } from 'svelte';
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/class_metrics');
			data = await response.json();
			loading = false;
		} catch (err) {
			loading = false;
		}
	});
</script>

<div class="class-panel">
	<header class="panel-header">
		<span class="header-icon">◐</span>
		<h2>CLASS ANALYSIS</h2>
		<p>Keyword "class" + number extraction</p>
	</header>
	
	{#if loading}
		<div class="loading">Analyzing class numbers...</div>
	{:else}
		<div class="class-list">
			{#each Object.entries(data.classification_matrix || {}) as [className, count]}
				<div class="class-row">
					<span class="class-name">{className.toUpperCase()}</span>
					<span class="class-count">{count}</span>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.class-panel {
		background: rgba(0, 26, 0, 0.95);
		border: 1px solid #00ff41;
		border-radius: 8px;
		padding: 20px;
	}
	.class-list {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	.class-row {
		display: flex;
		justify-content: space-between;
		padding: 10px;
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-radius: 4px;
	}
	.class-name {
		color: #00ff41;
	}
	.class-count {
		color: #66ff66;
		font-weight: bold;
	}
</style>