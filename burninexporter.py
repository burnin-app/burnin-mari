import mari
import os
from PySide2 import QtWidgets, QtGui,QtCore
from utils.project import isProjectSuitable
from burnin.api import BurninClient
from burnin.entity.surreal import Thing

os.environ['current_dcc'] = "mari"

gui = PySide2.QtGui
core = PySide2.QtCore
widgets = PySide2.QtWidgets


def populate_channel(channel_list_widget, root_id, node_path):
    print(root_id, node_path)
    shader_node_id = Thing.from_str(f"nodes-{root_id}", node_path)

    try:
        burnin_client = BurninClient()
        print(f"Shader node ID: {shader_node_id}")
        print(f"Root ID: {root_id}")
        print(f"Node path: {node_path}")
        node = burnin_client.get_node_by_id(shader_node_id)
        print(f"Node retrieved: {node}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(f"Full error details: {repr(e)}")
        # If it's an HTTP error, the details should be in the exception message
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        # Also check if it's a requests exception
        if hasattr(e, 'request'):
            print(f"Request URL: {e.request.url}")
            print(f"Request method: {e.request.method}")
            print(f"Request body: {e.request.body}")

class ChannelListItem(QtWidgets.QWidget):
    def __init__(self, channel_node, version_number):
        super(ChannelListItem, self).__init__()

        self.channe_node = channel_node
        self.channel_name = channel_node.node_name
        self.channel_name_la = QtWidgets.QLabel(self.channel_name)

        self.version_number = version_number
        self.version_number_la = QtWidgets.QLabel(self.version_number)

        self.override_res = QtWidgets.QComboBox()
        self.override_res.addItems(["4096", "1080"])

        self.publish_btn = QtWidgets.QPushButton('Export')
        self.publish_btn.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.publish_btn.clicked.connect(self.export)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.channel_name_la)
        layout.addWidget(self.version_number_la)
        layout.addWidget(self.override_res)
        layout.addWidget(self.publish_btn)

        self.setLayout(layout)

    def export(self):
        print("Exporting channel")


def burninExporter():
    if not isProjectSuitable():
        return

    # MAIN WINDOW
    global burnin_exporter_window
    burnin_exporter_window = widgets.QDialog()

    # HEADER
    header_h_layout = widgets.QHBoxLayout()
    node_path = os.getenv("NODE_PATH")

    shader_path_le = QtWidgets.QLineEdit("")
    if node_path:
        shader_path_le.setText(node_path)
    
    # fetch button
    fetch_btn = QtWidgets.QPushButton("Fetch Channels")
    channel_list_widget = QtWidgets.QListWidget()
    root_id = os.getenv("BURNIN_ROOT_ID")
    mari.utils.connect(fetch_btn.clicked, lambda: populate_channel(channel_list_widget, root_id, shader_path_le.text()))

    header_h_layout.addWidget(shader_path_le)
    header_h_layout.addWidget(fetch_btn)

    main_layout = widgets.QVBoxLayout()
    main_layout.addLayout(header_h_layout)
    main_layout.addWidget(channel_list_widget)


    burnin_exporter_window.setLayout(main_layout)
    burnin_exporter_window.setWindowTitle("Burnin Exporter")

    burnin_exporter_window.show()



def __addMenuItem():
    print("Adding menu item")
    mari.menus.addAction(mari.actions.create('Burnin Exporter','burninExporter()'), "MainWindow/Burnin")

__addMenuItem()