<!-- SystemClassification.svelte -->
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

<div class="system-taxonomy-hub">
	<div class="taxonomy-header">
		<div class="system-core">
			<div class="core-frame">◑</div>
		</div>
		<div class="taxonomy-info">
			<h2>SYSTEM TAXONOMY</h2>
			<p>PIPE-SEPARATED SYSTEM CLASSIFICATIONS</p>
		</div>
	</div>

	{#if loading}
		<div class="system-scan">
			<div class="classification-grid">
				{#each Array(12) as _, i}
					<div class="system-cell" style="animation-delay: {i * 0.1}s"></div>
				{/each}
			</div>
			<p>CLASSIFYING SYSTEMS...</p>
		</div>
	{:else}
		<div class="system-list">
			{#each sortedSystems.slice(0, 25) as [system, count], i}
				<div class="system-entry" style="animation-delay: {i * 0.05}s">
					<div class="system-indicator">◈</div>
					<div class="system-name">{system.toUpperCase()}</div>
					<div class="system-count">{count.toLocaleString()}</div>
					<div class="system-bar">
						<div class="bar-fill" style="width: {(count / Math.max(...sortedSystems.map(([,c]) => c))) * 100}%"></div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.system-taxonomy-hub {
		font-family: 'Orbitron', monospace;
		color: #fff;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.taxonomy-header {
		display: flex;
		align-items: center;
		gap: 2rem;
		padding: 1.5rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 150, 255, 0.05));
		border: 2px solid #0096ff;
		border-radius: 12px;
		margin-bottom: 1.5rem;
	}

	.system-core {
		width: 80px;
		height: 80px;
		background: radial-gradient(circle, rgba(0, 150, 255, 0.2), transparent);
		border: 3px solid #0096ff;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		color: #0096ff;
		text-shadow: 0 0 20px #0096ff;
		animation: systemPulse 3s ease-in-out infinite;
	}

	.taxonomy-info h2 {
		margin: 0;
		font-size: 1.5rem;
		color: #fff;
		text-shadow: 0 0 15px rgba(0, 150, 255, 0.5);
	}

	.taxonomy-info p {
		margin: 0.3rem 0 0 0;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.system-scan {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2rem;
		padding: 3rem;
	}

	.classification-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 0.5rem;
	}

	.system-cell {
		width: 30px;
		height: 30px;
		background: #0096ff;
		border-radius: 4px;
		animation: cellClassify 2s ease-in-out infinite;
	}

	.system-list {
		max-height: 70vh;
		overflow-y: auto;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 150, 255, 0.02));
		border: 2px solid rgba(0, 150, 255, 0.3);
		border-radius: 12px;
		padding: 1rem;
	}

	.system-entry {
		display: grid;
		grid-template-columns: auto 2fr auto auto;
		gap: 1rem;
		align-items: center;
		padding: 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		animation: entrySlide 0.5s ease-out;
		animation-fill-mode: both;
		opacity: 0;
	}

	.system-entry:hover {
		background: linear-gradient(90deg, rgba(0, 150, 255, 0.05), transparent);
	}

	.system-indicator {
		color: #0096ff;
		font-size: 1.2rem;
		text-shadow: 0 0 10px #0096ff;
	}

	.system-name {
		font-size: 0.9rem;
		font-weight: 600;
		color: #fff;
	}

	.system-count {
		font-size: 1.1rem;
		font-weight: 700;
		color: #0096ff;
		text-shadow: 0 0 8px #0096ff;
		min-width: 60px;
		text-align: right;
	}

	.system-bar {
		width: 100px;
		height: 6px;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 3px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		background: linear-gradient(90deg, #0096ff, #00ccff);
		border-radius: 3px;
		transition: width 1s ease-out;
		box-shadow: 0 0 8px #0096ff;
	}

	@keyframes systemPulse {
		0%, 100% { box-shadow: 0 0 20px rgba(0, 150, 255, 0.3); }
		50% { box-shadow: 0 0 40px rgba(0, 150, 255, 0.6); }
	}

	@keyframes cellClassify {
		0%, 100% { opacity: 0.3; background: #0096ff; }
		50% { opacity: 1; background: #fff; }
	}

	@keyframes entrySlide {
		0% { opacity: 0; transform: translateX(-20px); }
		100% { opacity: 1; transform: translateX(0); }
	}
</style>
