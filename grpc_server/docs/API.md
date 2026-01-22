# Graphiti gRPC API Documentation

## Overview

Graphiti provides a gRPC API for building and querying temporally-aware knowledge graphs. The API is organized into three core services:

1. **IngestService** - Data ingestion and graph building operations
2. **RetrieveService** - Data retrieval, search, and query operations
3. **AdminService** - Administrative operations and maintenance tasks

All services use Protocol Buffers v3 (proto3) and are defined in the `graphiti.v1` package.

### Key Concepts

- **Episodes**: Individual units of content (messages, text, JSON) that are processed to extract entities and relationships
- **Entities (EntityNode)**: Named objects extracted from episodes (people, places, concepts, etc.)
- **Entity Edges**: Relationships between entities with temporal validity tracking
- **Groups**: Logical partitions for multi-tenant support (all data belongs to a group_id)
- **Sagas**: Sequences of related episodes (e.g., conversation threads)
- **Communities**: Clusters of related entities discovered through graph analysis
- **Temporal Tracking**: Bi-temporal model tracking both when facts are created and when they are valid/invalid

---

## IngestService

The IngestService handles all data ingestion operations, transforming raw content into structured knowledge graphs.

### Methods

#### AddEpisode

Add a single episode to the knowledge graph. The system extracts entities, relationships, and attributes from the episode content.

**Request:** `AddEpisodeRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uuid | string | No | Optional UUID for the episode. If not provided, one is generated. |
| group_id | string | Yes | Group identifier for multi-tenant partitioning. |
| name | string | Yes | Human-readable name for the episode. |
| episode_body | string | Yes | The content to process (text, JSON, or message format). |
| reference_time | Timestamp | Yes | Timestamp when the episode occurred. |
| source | EpisodeType | Yes | Type of episode: MESSAGE, JSON, or TEXT. |
| source_description | string | Yes | Description of the episode source. |
| saga | string | No | Optional saga name to link episodes in a sequence. |
| entity_types | Struct | No | Custom entity type definitions (Pydantic-like schemas). |
| update_communities | bool | Yes | Whether to update community detection after ingestion. |
| saga_previous_episode_uuid | string | No | UUID of previous episode in saga (for sequential linking). |
| previous_episode_uuids | []string | No | List of related episode UUIDs. |
| custom_extraction_instructions | string | No | Additional instructions for LLM entity extraction. |

**Response:** `AddEpisodeResponse`

| Field | Type | Description |
|-------|------|-------------|
| episode | EpisodicNode | The created episodic node. |
| nodes | []EntityNode | Entities extracted from the episode. |
| edges | []EntityEdge | Relationships extracted between entities. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_id": "user_123",
  "name": "Team Meeting Notes",
  "episode_body": "Alice discussed the new feature with Bob. They decided to launch next week.",
  "reference_time": "2026-01-22T10:00:00Z",
  "source": "EPISODE_TYPE_TEXT",
  "source_description": "Meeting notes from standup",
  "update_communities": false
}' localhost:50051 graphiti.v1.IngestService/AddEpisode
```

---

#### AddEpisodeBulk

Add multiple episodes with progress streaming. Ideal for batch imports.

**Request:** `AddEpisodeBulkRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| episodes | []AddEpisodeRequest | Yes | Array of episodes to add. |

**Response Stream:** `AddEpisodeBulkProgress`

| Field | Type | Description |
|-------|------|-------------|
| total | int32 | Total number of episodes to process. |
| completed | int32 | Number successfully completed. |
| failed | int32 | Number that failed. |
| current_uuid | string | UUID of currently processing episode. |
| error_message | string | Error message if current episode failed. |
| is_complete | bool | True when all episodes processed. |
| results | []AddEpisodeResponse | Completed episode results. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "episodes": [
    {
      "group_id": "user_123",
      "name": "Episode 1",
      "episode_body": "Content 1",
      "reference_time": "2026-01-22T10:00:00Z",
      "source": "EPISODE_TYPE_TEXT",
      "source_description": "Import batch 1",
      "update_communities": false
    },
    {
      "group_id": "user_123",
      "name": "Episode 2",
      "episode_body": "Content 2",
      "reference_time": "2026-01-22T11:00:00Z",
      "source": "EPISODE_TYPE_TEXT",
      "source_description": "Import batch 1",
      "update_communities": false
    }
  ]
}' localhost:50051 graphiti.v1.IngestService/AddEpisodeBulk
```

---

#### AddMessages

Add chat/conversation messages for processing. Messages are queued and processed asynchronously.

**Request:** `AddMessagesRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_id | string | Yes | Group identifier. |
| messages | []Message | Yes | Array of conversation messages. |

**Message Structure:**

| Field | Type | Description |
|-------|------|-------------|
| uuid | string | Unique message identifier. |
| name | string | Sender name. |
| role | string | Sender role (user, assistant, system). |
| role_type | string | Additional role type classification. |
| content | string | Message content. |
| timestamp | Timestamp | When the message was sent. |
| source_description | string | Description of message source. |

**Response:** `AddMessagesResponse`

| Field | Type | Description |
|-------|------|-------------|
| result | OperationResult | Operation success/failure status. |
| queued_count | int32 | Number of messages queued for processing. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_id": "user_123",
  "messages": [
    {
      "uuid": "msg_1",
      "name": "Alice",
      "role": "user",
      "role_type": "human",
      "content": "What is the status of project X?",
      "timestamp": "2026-01-22T10:00:00Z",
      "source_description": "Slack message"
    },
    {
      "uuid": "msg_2",
      "name": "Bob",
      "role": "user",
      "role_type": "human",
      "content": "Project X is 80% complete",
      "timestamp": "2026-01-22T10:01:00Z",
      "source_description": "Slack message"
    }
  ]
}' localhost:50051 graphiti.v1.IngestService/AddMessages
```

---

#### AddEntityNode

Directly add an entity node without episode processing. Useful for pre-known entities.

