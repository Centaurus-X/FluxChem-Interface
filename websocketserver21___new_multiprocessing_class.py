#
# Websocket_Server_Python_Script
#
# Controling a PLC over Ethernet TCP/IP
# Free to use with 'The MIT License' (Massachusetts Institute of Technology)
# Autor: Philipp Niedermeier
# Contact: philipp.niedermeier@******.de
# GitHub: 
#

from colorama import *
init(autoreset=True)

import multiprocessing
from multiprocessing import Process
from multiprocessing import Lock
from multiprocessing import Queue, Pipe
from multiprocessing import active_children

import queue
import subprocess
import threading
from threading import Thread

import sqlite3
from sqlite3 import Error


from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, text, NullPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base

Base = declarative_base()


import mysql.connector
from mysql.connector import MySQLConnection, connect, Error, cursor
from mysql.connector.cursor import MySQLCursorBuffered

from contextlib import contextmanager


#from customjsonencoder import CustomJSONEncoder

import signal, psutil, sys, json, os, shutil, logging, random, time, cProfile, pstats
from os import getpid
from simple_pid import PID
from functools import partial
from collections import defaultdict


#from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.client import ModbusTcpClient as ModbusClient

from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer
#from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket



# Configure the logging level and format
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

# Log different levels of messages
logging.debug('This is a debug message')
logging.info('This is an info message')
logging.warning('This is a warning message')
logging.error('This is an error message')
logging.critical('This is a critical message')

logger = logging.getLogger(__name__)


# Modbus Interface Unit
UNIT = 0x1

# IP Adresses to Modbus Master
HOST = '192.168.0.24'
#HOST = '192.168.0.50'

# Portnumber to Modbus master
PORT = 5020
#PORT = 502

# Coil Output Base Address
COILBASE = 512

# Websocket listen Portnumber
PORTNUM = 8001

#
# Modbus Addresses
#
# Relaises: 512 - 523
#
# 24 V Digital Output 524 - 535
# Heating: 524, 525, 526
# Cooling: 528, 529
#
# 24 V Digital Input 536 -  543
# 0-10 V Analog Output 544 - 545
# 0-10 V Analog Eingang 546 - 547
# Thermoelement K 548 - 551 0x00, 8
#


#####################################################
#                                                   #
#####################################################

# e.g. {'device_id': 1, 'device_name': 'cooling_pump_1', 'address': 512, 'device_type': 'pump', 'device_group_function': 'cooling', 'state_name': 'cooling_pump_1', 'rate': 0, 'power': 1, 'state_value': 'false'}

#####################################################
#                                                   #
#####################################################


class SimpleEcho(WebSocket):

    def __init__(self, server, sock, address, wss, queue_io, queue_ws, queue_bc):
        super().__init__(server, sock, address)
        self.wss = wss
        self.item = None

        self.queue_io = queue_io
        self.queue_ws = queue_ws
        self.queue_bc = queue_bc

        self.thread_run = True

        threading.Thread.__init__(self)
        self.broadcast = threading.Thread(target=self.broadcast, args=())
        self.broadcast.start()

    def handleMessage(self):
        # echo message back to client
        #self.sendMessage(self.data)

        logger.info(f"{Fore.GREEN}Data: {self.data}, Address: {self.address}{Style.RESET_ALL}")
        print(f'Data: {self.data}, Address: {self.address}')

        self.queue_io.put(self.data)

    def handleConnected(self):
        #self.thread_run = True
        print(self.address, 'connected')

        if self not in self.wss:
            self.wss.append(self)

    def handleClose(self):
        self.wss.remove(self)
        self.thread_run = False
        print(self.address, 'closed')

        self.broadcast.join() 

    #def sendMessageToClient(self, message, ip):
        # Send to specific client via IP-Address
    #    if ip in self.wss:
    #        self.wss[ip].sendMessage(message)

    def handle_signal(self, signum, frame):
        # Thread joining
        self.thread_run = False
        self.broadcast.join()

        # Exit the programm
        sys.exit(0)

    def broadcast(self):
        print(Fore.YELLOW + Back.RED + f'Broadcast_queue_handler', flush=True)

        while self.thread_run:
            try:
                time.sleep(0.001)
                self.item = self.queue_bc.get()

                for ws in self.wss: #self.wss:
                    ws.sendMessage(self.item)

                # Print the number of active threads
                print(Fore.GREEN + f'Number of active threads: {threading.active_count()}')
                
                # Print the list of all active threads
                thread_list = self.threading.enumerate()
                print(Fore.BLUE + f'List of all active threads:')

                for thread in thread_list:
                    print(thread)


                ##ws.sendMessage(json.dumps(self.item))

            except Exception:
                pass


#####################################################

#####################################################


class IO_Handler:

    def __init__(self, lock_io, queue_io, queue_io2, queue_io3, queue_io4, queue_ws, queue_db, queue_mb, queue_mb2, queue_bc, queue_tempctr, queue_ctr, queue_ctr2, queue_ah):
        super().__init__()

        self.rlock = threading.RLock()
        self.lock = threading.Lock()
        self.lock_io = lock_io

        self.queue_ah = queue_ah
        self.queue_io = queue_io
        self.queue_io2 = queue_io2
        self.queue_io3 = queue_io3
        self.queue_io4 = queue_io4

        self.queue_ctr = queue_ctr
        self.queue_ctr2 = queue_ctr2

        self.queue_ws = queue_ws
        self.queue_db = queue_db
        self.queue_mb = queue_mb
        self.queue_mb2 = queue_mb2
        self.queue_bc = queue_bc
        self.queue_tempctr = queue_tempctr

        self.address = None
        self.item = None
        self.data = None
        self.data2 = None
        self.data3 = None
        self.states = []

        self.cooling_pump_1_address = None
        gas_valve_1_address = None
        feed_pump_1_address = None
        heating_mantle_1 = None
        pre_heating_mantle_1_address = None

        temperature_heating_mantle_1_address = None
        temperature_pre_heating_1_address = None
        temperature_coolant_1_address = None
        temperature_heating_mantle_1_address = None


        try:
            self.functions = {
                "mysql": partial(self.simple_switch),
                "heartbeat": partial(self.heartbeat),
                "temperatur": partial(self.get_temperature),
                "systemp": self.systemp,
                "request": self.state_request
            }
        except Exception: # as exception:
            pass


    def simple_switch(self, value, address, address_value, param1=None, param2=None, param3=None):
        logging.debug('Entering simple_switch function')

        try:
            print(Fore.RED + Back.GREEN + f'simple_switch', flush=True)
            self.data2 = json.loads(self.item)
            action = self.data2.get("mysql")
            if action == "set":
                # Remove "mysql" key from the dictionary
                data_to_process = self.data2.copy()
                data_to_process.pop("mysql")

                print(Fore.RED + Back.GREEN + f'simple_switch', flush=True)

                # Add 'action': 'set' to the new dictionary
                data_to_process["action"] = "set"
                #data_to_process["state"] = "update"

                self.queue_db.put(json.dumps(data_to_process))

                #self.state_request(value=None, address=None)
                self.state_request_all(value=None, address=None)
                #self.state_request_all(value="request_all_states", address=None)

        except Exception as e:
            # Handle exception
            pass


    def heartbeat(self, value, address, address_value, param1=None, param2=None, param3=None):
        self.data = {
            'heartbeat': 'true'
        }
        self.data = json.dumps(self.data)
        self.queue_bc.put(self.data)


    def get_temperature(self, value=None, address=None):
        print(Fore.GREEN + Back.WHITE + f'get_temperature', flush=True)

        # interval [1, 4] 5 is exclusive
        for address in range(1, 5):

            self.data = {
                'address': address,
                'type': 'read',
                'interprocess_state': 'state_requester'
            }
            self.data = json.dumps(self.data)
            self.queue_mb.put(self.data)


    def systemp(self):
        l = 0


    # get states from the mysql data base
    def state_request(self, value=None, address=None):

        with self.lock_io:
            logging.debug('Entering state_request function')
            #print(Fore.YELLOW + Back.RED + f'state_request self.item: {self.item}', flush=True)

            data = {
                'action': 'get',
                'state': 'request_all_states'
            }
            data = json.dumps(data)
            self.queue_db.put(data)

            data = {
                'action': 'get',
                'state': 'get_all',
                'interprocess_state': value
            }
            data = json.dumps(data)
            self.queue_db.put(data)


    # get states from the mysql data base
    def state_request_all(self, value=None, address=None):

        with self.lock_io:
            logging.debug('Entering state_request_all function')
            #print(Fore.YELLOW + Back.RED + f'state_request self.item: {self.item}', flush=True)

            data = {
                'action': 'get',
                'state': 'get_all',
                'interprocess_state': value
            }
            print(Fore.YELLOW + Back.RED + f'state_requester3 data: {data}', flush=True)
            data = json.dumps(data)
            self.queue_db.put(data)


    # get the imput data from the websocket queue
    def queue_handler(self):
        print(Fore.YELLOW + Back.RED + f'IO_queue_handler', flush=True)
        time.sleep(0.001)

        # Start functions state_requester I + II in a new thread
        state_requester_thread = threading.Thread(target=self.state_requester)
        state_requester_thread.start()
        temp_requester_thread = threading.Thread(target=self.state_requester2)
        temp_requester_thread.start()

        while True:
            time.sleep(0.001)
            try:
                # Does not Block when queue is empty
                if not self.queue_io.empty():

                    self.item = self.queue_io.get(block=False)
                    #time.sleep(0.0001)
                    print(Fore.WHITE + Back.GREEN + f'IO_queue_handler _ self.item: {self.item}', flush=True)

                    commands = json.loads(self.item)

                    new_state = {}

                    selected_keys = self.functions.keys()

                    for key, value in commands.items():
                        if key in selected_keys:
                            function = self.functions[key]
                        if hasattr(function, 'func'):  # Wenn die Funktion ein Teilobjekt ist, wird der erste Parameter automatisch übersprungen
                            new_state[key] = function(commands.get(key), commands.get(key+"_param1", None), commands.get(key+"_param2", None), commands.get(key+"_param3", None), commands.get(key+"_param4", None))
                        else:
                            new_state[key] = function(value)
                    else:
                        new_state[key] = value
            except Exception as e:
                print("An error occurred:", e)

        state_requester_thread.join()
        temp_requester_thread.join()


    # call function state_request periodically
    def state_requester(self, value=None, address=None):
        while True:
            time.sleep(20)
            #self.state_request(value, address)


    # Request all temperaturee states of modbus and broadcast to clients
    def state_requester2(self, value=None, address=None):
        #self.states = 0
        while True:
            time.sleep(7)
            self.get_temperature(value, address)


    # call function state_request periodically
    def state_requester3(self, value=None, address=None):
        while True:
            self.state_request_all(value, address)
            time.sleep(8)



    def queue_handler2(self):
        print(Fore.YELLOW + Back.RED + f'IO_queue_handler2', flush=True)
        time.sleep(0.001)

        # Start function in a new thread
        state_prcessing_thread = threading.Thread(target=self.state_requester3)
        state_prcessing_thread.start()

        while True:
            time.sleep(0.001)
            try:

                self.item = self.queue_io2.get()
                if self.item is not None:
                    self.item = json.loads(self.item)
                    print(Fore.GREEN + Back.WHITE + f'IO_Handler - queue_handler2 - get_all  self.item: {self.item}')

                device_data = {
                    "device_id": self.item.get("device_id", None),
                    "device_type": self.item.get("device_type", None),
                    "device_name": self.item.get("device_name", None),
                    "device_address_name": self.item.get("device_address_name", None),
                    "address": self.item.get("address", None),
                    "state_name": self.item.get("state_name", None),
                    "state_value": self.item.get("state_value", None),
                    "heating_temp": self.item.get("heating_temp", None),
                    "cooling_temp": self.item.get("cooling_temp", None),
                    "flow": self.item.get("flow", None),
                    "rate": self.item.get("rate", None),
                    "temp_device_name": self.item.get("temp_device_name", None),
                    "temp_device_id": self.item.get("temp_device_id", None),
                    "temp_device_address": self.item.get("temp_device_address", None),
                    "interprocess_state": self.item.get("interprocess_state", None)
                }

                #if self.item.get("interprocess_state") == 'request_all_states':
                data = {
                    'state_name': self.item.get("state_name", None),
                    'state_value': self.item.get("state_value", None)
                    #'interprocess_state': self.item.get("interprocess_state", None)
                }
                print(Fore.BLUE + Back.RED + f'self.item.get(interprocess_state) data: {data}', flush=True)
                self.queue_bc.put(json.dumps(data))

                self.queue_ctr.put(json.dumps(device_data))
                self.queue_ctr2.put(json.dumps(device_data))

            except Exception as e:
                print("An error occurred:", e)

        state_prcessing_thread.join()


