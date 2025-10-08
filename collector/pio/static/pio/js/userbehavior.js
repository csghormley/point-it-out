/**
 * User behavior tracking module
 * Modern JavaScript implementation using Fetch API
 */
const userBehaviorTracker = (() => {
  // Default configuration
  const defaultConfig = {
    userInfo: false,
    clicks: true,
    mouseMovement: true,
    mouseMovementInterval: 1,
    mouseScroll: false,
    timeCount: true,
    clearAfterProcess: true,
    processTime: 10,
    processData: async (results) => {
      if (!window.context?.responseid) return;
      
      const csrftoken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
      
      if (!csrftoken) {
        console.error('CSRF token not found');
        return;
      }

      const data = {
        responseid: window.context.responseid,
        logdata: JSON.stringify(results)
      };

      try {
        const response = await fetch('/api/visitorlog/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Csrftoken': csrftoken
          },
          body: JSON.stringify(data)
        });

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        // Optional: process the response data if needed
        // const responseData = await response.json();
      } catch (error) {
        console.error('Problem saving the log data:', error);
      }
    }
  };

  // Tracking data storage
  let trackingData = {
    clicks: [],
    mouseMovements: [],
    mouseScrolls: [],
    timeSpent: 0
  };

  // Timer and interval IDs
  let processIntervalId = null;
  let timeCounterIntervalId = null;
  let mouseMovementThrottleId = null;
  
  // Configuration storage
  let config = {...defaultConfig};

  /**
   * Initializes the tracking with custom configuration
   * @param {Object} userConfig - Custom configuration object
   */
  const initialize = (userConfig = {}) => {
    // Merge default config with user config
    config = {...defaultConfig, ...userConfig};
    
    // Start tracking based on configuration
    if (config.clicks) {
      document.addEventListener('click', trackClick);
    }
    
    if (config.mouseMovement) {
      document.addEventListener('mousemove', throttleMouseMovement);
    }
    
    if (config.mouseScroll) {
      window.addEventListener('scroll', trackScroll);
    }
    
    if (config.timeCount) {
      startTimeCounter();
    }
    
    // Set up processing interval
    processIntervalId = setInterval(processTrackingData, config.processTime * 1000);
  };

  /**
   * Tracks mouse clicks
   * @param {MouseEvent} event - Click event
   */
  const trackClick = (event) => {
    trackingData.clicks.push({
      x: event.clientX,
      y: event.clientY,
      target: event.target.tagName,
      timestamp: Date.now()
    });
  };

  /**
   * Throttles mouse movement tracking to reduce data volume
   * @param {MouseEvent} event - Mouse movement event
   */
  const throttleMouseMovement = (event) => {
    if (mouseMovementThrottleId) return;
    
    mouseMovementThrottleId = setTimeout(() => {
      trackMouseMovement(event);
      mouseMovementThrottleId = null;
    }, config.mouseMovementInterval * 1000);
  };

  /**
   * Tracks mouse movement
   * @param {MouseEvent} event - Mouse movement event
   */
  const trackMouseMovement = (event) => {
    trackingData.mouseMovements.push({
      x: event.clientX,
      y: event.clientY,
      timestamp: Date.now()
    });
  };

  /**
   * Tracks scrolling
   */
  const trackScroll = () => {
    trackingData.mouseScrolls.push({
      scrollX: window.scrollX,
      scrollY: window.scrollY,
      timestamp: Date.now()
    });
  };

  /**
   * Starts time counter for session duration
   */
  const startTimeCounter = () => {
    const startTime = Date.now();
    timeCounterIntervalId = setInterval(() => {
      const currentTime = Date.now();
      trackingData.timeSpent = Math.floor((currentTime - startTime) / 1000);
    }, 1000);
  };

  /**
   * Processes collected tracking data
   */
  const processTrackingData = () => {
    // Create a copy of current data
    const dataToProcess = {...trackingData};
    
    // Clear tracking data if configured
    if (config.clearAfterProcess) {
      trackingData = {
        clicks: [],
        mouseMovements: [],
        mouseScrolls: [],
        timeSpent: trackingData.timeSpent
      };
    }
    
    // Process the data using the configured function
    config.processData(dataToProcess);
  };

  /**
   * Stops all tracking activities
   */
  const stop = () => {
    // Clear intervals
    clearInterval(processIntervalId);
    clearInterval(timeCounterIntervalId);
    clearTimeout(mouseMovementThrottleId);
    
    // Remove event listeners
    document.removeEventListener('click', trackClick);
    document.removeEventListener('mousemove', throttleMouseMovement);
    window.removeEventListener('scroll', trackScroll);
    
    // Process any remaining data
    processTrackingData();
  };

  // Public API
  return {
    initialize,
    stop,
    getConfig: () => ({...config})
  };
})();

// Example usage:
// Initialize with default configuration
// userBehaviorTracker.initialize();

// Or initialize with custom configuration
// userBehaviorTracker.initialize({
//   processTime: 5,
//   mouseMovementInterval: 0.5
// });

// Export the module
export default userBehaviorTracker;
// module.exports = userBehaviorTracker;
