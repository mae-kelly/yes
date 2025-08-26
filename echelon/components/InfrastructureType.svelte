// src/components/InfrastructureType.svelte
<script>
	import { onMount } from 'svelte';

	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/infrastructure_type');
			data = await response.json();
			loading = false;
		} catch (err) {
			loading = false;
		}
	});

	$: sortedTypes = data.infrastructure_matrix ? 
		Object.entries(data.infrastructure_matrix).sort((a, b) => b[1] - a[1]) : [];
</script>

<div class="infra-panel">
	<header class="panel-header">
		<span class="header-icon">⬢</span>
		<h2>INFRASTRUCTURE TYPES</h2>
	</header>
	
	{#if loading}
		<div class="loading">Analyzing infrastructure types...</div>
	{:else}
		<div class="grid-container">
			{#each sortedTypes as [type, count]}
				<div class="infra-card">
					<div class="type-name">{type}</div>
					<div class="type-count">{count}</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.infra-panel {
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
	}
	.header-icon {
		font-size: 24px;
		color: #00ff41;
	}
	.grid-container {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 15px;
	}
	.infra-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-radius: 6px;
		padding: 15px;
		text-align: center;
	}
	.type-name {
		color: #00ff41;
		margin-bottom: 10px;
	}
	.type-count {
		font-size: 20px;
		font-weight: bold;
		color: #66ff66;
	}
</style>

// src/components/RegionMetrics.svelte
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
			loading = false;
		}
	});

	function getRegionColor(region) {
		const colors = {
			'north america': '#00ff41',
			'emea': '#0099ff',
			'apac': '#ff6600',
			'latam': '#ff0099'
		};
		return colors[region.toLowerCase()] || '#666';
	}
</script>

<div class="region-panel">
	<header class="panel-header">
		<span class="header-icon">◉</span>
		<h2>REGIONAL DISTRIBUTION</h2>
	</header>
	
	{#if loading}
		<div class="loading">Mapping global regions...</div>
	{:else}
		<div class="region-grid">
			{#each Object.entries(data.global_surveillance || {}) as [region, count]}
				<div class="region-card" style="border-color: {getRegionColor(region)}">
					<div class="region-name" style="color: {getRegionColor(region)}">
						{region.toUpperCase()}
					</div>
					<div class="region-count">{count}</div>
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
	}
	.panel-header {
		display: flex;
		align-items: center;
		gap: 15px;
		margin-bottom: 20px;
	}
	.region-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 20px;
	}
	.region-card {
		background: rgba(0, 0, 0, 0.6);
		border: 2px solid;
		border-radius: 8px;
		padding: 20px;
		text-align: center;
	}
	.region-name {
		font-size: 14px;
		margin-bottom: 10px;
		font-weight: bold;
	}
	.region-count {
		font-size: 28px;
		font-weight: bold;
		color: #ffffff;
	}
</style>

// vite.config.js
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 3000,
    host: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})

// src/main.js
import App from './App.svelte'

const app = new App({
  target: document.getElementById('app')
})

export default app