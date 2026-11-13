from typing import Optional, List
from pydantic import BaseModel, Field


# ===================== USER & AUTH SCHEMAS =====================

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, examples=["Alex Taylor"])
    email: str = Field(..., examples=["alex@example.com"])
    phone: str = Field(..., min_length=10, max_length=20, examples=["+447123456789"])
    password: str = Field(..., min_length=8, examples=["Secret1234"])
    role: str = Field("both", pattern="^(poster|runner|both)$", examples=["both"])
    id_type: Optional[str] = Field("Passport", examples=["Passport", "UK Driving Licence", "National ID Card", "Student ID"])
    id_number: Optional[str] = Field(None, examples=["P98765432"])
    residential_address: Optional[str] = Field(None, examples=["14 Maplewood Street"])
    postcode: Optional[str] = Field(None, examples=["CF24 9ZZ"])


class UserLogin(BaseModel):
    email: str = Field(..., examples=["alex@example.com", "admin"])
    password: str = Field(..., examples=["Secret1234", "admin123"])


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    role: str
    username: Optional[str] = None
    id_type: Optional[str] = "Passport"
    id_number: Optional[str] = None
    residential_address: Optional[str] = None
    postcode: Optional[str] = None
    is_id_verified: Optional[int] = 1
    tasks_done: int
    joined_date: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user: UserResponse


class UserProfileUpdate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    role: str = Field("both", pattern="^(poster|runner|both)$")


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


# ===================== TASK SCHEMAS =====================

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150, examples=["Weekly Grocery Shopping"])
    description: Optional[str] = Field(None, max_length=2000, examples=["Pickup items from Tesco on Albany Road"])
    category: str = Field("Other", examples=["Grocery Shopping"])
    location: str = Field(..., min_length=2, max_length=200, examples=["Cardiff, CF24"])
    price: float = Field(..., gt=0, examples=[15.00])
    deadline: Optional[str] = Field(None, examples=["Tomorrow 5 PM"])


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = Field(None, min_length=2)
    price: Optional[float] = Field(None, gt=0)
    deadline: Optional[str] = None


class TaskCancel(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    location: str
    price: float
    deadline: Optional[str] = None
    status: str
    poster_id: int
    runner_id: Optional[int] = None
    poster_name: Optional[str] = None
    runner_name: Optional[str] = None
    runner_rating: Optional[float] = None
    posted_on: Optional[str] = None
    accepted_on: Optional[str] = None
    started_on: Optional[str] = None
    submitted_on: Optional[str] = None
    finished_on: Optional[str] = None
    cancelled_on: Optional[str] = None
    cancellation_reason: Optional[str] = None


# ===================== RATING SCHEMAS =====================

class RatingCreate(BaseModel):
    task_id: int
    rating: int = Field(..., ge=1, le=5, examples=[5])
    review: Optional[str] = Field(None, max_length=1000, examples=["Fast and friendly service!"])


class RatingResponse(BaseModel):
    id: int
    task_id: int
    reviewer_id: int
    reviewer_name: Optional[str] = None
    runner_id: int
    runner_name: Optional[str] = None
    task_title: Optional[str] = None
    rating: int
    review: Optional[str] = None
    created_on: str


# ===================== STATS & SYSTEM SCHEMAS =====================

class DashboardStats(BaseModel):
    total_open_tasks: int
    my_posted_tasks: int
    my_active_tasks: int
    my_completed_tasks: int
    my_earnings: float
    platform_total_tasks: int
    platform_completed_tasks: int
    runner_average_rating: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    timestamp: str


# ===================== AI & AUTONOMOUS ENGINE SCHEMAS =====================

class AIPromptRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=1500, examples=["Pick up groceries from Tesco Albany Rd tomorrow 4pm, paying 15 quid"])


class AIPricingRequest(BaseModel):
    category: str = Field("Other", examples=["Grocery Shopping"])
    title: Optional[str] = Field("", examples=["Grocery Shopping at Tesco"])
    description: Optional[str] = Field("", examples=["Need 2 bags of groceries picked up"])
    deadline: Optional[str] = Field("", examples=["Today 5 PM"])
    user_price: Optional[float] = Field(None, examples=[15.0])


class AICrosscheckRequest(BaseModel):
    completion_notes: Optional[str] = Field(None, max_length=1000, examples=["Delivered to front porch, receipt in bag"])

