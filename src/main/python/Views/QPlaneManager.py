import sys
sys.path.append('..')

from _tools import ProgressBarDecoratorArguments

from os import path
from PyQt5 import QtWidgets
import numpy as np

def QPlane_plot_button_function(self):
    # Make plot
    if not self.stateMachine.requireStateByName('Converted'):
        return False
    ds = self.DataSetModel.getCurrentDataSet()
    if len(ds.convertedFiles)==0:
        self.DataSet_convertData_button_function()        
    
    # Check various plot settings
    if self.ui.QELine_SelectUnits_RLU_radioButton.isChecked():
        rlu=True
    else:
        rlu=False        

    if self.ui.QPlane_LogScale_checkBox.isChecked():
        log=True
    else:
        log=False          

    EMin=float(self.ui.QPlane_EMin_lineEdit.text())
    EMax=float(self.ui.QPlane_EMax_lineEdit.text())
    QxWidth = float(self.ui.QPlane_QxWidth_lineEdit.text())           
    QyWidth = float(self.ui.QPlane_QyWidth_lineEdit.text())           

    Data,Bins,ax = ds.plotQPlane(EMin=EMin, EMax=EMax,xBinTolerance=QxWidth,yBinTolerance=QyWidth,log=log,rlu=rlu)
    
    self.QPlane=ax    
    
    fig = self.QPlane.get_figure()
    fig.colorbar(ax.pmeshs[0])
    fig.set_size_inches(8,6)

    if self.ui.QPlane_Grid_checkBox.isChecked():
        ax.grid(True)
    else:
        ax.grid(False)
    
    self.QPlane_setCAxis_button_function()
    self.QPlane_SetTitle_button_function()
    self.windows.append(self.QPlane.get_figure())

    return True
    

def QPlane_setCAxis_button_function(self):
    CAxisMin=float(self.ui.QPlane_CAxisMin_lineEdit.text())
    CAxisMax=float(self.ui.QPlane_CAxisMax_lineEdit.text())

    self.QPlane.set_clim(CAxisMin,CAxisMax)
    fig = self.QPlane.get_figure()
    fig.canvas.draw()
    
def QPlane_SetTitle_button_function(self):
    TitleText=self.ui.QPlane_SetTitle_lineEdit.text()        
    if hasattr(self, 'QPlane'):
        TitleText=self.ui.QPlane_SetTitle_lineEdit.text()        
        self.QPlane.set_title(TitleText)
        fig = self.QPlane.get_figure()
        fig.canvas.draw()
    



def initQPlaneManager(guiWindow):
    guiWindow.QPlane_plot_button_function = lambda: QPlane_plot_button_function(guiWindow)
    guiWindow.QPlane_setCAxis_button_function = lambda: QPlane_setCAxis_button_function(guiWindow)
    guiWindow.QPlane_SetTitle_button_function = lambda: QPlane_SetTitle_button_function(guiWindow)

def setupQPlaneManager(guiWindow):
    
    guiWindow.ui.QPlane_plot_button.clicked.connect(guiWindow.QPlane_plot_button_function)
    guiWindow.ui.QPlane_setCAxis_button.clicked.connect(guiWindow.QPlane_setCAxis_button_function)
    guiWindow.ui.QPlane_SetTitle_button.clicked.connect(guiWindow.QPlane_SetTitle_button_function)
