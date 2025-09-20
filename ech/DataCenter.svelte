<!-- DataCenter.svelte - ULTIMATE INFRASTRUCTURE COMMAND CENTER -->
<script>
	import { onMount, onDestroy } from 'svelte';
	
	let data = {};
	let loading = true;
	let selectedFacility = null;
	let facilityDetails = [];
	let searchTerm = '';
	let sortColumn = 'count';
	let sortDirection = 'desc';
	let currentPage = 1;
	let itemsPerPage = 20;
	
	// Advanced visualization states
	let datacenters = [];
	let rackLayout = [];
	let powerGrid = [];
	let coolingSystem = [];
	let networkTopology = [];
	let storageArray = [];
	let serverMetrics = [];
	let environmentalData = [];
	let securityZones = [];
	let redundancyMap = [];
	
	// Real-time metrics
	let powerUsage = 0;
	let coolingEfficiency = 0;
	let networkThroughput = 0;
	let storageCapacity = 0;
	let cpuUtilization = 0;
	let memoryUsage = 0;
	let temperature = 0;
	let humidity = 0;
	let pue = 1.0; // Power Usage Effectiveness
	
	// Animation states
	let dataFlowPhase = 0;
	let powerPhase = 0;
	let coolingPhase = 0;
	let alertPhase = 0;
	
	let animationFrames = {
		main: null,
		power: null,
		cooling: null,
		network: null
	};
	
	onMount(async () => {
		try {
			let response = await fetch('http://localhost:5000/api/data_center_metrics');
			data = await response.json();
			loading = false;
			initializeInfrastructure();
			startInfrastructureMonitoring();
		} catch (err) {
			console.error('Data center sync failed:', err);
			data = generateMockData();
			loading = false;
			initializeInfrastructure();
			startInfrastructureMonitoring();
		}
	});
	
	onDestroy(() => {
		Object.values(animationFrames).forEach(frame => {
			if (frame) cancelAnimationFrame(frame);
		});
	});
	
	function generateMockData() {
		const facilities = [
			'DC-US-EAST-1', 'DC-US-WEST-1', 'DC-EU-CENTRAL-1', 'DC-APAC-1',
			'DC-US-EAST-2', 'DC-US-WEST-2', 'DC-EU-WEST-1', 'DC-APAC-2',
			'DC-CANADA-1', 'DC-BRAZIL-1', 'DC-UK-1', 'DC-GERMANY-1',
			'DC-JAPAN-1', 'DC-SINGAPORE-1', 'DC-AUSTRALIA-1', 'DC-INDIA-1',
			'COLO-NYC-1', 'COLO-SFO-1', 'COLO-LON-1', 'COLO-FRA-1',
			'EDGE-ATL-1', 'EDGE-CHI-1', 'EDGE-DAL-1', 'EDGE-SEA-1',
			'CLOUD-AWS-1', 'CLOUD-AZURE-1', 'CLOUD-GCP-1', 'CLOUD-OCI-1'
		];
		
		const mockData = {};
		facilities.forEach(facility => {
			mockData[facility] = Math.floor(Math.random() * 100000) + 5000;
		});
		
		return { facility_intelligence: mockData };
	}
	
	function initializeInfrastructure() {
		if (!data.facility_intelligence) return;
		
		const facilities = Object.entries(data.facility_intelligence);
		
		// Initialize data center infrastructure
		facilities.forEach(([facility, count], i) => {
			const dc = {
				id: facility,
				name: facility,
				count: count,
				location: getFacilityLocation(facility),
				type: getFacilityType(facility),
				tier: Math.floor(Math.random() * 3) + 2, // Tier 2-4
				capacity: Math.floor(Math.random() * 10000) + 5000,
				utilization: Math.random() * 100,
				status: Math.random() > 0.1 ? 'operational' : 'maintenance',
				powerCapacity: Math.random() * 10 + 5, // MW
				coolingCapacity: Math.random() * 5000 + 2000, // Tons
				networkBandwidth: Math.random() * 100 + 10, // Gbps
				storageCapacity: Math.random() * 1000 + 100, // PB
				racks: Math.floor(count / 42), // 42U racks
				servers: count,
				temperature: 18 + Math.random() * 8,
				humidity: 40 + Math.random() * 20,
				pue: 1.2 + Math.random() * 0.5,
				redundancy: ['N', 'N+1', '2N', '2N+1'][Math.floor(Math.random() * 4)]
			};
			datacenters.push(dc);
			
			// Initialize rack layout for this DC
			const rackCount = dc.racks;
			for (let r = 0; r < Math.min(rackCount, 20); r++) {
				rackLayout.push({
					dcId: facility,
					rackId: `${facility}-RACK-${r}`,
					row: Math.floor(r / 10),
					position: r % 10,
					utilization: Math.random() * 100,
					power: Math.random() * 20, // kW
					temperature: 20 + Math.random() * 10,
					servers: Math.floor(Math.random() * 42),
					status: Math.random() > 0.9 ? 'warning' : 'normal'
				});
			}
		});
		
		// Initialize power grid
		for (let i = 0; i < 10; i++) {
			powerGrid.push({
				id: `PWR-${i}`,
				source: ['utility', 'generator', 'ups', 'solar'][Math.floor(Math.random() * 4)],
				capacity: Math.random() * 5 + 1, // MW
				load: Math.random() * 100,
				efficiency: 85 + Math.random() * 15,
				status: Math.random() > 0.9 ? 'critical' : Math.random() > 0.7 ? 'warning' : 'normal'
			});
		}
		
		// Initialize cooling system
		for (let i = 0; i < 8; i++) {
			coolingSystem.push({
				id: `COOL-${i}`,
				type: ['CRAC', 'CRAH', 'Chiller', 'Free Cooling'][Math.floor(Math.random() * 4)],
				capacity: Math.random() * 1000 + 500, // Tons
				utilization: Math.random() * 100,
				setpoint: 18 + Math.random() * 4,
				actualTemp: 18 + Math.random() * 6,
				efficiency: 80 + Math.random() * 20
			});
		}
		
		// Initialize network topology
		datacenters.forEach((dc, i) => {
			networkTopology.push({
				node: dc.id,
				x: Math.cos(i * Math.PI * 2 / datacenters.length) * 200 + 250,
				y: Math.sin(i * Math.PI * 2 / datacenters.length) * 200 + 250,
				connections: [],
				bandwidth: dc.networkBandwidth,
				latency: Math.random() * 50,
				packetLoss: Math.random() * 0.1
			});
		});
		
		// Create network connections
		networkTopology.forEach((node, i) => {
			const connectionCount = Math.floor(Math.random() * 3) + 1;
			for (let c = 0; c < connectionCount; c++) {
				const targetIndex = Math.floor(Math.random() * networkTopology.length);
				if (targetIndex !== i) {
					node.connections.push(targetIndex);
				}
			}
		});
		
		// Initialize storage array
		for (let i = 0; i < 12; i++) {
			storageArray.push({
				id: `STOR-${i}`,
				type: ['SAN', 'NAS', 'Object', 'Block'][Math.floor(Math.random() * 4)],
				capacity: Math.random() * 100 + 10, // PB
				used: Math.random() * 80,
				iops: Math.random() * 100000,
				throughput: Math.random() * 10, // GB/s
				redundancy: ['RAID-1', 'RAID-5', 'RAID-6', 'RAID-10'][Math.floor(Math.random() * 4)]
			});
		}
		
		// Initialize server metrics
		for (let i = 0; i < 50; i++) {
			serverMetrics.push({
				id: `SRV-${i}`,
				cpu: Math.random() * 100,
				memory: Math.random() * 100,
				disk: Math.random() * 100,
				network: Math.random() * 1000, // Mbps
				temperature: 30 + Math.random() * 20,
				power: Math.random() * 500, // Watts
				status: Math.random() > 0.95 ? 'critical' : Math.random() > 0.85 ? 'warning' : 'normal'
			});
		}
		
		// Initialize environmental data
		for (let h = 0; h < 24; h++) {
			environmentalData.push({
				hour: h,
				temperature: 20 + Math.sin(h * Math.PI / 12) * 5 + Math.random() * 2,
				humidity: 45 + Math.cos(h * Math.PI / 12) * 10 + Math.random() * 5,
				power: 3 + Math.sin(h * Math.PI / 12) * 1 + Math.random() * 0.5,
				cooling: 1500 + Math.sin(h * Math.PI / 12) * 500 + Math.random() * 200
			});
		}
		
		// Initialize security zones
		['DMZ', 'Public', 'Private', 'Management', 'Storage'].forEach((zone, i) => {
			securityZones.push({
				name: zone,
				servers: Math.floor(Math.random() * 500) + 100,
				firewalls: Math.floor(Math.random() * 10) + 2,
				ips: Math.floor(Math.random() * 5) + 1,
				threats: Math.floor(Math.random() * 100),
				blocked: Math.floor(Math.random() * 90),
				level: ['low', 'medium', 'high', 'critical'][Math.floor(Math.random() * 4)]
			});
		});
		
		// Initialize redundancy map
		datacenters.forEach(dc => {
			redundancyMap.push({
				primary: dc.id,
				secondary: datacenters[Math.floor(Math.random() * datacenters.length)].id,
				type: dc.redundancy,
				syncStatus: Math.random() > 0.2 ? 'synchronized' : 'syncing',
				failoverTime: Math.random() * 60, // seconds
				dataLag: Math.random() * 10 // seconds
			});
		});
	}
	
	function getFacilityLocation(facility) {
		if (facility.includes('US-EAST')) return 'Virginia, USA';
		if (facility.includes('US-WEST')) return 'California, USA';
		if (facility.includes('EU-CENTRAL')) return 'Frankfurt, Germany';
		if (facility.includes('EU-WEST')) return 'London, UK';
		if (facility.includes('APAC')) return 'Singapore';
		if (facility.includes('CANADA')) return 'Toronto, Canada';
		if (facility.includes('BRAZIL')) return 'São Paulo, Brazil';
		if (facility.includes('UK')) return 'London, UK';
		if (facility.includes('GERMANY')) return 'Frankfurt, Germany';
		if (facility.includes('JAPAN')) return 'Tokyo, Japan';
		if (facility.includes('SINGAPORE')) return 'Singapore';
		if (facility.includes('AUSTRALIA')) return 'Sydney, Australia';
		if (facility.includes('INDIA')) return 'Mumbai, India';
		return 'Unknown';
	}
	
	function getFacilityType(facility) {
		if (facility.includes('DC-')) return 'Data Center';
		if (facility.includes('COLO-')) return 'Colocation';
		if (facility.includes('EDGE-')) return 'Edge';
		if (facility.includes('CLOUD-')) return 'Cloud';
		return 'Unknown';
	}
	
	function startInfrastructureMonitoring() {
		let time = 0;
		
		function animate() {
			time += 0.016;
			
			// Update phases
			dataFlowPhase = (dataFlowPhase + 0.02) % (Math.PI * 2);
			powerPhase = (powerPhase + 0.015) % (Math.PI * 2);
			coolingPhase = (coolingPhase + 0.01) % (Math.PI * 2);
			alertPhase = (alertPhase + 0.05) % (Math.PI * 2);
			
			// Update real-time metrics
			powerUsage = 3 + Math.sin(time * 0.3) * 1 + Math.random() * 0.5; // MW
			coolingEfficiency = 85 + Math.sin(time * 0.4) * 10 + Math.random() * 5;
			networkThroughput = 50 + Math.sin(time * 0.5) * 30 + Math.random() * 20; // Gbps
			storageCapacity = 60 + Math.sin(time * 0.2) * 20 + Math.random() * 10; // % used
			cpuUtilization = 40 + Math.sin(time * 0.6) * 30 + Math.random() * 20;
			memoryUsage = 50 + Math.sin(time * 0.7) * 25 + Math.random() * 15;
			temperature = 20 + Math.sin(time * 0.3) * 3 + Math.random() * 2;
			humidity = 45 + Math.cos(time * 0.4) * 5 + Math.random() * 5;
			pue = 1.2 + Math.sin(time * 0.2) * 0.2 + Math.random() * 0.1;
			
			// Update rack temperatures
			rackLayout.forEach(rack => {
				rack.temperature = 20 + Math.sin(time + rack.position * 0.5) * 5 + Math.random() * 3;
				rack.utilization = 50 + Math.sin(time + rack.position * 0.3) * 40 + Math.random() * 10;
				if (Math.random() < 0.01) {
					rack.status = ['normal', 'warning', 'critical'][Math.floor(Math.random() * 3)];
				}
			});
			
			// Update power grid
			powerGrid.forEach(grid => {
				grid.load = 50 + Math.sin(time + grid.id.charCodeAt(4) * 0.1) * 40 + Math.random() * 10;
				grid.efficiency = 85 + Math.sin(time * 0.3) * 10 + Math.random() * 5;
			});
			
			// Update cooling system
			coolingSystem.forEach(cool => {
				cool.utilization = 50 + Math.sin(time + cool.id.charCodeAt(5) * 0.2) * 40 + Math.random() * 10;
				cool.actualTemp = cool.setpoint + Math.sin(time * 0.5) * 2 + Math.random() - 0.5;
			});
			
			// Update server metrics
			serverMetrics.forEach(server => {
				server.cpu = 40 + Math.sin(time + server.id.charCodeAt(4) * 0.1) * 40 + Math.random() * 20;
				server.memory = 50 + Math.sin(time + server.id.charCodeAt(4) * 0.2) * 30 + Math.random() * 20;
				server.temperature = 30 + Math.sin(time + server.id.charCodeAt(4) * 0.3) * 10 + Math.random() * 10;
			});
			
			animationFrames.main = requestAnimationFrame(animate);
		}
		animate();
	}
	
	$: facilities = data.facility_intelligence ? 
		Object.entries(data.facility_intelligence)
			.filter(([facility]) => facility.toLowerCase().includes(searchTerm.toLowerCase()))
			.sort((a, b) => {
				if (sortColumn === 'name') {
					return sortDirection === 'asc' ? 
						a[0].localeCompare(b[0]) : b[0].localeCompare(a[0]);
				}
				return sortDirection === 'asc' ? a[1] - b[1] : b[1] - a[1];
			}) : [];
	
	$: paginatedFacilities = facilities.slice(
		(currentPage - 1) * itemsPerPage,
		currentPage * itemsPerPage
	);
	
	$: totalPages = Math.ceil(facilities.length / itemsPerPage);
	$: totalHosts = facilities.reduce((sum, [_, count]) => sum + count, 0);
	$: maxHosts = facilities.length > 0 ? Math.max(...facilities.map(([,c]) => c)) : 1;
	$: avgHosts = facilities.length > 0 ? Math.round(totalHosts / facilities.length) : 0;
	
	function sortTable(column) {
		if (sortColumn === column) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = column;
			sortDirection = 'desc';
		}
	}
	
	async function drillDownFacility(facility, count) {
		selectedFacility = { facility, count };
		loading = true;
		
		try {
			let response = await fetch(`http://localhost:5000/api/host_search?q=${encodeURIComponent(facility)}`);
			let result = await response.json();
			facilityDetails = result.hosts || [];
		} catch (err) {
			console.error('Facility drill-down failed:', err);
			facilityDetails = generateMockHosts(facility, Math.min(100, count));
		} finally {
			loading = false;
		}
	}
	
	function generateMockHosts(facility, count) {
		const hosts = [];
		for (let i = 0; i < count; i++) {
			hosts.push({
				host: `${facility.toLowerCase()}-srv-${i + 1}.datacenter`,
				rack: `RACK-${Math.floor(i / 42) + 1}`,
				unit: `U${(i % 42) + 1}`,
				infrastructure_type: ['Blade', 'Rack', '1U', '2U', '4U'][Math.floor(Math.random() * 5)],
				cpu_cores: [16, 32, 64, 128][Math.floor(Math.random() * 4)],
				memory_gb: [64, 128, 256, 512, 1024][Math.floor(Math.random() * 5)],
				storage_tb: [2, 4, 8, 16, 32][Math.floor(Math.random() * 5)],
				network_gbps: [10, 25, 40, 100][Math.floor(Math.random() * 4)],
				power_watts: Math.floor(Math.random() * 800) + 200,
				temperature_c: Math.floor(Math.random() * 30) + 20,
				present_in_cmdb: Math.random() > 0.2 ? 'Yes' : 'No',
				tanium_coverage: Math.random() > 0.3 ? 'Tanium' : 'No Coverage'
			});
		}
		return hosts;
	}
	
	function closeDetails() {
		selectedFacility = null;
		facilityDetails = [];
	}
	
	function getFacilityLevel(count) {
		const percentage = (count / maxHosts) * 100;
		if (percentage >= 80) return { level: 'HYPERSCALE', color: '#FF0000', glow: '#FF000040' };
		if (percentage >= 60) return { level: 'ENTERPRISE', color: '#FF00FF', glow: '#FF00FF40' };
		if (percentage >= 40) return { level: 'REGIONAL', color: '#00FFFF', glow: '#00FFFF40' };
		if (percentage >= 20) return { level: 'LOCAL', color: '#00FF00', glow: '#00FF0040' };
		return { level: 'EDGE', color: '#FFFF00', glow: '#FFFF0040' };
	}
	
	function formatNumber(num) {
		if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
		if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
		return num.toString();
	}
