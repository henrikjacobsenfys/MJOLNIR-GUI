try:
    import IPython
    shell = IPython.get_ipython()
    shell.enable_matplotlib(gui='qt')
except:
    pass


from MJOLNIR import _tools # Useful tools useful across MJOLNIR
import _tools as _guitools
import numpy as np
import matplotlib.pyplot as plt
import sys
import datetime
from time import sleep

from os import path
import os

import qtmodern.styles
import qtmodern.windows

plt.ion()
from PyQt5 import QtWidgets, QtCore, QtGui, Qt
try:
    #from MJOLNIR_GUI_ui import Ui_MainWindow  
    from Views.main import Ui_MainWindow
    from Views.DataSetManager import DataSetManager
    from Views.View3DManager import View3DManager
    from Views.QELineManager import QELineManager
    from Views.QPlaneManager import QPlaneManager
    from Views.Cut1DManager import Cut1DManager
    from Views.Raw1DManager import Raw1DManager
    from Views.collapsibleBox import CollapsibleBox
    from MJOLNIR_Data import GuiDataFile,GuiDataSet
    from DataModels import DataSetModel,DataFileModel
    from StateMachine import StateMachine
    from GuiStates import empty,partial,raw,converted
    from AboutDialog import AboutDialog
    from HelpDialog import HelpDialog
    from generateScripts import initGenerateScript,setupGenerateScript
    from _tools import loadSetting,updateSetting,ProgressBarDecoratorArguments
except ModuleNotFoundError:
    sys.path.append('.')
    
    #from .MJOLNIR_GUI_ui import Ui_MainWindow  
    from .Views.main import Ui_MainWindow
    from .Views.DataSetManager import DataSetManager
    from .Views.View3DManager import View3DManager
    from .Views.QELineManager import QELineManager
    from .Views.QPlaneManager import QPlaneManager
    from .Views.Cut1DManager import Cut1DManager
    from .Views.Raw1DManager import Raw1DManager
    from .Views.Raw1DManager import Raw1DManager
    from .Views.collapsibleBox import CollapsibleBox
    from .MJOLNIR_Data import GuiDataFile,GuiDataSet
    from .DataModels import DataSetModel,DataFileModel
    from .StateMachine import StateMachine
    from .GuiStates import empty,partial,raw,converted
    from .AboutDialog import AboutDialog
    from .HelpDialog import HelpDialog
    from .generateScripts import initGenerateScript,setupGenerateScript
    from ._tools import loadSetting,updateSetting,ProgressBarDecoratorArguments

import sys


from pathlib import Path
home = str(Path.home())


####

# Naming convention: WhereInGui_description_type
# Append _function if it is a function
# E.g.: View3D_plot_button and View3D_plot_button_function

#Headlines so far are:
#DataSet, View3D, QELine, QPlane, Cut1D, Raw1D

###### generate allowed themes from qtmodern

from qtmodern import styles
styleNames = [att for att in dir(styles) if (hasattr(getattr(styles,att),'__call__') and att[0]!='_') and not att in ['QColor','QStyleFactory','QPalette'] ]
themes = {}
for name in styleNames:
    themes[name] = getattr(styles,name)

