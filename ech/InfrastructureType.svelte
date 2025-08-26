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
</script>

<div class="infra-panel">
	<header class="panel-header">
		<span class="header-icon">⬢</span>
		<h2>INFRASTRUCTURE TYPE ANALYSIS</h2>
		<p>Pipe-separated infrastructure classification</p>
	</header>
	
	{#if loading}
		<div class="loading">Analyzing infrastructure types...</div>
	{:else}
		<div class="infra-grid">
			{#each Object.entries(data.infrastructure_matrix || {}).slice(0, 16) as [type, count]}
				<div class="infra-card">
					<div class="infra-type">{type}</div>
					<div class="infra-count">{count.toLocaleString()}</div>
					<div class="infra-bar">
						<div class="bar-fill" style="width: {(count / Math.max(...Object.values(data.infrastructure_matrix || {}))) * 100}%"></div>
					</div>
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
		animation: hex-rotate 6s linear infinite;
	}
	@keyframes hex-rotate {
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
	.infra-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 15px;
	}
	.infra-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-radius: 6px;
		padding: 15px;
		transition: all 0.3s ease;
	}
	.infra-card:hover {
		border-color: #00ff41;
		transform: translateY(-2px);
		box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
	}
	.infra-type {
		color: #00ff41;
		font-weight: bold;
		margin-bottom: 10px;
		font-size: 12px;
	}
	.infra-count {
		font-size: 20px;
		font-weight: bold;
		color: #ffffff;
		margin-bottom: 10px;
	}
	.infra-bar {
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