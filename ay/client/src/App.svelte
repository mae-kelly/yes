<script>
  console.log('🔍 App.svelte: Component script starting...');
  
  let count = 0;
  let message = "Hello from Svelte!";
  
  function increment() {
    count += 1;
    console.log('🔍 App.svelte: Count incremented to:', count);
  }
  
  function handleMount() {
    console.log('✅ App.svelte: Component mounted successfully!');
    console.log('🔍 App.svelte: Initial state - count:', count, 'message:', message);
  }
  
  // Run on mount
  import { onMount } from 'svelte';
  
  onMount(() => {
    handleMount();
    return () => {
      console.log('🔍 App.svelte: Component unmounting...');
    };
  });
  
  console.log('🔍 App.svelte: Script block completed');
</script>

<main>
  <div class="container">
    <h1>🎉 Svelte App is Working!</h1>
    <p class="message">{message}</p>
    
    <div class="counter-section">
      <p>Counter: <strong>{count}</strong></p>
      <button on:click={increment} class="btn">
        Click me! (+1)
      </button>
    </div>
    
    <div class="debug-info">
      <h3>Debug Info:</h3>
      <p>✅ Svelte component rendered</p>
      <p>✅ CSS styles applied</p>
      <p>✅ Event handlers working</p>
      <p><small>Check console for detailed logs</small></p>
    </div>
  </div>
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
  
  main {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 20px;
  }
  
  .container {
    background: white;
    border-radius: 15px;
    padding: 40px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    text-align: center;
    max-width: 500px;
    width: 100%;
  }
  
  h1 {
    color: #333;
    margin-bottom: 20px;
    font-size: 2.5em;
  }
  
  .message {
    color: #666;
    font-size: 1.2em;
    margin-bottom: 30px;
  }
  
  .counter-section {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
  }
  
  .counter-section p {
    font-size: 1.1em;
    margin-bottom: 15px;
  }
  
  .btn {
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 25px;
    font-size: 1em;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  
  .btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
  }
  
  .btn:active {
    transform: translateY(0);
  }
  
  .debug-info {
    margin-top: 30px;
    padding: 15px;
    background: #e8f5e8;
    border-radius: 8px;
    border-left: 4px solid #28a745;
  }
  
  .debug-info h3 {
    color: #155724;
    margin-top: 0;
  }
  
  .debug-info p {
    color: #155724;
    margin: 5px 0;
  }
</style>