from PySide2 import QtCore,QtWidgets,QtGui
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.mel as mel

import utils
import viewer
reload(utils)   # Temp
reload(viewer)   # Temp
import json
import os

# boilerplate code, return maya main window
def maya_main_window():
    # Return the maya main window widget as a python object
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class MasterToolkit(QtWidgets.QDialog):
    
    class_instance = None
    @classmethod
    def show_dialog(cls):
        if not cls.class_instance:
            cls.class_instance = MasterToolkit()
        if cls.class_instance.isHidden():
            cls.class_instance.show()
        else:
            cls.class_instance.raise_()
            cls.class_instance.activateWindow()
    
    def __init__(self, parent=maya_main_window()):
        super(MasterToolkit ,self).__init__(parent)

        # runtime data
        self.menu = []  # only include top level menu (not include menu that inside submenu)

        # window configuration
        self.setWindowTitle("Toolkit Menu")
        self.setWindowFlags(QtCore.Qt.WindowType.Window)
        self.setStyleSheet("borderstyle:outset")
        self.setMinimumWidth(375)
        self.setMinimumHeight(275)

        # Remove window question 
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        # completing window
        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        self.load_menu()
        self.load_dependency()

    def create_widgets(self):
        # Label icon and qimage class
        self.search_icon = utils.GraphicLabel(":search.png", (18,18))
        
        # line edit
        self.search_line_edit = utils.SearchLineEdit()
        
        # Button
        self.add_scripts_btn = QtWidgets.QPushButton()
        self.add_scripts_btn.setIcon(QtGui.QIcon(":addClip.png"))
        self.reload_data_btn = QtWidgets.QPushButton("Reload")
        self.reload_data_btn.setIcon(QtGui.QIcon(":refresh.png"))
        
        # QWidget
        self.data_list_qwidget = QtWidgets.QWidget()
        self.data_list_qwidget.setStyleSheet("background-color: #333333;")
        
        # QScrollArea
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.data_list_qwidget)

        # QTabWidget 
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabsClosable(True)

        self.tab_widget.addTab(self.scroll_area, "Explore")
        self.home_icon = QtGui.QIcon(QtGui.QPixmap.fromImage(utils.validate_image_path(utils.get_path("python.png"))))
        self.tab_widget.setTabIcon(0, QtGui.QIcon(self.home_icon))
        self.tab_bar = self.tab_widget.tabBar().setTabButton(0, QtWidgets.QTabBar.RightSide, None)  # remove close button for home page
    
    def create_layouts(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        
        # Layout
        self.header_layout = QtWidgets.QHBoxLayout()
        
        self.data_entry_layout = QtWidgets.QVBoxLayout(self.data_list_qwidget)
        self.data_entry_layout.setAlignment(QtCore.Qt.AlignTop)
        
        self.bottom_layout = QtWidgets.QHBoxLayout()
        
        # parent widget to layout
        self.header_layout.addWidget(self.search_icon)
        self.header_layout.addWidget(self.search_line_edit)
        self.header_layout.addWidget(self.add_scripts_btn)
        self.bottom_layout.addWidget(self.reload_data_btn)
        
        # parent layout/widget to main_layout
        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addWidget(self.tab_widget)
        self.main_layout.addLayout(self.bottom_layout)
      
    def create_connections(self):
        self.add_scripts_btn.clicked.connect(self.new_script)
        self.search_line_edit.returnPressed.connect(self.filter_menu)
        self.search_line_edit.textChanged.connect(lambda text: self.reset_filter_menu() if text == "" else None)   # show every menu if search input is empty
        self.reload_data_btn.clicked.connect(self.load_menu)
        self.tab_widget.tabCloseRequested.connect(self.onTabClose)

    def new_script(self):
        self.script_config_dialog.edit = False
        self.script_config_dialog.show()

    def load_menu(self, event=None):
        self.data_path = utils.get_path("data/scriptsData.json", icon=False)
        self.delete_all_menu()
        
        with open(self.data_path, 'r') as file:
            data = json.load(file)
        if len(data) == 0: 
            cmds.warning("No data was found, can't load menu")
            return
        self.deserialize(data)

        self.completer = QtWidgets.QCompleter([item.name for item in self.menu], 
                                            caseSensitivity=QtCore.Qt.CaseInsensitive)
        self.completer.setFilterMode(QtCore.Qt.MatchContains)
        self.search_line_edit.setCompleter(self.completer)
        self.completer.activated.connect(self.filter_menu)

    def save_menu(self):
        top_level_menu = [self.data_entry_layout.itemAt(index).widget() for index in range(self.data_entry_layout.count())]  # remember to only query top level menu to prevent serializing same menu twice
        try:
            json_obj = json.dumps(self.serialize(top_level_menu), indent=4)
            with open(self.data_path, 'w') as file:
                file.write(json_obj)
        except Exception as e:
            cmds.warning(e)

    def load_dependency(self):
        """load any helper window or data to prevent slow loading time when being used"""
        self.script_config_dialog = ScriptConfigDialog(toolkit_menu=self)

    def add_spacer(self,width=0,height=0):
        return QtWidgets.QSpacerItem(width, height, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    def filter_menu(self):
        text=self.search_line_edit.text()
        for menu in self.menu:
            visibility = text.lower() in menu.name.lower()
            menu.setVisible(visibility)
            if visibility and menu.subs:
                self.show_subs(menu)
    
    def reset_filter_menu(self):
        for menu in self.menu:
            menu.setVisible(True)
    
    def show_subs(self, menu):
        if menu.subs:
            menu.subs.setVisible(True)
            self.show_subs(menu.subs)
            menu.subs.menu_list_widget.collapse_detail(False)

    def delete_all_menu(self):
        for i in self.menu:
            i.deleteLater()
        self.menu = []

    def serialize(self, list_menu, file_type="folder", name="scripts"):
        result = {'name': name, 
                'type': file_type, 'children': []}

        for item in list_menu:
            if isinstance(item, ScriptSubmenu):
                result['children'].append(self.serialize(item.menu, "folder", item.name))
            else: 
                result['children'].append({'name': item.name, 'type': item.language, 'content': item.scripts, "icon":item.icon})
        return result 

    def deserialize(self, data, parent_menu=None, top_level=True):
        """build menu"""
        if data["children"]:
            for entry in data["children"]:
                if entry["type"] == "mel" or entry["type"] == "python":
                    new_menu = ScriptMenu(self, entry["name"], entry["icon"], entry["content"], entry["type"])
                    if parent_menu: parent_menu.addMenu(new_menu)
                    self.menu.append(new_menu)
                    if top_level: self.data_entry_layout.addWidget(new_menu)
                else:
                    new_submenu = ScriptSubmenu(self, entry["name"])
                    if parent_menu: parent_menu.addMenu(new_submenu)
                    self.menu.append(new_submenu)
                    self.deserialize(entry, new_submenu, False)
                    if top_level: self.data_entry_layout.addWidget(new_submenu)

    def onTabClose(self, index):
        menu_widget = self.tab_widget.widget(index)
        menu = menu_widget.menu
        if menu.isModified:
            res = QtWidgets.QMessageBox.question(self, "Confirmation",
                                                "%s has been changed. Do you want to save it?"%menu.name,
                                                QtWidgets.QMessageBox.Yes,
                                                QtWidgets.QMessageBox.No)
            if res == QtWidgets.QMessageBox.Yes:
                menu.scripts = menu.scriptPageWidget.textEdit.toPlainText()
                menu.language = menu.scriptPageWidget.language_btn_grp.checkedButton().text().lower()
                self.save_menu()
            menu.isModified = False
        self.tab_widget.removeTab(index)  

class ScriptConfigDialog(QtWidgets.QDialog):
    def __init__(self, name="", icon=None, script="", language = "python", toolkit_menu=None):
        super(ScriptConfigDialog, self).__init__(toolkit_menu)

        self.name = name
        self.icon = icon
        self.script = script
        self.language = language
        self.toolkit_menu = toolkit_menu

        self.editing_menu = None

        self.setWindowTitle("Script Config")
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        #self.setModal(True)
        self.resize(275,150)
        self.initUI()

    @property
    def edit(self):
        return self._edit
    
    @edit.setter
    def edit(self, bool):
        self._edit = bool
        if bool:
            self.save_btn.show()
            self.delete_btn.show()
            self.confirm_btn.hide()
        else:
            self.save_btn.hide()
            self.delete_btn.hide()
            self.confirm_btn.show()
        self.cleanup_data()

    def initUI(self):
        # widgets
        self.name_label = QtWidgets.QLabel("Name: ")
        self.name_line_edit = QtWidgets.QLineEdit()
        self.name_line_edit.setText(self.name)

        self.icon_label = QtWidgets.QLabel("icon: ")
        self.icon_line_edit = QtWidgets.QLineEdit()
        self.icon_line_edit.setText(self.icon)
        self.icon_explore_btn = utils.GraphicButton(utils.get_path("folder.png"), self.openFileDialog, size=(20,20))

        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.clicked.connect(self.onSave)
        self.delete_btn = QtWidgets.QPushButton("Delete")
        self.delete_btn.clicked.connect(self.onDelete)
        self.delete_btn.setStyleSheet("background-color:#c12e2e")
        self.confirm_btn = QtWidgets.QPushButton("Confirm")
        self.confirm_btn.clicked.connect(self.onConfirm)

        self.language_label = QtWidgets.QLabel("Language: ")
        self.language_btn_grp = QtWidgets.QButtonGroup()
        self.python_btn = QtWidgets.QRadioButton("Python")
        self.python_btn.setChecked(True)
        self.mel_btn = QtWidgets.QRadioButton("MEL")

        self.language_btn_grp.addButton(self.python_btn)
        self.language_btn_grp.addButton(self.mel_btn)

        self.script_text_edit = viewer.CodeViewer()
        viewer.PythonHighlighter(self.script_text_edit.document())
        self.script_text_edit.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)

        # layouts
        self.main_layout = QtWidgets.QVBoxLayout(self) 
        self.name_layout = QtWidgets.QHBoxLayout()
        self.icon_layout = QtWidgets.QHBoxLayout()
        self.language_layout = QtWidgets.QHBoxLayout()
        self.confirmation_layout = QtWidgets.QHBoxLayout()

        # organize
        self.name_layout.addWidget(self.name_label)
        self.name_layout.addWidget(self.name_line_edit)

        self.icon_layout.addWidget(self.icon_label)
        self.icon_layout.addWidget(self.icon_line_edit)
        self.icon_layout.addWidget(self.icon_explore_btn)

        self.language_layout.addWidget(self.language_label)
        self.language_layout.addWidget(self.python_btn)
        self.language_layout.addWidget(self.mel_btn)
        self.language_layout.addStretch()

        self.confirmation_layout.addWidget(self.save_btn)
        self.confirmation_layout.addWidget(self.delete_btn)
        self.confirmation_layout.addWidget(self.confirm_btn)

        self.main_layout.addLayout(self.name_layout)
        self.main_layout.addLayout(self.icon_layout)
        self.main_layout.addLayout(self.language_layout)
        self.main_layout.addWidget(self.script_text_edit)
        self.main_layout.addLayout(self.confirmation_layout)

    def onConfirm(self, event):
        new_menu = ScriptMenu(self.toolkit_menu, self.name_line_edit.text(), self.icon_line_edit.text(), self.script_text_edit.toPlainText(), self.language_btn_grp.checkedButton().text().lower())
        self.toolkit_menu.menu.append(new_menu)
        self.toolkit_menu.data_entry_layout.addWidget(new_menu)
        self.cleanup_data()
        self.toolkit_menu.save_menu()

    def onSave(self, event):
        if self.editing_menu:
            self.editing_menu.name = self.name_line_edit.text()
            self.editing_menu.icon = self.icon_line_edit.text()
            self.editing_menu.scripts = self.script_text_edit.toPlainText()
            self.editing_menu.language = self.language_btn_grp.checkedButton().text().lower()
        self.cleanup_data()
        self.toolkit_menu.save_menu()

    def onDelete(self, event):
        res = QtWidgets.QMessageBox.question(self, "Confirmation",
                                            "Are you sure you want to delete %s?"%self.editing_menu.name,
                                            QtWidgets.QMessageBox.Yes,
                                            QtWidgets.QMessageBox.No)
        if res == QtWidgets.QMessageBox.Yes:
            self.toolkit_menu.menu.remove(self.editing_menu)
            self.editing_menu.setParent(None)
            self.cleanup_data()
            self.toolkit_menu.save_menu()

    def load_data(self, menu):
        self.show()
        self.editing_menu = menu
        self.name_line_edit.setText(menu.name)
        self.icon_line_edit.setText(menu.icon)
        self.script_text_edit.setPlainText(menu.scripts)
        if menu.language == "python":
            self.python_btn.setChecked(True)
        else:
            self.mel_btn.setChecked(True)

    def cleanup_data(self):
        self.name_line_edit.clear()
        self.icon_line_edit.clear()
        self.script_text_edit.clear()
        self.hide()

    def openFileDialog(self, event):
        fname, filter = QtWidgets.QFileDialog.getOpenFileName(self, "Explore Icon", filter=("Image Files (*.png *.jpg *.bmp *.jpeg)"))
        if fname != "":
            self.icon_line_edit.setText(fname)

"-----------------------------------------------------------------------------------------------------------------"
"--------------------------------------------------  Menu Item  --------------------------------------------------"
"-----------------------------------------------------------------------------------------------------------------"

class BaseItem(QtWidgets.QFrame):
    def __init__(self, name, toolkit_menu, parent=None):
        super(BaseItem, self).__init__(parent)

        self._name = name
        self.toolkit_menu = toolkit_menu

        self.subs = None # added via submenu class addMenu
        self._hovered = False
        self.hovered_color = "#b37400"
        self.border_color = "#202020"
        self.setObjectName('selectiveFrame')
        self.setStyleSheet('BaseItem#selectiveFrame{border: 1px solid %s}'%self.border_color)

        self.initUI()

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, text):
        self._name = text
        self.name_label.setText(text)
        
    @property
    def hovered(self):
        return self._hovered
    
    @hovered.setter
    def hovered(self, bool):
        self._hovered = bool
        self.paintBorder()

    def initUI(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(5,5,5,5)

        self.name_label = QtWidgets.QLabel(self.name)
        self.name_label.setStyleSheet("background-color: transparent;")

        self.main_layout.addWidget(self.name_label)

    def mousePressEvent(self, event):
        # Dispatch Qt's mousePress event to corresponding function below
        if event.button() == QtCore.Qt.LeftButton:
            self.mouseClickEvent(event)
        elif event.button() == QtCore.Qt.RightButton:
            self.mouseRightClickEvent(event)
        else: super(BaseItem, self).mousePressEvent(event)

    def mouseClickEvent(self, event):
        """ Abstract Method, Override if used """
        pass

    def mouseRightClickEvent(self, event):
        """ Abstract Method, Override if used """
        pass

    def enterEvent(self, event):
        self.hovered = True
        self.paintBorder()

    def leaveEvent(self, event):
        self.hovered = False
        self.paintBorder()

    def paintBorder(self):
        if self.hovered: 
            self.setStyleSheet('BaseItem#selectiveFrame{border: 1px solid %s}'%self.hovered_color)
        else: 
            self.setStyleSheet('BaseItem#selectiveFrame{border: 1px solid %s}'%self.border_color)

class ScriptMenu(BaseItem):
    def __init__(self, toolkit_menu, name, icon, scripts, language="python", parent=None):
        self._icon = icon
        self.scripts = scripts  # only import as string 
        self.language = language
        self.toolkit_menu = toolkit_menu

        self._isModified = False

        super(ScriptMenu, self).__init__(name, toolkit_menu, parent) 
        self.setCursor(QtCore.Qt.PointingHandCursor)

    @property   
    def isModified(self):
        return self._isModified
    
    @isModified.setter
    def isModified(self, bool):
        self._isModified = bool
        try:
            widget_number = self.toolkit_menu.tab_widget.indexOf(self.scriptPageWidget)
            tabBar = self.toolkit_menu.tab_widget.tabBar()
            if bool: tabBar.setTabText(widget_number, self.name+'*')
            else: tabBar.setTabText(widget_number, self.name)
        except: pass

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, path):
        if utils.can_read_image(path):
            self.menu_icon.change_icon(path)
            self._icon = path
        else:
            self.menu_icon.change_icon(utils.get_path("python.png"))
            self._icon = path

    def initUI(self):
        super(ScriptMenu, self).initUI()
        self.main_layout.setContentsMargins(0,0,10,0)

        self.menu_icon = utils.GraphicLabel(self.icon, (48,48), utils.get_path("python.png"))
        self.menu_icon.setMinimumSize(50,50)    # retain the ideal size of item
        self.config_btn = utils.GraphicButton(utils.get_path("cog.png"), self.edit_menu, QtGui.QColor("green"), strength=0.7, size = (18, 18))
        self.inspect_code_btn = utils.GraphicButton(utils.get_path("code.png"), self.inspect_code, QtGui.QColor("orange"), strength=1, size = (18, 18))
        self.config_btn.setContentsMargins(5,0,0,0)

        # Build for script viewing purpose later
        self.code_font = QtGui.QFont('arial', 8)
        self.scriptPageWidget = utils.ScriptTextEdit(self.onModified, self.onSave, self)
        self.scriptPageWidget.textEdit.setFont(self.code_font)    # hmm when set font zoom in and out is enabled, weird

        self.main_layout.insertWidget(0, self.menu_icon)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.inspect_code_btn)
        self.main_layout.addWidget(self.config_btn)

    def onModified(self):
        self.isModified = True

    def onSave(self):
        if self.isModified:
            self.scripts = self.scriptPageWidget.textEdit.toPlainText()
            self.language = self.scriptPageWidget.language_btn_grp.checkedButton().text().lower()
            self.toolkit_menu.save_menu()
            self.isModified = False

    def mouseClickEvent(self, event):
        if self.language == "python":
            cmds.evalDeferred(self.scripts)
        else:
            mel.eval(self.scripts)

    def edit_menu(self, event):
        self.toolkit_menu.script_config_dialog.edit = True
        self.toolkit_menu.script_config_dialog.load_data(self)

    def inspect_code(self, event):
        widget_number = self.toolkit_menu.tab_widget.indexOf(self.scriptPageWidget)
        if widget_number == -1: # -1 means its not present
            self.toolkit_menu.tab_widget.addTab(self.scriptPageWidget, self.name)
            widget_number = self.toolkit_menu.tab_widget.indexOf(self.scriptPageWidget) # reassign again
            self.scriptPageWidget.textEdit.blockSignals(True)    # block signal to prevent modification changed being emitted
            self.scriptPageWidget.textEdit.setPlainText(self.scripts) # put it here instead in init cause I'm afraid it will affect load time
            self.scriptPageWidget.textEdit.blockSignals(False)
            viewer.PythonHighlighter(self.scriptPageWidget.textEdit.document())
            
        self.toolkit_menu.tab_widget.setCurrentIndex(widget_number)

    def paintBorder(self):
        if self.hovered: 
            self.setStyleSheet('BaseItem#selectiveFrame{border: 1px solid %s;background-color:#3E6680}'%self.hovered_color)
        else: 
            self.setStyleSheet('BaseItem#selectiveFrame{border: 1px solid %s}'%self.border_color)

class ScriptSubmenu(BaseItem):
    def __init__(self, toolkit_menu, name, parent=None):
        super(ScriptSubmenu, self).__init__(name, toolkit_menu, parent)
        self.hovered_color = "#376180"
        self.menu = []

    def initUI(self):
        super(ScriptSubmenu, self).initUI()
        self.main_layout.setContentsMargins(0,0,0,5)

        self.menu_list_widget = utils.ExpandableWidget()
        self.menu_list_widget.tab_widget.setStyleSheet("background-color:#232329")  # blue color "#182538"

        self.menu_list_widget.header_layout.insertWidget(0, self.name_label)
        self.menu_list_widget.header_layout.addStretch()
        
        self.main_layout.addWidget(self.menu_list_widget)

    def addMenu(self, menu):
        self.menu_list_widget.add_item(menu)
        self.menu.append(menu)
        if isinstance(menu, BaseItem):
            menu.subs = self
        
# development phase code
if __name__ == "__main__":
    
    try:
        MasterToolkitWindow.close()
        MasterToolkitWindow.deleteLater()
    except:
        pass
    
    MasterToolkitWindow = MasterToolkit()
    MasterToolkitWindow.show()