#####################################################

#####################################################

# Interprocess State Communication
# self.item['interprocess_state']
# 
# modbus_tempctl
# state_requester
# modbus_tempctl_set_temp
#


class AddressHandler:
    def __init__(self, queue_ah, queue_ah2, queue_db, queue_io, queue_mb, queue_tempctr):
        super().__init__()
        self.item = None

        self.queue_ah = queue_ah
        self.queue_ah2 = queue_ah2

        self.queue_db = queue_db
        self.queue_io = queue_io
        self.queue_mb = queue_mb
        self.queue_tempctr = queue_tempctr

        self.address_types = ['cooling_pump_1_address', 'gas_valve_1_address', 'feed_pump_1_address',
                              'heating_mantle_1_address', 'temp_heating_mantle_1_address',
                              'temp_pre_heating_1_address', 'temp_coolant_1_address', 'pre_heating_mantle_1_address',
                              'temp_pre_heating_mantle_1_address', 'temp_feed_1_address', 'heating_feed_1_address',
                              'cooling_fan_1_address', 'feed_pressure_1_address']
        self.addresses = {address_type: None for address_type in self.address_types}


    def request_address_updates(self):
        try:
            for address_type in self.address_types:
                self.queue_db.put(json.dumps({'action': 'get_update_address', 'address_type': address_type}))
        except Exception:
            pass

    def address_get_update_loop(self):
        while True:
            try:
                self.request_address_updates()
                time_to_wait = 300
                time.sleep(time_to_wait)
                #print(Fore.WHITE + Back.BLUE + f'request_address_update')
            except Exception:
                pass

    def update_address(self, address_type, address_value):
        try:
            if address_type in self.address_types:
                self.addresses[address_type] = address_value
            else:
                print(f"Error: Unknown address type '{address_type}'")
        except Exception:
            pass

    def address_set_update_loop(self):
        while True:
            try:
                self.item = self.queue_ah.get()
                self.item = json.loads(self.item)
                #print(Fore.WHITE + Back.RED + f'self.item {self.item}')

                action = self.item.get('action')
                address_type = self.item.get('address_type')
                address_value = self.item.get('address_value')

                if action == 'update_address':
                    self.update_address(address_type, address_value)
                    #print(Fore.WHITE + Back.RED + f'Action: {action}, Address Type: {address_type}, Address Value: {address_value}')

                else:
                    print(f"Error: Unknown action '{action}'")

            except Exception:
                pass


    def get_address(self, address_type):
        if address_type in self.addresses:
            return self.addresses[address_type]
        else:
            print(f"Error: Unknown address type '{address_type}'")
            return None

    def queue_handler(self):
        print(Fore.YELLOW + Back.RED + f'AddressHandler_queue_handler2', flush=True)

        time.sleep(0.1)
        #print(Fore.WHITE + Back.BLUE + f'ADRESS HANDLER PROCESS')

        # Start threads for request addresses
        address_get_update_loop_thread = threading.Thread(target=self.address_get_update_loop)
        address_get_update_loop_thread.start()
        address_set_update_loop_thread = threading.Thread(target=self.address_set_update_loop)
        address_set_update_loop_thread.start()

        while True:
            time.sleep(0.1)
            try:
                self.item = self.queue_ah2.get()
                self.item = json.loads(self.item)
                #print(Fore.WHITE + Back.BLUE + f'self.item {self.item}')

                if action == 'get_address':
                    address_value = self.get_address(address_type)
                    if address_value is not None:
                        response = {
                            'action': 'address_response',
                            'address_type': address_type,
                            'address_value': address_value
                        }
                        #self.queue_ah2.put(json.dumps(response))

            except Exception:
                pass
        address_get_update_loop_thread.join()
        address_set_update_loop_thread.join()



#####################################################

#####################################################


class MySQLDatabase:
    def __init__(self, lock, lock1, lock2, lock3, lock4, queue_db, queue_db2, queue_db_read, queue_db_write, queue_io, queue_io2, queue_bc, queue_tempctr2, queue_ah):
        super().__init__()

        #self.lock = multiprocessing.Lock()
        #self.lock = Lock()
        self.lock = lock

        self.lock1 = lock1
        self.lock2 = lock2
        self.lock3 = lock3
        self.lock4 = lock4

        self.locked1 = multiprocessing.Value('i', 0)
        self.locked2 = multiprocessing.Value('i', 0)

        self.locked = multiprocessing.Value('i', 0)

        self.item = None
        self.result = None
        self.results = None

        self.queue_ah = queue_ah
        self.queue_db = queue_db
        self.queue_db2 = queue_db2

        self.queue_db_read = queue_db_read
        self.queue_db_write = queue_db_write

        self.queue_io = queue_io
        self.queue_io2 = queue_io2
        self.queue_bc = queue_bc
        self.queue_tempctr2 = queue_tempctr2
        self.host = '192.168.0.17'
        self.user = 'root'
        self.password = '#q23LopaQ7'
        self.database = 'websocket_database'
        self.connection = None
        self.cursor = None


        self.connection = None
        self.cursor = None
        self.engine = None
        self.session = None

        connection_string = f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.database}"
        self.engine = create_engine(connection_string)
        self.connect()



    class Device(Base):
        __tablename__ = 'devices'
        device_id = Column(Integer, primary_key=True)
        device_address_name = Column(String(64))
        address = Column(Integer, unique=True)
        device_name = Column(String(64))
        device_type = Column(String(64))
        device_group_function = Column(String(64))

    class CoolingState(Base):
        __tablename__ = 'cooling_states'
        id = Column(Integer, primary_key=True)
        device_id = Column(Integer, ForeignKey('devices.device_id'))
        state_name = Column(String(64))
        state_value = Column(String(64))
        temp_device_id = Column(Integer, ForeignKey('devices.device_id'))
        cooling_temp = Column(Integer)
        power_rate = Column(Integer)
        device_group_function = Column(String(64))
        device = relationship("Device", foreign_keys=[device_id])
        temp_device = relationship("Device", foreign_keys=[temp_device_id])

    class HeatingState(Base):
        __tablename__ = 'heating_states'
        id = Column(Integer, primary_key=True)
        device_id = Column(Integer, ForeignKey('devices.device_id'))
        state_name = Column(String(64))
        state_value = Column(String(64))
        heating_temp = Column(Integer)
        temp_device_id = Column(Integer, ForeignKey('devices.device_id'), unique=True)
        device_group_function = Column(String(64))
        device = relationship("Device", foreign_keys=[device_id])
        temp_device = relationship("Device", foreign_keys=[temp_device_id])

    class PressureState(Base):
        __tablename__ = 'pressure_states'
        id = Column(Integer, primary_key=True)
        device_id = Column(Integer, ForeignKey('devices.device_id'))
        state_name = Column(String(64))
        state_value = Column(String(64))
        pres_device_id = Column(Integer, ForeignKey('devices.device_id'))
        pressure_abs = Column(Float, nullable=True)
        pressure_div = Column(Float, nullable=True)
        device_group_function = Column(String(64))
        device = relationship("Device", foreign_keys=[device_id])
        pres_device = relationship("Device", foreign_keys=[pres_device_id])

    class PumpState(Base):
        __tablename__ = 'pump_states'
        id = Column(Integer, primary_key=True)
        device_id = Column(Integer, ForeignKey('devices.device_id'))
        state_name = Column(String(64))
        state_value = Column(String(64))
        rate = Column(Integer)
        power = Column(Integer)
        device_group_function = Column(String(64))
        device = relationship("Device", foreign_keys=[device_id])

    class ValveState(Base):
        __tablename__ = 'valve_states'
        id = Column(Integer, primary_key=True)
        device_id = Column(Integer, ForeignKey('devices.device_id'))
        state_name = Column(String(64))
        state_value = Column(String(64))
        flow = Column(Integer)
        device_group_function = Column(String(64))
        device = relationship("Device", foreign_keys=[device_id])