**Request:** `AddEntityNodeRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uuid | string | No | Optional UUID. Generated if not provided. |
| group_id | string | Yes | Group identifier. |
| name | string | Yes | Entity name. |
| summary | string | No | Optional entity summary/description. |
| labels | []string | Yes | Entity type labels (e.g., ["Person"], ["Organization"]). |
| attributes | Struct | No | Additional structured attributes. |

**Response:** `EntityNode`

Returns the created entity node with all fields populated.

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_id": "user_123",
  "name": "Alice Johnson",
  "summary": "Senior Software Engineer",
  "labels": ["Person", "Employee"],
  "attributes": {
    "department": "Engineering",
    "years_experience": 8
  }
}' localhost:50051 graphiti.v1.IngestService/AddEntityNode
```

---

#### AddTriplet

Add a subject-predicate-object relationship directly to the graph.

**Request:** `AddTripletRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_id | string | Yes | Group identifier. |
| subject_name | string | Yes | Name of the subject entity. |
| predicate | string | Yes | Relationship type/name. |
| object_name | string | Yes | Name of the object entity. |
| subject_uuid | string | No | UUID of existing subject entity (creates new if not provided). |
| object_uuid | string | No | UUID of existing object entity (creates new if not provided). |
| valid_at | Timestamp | No | When the relationship became valid. |
| invalid_at | Timestamp | No | When the relationship became invalid. |

**Response:** `AddTripletResponse`

| Field | Type | Description |
|-------|------|-------------|
| subject_node | EntityNode | Subject entity (created or existing). |
| object_node | EntityNode | Object entity (created or existing). |
| edge | EntityEdge | The relationship edge. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_id": "user_123",
  "subject_name": "Alice",
  "predicate": "works_with",
  "object_name": "Bob",
  "valid_at": "2026-01-01T00:00:00Z"
}' localhost:50051 graphiti.v1.IngestService/AddTriplet
```

---

#### StreamEpisodes

Bidirectional streaming for continuous episode ingestion with real-time responses.

**Request Stream:** `StreamEpisodeRequest`

| Field | Type | Description |
|-------|------|-------------|
| episode | AddEpisodeRequest | Episode to add. |
| correlation_id | string | Optional ID to correlate request with response. |

**Response Stream:** `StreamEpisodeResponse`

| Field | Type | Description |
|-------|------|-------------|
| correlation_id | string | Matches request correlation_id. |
| success | AddEpisodeResponse | Result on success (oneof). |
| error | string | Error message on failure (oneof). |

**Example:**

This method requires a bidirectional streaming client. See the gRPC client libraries for your language.

---

## RetrieveService

The RetrieveService provides flexible querying and retrieval of graph data with hybrid search capabilities.

### Methods

#### Search

Simple search returning facts (relationships) relevant to a query.

**Request:** `SearchRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_ids | []string | Yes | Groups to search within. |
| query | string | Yes | Natural language search query. |
| max_facts | int32 | No | Maximum number of facts to return (default: 10). |

**Response:** `SearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| facts | []FactResult | Relevant relationship facts. |

**FactResult Structure:**

| Field | Type | Description |
|-------|------|-------------|
| uuid | string | Fact UUID. |
| name | string | Relationship name. |
| fact | string | Natural language fact description. |
| valid_at | Timestamp | When fact became valid. |
| invalid_at | Timestamp | When fact became invalid. |
| created_at | Timestamp | When fact was created. |
| expired_at | Timestamp | When fact expired. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "query": "What does Alice work on?",
  "max_facts": 5
}' localhost:50051 graphiti.v1.RetrieveService/Search
```

---

#### AdvancedSearch

Advanced search with full configuration for search methods, reranking, and filtering.

**Request:** `AdvancedSearchRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_ids | []string | Yes | Groups to search within. |
| query | string | Yes | Search query. |
| config | SearchConfig | No | Search algorithm configuration. |
| filters | SearchFilters | No | Temporal and attribute filters. |
| center_node_uuids | []string | No | UUIDs of central nodes to search around. |

**SearchConfig Structure:**

Configures search algorithms for each graph element type.

| Field | Type | Description |
|-------|------|-------------|
| edge_config | EdgeSearchConfig | Edge search configuration. |
| node_config | NodeSearchConfig | Node search configuration. |
| episode_config | EpisodeSearchConfig | Episode search configuration. |
| community_config | CommunitySearchConfig | Community search configuration. |
| limit | int32 | Global result limit. |
| reranker_min_score | double | Minimum reranker score threshold. |

**EdgeSearchConfig:**

| Field | Description |
|-------|-------------|
| search_methods | Array of methods: COSINE_SIMILARITY, BM25, BFS |
| reranker | Reranking algorithm: RRF, NODE_DISTANCE, EPISODE_MENTIONS, MMR, CROSS_ENCODER |
| sim_min_score | Minimum similarity score (0-1) |
| mmr_lambda | MMR diversity parameter (0-1) |
| bfs_max_depth | Maximum BFS traversal depth |

**SearchFilters Structure:**

| Field | Type | Description |
|-------|------|-------------|
| node_labels | []string | Filter by entity labels. |
| edge_types | []string | Filter by relationship types. |
| valid_at | []DateFilterGroup | Filter by valid_at timestamp. |
| invalid_at | []DateFilterGroup | Filter by invalid_at timestamp. |
| created_at | []DateFilterGroup | Filter by created_at timestamp. |
| expired_at | []DateFilterGroup | Filter by expired_at timestamp. |
| edge_uuids | []string | Filter by specific edge UUIDs. |
| property_filters | []PropertyFilter | Filter by node/edge attributes. |

**DateFilterGroup:**

Groups of date filters with AND logic within group, OR logic between groups.

```protobuf
message DateFilterGroup {
  repeated DateFilter filters = 1;
}

message DateFilter {
  optional Timestamp date = 1;
  ComparisonOperator comparison_operator = 2;
}
```

