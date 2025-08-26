<!-- CloudRegionMetrics.svelte -->
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

<div class="cloud-matrix-hub">
	<div class="matrix-header">
		<div class="cloud-core">
			<div class="cloud-ring">◯</div>
		</div>
		<div class="matrix-info">
			<h2>CLOUD MATRIX</h2>
			<p>UNIQUE CLOUD REGION MAPPING</p>
		</div>
	</div>

	{#if loading}
		<div class="cloud-scan">
			<div class="scanning-cloud">☁️</div>
			<p>SCANNING CLOUD REGIONS...</p>
		</div>
	{:else}
		<div class="cloud-grid">
			{#each data.cloud_matrix || [] as region, i}
				<div class="cloud-region" style="animation-delay: {i * 0.05}s">
					<div class="region-frame">
						<div class="region-code">{region}</div>
						<div class="region-status">ACTIVE</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.cloud-matrix-hub {
		font-family: 'Orbitron', monospace;
		color: #fff;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.matrix-header {
		display: flex;
		align-items: center;
		gap: 2rem;
		padding: 1.5rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 255, 255, 0.05));
		border: 2px solid #00ffff;
		border-radius: 12px;
		margin-bottom: 1.5rem;
	}

	.cloud-core {
		width: 80px;
		height: 80px;
		background: radial-gradient(circle, rgba(0, 255, 255, 0.2), transparent);
		border: 3px solid #00ffff;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		color: #00ffff;
		text-shadow: 0 0 20px #00ffff;
		animation: cloudPulse 3s ease-in-out infinite;
	}

	.matrix-info h2 {
		margin: 0;
		font-size: 1.5rem;
		color: #fff;
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
	}

	.matrix-info p {
		margin: 0.3rem 0 0 0;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.cloud-scan {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2rem;
		padding: 3rem;
	}

	.scanning-cloud {
		font-size: 4rem;
		animation: cloudFloat 3s ease-in-out infinite;
		filter: hue-rotate(180deg) saturate(2);
	}

	.cloud-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}

	.cloud-region {
		animation: regionEntrance 0.5s ease-out;
		animation-fill-mode: both;
		opacity: 0;
	}

	.region-frame {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 255, 255, 0.05));
		border: 2px solid #00ffff;
		border-radius: 8px;
		padding: 1.5rem;
		text-align: center;
		transition: all 0.3s ease;
		backdrop-filter: blur(20px);
	}

	.region-frame:hover {
		transform: translateY(-3px);
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6), 0 0 20px #00ffff;
	}

	.region-code {
		font-size: 1rem;
		font-weight: 700;
		color: #00ffff;
		margin-bottom: 0.5rem;
		text-shadow: 0 0 10px #00ffff;
	}

	.region-status {
		font-size: 0.6rem;
		color: #00ff85;
		padding: 0.2rem 0.5rem;
		background: rgba(0, 255, 133, 0.1);
		border: 1px solid #00ff85;
		border-radius: 3px;
		text-shadow: 0 0 8px #00ff85;
	}

	@keyframes cloudPulse {
		0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 255, 0.3); }
		50% { box-shadow: 0 0 40px rgba(0, 255, 255, 0.6); }
	}

	@keyframes cloudFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-10px); }
	}

	@keyframes regionEntrance {
		0% { opacity: 0; transform: scale(0.8); }
		100% { opacity: 1; transform: scale(1); }
	}
</style>