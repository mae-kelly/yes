<script>
	import { onMount } from 'svelte';
	
	let data = {};
	let loading = true;
	let activeView = 'correlation';
	let selectedMetric = null;
	let aiValidationResults = {};
	
	onMount(async () => {
		try {
			const response = await fetch('http://localhost:5000/api/advanced_analytics');
			data = await response.json();
			loading = false;
			runAiValidation();
		} catch (err) {
			loading = false;
		}
	});
	
	function runAiValidation() {
		const anomalies = detectAnomalies();
		const patterns = identifyPatterns();
		const predictions = generatePredictions();
		
		aiValidationResults = {
			anomalies,
			patterns,
			predictions,
			confidence: calculateConfidenceScore(anomalies, patterns),
			recommendations: generateRecommendations(anomalies, patterns, predictions)
		};
	}
	
	function detectAnomalies() {
		const anomalies = [];
		
		if (data.correlation_analysis) {
			data.correlation_analysis.forEach(item => {
				if (item.security_score < 30 && item.asset_count > 100) {
					anomalies.push({
						type: 'critical_security_gap',
						severity: 'CRITICAL',
						region: item.region,
						infrastructure: item.infrastructure_type,
						assets_affected: item.asset_count,
						message: `Critical security gap detected: ${item.security_score}% coverage for ${item.asset_count} assets`
					});
				}
				
				if (item.business_unit_diversity > 10 && item.datacenter_diversity === 1) {
					anomalies.push({
						type: 'single_point_failure',
						severity: 'HIGH',
						region: item.region,
						infrastructure: item.infrastructure_type,
						message: `Single datacenter supporting ${item.business_unit_diversity} business units`
					});
				}
				
				if (item.cmdb_coverage > 90 && item.tanium_coverage < 20) {
					anomalies.push({
						type: 'coverage_mismatch',
						severity: 'MEDIUM',
						region: item.region,
						infrastructure: item.infrastructure_type,
						message: `CMDB registered but lacking security coverage`
					});
				}
			});
		}
		
		return anomalies;
	}
	
	function identifyPatterns() {
		const patterns = {
			regional: {},
			infrastructure: {},
			security: {},
			business: {}
		};
		
		if (data.correlation_analysis) {
			const regionalGroups = {};
			const infraGroups = {};
			
			data.correlation_analysis.forEach(item => {
				if (!regionalGroups[item.region]) {
					regionalGroups[item.region] = [];
				}
				regionalGroups[item.region].push(item);
				
				if (!infraGroups[item.infrastructure_type]) {
					infraGroups[item.infrastructure_type] = [];
				}
				infraGroups[item.infrastructure_type].push(item);
			});
			
			for (const [region, items] of Object.entries(regionalGroups)) {
				const avgSecurity = items.reduce((sum, i) => sum + i.security_score, 0) / items.length;
				const totalAssets = items.reduce((sum, i) => sum + i.asset_count, 0);
				
				patterns.regional[region] = {
					avg_security_score: avgSecurity.toFixed(2),
					total_assets: totalAssets,
					risk_trend: avgSecurity < 50 ? 'declining' : avgSecurity < 80 ? 'stable' : 'improving',
					diversity_index: new Set(items.map(i => i.infrastructure_type)).size
				};
			}
			
			for (const [infra, items] of Object.entries(infraGroups)) {
				const avgSecurity = items.reduce((sum, i) => sum + i.security_score, 0) / items.length;
				const avgBuDiversity = items.reduce((sum, i) => sum + i.business_unit_diversity, 0) / items.length;
				
				patterns.infrastructure[infra] = {
					avg_security_score: avgSecurity.toFixed(2),
					avg_business_diversity: avgBuDiversity.toFixed(2),
					deployment_complexity: avgBuDiversity > 5 ? 'complex' : 'simple',
					modernization_candidate: infra.toLowerCase().includes('legacy') || avgSecurity < 40
				};
			}
			
			const securityBands = { critical: 0, high: 0, medium: 0, low: 0 };
			data.correlation_analysis.forEach(item => {
				if (item.security_score < 30) securityBands.critical++;
				else if (item.security_score < 50) securityBands.high++;
				else if (item.security_score < 80) securityBands.medium++;
				else securityBands.low++;
			});
			patterns.security = securityBands;
		}
		
		return patterns;
	}
	
	function generatePredictions() {
		const predictions = {
			risk_trajectory: [],
			improvement_areas: [],
			incident_probability: {},
			resource_requirements: {}
		};
		
		if (data.trend_analysis) {
			for (const [region, metrics] of Object.entries(data.trend_analysis)) {
				const riskScore = 100 - metrics.avg_security_score;
				const incidentProbability = Math.min(95, riskScore * 1.2);
				
				predictions.incident_probability[region] = {
					probability: incidentProbability.toFixed(1),
					severity: incidentProbability > 70 ? 'CRITICAL' : incidentProbability > 40 ? 'HIGH' : 'MEDIUM',
					timeframe: '30_days'
				};
				
				if (metrics.high_risk_segments > 2) {
					predictions.risk_trajectory.push({
						region,
						trend: 'ESCALATING',
						segments_at_risk: metrics.high_risk_segments,
						projected_incidents: Math.ceil(metrics.total_assets * 0.001 * riskScore),
						mitigation_priority: 'URGENT'
					});
				}
				
				const resourceNeed = Math.ceil(metrics.total_assets * (100 - metrics.avg_security_score) / 1000);
				predictions.resource_requirements[region] = {
					security_agents: resourceNeed,
					cmdb_registrations: Math.ceil(resourceNeed * 0.7),
					estimated_hours: resourceNeed * 4,
					priority_level: metrics.avg_security_score < 50 ? 'CRITICAL' : 'STANDARD'
				};
			}
		}
		
		if (data.high_risk_combinations) {
			data.high_risk_combinations.forEach(combo => {
				predictions.improvement_areas.push({
					region: combo.region,
					infrastructure: combo.infrastructure_type,
					current_security: combo.security_score,
					target_security: 80,
					gap_to_close: 80 - combo.security_score,
					estimated_timeline: Math.ceil((80 - combo.security_score) / 10) + ' weeks',
					assets_to_secure: combo.asset_count
				});
			});
		}
		
		return predictions;
	}
	
	function calculateConfidenceScore(anomalies, patterns) {
		const dataCompleteness = data.correlation_analysis ? data.correlation_analysis.length : 0;
		const anomalyFactor = Math.max(0, 100 - (anomalies.length * 5));
		const patternConsistency = Object.keys(patterns.regional || {}).length > 0 ? 80 : 40;
		
		return Math.round((dataCompleteness > 10 ? 70 : 40) + (anomalyFactor / 5) + (patternConsistency / 10));
	}
	
	function generateRecommendations(anomalies, patterns, predictions) {
		const recommendations = [];
		
		const criticalAnomalies = anomalies.filter(a => a.severity === 'CRITICAL');
		if (criticalAnomalies.length > 0) {
			recommendations.push({
				priority: 'IMMEDIATE',
				action: 'Deploy Security Coverage',
				targets: criticalAnomalies.map(a => `${a.region} - ${a.infrastructure}`),
				impact: criticalAnomalies.reduce((sum, a) => sum + (a.assets_affected || 0), 0),
				timeline: '1 week'
			});
		}
		
		const highRiskRegions = Object.entries(patterns.regional || {})
			.filter(([_, data]) => data.risk_trend === 'declining')
			.map(([region]) => region);
		
		if (highRiskRegions.length > 0) {
			recommendations.push({
				priority: 'HIGH',
				action: 'Regional Security Reinforcement',
				targets: highRiskRegions,
				impact: 'Prevent security degradation',
				timeline: '2 weeks'
			});
		}
		
		const modernizationCandidates = Object.entries(patterns.infrastructure || {})
			.filter(([_, data]) => data.modernization_candidate)
			.map(([infra]) => infra);
		
		if (modernizationCandidates.length > 0) {
			recommendations.push({
				priority: 'MEDIUM',
				action: 'Infrastructure Modernization',
				targets: modernizationCandidates,
				impact: 'Improve security posture and reduce technical debt',
				timeline: '3 months'
			});
		}
		
		const resourceCritical = Object.entries(predictions.resource_requirements || {})
			.filter(([_, req]) => req.priority_level === 'CRITICAL');
		
		if (resourceCritical.length > 0) {
			recommendations.push({
				priority: 'HIGH',
				action: 'Resource Allocation',
				targets: resourceCritical.map(([region]) => region),
				impact: `${resourceCritical.reduce((sum, [_, req]) => sum + req.security_agents, 0)} security agents needed`,
				timeline: '1 month'
			});
		}
		
		return recommendations;
	}
	
	function selectMetric(metric) {
		selectedMetric = selectedMetric === metric ? null : metric;
	}
	
	$: correlationData = data.correlation_analysis || [];
	$: trendData = data.trend_analysis || {};
	$: riskCombinations = data.high_risk_combinations || [];
	$: insights = data.predictive_insights || {};
