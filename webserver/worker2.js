

self.onmessage = function (event) {
  const { address, temp, timestamp } = event.data;

  if (address === 1) {
    const mantle_temp = temp;
    // Führen Sie hier die gewünschten Operationen mit mantle_temp durch
  } else if (address === 2) {
    const pre_heating_temp = temp;
    // Führen Sie hier die gewünschten Operationen mit pre_heating_temp durch
  } else if (address === 3) {
    const feed_temp = temp;
    // Führen Sie hier die gewünschten Operationen mit feed_temp durch
  } else if (address === 4) {
    const cooling_temp = temp;
    // Führen Sie hier die gewünschten Operationen mit cooling_temp durch
  }

};
