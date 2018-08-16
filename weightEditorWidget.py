"""
import __main__
self = __main__.weightEditor
"""
from Qt import QtGui, QtCore, QtWidgets

# import shiboken2 as shiboken
from functools import partial
from maya import cmds
import blurdev


from tools.skinData import DataOfSkin
from tools.tableWidget import TableView, TableModel
from tools.spinnerSlider import ValueSetting, ButtonPruneWeights
from tools.utils import GlobalContext

styleSheet = """

QWidget {
    background:  #aba8a6;
    color:black;
    selection-background-color: #a0a0ff;

}

QMenu::item:disabled {
    color:grey;
    font: italic;
}
QMenu::item:selected  {
    background-color:rgb(120, 120, 120);  
}
QPushButton {
    color:  black;
}
QPushButton:checked{
    background-color: rgb(80, 80, 80);
    color:white;
    border: none; 
}
QPushButton:hover{  
    background-color: grey; 
    border-style: outset;  
}  

TableView {
     selection-background-color: #a0a0ff;
     background : #aba8a6;
     color: black;
     selection-color: black;
     border : 0px;
 }
QTableView QTableCornerButton::section {
    background:  #878787;
    border : 1px solid black;
}
 
TableView::section {
    background-color: #878787;
    color: black;
    border : 1px solid black;
}
QHeaderView::section {
    background-color: #878787;
    color: black;
    border : 1px solid black;
}
VertHeaderView{
    color: black;
    border : 0px solid black;
}
HorizHeaderView{
    color: black;
    border : 0px solid black;
}

"""
"""
MyHeaderView{
    background-color: #878787;
    color: black;
    border : 0px solid black;
}
"""

###################################################################################
#
#   the window
#
###################################################################################


