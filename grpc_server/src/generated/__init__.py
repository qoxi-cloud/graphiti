"""Generated gRPC code from proto files.

Run `make proto` to generate the Python code from proto files.
"""

# These will be populated after running `make proto`
# Import order matters: common_pb2 must be first as other protos depend on it
# ruff: noqa: I001
try:
    from src.generated.graphiti.v1 import common_pb2 as common_pb2  # noqa: F401
    from src.generated.graphiti.v1 import common_pb2_grpc as common_pb2_grpc  # noqa: F401
    from src.generated.graphiti.v1 import nodes_pb2 as nodes_pb2  # noqa: F401
    from src.generated.graphiti.v1 import nodes_pb2_grpc as nodes_pb2_grpc  # noqa: F401
    from src.generated.graphiti.v1 import edges_pb2 as edges_pb2  # noqa: F401
    from src.generated.graphiti.v1 import edges_pb2_grpc as edges_pb2_grpc  # noqa: F401
    from src.generated.graphiti.v1 import search_pb2 as search_pb2  # noqa: F401
    from src.generated.graphiti.v1 import search_pb2_grpc as search_pb2_grpc  # noqa: F401
    from src.generated.graphiti.v1 import ingest_service_pb2 as ingest_service_pb2  # noqa: F401
    from src.generated.graphiti.v1 import ingest_service_pb2_grpc as ingest_service_pb2_grpc  # noqa: F401
    from src.generated.graphiti.v1 import retrieve_service_pb2 as retrieve_service_pb2  # noqa: F401
    from src.generated.graphiti.v1 import retrieve_service_pb2_grpc as retrieve_service_pb2_grpc  # noqa: F401
    from src.generated.graphiti.v1 import admin_service_pb2 as admin_service_pb2  # noqa: F401
    from src.generated.graphiti.v1 import admin_service_pb2_grpc as admin_service_pb2_grpc  # noqa: F401

    __all__ = [
        'common_pb2',
        'common_pb2_grpc',
        'nodes_pb2',
        'nodes_pb2_grpc',
        'edges_pb2',
        'edges_pb2_grpc',
        'search_pb2',
        'search_pb2_grpc',
        'ingest_service_pb2',
        'ingest_service_pb2_grpc',
        'retrieve_service_pb2',
        'retrieve_service_pb2_grpc',
        'admin_service_pb2',
        'admin_service_pb2_grpc',
    ]
except ImportError:
    # Proto files not yet generated
    __all__ = []