</script>

<div class="advanced-analytics-matrix">
	<div class="matrix-header">
		<div class="neural-interface">
			<div class="neural-core">
				<div class="core-rings">
					<div class="ring ring-1"></div>
					<div class="ring ring-2"></div>
					<div class="ring ring-3"></div>
				</div>
				<div class="core-symbol">◎</div>
			</div>
			<div class="interface-info">
				<h2>ADVANCED ANALYTICS</h2>
				<p>AI-POWERED THREAT INTELLIGENCE</p>
			</div>
		</div>
		
		<div class="view-selector">
			<button class="view-btn {activeView === 'correlation' ? 'active' : ''}" on:click={() => activeView = 'correlation'}>
				<span class="btn-icon">◈</span>
				CORRELATION
			</button>
			<button class="view-btn {activeView === 'predictions' ? 'active' : ''}" on:click={() => activeView = 'predictions'}>
				<span class="btn-icon">◆</span>
				PREDICTIONS
			</button>
			<button class="view-btn {activeView === 'validation' ? 'active' : ''}" on:click={() => activeView = 'validation'}>
				<span class="btn-icon">◉</span>
				AI VALIDATION
			</button>
		</div>
	</div>

	{#if loading}
		<div class="quantum-loading">
			<div class="quantum-core">
				<div class="quantum-particle"></div>
				<div class="quantum-field">
					{#each Array(8) as _, i}
						<div class="field-wave" style="animation-delay: {i * 0.2}s"></div>
					{/each}
				</div>
			</div>
			<p>PROCESSING QUANTUM ALGORITHMS...</p>
		</div>
	{:else}
		{#if activeView === 'correlation'}
			<div class="correlation-matrix">
				<div class="matrix-grid">
					{#each correlationData.slice(0, 20) as item, i}
						<div class="correlation-node" 
							 class:high-risk={item.risk_category === 'HIGH'}
							 style="animation-delay: {i * 0.05}s"
							 on:click={() => selectMetric(item)}>
							<div class="node-header">
								<div class="region-badge">{item.region.toUpperCase()}</div>
								<div class="risk-indicator {item.risk_category.toLowerCase()}">{item.risk_category}</div>
							</div>
							
							<div class="node-metrics">
								<div class="metric-row">
									<span class="metric-label">Infrastructure:</span>
									<span class="metric-value">{item.infrastructure_type}</span>
								</div>
								<div class="metric-row">
									<span class="metric-label">Assets:</span>
									<span class="metric-value">{item.asset_count.toLocaleString()}</span>
								</div>
								<div class="metric-row">
									<span class="metric-label">Security:</span>
									<span class="metric-value security-score" style="--score: {item.security_score}">{item.security_score}%</span>
								</div>
							</div>
							
							<div class="coverage-bars">
								<div class="coverage-bar">
									<div class="bar-label">CMDB</div>
									<div class="bar-track">
										<div class="bar-fill cmdb" style="width: {item.cmdb_coverage}%"></div>
									</div>
									<div class="bar-value">{item.cmdb_coverage}%</div>
								</div>
								<div class="coverage-bar">
									<div class="bar-label">TANIUM</div>
									<div class="bar-track">
										<div class="bar-fill tanium" style="width: {item.tanium_coverage}%"></div>
									</div>
									<div class="bar-value">{item.tanium_coverage}%</div>
								</div>
							</div>
							
							<div class="diversity-metrics">
								<div class="diversity-item">
									<span class="diversity-value">{item.business_unit_diversity}</span>
									<span class="diversity-label">BUs</span>
								</div>
								<div class="diversity-item">
									<span class="diversity-value">{item.datacenter_diversity}</span>
									<span class="diversity-label">DCs</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
				
				{#if selectedMetric}
					<div class="metric-detail-panel">
						<div class="panel-header">
							<h3>DETAILED ANALYSIS</h3>
							<button class="close-btn" on:click={() => selectedMetric = null}>✕</button>
						</div>
						<div class="detail-content">
							<div class="detail-section">
								<h4>{selectedMetric.region.toUpperCase()} - {selectedMetric.infrastructure_type}</h4>
								<div class="security-assessment">
									<div class="assessment-score" style="--color: {selectedMetric.security_score < 50 ? '#ff0066' : selectedMetric.security_score < 80 ? '#ffaa00' : '#00ff85'}">
										{selectedMetric.security_score}%
									</div>
									<div class="assessment-status">{selectedMetric.risk_category} RISK</div>
								</div>
							</div>
							<div class="detail-metrics">
								<div class="metric-card">
									<div class="card-value">{selectedMetric.asset_count.toLocaleString()}</div>
									<div class="card-label">Total Assets</div>
								</div>
								<div class="metric-card">
									<div class="card-value">{selectedMetric.cmdb_coverage}%</div>
									<div class="card-label">CMDB Coverage</div>
								</div>
								<div class="metric-card">
									<div class="card-value">{selectedMetric.tanium_coverage}%</div>
									<div class="card-label">Tanium Coverage</div>
								</div>
								<div class="metric-card">
									<div class="card-value">{selectedMetric.business_unit_diversity}</div>
									<div class="card-label">Business Units</div>
								</div>
							</div>
						</div>
					</div>
				{/if}
			</div>
		{:else if activeView === 'predictions'}
			<div class="predictions-interface">
				<div class="prediction-grid">
					<div class="prediction-panel risk-trajectory">
						<div class="panel-header">
							<div class="header-icon">⚡</div>
							<h3>RISK TRAJECTORY</h3>
						</div>
						<div class="trajectory-list">
							{#each aiValidationResults.predictions?.risk_trajectory || [] as trajectory}
								<div class="trajectory-item {trajectory.trend.toLowerCase()}">
									<div class="item-header">
										<span class="region">{trajectory.region.toUpperCase()}</span>
										<span class="trend-badge">{trajectory.trend}</span>
									</div>
									<div class="item-metrics">
										<div class="metric">
											<span class="value">{trajectory.segments_at_risk}</span>
											<span class="label">Risk Segments</span>
										</div>
										<div class="metric">
											<span class="value">{trajectory.projected_incidents}</span>
											<span class="label">Projected Incidents</span>
										</div>
									</div>
									<div class="priority-indicator {trajectory.mitigation_priority.toLowerCase()}">
										{trajectory.mitigation_priority} PRIORITY
									</div>
								</div>
							{/each}
						</div>
					</div>
					
					<div class="prediction-panel incident-probability">
						<div class="panel-header">
							<div class="header-icon">⚠</div>
							<h3>INCIDENT PROBABILITY</h3>
						</div>
						<div class="probability-grid">
							{#each Object.entries(aiValidationResults.predictions?.incident_probability || {}) as [region, data]}
								<div class="probability-card {data.severity.toLowerCase()}">
									<div class="card-region">{region.toUpperCase()}</div>
									<div class="probability-meter">
										<svg width="80" height="80" viewBox="0 0 80 80">
											<circle cx="40" cy="40" r="35" fill="none" stroke="rgba(255, 255, 255, 0.1)" stroke-width="3"/>
											<circle 
												cx="40" cy="40" r="35" 
												fill="none" 
												stroke={data.severity === 'CRITICAL' ? '#ff0066' : data.severity === 'HIGH' ? '#ffaa00' : '#0096ff'}
												stroke-width="3"
												stroke-dasharray="220"
												stroke-dashoffset={220 - (data.probability / 100 * 220)}
												transform="rotate(-90 40 40)"
											/>
										</svg>
										<div class="probability-value">{data.probability}%</div>
									</div>
									<div class="timeframe">Next {data.timeframe.replace('_', ' ')}</div>
								</div>
							{/each}
						</div>
					</div>
					
					<div class="prediction-panel resource-requirements">
						<div class="panel-header">
							<div class="header-icon">📊</div>
							<h3>RESOURCE REQUIREMENTS</h3>
						</div>
						<div class="resource-list">
							{#each Object.entries(aiValidationResults.predictions?.resource_requirements || {}) as [region, req]}
								<div class="resource-item">
									<div class="item-region">{region.toUpperCase()}</div>
									<div class="resource-metrics">
										<div class="resource-stat">
											<span class="stat-value">{req.security_agents}</span>
											<span class="stat-label">Agents</span>
										</div>
										<div class="resource-stat">
											<span class="stat-value">{req.cmdb_registrations}</span>
											<span class="stat-label">CMDB</span>
										</div>
										<div class="resource-stat">
											<span class="stat-value">{req.estimated_hours}</span>
											<span class="stat-label">Hours</span>
										</div>
									</div>
									<div class="priority-level {req.priority_level.toLowerCase()}">
										{req.priority_level}
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>
			</div>
		{:else if activeView === 'validation'}
			<div class="ai-validation-interface">
				<div class="validation-header">
					<div class="confidence-meter">
						<div class="meter-label">AI CONFIDENCE</div>
						<div class="meter-display">
							<div class="confidence-ring">
								<svg width="120" height="120" viewBox="0 0 120 120">
									<circle cx="60" cy="60" r="50" fill="none" stroke="rgba(0, 255, 255, 0.2)" stroke-width="3"/>
									<circle 
										cx="60" cy="60" r="50" 
										fill="none" 
										stroke="#00ffff" 
										stroke-width="5"
										stroke-dasharray="314"
										stroke-dashoffset={314 - ((aiValidationResults.confidence || 0) / 100 * 314)}
										transform="rotate(-90 60 60)"
									/>
								</svg>
								<div class="confidence-value">{aiValidationResults.confidence || 0}%</div>
							</div>
						</div>
					</div>
					
					<div class="validation-stats">
						<div class="stat-card">
							<div class="stat-value">{aiValidationResults.anomalies?.length || 0}</div>
							<div class="stat-label">Anomalies Detected</div>
						</div>
						<div class="stat-card">
							<div class="stat-value">{Object.keys(aiValidationResults.patterns?.regional || {}).length}</div>
							<div class="stat-label">Patterns Identified</div>
						</div>
						<div class="stat-card">
							<div class="stat-value">{aiValidationResults.recommendations?.length || 0}</div>
							<div class="stat-label">Recommendations</div>
						</div>
					</div>
				</div>
				
				<div class="validation-content">
					<div class="anomaly-section">
						<h3>🔍 DETECTED ANOMALIES</h3>
						<div class="anomaly-list">
							{#each aiValidationResults.anomalies || [] as anomaly}
								<div class="anomaly-item {anomaly.severity.toLowerCase()}">
									<div class="anomaly-header">
										<span class="severity-badge">{anomaly.severity}</span>
										<span class="anomaly-type">{anomaly.type.replace(/_/g, ' ').toUpperCase()}</span>
									</div>
									<div class="anomaly-details">
										<div class="detail-text">{anomaly.message}</div>
										<div class="affected-info">
											<span class="region">{anomaly.region}</span>
											<span class="infrastructure">{anomaly.infrastructure}</span>
											{#if anomaly.assets_affected}
												<span class="assets">{anomaly.assets_affected.toLocaleString()} assets</span>
											{/if}
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
					
					<div class="patterns-section">
						<h3>🔗 IDENTIFIED PATTERNS</h3>
						<div class="pattern-grid">
							<div class="pattern-category">
								<h4>Regional Patterns</h4>
								{#each Object.entries(aiValidationResults.patterns?.regional || {}).slice(0, 5) as [region, pattern]}
									<div class="pattern-item">
										<div class="pattern-name">{region.toUpperCase()}</div>
										<div class="pattern-data">
											<span class="data-point">Security: {pattern.avg_security_score}%</span>
											<span class="data-point">Trend: {pattern.risk_trend}</span>
											<span class="data-point">Assets: {pattern.total_assets.toLocaleString()}</span>
										</div>
									</div>
								{/each}
							</div>
							
							<div class="pattern-category">
								<h4>Security Distribution</h4>
								<div class="security-bands">
									{#each Object.entries(aiValidationResults.patterns?.security || {}) as [band, count]}
										<div class="band-item">
											<div class="band-name">{band.toUpperCase()}</div>
											<div class="band-bar">
												<div class="bar-fill" style="width: {(count / correlationData.length * 100)}%"></div>
											</div>
											<div class="band-count">{count}</div>
										</div>
									{/each}
								</div>
							</div>
						</div>
					</div>
					
					<div class="recommendations-section">
						<h3>💡 AI RECOMMENDATIONS</h3>
						<div class="recommendation-list">
							{#each aiValidationResults.recommendations || [] as rec, i}
								<div class="recommendation-card" style="animation-delay: {i * 0.1}s">
									<div class="rec-header">
										<span class="priority-badge {rec.priority.toLowerCase()}">{rec.priority}</span>
										<span class="action-type">{rec.action}</span>
									</div>
									<div class="rec-content">
										<div class="targets">
											<strong>Targets:</strong>
											{#each rec.targets.slice(0, 3) as target}
												<span class="target-chip">{target}</span>
											{/each}
											{#if rec.targets.length > 3}
												<span class="more-chip">+{rec.targets.length - 3} more</span>
											{/if}
										</div>
										<div class="impact">
											<strong>Impact:</strong> {rec.impact}
										</div>
										<div class="timeline">
											<strong>Timeline:</strong> {rec.timeline}
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>
			</div>
		{/if}
	{/if}
	
	<div class="interface-footer">
		<div class="footer-line"></div>
		<div class="protocol-notice">
			◎ ADVANCED ANALYTICS // AI-POWERED THREAT INTELLIGENCE ACTIVE
		</div>
	</div>
</div>

<style>
	.advanced-analytics-matrix {
		width: 100%;
		height: 100%;
		font-family: 'Orbitron', 'Exo 2', monospace;
		color: #fff;
		display: flex;
		flex-direction: column;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.matrix-header {
		background: linear-gradient(135deg, 
			rgba(0, 0, 0, 0.8) 0%, 
			rgba(255, 0, 255, 0.05) 50%,
			rgba(0, 0, 0, 0.8) 100%);
		border: 2px solid #ff00ff;
		border-radius: 12px;
		padding: 1.5rem 2rem;
		margin-bottom: 1.5rem;
		backdrop-filter: blur(20px);
		box-shadow: 0 0 40px rgba(255, 0, 255, 0.2);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.neural-interface {
		display: flex;
		align-items: center;
		gap: 2rem;
	}

	.neural-core {
		position: relative;
		width: 80px;
		height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.core-rings {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.ring {
		position: absolute;
		border-radius: 50%;
		border: 2px solid;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		animation: ringRotate 10s linear infinite;
	}

	.ring-1 {
		width: 80px;
		height: 80px;
		border-color: #ff00ff;
		opacity: 0.8;
	}

	.ring-2 {
		width: 60px;
		height: 60px;
		border-color: #cc00cc;
		opacity: 0.6;
		animation-direction: reverse;
		animation-duration: 8s;
	}

	.ring-3 {
		width: 40px;
		height: 40px;
		border-color: #990099;
		animation-duration: 6s;
	}

	.core-symbol {
		position: relative;
		z-index: 3;
		font-size: 2rem;
		color: #ff00ff;
		text-shadow: 0 0 25px #ff00ff;
		animation: symbolPulse 3s ease-in-out infinite;
	}

	.interface-info h2 {
		margin: 0;
		font-size: 1.5rem;
		color: #fff;
		text-shadow: 0 0 15px rgba(255, 0, 255, 0.5);
		letter-spacing: 0.1em;
	}

	.interface-info p {
		margin: 0.3rem 0 0 0;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.6);
		font-weight: 300;
	}

	.view-selector {
		display: flex;
		gap: 1rem;
	}

	.view-btn {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 0, 255, 0.02));
		border: 2px solid rgba(255, 0, 255, 0.3);
		border-radius: 8px;
		padding: 0.8rem 1.5rem;
		color: rgba(255, 255, 255, 0.7);
		font-family: inherit;
		font-size: 0.8rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.view-btn:hover,
	.view-btn.active {
		border-color: #ff00ff;
		color: #ff00ff;
		box-shadow: 0 0 20px rgba(255, 0, 255, 0.3);
		text-shadow: 0 0 8px #ff00ff;
	}

	.btn-icon {
		font-size: 1rem;
		animation: iconFloat 3s ease-in-out infinite;
	}

	.quantum-loading {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2rem;
	}

	.quantum-core {
		position: relative;
		width: 150px;
		height: 150px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.quantum-particle {
		width: 30px;
		height: 30px;
		background: radial-gradient(circle, #ff00ff, transparent);
		border-radius: 50%;
		animation: particleSpin 2s linear infinite;
	}

	.quantum-field {
		position: absolute;
		width: 100%;
		height: 100%;
	}

	.field-wave {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid #ff00ff;
		border-radius: 50%;
		animation: waveExpand 2s ease-in-out infinite;
		opacity: 0;
	}

	.correlation-matrix {
		flex: 1;
		overflow-y: auto;
	}

	.matrix-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.correlation-node {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(255, 255, 255, 0.02));
		border: 2px solid rgba(255, 0, 255, 0.3);
		border-radius: 12px;
		padding: 1.5rem;
		cursor: pointer;
		transition: all 0.3s ease;
		animation: nodeEntrance 0.6s ease-out;
		animation-fill-mode: both;
		opacity: 0;
	}

	.correlation-node:hover {
		transform: translateY(-5px);
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 30px rgba(255, 0, 255, 0.3);
	}

	.correlation-node.high-risk {
		border-color: #ff0066;
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.05), rgba(0, 0, 0, 0.8));
	}

	.node-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.region-badge {
		padding: 0.3rem 0.8rem;
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid #00ffff;
		border-radius: 4px;
		font-size: 0.7rem;
		font-weight: 600;
		color: #00ffff;
		text-shadow: 0 0 8px #00ffff;
	}

	.risk-indicator {
		padding: 0.3rem 0.8rem;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.risk-indicator.high {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
		text-shadow: 0 0 8px #ff0066;
	}

	.risk-indicator.medium {
		background: rgba(255, 170, 0, 0.2);
		color: #ffaa00;
		border: 1px solid #ffaa00;
		text-shadow: 0 0 8px #ffaa00;
	}

	.risk-indicator.low {
		background: rgba(0, 255, 133, 0.2);
		color: #00ff85;
		border: 1px solid #00ff85;
		text-shadow: 0 0 8px #00ff85;
	}

	.node-metrics {
		margin-bottom: 1rem;
	}

	.metric-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.3rem 0;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}

	.metric-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.metric-value {
		font-size: 0.8rem;
		font-weight: 600;
		color: #fff;
	}

	.security-score {
		color: #00ffff;
		text-shadow: 0 0 8px #00ffff;
	}

	.coverage-bars {
		margin-bottom: 1rem;
	}

	.coverage-bar {
		display: grid;
		grid-template-columns: 60px 1fr 50px;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.bar-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.7);
	}

	.bar-track {
		height: 6px;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 3px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		border-radius: 3px;
		transition: width 1s ease-out;
	}

	.bar-fill.cmdb {
		background: linear-gradient(90deg, #00ff85, #00cc6a);
		box-shadow: 0 0 8px rgba(0, 255, 133, 0.5);
	}

	.bar-fill.tanium {
		background: linear-gradient(90deg, #0096ff, #0077cc);
		box-shadow: 0 0 8px rgba(0, 150, 255, 0.5);
	}

	.bar-value {
		font-size: 0.7rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.8);
		text-align: right;
	}

	.diversity-metrics {
		display: flex;
		justify-content: space-around;
		align-items: center;
		padding-top: 1rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}

	.diversity-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.2rem;
	}

	.diversity-value {
		font-size: 1.2rem;
		font-weight: 700;
		color: #ff00ff;
		text-shadow: 0 0 10px #ff00ff;
	}

	.diversity-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.metric-detail-panel {
		position: fixed;
		right: 2rem;
		top: 50%;
		transform: translateY(-50%);
		width: 400px;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.95), rgba(255, 0, 255, 0.05));
		border: 2px solid #ff00ff;
		border-radius: 12px;
		padding: 2rem;
		backdrop-filter: blur(20px);
		box-shadow: 0 0 50px rgba(255, 0, 255, 0.3);
		animation: panelSlide 0.5s ease-out;
		z-index: 100;
	}

	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.panel-header h3 {
		margin: 0;
		font-size: 1rem;
		color: #ff00ff;
		text-shadow: 0 0 10px #ff00ff;
	}

	.close-btn {
		background: transparent;
		border: 1px solid #ff00ff;
		border-radius: 50%;
		width: 30px;
		height: 30px;
		color: #ff00ff;
		font-size: 1rem;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-btn:hover {
		background: rgba(255, 0, 255, 0.1);
		transform: rotate(90deg);
	}

	.detail-section h4 {
		margin: 0 0 1rem 0;
		font-size: 0.9rem;
		color: rgba(255, 255, 255, 0.9);
	}

	.security-assessment {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.assessment-score {
		font-size: 2.5rem;
		font-weight: 700;
		color: var(--color);
		text-shadow: 0 0 20px var(--color);
	}

	.assessment-status {
		font-size: 0.8rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.7);
	}

	.detail-metrics {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
	}

	.metric-card {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		padding: 1rem;
		text-align: center;
	}

	.card-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #ff00ff;
		text-shadow: 0 0 10px #ff00ff;
		margin-bottom: 0.3rem;
	}

	.card-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		text-transform: uppercase;
	}

	.predictions-interface {
		flex: 1;
		overflow-y: auto;
	}

	.prediction-grid {
		display: grid;
		gap: 2rem;
	}

	.prediction-panel {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 0, 255, 0.02));
		border: 2px solid rgba(255, 0, 255, 0.3);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
	}

	.panel-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.header-icon {
		font-size: 1.5rem;
		animation: iconPulse 3s ease-in-out infinite;
	}

	.panel-header h3 {
		margin: 0;
		font-size: 1.1rem;
		color: #ff00ff;
		letter-spacing: 0.05em;
	}

	.trajectory-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.trajectory-item {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		padding: 1rem;
	}

	.trajectory-item.escalating {
		border-left: 4px solid #ff0066;
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.05), rgba(0, 0, 0, 0.4));
	}

	.item-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.8rem;
	}

	.region {
		font-size: 0.9rem;
		font-weight: 600;
		color: #fff;
	}

	.trend-badge {
		padding: 0.2rem 0.6rem;
		background: rgba(255, 0, 102, 0.2);
		border: 1px solid #ff0066;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 600;
		color: #ff0066;
		text-shadow: 0 0 6px #ff0066;
	}

	.item-metrics {
		display: flex;
		gap: 2rem;
		margin-bottom: 0.8rem;
	}

	.metric {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.metric .value {
		font-size: 1.2rem;
		font-weight: 700;
		color: #ff00ff;
		text-shadow: 0 0 8px #ff00ff;
	}

	.metric .label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		margin-top: 0.2rem;
	}

	.priority-indicator {
		padding: 0.4rem 0.8rem;
		border-radius: 4px;
		font-size: 0.7rem;
		font-weight: 600;
		text-align: center;
		text-transform: uppercase;
	}

	.priority-indicator.urgent {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
		text-shadow: 0 0 8px #ff0066;
	}

	.probability-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1.5rem;
	}

	.probability-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.8rem;
		padding: 1rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
	}

	.card-region {
		font-size: 0.8rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.9);
	}

	.probability-meter {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.probability-value {
		position: absolute;
		font-size: 1.2rem;
		font-weight: 700;
		color: #ff00ff;
		text-shadow: 0 0 10px #ff00ff;
	}

	.timeframe {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
		text-transform: uppercase;
	}

	.resource-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.resource-item {
		display: grid;
		grid-template-columns: 150px 1fr auto;
		gap: 1rem;
		align-items: center;
		padding: 1rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
	}

	.item-region {
		font-size: 0.8rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.9);
	}

	.resource-metrics {
		display: flex;
		gap: 2rem;
	}

	.resource-stat {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.stat-value {
		font-size: 1rem;
		font-weight: 700;
		color: #ff00ff;
		text-shadow: 0 0 8px #ff00ff;
	}

	.stat-label {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.priority-level {
		padding: 0.3rem 0.8rem;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 600;
	}

	.priority-level.critical {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
		text-shadow: 0 0 6px #ff0066;
	}

	.priority-level.standard {
		background: rgba(0, 150, 255, 0.2);
		color: #0096ff;
		border: 1px solid #0096ff;
		text-shadow: 0 0 6px #0096ff;
	}

	.ai-validation-interface {
		flex: 1;
		overflow-y: auto;
	}

	.validation-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		padding: 1.5rem;
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 255, 255, 0.02));
		border: 2px solid rgba(0, 255, 255, 0.3);
		border-radius: 12px;
	}

	.confidence-meter {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.meter-label {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
		letter-spacing: 0.05em;
	}

	.confidence-ring {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.confidence-value {
		position: absolute;
		font-size: 1.5rem;
		font-weight: 700;
		color: #00ffff;
		text-shadow: 0 0 15px #00ffff;
	}

	.validation-stats {
		display: flex;
		gap: 2rem;
	}

	.stat-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.3rem;
		padding: 1rem;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
	}

	.validation-content {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.anomaly-section,
	.patterns-section,
	.recommendations-section {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(255, 0, 255, 0.02));
		border: 2px solid rgba(255, 0, 255, 0.2);
		border-radius: 12px;
		padding: 1.5rem;
		backdrop-filter: blur(20px);
	}

	.anomaly-section h3,
	.patterns-section h3,
	.recommendations-section h3 {
		margin: 0 0 1rem 0;
		font-size: 1rem;
		color: #ff00ff;
		text-shadow: 0 0 10px #ff00ff;
		letter-spacing: 0.05em;
	}

	.anomaly-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.anomaly-item {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		padding: 1rem;
	}

	.anomaly-item.critical {
		border-left: 4px solid #ff0066;
		background: linear-gradient(135deg, rgba(255, 0, 102, 0.05), rgba(0, 0, 0, 0.4));
	}

	.anomaly-item.high {
		border-left: 4px solid #ffaa00;
		background: linear-gradient(135deg, rgba(255, 170, 0, 0.05), rgba(0, 0, 0, 0.4));
	}

	.anomaly-item.medium {
		border-left: 4px solid #0096ff;
		background: linear-gradient(135deg, rgba(0, 150, 255, 0.05), rgba(0, 0, 0, 0.4));
	}

	.anomaly-header {
		display: flex;
		gap: 1rem;
		align-items: center;
		margin-bottom: 0.8rem;
	}

	.severity-badge {
		padding: 0.2rem 0.6rem;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 700;
	}

	.anomaly-item.critical .severity-badge {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
		text-shadow: 0 0 6px #ff0066;
	}

	.anomaly-type {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.anomaly-details {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.detail-text {
		font-size: 0.8rem;
		color: rgba(255, 255, 255, 0.7);
		line-height: 1.4;
	}

	.affected-info {
		display: flex;
		gap: 1rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.pattern-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1.5rem;
	}

	.pattern-category h4 {
		margin: 0 0 1rem 0;
		font-size: 0.9rem;
		color: #00ffff;
		text-shadow: 0 0 8px #00ffff;
	}

	.pattern-item {
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 6px;
		padding: 0.8rem;
		margin-bottom: 0.8rem;
	}

	.pattern-name {
		font-size: 0.8rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.9);
		margin-bottom: 0.5rem;
	}

	.pattern-data {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.data-point {
		font-size: 0.6rem;
		color: rgba(255, 255, 255, 0.6);
	}

	.security-bands {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.band-item {
		display: grid;
		grid-template-columns: 80px 1fr 50px;
		align-items: center;
		gap: 0.5rem;
	}

	.band-name {
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.8);
	}

	.band-bar {
		height: 8px;
		background: rgba(0, 0, 0, 0.4);
		border-radius: 4px;
		overflow: hidden;
	}

	.band-bar .bar-fill {
		height: 100%;
		background: linear-gradient(90deg, #ff00ff, #cc00cc);
		border-radius: 4px;
		box-shadow: 0 0 8px rgba(255, 0, 255, 0.5);
	}

	.band-count {
		font-size: 0.7rem;
		font-weight: 600;
		color: #ff00ff;
		text-align: right;
		text-shadow: 0 0 6px #ff00ff;
	}

	.recommendation-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.recommendation-card {
		background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		padding: 1rem;
		animation: cardSlide 0.6s ease-out;
		animation-fill-mode: both;
		opacity: 0;
	}

	.rec-header {
		display: flex;
		gap: 1rem;
		align-items: center;
		margin-bottom: 1rem;
	}

	.priority-badge {
		padding: 0.3rem 0.6rem;
		border-radius: 4px;
		font-size: 0.6rem;
		font-weight: 700;
		text-transform: uppercase;
	}

	.priority-badge.immediate {
		background: rgba(255, 0, 102, 0.2);
		color: #ff0066;
		border: 1px solid #ff0066;
		text-shadow: 0 0 6px #ff0066;
	}

	.priority-badge.high {
		background: rgba(255, 170, 0, 0.2);
		color: #ffaa00;
		border: 1px solid #ffaa00;
		text-shadow: 0 0 6px #ffaa00;
	}

	.priority-badge.medium {
		background: rgba(0, 150, 255, 0.2);
		color: #0096ff;
		border: 1px solid #0096ff;
		text-shadow: 0 0 6px #0096ff;
	}

	.action-type {
		font-size: 0.8rem;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.9);
	}

	.rec-content {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		font-size: 0.7rem;
		color: rgba(255, 255, 255, 0.7);
		line-height: 1.4;
	}

	.targets {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		align-items: center;
	}

	.target-chip {
		padding: 0.2rem 0.5rem;
		background: rgba(0, 255, 255, 0.1);
		border: 1px solid #00ffff;
		border-radius: 3px;
		font-size: 0.6rem;
		color: #00ffff;
		text-shadow: 0 0 4px #00ffff;
	}

	.more-chip {
		padding: 0.2rem 0.5rem;
		background: rgba(255, 0, 255, 0.1);
		border: 1px solid #ff00ff;
		border-radius: 3px;
		font-size: 0.6rem;
		color: #ff00ff;
		text-shadow: 0 0 4px #ff00ff;
	}

	.interface-footer {
		padding-top: 1rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		text-align: center;
		margin-top: 1rem;
	}

	.footer-line {
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, 
			transparent, 
			rgba(255, 0, 255, 0.6), 
			transparent);
		margin-bottom: 1rem;
	}

	.protocol-notice {
		font-size: 0.7rem;
		color: #ff00ff;
		font-weight: 600;
		letter-spacing: 0.05em;
		text-shadow: 0 0 8px #ff00ff;
	}

	@keyframes ringRotate {
		0% { transform: translate(-50%, -50%) rotate(0deg); }
		100% { transform: translate(-50%, -50%) rotate(360deg); }
	}

	@keyframes symbolPulse {
		0%, 100% { 
			text-shadow: 0 0 25px #ff00ff; 
			transform: scale(1);
		}
		50% { 
			text-shadow: 0 0 35px #ff00ff; 
			transform: scale(1.05);
		}
	}

	@keyframes iconFloat {
		0%, 100% { transform: translateY(0px); }
		50% { transform: translateY(-3px); }
	}

	@keyframes particleSpin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	@keyframes waveExpand {
		0% { 
			transform: scale(0.3); 
			opacity: 1;
		}
		100% { 
			transform: scale(1.5); 
			opacity: 0;
		}
	}

	@keyframes nodeEntrance {
		0% { 
			opacity: 0; 
			transform: translateY(30px);
		}
		100% { 
			opacity: 1; 
			transform: translateY(0);
		}
	}

	@keyframes panelSlide {
		0% { 
			opacity: 0; 
			transform: translateX(50px) translateY(-50%);
		}
		100% { 
			opacity: 1; 
			transform: translateX(0) translateY(-50%);
		}
	}

	@keyframes iconPulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.8; transform: scale(1.1); }
	}

	@keyframes cardSlide {
		0% { 
			opacity: 0; 
			transform: translateY(20px);
		}
		100% { 
			opacity: 1; 
			transform: translateY(0);
		}
	}

	@media (max-width: 1400px) {
		.matrix-grid {
			grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		}

		.metric-detail-panel {
			width: 350px;
			right: 1rem;
		}

		.pattern-grid {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 768px) {
		.matrix-header {
			flex-direction: column;
			gap: 1.5rem;
			text-align: center;
		}

		.neural-interface {
			flex-direction: column;
			gap: 1rem;
		}

		.view-selector {
			flex-direction: column;
			width: 100%;
		}

		.view-btn {
			width: 100%;
			justify-content: center;
		}

		.matrix-grid {
			grid-template-columns: 1fr;
		}

		.metric-detail-panel {
			position: fixed;
			top: auto;
			bottom: 0;
			left: 0;
			right: 0;
			width: 100%;
			transform: translateY(0);
			border-radius: 12px 12px 0 0;
			max-height: 70vh;
			overflow-y: auto;
		}

		.validation-header {
			flex-direction: column;
			gap: 1.5rem;
		}

		.validation-stats {
			width: 100%;
			justify-content: space-around;
		}

		.probability-grid {
			grid-template-columns: 1fr;
		}

		.resource-item {
			grid-template-columns: 1fr;
			gap: 0.8rem;
			text-align: center;
		}

		.resource-metrics {
			justify-content: center;
		}

		.item-metrics {
			justify-content: center;
		}

		.recommendation-card {
			padding: 0.8rem;
		}

		.rec-header {
			flex-wrap: wrap;
		}

		.targets {
			flex-direction: column;
			align-items: flex-start;
		}
	}

	@media (max-width: 480px) {
		.correlation-node {
			padding: 1rem;
		}

		.diversity-metrics {
			padding-top: 0.8rem;
		}

		.diversity-value {
			font-size: 1rem;
		}

		.prediction-panel {
			padding: 1rem;
		}

		.anomaly-section,
		.patterns-section,
		.recommendations-section {
			padding: 1rem;
		}

		.stat-card {
			padding: 0.8rem;
		}

		.stat-value {
			font-size: 0.9rem;
		}

		.confidence-value {
			font-size: 1.2rem;
		}

		.assessment-score {
			font-size: 2rem;
		}
	}