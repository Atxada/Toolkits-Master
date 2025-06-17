from PySide2 import QtCore,QtWidgets,QtGui,QtSvg

import viewer
import os

APPLICATION_PATH = os.path.dirname(os.path.abspath(__file__))   # current directory exclude file
ICON_PATH = os.path.join(APPLICATION_PATH, 'icons')

SVG_DATA = {
    "cancel":"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#BA4848" class="size-6">
    <path fill-rule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25ZM7.75 7.75a.75.75 0 0 1 1.06 0L12 10.94l3.19-3.19a.75.75 0 0 1 1.06 1.06L13.06 12l3.19 3.19a.75.75 0 0 1-1.06 1.06L12 13.06l-3.19 3.19a.75.75 0 0 1-1.06-1.06L10.94 12 7.75 8.81a.75.75 0 0 1 0-1.06Z" clip-rule="evenodd" />
    </svg>""",
    "no image":"""
    <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#505154">
    <path d="m840-234-80-80v-446H314l-80-80h526q33 0 56.5 23.5T840-760v526ZM792-56l-64-64H200q-33 0-56.5-23.5T120-200v-528l-64-64 56-56 736 736-56 56ZM240-280l120-160 90 120 33-44-283-283v447h447l-80-80H240Zm297-257ZM424-424Z"/>
    </svg>""",
    "save":"""
    <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#dbdbdb">
    <path d="M840-680v480q0 33-23.5 56.5T760-120H200q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h480l160 160Zm-80 34L646-760H200v560h560v-446ZM480-240q50 0 85-35t35-85q0-50-35-85t-85-35q-50 0-85 35t-35 85q0 50 35 85t85 35ZM240-560h360v-160H240v160Zm-40-86v446-560 114Z"/>
    </svg>""",
    "arrow forward":"""
    <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#A3A3A3">
    <path d="M647-440H160v-80h487L423-744l57-56 320 320-320 320-57-56 224-224Z"/>
    </svg>""",
    "arrow back":"""
    <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#A3A3A3">
    <path d="m313-440 224 224-57 56-320-320 320-320 57 56-224 224h487v80H313Z"/>
    </svg>"""
}

def get_path(file="", icon=True):
    path = ICON_PATH
    if not icon: path = APPLICATION_PATH
    path = os.path.join(path, file)
    if os.path.exists(path):
        return path
    else:
        return False

def can_read_image(path):
    validator = QtGui.QImageReader(path)
    if QtGui.QImageReader.canRead(validator):
        return True
    else:
        return False

def render_svg(svg_data):
    byte_array = QtCore.QByteArray(svg_data.encode("utf-8"))
    renderer = QtSvg.QSvgRenderer(byte_array)

    # Create a QPixmap to render into
    size = QtCore.QSize(100, 100)
    pixmap = QtGui.QPixmap(size)
    pixmap.fill(QtCore.Qt.transparent)  # make background transparent

    # Render SVG onto the pixmap
    painter = QtGui.QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return pixmap

def validate_image_path(path, backup=None):  
    if path and can_read_image(path):
        return QtGui.QImage(path)
    elif backup:
        try:
            return QtGui.QImage(backup)
        except Exception as e: 
            print("backup icon not found! #validate_image_path function")
            print(e)
    else:   
        image = render_svg(SVG_DATA["no image"]).toImage()
        return image

class GraphicLabel(QtWidgets.QLabel):
    def __init__(self, icon="", size=(32,32), backup_icon=None, parent=None):
        super(GraphicLabel, self).__init__(parent)

        self.icon = icon
        self.icon_size = size
        self.backup_icon = backup_icon
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)

        self.initUI()

    def initUI(self):
        if not isinstance(self.icon, QtGui.QImage): 
            self.item_image = validate_image_path(self.icon, self.backup_icon)
        else:
            self.item_image = self.icon
        self.item_image = self.item_image.scaled(self.icon_size[0],self.icon_size[1],QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation)
        self.item_pixmap = QtGui.QPixmap()
        self.item_pixmap.convertFromImage(self.item_image)
        self.setPixmap(self.item_pixmap)
        self.setAlignment(QtCore.Qt.AlignCenter)
    
    def change_icon(self, icon, size=None):
        self.icon = icon
        if size: self.icon_size = size

        if not isinstance(self.icon, QtGui.QImage): 
            self.item_image = validate_image_path(self.icon)
        else:
            self.item_image = self.icon

        self.item_image = self.item_image.scaled(self.icon_size[0],self.icon_size[1],QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation)
        self.item_pixmap.convertFromImage(self.item_image)

        self.setPixmap(self.item_pixmap)

class GraphicButton(GraphicLabel):
    def __init__(self, icon="", callback=None, color=QtGui.QColor('silver'), strength=0.25, size=(32,32), parent=None):
        self.callback = []
        if callback: self.callback.append(callback)
        self.color = color
        self.strength = strength
        
        super(GraphicButton, self).__init__(icon, size, parent)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)   # PySide2 need to specify this since graphic effect applied to transparent background
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def initUI(self):
        super(GraphicButton, self).initUI()

        # set highlight mouse hover effect
        self.highlight = QtWidgets.QGraphicsColorizeEffect()
        self.highlight.setColor(self.color)
        self.highlight.setStrength(0.0)
        self.setGraphicsEffect(self.highlight)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            for callback in self.callback: 
                callback(event)

    def enterEvent(self, event):
        self.highlight.setStrength(self.strength)
        self.update()

    def leaveEvent(self, event):
        self.highlight.setStrength(0.0)
        self.update()

class SearchLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(SearchLineEdit, self).__init__(parent)
        self.initUI()
        self.initConnection()

    def initUI(self):
        self.setPlaceholderText(" search...")
        self.setMinimumHeight(30)

        self.cancel_btn = GraphicButton(render_svg(SVG_DATA["cancel"]).toImage(), self.cancelEvent, size=(20,20))
        self.cancel_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.cancel_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.cancel_btn.setVisible(False)

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.addWidget(self.cancel_btn, alignment=QtCore.Qt.AlignRight)
        self.main_layout.setContentsMargins(3,0,5,0)

    def initConnection(self):
        self.textChanged.connect(self.textChangedEvent)

    def cancelEvent(self, event):
        self.setText("")
        self.cancel_btn.setVisible(False)

    def textChangedEvent(self, text):
        if text != "":
            self.cancel_btn.setVisible(True)
        else:
            self.cancel_btn.setVisible(False)

class ScriptTextEdit(QtWidgets.QWidget):
    def __init__(self, modified_callback=None, save_callback=None, parent=None):
        super(ScriptTextEdit, self).__init__(parent=None)

        self.menu = parent
        self.modified_callback = []
        if modified_callback: self.modified_callback.append(modified_callback)
        self.save_callback = []
        if save_callback: self.save_callback.append(save_callback)
        self.initUI()

    def initUI(self):
        # widgets 
        self.language_btn_grp = QtWidgets.QButtonGroup()
        self.python_btn = QtWidgets.QRadioButton("Python")
        self.python_btn.setChecked(True)
        self.mel_btn = QtWidgets.QRadioButton("MEL")

        self.language_btn_grp.addButton(self.python_btn)
        self.language_btn_grp.addButton(self.mel_btn)

        self.find_label = QtWidgets.QLabel("Find")
        self.find_line_edit = QtWidgets.QLineEdit()
        self.find_line_edit.setFocusPolicy(QtCore.Qt.ClickFocus)    # let plain text edit get the focus
        self.find_line_edit.setPlaceholderText("Search...")
        self.find_line_edit.setMaximumWidth(200)
        self.find_next_btn = GraphicButton(render_svg(SVG_DATA["arrow forward"]).toImage(), self.find_next, strength=1, size=(16,16))
        self.find_previous_btn = GraphicButton(render_svg(SVG_DATA["arrow back"]).toImage(), self.find_previous, strength=1, size=(16,16))
      
        self.textEdit = viewer.CodeViewer()
        self.textEdit.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)

        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.setIcon(QtGui.QIcon(render_svg(SVG_DATA["save"])))
        self.save_btn.setStyleSheet("background-color:#0078d4")

        # connection
        self.language_btn_grp.buttonToggled.connect(self.onModified)  
        self.textEdit.modificationChanged.connect(self.onModified)
        self.save_btn.clicked.connect(self.onSave)

        # layouts
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(5,5,5,5)
        self.header_layout = QtWidgets.QHBoxLayout()
        self.header_layout.setContentsMargins(5,0,5,0)

        # organize
        self.header_layout.addWidget(self.python_btn)
        self.header_layout.addWidget(self.mel_btn)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.find_label)
        self.header_layout.addWidget(self.find_line_edit)
        self.header_layout.addWidget(self.find_previous_btn)
        self.header_layout.addWidget(self.find_next_btn)

        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addWidget(self.textEdit)
        self.main_layout.addWidget(self.save_btn)

    def keyPressEvent(self, event):
        super(ScriptTextEdit, self).keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_S and event.modifiers() & QtCore.Qt.ControlModifier:
            self.onSave(event)

    def find_next(self, event=None):
        word = self.find_line_edit.text()
        if word: 
            doc = self.textEdit.document()
            cursor = self.textEdit.textCursor()
            found = doc.find(word, cursor)
            if found.isNull():
                found = doc.find(word, QtGui.QTextCursor(doc))  # wrap around if already at the end
            if not found.isNull():
                self.textEdit.setTextCursor(found)
                self.textEdit.ensureCursorVisible()     # Ensures that the cursor is visible by scrolling the text edit if necessary.

    def find_previous(self, event=None):
        word = self.find_line_edit.text()
        if word: 
            doc = self.textEdit.document()
            cursor = self.textEdit.textCursor()
            found = doc.find(word, cursor, QtGui.QTextDocument.FindBackward)
            if found.isNull():
                end_cursor = QtGui.QTextCursor(doc) 
                end_cursor.movePosition(QtGui.QTextCursor.End) # wrap around from end
                found = doc.find(word, end_cursor, QtGui.QTextDocument.FindBackward)
            if not found.isNull():
                self.textEdit.setTextCursor(found)
                self.textEdit.ensureCursorVisible()

    def onModified(self):
        for callback in self.modified_callback:
            callback()
        self.textEdit.document().setModified(False)

    def onSave(self, event):
        for callback in self.save_callback:
            callback()

class ExpandableWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ExpandableWidget, self).__init__(parent)
        self.initUI()
        self.collapsed = True
    
    def initUI(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)   

        self.tab_widget = QtWidgets.QWidget()
        self.header_layout = QtWidgets.QHBoxLayout(self.tab_widget)
        self.content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20,0,5,0)
        self.content_widget.setVisible(False)

        self.expand_icon = GraphicButton(":teRightArrow.png", self.toggle_detail, size=(16,16), strength=0)
        self.header_layout.addWidget(self.expand_icon)
        
        self.main_layout.addWidget(self.tab_widget)
        self.main_layout.addWidget(self.content_widget)

    def add_item(self, widget):
        self.content_layout.insertWidget(0, widget)

    def remove_widget(self, widget):
        widget.setParent(None)

    def collapse_detail(self, collapse=True):
        self.collapsed = not collapse
        self.toggle_detail(None)

    def toggle_detail(self, event):
        if self.collapsed:
            self.content_widget.setVisible(True)
            self.expand_icon.change_icon(":teDownArrow.png")
            self.collapsed = False
        else:
            self.content_widget.setVisible(False)
            self.expand_icon.change_icon(":teRightArrow.png")
            self.collapsed = True