#####################################################


    def connect(self):
        print("Connecting to the database")  # Debug print
        connection_string = f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.database}"
        engine = create_engine(connection_string, poolclass=NullPool)
        Session = sessionmaker(bind=engine, expire_on_commit=False)
        session = Session()

        return session


    def disconnect(self):
        self.session.close()
        self.connection.close()
        print("Disconnected from the database")  # Debug print


    def run_in_thread(self, func, *args, **kwargs):
        result_container = []

        def thread_wrapper(func, *args, result_container=result_container):
            result = func(*args, **kwargs)
            if result is not None:
                result_container.extend(result)

        thread = Thread(target=thread_wrapper, args=(func, *args))
        thread.start()
        print(f"Debug: Thread status, alive: {thread.is_alive()}")
        thread.join()
        print(f"Debug: Thread status, alive: {thread.is_alive()}")  # Debug-Ausgabe zum Überprüfen des Thread-Status
        return result_container



    def get_table_name(self, state_name):
        logger.debug('Entering get_table_name function')
        print(f"Debug: get_table_name called with state_name: {state_name}")  # Debug-Ausgabe

        print("Debug: get_table_name")  # Debug-Ausgabe
        query = f"""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE COLUMN_NAME = 'state_name' AND TABLE_SCHEMA = 'websocket_database'
        """

        tables = self.read_db(query)
        print(f"Debug: Found tables: {tables}")  # Debug-Ausgabe

        if not tables:  # Überprüfen, ob 'tables' leer ist
            print("Debug: No tables found by read_db")  # Debug-Ausgabe
            return None

        for table in tables:
            table_name = table[0]
            query = f"SELECT state_name FROM {table_name} WHERE state_name = :state_name"
            params = {'state_name': state_name}
            result = self.read_db(query, params)
            print(f"Debug: Checking table '{table_name}', result: {result}")  # Debug-Ausgabe

            if result:
                print(f"Debug: Found matching table_name: {table_name}")  # Debug-Ausgabe
                return table_name

        print(f"Debug: No matching table_name found")  # Debug-Ausgabe
        return None



    def update_db(self, query, params=None, result_container=None):
        logger.debug('Entering update_db function')

        # acquire the lock
        with self.lock:
            print(f"Debug: update_db called with query: {query} and params: {params}")

            try:

                if result_container is not None:
                    result_container.append(True)

                # Erstellen einer neuen Verbindung und Session für jeden Thread
                connection_string = f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.database}"
                engine = create_engine(connection_string, poolclass=NullPool)
                Session = sessionmaker(bind=engine, expire_on_commit=False)
                session = Session()

                statement = text(query)

                if params:
                    session.execute(statement, params)
                else:
                    session.execute(statement)

                # Commit the transaction
                session.commit()

                # Schließen der Session
                session.close()

            except Exception as e:
                print(f"Error in update_db: {e}")
                session.close()


    def read_db(self, query, params=None, result_container=None):
        logger.debug('Entering read_db function')

        # acquire the lock
        with self.lock:
            print(f"Debug: read_db called with query: {query} and params: {params}")

            try:
                # Erstellen einer neuen Verbindung und Session für jeden Thread
                connection_string = f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.database}"
                engine = create_engine(connection_string, poolclass=NullPool)
                Session = sessionmaker(bind=engine, expire_on_commit=False)
                session = Session()

                statement = text(query)

                if params:
                    results = session.execute(statement, params)
                else:
                    results = session.execute(statement)

                result = results.fetchall()

                # Schließen der Session
                session.close()

                if result_container is not None:
                    result_container.extend(result)

                print(f"Debug: read_db result: {result}")  # Hinzufügen einer Debug-Ausgabe, um den Wert von 'result' zu überprüfen
                # Rückgabe des Ergebnisses innerhalb des try-Blocks
                return result

            except Exception as e:
                print(f"Error in read_db: {e}")
                session.close()



    def read_db2(self, query, result_container=None):
        logger.debug('Entering read_db2 function')

        # acquire the lock
        with self.lock:
            print(f"Debug: read_db2 called")  # Debug-Ausgabe

            data = []  # Definieren Sie 'data' vor dem ersten 'try'-Block

            try:
                # Erstellen einer neuen Verbindung und Session für jeden Thread
                connection_string = f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.database}"
                engine = create_engine(connection_string, poolclass=NullPool)
                Session = sessionmaker(bind=engine, expire_on_commit=False)
                session = Session()

                try:
                    print("Executing query")
                    statement = text(query)  # Use the text function to create a textual statement
                    results = session.execute(statement)
                    print("Query executed")

                    # Get the column names
                    column_names = results.keys()

                    # Convert each row into a dictionary with column names as keys
                    for row in results:
                        row_data = dict(zip(column_names, row))
                        data.append(row_data)

                except SQLAlchemyError as e:
                    print(f"An error occurred: {e}")
                finally:
                    # Close the session
                    session.close()

                if result_container is not None:
                    result_container.extend(data)

                return data

            except Exception as e:
                print(f"Error in read_db2: {e}")
                self.disconnect()


    def queue_handler(self):
        print(Fore.YELLOW + Back.RED + f'MYSQL_queue_handler', flush=True)
        while True:
            time.sleep(0.0001)

            try:
                self.item = self.queue_db.get()
                self.item = json.loads(self.item)

                # Process incoming message
                action = self.item.get('action')
                state = self.item.get('state')
                address = self.item.get('address')
                state_name = self.item.get('state_name')
                state_value = self.item.get('state_value')
                device_id = self.item.get('device_id')
                heating_temp = self.item.get('heating_temp')
                rate = self.item.get('rate')
                interprocess_state = self.item.get('interprocess_state')

                keys_map = {'heating_temp', 'cooling_temp', 'power_rate', 'reflux_rate', 'pressure_abs', 'pressure_div', 'rate', 'power', 'flow'}

                print(Fore.BLACK + Back.WHITE + f'Action: {action}, State: {state}, Address: {address}, State_Name: {state_name}, State_Value: {state_value}')

                        #query = f"""
                        #SELECT hs.address, hs.state_value
                        #FROM heating_states hs
                        #INNER JOIN states s ON hs.state_id = s.id
                        #WHERE s.state_name = 'heating_temp'
                        #"""

                # get
                if action == 'get':

                    if state == 'read':
                        query = f'SELECT * FROM heating_states WHERE address = {address}'
                        result = self.run_in_thread(self.read_db, query)
                        self.queue_db_read.put(json.dumps({'action': 'read', 'result': result}))

                    elif state == 'state_value':
                        table = f"{state}_states"  # Tabellennamen dynamisch generieren
                        query = f'SELECT state_value FROM {table} WHERE state_name = %s AND address = %s'
                        #result = self.read_db(query, (state, address))
                        result = self.run_in_thread(self.read_db, query)

                    elif state == 'request_all_states':
                        print(Fore.BLUE + Back.GREEN + f'request_all_states from mysql_queue_handler I !!!')

                        query = f"""
                        SELECT TABLE_NAME
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE COLUMN_NAME IN ('state_name', 'state_value') AND TABLE_SCHEMA = 'websocket_database'
                        GROUP BY TABLE_NAME
                        HAVING COUNT(*) = 2
                        """


                        #tables = self.read_db(query)
                        tables = self.run_in_thread(self.read_db, query)
                        print(Fore.BLUE + Back.YELLOW + f'request_all_states  tables: {tables}')

                        for table in tables:
                            table_name = table[0]
                            query = f"SELECT state_name, state_value FROM {table_name}"
                            #results = self.read_db(query)
                            results = self.run_in_thread(self.read_db, query)

                            for result in results:
                                state_name, state_value = result
                                data = {
                                    'state_name': state_name,
                                    'state_value': state_value
                                }
                                print(Fore.BLUE + Back.YELLOW + f'request_all_states  data: {data}')
                                self.queue_bc.put(json.dumps(data))


                    elif state == 'get_process_parameters':
                        table_name = self.get_table_name(state_name)

                        # Find the column name from the JSON object
                        column_name = None
                        for key in self.item.keys():
                            if key in keys_map:
                                column_name = key
                                break

                        if table_name and column_name:
                            query = f"""
                            SELECT {column_name}
                            FROM {table_name}
                            WHERE state_name = %s
                            """
                            params = (state_name,)

                            #result = self.read_db(query, params)
                            result = self.run_in_thread(self.read_db, query)
                            if result:
                                self.queue_io2.put(json.dumps({'state': state, 'state_name': state_name, 'column_name': column_name, 'value': result[0]}))
                            else:
                                print(f"Error: Could not get value for state_name '{state_name}' and column_name '{column_name}'")
                        else:
                            print(f"Error: Unknown table_name '{table_name}' or column_name '{column_name}' for action 'get'")



                    elif state == 'get_all':
                        print(Fore.BLUE + Back.GREEN + f'"Entered get_all state _ queue_handler I"')

                        query_heating_states = """
                            SELECT d.device_id, d.device_name, d.address, d.device_type, d.device_group_function,
                                   hs.state_name, hs.heating_temp, hs.temp_device_id, hs.state_value,
                                   temp_d.device_name as temp_device_name, temp_d.address as temp_device_address
                            FROM heating_states hs
                            LEFT JOIN devices d ON d.device_id = hs.device_id
                            LEFT JOIN devices temp_d ON temp_d.device_id = hs.temp_device_id; 
                        """

                        query_cooling_states = """
                              SELECT d.device_id, d.device_name, d.address, d.device_type, d.device_group_function,
                                   cs.state_name, cs.cooling_temp, cs.temp_device_id, cs.state_value, cs.power_rate,
                                   temp_d.device_name as temp_device_name, temp_d.address as temp_device_address
                            FROM cooling_states cs
                            LEFT JOIN devices d ON d.device_id = cs.device_id
                            LEFT JOIN devices temp_d ON temp_d.device_id = cs.temp_device_id;
                        """

                        query_pressure_states = """
                            SELECT d.device_id, d.device_name, d.address, d.device_type, d.device_group_function,
                                   state_name, pres_device_id, pressure_abs, pressure_div, state_value
                            FROM devices d
                            RIGHT JOIN pressure_states ps ON d.device_id = ps.device_id;
                        """

                        query_pump_states = """
                            SELECT d.device_id, d.device_name, d.address, d.device_type, d.device_group_function,
                                   state_name, rate, power, state_value
                            FROM devices d
                            RIGHT JOIN pump_states pms ON d.device_id = pms.device_id;
                        """

                        query_valve_states = """
                            SELECT d.device_id, d.device_name, d.address, d.device_type, d.device_group_function,
                                   state_name, flow, state_value
                            FROM devices d
                            RIGHT JOIN valve_states vs ON d.device_id = vs.device_id;
                        """

                        #query_temp_heating_device_address = """
                        #    SELECT d.device_id, d.device_name, d.address as temp_device_address, d.device_type,
                        #            state_name, temp_device_id
                        #    FROM devices d
                        #    RIGHT JOIN heating_states hs ON d.device_id = hs.temp_device_id;
                        #"""

                        #query_temp_cooling_device_address = """
                        #    SELECT d.device_id, d.device_name, d.address as temp_device_address, d.device_type,
                        #           state_name, temp_device_id
                        #    FROM devices d
                        #    RIGHT JOIN cooling_states cs ON d.device_id = cs.temp_device_id;
                        #"""



                        for query in [query_heating_states, query_cooling_states, query_pressure_states, query_pump_states, query_valve_states,]:
                            #print(Fore.BLUE + Back.YELLOW + f'Executing query: {query}')  # Add this line
                            #results = self.read_db2(query)
                            results = self.run_in_thread(self.read_db2, query)

                            for row in results:
                                #print(Fore.BLUE + Back.GREEN + f'get_all  row: {row}')
                                if self.item.get('interprocess_state') == 'request_all_states':
                                    row["interprocess_state"] = interprocess_state
                                self.queue_io2.put(json.dumps(row))



                    else:
                        print(f"Error: Unknown state '{state}' for action 'get'")


                # set
                elif action == 'set':

                    if state == 'update':
                        print(f"Debug: state_update")  # Debug-Ausgabe
                        table_name = self.get_table_name(state_name)
                        print(f"Debug: table_name found: {table_name}")  # Debug-Ausgabe

                        if table_name:
                            query = f"""
                            UPDATE {table_name}
                            SET state_value = :state_value
                            WHERE state_name = :state_name
                            """
                            params = {'state_value': state_value, 'state_name': state_name}
                            print(f"Debug: Executing update_db with params: {params}")  # Debug-Ausgabe

                            try:
                                #self.update_db(query, params)
                                self.run_in_thread(self.update_db, query, params)
                                print(f"Debug: update_db executed successfully")  # Debug-Ausgabe
                            except Exception as e:
                                print(f"Debug: Error occurred while executing update_db: {e}")  # Debug-Ausgabe

                        else:
                            print(f"Error: Unknown table_name '{table_name}' for action 'set'")





                    elif state == 'update_process_parameters':
                        table_name = self.get_table_name(state_name)

                        column_name = None
                        column_value = None
                        for key, value in self.item.items():
                            if key in keys_map:
                                column_name = key
                                column_value = value
                                break

                        if table_name and column_name and column_value is not None:
                            query = f"""
                            UPDATE {table_name}
                            SET {column_name} = :column_value
                            WHERE state_name = :state_name
                            """
                            params = {'column_value': column_value, 'state_name': state_name}
                            print(f"Debug: Executing update_db with params: {params}")  # Debug-Ausgabe

                            self.run_in_thread(self.update_db, query, params)
                            #self.update_db(query, params)

                        else:
                            print(f"Error: Unknown table_name '{table_name}' or column_name '{column_name}' for action 'set'")

                    else:
                        print(f"Error: Unknown state '{state}' for action 'set'")




                elif action == 'get_update_address':
                    address_type = self.item.get('address_type')
                    print(Fore.WHITE + Back.BLUE + f'Getting update_address for {address_type}')

                    query = f"""
                    SELECT address
                    FROM devices
                    WHERE device_address_name = :address_type
                    """

                    params = {'address_type': address_type}
                    result = self.read_db(query, params)

                    if result:
                        data = {
                            'action': 'update_address',
                            'address_type': address_type,
                            'address_value': result[0]
                        }
                        data = json.dumps(data)
                        self.queue_ah.put(data)
                        #print(Fore.GREEN + Back.YELLOW + f'DATA SENDED')
                    else:
                        print(Fore.RED + Back.YELLOW + f'Error: No result found for {address_type}')



                else:
                    print(f"Error: Unknown action '{action}'")

            except Exception:
                pass


