# GraphQL

## Overview

GraphQL is a query language for APIs and a runtime for executing those queries. Developed by Facebook, it provides a complete and understandable description of the data in your API, giving clients the power to ask for exactly what they need.

## Key Characteristics

- **Flexible queries** - Clients specify exact data requirements.
- **Single endpoint** - All operations through one URL.
- **Strongly typed** - Schema defines API capabilities.
- **No over/under-fetching** - Get exactly what you request.
- **Introspection** - Self-documenting API.
- **Real-time** - Subscriptions for live data.

## Core Concepts

### Schema Definition Language (SDL)

```graphql
type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post!]!
  createdAt: DateTime!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  comments: [Comment!]!
  publishedAt: DateTime
}

type Comment {
  id: ID!
  text: String!
  author: User!
  post: Post!
}

type Query {
  user(id: ID!): User
  users(limit: Int, offset: Int): [User!]!
  post(id: ID!): Post
  posts(authorId: ID): [Post!]!
}

type Mutation {
  createUser(name: String!, email: String!): User!
  updateUser(id: ID!, name: String, email: String): User!
  deleteUser(id: ID!): Boolean!
  createPost(title: String!, content: String!, authorId: ID!): Post!
}

type Subscription {
  postCreated: Post!
  commentAdded(postId: ID!): Comment!
}
```

## Operations

### Query (Read)

```graphql
query GetUserWithPosts {
  user(id: "123") {
    id
    name
    email
    posts {
      id
      title
      publishedAt
    }
  }
}
```

### Mutation (Write)

```graphql
mutation CreatePost {
  createPost(
    title: "GraphQL Guide",
    content: "Learn GraphQL...",
    authorId: "123"
  ) {
    id
    title
    author {
      name
    }
  }
}
```

### Subscription (Real-time)

```graphql
subscription OnPostCreated {
  postCreated {
    id
    title
    author {
      name
    }
  }
}
```

## Architecture Diagram

```
┌──────────────────────────────────┐
│              Client              │
│  ┌────────────────────────────┐  │
│  │  GraphQL Query             │  │
│  │  {                         │  │
│  │    user(id: "123") {       │  │
│  │      name                  │  │
│  │      posts { title }       │  │
│  │    }                       │  │
│  │  }                         │  │
│  └────────────────────────────┘  │
└────────────────┬─────────────────┘
                 │
                 ▼
┌──────────────────────────────────┐
│         GraphQL Server           │
│  ┌────────────────────────────┐  │
│  │  Query Parser & Validator  │  │
│  └─────────────┬──────────────┘  │
│                ▼                 │
│  ┌────────────────────────────┐  │
│  │  Resolver Functions        │  │
│  │  - userResolver()          │  │
│  │  - postsResolver()         │  │
│  └─────────────┬──────────────┘  │
└────────────────┼─────────────────┘
                 │
       ┌─────────┴──────────┐
       ▼                    ▼
 ┌──────────┐      ┌───────────────┐
 │ Database │      │ REST APIs     │
 │          │      │ Microservices │
 └──────────┘      └───────────────┘
```

## Resolver Pattern

```javascript

const resolvers = {
  Query: {
    user: async (parent, { id }, context) => {
      return await context.db.user.findById(id);
    },
    users: async (parent, { limit, offset }, context) => {
      return await context.db.user.findMany({ limit, offset });
    },
  },
  
  Mutation: {
    createUser: async (parent, { name, email }, context) => {
      return await context.db.user.create({ name, email });
    },
  },
  
  User: {
    posts: async (parent, args, context) => {
      // parent is the User object
      return await context.db.post.findByAuthorId(parent.id);
    },
  },
  
  Subscription: {
    postCreated: {
      subscribe: (parent, args, context) => {
        return context.pubsub.asyncIterator(['POST_CREATED']);
      },
    },
  },
};
```

## N+1 Problem & Solutions

### Problem

```javascript
// Query
query {
  users {        // 1 query to get users
    posts {      // N queries (one per user)
      comments { // N*M queries
      }
    }
  }
}
```

### Solution: DataLoader

```javascript
const DataLoader = require('dataloader');

const postLoader = new DataLoader(async (userIds) => {
  // Batch load all posts for these user IDs
  const posts = await db.post.findByAuthorIds(userIds);
  
  // Group posts by author ID
  return userIds.map(id => 
    posts.filter(post => post.authorId === id)
  );
});

// In resolver
User: {
  posts: (parent) => postLoader.load(parent.id)
}
```

## Query Complexity & Rate Limiting

### Calculate Query Complexity

```javascript
function calculateComplexity(query) {
  let complexity = 0;
  
  // Each field has a cost
  // Nested fields multiply cost
  // Lists multiply by estimated size
  
  return complexity;
}

// Set max complexity
const MAX_COMPLEXITY = 1000;
```

### Depth Limiting

```javascript
const depthLimit = require('graphql-depth-limit');

const server = new ApolloServer({
  schema,
  validationRules: [depthLimit(5)] // Max depth of 5
});
```

## Pagination Patterns

### Offset-based

```graphql
query {
  users(limit: 10, offset: 20) {
    id
    name
  }
}
```

### Cursor-based (Relay Connection)

