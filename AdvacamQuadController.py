import pypixet
import dearpygui.dearpygui as dpg
import os
import time
import datetime

from enum import Enum
import threading

TIMEOUT = 5 # in seconds

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 300

logTxt = ""
pixet = -1
devices = -1

def log(new_line):
    global logTxt
    time = datetime.datetime.now()
    logTxt = "[" + time.strftime("%H:%M:%S") + "]: " + new_line + "\n" + logTxt
    dpg.set_value("logText",logTxt)

class State(Enum):
    PXCORE_INIT = 0
    CONFIG_LOAD = 1
    READY = 2
    ACQ_RUNNING = 3
    NO_CONFIGS = 4
    NO_DEVICES = 5
    NO_MASTER = 6

    def get_color(state):
        if(state == State.READY):
            return [0, 153, 0]
        elif(state == State.ACQ_RUNNING):
            return [0, 153, 0]
        elif(state == State.CONFIG_LOAD):
            return [255, 255, 0]
        elif(state == State.PXCORE_INIT):
            return [255, 255, 0]
        elif(state == State.NO_CONFIGS):
            return [255, 0, 0]
        elif(state == State.NO_DEVICES):
            return [255, 0, 0]
        elif(state == State.NO_MASTER):
            return [255, 0, 0]

    def get_text(state):
        if(state == State.READY):
            return "Ready"
        elif(state == State.ACQ_RUNNING):
            return "Acquisition in progress..."
        elif(state == State.CONFIG_LOAD):
            return "Loading configs..."
        elif(state == State.PXCORE_INIT):
            return "Initializing Pixet core... (might take a few minutes)"
        elif(state == State.NO_CONFIGS):
            return "Configs not found, load them manually in Pixet."
        elif(state == State.NO_DEVICES):
            return "Devices not found, connect devices and restart this app."    
        elif(state == State.NO_MASTER):
            return "No master device found, check the sync cable connection."  

def disable_input():
    dpg.configure_item("btnStartAcq", enabled=False)
    dpg.configure_item("btnDirBrowse", enabled=False)
    dpg.configure_item("inFileName", enabled=False)
    dpg.configure_item("inAcqTime", enabled=False)
    dpg.configure_item("inBlockSize", enabled=False)
    dpg.configure_item("inBufferSize", enabled=False)

def enable_input():
    dpg.configure_item("btnStartAcq", enabled=True)
    dpg.configure_item("btnDirBrowse", enabled=True)
    dpg.configure_item("inFileName", enabled=True)
    dpg.configure_item("inAcqTime", enabled=True)
    dpg.configure_item("inBlockSize", enabled=True)
    dpg.configure_item("inBufferSize", enabled=True)

def find_master_dev():
    global devices

    for dev in devices:
        pars = dev.parameters()
        if pars.get("IsMaster").getString() == "Yes":
            return dev
    return -1
def thread_start_acquisition():
    th = threading.Thread(target=start_acquisition)
    th.start()

def start_acquisition():
    global pixet, devices
    set_status(State.ACQ_RUNNING)
    dpg.configure_item("btnStopAcq", enabled=True)
    dpg.configure_item("btnStartAcq", enabled=False)

    masterDev = find_master_dev()
    if(masterDev == -1):
        set_status(State.NO_MASTER)
        return

    # running threads
    ths = []
    thsDevName = []
    log("--------------------------")

    if len(devices)>0:
        for dev in devices:
            if dev != masterDev:
                # start a thread and init and start acquisition on waiting devices 
                thread = threading.Thread(target=startSlave, args=(dev, dpg.get_value("inBlockSize"), dpg.get_value("inBufferSize"), dpg.get_value("inAcqTime"), dpg.get_value("txtCurrDir"), dpg.get_value("inFileName"),))
                ths.append(thread)
                thsDevName.append(dev.fullName())
                thread.start()

        # start all acqusitions
        startMaster(masterDev, dpg.get_value("inBlockSize"), dpg.get_value("inBufferSize"), dpg.get_value("inAcqTime"), dpg.get_value("txtCurrDir"), dpg.get_value("inFileName"),)
        for i in range(len(ths)):
            thread = ths[i]
            thread.join(TIMEOUT)

            if thread.is_alive():
                log("Thread " + str(i) + " with device " + thsDevName[i] + " timed out.")

        set_status(State.READY)
        dpg.configure_item("btnStopAcq", enabled=False)
        dpg.configure_item("btnStartAcq", enabled=True)
    else:
        set_status(State.NO_DEVICES)
        log("Acquisition not started.")   
    

