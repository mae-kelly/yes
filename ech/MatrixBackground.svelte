// ech/MatrixBackground.svelte
<script>
	import { onMount } from 'svelte';

	let canvas;
	let ctx;
	let drops = [];
	let particles = [];

	onMount(() => {
		ctx = canvas.getContext('2d');
		canvas.width = window.innerWidth;
		canvas.height = window.innerHeight;

		const chars = "◢◤◈◆◇◐◑◒◓⬢⬡⬟⬠▲▼■□●○◯◉⧫ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789SHADOWNETQUANTUMNEURALGHOST1337DEFCONAGENTSKYNETVAULTCIPHERPHANTOM";
		const fontSize = 12;
		const columns = Math.floor(canvas.width / fontSize);

		for (let i = 0; i < columns; i++) {
			drops[i] = {
				y: Math.random() * canvas.height,
				speed: Math.random() * 3 + 1,
				opacity: Math.random(),
				chars: [],
				glitch: false
			};
		}

		for (let i = 0; i < 50; i++) {
			particles.push({
				x: Math.random() * canvas.width,
				y: Math.random() * canvas.height,
				vx: (Math.random() - 0.5) * 2,
				vy: (Math.random() - 0.5) * 2,
				life: Math.random(),
				maxLife: Math.random() * 100 + 50
			});
		}

		function drawQuantumEffect() {
			ctx.fillStyle = 'rgba(0, 0, 0, 0.03)';
			ctx.fillRect(0, 0, canvas.width, canvas.height);

			ctx.shadowBlur = 5;
			ctx.shadowColor = '#00ff41';

			for (let i = 0; i < drops.length; i++) {
				const drop = drops[i];
				const x = i * fontSize;

				if (Math.random() < 0.001) {
					drop.glitch = !drop.glitch;
				}

				for (let j = 0; j < 15; j++) {
					const y = drop.y - (j * fontSize);
					if (y > 0 && y < canvas.height) {
						const char = chars[Math.floor(Math.random() * chars.length)];
						const alpha = Math.max(0, drop.opacity - (j * 0.1));
						
						if (drop.glitch && Math.random() < 0.3) {
							ctx.fillStyle = `rgba(255, 0, 64, ${alpha})`;
						} else if (j === 0) {
							ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
						} else if (j < 3) {
							ctx.fillStyle = `rgba(0, 255, 65, ${alpha})`;
						} else {
							ctx.fillStyle = `rgba(0, ${Math.floor(255 * alpha)}, 41, ${alpha * 0.8})`;
						}

						ctx.font = `${fontSize}px monospace`;
						ctx.fillText(char, x, y);

						if (Math.random() < 0.05) {
							ctx.shadowBlur = 15;
							ctx.shadowColor = drop.glitch ? '#ff0040' : '#00ff41';
							ctx.fillText(char, x, y);
							ctx.shadowBlur = 5;
						}
					}
				}

				drop.y += drop.speed;
				drop.opacity = 0.3 + Math.sin(Date.now() * 0.001 + i) * 0.2;

				if (drop.y > canvas.height + 100 && Math.random() > 0.975) {
					drop.y = -100;
					drop.speed = Math.random() * 3 + 1;
				}
			}

			particles.forEach((particle, index) => {
				particle.x += particle.vx;
				particle.y += particle.vy;
				particle.life++;

				if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
				if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;

				const alpha = 1 - (particle.life / particle.maxLife);
				if (alpha > 0) {
					ctx.fillStyle = `rgba(0, 255, 65, ${alpha * 0.3})`;
					ctx.beginPath();
					ctx.arc(particle.x, particle.y, 1, 0, Math.PI * 2);
					ctx.fill();

					if (Math.random() < 0.1) {
						ctx.strokeStyle = `rgba(0, 255, 65, ${alpha * 0.2})`;
						ctx.lineWidth = 0.5;
						ctx.beginPath();
						
						const nearestParticle = particles.find(p => 
							p !== particle && 
							Math.abs(p.x - particle.x) < 100 && 
							Math.abs(p.y - particle.y) < 100
						);
						
						if (nearestParticle) {
							ctx.moveTo(particle.x, particle.y);
							ctx.lineTo(nearestParticle.x, nearestParticle.y);
							ctx.stroke();
						}
					}
				}

				if (particle.life >= particle.maxLife) {
					particles[index] = {
						x: Math.random() * canvas.width,
						y: Math.random() * canvas.height,
						vx: (Math.random() - 0.5) * 2,
						vy: (Math.random() - 0.5) * 2,
						life: 0,
						maxLife: Math.random() * 100 + 50
					};
				}
			});

			if (Math.random() < 0.01) {
				const glitchLines = Math.floor(Math.random() * 3) + 1;
				for (let i = 0; i < glitchLines; i++) {
					const y = Math.random() * canvas.height;
					ctx.fillStyle = `rgba(255, 0, 64, 0.1)`;
					ctx.fillRect(0, y, canvas.width, 2);
				}
			}

			if (Math.random() < 0.005) {
				const scanLineY = Math.random() * canvas.height;
				const gradient = ctx.createLinearGradient(0, scanLineY - 10, 0, scanLineY + 10);
				gradient.addColorStop(0, 'rgba(0, 255, 65, 0)');
				gradient.addColorStop(0.5, 'rgba(0, 255, 65, 0.3)');
				gradient.addColorStop(1, 'rgba(0, 255, 65, 0)');
				ctx.fillStyle = gradient;
				ctx.fillRect(0, scanLineY - 10, canvas.width, 20);
			}
		}

		const interval = setInterval(drawQuantumEffect, 50);

		const handleResize = () => {
			canvas.width = window.innerWidth;
			canvas.height = window.innerHeight;
			
			const newColumns = Math.floor(canvas.width / fontSize);
			drops.length = newColumns;
			for (let i = 0; i < newColumns; i++) {
				if (!drops[i]) {
					drops[i] = {
						y: Math.random() * canvas.height,
						speed: Math.random() * 3 + 1,
						opacity: Math.random(),
						chars: [],
						glitch: false
					};
				}
			}
		};

		window.addEventListener('resize', handleResize);

		return () => {
			clearInterval(interval);
			window.removeEventListener('resize', handleResize);
		};
	});
</script>

<canvas
	bind:this={canvas}
	class="quantum-canvas"
></canvas>

<style>
	.quantum-canvas {
		position: fixed;
		top: 0;
		left: 0;
		width: 100vw;
		height: 100vh;
		z-index: 1;
		pointer-events: none;
		opacity: 0.08;
		filter: blur(0.5px);
		mix-blend-mode: screen;
	}
</style>