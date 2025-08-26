<!-- DataCenterMetrics.svelte -->
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

<div class="datacenter-command-hub">
	<div class="hub-header">
		<div class="facility-core">
			<div class="hexagon-frame">⬡</div>
		</div>
		<div class="hub-info">
			<h2>DATA CENTER MAPPING</h2>
			<p>FIRST WORD FACILITY ANALYSIS</p>
		</div>
	</div>

	{#if loading}
		<div class="facility-scan">
			<div class="scan-grid">
				{#each Array(9) as _, i}
					<div class="facility-node" style="animation-delay: {i * 0.2}s"></div>
				{/each}
			</div>
			<p>MAPPING DATA CENTERS...</p>
		</div>
	{:else}
		<div class="facility-grid">
			{#each sortedCenters as [center, count], i}
				<div class="facility-card" style="animation-delay: {i * 0.1}s">
					<div class="card-frame">
						<div class="facility-icon">🏢</div>
						<div class="facility-name">{center.toUpperCase()}</div>
						<div class="facility-count">{count.toLocaleString()}</div>
						<div class="connection-ports">
							{#each Array(4) as _}
								<div class="port"></div>
							{/each}
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.datacenter-command-hub {
		font-family: 'Orbitron', monospace;
		color: #fff;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.hub-header {
		display: flex;
		align-items: center;
		gap: 2rem;
		padding: 1.5rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 150, 255, 0.05));
		border: 2px solid #0096ff;
		border-radius: 12px;
		margin-bottom: 1.5rem;
	}

	.facility-core {
		width: 80px;
		height: 80px;
		background: radial-gradient(circle, rgba(0, 150, 255, 0.2), transparent);
		border: 3px solid #0096ff;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		color: #0096ff;
		text-shadow: 0 0 20px #0096ff;
		animation: facilityPulse 3s ease-in-out infinite;
	}

	.hub-info h2 {
		margin: 0;
		font-size: 1.5rem;
		color: #fff;
		text-shadow: 0 0 15px rgba(0, 150, 255, 0.5);
	}

	.hub-info p {
		margin: 0.3rem 0 0 0;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.facility-scan {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2rem;
		padding: 3rem;
	}

	.scan-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
	}

	.facility-node {
		width: 60px;
		height: 60px;
		background: #0096ff;
		border-radius: 8px;
		animation: nodeScan 2s ease-in-out infinite;
	}

	.facility-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
	}

	.facility-card {
		animation: cardEntrance 0.6s ease-out;
		animation-fill-mode: both;
		opacity: 0;
	}

	.card-frame {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 150, 255, 0.05));
		border: 2px solid #0096ff;
		border-radius: 12px;
		padding: 2rem;
		text-align: center;
		transition: all 0.3s ease;
		backdrop-filter: blur(20px);
	}

	.card-frame:hover {
		transform: translateY(-5px);
		box-shadow: 0 15px 40px rgba(0, 0, 0, 0.6), 0 0 30px #0096ff;
	}

	.facility-icon {
		font-size: 3rem;
		margin-bottom: 1rem;
		filter: hue-rotate(200deg) saturate(2);
	}

	.facility-name {
		font-size: 1.1rem;
		font-weight: 700;
		color: #0096ff;
		margin-bottom: 1rem;
		text-shadow: 0 0 10px #0096ff;
	}

	.facility-count {
		font-size: 2rem;
		font-weight: 700;
		color: #fff;
		margin-bottom: 1rem;
		text-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
	}

	.connection-ports {
		display: flex;
		justify-content: center;
		gap: 0.5rem;
	}

	.port {
		width: 8px;
		height: 8px;
		background: #0096ff;
		border-radius: 50%;
		animation: portBlink 2s ease-in-out infinite;
		box-shadow: 0 0 8px #0096ff;
	}

	@keyframes facilityPulse {
		0%, 100% { box-shadow: 0 0 20px rgba(0, 150, 255, 0.3); }
		50% { box-shadow: 0 0 40px rgba(0, 150, 255, 0.6); }
	}

	@keyframes nodeScan {
		0%, 100% { opacity: 0.3; background: #0096ff; }
		50% { opacity: 1; background: #fff; }
	}

	@keyframes cardEntrance {
		0% { opacity: 0; transform: translateY(30px); }
		100% { opacity: 1; transform: translateY(0); }
	}

	@keyframes portBlink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}
</style>