def stop_acquisition():
    threads = []
    for dev in devices:
        threads.append(threading.Thread(target=dev.abortOperation))
        
    for th in threads:
        th.start()

    for th in threads:
        th.join()
    
    set_status(State.READY)
    dpg.configure_item("btnStartAcq", enabled=True)

def set_status(state):
    if(state == State.READY):
        enable_input()
    else:
        disable_input()

    dpg.set_value("txtStatus", State.get_text(state))
    dpg.configure_item("txtStatus", color=State.get_color(state))

def set_disable_theme():
    with dpg.theme() as disabled_theme:
        with dpg.theme_component(dpg.mvButton, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Button, [128, 128, 128])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [128, 128, 128])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [128, 128, 128])  
        with dpg.theme_component(dpg.mvInputInt, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Button, [128, 128, 128])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [128, 128, 128])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [128, 128, 128])          
        dpg.bind_theme(disabled_theme)

def set_directory(sender, app_data):
    dpg.set_value("txtCurrDir", app_data['file_path_name'])

def setup_GUI_items():
    with dpg.window(tag="Primary Window", no_resize=True):

        with dpg.group(tag="filepathRow", horizontal=True):
            #txtSaveFile = dpg.add_text("Save directory:")
            fdBlockSize = dpg.add_file_dialog(width=WINDOW_WIDTH-50, height=WINDOW_HEIGHT-50,directory_selector=True, show=False, tag="fileDialog", callback=set_directory)
            btnBrowse = dpg.add_button(tag="btnDirBrowse", label="Select save directory", callback=lambda: dpg.show_item("fileDialog"))
            txtCurrDir = dpg.add_text(os.getcwd(), tag="txtCurrDir", wrap=WINDOW_WIDTH-200)

        with dpg.group(tag="filenameRow", horizontal=True):
            txtFileName = dpg.add_text("File name:")
            inFileName = dpg.add_input_text(tag="inFileName", default_value="test", width=100)
       
        with dpg.group(tag="acqtimeRow", horizontal=True):
            txtAcqTime = dpg.add_text("Acq. time (s):")
            inAcqTime = dpg.add_input_double(default_value=1, width=80, tag="inAcqTime", step=0, format="%.5f", min_value=0, min_clamped=True)
                        
        with dpg.group(tag="blockSizeRow", horizontal=True):
            txtBlockSize = dpg.add_text("Block Size (MB):")
            inBlockSize = dpg.add_input_int(default_value=15, width=100, tag="inBlockSize", step=5, min_value=1, min_clamped=True)
        
        with dpg.group(tag="bufferSizeRow", horizontal=True):
            txtBufferSize = dpg.add_text("Buffer Size (MB):")
            inBufferSize = dpg.add_input_int(default_value=600, width=100, tag="inBufferSize", step=100, min_value=1, min_clamped=True)

        with dpg.group(tag="btnRow", horizontal=True):
            btnStartAcq = dpg.add_button(width=100, tag="btnStartAcq", label="Start", callback=thread_start_acquisition)
            btnStopAcq = dpg.add_button(width=100, tag="btnStopAcq", label="Stop", enabled=False, callback=stop_acquisition)
        
        with dpg.group(tag="footer", horizontal=True):
            dpg.add_text("Status: ")
            dpg.add_text(tag="txtStatus")
            set_status(State.READY)
        
        with dpg.group(tag="log"):
            dpg.add_text("", tag="logText", wrap = WINDOW_WIDTH-20 )
   

    dpg.create_viewport(title='Advacam Quads Controller', width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

    dpg.setup_dearpygui()


def startSlave(dev, blockSize, bufferSize, acqTime, oFileDir, oFileName):
    log("Setting up slave device " + dev.fullName())
    log("   dev.setOperationMode" + str(dev.setOperationMode(pixet.PX_TPX3_OPM_TOATOT)))
    pars = dev.parameters()

    rc = pars.get("DDBuffSize").setU32(bufferSize)
    log("   DDBuffSize .setU32" + str(rc))
    rc = pars.get("DDBlockSize").setU32(blockSize)
    log("   DDBlockSize .setU32 " + str(rc))

    rc = pars.get("TrgStg").setByte(3)
    rc = pars.get("TrgMulti").setBOOL(False)
    rc = pars.get("TrgT0SyncReset").setBOOL(False)
    rc = pars.get("TrgTimestamp").setBOOL(False)
    rc = pars.get("TrgReady").setBOOL(True)
    rc = pars.get("TrgCmos").setBOOL(False)

    log("Starting acquisition on device " + dev.fullName())
    rc = dev.doAdvancedAcquisition(1, acqTime, pixet.PX_ACQTYPE_DATADRIVEN, pixet.PX_ACQMODE_TRG_HWSTARTSTOP, pixet.PX_FTYPE_TPX3_PIXELS_ASCII, 0, oFileDir + "/" + oFileName + "_" + dev.deviceID() + ".t3pa")
    log("Acquisition finished on device " + dev.fullName())
# dev startSlave(dev):

def startMaster(dev, blockSize, bufferSize, acqTime, oFileDir, oFileName):
    log("Setting up master device " + dev.fullName())
    log("dev.setOperationMode " + str(dev.setOperationMode(pixet.PX_TPX3_OPM_TOATOT)))
    pars = dev.parameters()

    rc = pars.get("DDBuffSize").setU32(bufferSize)
    log("     DDBuffSize .setU32 " + str(rc))
    rc = pars.get("DDBlockSize").setU32(blockSize)
    log("     DDBlockSize .setU32 " + str(rc))

    rc = pars.get("TrgStg").setByte(3)
    rc = pars.get("TrgMulti").setBOOL(False)
    rc = pars.get("TrgT0SyncReset").setBOOL(False)
    rc = pars.get("TrgTimestamp").setBOOL(False)
    rc = pars.get("TrgReady").setBOOL(True)
    rc = pars.get("TrgCmos").setBOOL(False)

    log("Starting acquisition on device " + dev.fullName())
    rc = dev.doAdvancedAcquisition(1, acqTime, pixet.PX_ACQTYPE_DATADRIVEN, pixet.PX_ACQMODE_TRG_NO, pixet.PX_FTYPE_TPX3_PIXELS_ASCII, 0, oFileDir + "/" + oFileName + "_" + dev.deviceID() + ".t3pa")
    log("Acquisition finished on device " + dev.fullName())
# dev startMaster(dev):

def init_pxcore():
    global pixet, devices
    set_status(State.PXCORE_INIT)
    # start the pypixet and the Pixet core
    time.sleep(0.5)
    log("pixet core init...")
    pypixet.start()
    pixet=pypixet.pixet
    devices = pixet.devices()
    set_status(State.READY)

def load_configs(thInit):
    global pixet, devices
    #wait for pixet core init
    thInit.join()
    set_status(State.CONFIG_LOAD)

    if len(devices)>0:
        log("Devices list (idx, device name, chips count, [chips list], material:")
        for n in range(len(devices)):
            dev = devices[n]
            log(str(n) + ": " + str(dev.fullName()) + ", " + str(dev.chipCount()) + ", " +  str(dev.chipIDs()) + ", " +  str(dev.sensorType(0)))

        if devices[0].fullName()=="FileDevice 0":
            set_status(State.NO_DEVICES)
            log("No devices connected")
        else:
            for dev in devices:
                # If the device not configured (has HW defaults), try to configure
                rc = dev.hasDefaultConfig()
                if rc==1: # the config XML was not automatically loaded from the configs directory
                    log("No default config loaded")
                    rc = dev.loadConfigFromDevice()
                    log("dev.loadConfigFromDevice")
                    if rc!=0:
                        rc = dev.loadFactoryConfig()
                        log("dev.loadFactoryConfig")
                        if rc!=0:
                            set_status(State.NO_CONFIGS)
                            log("Warning: Device may not be properly configurated")
                else:
                    set_status(State.READY)
                    log("XML config file from 'configs' directory was used")
    else:
        set_status(State.NO_DEVICES)
        log("No devices connected")  

def destroy_pixet():    
    print("------------------------------------------------------------")
    # end the Pixet core and the pypixet
    print("pixet.exitPixet...")       
    print(pixet.exitPixet(), "(0 is OK)") # exit Pixet, stop devices and save configs
    print("pypixet.exit...")
    print(pypixet.exit(), "(0 is OK)")
    print("complete")

def GUI():
    dpg.create_context()
    set_disable_theme()
    setup_GUI_items()
    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)

    thInit = threading.Thread(target=init_pxcore)
    thInit.start()
    
    thConfig = threading.Thread(target=load_configs, args=(thInit,))
    thConfig.start()

    #render loop   
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
        

    dpg.destroy_context()
    destroy_pixet()


GUI()
exit()