**Comparison Operators:**
- EQUALS, NOT_EQUALS
- GREATER_THAN, LESS_THAN
- GREATER_THAN_EQUAL, LESS_THAN_EQUAL
- IS_NULL, IS_NOT_NULL

**Response:** `SearchResults`

| Field | Type | Description |
|-------|------|-------------|
| edges | []EntityEdge | Matching edges with full details. |
| edge_reranker_scores | []double | Scores for each edge. |
| nodes | []EntityNode | Matching nodes. |
| node_reranker_scores | []double | Scores for each node. |
| episodes | []EpisodicNode | Matching episodes. |
| episode_reranker_scores | []double | Scores for each episode. |
| communities | []CommunityNode | Matching communities. |
| community_reranker_scores | []double | Scores for each community. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "query": "engineering projects",
  "config": {
    "edge_config": {
      "search_methods": ["EDGE_SEARCH_METHOD_COSINE_SIMILARITY", "EDGE_SEARCH_METHOD_BM25"],
      "reranker": "EDGE_RERANKER_RRF",
      "sim_min_score": 0.7
    },
    "limit": 20
  },
  "filters": {
    "node_labels": ["Project", "Task"],
    "created_at": [
      {
        "filters": [
          {
            "date": "2026-01-01T00:00:00Z",
            "comparison_operator": "COMPARISON_OPERATOR_GREATER_THAN"
          }
        ]
      }
    ]
  }
}' localhost:50051 graphiti.v1.RetrieveService/AdvancedSearch
```

---

#### StreamSearch

Streaming search for large result sets. Results are sent incrementally.

**Request:** `SearchRequest`

**Response Stream:** `SearchResultChunk`

| Field | Type | Description |
|-------|------|-------------|
| edge | EntityEdge | Edge result (oneof). |
| node | EntityNode | Node result (oneof). |
| episode | EpisodicNode | Episode result (oneof). |
| community | CommunityNode | Community result (oneof). |
| fact | FactResult | Fact result (oneof). |
| score | double | Relevance score. |
| is_last | bool | True for last chunk. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "query": "all engineering activities",
  "max_facts": 100
}' localhost:50051 graphiti.v1.RetrieveService/StreamSearch
```

---

#### GetEntityEdge

Retrieve a specific entity edge by UUID.

**Request:** `GetEntityEdgeRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uuid | string | Yes | UUID of the entity edge. |

**Response:** `EntityEdge`

**Example:**

```bash
grpcurl -plaintext -d '{
  "uuid": "edge_uuid_123"
}' localhost:50051 graphiti.v1.RetrieveService/GetEntityEdge
```

---

#### GetEntityEdges

Retrieve multiple entity edges by UUIDs.

**Request:** `GetEntityEdgesRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uuids | []string | Yes | Array of edge UUIDs. |

**Response:** `GetEntityEdgesResponse`

| Field | Type | Description |
|-------|------|-------------|
| edges | []EntityEdge | Retrieved edges. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "uuids": ["edge_uuid_1", "edge_uuid_2", "edge_uuid_3"]
}' localhost:50051 graphiti.v1.RetrieveService/GetEntityEdges
```

---

#### GetEpisodes

Retrieve episodes for a group with pagination.

**Request:** `GetEpisodesRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_id | string | Yes | Group identifier. |
| last_n | int32 | No | Return last N episodes. |
| reference_time | Timestamp | No | Reference time for temporal filtering. |
| pagination | PaginationCursor | No | Pagination cursor. |

**PaginationCursor:**

| Field | Type | Description |
|-------|------|-------------|
| uuid_cursor | string | UUID to start after. |
| limit | int32 | Page size limit. |

**Response:** `GetEpisodesResponse`

| Field | Type | Description |
|-------|------|-------------|
| episodes | []EpisodicNode | Retrieved episodes. |
| next_cursor | string | Cursor for next page (null if last page). |

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_id": "user_123",
  "last_n": 10
}' localhost:50051 graphiti.v1.RetrieveService/GetEpisodes
```

---

#### RetrieveEpisodes

Streaming retrieval of episodes with filtering. Returns episodes as they are found.

**Request:** `RetrieveEpisodesRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_ids | []string | Yes | Groups to retrieve from. |
| reference_time | Timestamp | Yes | Reference time for filtering. |
| last_n | int32 | Yes | Number of episodes to retrieve. |
| source | EpisodeType | No | Filter by episode type. |
| saga | string | No | Filter by saga name. |

**Response Stream:** `EpisodicNode`

Streams episodes one at a time.

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "reference_time": "2026-01-22T12:00:00Z",
  "last_n": 50,
  "source": "EPISODE_TYPE_MESSAGE"
}' localhost:50051 graphiti.v1.RetrieveService/RetrieveEpisodes
```

---

#### GetMemory

Contextual retrieval based on conversation messages. Returns relevant facts for the conversation context.

**Request:** `GetMemoryRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_id | string | Yes | Group identifier. |
| max_facts | int32 | No | Maximum facts to return. |
| center_node_uuid | string | No | Optional central entity for focused retrieval. |
| messages | []Message | Yes | Conversation messages for context. |

**Response:** `GetMemoryResponse`

| Field | Type | Description |
|-------|------|-------------|
| facts | []FactResult | Relevant facts for the conversation. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_id": "user_123",
  "max_facts": 10,
  "messages": [
    {
      "uuid": "msg_1",
      "name": "User",
      "role": "user",
      "role_type": "human",
      "content": "Tell me about the Q4 project status",
      "timestamp": "2026-01-22T10:00:00Z",
      "source_description": "Chat"
    }
  ]
}' localhost:50051 graphiti.v1.RetrieveService/GetMemory
```

---

#### GetEntityNode

Retrieve a specific entity node by UUID.

**Request:** `GetEntityNodeRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uuid | string | Yes | Entity node UUID. |

**Response:** `EntityNode`

**Example:**

