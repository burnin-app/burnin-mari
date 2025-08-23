import mari
import os
from pathlib import Path
from PySide2 import QtWidgets, QtGui,QtCore
from utils.project import isProjectSuitable
from burnin.api import BurninClient
from burnin.entity.surreal import Thing
from burnin.entity.node import Node
from burnin.entity.filetype import FileType
from burnin.entity.utils import parse_node_path, TypeWrapper
from burnin.entity.version import Version, VersionStatus
from server import get_channel_nodes

os.environ['current_dcc'] = "mari"

gui = PySide2.QtGui
core = PySide2.QtCore
widgets = PySide2.QtWidgets


def populate_channel(channel_list_widget, root_id, node_path):
    print(root_id, node_path)
    shader_node_id = Thing.from_str(f"nodes-{root_id}", node_path)

    try:
        channel_nodes = get_channel_nodes(shader_node_id)
        
        if channel_nodes:
            channel_list_widget.clear()
            for channel_node in channel_nodes:
                channel_item = QtWidgets.QListWidgetItem()

                channel_item_widget = ChannelListItem(channel_node)
                channel_item.setSizeHint(channel_item_widget.sizeHint())
                channel_item.setData(QtCore.Qt.UserRole, channel_node)

                channel_list_widget.addItem(channel_item)
                channel_list_widget.setItemWidget(channel_item, channel_item_widget)
        else:
            print("No channel nodes found")

    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(f"Full error details: {repr(e)}")

        # clear channel list widget
        channel_list_widget.clear()

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
    def __init__(self, node: Node):
        super(ChannelListItem, self).__init__()

        self.channe_node: Node = node
        self.channel_name = self.channe_node.name
        self.channel_name_la = QtWidgets.QLabel(self.channel_name)

        # self.version_number = version_number
        # self.version_number_la = QtWidgets.QLabel(self.version_number)

        self.override_res = QtWidgets.QComboBox()
        self.override_res.addItems(["4096", "1080"])

        self.publish_btn = QtWidgets.QPushButton('Export')
        self.publish_btn.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.publish_btn.clicked.connect(self.export)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.channel_name_la)
        # layout.addWidget(self.version_number_la)
        layout.addWidget(self.override_res)
        layout.addWidget(self.publish_btn)

        self.setLayout(layout)

    def export(self):
        current_channel = None
        try:
            current_channel = mari.geo.current().channel(self.channel_name)
        except:
            current_channel = None
            print("Channel doesn't exists in Mari")
        
        if current_channel:
            print("Current Channel: ", current_channel)
            root_id = os.getenv("BURNIN_ROOT_ID")
            version_node_id = Thing.from_ids(root_id, self.channe_node.id.get_id() + "/v000")
            version_node = Node.new_version(version_node_id, FileType.Image)
            version_node_type: Version = version_node.node_type.data
            file_type: FileType = version_node_type.file_type.data
            print("FILE TYPE Three: ", file_type)

            burnin_client = BurninClient()
            version_node = burnin_client.create_or_update_component_version(version_node)
            if version_node:
                print(version_node)

                resolution: tuple[int, int] = (current_channel.width(), current_channel.height())
                colorConfig = current_channel.colorspaceConfig()
                print(colorConfig)
                print(dir(colorConfig))

                if "aces" in colorConfig.fileName():
                    color_space = "aces"
                else:
                    color_space = "sRGB"
                
                if colorConfig.scalar():
                    channel_type = "scalar:1"
                else:
                    channel_type = "scalar:0"
                
                version_node_id = version_node.get_node_id_str()
                version_number = version_node_id.split("/")[-1]

                root_path = os.getenv("BURNIN_ROOT_PATH")
                root_name = os.getenv("BURNIN_ROOT_NAME")
                component_path = self.channe_node.id.get_id()
                parsed_component_path = parse_node_path(self.channe_node.id.get_id())

                # Remove leading slash if present (like in other implementations)
                if parsed_component_path.startswith('/'):
                    parsed_component_path = parsed_component_path[1:]
                
                if parsed_component_path.startswith('\\'):
                    parsed_component_path = parsed_component_path[1:]

                path = Path(root_path) / root_name

                file_name = component_path.split("/")[-1] + "_" + color_space + "_" + version_number + ".$UDIM" + ".exr"
                file_path = path / parsed_component_path / version_number
                print(file_path)

                 # EXPORT CHANNEL
                eItem = mari.ExportItem()
                eItem.setSourceNode(current_channel.channelNode())
                eItem.setFileTemplate(file_name)
                mari.exports.addExportItem(eItem, mari.current.geo())
                mari.exports.exportTextures([eItem], str(file_path))

                # update node type data: Version
                version_type: Version = version_node.node_type.data
                version_type.comment = "test"
                version_type.software = "mari"
                version_type.status = VersionStatus.Published
                version_type.head_file = file_name

                # update node type data: FileType
                file_type: FileType = version_type.file_type.data
                print("FILE TYPE: ", file_type)
                file_type.file_name = file_name
                file_type.time_dependent = False
                file_type.frame_range = None
                file_type.resolution = resolution
                file_type.color_space = color_space
                file_type.channel_type = channel_type
                file_type.file_format = "exr"

                version_type.file_type = TypeWrapper(file_type)
                version_node.node_type = TypeWrapper(version_type)
                version_node.created_at = None

                version_node = burnin_client.commit_component_version(version_node)
                version_node_type: Version = version_node.node_type.data
                print(version_node)
                print(version_node_type)

def burninExporter():
    if not isProjectSuitable():
        return

    burnin_client = BurninClient()

    # MAIN WINDOW
    global burnin_exporter_window
    burnin_exporter_window = widgets.QDialog()

    # root list channelBox
    root_list = QtWidgets.QComboBox()
    root_dict = {}
    # add item with data
    for root in burnin_client.roots:
        root_dict[root.name] = root.id['id']['String']
        root_list.addItem(root.name)
    root_list.currentTextChanged.connect(lambda: burnin_client.set_root_env_by_id(root_dict[root_list.currentText()]))

    # select default root by ENV
    if os.getenv("BURNIN_ROOT_NAME"):
        root_list.setCurrentText(os.getenv("BURNIN_ROOT_NAME"))
    else:
        root_list.setCurrentText(root_dict[os.getenv("BURNIN_ROOT_ID")])

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

    header_h_layout.addWidget(root_list)
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