#####################################################

    # Load Balancing
    def queue_handler2(self):
        print(Fore.YELLOW + Back.RED + f'MYSQL_queue_handler2', flush=True)
        while True:
            time.sleep(0.0001)

            try:
                self.item = self.queue_db.get()
                self.item = json.loads(self.item)

                # Process incoming message
                action = self.item.get('action')
                state = self.item.get('state')
                address = self.item.get('address')
                state_name = self.item.get('state_name')
                state_value = self.item.get('state_value')
                device_id = self.item.get('device_id')
                heating_temp = self.item.get('heating_temp')
                rate = self.item.get('rate')

                keys_map = {'heating_temp', 'cooling_temp', 'power_rate', 'reflux_rate', 'pressure_abs', 'pressure_div', 'rate', 'power', 'flow'}

                print(Fore.BLACK + Back.WHITE + f'Action: {action}, State: {state}, Address: {address}, State_Name: {state_name}, State_Value: {state_value}')

                        #query = f"""
                        #SELECT hs.address, hs.state_value
                        #FROM heating_states hs
                        #INNER JOIN states s ON hs.state_id = s.id
                        #WHERE s.state_name = 'heating_temp'
                        #"""

                # get
                if action == 'get':

                    if state == 'read':
                        query = f'SELECT * FROM heating_states WHERE address = {address}'
                        result = self.read_db(query)
                        self.queue_db_read.put(json.dumps({'action': 'read', 'result': result}))

                    elif state == 'state_value':
                        table = f"{state}_states"  # Tabellennamen dynamisch generieren
                        query = f'SELECT state_value FROM {table} WHERE state_name = %s AND address = %s'
                        #result = self.read_db(query, (state, address))
                        result = self.run_in_thread(self.read_db, query)

                    elif state == 'request_all_states':
                        print(Fore.BLUE + Back.GREEN + f'request_all_states from mysql_queue_handler II !!!')

                        query = f"""
                        SELECT TABLE_NAME
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE COLUMN_NAME IN ('state_name', 'state_value') AND TABLE_SCHEMA = 'websocket_database'
                        GROUP BY TABLE_NAME
                        HAVING COUNT(*) = 2
                        """


                        #tables = self.read_db(query)
                        tables = self.run_in_thread(self.read_db, query)
                        print(Fore.BLUE + Back.YELLOW + f'request_all_states  tables: {tables}')

                        for table in tables:
                            table_name = table[0]
                            query = f"SELECT state_name, state_value FROM {table_name}"
                            #results = self.read_db(query)
                            results = self.run_in_thread(self.read_db, query)

                            for result in results:
                                state_name, state_value = result
                                data = {
                                    'state_name': state_name,
                                    'state_value': state_value
                                }
                                print(Fore.BLUE + Back.YELLOW + f'request_all_states  data: {data}')
                                self.queue_bc.put(json.dumps(data))


                    elif state == 'get_process_parameters':
                        table_name = self.get_table_name(state_name)

                        # Find the column name from the JSON object
                        column_name = None
                        for key in self.item.keys():
                            if key in keys_map:
                                column_name = key
                                break

                        if table_name and column_name:
                            query = f"""
                            SELECT {column_name}
                            FROM {table_name}
                            WHERE state_name = %s
                            """
                            params = (state_name,)

                            #result = self.read_db(query, params)
                            result = self.run_in_thread(self.read_db, query)
                            if result:
                                self.queue_io2.put(json.dumps({'state': state, 'state_name': state_name, 'column_name': column_name, 'value': result[0]}))
                            else:
                                print(f"Error: Could not get value for state_name '{state_name}' and column_name '{column_name}'")
                        else:
                            print(f"Error: Unknown table_name '{table_name}' or column_name '{column_name}' for action 'get'")



                    elif state == 'get_all':
                        print(Fore.BLUE + Back.GREEN + f'"Entered get_all state _ queue_handler II"')

                        query_heating_states = """
                            SELECT d.device_id, d.device_name, d.address, d.device_type, d.device_group_function,
                                   hs.state_name, hs.heating_temp, hs.temp_device_id, hs.state_value,
                                   temp_d.device_name as temp_device_name, temp_d.address as temp_device_address
                            FROM heating_states hs
                            LEFT JOIN devices d ON d.device_id = hs.device_id
                            LEFT JOIN devices temp_d ON temp_d.device_id = hs.temp_device_id; 
                        """

                        query_cooling_states = """
                              SELECT d.device_id, d.device_name, d.address, d.device_type, d.device_group_function,
                                   cs.state_name, cs.cooling_temp, cs.temp_device_id, cs.state_value, cs.power_rate,
                                   temp_d.device_name as temp_device_name, temp_d.address as temp_device_address
                            FROM cooling_states cs
                            LEFT JOIN devices d ON d.device_id = cs.device_id
                            LEFT JOIN devices temp_d ON temp_d.device_id = cs.temp_device_id;
                        """

                        query_pressure_states = """
                            SELECT d.device_id, d.device_name, d.address, d.device_type, d.device_group_function,
                                   state_name, pres_device_id, pressure_abs, pressure_div, state_value
                            FROM devices d
                            RIGHT JOIN pressure_states ps ON d.device_id = ps.device_id;
                        """

                        query_pump_states = """
                            SELECT d.device_id, d.device_name, d.address, d.device_type, d.device_group_function,
                                   state_name, rate, power, state_value
                            FROM devices d
                            RIGHT JOIN pump_states pms ON d.device_id = pms.device_id;
                        """

                        query_valve_states = """
                            SELECT d.device_id, d.device_name, d.address, d.device_type, d.device_group_function,
                                   state_name, flow, state_value
                            FROM devices d
                            RIGHT JOIN valve_states vs ON d.device_id = vs.device_id;
                        """


                        # temp_device_address
                        query_valve_states = """
                            SELECT d.device_id, d.device_name, d.address as temp_device_address, d.device_type,
                                    state_name, temp_device_id
                            FROM devices d
                            RIGHT JOIN heating_states hs ON d.device_id = hs.temp_device_id;
                        """

                        # temp_device_address
                        query_valve_states = """
                            SELECT d.device_id, d.device_name, d.address as temp_device_address, d.device_type,
                                   state_name, temp_device_id
                            FROM devices d
                            RIGHT JOIN cooling_states cs ON d.device_id = cs.temp_device_id;
                        """



                        for query in [query_heating_states, query_cooling_states, query_pressure_states, query_pump_states, query_valve_states]:
                            #print(Fore.BLUE + Back.YELLOW + f'Executing query: {query}')  # Add this line
                            #results = self.read_db2(query)
                            results = self.run_in_thread(self.read_db2, query)

                            for row in results:
                                #print(Fore.BLUE + Back.GREEN + f'get_all  row: {row}')
                                if self.item.get('interprocess_state') == 'request_all_states':
                                    row["interprocess_state"] = interprocess_state
                                self.queue_io2.put(json.dumps(row))



                    else:
                        print(f"Error: Unknown state '{state}' for action 'get'")


                # set
                elif action == 'set':

                    if state == 'update':
                        print(f"Debug: state_update")  # Debug-Ausgabe
                        table_name = self.get_table_name(state_name)
                        print(f"Debug: table_name found: {table_name}")  # Debug-Ausgabe

                        if table_name:
                            query = f"""
                            UPDATE {table_name}
                            SET state_value = :state_value
                            WHERE state_name = :state_name
                            """
                            params = {'state_value': state_value, 'state_name': state_name}
                            print(f"Debug: Executing update_db with params: {params}")  # Debug-Ausgabe

                            try:
                                #self.update_db(query, params)
                                self.run_in_thread(self.update_db, query, params)
                                print(f"Debug: update_db executed successfully")  # Debug-Ausgabe
                            except Exception as e:
                                print(f"Debug: Error occurred while executing update_db: {e}")  # Debug-Ausgabe

                        else:
                            print(f"Error: Unknown table_name '{table_name}' for action 'set'")





                    elif state == 'update_process_parameters':
                        table_name = self.get_table_name(state_name)

                        column_name = None
                        column_value = None
                        for key, value in self.item.items():
                            if key in keys_map:
                                column_name = key
                                column_value = value
                                break

                        if table_name and column_name and column_value is not None:
                            query = f"""
                            UPDATE {table_name}
                            SET {column_name} = :column_value
                            WHERE state_name = :state_name
                            """
                            params = {'column_value': column_value, 'state_name': state_name}
                            print(f"Debug: Executing update_db with params: {params}")  # Debug-Ausgabe

                            self.run_in_thread(self.update_db, query, params)
                            #self.update_db(query, params)

                        else:
                            print(f"Error: Unknown table_name '{table_name}' or column_name '{column_name}' for action 'set'")

                    else:
                        print(f"Error: Unknown state '{state}' for action 'set'")




                elif action == 'get_update_address':
                    address_type = self.item.get('address_type')
                    print(Fore.WHITE + Back.BLUE + f'Getting update_address for {address_type}')

                    query = f"""
                    SELECT address
                    FROM devices
                    WHERE device_address_name = :address_type
                    """

                    params = {'address_type': address_type}
                    result = self.read_db(query, params)

                    if result:
                        data = {
                            'action': 'update_address',
                            'address_type': address_type,
                            'address_value': result[0]
                        }
                        data = json.dumps(data)
                        self.queue_ah.put(data)
                        #print(Fore.GREEN + Back.YELLOW + f'DATA SENDED')
                    else:
                        print(Fore.RED + Back.YELLOW + f'Error: No result found for {address_type}')



                else:
                    print(f"Error: Unknown action '{action}'")

            except Exception:
                pass



#####################################################

#####################################################