```bash
grpcurl -plaintext -d '{
  "uuid": "entity_uuid_123"
}' localhost:50051 graphiti.v1.RetrieveService/GetEntityNode
```

---

#### GetEntityNodes

Retrieve entity nodes by group with pagination.

**Request:** `GetEntityNodesRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_ids | []string | Yes | Groups to retrieve from. |
| pagination | PaginationCursor | No | Pagination cursor. |

**Response:** `GetEntityNodesResponse`

| Field | Type | Description |
|-------|------|-------------|
| nodes | []EntityNode | Retrieved entity nodes. |
| next_cursor | string | Cursor for next page. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "pagination": {
    "limit": 50
  }
}' localhost:50051 graphiti.v1.RetrieveService/GetEntityNodes
```

---

#### GetCommunities

Retrieve community nodes by group with pagination.

**Request:** `GetCommunitiesRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_ids | []string | Yes | Groups to retrieve from. |
| pagination | PaginationCursor | No | Pagination cursor. |

**Response:** `GetCommunitiesResponse`

| Field | Type | Description |
|-------|------|-------------|
| communities | []CommunityNode | Retrieved communities. |
| next_cursor | string | Cursor for next page. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "pagination": {
    "limit": 20
  }
}' localhost:50051 graphiti.v1.RetrieveService/GetCommunities
```

---

#### GetNodesByEpisodes

Retrieve all nodes and edges associated with specific episodes.

**Request:** `GetNodesByEpisodesRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| episode_uuids | []string | Yes | Episode UUIDs. |

**Response:** `GetNodesByEpisodesResponse`

| Field | Type | Description |
|-------|------|-------------|
| nodes | []EntityNode | Entities from episodes. |
| edges | []EntityEdge | Relationships from episodes. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "episode_uuids": ["episode_uuid_1", "episode_uuid_2"]
}' localhost:50051 graphiti.v1.RetrieveService/GetNodesByEpisodes
```

---

#### SearchNodes

Search for entity nodes by query and optional entity type filtering.

**Request:** `SearchNodesRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | Yes | Search query. |
| group_ids | []string | Yes | Groups to search. |
| max_nodes | int32 | No | Maximum nodes to return. |
| entity_types | []string | No | Filter by entity type labels. |

**Response:** `SearchNodesResponse`

| Field | Type | Description |
|-------|------|-------------|
| nodes | []EntityNode | Matching entity nodes. |
| message | string | Status or info message. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "query": "senior engineers",
  "group_ids": ["user_123"],
  "max_nodes": 10,
  "entity_types": ["Person", "Employee"]
}' localhost:50051 graphiti.v1.RetrieveService/SearchNodes
```

---

#### SearchFacts

Search for relationship facts with optional center node focusing.

**Request:** `SearchFactsRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | Yes | Search query. |
| group_ids | []string | Yes | Groups to search. |
| max_facts | int32 | No | Maximum facts to return. |
| center_node_uuid | string | No | UUID of central node to focus search. |

**Response:** `SearchFactsResponse`

| Field | Type | Description |
|-------|------|-------------|
| facts | []FactResult | Matching facts. |
| message | string | Status or info message. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "query": "project deadlines",
  "group_ids": ["user_123"],
  "max_facts": 15
}' localhost:50051 graphiti.v1.RetrieveService/SearchFacts
```

---

## AdminService

The AdminService provides administrative operations for managing the knowledge graph.

### Methods

#### HealthCheck

Check if the service is healthy and responding.

**Request:** `HealthCheckRequest` (empty)

**Response:** `HealthCheckResponse`

| Field | Type | Description |
|-------|------|-------------|
| status | ServingStatus | SERVING, NOT_SERVING, or UNSPECIFIED. |
| message | string | Health status message. |

**Example:**

```bash
grpcurl -plaintext -d '{}' localhost:50051 graphiti.v1.AdminService/HealthCheck
```

---

#### GetStatus

Get detailed server status including versions and provider information.

**Request:** `GetStatusRequest` (empty)

**Response:** `GetStatusResponse`

| Field | Type | Description |
|-------|------|-------------|
| version | string | Graphiti version. |
| database_provider | string | Database backend (Neo4j, FalkorDB, Kuzu, Neptune). |
| llm_provider | string | LLM provider name. |
| embedder_provider | string | Embedding provider name. |
| database_connected | bool | Database connection status. |
| uptime_seconds | int64 | Server uptime in seconds. |

**Example:**

```bash
grpcurl -plaintext -d '{}' localhost:50051 graphiti.v1.AdminService/GetStatus
```

---

#### DeleteEntityEdge

Delete a specific entity edge by UUID.

**Request:** `DeleteEntityEdgeRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uuid | string | Yes | UUID of edge to delete. |

**Response:** `OperationResult`

| Field | Type | Description |
|-------|------|-------------|
| success | bool | Whether operation succeeded. |
| message | string | Result message. |
| error_code | string | Error code if failed. |
| error_details | string | Detailed error information. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "uuid": "edge_uuid_123"
}' localhost:50051 graphiti.v1.AdminService/DeleteEntityEdge
```

---

#### DeleteEntityEdges

Delete multiple entity edges by UUIDs.

**Request:** `DeleteEntityEdgesRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uuids | []string | Yes | UUIDs of edges to delete. |

**Response:** `OperationResult`

**Example:**

```bash
grpcurl -plaintext -d '{
  "uuids": ["edge_uuid_1", "edge_uuid_2", "edge_uuid_3"]
}' localhost:50051 graphiti.v1.AdminService/DeleteEntityEdges
```

---

#### DeleteGroup

Delete an entire group and all associated data (episodes, nodes, edges).

**WARNING:** This is a destructive operation that cannot be undone.

**Request:** `DeleteGroupRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_id | string | Yes | Group identifier to delete. |

**Response:** `OperationResult`

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_id": "user_123"
}' localhost:50051 graphiti.v1.AdminService/DeleteGroup
```

---

#### DeleteEpisode

Delete a specific episode by UUID.

**Request:** `DeleteEpisodeRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uuid | string | Yes | Episode UUID to delete. |

