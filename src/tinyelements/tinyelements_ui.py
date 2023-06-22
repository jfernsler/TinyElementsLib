from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

import nuke
import os

from tinyelements.tinyelements_helpers import load_element_list, get_dirs
from tinyelements.tinyelements_thumbmaker import generate_thumb

from tinyelements.globals import DEFAULT_THUMB, GLOBAL_DIR, SHOW_DIR

__author__ = "Jeremy Fernsler"
__email__ = "jfernsler@mac.com"
__status__ = "Prototype"

class TinyElements_Library(QWidget):
    """2D Element Library viewer and loader.

    Arguments:
    None.

    Returns:
    None.

    """

    def __init__(self):
        """Init - knob layout and data population.

        Arguments:
        self (object) : self.

        Returns:
        None.

        """
        #super(Panel, self).__init__()
        QWidget.__init__(self)

        self.LIB_DIR = GLOBAL_DIR
        category_list = get_dirs(self.LIB_DIR)
        self.element_list = list()

        self.default_thumb = DEFAULT_THUMB
        preview_sizes = ['None', 'Small', 'Large']

        catalog_list = ['Global Library', 'Show Library']
        load_list = ['Standard', 'Switch', 'Centered', 'Centered Switch', 'Thumb Setup', 'Make Thumbs']

        self.start_frame = int(nuke.root()['first_frame'].value())

        # CREATE KNOBS

        # Category dropdown
        self.category_combo = QComboBox()
        self.category_combo.addItems(category_list)
        self.category_combo.name = 'category drop'
        self.category_combo.setCurrentIndex(0)
        self.category_combo.currentIndexChanged.connect(self.combo_click_handler)
        self.category_combo.show()

        self.catalog_combo = QComboBox()
        self.catalog_combo.addItems(catalog_list)
        self.catalog_combo.name = 'catalog drop'
        self.catalog_combo.setCurrentIndex(0)
        self.catalog_combo.currentIndexChanged.connect(self.combo_click_handler)
        self.catalog_combo.show()

        category_layout = QHBoxLayout()
        category_layout.addWidget(self.category_combo)
        category_layout.addWidget(QLabel('Library:'))
        category_layout.addWidget(self.catalog_combo)
        
        topform_layout = QFormLayout()
        topform_layout.addRow(QLabel('Category:'), category_layout)

        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText('Begin Typing To Search Names')
        self.search_field.textChanged.connect(self.text_field_edit_handler)

        topform_layout.addRow(QLabel('Search Name:'), self.search_field)

        self.get_element_list()

        ### The Element Table
        headers = ['Thumb', 'Element Name']
        self.table = QTableWidget(0, len(headers))
        self.table.cellClicked.connect(self.table_click_handler)
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.populate_table(self.element_list)
        self.table.showGrid()

        table_layout = QHBoxLayout()
        table_layout.addWidget(self.table)

        ### start frame field
        self.frame_field = QLineEdit()
        self.frame_field.setText(str(self.start_frame))
        
        self.reset_button = QPushButton('Reset Frame')
        self.reset_button.clicked.connect(self.click_handler)
        
        self.current_button = QPushButton('Current Frame')
        self.current_button.clicked.connect(self.click_handler)

        startframe_layout = QHBoxLayout()
        startframe_layout.addWidget(self.frame_field)
        startframe_layout.addWidget(self.reset_button)
        startframe_layout.addWidget(self.current_button)

        ### Load options
        self.load_button = QPushButton('Load Element(s)')
        self.load_button.clicked.connect(self.click_handler)

        self.load_combo = QComboBox()
        self.load_combo.addItems(load_list)
        self.load_combo.name = 'load drop'
        self.load_combo.setCurrentIndex(0)
        self.load_combo.show()

        self.copy_box = QCheckBox('Copy To Show')
        self.copy_box.setChecked(False)
        #self.copy_box.setEnabled(False)

        load_layout = QHBoxLayout()
        load_layout.addWidget(self.load_button)
        load_layout.addWidget(self.load_combo)
        load_layout.addWidget(self.copy_box)

        ### Preview
        self.preview_combo = QComboBox()
        self.preview_combo.addItems(preview_sizes)
        self.preview_combo.name = 'preview drop'
        self.preview_combo.setCurrentIndex(0)
        self.preview_combo.currentIndexChanged.connect(self.combo_click_handler)
        self.preview_combo.show()

        self.preview_playcheck = QCheckBox('Play')
        self.preview_playcheck.clicked.connect(self.click_handler)
        self.preview_playcheck.setChecked(False)

        self.gen_thumb_button = QPushButton('Generate Thumb')
        self.gen_thumb_button.clicked.connect(self.click_handler)

        ## stock up layouts
        preview_options_layout = QHBoxLayout()
        preview_options_layout.addWidget(self.preview_combo)
        preview_options_layout.addWidget(self.preview_playcheck)
        preview_options_layout.addWidget(self.gen_thumb_button)

        self.gif_label = QLabel()
        self.gif_label.setMinimumSize(QSize(100,100))
        self.gif_label.setMaximumSize(QSize(100,100))
        self.gif_label.setScaledContents(True)
        self.gif_label.setStyleSheet('border: 1px solid black')
        self.gif_label.installEventFilter(self)

        self.gif_label.hide()

        self.thumb = QMovie(self.default_thumb)
        self.thumb.setCacheMode(QMovie.CacheAll)
        self.gif_label.setMovie(self.thumb)

        preview_layout = QFormLayout()
        preview_layout.addRow(QLabel('Preview:'), preview_options_layout)

        thumb_layout = QHBoxLayout()
        thumb_layout.addStretch()
        thumb_layout.addWidget(self.gif_label)
        thumb_layout.addStretch()

        #Layouts
        master_layout = QVBoxLayout()

        master_layout.addLayout(topform_layout)
        master_layout.addLayout(table_layout)
        master_layout.addLayout(startframe_layout)
        master_layout.addLayout(load_layout)
        master_layout.addLayout(preview_layout)
        master_layout.addLayout(thumb_layout)

        title = "2D Element Catalog"
        self.setMinimumSize(400, 200)
        self.setWindowTitle(title)
        self.setLayout(master_layout)

    def updateValue(self):
        pass

    def search_elements(self, search_text):
        """Match the head of the frag name with search text

            Returns:
            a catalog of matching elements
        """
        table_data = [n for n in self.element_list if search_text.lower() in n.lower()]
        return table_data    

    def current_start_frame(self):
        """Set the start frame to the current frame.

        Arguments:
        self (object) : self.

        Returns:
        none.
        """
        curr_frame = nuke.root()['frame'].getValue()
        self.set_frame_field(curr_frame)

    def reset_start_frame(self):
        """Set the start frame back to 1001.

        Arguments:
        self (object) : self.

        Returns:
        none.
        """
        self.set_frame_field(str(self.start_frame))

    def get_frame_field(self):
        """Set the start frame based on entered value.

        Arguments:
        self (object) : self.

        Returns:
        none.
        """
        frame = self.frame_num.getValue()
        self.set_frame_field(frame)

    def set_frame_field(self, frame):
        """Sets the displayed frame and class start_frame.

        Arguments:
        self (object) : self.
        frame (int) : frame where the element should start

        Returns:
        none.
        """
        self.start_frame = frame
        self.frame_num.setValue(int(frame))

    def eventFilter(self, object, event):
        #print(event.type(), object)
        if event.type() == QEvent.Type.Enter:
            self.thumb.setPaused(True)

        if event.type() == QEvent.Type.Leave:
            self.check_playstate()

        if event.type() == QEvent.Type.MouseMove:
            xpos = event.pos().x()
            label_size = self.gif_label.size().width()
            value = max(0, min(xpos, label_size))
            framecount = self.thumb.frameCount()
            value = int(value/float(label_size) * framecount)
            #print(value, framecount)
            #self.thumb.start()
            self.thumb.jumpToFrame(value)

        return False

    def click_handler(self, data=None):
        """Handle updates to combo boxes and button clicks

        Returns:
        None.
        """
        target = self.sender()  # <<< get the event target, i.e. the button widget
        ui_type = type(target).__name__

        if 'Load' in target.text():
            indexes = self.table.selectionModel().selectedRows()
            load_info=dict()
            elements_to_load = list()
            for index in sorted(indexes):
                row = index.row()
                elements_to_load.append(self.table.item(row,1).text())

            load_info['element_list'] = elements_to_load
            load_info['type'] = self.load_combo.currentText()
            load_info['category'] = self.category_combo.currentText()
            load_info['start_frame'] = int(self.frame_field.text())
            load_info['copy_to'] = self.copy_box.isChecked()
            load_info['global_lib'] = GLOBAL_DIR
            load_info['show_lib'] = SHOW_DIR
            load_info['from_dir'] = self.catalog_combo.currentText()

            load_element_list(load_info)

        if 'Reset' in target.text():
            #self.current_start_frame
            self.frame_field.setText(str(int(nuke.root()['first_frame'].value())))
        
        if 'Current' in target.text():
            self.frame_field.setText(str(nuke.frame()))

        if 'Clear' in target.text():
            self.search_field.clear()

        if 'Play' in target.text():
            self.check_thumbstate()
        
        if 'Thumb' in target.text():
            indexes = self.table.selectionModel().selectedRows()
            element_info=dict()
            elements_to_load = list()
            for index in sorted(indexes):
                row = index.row()
                elements_to_load.append(self.table.item(row,1).text())

            element_info['element_list'] = elements_to_load
            element_info['category'] = self.category_combo.currentText()
            element_info['global_lib'] = GLOBAL_DIR
            element_info['show_lib'] = SHOW_DIR
            element_info['from_dir'] = self.catalog_combo.currentText()

            generate_thumb(element_info)

    def text_field_edit_handler(self, data=None):
        """For live searching the names and passes those right to populate table

        Returns:
        None.
        """
        table_data = self.search_elements(self.search_field.text())
        self.populate_table(table_data)

    def table_click_handler(self, data=None):
        """Handle clicks w/in the table:
            Just row selection at the moment

            Returns:
            None.
        """
        self.table.selectRow(data)
        self.get_current_thumb()

    def get_current_thumb(self):
        indexes = self.table.selectionModel().selectedRows()

        thumb_path = self.default_thumb

        if len(indexes) > 0 and 'None' not in self.preview_combo.currentText():

            row = indexes[-1].row()

            element_name = self.table.item(row,1).text()
            element_type = self.category_combo.currentText()

            t_path = os.path.join(self.LIB_DIR, element_type, element_name, element_name+'.gif')
        
            if os.path.exists(t_path):
                thumb_path = t_path            
        
        self.thumb = QMovie(thumb_path)
        self.gif_label.setMovie(self.thumb)
        self.thumb.setCacheMode(QMovie.CacheAll)
        self.check_thumbstate()

    def combo_click_handler(self, data=None):
        """Handle the combo boxes - just one in here app though

        Returns:
        None.
        """
        target = self.sender()  # <<< get the event target, i.e. the button widget

        if 'category' in target.name:
            self.refresh_listing()
        
        if 'preview' in target.name:
            self.get_current_thumb()
            self.check_thumbstate()

        if 'catalog' in target.name:
            choice = self.catalog_combo.currentText()
            if 'Global' in choice:
                self.switch_catalog(GLOBAL_DIR)
            if 'Show' in choice:
                self.switch_catalog(SHOW_DIR)
            
    def check_thumbstate(self):
        size = self.preview_combo.currentText()
        if 'None' in size:
            self.show_preview(False)
        if 'Small' in size:
            self.set_thumbsize(100)
            self.show_preview(True)
            self.check_playstate()
        if 'Large' in size:
            self.set_thumbsize(256)
            self.show_preview(True)
            self.check_playstate()

        self.gif_label.setMovie(self.thumb)

    def set_thumbsize(self, size):
        self.thumb.start()
        width = self.thumb.currentImage().size().width()
        height = self.thumb.currentImage().size().height() + 0.001

        mult = width/float(height)
        label_width = int(size * mult)
        label_height = size
        
        self.gif_label.setMinimumSize(QSize(label_width,label_height))
        self.gif_label.setMaximumSize(QSize(label_width,label_height))

    def show_preview(self, show):
        if show:
            self.gif_label.show()
        else:
            self.thumb = QMovie(self.default_thumb)
            self.gif_label.hide()
            self.gif_label.setMovie(self.thumb)

    def check_playstate(self):
        if self.preview_playcheck.isChecked():
            self.thumb.start()
        else:
            self.thumb.start()
            self.thumb.setPaused(True)
            self.thumb.jumpToFrame(self.thumb.frameCount()/2)

    def switch_catalog(self, library):
        self.LIB_DIR = library
        self.category_combo.clear()

        if not os.path.exists(self.LIB_DIR):
            self.make_error_table(self.LIB_DIR)
            self.load_button.setEnabled(False)
            return

        self.load_button.setEnabled(True)

        category_list = get_dirs(self.LIB_DIR)
        self.category_combo.addItems(category_list)
        self.category_combo.setCurrentIndex(0)
        self.refresh_listing()

    def refresh_listing(self):
        self.search_field.setText('')
        self.get_element_list()
        self.populate_table(self.element_list)

    def get_element_list(self):
        """Sets the internal full element list to the listing of the currently
            selected category.

        Arguments:
        self (object) : self

        Returns:
        None.
        """
        ## TODO ##
        ## This seems dumb and should probably return this value and should be passed the
        ## category listing.. or could just be collapsed into the combobox handler
        self.element_list = get_dirs(os.path.join(self.LIB_DIR, self.category_combo.currentText()))

    def make_error_table(self, error_path):
        element_list = list()
        element_list.append('No Library Found At:')
        element_list.append(error_path)
        element_list.append('Add some elements there')
        element_list.append('or switch back.')

        table_data = list()
        for element in element_list:
            element_data = dict()
            element_data['name'] = element
            element_data['thumb'] = 'no'
            table_data.append(element_data)

        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        for i, d in enumerate(table_data):
            self.table.insertRow(self.table.rowCount())
            for j, k in enumerate(['thumb', 'name']):
                it = QTableWidgetItem()
                it.setData(Qt.DisplayRole, d[k])
                self.table.setItem(i,j,it)
        self.table.setSortingEnabled(True)
        self.table.show()

    def populate_table(self, element_list):
        """Take a list and fill the table

            Returns:
            None.
        """
        ## TODO ##
        ## Add thumbnail support to this
        cat = self.category_combo.currentText()
        table_data = list()
        for element in element_list:
            element_data = dict()
            element_data['name'] = element
            element_data['thumb'] = 'no'
            thumb_path = os.path.join(self.LIB_DIR, cat, element, element+'.gif')
            if os.path.exists(thumb_path):
                element_data['thumb'] = 'yes'

            table_data.append(element_data)

        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        for i, d in enumerate(table_data):
            self.table.insertRow(self.table.rowCount())
            for j, k in enumerate(['thumb', 'name']):
                it = QTableWidgetItem()
                it.setData(Qt.DisplayRole, d[k])
                self.table.setItem(i,j,it)
        self.table.setSortingEnabled(True)
        self.table.show()