class Modbus:
    def __init__(self, client, lock_mb, queue_bc, queue_mb, queue_mb2, queue_io, queue_tempctr):
        super().__init__()
        #self.client = ModbusTcpClient(host, port)

        self.modbus = client

        self.item = None
        self.lock = lock_mb
        self.command_map = None

        self.result = None
        self.value = None
        self.address = None
        self.type = None
        self.interprocess_state = None


        self.queue_bc = queue_bc
        self.queue_mb = queue_mb
        self.queue_mb2 = queue_mb2
        self.queue_io = queue_io
        self.queue_tempctr = queue_tempctr

        # Define address-command mapping
        self.command_map_read = {
        # Read Coils
        1: {'func': self.read_register, 'type': 'read'},
        2: {'func': self.read_register, 'type': 'read'},
        3: {'func': self.read_register, 'type': 'read'},
        4: {'func': self.read_register, 'type': 'read'},
        512: {'func': self.read_coil, 'type': 'read'},
        513: {'func': self.read_coil, 'type': 'read'},
        514: {'func': self.read_coil, 'type': 'read'},
        515: {'func': self.read_coil, 'type': 'read'},
        524: {'func': self.read_coil, 'type': 'read'},
        525: {'func': self.read_coil, 'type': 'read'},
        526: {'func': self.read_coil, 'type': 'read'},
        528: {'func': self.read_coil, 'type': 'read'},
        }
        # Write Coils
        self.command_map_write = {
        1: {'func': self.write_register, 'type': 'write'},
        2: {'func': self.write_register, 'type': 'write'},
        3: {'func': self.write_register, 'type': 'write'},
        4: {'func': self.write_register, 'type': 'write'},
        512: {'func': self.write_coil, 'type': 'write'},
        513: {'func': self.write_coil, 'type': 'write'},
        514: {'func': self.write_coil, 'type': 'write'},
        520: {'func': self.write_coil, 'type': 'write'},
        521: {'func': self.write_coil, 'type': 'write'},
        522: {'func': self.write_coil, 'type': 'write'},
        524: {'func': self.write_coil, 'type': 'write'},
        525: {'func': self.write_coil, 'type': 'write'},
        526: {'func': self.write_coil, 'type': 'write'},
        528: {'func': self.write_coil, 'type': 'write'},
        523: {'func': self.write_coil, 'type': 'write'},
        532: {'func': self.write_coil, 'type': 'write'},
        533: {'func': self.write_coil, 'type': 'write'},
        544: {'func': self.write_coil, 'type': 'write'},
        536: {'func': self.write_coil, 'type': 'write'},
        }
        # Write Register
        self.command_map_write_register = {
        512: {'func': self.write_register, 'type': 'write'},
        513: {'func': self.write_register, 'type': 'write'},
        514: {'func': self.write_register, 'type': 'write'},
        515: {'func': self.write_register, 'type': 'write'},
        }
        # Read Register
        self.command_map_read_register = {
        1: {'func': self.read_register, 'type': 'read_register'},
        2: {'func': self.read_register, 'type': 'read_register'},
        3: {'func': self.read_register, 'type': 'read_register'},
        4: {'func': self.read_register, 'type': 'read_register'},
        512: {'func': self.read_register, 'type': 'read'},
        513: {'func': self.read_register, 'type': 'read'},
        514: {'func': self.read_register, 'type': 'read'},
        515: {'func': self.read_register, 'type': 'read'},
        }



    def connect(self):
        #self.client.connect()
        self.modbus = client


    def close(self):
        self.modbus.close()


    def write_register(self, address, value, value1=None, value2=None):

        #with self.lock:

        try:
            #self.modbus.write_register(0x00, address, value)

            #self.modbus.write_registers(address, [value, value], unit=UNIT)

            #rq = self.modbus.write_register(512, 16383, unit=UNIT)

            rq = self.modbus.write_register(address, value, unit=UNIT)

            print(Fore.BLACK + Back.BLUE + f'write_register triggered', flush=True)

        except Exception:
            pass



    def read_register(self, address, value=None, value1=None, value2=None):
        response_dict = {'registers': [], 'unit': None, 'address': None}

        #with self.lock:

        try:

            #response = client.read_holding_registers(i, 1, unit=UNIT)

            response = self.modbus.read_holding_registers(address, 8, unit=UNIT)
            #response = self.modbus.read_holding_registers(0x00, 8, unit=UNIT)


            values = response.registers

            #t = response.registers[1]

            t = int(random.uniform(400,440))

            print(Fore.BLACK + Back.BLUE + f'read_register triggered - t, response, address, values: ', t, response, address, values, flush=True)

            return t/10 #250 #values #response_dict #t/10

        except Exception:
            pass 


    def write_coil(self, address, value, value1=None, value2=None):

        #with self.lock:
        #self.lock.acquire()

        try:
            #rq = self.modbus.write_coil(address, value == "on", unit=UNIT)
            rq = self.modbus.write_coil(address, value, unit=UNIT)

            print(Fore.BLACK + Back.BLUE + f'write_coil triggered', flush=True)
            print(Fore.WHITE + Back.MAGENTA + f'write_coil: address: {address} value: {value} ', flush=True)
            print(Fore.WHITE + Back.MAGENTA + f'write_coil: address: {address} value: {value} ', flush=True)


        except Exception:
            pass
        #finally:
        #    self.lock.release()

#Item from Modbus_queue_handler:  {'value': True, 'address': 514, 'type': 'write'}
#Item from Modbus_queue_handler2:  {'value': 1901, 'address': 524, 'type': 'write', 'interprocess_state': 'modbus_tempctl_set_temp'}
#Item from Modbus_queue_handler2:  {'value': True, 'address': 512, 'type': 'write'}




    def read_coil(self, address):

        #with self.lock:

        try:

            result = self.modbus.read_coils(address, unit=UNIT)
            print(Fore.BLACK + Back.YELLOW + f'read_coil triggered', result.bits[0], flush=True)


            return result.bits[0]

        except Exception:
            pass



    def modbus_command(self, command_map_read, command_map_write, command_map_write_register, command_map_read_register, address, command_type, value=None, value1=None, value2=None):
        print(Fore.RED + f'modbus_command', flush=True)

        with self.lock:
            try:
                if command_type == 'read':
                    if address in command_map_read:
                        command_func = command_map_read[address]['func']
                        result = command_func(address)
                        return result
                    else:
                        print(f"Error: Invalid address {address}", flush=True)

                elif command_type == 'write':
                    if address in command_map_write:
                        command_func = command_map_write[address]['func']
                        result = command_func(address, value, value1=None, value2=None)
                        return result
                    else:
                        print(f"Error: Invalid address {address}", flush=True)

                elif command_type == 'write_register':
                    if address in command_map_write_register:
                        command_func = command_map_write_register[address]['func']
                        result = command_func(address, value, value1=None, value2=None)
                        return result
                    else:
                        print(f"Error: Invalid address {address}", flush=True)

                elif command_type == 'read_register':
                    if address in command_map_read_register:
                        command_func = command_map_read_register[address]['func']
                        result = command_func(address, value=None, value1=None, value2=None)
                        return result
                    else:
                        print(f"Error: Invalid address {address}", flush=True)

                else:
                    print(f"Error: Invalid command type {command_type}", flush=True)

            except Exception:
                pass



        #finally:
            #self.lock.release()  # Releasing the lock after operation is finished



    def queue_handler(self):
        print(Fore.YELLOW + Back.RED + f'Modbus_queue_handler', flush=True)

        while True:

            time.sleep(0.05)
            try:
                self.item = self.queue_mb.get()
                self.item = json.loads(self.item)

                #if self.item['address'] in range(512, 550):
                #    print("Item from Modbus_queue_handler: " , self.item, flush=True)

                logging.debug(f"{Fore.RED} Item from Modbus_queue_handler self.item: {self.item} {Style.RESET_ALL}" )


                # Extrahieren von address und value aus dem item-Dictionary
                if 'value' in self.item:
                    value = self.item['value']   #int(self.item['value'])
                else:
                    value = None
                if 'value1' in self.item:
                    value1 = self.item['value1']   #int(self.item['value'])
                else:
                    value1 = None
                if 'value2' in self.item:
                    value2 = self.item['value2']   #int(self.item['value'])
                else:
                    value2 = None

                if 'address' in self.item:
                    self.address = int(self.item['address']) #self.item['address'] #int(self.item['address'])
                else:
                    self.address = None
                    

                if 'type' in self.item:
                    type = self.item['type']
                else:
                    type = None

                if 'interprocess_state' in self.item:
                    interprocess_state = self.item['interprocess_state']
                else:
                    interprocess_state = None


                #########################################

                if type == 'write_register':
                    result = self.modbus_command(self.command_map_read, self.command_map_write, self.command_map_write_register, self.command_map_read_register, self.address, self.item['type'], value, value1, value2)

                if type == 'read_register':
                    result = self.modbus_command(self.command_map_read, self.command_map_write, self.command_map_write_register, self.command_map_read_register, self.address, self.item['type'])


                #########################################

                #modbus_command(command_map, address, value)
                if type == 'read':
                    result = self.modbus_command(self.command_map_read, self.command_map_write, self.command_map_write_register, self.command_map_read_register, self.address, self.item['type'])

                if type == 'write':
                    result = self.modbus_command(self.command_map_read, self.command_map_write, self.command_map_write_register, self.command_map_read_register, self.address, self.item['type'], value, value1, value2)


                #########################################


                #print(Fore.BLUE + Back.YELLOW + f'Result from modbus_queue_handler: ', result, flush=True)

                self.result = result

                if interprocess_state == 'modbus_tempctl':
                    print(Fore.BLUE + Back.YELLOW + f'IS - Result from modbus_queue_handler - result: ', result, flush=True)
                    result = json.dumps(result)
                    self.queue_tempctr.put(result)

                if interprocess_state == 'state_requester':

                    if self.address in range(512, 524):
                        data = {
                        'relais': self.result,
                        'address': self.address,
                        'type': type,
                        'interprocess_state': 'state_requester'
                        }
                        data = json.dumps(data)
                        self.queue_bc.put(data)

                    if self.address in range(524, 529) and self.address in range(544, 545):
                        data = {
                        'heizen': self.result,
                        'address': self.address,
                        'type': type,
                        'interprocess_state': 'state_requester'
                        }
                        data = json.dumps(data)
                        self.queue_bc.put(data)

                    if self.address in range(1, 5):
                        data = {
                        'temperature': 'mantle',#self.result,
                        'address': self.address,
                        'type': type,
                        'temp': self.result,
                        'interprocess_state': 'state_requester'
                        }
                        print(Fore.BLACK + Back.BLUE + f'Modbus temperature data put in queue_bc {data}', flush=True)
                        data = json.dumps(data)
                        self.queue_bc.put(data)

            except Exception:
                pass


    # Load Balancing
    def queue_handler2(self):
        print(Fore.YELLOW + Back.RED + f'Modbus_queue_handler2', flush=True)

        while True:

            time.sleep(0.05)
            try:
                self.item = self.queue_mb.get()
                self.item = json.loads(self.item)

                #if self.item['address'] in range(512, 550):
                #    print("Item from Modbus_queue_handler2: " , self.item, flush=True)

                logging.debug(f"{Fore.RED} Item from Modbus_queue_handler2 self.item: {self.item} {Style.RESET_ALL}" )


                # Extrahieren von address und value aus dem item-Dictionary
                if 'value' in self.item:
                    value = self.item['value']   #int(self.item['value'])
                else:
                    value = None
                if 'value1' in self.item:
                    value1 = self.item['value1']   #int(self.item['value'])
                else:
                    value1 = None
                if 'value2' in self.item:
                    value2 = self.item['value2']   #int(self.item['value'])
                else:
                    value2 = None

                if 'address' in self.item:
                    self.address = int(self.item['address']) #self.item['address'] #int(self.item['address'])
                else:
                    self.address = None
                    

                if 'type' in self.item:
                    type = self.item['type']
                else:
                    type = None

                if 'interprocess_state' in self.item:
                    interprocess_state = self.item['interprocess_state']
                else:
                    interprocess_state = None


                #########################################

                if type == 'write_register':
                    result = self.modbus_command(self.command_map_read, self.command_map_write, self.command_map_write_register, self.command_map_read_register, self.address, self.item['type'], value, value1, value2)

                if type == 'read_register':
                    result = self.modbus_command(self.command_map_read, self.command_map_write, self.command_map_write_register, self.command_map_read_register, self.address, self.item['type'], value, value1, value2)


                #########################################

                #modbus_command(command_map, address, value)
                if type == 'read':
                    result = self.modbus_command(self.command_map_read, self.command_map_write, self.command_map_write_register, self.command_map_read_register, self.address, self.item['type'])

                if type == 'write':
                    result = self.modbus_command(self.command_map_read, self.command_map_write, self.command_map_write_register, self.command_map_read_register, self.address, self.item['type'], value, value1, value2)


                #########################################


                #print(Fore.BLUE + Back.YELLOW + f'Result from modbus_queue_handler2: ', result, flush=True)

                self.result = result

                if interprocess_state == 'modbus_tempctl':
                    print(Fore.BLUE + Back.YELLOW + f'IS - Result from modbus_queue_handler2 - result: ', result, flush=True)
                    result = json.dumps(result)
                    self.queue_tempctr.put(result)

                if interprocess_state == 'state_requester':

                    if self.address in range(512, 524):
                        data = {
                        'relais': self.result,
                        'address': self.address,
                        'type': type,
                        'interprocess_state': 'state_requester'
                        }
                        data = json.dumps(data)
                        self.queue_bc.put(data)

                    if self.address in range(524, 529) and self.address in range(544, 545):
                        data = {
                        'heizen': self.result,
                        'address': self.address,
                        'type': type,
                        'interprocess_state': 'state_requester'
                        }
                        data = json.dumps(data)
                        self.queue_bc.put(data)

                    if self.address in range(1, 5):
                        data = {
                        'temperature': 'mantle',#self.result,
                        'address': self.address,
                        'type': type,
                        'temp': self.result,
                        'interprocess_state': 'state_requester'
                        }
                        print(Fore.BLACK + Back.BLUE + f'Modbus temperature data put in queue_bc {data}', flush=True)
                        data = json.dumps(data)
                        self.queue_bc.put(data)

            except Exception:
                pass



