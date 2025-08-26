<script>
	import { onMount } from 'svelte';

	let canvas;
	let ctx;
	let drops = [];

	onMount(() => {
		ctx = canvas.getContext('2d');
		canvas.width = window.innerWidth;
		canvas.height = window.innerHeight;

		const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789◈◯◎⬢⬡◆◇◐◑◒◓AO1LOGVISIBILITYFISRVCSOC";
		const fontSize = 14;
		const columns = canvas.width / fontSize;

		for (let i = 0; i < columns; i++) {
			drops[i] = Math.random() * canvas.height;
		}

		function draw() {
			ctx.fillStyle = 'rgba(0, 0, 0, 0.04)';
			ctx.fillRect(0, 0, canvas.width, canvas.height);

			ctx.fillStyle = '#00ff41';
			ctx.font = fontSize + 'px monospace';

			for (let i = 0; i < drops.length; i++) {
				const char = chars[Math.floor(Math.random() * chars.length)];
				
				ctx.fillText(char, i * fontSize, drops[i]);

				if (drops[i] > canvas.height && Math.random() > 0.975) {
					drops[i] = 0;
				}

				drops[i] += fontSize;
			}
		}

		const interval = setInterval(draw, 60);

		const handleResize = () => {
			canvas.width = window.innerWidth;
			canvas.height = window.innerHeight;
			
			const newColumns = canvas.width / fontSize;
			drops.length = newColumns;
			for (let i = 0; i < newColumns; i++) {
				if (drops[i] === undefined) {
					drops[i] = Math.random() * canvas.height;
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
	class="matrix-canvas"
></canvas>

<style>
	.matrix-canvas {
		position: fixed;
		top: 0;
		left: 0;
		width: 100vw;
		height: 100vh;
		z-index: 1;
		pointer-events: none;
		opacity: 0.06;
	}
</style>