<!-- CioMetrics.svelte -->
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

<div class="cio-command-matrix">
	<div class="matrix-header">
		<div class="cio-core">
			<div class="core-symbol">◓</div>
		</div>
		<div class="matrix-info">
			<h2>CIO ANALYSIS</h2>
			<p>PIPE-SEPARATED WORDS ONLY (NO NUMBERS)</p>
		</div>
	</div>

	{#if loading}
		<div class="cio-scan">
			<div class="executive-grid">
				{#each Array(6) as _, i}
					<div class="exec-node" style="animation-delay: {i * 0.3}s"></div>
				{/each}
			</div>
			<p>ANALYZING CIO DATA...</p>
		</div>
	{:else}
		<div class="cio-list">
			{#each sortedCios as [cio, count], i}
				<div class="cio-entry" style="animation-delay: {i * 0.05}s">
					<div class="cio-avatar">👤</div>
					<div class="cio-details">
						<div class="cio-name">{cio.toUpperCase()}</div>
						<div class="cio-count">{count.toLocaleString()}</div>
					</div>
					<div class="access-level">
						<div class="level-indicator">◈</div>
						<div class="level-text">EXEC</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.cio-command-matrix {
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
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 0, 255, 0.05));
		border: 2px solid #ff00ff;
		border-radius: 12px;
		margin-bottom: 1.5rem;
	}

	.cio-core {
		width: 80px;
		height: 80px;
		background: radial-gradient(circle, rgba(255, 0, 255, 0.2), transparent);
		border: 3px solid #ff00ff;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		color: #ff00ff;
		text-shadow: 0 0 20px #ff00ff;
		animation: cioPulse 3s ease-in-out infinite;
	}

	.matrix-info h2 {
		margin: 0;
		font-size: 1.5rem;
		color: #fff;
		text-shadow: 0 0 15px rgba(255, 0, 255, 0.5);
	}

	.matrix-info p {
		margin: 0.3rem 0 0 0;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.cio-scan {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2rem;
		padding: 3rem;
	}

	.executive-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
	}

	.exec-node {
		width: 60px;
		height: 60px;
		background: #ff00ff;
		border-radius: 50%;
		animation: execScan 2s ease-in-out infinite;
	}

	.cio-list {
		max-height: 60vh;
		overflow-y: auto;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 0, 255, 0.02));
		border: 2px solid rgba(255, 0, 255, 0.3);
		border-radius: 12px;
		padding: 1rem;
	}

	.cio-entry {
		display: grid;
		grid-template-columns: auto 1fr auto;
		gap: 1rem;
		align-items: center;
		padding: 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		animation: entryFade 0.5s ease-out;
		animation-fill-mode: both;
		opacity: 0;
	}

	.cio-entry:hover {
		background: linear-gradient(90deg, rgba(255, 0, 255, 0.05), transparent);
	}

	.cio-avatar {
		font-size: 2rem;
		filter: hue-rotate(300deg) saturate(2);
	}

	.cio-details {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.cio-name {
		font-size: 1rem;
		font-weight: 700;
		color: #fff;
	}

	.cio-count {
		font-size: 1.3rem;
		font-weight: 700;
		color: #ff00ff;
		text-shadow: 0 0 8px #ff00ff;
	}

	.access-level {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.2rem;
	}

	.level-indicator {
		color: #ff00ff;
		font-size: 1.2rem;
		text-shadow: 0 0 10px #ff00ff;
	}

	.level-text {
		font-size: 0.6rem;
		color: #ff00ff;
		padding: 0.2rem 0.5rem;
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid #ff00ff;
		border-radius: 3px;
		text-shadow: 0 0 8px #ff00ff;
	}

	@keyframes cioPulse {
		0%, 100% { box-shadow: 0 0 20px rgba(255, 0, 255, 0.3); }
		50% { box-shadow: 0 0 40px rgba(255, 0, 255, 0.6); }
	}

	@keyframes execScan {
		0%, 100% { opacity: 0.3; background: #ff00ff; }
		50% { opacity: 1; background: #fff; }
	}

	@keyframes entryFade {
		0% { opacity: 0; transform: translateX(-20px); }
		100% { opacity: 1; transform: translateX(0); }
	}
</style>