#####################################################

#####################################################



class Observer:
    def __init__(self):
        self.device_data_new = None
        self.temp_new = None

    def update_device_data(self, data):
        self.device_data_new = data
        self.data_changed()

    def update_temp(self, temp):
        self.temp_new = temp
        self.data_changed()

    def data_changed(self):
        if self.device_data_new is not None and self.temp_new is not None:
            print(f'New data: {self.device_data_new}, {self.temp_new}')




class Control:
    def __init__(self, queue_ctr, queue_ctr2, queue_tempctr, queue_tempctr2, queue_io, queue_mb, queue_mb2):
        super().__init__()
        #threading.Thread.__init__(self)

        self.lock = threading.Lock()

        self.queue_ctr = queue_ctr
        self.queue_ctr2 = queue_ctr2
        self.queue_tempctr = queue_tempctr
        self.queue_tempctr2 = queue_tempctr2
        self.queue_io = queue_io
        self.queue_mb = queue_mb
        self.queue_mb2 = queue_mb2

        self.data = None
        self.data2 = None
        self.data3 = None
        self.data4 = None

        self.get = None

        self.device_data = {}
        self.devices = {}

        self.temp_device = None
        self.manteltemp = None
        self.preheatertemp = None
        self.coolingtemp = None

        self.queue_heating_1 = multiprocessing.Queue()
        self.queue_preheating_1 = multiprocessing.Queue()
        self.queue_heating_feed_1 = multiprocessing.Queue()
        self.queue_feed_pump_1 = multiprocessing.Queue()
        self.queue_cooling_pump_1 = multiprocessing.Queue()
        self.queue_gas_valve_1 = multiprocessing.Queue()
        self.queue_reflux_1 = multiprocessing.Queue()

        self.threads = []

        #self.threads = {}
        #self.thread_events = {}
        #self.thread_flags = {}


        #self.stop_thread = {}
        #self.thread_queues = {}
        self.thread_lock = threading.Lock()

        self.thread = None
        self.thread_started = False

        self.num_threads_running = 0
        self.num_threads_started = 0


    def set_heater_power(self, pid_output):
        # -32768 bis 32767
        x = pid_output/100 * 32767
        return x


    def update_temp_1(self, temp_device_address):
        logging.debug('Entering update_temp_1 function')
        print(Fore.BLACK + Back.GREEN + f'update_temp_1 started', flush=True)

        try:

            data = {
                'value': '',
                'address': temp_device_address,
                #'type': 'read',
                'type': 'read_register',
                'interprocess_state': 'modbus_tempctl'
            }


            data = json.dumps(data)
            self.queue_mb.put(data)


        except Exception as e:
            print("Debug: Exception occurred:", type(e).__name__, e, flush=True)
            pass



    def write_to_modbus(self, device_data):
        logging.debug('Entering write_to_modbus function')
        print(Fore.BLACK + Back.GREEN + f'write_to_modbus started', flush=True)

        device_data = device_data.copy()

        try:
            time.sleep(1)

            address = device_data['address']
            heating_temp = device_data['heating_temp']
            temp_device_address = device_data['temp_device_address']


            #print(Fore.WHITE + Back.MAGENTA + f'write_to_modbus device_data: {device_data}', flush=True)

            # Set parameter for the PID
            pid = PID(1, 0.1, 0.05, setpoint = heating_temp)
            pid.output_limits = (0, 100)


            print(Fore.YELLOW + f"Debug: heating_temp - {heating_temp} {address} {temp_device_address} ", flush=True)

            print(Fore.BLACK + Back.GREEN + f'control_tube_heater - Trying to get temperature data from queue_tempctr', flush=True)

            # Call the temperature update function
            self.update_temp_1(temp_device_address)


            #if not self.queue_tempctr.empty():

            #if self.queue_tempctr.empty():
            #    time.sleep(0.5)
            #    if self.queue_tempctr.empty():
            #        self.update_temp_1(temp_device_address)

            while self.queue_tempctr.empty():
                time.sleep(0.5)
                self.update_temp_1(temp_device_address)


            # Recive the current temperature
            while not self.queue_tempctr.empty():
                temperature = json.loads(self.queue_tempctr.get())


            print(Fore.BLACK + Back.GREEN + f'control_tube_heater - temperature: {temperature} ', flush=True)

            print(Fore.YELLOW + f"Debug: pid - {pid}", flush=True)
            print(Fore.YELLOW + f"Debug: pid.setpoint - {pid.setpoint}", flush=True)
            print(Fore.YELLOW + f"Debug: pid.components - {pid.components}", flush=True)

            pid_output = pid(temperature)

            print(Fore.YELLOW + f"Debug: pid_output - {pid_output}", flush=True)


            value = self.set_heater_power(pid_output)

            print(Fore.YELLOW + Back.RED + f'control_tube_heater - device_data: {device_data} ', flush=True)
            print(Fore.BLACK + Back.GREEN + f'temp - heating_temp: {heating_temp} ', flush=True)
            #print(Fore.BLACK + Back.GREEN + f'control_tube_heater - temperature: {temperature} ', flush=True)
            print(Fore.BLACK + Back.GREEN + f'pid_output - pid_output {pid_output} ', flush=True)
            print(Fore.RED + Back.GREEN + f'set_heater_power: {self.set_heater_power(pid_output)} ', flush=True)

            if pid_output > 0:
                data2 = {
                    'value': int(value),
                    'address': address,
                    'type': 'write_register',
                    'interprocess_state': 'modbus_tempctl_set_temp'
                }
                self.queue_mb.put(json.dumps(data2))
            else:
                data3 = {
                    'value': 0,
                    'address': address,
                    'type': 'write_register',
                    'interprocess_state': 'modbus_tempctl_set_temp'
                }
                self.queue_mb.put(json.dumps(data3))

            #for thread in threading.enumerate():
            #    print(thread.name, flush=True)


        except Exception as e:
            print("Debug: Exception occurred in write_to_modbus:", type(e).__name__, e, flush=True)
            pass



    def control_heating_mantle_1(self):
        logging.debug('Entering control_heating_thread function')
        print(Fore.BLACK + Back.GREEN + f'control_heating_thread started', flush=True)

        # Start profiling
        #profiler = cProfile.Profile()
        #profiler.enable()

        device_data = None
        state_value = None

        init_flag = False
        shutdown_flag = False

        while True:

            try:


                if not self.queue_heating_1.empty():
                    while not self.queue_heating_1.empty():
                        device_data = self.queue_heating_1.get()
                        print(Fore.WHITE + Back.MAGENTA + f'control_heating_mantle_1 - if not self.queue_heating_1.empty - device_data: {device_data}', flush=True)
                        #time.sleep(0.1)


                if device_data is not None:

                    state_name = device_data['state_name']
                    address = device_data['address']
                    heating_temp = device_data['heating_temp']
                    temp_device_address = device_data['temp_device_address']
                    state_value = device_data.get("state_value")

                    init_flag = True



                if state_value == 'true' and init_flag == True:

                    self.write_to_modbus(device_data)
                    shutdown_flag = False


                elif state_value == 'false' and shutdown_flag == False:

                    data = {
                        'value': 0,
                        'address': address,
                        'type': 'write_register',
                        'interprocess_state': 'modbus_tempctl_set_temp'
                    }
                    self.queue_mb.put(json.dumps(data))

                    shutdown_flag = True
                    init_flag = False



                #elif state_value == None:
                #    time.sleep(1)
                #    continue


                time.sleep(2)

            except Exception as e:
                print("Debug: Exception occurred in control_heating_mantle_1:", type(e).__name__, e, flush=True)
                pass

            #finally:
            #    profiler.disable()
            #    stats = pstats.Stats(profiler).sort_stats('cumtime')
            #    stats.print_stats()



    def control_pre_heating_mantle_1(self):
        logging.debug('Entering control_preheater function')
        print(Fore.BLACK + Back.GREEN + f'control_preheater started', flush=True)

        init_flag = False
        device_data = None

        while True:

            try:

                while device_data is None:

                    if not self.queue_preheating_1.empty():
                        device_data = self.queue_preheating_1.get()


                #device_data = self.queue_preheating_1.get_nowait()

                if device_data is not None:

                    state_name = device_data['state_name']
                    address = device_data['address']
                    heating_temp = device_data['heating_temp']
                    temp_device_address = device_data['temp_device_address']
                    state_value = device_data.get("state_value")

                    init_flag = True


                time.sleep(2)

            except queue.Empty:
                pass
            except Exception as e:
                print("Debug: Exception occurred:", type(e).__name__, e, flush=True)
                pass



    def control_heating_feed_1(self):
        logging.debug('Entering control_heating_feed_1 function')
        print(Fore.BLACK + Back.GREEN + f'control_heating_feed_1 ', flush=True)

        device_data = None

        while True:

            try:

                while device_data is None:
                    if not self.queue_heating_feed_1.empty():
                        device_data = self.queue_heating_feed_1.get()
                        time.sleep(5)

                if device_data is not None:

                    address = device_data.get("address")
                    heating_temp = device_data("heating_temp")
                    temp_device_address = device_data.get("temp_device_address")

                time.sleep(2)

            except Exception as e:
                print("Debug: Exception occurred:", type(e).__name__, e, flush=True)
                pass



    def control_feed_pump_1(self):
        logging.debug('Entering control_feed_pump_1_thread function')
        print(Fore.BLACK + Back.GREEN + f'control_feed_pump_1_thread ', flush=True)

        current_rate = 1

        device_data = None
        state_value = None

        init_flag = False
        shutdown_flag = False


        while True:

            try:

                if not self.queue_feed_pump_1.empty():
                    while not self.queue_feed_pump_1.empty():
                        device_data = self.queue_feed_pump_1.get()


                if device_data is not None:

                    state_name = device_data['state_name']
                    address = device_data['address']
                    heating_temp = device_data['heating_temp']
                    temp_device_address = device_data['temp_device_address']
                    state_value = device_data.get("state_value")

                    init_flag = True
                    print(Fore.WHITE + Back.MAGENTA + f'control_feed_pump_1 state_value: {state_value} device_data: {device_data}', flush=True)



                if state_value == 'true' and init_flag == True:

                    data = {
                        'value': True,
                        'address': address,
                        'type': 'write'
                    }

                    data = json.dumps(data)
                    self.queue_mb.put(data)

                    time.sleep(current_rate + 1)

                    data = {
                        'value': False,
                        'address': address,
                        'type': 'write'
                    }

                    data = json.dumps(data)
                    self.queue_mb.put(data)


                    print(Fore.BLACK + Back.GREEN + f'control_feed_pump - rate: {current_rate} data: {data}', flush=True)

                    time.sleep(current_rate + 1)
                    shutdown_flag = False



                elif state_value == 'false' and shutdown_flag == False:
                    data = {
                        'value': False,
                        'address': address,
                        'type': 'write'
                    }

                    data = json.dumps(data)
                    self.queue_mb.put(data)

                    shutdown_flag = True
                    init_flag = False


                time.sleep(2)


            except queue.Empty:
                pass
            except Exception as e:
                print("Debug: Exception occurred:", type(e).__name__, e, flush=True)
                pass


    def control_cooling_pump_1(self):
        logging.debug('Entering control_cooling_pump_1_thread function')
        print(Fore.BLACK + Back.GREEN + f'control_cooling_pump_1_thread ', flush=True)

        device_data = None
        state_value = None

        init_flag = False
        init_flag2 = True

        shutdown_flag = False

        while True:
            print(Fore.BLACK + Back.GREEN + f'Debug: into while loop: control_cooling_pump_1_thread ', flush=True)

            try:

                if not self.queue_cooling_pump_1.empty():
                    while not self.queue_cooling_pump_1.empty():
                        device_data = self.queue_cooling_pump_1.get()


                if device_data is not None:

                    address = device_data['address']
                    state_value = device_data.get("state_value")

                    init_flag = True


                    if state_value == 'true':
                        state_value = True
                    if state_value == 'false':
                        state_value = False

                    print(Fore.WHITE + Back.MAGENTA + f'control_cooling_pump_1 state_value: {state_value}', flush=True)


                if state_value == True and init_flag == True and init_flag2 == True:

                    data = {
                        'value': state_value,
                        'address': address,
                        'type': 'write'
                        #'interprocess_state': ''
                    }

                    data = json.dumps(data)
                    self.queue_mb.put(data)

                    print(Fore.WHITE + Back.MAGENTA + f'control_cooling_pump_1 send to queue_mb: device_data: {device_data}, data: {data}', flush=True)

                    shutdown_flag = False
                    init_flag2 = False



                elif state_value == False and shutdown_flag == False:
                    data = {
                        'value': False,
                        'address': address,
                        'type': 'write'
                    }

                    data = json.dumps(data)
                    self.queue_mb.put(data)

                    shutdown_flag = True
                    init_flag = False
                    init_flag2 = True



                time.sleep(2)

            except Exception as e:
                print("Debug: Exception occurred:", type(e).__name__, e, flush=True)
                pass


    def control_gas_valve_1(self):
        logging.debug('Entering control_gas_valve_1_thread function')
        print(Fore.BLACK + Back.GREEN + f'control_gas_valve_1_thread ', flush=True)

        device_data = None
        state_value = None

        init_flag = False
        init_flag2 = True

        shutdown_flag = False

        flow = 2

        while True:

            try:

                if not self.queue_gas_valve_1.empty():
                    while not self.queue_gas_valve_1.empty():
                        device_data = self.queue_gas_valve_1.get()


                if device_data is not None:

                    address = device_data['address']
                    state_value = device_data.get("state_value")

                    flow = device_data.get("flow")

                    init_flag = True


                    if state_value == 'false':
                        state_value = False
                    if state_value == 'true':
                        state_value = True


                if state_value == True and init_flag == True and init_flag2 == True:
                        data = {
                            'value': state_value,
                            'address': address,
                            'type': 'write'
                            #'interprocess_state': ''
                        }

                        data = json.dumps(data)
                        self.queue_mb.put(data)

                        shutdown_flag = False
                        init_flag2 = False

                        print(Fore.WHITE + Back.MAGENTA + f'control_gas_valve_1 send to queue_mb: device_data: {device_data}, data: {data}', flush=True)



                elif state_value == False and shutdown_flag == False:
                    data = {
                        'value': False,
                        'address': address,
                        'type': 'write'
                    }

                    data = json.dumps(data)
                    self.queue_mb.put(data)

                    shutdown_flag = True
                    init_flag = False
                    init_flag2 = True


                time.sleep(2)

            except Exception as e:
                print("Debug: Exception occurred:", type(e).__name__, e, flush=True)
                pass


    def control_reflux_1(self):
        logging.debug('Entering control_reflux_1_thread function')
        print(Fore.BLACK + Back.GREEN + f'control_reflux_1_thread ', flush=True)

        device_data = None
        previous_state_value = None
        reflux_rate = 100

        while True:

            try:

                time.sleep(2)

                while device_data is None:

                    if not self.queue_reflux_1.empty():
                        device_data = self.queue_reflux_1.get()
                        time.sleep(5)


                if device_data is not None:

                    address = device_data.get("address")
                    #reflux_rate = device_data.get("reflux_rate")


            except Exception as e:
                print("Debug: Exception occurred:", type(e).__name__, e, flush=True)
                pass


    def control_pressure_1(self):
        logging.debug('Entering control_pressure_1_thread function')
        print(Fore.BLACK + Back.GREEN + f'control_pressure_1_thread ', flush=True)

        previous_state_value = None
        device_data = None

        while True:

            try:

                time.sleep(2)

                while device_data is None:

                    if not self.control_pressure_1.empty():
                        device_data = self.control_pressure_1.get()
                        time.sleep(5)


                if device_data is not None:

                    address = device_data.get("address")



            except Exception as e:
                print("Debug: Exception occurred:", type(e).__name__, e, flush=True)
                pass



    def queue_handler(self):
        logging.debug('Entering Control_queue_handler function')
        print(Fore.YELLOW + Back.RED + f'Control_queue_handler', flush=True)

        previous_state_values = {}

        while True:
            #print(f"Debug: Queue size: {self.queue_ctr.qsize()}")
            try:
                #time.sleep(0.0001)
                #print(Fore.WHITE + Back.MAGENTA + f'control_queue_handler: Inside while loop', flush=True)

                self.item = json.loads(self.queue_ctr.get())
                self.device_data = self.item.copy()

                #print(Fore.WHITE + Back.BLUE + f'control_queue_handler self.item: {self.item}', flush=True)
                #print(Fore.WHITE + Back.MAGENTA + f'control_queue_handler self.item: {self.device_data["state_value"]}', flush=True)


                state_name = self.device_data['state_name']
                state_value = self.device_data['state_value']

                if state_value == "true" or state_value is True:
                    state_value = True
                elif state_value == "false" or state_value is False:
                    state_value = False
                else:
                    print("state_value not defined for", state_name, flush=True)
                    continue


                # If state_name is not in previous_state_values or the state_value has changed
                #if state_name not in previous_state_values or previous_state_values[state_name] != state_value:
                #    self.start_stop_thread(state_name, state_value, self.device_data['address'], self.device_data['heating_temp'], self.device_data['temp_device_address'])
                #    previous_state_values[state_name] = state_value  # Update the previous state value



                #if self.device_data['state_value'] == "true" or self.device_data['state_value'] is True:
                #    self.start_stop_thread(self.device_data['state_name'], True, self.device_data['address'], self.device_data['heating_temp'], self.device_data['temp_device_address'])

                #elif self.device_data['state_value'] == "false" or self.device_data['state_value'] is False:
                #    self.start_stop_thread(self.device_data['state_name'], False, self.device_data['address'], self.device_data['heating_temp'], self.device_data['temp_device_address'])

                #else:
                #    print("state_value not define for", self.device_data['state_name'], flush=True)


            ##################################################################################

                #self.device_data = {
                #    "device_id": self.item.get("device_id", None),
                #    "device_type": self.item.get("device_type", None),
                #    "device_name": self.item.get("device_name", None),
                #    "device_address_name": self.item.get("device_address_name", None),
                #    "address": self.item.get("address", None),
                #    "state_name": self.item.get("state_name", None),
                #    "state_value": self.item.get("state_value", None),
                #    "heating_temp": self.item.get("heating_temp", None),
                #    "cooling_temp": self.item.get("cooling_temp", None),
                #    "temp_device_id": self.item.get("temp_device_id", None),
                #    "temp_device_address": self.item.get("temp_device_address", None),
                #    "flow": self.item.get("flow", None),
                #    "rate": self.item.get("rate", None),
                #    "interprocess_state": self.item.get("interprocess_state", None)
                #}

            ##################################################################################


            except Exception as e:
                print("Exception in control_queue_handler:", e)
                pass



    def queue_handler2(self):
        logging.debug('Entering Controll queue_handler2 function')
        print(Fore.YELLOW + Back.RED + f'Control_queue_handler2', flush=True)

        # All registered running threads, default = false
        thread_register = defaultdict(bool)

        while True:
            #print(f"Debug: Queue size: {self.queue_ctr.qsize()}")
            try:
                time.sleep(0.001)


                self.item = json.loads(self.queue_ctr2.get())
                self.device_data = self.item.copy()


                if self.device_data['interprocess_state'] == 'thread_register':
                    thread_register[self.device_data['state_name']] = self.device_data['status']


                print(Fore.BLACK + Back.GREEN + f'control_queue_handler2 self.device_data ', self.device_data, flush=True)


                # the state name ist unique, so state data are easy assigned
                if self.device_data['state_name'] == "heating_mantle_1":
                    #if self.device_data['state_value'] == "true":
                    print(Fore.WHITE + Back.MAGENTA + f'control_queue_handler2 self.item: {self.device_data}', flush=True)
                    self.queue_heating_1.put(self.device_data)

                if self.device_data["state_name"] == "pre_heating_mantle_1":
                    #if self.device_data["state_value"] == "true":
                    self.queue_preheating_1.put(self.device_data)

                if self.device_data["state_name"] == "heating_feed_1":
                    #if self.device_data["state_value"] == "true":
                    self.queue_heating_feed_1.put(self.device_data)

                if self.device_data["state_name"] == "gas_valve_1":
                    #if self.device_data["state_value"] == "true":
                    self.queue_gas_valve_1.put(self.device_data)

                if self.device_data["state_name"] == "feed_pump_1":
                    #if self.device_data["state_value"] == "true":
                    self.queue_feed_pump_1.put(self.device_data)

                if self.device_data["state_name"] == "cooling_pump_1":
                    #if self.device_data["state_value"] == "true":
                    self.queue_cooling_pump_1.put(self.device_data)

                #if self.device_data["state_name"] == "reflux_1":
                #    if thread_register[self.device_data["state_name"]]:
                #    #if self.device_data["state_value"] == "true":
                #        self.queue_reflux_1.put(self.device_data)


            except Exception as e:
                print("Exception in control_queue_handler2:", e)
                pass



    def start_threads(self):
        logging.debug('Entering start_threads function')
        print(Fore.BLACK + Back.GREEN + 'Entering start_threads function ', flush=True)


        #profiler = cProfile.Profile()
        #profiler.enable()

        time.sleep(1.0)

        try:



            thread_1 = threading.Thread(target=self.control_heating_mantle_1, args=())
            thread_2 = threading.Thread(target=self.control_feed_pump_1, args=())
            thread_3 = threading.Thread(target=self.control_cooling_pump_1, args=())
            thread_4 = threading.Thread(target=self.control_gas_valve_1, args=())


            thread_1.start()
            thread_2.start()
            thread_3.start()
            thread_4.start()


            #data = {
            #    "request": "all"
            #}
            #time.sleep(2)
            #self.queue_io.put(json.dumps(data))
            #print(Fore.WHITE + Back.MAGENTA + 'init request: all', flush=True)



        except Exception as e:
            print(Fore.RED + Back.YELLOW + "Error in start_threads: " + str(e), flush=True)
            pass

            #finally:
            #    profiler.disable()
            #    stats = pstats.Stats(profiler).sort_stats('cumtime')
            #    stats.print_stats()