class MJOLNIRMainWindow(QtWidgets.QMainWindow):

    def __init__(self,AppContext):

        super(MJOLNIRMainWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.AppContext = AppContext

        ### Settings saved in .MJOLNIRGuiSettings
        self.settingsFile = path.join(home,'.MJOLNIRGuiSettings')
        self.views = []
        guiSettings = loadSetting(self.settingsFile,'guiSettings')
        
        
        if guiSettings is None:
            self.theme = 'light'
        else:
            if not 'theme' in guiSettings:
                self.theme = 'light'
            else:
                self.theme = guiSettings['theme']
                

        
        self.ui.setupUi(self)
        self.update()

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(self.AppContext.get_resource('Icons/Own/MJOLNIR.png')))
        self.setWindowIcon(icon)

        # List to hold all views that need to be setup
        self.views = []
        ## Set up DataSetManager
        self.ui.dataSetManager = DataSetManager(self.ui.fixedOpen,self)
        self.update()
        self.views.append(self.ui.dataSetManager)

        # Lists of views in shown order
        self.nameList = ['View3D','QE line','Q plane','1D cuts','1D raw data']
        self.viewClasses = [View3DManager,QELineManager,QPlaneManager,Cut1DManager,Raw1DManager]#[View3D,View3D,View3D,Cut1D,Raw1D]
        self.startState = [True,False,False,False,True] # If not collapsed

        # Find correct layout to insert views
        vlay = QtWidgets.QVBoxLayout(self.ui.collapsibleContainer)
        # Insert all views
        for name,Type,state in zip(self.nameList,self.viewClasses,self.startState):
            self.update()
            box = CollapsibleBox(name,startState=state)
            vlay.addWidget(box)
            lay = QtWidgets.QVBoxLayout()

            widget = Type(guiWindow=self)
            self.views.append(widget)
            lay.addWidget(widget)
           
            box.setContentLayout(lay)
        vlay.addStretch()

        self.windows = [] # Holder for generated plotting windows

        self.dataSets = []

        self.current_timer = None
        
        self.blockItems = [getattr(self.ui,item) for item in self.ui.__dict__ if '_button' in item[-7:]] # Collect all items to block on calls
        self.blockItems.append(self.ui.DataSet_binning_comboBox)

        self.lineEdits = [getattr(self.ui,item) for item in self.ui.__dict__ if '_lineEdit' in item[-9:]] # Collect all items to block on calls
        
        self.update()
        initGenerateScript(self)

        for view in self.views: # Run through all views to set them up
            view.setup()

        setupGenerateScript(self)
        self.update()
        self.setupMenu()
        self.update()
        self.setupStateMachine()
        self.update()
        self.stateMachine.run()
        self.update()
        self.loadFolder() # Load last folder as default 
        self.loadedGuiSettings = None
        self.changeTheme(self.theme)
        self.ui.menubar.setNativeMenuBar(False)

    def setupMenu(self): # Set up all QActions and menus
        self.ui.actionExit.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/cross-button.png')))
        self.ui.actionExit.setToolTip('Exit the application') 
        self.ui.actionExit.setStatusTip(self.ui.actionExit.toolTip())
        self.ui.actionExit.triggered.connect(self.close)

        self.ui.actionAbout.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/information-button.png')))
        self.ui.actionAbout.setToolTip('Show About') 
        self.ui.actionAbout.setStatusTip(self.ui.actionAbout.toolTip())
        self.ui.actionAbout.triggered.connect(self.about)

        self.ui.actionHelp.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/question-button.png')))
        self.ui.actionHelp.setToolTip('Show Help') 
        self.ui.actionHelp.setStatusTip(self.ui.actionHelp.toolTip())
        self.ui.actionHelp.triggered.connect(self.help)

        self.ui.actionSave_GUI_state.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/folder-save.png')))
        self.ui.actionSave_GUI_state.setToolTip('Save current Gui setup') 
        self.ui.actionSave_GUI_state.setStatusTip(self.ui.actionSave_GUI_state.toolTip())
        self.ui.actionSave_GUI_state.triggered.connect(self.saveCurrentGui)
        self.actionSave_GUI_state_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        self.actionSave_GUI_state_shortcut.activated.connect(self.saveCurrentGui)

        self.ui.actionLoad_GUI_state.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/folder--arrow.png')))
        self.ui.actionLoad_GUI_state.setToolTip('Load Gui setup') 
        self.ui.actionLoad_GUI_state.setStatusTip(self.ui.actionLoad_GUI_state.toolTip())
        self.ui.actionLoad_GUI_state.triggered.connect(self.loadGui)
        self.actionLoad_GUI_state_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self)
        self.actionLoad_GUI_state_shortcut.activated.connect(self.loadGui)

        self.ui.actionGenerate_View3d_script.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/script-3D.png')))
        self.ui.actionGenerate_View3d_script.setToolTip('Generate 3D Script') 
        self.ui.actionGenerate_View3d_script.setStatusTip(self.ui.actionGenerate_View3d_script.toolTip())
        self.ui.actionGenerate_View3d_script.triggered.connect(self.generate3DScript)

        self.ui.actionGenerate_QELine_script.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/script-QE.png')))
        self.ui.actionGenerate_QELine_script.setToolTip('Generate QELine Script') 
        self.ui.actionGenerate_QELine_script.setStatusTip(self.ui.actionGenerate_QELine_script.toolTip())
        self.ui.actionGenerate_QELine_script.triggered.connect(self.generateQELineScript)
        
        self.ui.actionGenerate_QPlane_script.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/script-QP.png')))
        self.ui.actionGenerate_QPlane_script.setToolTip('Generate QPlane Script') 
        self.ui.actionGenerate_QPlane_script.setStatusTip(self.ui.actionGenerate_QPlane_script.toolTip())
        self.ui.actionGenerate_QPlane_script.triggered.connect(self.generateQPlaneScript)
        
        self.ui.actionGenerate_1d_script.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/script-1D.png')))
        self.ui.actionGenerate_1d_script.setToolTip('Generate Cut1D Script') 
        self.ui.actionGenerate_1d_script.setStatusTip(self.ui.actionGenerate_1d_script.toolTip())
        self.ui.actionGenerate_1d_script.triggered.connect(self.generateCut1DScript)
        
        self.ui.actionOpen_mask_gui.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/mask-open.png')))
        self.ui.actionOpen_mask_gui.setDisabled(True)
        self.ui.actionOpen_mask_gui.setToolTip('Open Mask Gui - Not Implemented') 
        self.ui.actionOpen_mask_gui.setStatusTip(self.ui.actionOpen_mask_gui.toolTip())
        
        self.ui.actionLoad_mask.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/mask-load.png')))
        self.ui.actionLoad_mask.setDisabled(True)
        self.ui.actionLoad_mask.setToolTip('Load Mask - Not Implemented') 
        self.ui.actionLoad_mask.setStatusTip(self.ui.actionLoad_mask.toolTip())

        self.ui.actionSettings.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/settings.png')))
        self.ui.actionSettings.setDisabled(False)
        self.ui.actionSettings.setToolTip('Change View Settings') 
        self.ui.actionSettings.setStatusTip(self.ui.actionSettings.toolTip())
        self.ui.actionSettings.triggered.connect(self.settingsDialog)

        
        self.ui.actionClose_Windows.setIcon(QtGui.QIcon(self.AppContext.get_resource('Icons/Own/CloseWindows.png')))
        self.ui.actionClose_Windows.setDisabled(False)
        self.ui.actionClose_Windows.setToolTip('Close All Plotting Windows') 
        self.ui.actionClose_Windows.setStatusTip(self.ui.actionClose_Windows.toolTip())
        self.ui.actionClose_Windows.triggered.connect(self.closeWindows)

    def getProgressBarValue(self):
        return self.ui.progressBar.value

    def setProgressBarValue(self,value):
        if not hasattr(self,'ui.progressBar.value'):
            self.ui.progressBar.value = 0
        
        self.ui.progressBar.setValue(value)
        self.ui.progressBar.value = value

    def setProgressBarLabelText(self,text):
        if self.current_timer:
            self.current_timer.stop()
        self.ui.progressBar_label.setText(text)

    def setProgressBarMaximum(self,value):
        self.ui.progressBar.setMaximum(value)

    def resetProgressBar(self):
        self.setProgressBarValue(0)
        self.setProgressBarLabelText('Ready')

    def saveSettingsDialog(self,event):
        res = QtWidgets.QMessageBox.question(self,
                                    "Exit - Save Gui Settings",
                                    "Do you want to save Gui Settings?",
                                    QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
        
        
        if res == QtWidgets.QMessageBox.Save:
            self.saveCurrentGui()
            self.closeWindows()
            event.accept()
        elif res == QtWidgets.QMessageBox.No:
            self.closeWindows()
            event.accept()
            return 1
        else:
            event.ignore()
            return 0

    def quitDialog(self,event):
        res = QtWidgets.QMessageBox.question(self,
                                    "Exit",
                                    "Do you want to exit the Gui?",
                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        
        if res == QtWidgets.QMessageBox.Yes:
            self.closeWindows()
            event.accept()
            return 1
        else:
            event.ignore()
            return 0

    def closeEvent(self, event):

        if self.loadedGuiSettings is None:
            if not self.saveSettingsDialog(event): # The dialog is cancelled
                return
        
        elif np.all([s1==s2 for s1,s2 in zip(self.loadedGuiSettings.values(),self.generateCurrentGuiSettings().values())]):
            if not self.quitDialog(event):
                return

        else:
            if not self.saveSettingsDialog(event): # The dialog is cancelled
                return

        self.closeWindows()

    @ProgressBarDecoratorArguments(runningText='Closing Windowa',completedText='Windows Closed')
    def closeWindows(self):
        if hasattr(self,'windows'):
            for window in self.windows:
                try:
                    plt.close(window)
                except:
                    pass
        return True

    def about(self):
        dialog = qtmodern.windows.ModernWindow(AboutDialog(self.AppContext.get_resource('About.txt')))
        dialog.show()

    def help(self):
        dialog = qtmodern.windows.ModernWindow(HelpDialog(self.AppContext.get_resource('Help.txt')))
        dialog.show()


    def setupStateMachine(self):
        self.stateMachine = StateMachine([empty,partial,raw,converted],self)

    def update(self):
        QtWidgets.QApplication.processEvents()
        QtWidgets.QApplication.processEvents()
        

    @ProgressBarDecoratorArguments(runningText='Saving Gui Settings',completedText='Gui Settings Saved',failedText='Cancelled')
    def saveCurrentGui(self): # save data set and files in format DataSetNAME DataFileLocation DataFileLocation:DataSetNAME
        #DataSet = [self.dataSets[I].name for I in range(self.DataSetModel.rowCount(None))]
        
        settingsDict = self.generateCurrentGuiSettings(updateProgressBar=True)
        if not hasattr(self,'loadedSettingsFile'):
            self.loadedSettingsFile = home
        saveSettings,_ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File',self.loadedSettingsFile)

        if saveSettings is None or saveSettings == '':
            return False

        if not saveSettings.split('.')[-1] == 'MJOLNIRGuiSettings':
            saveSettings+='.MJOLNIRGuiSettings'

        for key,value in settingsDict.items():
            updateSetting(saveSettings,key,value)

        return True


    def generateCurrentGuiSettings(self,updateProgressBar=False):
        saveString = []
        
        if updateProgressBar: self.setProgressBarMaximum(len(self.DataSetModel.dataSets))

        for i,ds in enumerate(self.DataSetModel.dataSets):
            dsDict = {'name':ds.name}
            
            localstring = [df.fileLocation if df.type != 'nxs' else df.original_file.fileLocation for df in ds]
            dsDict['files']=localstring
            dsDict['binning'] = [None if df.type != 'nxs' else df.binning for df in ds]
            saveString.append(dsDict)
            if updateProgressBar: self.setProgressBarValue((i+1))

        lineEditString = self.generateCurrentLineEditSettings()
        fileDir = self.getCurrentDirectory()

        infos = self.DataFileInfoModel.currentInfos()
        guiSettings = self.guiSettings()
        
        returnDict = {'dataSet':saveString, 'lineEdits':lineEditString, 
                      'fileDir':fileDir, 'infos':infos, 'guiSettings':guiSettings}
        return returnDict

    def generateCurrentLineEditSettings(self):
        lineEditValueString = {}
        for item in self.lineEdits:
            lineEditValueString[item.objectName()] = item.text()
        return lineEditValueString


    def loadFolder(self):
        fileDir = loadSetting(self.settingsFile,'fileDir')
        if not fileDir is None:
            self.setCurrentDirectory(fileDir)


    @ProgressBarDecoratorArguments(runningText='Loading gui settings',completedText='Loading Done',failedText='Cancelled')
    def loadGui(self):
        
        # Load saveFile
        if not hasattr(self,'loadedSettingsFolder'):
            folder = home
        else:
            folder = self.loadedSettingsFolder
        
        settingsFile,_ = QtWidgets.QFileDialog.getOpenFileName(self,"Open GUI settings file", folder,"Setting (*.MJOLNIRGuiSettings);;All Files (*)")
        self.update()
        self.loadedSettingsFolder = os.path.dirname(settingsFile)
        self.loadedSettingsFile = settingsFile
        
        if settingsFile is None or settingsFile == '':
            return False
        
        self.setProgressBarLabelText('Deleating Old Data Sets and Files')
        while self.DataSetModel.rowCount(None)>0:
            self.DataSetModel.delete(self.DataSetModel.getCurrentDatasetIndex())
        else:
            self.DataSetModel.layoutChanged.emit()
            self.DataFileModel.updateCurrentDataSetIndex()
        self.update()
        dataSetString = loadSetting(settingsFile,'dataSet')

        totalFiles = np.sum([len(dsDict['files'])+np.sum(1-np.array([d is None for d in dsDict['binning']]))+1 for dsDict in dataSetString])+1
        # Get estimate of total number of data files
        self.setProgressBarMaximum(totalFiles)
        counter = 0


        for dsDict in dataSetString:
            self.setProgressBarLabelText('Loading Data Set')
            DSName = dsDict['name']
            files = dsDict['files']
            dfs = None
            if len(files)!=0: # If files in dataset, continue
                dfs = []
                for dfLocation in files:
                    df = GuiDataFile(dfLocation)
                    self.update()
                    dfs.append(df)
                    counter+=1
                    self.setProgressBarValue(counter)
            if DSName == '':
                continue
            ds = GuiDataSet(name=DSName,dataFiles=dfs)
            if 'binning' in dsDict:
                if not np.any([b is None for b in dsDict['binning']]):
                    binnings = dsDict['binning']
                    for df,binning in zip(ds,binnings):
                        df.binning = binning
                    self.setProgressBarLabelText('Converting Data Set')    
                    ds.convertDataFile(guiWindow=self,setProgressBarMaximum=False)
                    self.update()
            
            self.DataSetModel.append(ds)
            self.DataSetModel.layoutChanged.emit()
            self.update()
            counter+=1
            self.setProgressBarValue(counter)
            
        DataFileListInfos = loadSetting(settingsFile,'infos')
        if not DataFileListInfos is None:
            self.DataFileInfoModel.infos = DataFileListInfos

        guiSettings = loadSetting(settingsFile,'guiSettings')
        if guiSettings:
            if not self.theme == guiSettings['theme']:
                self.changeTheme(guiSettings['theme'])

        self.loadLineEdits(file=settingsFile)
        self.DataSetModel.layoutChanged.emit()
        self.DataFileInfoModel.layoutChanged.emit()
        self.DataFileModel.updateCurrentDataSetIndex()
        self.update()


        self.loadedGuiSettings = self.generateCurrentGuiSettings()
        return True

    def guiSettings(self):
        settingsDict = {'theme':self.theme}
        return settingsDict

    def loadLineEdits(self,file=None):
        if file is None:
            file = self.settingsFile
        lineEditValueString = loadSetting(file,'lineEdits')
        if not lineEditValueString is None:
            if isinstance(lineEditValueString,str):
                print('Please save a new gui state to comply with the new version')
                return
            for item,value in lineEditValueString.items():
                try:
                    getattr(self.ui,item).setText(value)
                except AttributeError:
                    pass

    def getCurrentDirectory(self):
        return self.ui.DataSet_path_lineEdit.text()

    def setCurrentDirectory(self,folder):
        self.currentFolder = folder
        self.ui.DataSet_path_lineEdit.setText(folder)
        

    

    def resetProgressBarTimed(self):
        if self.current_timer:
            self.current_timer.stop()
        self.current_timer = QtCore.QTimer()
        self.current_timer.timeout.connect(self.resetProgressBar)
        self.current_timer.setSingleShot(True)
        self.current_timer.start(3000)

    def changeTheme(self,name):
        if not name in themes.keys():
            raise AttributeError('Theme name not recognized. Got {}, but allowed are: '.format(name),', '.join(themes.keys()))
        app = QtWidgets.QApplication.instance()
        self.theme = name
        themes[name](app)
        #palette = app.palette()
        #print('Palette:',palette)
        #for view in self.views:
        #    view.setPalette(palette)


    def settingsDialog(self):
        # Get infos from DataFileInfoModel
        
        dataFileInfoModelPossibleSettings,dataFileInfoModelInitial = self.DataFileInfoModel.settingsDialog()
        # Create a widget holding check boxes for all possible settings

        dFIMLayout = QtWidgets.QVBoxLayout()
        dFIMTitleLabel = QtWidgets.QLabel(text='Select infos to be shown for selected file(s)')
        dFIMTitleLabel.setAlignment(QtCore.Qt.AlignCenter)
        # Add title to layout
        dFIMLayout.addWidget(dFIMTitleLabel)

        # make check boxes for all settings
        dFIMcheckBoxes = []
        for setting in dataFileInfoModelPossibleSettings.values():
            checkBox = QtWidgets.QCheckBox()
            dFIMcheckBoxes.append(checkBox)
            name = setting.location
            checkBox.setText(name)
            checkBox.setChecked(setting in dataFileInfoModelInitial)
            dFIMLayout.addWidget(checkBox)

        # accept function arguments: self (dialog), layout which was passed in
        def dFIMAcceptFunction(self,layout,possibleSettings=dataFileInfoModelPossibleSettings):
            self.dMFIASettings = []
            for idx,setting in enumerate(possibleSettings.values()): # Loop through all the possible settings
                box = layout.itemAt(idx+1).widget() # Skip 0 as it is a QLabel
                if box.isChecked():# If checked add the corresponding setting to list of loaded settings
                    self.dMFIASettings.append(setting.location)


        # Create layout for gui settings
        guiSettingsLayout = QtWidgets.QVBoxLayout()
        guiSettingsTitleLabel = QtWidgets.QLabel(text='Settings for the Gui')
        guiSettingsTitleLabel.setAlignment(QtCore.Qt.AlignCenter)
        guiSettingsLayout.addWidget(guiSettingsTitleLabel)


        # Create radiobuttons
        for theme in themes.keys():
            radiobutton = QtWidgets.QRadioButton(theme)
            radiobutton.setChecked(theme == self.theme)
            radiobutton.theme = theme
            guiSettingsLayout.addWidget(radiobutton)
        
        def guiSettingsAcceptFunction(self,layout):
            length = layout.count()-1 # first entry is QLabel
            
            for idx in range(length):
                radiobutton = layout.itemAt(idx+1).widget()
                if radiobutton.isChecked():
                    theme = radiobutton.theme
            self.theme = theme

        # settings holds a list of possible settings for all setting fields
        layouts = [guiSettingsLayout,dFIMLayout]
        acceptFunctions = [guiSettingsAcceptFunction,dFIMAcceptFunction]
        dialog = settingsBoxDialog(layouts=layouts,acceptFunctions=acceptFunctions)

        dialog.resize(dialog.sizeHint())
        
        
        
        if dialog.exec_(): # Execute the dialog
            self.DataFileInfoModel.infos = dialog.dMFIASettings # update settings
            self.DataFileInfoModel.layoutChanged.emit()
            self.changeTheme(dialog.theme)
        else:
            return

class settingsBoxDialog(qtmodern.windows.ModernDialog):

    def __init__(self, layouts, acceptFunctions, *args, **kwargs):
        super(settingsBoxDialog, self).__init__(*args, **kwargs)
        
        self.setWindowTitle("Settings")
        self.acceptFunctions = acceptFunctions
        self.layouts = layouts

        self.layout = QtWidgets.QVBoxLayout()
        
        for layout in layouts:
            self.layout.addLayout(layout)
        
        
        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        
        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def accept(self): # the accept button has been pressed
        for aFunc,layout in zip(self.acceptFunctions,self.layouts):
            aFunc(self,layout)
        return super(settingsBoxDialog,self).accept()

    def reject(self):
        return super(settingsBoxDialog,self).reject()

def updateSplash(splash,originalTime,updateInterval,padding='\n'*7+20*' '):
    currentTime = datetime.datetime.now()
    points = int(1000.0*(currentTime-originalTime).total_seconds()/updateInterval)+1

    alignment = QtCore.Qt.AlignTop# | QtCore.Qt.AlignHCenter
    splash.showMessage(padding+'Loading MJOLNIRGui'+'.'*points,color=QtGui.QColor(255,255,255),alignment=alignment)
    #QTimer.singleShot(1000, updateSplash(splash,points+1) )
    QtWidgets.QApplication.processEvents()

def main():
    import AppContextEmulator

    app = QtWidgets.QApplication(sys.argv) # Passing command line arguments to app
    qtmodern.styles.dark(app)

    appEmu = AppContextEmulator.AppContextEmulator(__file__)

    splash = QtWidgets.QSplashScreen(QtGui.QPixmap(appEmu.get_resource('splash.png')))                                    
    splash.show()

    timer = QtCore.QTimer() 

    # adding action to timer 
    updateInterval = 400 # ms
    originalTime = datetime.datetime.now()
    updater = lambda:updateSplash(splash,originalTime=originalTime,updateInterval=updateInterval)
    updater()
    timer.timeout.connect(updater) 

    # update the timer every updateInterval 
    timer.start(updateInterval)
    

    window = MJOLNIRMainWindow(appEmu) # This window has to be closed for app to end
    window = qtmodern.windows.ModernWindow(window)
    splash.finish(window)
    window.show()
    timer.stop()

    app.exec_() 

if __name__ == '__main__':
    main()

    