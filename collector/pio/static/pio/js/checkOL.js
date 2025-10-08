// checkOL.js
// This is a diagnostic script to check the structure of the OpenLayers library
// Add this as a separate script in your HTML to check the structure

(function() {
  console.log("Checking OpenLayers structure...");
  
  if (typeof ol === 'undefined') {
    console.error("OpenLayers (ol) is not defined. Make sure it's loaded before this script.");
    return;
  }
  
  console.log("OpenLayers version:", ol.VERSION || "unknown");
  
  // Check control.defaults
  console.log("\nol.control.defaults:");
  console.log("Type:", typeof ol.control.defaults.defaults);
  if (typeof ol.control.defaults.defaults === 'function') {
    console.log("✅ ol.control.defaults.defaults is a function");
    try {
      const controls = ol.control.defaults.defaults();
      console.log("Return type:", Object.prototype.toString.call(controls));
    } catch (e) {
      console.error("Error calling ol.control.defaults.defaults:", e);
    }
  } else {
    console.error("❌ ol.control.defaults is not a function");
    console.log("Control object structure:", Object.keys(ol.control));
  }
  
  // Check interaction.defaults
  console.log("\nol.interaction.defaults:");
  console.log("Type:", typeof ol.interaction.defaults.defaults);
  if (typeof ol.interaction.defaults.defaults === 'function') {
    console.log("✅ ol.interaction.defaults.defaults is a function");
  } else {
    console.error("❌ ol.interaction.defaults.defaults is not a function");
    console.log("Interaction object structure:", Object.keys(ol.interaction));
  }
  
  // Check a few more key components
  console.log("\nKey OpenLayers components:");
  console.log("Map:", typeof ol.Map === 'function' ? "✅" : "❌");
  console.log("View:", typeof ol.View === 'function' ? "✅" : "❌");
  console.log("Feature:", typeof ol.Feature === 'function' ? "✅" : "❌");
  console.log("style.Circle:", typeof ol.style.Circle === 'function' ? "✅" : "❌");
})();
