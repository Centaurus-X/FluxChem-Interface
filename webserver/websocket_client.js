
//"use strict";

  // ######################################################
  //  Initialization of the variables
  // ######################################################


  const portnum = 8001;

  let websock;
  let connected = false;
  let timerId;
  let address = null;
  let temp = null;
  let displayQueue = [];

  let clickCount1 = 1, clickCount2 = 1, clickCount3 = 1, clickCount4 = 1;
  let relais1 = false, relais2 = false, relais3 = false, relais4 = false, heating_mantle = false, mantle_temp = 0, temp1 = false, temp2 = false, temperatur1 = 0, temperatur2 = 0, button_temp1 = false, button_temp2 = false, heating = false, feedpump = false, tempinput_new, tempinput =10;

  let process_data;

  let p_name;
  let p_pid;
  //let cpu_use;

  let pre_heating_temp = 0;
  let feed_temp = 0;
  let cooling_temp = 0;

  let tempper = 10;

  let cpu_use = new Array(10).fill("-");
  let newProcessName;
  let newCpuUsage; 


  const worker = new Worker('worker.js');
  const worker2 = new Worker('worker2.js');


  // ######################################################
  //  Worker initialization and variable transfer
  // ######################################################


  function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  //const worker = new Worker('worker.js');

  //worker.onmessage = function(event) {
  //  handleWorkerMessage(event);
  //  console.log(event.data);
  //}


  worker.onmessage = async function(event) {
    await handleWorkerMessage(event);
    console.log(event.data);
  }


  async function handleWorkerMessage(event) {
      const startTime = performance.now();
    // Wenn der Worker eine Nachricht "updateVars" sendet, aktualisieren Sie die Variablen im Hauptthread
    //if (event.data.type === "updateVars") {
      clickCount1 = event.data.clickCount1;
      clickCount2 = event.data.clickCount2;
      clickCount3 = event.data.clickCount3;
      clickCount4 = event.data.clickCount4;
      relais1 = event.data.relais1;
      relais2 = event.data.relais2;
      relais3 = event.data.relais3;
      feedpump = event.data.feedpump;
      heating_mantle = event.data.heating_mantle;
      mantle_temp = event.data.mantle_temp;
      pre_heating_temp = event.data.pre_heating_temp;
      feed_temp = event.data.feed_temp;
      cooling_temp = event.data.cooling_temp;
      p_name = event.data.p_name;
      p_pid = event.data.p_pid;
      cpu_use = event.data.cpu_use;
    //}

      const endTime = performance.now();
      console.log('Execution time:', endTime - startTime);
  }


  // ######################################################
  //  Initialisation
  // ######################################################


  async function init() {
    const host = "192.168.0.24:8001";
    document.myform.text.value = "Host " + host + "\n";
    setInterval(timer_tick, 1000);
    setInterval(timer_tick2, 10000);
    setInterval(processDisplayQueue, 100); // Prozessdisplay-Warteschlange alle 100 ms
    //timerId = window.setInterval(timer_tick, 1000);

    worker.postMessage('start');
    requestAnimationFrame(animationLoop);

  }


  // ######################################################
  //  Websocket connection
  // ######################################################


  async function connect() {
    try {
      const server = '192.168.0.24:8001';
      const url = 'ws://' + server + "/";
      console.log('Opening websocket ' + url);
      websock = new WebSocket(url);
  
      // Handler für das Öffnen der WebSocket-Verbindung
      websock.onopen = function(event) {
        display("Websocket connection opened\n");
        connected = true;
      };
  
      // Handler für das Schließen der WebSocket-Verbindung
      websock.onclose = function(event) {
        display("Websocket connection closed\n");
        clearInterval(timerId);
      };
  
      // Handler für Fehler in der WebSocket-Verbindung
      websock.onerror = function(event) {
        display("Websocket error: " + event.data + "\n");
      };
  
      // Handler für das Empfangen von Nachrichten über die WebSocket-Verbindung
      websock.onmessage = handleWebsocketMessage;
      {
        websock.bufferedAmount = 0;
        display("Opening websocket " + url + "\n");
      }

    } catch (error) {
      console.error('Websocket connection failed:', error);
    }
  }

  function disconnect()
  {
    connected = false;
    clearInterval(timerId);
    websock.close();

    displayQueue = [];
    document.myform.text.value = "";
  }


  // ######################################################
  //  Display the given text in Toggel Console
  // ######################################################

  // Push event.data (s) into queue
  async function display(s) {
    displayQueue.push(s);
  }


  // Display message queue in interval -> look at setInterval
  async function processDisplayQueue() {
    if (displayQueue.length > 0) {
      let message = displayQueue.shift();
      document.myform.text.value += message;
      document.myform.text.scrollTop = document.myform.text.scrollHeight;
    }
  }


  // At event call function display
  async function handleWebsocketMessage(event) {
    websock.bufferedAmount = 0;
    display("Received message: " + event.data + "\n");
    sock_message(event);
  }

  async function sock_message(evt)
  {
    //const received_msg = JSON.parse(evt.data);
  
    // Nachricht an den WebWorker senden
    //worker.postMessage(received_msg);
  }

  window.addEventListener("load", async () => {
    await init();
  }, false);


  // ######################################################

      //display("#####_heating_mantle " + heating_mantle);

      //websock.send('*');
      //websock.send(JSON.stringify({set_temp1: '350'}));
      //websock.send(JSON.stringify({set_temp2: '222'})); //, set_temp3: '250'}));

      //websock.send(JSON.stringify({"heizen": "on", "address": "524", "": ''}));
      //websock.send(JSON.stringify({"heizen": "off", "address": "524", "temp": '522'}));

      //websock.send(JSON.stringify({"heizen": "on", "address": "544", "temp": '445'}));
      //websock.send(JSON.stringify({"heizen": "off", "address": "545", "temp": '500'}));

      //websock.send(JSON.stringify({"relais": "off", "address": '512'}));
      //websock.send(JSON.stringify({"heizen": "off", "address": '524'}));
      //websock.send(JSON.stringify({"heizen": "get", "address": "524", "temp": '477'}));

  // ######################################################


  // ######################################################
  //  Intervall to update page content
  // ######################################################


    async function timer_tick()
    {

      const myBox1 = document.getElementById("myBox1");
      const myBox2 = document.getElementById("myBox2");
      const myBox3 = document.getElementById("myBox3");
      const myBox4 = document.getElementById("myBox4");

      // Output
      if (myBox1 && myBox2 && myBox3 && myBox4) // && websock.readyState === WebSocket.OPEN)
      {
        document.getElementById("myBox1").innerHTML = "Temperatur: " + cooling_temp + "°C";
        document.getElementById("myBox2").innerHTML = "Temperatur: " + 0.3 + "Nm3/h";
        document.getElementById("myBox3").innerHTML = "Temperatur: " + feed_temp + "°C";
        document.getElementById("myBox4").innerHTML = "Temperatur: " + mantle_temp + "°C";
      }

      if (connected === false)
      {
        //connect();
      }

      if (connected === true)
      {
        //
      }

      if (p_name == 'Process1')
      {
      document.getElementById("cpuUse1").innerHTML = "" + cpu_use + "%";
      }
      if (p_name == 'Process2')
      {
      document.getElementById("cpuUse2").innerHTML = "" + cpu_use + "%";
      }
      if (p_name == 'Process3')
      {
      document.getElementById("cpuUse3").innerHTML = "" + cpu_use + "%";
      }
      if (p_name == 'Process4')
      {
      document.getElementById("cpuUse4").innerHTML = "" + cpu_use + "%";
      }
      if (p_name == 'Process5')
      {
      document.getElementById("cpuUse5").innerHTML = "" + cpu_use + "%";
      }
      if (p_name == 'Process6')
      {
      document.getElementById("cpuUse6").innerHTML = "" + cpu_use + "%";
      }
      if (p_name == 'Process7')
      {
      document.getElementById("cpuUse7").innerHTML = "" + cpu_use + "%";
      }
      if (p_name == 'Process8')
      {
      document.getElementById("cpuUse8").innerHTML = "" + cpu_use + "%";
      }
      if (p_name == 'Process9')
      {
      document.getElementById("cpuUse9").innerHTML = "" + cpu_use + "%";
      }
      if (p_name == 'Process10')
      {
      document.getElementById("cpuUse10").innerHTML = "" + cpu_use + "%";
      }


    }


    async function timer_tick2()
    {

      updatemyChart([
        { type: 'mantle', value: mantle_temp, timestamp: new Date() },
        { type: 'pre_heating', value: pre_heating_temp, timestamp: new Date() },
        { type: 'feed', value: feed_temp, timestamp: new Date() },
        { type: 'cooling', value: cooling_temp, timestamp: new Date() },
      ]);

    }


    function animationLoop() {
      // DOM-Update
      image0();
    
      requestAnimationFrame(animationLoop);
    }


  // ######################################################
  //  Clickcount funktions "+1"
  // ######################################################


    function toggleclickFunction1()
    {
      clickCount1++;
    }
  
    function toggleclickFunction2()
    {
      clickCount2++;
    }
  
    function toggleclickFunction3()
    {
      clickCount3++;
    }
  
    function toggleclickFunction4()
    {
      clickCount4++;
    }



  // ######################################################
  //  Tab 1
  // ######################################################


  function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablink");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].style.backgroundColor = "";
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.style.backgroundColor = "#ccc";
  }
  
  document.getElementsByClassName("tablink")[0].click();



  // ######################################################
  //  Tab 2 - Charts
  // ######################################################


  const mantleChart = createLineChart("mantleChart", "Mantle Temperature", "blue");
  const preHeatingChart = createLineChart("preHeatingChart", "Pre-Heating Temperature", "green");
  const feedChart = createLineChart("feedChart", "Feed Temperature", "orange");
  const coolingChart = createLineChart("coolingChart", "Cooling Temperature", "red");
  
  
  function createLineChart(canvasId, label, borderColor) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext("2d");
  
    return new Chart(ctx, {
      type: "line",
      data: {
        datasets: [
          {
            label,
            data: [],
            borderColor,
            fill: false,
          },
        ],
      },
      options: {
        scales: {
          x: {
            type: 'linear',
            title: {
              display: true,
              text: 'Time',
            },
            ticks: {
              callback: function(value, index, values) {
                const date = new Date(value);
                const hours = date.getUTCHours().toString().padStart(2, '0');
                const minutes = date.getUTCMinutes().toString().padStart(2, '0');
                const seconds = date.getUTCSeconds().toString().padStart(2, '0');
                return `${hours}:${minutes}:${seconds}`;
              },
              min: Date.now() - 100000, // Anpassen, um die minimale Zeitachse festzulegen
              max: Date.now(), // Anpassen, um die maximale Zeitachse festzulegen
            },
          },
          y: {
            title: {
              display: true,
              text: '°C',
            },
            min: 0, // Anpassen, um den minimalen Wert der Y-Achse festzulegen
            max: 100, // Anpassen, um den maximalen Wert der Y-Achse festzulegen
          },
        },
      },
    });
  }

  async function updatemyChart(newData) {
    newData.forEach((d) => {
      const dataPoint = { x: d.timestamp.getTime(), y: d.value };
  
      switch (d.type) {
        case "mantle":
          mantleChart.data.datasets[0].data.push(dataPoint);
          mantleChart.update();
          break;
        case "pre_heating":
          preHeatingChart.data.datasets[0].data.push(dataPoint);
          preHeatingChart.update();
          break;
        case "feed":
          feedChart.data.datasets[0].data.push(dataPoint);
          feedChart.update();
          break;
        case "cooling":
          coolingChart.data.datasets[0].data.push(dataPoint);
          coolingChart.update();
          break;
      }
    });
  }


  // ######################################################
  //  Tab 3
  // ######################################################




  // ######################################################
  //  Toggel websocket communication consol on right top
  // ######################################################


  function toggle(event) {
    var element = event.target;
    element.classList.toggle("active");
    var content = element.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  }


  // ######################################################
  //  Sidebar Buttons on the left side bar "Settings"
  // ######################################################


  async function settings_temp() {
    var content = document.getElementById("toggelContent1");

    var output_heater_temp = document.getElementById("mantle_temp");
    var output_preheater_temp = document.getElementById("pre_heater_temp");

    //heater_temp = input_heating_temp.value;

    function updateOutput() {
      output_heater_temp.innerHTML = "Heating Mantle Temperature: " + mantle_temp + "°C";
      output_preheater_temp.innerHTML = "PreHeater Temperature: " + pre_heating_temp + "°C";
    }
  
    if (content.style.display === "block") {
      content.style.display = "none";
      updateOutput(); // Aktualisiere den Output hier, wenn das Panel geschlossen wird
    } else {
      content.style.display = "block";
    }
    closeOtherContents("toggelContent1");
  
    var interval = 2000; // Zeitintervall in Millisekunden, hier 1000 ms (1 Sekunde)
    setInterval(updateOutput, interval); // Rufe die updateOutput() Funktion alle 'interval' Millisekunden auf
  }

  async function settings_feed() {
    var content = document.getElementById("toggelContent2");
  
    var output_feed_temp = document.getElementById("feed_temp");
    var output_feed_interval = document.getElementById("feed_interval");
    var output_feed_level = document.getElementById("feed_level");
  
    function updateOutput() {
      output_feed_temp.innerHTML = "Feed Temperature: " + feed_temp + "°C";
      output_feed_interval.innerHTML = "Feedpump Interval: " + 2;
      output_feed_level.innerHTML = "Feedpump Level: " + 0.9;
    }
  
    if (content.style.display === "block") {
      content.style.display = "none";
      updateOutput(); // Aktualisiere den Output hier, wenn das Panel geschlossen wird
    } else {
      content.style.display = "block";
    }
    closeOtherContents("toggelContent2");
  
    var interval = 2000; // Zeitintervall in Millisekunden, hier 1000 ms (1 Sekunde)
    setInterval(updateOutput, interval); // Rufe die updateOutput() Funktion alle 'interval' Millisekunden auf
  }


  async function settings_gas() {
    var content = document.getElementById("toggelContent3");

    var output_gas_pressure = document.getElementById("gas_pressure");
    var output_gas_flow = document.getElementById("gas_flow");

    function updateOutput() {
      output_gas_pressure.innerHTML = "Gas Pressure: " + 1.01 + "bar";
      output_gas_flow.innerHTML = "Gas Flow: " + 0.3 + "Nm^3/h";
    }
  
    if (content.style.display === "block") {
      content.style.display = "none";
      updateOutput(); // Aktualisiere den Output hier, wenn das Panel geschlossen wird
    } else {
      content.style.display = "block";
    }
    closeOtherContents("toggelContent3");
  
    var interval = 2000; // Zeitintervall in Millisekunden, hier 1000 ms (1 Sekunde)
    setInterval(updateOutput, interval); // Rufe die updateOutput() Funktion alle 'interval' Millisekunden auf
  }


  async function settings_cooling() {
    var content = document.getElementById("toggelContent4");

    var output_water_temperature = document.getElementById("water_temperature");
    var output_water_flow = document.getElementById("water_flow");
    var output_recuperator_vent = document.getElementById("recuperator_vent");

    function updateOutput() {
      output_water_temperature.innerHTML = "Water Temperature: " + cooling_temp + "°C";
      output_water_flow.innerHTML = "Water Flow: " + 1.7 + "Nm^3/h";
      output_recuperator_vent.innerHTML = "Recuperator Vent: " + 400 + "rpm";
    }
  
    if (content.style.display === "block") {
      content.style.display = "none";
      updateOutput(); // Aktualisiere den Output hier, wenn das Panel geschlossen wird
    } else {
      content.style.display = "block";
    }
    closeOtherContents("toggelContent4");
  
    var interval = 2000; // Zeitintervall in Millisekunden, hier 1000 ms (1 Sekunde)
    setInterval(updateOutput, interval); // Rufe die updateOutput() Funktion alle 'interval' Millisekunden auf
  }


  window.onload = function() {
    document.getElementById("toggelContent1").style.display = "none";
    document.getElementById("toggelContent2").style.display = "none";
    document.getElementById("toggelContent3").style.display = "none";
    document.getElementById("toggelContent4").style.display = "none";
  };
  

  function closeOtherContents(excludeId) {
    const contentIds = ["toggelContent1", "toggelContent2", "toggelContent3", "toggelContent4"];
  
    contentIds.forEach(id => {
      if (id !== excludeId) {
        document.getElementById(id).style.display = "none";
      }
    });
  }



  // ######################################################
  //  Imput Data from the sidebar send to server
  // ######################################################


  async function sendData(data) {
    var jsonStr = JSON.stringify(data);
    console.log(jsonStr);
    display(jsonStr);
    await new Promise(resolve => {
      websock.send(jsonStr);
      websock.addEventListener('message', resolve);
    });
  }
  // Heating
  async function submitHeatingTemp() {
    var heating_mantle_temp = document.getElementById("input_heating_temp").value;
    sendData({"mysql": "set", "state": "update_process_parameters", "state_name": "heating_mantle_1", "heating_temp": heating_mantle_temp});
  }
  async function submitPreHeatingTemp() {
    var pre_heating_temp_input = document.getElementById("input_pre_heating_temp").value;
    sendData({"mysql": "set", "state": "update_process_parameters", "state_name": "pre_heating_mantle_1", "heating_temp": pre_heating_temp_input});
  }
  // Feed
  async function submitPump_Intervall() {
    var pump_interval_input = document.getElementById("input_pump_interval").value;
    sendData({"mysql": "set", "state": "update_process_parameters", "state_name": "feed_pump_1", "rate": pump_interval_input});
  }
  async function submitPump_Power() {
    var pump_power_input = document.getElementById("input_pump_power").value;
    sendData({"mysql": "set", "state": "update_process_parameters", "state_name": "feed_pump_1", "power": pump_power_input});
  }
  async function submitFeed_Level() {
    var feed_level_input = document.getElementById("input_feed_level").value;
    sendData({"mysql": "set", "state": "update_process_parameters", "state_name": "feed_level_1", "level": feed_level_input});
  }
  async function submitFeed_Temp() {
    var feed_temp_input = document.getElementById("input_feed_temp").value;
    sendData({"mysql": "set", "state": "update_process_parameters", "state_name": "heating_feed_1", "heating_temp": feed_temp_input});
  }
  // Gas
  async function submitGas_Pressure() {
    var gas_pressure_input = document.getElementById("input_gas_pressure").value;
    sendData({"mysql": "set", "state": "update_process_parameters", "state_name": "gas_pressure_1", "pressure_abs": gas_pressure_input});
  }
  async function submitGas_Flow() {
    var gas_flow_input = document.getElementById("input_gas_flow").value;
    sendData({"mysql": "set", "state": "update_process_parameters", "state_name": "gas_valve_1", "flow": gas_flow_input});
  }
  // Cooling
  async function submitMin_Cooling_Temp() {
    var cooling_temp_input = document.getElementById("input_min_cooling_temp").value;
    sendData({"mysql": "set", "state": "update_process_parameters", "state_name": "cooling_1", "cooling_temp": cooling_temp_input});
  }
  async function submitRecuperator_Vent() {
    var recuperator_vent_input = document.getElementById("input_recuperator_vent").value;
    sendData({"mysql": "set", "state": "update_process_parameters", "state_name": "cooling_fan_1", "power_rate": recuperator_vent_input});
  }

  

  // ######################################################
  //  Control Buttons in the plant view picture
  // ######################################################


  async function relais1_on()
  {
    toggleclickFunction1()
    if (relais1 === true && clickCount1 % 2 === 1)
    {
      await websock.send(JSON.stringify({"mysql": "set", "state": "update", "state_name": "cooling_pump_1", "state_value": "false"}));
    }
    if (relais1 === false && clickCount1 % 2 === 0)
    {
      await websock.send(JSON.stringify({"mysql": "set", "state": "update", "state_name": "cooling_pump_1", "state_value": "true"}));
    }
  }

  async function relais2_on()
  {
    toggleclickFunction2()
    if (relais2 === true && clickCount2 % 2 === 1)
    {
      await websock.send(JSON.stringify({"mysql": "set", "state": "update", "state_name": "gas_valve_1", "state_value": "false"}));
    }
    if (relais2 === false && clickCount2 % 2 === 0)
    {
      await websock.send(JSON.stringify({"mysql": "set", "state": "update", "state_name": "gas_valve_1", "state_value": "true"}));
    }
  }

  async function relais3_on()
  {
    toggleclickFunction3()
    if (relais3 === true && clickCount3 % 2 === 1)
    {
      await websock.send(JSON.stringify({"mysql": "set", "state": "update", "state_name": "feed_pump_1", "state_value": "false"}));
    }
    if (relais3 === false && clickCount3 % 2 === 0)
    {
      await websock.send(JSON.stringify({"mysql": "set", "state": "update", "state_name": "feed_pump_1", "state_value": "true"}));
    }
  }

  async function heating_mantle_on()
  {
    toggleclickFunction4()
    if (clickCount4 % 2 === 1)
    {
      await websock.send(JSON.stringify({"mysql": "set", "state": "update", "state_name": "heating_mantle_1", "state_value": "false"}));
    }
    if (clickCount4 % 2 === 0)
    {
      await websock.send(JSON.stringify({"mysql": "set", "state": "update", "state_name": "heating_mantle_1", "state_value": "true"}));
    }
  }




  // ######################################################
  //  Control Input from the middel
  // ######################################################


  const submitbutton = document.getElementById("submit-button");
  const submitbutton2 = document.getElementById("submit-button2");

  if (submitbutton && submitbutton2) {

    document.getElementById("submit-button").addEventListener("click", async function() {
      var heater_temp = document.getElementById("input-field").value;
      var obj = {
        "mysql": "set",
        "state": "update_process_parameters",
        "state_name": "heating_mantle_1",
        "heating_temp": heater_temp
      };
      var updatedJsonStr = JSON.stringify(obj);
      console.log(updatedJsonStr);
      display(updatedJsonStr);
      await new Promise(resolve => {
        websock.send(updatedJsonStr);
        websock.addEventListener('message', resolve);
      });
    });


    document.getElementById("submit-button2").addEventListener("click", async function() {
      var pre_heater_temp = document.getElementById("input-field2").value;
      var obj = {
        "mysql": "set",
        "state": "update_process_parameters",
        "state_name": "pre_heating_mantle_1",
        "heating_temp": pre_heater_temp
      };
      var updatedJsonStr = JSON.stringify(obj);
      console.log(updatedJsonStr);
      display(updatedJsonStr);
      await new Promise(resolve => {
        websock.send(updatedJsonStr);
        websock.addEventListener('message', resolve);
      });
    });

  }


  // ######################################################
  //  Plant State View Handler
  // ######################################################


  function image0()
  {


  //Relais1 = Cooling
  //Relais2 = Gas
  //Relais3 = Feed

    var image = document.getElementById("myImage1");

    //if (relais1 === false && relais2 === false && feedpump === false && heating_mantle === false) {
    //  image.src = "RI.png";
    //}
    //if ((relais1 === false && relais2 === false && feedpump === false) && heating_mantle === true) {
    //  image.src = "RI_hot3.png";
    //}
    if (relais2 === true && relais1 === true && feedpump === false && heating_mantle === false) {
      image.src = "RI_cool_gas.png";
    }
    else if (relais2 === true && relais1 === false && feedpump === true && heating_mantle === false) {
      image.src = "RI_feed_gas.png";
    }
    else if (relais2 === false && relais1 === true && feedpump === true && heating_mantle === false) {
      image.src = "RI_cool_feed.png";
    }
    else if (relais2 === true && relais1 === true && feedpump === true && heating_mantle === false) {
      image.src = "RI_cool_feed_gas.png";
    }
    else if (heating_mantle === true && relais1 === true && relais2 === true && feedpump === false) {
      image.src = "RI_hot5_cool_gas.png";
    }
    else if (heating_mantle === true && relais1 === true && relais2 === true && feedpump === true) {
      image.src = "RI_hot5_feed_cool_gas.png";
    }
    else if (heating_mantle === true && relais1 === true && feedpump === true && relais2 === false) {
      image.src = "RI_hot5_feed_cool.png";
    }
    else if (heating_mantle === true && relais1 === false && feedpump === true && relais2 === true) {
      image.src = "RI_hot5_feed_gas.png";
    }
    else if (heating_mantle === true && relais1 === true) {
      image.src = "RI_hot5_cool.png";
    }
    else if (heating_mantle === true && relais2 === true) {
      image.src = "RI_hot5_gas.png";
    }
    else if (heating_mantle === true && feedpump === true) {
      image.src = "RI_hot5_feed.png";
    }
    else if (relais1 === true) {
      image.src = "RI_cool.png";
    }
    else if (relais2 === true) {
      image.src = "RI_gas.png";
    }
    else if (feedpump === true) {
      image.src = "RI_feed.png";
    }
    else if (heating_mantle === true) {
      image.src = "RI_hot3.png";
    }
    else {
      image.src = "RI.png";
    }
  
  }
