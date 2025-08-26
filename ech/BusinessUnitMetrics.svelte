<!-- BusinessUnitMetrics.svelte -->
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
			console.error('Business unit metrics error:', err);
			loading = false;
		}
	});

	$: sortedUnits = data.business_intelligence ? 
		Object.entries(data.business_intelligence).sort((a, b) => b[1] - a[1]) : [];
</script>

<div class="business-command-center">
	<div class="command-header">
		<div class="business-core">
			<div class="core-symbol">◒</div>
		</div>
		<div class="command-info">
			<h2>BUSINESS UNITS</h2>
			<p>COMMA AND PIPE-SEPARATED ANALYSIS</p>
		</div>
	</div>

	{#if loading}
		<div class="business-scan">
			<div class="org-chart">
				{#each Array(8) as _, i}
					<div class="org-node" style="animation-delay: {i * 0.2}s"></div>
				{/each}
			</div>
			<p>ANALYZING BUSINESS UNITS...</p>
		</div>
	{:else}
		<div class="unit-grid">
			{#each sortedUnits.slice(0, 20) as [unit, count], i}
				<div class="unit-card" style="animation-delay: {i * 0.1}s">
					<div class="card-header">
						<div class="unit-icon">🏢</div>
						<div class="unit-rank">#{i + 1}</div>
					</div>
					<div class="unit-name">{unit.toUpperCase()}</div>
					<div class="unit-count">{count.toLocaleString()}</div>
					<div class="unit-connections">
						{#each Array(5) as _, j}
							<div class="connection-node" style="animation-delay: {j * 0.1}s"></div>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.business-command-center {
		font-family: 'Orbitron', monospace;
		color: #fff;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.command-header {
		display: flex;
		align-items: center;
		gap: 2rem;
		padding: 1.5rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 255, 255, 0.05));
		border: 2px solid #00ffff;
		border-radius: 12px;
		margin-bottom: 1.5rem;
	}

	.business-core {
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
		animation: businessPulse 3s ease-in-out infinite;
	}

	.command-info h2 {
		margin: 0;
		font-size: 1.5rem;
		color: #fff;
		text-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
	}

	.command-info p {
		margin: 0.3rem 0 0 0;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.business-scan {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2rem;
		padding: 3rem;
	}

	.org-chart {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
	}

	.org-node {
		width: 50px;
		height: 50px;
		background: #00ffff;
		border-radius: 8px;
		animation: orgPulse 2s ease-in-out infinite;
	}

	.unit-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
	}

	.unit-card {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 255, 255, 0.05));
		border: 2px solid #00ffff;
		border-radius: 12px;
		padding: 1.5rem;
		text-align: center;
		transition: all 0.3s ease;
		backdrop-filter: blur(20px);
		animation: cardSlide 0.6s ease-out;
		animation-fill-mode: both;
		opacity: 0;
	}

	.unit-card:hover {
		transform: translateY(-5px);
		box-shadow: 0 15px 40px rgba(0, 0, 0, 0.6), 0 0 30px #00ffff;
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.unit-icon {
		font-size: 2rem;
		filter: hue-rotate(180deg) saturate(2);
	}

	.unit-rank {
		font-size: 0.8rem;
		font-weight: 700;
		color: #00ffff;
		padding: 0.3rem 0.6rem;
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid #00ffff;
		border-radius: 4px;
		text-shadow: 0 0 8px #00ffff;
	}

	.unit-name {
		font-size: 1rem;
		font-weight: 700;
		color: #fff;
		margin-bottom: 0.5rem;
		text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
	}

	.unit-count {
		font-size: 2rem;
		font-weight: 700;
		color: #00ffff;
		margin-bottom: 1rem;
		text-shadow: 0 0 15px #00ffff;
	}

	.unit-connections {
		display: flex;
		justify-content: center;
		gap: 0.3rem;
	}

	.connection-node {
		width: 4px;
		height: 15px;
		background: #00ffff;
		border-radius: 2px;
		animation: connectionFlicker 2s ease-in-out infinite;
		box-shadow: 0 0 6px #00ffff;
	}

	@keyframes businessPulse {
		0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 255, 0.3); }
		50% { box-shadow: 0 0 40px rgba(0, 255, 255, 0.6); }
	}

	@keyframes orgPulse {
		0%, 100% { opacity: 0.3; background: #00ffff; }
		50% { opacity: 1; background: #fff; }
	}

	@keyframes cardSlide {
		0% { opacity: 0; transform: translateY(30px); }
		100% { opacity: 1; transform: translateY(0); }
	}

	@keyframes connectionFlicker {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}
</style>