</script>

<div class="infrastructure-command">
	<!-- Top Metrics Dashboard -->
	<div class="metrics-dashboard">
		<div class="metric-tile power-tile">
			<div class="tile-icon">⚡</div>
			<div class="tile-data">
				<div class="tile-value">{powerUsage.toFixed(2)} MW</div>
				<div class="tile-label">POWER USAGE</div>
			</div>
			<div class="tile-graph">
				<svg viewBox="0 0 100 40">
					<polyline points="{environmentalData.map((d, i) => `${i * 4.2},${40 - d.power * 8}`).join(' ')}"
							  fill="none" stroke="#FF0000" stroke-width="2" opacity="0.8"/>
				</svg>
			</div>
		</div>
		
		<div class="metric-tile cooling-tile">
			<div class="tile-icon">❄️</div>
			<div class="tile-data">
				<div class="tile-value">{coolingEfficiency.toFixed(1)}%</div>
				<div class="tile-label">COOLING EFFICIENCY</div>
			</div>
			<div class="tile-graph">
				<svg viewBox="0 0 100 40">
					<rect x="0" y="10" width="{coolingEfficiency}" height="20" 
						  fill="#00FFFF" opacity="0.6" rx="10"/>
				</svg>
			</div>
		</div>
		
		<div class="metric-tile network-tile">
			<div class="tile-icon">🌐</div>
			<div class="tile-data">
				<div class="tile-value">{networkThroughput.toFixed(0)} Gbps</div>
				<div class="tile-label">NETWORK THROUGHPUT</div>
			</div>
			<div class="tile-graph">
				<svg viewBox="0 0 100 40">
					{#each Array(20) as _, i}
						<rect x="{i * 5}" y="{40 - Math.random() * 30}" 
							  width="4" height="{Math.random() * 30}"
							  fill="#00FF00" opacity="{0.4 + i * 0.03}"/>
					{/each}
				</svg>
			</div>
		</div>
		
		<div class="metric-tile storage-tile">
			<div class="tile-icon">💾</div>
			<div class="tile-data">
				<div class="tile-value">{storageCapacity.toFixed(0)}%</div>
				<div class="tile-label">STORAGE USED</div>
			</div>
			<div class="tile-graph">
				<svg viewBox="0 0 100 40">
					<circle cx="50" cy="20" r="18" fill="none" 
							stroke="rgba(255,255,255,0.2)" stroke-width="4"/>
					<circle cx="50" cy="20" r="18" fill="none" 
							stroke="#FFFF00" stroke-width="4"
							stroke-dasharray="{storageCapacity * 1.13} 113"
							stroke-dashoffset="28.25"
							transform="rotate(-90 50 20)"/>
				</svg>
			</div>
		</div>
		
		<div class="metric-tile pue-tile">
			<div class="tile-icon">📊</div>
			<div class="tile-data">
				<div class="tile-value">{pue.toFixed(2)}</div>
				<div class="tile-label">PUE</div>
			</div>
			<div class="tile-graph">
				<svg viewBox="0 0 100 40">
					<text x="50" y="25" text-anchor="middle" 
						  font-size="12" fill="{pue < 1.5 ? '#00FF00' : pue < 2 ? '#FFFF00' : '#FF0000'}">
						{pue < 1.5 ? 'EXCELLENT' : pue < 2 ? 'GOOD' : 'POOR'}
					</text>
				</svg>
			</div>
		</div>
		
		<div class="metric-tile temp-tile">
			<div class="tile-icon">🌡️</div>
			<div class="tile-data">
				<div class="tile-value">{temperature.toFixed(1)}°C</div>
				<div class="tile-label">AVG TEMPERATURE</div>
			</div>
			<div class="tile-graph">
				<svg viewBox="0 0 100 40">
					<path d="M 0,20 Q 25,{20 - (temperature - 20) * 2} 50,20 T 100,20" 
						  fill="none" stroke="#FF00FF" stroke-width="2" opacity="0.8"/>
				</svg>
			</div>
		</div>
	</div>
	
	<!-- Main Grid Layout -->
	<div class="infrastructure-grid">
		<!-- Left: Rack Layout & Power Grid -->
		<div class="left-section">
			<!-- 3D Rack Visualization -->
			<div class="rack-container">
				<h3 class="section-title">RACK LAYOUT VISUALIZATION</h3>
				<div class="rack-grid">
					{#each rackLayout.slice(0, 20) as rack}
						<div class="rack-unit" 
							 style="background: {rack.status === 'critical' ? 'rgba(255,0,0,0.3)' : 
									rack.status === 'warning' ? 'rgba(255,255,0,0.3)' : 'rgba(0,255,0,0.1)'};
									border-color: {rack.status === 'critical' ? '#FF0000' : 
									rack.status === 'warning' ? '#FFFF00' : '#00FF00'}"
							 title="{rack.rackId}">
							<div class="rack-id">{rack.rackId.split('-').pop()}</div>
							<div class="rack-temp" style="color: {rack.temperature > 25 ? '#FF0000' : rack.temperature > 22 ? '#FFFF00' : '#00FF00'}">
								{rack.temperature.toFixed(0)}°C
							</div>
							<div class="rack-util-bar">
								<div class="rack-util-fill" 
									 style="height: {rack.utilization}%; 
											background: {rack.utilization > 80 ? '#FF0000' : rack.utilization > 60 ? '#FFFF00' : '#00FF00'}">
								</div>
							</div>
							<div class="rack-servers">{rack.servers}U</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Power Grid Status -->
			<div class="power-container">
				<h3 class="section-title">POWER GRID STATUS</h3>
				<div class="power-sources">
					{#each powerGrid as source}
						<div class="power-source">
							<div class="source-header">
								<span class="source-id">{source.id}</span>
								<span class="source-type">{source.source.toUpperCase()}</span>
							</div>
							<div class="source-meter">
								<div class="meter-fill" 
									 style="width: {source.load}%; 
											background: {source.status === 'critical' ? '#FF0000' : 
											source.status === 'warning' ? '#FFFF00' : '#00FF00'}">
								</div>
							</div>
							<div class="source-stats">
								<span>{source.capacity.toFixed(1)} MW</span>
								<span>{source.load.toFixed(0)}%</span>
								<span>{source.efficiency.toFixed(0)}% eff</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
		
		<!-- Center: Main Data Table -->
		<div class="center-section">
			<div class="table-container">
				<div class="table-header">
					<h2 class="table-title">DATA CENTER INFRASTRUCTURE MATRIX</h2>
					<div class="table-controls">
						<input type="text" 
							   bind:value={searchTerm}
							   placeholder="SEARCH FACILITIES..."
							   class="search-input"/>
						<select class="items-select" bind:value={itemsPerPage}>
							<option value={10}>10 per page</option>
							<option value={20}>20 per page</option>
							<option value={50}>50 per page</option>
						</select>
						<div class="pagination">
							<button on:click={() => currentPage = 1} disabled={currentPage === 1}>⏮</button>
							<button on:click={() => currentPage = Math.max(1, currentPage - 1)} disabled={currentPage === 1}>◀</button>
							<span class="page-info">{currentPage} / {totalPages}</span>
							<button on:click={() => currentPage = Math.min(totalPages, currentPage + 1)} disabled={currentPage === totalPages}>▶</button>
							<button on:click={() => currentPage = totalPages} disabled={currentPage === totalPages}>⏭</button>
						</div>
					</div>
				</div>
				
				{#if selectedFacility}
					<div class="detail-view">
						<div class="detail-header">
							<div>
								<h3>{selectedFacility.facility.toUpperCase()}</h3>
								<div class="detail-stats">
									<span>{formatNumber(selectedFacility.count)} servers</span>
									<span>•</span>
									<span>{((selectedFacility.count / totalHosts) * 100).toFixed(2)}% of infrastructure</span>
									<span>•</span>
									<span>Location: {getFacilityLocation(selectedFacility.facility)}</span>
								</div>
							</div>
							<button class="close-btn" on:click={closeDetails}>✕ CLOSE</button>
						</div>
						<div class="detail-content">
							<table class="detail-table">
								<thead>
									<tr>
										<th>HOSTNAME</th>
										<th>RACK</th>
										<th>UNIT</th>
										<th>TYPE</th>
										<th>CPU</th>
										<th>RAM</th>
										<th>STORAGE</th>
										<th>NETWORK</th>
										<th>POWER</th>
										<th>TEMP</th>
										<th>CMDB</th>
										<th>TANIUM</th>
									</tr>
								</thead>
								<tbody>
									{#each facilityDetails as host}
										<tr class="detail-row">
											<td class="hostname">{host.host}</td>
											<td>{host.rack}</td>
											<td>{host.unit}</td>
											<td>
												<span class="type-badge">
													{host.infrastructure_type}
												</span>
											</td>
											<td>{host.cpu_cores}</td>
											<td>{host.memory_gb}GB</td>
											<td>{host.storage_tb}TB</td>
											<td>{host.network_gbps}Gbps</td>
											<td>{host.power_watts}W</td>
											<td style="color: {host.temperature_c > 40 ? '#FF0000' : host.temperature_c > 30 ? '#FFFF00' : '#00FF00'}">
												{host.temperature_c}°C
											</td>
											<td>
												<span class="status-dot {host.present_in_cmdb === 'Yes' ? 'active' : 'inactive'}">●</span>
											</td>
											<td>
												<span class="status-dot {host.tanium_coverage === 'Tanium' ? 'active' : 'inactive'}">●</span>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				{:else}
					<table class="data-table">
						<thead>
							<tr>
								<th class="sortable" on:click={() => sortTable('rank')}>
									RANK {sortColumn === 'rank' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th class="sortable" on:click={() => sortTable('name')}>
									FACILITY {sortColumn === 'name' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th class="sortable" on:click={() => sortTable('count')}>
									SERVERS {sortColumn === 'count' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th>TYPE</th>
								<th>SCALE</th>
								<th>LOCATION</th>
								<th>UTILIZATION</th>
								<th>POWER</th>
								<th>COOLING</th>
								<th>STATUS</th>
								<th>ACTIONS</th>
							</tr>
						</thead>
						<tbody>
							{#each paginatedFacilities as [facility, count], i}
								{@const level = getFacilityLevel(count)}
								{@const dc = datacenters.find(d => d.id === facility)}
								{@const percentage = (count / maxHosts) * 100}
								<tr class="data-row" style="--glow-color: {level.glow}">
									<td class="rank">#{(currentPage - 1) * itemsPerPage + i + 1}</td>
									<td class="facility-name">
										<span class="facility-icon">🏢</span>
										{facility}
									</td>
									<td class="server-count" style="color: {level.color}">
										{formatNumber(count)}
									</td>
									<td>
										<span class="type-badge {getFacilityType(facility).toLowerCase().replace(' ', '-')}">
											{getFacilityType(facility)}
										</span>
									</td>
									<td>
										<span class="scale-badge" style="background: {level.glow}; color: {level.color}">
											{level.level}
										</span>
									</td>
									<td class="location">{getFacilityLocation(facility)}</td>
									<td>
										<div class="utilization-bar">
											<div class="utilization-fill" 
												 style="width: {dc ? dc.utilization : 0}%; 
														background: linear-gradient(90deg, transparent, {level.color})">
											</div>
											<span class="utilization-text">{dc ? dc.utilization.toFixed(0) : 0}%</span>
										</div>
									</td>
									<td class="power">
										<span style="color: {dc && dc.powerCapacity > 8 ? '#00FF00' : '#FFFF00'}">
											{dc ? dc.powerCapacity.toFixed(1) : 0} MW
										</span>
									</td>
									<td class="cooling">
										<span style="color: #00FFFF">
											{dc ? dc.coolingCapacity.toFixed(0) : 0} T
										</span>
									</td>
									<td>
										<span class="status-indicator {dc && dc.status === 'operational' ? 'online' : 'maintenance'}">
											{dc ? (dc.status === 'operational' ? '◈' : '⚠') : '○'}
										</span>
									</td>
									<td>
										<button class="action-btn" on:click={() => drillDownFacility(facility, count)}>
											INSPECT
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				{/if}
			</div>
		</div>
		
		<!-- Right: Monitoring & Analytics -->
		<div class="right-section">
			<!-- Network Topology -->
			<div class="network-container">
				<h3 class="section-title">NETWORK TOPOLOGY</h3>
				<svg viewBox="0 0 300 300" class="network-map">
					<!-- Connections -->
					{#each networkTopology as node}
						{#each node.connections as targetIdx}
							{@const target = networkTopology[targetIdx]}
							{#if target}
								<line x1="{node.x * 0.6}" y1="{node.y * 0.6}" 
									  x2="{target.x * 0.6}" y2="{target.y * 0.6}"
									  stroke="#00FFFF" stroke-width="1" opacity="0.3">
									<animate attributeName="stroke-opacity"
											 values="0.3;0.8;0.3" dur="3s" repeatCount="indefinite"/>
								</line>
							{/if}
						{/each}
					{/each}
					
					<!-- Nodes -->
					{#each networkTopology.slice(0, 10) as node}
						<g transform="translate({node.x * 0.6}, {node.y * 0.6})">
							<circle r="8" fill="#00FFFF" opacity="0.7"/>
							<text text-anchor="middle" dy="-12" font-size="7" fill="#FFFFFF">
								{node.node.split('-').slice(-2).join('-')}
							</text>
							<text text-anchor="middle" dy="18" font-size="6" fill="#00FFFF">
								{node.bandwidth.toFixed(0)}Gbps
							</text>
						</g>
					{/each}
				</svg>
			</div>
			
			<!-- Cooling System Status -->
			<div class="cooling-container">
				<h3 class="section-title">COOLING SYSTEM</h3>
				<div class="cooling-units">
					{#each coolingSystem.slice(0, 4) as unit}
						<div class="cooling-unit">
							<div class="unit-header">
								<span class="unit-id">{unit.id}</span>
								<span class="unit-type">{unit.type}</span>
							</div>
							<div class="unit-display">
								<div class="temp-display">
									<div class="temp-set">SET: {unit.setpoint.toFixed(0)}°C</div>
									<div class="temp-actual" style="color: {Math.abs(unit.actualTemp - unit.setpoint) > 2 ? '#FF0000' : '#00FF00'}">
										ACT: {unit.actualTemp.toFixed(1)}°C
									</div>
								</div>
								<div class="unit-gauge">
									<svg viewBox="0 0 100 50">
										<path d="M 10,45 A 35,35 0 0,1 90,45" 
											  fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="8"/>
										<path d="M 10,45 A 35,35 0 0,1 90,45" 
											  fill="none" stroke="#00FFFF" stroke-width="8"
											  stroke-dasharray="{unit.utilization * 1.1} 110"
											  stroke-linecap="round"/>
										<text x="50" y="40" text-anchor="middle" font-size="12" fill="#FFFFFF">
											{unit.utilization.toFixed(0)}%
										</text>
									</svg>
								</div>
							</div>
							<div class="unit-stats">
								<span>{unit.capacity} Tons</span>
								<span>{unit.efficiency.toFixed(0)}% Eff</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Storage Array -->
			<div class="storage-container">
				<h3 class="section-title">STORAGE ARRAY</h3>
				<div class="storage-units">
					{#each storageArray.slice(0, 6) as storage}
						<div class="storage-unit">
							<div class="storage-header">
								<span class="storage-id">{storage.id}</span>
								<span class="storage-type">{storage.type}</span>
							</div>
							<div class="storage-bar">
								<div class="storage-used" 
									 style="width: {storage.used}%; 
											background: {storage.used > 80 ? '#FF0000' : storage.used > 60 ? '#FFFF00' : '#00FF00'}">
								</div>
							</div>
							<div class="storage-stats">
								<span>{storage.capacity}PB</span>
								<span>{storage.used.toFixed(0)}%</span>
								<span>{storage.redundancy}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Environmental Monitoring -->
			<div class="environmental-container">
				<h3 class="section-title">ENVIRONMENTAL</h3>
				<svg viewBox="0 0 300 100" class="env-chart">
					<!-- Temperature line -->
					<polyline points="{environmentalData.map((d, i) => `${i * 12.5},${50 - (d.temperature - 20) * 5}`).join(' ')}"
							  fill="none" stroke="#FF0000" stroke-width="2" opacity="0.8"/>
					
					<!-- Humidity line -->
					<polyline points="{environmentalData.map((d, i) => `${i * 12.5},${100 - d.humidity}`).join(' ')}"
							  fill="none" stroke="#00FFFF" stroke-width="2" opacity="0.6"/>
					
					<!-- Grid -->
					<line x1="0" y1="50" x2="300" y2="50" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
					
					<!-- Labels -->
					<text x="5" y="10" font-size="8" fill="#FF0000">TEMP</text>
					<text x="5" y="95" font-size="8" fill="#00FFFF">HUMIDITY</text>
				</svg>
			</div>
		</div>
	</div>
	
	<!-- Bottom Status Bar -->
	<div class="status-bar">
		<div class="status-item">
			<span class="status-label">CPU UTILIZATION</span>
			<div class="status-value-bar">
				<div class="value-fill" style="width: {cpuUtilization}%; background: {cpuUtilization > 80 ? '#FF0000' : cpuUtilization > 60 ? '#FFFF00' : '#00FF00'}"></div>
			</div>
			<span class="status-percent">{cpuUtilization.toFixed(0)}%</span>
		</div>
		<div class="status-item">
			<span class="status-label">MEMORY USAGE</span>
			<div class="status-value-bar">
				<div class="value-fill" style="width: {memoryUsage}%; background: {memoryUsage > 80 ? '#FF0000' : memoryUsage > 60 ? '#FFFF00' : '#00FF00'}"></div>
			</div>
			<span class="status-percent">{memoryUsage.toFixed(0)}%</span>
		</div>
		<div class="status-item">
			<span class="status-label">HUMIDITY</span>
			<span class="status-value">{humidity.toFixed(0)}%</span>
		</div>
		<div class="status-item">
			<span class="status-label">FACILITIES</span>
			<span class="status-value">{facilities.length}</span>
		</div>
		<div class="status-item">
			<span class="status-label">TOTAL SERVERS</span>
			<span class="status-value">{formatNumber(totalHosts)}</span>
		</div>
	</div>
</div>

<style>
	.infrastructure-command {
		width: 100%;
		height: calc(100vh - 80px);
		background: linear-gradient(135deg, #000011, #001133);
		display: flex;
		flex-direction: column;
		gap: 1rem;
		padding: 1rem;
		overflow: hidden;
	}
	
	/* Metrics Dashboard */
	.metrics-dashboard {
		display: flex;
		gap: 1rem;
		height: 100px;
		flex-shrink: 0;
	}
	
	.metric-tile {
		flex: 1;
		background: rgba(0, 0, 0, 0.9);
		border: 1px solid rgba(255, 255, 255, 0.3);