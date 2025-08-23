from burnin.api import BurninClient
from burnin.entity.surreal import Thing
from burnin.entity.node import Node


def get_channel_nodes(shader_node_id: Thing) -> list[Node]:
    burnin_client = BurninClient()
    shader_node: Node  = burnin_client.get_node_by_id(shader_node_id)
    print(shader_node)
    if shader_node.is_node_segments_locked_to_component():
        segments = burnin_client.get_node_segments_from_id(shader_node_id)
        return segments
    else:
        return []