class SkinWeightWin(QtWidgets.QDialog):
    """
    A simple test widget to contain and own the model and table.
    """

    colWidth = 30
    maxWidthCentralWidget = 340

    def __init__(self, parent=None):
        super(SkinWeightWin, self).__init__(parent)
        """
        self.setFloating (True)
        self.setAllowedAreas( QtCore.Qt.DockWidgetAreas ())
        self.isDockable = False
        """
        import __main__

        __main__.__dict__["weightEditor"] = self

        if not cmds.pluginInfo("blurSkin", query=True, loaded=True):
            cmds.loadPlugin("blurSkin")
        blurdev.gui.loadUi(__file__, self)

        # QtWidgets.QWidget.__init__(self, parent)
        self.dataOfSkin = DataOfSkin()
        self.get_data_frame()
        self.createWindow()
        self.setStyleSheet(styleSheet)

        refreshSJ = cmds.scriptJob(event=["SelectionChanged", self.refresh])
        self.listJobEvents = [refreshSJ]

        self.setWindowDisplay()

    def setWindowDisplay(self):
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.Tool)
        self.setWindowTitle("Weight Editor")
        self.refreshPosition()
        self.show()

    def mousePressEvent(self, event):
        # print "click"
        if event.button() == QtCore.Qt.MidButton:
            nbShown = 0
            for ind in range(self._tv.HHeaderView.count()):
                if not self._tv.HHeaderView.isSectionHidden(ind):
                    nbShown += 1
            wdth = self._tv.VHeaderView.width() + nbShown * self.colWidth + 50
            self.resize(wdth, self.height())
        else:
            self._tv.clearSelection()
        super(SkinWeightWin, self).mousePressEvent(event)

    def refreshPosition(self):
        vals = cmds.optionVar(q="SkinWeightWindow")
        if vals:
            self.move(vals[0], vals[1])
            self.resize(vals[2], vals[3])

    def closeEvent(self, event):
        for jobNum in self.listJobEvents:
            cmds.scriptJob(kill=jobNum, force=True)
        pos = self.pos()
        size = self.size()
        cmds.optionVar(clearArray="SkinWeightWindow")
        for el in pos.x(), pos.y(), size.width(), size.height():
            cmds.optionVar(intValueAppend=("SkinWeightWindow", el))
        # self.headerView.deleteLater()
        super(SkinWeightWin, self).closeEvent(event)

    def keyPressEvent(self, event):
        theKeyPressed = event.key()
        ctrlPressed = event.modifiers() == QtCore.Qt.ControlModifier

        if ctrlPressed and event.key() == QtCore.Qt.Key_Z:
            self.storeSelection()
            self._tm.beginResetModel()

            self.dataOfSkin.callUndo()

            self._tm.endResetModel()
            self.retrieveSelection()

            # super(SkinWeightWin, self).keyPressEvent(event)
            return
        super(SkinWeightWin, self).keyPressEvent(event)

    def addButtonsDirectSet(self, lstBtns):
        theCarryWidget = QtWidgets.QWidget()

        carryWidgLayoutlayout = QtWidgets.QHBoxLayout(theCarryWidget)
        carryWidgLayoutlayout.setContentsMargins(40, 0, 0, 0)
        carryWidgLayoutlayout.setSpacing(0)

        for theVal in lstBtns:
            newBtn = QtWidgets.QPushButton("{0:.0f}".format(theVal))

            newBtn.clicked.connect(self.prepareToSetValue)
            newBtn.clicked.connect(partial(self.doAddValue, theVal / 100.0))
            newBtn.clicked.connect(self.dataOfSkin.postSkinSet)

            carryWidgLayoutlayout.addWidget(newBtn)
        theCarryWidget.setMaximumSize(self.maxWidthCentralWidget, 14)

        return theCarryWidget

    def createWindow(self):
        theLayout = self.layout()  # QtWidgets.QVBoxLayout(self)
        theLayout.setContentsMargins(10, 10, 10, 10)
        theLayout.setSpacing(3)

        topButtonsLay = self.topButtonsWidget.layout()

        self._tm = TableModel(self)
        self._tm.update(self.dataOfSkin)

        self._tv = TableView(self, colWidth=self.colWidth)
        self._tv.setModel(self._tm)
        # self._tm._tv = self._tv

        self.valueSetter = ValueSetting(self)  # ProgressItem("BlendShape", szrad = 0, value = 0)
        Hlayout = QtWidgets.QHBoxLayout(self)
        Hlayout.setContentsMargins(0, 0, 0, 0)
        Hlayout.setSpacing(0)
        Hlayout.addWidget(self.valueSetter)
        self.valueSetter.setMaximumWidth(self.maxWidthCentralWidget)

        self.widgetAbs = self.addButtonsDirectSet(
            [0, 10, 25, 100.0 / 3, 50, 200 / 3.0, 75, 90, 100]
        )
        self.widgetAdd = self.addButtonsDirectSet(
            [-100, -75, -200 / 3.0, -50, -100.0 / 3, -25, 25, 100.0 / 3, 50, 200 / 3.0, 75, 100]
        )

        Hlayout2 = QtWidgets.QHBoxLayout(self)
        Hlayout2.setContentsMargins(0, 0, 0, 0)
        Hlayout2.setSpacing(0)
        Hlayout2.addWidget(self.widgetAbs)
        Hlayout2.addWidget(self.widgetAdd)

        topButtonsLay.addSpacing(10)
        topButtonsLay.addLayout(Hlayout2)
        self.widgetAbs.hide()
        topButtonsLay.addLayout(Hlayout)
        topButtonsLay.addSpacing(10)

        theLayout.addWidget(self._tv)

        self.setColumnVisSize()

        self.pruneWghtBTN = ButtonPruneWeights(self)
        self.botLayout.insertWidget(3, self.pruneWghtBTN)

        # -----------------------------------------------------------
        self.refreshBTN.clicked.connect(self.refreshBtn)
        self.smoothBTN.clicked.connect(self.smooth)
        self.addBTN.toggled.connect(self.changeAddAbs)
        self.pruneWghtBTN.clicked.connect(self.pruneWeights)

        self.addPercBTN.setEnabled(False)

    def pruneWeights(self):
        print self.pruneWghtBTN.precisionValue

    def changeAddAbs(self, checked):
        self.widgetAbs.setVisible(False)
        self.widgetAdd.setVisible(False)
        self.widgetAbs.setVisible(not checked)
        self.widgetAdd.setVisible(checked)
        self.valueSetter.setAddMode(checked)

    def smooth(self):
        cmds.blurSkinCmd(command="smooth", repeat=3)

    def prepareToSetValue(self):
        # with GlobalContext (message = "prepareValuesforSetSkinData"):
        chunks = self.getRowColumnsSelected()

        actualyVisibleColumns = [
            indCol
            for indCol in self.dataOfSkin.hideColumnIndices
            if not self._tv.HHeaderView.isSectionHidden(indCol)
        ]
        if chunks:
            self.dataOfSkin.prepareValuesforSetSkinData(chunks, actualyVisibleColumns)
            return True
        return False

    def storeSelection(self):
        selection = self._tv.selectionModel().selection()
        self.topLeftBotRightSel = [
            (item.top(), item.left(), item.bottom(), item.right()) for item in selection
        ]

    def retrieveSelection(self):
        newSel = self._tv.selectionModel().selection()
        for top, left, bottom, right in self.topLeftBotRightSel:
            newSel.select(self._tm.index(top, left), self._tm.index(bottom, right))
        self._tv.selectionModel().select(newSel, QtCore.QItemSelectionModel.ClearAndSelect)

    def doAddValue(self, val, forceAbsolute=False):
        self.storeSelection()
        self._tm.beginResetModel()

        if self.valueSetter.addMode and not forceAbsolute:
            self.dataOfSkin.setSkinData(val)
        else:
            self.dataOfSkin.absoluteVal(val)

        self._tm.endResetModel()
        self.retrieveSelection()

    def getRowColumnsSelected(self):
        sel = self._tv.selectionModel().selection()
        chunks = []
        for item in sel:
            chunks.append((item.top(), item.bottom(), item.left(), item.right()))
        return chunks

    def refreshBtn(self):
        self.storeSelection()
        self.refresh()
        self.retrieveSelection()

    def refresh(self):
        self._tm.beginResetModel()
        for ind in self.dataOfSkin.hideColumnIndices:
            self._tv.showColumn(ind)
        self.dataOfSkin.getAllData()
        self._tm.endResetModel()
        self.setColumnVisSize()

    def setColumnVisSize(self):
        if self.dataOfSkin.columnCount:
            for i in range(self.dataOfSkin.columnCount):
                self._tv.setColumnWidth(i, self.colWidth)
            self._tv.setColumnWidth(i + 1, self.colWidth + 10)  # sum column
        self.hideColumns()

    def hideColumns(self):
        # self.dataOfSkin.getZeroColumns ()
        for ind in self.dataOfSkin.hideColumnIndices:
            self._tv.hideColumn(ind)
        # self._tv.headerView.setMaximumWidth(self.colWidth*len (self.dataOfSkin.usedDeformersIndices))

    def get_data_frame(self):
        with GlobalContext(message="get_data_frame"):
            self.dataOfSkin.getAllData()
        return self.dataOfSkin