**Response:** `OperationResult`

**Example:**

```bash
grpcurl -plaintext -d '{
  "uuid": "episode_uuid_123"
}' localhost:50051 graphiti.v1.AdminService/DeleteEpisode
```

---

#### DeleteEpisodes

Delete multiple episodes by UUIDs.

**Request:** `DeleteEpisodesRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uuids | []string | Yes | Episode UUIDs to delete. |

**Response:** `OperationResult`

**Example:**

```bash
grpcurl -plaintext -d '{
  "uuids": ["episode_uuid_1", "episode_uuid_2"]
}' localhost:50051 graphiti.v1.AdminService/DeleteEpisodes
```

---

#### DeleteEntityNode

Delete a specific entity node by UUID.

**Request:** `DeleteEntityNodeRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uuid | string | Yes | Entity node UUID to delete. |

**Response:** `OperationResult`

**Example:**

```bash
grpcurl -plaintext -d '{
  "uuid": "entity_uuid_123"
}' localhost:50051 graphiti.v1.AdminService/DeleteEntityNode
```

---

#### ClearData

Clear all data from the graph database.

**WARNING:** This is a destructive operation that deletes ALL data.

**Request:** `ClearDataRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| confirm | bool | Yes | Must be true to confirm deletion. |

**Response:** `OperationResult`

**Example:**

```bash
grpcurl -plaintext -d '{
  "confirm": true
}' localhost:50051 graphiti.v1.AdminService/ClearData
```

---

#### BuildIndices

Build or rebuild database indices and constraints for optimal performance.

**Request:** `BuildIndicesRequest` (empty)

**Response:** `OperationResult`

**Example:**

```bash
grpcurl -plaintext -d '{}' localhost:50051 graphiti.v1.AdminService/BuildIndices
```

---

#### RemoveEpisode

Remove an episode and clean up orphaned nodes and edges that are no longer referenced.

**Request:** `RemoveEpisodeRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uuid | string | Yes | Episode UUID to remove. |

**Response:** `RemoveEpisodeResponse`

| Field | Type | Description |
|-------|------|-------------|
| result | OperationResult | Operation result. |
| orphaned_nodes_removed | int32 | Count of orphaned nodes deleted. |
| orphaned_edges_removed | int32 | Count of orphaned edges deleted. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "uuid": "episode_uuid_123"
}' localhost:50051 graphiti.v1.AdminService/RemoveEpisode
```

---

#### BuildCommunities

Run community detection algorithm on specified groups to identify entity clusters.

**Request:** `BuildCommunitiesRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| group_ids | []string | Yes | Groups to build communities for. |

**Response:** `BuildCommunitiesResponse`

| Field | Type | Description |
|-------|------|-------------|
| communities | []CommunityNode | Created community nodes. |
| total_created | int32 | Total number of communities created. |

**Example:**

```bash
grpcurl -plaintext -d '{
  "group_ids": ["user_123"]
}' localhost:50051 graphiti.v1.AdminService/BuildCommunities
```

---

## Data Types

### Node Types

#### EntityNode

Represents an entity extracted from episodes (people, places, concepts, etc.).

| Field | Type | Description |
|-------|------|-------------|
| uuid | string | Unique identifier. |
| name | string | Entity name. |
| group_id | string | Group this entity belongs to. |
| labels | []string | Entity type labels (e.g., ["Person", "Employee"]). |
| created_at | Timestamp | When entity was first created. |
| summary | string | Natural language summary of entity. |
| attributes | Struct | Structured attributes (JSON-like). |

Note: Embeddings (name_embedding) are generated server-side and not exposed via gRPC.

---

#### EpisodicNode

Represents an episode (unit of content) that has been processed.

| Field | Type | Description |
|-------|------|-------------|
| uuid | string | Unique identifier. |
| name | string | Episode name. |
| group_id | string | Group identifier. |
| labels | []string | Node labels. |
| created_at | Timestamp | When episode was created. |
| source | EpisodeType | Episode type (MESSAGE, JSON, TEXT). |
| source_description | string | Description of source. |
| content | string | Episode content. |
| valid_at | Timestamp | Reference time when episode occurred. |
| entity_edges | []string | UUIDs of edges to entities. |

---

#### CommunityNode

Represents a cluster of related entities discovered through community detection.

| Field | Type | Description |
|-------|------|-------------|
| uuid | string | Unique identifier. |
| name | string | Community name. |
| group_id | string | Group identifier. |
| labels | []string | Node labels. |
| created_at | Timestamp | When community was created. |
| summary | string | Summary of community theme. |

---

#### SagaNode

Represents a sequence or thread of related episodes.

| Field | Type | Description |
|-------|------|-------------|
| uuid | string | Unique identifier. |
| name | string | Saga name. |
| group_id | string | Group identifier. |
| labels | []string | Node labels. |
| created_at | Timestamp | When saga was created. |

---

### Edge Types

#### EntityEdge

Represents a relationship between two entities with temporal tracking.

| Field | Type | Description |
|-------|------|-------------|
| uuid | string | Unique identifier. |
| group_id | string | Group identifier. |
| source_node_uuid | string | UUID of source entity. |
| target_node_uuid | string | UUID of target entity. |
| created_at | Timestamp | When edge was created. |
| name | string | Relationship type/name. |
| fact | string | Natural language fact description. |
| episodes | []string | Episode UUIDs that mention this fact. |
| expired_at | Timestamp | When edge was superseded by newer information. |
| valid_at | Timestamp | When relationship became valid (fact occurrence time). |
| invalid_at | Timestamp | When relationship became invalid. |
| attributes | Struct | Additional structured attributes. |

Note: Embeddings (fact_embedding) are generated server-side and not exposed via gRPC.

---

#### EpisodicEdge

Connects episodes to entities they mention.

