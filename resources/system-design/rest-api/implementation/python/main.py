"""
REST API Implementation with FastAPI

Demonstrates REST best practices:
- CRUD operations with proper HTTP methods
- Request/response validation with Pydantic
- Pagination and filtering
- Error handling
- Rate limiting
- API versioning
- Automatic OpenAPI documentation
"""
import time

from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Header, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import uuid4, UUID

# ============= Pydantic Models ============= #

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    pass

class UserUpdate(UserBase):
    pass


class UserPartialUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None


class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class PostCreate(PostBase):
    pass


class Post(PostBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PaginationMetadata(BaseModel):
    total: int
    limit: int
    offset: int
    has_more: bool


class UserListResponse(BaseModel):
    data: List[User]
    pagination: PaginationMetadata


class PostListResponse(BaseModel):
    data: List[Post]
    pagination: PaginationMetadata


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime


# ============= FastAPI App ============= #

app = FastAPI(
    title="REST API Example",
    description="A comprehensive REST API implementation demonstrating best practices",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# In-memory database (simplified - use a real database in production)
users_db = {}
posts_db = {}

# Rate limiting (simplified - use Redis in production)
rate_limit_storage = {}


# ============= Dependencies ============= #

def verify_auth(authorization: Optional[str] = Header(None)):
    """Verify authentication token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authorization header"
        )
    return authorization


def rate_limiter(max_requests: int = 100, window_seconds: int = 3600):
    """Simple rate limiting dependency"""
    def limiter(authorization: Optional[str] = Header(None)):
        if not authorization:
            client_id = "anonymous"
        else:
            client_id = authorization
        
        current_time = time.time()
        
        if client_id not in rate_limit_storage:
            rate_limit_storage[client_id] = []
        
        # Remove old requests outside the window
        rate_limit_storage[client_id] = [
            req_time for req_time in rate_limit_storage[client_id]
            if current_time - req_time < window_seconds
        ]
        
        # Check rate limit
        if len(rate_limit_storage[client_id]) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        rate_limit_storage[client_id].append(current_time)
        return True
    
    return limiter


# ============= User Endpoints =============

@app.get(
    "/api/v1/users",
    response_model=UserListResponse,
    tags=["users"],
    summary="List all users"
)
async def list_users(
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    sort: str = Query("created_at", description="Sort field (prefix with - for descending)"),
    _: bool = Depends(rate_limiter(max_requests=100, window_seconds=3600))
):
    """
    Retrieve a paginated list of users.
    
    - **limit**: Maximum number of users to return (1-100)
    - **offset**: Number of users to skip
    - **sort**: Field to sort by (use -field for descending order)
    """
    users_list = list(users_db.values())
    total = len(users_list)
    
    # Sort
    reverse = sort.startswith('-')
    sort_key = sort[1:] if reverse else sort
    
    try:
        users_list.sort(key=lambda x: getattr(x, sort_key, ''), reverse=reverse)
    except AttributeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort field: {sort_key}"
        )
    
    # Paginate
    paginated_users = users_list[offset:offset + limit]
    
    return UserListResponse(
        data=paginated_users,
        pagination=PaginationMetadata(
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + limit < total
        )
    )


@app.get(
    "/api/v1/users/{user_id}",
    response_model=User,
    tags=["users"],
    summary="Get a user by ID"
)
async def get_user(user_id: UUID):
    """
    Retrieve a specific user by ID.
    
    Returns 404 if user not found.
    """
    user = users_db.get(str(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@app.post(
    "/api/v1/users",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
    summary="Create a new user"
)
async def create_user(
    user_data: UserCreate,
    authorization: str = Depends(verify_auth),
    _: bool = Depends(rate_limiter(max_requests=20, window_seconds=3600))
):
    """
    Create a new user.
    
    Requires authentication.
    """
    user_id = str(uuid4())
    now = datetime.utcnow()
    
    user = User(
        id=user_id,
        name=user_data.name,
        email=user_data.email,
        created_at=now,
        updated_at=now
    )
    
    users_db[user_id] = user
    
    return user


@app.put(
    "/api/v1/users/{user_id}",
    response_model=User,
    tags=["users"],
    summary="Update a user (full replacement)"
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    authorization: str = Depends(verify_auth)
):
    """
    Update a user with full replacement.
    
    All fields must be provided. Use PATCH for partial updates.
    """
    user = users_db.get(str(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.name = user_data.name
    user.email = user_data.email
    user.updated_at = datetime.utcnow()
    
    return user


@app.patch(
    "/api/v1/users/{user_id}",
    response_model=User,
    tags=["users"],
    summary="Partially update a user"
)
async def patch_user(
    user_id: UUID,
    user_data: UserPartialUpdate,
    authorization: str = Depends(verify_auth)
):
    """
    Partially update a user.
    
    Only provided fields will be updated.
    """
    user = users_db.get(str(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update only provided fields
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    
    return user


@app.delete(
    "/api/v1/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["users"],
    summary="Delete a user"
)
async def delete_user(
    user_id: UUID,
    authorization: str = Depends(verify_auth)
):
    """
    Delete a user.
    
    Returns 204 No Content on success.
    """
    if str(user_id) not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    del users_db[str(user_id)]
    return None


# ============= Post Endpoints (Nested Resources) =============

@app.get(
    "/api/v1/users/{user_id}/posts",
    response_model=PostListResponse,
    tags=["posts"],
    summary="Get all posts for a user"
)
async def list_user_posts(
    user_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Retrieve all posts for a specific user.
    """
    if str(user_id) not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Filter posts by user_id
    user_posts = [
        post for post in posts_db.values()
        if str(post.user_id) == str(user_id)
    ]
    
    total = len(user_posts)
    paginated_posts = user_posts[offset:offset + limit]
    
    return PostListResponse(
        data=paginated_posts,
        pagination=PaginationMetadata(
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + limit < total
        )
    )


@app.post(
    "/api/v1/users/{user_id}/posts",
    response_model=Post,
    status_code=status.HTTP_201_CREATED,
    tags=["posts"],
    summary="Create a post for a user"
)
async def create_post(
    user_id: UUID,
    post_data: PostCreate,
    authorization: str = Depends(verify_auth)
):
    """
    Create a new post for a user.
    """
    if str(user_id) not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    post_id = str(uuid4())
    now = datetime.utcnow()
    
    post = Post(
        id=post_id,
        user_id=user_id,
        title=post_data.title,
        content=post_data.content,
        created_at=now,
        updated_at=now
    )
    
    posts_db[post_id] = post
    
    return post


@app.get(
    "/api/v1/posts/{post_id}",
    response_model=Post,
    tags=["posts"],
    summary="Get a post by ID"
)
async def get_post(post_id: UUID):
    """
    Retrieve a specific post by ID.
    """
    post = posts_db.get(str(post_id))
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    return post


# ============= Health & Info Endpoints =============

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check"
)
async def health_check():
    """
    Check API health status.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.get(
    "/api/v1",
    tags=["info"],
    summary="API information"
)
async def api_info():
    """
    Get API version and available endpoints.
    """
    return {
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "users": "/api/v1/users",
            "posts": "/api/v1/posts",
            "health": "/health"
        }
    }


# ============= Startup Event =============

@app.on_event("startup")
async def startup_event():
    """Initialize with sample data"""
    # Create sample user
    user_id = str(uuid4())
    now = datetime.utcnow()
    
    sample_user = User(
        id=user_id,
        name="John Doe",
        email="john@example.com",
        created_at=now,
        updated_at=now
    )
    
    users_db[user_id] = sample_user
    
    # Create sample post
    post_id = str(uuid4())
    sample_post = Post(
        id=post_id,
        user_id=user_id,
        title="Welcome Post",
        content="This is a sample post to demonstrate the API",
        created_at=now,
        updated_at=now
    )
    
    posts_db[post_id] = sample_post
    
    print(f"✓ Sample user created: {user_id}")
    print(f"✓ Sample post created: {post_id}")
    print("✓ API Documentation: http://localhost:8000/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