#####################################################

#####################################################


class ProcessMonitor:
    def __init__(self, queue_monitor, queue_bc, IO_p, IO_p2, address_handler_p, my_sql_p, my_sql_p2, modbus_p, modbus_p2, ctrl_p, ctrl_p2, ctrl_p3):
        self.processes = {}
        self.queue_monitor = queue_monitor
        self.queue_bc = queue_bc

        self.IO_p = IO_p
        self.IO_p2 = IO_p2
        self.address_handler_p = address_handler_p
        self.my_sql_p = my_sql_p
        self.my_sql_p2 = my_sql_p2
        self.modbus_p = modbus_p
        self.modbus_p2 = modbus_p2
        self.ctrl_p = ctrl_p
        self.ctrl_p2 = ctrl_p2
		
        self.process_list = [IO_p, my_sql_p, modbus_p, modbus_p2, ctrl_p]

        self.process_names = {}

        for process in self.process_list:
            ps_process = psutil.Process(process.pid)
            self.process_names[process.pid] = ps_process.name()

        self.stop_monitoring = False


    def add_process(self, name, process):
        self.processes[name] = {
            "pid": process.pid,
            "name": name,
            "start_time": time.time()
        }


    def monitor_cpu_usage(self):
        while not self.stop_monitoring:
            for process_name, process_info in self.processes.items():
                ps_process = psutil.Process(process_info["pid"])
                cpu_percent = ps_process.cpu_percent(interval=1)
                print("CPU usage of process '{}' with PID {}: {}%".format(process_info["name"], process_info["pid"], cpu_percent))

                process_data = {
                    "process_data": "",
                    "name": (process_info["name"]),
                    "pid": (process_info["pid"]),
                    "cpu_usage": format(cpu_percent)
                }
                print(Fore.WHITE + Back.MAGENTA + f'process_data: ' + json.dumps(process_data), flush=True)
                self.queue_bc.put(json.dumps(process_data))


    def stop_monitoring(self):
        self.stop_monitoring = True


    def queue_handler(self):
        logging.debug('Entering ProcessMonitor queue_handler function')
        print(Fore.BLACK + Back.GREEN + 'Entering ProcessMonitor queue_handler function ', flush=True)

        while True:
            time.sleep(5)
            self.monitor_cpu_usage()
            all_processes_terminated = True
            process_data = {}

            for name, process_info in self.processes.items():
                pid = process_info["pid"]
                start_time = process_info["start_time"]

                try:
                    ps_process = psutil.Process(pid)

                    if time.time() - start_time < 60:  # Check if a process is not older then 60 sec.
                        all_processes_terminated = False
                        cpu_percent = ps_process.cpu_percent(interval=1)

                    process_data[process_info["name"]] = {
                        "pid": pid,
                        "cpu_usage": cpu_percent
                    }

                except psutil.NoSuchProcess:
                    pass


            #print(Fore.WHITE + Back.MAGENTA + f'process_data: ' + process_data, flush=True)
            #self.queue_bc.put(json.dumps({"process_data": process_data}))


            if all_processes_terminated:
                break