| Field | Type | Description |
|-------|------|-------------|
| uuid | string | Unique identifier. |
| group_id | string | Group identifier. |
| source_node_uuid | string | UUID of episode. |
| target_node_uuid | string | UUID of entity. |
| created_at | Timestamp | When edge was created. |

---

#### CommunityEdge

Connects communities to their member entities.

| Field | Type | Description |
|-------|------|-------------|
| uuid | string | Unique identifier. |
| group_id | string | Group identifier. |
| source_node_uuid | string | UUID of community. |
| target_node_uuid | string | UUID of entity. |
| created_at | Timestamp | When edge was created. |

---

#### HasEpisodeEdge

Connects sagas to their episodes.

| Field | Type | Description |
|-------|------|-------------|
| uuid | string | Unique identifier. |
| group_id | string | Group identifier. |
| source_node_uuid | string | UUID of saga. |
| target_node_uuid | string | UUID of episode. |
| created_at | Timestamp | When edge was created. |

---

#### NextEpisodeEdge

Connects sequential episodes in a saga or conversation.

| Field | Type | Description |
|-------|------|-------------|
| uuid | string | Unique identifier. |
| group_id | string | Group identifier. |
| source_node_uuid | string | UUID of current episode. |
| target_node_uuid | string | UUID of next episode. |
| created_at | Timestamp | When edge was created. |

---

## Common Patterns and Best Practices

### Multi-Tenant Support with Groups

Always use `group_id` to partition data for different users or tenants:

```bash
# User 1's data
grpcurl -plaintext -d '{
  "group_id": "user_1",
  "name": "Episode 1",
  ...
}' localhost:50051 graphiti.v1.IngestService/AddEpisode

# User 2's data (isolated from User 1)
grpcurl -plaintext -d '{
  "group_id": "user_2",
  "name": "Episode 1",
  ...
}' localhost:50051 graphiti.v1.IngestService/AddEpisode
```

---

### Temporal Awareness

Graphiti tracks two temporal dimensions:

1. **Created At**: When the data was added to the graph (system time)
2. **Valid At / Invalid At**: When the fact actually occurred or was true (event time)

Example with temporal validity:

```bash
grpcurl -plaintext -d '{
  "group_id": "user_123",
  "subject_name": "Alice",
  "predicate": "works_at",
  "object_name": "Acme Corp",
  "valid_at": "2020-01-01T00:00:00Z",
  "invalid_at": "2025-06-01T00:00:00Z"
}' localhost:50051 graphiti.v1.IngestService/AddTriplet
```

---

### Episode Sequences with Sagas

Link related episodes into sequences (conversations, document chapters, etc.):

```bash
# First episode in saga
grpcurl -plaintext -d '{
  "group_id": "user_123",
  "name": "Meeting Start",
  "episode_body": "Meeting started at 10am",
  "reference_time": "2026-01-22T10:00:00Z",
  "source": "EPISODE_TYPE_TEXT",
  "source_description": "Meeting notes",
  "saga": "team_meeting_jan_22",
  "update_communities": false
}' localhost:50051 graphiti.v1.IngestService/AddEpisode

# Second episode in same saga
grpcurl -plaintext -d '{
  "group_id": "user_123",
  "name": "Meeting Discussion",
  "episode_body": "Discussed Q1 goals",
  "reference_time": "2026-01-22T10:15:00Z",
  "source": "EPISODE_TYPE_TEXT",
  "source_description": "Meeting notes",
  "saga": "team_meeting_jan_22",
  "saga_previous_episode_uuid": "<uuid_from_first_episode>",
  "update_communities": false
}' localhost:50051 graphiti.v1.IngestService/AddEpisode
```

---

### Custom Entity Types

Provide custom entity type schemas for domain-specific extraction:

```bash
grpcurl -plaintext -d '{
  "group_id": "user_123",
  "name": "Product Requirements",
  "episode_body": "We need a user authentication system with 2FA",
  "reference_time": "2026-01-22T10:00:00Z",
  "source": "EPISODE_TYPE_TEXT",
  "source_description": "Requirements doc",
  "entity_types": {
    "Feature": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        "complexity": {"type": "string"}
      }
    },
    "Technology": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "category": {"type": "string"}
      }
    }
  },
  "update_communities": false
}' localhost:50051 graphiti.v1.IngestService/AddEpisode
```

---

### Hybrid Search Strategies

Combine multiple search methods for best recall and precision:

**Cosine Similarity**: Best for semantic/conceptual similarity
**BM25**: Best for keyword matching and exact terms
**BFS**: Best for graph traversal from known nodes

Example combining all three:

```bash
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "query": "machine learning projects",
  "config": {
    "edge_config": {
      "search_methods": [
        "EDGE_SEARCH_METHOD_COSINE_SIMILARITY",
        "EDGE_SEARCH_METHOD_BM25",
        "EDGE_SEARCH_METHOD_BFS"
      ],
      "reranker": "EDGE_RERANKER_RRF",
      "sim_min_score": 0.6
    },
    "limit": 30
  },
  "center_node_uuids": ["<node_uuid_for_ml_team>"]
}' localhost:50051 graphiti.v1.RetrieveService/AdvancedSearch
```

---

### Reranking Strategies

Choose reranker based on your requirements:

- **RRF (Reciprocal Rank Fusion)**: Combine results from multiple search methods
- **NODE_DISTANCE**: Prioritize results closer to center nodes
- **EPISODE_MENTIONS**: Prioritize facts mentioned in more episodes
- **MMR (Maximal Marginal Relevance)**: Balance relevance with diversity
- **CROSS_ENCODER**: Use transformer model for highest accuracy (slowest)

---

### Pagination

Use pagination for large result sets:

```bash
# First page
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "pagination": {
    "limit": 50
  }
}' localhost:50051 graphiti.v1.RetrieveService/GetEntityNodes

# Next page using cursor from previous response
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "pagination": {
    "uuid_cursor": "<next_cursor_from_previous_response>",
    "limit": 50
  }
}' localhost:50051 graphiti.v1.RetrieveService/GetEntityNodes
```

