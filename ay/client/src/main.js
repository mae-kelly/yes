console.log('🔍 main.js: Starting to load...');

try {
  console.log('🔍 main.js: Importing CSS...');
  import('./app.css').then(() => {
    console.log('✅ main.js: CSS imported successfully');
  }).catch(err => {
    console.error('❌ main.js: CSS import failed:', err);
  });
  
  console.log('🔍 main.js: Importing App.svelte...');
  
  import('./App.svelte').then((AppModule) => {
    console.log('✅ main.js: App.svelte imported successfully');
    console.log('🔍 main.js: App module:', AppModule);
    
    const App = AppModule.default;
    console.log('🔍 main.js: App constructor:', App);
    
    const appElement = document.getElementById('app');
    console.log('🔍 main.js: App div element:', appElement);
    
    if (!appElement) {
      console.error('❌ main.js: Could not find #app element!');
      return;
    }
    
    console.log('🔍 main.js: Creating Svelte app instance...');
    
    const app = new App({
      target: appElement,
      props: {
        // Add any props here if needed
      }
    });
    
    console.log('✅ main.js: Svelte app created successfully!', app);
    
    // Make app available globally for debugging
    window.svelteApp = app;
    console.log('🔍 main.js: App attached to window.svelteApp for debugging');
    
  }).catch(err => {
    console.error('❌ main.js: Failed to import App.svelte:', err);
    console.error('❌ main.js: Error details:', err.message, err.stack);
  });
  
} catch (error) {
  console.error('❌ main.js: Unexpected error:', error);
  console.error('❌ main.js: Error details:', error.message, error.stack);
}