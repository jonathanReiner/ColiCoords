from PyQt4 import QtGui
import sys
from colicoords.gui.controller import InputController

app = QtGui.QApplication(sys.argv)

ctrl = InputController()
ctrl.show()

sys.exit(app.exec_())