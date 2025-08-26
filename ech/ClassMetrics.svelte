<!-- ClassMetrics.svelte -->
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

<div class="class-analysis-hub">
	<div class="analysis-header">
		<div class="class-core">
			<div class="core-symbol">◐</div>
		</div>
		<div class="analysis-info">
			<h2>CLASS ANALYSIS</h2>
			<p>KEYWORD "CLASS" + NUMBER EXTRACTION</p>
		</div>
	</div>

	{#if loading}
		<div class="class-scan">
			<div class="scan-rings">
				{#each Array(4) as _, i}
					<div class="scan-ring" style="animation-delay: {i * 0.3}s"></div>
				{/each}
			</div>
			<p>ANALYZING CLASS NUMBERS...</p>
		</div>
	{:else}
		<div class="class-grid">
			{#each Object.entries(data.classification_matrix || {}) as [className, count], i}
				<div class="class-node" style="animation-delay: {i * 0.1}s">
					<div class="node-frame">
						<div class="class-icon">◆</div>
						<div class="class-name">{className.toUpperCase()}</div>
						<div class="class-count">{count.toLocaleString()}</div>
						<div class="node-connections">
							{#each Array(3) as _}
								<div class="connection"></div>
							{/each}
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.class-analysis-hub {
		font-family: 'Orbitron', monospace;
		color: #fff;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.analysis-header {
		display: flex;
		align-items: center;
		gap: 2rem;
		padding: 1.5rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 0, 255, 0.05));
		border: 2px solid #ff00ff;
		border-radius: 12px;
		margin-bottom: 1.5rem;
	}

	.class-core {
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
		animation: classPulse 3s ease-in-out infinite;
	}

	.analysis-info h2 {
		margin: 0;
		font-size: 1.5rem;
		color: #fff;
		text-shadow: 0 0 15px rgba(255, 0, 255, 0.5);
	}

	.analysis-info p {
		margin: 0.3rem 0 0 0;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.class-scan {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2rem;
		padding: 3rem;
	}

	.scan-rings {
		position: relative;
		width: 120px;
		height: 120px;
	}

	.scan-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid #ff00ff;
		border-radius: 50%;
		opacity: 0.6;
		animation: ringExpand 2s ease-in-out infinite;
	}

	.class-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 1.5rem;
	}

	.class-node {
		animation: nodeEntrance 0.6s ease-out;
		animation-fill-mode: both;
		opacity: 0;
	}

	.node-frame {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 0, 255, 0.05));
		border: 2px solid #ff00ff;
		border-radius: 12px;
		padding: 1.5rem;
		text-align: center;
		transition: all 0.3s ease;
		backdrop-filter: blur(20px);
	}

	.node-frame:hover {
		transform: translateY(-5px);
		box-shadow: 0 15px 40px rgba(0, 0, 0, 0.6), 0 0 30px #ff00ff;
	}

	.class-icon {
		font-size: 2rem;
		color: #ff00ff;
		margin-bottom: 1rem;
		text-shadow: 0 0 15px #ff00ff;
	}

	.class-name {
		font-size: 1rem;
		font-weight: 700;
		color: #fff;
		margin-bottom: 0.5rem;
		text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
	}

	.class-count {
		font-size: 1.8rem;
		font-weight: 700;
		color: #ff00ff;
		margin-bottom: 1rem;
		text-shadow: 0 0 15px #ff00ff;
	}

	.node-connections {
		display: flex;
		justify-content: center;
		gap: 0.5rem;
	}

	.connection {
		width: 6px;
		height: 6px;
		background: #ff00ff;
		border-radius: 50%;
		animation: connectionPulse 2s ease-in-out infinite;
		box-shadow: 0 0 8px #ff00ff;
	}

	@keyframes classPulse {
		0%, 100% { box-shadow: 0 0 20px rgba(255, 0, 255, 0.3); }
		50% { box-shadow: 0 0 40px rgba(255, 0, 255, 0.6); }
	}

	@keyframes ringExpand {
		0% { transform: scale(0.5); opacity: 1; }
		100% { transform: scale(1.2); opacity: 0; }
	}

	@keyframes nodeEntrance {
		0% { opacity: 0; transform: translateY(30px); }
		100% { opacity: 1; transform: translateY(0); }
	}

	@keyframes connectionPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}
</style>