---

### Temporal Filtering

Filter results by date ranges:

```bash
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "query": "project updates",
  "filters": {
    "created_at": [
      {
        "filters": [
          {
            "date": "2026-01-01T00:00:00Z",
            "comparison_operator": "COMPARISON_OPERATOR_GREATER_THAN_EQUAL"
          },
          {
            "date": "2026-01-31T23:59:59Z",
            "comparison_operator": "COMPARISON_OPERATOR_LESS_THAN_EQUAL"
          }
        ]
      }
    ]
  }
}' localhost:50051 graphiti.v1.RetrieveService/AdvancedSearch
```

---

### Attribute Filtering

Filter by node/edge attributes:

```bash
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "query": "engineering team",
  "filters": {
    "node_labels": ["Person"],
    "property_filters": [
      {
        "property_name": "department",
        "string_value": "Engineering",
        "comparison_operator": "COMPARISON_OPERATOR_EQUALS"
      },
      {
        "property_name": "years_experience",
        "int_value": 5,
        "comparison_operator": "COMPARISON_OPERATOR_GREATER_THAN_EQUAL"
      }
    ]
  }
}' localhost:50051 graphiti.v1.RetrieveService/AdvancedSearch
```

---

### Batch Operations

Use bulk operations for efficiency:

```bash
# Bulk episode ingestion
grpcurl -plaintext -d '{
  "episodes": [
    {"group_id": "user_123", "name": "Episode 1", ...},
    {"group_id": "user_123", "name": "Episode 2", ...},
    {"group_id": "user_123", "name": "Episode 3", ...}
  ]
}' localhost:50051 graphiti.v1.IngestService/AddEpisodeBulk

# Bulk edge retrieval
grpcurl -plaintext -d '{
  "uuids": ["edge_1", "edge_2", "edge_3", ...]
}' localhost:50051 graphiti.v1.RetrieveService/GetEntityEdges

# Bulk deletion
grpcurl -plaintext -d '{
  "uuids": ["edge_1", "edge_2", "edge_3", ...]
}' localhost:50051 graphiti.v1.AdminService/DeleteEntityEdges
```

---

### Community Detection

Build and query communities for entity clustering:

```bash
# Build communities for a group
grpcurl -plaintext -d '{
  "group_ids": ["user_123"]
}' localhost:50051 graphiti.v1.AdminService/BuildCommunities

# Query communities
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "pagination": {"limit": 20}
}' localhost:50051 graphiti.v1.RetrieveService/GetCommunities

# Search with community context
grpcurl -plaintext -d '{
  "group_ids": ["user_123"],
  "query": "development teams",
  "config": {
    "community_config": {
      "search_methods": ["COMMUNITY_SEARCH_METHOD_COSINE_SIMILARITY"],
      "reranker": "COMMUNITY_RERANKER_RRF"
    }
  }
}' localhost:50051 graphiti.v1.RetrieveService/AdvancedSearch
```

---

### Contextual Memory Retrieval

Retrieve relevant facts based on conversation context:

```bash
grpcurl -plaintext -d '{
  "group_id": "user_123",
  "max_facts": 10,
  "messages": [
    {
      "uuid": "msg_1",
      "name": "User",
      "role": "user",
      "role_type": "human",
      "content": "What are the latest project updates?",
      "timestamp": "2026-01-22T10:00:00Z",
      "source_description": "Chat"
    },
    {
      "uuid": "msg_2",
      "name": "Assistant",
      "role": "assistant",
      "role_type": "ai",
      "content": "Which project are you interested in?",
      "timestamp": "2026-01-22T10:00:05Z",
      "source_description": "Chat"
    },
    {
      "uuid": "msg_3",
      "name": "User",
      "role": "user",
      "role_type": "human",
      "content": "The mobile app project",
      "timestamp": "2026-01-22T10:00:15Z",
      "source_description": "Chat"
    }
  ]
}' localhost:50051 graphiti.v1.RetrieveService/GetMemory
```

---

## Error Handling and Status Codes

### gRPC Status Codes

Graphiti uses standard gRPC status codes:

| Code | Name | Description |
|------|------|-------------|
| 0 | OK | Success |
| 1 | CANCELLED | Operation cancelled |
| 2 | UNKNOWN | Unknown error |
| 3 | INVALID_ARGUMENT | Invalid request parameters |
| 4 | DEADLINE_EXCEEDED | Operation timeout |
| 5 | NOT_FOUND | Resource not found |
| 6 | ALREADY_EXISTS | Resource already exists |
| 7 | PERMISSION_DENIED | Permission denied |
| 8 | RESOURCE_EXHAUSTED | Rate limit or quota exceeded |
| 9 | FAILED_PRECONDITION | Operation precondition failed |
| 10 | ABORTED | Operation aborted |
| 11 | OUT_OF_RANGE | Parameter out of range |
| 12 | UNIMPLEMENTED | Method not implemented |
| 13 | INTERNAL | Internal server error |
| 14 | UNAVAILABLE | Service unavailable |
| 15 | DATA_LOSS | Data loss or corruption |
| 16 | UNAUTHENTICATED | Authentication required |

---

### OperationResult

Many operations return `OperationResult` with detailed error information:

```json
{
  "success": false,
  "message": "Failed to delete entity edge",
  "error_code": "EDGE_NOT_FOUND",
  "error_details": "Edge with UUID 'invalid_uuid' does not exist"
}
```

---

### Error Handling Best Practices

1. **Check Status Codes**: Always check gRPC status codes in responses
2. **Parse Error Messages**: Extract useful information from error messages
3. **Implement Retries**: Use exponential backoff for transient errors (UNAVAILABLE, RESOURCE_EXHAUSTED)
4. **Validate Input**: Validate required fields before sending requests
5. **Handle Partial Failures**: In bulk operations, check individual results
6. **Log Errors**: Log error_code and error_details for debugging

