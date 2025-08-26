<script>
	import { onMount } from 'svelte';
	let data = {};
	let loading = true;

	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/cmdb_presence');
			data = await response.json();
			loading = false;
		} catch (err) {
			loading = false;
		}
	});

	$: registrationColor = data.registration_rate >= 80 ? '#00ff41' : 
	                      data.registration_rate >= 60 ? '#ffaa00' : '#ff4444';
</script>

<div class="cmdb-panel">
	<header class="panel-header">
		<span class="header-icon">⬢</span>
		<h2>CMDB PRESENCE</h2>
		<p>Keyword search: "yes" in present_in_cmdb</p>
	</header>
	
	{#if loading}
		<div class="loading">Checking CMDB presence...</div>
	{:else}
		<div class="cmdb-stats">
			<div class="stat-card">
				<div class="stat-value" style="color: {registrationColor}">
					{data.cmdb_registered || 0}
				</div>
				<div class="stat-label">REGISTERED</div>
			</div>
			<div class="stat-card">
				<div class="stat-value">{data.total_assets || 0}</div>
				<div class="stat-label">TOTAL ASSETS</div>
			</div>
			<div class="stat-card">
				<div class="stat-value" style="color: {registrationColor}">
					{data.registration_rate || 0}%
				</div>
				<div class="stat-label">RATE</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.cmdb-panel {
		background: rgba(0, 26, 0, 0.95);
		border: 1px solid #00ff41;
		border-radius: 8px;
		padding: 20px;
	}
	.cmdb-stats {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 20px;
	}
	.stat-card {
		background: rgba(0, 0, 0, 0.6);
		border: 1px solid #004400;
		border-radius: 6px;
		padding: 20px;
		text-align: center;
	}
	.stat-value {
		font-size: 24px;
		font-weight: bold;
		color: #00ff41;
		margin-bottom: 10px;
	}
	.stat-label {
		color: #66ff66;
		font-size: 12px;
	}
</style>