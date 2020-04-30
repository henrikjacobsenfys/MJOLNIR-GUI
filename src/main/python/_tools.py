import pickle as pickle
import os
import functools
from PyQt5 import QtWidgets

def ProgressBarDecoratorArguments(runningText='Running',completedText='Completed',failedText='Failed'):

    def ProgressBarDecorator(func):
        @functools.wraps(func)
        def newFunc(self,*args,**kwargs):
            self.setProgressBarValue(0)
            self.setProgressBarLabelText(runningText)
            if len(args) == 1:
                args = ()
            else:
                args = args[1:]
            self.update()
            returnval = func(self,*args,**kwargs)

            self.setProgressBarMaximum(100)
            if returnval is not None:
                if returnval is False:
                    self.setProgressBarValue(0)
                    self.setProgressBarLabelText(failedText)
                    self.resetProgressBarTimed()
                    return returnval
        
            self.setProgressBarValue(100)
            self.setProgressBarLabelText(completedText)
            self.resetProgressBarTimed()
            return returnval
        return newFunc
    return ProgressBarDecorator


def loadSetting(settingsFile,string): # pragma: no cover
    if Exists(settingsFile):
        with open(settingsFile,"rb") as pickle_in:
            loaded_dict = pickle.load(pickle_in)
        if string in loaded_dict:
            returnValue = loaded_dict[string]
        else:
            returnValue = None
        return returnValue
    else:
        return None

def updateSetting(settingsFile, name,value):# pragma: no cover
    if Exists(settingsFile):
        with open(settingsFile,"rb") as pickle_in:
            loaded_dict = pickle.load(pickle_in)
    else:
        loaded_dict = {}
    loaded_dict[name]=value
    with open(settingsFile,"wb") as pickle_out:
        pickle.dump(loaded_dict, pickle_out,protocol=pickle.HIGHEST_PROTOCOL)

def Exists(settingsFile):# pragma: no cover
    return os.path.isfile(settingsFile)

def dialog(text):
    dialog = QtWidgets.QMessageBox()
    dialog.setIcon(QtWidgets.QMessageBox.Critical)
    dialog.setText(text)
    dialog.addButton(QtWidgets.QMessageBox.Ok)
    dialog.exec() 