#####################################################

#####################################################

"""
@contextmanager
def locked(lock):
    lock.acquire()
    try:
        yield
    finally:
        lock.release()
"""

#####################################################

#####################################################


def initialization():
    print("initi()")
    time.sleep(0.1)
    #({"heizen": "on", "address": "524", "temp": '522'}));

    #while True:
        #print("test()")
        #time.sleep(1)
	    #SimpleEcho.broadcast("123")
        #for ws in wss:
        #    ws.sendMessage("test123")


#####################################################

#####################################################



def main():

    logging.basicConfig()

    # Manager für gemeinsam genutzten Speicher erstellen
    # manager = multiprocessing.Manager()

    # create the shared mutex lock
    lock_io = multiprocessing.Lock()

    #lock_db = multiprocessing.RLock()
    lock_db = multiprocessing.Lock()

    lock_db1 = multiprocessing.Lock()
    lock_db2 = multiprocessing.Lock()
    lock_db3 = multiprocessing.Lock()
    lock_db4 = multiprocessing.Lock()
    lock_db5 = multiprocessing.Lock()

    lock_mb = multiprocessing.Lock()

    lock_ctr = multiprocessing.Lock()

    # Define process list here
    processes = []

    # Define threads list here
    threads = []

    # Generate ws clients list
    global wss
    wss = []

    # Generate Queue
    queue_ws = Queue()

    queue_io = Queue()
    queue_io2 = Queue()
    queue_io3 = Queue()
    queue_io4 = Queue()

    queue_ah = Queue()
    queue_ah2 = Queue()

    queue_db = Queue()
    queue_db2 = Queue()
    queue_db_read = Queue()
    queue_db_write = Queue()

    queue_mb = Queue()
    queue_mb2 = Queue()

    queue_bc = Queue()
    queue_bc2 = Queue()

    queue_ctr = Queue()
    queue_ctr2 = Queue()
    queue_tempctr = Queue()
    queue_tempctr2 = Queue()
    queue_tempctr3 = Queue()

    queue_monitor = Queue()



    # check the size of the queue
    size = queue_ws.qsize()
    print("queue_ws size: ", size)

    #Create Modbus Client Connection to Modbus Server - Important, client is not the same as clients!
    with ModbusClient(host=HOST, port=PORT) as client:
        client.connect()
        #time.sleep(0.01)


        # Precess IO Handler
        IO = IO_Handler(lock_io, queue_io, queue_io2, queue_io3, queue_io4, queue_ws, queue_db, queue_mb, queue_mb2, queue_bc, queue_tempctr, queue_ctr, queue_ctr2, queue_ah)
        IO_p = Process(target=IO.queue_handler) #, args=[wss])
        IO_p2 = Process(target=IO.queue_handler2) #, args=[wss])
        IO_p.start()
        IO_p2.start()


        # Address Handler
        address_handler = AddressHandler(queue_ah, queue_ah2, queue_db, queue_io, queue_mb, queue_tempctr)
        address_handler_p = Process(target=address_handler.queue_handler)
        address_handler_p.start()


        # Precess MySQL Database
        my_sql = MySQLDatabase(lock_db, lock_db1, lock_db2, lock_db3, lock_db4, queue_db, queue_db2, queue_db_read, queue_db_write, queue_io, queue_io2, queue_bc, queue_tempctr2, queue_ah)
        my_sql_p = Process(target=my_sql.queue_handler)
        my_sql_p2 = Process(target=my_sql.queue_handler2)
        my_sql_p.start()
        my_sql_p2.start()


        # Precess Modbus
        modbus = Modbus(client, lock_mb, queue_bc, queue_mb, queue_mb2, queue_io, queue_tempctr)
        modbus_p = Process(target=modbus.queue_handler) #, args=(queue_mb, ))
        modbus_p2 = Process(target=modbus.queue_handler2) #, args=(queue_mb, ))
        modbus_p.start()
        modbus_p2.start()


        # Control
        ctrl = Control(queue_ctr, queue_ctr2, queue_tempctr, queue_tempctr2, queue_io, queue_mb, queue_mb2)
        ctrl_p = Process(target=ctrl.queue_handler)
        ctrl_p2 = Process(target=ctrl.queue_handler2)
        ctrl_p3 = Process(target=ctrl.start_threads)
        ctrl_p.start()
        ctrl_p2.start()
        ctrl_p3.start()


        # Process Monitor
        process_monitor = ProcessMonitor(queue_monitor, queue_bc, IO_p, IO_p2, address_handler_p, my_sql_p, my_sql_p2, modbus_p, modbus_p2, ctrl_p, ctrl_p2, ctrl_p3)
        #process_monitor_p = multiprocessing.Process(target=process_monitor.queue_handler, args=(IO_p.pid, my_sql_p.pid, modbus_p.pid, modbus_p2.pid, ctrl_p.pid,))
        #
        process_monitor.add_process("Process1", IO_p)
        process_monitor.add_process("Process2", IO_p2)
        process_monitor.add_process("Process3", address_handler_p)
        process_monitor.add_process("Process4", my_sql_p)
        process_monitor.add_process("Process5", my_sql_p2)
        process_monitor.add_process("Process6", modbus_p)
        process_monitor.add_process("Process7", modbus_p2)
        process_monitor.add_process("Process8", ctrl_p)
        process_monitor.add_process("Process9", ctrl_p2)
        process_monitor.add_process("Process10", ctrl_p3)
        #
        #
        process_monitor_p = multiprocessing.Process(target=process_monitor.queue_handler)
        process_monitor_p.start()


        # Broadcaster
        #broadcast = SimpleEcho(None, None, None, wss, None, None, queue_bc)
        #t_broadcast_p = threading.Thread(target=broadcast.broadcast)
        #t_broadcast_p.start()


        #processes = [IO_p, IO_p2, address_handler_p, my_sql_p, my_sql_p2, modbus_p, modbus_p2, ctrl_p, ctrl_p2]

        # Start all processes
        #for process in processes:
        #    process.start()

        children = active_children()
        print(f'Active Children: {len(children)}')

        for child in children:
            print(child)


        #initialization()
        #t1 = threading.Thread(target=initialization)
        #t1.start()


        print(f"Websocket server on port %s" % PORTNUM)
        #server = SimpleWebSocketServer('', PORTNUM, SimpleChat, queue_ws=queue_ws)
        server = SimpleWebSocketServer('0.0.0.0', PORTNUM, partial(SimpleEcho, wss=wss, queue_io=queue_io, queue_ws=queue_ws, queue_bc=queue_bc))


        try:
            server.serveforever()
            #initialization()
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
            IO_p.terminate()
            IO_p2.terminate()
            address_handler_p.terminate()
            my_sql_p.terminate()
            my_sql_p2.terminate()
            modbus_p.terminate()
            modbus_p2.terminate()
            ctrl_p.terminate()
            ctrl_p2.terminate()
            ctrl_p3.terminate()
            process_monitor_p.terminate()

            # Terminate all processes
            #for process in processes:
            #    process.terminate()

        finally:
            server.close()

            # Wait for all processes to finish
            #for process in processes:
            #    process.join()

            for child in children:
                child.join()

            # This entry is still redundant, a unification of the thread joinings should be considered
            for t in threads:
                t.join()
                for thread in threading.enumerate():
                    print(thread.name)


if __name__ == "__main__":
    main()


