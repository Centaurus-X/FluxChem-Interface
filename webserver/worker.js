
//"use strict";

// Variablen im Worker definieren
let connected = false;

let relais1 = false;
let relais2 = false;
let relais3 = false;
let feedpump = false;
let mantle_temp = 0;
let heating_mantle = false;
let received_msg;
let reconnectInterval;

let pre_heating_temp = 0;
let feed_temp = 0;
let cooling_temp = 0;

let process_data = {}; 
let process_data_global = {};

let p_name;
let p_pid;
let cpu_use;


let clickCount1, clickCount2, clickCount3, clickCount4;


const worker2 = new Worker('worker2.js');


  async function init() {
    await connect();

    reconnectInterval = setInterval(async () => {
      websock.close(); // Schließt die aktuelle WebSocket-Verbindung
      await connect();
    }, 25000);

  }


  setInterval(async () => {
    if (connected === true)
    {
      websock.send(JSON.stringify({"heartbeat": ""}));
    }
  }, 10000);


  async function connect() {
    const server = '192.168.0.24:8001';
    const url = 'ws://' + server + "/";
    console.log('Opening websocket ' + url);
    websock = new WebSocket(url);

    // Handler für das Öffnen der WebSocket-Verbindung
    websock.onopen = function (event) {
      connected = true;
    };

    // Handler für das Schließen der WebSocket-Verbindung
    websock.onclose = function (event) {
      connected = false;
    };

    // Handler für Fehler in der WebSocket-Verbindung
    websock.onerror = function(event) {
    };

    // Handler für das Empfangen von Nachrichten über die WebSocket-Verbindung
    websock.onmessage = function(event) {
      sock_message(event); // optional, wenn Sie möchten, dass Ihre andere Funktion aufgerufen wird
    };

  }

  init();

  setTimeout(async () =>
  {
    if (connected === true)
    {
      await websock.send(JSON.stringify({"request": "all"}));
      console.log(`{"request": "all"}`);
    }
  }, 10);


  async function sock_message(evt) {
    const received_msg = JSON.parse(evt.data);

    const functionMap = {
        state_name: function (state_n, state_v) {
            try {
                if (state_n === "cooling_pump_1") {
                    if (state_v === "true" || state_v === "on") {
                        relais1 = true;
                        console.log(`function(state_n, state_value)`);
                        if (clickCount1 != 2) {
                            clickCount1 = 2;
                        }
                    } else if (state_v === "false" || state_v === "off") {
                        relais1 = false;
                        if (clickCount1 != 1) {
                            clickCount1 = 1;
                        }
                    }
                }
                if (state_n === "gas_valve_1") {
                  if (state_v === "true" || state_v === "on") {
                      relais2 = true;
                      console.log(`function(state_n, state_value)`);
                      if (clickCount2 != 2) {
                          clickCount2 = 2;
                      }
                  } else if (state_v === "false" || state_v === "off") {
                      relais2 = false;
                      if (clickCount2 != 1) {
                          clickCount2 = 1;
                      }
                  }
              }
              if (state_n === "feed_pump_1") {
                if (state_v === "true" || state_v === "on") {
                    relais3 = true;
                    feedpump = true;
                    console.log(`function(state_n, state_value)`);
                    if (clickCount3 != 2) {
                        clickCount3 = 2;
                    }
                } else if (state_v === "false" || state_v === "off") {
                    relais3 = false;
                    feedpump = false;
                    if (clickCount3 != 1) {
                        clickCount3 = 1;
                    }
                }
            }
            if (state_n === "heating_mantle_1") {
              if (state_v === "true" || state_v === "on") {
                heating_mantle = true;
                  console.log(`function(state_n, state_value)`);
                  if (clickCount4 != 2) {
                      clickCount4 = 2;
                  }
              } else if (state_v === "false" || state_v === "off") {
                heating_mantle = false;
                  if (clickCount4 != 1) {
                      clickCount4 = 1;
                  }
              }
            }
            } catch (error) {
              console.log(`Error in state_name function: ${error}`);
            }
        },

        temperature: function (address, temp) {
          try {
            console.log(`Temperature: Address: ${address}, Temp: ${temp}`);
            if (typeof address === 'string') {
              address = parseInt(address);
            } 
            if (address === 1) {
              {
                mantle_temp = temp;
                //worker2.postMessage({ address, temp, timestamp });
              }
            }

            if (typeof address === 'string') {
              address = parseInt(address);
            } 
            if (address === 2) {
              {
                pre_heating_temp = temp;
                //worker2.postMessage({ address, temp, timestamp });
              }
            }

            if (typeof address === 'string') {
              address = parseInt(address);
            } 
            if (address === 3) {
              {
                feed_temp = temp;
                //worker2.postMessage({ address, temp, timestamp });
              }
            }

            if (typeof address === 'string') {
              address = parseInt(address);
            } 
            if (address === 4) {
              {
                cooling_temp = temp;
                //worker2.postMessage({ address, temp, timestamp });
              }
            }


            // Add more address-specific actions as needed
          } catch (error) {
            console.log(`Error in state_name function: ${error}`);
          }
        },

        heartbeat: function(heartbeat_value) {
          try {
            if (heartbeat_value === "true") {
              console.log(`heartbeat ${heartbeat_value} `);
            }
          } catch (error) {
            console.log(`Error in state_name function: ${error}`);
          }
        },

        process_data: function(name_p, pid, cpu_usage) {
          try {
            for (const process_name in name_p) {
              p_name = name_p;
              p_pid = pid;
              cpu_use = cpu_usage;

              //const process_info = name_p[process_name];
              //const pid = process_info["pid"];
              //const cpu_percent = process_info["cpu_usage"];
              console.log(`Process ${p_name} (PID: ${p_pid}) is using ${cpu_use}% CPU.`);
            }
          } catch (error) {
            console.log(`Error in process_data function: ${error}`);
          }
        },


    };

    //name_p, pid, cpu_usage

    for (const key in received_msg) {
      if (key in functionMap) {
          const state_n = received_msg['state_name'] || null;
          const state_v = received_msg['state_value'] || null;
          const address = received_msg['address'] || null;
          const temp = received_msg['temp'] || null;
          const heartbeat_value = received_msg['heartbeat'] || null;
          const name_p = received_msg['name'] || null;
          const pid = received_msg['pid'] || null;
          const cpu_usage = received_msg['cpu_usage'] || null;

          if (typeof functionMap[key] === 'function') {
              if (key === 'temperature') {
                  functionMap[key](address, temp);
              } else if (key === 'heartbeat') {
                  functionMap[key](heartbeat_value);
              } else if (key === 'process_data') {  //&& received_msg[key] === "send") {
                  functionMap[key](name_p, pid, cpu_usage);
              } else {
                  functionMap[key](state_n, state_v);
              }
          } else {
              console.log(`Function ${key} is not defined in functionMap.`);
          }


          //self.postMessage('Nachricht verarbeitet');
          // Nachricht an den Hauptthread senden

          self.postMessage({
            clickCount1: clickCount1,
            clickCount2: clickCount2,
            clickCount3: clickCount3,
            clickCount4: clickCount4,
            relais1: relais1,
            relais2: relais2,
            relais3: relais3,
            feedpump: feedpump,
            heating_mantle: heating_mantle,
            mantle_temp: mantle_temp,
            pre_heating_temp: pre_heating_temp,
            feed_temp: feed_temp,
            cooling_temp: cooling_temp,
            p_name: p_name,
            p_pid: p_pid,
            cpu_use: cpu_use
          });


        }
    }
  }