```graphql
query {
  users(first: 10, after: "cursor123") {
    edges {
      node {
        id
        name
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## Error Handling

```json
{
  "data": {
    "user": null
  },
  "errors": [
    {
      "message": "User not found",
      "locations": [{ "line": 2, "column": 3 }],
      "path": ["user"],
      "extensions": {
        "code": "NOT_FOUND",
        "userId": "123"
      }
    }
  ]
}
```

## Caching Strategies

### Client-Side (Apollo Client)

```javascript
// Automatic normalized cache
const client = new ApolloClient({
  cache: new InMemoryCache({
    typePolicies: {
      Query: {
        fields: {
          user: {
            read(_, { args, toReference }) {
              return toReference({
                __typename: 'User',
                id: args.id,
              });
            },
          },
        },
      },
    },
  }),
});
```

### Server-Side

- **Response caching** - Cache entire query results.
- **Partial caching** - Cache individual resolvers.
- **CDN caching** - Use GET for queries with cache headers.

## When to Use GraphQL

### ✅ Good For:

- Complex, nested data requirements.
- Multiple clients with different needs (web, mobile).
- Rapid frontend iteration.
- When avoiding over-fetching is important.
- API aggregation layer (BFF pattern).
- Real-time features with subscriptions.

### ❌ Less Ideal For:

- Simple CRUD APIs.
- File uploads (possible but cumbersome).
- When HTTP caching is critical.
- Very simple use cases.
- When REST tooling/experience is required.

## System Design Considerations

### Scalability

- **Query complexity limits** - Prevent expensive queries.
- **Pagination** - Use cursor-based for consistency.
- **DataLoader** - Batch and cache database queries.
- **Horizontal scaling** - Stateless resolvers.
- **CDN** - Cache GET queries.

### Performance

- **Persistent queries** - Pre-register queries, send hash.
- **Automatic Persisted Queries (APQ)** - Cache queries by hash.
- **Field-level caching** - Cache individual resolver results.
- **Lazy loading** - Load data on-demand.
- **Query batching** - Combine multiple queries.

### Security

- **Query depth limiting** - Prevent deeply nested queries.
- **Query complexity analysis** - Estimate cost before execution.
- **Rate limiting** - Per user/token.
- **Authentication** - Via context.
- **Authorization** - Field-level permissions.
- **Disable introspection in production**

### Reliability

- **Schema validation** - Type safety at compile time.
- **Error handling** - Partial responses with errors array.
- **Monitoring** - Track slow resolvers.
- **Timeout handling** - Set resolver timeouts.

## GraphQL vs REST

| Aspect | GraphQL | REST |
|--------|---------|------|
| Endpoints | Single | Multiple |
| Data fetching | Exact fields | Fixed structure |
| Versioning | Schema evolution | URL/header versioning |
| Caching | Complex | HTTP caching |
| Learning curve | Steep | Easy |
| Tooling | Growing | Mature |
| Over-fetching | No | Yes |
| Type system | Built-in | External (OpenAPI) |

## Common Interview Questions

1. **What problem does GraphQL solve?**
   - Over-fetching and under-fetching.
   - Multiple round trips.
   - API versioning challenges.
   - Flexible data requirements.

2. **How do you handle the N+1 problem?**
   - DataLoader for batching.
   - Batch queries at database level.
   - Optimize resolvers.
   - Monitor query performance.

3. **How do you scale GraphQL APIs?**
   - Query complexity limits.
   - Horizontal scaling of servers.
   - Caching at multiple layers.
   - DataLoader for batching.
   - CDN for GET queries.

4. **GraphQL vs REST - when to use each?**
   - GraphQL: Complex nested data, multiple clients.
   - REST: Simple CRUD, HTTP caching important.

5. **How do you handle authentication/authorization?**
   - Auth tokens in headers.
   - Context object with user info.
   - Field-level authorization in resolvers.
   - Directive-based permissions.

## Best Practices

- Design schema first, not database-driven.
- Use meaningful names for fields.
- Implement proper error handling.
- Use DataLoader to prevent N+1.
- Set query complexity limits.
- Implement pagination for lists.
- Use subscriptions sparingly (expensive).
- Enable query batching.
- Monitor resolver performance.
- Use strong typing everywhere.
- Document schema with descriptions.
- Version schema with deprecation.

## Advanced Patterns

### Federation (Microservices)

```graphql
# Users service
type User @key(fields: "id") {
  id: ID!
  name: String!
}

# Posts service
extend type User @key(fields: "id") {
  id: ID! @external
  posts: [Post!]!
}
```

### Directives

```graphql
type Query {
  user: User @auth(requires: ADMIN)
  posts: [Post!]! @cache(maxAge: 60)
}
```

### Interface & Union Types

```graphql
interface Node {
  id: ID!
}

type User implements Node {
  id: ID!
  name: String!
}

union SearchResult = User | Post | Comment
```

## Trade-offs

| Aspect | Advantage | Disadvantage |
|--------|-----------|--------------|
| Flexibility | Client gets exactly what it needs | More complex than REST |
| Performance | Reduces API calls | Can be slower without optimization |
| Type safety | Strong schema validation | Requires schema design effort |
| Caching | Fine-grained control | HTTP caching not automatic |
| Learning curve | Powerful once learned | Steeper than REST |

## Related Patterns

- [REST API](../rest-api/README.md) - Alternative API design.
- [gRPC](../grpc/README.md) - High-performance RPC.
- [WebSocket](../websocket/README.md) - For GraphQL subscriptions.
- [Server-Sent Events](../server-sent-events/README.md) - Alternative to subscriptions.