Example error handling (pseudo-code):

```python
try:
    response = stub.AddEpisode(request)
except grpc.RpcError as e:
    if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
        # Fix input and retry
        pass
    elif e.code() == grpc.StatusCode.UNAVAILABLE:
        # Wait and retry
        time.sleep(backoff_time)
        retry()
    elif e.code() == grpc.StatusCode.INTERNAL:
        # Log and alert
        logger.error(f"Server error: {e.details()}")
    else:
        # Handle other cases
        pass
```

---

## Performance Optimization

### Ingestion Performance

1. **Batch Operations**: Use `AddEpisodeBulk` for multiple episodes
2. **Disable Community Updates**: Set `update_communities: false` during bulk ingestion
3. **Parallel Streaming**: Use `StreamEpisodes` for concurrent ingestion
4. **Saga Management**: Link episodes in sagas for better context without redundant processing

---

### Search Performance

1. **Limit Results**: Set appropriate `limit` values to avoid large result sets
2. **Use Filters**: Filter early with `SearchFilters` to reduce search space
3. **Choose Search Methods**: Select appropriate search methods for your use case
4. **Streaming**: Use `StreamSearch` for large result sets
5. **Center Nodes**: Provide `center_node_uuids` for focused graph traversal
6. **Minimum Scores**: Set `sim_min_score` and `reranker_min_score` to filter low-quality results

---

### Database Performance

1. **Build Indices**: Run `BuildIndices` after bulk ingestion
2. **Prune Data**: Regularly remove orphaned nodes/edges
3. **Archive Old Data**: Delete or archive old groups/episodes
4. **Pagination**: Always use pagination for large retrievals

---

## Testing with grpcurl

### Basic Connection Test

```bash
# List available services
grpcurl -plaintext localhost:50051 list

# List methods for a service
grpcurl -plaintext localhost:50051 list graphiti.v1.IngestService

# Describe a method
grpcurl -plaintext localhost:50051 describe graphiti.v1.IngestService.AddEpisode
```

---

### Health Check

```bash
grpcurl -plaintext -d '{}' localhost:50051 graphiti.v1.AdminService/HealthCheck
```

---

### Complete Workflow Example

```bash
# 1. Check health
grpcurl -plaintext -d '{}' localhost:50051 graphiti.v1.AdminService/HealthCheck

# 2. Get status
grpcurl -plaintext -d '{}' localhost:50051 graphiti.v1.AdminService/GetStatus

# 3. Add an episode
grpcurl -plaintext -d '{
  "group_id": "test_user",
  "name": "Test Episode",
  "episode_body": "Alice is working with Bob on the ML project",
  "reference_time": "2026-01-22T10:00:00Z",
  "source": "EPISODE_TYPE_TEXT",
  "source_description": "Test data",
  "update_communities": false
}' localhost:50051 graphiti.v1.IngestService/AddEpisode

# 4. Search for facts
grpcurl -plaintext -d '{
  "group_ids": ["test_user"],
  "query": "Who is working on ML?",
  "max_facts": 5
}' localhost:50051 graphiti.v1.RetrieveService/Search

# 5. Get episodes
grpcurl -plaintext -d '{
  "group_id": "test_user",
  "last_n": 10
}' localhost:50051 graphiti.v1.RetrieveService/GetEpisodes

# 6. Get entity nodes
grpcurl -plaintext -d '{
  "group_ids": ["test_user"],
  "pagination": {"limit": 20}
}' localhost:50051 graphiti.v1.RetrieveService/GetEntityNodes

# 7. Build communities
grpcurl -plaintext -d '{
  "group_ids": ["test_user"]
}' localhost:50051 graphiti.v1.AdminService/BuildCommunities

# 8. Clean up (optional)
grpcurl -plaintext -d '{
  "group_id": "test_user"
}' localhost:50051 graphiti.v1.AdminService/DeleteGroup
```

---

## Client SDK Generation

Generate client libraries from proto files:

### Python

```bash
python -m grpc_tools.protoc \
  -I./protos \
  --python_out=./generated \
  --grpc_python_out=./generated \
  protos/graphiti/v1/*.proto
```

### Go

```bash
protoc \
  -I=./protos \
  --go_out=./generated \
  --go-grpc_out=./generated \
  protos/graphiti/v1/*.proto
```

### Node.js

```bash
grpc_tools_node_protoc \
  --js_out=import_style=commonjs,binary:./generated \
  --grpc_out=grpc_js:./generated \
  -I ./protos \
  protos/graphiti/v1/*.proto
```

### Java

```bash
protoc \
  -I=./protos \
  --java_out=./generated \
  --grpc-java_out=./generated \
  protos/graphiti/v1/*.proto
```

---

## Security Considerations

### Authentication

Graphiti gRPC server does not include built-in authentication. Implement authentication using:

1. **Mutual TLS (mTLS)**: Client certificate authentication
2. **Token-based auth**: Pass tokens in gRPC metadata
3. **API Gateway**: Use a gateway (Envoy, Kong) for authentication
4. **VPC/Network isolation**: Restrict access at network level

### Authorization

- Implement group-based access control using `group_id`
- Validate that clients only access their authorized groups
- Audit access patterns and implement rate limiting

### Data Protection

- Use TLS for all production deployments
- Encrypt sensitive data in graph attributes
- Regularly audit and purge old data
- Implement data retention policies

---

## Additional Resources

- **Proto Files**: `/grpc_server/protos/graphiti/v1/`
- **Graphiti Documentation**: [Main README](../../README.md)
- **gRPC Documentation**: https://grpc.io/docs/
- **Protocol Buffers**: https://protobuf.dev/

---

## Support and Contributing

For issues, questions, or contributions:

- GitHub: https://github.com/getzep/graphiti
- Documentation: https://docs.getzep.com/
- Community: Join our Discord or Slack

---

*Generated for Graphiti gRPC API v1*
